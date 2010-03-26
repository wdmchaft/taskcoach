'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>
Copyright (C) 2007 Jerome Laheurte <fraca7@free.fr>

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

import wx, uicommand


class ToolBar(wx.ToolBar, uicommand.UICommandContainerMixin):
    def __init__(self, window, size=(32, 32)):
        self.__window = window
        super(ToolBar, self).__init__(window, style=wx.TB_FLAT|wx.TB_NODIVIDER)
        self.SetToolBitmapSize(size) 
        if '__WXMAC__' in wx.PlatformInfo:
            # Extra margin needed because the search control is too high
            self.SetMargins((0, 7)) 
        self.appendUICommands(*self.uiCommands())
        self.Realize()

    def uiCommands(self):
        return self.__window.getToolBarUICommands()

    def AppendSeparator(self):
        ''' This little adapter is needed for 
        uicommand.UICommandContainerMixin.appendUICommands'''
        self.AddSeparator()

    def appendUICommand(self, uiCommand):
        return uiCommand.appendToToolBar(self)

