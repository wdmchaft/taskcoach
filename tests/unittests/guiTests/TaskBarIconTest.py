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

import wx
import test
from taskcoachlib import meta, config, gui
from taskcoachlib.domain import task, effort, date


class MainWindowMock(object):
    def restore(self):
        pass # pragma: no cover
    

class TaskBarIconTestCase(test.TestCase):
    def setUp(self):
        self.taskList = task.TaskList()
        self.settings = task.Task.settings = config.Settings(load=False)
        self.icon = gui.TaskBarIcon(MainWindowMock(), self.taskList,
            self.settings)

    def tearDown(self): # pragma: no cover
        if wx.Platform == '__WXMSW__':
            self.icon.Destroy()
        else:
            self.icon.RemoveIcon()
        super(TaskBarIconTestCase, self).tearDown()
            

class TaskBarIconTest(TaskBarIconTestCase):
    def testIcon_NoTasks(self):
        self.failUnless(self.icon.IsIconInstalled())
        
    def testStartTracking(self):
        activeTask = task.Task()
        self.taskList.append(activeTask)
        activeTask.addEffort(effort.Effort(activeTask))
        self.assertEqual('clock_icon', self.icon.bitmap())

    def testStopTracking(self):
        activeTask = task.Task()
        self.taskList.append(activeTask)
        activeEffort = effort.Effort(activeTask)
        activeTask.addEffort(activeEffort)
        activeTask.removeEffort(activeEffort)
        self.assertEqual(self.icon.defaultBitmap(), self.icon.bitmap())
        
        
class TaskBarIconTooltipTestCase(TaskBarIconTestCase):
    def assertTooltip(self, text):
        expectedTooltip = meta.name
        if text:
            expectedTooltip += ' - %s'%text
        self.assertEqual(expectedTooltip, self.icon.tooltip())


class TaskBarIconTooltipTest(TaskBarIconTooltipTestCase):
    def testNoTasks(self):
        self.assertTooltip('')
        
    def testOneTaskNoDueDateTime(self):
        self.taskList.append(task.Task())
        self.assertTooltip('')

    def testOneTaskDueSoon(self):
        self.taskList.append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.assertTooltip('one task due soon')
        
    def testTwoTasksDueSoon(self):
        self.taskList.append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.taskList.append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.assertTooltip('2 tasks due soon')
        
    def testOneTasksOverdue(self):
        self.taskList.append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.assertTooltip('one task overdue')
        
    def testTwoTasksOverdue(self):
        self.taskList.append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.taskList.append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.assertTooltip('2 tasks overdue')
        
    def testOneTaskDueSoonAndOneTaskOverdue(self):
        self.taskList.append(task.Task(dueDateTime=date.Now() - date.oneDay))
        self.taskList.append(task.Task(dueDateTime=date.Now() + date.oneHour))
        self.assertTooltip('one task overdue, one task due soon')
        
    def testRemoveTask(self):
        newTask = task.Task()
        self.taskList.append(newTask)
        self.taskList.remove(newTask)
        self.assertTooltip('')
        
    def testRemoveOverdueTask(self):
        overdueTask = task.Task(dueDateTime=date.Now() - date.oneDay)
        self.taskList.append(overdueTask)
        self.taskList.remove(overdueTask)
        self.assertTooltip('')


class TaskBarIconTooltipWithTrackedTaskTest(TaskBarIconTooltipTestCase):
    def setUp(self):
        super(TaskBarIconTooltipWithTrackedTaskTest, self).setUp()
        self.task = task.Task(subject='Subject')
        self.taskList.append(self.task)
        self.task.addEffort(effort.Effort(self.task))

    def testStartTracking(self):
        self.assertTooltip('tracking "Subject"')

    def testStopTracking(self):
        self.task.efforts()[0].setStop(date.DateTime(2000,1,1,10,0,0))
        self.assertTooltip('')

    def testTrackingTwoTasks(self):
        activeTask = task.Task()
        self.taskList.append(activeTask)
        activeTask.addEffort(effort.Effort(activeTask))
        self.assertTooltip('tracking effort for 2 tasks')

    def testChangingSubjectOfTrackedTask(self):
        self.task.setSubject('New subject')
        self.assertTooltip('tracking "New subject"')

    def testChangingSubjectOfTaskThatIsNotTrackedAnymore(self):
        self.task.efforts()[0].setStop(date.DateTime(2000,1,1,10,0,0))
        self.task.setSubject('New subject')
        self.assertTooltip('')

