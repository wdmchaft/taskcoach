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
from taskcoachlib.domain import base, date
import task


class ViewFilter(base.Filter):
    def __init__(self, *args, **kwargs):
        self.__dueDateTimeFilter = self.stringToDueDateTime(kwargs.pop('dueDateTimeFilter', 
                                                                       'Unlimited'))
        self.__hideCompletedTasks = kwargs.pop('hideCompletedTasks', False)
        self.__hideInactiveTasks = kwargs.pop('hideInactiveTasks', False)
        self.__hideActiveTasks = kwargs.pop('hideActiveTasks', False)
        self.__hideCompositeTasks = kwargs.pop('hideCompositeTasks', False)
        self.registerObservers()
        super(ViewFilter, self).__init__(*args, **kwargs)
        
    def registerObservers(self):
        publisher = patterns.Publisher()
        for eventType in ('task.dueDateTime', 'task.startDateTime', 
                          'task.completionDateTime', 'task.prerequisites',
                          task.Task.addChildEventType(),
                          task.Task.removeChildEventType(),
                          'clock.minute'):
            publisher.registerObserver(self.onTaskStatusChange,
                eventType=eventType)

    def onTaskStatusChange(self, event): # pylint: disable-msg=W0613
        self.reset()
        
    def setFilteredByDueDateTime(self, dueDateTimeString):
        self.__dueDateTimeFilter = self.stringToDueDateTime(dueDateTimeString)
        self.reset()
    
    def hideInactiveTasks(self, hide=True):
        self.__hideInactiveTasks = hide
        self.reset()

    def hideActiveTasks(self, hide=True):
        self.__hideActiveTasks = hide
        self.reset()
        
    def hideCompletedTasks(self, hide=True):
        self.__hideCompletedTasks = hide
        self.reset()
        
    def hideCompositeTasks(self, hide=True):
        self.__hideCompositeTasks = hide
        self.reset()
        
    def filter(self, tasks):
        return [task for task in tasks if self.filterTask(task)] # pylint: disable-msg=W0621
    
    def filterTask(self, task): # pylint: disable-msg=W0621
        result = True
        if self.__hideCompletedTasks and task.completed():
            result = False
        elif self.__hideInactiveTasks and task.inactive():
            result = False
        elif self.__hideActiveTasks and task.active():
            result = False
        elif self.__hideCompositeTasks and not self.treeMode() and task.children():
            result = False
        elif task.dueDateTime(recursive=self.treeMode()) > self.__dueDateTimeFilter():
            result = False
        return result

    @staticmethod
    def stringToDueDateTime(dueDateTimeString):
        # pylint: disable-msg=W0108
        dateTimeFactory = {'Today' : lambda: date.Now().endOfDay(), 
                           'Tomorrow' : lambda: date.Now().endOfTomorrow(),
                           'Workweek' : lambda: date.Now().endOfWorkWeek(), 
                           'Week' : lambda: date.Now().endOfWeek(), 
                           'Month' : lambda: date.Now().endOfMonth(), 
                           'Year' : lambda: date.Now().endOfYear(), 
                           'Unlimited' : date.DateTime }        
        return dateTimeFactory[dueDateTimeString]
