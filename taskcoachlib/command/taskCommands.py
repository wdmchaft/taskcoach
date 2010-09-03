# -*- coding: utf-8 -*-

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


from taskcoachlib.i18n import _
from taskcoachlib.domain import task, effort, date
import base


class SaveTaskStateMixin(base.SaveStateMixin, base.CompositeMixin):
    pass


class EffortCommand(base.BaseCommand): # pylint: disable-msg=W0223
    def stopTracking(self):
        self.stoppedEfforts = [] # pylint: disable-msg=W0201
        for taskToStop in self.tasksToStopTracking():
            self.stoppedEfforts.extend(taskToStop.activeEfforts())
            taskToStop.stopTracking()

    def startTracking(self):
        for stoppedEffort in self.stoppedEfforts:
            stoppedEffort.setStop(date.DateTime.max)
    
    def tasksToStopTracking(self):
        return self.list
                
    def do_command(self):
        self.stopTracking()
    
    def undo_command(self):
        self.startTracking()
        
    def redo_command(self):
        self.stopTracking()


class DragAndDropTaskCommand(base.DragAndDropCommand):
    plural_name = _('Drag and drop tasks')


class DeleteTaskCommand(base.DeleteCommand, EffortCommand):
    plural_name = _('Delete tasks')
    singular_name = _('Delete task "%s"')

    def tasksToStopTracking(self):
        return self.items

    # Mmmh,  these 3  methods  are copied  from EffortCommand  because
    # DeleteCommand does not call  super(). There is probably a better
    # way to do this.

    def do_command(self):
        super(DeleteTaskCommand, self).do_command()
        self.stopTracking()
    
    def undo_command(self):
        super(DeleteTaskCommand, self).undo_command()
        self.startTracking()
        
    def redo_command(self):
        super(DeleteTaskCommand, self).redo_command()
        self.stopTracking()


class NewTaskCommand(base.NewItemCommand):
    singular_name = _('New task')
    
    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New task'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        categories = kwargs.pop('categories', [])
        startDateTime = kwargs.pop('startDateTime', date.Now())
        super(NewTaskCommand, self).__init__(*args, **kwargs)
        self.items = [task.Task(subject=subject, description=description, 
                                attachments=attachments, categories=categories,
                                startDateTime=startDateTime, **kwargs)]


class NewSubTaskCommand(base.NewSubItemCommand, SaveTaskStateMixin):
    plural_name = _('New subtasks')
    singular_name = _('New subtask of "%s"')

    def __init__(self, *args, **kwargs):
        super(NewSubTaskCommand, self).__init__(*args, **kwargs)
        subject = kwargs.pop('subject', _('New subtask'))
        self.items = [parent.newChild(subject=subject, **kwargs) for parent in self.items]
        self.saveStates(self.getTasksToSave())
    
    def getTasksToSave(self):
        # FIXME: can be simplified to: return self.getAncestors(self.items) ?
        parents = [item.parent() for item in self.items if item.parent()]
        return parents + self.getAncestors(parents)

    def undo_command(self):
        super(NewSubTaskCommand, self).undo_command()
        self.undoStates()

    def redo_command(self):
        super(NewSubTaskCommand, self).redo_command()
        self.redoStates()


class EditTaskCommand(base.EditCommand):
    plural_name = _('Edit tasks')
    singular_name = _('Edit task "%s"')
    
    def __init__(self, *args, **kwargs):
        super(EditTaskCommand, self).__init__(*args, **kwargs)
        self.oldCategories = [item.categories() for item in self.items]
        
    def do_command(self):
        super(EditTaskCommand, self).do_command()
        self.newCategories = [item.categories() for item in self.items] # pylint: disable-msg=W0201
        self.updateCategories(self.oldCategories, self.newCategories)
        
    def undo_command(self):
        super(EditTaskCommand, self).undo_command()
        self.updateCategories(self.newCategories, self.oldCategories)
        
    def redo_command(self):
        super(EditTaskCommand, self).redo_command()
        self.updateCategories(self.oldCategories, self.newCategories)

    def getItemsToSave(self):
        return set([relative for item in self.items for relative in item.family()])
        
    def updateCategories(self, oldCategories, newCategories):
        for item, categories in zip(self.items, oldCategories):
            for category in categories:
                category.removeCategorizable(item)
        for item, categories in zip(self.items, newCategories):
            for category in categories:
                category.addCategorizable(item)


