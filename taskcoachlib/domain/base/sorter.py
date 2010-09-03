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


class Sorter(patterns.ListDecorator):
    ''' This class decorates a list and sorts its contents. '''
    
    def __init__(self, *args, **kwargs):
        self._sortKey = kwargs.pop('sortBy', 'subject')
        self._sortAscending = kwargs.pop('sortAscending', True)
        self._sortCaseSensitive = kwargs.pop('sortCaseSensitive', True)
        super(Sorter, self).__init__(*args, **kwargs)
        self._registerObserverForAttribute(self._sortKey)
        self.reset()

    @classmethod        
    def sortEventType(class_):
        return '%s.sorted'%class_
    
    @patterns.eventSource
    def extendSelf(self, items, event=None):
        super(Sorter, self).extendSelf(items, event)
        self.reset(event=event)

    # We don't implement removeItemsFromSelf() because there is no need 
    # to resort when items are removed since after removing items the 
    # remaining items are still in the right order.

    def sortBy(self, sortKey):
        if sortKey == self._sortKey:
            return # no need to sort
        self._removeObserverForAttribute(self._sortKey)
        self._registerObserverForAttribute(sortKey)
        self._sortKey = sortKey
        self.reset()

    def sortAscending(self, ascending):
        self._sortAscending = ascending
        self.reset()
        
    def sortCaseSensitive(self, caseSensitive):
        self._sortCaseSensitive = caseSensitive
        self.reset()
    
    @patterns.eventSource
    def reset(self, event=None):
        ''' reset does the actual sorting. If the order of the list changes, 
            observers are notified by means of the list-sorted event. '''
        oldSelf = self[:]
        self.sort(key=self.createSortKeyFunction(), 
                  reverse=not self._sortAscending)
        if self != oldSelf:
            event.addSource(self, type=self.sortEventType())

    def createSortKeyFunction(self):
        ''' createSortKeyFunction returns a function that is passed to the 
            builtin list.sort method to extract the sort key from each element
            in the list. '''
        if self._sortCaseSensitive:
            return lambda item: item.subject()
        else:
            return lambda item: item.subject().lower()

    def _registerObserverForAttribute(self, attribute):
        eventType = self._createEventTypeFromAttribute(attribute)
        patterns.Publisher().registerObserver(self.onAttributeChanged, 
                                              eventType=eventType)
            
    def _removeObserverForAttribute(self, attribute):
        eventType = self._createEventTypeFromAttribute(attribute)
        patterns.Publisher().removeObserver(self.onAttributeChanged, 
                                            eventType=eventType)
        
    def onAttributeChanged(self, event): # pylint: disable-msg=W0613
        self.reset()

    def _createEventTypeFromAttribute(self, attribute):
        ''' At the moment, there are two ways event types are specified: 
            1) by means of a simple, dot-separated, string. For example 
            "task.subject", or 
            2) by means of a method that returns an event type string. For
            example task.Task.subjectChangedEventType(). This method tries both
            options to get the event type. '''
        try:
            return getattr(self.DomainObjectClass, '%sChangedEventType'%attribute)()
        except AttributeError:
            return '%s.%s'%(self.EventTypePrefix, attribute) # FIXME: to be removed when no event type strings are used anymore.


class TreeSorter(Sorter):
    def rootItems(self):
        return [item for item in self if item.parent() is None]
