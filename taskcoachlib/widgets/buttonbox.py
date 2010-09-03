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
from taskcoachlib.i18n import _


class ButtonBox(wx.Panel):
    stockItems = {_('OK'): wx.ID_OK, _('Cancel'): wx.ID_CANCEL }

    def __init__(self, parent, *buttons, **kwargs):
        orientation = kwargs.pop('orientation', wx.HORIZONTAL)
        self.__borderWidth = kwargs.pop('borderWidth', 5)
        super(ButtonBox, self).__init__(parent, -1)
        self.__sizer = wx.BoxSizer(orientation)
        self.__buttons = {}
        for text, callback in buttons:
            self.createButton(text, callback)    
        self.SetSizerAndFit(self.__sizer)
        
    def __getitem__(self, buttonLabel):
        return self.__buttons[buttonLabel]

    def createButton(self, text, callback):
        id = self.stockItems.get(text, -1)
        self.__buttons[text] = button = wx.Button(self, id, text)
        if id == wx.ID_OK:
            button.SetDefault()
        button.Bind(wx.EVT_BUTTON, callback)
        self.__sizer.Add(button, border=self.__borderWidth, flag=wx.ALL|wx.EXPAND)
        
    def setDefault(self, buttonText):
        self.__buttons[buttonText].SetDefault()
              
    def enable(self, buttonText):
        self.__buttons[buttonText].Enable()
        
    def disable(self, buttonText):
        self.__buttons[buttonText].Disable()
        
    def buttonLabels(self):
        return self.__buttons.keys()
