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

import wx
import test
from taskcoachlib import gui, config


class WindowTest(test.wxTestCase):
    def setUp(self):
        super(WindowTest, self).setUp()
        self.settings = config.Settings(load=False)
        self.settings.set('window', 'position', '(100, 100)')
        self.tracker = gui.mainwindow.WindowDimensionsTracker(self.frame, self.settings)
        self.section = self.tracker._section
        
    def testInitialPosition(self):
        self.assertEqual(eval(self.settings.get(self.section, 'position')), 
            self.frame.GetPositionTuple())
         
    def testInitialSize(self):
        # See MainWindowTest...
        w, h = self.frame.GetSizeTuple()
        if wx.Platform == '__WXMAC__': 
            h += 29 # pragma: no cover
        self.assertEqual(eval(self.settings.get(self.section, 'size')),
            (w, h))
     
    def testInitialIconizeState(self):
        self.assertEqual(self.settings.getboolean(self.section, 'iconized'),
            self.frame.IsIconized())
            
    def testChangeSize(self):
        self.frame.ProcessEvent(wx.SizeEvent((100, 200)))
        self.assertEqual((100, 200), 
            eval(self.settings.get(self.section, 'size')))
        
    def testMove(self):
        self.frame.ProcessEvent(wx.MoveEvent((200, 200)))
        self.tracker.savePosition()
        #The move is not processed, dunno why:
        self.assertEqual((100, 100), eval(self.settings.get(self.section, 'position')))

