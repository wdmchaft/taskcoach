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

import test
from unittests import dummy
from taskcoachlib import gui, config, widgets, patterns, persistence
from taskcoachlib.domain import task


class DummyPane(object):
    def __init__(self, window):
        self.window = window
        
    def IsToolbar(self):
        return False
        
        
class DummyEvent(object):
    def __init__(self, selection=0, window=None):
        self.__selection = selection
        self.__pane = DummyPane(window)
    
    def GetSelection(self):
        return self.__selection
        
    Selection = property(GetSelection)
    
    def GetPane(self):
        return self.__pane

    def Skip(self):
        pass


class MainWindow(gui.MainWindow):
    def canCreateTaskBarIcon(self):
        return False
    
    
class ViewerContainerTest(test.wxTestCase):
    def setUp(self):
        super(ViewerContainerTest, self).setUp()
        self.events = []
        task.Task.settings = self.settings = config.Settings(load=False)
        self.settings.set('view', 'viewerwithdummywidgetcount', '2', new=True)
        self.taskFile = persistence.TaskFile()
        self.mainWindow = MainWindow(None, self.taskFile, self.settings)
        self.container = gui.viewer.ViewerContainer(self.mainWindow, 
            self.settings, 'mainviewer')
        self.viewer1 = self.createViewer('taskviewer1')
        self.container.addViewer(self.viewer1)
        self.viewer2 = self.createViewer('taskviewer2')
        self.container.addViewer(self.viewer2)

    def createViewer(self, settingsSection):
        self.settings.add_section(settingsSection)
        return dummy.ViewerWithDummyWidget(self.mainWindow, self.taskFile, 
            self.settings, settingsSection=settingsSection)
            
    def onEvent(self, event):
        self.events.append(event)
    
    def testCreate(self):
        self.assertEqual(0, self.container.size())

    def testAddTask(self):
        self.taskFile.tasks().append(task.Task())
        self.assertEqual(1, self.container.size())

    def testDefaultActiveViewer(self):
        self.assertEqual(self.viewer1, self.container.activeViewer())
        
    def testChangePage_ChangesActiveViewer(self):
        self.container.onPageChanged(DummyEvent(1))
        self.assertEqual(self.viewer2, self.container.activeViewer())

    def testChangePage_SavesActiveViewerInSettings(self):
        self.container.onPageChanged(DummyEvent(1))
        self.assertEqual(1, self.settings.getint('view', 'mainviewer'))

    def testChangePage_NotifiesObserversAboutNewActiveViewer(self):
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType=self.container.viewerChangeEventType(), 
            eventSource=self.container)
        self.container.onPageChanged(DummyEvent(1))
        self.failUnless(self.events)
        
    def testCloseViewer_RemovesViewerFromContainer(self):
        self.container.onPageClosed(DummyEvent(window=self.viewer1))
        self.assertEqual([self.viewer2], self.container.viewers)
        
    def testCloseViewer_RemovesViewerFromSettings(self):
        self.container.onPageClosed(DummyEvent(window=self.viewer1))
        self.assertEqual(1, self.settings.getint('view', 
            'viewerwithdummywidgetcount'))
        
    def testCloseViewer_ChangesActiveViewer(self):
        self.container.onPageChanged(DummyEvent(1))
        self.container.onPageClosed(DummyEvent(window=self.viewer2))
        self.assertEqual(self.viewer1, self.container.activeViewer())
        
    def testCloseViewer_SavesActiveViewerInSettings(self):
        self.container.onPageChanged(DummyEvent(1))
        self.container.onPageClosed(DummyEvent(window=self.viewer2))
        self.assertEqual(0, self.settings.getint('view', 'mainviewer'))

    def testCloseViewer_NotifiesObserversAboutNewActiveViewer(self):
        self.container.onPageChanged(DummyEvent(1))
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType=self.container.viewerChangeEventType(), 
            eventSource=self.container)
        self.container.onPageClosed(DummyEvent(window=self.viewer2))
        self.failUnless(self.events)

