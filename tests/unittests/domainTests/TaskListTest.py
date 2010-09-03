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
from taskcoachlib import config
from taskcoachlib.domain import task, effort, date
from taskcoachlib import config

 
class TaskListTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.taskList = task.TaskList()
        self.task1 = task.Task(dueDateTime=date.DateTime(2110,1,1))
        self.task2 = task.Task(dueDateTime=date.DateTime(2111,1,1))
        self.task3 = task.Task()
    
    def testNrCompleted(self):
        self.assertEqual(0, self.taskList.nrCompleted())
        self.taskList.append(self.task1)
        self.assertEqual(0, self.taskList.nrCompleted())
        self.task1.setCompletionDateTime()
        self.assertEqual(1, self.taskList.nrCompleted())
    
    def testNrOverdue(self):
        self.assertEqual(0, self.taskList.nrOverdue())
        self.taskList.append(self.task1)
        self.assertEqual(0, self.taskList.nrOverdue())
        self.task1.setDueDateTime(date.DateTime(1990, 1, 1))
        self.assertEqual(1, self.taskList.nrOverdue())

    def testAllCompleted(self):
        self.failIf(self.taskList.allCompleted())
        self.task1.setCompletionDateTime()
        self.taskList.append(self.task1)
        self.failUnless(self.taskList.allCompleted())

    def testNrDueSoon(self):
        self.assertEqual(0, self.taskList.nrDueSoon())
        self.taskList.append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.assertEqual(1, self.taskList.nrDueSoon())
        
    def testNrBeingTracked(self):
        self.assertEqual(0, self.taskList.nrBeingTracked())
        activeTask = task.Task()
        activeTask.addEffort(effort.Effort(activeTask))
        self.taskList.append(activeTask)
        self.assertEqual(1, self.taskList.nrBeingTracked())
        
    def testOriginalLength(self):
        self.assertEqual(0, self.taskList.originalLength())

    def testMinPriority_EmptyTaskList(self):
        self.assertEqual(0, self.taskList.minPriority())
        
    def testMinPriority_OneTaskWithDefaultPriority(self):
        self.taskList.append(self.task1)
        self.assertEqual(self.task1.priority(), self.taskList.minPriority())
        
    def testMinPriority_OneTaskWithNonDefaultPriority(self):
        self.taskList.append(task.Task(priority=-5))
        self.assertEqual(-5, self.taskList.minPriority())
        
    def testMinPriority_TwoTasks(self):
        self.taskList.extend([task.Task(priority=3), task.Task(priority=5)])
        self.assertEqual(3, self.taskList.minPriority())
        
    def testMaxPriority_EmptyTaskList(self):
        self.assertEqual(0, self.taskList.maxPriority())
        
    def testMaxPriority_OneTaskWithDefaultPriority(self):
        self.taskList.append(self.task1)
        self.assertEqual(self.task1.priority(), self.taskList.maxPriority())
        
    def testMaxPriority_OneTaskWithNonDefaultPriority(self):
        self.taskList.append(task.Task(priority=-5))
        self.assertEqual(-5, self.taskList.maxPriority())
        
    def testMaxPriority_TwoTasks(self):
        self.taskList.extend([task.Task(priority=3), task.Task(priority=5)])
        self.assertEqual(5, self.taskList.maxPriority())

