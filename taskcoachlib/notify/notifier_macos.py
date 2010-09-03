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

import sys, os, struct

if struct.calcsize('L') == 8:
    _subdir = 'IA64'
else:
    _subdir = 'IA32'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bin.in', 'macos', _subdir))

from taskcoachlib.thirdparty.Growl import GrowlNotifier, Image
from taskcoachlib import meta
from notifier import AbstractNotifier


class TaskCoachGrowlNotifier(GrowlNotifier):
    applicationName = meta.name
    notifications = [u'Reminder']


class GrowlNotifier(AbstractNotifier):
    def __init__(self):
        try:
            self._notifier = TaskCoachGrowlNotifier(applicationIcon=Image.imageWithIconForCurrentApplication())
            self._notifier.register()
        except:
            self._available = False
        else:
            self._available = True

    def getName(self):
        return 'Growl'

    def isAvailable(self):
        return self._available

    def notify(self, title, summary, bitmap, **kwargs):
        # The bitmap is not actually used here...
        self._notifier.notify(noteType=u'Reminder', title=title, description=summary,
                              sticky=True)


AbstractNotifier.register(GrowlNotifier())
