'''
Task Coach - Your friendly task manager
Copyright (C) 2010 Jerome Laheurte <fraca7@free.fr>

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

from notifier import AbstractNotifier
import snarl, tempfile, os, wx


class SnarlNotifier(AbstractNotifier):
    def getName(self):
        return u'Snarl'

    def isAvailable(self):
        return bool(snarl.snGetVersion())

    def notify(self, title, summary, bitmap):
        # Hum. Snarl needs a file.
        fd, filename = tempfile.mkstemp('.bmp')
        os.close(fd)
        bitmap.SaveFile(filename, wx.BITMAP_TYPE_PNG)
        try:
            snarl.snShowMessage(title, summary, iconPath=filename)
        finally:
            os.remove(filename)


AbstractNotifier.register(SnarlNotifier())
