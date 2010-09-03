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
from taskcoachlib.i18n import _                   


class MaxDateTimeMixin(object):
    def maxDateTime(self):
        stopTimes = [effort.getStop() for effort in self if effort.getStop() is not None]
        return max(stopTimes) if stopTimes else None


class EffortUICommandNamesMixin(object):
    newItemMenuText = _('&New effort...\tCtrl+E')
    newItemHelpText =  _('Add an effort period to the selected task(s)')
    editItemMenuText = _('&Edit effort...')
    editItemHelpText = _('Edit the selected effort period(s)')
    deleteItemMenuText = _('&Delete effort')
    deleteItemHelpText = _('Delete the selected effort period(s)')
    newSubItemMenuText = ''
    newSubItemHelpText = '' 
    
                        
class EffortList(patterns.SetDecorator, MaxDateTimeMixin, 
                 EffortUICommandNamesMixin):
    ''' EffortList observes a TaskList and contains all effort records of
        all tasks in the underlying TaskList. '''

    def  __init__(self, *args, **kwargs):
        super(EffortList, self).__init__(*args, **kwargs)
        patterns.Publisher().registerObserver(self.onAddEffortToTask, 
            eventType='task.effort.add')
        patterns.Publisher().registerObserver(self.onRemoveEffortFromTask,
            eventType='task.effort.remove')
    
    def extendSelf(self, tasks, event=None):
        ''' This method is called when a task is added to the observed list.
            It overrides ObservableListObserver.extendSelf whose default 
            behaviour is to add the item that is added to the observed 
            list to the observing list (this list) unchanged. But we want to 
            add the efforts of the tasks, rather than the tasks themselves. '''
        effortsToAdd = []
        for task in tasks:
            effortsToAdd.extend(task.efforts())
        super(EffortList, self).extendSelf(effortsToAdd, event)
        
    def removeItemsFromSelf(self, tasks, event=None):
        ''' This method is called when a task is removed from the observed 
            list. It overrides ObservableListObserver.removeItemsFromSelf 
            whose default behaviour is to remove the item that was removed
            from the observed list from the observing list (this list) 
            unchanged. But we want to remove the efforts of the tasks, rather 
            than the tasks themselves. '''
        effortsToRemove = []
        for task in tasks:
            effortsToRemove.extend(task.efforts())
        super(EffortList, self).removeItemsFromSelf(effortsToRemove, event)

    def onAddEffortToTask(self, event):
        effortsToAdd = []
        for task in event.sources():
            if task in self.observable():
                effortsToAdd.extend(event.values(task))
        super(EffortList, self).extendSelf(effortsToAdd)
        
    def onRemoveEffortFromTask(self, event):
        effortsToRemove = []
        for task in event.sources():
            if task in self.observable():
                effortsToRemove.extend(event.values(task))
        super(EffortList, self).removeItemsFromSelf(effortsToRemove)

    def originalLength(self):
        ''' Do not delegate originalLength to the underlying TaskList because
            that would return a number of tasks, and not the number of effort 
            records.'''
        return len(self)
        
    @patterns.eventSource
    def removeItems(self, efforts, event=None): # pylint: disable-msg=W0221
        ''' We override ObservableListObserver.removeItems because the default
            implementation is to remove the arguments from the original list,
            which in this case would mean removing efforts from a task list.
            Since that wouldn't work we remove the efforts from the tasks by
            hand. '''
        for effort in efforts:
            effort.task().removeEffort(effort, event=event)

    @patterns.eventSource
    def extend(self, efforts, event=None): # pylint: disable-msg=W0221
        ''' We override ObservableListObserver.extend because the default
            implementation is to add the arguments to the original list,
            which in this case would mean adding efforts to a task list.
            Since that wouldn't work we add the efforts to the tasks by
            hand. '''
        for effort in efforts:
            effort.task().addEffort(effort, event=event)
    
    @classmethod        
    def sortEventType(class_):
        return 'this event type is not used'
