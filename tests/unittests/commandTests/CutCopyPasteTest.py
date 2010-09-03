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

from unittests import asserts
from CommandTestCase import CommandTestCase
from TaskCommandsTest import TaskCommandTestCase, CommandWithChildrenTestCase, \
    CommandWithEffortTestCase
from taskcoachlib import command
from taskcoachlib.domain import task, note


class CutCommandWithTasksTest(TaskCommandTestCase):
    def testCutTasks_WithoutSelection(self):
        self.cut()
        self.assertDoUndoRedo(lambda: self.assertTaskList([self.task1]))

    def testCutTasks_SpecificTask(self):
        self.taskList.append(self.task2)
        self.cut([self.task1])
        self.assertDoUndoRedo(lambda: (self.assertTaskList([self.task2]),
            self.assertEqual([self.task1], command.Clipboard().get()[0])),
            lambda: (self.assertTaskList([self.task1, self.task2]),
            self.failIf(command.Clipboard())))

    def testCutTasks_All(self):
        self.cut('all')
        self.assertDoUndoRedo(self.assertEmptyTaskList, 
            lambda: self.assertTaskList(self.originalList))
        
    def testCutTaskThatBelongsToCategory(self):
        self.category.addCategorizable(self.task1)
        self.task1.addCategory(self.category)
        self.cut('all')
        self.assertDoUndoRedo(lambda: self.failIf(self.category.categorizables()),
                              lambda: self.assertEqual(set([self.task1]), 
                                                       self.category.categorizables()))


class CutCommandWithTasksWithChildrenTest(CommandWithChildrenTestCase):
    def testCutParent(self):
        self.cut([self.parent])
        self.assertDoUndoRedo(lambda: self.assertTaskList([self.task1]),
            lambda: self.assertTaskList(self.originalList))

    def testCutChild(self):
        self.cut([self.child])
        self.assertDoUndoRedo(
            lambda: (self.assertTaskList([self.task1, self.child2, self.parent]),
            self.assertEqual([self.child2], self.parent.children())),
            lambda: (self.assertTaskList(self.originalList),
            self.failUnlessParentAndChild(self.parent, self.child)))

    def testCutParentAndChild(self):
        self.cut([self.child, self.parent])
        self.assertDoUndoRedo(lambda: self.assertTaskList([self.task1]),
            lambda: self.assertTaskList(self.originalList))


class CutCommandWithEffortTest(CommandWithEffortTestCase):
    def testCutEfforts_WithoutSelection(self):
        self.cut()
        self.assertDoUndoRedo(lambda: self.assertEffortList(self.originalEffortList))

    def testCutEfforts_Selection(self):
        self.cut([self.effort1])
        self.assertDoUndoRedo(lambda: self.assertEffortList([self.effort2]),
                              lambda: self.assertEffortList(self.originalEffortList))
                              
    def testCutEfforts_All(self):
        self.cut('all')
        self.assertDoUndoRedo(lambda: self.assertEffortList([]),
                              lambda: self.assertEffortList(self.originalEffortList))


class NoteCommandTestCase(CommandTestCase, asserts.Mixin):
    def setUp(self):
        super(NoteCommandTestCase, self).setUp()
        self.note1 = note.Note()
        self.note2 = note.Note()
        self.list = self.noteContainer = note.NoteContainer([self.note1, self.note2])
        self.original = note.NoteContainer([self.note1, self.note2])


class CutCommandWithNotes(NoteCommandTestCase):        
    def testCutNotes_WithoutSelection(self):
        self.cut()
        self.assertDoUndoRedo(lambda: self.assertNoteContainer(self.original))

    def testCutNotes_Selection(self):
        self.cut([self.note1])
        self.assertDoUndoRedo(lambda: self.assertNoteContainer(note.NoteContainer([self.note2])),
            lambda: self.assertNoteContainer(self.original))
        
    def testCutNotes_All(self):
        self.cut('all')
        self.assertDoUndoRedo(lambda: self.assertNoteContainer(note.NoteContainer()),
            lambda: self.assertNoteContainer(self.original))
        

class PasteCommandWithTasksTest(TaskCommandTestCase):
    def testPasteWithoutPreviousCut(self):
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertTaskList(self.originalList))

    def testPaste(self):
        self.cut([self.task1])
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertTaskList(self.originalList),
            self.assertEmptyTaskList)

    def testClipboardIsEmptyAfterPaste(self):
        self.cut([self.task1])
        self.paste()
        # pylint: disable-msg=W0212
        self.assertDoUndoRedo(
            lambda: self.assertEqual([], command.Clipboard()._contents), 
            lambda: self.assertEqual([self.task1], command.Clipboard()._contents))


