# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 João Alexandre de Toledo <jtoledo@griffo.com.br>

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
from taskcoachlib import meta, patterns
from taskcoachlib.i18n import _
from taskcoachlib.domain import date, task
import artprovider

        
class TaskBarIcon(date.ClockObserver, wx.TaskBarIcon):
    def __init__(self, mainwindow, taskList, settings, 
            defaultBitmap='taskcoach', tickBitmap='clock_icon',
            tackBitmap='clock_stopwatch_icon', *args, **kwargs):
        super(TaskBarIcon, self).__init__(*args, **kwargs)
        self.__window = mainwindow
        self.__taskList = taskList
        self.__settings = settings
        self.__bitmap = self.__defaultBitmap = defaultBitmap
        self.__tooltipText = ''
        self.__tickBitmap = tickBitmap
        self.__tackBitmap = tackBitmap
        patterns.Publisher().registerObserver(self.onTaskListChanged,
            eventType=taskList.addItemEventType(),
            eventSource=taskList)
        patterns.Publisher().registerObserver(self.onTaskListChanged, 
            eventType=taskList.removeItemEventType(),
            eventSource=taskList)
        patterns.Publisher().registerObserver(self.onStartTracking,
            eventType=task.Task.trackStartEventType())
        patterns.Publisher().registerObserver(self.onStopTracking,
            eventType=task.Task.trackStopEventType())
        patterns.Publisher().registerObserver(self.onChangeDueDateTime,
            eventType='task.dueDateTime')
        event = wx.EVT_TASKBAR_LEFT_DOWN if '__WXGTK__' == wx.Platform else wx.EVT_TASKBAR_LEFT_DCLICK    
        self.Bind(event, self.onTaskbarClick)
        self.__setTooltipText()
        self.__setIcon()

    # Event handlers:

    def onTaskListChanged(self, event): # pylint: disable-msg=W0613
        self.__setTooltipText()
        self.__startOrStopTicking()
        
    def onStartTracking(self, event):
        for item in event.sources():
            patterns.Publisher().registerObserver(self.onChangeSubject,
                eventType=item.subjectChangedEventType(), eventSource=item)
        self.__setTooltipText()
        self.__startTicking()

    def onStopTracking(self, event):
        for item in event.sources():
            patterns.Publisher().removeObserver(self.onChangeSubject,
                eventType=item.subjectChangedEventType())
        self.__setTooltipText()
        self.__stopTicking()

    def onChangeSubject(self, event): # pylint: disable-msg=W0613
        self.__setTooltipText()
        self.__setIcon()

    def onChangeDueDateTime(self, event): # pylint: disable-msg=W0613
        self.__setTooltipText()
        self.__setIcon()

    def onEverySecond(self, *args, **kwargs):
        if self.__settings.getboolean('window', 
            'blinktaskbariconwhentrackingeffort'):
            self.__toggleTrackingBitmap()
            self.__setIcon()

    def onTaskbarClick(self, event):
        if self.__window.IsIconized() or not self.__window.IsShown():
            self.__window.restore(event)
        else:
            self.__window.Iconize()

    # Menu:

    def setPopupMenu(self, menu):
        self.Bind(wx.EVT_TASKBAR_RIGHT_UP, self.popupTaskBarMenu)
        self.popupmenu = menu # pylint: disable-msg=W0201

    def popupTaskBarMenu(self, event): # pylint: disable-msg=W0613
        self.PopupMenu(self.popupmenu)

    # Getters:

    def tooltip(self):
        return self.__tooltipText
        
    def bitmap(self):
        return self.__bitmap

    def defaultBitmap(self):
        return self.__defaultBitmap
            
    # Private methods:
    
    def __startOrStopTicking(self):
        self.__startTicking()
        self.__stopTicking()
            
    def __startTicking(self):
        if self.__taskList.nrBeingTracked() > 0 and not self.isClockStarted():
            self.startClock()
            self.__toggleTrackingBitmap()
            self.__setIcon()

    def __stopTicking(self):
        if self.__taskList.nrBeingTracked() == 0 and self.isClockStarted():
            self.stopClock()
            self.__setDefaultBitmap()
            self.__setIcon()

    toolTipMessages = \
        [('nrOverdue', _('one task overdue'), _('%d tasks overdue')),
         ('nrDueSoon', _('one task due soon'), _('%d tasks due soon'))]
    
    def __setTooltipText(self):
        ''' Note that Windows XP and Vista limit the text shown in the
            tool tip to 64 characters, so we cannot show everything we would
            like to and have to make choices. '''
        textParts = []              
        trackedTasks = self.__taskList.tasksBeingTracked()
        if trackedTasks:
            count = len(trackedTasks)
            if count == 1:
                tracking = _('tracking "%s"')%trackedTasks[0].subject()
            else:
                tracking = _('tracking effort for %d tasks')%count
            textParts.append(tracking)
        else:
            for getCountMethodName, singular, plural in self.toolTipMessages:
                count = getattr(self.__taskList, getCountMethodName)()
                if count == 1:
                    textParts.append(singular)
                elif count > 1:
                    textParts.append(plural%count)
                
        text = ', '.join(textParts)
        text = u'%s - %s'%(meta.name, text) if text else meta.name
        
        if text != self.__tooltipText:
            self.__tooltipText = text
            self.__setIcon() # Update tooltip
            
    def __setDefaultBitmap(self):
        self.__bitmap = self.__defaultBitmap

    def __toggleTrackingBitmap(self):
        tick, tack = self.__tickBitmap, self.__tackBitmap
        self.__bitmap = tack if self.__bitmap == tick else tick

    def __setIcon(self):
        icon = artprovider.getIcon(self.__bitmap)
        self.SetIcon(icon, self.__tooltipText)
