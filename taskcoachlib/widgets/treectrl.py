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

import wx, itemctrl, draganddrop
from taskcoachlib.thirdparty import hypertreelist
from taskcoachlib.thirdparty import customtreectrl as customtree

# pylint: disable-msg=E1101,E1103

class HyperTreeList(draganddrop.TreeCtrlDragAndDropMixin, 
                    hypertreelist.HyperTreeList):
    # pylint: disable-msg=W0223


    def __init__(self, *args, **kwargs):
        super(HyperTreeList, self).__init__(*args, **kwargs)
        if '__WXGTK__' == wx.Platform:
            self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.onItemCollapsed)

    def onItemCollapsed(self, event):
        event.Skip()
        # On Ubuntu, when the user has scrolled to the bottom of the tree
        # and collapses an item, the tree is not redrawn correctly. Refreshing
        # solves this. See http://trac.wxwidgets.org/ticket/11704
        wx.CallAfter(self.MainWindow.Refresh) 

    def GetSelections(self):
        ''' If the root item is hidden, it should never be selected, 
        unfortunately, CustomTreeCtrl and HyperTreeList allow it to be 
        selected. Override GetSelections to fix that. '''
        selections = super(HyperTreeList, self).GetSelections()
        if self.HasFlag(wx.TR_HIDE_ROOT):
            rootItem = self.GetRootItem()
            if rootItem and rootItem in selections:
                selections.remove(rootItem)
        return selections

    def GetMainWindow(self, *args, **kwargs):
        ''' Have a local GetMainWindow so we can create a MainWindow 
        property. '''
        return super(HyperTreeList, self).GetMainWindow(*args, **kwargs)
    
    MainWindow = property(fget=GetMainWindow)
    
    def HitTest(self, point): # pylint: disable-msg=W0221
        ''' Always return a three-tuple (item, flags, column). '''
        if type(point) == type(()):
            point = wx.Point(point[0], point[1])
        hitTestResult = super(HyperTreeList, self).HitTest(point)
        if len(hitTestResult) == 2:
            hitTestResult += (0,)
        if hitTestResult[0] is None:
            hitTestResult = (wx.TreeItemId(),) + hitTestResult[1:]
        return hitTestResult
    
    def isClickablePartOfNodeClicked(self, event):
        ''' Return whether the user double clicked some part of the node that
            can also receive regular mouse clicks. '''
        return self.isCollapseExpandButtonClicked(event)
    
    def isCollapseExpandButtonClicked(self, event):
        flags = self.HitTest(event.GetPosition())[1]
        return flags & wx.TREE_HITTEST_ONITEMBUTTON
            
    def isCheckBoxClicked(self, event):
        flags = self.HitTest(event.GetPosition())[1]
        return flags & customtree.TREE_HITTEST_ONITEMCHECKICON

    def collapseAllItems(self):
        for item in self.GetItemChildren():
            self.Collapse(item)
            
    def select(self, selection):
        for item in self.GetItemChildren(recursively=True):
            self.SelectItem(item, self.GetItemPyData(item) in selection)
        
    def clearselection(self):
        self.UnselectAll()
        self.selectCommand()

    def selectall(self):
        if self.GetItemCount() > 0:
            self.SelectAll()
        self.selectCommand()
                
    def isAnyItemCollapsable(self):
        for item in self.GetItemChildren():
            if self.isItemCollapsable(item): 
                return True
        return False
    
    def isAnyItemExpandable(self):
        for item in self.GetItemChildren():
            if self.isItemExpandable(item): 
                return True
        return False
    
    def isItemExpandable(self, item):
        return self.ItemHasChildren(item) and not self.IsExpanded(item)
    
    def isItemCollapsable(self, item):
        return self.ItemHasChildren(item) and self.IsExpanded(item)
    
    def IsLabelBeingEdited(self):
        return bool(self.GetLabelTextCtrl())
    
    def StopEditing(self):
        if self.IsLabelBeingEdited():
            self.GetLabelTextCtrl().StopEditing()
            
    def GetLabelTextCtrl(self):
        return self.GetMainWindow()._textCtrl
    
    def GetItemCount(self):
        rootItem = self.GetRootItem()
        return self.GetChildrenCount(rootItem, recursively=True) \
            if rootItem else 0
    

