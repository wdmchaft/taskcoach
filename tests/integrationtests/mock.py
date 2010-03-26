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

from taskcoachlib import application
from taskcoachlib.domain import task


class MockWxApp(object):
    def SetAppName(self, *args, **kwargs):
        pass

    def SetVendorName(self, *args, **kwargs):
        pass

    
class App(application.Application):
    def __init__(self, args=None): # pylint: disable-msg=W0231
        self._options = None
        self._args = args or []
        self.wxApp = MockWxApp()
        self.init()

    def init(self): # pylint: disable-msg=W0221
        super(App, self).init(loadSettings=False, loadTaskFile=False)

    def addTasks(self):
        # pylint: disable-msg=W0201
        self.parent = task.Task('Parent')
        self.child = task.Task('Child')
        self.parent.addChild(self.child)
        self.taskFile.tasks().extend([self.parent])


