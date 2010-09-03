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
 
''' These are unittests of wxPython functionality. Of course, the goal is
not to test all wxPython functions, but rather to document platform
inconsistencies or surprising behaviour. ''' # pylint: disable-msg=W0105

import wx
import test


class TextCtrlTest(test.wxTestCase):
    def testClearEmitsNoEventOnMacOSX(self):
        self.clearTextCausesEvent = False # pylint: disable-msg=W0201
        textCtrl = wx.TextCtrl(self.frame)
        textCtrl.Bind(wx.EVT_TEXT, self.onTextChanged)
        textCtrl.Clear()
        if '__WXMAC__' in wx.PlatformInfo: # pragma: no cover
            self.failIf(self.clearTextCausesEvent)
        else:
            self.failUnless(self.clearTextCausesEvent)

    def onTextChanged(self, event): # pylint: disable-msg=W0613
        self.clearTextCausesEvent = True

