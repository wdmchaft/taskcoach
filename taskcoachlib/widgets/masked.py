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
from wx.lib import masked
 

class FixOverwriteSelection(object):
    def _SetSelection(self, start, end):
        if '__WXGTK__' == wx.Platform:
            # By exchanging the start and end parameters we make sure that the 
            # cursor is at the start of the field so that typing overwrites the 
            # current field instead of moving to the next field:
            start, end = end, start
        super(FixOverwriteSelection, self)._SetSelection(start, end)


class TextCtrl(FixOverwriteSelection, masked.TextCtrl):
    pass


class NumCtrl(FixOverwriteSelection, masked.NumCtrl):
    pass