class TreeListCtrl(itemctrl.CtrlWithItemsMixin, itemctrl.CtrlWithColumnsMixin, 
                   itemctrl.CtrlWithToolTipMixin, HyperTreeList):
    # TreeListCtrl uses ALIGN_LEFT, ..., ListCtrl uses LIST_FORMAT_LEFT, ... for
    # specifying alignment of columns. This dictionary allows us to map from the 
    # ListCtrl constants to the TreeListCtrl constants:
    alignmentMap = {wx.LIST_FORMAT_LEFT: wx.ALIGN_LEFT, 
                    wx.LIST_FORMAT_CENTRE: wx.ALIGN_CENTRE,
                    wx.LIST_FORMAT_CENTER: wx.ALIGN_CENTER,
                    wx.LIST_FORMAT_RIGHT: wx.ALIGN_RIGHT}
    ct_type = 0
    
    def __init__(self, parent, columns, selectCommand, editCommand, 
                 dragAndDropCommand, editSubjectCommand,
                 itemPopupMenu=None, columnPopupMenu=None, 
                 *args, **kwargs):    
        self.__adapter = parent
        self.__selection = []
        self.__dontStartEditingLabelBecauseUserDoubleClicked = False
        self.__defaultFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        kwargs.setdefault('resizeableColumn', 0)
        super(TreeListCtrl, self).__init__(parent, style=self.getStyle(), 
            agwStyle=self.getAgwStyle(),
            columns=columns,  
            itemPopupMenu=itemPopupMenu,
            columnPopupMenu=columnPopupMenu, *args, **kwargs)
        self.bindEventHandlers(selectCommand, editCommand, dragAndDropCommand,
                               editSubjectCommand)

    def bindEventHandlers(self, selectCommand, editCommand, dragAndDropCommand,
                          editSubjectCommand):
        # pylint: disable-msg=W0201
        self.selectCommand = selectCommand
        self.editCommand = editCommand
        self.dragAndDropCommand = dragAndDropCommand
        self.editSubjectCommand = editSubjectCommand
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onSelect)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.onKeyDown)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.onItemActivated)
        # We deal with double clicks ourselves, to prevent the default behaviour
        # of collapsing or expanding nodes on double click. 
        self.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.onDoubleClick)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.onBeginEdit)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.onEndEdit)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.onItemExpanding)
        
    def getItemTooltipData(self, item, column):
        return self.__adapter.getItemTooltipData(item, column)
    
    def getItemCTType(self, item): # pylint: disable-msg=W0613
        return self.ct_type
    
    def curselection(self):
        return [self.GetItemPyData(item) for item in self.GetSelections()]
    
    def RefreshAllItems(self, count=0): # pylint: disable-msg=W0613
        self.Freeze()
        self.StopEditing()
        self.__selection = self.curselection()
        self.DeleteAllItems()
        rootItem = self.GetRootItem()
        if not rootItem:
            rootItem = self.AddRoot('Hidden root')
        self._addObjectRecursively(rootItem)
        if self.GetSelections():
            self.ScrollTo(self.GetSelections()[0])
        self.Thaw()
            
    def RefreshItems(self, *objects):
        self.StopEditing()
        self.__selection = self.curselection()
        self._refreshTargetObjects(self.GetRootItem(), *objects)
            
    def _refreshTargetObjects(self, parentItem, *targetObjects):
        childItem, cookie = self.GetFirstChild(parentItem)
        while childItem:
            itemObject = self.GetItemPyData(childItem) 
            if itemObject in targetObjects:
                self._refreshObjectCompletely(childItem, itemObject)
            self._refreshTargetObjects(childItem, *targetObjects)
            childItem, cookie = self.GetNextChild(parentItem, cookie)
            
    def _refreshObjectCompletely(self, item, *args):
        self._refreshAspects(('ItemType', 'Columns', 'Font', 'Colors',
                              'Selection'), item, check=True, *args)
        self.GetMainWindow().RefreshLine(item)
        
    def _addObjectRecursively(self, parentItem, parentObject=None):
        for childObject in self.__adapter.children(parentObject):
            childItem = self.AppendItem(parentItem, '', 
                                        self.getItemCTType(childObject), 
                                        data=childObject)
            self._refreshObjectMinimally(childItem, childObject)
            expanded = self.__adapter.getItemExpanded(childObject)
            if expanded:
                self._addObjectRecursively(childItem, childObject)
                # Call Expand on the item instead of on the tree
                # (self.Expand(childItem)) to prevent lots of events
                # (EVT_TREE_ITEM_EXPANDING/EXPANDED) being sent
                childItem.Expand()
            else:
                self.SetItemHasChildren(childItem,
                                        self.__adapter.children(childObject))

    def _refreshObjectMinimally(self, *args, **kwargs):
        self._refreshAspects(('Columns', 'Colors', 'Font', 'Selection'), *args, **kwargs)

    def _refreshAspects(self, aspects, *args, **kwargs):
        for aspect in aspects:
            refreshAspect = getattr(self, '_refresh%s'%aspect)
            refreshAspect(*args, **kwargs)
        
    def _refreshItemType(self, item, domainObject, check=False):
        ctType = self.getItemCTType(domainObject)
        if not check or (check and ctType != self.GetItemType(item)):
            self.SetItemType(item, ctType)
        
    def _refreshColumns(self, item, domainObject, check=False):
        for columnIndex in range(self.GetColumnCount()):
            self._refreshColumn(item, domainObject, columnIndex, check=check)
                
    def _refreshColumn(self, *args, **kwargs):
        self._refreshAspects(('Text', 'Image'), *args, **kwargs)
            
    def _refreshText(self, item, domainObject, columnIndex, check=False):
        text = self.__adapter.getItemText(domainObject, columnIndex)
        if text.count('\n') > 3:
            text = '\n'.join(text.split('\n')[:4]) + u' ...'
        if not check or (check and text != item.GetText(columnIndex)):
            item.SetText(columnIndex, text)
                
    def _refreshImage(self, item, domainObject, columnIndex, check=False):
        for which in (wx.TreeItemIcon_Expanded, wx.TreeItemIcon_Normal):
            image = self.__adapter.getItemImage(domainObject, which, columnIndex)
            image = image if image >= 0 else -1
            if not check or (check and image != item.GetImage(which, columnIndex)):
                item.SetImage(columnIndex, image, which)

    def _refreshColors(self, item, domainObject, check=False):
        bgColor = domainObject.backgroundColor(recursive=True) or wx.NullColour
        if not check or (check and bgColor != self.GetItemBackgroundColour(item)):
            self.SetItemBackgroundColour(item, bgColor)
        fgColor = domainObject.foregroundColor(recursive=True) or wx.NullColour
        if not check or (check and fgColor != self.GetItemTextColour(item)):
            self.SetItemTextColour(item, fgColor)
        
    def _refreshFont(self, item, domainObject, check=False):
        font = domainObject.font(recursive=True) or self.__defaultFont
        if not check or (check and font != self.GetItemFont(item)):
            self.SetItemFont(item, font)
        
    def _refreshSelection(self, item, domainObject, check=False):
        select = domainObject in self.__selection
        if not check or (check and select != item.IsSelected()):
            item.SetHilight(select)

    # Event handlers
    
    def onSelect(self, event):
        # Use CallAfter to prevent handling the select while items are 
        # being deleted:
        wx.CallAfter(self.selectCommand) 
        event.Skip()

    def onKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.editCommand(event)
        elif event.GetKeyCode() == wx.WXK_F2 and self.GetSelections():
            self.EditLabel(self.GetSelections()[0])
        else:
            event.Skip()
         
    def OnDrop(self, dropItem, dragItem):
        dropItem = None if dropItem == self.GetRootItem() else \
                   self.GetItemPyData(dropItem)
        dragItem = self.GetItemPyData(dragItem)
        self.dragAndDropCommand(dropItem, dragItem)
        
    def onItemExpanding(self, event):
        event.Skip()
        item = event.GetItem()
        if self.GetChildrenCount(item, recursively=False) == 0:
            domainObject = self.GetItemPyData(item)
            self._addObjectRecursively(item, domainObject)
                
    def onDoubleClick(self, event):
        self.__dontStartEditingLabelBecauseUserDoubleClicked = True
        if self.isClickablePartOfNodeClicked(event):
            event.Skip(False)
        else:
            self.onItemActivated(event)
        
    def onItemActivated(self, event):
        ''' Attach the column clicked on to the event so we can use it elsewhere. '''
        mousePosition = self.GetMainWindow().ScreenToClient(wx.GetMousePosition())
        item, _, column = self.HitTest(mousePosition)
        if item:
            # Only get the column name if the hittest returned an item,
            # otherwise the item was activated from the menu or by double 
            # clicking on a portion of the tree view not containing an item.
            column = max(0, column) # FIXME: Why can the column be -1?
            event.columnName = self._getColumn(column).name()
        self.editCommand(event)
        event.Skip(False)
        
    def onBeginEdit(self, event):
        if self.__dontStartEditingLabelBecauseUserDoubleClicked:
            event.Veto()
            self.__dontStartEditingLabelBecauseUserDoubleClicked = False
        elif self.IsLabelBeingEdited():
            # Don't start editing another label when the user is still editing
            # a label. This prevents left-over text controls in the tree.
            event.Veto()
        else:
            event.Skip()
        
    def onEndEdit(self, event):
        domainObject = self.GetItemPyData(event.GetItem())
        newValue = event.GetLabel()
        # Give HyperTreeList a chance to properly close the text editor:
        wx.FutureCall(50, self.editSubjectCommand, domainObject, newValue)
        event.Skip()
        
    # Override CtrlWithColumnsMixin with TreeListCtrl specific behaviour:
        
    def _setColumns(self, *args, **kwargs):
        super(TreeListCtrl, self)._setColumns(*args, **kwargs)
        self.SetMainColumn(0)
        self.SetColumnEditable(0, True)
                        
    # Extend TreeMixin with TreeListCtrl specific behaviour:

    def getStyle(self):
        return wx.WANTS_CHARS 
            
    def getAgwStyle(self):
        agwStyle = wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_MULTIPLE \
            | wx.TR_EDIT_LABELS | wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT \
            | customtree.TR_HAS_VARIABLE_ROW_HEIGHT
        if wx.Platform == '__WXMAC__':
            agwStyle |= wx.TR_NO_LINES
        agwStyle &= ~hypertreelist.TR_NO_HEADER
        return agwStyle

    # pylint: disable-msg=W0221
    
    def DeleteColumn(self, columnIndex):
        self.RemoveColumn(columnIndex)
        
    def InsertColumn(self, columnIndex, columnHeader, *args, **kwargs):
        format = self.alignmentMap[kwargs.pop('format', wx.LIST_FORMAT_LEFT)]
        if columnIndex == self.GetColumnCount():
            self.AddColumn(columnHeader, *args, **kwargs)
        else:
            super(TreeListCtrl, self).InsertColumn(columnIndex, columnHeader, 
                *args, **kwargs)
        self.SetColumnAlignment(columnIndex, format)

    def showColumn(self, *args, **kwargs):
        ''' Stop editing before we hide or show a column to prevent problems
            redrawing the tree list control contents. '''
        self.StopEditing()
        super(TreeListCtrl, self).showColumn(*args, **kwargs)


