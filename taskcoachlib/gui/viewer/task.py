# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import wx
from taskcoachlib import patterns, command, widgets, domain
from taskcoachlib.domain import task, date
from taskcoachlib.i18n import _
from taskcoachlib.gui import uicommand, menu, render, dialog
from taskcoachlib.thirdparty.calendar import wxSCHEDULER_NEXT, wxSCHEDULER_PREV, \
    wxSCHEDULER_TODAY, wxSCHEDULER_HORIZONTAL, wxSCHEDULER_TODAY, wxSCHEDULER_MONTHLY, \
    wxFancyDrawer
import base, mixin


class BaseTaskViewer(mixin.SearchableViewerMixin, 
                     mixin.FilterableViewerForTasksMixin,
                     base.UpdatePerSecondViewer, base.TreeViewer, 
                     patterns.Observer):
    defaultTitle = _('Tasks')
    defaultBitmap = 'led_blue_icon'
    
    def __init__(self, *args, **kwargs):
        super(BaseTaskViewer, self).__init__(*args, **kwargs)
        self.__registerForAppearanceChanges()
        
    def domainObjectsToView(self):
        return self.taskFile.tasks()

    def isShowingTasks(self): 
        return True

    def createFilter(self, taskList):
        tasks = domain.base.DeletedFilter(taskList)
        return super(BaseTaskViewer, self).createFilter(tasks)

    def trackStartEventType(self):
        return task.Task.trackStartEventType()
    
    def trackStopEventType(self):
        return task.Task.trackStopEventType()

    def newItemDialog(self, *args, **kwargs):
        kwargs['categories'] = self.taskFile.categories().filteredCategories()
        return super(BaseTaskViewer, self).newItemDialog(*args, **kwargs)
    
    def editItemDialog(self, items, bitmap, columnName=''):
        if isinstance(items[0], task.Task):
            return super(BaseTaskViewer, self).editItemDialog(items, bitmap, columnName)
        else:
            return dialog.editor.EffortEditor(wx.GetTopLevelParent(self),
                command.EditEffortCommand(self.taskFile.efforts(), items),
                self.settings, self.taskFile.efforts(), self.taskFile,  
                bitmap=bitmap)
            
    def itemEditorClass(self):
        return dialog.editor.TaskEditor
    
    def newItemCommandClass(self):
        return command.NewTaskCommand
    
    def newSubItemCommandClass(self):
        return command.NewSubTaskCommand
    
    def editItemCommandClass(self):
        return command.EditTaskCommand

    def deleteItemCommand(self):
        return command.DeleteTaskCommand(self.presentation(), self.curselection(),
                  shadow=self.settings.getboolean('feature', 'syncml'))    

    def createTaskPopupMenu(self):
        return menu.TaskPopupMenu(self.parent, self.settings,
                                  self.presentation(), self.taskFile.efforts(),
                                  self.taskFile.categories(), self)

    def createToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        taskUICommands = \
            [None,
             uicommand.TaskNew(taskList=self.presentation(),
                               settings=self.settings),
             uicommand.TaskNewSubTask(taskList=self.presentation(),
                                      viewer=self),
             uicommand.TaskNewFromTemplateButton(taskList=self.presentation(),
                                                 settings=self.settings,
                                                 bitmap='newtmpl'),
             uicommand.TaskEdit(taskList=self.presentation(), viewer=self),
             uicommand.TaskDelete(taskList=self.presentation(), viewer=self),
             None,
             uicommand.TaskToggleCompletion(viewer=self),
             None,
             uicommand.ViewerHideCompletedTasks(viewer=self,
                 bitmap='filtercompletedtasks'),
             uicommand.ViewerHideInactiveTasks(viewer=self,
                 bitmap='filterinactivetasks')]
        if self.settings.getboolean('feature', 'effort'):
            taskUICommands.extend([
                # EffortStart needs a reference to the original (task) list to
                # be able to stop tracking effort for tasks that are already 
                # being tracked, but that might be filtered in the viewer's 
                # presentation.
                None,
                uicommand.EffortStart(viewer=self, 
                                      taskList=self.taskFile.tasks()),
                uicommand.EffortStop(taskList=self.presentation())])
        
        baseUICommands = super(BaseTaskViewer, self).createToolBarUICommands()    
        # Insert the task viewer UI commands before the search box:
        return baseUICommands[:-2] + taskUICommands + baseUICommands[-2:]
 
    def statusMessages(self):
        status1 = _('Tasks: %d selected, %d visible, %d total')%\
            (len(self.curselection()), self.nrOfVisibleTasks(), 
             self.presentation().originalLength())         
        status2 = _('Status: %d over due, %d inactive, %d completed')% \
            (self.presentation().nrOverdue(), self.presentation().nrInactive(),
             self.presentation().nrCompleted())
        return status1, status2
    
    def nrOfVisibleTasks(self):
        # Make this overridable for viewers where the widget does not show all
        # items in the presentation, i.e. the widget does filtering on its own.
        return len(self.presentation())

    def __registerForAppearanceChanges(self):
        colorSettings = ['color.%s'%setting for setting in 'activetasks',\
            'inactivetasks', 'completedtasks', 'duesoontasks', 'overduetasks'] 
        colorSettings.append('behavior.duesoonhours')
        for colorSetting in colorSettings:
            patterns.Publisher().registerObserver(self.onColorSettingChange, 
                eventType=colorSetting)
        for eventType in (task.Task.foregroundColorChangedEventType(),
                          task.Task.backgroundColorChangedEventType(),
                          task.Task.fontChangedEventType(),
                          task.Task.iconChangedEventType(),
                          task.Task.selectedIconChangedEventType(),
                          task.Task.percentageCompleteChangedEventType()):
            patterns.Publisher().registerObserver(self.onAttributeChanged,
                                                  eventType=eventType)
        patterns.Publisher().registerObserver(self.atMidnight,
            eventType='clock.midnight')
        patterns.Publisher().registerObserver(self.onWake,
            eventType='powermgt.on')

    def atMidnight(self, event): # pylint: disable-msg=W0613
        pass

    def onWake(self, event):
        self.refresh()
        
    def onColorSettingChange(self, event): # pylint: disable-msg=W0613
        self.refresh()

    def iconName(self, item, isSelected):
        return item.selectedIcon(recursive=True) if isSelected else item.icon(recursive=True)

    def getItemTooltipData(self, task):
        if not self.settings.getboolean('view', 'descriptionpopups'):
            return []
        result = [(self.iconName(task, task in self.curselection()), 
                   [self.getItemText(task)])]
        if task.description():
            result.append((None, map(lambda x: x.rstrip('\n'),
                                 task.description().split('\n'))))
        if task.notes():
            result.append(('note_icon', sorted([note.subject() for note in task.notes()])))
        if task.attachments():
            result.append(('paperclip_icon',
                sorted([unicode(attachment) for attachment in task.attachments()])))
        return result

    def label(self, task):
        return self.getItemText(task)


