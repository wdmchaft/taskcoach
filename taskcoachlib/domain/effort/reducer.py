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
from taskcoachlib.domain import date, task
import effortlist, composite


class EffortAggregator(patterns.SetDecorator, 
                       effortlist.EffortUICommandNamesMixin):
    ''' This class observes an TaskList and aggregates the individual effort
        records to CompositeEfforts, e.g. per day or per week. '''
    def __init__(self, *args, **kwargs):
        self.__composites = {}
        aggregation = kwargs.pop('aggregation')
        assert aggregation in ('day', 'week', 'month')
        aggregation = aggregation.capitalize()
        self.startOfPeriod = getattr(date.DateTime, 'startOf%s'%aggregation)
        self.endOfPeriod = getattr(date.DateTime, 'endOf%s'%aggregation)
        super(EffortAggregator, self).__init__(*args, **kwargs)
        patterns.Publisher().registerObserver(self.onCompositeEmpty,
            eventType='effort.composite.empty')
        patterns.Publisher().registerObserver(self.onEffortAddedToTask, 
            eventType='task.effort.add')
        patterns.Publisher().registerObserver(self.onChildAddedToTask,
            eventType=task.Task.addChildEventType())
        patterns.Publisher().registerObserver(self.onEffortStartChanged, 
            eventType='effort.start')
    
    @patterns.eventSource    
    def extend(self, efforts, event=None): # pylint: disable-msg=W0221
        for effort in efforts:
            effort.task().addEffort(effort, event=event)

    @patterns.eventSource            
    def removeItems(self, efforts, event=None): # pylint: disable-msg=W0221
        for effort in efforts:
            effort.task().removeEffort(effort, event=event)
            
    def extendSelf(self, tasks, event=None):
        ''' extendSelf is called when an item is added to the observed
            list. The default behavior of extendSelf is to add the item
            to the observing list (i.e. this list) unchanged. We override 
            the default behavior to first get the efforts from the task
            and then group the efforts by time period. '''
        newComposites = []
        for task in tasks: # pylint: disable-msg=W0621
            newComposites.extend(self.createComposites(task, task.efforts()))
        super(EffortAggregator, self).extendSelf(newComposites, event)

    @patterns.eventSource
    def removeItemsFromSelf(self, tasks, event=None):
        ''' removeItemsFromSelf is called when an item is removed from the 
            observed list. The default behavior of removeItemsFromSelf is to 
            remove the item from the observing list (i.e. this list)
            unchanged. We override the default behavior to remove the 
            tasks' efforts from the CompositeEfforts they are part of. '''
        for task in tasks: # pylint: disable-msg=W0621
            self.removeComposites(task, task.efforts(), event=event)

    def onEffortAddedToTask(self, event):
        newComposites = []
        for task in event.sources(): # pylint: disable-msg=W0621
            if task in self.observable():
                efforts = event.values(task)
                newComposites.extend(self.createComposites(task, efforts))
        super(EffortAggregator, self).extendSelf(newComposites)
        
    def onChildAddedToTask(self, event):
        newComposites = []
        for task in event.sources(): # pylint: disable-msg=W0621
            if task in self.observable():
                child = event.value(task)
                newComposites.extend(self.createComposites(task,
                    child.efforts(recursive=True)))
        super(EffortAggregator, self).extendSelf(newComposites)

    def onCompositeEmpty(self, event):
        # pylint: disable-msg=W0621
        composites = [composite for composite in event.sources() if \
                      composite in self]
        keys = [self.keyForComposite(composite) for composite in composites]
        # A composite may already have been removed, e.g. when a
        # parent and child task have effort in the same period
        keys = [key for key in keys if key in self.__composites]
        for key in keys:
            del self.__composites[key]
        super(EffortAggregator, self).removeItemsFromSelf(composites)
        
    def onEffortStartChanged(self, event):
        newComposites = []
        for effort in event.sources():
            key = self.keyForEffort(effort)
            task = effort.task() # pylint: disable-msg=W0621
            if (task in self.observable()) and (key not in self.__composites):
                newComposites.extend(self.createComposites(task, [effort]))
        super(EffortAggregator, self).extendSelf(newComposites)
            
    def createComposites(self, task, efforts): # pylint: disable-msg=W0621
        newComposites = []
        taskAndAncestors = [task] + task.ancestors()
        for effort in efforts:
            for task in taskAndAncestors:
                newComposites.extend(self.createComposite(effort, task))
            newComposites.extend(self.createCompositeForPeriod(effort))
        return newComposites

    def createComposite(self, anEffort, task): # pylint: disable-msg=W0621
        key = self.keyForEffort(anEffort, task)
        if key in self.__composites:
            return []
        newComposite = composite.CompositeEffort(*key) # pylint: disable-msg=W0142
        self.__composites[key] = newComposite
        return [newComposite]
    
    def createCompositeForPeriod(self, anEffort):
        key = self.keyForPeriod(anEffort)
        if key in self.__composites:
            return []
        newCompositePerPeriod = composite.CompositeEffortPerPeriod(key[0], key[1], self.observable())
        self.__composites[key] = newCompositePerPeriod
        return [newCompositePerPeriod]

    def removeComposites(self, task, efforts, event): # pylint: disable-msg=W0621
        taskAndAncestors = [task] + task.ancestors()
        for effort in efforts:
            for task in taskAndAncestors:
                self.removeComposite(effort, task, event)

    def removeComposite(self, anEffort, task, event): # pylint: disable-msg=W0613,W0621
        key = self.keyForEffort(anEffort, task)
        if key not in self.__composites:
            # A composite may already have been removed, e.g. when a
            # parent and child task have effort in the same period
            return
        compositeToRemove = self.__composites.pop(key)
        # FIXME: Can't pass event to removeItemsFromSelf, because 
        # otherwise 
        super(EffortAggregator, self).removeItemsFromSelf([compositeToRemove])#, event)

    def maxDateTime(self):
        stopTimes = [effort.getStop() for compositeEffort in self for effort
            in compositeEffort if effort.getStop() is not None]
        if stopTimes:
            return max(stopTimes)
        else:
            return None

    @staticmethod
    def keyForComposite(compositeEffort):
        if compositeEffort.task().__class__.__name__ == 'Total':
            return (compositeEffort.getStart(), compositeEffort.getStop())
        else:
            return (compositeEffort.task(), compositeEffort.getStart(), 
                    compositeEffort.getStop())
    
    def keyForEffort(self, effort, task=None): # pylint: disable-msg=W0621
        task = task or effort.task()
        effortStart = effort.getStart()
        return (task, self.startOfPeriod(effortStart), 
            self.endOfPeriod(effortStart))
        
    def keyForPeriod(self, effort):
        key = self.keyForEffort(effort)
        return key[1], key[2]
    
    @classmethod
    def sortEventType(class_):
        return 'this event type is not used' 

