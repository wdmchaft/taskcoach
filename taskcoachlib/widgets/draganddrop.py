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
from taskcoachlib.mailer import thunderbird, outlook


class FileDropTarget(wx.FileDropTarget):
    def __init__(self, onDropCallback=None, onDragOverCallback=None):
        wx.FileDropTarget.__init__(self)
        self.__onDropCallback = onDropCallback
        self.__onDragOverCallback = onDragOverCallback or self.__defaultDragOverCallback
        
    def OnDropFiles(self, x, y, filenames): # pylint: disable-msg=W0221
        if self.__onDropCallback:
            self.__onDropCallback(x, y, filenames)
            return True
        else:
            return False

    def OnDragOver(self, x, y, defaultResult): # pylint: disable-msg=W0221
        return self.__onDragOverCallback(x, y, defaultResult)
    
    def __defaultDragOverCallback(self, x, y, defaultResult): # pylint: disable-msg=W0613
        return defaultResult
    
    
class TextDropTarget(wx.TextDropTarget):
    def __init__(self, onDropCallback):
        wx.TextDropTarget.__init__(self)
        self.__onDropCallback = onDropCallback
        
    def OnDropText(self, x, y, text): # pylint: disable-msg=W0613,W0221
        self.__onDropCallback(text)


class DropTarget(wx.DropTarget):
    def __init__(self, onDropURLCallback, onDropFileCallback,
            onDropMailCallback, onDragOverCallback=None):
        super(DropTarget, self).__init__()
        self.__onDropURLCallback = onDropURLCallback
        self.__onDropFileCallback = onDropFileCallback
        self.__onDropMailCallback = onDropMailCallback
        self.__onDragOverCallback = onDragOverCallback
        self.reinit()

    def reinit(self): 
        # pylint: disable-msg=W0201
        self.__compositeDataObject = wx.DataObjectComposite()
        self.__urlDataObject = wx.TextDataObject()
        self.__fileDataObject = wx.FileDataObject()
        self.__thunderbirdMailDataObject = wx.CustomDataObject('text/x-moz-message')
        self.__macThunderbirdMailDataObject = wx.CustomDataObject('MZ\x00\x00') # Doesn't work any more...
        self.__outlookDataObject = wx.CustomDataObject('Object Descriptor')
        # Starting with Snow Leopard, mail.app supports the message: protocol
        self.__macMailObject = wx.CustomDataObject('public.url')
        for dataObject in self.__fileDataObject, \
                          self.__thunderbirdMailDataObject, \
                          self.__outlookDataObject, \
                          self.__macThunderbirdMailDataObject, \
                          self.__urlDataObject, \
                          self.__macMailObject:
            # Note: The first data object added is the preferred data object.
            # We add urlData as last so that Outlook messages are not 
            # interpreted as text objects.
            self.__compositeDataObject.Add(dataObject)
        self.SetDataObject(self.__compositeDataObject)

    def OnDragOver(self, x, y, result): # pylint: disable-msg=W0221
        if self.__onDragOverCallback is None:
            return result
        self.__onDragOverCallback(x, y, result)
        return wx.DragCopy

    def OnDrop(self, x, y): # pylint: disable-msg=W0613,W0221
        return True
    
    def OnData(self, x, y, result): # pylint: disable-msg=W0613
        self.GetData()

        format = self.__compositeDataObject.GetReceivedFormat()

        if format.GetType() in [ wx.DF_TEXT, wx.DF_UNICODETEXT ]:
            if self.__onDropURLCallback:
                self.__onDropURLCallback(x, y, self.__urlDataObject.GetText())
        elif format.GetType() == wx.DF_FILENAME:
            if self.__onDropFileCallback:
                self.__onDropFileCallback(x, y, self.__fileDataObject.GetFilenames())
        elif format.GetId() == 'text/x-moz-message':
            if self.__onDropMailCallback:
                data = self.__thunderbirdMailDataObject.GetData()
                # We expect the data to be encoded with 'unicode_internal',
                # but on Fedora it can also be 'utf-16', be prepared:
                try:
                    data = data.decode('unicode_internal')
                except UnicodeDecodeError:
                    data = data.decode('utf-16')
                self.__onDropMailCallback(x, y, thunderbird.getMail(data))
        elif self.__macThunderbirdMailDataObject.GetData():
            if self.__onDropMailCallback:
                self.__onDropMailCallback(x, y,
                     thunderbird.getMail(self.__macThunderbirdMailDataObject.GetData().decode('unicode_internal')))
        elif format.GetId() == 'Object Descriptor':
            if self.__onDropMailCallback:
                for mail in outlook.getCurrentSelection():
                    self.__onDropMailCallback(x, y, mail)
        elif format.GetId() == 'public.url':
            url = self.__macMailObject.GetData()
            if url.startswith('message:') and self.__onDropURLCallback:
                self.__onDropURLCallback(x, y, url)

        self.reinit()
        return wx.DragCopy


