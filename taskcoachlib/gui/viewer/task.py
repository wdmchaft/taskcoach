# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2010 Jérôme Laheurte <fraca7@free.fr>
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
    wxSCHEDULER_TODAY, wxSCHEDULER_HORIZONTAL, wxSCHEDULER_TODAY, wxFancyDrawer
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
        tasks = super(BaseTaskViewer, self).createFilter(taskList)
        return domain.base.DeletedFilter(tasks)

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
            
    def editorClass(self):
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
             uicommand.TaskNewFromTemplateButton(taskList=self.presentation(),
                                                 settings=self.settings,
                                                 bitmap='newtmpl'),
             uicommand.TaskNewSubTask(taskList=self.presentation(),
                                      viewer=self),
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
        colorSettings.append('behavior.duesoondays')
        for colorSetting in colorSettings:
            patterns.Publisher().registerObserver(self.onColorSettingChange, 
                eventType=colorSetting)
        for eventType in (task.Task.foregroundColorChangedEventType(),
                          task.Task.backgroundColorChangedEventType(),
                          task.Task.fontChangedEventType(),
                          task.Task.iconChangedEventType(),
                          task.Task.selectedIconChangedEventType()):
            patterns.Publisher().registerObserver(self.onAttributeChanged,
                                                  eventType=eventType)
        patterns.Publisher().registerObserver(self.atMidnight,
            eventType='clock.midnight')
        patterns.Publisher().registerObserver(self.onWake,
            eventType='powermgt.on')

    def atMidnight(self, event): # pylint: disable-msg=W0613
        self.refresh()

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
            result.append(('note_icon', [note.subject() for note in task.notes()]))
        if task.attachments():
            result.append(('paperclip_icon',
                [unicode(attachment) for attachment in task.attachments()]))
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
        children.sort(key=lambda task: task.startDate())
        return children
    
    def parallel_children(self, recursive=False):
        return self.children(recursive)

    def sequential_children(self):
        return []

    def startDate(self, recursive=False):
        startDates = [item.startDate(recursive=True) for item in self.parallel_children()]
        startDates = [aDate for aDate in startDates if aDate != date.Date()]
        if not startDates:
            startDates.append(date.Today())
        return min(startDates)
    
    def dueDate(self, recursive=False):
        dueDates = [item.dueDate(recursive=True) for item in self.parallel_children()]
        dueDates = [aDate for aDate in dueDates if aDate != date.Date()]
        if not dueDates:
            dueDates.append(date.Tomorrow())    
        return max(dueDates)
    

