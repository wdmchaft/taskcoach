'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>

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
from taskcoachlib import patterns, command
from taskcoachlib.domain import date
from taskcoachlib.gui.dialog import reminder, editor
from taskcoachlib.i18n import _


if '__WXMAC__' in wx.PlatformInfo:
    import sys, os, struct

    if struct.calcsize('L') == 8:
        _subdir = 'IA64'
    else:
        _subdir = 'IA32'

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin.in', 'macos', _subdir))

    from taskcoachlib.thirdparty.Growl import GrowlNotifier, Image
    from taskcoachlib import meta

    class TaskCoachGrowlNotifier(GrowlNotifier):
        applicationName = meta.name
        notifications = [u'Reminder']


class ReminderController(object):
    def __init__(self, mainWindow, taskList, settings):
        super(ReminderController, self).__init__()
        patterns.Publisher().registerObserver(self.onSetReminder,
            eventType='task.reminder')
        patterns.Publisher().registerObserver(self.onAddTask,
            eventType=taskList.addItemEventType(),
            eventSource=taskList)
        patterns.Publisher().registerObserver(self.onRemoveTask,
            eventType=taskList.removeItemEventType(),
            eventSource=taskList)
        patterns.Publisher().registerObserver(self.onWake, eventType='powermgt.on')
        self.__tasksWithReminders = {} # {task: reminderDateTime}
        self.__mainWindow = mainWindow
        self.__mainWindowWasHidden = False
        self.__registerRemindersForTasks(taskList)
        self.settings = settings
        self.taskList = taskList

    def onWake(self, event):
        # Reminders set for when the computer was asleep must be
        # bumped

        now = date.DateTime.today()

        for task, reminderDateTime in self.__tasksWithReminders.items():
            if reminderDateTime <= now:
                self.showReminderMessage(task)
                if not ('__WXMAC__' in wx.PlatformInfo and self.settings.getboolean('feature', 'growl')):
                    self.__removeReminder(task)
        self.requestUserAttention()

    def onAddTask(self, event):
        self.__registerRemindersForTasks(event.values())
                
    def onRemoveTask(self, event):
        self.__removeRemindersForTasks(event.values())
                
    def onSetReminder(self, event):
        tasks = event.sources()
        self.__removeRemindersForTasks(tasks)
        self.__registerRemindersForTasks(tasks)
        
    def onReminder(self, event):
        now = event.value() + date.TimeDelta(seconds=1)
        for task, reminderDateTime in self.__tasksWithReminders.items():
            if reminderDateTime <= now:
                self.showReminderMessage(task)
                if not ('__WXMAC__' in wx.PlatformInfo and self.settings.getboolean('feature', 'growl')):
                    self.__removeReminder(task)
        self.requestUserAttention()
        
    def requestUserAttention(self):
        if '__WXMAC__' in wx.PlatformInfo and self.settings.getboolean('feature', 'growl'):
            # When using Growl, this is not necessary. Even when not using Growl, it's
            # annoying as hell. Anyway.
            return
        self.__mainWindowWasHidden = not self.__mainWindow.IsShown()
        if self.__mainWindowWasHidden:
            self.__mainWindow.Show()
        if not self.__mainWindow.IsActive():
            self.__mainWindow.RequestUserAttention()
        
    def showReminderMessage(self, task):
        if '__WXMAC__' in wx.PlatformInfo:
            if self.settings.getboolean('feature', 'growl'):
                notifier = TaskCoachGrowlNotifier(applicationIcon=Image.imageWithIconForCurrentApplication())
                notifier.register()
                notifier.notify(noteType=u'Reminder', title=_('%s Reminder') % meta.name,
                                description=task.subject(), sticky=True)
                self.__removeReminder(task)
                task.setReminder(None)
                return

        reminderDialog = reminder.ReminderDialog(task, self.taskList, self.settings, self.__mainWindow)
        reminderDialog.Bind(wx.EVT_CLOSE, self.onCloseReminderDialog)        
        reminderDialog.Show()
        
    def onCloseReminderDialog(self, event, show=True):
        event.Skip()
        dialog = event.EventObject
        task = dialog.task
        if not dialog.ignoreSnoozeOption:
            snoozeOptions = dialog.snoozeOptions
            snoozeTimeDelta = snoozeOptions.GetClientData(snoozeOptions.Selection)
            if snoozeTimeDelta:
                newReminder = date.DateTime.now() + snoozeTimeDelta
            else:
                newReminder = None
            task.setReminder(newReminder) # Note that this is not undoable
            # Undoing the snoozing makes little sense, because it would set the 
            # reminder back to its original date-time, which is now in the past.
        if dialog.openTaskAfterClose:
            editTask = editor.TaskEditor(self.__mainWindow,
                command.EditTaskCommand(self.taskList, [task]), 
                self.settings, self.taskList, self.__mainWindow.taskFile, 
                bitmap='edit')
            editTask.Show(show)
        else:
            editTask = None
        dialog.Destroy()
        if self.__mainWindowWasHidden:
            self.__mainWindow.Hide()
        return editTask # For unit testing purposes
            
    def __registerRemindersForTasks(self, tasks):
        for task in tasks:
            if task.reminder():
                self.__registerReminder(task)

    def __removeRemindersForTasks(self, tasks):
        for task in tasks:
            if task in self.__tasksWithReminders:
                self.__removeReminder(task)

    def __registerReminder(self, task):
        reminderDateTime = task.reminder()
        if reminderDateTime < date.DateTime.now():
            reminderDateTime = date.DateTime.now() + date.TimeDelta(seconds=2)
        if reminderDateTime not in self.__tasksWithReminders.values():
            self.__changeDateTimeObservation(reminderDateTime, 
                                             'registerObserver')
        self.__tasksWithReminders[task] = reminderDateTime
            
    def __removeReminder(self, task):
        oldReminderDateTime = self.__tasksWithReminders[task]
        del self.__tasksWithReminders[task]
        if oldReminderDateTime not in self.__tasksWithReminders.values():
            self.__changeDateTimeObservation(oldReminderDateTime, 
                                             'removeObserver')
    
    def __changeDateTimeObservation(self, reminderDateTime, registrationMethod):
        eventType = date.Clock().eventType(reminderDateTime)
        getattr(patterns.Publisher(), registrationMethod)(self.onReminder, 
            eventType=eventType)

