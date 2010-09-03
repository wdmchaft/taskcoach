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

from taskcoachlib import gui, config
import test


class Event(object):
    def Skip(self):
        pass


class VersionDialogTest(test.TestCase):
    def setUp(self):
        self.settings = config.Settings(load=False)
        self.dialog = gui.dialog.VersionDialog(None, version='0.0', settings=self.settings)

    def testCreateAndClose(self):
        self.dialog.onClose(Event())
        self.failUnless(self.settings.getboolean('version', 'notify'))
        
    def testNoMoreNotifications(self):
        self.dialog.check.SetValue(False)
        self.dialog.onClose(Event())
        self.failIf(self.settings.getboolean('version', 'notify'))