class PasteCommandWithNotesTest(NoteCommandTestCase):
    def testPasteWithoutPreviousCut(self):
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertNoteContainer(self.original))
        
    def testPaste(self):
        self.cut([self.note1])
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertNoteContainer(self.original),
            lambda: self.assertNoteContainer([self.note2]))
            

class PasteCommandWithEffortTest(CommandWithEffortTestCase):
    def testPasteWithoutPreviousCut(self):
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertEffortList(self.originalEffortList))

    def testPaste(self):
        self.cut([self.effort1])
        self.paste()
        self.assertDoUndoRedo(lambda: self.assertEffortList(self.originalEffortList),
            lambda: self.assertEqualLists([self.effort2], self.effortList))

    def testClipboardIsEmptyAfterPaste(self):
        self.cut([self.effort1])
        self.paste()
        # pylint: disable-msg=W0212
        self.assertDoUndoRedo(
            lambda: self.assertEqual([], command.Clipboard()._contents), 
            lambda: self.assertEqual([self.effort1], command.Clipboard()._contents))
        
        
class PasteCommandWithTasksWithChildrenTest(CommandWithChildrenTestCase):
    def testCutAndPasteChild(self):
        self.cut([self.child])
        self.paste()
        self.assertDoUndoRedo(lambda: (self.assertTaskList(self.originalList),
            self.failIfParentAndChild(self.parent, self.child),
            self.failUnlessParentAndChild(self.child, self.grandchild)),
            lambda: self.assertTaskList([self.task1, self.parent, self.child2]))

    def testCutAndPasteParentAndChild(self):
        self.cut([self.parent, self.child])
        self.paste()
        self.assertDoUndoRedo(lambda: (self.assertTaskList(self.originalList),
            self.failIfParentAndChild(self.parent, self.child)),
            lambda: self.assertTaskList([self.task1]))

    def testCutAndPasteParentAndGrandChild(self):
        self.cut([self.parent, self.grandchild])
        self.paste()
        self.assertDoUndoRedo(lambda: (self.assertTaskList(self.originalList),
            self.failUnlessParentAndChild(self.parent, self.child),
            self.failIfParentAndChild(self.child, self.grandchild)),
            lambda: self.assertTaskList([self.task1]))


class PasteIntoTaskCommandTest(CommandWithChildrenTestCase):
    def testPasteChild(self):
        self.cut([self.child])
        self.paste([self.task1])
        self.assertDoUndoRedo(
            lambda: (self.assertTaskList(self.originalList),
            self.failUnlessParentAndChild(self.task1, self.child), 
            self.failIfParentAndChild(self.parent, self.child),
            self.failUnlessParentAndChild(self.child, self.grandchild)),
            lambda: (self.assertEqual([self.child2], self.parent.children()),
            self.assertEqual([], self.task1.children())))

    def testPasteExtraChild(self):
        self.cut([self.task1])
        self.paste([self.parent])
        self.assertDoUndoRedo(
            lambda: self.failUnlessParentAndChild(self.parent, self.task1),
            lambda: (self.assertEqual([self.child, self.child2], 
            self.parent.children()), self.assertTaskList([self.parent, 
            self.child, self.child2, self.grandchild])))

    def testPasteChild_MarksNewParentAsNotCompleted(self):
        self.markCompleted([self.parent])
        self.cut([self.task1])
        self.paste([self.parent])
        self.assertDoUndoRedo(
            lambda: self.failIf(self.parent.completed()),
            lambda: self.failUnless(self.parent.completed()))

    def testPasteCompletedChild_DoesNotMarkParentAsNotCompleted(self):
        self.markCompleted([self.task1, self.parent])
        self.cut([self.task1])
        self.paste([self.parent])
        self.assertDoUndoRedo(
            lambda: self.failUnless(self.parent.completed()),
            lambda: self.failUnless(self.parent.completed()))


class PasteIntoTaskCommandWithEffortTest(CommandWithEffortTestCase):
    def testPaste(self):
        self.cut([self.effort1])
        self.paste([self.task2])
        self.assertDoUndoRedo(
            lambda: self.assertEqualLists([self.effort1, self.effort2], self.task2.efforts()),
            lambda: self.assertEqualLists([self.effort1], self.task1.efforts()))

        
class CutAndPasteTasksIntegrationTest(TaskCommandTestCase):
    def testUndoCutAndPaste(self):
        self.cut([self.task1])
        self.paste()
        self.undo()
        self.undo()
        self.assertTaskList(self.originalList)

