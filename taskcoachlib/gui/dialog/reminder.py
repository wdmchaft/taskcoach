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
from taskcoachlib import meta, patterns, command
from taskcoachlib.widgets import sized_controls
from taskcoachlib.i18n import _
from taskcoachlib.domain import date
from taskcoachlib.gui import render


class ReminderDialog(sized_controls.SizedDialog):
    snoozeChoices = [(0, _("Don't snooze")), (5, _('5 minutes')),
             (10, _('10 minutes')), (15, _('15 minutes')),
             (20, _('20 minutes')), (30, _('30 minutes')), 
             (45, _('45 minutes')), (60, _('1 hour')), (90, _('1.5 hour')), 
             (120, _('2 hours')), (3*60, _('3 hours')), (4*60, _('4 hours')), 
             (6*60, _('6 hours')), (8*60, _('8 hours')), (12*60, _('12 hours')), 
             (18*60, _('18 hours')), (24*60, _('24 hours')),
             (48*60, _('48 hours')), (72*60, _('72 hours'))] # FIMXE: duplicated in preferences dialog
    snoozeTimes = [date.TimeDelta(minutes=minutes[0]) for minutes in \
                   snoozeChoices]
    
    def __init__(self, task, taskList, settings, *args, **kwargs):
        kwargs['title'] = kwargs.get('title', meta.name + ' ' + _('Reminder'))
        super(ReminderDialog, self).__init__(*args, **kwargs)
        self.task = task
        self.taskList = taskList
        self.settings = settings
        patterns.Publisher().registerObserver(self.onTaskRemoved, 
                                              eventType=self.taskList.removeItemEventType(),
                                              eventSource=self.taskList)
        patterns.Publisher().registerObserver(self.onTaskCompletionDateChanged, 
                                              eventType='task.completionDate',
                                              eventSource=self.task)
        self.openTaskAfterClose = self.ignoreSnoozeOption = False
        pane = self.GetContentsPane()
        pane.SetSizerType("form")
        wx.StaticText(pane, label=_('Task') + ':')
        self.openTask = wx.Button(pane, label=self.task.subject(recursive=True))
        self.openTask.Bind(wx.EVT_BUTTON, self.onOpenTask)
        for label in _('Reminder date/time') + ':', \
            render.dateTime(self.task.reminder()), _('Snooze') + ':':
            wx.StaticText(pane, label=label)
        self.snoozeOptions = wx.ComboBox(pane)
        snoozeTimesUserWantsToSee = [0] + eval(self.settings.get('view', 'snoozetimes'))
        for choice, timeDelta in zip(self.snoozeChoices, self.snoozeTimes):
            if choice[0] in snoozeTimesUserWantsToSee:
                self.snoozeOptions.Append(choice[1], timeDelta)
        self.snoozeOptions.SetSelection(0)
        buttonSizer = self.CreateStdDialogButtonSizer(wx.OK)
        self.markCompleted = wx.Button(self, label=_('Mark task completed'))
        self.markCompleted.Bind(wx.EVT_BUTTON, self.onMarkTaskCompleted)
        if self.task.completed():
            self.markCompleted.Disable()
        buttonSizer.Add(self.markCompleted)
        self.SetButtonSizer(buttonSizer)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Bind(wx.EVT_BUTTON, self.onOK, id=self.GetAffirmativeId())
        self.Fit()

    def onOpenTask(self, event): # pylint: disable-msg=W0613
        self.openTaskAfterClose = True
        self.Close()
        
    def onMarkTaskCompleted(self, event): # pylint: disable-msg=W0613
        self.ignoreSnoozeOption = True
        self.Close()
        command.MarkCompletedCommand(self.taskList, [self.task]).do()
    
    def onTaskRemoved(self, event):
        if self.task in event.values():
            self.Close()
            
    def onTaskCompletionDateChanged(self, event): # pylint: disable-msg=W0613
        if self.task.completed():
            self.Close()
        else:
            self.markCompleted.Enable()
    
    def onClose(self, event):
        event.Skip()
        patterns.Publisher().removeInstance(self)
        
    def onOK(self, event):
        event.Skip()
        self.Close()