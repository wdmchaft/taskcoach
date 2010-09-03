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


import test
from taskcoachlib import gui, config
from taskcoachlib.domain import task, date


class ReminderFrameTest(test.wxTestCase):
    def setUp(self):
        super(ReminderFrameTest, self).setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.task = task.Task('Task') 
        self.taskList = task.TaskList()
        self.taskList.append(self.task)
        self.frame = gui.reminder.ReminderFrame(self.task, 
            self.taskList, self.settings, self.frame)

    def testMarkTaskCompleted(self): 
        self.frame.onMarkTaskCompleted(None)
        self.failUnless(self.task.completed())
        
    def testMarkRecurringTaskCompleted(self):
        self.task.setRecurrence(date.Recurrence('daily'))
        self.frame.onMarkTaskCompleted(None)
        self.failIf(self.task.completed())
        
    def testMarkRecurringTaskWithReminderCompleted(self):
        self.task.setReminder(date.DateTime(2000,1,1,1,1,1))
        self.task.setRecurrence(date.Recurrence('daily'))
        self.frame.onMarkTaskCompleted(None)
        self.assertEqual(date.DateTime(2000,1,2,1,1,1), self.task.reminder())
