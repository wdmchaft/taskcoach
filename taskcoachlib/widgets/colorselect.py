'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>

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

import wx, wx.lib.colourselect

class ColorSelect(wx.lib.colourselect.ColourSelect):            
    def MakeBitmap(self):
        ''' This code was copied and adapted from 
            ColourSelect.MakeBitmap. '''
        bdr = 8
        width, height = self.GetSize()

        # yes, this is weird, but it appears to work around a bug in wxMac
        if "wxMac" in wx.PlatformInfo and width == height:
            height -= 1

        bmp = wx.EmptyBitmap(width-bdr, height-bdr)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        dc.SetFont(self.GetFont())
        label = self.GetLabel()
        # Just make a little colored bitmap
        dc.SetBackground(wx.Brush(wx.TreeCtrl.GetClassDefaultAttributes().colBg))
        dc.Clear()

        if label:
            # Add a label to it
            dc.SetTextForeground(self.colour)
            dc.DrawLabel(label, (0,0, width-bdr, height-bdr),
                         wx.ALIGN_CENTER)

        dc.SelectObject(wx.NullBitmap)
        return bmp

