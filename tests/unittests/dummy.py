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
from taskcoachlib import widgets, patterns, persistence, gui


class DummyWidget(wx.Frame):
    def __init__(self, viewer):
        super(DummyWidget, self).__init__(viewer)
        self.viewer = viewer

    def curselection(self):
        return []

    def GetItemCount(self):
        return len(self.viewer.presentation())

    def RefreshAllItems(self, *args, **kwargs):
        pass

    def IsAutoResizing(self):
        return False
        

class DummyUICommand(gui.uicommand.UICommand):
    bitmap = 'undo'
    section = 'view'
    setting = 'setting'

    def onCommandActivate(self, event):
        self.activated = True


class ViewerWithDummyWidget(gui.viewer.base.Viewer):
    defaultTitle = 'ViewerWithDummyWidget'
    defaultBitmap = ''
    
    def domainObjectsToView(self):
        return self.taskFile.tasks()
    
    def createWidget(self):
        self._columns = self._createColumns()
        return DummyWidget(self)

    def _createColumns(self):
        return []
    
    
class TaskFile(persistence.TaskFile):
    raiseIOError = False
    
    def load(self, *args, **kwargs):
        if self.raiseIOError:
            raise IOError
        
    merge = save = saveas = load
    

class MainWindow:
    showFindDialog = None
