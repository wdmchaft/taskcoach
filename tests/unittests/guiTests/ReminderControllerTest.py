'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>

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

import test, wx
from taskcoachlib import gui, patterns, config, persistence
from taskcoachlib.domain import task, date


class ReminderControllerUnderTest(gui.ReminderController):
    def __init__(self, *args, **kwargs):
        self.messages = []
        self.userAttentionRequested = False
        super(ReminderControllerUnderTest, self).__init__(*args, **kwargs)
        
    def showReminderMessage(self, message):
        self.messages.append(message)
        return True
    
    def requestUserAttention(self):
        self.userAttentionRequested = True

        
class DummyWindow(wx.Frame):
    def __init__(self):
        super(DummyWindow, self).__init__(None)
        self.taskFile = persistence.TaskFile()
    

class ReminderControllerTestCase(test.TestCase):
    def setUp(self):
        self.taskList = task.TaskList()
        self.reminderController = ReminderControllerUnderTest(DummyWindow(), 
            self.taskList, config.Settings(load=False))
        self.nowDateTime = date.DateTime.now()
        self.reminderDateTime = self.nowDateTime + date.TimeDelta(hours=1)


class ReminderControllerTest(ReminderControllerTestCase):
    def setUp(self):
        super(ReminderControllerTest, self).setUp()
        self.task = task.Task('Task')
        self.taskList.append(self.task)

    def testSetTaskReminderAddsClockEventToPublisher(self):
        self.task.setReminder(self.reminderDateTime)
        self.assertEqual([self.reminderController.onReminder], 
            patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))

    def testClockTriggersReminder(self):
        self.task.setReminder(self.reminderDateTime)
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime)
        self.assertEqual([self.task], 
                         self.reminderController.messages)
        
    def testAfterReminderClockEventIsRemovedFromPublisher(self):
        self.task.setReminder(self.reminderDateTime)
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime)
        self.assertEqual([], patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))
        
    def testAddTaskWithReminderAddsClockEventToPublisher(self):
        taskWithReminder = task.Task('Task with reminder', 
                                     reminder=self.reminderDateTime)
        self.taskList.append(taskWithReminder)
        self.assertEqual([self.reminderController.onReminder], 
            patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))
                
    def testRemoveTaskWithReminderRemovesClockEventFromPublisher(self):
        self.task.setReminder(self.reminderDateTime)
        self.taskList.remove(self.task)
        self.assertEqual([], patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))
                
    def testChangeReminderRemovesOldReminder(self):
        self.task.setReminder(self.reminderDateTime)
        self.task.setReminder(self.reminderDateTime + date.TimeDelta(hours=1))
        self.assertEqual([], patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))
        
    def testMarkTaskCompletedRemovesReminder(self):
        self.task.setReminder(self.reminderDateTime)
        self.task.setCompletionDateTime(date.Now())
        self.assertEqual([], patterns.Publisher().observers(eventType=\
                date.Clock.eventType(self.reminderDateTime)))
        
    def dummyCloseEvent(self, snoozeTimeDelta=None, openAfterClose=False):
        class DummySnoozeOptions(object):
            Selection = 0
            def GetClientData(self, *args): # pylint: disable-msg=W0613
                return snoozeTimeDelta
        class DummyDialog(object):
            task = self.task
            openTaskAfterClose = openAfterClose
            ignoreSnoozeOption = False
            snoozeOptions = DummySnoozeOptions()
            def Destroy(self):
                pass
        class DummyEvent(object):
            EventObject = DummyDialog()
            def Skip(self):
                pass
        return DummyEvent()
    
    def testOnCloseReminderResetsReminder(self):
        self.task.setReminder(self.reminderDateTime)
        self.reminderController.onCloseReminderDialog(self.dummyCloseEvent(), 
                                                     show=False)
        self.assertEqual(None, self.task.reminder())

    def testOnCloseReminderSetsReminder(self):
        self.task.setReminder(self.reminderDateTime)
        oneHour = date.TimeDelta(hours=1)
        self.reminderController.onCloseReminderDialog(\
            self.dummyCloseEvent(oneHour), show=False)
        self.failUnless(abs(self.nowDateTime + oneHour - self.task.reminder()) \
                        < date.TimeDelta(seconds=5))

    def testOnCloseMayOpenTask(self):
        self.task.setReminder(self.reminderDateTime)
        frame = self.reminderController.onCloseReminderDialog(\
            self.dummyCloseEvent(openAfterClose=True), show=False)
        self.failUnless(frame)
        
    def testOnWakeDoesNotRequestUserAttentionWhenThereAreNoReminders(self):
        self.reminderController.onWake(None)
        self.failIf(self.reminderController.userAttentionRequested)
        

class ReminderControllerTest_TwoTasksWithSameReminderDateTime(ReminderControllerTestCase):
    def setUp(self):
        super(ReminderControllerTest_TwoTasksWithSameReminderDateTime, self).setUp()
        self.task1 = task.Task('Task 1', reminder=self.reminderDateTime)
        self.task2 = task.Task('Task 2', reminder=self.reminderDateTime)
        self.taskList.extend([self.task1, self.task2])

    def testClockNotificationResultsInTwoMessages(self):
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime)
        self.assertEqualLists([self.task1, self.task2], 
            self.reminderController.messages)

    def testChangeOneReminder(self):
        self.task1.setReminder(self.reminderDateTime + date.TimeDelta(hours=1))
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime + date.TimeDelta(hours=1))
        self.assertEqualLists([self.task1, self.task2], 
                              self.reminderController.messages)
                         
    def testChangeOneReminderDoesNotAffectTheOther(self):
        self.task1.setReminder(self.reminderDateTime + date.TimeDelta(hours=1))
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime)
        self.assertEqual([self.task2], self.reminderController.messages)
                                                  
    def testRemoveOneTaskDoesNotAffectTheOther(self):
        self.taskList.remove(self.task1)
        date.Clock().notifySpecificTimeObservers(now=self.reminderDateTime)
        self.assertEqual([self.task2], self.reminderController.messages)


