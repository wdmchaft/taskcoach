'''
Task Coach - Your friendly task manager
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>

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
from taskcoachlib.syncml.core import *
from taskcoachlib.i18n import _


class BaseSource(SyncSource):
    STATE_NONE         = 0
    STATE_FIRSTPASS    = 1
    STATE_SECONDPASS   = 2
    STATE_NORMAL       = 3

    def __init__(self, callback, objectList, *args, **kwargs):
        super(BaseSource, self).__init__(*args, **kwargs)

        self.callback = callback
        self.objectList = objectList

        self.allObjectsList = [obj for obj in objectList]
        self.newObjectsList = [obj for obj in objectList if obj.isNew()]
        self.changedObjectsList = [obj for obj in objectList if obj.isModified()]
        self.deletedObjectsList = [obj for obj in objectList if obj.isDeleted()]

        self.state = self.STATE_NONE
        self.lastLast = None

    def __getstate__(self):
        return {'state': self.state, 'lastLast': self.lastLast}

    def __setstate__(self, state):
        self.__dict__.update(state)

    def beginSync(self):
        if self.state == self.STATE_NONE:
            if self.syncMode in [TWO_WAY, SLOW]:
                self.lastLast = self.lastAnchor
                self.state = self.STATE_FIRSTPASS
            elif self.syncMode in [REFRESH_FROM_SERVER,
                                 REFRESH_FROM_SERVER_BY_SERVER]:
                if self.objectList:
                    if wx.MessageBox(_('The synchronization for source %s') % self.name + \
                                     _('will be a refresh from server. All local items will\n' \
                                       'be deleted. Do you wish to continue?'),
                                     _('Refresh from server'), wx.YES_NO) != wx.YES:
                        return 514 # Not sure of this
                    self.objectList.clear()
                    self.allObjectsList = []
                    self.newObjectsList = []
                    self.changedObjectsList = []
                    self.deletedObjectsList = []
            elif self.syncMode in [REFRESH_FROM_CLIENT,
                                   REFRESH_FROM_CLIENT_BY_SERVER]:
                if wx.MessageBox(_('The synchronization for source %s') % self.name + \
                                 _('will be a refresh from client. All remote items will\n' \
                                   'be deleted. Do you wish to continue?'),
                                 _('Refresh from server'), wx.YES_NO) != wx.YES:
                    return 514 # Not sure of this

                self.state = self.STATE_NORMAL
        elif self.state == self.STATE_FIRSTPASS:
            lastLast = self.lastAnchor
            self.lastAnchor = self.lastLast
            self.lastLast = lastLast
            self.state = self.STATE_SECONDPASS

    def endSync(self):
        if self.state == self.STATE_SECONDPASS:
            self.lastAnchor = self.lastLast

    def _getObject(self, key):
        """Returns the domain object with local ID 'key', or raise
        KeyError if not found."""

        for obj in self.allObjectsList:
            if obj.id() == key:
                return obj
        raise KeyError, 'No such object: %s' % key

    def _getItem(self, ls):
        """Returns a SyncItem instance representing the first domain
        object in the 'ls' sequence."""

        try:
            obj = ls.pop(0)
        except IndexError:
            return None

        item = SyncItem(obj.id())

        if obj.getStatus() == obj.STATUS_NONE:
            item.state = STATE_NONE
        elif obj.getStatus() == obj.STATUS_NEW:
            item.state = STATE_NEW
        elif obj.getStatus() == obj.STATUS_CHANGED:
            item.state = STATE_UPDATED
        elif obj.getStatus() == obj.STATUS_DELETED:
            item.state = STATE_DELETED

        self.updateItemProperties(item, obj)

        return item

    def updateItemProperties(self, item, obj):
        """Set item properties (data, dataType...) according to the
        domain object 'obj'. You must overload this in subclasses."""

        raise NotImplementedError

    def compareItemProperties(self, local, remote):
        """Compare the two domain objects, and return 0 if they're the
        same. The return value will then be passed to the conflict
        resolution methods if there is a conflict."""

        raise NotImplementedError

    def _parseObject(self, item):
        """Must return a new domain object from a SyncItem instance."""

        raise NotImplementedError

    # These two methods seem to be obsolete.

    def getFirstItemKey(self):
        return None

    def getNextItemKey(self):
        return None

    def getFirstItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            self.allObjectsListCopy = self.allObjectsList[:]
            return self._getItem(self.allObjectsListCopy)

    def getNextItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            return self._getItem(self.allObjectsListCopy)

    def getFirstNewItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            self.newObjectsListCopy = self.newObjectsList[:]
            return self._getItem(self.newObjectsListCopy)

    def getNextNewItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            return self._getItem(self.newObjectsListCopy)

    def getFirstUpdatedItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            self.changedObjectsListCopy = self.changedObjectsList[:]
            return self._getItem(self.changedObjectsListCopy)

    def getNextUpdatedItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            return self._getItem(self.changedObjectsListCopy)

    def getFirstDeletedItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            self.deletedObjectsListCopy = self.deletedObjectsList[:]
            return self._getItem(self.deletedObjectsListCopy)

    def getNextDeletedItem(self):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            return self._getItem(self.deletedObjectsListCopy)

    def addItem(self, item):
        self.callback.onAddItem()

        if self.state in [self.STATE_NORMAL, self.STATE_FIRSTPASS]:
            obj = self._parseObject(item)
            self.objectList.append(obj)
            item.key = obj.id().encode('UTF-8')

            return self.doAddItem(obj)

        return 201

    def doAddItem(self, obj):
        """Called after a domain object has been added; use this to
        set up the object if it needs to."""

        return 201

    def updateItem(self, item):
        self.callback.onUpdateItem()

        if self.state in [self.STATE_NORMAL, self.STATE_FIRSTPASS]:
            obj = self._parseObject(item)

            try:
                local = self._getObject(item.key)
            except KeyError:
                return 404

            if local.isModified():
                result = self.compareItemProperties(local, obj)

                if result:
                    obj = self.doResolveConflict(obj, local, result)
                    local.markDirty() # so that the resolved item is uploaded on second pass
            elif local.isDeleted():
                if self.objectRemovedOnClient(local):
                    self.doUpdateItem(obj, local)
                    local.cleanDirty()
                    return 200

            return self.doUpdateItem(obj, local)

        return 200

    def doUpdateItem(self, obj, local):
        """Must update the 'local' domain object according to 'obj'
        (which is a 'temporary' domain object)"""

        raise NotImplementedError

    def deleteItem(self, item):
        self.callback.onDeleteItem()

        if self.state in [self.STATE_NORMAL, self.STATE_FIRSTPASS]:
            try:
                obj = self._getObject(item.key)
            except KeyError:
                return 211

            if obj.isModified():
                if self.objectRemovedOnServer(obj):
                    obj.markNew() # Will be uploaded on second pass
                else:
                    self.objectList.remove(obj)
            else:
                self.objectList.remove(obj)

        return 200

    def doResolveConflict(self, obj, local, result):
        """Called when an object has been modified both on server and
        client. Must return a domain object to replace both."""

        raise NotImplementedError

    def objectRemovedOnServer(self, obj):
        """Called when an object has been removed on server and
        locally modified. Return True to keep the object alive."""

        raise NotImplementedError

    def objectRemovedOnClient(self, obj):
        """Called when an object has been removed on client and
        remotely modified. Return True to keep the object alive."""

        raise NotImplementedError

    def setItemStatus(self, key, status):
        self.callback.pulse()

        if self.state in [self.STATE_NORMAL, self.STATE_SECONDPASS]:
            obj = self._getObject(key)

            if status in [200, 201, 211, 418]:
                # 200: Generic OK
                # 201: Added.
                # 211: Item not deleted (not found)
                # 418: Already exists.

                if obj.isDeleted():
                    self.objectList.remove(obj)
                else:
                    obj.cleanDirty()

                return 200

            print 'UNHANDLED ITEM STATUS %s %d' % (key, status)

            return 501
        else:
            raise RuntimeError, 'This shouldn\'t happen'