class RootNode(object):
    def __init__(self, tasks):
        self.tasks = tasks
        
    def subject(self):
        return ''
    
    def children(self, recursive=False):
        if recursive:
            return self.tasks[:]
        else:
            return self.tasks.rootItems()

    def foregroundColor(self, *args, **kwargs):
        return None

    def backgroundColor(self, *args, **kwargs):
        return None
    
    def font(self, *args, **kwargs):
        return None

    def completed(self, *args, **kwargs):
        return False

    dueSoon = inactive = overdue = isBeingTracked = completed


class SquareMapRootNode(RootNode):
    def __getattr__(self, attr):
        def getTaskAttribute(recursive=True):
            if recursive:
                return max(sum((getattr(task, attr)(recursive=True) for task in self.children()),
                               self.__zero), 
                           self.__zero)
            else:
                return self.__zero

        if attr in ('budget', 'budgetLeft', 'timeSpent'):
            self.__zero = date.TimeDelta()
        else:
            self.__zero = 0
        return getTaskAttribute


class TimelineRootNode(RootNode):
    def children(self, recursive=False):
        children = super(TimelineRootNode, self).children(recursive)
        children.sort(key=lambda task: task.startDateTime())
        return children
    
    def parallel_children(self, recursive=False):
        return self.children(recursive)

    def sequential_children(self):
        return []

    def startDateTime(self, recursive=False):
        startDateTimes = [item.startDateTime(recursive=True) for item in self.parallel_children()]
        startDateTimes = [dt for dt in startDateTimes if dt != date.DateTime()]
        if not startDateTimes:
            startDateTimes.append(date.Now())
        return min(startDateTimes)
    
    def dueDateTime(self, recursive=False):
        dueDateTimes = [item.dueDateTime(recursive=True) for item in self.parallel_children()]
        dueDatetimes = [dt for dt in dueDateTimes if dt != date.DateTime()]
        if not dueDateTimes:
            dueDateTimes.append(date.Now() + date.oneDay)    
        return max(dueDateTimes)
    

