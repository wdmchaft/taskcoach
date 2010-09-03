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
from taskcoachlib.domain import effort
import base


class NewEffortCommand(base.BaseCommand):
    plural_name = _('New efforts')
    singular_name = _('New effort of "%s"')
    
    def __init__(self, *args, **kwargs):
        super(NewEffortCommand, self).__init__(*args, **kwargs)
        self.items = self.efforts = [effort.Effort(task) for task in self.items]

    def name_subject(self, effort):
        return effort.task().subject()
        
    def do_command(self):
        for effort in self.efforts: # pylint: disable-msg=W0621
            effort.task().addEffort(effort)
            
    def undo_command(self):
        for effort in self.efforts: # pylint: disable-msg=W0621
            effort.task().removeEffort(effort)
            
    redo_command = do_command


class EditEffortCommand(base.BaseCommand, base.SaveStateMixin):
    plural_name = _('Edit efforts')
    singular_name = _('Edit effort "%s"')
    
    def __init__(self, *args, **kwargs):
        super(EditEffortCommand, self).__init__(*args, **kwargs)
        self.saveStates(self.getEffortsToSave())
        self.efforts = self.items # FIXME: hack
        # FIXME: EditEffortCommand doesn't need the (effort)list argument

    def getEffortsToSave(self):
        return self.items

    def do_command(self):
        pass

    def undo_command(self):
        self.undoStates()

    def redo_command(self):
        self.redoStates()
    

class DeleteEffortCommand(base.DeleteCommand):
    plural_name = _('Delete efforts')
    singular_name = _('Delete effort "%s"')