class CutAndPasteWithChildrenIntegrationTest(CommandWithChildrenTestCase):
    def assertTaskListUnchanged(self):
        self.assertTaskList(self.originalList)
        self.failUnlessParentAndChild(self.parent, self.child)
        self.failUnlessParentAndChild(self.child, self.grandchild)

    def testUndoCutAndPaste(self):
        self.cut([self.child])
        self.paste()
        self.undo()
        self.undo()
        self.assertTaskListUnchanged()
        
    def testUndoCutAndPasteAsSubtask(self):
        self.cut([self.child])
        self.paste([self.child2])
        self.undo()
        self.undo()
        self.assertTaskListUnchanged()

    def testUndoCutAndPasteParentAndGrandChild(self):
        self.cut([self.parent, self.grandchild])
        self.paste()
        self.undo()
        self.undo()
        self.assertTaskListUnchanged()

    def testRedoCutAndPasteParentAndGrandChild(self):
        self.cut([self.parent, self.grandchild])
        self.paste()
        self.undo()
        self.undo()
        self.redo()
        self.redo()
        self.assertEqual(None, self.grandchild.parent())
        self.failIf(self.child.children())
        

class CopyCommandWithTasksTest(TaskCommandTestCase):
    def testCopyTaskWithoutSelection(self):
        self.copy([])
        self.assertDoUndoRedo(
            lambda: self.assertEqual([], command.Clipboard().get()[0]),
                    self.assertTaskList(self.originalList))

    def testCopyTask(self):
        self.copy([self.task1])
        copiedTask = command.Clipboard().get()[0][0]
        self.assertDoUndoRedo(lambda: (self.assertTaskCopy(self.task1, copiedTask),
            self.assertTaskList(self.originalList)),
            lambda: (self.assertTaskList(self.originalList),
            self.failIf(command.Clipboard())))


class CopyCommandWithTasksWithChildrenTest(CommandWithChildrenTestCase):
    def testCopy(self):
        self.copy([self.parent])
        copiedTask = command.Clipboard().get()[0][0]
        self.assertDoUndoRedo(
            lambda: self.assertTaskCopy(self.parent, copiedTask),
            lambda: (self.assertTaskList(self.originalList),
            self.failIf(command.Clipboard())))


class CopyCommandWithEffortTest(CommandWithEffortTestCase):
    def testCopyEffortWithoutSelection(self):
        self.copy([])
        self.assertDoUndoRedo(
            lambda: self.assertEqual([], command.Clipboard().get()[0]),
                    self.assertEffortList(self.originalEffortList))
        
    def testCopyEffort(self):
        self.copy([self.effort1])
        copiedEffort = command.Clipboard().get()[0][0]
        self.assertDoUndoRedo(
            lambda: self.assertEqualEfforts(self.effort1, copiedEffort),
            lambda: (self.assertEffortList(self.originalEffortList),
            self.failIf(command.Clipboard())))
            
    def testCopyMultipleEfforts(self):
        self.copy([self.effort1, self.effort2])
        copiedEfforts = command.Clipboard().get()[0]
        self.assertDoUndoRedo(
            lambda: (self.assertEqualEfforts(self.effort1, copiedEfforts[0]), 
                    self.assertEqualEfforts(self.effort2, copiedEfforts[1])),
            lambda: (self.assertEffortList(self.originalEffortList),
            self.failIf(command.Clipboard())))
     
        
class DragAndDropWithTasksTest(CommandWithChildrenTestCase):
    def dragAndDrop(self, draggedItems, dropItem): # pylint: disable-msg=W0222
        command.DragAndDropTaskCommand(self.taskList, draggedItems, drop=[dropItem]).do()
        
    def testDragAndDropRootTask(self):
        self.taskList.append(self.task2)
        self.dragAndDrop([self.task2], self.task1)
        self.assertDoUndoRedo(
            lambda: self.failUnless(self.task2 in self.task1.children()),
            lambda: self.failIf(self.task2 in self.task1.children()))
            
    def testDontAllowDropOnSelf(self):
        self.dragAndDrop([self.task1], self.task1)
        self.assertDoUndoRedo(lambda: self.failIf(self.task1 in self.task1.children()))
        
    def testDragChildTaskAndDropOnOtherRootTask(self):
        self.dragAndDrop([self.child2], self.task1)
        self.assertDoUndoRedo(
             lambda: (self.failUnless(self.child2 in self.task1.children()),
                     self.failIf(self.child2 in self.parent.children())),
             lambda: (self.failIf(self.child2 in self.task1.children()), 
                     self.failUnless(self.child2 in self.parent.children())))
                     
    def testDragChildAndDropOnOwnParent(self):
        self.dragAndDrop([self.child2], self.parent)
        self.assertDoUndoRedo(
            lambda: self.failUnless(self.child2 in self.parent.children()))
            
    def testDragParentAndDropOnOwnChild(self):
        self.dragAndDrop([self.parent], self.child2) 
        self.assertDoUndoRedo(
            lambda: (self.failUnless(self.child2 in self.parent.children()),
                    self.failIf(self.parent in self.child2.children())))
                    

        
