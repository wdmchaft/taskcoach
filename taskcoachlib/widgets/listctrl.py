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

import wx, itemctrl

class _ListCtrl(wx.ListCtrl):
    ''' Make ListCtrl API more like the TreeList and TreeListCtrl API '''
    
    def HitTest(self, (x,y)):
        ''' Always return a three-tuple (item, flag, column). '''
        index, flags = super(_ListCtrl, self).HitTest((x,y))
        column = 0
        if self.InReportView():
            # Determine the column in which the user clicked
            cumulativeColumnWidth = 0
            for columnIndex in range(self.GetColumnCount()):
                cumulativeColumnWidth += self.GetColumnWidth(columnIndex)
                if x <= cumulativeColumnWidth:
                    column = columnIndex
                    break
        return index, flags, column

    def ToggleItemSelection(self, index):
        currentState = self.GetItemState(index, wx.LIST_STATE_SELECTED)
        self.SetItemState(index, ~currentState, wx.LIST_STATE_SELECTED)
     
        
class VirtualListCtrl(itemctrl.CtrlWithItemsMixin, itemctrl.CtrlWithColumnsMixin, 
                      itemctrl.CtrlWithToolTipMixin, _ListCtrl):
    def __init__(self, parent, columns, selectCommand=None, editCommand=None, 
                 itemPopupMenu=None, columnPopupMenu=None, resizeableColumn=0, 
                 *args, **kwargs):
        super(VirtualListCtrl, self).__init__(parent,
            style=wx.LC_REPORT|wx.LC_VIRTUAL, columns=columns, 
            resizeableColumn=resizeableColumn, itemPopupMenu=itemPopupMenu, 
            columnPopupMenu=columnPopupMenu, *args, **kwargs)
        self.__parent = parent
        self.bindEventHandlers(selectCommand, editCommand)
            
    def bindEventHandlers(self, selectCommand, editCommand):
        if selectCommand:
            self.selectCommand = selectCommand
            self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onSelect)
            self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect)
            self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onSelect)
        if editCommand:
            self.editCommand = editCommand
            self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated)  
            
    def getItemWithIndex(self, rowIndex):
        return self.__parent.getItemWithIndex(rowIndex)

    def getItemText(self, domainObject, columnIndex):
        return self.__parent.getItemText(domainObject, columnIndex)
    
    def getItemTooltipData(self, domainObject, columnIndex):
        return self.__parent.getItemTooltipData(domainObject, columnIndex)
    
    def getItemImage(self, domainObject, columnIndex=0):
        return self.__parent.getItemImage(domainObject, wx.TreeItemIcon_Normal, 
                                          columnIndex)
    
    def OnGetItemText(self, rowIndex, columnIndex):
        item = self.getItemWithIndex(rowIndex)
        return self.getItemText(item, columnIndex)

    def OnGetItemTooltipData(self, rowIndex, columnIndex):
        item = self.getItemWithIndex(rowIndex)
        return self.getItemTooltipData(item, columnIndex)

    def OnGetItemImage(self, rowIndex):
        item = self.getItemWithIndex(rowIndex)
        return self.getItemImage(item)
    
    def OnGetItemColumnImage(self, rowIndex, columnIndex):
        item = self.getItemWithIndex(rowIndex)
        return self.getItemImage(item, columnIndex)

    def OnGetItemAttr(self, rowIndex):
        item = self.getItemWithIndex(rowIndex)
        foregroundColor = item.foregroundColor(recursive=True)
        backgroundColor = item.backgroundColor(recursive=True)
        itemAttrArgs = [foregroundColor, backgroundColor] 
        font = item.font(recursive=True)
        if font:
            itemAttrArgs.append(font)
        # We need to keep a reference to the item attribute to prevent it
        # from being garbage collected too soon:
        self.__itemAttribute = wx.ListItemAttr(*itemAttrArgs)
        return self.__itemAttribute
        
    def onSelect(self, event):
        self.selectCommand(event)
        
    def onItemActivated(self, event):
        ''' Override default behavior to attach the column clicked on
            to the event so we can use it elsewhere. '''
        mousePosition = self.GetMainWindow().ScreenToClient(wx.GetMousePosition())
        index, flags, column = self.HitTest(mousePosition)
        if index >= 0:
            # Only get the column name if the hittest returned an item,
            # otherwise the item was activated from the menu or by double 
            # clicking on a portion of the tree view not containing an item.
            column = max(0, column) # FIXME: Why can the column be -1?
            event.columnName = self._getColumn(column).name()
        self.editCommand(event)

    def RefreshAllItems(self, count):
        self.SetItemCount(count)
        if count == 0:
            self.DeleteAllItems()
        else:
            # The VirtualListCtrl makes sure only visible items are updated
            super(VirtualListCtrl, self).RefreshItems(0, count-1)

    def RefreshItems(self, *items):
        ''' Refresh specific items. '''
        if len(items) <= 5:
            for item in items:
                self.RefreshItem(self.__parent.getIndexOfItem(item))
        else:
            self.RefreshAllItems(self.GetItemCount())
        
    def curselection(self):
        return [self.getItemWithIndex(index) for index in self.curselectionIndices()]
    
    def curselectionIndices(self):
        return wx.lib.mixins.listctrl.getListCtrlSelection(self)

    def select(self, items):
        indices = [self.__parent.getIndexOfItem(item) for item in items]
        for index in range(self.GetItemCount()):
            self.Select(index, index in indices)
        if self.curselection():
            self.Focus(self.GetFirstSelected())        
    
    def clearselection(self):
        for index in self.curselectionIndices():
            self.Select(index, False)

    def selectall(self):
        for index in range(self.GetItemCount()):
            self.Select(index)


class ListCtrl(VirtualListCtrl):
    pass
    
