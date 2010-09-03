# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 João Alexandre de Toledo <jtoledo@griffo.com.br>

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
from taskcoachlib.i18n import _
from taskcoachlib.domain import categorizable
import task


def accelerator(modifier, key, macKey=None):
    # There is a bug in wxWidget/wxPython on the Mac that causes the 
    # INSERT accelerator to be mapped so some other key sequence ('c' in
    # this case) so that whenever that key sequence is typed, this command
    # is invoked. Hence, we use a different accelarator on the Mac.
    macKey = macKey if macKey else key
    return u'\t%s+%s'%(modifier, macKey if '__WXMAC__' == wx.Platform else key)


class TaskList(categorizable.CategorizableContainer):
    # FIXME: TaskList should be called TaskCollection or TaskSet

    newItemMenuText = _('&New task...') + accelerator('Ctrl', 'INS', 'N')
    newItemHelpText = _('Insert a new task')
    editItemMenuText = _('&Edit task...')
    editItemHelpText = _('Edit the selected task(s)')
    deleteItemMenuText = _('&Delete task') + accelerator('Ctrl', 'DEL')
    deleteItemHelpText = _('Delete the selected task(s)')
    newSubItemMenuText = _('New &subtask...') + accelerator('Shift+Ctrl', 'INS', 'N')
    newSubItemHelpText = _('Insert a new subtask into the selected task')
    
    def _nrInterestingTasks(self, isInteresting):
        return len(self._getInterestingTasks(isInteresting))
    
    def _getInterestingTasks(self, isInteresting):
        return [task for task in self if isInteresting(task)] # pylint: disable-msg=W0621

    def nrCompleted(self):
        return self._nrInterestingTasks(task.Task.completed)

    def nrOverdue(self):
        return self._nrInterestingTasks(task.Task.overdue)
    
    def nrActive(self):
        return self._nrInterestingTasks(task.Task.active)

    def nrInactive(self):
        return self._nrInterestingTasks(task.Task.inactive)

    def nrDueSoon(self):
        return self._nrInterestingTasks(task.Task.dueSoon)
    
    def nrBeingTracked(self):
        return self._nrInterestingTasks(task.Task.isBeingTracked)
    
    def tasksBeingTracked(self):
        return self._getInterestingTasks(task.Task.isBeingTracked)        

    def allCompleted(self):
        nrCompleted = self.nrCompleted()
        return nrCompleted > 0 and nrCompleted == len(self)
            
    def efforts(self):
        result = []
        for task in self: # pylint: disable-msg=W0621
            result.extend(task.efforts())
        return result
        
    def originalLength(self):
        ''' Provide a way for bypassing the __len__ method of decorators. '''
        return len([t for t in self if not t.isDeleted()])
    
    def minPriority(self):
        return min(self.__allPriorities())
        
    def maxPriority(self):
        return max(self.__allPriorities())
        
    def __allPriorities(self):
        return [task.priority() for task in self if not task.isDeleted()] or (0,) # pylint: disable-msg=W0621
