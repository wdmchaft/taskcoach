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

class TaskListAssertsMixin(object):
    def assertTaskList(self, expected):
        self.assertEqualLists(expected, self.taskList)
        self.assertAllChildrenInTaskList()

    def assertAllChildrenInTaskList(self):
        for task in self.taskList:
            for child in task.children():
                self.failUnless(child in self.taskList)

    def assertEmptyTaskList(self):
        self.failIf(self.taskList)


class EffortListAssertsMixin(object):
    def assertEffortList(self, expected):
        self.assertEqualLists(expected, self.effortList)
        
        
class NoteContainerAssertsMixin(object):
    def assertNoteContainer(self, expected):
        for note in expected:
            self.failUnless(note in self.noteContainer)
        for note in self.noteContainer:
            self.failUnless(note in expected)

                
class EffortAssertsMixin(object):
    def assertEqualEfforts(self, effort1, effort2):
        self.assertEqual(effort1.task(), effort2.task())
        self.assertEqual(effort1.getStart(), effort2.getStart())
        self.assertEqual(effort1.getStop(), effort2.getStop())
        self.assertEqual(effort1.description(), effort2.description())
        
                
class TaskAssertsMixin(object):
    def failIfParentAndChild(self, parent, child):
        self.failIf(child in parent.children())
        if child.parent():
            self.failIf(child.parent() == parent)

    def failUnlessParentAndChild(self, parent, child):
        self.failUnless(child in parent.children())
        self.failUnless(child.parent() == parent)

    def assertTaskCopy(self, orig, copy):
        self.failIf(orig == copy)
        self.assertEqual(orig.subject(), copy.subject())
        self.assertEqual(orig.description(), copy.description())
        self.assertEqual(orig.dueDateTime(), copy.dueDateTime())
        self.assertEqual(orig.startDateTime(), copy.startDateTime())
        self.assertEqual(orig.completionDateTime(), copy.completionDateTime())
        self.assertEqual(orig.recurrence(), copy.recurrence())
        self.assertEqual(orig.budget(), copy.budget())
        if orig.parent():
            self.failIf(copy in orig.parent().children()) 
        self.failIf(orig.id() == copy.id())
        self.assertEqual(orig.categories(), copy.categories())
        self.assertEqual(orig.priority(), copy.priority())
        self.assertEqual(orig.fixedFee(), copy.fixedFee())
        self.assertEqual(orig.hourlyFee(), copy.hourlyFee())
        self.assertEqual(orig.attachments(), copy.attachments())
        self.assertEqual(orig.reminder(), copy.reminder())
        self.assertEqual(orig.shouldMarkCompletedWhenAllChildrenCompleted(),
                         copy.shouldMarkCompletedWhenAllChildrenCompleted())
        self.assertEqual(len(orig.children()), len(copy.children()))
        for origChild, copyChild in zip(orig.children(), copy.children()):
            self.assertTaskCopy(origChild, copyChild)
        for origEffort, copyEffort in zip(orig.efforts(), copy.efforts()):
            self.assertEffortCopy(origEffort, copyEffort)

    def assertEffortCopy(self, orig, copy):
        self.failIf(orig.id() == copy.id())
        self.failIf(orig.task() == copy.task())
        self.assertEqual(orig.getStart(), copy.getStart())
        self.assertEqual(orig.getStop(), copy.getStop())
        self.assertEqual(orig.description(), copy.description())


class CommandAssertsMixin(object):
    def assertHistoryAndFuture(self, expectedHistory, expectedFuture):
        from taskcoachlib import patterns
        commands = patterns.CommandHistory()
        self.assertEqual(expectedHistory, commands.getHistory())
        self.assertEqual(expectedFuture, commands.getFuture())

    def assertDoUndoRedo(self, assertDone, assertUndone=None):
        if not assertUndone:
            assertUndone = assertDone
        assertDone()
        self.undo()
        assertUndone()
        self.redo()
        assertDone()

class Mixin(CommandAssertsMixin, TaskAssertsMixin, EffortAssertsMixin, 
            TaskListAssertsMixin, EffortListAssertsMixin, 
            NoteContainerAssertsMixin):
    pass
