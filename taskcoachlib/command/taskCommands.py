'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jerome Laheurte <fraca7@free.fr>

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


class PasteIntoTaskCommand(base.PasteCommand, base.CompositeMixin):
    def name(self):
        return _('Paste into task')

    def setParentOfPastedItems(self): # pylint: disable-msg=W0221
        newParent = self.items[0]
        super(PasteIntoTaskCommand, self).setParentOfPastedItems(newParent)

    def getItemsToSave(self):
        parents = [parent for parent in [self.items[0]] if parent.completed()]
        return parents + self.getAncestors(parents) + \
            super(PasteIntoTaskCommand, self).getItemsToSave()


class DragAndDropTaskCommand(base.DragAndDropCommand):
    def name(self):
        return _('Drag and drop task')


class DeleteTaskCommand(base.DeleteCommand, EffortCommand):
    def name(self):
        return _('Delete task')

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


class NewTaskCommand(base.BaseCommand):
    def name(self):
        return _('New task')

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New task'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        categories = kwargs.pop('categories', [])
        super(NewTaskCommand, self).__init__(*args, **kwargs)
        self.items = [task.Task(subject=subject, description=description, 
                                attachments=attachments, categories=categories,
                                **kwargs)]

    def do_command(self):
        self.list.extend(self.items)

    def undo_command(self):
        self.list.removeItems(self.items)

    def redo_command(self):
        self.list.extend(self.items)


class NewSubTaskCommand(base.BaseCommand, SaveTaskStateMixin):
    def name(self):
        return _('New subtask')

    def __init__(self, *args, **kwargs):
        super(NewSubTaskCommand, self).__init__(*args, **kwargs)
        subject = kwargs.pop('subject', _('New subtask'))
        self.items = [parent.newChild(subject=subject, **kwargs) for parent in self.items]
        self.saveStates(self.getTasksToSave())
        
    def getTasksToSave(self):
        # FIXME: can be simplified to: return self.getAncestors(self.items) ?
        parents = [item.parent() for item in self.items if item.parent()]
        return parents + self.getAncestors(parents)

    def do_command(self):
        self.list.extend(self.items)

    def undo_command(self):
        self.list.removeItems(self.items)
        self.undoStates()

    def redo_command(self):
        self.list.extend(self.items)
        self.redoStates()


class EditTaskCommand(base.EditCommand):
    def name(self):
        return _('Edit task')
    
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
    def name(self):
        return _('Mark completed')

    def do_command(self):
        super(MarkCompletedCommand, self).do_command()
        for item in self.items:
            if item.completed():
                item.setCompletionDate(date.Date())
            else:
                item.setCompletionDate()

    def tasksToStopTracking(self):
        return self.items


class StartEffortCommand(EffortCommand):
    def name(self):
        return _('Start tracking')

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
    def name(self):
        return _('Stop tracking')
                  
    def canDo(self):
        return True    



class ExtremePriorityCommand(base.BaseCommand): # pylint: disable-msg=W0223
    delta = 'Subclass responsibility'
    
    def __init__(self, *args, **kwargs):
        super(ExtremePriorityCommand, self).__init__(*args, **kwargs)
        self.oldPriorities = [item.priority() for item in self.items]
        self.oldExtremePriority = self.getOldExtremePriority()
        
    def getOldExtremePriority(self):
        raise NotImplementedError

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
    def name(self):
        return _('Maximize priority')
    
    delta = +1
    
    def getOldExtremePriority(self):
        return self.list.maxPriority()
    

class MinPriorityCommand(ExtremePriorityCommand):
    def name(self):
        return _('Minimize priority')
    
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
    def name(self):
        return _('Increase priority')

    delta = +1


class DecPriorityCommand(ChangePriorityCommand):
    def name(self):
        return _('Decrease priority')

    delta = -1
    
    
class AddTaskNoteCommand(base.AddNoteCommand):
    def name(self):
        return _('Add note to task')

