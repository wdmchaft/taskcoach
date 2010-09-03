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

import win32gui, win32con
from taskcoachlib.powermgt.base import PowerStateMixinBase

class PowerStateMixin(PowerStateMixinBase):
    def __init__(self, *args, **kwargs):
        super(PowerStateMixin, self).__init__(*args, **kwargs)

        self.__oldProc = win32gui.SetWindowLong(self.GetHandle(),
                                                win32con.GWL_WNDPROC,
                                                self.__WndProc)

    def __WndProc(self, hWnd, msg, wParam, lParam):
        if msg == win32con.WM_DESTROY:
            win32api.SetWindowLong(self.GetHandle(),
                                   win32con.GWL_WNDPROC,
                                   self.__oldProc)

        if msg == win32con.WM_POWERBROADCAST:
            if wParam == win32con.PBT_APMSUSPEND:
                self.OnPowerState(self.POWEROFF)
            elif wParam == win32con.PBT_APMRESUMESUSPEND:
                self.OnPowerState(self.POWERON)

        return win32gui.CallWindowProc(self.__oldProc,
                                       hWnd, msg, wParam, lParam)
