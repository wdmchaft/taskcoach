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
from taskcoachlib import patterns


class StatusBar(wx.StatusBar):
    def __init__(self, parent, viewer):
        super(StatusBar, self).__init__(parent, -1)
        self.SetFieldsCount(2)
        self.parent = parent
        self.viewer = viewer
        self.viewerEventTypes = (viewer.selectEventType(), 
                                 viewer.viewerChangeEventType())
        register = patterns.Publisher().registerObserver
        for eventType in self.viewerEventTypes:
            register(self.onSelect, eventType=eventType, eventSource=viewer)
        self.scheduledStatusDisplay = None
        self.onSelect(None)
        self.wxEventTypes = (wx.EVT_MENU_HIGHLIGHT_ALL, wx.EVT_TOOL_ENTER)
        for eventType in self.wxEventTypes:
            parent.Bind(eventType, self.resetStatusBar)

    def resetStatusBar(self, event):
        ''' Unfortunately, the menu's and toolbar don't restore the
            previous statusbar text after they have displayed their help
            text, so we have to do it by hand. '''
        try:
            toolOrMenuId = event.GetSelection() # for CommandEvent from the Toolbar
        except AttributeError:
            toolOrMenuId = event.GetMenuId() # for MenuEvent
        if toolOrMenuId == -1:
            self._displayStatus()
        event.Skip()

    def onSelect(self, event): # pylint: disable-msg=W0613
        # Give viewer a chance to update first:
        wx.CallAfter(self._displayStatus)

    def _displayStatus(self):
        try:
            status1, status2 = self.viewer.statusMessages()
        except AttributeError:
            return # Viewer container contains no viewers 
        super(StatusBar, self).SetStatusText(status1, 0)
        super(StatusBar, self).SetStatusText(status2, 1)

    def SetStatusText(self, message, pane=0, delay=3000): # pylint: disable-msg=W0221
        if self.scheduledStatusDisplay:
            self.scheduledStatusDisplay.Stop()
        super(StatusBar, self).SetStatusText(message, pane)
        self.scheduledStatusDisplay = wx.FutureCall(delay, self._displayStatus)

    def Destroy(self): # pylint: disable-msg=W0221
        remove = patterns.Publisher().removeObserver
        for eventType in self.viewerEventTypes:
            remove(self.onSelect, eventType=eventType)
        for eventType in self.wxEventTypes:
            self.parent.Unbind(eventType)
        if self.scheduledStatusDisplay:
            self.scheduledStatusDisplay.Stop()
        super(StatusBar, self).Destroy()

