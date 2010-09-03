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
import taskcoachlib.thirdparty.aui as aui


class AuiManagedFrameWithDynamicCenterPane(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(AuiManagedFrameWithDynamicCenterPane, self).__init__(*args, **kwargs)
        self.manager = aui.AuiManager(self, 
            aui.AUI_MGR_DEFAULT|aui.AUI_MGR_ALLOW_ACTIVE_PANE)
        self.manager.SetAutoNotebookStyle(aui.AUI_NB_BOTTOM|aui.AUI_NB_CLOSE_ON_ACTIVE_TAB|aui.AUI_NB_SUB_NOTEBOOK)
        self.bindEvents()

    def bindEvents(self):
        for eventType in aui.EVT_AUI_PANE_CLOSE, aui.EVT_AUI_PANE_FLOATING:
           self.manager.Bind(eventType, self.onPaneClosingOrFloating)

    def onPaneClosingOrFloating(self, event):
        pane = event.GetPane()
        dockedPanes = self.dockedPanes()
        if self.isCenterPane(pane) and len(dockedPanes) == 1:
            event.Veto() 
        else:
            event.Skip() 
            if self.isCenterPane(pane):                
                dockedPanes.remove(pane)
                dockedPanes[0].Center()
                
    def addPane(self, window, caption, name):
        paneInfo = aui.AuiPaneInfo()
        paneInfo = paneInfo.CloseButton(True).Floatable(True).\
            Name(name).Caption(caption).Right().\
            FloatingSize((300,200)).BestSize((200,200)).\
            CaptionVisible().MaximizeButton().DestroyOnClose()
        if not self.dockedPanes():
            paneInfo = paneInfo.Center()
        self.manager.AddPane(window, paneInfo)
        self.manager.Update()
   
    def dockedPanes(self):
        return [pane for pane in self.manager.GetAllPanes() \
                if not pane.IsToolbar() and not pane.IsFloating() \
                and not pane.IsNotebookPage()]

    @staticmethod
    def isCenterPane(pane):
        return pane.dock_direction_get() == aui.AUI_DOCK_CENTER
