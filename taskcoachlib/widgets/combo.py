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

import wx, wx.combo

class ListCtrlComboPopup(wx.ListCtrl, wx.combo.ComboPopup):
        
    def __init__(self):        
        # Since we are using multiple inheritance, and don't know yet
        # which window is to be the parent, we'll do 2-phase create of
        # the ListCtrl instead, and call its Create method later in
        # our Create method.  (See Create below.)
        self.PostCreate(wx.PreListCtrl())
        # Also init the ComboPopup base class.
        wx.combo.ComboPopup.__init__(self)

    def Create(self, parent):
        # Create the popup child control. Return True for success.
        wx.ListCtrl.Create(self, parent,
            style=wx.LC_REPORT|wx.LC_NO_HEADER|wx.LC_SINGLE_SEL|wx.SIMPLE_BORDER)
        self.InsertColumn(0, "")
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        return True
        
    def AddItem(self, text):
        self.InsertStringItem(self.GetItemCount(), text)

    def OnLeftDown(self, event):
        item = self.HitTest(event.GetPosition())[0]
        if item >= 0:
            self.Select(item)
            self.currentItem = item
        self.Dismiss()

    def Init(self):
        self.currentItem = -1

    def GetControl(self):
        return self

    def SetStringValue(self, value):
        ''' Try to select the given item. '''
        index = self.FindItem(-1, value)
        if index != wx.NOT_FOUND:
            self.Select(index)
            self.EnsureVisible(index)

    def GetStringValue(self):
        ''' Return a string representation of the current item. '''
        currentItem = self.currentItem
        return self.GetItemText(currentItem) if currentItem >= 0 else ''


class ComboCtrl(wx.combo.ComboCtrl):
    def __init__(self, parent, value, choices, size):
        super(ComboCtrl, self).__init__(parent, size=size)
        # Create a Popup
        popup = ListCtrlComboPopup()
        # Associate them with each other.  This also triggers the
        # creation of the ListCtrl.
        self.SetPopupControl(popup)
        # Add some items to the listctrl.
        for choice in choices:
            popup.AddItem(choice)
        self.SetValue(value)