class TimelineViewer(BaseTaskViewer):
    defaultTitle = _('Timeline')
    defaultBitmap = 'timelineviewer'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'timelineviewer')
        super(TimelineViewer, self).__init__(*args, **kwargs)
        for eventType in (task.Task.subjectChangedEventType(), 'task.startDateTime',
            'task.dueDateTime', 'task.completionDateTime'):
            self.registerObserver(self.onAttributeChanged, eventType)
        
    def createWidget(self):
        self.rootNode = TimelineRootNode(self.presentation())
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        return widgets.Timeline(self, self.rootNode, self.onSelect, self.onEdit,
                                itemPopupMenu)

    def onEdit(self, item):
        if isinstance(item, task.Task):
            edit = uicommand.TaskEdit(taskList=self.presentation(), viewer=self)
        else:
            edit = uicommand.EffortEdit(effortList=self.taskFile.efforts(), viewer=self)
        edit(item)
        
    def curselection(self):
        # Override curselection, because there is no need to translate indices
        # back to domain objects. Our widget already returns the selected domain
        # object itself.
        return self.widget.curselection()
    
    def bounds(self, item):
        times = [self.start(item), self.stop(item)]
        for child in self.parallel_children(item) + self.sequential_children(item):
            times.extend(self.bounds(child))
        times = [time for time in times if time is not None]
        if times:
            return min(times), max(times)
        else:
            return []
 
    def start(self, item, recursive=False):
        try:
            start = item.startDateTime(recursive=recursive)
            if start == date.DateTime():
                return None
        except AttributeError:
            start = item.getStart()
        return start.toordinal()

    def stop(self, item, recursive=False):
        try:
            if item.completed():
                stop = item.completionDateTime(recursive=recursive)
            else:
                stop = item.dueDateTime(recursive=recursive)
            if stop == date.DateTime():
                return None   
            else:
                stop += date.oneDay
        except AttributeError:
            stop = item.getStop()
            if not stop:
                return None
        return stop.toordinal() 

    def sequential_children(self, item):
        try:
            return item.efforts()
        except AttributeError:
            return []

    def parallel_children(self, item, recursive=False):
        try:
            children = [child for child in item.children(recursive=recursive) \
                        if child in self.presentation()]
            children.sort(key=lambda task: task.startDateTime())
            return children
        except AttributeError:
            return []

    def foreground_color(self, item, depth=0):
        return item.foregroundColor(recursive=True)
          
    def background_color(self, item, depth=0):
        return item.backgroundColor(recursive=True)
    
    def font(self, item, depth=0):
        return item.font(recursive=True)

    def icon(self, item, isSelected=False):
        bitmap = self.iconName(item, isSelected)
        return wx.ArtProvider_GetIcon(bitmap, wx.ART_MENU, (16,16))
    
    def now(self):
        return date.Now().toordinal()
    
    def nowlabel(self):
        return _('Now')

    def getItemTooltipData(self, item):
        if not self.settings.getboolean('view', 'descriptionpopups'):
            result = []
        elif isinstance(item, task.Task):
            result = super(TimelineViewer, self).getItemTooltipData(item)
        else:
            result = [(None, [render.dateTimePeriod(item.getStart(), item.getStop())])]
            if item.description(): 
                result.append((None, map(lambda x: x.rstrip('\n'),
                                 item.description().split('\n'))))       
        return result


class SquareTaskViewer(BaseTaskViewer):
    defaultTitle = _('Task square map')
    defaultBitmap = 'squaremapviewer'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'squaretaskviewer')
        self.__orderBy = 'revenue'
        self.__transformTaskAttribute = lambda x: x
        self.__zero = 0
        super(SquareTaskViewer, self).__init__(*args, **kwargs)
        self.orderBy(self.settings.get(self.settingsSection(), 'sortby'))
        self.orderUICommand.setChoice(self.__orderBy)
        for eventType in (task.Task.subjectChangedEventType(), 'task.dueDateTime',
            'task.startDateTime', 'task.completionDateTime'):
            self.registerObserver(self.onAttributeChanged, eventType)

    def curselectionIsInstanceOf(self, class_):
        return class_ == task.Task
    
    def createWidget(self):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        return widgets.SquareMap(self, SquareMapRootNode(self.presentation()), 
            self.onSelect, 
            uicommand.TaskEdit(taskList=self.presentation(), viewer=self),
            itemPopupMenu)
        
    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(SquareTaskViewer, self).getToolBarUICommands()
        toolBarUICommands.insert(-2, None) # Separator
        self.orderUICommand = \
            uicommand.SquareTaskViewerOrderChoice(viewer=self)
        toolBarUICommands.insert(-2, self.orderUICommand)
        return toolBarUICommands
    
    def orderBy(self, choice):
        if choice == self.__orderBy:
            return
        oldChoice = self.__orderBy
        self.__orderBy = choice
        self.settings.set(self.settingsSection(), 'sortby', choice)
        self.removeObserver(self.onAttributeChanged, 'task.%s'%oldChoice)
        self.registerObserver(self.onAttributeChanged, 'task.%s'%choice)
        if choice in ('budget', 'timeSpent'):
            self.__transformTaskAttribute = lambda timeSpent: timeSpent.milliseconds()/1000
            self.__zero = date.TimeDelta()
        else:
            self.__transformTaskAttribute = lambda x: x
            self.__zero = 0
        self.refresh()
        
    def curselection(self):
        # Override curselection, because there is no need to translate indices
        # back to domain objects. Our widget already returns the selected domain
        # object itself.
        return self.widget.curselection()
    
    def nrOfVisibleTasks(self):
        return len([task for task in self.presentation() if getattr(task, 
                    self.__orderBy)(recursive=True) > self.__zero])
        

    # SquareMap adapter methods:
    
    def overall(self, task):
        return self.__transformTaskAttribute(max(getattr(task, self.__orderBy)(recursive=True),
                                                 self.__zero))
    
    def children_sum(self, children, parent): # pylint: disable-msg=W0613
        children_sum = sum((max(getattr(child, self.__orderBy)(recursive=True), self.__zero) for child in children \
                            if child in self.presentation()), self.__zero)
        return self.__transformTaskAttribute(max(children_sum, self.__zero))
    
    def empty(self, task):
        overall = self.overall(task)
        if overall:
            children_sum = self.children_sum(self.children(task), task)
            return max(self.__transformTaskAttribute(self.__zero), (overall - children_sum))/float(overall)
        return 0
    
    def getItemText(self, task):
        text = super(SquareTaskViewer, self).getItemText(task)
        value = self.render(getattr(task, self.__orderBy)(recursive=False))
        return '%s (%s)'%(text, value) if value else text

    def value(self, task, parent=None): # pylint: disable-msg=W0613
        return self.overall(task)

    def foreground_color(self, task, depth): # pylint: disable-msg=W0613
        return task.foregroundColor(recursive=True)
        
    def background_color(self, task, depth): # pylint: disable-msg=W0613
        return task.backgroundColor(recursive=True)
    
    def font(self, task, depth): # pylint: disable-msg=W0613
        return task.font(recursive=True)

    def icon(self, task, isSelected):
        bitmap = self.iconName(task, isSelected) or 'led_blue_icon'
        return wx.ArtProvider_GetIcon(bitmap, wx.ART_MENU, (16,16))

    # Helper methods
    
    renderer = dict(budget=render.budget, timeSpent=render.timeSpent, 
                    fixedFee=render.monetaryAmount, 
                    revenue=render.monetaryAmount,
                    priority=render.priority)
    
    def render(self, value):
        return self.renderer[self.__orderBy](value)

    

