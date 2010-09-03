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
from taskcoachlib.domain import category
import base


class NewCategoryCommand(base.NewItemCommand):
    singular_name = _('New category')
    
    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New category'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        super(NewCategoryCommand, self).__init__(*args, **kwargs)
        self.items = self.createNewCategories(subject=subject, 
            description=description, attachments=attachments)

    def createNewCategories(self, **kwargs):
        return [category.Category(**kwargs)]
        

class NewSubCategoryCommand(base.NewSubItemCommand):
    plural_name = _('New subcategories')
    singular_name = _('New subcategory of "%s"')

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New subcategory'))
        description = kwargs.pop('description', '')
        attachments = kwargs.pop('attachments', [])
        super(NewSubCategoryCommand, self).__init__(*args, **kwargs)
        self.items = self.createNewCategories(subject=subject,
            description=description, attachments=attachments)

    def createNewCategories(self, **kwargs):
        return [parent.newChild(**kwargs) for parent in self.items]


class EditCategoryCommand(base.EditCommand):
    plural_name = _('Edit categories')
    singular_name = _('Edit category "%s"')
    
    def getItemsToSave(self):
        return self.items


class DeleteCategoryCommand(base.DeleteCommand):
    plural_name = _('Delete categories')
    singular_name = _('Delete category "%s"')
    
    
class DragAndDropCategoryCommand(base.DragAndDropCommand):
    plural_name = _('Drag and drop categories')


class AddCategoryNoteCommand(base.AddNoteCommand):
    plural_name = _('Add note to categories')
        

