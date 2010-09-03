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
from taskcoachlib import patterns


class ViewerContainer(object):
    ''' ViewerContainer is a container of viewers. It has a containerWidget
        that displays the viewers. The containerWidget can be a notebook or
        an AUI managed frame. The ViewerContainer knows which of its viewers
        is active and dispatches method calls to the active viewer or to the
        first viewer that can handle the method. This allows other GUI 
        components, e.g. menu's, to talk to the ViewerContainer as were
        it a regular viewer. '''
        
    def __init__(self, containerWidget, settings, setting, *args, **kwargs):
        self.containerWidget = containerWidget
        self.bindContainerWidgetEvents()
        self._settings = settings
        self.__setting = setting
        self.viewers = []
        self.__currentPageNumber = 0
        # Prepare for an exception, because this setting used to be a string
        try:
            self.__desiredPageNumber = int(self._settings.get('view', setting))
        except ValueError:
            self.__desiredPageNumber = 0
        super(ViewerContainer, self).__init__(*args, **kwargs)
        
    def isViewerContainer(self):
        return True

    def bindContainerWidgetEvents(self):
        eventsAndHandlers = dict(pageClosedEvent=self.onPageClosed, 
                                 pageChangedEvent=self.onPageChanged)
        for event, handler in eventsAndHandlers.items():
            if hasattr(self.containerWidget, event):
                self.containerWidget.Bind(getattr(self.containerWidget, event),
                    handler)
    
    def __getitem__(self, index):
        return self.viewers[index]

    def addViewer(self, viewer):
        self.containerWidget.AddPage(viewer, viewer.title(), viewer.bitmap())
        self.viewers.append(viewer)
        viewer.widget.Bind(wx.EVT_SET_FOCUS, self.onViewerReceivesFocus)
        if len(self.viewers) - 1 == self.__desiredPageNumber:
            # We need to use CallAfter because the AuiNotebook doesn't allow
            # PAGE_CHANGING events while the window is not active. See 
            # widgets/notebook.py
            wx.CallAfter(self.containerWidget.SetSelection, 
                         self.__desiredPageNumber)
        patterns.Publisher().registerObserver(self.onSelect, 
            eventType=viewer.selectEventType(), eventSource=viewer)

    def onViewerReceivesFocus(self, event):
        event.Skip()
        for viewer in self.viewers:
            if event.EventObject == viewer.widget:
                # Don't activate the viewer immediately, it may cause another
                # AuiManager.Update call which could undock a viewer that is 
                # in the process of being docked to an automatic notebook. 
                wx.CallAfter(self.activateViewer, viewer)
                break

    @classmethod
    def selectEventType(class_):
        return '%s.select'%class_
    
    @classmethod
    def viewerChangeEventType(class_):
        return '%s.viewerChange'%class_
    
    def __getattr__(self, method):
        ''' Return a function that will call the method on the first viewer 
            that both has the requested method and does not raise an exception.
            Start looking in the current viewer. NB: this auto forwarding only 
            works for methods, not for properties. '''
        def findFirstViewer(*args, **kwargs):
            for viewer in [self.activeViewer()] + self.viewers:
                if hasattr(viewer, method):
                    return getattr(viewer, method)(*args, **kwargs)
            else:
                raise AttributeError
        return findFirstViewer

    def activeViewer(self):
        ''' Return the active viewer, i.e. the viewer that has the focus. '''
        # There is no pageChanged event for the AuiManager, so we have
        # to check which pane is active.
        for viewer in self.viewers:
            info = self.containerWidget.manager.GetPane(viewer)
            if info.HasFlag(info.optionActive):
                return viewer
        return self.viewers[self.__currentPageNumber]

    def activateViewer(self, viewerToActivate):
        for viewer in self.viewers:
            info = self.containerWidget.manager.GetPane(viewer)
            info.SetFlag(info.optionActive, viewer==viewerToActivate)
        self.containerWidget.manager.Update()

    def __del__(self):
        pass # Don't forward del to one of the viewers.
    
    def onSelect(self, event):
        patterns.Event(self.selectEventType(), self, *event.values()).send()

    def onPageChanged(self, event):
        self._changePage(event.GetSelection())
        event.Skip()

    def onPageClosed(self, event):
        if hasattr(event, 'GetPane'):
            if event.GetPane().IsToolbar():
                return
            window = event.GetPane().window
        else:
            window = self.containerWidget.GetPage(event.GetSelection())
        if hasattr(window, 'GetPage'):
            # Window is a notebook, close each of its pages
            for pageIndex in range(window.GetPageCount()):
                self._closePage(window.GetPage(pageIndex))
        else:
            # Window is a viewer, close it
            self._closePage(window)
        # Make sure the current pane is a valid pane
        if self.__currentPageNumber >= len(self.viewers):
            self._changePage(0)
        event.Skip()
        
    def _closePage(self, viewer):
        # When closing an AUI managed frame, we get two close events, 
        # be prepared:
        if not viewer in self.viewers:
            return
        self.viewers.remove(viewer)
        viewer.detach()
        setting = viewer.__class__.__name__.lower() + 'count'
        viewerCount = self._settings.getint('view', setting)
        self._settings.set('view', setting, str(viewerCount-1))        
        
    def _changePage(self, pageNumber):
        self.__currentPageNumber = pageNumber        
        self._settings.set('view', self.__setting, str(pageNumber))
        patterns.Event(self.viewerChangeEventType(), self, pageNumber).send()

