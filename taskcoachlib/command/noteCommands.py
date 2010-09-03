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
from taskcoachlib.domain import note
import base


class NewNoteCommand(base.NewItemCommand):
    singular_name = _('New note')
    
    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New note'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        categories = kwargs.get('categories',  None)
        super(NewNoteCommand, self).__init__(*args, **kwargs)
        self.items = self.notes = [note.Note(subject=subject,
            description=description, categories=categories, 
            attachments=attachments)]
        

class NewSubNoteCommand(base.NewSubItemCommand):
    plural_name = _('New subnotes')
    singular_name = _('New subnote of "%s"')

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New subnote'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        categories = kwargs.get('categories',  None)
        super(NewSubNoteCommand, self).__init__(*args, **kwargs)
        self.items = self.notes = [parent.newChild(subject=subject,
            description=description, categories=categories,
            attachments=attachments) for parent in self.items]
        

class EditNoteCommand(base.EditCommand):
    plural_name = _('Edit notes')
    singular_name = _('Edit note "%s"')

    def __init__(self, *args, **kwargs):
        super(EditNoteCommand, self).__init__(*args, **kwargs)
        self.notes = self.items
            
    def getItemsToSave(self):
        return self.items


class DeleteNoteCommand(base.DeleteCommand):
    plural_name = _('Delete notes')
    singular_name = _('Delete note "%s"')
    
    
class DragAndDropNoteCommand(base.DragAndDropCommand):
    plural_name = _('Drag and drop notes')
    singular_name = _('Drag and drop note "%s"')
