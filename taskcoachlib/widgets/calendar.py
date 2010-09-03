'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2010 Frank Niessink <frank@niessink.com>

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

import wx, operator
from taskcoachlib.thirdparty.calendar import wxScheduler, wxSchedule, \
    EVT_SCHEDULE_ACTIVATED, EVT_SCHEDULE_RIGHT_CLICK, \
    EVT_SCHEDULE_DCLICK
from taskcoachlib.domain import date
from taskcoachlib.widgets import draganddrop
import tooltip


class _CalendarContent(tooltip.ToolTipMixin, wxScheduler):
    def __init__(self, parent, taskList, iconProvider, onSelect, onEdit,
                 onCreate, popupMenu, *args, **kwargs):
        self.getItemTooltipData = parent.getItemTooltipData

        self.__onDropURLCallback = kwargs.pop('onDropURL', None)
        self.__onDropFilesCallback = kwargs.pop('onDropFiles', None)
        self.__onDropMailCallback = kwargs.pop('onDropMail', None)

        self.dropTarget = draganddrop.DropTarget(self.OnDropURL,
                                                 self.OnDropFiles,
                                                 self.OnDropMail)

        super(_CalendarContent, self).__init__(parent, wx.ID_ANY, *args, **kwargs)

        self.SetDropTarget(self.dropTarget)

        self.selectCommand = onSelect
        self.iconProvider = iconProvider
        self.editCommand = onEdit
        self.createCommand = onCreate
        self.popupMenu = popupMenu

        self.__tip = tooltip.SimpleToolTip(self)
        self.__selection = []

        self.__showNoStartDate = False
        self.__showNoDueDate = False
        self.__showUnplanned = False

        self.SetShowWorkHour(False)
        self.SetResizable(True)

        self.taskList = taskList
        self.RefreshAllItems(0)

        EVT_SCHEDULE_ACTIVATED(self, self.OnActivation)
        EVT_SCHEDULE_RIGHT_CLICK(self, self.OnPopup)
        EVT_SCHEDULE_DCLICK(self, self.OnEdit)

    def _handleDrop(self, x, y, object, cb):
        if cb is not None:
            item = self._findSchedule(wx.Point(x, y))

            if item is not  None:
                if isinstance(item, TaskSchedule):
                    cb(item.task, object)
                else:
                    datetime = date.DateTime(item.GetYear(), item.GetMonth() + 1, item.GetDay())
                    cb(None, object, startDateTime=datetime, dueDateTime=datetime.endOfDay())

    def OnDropURL(self, x, y, url):
        self._handleDrop(x, y, url, self.__onDropURLCallback)

    def OnDropFiles(self, x, y, filenames):
        self._handleDrop(x, y, filenames, self.__onDropFilesCallback)

    def OnDropMail(self, x, y, mail):
        self._handleDrop(x, y, mail, self.__onDropMailCallback)

    def SetShowNoStartDate(self, doShow):
        self.__showNoStartDate = doShow
        self.RefreshAllItems(0)

    def SetShowNoDueDate(self, doShow):
        self.__showNoDueDate = doShow
        self.RefreshAllItems(0)

    def SetShowUnplanned(self, doShow):
        self.__showUnplanned = doShow
        self.RefreshAllItems(0)

    def OnActivation(self, event):
        self.SetFocus()

        if self.__selection:
            self.taskMap[self.__selection[0].id()].SetSelected(False)

        if event.schedule is None:
            self.__selection = []
        else:
            self.__selection = [event.schedule.task]
            event.schedule.SetSelected(True)

        wx.CallAfter(self.selectCommand)
        event.Skip()

    def OnPopup(self, event):
        self.OnActivation(event)
        wx.CallAfter(self.PopupMenu, self.popupMenu)

    def OnEdit(self, event):
        if event.schedule is None:
            if event.date is not None:
                self.createCommand(date.DateTime(event.date.GetYear(),
                                                 event.date.GetMonth() + 1,
                                                 event.date.GetDay(),
                                                 event.date.GetHour(),
                                                 event.date.GetMinute(),
                                                 event.date.GetSecond()))
        else:
            self.editCommand(event.schedule.task)

    def RefreshAllItems(self, count):
        x, y = self.GetViewStart()
        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        self.DeleteAll()

        schedules = []
        self.taskMap = {}

        for task in self.taskList:
            if not task.isDeleted():
                if task.startDateTime() == date.DateTime() and not self.__showNoStartDate:
                    continue

                if task.dueDateTime() == date.DateTime() and not self.__showNoDueDate:
                    continue

                if not self.__showUnplanned:
                    if task.startDateTime() == date.DateTime() and task.dueDateTime() == date.DateTime():
                        continue

                schedule = TaskSchedule(task, self.iconProvider)
                schedules.append(schedule)
                self.taskMap[task.id()] = schedule

                if task.id() == selectionId:
                    self.__selection = [task]
                    schedule.SetSelected(True)

        self.Add(schedules)
        wx.CallAfter(self.selectCommand)
        self.Scroll(x, y)

    def RefreshItems(self, *args):
        selectionId = None
        if self.__selection:
            selectionId = self.__selection[0].id()
        self.__selection = []

        for task in args:
            doShow = True

            if task.isDeleted():
                doShow = False

            if task.startDateTime() == date.DateTime() and task.dueDateTime() == date.DateTime():
                doShow = False

            if task.startDateTime() == date.DateTime() and not self.__showNoStartDate:
                doShow = False

            if task.dueDateTime() == date.DateTime() and not self.__showNoDueDate:
                doShow = False

            if doShow:
                if self.taskMap.has_key(task.id()):
                    schedule = self.taskMap[task.id()]
                    schedule.update()
                else:
                    schedule = TaskSchedule(task, self.iconProvider)
                    self.taskMap[task.id()] = schedule
                    self.Add([schedule])

                if task.id() == selectionId:
                    self.__selection = [task]
                    schedule.SetSelected(True)
            else:
                if self.taskMap.has_key(task.id()):
                    self.Delete(self.taskMap[task.id()])
                    del self.taskMap[task.id()]
                    if self.__selection and self.__selection[0].id() == task.id():
                        self.__selection = []
                        wx.CallAfter(self.selectCommand)

    def GetItemCount(self):
        return len(self.GetSchedules())
        
    def OnBeforeShowToolTip(self, x, y):
        originX, originY = self.GetViewStart()
        unitX, unitY = self.GetScrollPixelsPerUnit()

        schedule = self._findSchedule(wx.Point(x + originX * unitX, y + originY * unitY))

        if schedule and isinstance(schedule, TaskSchedule):
            item = schedule.task

            tooltipData = self.getItemTooltipData(item)
            doShow = reduce(operator.__or__,
                            map(bool, [data[1] for data in tooltipData]),
                            False)
            if doShow:
                self.__tip.SetData(tooltipData)
                return self.__tip
            else:
                return None

    def GetMainWindow(self):
        return self
    
    MainWindow = property(GetMainWindow)

    def curselection(self):
        return self.__selection


