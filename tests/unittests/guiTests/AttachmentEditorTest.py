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

import wx, sys
import test
from taskcoachlib import gui, command, config, persistence
from taskcoachlib.domain import note, attachment


class AttachmentEditorTestCase(test.wxTestCase):
    def setUp(self):
        super(AttachmentEditorTestCase, self).setUp()
        self.taskFile = persistence.TaskFile()
        self.attachments = attachment.AttachmentList()
        self.attachments.extend(self.createAttachments())
        self.settings = config.Settings(load=False)
        self.editor = self.createEditor()
        
    def createEditor(self):
        return gui.dialog.editor.AttachmentEditor(self.frame, self.createCommand(),
            self.settings, self.attachments, self.taskFile, raiseDialog=False)

    def tearDown(self):
        # AttachmentEditor uses CallAfter for setting the focus, make sure those 
        # calls are dealt with, otherwise they'll turn up in other tests
        if '__WXMAC__' not in wx.PlatformInfo and ('__WXMSW__' not in wx.PlatformInfo or sys.version_info < (2, 5)):
            wx.Yield() # pragma: no cover 
        super(AttachmentEditorTestCase, self).tearDown()
        
    def createCommand(self):
        raise NotImplementedError # pragma: no cover
    
    def createAttachments(self):
        return []

    def setSubject(self, newSubject, index=0):
        self.editor[index][0].setSubject(newSubject)

    def setDescription(self, newDescription, index=0):
        self.editor[index][0].setDescription(newDescription)
        
        
class NewAttachmentTest(AttachmentEditorTestCase):
    def createCommand(self):
        newAttachmentCommand = command.NewAttachmentCommand(self.attachments)
        self.attachment = newAttachmentCommand.items[0] # pylint: disable-msg=W0201
        return newAttachmentCommand

    def testCreate(self):
        # pylint: disable-msg=W0212
        self.assertEqual('New attachment', self.editor[0][0]._subjectEntry.GetValue())

    def testOk(self):
        self.setSubject('Done')
        self.editor.ok()
        self.assertEqual('Done', self.attachment.subject())

    def testCancel(self):
        self.setSubject('Done')
        self.editor.cancel()
        self.assertEqual('New attachment', self.attachment.subject())

    def testSetDescription(self):
        self.setDescription('Description')
        self.editor.ok()
        self.assertEqual('Description', self.attachment.description())
        
    def testAddNote(self):
        self.editor[0][1].notes.append(note.Note(subject='New note'))
        self.editor.ok()
        self.assertEqual(1, len(self.attachment.notes()))