class TimelineViewer(BaseTaskViewer):
    defaultTitle = _('Timeline')
    defaultBitmap = 'timelineviewer'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'timelineviewer')
        super(TimelineViewer, self).__init__(*args, **kwargs)
        for eventType in (task.Task.subjectChangedEventType(), 'task.startDate',
            'task.dueDate', 'task.completionDate'):
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
            start = item.startDate(recursive=recursive)
            if start == date.Date():
                return None
        except AttributeError:
            start = item.getStart()
        return start.toordinal()

    def stop(self, item, recursive=False):
        try:
            if item.completed():
                stop = item.completionDate(recursive=recursive)
            else:
                stop = item.dueDate(recursive=recursive)
            if stop == date.Date():
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
            children.sort(key=lambda task: task.startDate())
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
        return date.Today().toordinal()
    
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
        for eventType in (task.Task.subjectChangedEventType(), 'task.dueDate',
            'task.startDate', 'task.completionDate'):
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
                     BaseTaskViewer):
    defaultTitle = _('Calendar')
    defaultBitmap = 'calendar_icon'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'calendarviewer')
        super(CalendarViewer, self).__init__(*args, **kwargs)

        self.widget.SetViewType(self.settings.getint(self.settingsSection(), 'viewtype'))
        self.widget.SetStyle(wxSCHEDULER_HORIZONTAL)

        self.typeUICommand.setChoice(self.settings.getint(self.settingsSection(), 'viewtype'))
        self.filterChoiceUICommand.setChoice((self.settings.getboolean(self.settingsSection(), 'shownostart'),
                                              self.settings.getboolean(self.settingsSection(), 'shownodue')))

        start = self.settings.get(self.settingsSection(), 'viewdate')
        if start:
            dt = wx.DateTime.Now()
            dt.ParseDateTime(start)
            self.widget.SetDate(dt)

        self.widget.SetWorkHours(self.settings.getint('view', 'efforthourstart'),
                                 self.settings.getint('view', 'efforthourend'))

        self.widget.SetShowNoStartDate(self.settings.getboolean(self.settingsSection(), 'shownostart'))
        self.widget.SetShowNoDueDate(self.settings.getboolean(self.settingsSection(), 'shownodue'))

        for eventType in ('view.efforthourstart', 'view.efforthourend'):
            self.registerObserver(self.onWorkingHourChanged, eventType)

        for eventType in (task.Task.subjectChangedEventType(), 'task.startDate',
                          'task.dueDate', 'task.completionDate',
                          task.Task.attachmentsChangedEventType(),
                          task.Task.notesChangedEventType()):
            self.registerObserver(self.onAttributeChanged, eventType)

    def onEverySecond(self, event): # pylint: disable-msg=W0221,W0613
        pass # Too expensive

    def atMidnight(self, event): # pylint: disable-msg=W0613
        if not self.settings.get(self.settingsSection(), 'viewdate'):
            # User has selected the "current" date/time; it may have
            # changed now
            self.SetViewType(wxSCHEDULER_TODAY)

        super(CalendarViewer, self).atMidnight(event)

    def onWake(self, event):
        self.atMidnight(event)

    def onWorkingHourChanged(self, event):
        self.widget.SetWorkHours(self.settings.getint('view', 'efforthourstart'),
                                 self.settings.getint('view', 'efforthourend'))

    def createWidget(self):
        itemPopupMenu = self.createTaskPopupMenu()
        self._popupMenus.append(itemPopupMenu)
        widget = widgets.Calendar(self, self.presentation(), self.iconName, self.onSelect,
                                  self.onEdit, self.onCreate, itemPopupMenu,
                                  **self.widgetCreationKeywordArguments())

        if self.settings.getboolean('calendarviewer', 'gradient'):
            # If called directly, we crash with a Cairo assert failing...
            wx.CallAfter(widget.SetDrawer, wxFancyDrawer)

        return widget

    def onEdit(self, item):
        edit = uicommand.TaskEdit(taskList=self.presentation(), viewer=self)
        edit(item)

    def onCreate(self, date):
        create = uicommand.TaskNew(taskList=self.presentation(), settings=self.settings,
                                   taskKeywords=dict(startDate=date, dueDate=date))
        create(None)

    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(CalendarViewer, self).getToolBarUICommands()
        toolBarUICommands.insert(-2, None) # Separator
        self.typeUICommand = uicommand.CalendarViewerTypeChoice(viewer=self)
        toolBarUICommands.insert(-2, self.typeUICommand)
        toolBarUICommands.insert(-2, uicommand.CalendarViewerPreviousPeriod(viewer=self))
        toolBarUICommands.insert(-2, uicommand.CalendarViewerToday(viewer=self))
        toolBarUICommands.insert(-2, uicommand.CalendarViewerNextPeriod(viewer=self))
        self.filterChoiceUICommand = uicommand.CalendarViewerTaskFilterChoice(viewer=self)
        toolBarUICommands.insert(-2, self.filterChoiceUICommand)
        return toolBarUICommands

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

    def SetShowNoStartDate(self, doShow):
        self.settings.setboolean(self.settingsSection(), 'shownostart', doShow)
        self.widget.SetShowNoStartDate(doShow)

    def SetShowNoDueDate(self, doShow):
        self.settings.setboolean(self.settingsSection(), 'shownodue', doShow)
        self.widget.SetShowNoDueDate(doShow)

    # We need to override these because BaseTaskViewer is a tree viewer, but
    # CalendarViewer is not. There is probably a better solution...

    def isSelectionExpandable(self):
        return False

    def isSelectionCollapsable(self):
        return False

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
        return widget    
    
    def _createColumns(self):
        kwargs = dict(renderDescriptionCallback=lambda task: task.description(),
                      resizeCallback=self.onResizeColumn)
        columns = [widgets.Column('subject', _('Subject'), 
                task.Task.subjectChangedEventType(), 
                'task.completionDate', 'task.dueDate', 'task.startDate',
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
                renderCallback=lambda task: render.multilineText(task.description()), 
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
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                                           value='categories'),
                width=self.getColumnWidth('categories'),
                renderCallback=self.renderCategory, **kwargs)] + \
            [widgets.Column('totalCategories', _('Overall categories'),
                task.Task.totalCategoryAddedEventType(),
                task.Task.totalCategoryRemovedEventType(),
                task.Task.totalCategorySubjectChangedEventType(),
                sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                                           value='totalCategories'),
                renderCallback=lambda task: self.renderCategory(task, recursive=True),
                width=self.getColumnWidth('totalCategories'), **kwargs)])
        effortOn = self.settings.getboolean('feature', 'effort')
        dependsOnEffortFeature = ['budget', 'totalBudget', 
                                  'timeSpent', 'totalTimeSpent', 
                                  'budgetLeft', 'totalBudgetLeft',
                                  'hourlyFee', 'fixedFee', 'totalFixedFee',
                                  'revenue', 'totalRevenue']
        for name, columnHeader, renderCallback, eventType in [
            ('startDate', _('Start date'), lambda task: render.date(task.startDate()), None),
            ('dueDate', _('Due date'), lambda task: render.date(task.dueDate()), None),
            ('completionDate', _('Completion date'), lambda task: render.date(task.completionDate()), None),
            ('percentageComplete', _('% complete'), lambda task: render.percentage(task.percentageComplete()), None),
            ('totalPercentageComplete', _('Overall % complete'), lambda task: render.percentage(task.percentageComplete(recursive=True)), None),
            ('timeLeft', _('Days left'), lambda task: render.daysLeft(task.timeLeft(), task.completed()), None),
            ('recurrence', _('Recurrence'), lambda task: render.recurrence(task.recurrence()), None),
            ('budget', _('Budget'), lambda task: render.budget(task.budget()), None),
            ('totalBudget', _('Total budget'), lambda task: render.budget(task.budget(recursive=True)), None),
            ('timeSpent', _('Time spent'), lambda task: render.timeSpent(task.timeSpent()), None),
            ('totalTimeSpent', _('Total time spent'), lambda task: render.timeSpent(task.timeSpent(recursive=True)), None),
            ('budgetLeft', _('Budget left'), lambda task: render.budget(task.budgetLeft()), None),
            ('totalBudgetLeft', _('Total budget left'), lambda task: render.budget(task.budgetLeft(recursive=True)), None),
            ('priority', _('Priority'), lambda task: render.priority(task.priority()), None),
            ('totalPriority', _('Overall priority'), lambda task: render.priority(task.priority(recursive=True)), None),
            ('hourlyFee', _('Hourly fee'), lambda task: render.monetaryAmount(task.hourlyFee()), task.Task.hourlyFeeChangedEventType()),
            ('fixedFee', _('Fixed fee'), lambda task: render.monetaryAmount(task.fixedFee()), None),
            ('totalFixedFee', _('Total fixed fee'), lambda task: render.monetaryAmount(task.fixedFee(recursive=True)), None),
            ('revenue', _('Revenue'), lambda task: render.monetaryAmount(task.revenue()), None),
            ('totalRevenue', _('Total revenue'), lambda task: render.monetaryAmount(task.revenue(recursive=True)), None),
            ('reminder', _('Reminder'), lambda task: render.dateTime(task.reminder()), None)]:
            eventType = eventType or 'task.'+name
            if (name in dependsOnEffortFeature and effortOn) or name not in dependsOnEffortFeature:
                columns.append(widgets.Column(name, columnHeader, eventType, 
                    sortCallback=uicommand.ViewerSortByCommand(viewer=self, value=name),
                    renderCallback=renderCallback, width=self.getColumnWidth(name),
                    alignment=wx.LIST_FORMAT_RIGHT, **kwargs))
        return columns
    
    def createColumnUICommands(self):
        commands = [
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            (_('&Dates'),
             uicommand.ViewColumns(menuText=_('All date columns'),
                helpText=_('Show/hide all date-related columns'),
                setting=['startDate', 'dueDate', 'timeLeft', 'completionDate',
                         'recurrence'],
                viewer=self),
             None,
             uicommand.ViewColumn(menuText=_('&Start date'),
                 helpText=_('Show/hide start date column'),
                 setting='startDate', viewer=self),
             uicommand.ViewColumn(menuText=_('&Due date'),
                 helpText=_('Show/hide due date column'),
                 setting='dueDate', viewer=self),
             uicommand.ViewColumn(menuText=_('Co&mpletion date'),
                 helpText=_('Show/hide completion date column'),
                 setting='completionDate', viewer=self),
             uicommand.ViewColumn(menuText=_('&Percentage complete'),
                 helpText=_('Show/hide percentage complete column'),
                 setting='percentageComplete', viewer=self),
             uicommand.ViewColumn(menuText=_('&Overall percentage complete'),
                 helpText=_('Show/hide overall percentage complete column'),
                 setting='totalPercentageComplete', viewer=self),
             uicommand.ViewColumn(menuText=_('D&ays left'),
                 helpText=_('Show/hide days left column'),
                 setting='timeLeft', viewer=self),
             uicommand.ViewColumn(menuText=_('&Recurrence'),
                 helpText=_('Show/hide recurrence column'),
                 setting='recurrence', viewer=self))]
        if self.settings.getboolean('feature', 'effort'):
            commands.extend([
                (_('&Budget'),
                 uicommand.ViewColumns(menuText=_('All budget columns'),
                     helpText=_('Show/hide all budget-related columns'),
                     setting=['budget', 'totalBudget', 'timeSpent',
                              'totalTimeSpent', 'budgetLeft','totalBudgetLeft'],
                     viewer=self),
                 None,
                 uicommand.ViewColumn(menuText=_('&Budget'),
                     helpText=_('Show/hide budget column'),
                     setting='budget', viewer=self),
                 uicommand.ViewColumn(menuText=_('Total b&udget'),
                     helpText=_('Show/hide total budget column (total budget includes budget for subtasks)'),
                     setting='totalBudget', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Time spent'),
                     helpText=_('Show/hide time spent column'),
                     setting='timeSpent', viewer=self),
                 uicommand.ViewColumn(menuText=_('T&otal time spent'),
                     helpText=_('Show/hide total time spent column (total time includes time spent on subtasks)'),
                     setting='totalTimeSpent', viewer=self),
                 uicommand.ViewColumn(menuText=_('Budget &left'),
                     helpText=_('Show/hide budget left column'),
                     setting='budgetLeft', viewer=self),
                 uicommand.ViewColumn(menuText=_('Total budget l&eft'),
                     helpText=_('Show/hide total budget left column (total budget left includes budget left for subtasks)'),
                     setting='totalBudgetLeft', viewer=self)
                ),
                (_('&Financial'),
                 uicommand.ViewColumns(menuText=_('All financial columns'),
                     helpText=_('Show/hide all finance-related columns'),
                     setting=['hourlyFee', 'fixedFee', 'totalFixedFee',
                              'revenue', 'totalRevenue'],
                     viewer=self),
                 None,
                 uicommand.ViewColumn(menuText=_('&Hourly fee'),
                     helpText=_('Show/hide hourly fee column'),
                     setting='hourlyFee', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Fixed fee'),
                     helpText=_('Show/hide fixed fee column'),
                     setting='fixedFee', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Total fixed fee'),
                     helpText=_('Show/hide total fixed fee column'),
                     setting='totalFixedFee', viewer=self),
                 uicommand.ViewColumn(menuText=_('&Revenue'),
                     helpText=_('Show/hide revenue column'),
                     setting='revenue', viewer=self),
                 uicommand.ViewColumn(menuText=_('T&otal revenue'),
                     helpText=_('Show/hide total revenue column'),
                     setting='totalRevenue', viewer=self))])
        commands.extend([
            uicommand.ViewColumn(menuText=_('&Description'),
                helpText=_('Show/hide description column'),
                setting='description', viewer=self),
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
            uicommand.ViewColumn(menuText=_('Overall categories'),
                helpText=_('Show/hide overall categories column'),
                setting='totalCategories', viewer=self),
            uicommand.ViewColumn(menuText=_('&Priority'),
                helpText=_('Show/hide priority column'),
                setting='priority', viewer=self),
            uicommand.ViewColumn(menuText=_('O&verall priority'),
                helpText=_('Show/hide overall priority column (overall priority is the maximum priority of a task and all its subtasks'),
                setting='totalPriority', viewer=self),
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
    
    def onEverySecond(self, event):
        # Only update when a column is visible that changes every second 
        if any([self.isVisibleColumnByName(column) for column in 'timeSpent', 
               'totalTimeSpent', 'budgetLeft', 'totalBudgetLeft',
               'revenue', 'totalRevenue']):
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
