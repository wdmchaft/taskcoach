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
import draganddrop, frame
import taskcoachlib.thirdparty.aui as aui
import taskcoachlib.thirdparty.flatnotebook as fnb


class GridCursor:
    ''' Utility class to help when adding controls to a GridBagSizer. '''
    
    def __init__(self, columns):
        self.__columns = columns
        self.__nextPosition = (0, 0)
    
    def __updatePosition(self, colspan):
        ''' Update the position of the cursor, taking colspan into account. '''
        row, column = self.__nextPosition
        if column == self.__columns - colspan:
            row += 1
            column = 0
        else:
            column += colspan
        self.__nextPosition = (row, column)
                    
    def next(self, colspan=1):
        row, column = self.__nextPosition
        self.__updatePosition(colspan)
        return row, column

    def maxRow(self):
        row, column = self.__nextPosition
        return max(0, row-1) if column == 0 else row


class BookPage(wx.Panel):
    ''' A page in a notebook. '''
    def __init__(self, parent, columns, growableColumn=None, *args, **kwargs):
        super(BookPage, self).__init__(parent, style=wx.TAB_TRAVERSAL, 
            *args, **kwargs)
        self._sizer = wx.GridBagSizer(vgap=5, hgap=5)
        self._columns = columns
        self._position = GridCursor(columns)
        if growableColumn is None:
            growableColumn = columns - 1
        if growableColumn > -1:
            self._sizer.AddGrowableCol(growableColumn)
        self._borderWidth = 5

    def fit(self):
        self.SetSizerAndFit(self._sizer)

    def __defaultFlags(self, controls):
        ''' Return the default flags for placing a list of controls. '''
        labelInFirstColumn = type(controls[0]) in [type(''), type(u'')]
        flags = []
        for columnIndex in range(len(controls)):
            flag = wx.ALL|wx.ALIGN_CENTER_VERTICAL
            if columnIndex == 0 and labelInFirstColumn:
                flag |= wx.ALIGN_LEFT
            else:
                flag |= wx.ALIGN_RIGHT|wx.EXPAND
            flags.append(flag)
        return flags

    def __determineFlags(self, controls, flagsPassed):
        ''' Return a merged list of flags by overriding the default
            flags with flags passed by the caller. '''
        flagsPassed = flagsPassed or [None] * len(controls)
        defaultFlags = self.__defaultFlags(controls)
        return [defaultFlag if flagPassed is None else flagPassed 
                for flagPassed, defaultFlag in zip(flagsPassed, defaultFlags)]
 
    def addEntry(self, *controls, **kwargs):
        ''' Add a number of controls to the page. All controls are
            placed on one row, and together they form one entry. E.g. a
            label, a text field and an explanatory label. The default
            flags for placing the controls can be overridden by
            providing a keyword parameter 'flags'. flags should be a
            list of flags (wx.ALIGN_LEFT and the like). The list may
            contain None for controls that should be placed using the default
            flag. If the flags list is shorter than the number of
            controls it is extended with as much 'None's as needed.
            So, addEntry(aLabel, aTextCtrl, flags=[None, wx.ALIGN_LEFT]) 
            will place the label with the default flag and will place the 
            textCtrl left aligned. '''
        flags = self.__determineFlags(controls, kwargs.get('flags', None))
        controls = [self.__createStaticTextControlIfNeeded(control) \
                    for control in controls if control is not None]
        lastColumnIndex = len(controls) - 1
        for columnIndex, control in enumerate(controls):
            self.__addControl(columnIndex, control, flags[columnIndex], 
                              lastColumn=columnIndex==lastColumnIndex)
            if columnIndex > 0:
                control.MoveAfterInTabOrder(controls[columnIndex-1])
        if kwargs.get('growable', False):
            self._sizer.AddGrowableRow(self._position.maxRow())
            
    def addLine(self):
        line = wx.StaticLine(self)
        self.__addControl(0, line, flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL, lastColumn=True)

    def __addControl(self, columnIndex, control, flag, lastColumn):
        colspan = max(self._columns - columnIndex, 1) if lastColumn else 1
        self._sizer.Add(control, self._position.next(colspan),
            span=(1, colspan), flag=flag, border=self._borderWidth)
        
    def __createStaticTextControlIfNeeded(self, control):
        if type(control) in [type(''), type(u'')]:
            control = wx.StaticText(self, label=control)
        return control
        