class TreeHelperMixin(object):
    """ This class provides methods that are not part of the API of any 
    tree control, but are convenient to have available. """

    def GetItemChildren(self, item=None, recursively=False):
        """ Return the children of item as a list. """
        if not item:
            item = self.GetRootItem()
            if not item:
                return []
        children = []
        child, cookie = self.GetFirstChild(item)
        while child:
            children.append(child)
            if recursively:
                children.extend(self.GetItemChildren(child, True))
            child, cookie = self.GetNextChild(item, cookie)
        return children


class TreeCtrlDragAndDropMixin(TreeHelperMixin):
    """ This is a mixin class that can be used to easily implement
    dragging and dropping of tree items. It can be mixed in with 
    wx.TreeCtrl, wx.gizmos.TreeListCtrl, or wx.lib.customtree.CustomTreeCtrl.

    To use it derive a new class from this class and one of the tree
    controls, e.g.:
    class MyTree(TreeCtrlDragAndDropMixin, wx.TreeCtrl):
        ...

    You *must* implement OnDrop. OnDrop is called when the user has
    dropped an item on top of another item. It's up to you to decide how
    to handle the drop. If you are using this mixin together with the
    VirtualTree mixin, it makes sense to rearrange your underlying data
    and then call RefreshItems to let the virtual tree refresh itself. """    
 
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.get('style', wx.TR_DEFAULT_STYLE) | \
                          wx.TR_HIDE_ROOT
        super(TreeCtrlDragAndDropMixin, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnBeginDrag)
        self._dragItem = None

    def OnDrop(self, dropItem, dragItem):
        ''' This function must be overloaded in the derived class.
        dragItem is the item being dragged by the user. dropItem is the
        item dragItem is dropped upon. If the user doesn't drop dragItem
        on another item, dropItem equals the (hidden) root item of the
        tree control. '''
        raise NotImplementedError

    def OnBeginDrag(self, event):
        ''' This method is called when the drag starts. It either allows the
        drag and starts it or it vetoes the drag when the dragged item is the
        root item. '''
        selections = self.GetSelections()
        # We allow only one item to be dragged at a time, to keep it simple
        self._dragItem = selections[0] if selections else event.GetItem()
        if self._dragItem and self._dragItem != self.GetRootItem(): 
            self.StartDragging()
            event.Allow()
        else:
            event.Veto()

    def OnEndDrag(self, event):
        self.StopDragging()
        dropTarget = event.GetItem()
        if not dropTarget:
            dropTarget = self.GetRootItem()
        if self.IsValidDropTarget(dropTarget):
            self.UnselectAll()
            if dropTarget != self.GetRootItem():
                self.SelectItem(dropTarget)
            self.OnDrop(dropTarget, self._dragItem)
        else:
            # Work around an issue with HyperTreeList. HyperTreeList will
            # restore the selection to the last item highlighted by the drag,
            # after we have processed the end drag event. That's not what we
            # want, so use wx.CallAfter to clear the selection after
            # HyperTreeList did its (wrong) thing and reselect the previously
            # dragged item.
            wx.CallAfter(self.selectDraggedItem)

    def selectDraggedItem(self):
        self.UnselectAll()
        self.SelectItem(self._dragItem)
        
    def OnDragging(self, event):
        if not event.Dragging():
            self.StopDragging()
            return
        item, flags = self.HitTest(wx.Point(event.GetX(), event.GetY()))[:2]
        if not item:
            item = self.GetRootItem()
        if self.IsValidDropTarget(item):
            self.SetCursorToDragging()
        else:
            self.SetCursorToDroppingImpossible()
        if flags & wx.TREE_HITTEST_ONITEMBUTTON:
            self.Expand(item)
        if self.GetSelections() != [item]:
            self.UnselectAll()
            if item != self.GetRootItem(): 
                self.SelectItem(item)
        event.Skip()
        
    def StartDragging(self):
        self.GetMainWindow().Bind(wx.EVT_MOTION, self.OnDragging)
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.SetCursorToDragging()

    def StopDragging(self):
        self.GetMainWindow().Unbind(wx.EVT_MOTION)
        self.Unbind(wx.EVT_TREE_END_DRAG)
        self.ResetCursor()
        self.UnselectAll()
        self.SelectItem(self._dragItem)
        
    def SetCursorToDragging(self):
        self.GetMainWindow().SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        
    def SetCursorToDroppingImpossible(self):
        self.GetMainWindow().SetCursor(wx.StockCursor(wx.CURSOR_NO_ENTRY))
        
    def ResetCursor(self):
        self.GetMainWindow().SetCursor(wx.NullCursor)

    def IsValidDropTarget(self, dropTarget):
        if dropTarget: 
            allChildren = self.GetItemChildren(self._dragItem, recursively=True)
            parent = self.GetItemParent(self._dragItem) 
            return dropTarget not in [self._dragItem, parent] + allChildren
        else:
            return True        
