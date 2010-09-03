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

import wx, sys
import test
from taskcoachlib import gui, command, config, persistence
from taskcoachlib.domain import category, note, attachment


class CategoryEditorTestCase(test.wxTestCase):
    def setUp(self):
        super(CategoryEditorTestCase, self).setUp()
        self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.categories = self.taskFile.categories()
        self.categories.extend(self.createCategories())
        self.editor = self.createEditor()
        
    def createEditor(self):
        return gui.dialog.editor.CategoryEditor(self.frame, self.createCommand(),
            self.settings, self.categories, self.taskFile, raiseDialog=False)

    def tearDown(self):
        # CategoryEditor uses CallAfter for setting the focus, make sure those 
        # calls are dealt with, otherwise they'll turn up in other tests
        if '__WXMAC__' not in wx.PlatformInfo and ('__WXMSW__' not in wx.PlatformInfo or sys.version_info < (2, 5)):
            wx.Yield() # pragma: no cover 
        super(CategoryEditorTestCase, self).tearDown()
        
    def createCommand(self):
        raise NotImplementedError # pragma: no cover
    
    def createCategories(self):
        return []

    def setSubject(self, newSubject):
        self.editor._interior[0].setSubject(newSubject)

    def setDescription(self, newDescription):
        self.editor._interior[0].setDescription(newDescription)
        
        
class NewCategoryTest(CategoryEditorTestCase):
    def createCommand(self):
        newCategoryCommand = command.NewCategoryCommand(self.categories)
        self.category = newCategoryCommand.items[0] # pylint: disable-msg=W0201
        return newCategoryCommand

    def testCreate(self):
        # pylint: disable-msg=W0212
        self.assertEqual('New category', self.editor._interior[0]._subjectEntry.GetValue())

    def testOk(self):
        self.setSubject('Done')
        self.editor.ok()
        self.assertEqual('Done', self.category.subject())

    def testCancel(self):
        self.setSubject('Done')
        self.editor.cancel()
        self.assertEqual('New category', self.category.subject())

    def testSetDescription(self):
        self.setDescription('Description')
        self.editor.ok()
        self.assertEqual('Description', self.category.description())
        
    def testAddNote(self):
        self.editor._interior[1].notes.append(note.Note(subject='New note'))
        self.editor.ok()
        self.assertEqual(1, len(self.category.notes()))


class NewSubCategoryTest(CategoryEditorTestCase):
    def createCommand(self):
        newSubCategoryCommand = command.NewSubCategoryCommand(self.categories, 
                                                              [self.category])
        self.subCategory = newSubCategoryCommand.items[0] # pylint: disable-msg=W0201
        return newSubCategoryCommand

    def createCategories(self):
        self.category = category.Category('Category') # pylint: disable-msg=W0201
        return [self.category]

    def testOk(self):
        self.editor.ok()
        self.assertEqual([self.subCategory], self.category.children())

    def testCancel(self):
        self.editor.cancel()
        self.assertEqual([], self.category.children())


class EditCategoryTest(CategoryEditorTestCase):
    def setUp(self):
        super(EditCategoryTest, self).setUp()
        self.setSubject('Done')

    def createCommand(self):
        return command.EditCategoryCommand(self.categories, [self.category])

    # pylint: disable-msg=E1101
    
    def createCategories(self):
        # pylint: disable-msg=W0201
        self.category = category.Category('Category to edit')
        self.attachment = attachment.FileAttachment('some attachment')
        self.category.addAttachments(self.attachment)
        return [self.category]

    def testOk(self):
        self.editor.ok()
        self.assertEqual('Done', self.category.subject())

    def testCancel(self):
        self.editor.cancel()
        self.assertEqual('Category to edit', self.category.subject())

    def testAddAttachment(self):
        self.editor._interior[2].viewer.onDropFiles(None, ['filename'])
        self.editor.ok()
        self.failUnless('filename' in [att.location() for att in self.category.attachments()])
        self.failUnless('filename' in [att.subject() for att in self.category.attachments()])
        
    def testRemoveAttachment(self):
        self.editor._interior[2].viewer.presentation().removeItems([self.attachment])
        self.editor.ok()
        self.assertEqual([], self.category.attachments())
