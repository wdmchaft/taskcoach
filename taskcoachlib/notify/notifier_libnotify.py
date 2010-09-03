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

import tempfile, wx, os

from notifier import AbstractNotifier
from taskcoachlib.meta import data

class LibnotifyNotifier(AbstractNotifier):
    def __init__(self):
        super(LibnotifyNotifier, self).__init__()

        try:
            import pynotify
        except ImportError:
            self.__notify = None
        else:
            self.__notify = pynotify
            self.__notify.init(data.name)

    def getName(self):
        return u'libnotify'

    def isAvailable(self):
        return self.__notify is not None

    def notify(self, title, summary, bitmap):
        # Libnotify needs a file, like Snarl.
        fd, filename = tempfile.mkstemp('.png')
        os.close(fd)
        bitmap.SaveFile(filename, wx.BITMAP_TYPE_PNG)
        try:
            n = self.__notify.Notification(title.encode('UTF-8'),
                                           summary.encode('UTF-8'),
                                           filename)
            n.show()
        finally:
            os.remove(filename)


AbstractNotifier.register(LibnotifyNotifier())
