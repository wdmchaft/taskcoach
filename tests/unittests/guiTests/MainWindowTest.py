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

import wx, test
from taskcoachlib import gui, config, persistence, meta


class MockViewer(wx.Frame):
    def title(self):
        return ''
    
    def bitmap(self):
        return ''
    
    def settingsSection(self):
        return 'taskviewer'
    
    def selectEventType(self):
        return ''


class MainWindowUnderTest(gui.MainWindow):
    def createWindowComponents(self):
        # Create only the window components we really need for the tests
        self.createViewerContainer()
        self.viewer.addViewer(MockViewer(None))
        self.createStatusBar()
    

class DummyIOController(object):
    def needSave(self, *args, **kwargs): # pylint: disable-msg=W0613
        return False # pragma: no cover


class MainWindowTestCase(test.wxTestCase):
    def setUp(self):
        super(MainWindowTestCase, self).setUp()
        self.settings = config.Settings(load=False)
        self.setSettings()
        self.taskFile = persistence.TaskFile()
        self.mainwindow = MainWindowUnderTest(DummyIOController(),
            self.taskFile, self.settings)
        
    def setSettings(self):
        pass

    def tearDown(self):
        del self.mainwindow
        super(MainWindowTestCase, self).tearDown()
        
        
class MainWindowTest(MainWindowTestCase):
    def testStatusBar_Show(self):
        self.settings.set('view', 'statusbar', 'True')
        self.failUnless(self.mainwindow.GetStatusBar().IsShown())

    def testStatusBar_Hide(self):
        self.settings.set('view', 'statusbar', 'False')
        self.failIf(self.mainwindow.GetStatusBar().IsShown())

    def testTitle_Default(self):
        self.assertEqual(meta.name, self.mainwindow.GetTitle())
        
    def testTitle_AfterFilenameChange(self):
        self.taskFile.setFilename('New filename')
        self.assertEqual('%s - %s'%(meta.name, self.taskFile.filename()), 
            self.mainwindow.GetTitle())

        

class MainWindowMaximizeTestCase(MainWindowTestCase):
    maximized = 'Subclass responsibility'
    
    def setUp(self):
        super(MainWindowMaximizeTestCase, self).setUp()
        self.mainwindow.Show() # Or IsMaximized() returns always False...
        
    def setSettings(self):
        self.settings.setboolean('window', 'maximized', self.maximized)


class MainWindowNotMaximizedTest(MainWindowMaximizeTestCase):
    maximized = False
    
    def testCreate(self):
        self.failIf(self.mainwindow.IsMaximized())

    @test.skipOnPlatform('__WXGTK__', '__WXMAC__')
    def testMaximize(self): # pragma: no cover
        # Skipping this test under wxGTK. I don't know how it managed
        # to pass before but according to
        # http://trac.wxwidgets.org/ticket/9167 and to my own tests,
        # EVT_MAXIMIZE is a noop under this platform.
        self.mainwindow.Maximize()
        wx.Yield()
        self.failUnless(self.settings.getboolean('window', 'maximized'))


class MainWindowMaximizedTest(MainWindowMaximizeTestCase):
    maximized = True

    @test.skipOnPlatform('__WXMAC__')
    def testCreate(self):
        self.failUnless(self.mainwindow.IsMaximized()) # pragma: no cover


class MainWindowIconizedTest(MainWindowTestCase):
    def setUp(self):
        super(MainWindowIconizedTest, self).setUp()        
        if '__WXGTK__' == wx.Platform:
            wx.SafeYield() # pragma: no cover
            
    def setSettings(self):
        self.settings.set('window', 'starticonized', 'Always')
        
    def expectedHeight(self):
        height = 500
        if '__WXMAC__' == wx.Platform:
            height -= 29 # pragma: no cover
        return height
    
    @test.skipOnPlatform('__WXGTK__', '__WXMAC__') # Test fails on Fedora and Mac OS X, don't know why nor how to fix it    
    def testIsIconized(self):
        self.failUnless(self.mainwindow.IsIconized()) # pragma: no cover
                        
    def testWindowSize(self):
        self.assertEqual((700, self.expectedHeight()), 
                         eval(self.settings.get('window', 'size')))
        
    def testWindowSizeShouldnotChangeWhenReceivingChangeSizeEvent(self):
        event = wx.SizeEvent((100, 20))
        process = self.mainwindow.ProcessEvent
        if '__WXGTK__' == wx.Platform:
            wx.CallAfter(process, event) # pragma: no cover
        else:
            process(event) # pragma: no cover
        self.assertEqual((700, self.expectedHeight()),
                         eval(self.settings.get('window', 'size')))

