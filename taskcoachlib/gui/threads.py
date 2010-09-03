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

import wx, threading

wxEVT_INVOKE = wx.NewEventType()


def EVT_INVOKE(win, func):
    win.Connect(wx.ID_ANY, wx.ID_ANY, wxEVT_INVOKE, func)


class InvokeEvent(wx.PyEvent):
    def __init__(self, sync, func, args, kwargs):
        super(InvokeEvent, self).__init__()

        self.SetEventType(wxEVT_INVOKE)

        self.sync = sync
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.event = threading.Event()
        self.result = None


class DeferredCallMixin(object):
    """Use this mixin on wxWindow children and use Invoke to make a
    deferred call to a method from the wx GUI thread."""

    def __init__(self, *args, **kwargs):
        super(DeferredCallMixin, self).__init__(*args, **kwargs)

        EVT_INVOKE(self, self.__OnInvoke)

    def __OnInvoke(self, event):
        event.result = event.func(*event.args, **event.kwargs)
        event.event.set()

    def Invoke(self, sync, func, *args, **kwargs):
        """When called from any thread other than the main GUI thread,
        Invoke(function, *args, **kwargs) will call 'function' from
        the GUI thread, block until it returns, and return its return
        value, or returns immediately if 'sync' is False."""

        event = InvokeEvent(sync, func, args, kwargs)
        wx.PostEvent(self, event)

        if sync:
            event.event.wait()

        return event.result


def synchronized(func):
    """Use this decorator on a class using te DeferredCallMixin to
    make a method automatically called through Invoke."""

    def inner(self, *args, **kwargs):
        return self.Invoke(True, func, self, *args, **kwargs)

    return inner

def synchronizednb(func):
    """Same as synchronized, but the call doesn't block."""

    def inner(self, *args, **kwargs):
        return self.Invoke(False, func, self, *args, **kwargs)

    return inner
