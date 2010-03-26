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

from taskcoachlib import patterns
from taskcoachlib.domain import base, date
import task


class ViewFilter(base.Filter):
    def __init__(self, *args, **kwargs):
        self.__dueDateFilter = self.stringToDueDate(kwargs.pop('dueDateFilter', 
                                                               'Unlimited'))
        self.__hideCompletedTasks = kwargs.pop('hideCompletedTasks', False)
        self.__hideInactiveTasks = kwargs.pop('hideInactiveTasks', False)
        self.__hideActiveTasks = kwargs.pop('hideActiveTasks', False)
        self.__hideCompositeTasks = kwargs.pop('hideCompositeTasks', False)
        for eventType in ('task.dueDate', 'task.startDate', 
                          'task.completionDate', 
                          task.Task.addChildEventType(),
                          task.Task.removeChildEventType()):
            patterns.Publisher().registerObserver(self.onTaskChange,
                eventType=eventType)
        super(ViewFilter, self).__init__(*args, **kwargs)

    def onTaskChange(self, event):
        tasks = event.sources()
        newEvent = patterns.Event()
        tasksToRemove = [task for task in tasks if not self.filterTask(task)] # pylint: disable-msg=W0621
        self.removeItemsFromSelf(tasksToRemove, newEvent)
        tasksToAdd = [task for task in tasks if self.filterTask(task) \
                      and task in self.observable() and task not in self]
        self.extendSelf(tasksToAdd, newEvent)
        newEvent.send()
            
    def setFilteredByDueDate(self, dueDateString):
        self.__dueDateFilter = self.stringToDueDate(dueDateString)
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
        elif task.dueDate(recursive=self.treeMode()) > self.__dueDateFilter:
            result = False
        return result

    @staticmethod
    def stringToDueDate(dueDateString):
        dateFactory = { 'Today' : date.Today, 
                        'Tomorrow' : date.Tomorrow,
                        'Workweek' : date.NextFriday, 
                        'Week' : date.NextSunday, 
                        'Month' : date.LastDayOfCurrentMonth, 
                        'Year' : date.LastDayOfCurrentYear, 
                        'Unlimited' : date.Date }        
        return dateFactory[dueDateString]()