class CheckTreeCtrl(TreeListCtrl):
    def __init__(self, parent, columns, selectCommand, checkCommand, 
                 editCommand, dragAndDropCommand, itemPopupMenu=None, 
                 *args, **kwargs):
        self.__checking = False
        super(CheckTreeCtrl, self).__init__(parent, columns,
            selectCommand, editCommand, dragAndDropCommand, 
            itemPopupMenu, *args, **kwargs)
        self.checkCommand = checkCommand
        self.Bind(customtree.EVT_TREE_ITEM_CHECKED, self.onItemChecked)
        self.getIsItemCheckable = parent.getIsItemCheckable if hasattr(parent, 'getIsItemCheckable') else lambda item: True
        self.getIsItemChecked = parent.getIsItemChecked
        self.getItemParentHasExclusiveChildren = parent.getItemParentHasExclusiveChildren
        
    def getItemCTType(self, domainObject):
        ''' Use radio buttons (ct_type == 2) when the object has "exclusive" 
            children, meaning that only one child can be checked at a time. Use
            check boxes (ct_type == 1) otherwise. '''
        if self.getIsItemCheckable(domainObject):
            return 2 if self.getItemParentHasExclusiveChildren(domainObject) else 1
        else:
            return 0
    
    def CheckItem(self, item, checked=True):
        if self.GetItemType(item) == 2:
            # Use UnCheckRadioParent because CheckItem always keeps at least
            # one item selected, which we don't want to enforce
            self.UnCheckRadioParent(item, checked)
        else:
            super(CheckTreeCtrl, self).CheckItem(item, checked)
        
    def _refreshObjectCompletely(self, item, domainObject):
        super(CheckTreeCtrl, self)._refreshObjectCompletely(item, domainObject)
        self._refreshCheckState(item, domainObject)
        
    def _refreshObjectMinimally(self, item, domainObject):
        super(CheckTreeCtrl, self)._refreshObjectMinimally(item, domainObject)
        self._refreshCheckState(item, domainObject)
    
    def _refreshCheckState(self, item, domainObject):
        # Use CheckItem2 so no events get sent:
        self.CheckItem2(item, self.getIsItemChecked(domainObject))
        parent = item.GetParent()
        while parent:
            if self.GetItemType(parent) == 2:
                self.EnableItem(item, self.IsItemChecked(parent))
                break
            parent = parent.GetParent()

    def onItemChecked(self, event):
        if self.__checking: 
            # Ignore checked events while we're making the tree consistent,
            # only invoke the callback:
            self.checkCommand(event)
            return
        self.__checking = True
        item = event.GetItem()
        # Uncheck mutual exclusive children:
        for child in self.GetItemChildren(item):
            if self.GetItemType(child) == 2:
                self.CheckItem(child, False)
                # Recursively uncheck children of mutual exclusive children:
                for grandchild in self.GetItemChildren(child, recursively=True):
                    self.CheckItem(grandchild, False)
        # If this item is mutual exclusive, recursively uncheck siblings and parent:
        parent = item.GetParent()
        if parent and self.GetItemType(item) == 2:
            for child in self.GetItemChildren(parent):
                if child == item:
                    continue
                self.CheckItem(child, False)
                for grandchild in self.GetItemChildren(child, recursively=True):
                    self.CheckItem(grandchild, False)
            if self.GetItemType(parent) != 2:
                self.CheckItem(parent, False)
        self.__checking = False
        self.checkCommand(event)
        
    def onItemActivated(self, event):
        if self.isDoubleClicked(event):
            # Invoke super.onItemActivated to edit the item
            super(CheckTreeCtrl, self).onItemActivated(event)
        else:
            # Item is activated, let another event handler deal with the event 
            event.Skip()
            
    def isDoubleClicked(self, event):
        return hasattr(event, 'LeftDClick') and event.LeftDClick()
    
