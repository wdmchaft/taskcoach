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

import test, wx
from taskcoachlib import meta, application


class AppTests(test.TestCase):
    def testAppProperties(self):
        # Normally I prefer one assert per test, but creating the app is
        # expensive, so we do all the queries in one test method.
        application.Application(loadSettings=False, loadTaskFile=False)
        wxApp = wx.GetApp()
        self.assertEqual(meta.name, wxApp.GetAppName())
        self.assertEqual(meta.author, wxApp.GetVendorName())