class BookMixin(object):
    ''' Mixin class for *book '''
    
    _bitmapSize = (16, 16)
    pageChangedEvent = 'Subclass responsibility'
    
    def __init__(self, parent, *args, **kwargs):
        super(BookMixin, self).__init__(parent, -1, *args, **kwargs)
        dropTarget = draganddrop.FileDropTarget(onDragOverCallback=self.onDragOver)
        self.SetDropTarget(dropTarget)
        self.Bind(self.pageChangedEvent, self.onPageChanged)
        self.createImageList()
        
    def createImageList(self):
        self.AssignImageList(wx.ImageList(*self._bitmapSize))
        
    def __getitem__(self, index):
        ''' More pythonic way to get a specific page, also useful for iterating
            over all pages, e.g: for page in notebook: ... '''
        if index < self.GetPageCount():
            return self.GetPage(index)
        else:
            raise IndexError
        
    def onDragOver(self, x, y, defaultResult, pageSelectionArea=None):
        ''' When the user drags something (currently limited to files because
            the DropTarget created in __init__ is a FileDropTarget) over a tab
            raise the appropriate page. '''
        pageSelectionArea = pageSelectionArea or self
        pageIndex = pageSelectionArea.HitTest((x, y))
        if type(pageIndex) == type((),):
            pageIndex = pageIndex[0]
        if pageIndex != wx.NOT_FOUND:
            self.SetSelection(pageIndex)
        return wx.DragNone
    
    def onPageChanged(self, event):
        ''' Can be overridden in a subclass to do something useful '''
        event.Skip()    

    def AddPage(self, page, name, bitmap=None):
        if bitmap:
            imageList = self.GetImageList()
            imageList.Add(wx.ArtProvider_GetBitmap(bitmap, wx.ART_MENU, 
                          self._bitmapSize))
            imageId = imageList.GetImageCount()-1
        else:
            imageId = -1
        super(BookMixin, self).AddPage(page, name, imageId=imageId)

    def ok(self, *args, **kwargs):
        for page in self:
            page.ok(*args, **kwargs)
            

class Notebook(BookMixin, fnb.FlatNotebook):
    pageChangedEvent = wx.EVT_NOTEBOOK_PAGE_CHANGED
    
    def __init__(self, *args, **kwargs):
        kwargs['agwStyle'] = fnb.FNB_NO_X_BUTTON | fnb.FNB_VC8 | fnb.FNB_SMART_TABS | fnb.FNB_NO_NAV_BUTTONS | fnb.FNB_DROPDOWN_TABS_LIST
        super(Notebook, self).__init__(*args, **kwargs)
        bitmap = wx.BitmapFromIcon(self.TopLevelParent.GetIcon())
        if bitmap:
            # Despite its name, we need to pass a bitmap to SetNavigatorIcon
            self.SetNavigatorIcon(bitmap) 


class AuiManagedFrameWithNotebookAPI(frame.AuiManagedFrameWithDynamicCenterPane):
    ''' An AUI managed frame that provides (part of) the notebook API. '''

    def AddPage(self, page, caption, name):
        super(AuiManagedFrameWithNotebookAPI, self).addPane(page, caption, name) 

    def SetPageText(self, index, title):
        self.manager.GetAllPanes()[index].Caption(title)
        self.manager.Update()
        
    def GetPageText(self, index):
        return self.manager.GetAllPanes()[index].caption

    def GetPageIndex(self, window):
        for index, paneInfo in enumerate(self.manager.GetAllPanes()):
            if paneInfo.window == window:
                return index
        return wx.NOT_FOUND
    
    def __getitem__(self, index):
        return self.manager.GetAllPanes()[index].window
    
    def AdvanceSelection(self, forward=True):
        if self.PageCount <= 1:
            return # Not enough pages to advance selection
        curSelection = self.GetSelection()
        minSelection, maxSelection = 0, self.PageCount - 1
        if forward:
            newSelection = curSelection + 1 if minSelection <= curSelection < maxSelection else minSelection
        else:
            newSelection = curSelection - 1 if minSelection < curSelection <= maxSelection else maxSelection
        self.SetSelection(newSelection)
        selectedPane = self.manager.GetAllPanes()[newSelection]
        if selectedPane.IsToolbar() and self.PageCount > 1:
            self.AdvanceSelection(forward)

    def GetPageCount(self):
        return len(self.manager.GetAllPanes())
    
    PageCount = property(GetPageCount)
        
    def GetSelection(self):
        for index, paneInfo in enumerate(self.manager.GetAllPanes()):
            if paneInfo.HasFlag(aui.AuiPaneInfo.optionActive):
                return index
        return wx.NOT_FOUND

    def SetSelection(self, targetIndex, *args):
        for index, paneInfo in enumerate(self.manager.GetAllPanes()):
            # We can't use the variable paneInfo here. Apparently modifying the
            # first paneInfo in the list invalidates later ones. So we retrieve
            # the paneInfo's one by one:
            self.manager.GetAllPanes()[index].SetFlag(aui.AuiPaneInfo.optionActive, index==targetIndex)
        self.manager.Update()
        
    Selection = property(GetSelection, SetSelection)
