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

import wx, re, sre_constants
from taskcoachlib.widgets import tooltip
from taskcoachlib.i18n import _


class SearchCtrl(tooltip.ToolTipMixin, wx.SearchCtrl):
    def __init__(self, *args, **kwargs):
        self.__callback = kwargs.pop('callback')
        self.__matchCase = kwargs.pop('matchCase', False)
        self.__includeSubItems = kwargs.pop('includeSubItems', False)
        self.__searchDescription = kwargs.pop('searchDescription', False)
        self.__bitmapSize = kwargs.pop('size', (16, 16))
        super(SearchCtrl, self).__init__(*args, **kwargs)
        self.SetSearchMenuBitmap(self.getBitmap('magnifier_glass_dropdown_icon'))
        self.SetSearchBitmap(self.getBitmap('magnifier_glass_icon'))
        self.SetCancelBitmap(self.getBitmap('cross_red_icon'))
        self.__timer = wx.Timer(self)
        self.__recentSearches = []
        self.__maxRecentSearches = 5
        self.__tooltip = tooltip.SimpleToolTip(self)
        self.createMenu()
        self.bindEventHandlers()
        self.onFind(None)
        
    def GetMainWindow(self):
        return self

    def getBitmap(self, bitmap):
        return wx.ArtProvider_GetBitmap(bitmap, wx.ART_TOOLBAR,
                                        self.__bitmapSize)

    def createMenu(self):
        menu = wx.Menu()
        self.__matchCaseMenuItem = menu.AppendCheckItem(wx.ID_ANY, 
            _('&Match case'), _('Match case when filtering'))
        self.__matchCaseMenuItem.Check(self.__matchCase)
        self.__includeSubItemsMenuItem = menu.AppendCheckItem(wx.ID_ANY, 
            _('&Include sub items'), 
            _('Include sub items of matching items in the search results'))
        self.__includeSubItemsMenuItem.Check(self.__includeSubItems)
        self.__searchDescriptionMenuItem = menu.AppendCheckItem(wx.ID_ANY,
            _('&Search description too'),
            _('Search both subject and description'))
        self.__searchDescriptionMenuItem.Check(self.__searchDescription)
        self.SetMenu(menu)
        
    def bindEventHandlers(self):
        for args in [(wx.EVT_TIMER, self.onFind),
                     (wx.EVT_TEXT_ENTER, self.onFind),
                     (wx.EVT_TEXT, self.onFindLater),
                     (wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancel),
                     (wx.EVT_MENU, self.onMatchCaseMenuItem, 
                         self.__matchCaseMenuItem),
                     (wx.EVT_MENU, self.onIncludeSubItemsMenuItem, 
                         self.__includeSubItemsMenuItem),
                     (wx.EVT_MENU, self.onSearchDescriptionMenuItem,
                         self.__searchDescriptionMenuItem)]:
            self.Bind(*args)
        # Precreate menu item ids for the recent searches and bind the event
        # handler for those menu item ids. It's no problem that the actual menu
        # items don't exist yet. 
        self.__recentSearchMenuItemIds = \
            [wx.NewId() for i in range(self.__maxRecentSearches)]
        self.Bind(wx.EVT_MENU_RANGE, self.onRecentSearchMenuItem, 
            id=self.__recentSearchMenuItemIds[0], 
            id2=self.__recentSearchMenuItemIds[-1])

    def setMatchCase(self, matchCase):
        self.__matchCase = matchCase
        self.__matchCaseMenuItem.Check(matchCase)
        
    def setIncludeSubItems(self, includeSubItems):
        self.__includeSubItems = includeSubItems
        self.__includeSubItemsMenuItem.Check(includeSubItems)

    def setSearchDescription(self, searchDescription):
        self.__searchDescription = searchDescription
        self.__searchDescriptionMenuItem.Check(searchDescription)
        
    def isValid(self):
        try:
            re.compile(self.GetValue())
        except sre_constants.error:
            return False
        return True

    def onFindLater(self, event):
        # Start the timer so that the actual filtering will be done
        # only when the user pauses typing (at least 0.5 second)
        self.__timer.Start(500, oneShot=True)

    def onFind(self, event):
        if self.__timer.IsRunning():
            self.__timer.Stop()
        if not self.IsEnabled():
            return
        if not self.isValid():
            self.__tooltip.SetData([(None, 
                [_('This is an invalid regular expression.'), 
                 _('Defaulting to substring search.')])])
            x, y = self.GetParent().ClientToScreenXY(*self.GetPosition())
            w, h = self.GetClientSize()
            self.DoShowTip(x + 3, y + h + 4, self.__tooltip)
        else:
            self.HideTip()
        searchString = self.GetValue()
        if searchString:
            self.rememberSearchString(searchString)
        self.ShowCancelButton(bool(searchString))
        self.__callback(searchString, self.__matchCase, self.__includeSubItems,
                        self.__searchDescription)

    def onCancel(self, event):
        self.SetValue('')
        self.onFind(event)
        event.Skip()
    
    def onMatchCaseMenuItem(self, event):
        self.__matchCase = self._isMenuItemChecked(event)
        self.onFind(event)
        event.Skip()
        
    def onIncludeSubItemsMenuItem(self, event):
        self.__includeSubItems = self._isMenuItemChecked(event)
        self.onFind(event)
        event.Skip()
        
    def onSearchDescriptionMenuItem(self, event):
        self.__searchDescription = self._isMenuItemChecked(event)
        self.onFind(event)
        event.Skip()
        
    def onRecentSearchMenuItem(self, event):
        self.SetValue(self.__recentSearches[event.GetId()-self.__recentSearchMenuItemIds[0]])
        self.onFind(event)
        event.Skip()
                
    def rememberSearchString(self, searchString):
        if searchString in self.__recentSearches:
            self.__recentSearches.remove(searchString)
        self.__recentSearches.insert(0, searchString)
        if len(self.__recentSearches) > self.__maxRecentSearches:
            self.__recentSearches.pop()
        self.updateRecentSearches()
                   
    def updateRecentSearches(self):
        menu = self.GetMenu()
        self.removeRecentSearches(menu)
        self.addRecentSearches(menu)
        
    def removeRecentSearches(self, menu):
        while menu.GetMenuItemCount() > 3:
            item = menu.FindItemByPosition(3)
            menu.DestroyItem(item)

    def addRecentSearches(self, menu):
        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY, _('Recent searches'))
        item.Enable(False)
        for index, searchString in enumerate(self.__recentSearches):
            menu.Append(self.__recentSearchMenuItemIds[index], searchString)
            
    def Enable(self, enable=True):
        ''' When wx.SearchCtrl is disabled it doesn't grey out the buttons,
            so we remove those. '''
        self.SetValue('' if enable else _('Viewer not searchable'))
        super(SearchCtrl, self).Enable(enable)
        self.ShowCancelButton(enable and bool(self.GetValue()))
        self.ShowSearchButton(enable)
        
    def _isMenuItemChecked(self, event):
        # There's a bug in wxPython 2.8.3 on Windows XP that causes 
        # event.IsChecked() to return the wrong value in the context menu.
        # The menu on the main window works fine. So we first try to access the
        # context menu to get the checked state from the menu item itself.
        # This will fail if the event is coming from the window, but in that
        # case we can event.IsChecked() expect to work so we use that.
        try:
            return event.GetEventObject().FindItemById(event.GetId()).IsChecked()
        except AttributeError:
            return event.IsChecked()
        
    def OnBeforeShowToolTip(self, x, y):
        return None