class MarkCompletedCommand(EditTaskCommand, EffortCommand):
    plural_name = _('Mark tasks completed')
    singular_name = _('Mark "%s" completed')

    def do_command(self):
        super(MarkCompletedCommand, self).do_command()
        for item in self.items:
            if item.completed():
                item.setCompletionDateTime(date.DateTime())
            else:
                item.setCompletionDateTime()

    def tasksToStopTracking(self):
        return self.items


class StartEffortCommand(EffortCommand):
    plural_name = _('Start tracking')
    singular_name = _('Start tracking "%s"')

    def __init__(self, *args, **kwargs):
        super(StartEffortCommand, self).__init__(*args, **kwargs)
        start = date.DateTime.now()
        self.efforts = [effort.Effort(item, start) for item in self.items]
        
    def do_command(self):
        super(StartEffortCommand, self).do_command()
        self.addEfforts()
        
    def undo_command(self):
        self.removeEfforts()
        super(StartEffortCommand, self).undo_command()
        
    def redo_command(self):
        super(StartEffortCommand, self).redo_command()
        self.addEfforts()

    def addEfforts(self):
        for item, newEffort in zip(self.items, self.efforts):
            item.addEffort(newEffort)

    def removeEfforts(self):
        for item, newEffort in zip(self.items, self.efforts):
            item.removeEffort(newEffort)
            
        
class StopEffortCommand(EffortCommand):
    plural_name = _('Stop tracking')
    singular_name = _('Stop tracking "%s"')
                  
    def canDo(self):
        return True # No selected items needed.


class ExtremePriorityCommand(base.BaseCommand): # pylint: disable-msg=W0223
    delta = 'Subclass responsibility'
    
    def __init__(self, *args, **kwargs):
        super(ExtremePriorityCommand, self).__init__(*args, **kwargs)
        self.oldPriorities = [item.priority() for item in self.items]
        self.oldExtremePriority = self.getOldExtremePriority()
        
    def getOldExtremePriority(self):
        raise NotImplementedError # pragma: no cover

    def setNewExtremePriority(self):
        newExtremePriority = self.oldExtremePriority + self.delta 
        for item in self.items:
            item.setPriority(newExtremePriority)

    def restorePriorities(self):
        for item, oldPriority in zip(self.items, self.oldPriorities):
            item.setPriority(oldPriority)

    def do_command(self):
        super(ExtremePriorityCommand, self).do_command()
        self.setNewExtremePriority()
        
    def undo_command(self):
        self.restorePriorities()
        super(ExtremePriorityCommand, self).undo_command()
        
    def redo_command(self):
        super(ExtremePriorityCommand, self).redo_command()
        self.setNewExtremePriority()


class MaxPriorityCommand(ExtremePriorityCommand):
    plural_name = _('Maximize priority')
    singular_name = _('Maximize priority of "%s"')
    
    delta = +1
    
    def getOldExtremePriority(self):
        return self.list.maxPriority()
    

class MinPriorityCommand(ExtremePriorityCommand):
    plural_name = _('Minimize priority')
    singular_name = _('Minimize priority of "%s"')
    
    delta = -1
                    
    def getOldExtremePriority(self):
        return self.list.minPriority()
    

class ChangePriorityCommand(base.BaseCommand): # pylint: disable-msg=W0223
    delta = 'Subclass responsibility'
    
    def changePriorities(self, delta):
        for item in self.items:
            item.setPriority(item.priority() + delta)

    def do_command(self):
        super(ChangePriorityCommand, self).do_command()
        self.changePriorities(self.delta)

    def undo_command(self):
        self.changePriorities(-self.delta)
        super(ChangePriorityCommand, self).undo_command()

    def redo_command(self):
        super(ChangePriorityCommand, self).redo_command()
        self.changePriorities(self.delta)


class IncPriorityCommand(ChangePriorityCommand):
    plural_name = _('Increase priority')
    singular_name = _('Increase priority of "%s"')
    
    delta = +1


class DecPriorityCommand(ChangePriorityCommand):
    plural_name = _('Decrease priority')
    singular_name = _('Decrease priority of "%s"')

    delta = -1
    
    
class AddTaskNoteCommand(base.AddNoteCommand):
    plural_name = _('Add note to tasks')
