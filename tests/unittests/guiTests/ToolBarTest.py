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
from unittests import dummy
from taskcoachlib import gui
 

class ToolBar(gui.toolbar.ToolBar):
    def uiCommands(self):
        return []


class ToolBarTest(test.wxTestCase):
    def testAppendUICommand(self):
        gui.init()
        toolbar = ToolBar(self.frame)
        uiCommand = dummy.DummyUICommand(menuText='undo', bitmap='undo')
        toolId = toolbar.appendUICommand(uiCommand)
        self.assertNotEqual(wx.NOT_FOUND, toolbar.GetToolPos(toolId))


class ToolBarSizeTest(test.wxTestCase):
    def testSizeDefault(self):
        self.createToolBarAndTestSize(None, (32, 32))

    def testSizeSmall(self):
        self.createToolBarAndTestSize((16, 16))

    def testSizeMedium(self):
        self.createToolBarAndTestSize((22, 22))

    def testSizeBig(self):
        self.createToolBarAndTestSize((32, 32))

    def createToolBarAndTestSize(self, size, expectedSize=None):
        toolbarArgs = [self.frame]
        if size:
            toolbarArgs.append(size)
        toolbar = ToolBar(*toolbarArgs)
        if not expectedSize:
            expectedSize = size
        self.assertEqual(wx.Size(*expectedSize), toolbar.GetToolBitmapSize())
