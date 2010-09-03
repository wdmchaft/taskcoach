'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
from taskcoachlib.domain import date, base
import base as baseeffort
    

class Effort(baseeffort.BaseEffort, base.Object):
    def __init__(self, task=None, start=None, stop=None, *args, **kwargs):
        super(Effort, self).__init__(task, start or date.DateTime.now(), stop, 
            *args, **kwargs)

    @patterns.eventSource
    def setTask(self, task, event=None):
        if self._task is None: 
            # We haven't been fully initialised yet, so allow setting of the
            # task, without notifying observers. Also, don't call addEffort()
            # on the new task, because we assume setTask was invoked by the
            # new task itself.
            self._task = task
            return
        if task in (self._task, None): 
            # command.PasteCommand may try to set the parent to None
            return
        self._task.removeEffort(self, event=event)
        self._task = task
        self._task.addEffort(self, event=event)
        event.addSource(self, task, type=self.taskChangedEventType())
        
    setParent = setTask # FIXME: should we create a common superclass for Effort and Task?
    
    @classmethod
    def taskChangedEventType(class_):
        return '%s.task'%class_
    
    def __str__(self):
        return 'Effort(%s, %s, %s)'%(self._task, self._start, self._stop)
    
    __repr__ = __str__
        
    def __getstate__(self):
        state = super(Effort, self).__getstate__()
        state.update(dict(task=self._task, start=self._start, stop=self._stop))
        return state

    @patterns.eventSource
    def __setstate__(self, state, event=None):
        super(Effort, self).__setstate__(state, event=event)
        self.setTask(state['task'], event=event)
        self.setStart(state['start'], event=event)
        self.setStop(state['stop'], event=event)

    def __getcopystate__(self):
        state = super(Effort, self).__getcopystate__()
        state.update(dict(task=self._task, start=self._start, stop=self._stop))
        return state
   
    def duration(self, now=date.DateTime.now):
        stop = self._stop if self._stop else now()
        return stop - self._start
     
    @patterns.eventSource   
    def setStart(self, startDateTime, event=None):
        if startDateTime == self._start:
            return
        self._start = startDateTime
        self.task().timeSpentEvent(event, self)
        event.addSource(self, self._start, type='effort.start')
        event.addSource(self, self.duration(), type='effort.duration')
        if self.task().hourlyFee():
            self.revenueEvent(event)

    @patterns.eventSource        
    def setStop(self, newStop=None, event=None):
        if newStop is None:
            newStop = date.DateTime.now()
        elif newStop == date.DateTime.max:
            newStop = None
        if newStop == self._stop:
            return
        previousStop = self._stop
        self._stop = newStop
        if newStop == None:
            event.addSource(self, type=self.trackStartEventType())
            self.task().startTrackingEvent(event, self)
        elif previousStop == None:
            event.addSource(self, type=self.trackStopEventType())
            self.task().stopTrackingEvent(event, self)
        self.task().timeSpentEvent(event, self)
        event.addSource(self, newStop, type='effort.stop')
        event.addSource(self, self.duration(), type='effort.duration')
        if self.task().hourlyFee():
            self.revenueEvent(event)
        
    def isBeingTracked(self, recursive=False): # pylint: disable-msg=W0613
        return self._stop is None

    def revenue(self):
        task = self.task()
        variableRevenue = self.duration().hours() * task.hourlyFee()
        if task.timeSpent().hours() > 0:
            fixedRevenue = self.duration().hours() / \
                task.timeSpent().hours() * task.fixedFee()
        else:
            fixedRevenue = 0
        return variableRevenue + fixedRevenue
    
    def revenueEvent(self, event):
        event.addSource(self, self.revenue(), type='effort.revenue')
            
    @classmethod    
    def modificationEventTypes(class_):
        eventTypes = super(Effort, class_).modificationEventTypes()
        return eventTypes + [class_.taskChangedEventType(), 
                             'effort.start', 'effort.stop']
 
