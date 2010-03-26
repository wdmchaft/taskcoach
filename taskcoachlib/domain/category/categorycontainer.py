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

from taskcoachlib.domain import base
from taskcoachlib.i18n import _
from taskcoachlib import patterns


class CategoryList(base.Collection):
    newItemMenuText = _('New category...')
    newItemHelpText =  _('Insert a new category')
    editItemMenuText = _('Edit category...')
    editItemHelpText = _('Edit the selected categories')
    deleteItemMenuText = _('Delete category')
    deleteItemHelpText = _('Delete the selected categories')
    newSubItemMenuText = _('New subcategory...')
    newSubItemHelpText = _('Insert a new subcategory')
    
    def extend(self, categories, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CategoryList, self).extend(categories, event)
        for category in self._compositesAndAllChildren(categories):
            for categorizable in category.categorizables():
                categorizable.addCategory(category, event=event)
        if notify:
            event.send()
                
    def removeItems(self, categories, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CategoryList, self).removeItems(categories, event)
        for category in self._compositesAndAllChildren(categories):
            for categorizable in category.categorizables():
                categorizable.removeCategory(category, event=event)
        if notify:
            event.send()

    def findCategoryByName(self, name):
        for category in self:
            if category.subject() == name:
                return category
        return None
    
    def filteredCategories(self):
        return [category for category in self if category.isFiltered()]
