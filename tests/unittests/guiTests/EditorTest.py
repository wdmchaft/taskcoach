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

import wx
import test
from taskcoachlib import gui, command, config, persistence
from taskcoachlib.domain import task


class EditorWithCommandUnderTest(gui.dialog.editor.EditorWithCommand):
    def __init__(self, *args, **kwargs):
        super(EditorWithCommandUnderTest, self).__init__(*args, **kwargs)
        self.cancelCalled = False
        
    def addPage(self, item):
        page = wx.Panel(self)
        page.item = item
        self._interior.AddPage(page, 'Title')
        
    def setFocusOnFirstEntry(self):
        pass
    
    def cancel(self, *args, **kwargs):
        super(EditorWithCommandUnderTest, self).cancel(*args, **kwargs)
        self.cancelCalled = True
    

class EditorTestCase(test.wxTestCase):
    def setUp(self):
        super(EditorTestCase, self).setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.taskFile = persistence.TaskFile()
        self.taskList = self.taskFile.tasks()
        self.task = task.Task('task')
        self.taskList.append(self.task)
        self.editor = self.createEditor()
        
    def createEditor(self):
        return EditorWithCommandUnderTest(self.frame, 
            self.createCommand(), self.taskList, raiseDialog=False)
        
    def createCommand(self):
        return command.EditTaskCommand(self.taskList, self.taskList)

    def testCloseEditorWhenItemIsDeleted(self):
        self.failIf(self.editor.cancelCalled)
        self.taskList.remove(self.task)
        self.failUnless(self.editor.cancelCalled)
        