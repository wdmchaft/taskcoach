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

import test, wx
from taskcoachlib import widgets
import taskcoachlib.thirdparty.aui as aui


class DummyEvent(object):
    def Skip(self):
        pass
    
    
class AUINotebookTest(test.wxTestCase):
    def setUp(self):
        self.notebook = widgets.AUINotebook(self.frame)
        self.addPage('page 1')
        
    def addPage(self, title):
        self.notebook.AddPage(wx.Panel(self.notebook), title)
        
    def closePage(self, index):
        self.notebook.RemovePage(1)
        self.notebook.onClosePage(DummyEvent()) # Fake a page close event being sent
        
    def assertCloseButtonOnActiveTab(self):
        self.failUnless(self.closeButtonOnActiveTab())

    def assertNoCloseButtonOnActiveTab(self):
        self.failIf(self.closeButtonOnActiveTab())
        
    def closeButtonOnActiveTab(self):
        return self.notebook.GetWindowStyleFlag() & aui.AUI_NB_CLOSE_ON_ACTIVE_TAB
        
    def testTabHasNoCloseButtonAfterFirstPageAdded(self):
        self.assertNoCloseButtonOnActiveTab()

    def testTabHasCloseButtonAfterSecondPageAdded(self):
        self.addPage('page 2')
        self.assertCloseButtonOnActiveTab()

    def testTabStillHasCloseButtonAfterThirdPageAdded(self):
        self.addPage('page 2')
        self.addPage('page 3')
        self.assertCloseButtonOnActiveTab()

    def testTabHasNoCloseButtonAfterSecondPageClosed(self):
        self.addPage('page 2')
        self.closePage(1)
        self.assertNoCloseButtonOnActiveTab()

    def testTabHasNoCloseButtonAfterSecondAndThirdPageClosed(self):
        self.addPage('page 2')
        self.addPage('page 3')
        self.closePage(2)
        self.closePage(1)
        self.assertNoCloseButtonOnActiveTab()
        