class CalendarViewer(mixin.AttachmentDropTargetMixin,
                     mixin.SortableViewerForTasksMixin,
                     BaseTaskViewer):
    defaultTitle = _('Calendar')
    defaultBitmap = 'calendar_icon'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'calendarviewer')
        super(CalendarViewer, self).__init__(*args, **kwargs)

        self.widget.SetViewType(self.settings.getint(self.settingsSection(), 'viewtype'))
        self.widget.SetStyle(self.settings.getint(self.settingsSection(), 'vieworientation'))
        self.widget.SetPeriodCount(self.settings.getint(self.settingsSection(), 'periodcount'))
        self.widget.SetPeriodWidth(self.settings.getint(self.settingsSection(), 'periodwidth'))

        self.periodCountUICommand.setValue(self.settings.getint(self.settingsSection(), 'periodcount'))
        self.periodCountUICommand.enable(self.widget.GetViewType() != wxSCHEDULER_MONTHLY)
        self.typeUICommand.setChoice(self.settings.getint(self.settingsSection(), 'viewtype'))
        self.orientationUICommand.setChoice(self.settings.getint(self.settingsSection(), 'vieworientation'))
        self.filterChoiceUICommand.setChoice((self.settings.getboolean(self.settingsSection(), 'shownostart'),
                                              self.settings.getboolean(self.settingsSection(), 'shownodue'),
                                              self.settings.getboolean(self.settingsSection(), 'showunplanned')))

        start = self.settings.get(self.settingsSection(), 'viewdate')
        if start:
            dt = wx.DateTime.Now()
            dt.ParseDateTime(start)
            self.widget.SetDate(dt)

        self.widget.SetWorkHours(self.settings.getint('view', 'efforthourstart'),
                                 self.settings.getint('view', 'efforthourend'))

        self.widget.SetShowNoStartDate(self.settings.getboolean(self.settingsSection(), 'shownostart'))
        self.widget.SetShowNoDueDate(self.settings.getboolean(self.settingsSection(), 'shownodue'))
        self.widget.SetShowUnplanned(self.settings.getboolean(self.settingsSection(), 'showunplanned'))

        for eventType in ('view.efforthourstart', 'view.efforthourend'):
            self.registerObserver(self.onWorkingHourChanged, eventType)

        for eventType in (task.Task.subjectChangedEventType(), 'task.startDateTime',
                          'task.dueDateTime', 'task.completionDateTime',
                          task.Task.attachmentsChangedEventType(),
                          task.Task.notesChangedEventType()):
            self.registerObserver(self.onAttributeChanged, eventType)

    def isTreeViewer(self):
        return False

    def onEverySecond(self, event): # pylint: disable-msg=W0221,W0613
        pass # Too expensive

    def atMidnight(self, event):
        if not self.settings.get(self.settingsSection(), 'viewdate'):
            # User has selected the "current" date/time; it may have
            # changed now
            self.SetViewType(wxSCHEDULER_TODAY)

    def onWake(self, event):
        self.atMidnight(event)

    def onWorkingHourChanged(self, event):
        self.widget.SetWorkHours(self.settings.getint('view', 'efforthourstart'),
                                 self.settings.getint('view', 'efforthourend'))

    def createWidget(self):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        widget = widgets.Calendar(self, self.presentation(), self.iconName, self.onSelect,
                                  self.onEdit, self.onCreate, self.onChangeConfig, itemPopupMenu,
                                  **self.widgetCreationKeywordArguments())

        if self.settings.getboolean('calendarviewer', 'gradient'):
            # If called directly, we crash with a Cairo assert failing...
            wx.CallAfter(widget.SetDrawer, wxFancyDrawer)

        return widget

    def onChangeConfig(self):
        self.settings.set(self.settingsSection(), 'periodwidth', str(self.widget.GetPeriodWidth()))

    def onEdit(self, item):
        edit = uicommand.TaskEdit(taskList=self.presentation(), viewer=self)
        edit(item)

    def onCreate(self, dateTime, show=True):
        startDateTime = dateTime
        dueDateTime = dateTime.endOfDay() if dateTime == dateTime.startOfDay() else dateTime
        create = uicommand.TaskNew(taskList=self.presentation(), 
                                   settings=self.settings,
                                   taskKeywords=dict(startDateTime=startDateTime, 
                                                     dueDateTime=dueDateTime))
        return create(event=None, show=show)

    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(CalendarViewer, self).getToolBarUICommands()
        toolBarUICommands.insert(-2, None) # Separator
        self.periodCountUICommand = uicommand.CalendarViewerPeriodCount(viewer=self)
        self.typeUICommand = uicommand.CalendarViewerTypeChoice(viewer=self)
        self.orientationUICommand = uicommand.CalendarViewerOrientationChoice(viewer=self)
        toolBarUICommands.insert(-2, self.periodCountUICommand)
        toolBarUICommands.insert(-2, self.typeUICommand)
        toolBarUICommands.insert(-2, self.orientationUICommand)
        toolBarUICommands.insert(-2, uicommand.CalendarViewerPreviousPeriod(viewer=self))
        toolBarUICommands.insert(-2, uicommand.CalendarViewerToday(viewer=self))
        toolBarUICommands.insert(-2, uicommand.CalendarViewerNextPeriod(viewer=self))
        self.filterChoiceUICommand = uicommand.CalendarViewerTaskFilterChoice(viewer=self)
        toolBarUICommands.insert(-2, self.filterChoiceUICommand)
        return toolBarUICommands

    def SetPeriodCount(self, count):
        self.settings.set(self.settingsSection(), 'periodcount', str(count))
        self.widget.SetPeriodCount(count)

    def SetViewType(self, type_):
        if type_ not in [wxSCHEDULER_NEXT, wxSCHEDULER_TODAY, wxSCHEDULER_PREV]:
            self.settings.set(self.settingsSection(), 'viewtype', str(type_))
        self.widget.SetViewType(type_)
        if type_ in [wxSCHEDULER_NEXT, wxSCHEDULER_TODAY, wxSCHEDULER_PREV]:
            dt = self.widget.GetDate()
            now = wx.DateTime.Today()
            if (dt.GetYear(), dt.GetMonth(), dt.GetDay()) == (now.GetYear(), now.GetMonth(), now.GetDay()):
                toSave = ''
            else:
                toSave = dt.Format()
            self.settings.set(self.settingsSection(), 'viewdate', toSave)

        # Overriding enabled() does not seem to work on controls,
        # neither does EnableTool

        self.periodCountUICommand.enable(type_ != wxSCHEDULER_MONTHLY)

    def SetViewOrientation(self, orientation):
        self.settings.set(self.settingsSection(), 'vieworientation', str(orientation))
        self.widget.SetStyle(orientation)

    def SetShowNoStartDate(self, doShow):
        self.settings.setboolean(self.settingsSection(), 'shownostart', doShow)
        self.widget.SetShowNoStartDate(doShow)

    def SetShowNoDueDate(self, doShow):
        self.settings.setboolean(self.settingsSection(), 'shownodue', doShow)
        self.widget.SetShowNoDueDate(doShow)

    def SetShowUnplanned(self, doShow):
        self.settings.setboolean(self.settingsSection(), 'showunplanned', doShow)
        self.widget.SetShowUnplanned(doShow)

    # We need to override these because BaseTaskViewer is a tree viewer, but
    # CalendarViewer is not. There is probably a better solution...

    def isAnyItemExpandable(self):
        return False

    def isAnyItemCollapsable(self):
        return False


