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

from taskcoachlib import patterns


class ChangeTracker(patterns.Observer):
    ''' ChangeTracker keeps track of changes to a collection (additions, 
        removals) as well as changes to the items in the collection. To be used
        for synchronization. '''
         
    def __init__(self, collection):
        super(ChangeTracker, self).__init__()
        self.__collection = collection
        self.__added = set()
        self.reset()
        self.registerForCollectionChanges()
        self.registerForItemChanges()
        
    def reset(self): 
        self.registerForItemChanges([item for item in self.__collection \
                                     if item.id() in self.__added])
        self.__added = set()
        # pylint: disable-msg=W0201
        self.__removed = set()
        self.__modified = set()
        
    def registerForCollectionChanges(self):
        for handler, eventType in \
                [(self.onAddItem, self.__collection.addItemEventType()),
                 (self.onRemoveItem, self.__collection.removeItemEventType())]:
            self.registerObserver(handler, eventType, eventSource=self.__collection)
            
    def registerForItemChanges(self, items=None, register=True):
        items = items or self.__collection
        if register:
            changeObservation = self.registerObserver
        else:
            changeObservation = self.removeObserver
        for item in items:
            for eventType in item.modificationEventTypes():
                changeObservation(self.onModifyItem, eventType, eventSource=item)
                    
    def onAddItem(self, event):
        self.__added |= set([item.id() for item in event.values()])
    
    def onRemoveItem(self, event):
        items = event.values()
        self.registerForItemChanges(items, register=False)
        removedItemIds = set([item.id() for item in items])
        removedItemIdsToRemember = removedItemIds - self.__added
        self.__removed |= removedItemIdsToRemember
        self.__added -= removedItemIds
        self.__modified -= removedItemIds
        
    def onModifyItem(self, event):
        self.__modified |= set([item.id() for item in event.sources()])
        
    def added(self):
        return self.__added
    
    def removed(self):
        return self.__removed
    
    def modified(self):
        return self.__modified
    
