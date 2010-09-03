'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

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


class SpinCtrl(wx.SpinCtrl):
    # Can't use sys.maxint for the range because Python and wxPython disagree 
    # on what the maximum integer is on Suse 10.0 x86_64. Using sys.maxint 
    # will cause an Overflow exception, so we use a constant:
    maxRange = 2147483647
    
    def __init__(self, *args, **kwargs):
        kwargs['style'] = wx.SP_ARROW_KEYS
        if 'min' not in kwargs:
            kwargs['min'] = -self.maxRange
        if 'max' not in kwargs:
            kwargs['max'] = self.maxRange
        super(SpinCtrl, self).__init__(*args, **kwargs)
        if '__WXGTK__' != wx.Platform:
            # on wxGtk, entering text is not possible anyway, so no need to deal
            # with it.
            self.Bind(wx.EVT_SPINCTRL, self.onValueChanged)

    def onValueChanged(self, event):
        ''' wx.SpinCtrl resets invalid values (e.g. text or an empty string)
            to wx.SpinCtrl.GetMin(). The minimum priority value is a large
            (negative) number by default. It makes more sense to reset the 
            SpinCtrl to 0 in case of invalid input. '''
        if self.GetValue() == -self.maxRange:
            wx.CallAfter(self.SetValue, 0)
        event.Skip()