class Calendar(wx.Panel):
    def __init__(self, parent, taskList, iconProvider, onSelect, onEdit,
                 onCreate, popupMenu, *args, **kwargs):
        self.getItemTooltipData = parent.getItemTooltipData

        super(Calendar, self).__init__(parent)

        self._headers = wx.Panel(self)
        self._content = _CalendarContent(self, taskList, iconProvider, onSelect, onEdit,
                                         onCreate, popupMenu, *args, **kwargs)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._headers, 0, wx.EXPAND)
        sizer.Add(self._content, 1, wx.EXPAND)
        self.SetSizer(sizer)

        # Must wx.CallAfter because SetDrawerClass is called this way.
        wx.CallAfter(self._content.SetHeaderPanel, self._headers)

    def SetShowNoStartDate(self, doShow):
        self._content.SetShowNoStartDate(doShow)

    def SetShowNoDueDate(self, doShow):
        self._content.SetShowNoDueDate(doShow)

    def SetShowUnplanned(self, doShow):
        self._content.SetShowUnplanned(doShow)

    def RefreshAllItems(self, count):
        self._content.RefreshAllItems(count)

    def RefreshItems(self, *args):
        self._content.RefreshItems(*args)

    def GetItemCount(self):
        return self._content.GetItemCount()

    def curselection(self):
        return self._content.curselection()

    def isAnyItemCollapsable(self):
        return False

    def __getattr__(self, name):
        return getattr(self._content, name)


class TaskSchedule(wxSchedule):
    def __init__(self, task, iconProvider):
        super(TaskSchedule, self).__init__()

        self.__selected = False

        self.clientdata = task
        self.iconProvider = iconProvider
        self.update()

    def SetSelected(self, selected):
        self.__selected = selected
        if selected:
            self.color = wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            self.color = wx.Color(*(self.task.backgroundColor() or (255, 255, 255)))

    @property
    def task(self):
        return self.clientdata

    def update(self):
        self.Freeze()
        try:
            self.description = self.task.subject()

            started = self.task.startDateTime()
            if started == date.DateTime():
                self.start = wx.DateTimeFromDMY(1, 1, 0) # Huh
            else:
                self.start = wx.DateTimeFromDMY(started.day, started.month - 1, 
                                                started.year, started.hour, 
                                                started.minute, started.second)

            ended = self.task.dueDateTime()
            if ended == date.DateTime():
                self.end = wx.DateTimeFromDMY(1, 1, 9999)
            else:
                self.end = wx.DateTimeFromDMY(ended.day, ended.month - 1, 
                                              ended.year, ended.hour,
                                              ended.minute, ended.second)

            if self.task.completed():
                self.done = True

            self.color = wx.Color(*(self.task.backgroundColor() or (255, 255, 255)))
            self.foreground = wx.Color(*(self.task.foregroundColor(True) or (0, 0, 0)))
            self.font = self.task.font()

            icons = [self.iconProvider(self.task, False)]

            if self.task.attachments():
                icons.append('paperclip_icon')

            if self.task.notes():
                icons.append('note_icon')

            self.icons = icons

            if self.task.percentageComplete(True):
                # If 0, just let the default None value so the progress bar isn't drawn
                # at all
                self.complete = 1.0 * self.task.percentageComplete(True) / 100
        finally:
            self.Thaw()