class TaskViewer(mixin.AttachmentDropTargetMixin, 
                 mixin.SortableViewerForTasksMixin, 
                 mixin.NoteColumnMixin, mixin.AttachmentColumnMixin,
                 base.SortableViewerWithColumns, BaseTaskViewer):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'taskviewer')
        super(TaskViewer, self).__init__(*args, **kwargs)
        self.treeOrListUICommand.setChoice(self.isTreeViewer())
    
    def isTreeViewer(self):
        # We first ask our presentation what the mode is because 
        # ConfigParser.getboolean is a relatively expensive method. However,
        # when initializing, the presentation might not be created yet. So in
        # that case we get an AttributeError and we use the settings.
        try:
            return self.presentation().treeMode()
        except AttributeError:
            return self.settings.getboolean(self.settingsSection(), 'treemode')
    
    def curselectionIsInstanceOf(self, class_):
        return class_ == task.Task
    
    def createWidget(self):
        imageList = self.createImageList() # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = self.createTaskPopupMenu()
        columnPopupMenu = self.createColumnPopupMenu()
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        widget = widgets.TreeListCtrl(self, self.columns(), self.onSelect, 
            uicommand.TaskEdit(taskList=self.presentation(), viewer=self),
            uicommand.TaskDragAndDrop(taskList=self.presentation(), viewer=self),
            uicommand.EditSubject(viewer=self),
            itemPopupMenu, columnPopupMenu,
            **self.widgetCreationKeywordArguments())
        widget.AssignImageList(imageList) # pylint: disable-msg=E1101
        widget.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        widget.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        return widget
    
    def onBeginEdit(self, event):
        ''' Make sure only the non-recursive part of the subject can be
            edited inline. '''
        event.Skip()
        if not self.isTreeViewer():
            # Make sure the text control only shows the non-recursive subject
            # by temporarily changing the item text into the non-recursive
            # subject. When the editing ends, we change the item text back into
            # the recursive subject. See onEndEdit.
            treeItem = event.GetItem()
            task = self.widget.GetItemPyData(treeItem)
            self.widget.SetItemText(treeItem, task.subject())
            
    def onEndEdit(self, event):
        ''' Make sure only the non-recursive part of the subject can be
            edited inline. '''
        event.Skip()
        if not self.isTreeViewer():
            # Restore the recursive subject. Here we don't care whether the user
            # actually changed the subject. If she did, the subject will updated
            # via the regular notification mechanism.
            treeItem = event.GetItem()
            task = self.widget.GetItemPyData(treeItem)
            self.widget.SetItemText(treeItem, task.subject(recursive=True))
    
    def _createColumns(self):
        kwargs = dict(renderDescriptionCallback=lambda task: task.description(),
                      resizeCallback=self.onResizeColumn)
        columns = [widgets.Column('subject', _('Subject'), 
                task.Task.subjectChangedEventType(), 
                'task.completionDateTime', 'task.dueDateTime', 
                'task.startDateTime',
                task.Task.trackStartEventType(), task.Task.trackStopEventType(), 
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                    value='subject'),
                width=self.getColumnWidth('subject'), 
                imageIndexCallback=self.subjectImageIndex,
                renderCallback=self.renderSubject, **kwargs)] + \
            [widgets.Column('description', _('Description'), 
                task.Task.descriptionChangedEventType(), 
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                    value='description'),
                renderCallback=lambda task: task.description(), 
                width=self.getColumnWidth('description'), **kwargs)] + \
            [widgets.Column('attachments', '', 
                task.Task.attachmentsChangedEventType(), # pylint: disable-msg=E1101
                width=self.getColumnWidth('attachments'),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndexCallback=self.attachmentImageIndex,
                headerImageIndex=self.imageIndex['paperclip_icon'],
                renderCallback=lambda task: '', **kwargs)]
        if self.settings.getboolean('feature', 'notes'):
            columns.append(widgets.Column('notes', '', 
                task.Task.notesChangedEventType(), # pylint: disable-msg=E1101
                width=self.getColumnWidth('notes'),
                alignment=wx.LIST_FORMAT_LEFT,
                imageIndexCallback=self.noteImageIndex,
                headerImageIndex=self.imageIndex['note_icon'],
                renderCallback=lambda task: '', **kwargs))
        columns.extend(
            [widgets.Column('categories', _('Categories'), 
                task.Task.categoryAddedEventType(), 
                task.Task.categoryRemovedEventType(), 
                task.Task.categorySubjectChangedEventType(),
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                                           value='categories'),
                width=self.getColumnWidth('categories'),
                renderCallback=self.renderCategories, **kwargs),
             widgets.Column('prerequisites', _('Prerequisites'),
                'task.prerequisites', 'task.prerequisite.subject',
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                                           value='prerequisites'),
                renderCallback=self.renderPrerequisites,
                width=self.getColumnWidth('prerequisites'), **kwargs),
             widgets.Column('dependencies', _('Dependencies'),
                'task.dependencies', 'task.dependency.subject',
                task.Task.expansionChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                                           value='dependencies'),
                renderCallback=self.renderDependencies,
                width=self.getColumnWidth('dependencies'), **kwargs)])
        
        effortOn = self.settings.getboolean('feature', 'effort')
        dependsOnEffortFeature = ['budget',  'timeSpent', 'budgetLeft',
                                  'hourlyFee', 'fixedFee', 'revenue']
        for name, columnHeader, eventTypes in [
            ('startDateTime', _('Start date'), []),
            ('dueDateTime', _('Due date'), [task.Task.expansionChangedEventType()]),
            ('completionDateTime', _('Completion date'), [task.Task.expansionChangedEventType()]),
            ('percentageComplete', _('% complete'), [task.Task.expansionChangedEventType(), 'task.percentageComplete']),
            ('timeLeft', _('Time left'), [task.Task.expansionChangedEventType(), 'task.timeLeft']),
            ('recurrence', _('Recurrence'), [task.Task.expansionChangedEventType(), 'task.recurrence']),
            ('budget', _('Budget'), [task.Task.expansionChangedEventType(), 'task.budget']),            
            ('timeSpent', _('Time spent'), [task.Task.expansionChangedEventType(), 'task.timeSpent']),
            ('budgetLeft', _('Budget left'), [task.Task.expansionChangedEventType(), 'task.budgetLeft']),            
            ('priority', _('Priority'), [task.Task.expansionChangedEventType(), 'task.priority']),
            ('hourlyFee', _('Hourly fee'), [task.Task.hourlyFeeChangedEventType()]),
            ('fixedFee', _('Fixed fee'), [task.Task.expansionChangedEventType(), 'task.fixedFee']),            
            ('revenue', _('Revenue'), [task.Task.expansionChangedEventType(), 'task.revenue']),
            ('reminder', _('Reminder'), [task.Task.expansionChangedEventType(), 'task.reminder'])]:
            if (name in dependsOnEffortFeature and effortOn) or name not in dependsOnEffortFeature:
                renderCallback = getattr(self, 'render%s'%(name[0].capitalize()+name[1:]))
                columns.append(widgets.Column(name, columnHeader,  
                    sortCallback=uicommand.ViewerSortByCommand(viewer=self, value=name),
                    renderCallback=renderCallback, width=self.getColumnWidth(name),
                    alignment=wx.LIST_FORMAT_RIGHT, *eventTypes, **kwargs))
        return columns
    
    def createColumnUICommands(self):
        commands = [
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            (_('&Dates'),
             uicommand.ViewColumns(menuText=_('&All date columns'),
                helpText=_('Show/hide all date-related columns'),
                setting=['startDateTime', 'dueDateTime', 'timeLeft', 
                         'completionDateTime', 'recurrence'],
                viewer=self),
             None,
             uicommand.ViewColumn(menuText=_('&Start date'),
                 helpText=_('Show/hide start date column'),
                 setting='startDateTime', viewer=self),
             uicommand.ViewColumn(menuText=_('&Due date'),
                 helpText=_('Show/hide due date column'),
                 setting='dueDateTime', viewer=self),
             uicommand.ViewColumn(menuText=_('&Completion date'),
                 helpText=_('Show/hide completion date column'),
                 setting='completionDateTime', viewer=self),
             uicommand.ViewColumn(menuText=_('&Time left'),
                 helpText=_('Show/hide time left column'),
                 setting='timeLeft', viewer=self),
             uicommand.ViewColumn(menuText=_('&Recurrence'),
                 helpText=_('Show/hide recurrence column'),
                 setting='recurrence', viewer=self))]
        if self.settings.getboolean('feature', 'effort'):
            commands.extend([
                (_('&Budget'),
                 uicommand.ViewColumns(menuText=_('&All budget columns'),
                     helpText=_('Show/hide all budget-related columns'),
                     setting=['budget', 'timeSpent', 'budgetLeft'],
                     viewer=self),
                 None,
                 uicommand.ViewColumn(menuText=_('&Budget'),
                     helpText=_('Show/hide budget column'),
                     setting='budget', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Time spent'),
                     helpText=_('Show/hide time spent column'),
                     setting='timeSpent', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Budget left'),
                     helpText=_('Show/hide budget left column'),
                     setting='budgetLeft', viewer=self),
                ),
                (_('&Financial'),
                 uicommand.ViewColumns(menuText=_('&All financial columns'),
                     helpText=_('Show/hide all finance-related columns'),
                     setting=['hourlyFee', 'fixedFee', 'revenue'],
                     viewer=self),
                 None,
                 uicommand.ViewColumn(menuText=_('&Hourly fee'),
                     helpText=_('Show/hide hourly fee column'),
                     setting='hourlyFee', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Fixed fee'),
                     helpText=_('Show/hide fixed fee column'),
                     setting='fixedFee', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Revenue'),
                     helpText=_('Show/hide revenue column'),
                     setting='revenue', viewer=self))])
        commands.extend([
            uicommand.ViewColumn(menuText=_('&Description'),
                helpText=_('Show/hide description column'),
                setting='description', viewer=self),
            uicommand.ViewColumn(menuText=_('&Prerequisites'),
                 helpText=_('Show/hide prerequisites column'),
                 setting='prerequisites', viewer=self),
            uicommand.ViewColumn(menuText=_('&Dependencies'),
                 helpText=_('Show/hide dependencies column'),
                 setting='dependencies', viewer=self),
             uicommand.ViewColumn(menuText=_('&Percentage complete'),
                 helpText=_('Show/hide percentage complete column'),
                 setting='percentageComplete', viewer=self),
            uicommand.ViewColumn(menuText=_('&Attachments'),
                helpText=_('Show/hide attachment column'),
                setting='attachments', viewer=self)])
        if self.settings.getboolean('feature', 'notes'):
            commands.append(
                uicommand.ViewColumn(menuText=_('&Notes'),
                    helpText=_('Show/hide notes column'),
                    setting='notes', viewer=self))
        commands.extend([
            uicommand.ViewColumn(menuText=_('&Categories'),
                helpText=_('Show/hide categories column'),
                setting='categories', viewer=self),
            uicommand.ViewColumn(menuText=_('&Priority'),
                helpText=_('Show/hide priority column'),
                setting='priority', viewer=self),
            uicommand.ViewColumn(menuText=_('&Reminder'),
                helpText=_('Show/hide reminder column'),
                setting='reminder', viewer=self)])
        return commands

    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(TaskViewer, self).getToolBarUICommands() 
        toolBarUICommands.insert(-2, None) # Separator
        self.treeOrListUICommand = \
            uicommand.TaskViewerTreeOrListChoice(viewer=self)
        toolBarUICommands.insert(-2, self.treeOrListUICommand)
        return toolBarUICommands

    def createColumnPopupMenu(self):
        return menu.ColumnPopupMenu(self)
        
    def getImageIndices(self, task):
        bitmap = task.icon(recursive=True)
        bitmap_selected = task.selectedIcon(recursive=True) or bitmap 
        return self.imageIndex[bitmap], self.imageIndex[bitmap_selected]

    def subjectImageIndex(self, task, which):
        normalImageIndex, expandedImageIndex = self.getImageIndices(task) 
        expanded = which in [wx.TreeItemIcon_Expanded, 
                             wx.TreeItemIcon_SelectedExpanded]
        return expandedImageIndex if expanded else normalImageIndex
                    
    def setSortByTaskStatusFirst(self, *args, **kwargs): # pylint: disable-msg=W0221
        super(TaskViewer, self).setSortByTaskStatusFirst(*args, **kwargs)
        self.showSortOrder()
        
    def getSortOrderImage(self):
        sortOrderImage = super(TaskViewer, self).getSortOrderImage()
        if self.isSortByTaskStatusFirst():
            sortOrderImage = sortOrderImage.rstrip('icon') + 'with_status_icon'
        return sortOrderImage

    def setSearchFilter(self, searchString, *args, **kwargs): # pylint: disable-msg=W0221
        super(TaskViewer, self).setSearchFilter(searchString, *args, **kwargs)
        if searchString:
            self.expandAll()           

    def showTree(self, treeMode):
        self.settings.set(self.settingsSection(), 'treemode', str(treeMode))
        self.presentation().setTreeMode(treeMode)
        
    def renderSubject(self, task):
        return task.subject(recursive=not self.isTreeViewer())
    
    @staticmethod
    def renderStartDateTime(task):
        # The rendering of the start date time doesn't depend on whether the
        # task is collapsed since the start date time is a parent is always <=
        # start date times of all children. 
        return render.dateTime(task.startDateTime())
    
    def renderDueDateTime(self, task):
        return self.renderedValue(task, task.dueDateTime, render.dateTime)

    def renderCompletionDateTime(self, task):
        return self.renderedValue(task, task.completionDateTime, render.dateTime)

    def renderRecurrence(self, task):
        return self.renderedValue(task, task.recurrence, render.recurrence)
    
    def renderPrerequisites(self, task):
        return self.renderSubjectsOfRelatedItems(task, task.prerequisites)
    
    def renderDependencies(self, task):
        return self.renderSubjectsOfRelatedItems(task, task.dependencies)
    
    def renderTimeLeft(self, task):
        return self.renderedValue(task, task.timeLeft, render.timeLeft, task.completed())
        
    def renderTimeSpent(self, task):
        return self.renderedValue(task, task.timeSpent, render.timeSpent)

    def renderBudget(self, task):
        return self.renderedValue(task, task.budget, render.budget)

    def renderBudgetLeft(self, task):
        return self.renderedValue(task, task.budgetLeft, render.budget)

    def renderRevenue(self, task):
        return self.renderedValue(task, task.revenue, render.monetaryAmount)
    
    def renderHourlyFee(self, task):
        return render.monetaryAmount(task.hourlyFee()) # hourlyFee has no recursive value
    
    def renderFixedFee(self, task):
        return self.renderedValue(task, task.fixedFee, render.monetaryAmount)

    def renderPercentageComplete(self, task):
        return self.renderedValue(task, task.percentageComplete, render.percentage)

    def renderPriority(self, task):
        return self.renderedValue(task, task.priority, render.priority)
    
    def renderReminder(self, task):
        return self.renderedValue(task, task.reminder, render.dateTime)
    
    def renderedValue(self, item, getValue, renderValue, *extraRenderArgs):
        value = getValue(recursive=False)
        template = '%s'
        if self.isItemCollapsed(item):
            recursiveValue = getValue(recursive=True)
            if value != recursiveValue:
                value = recursiveValue
                template = '(%s)'
        return template%renderValue(value, *extraRenderArgs)
                                
    def onEverySecond(self, event):
        # Only update when a column is visible that changes every second 
        if any([self.isVisibleColumnByName(column) for column in 'timeSpent', 
               'budgetLeft', 'revenue']):
            super(TaskViewer, self).onEverySecond(event)

    def getRootItems(self):
        ''' If the viewer is in tree mode, return the real root items. If the
            viewer is in list mode, return all items. '''
        return super(TaskViewer, self).getRootItems() if \
            self.isTreeViewer() else self.presentation()
    
    def getItemParent(self, item):
        return super(TaskViewer, self).getItemParent(item) if \
            self.isTreeViewer() else None

    def children(self, item=None):
        return super(TaskViewer, self).children(item) if \
            (self.isTreeViewer() or item is None) else []


class CheckableTaskViewer(TaskViewer):
    def createWidget(self):
        imageList = self.createImageList() # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = self.createTaskPopupMenu()
        columnPopupMenu = self.createColumnPopupMenu()
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        widget = widgets.CheckTreeCtrl(self, self.columns(), self.onSelect,
            self.onCheck, 
            uicommand.TaskEdit(taskList=self.presentation(), viewer=self),
            uicommand.TaskDragAndDrop(taskList=self.presentation(), viewer=self),
            uicommand.EditSubject(viewer=self),
            itemPopupMenu, columnPopupMenu,
            **self.widgetCreationKeywordArguments())
        widget.AssignImageList(imageList) # pylint: disable-msg=E1101
        return widget    
    
    def onCheck(self, *args, **kwargs):
        pass
    
    def getIsItemChecked(self, task):
        return False
    
    def getItemParentHasExclusiveChildren(self, task):
        return False
