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
from taskcoachlib.thirdparty import hypertreelist
    
    
class AutoColumnWidthMixin(object):
    """ A mix-in class that automatically resizes one column to take up
        the remaining width of a control with columns (i.e. ListCtrl, 
        TreeListCtrl).

        This causes the control to automatically take up the full width 
        available, without either a horizontal scroll bar (unless absolutely
        necessary) or empty space to the right of the last column.

        NOTE:    When using this mixin with a ListCtrl, make sure the ListCtrl
                 is in report mode.

        WARNING: If you override the EVT_SIZE event in your control, make
                 sure you call event.Skip() to ensure that the mixin's
                 OnResize method is called.
    """
    def __init__(self, *args, **kwargs):
        self._isAutoResizing = False
        self.ResizeColumn = kwargs.pop('resizeableColumn', -1)
        self.ResizeColumnMinWidth = kwargs.pop('resizeableColumnMinWidth', 50)
        super(AutoColumnWidthMixin, self).__init__(*args, **kwargs)
        
    def ToggleAutoResizing(self, on):
        if on == self._isAutoResizing:
            return
        self._isAutoResizing = on
        if on:
            self.Bind(wx.EVT_SIZE, self.OnResize)
            self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnBeginColumnDrag)
            self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnEndColumnDrag)
            self.DoResize()
        else:
            self.Unbind(wx.EVT_SIZE)
            self.Unbind(wx.EVT_LIST_COL_BEGIN_DRAG)
            self.Unbind(wx.EVT_LIST_COL_END_DRAG)

    def IsAutoResizing(self):
        return self._isAutoResizing
            
    def OnBeginColumnDrag(self, event):
        if event.Column == self.ResizeColumn:
            self.__oldResizeColumnWidth = self.GetColumnWidth(self.ResizeColumn)
        # Temporarily unbind the EVT_SIZE to prevent resizing during dragging
        self.Unbind(wx.EVT_SIZE)
        if '__WXMAC__' != wx.Platform:
            event.Skip()
        
    def OnEndColumnDrag(self, event):
        if event.Column == self.ResizeColumn and self.GetColumnCount() > 1:
            extraWidth = self.__oldResizeColumnWidth - \
                             self.GetColumnWidth(self.ResizeColumn)
            self.DistributeWidthAcrossColumns(extraWidth)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        wx.CallAfter(self.DoResize)
        event.Skip()
        
    def OnResize(self, event):
        event.Skip()
        if '__WXMSW__' == wx.Platform:
            wx.CallAfter(self.DoResize)
        else:
            self.DoResize()

    def DoResize(self):
        if not self:
            return # Avoid a potential PyDeadObject error
        if not self.IsAutoResizing():
            return
        if self.GetSize().height < 32:
            return # Avoid an endless update bug when the height is small.
        if self.GetColumnCount() <= self.ResizeColumn:
            return # Nothing to resize.

        resizeColumnWidth = self.ResizeColumnMinWidth
        unusedWidth = max(self.AvailableWidth - self.NecessaryWidth, 0)
        resizeColumnWidth += unusedWidth
        self.SetColumnWidth(self.ResizeColumn, resizeColumnWidth)
        
    def DistributeWidthAcrossColumns(self, extraWidth):
        # When the user resizes the ResizeColumn distribute the extra available
        # space across the other columns, or get the extra needed space from
        # the other columns. The other columns are resized proportionally to 
        # their previous width.
        otherColumns = [index for index in range(self.GetColumnCount())
                        if index != self.ResizeColumn]
        totalWidth = float(sum(self.GetColumnWidth(index) for index in 
                               otherColumns))
        for columnIndex in otherColumns:
            thisColumnWidth = self.GetColumnWidth(columnIndex)
            thisColumnWidth += thisColumnWidth / totalWidth * extraWidth
            self.SetColumnWidth(columnIndex, thisColumnWidth)
        
    def GetResizeColumn(self):
        if self._resizeColumn == -1:
            return self.GetColumnCount() - 1
        else:
            return self._resizeColumn
        
    def SetResizeColumn(self, columnIndex):
        self._resizeColumn = columnIndex

    ResizeColumn = property(GetResizeColumn, SetResizeColumn)
    
    def GetAvailableWidth(self):
        availableWidth = self.GetClientSize().width
        if self.__isScrollbarVisible() and self.__isScrollbarIncludedInClientSize():
            scrollbarWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
            availableWidth -= scrollbarWidth
        return availableWidth

    AvailableWidth = property(GetAvailableWidth)

    def GetNecessaryWidth(self):
        necessaryWidth = 0
        for columnIndex in range(self.GetColumnCount()):
            if columnIndex == self._resizeColumn:
                necessaryWidth += self.ResizeColumnMinWidth
            else:
                necessaryWidth += self.GetColumnWidth(columnIndex)
        return necessaryWidth
    
    NecessaryWidth = property(GetNecessaryWidth)
   
    # Override all methods that manipulate columns to be able to resize the
    # columns after any additions or removals. 
   
    def InsertColumn(self, *args, **kwargs):
        ''' Insert the new column and then resize. '''
        result = super(AutoColumnWidthMixin, self).InsertColumn(*args, **kwargs)
        self.DoResize()
        return result
        
    def DeleteColumn(self, *args, **kwargs):
        ''' Delete the column and then resize. '''
        result = super(AutoColumnWidthMixin, self).DeleteColumn(*args, **kwargs)
        self.DoResize()
        return result
        
    def RemoveColumn(self, *args, **kwargs):
        ''' Remove the column and then resize. '''
        result = super(AutoColumnWidthMixin, self).RemoveColumn(*args, **kwargs)
        self.DoResize()
        return result

    def AddColumn(self, *args, **kwargs):
        ''' Add the column and then resize. '''
        result = super(AutoColumnWidthMixin, self).AddColumn(*args, **kwargs)
        self.DoResize()
        return result

    # Private helper methods:

    def __isScrollbarVisible(self):
        return self.MainWindow.HasScrollbar(wx.VERTICAL)

    def __isScrollbarIncludedInClientSize(self):
        # NOTE: on GTK, the scrollbar is included in the client size, but on
        # Windows it is not included
        if wx.Platform == '__WXMSW__':
            return isinstance(self, hypertreelist.HyperTreeList)
        else:
            return True
 
