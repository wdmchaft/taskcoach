'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>

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

from unittests import asserts
from CommandTestCase import CommandTestCase
from taskcoachlib import command, patterns
from taskcoachlib.domain import task, effort, date


class EffortCommandTestCase(CommandTestCase, asserts.CommandAsserts):
    def setUp(self):
        self.taskList = task.TaskList()
        self.effortList = effort.EffortList(self.taskList)
        self.originalTask = task.Task()
        self.taskList.append(self.originalTask)
        self.originalStop = date.DateTime.now() 
        self.originalStart = self.originalStop - date.TimeDelta(hours=1) 
        self.effort = effort.Effort(self.originalTask, self.originalStart, 
                                    self.originalStop)
        self.originalTask.addEffort(self.effort)


class NewEffortCommandTest(EffortCommandTestCase):        
    def testNewEffort(self):
        newEffortCommand = command.NewEffortCommand(self.effortList, 
                                                    [self.originalTask])
        newEffortCommand.do()
        newEffort = newEffortCommand.efforts[0]
        self.assertDoUndoRedo(
            lambda: self.failUnless(newEffort in self.originalTask.efforts()),
            lambda: self.assertEqual([self.effort], self.originalTask.efforts()))

    def testNewEffortWhenUserEditsTask(self):
        secondTask = task.Task()
        self.taskList.append(secondTask)
        newEffortCommand = command.NewEffortCommand(self.effortList, 
                                                    [self.originalTask])
        newEffort = newEffortCommand.efforts[0]
        newEffort.setTask(secondTask)
        newEffortCommand.do()
        self.assertDoUndoRedo(
            lambda: self.failUnless(newEffort in secondTask.efforts() and \
                    newEffort not in self.originalTask.efforts()),
            lambda: self.failUnless(newEffort not in secondTask.efforts() and \
                    newEffort not in self.originalTask.efforts()))
        

class EditEffortCommandTest(EffortCommandTestCase):
    def setUp(self):
        super(EditEffortCommandTest, self).setUp()
        self.newTask = task.Task()
        self.events = []

    def onEvent(self, event):
        self.events.append(event)
        
    def registerObserver(self, eventType): # pylint: disable-msg=W0221
        patterns.Publisher().registerObserver(self.onEvent, eventType=eventType)

    def testEditStartDateTime(self):
        edit = command.EditEffortCommand(self.effortList, [self.effort])
        expected = date.DateTime(2000,1,1)
        edit.items[0].setStart(expected)
        edit.do()
        self.assertDoUndoRedo(
            lambda: self.assertEqual(expected, self.effort.getStart()),
            lambda: self.assertEqual(self.originalStart, self.effort.getStart()))

    def doEditEffortTask(self):
        edit = command.EditEffortCommand(self.effortList, [self.effort])
        edit.items[0].setTask(self.newTask)
        edit.do()

    def testEditTask(self):
        self.doEditEffortTask()
        self.assertDoUndoRedo(
            lambda: self.assertEqual(self.newTask, self.effort.task()),
            lambda: self.assertEqual(self.originalTask, self.effort.task()))

    def testEditTaskNotifiesOriginalTask(self):
        self.registerObserver('task.effort.remove')
        self.doEditEffortTask()
        self.assertEqual(self.effort, self.events[0].value())

    def testEditTaskNotifiesNewTask(self):
        self.registerObserver('task.effort.add')
        self.doEditEffortTask()
        self.assertEqual(self.effort, self.events[0].value())

    def testEditTaskUndoNotifiesOriginalTask(self):
        self.registerObserver('task.effort.add')
        self.doEditEffortTask()
        self.undo()
        self.assertEqual(self.effort, self.events[0].value())
        
    def testEditTaskUndoNotifiesNewTask(self):
        self.registerObserver('task.effort.remove')
        self.doEditEffortTask()
        self.undo()
        self.assertEqual(self.effort, self.events[0].value())

    def testEditTaskRedoNotifiesOriginalTask(self):
        self.registerObserver('task.effort.remove')
        self.doEditEffortTask()
        self.undo()
        self.redo()
        self.assertEqual(self.effort, self.events[1].value())

    def testEditTaskRedoNotifiesNewTask(self):
        self.registerObserver('task.effort.add')
        self.doEditEffortTask()
        self.undo()
        self.redo()
        self.assertEqual(self.effort, self.events[1].value())


class StartAndStopEffortCommandTest(EffortCommandTestCase):
    def setUp(self):
        super(StartAndStopEffortCommandTest, self).setUp()
        self.start = command.StartEffortCommand(self.taskList, [self.originalTask])
        self.start.do()
        
    def testStart(self):
        self.assertDoUndoRedo(
            lambda: self.failUnless(self.originalTask.isBeingTracked()),
            lambda: self.failIf(self.originalTask.isBeingTracked()))
                        
    def testStop(self):
        stop = command.StopEffortCommand(self.taskList)
        stop.do()
        self.assertDoUndoRedo(
            lambda: self.failIf(self.originalTask.isBeingTracked()),
            lambda: self.failUnless(self.originalTask.isBeingTracked()))
                
    def testStartStopsPreviousStart(self):
        task2 = task.Task()
        start = command.StartEffortCommand(self.taskList, [task2])
        start.do()
        self.assertDoUndoRedo(
            lambda: self.failIf(self.originalTask.isBeingTracked()),
            lambda: self.failUnless(self.originalTask.isBeingTracked()))
