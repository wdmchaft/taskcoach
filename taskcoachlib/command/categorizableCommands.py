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

from taskcoachlib.i18n import _
from taskcoachlib import patterns
import base


class ToggleCategoryCommand(base.BaseCommand):
    def name(self):
        return _('Toggle category')
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        super(ToggleCategoryCommand, self).__init__(*args, **kwargs) 
        # Keep track of previous category per categorizable in case of mutual 
        # exclusive categories:
        self.__previous_categories = dict()
        
    def do_command(self):
        self.toggle_category()
        
    undo_command = redo_command = do_command
        
    def toggle_category(self):
        event = patterns.Event()
        for categorizable in self.items:
            if self.category in categorizable.categories():
                self.unlink_category(self.category, categorizable, event)
                self.relink_previous_categories(categorizable, event)
            else:
                self.link_category(self.category, categorizable, event)
                self.unlink_previous_categories(categorizable, event)
        event.send()
        
    def unlink_previous_categories(self, categorizable, event):
        ''' Remove categorizable from any mutual exclusive categories it might
            belong to. '''
        if self.category.isMutualExclusive():
            parent = self.category.parent()
            if parent in categorizable.categories() and not parent.isMutualExclusive():
                self.unlink_previous_category(parent, categorizable, event)
            else:
                self.unlink_previous_mutual_exclusive_category(self.category.siblings(recursive=True), categorizable, event)
        if self.category.hasExclusiveSubcategories():
            self.unlink_previous_mutual_exclusive_category(self.category.children(), categorizable, event)
                
    def unlink_previous_mutual_exclusive_category(self, categories, categorizable, event):
        ''' Look for the category that categorizable belongs to and remove
            categorizable from it. '''
        for category in categories:
            if categorizable in category.categorizables():
                self.unlink_previous_category(category, categorizable, event)
                
    def unlink_previous_category(self, category, categorizable, event):
        ''' Remove categorizable from category, but remember the category so
            it can be restored later. '''
        self.unlink_category(category, categorizable, event)
        self.__previous_categories.setdefault(categorizable, []).append(category)
            
    def relink_previous_categories(self, categorizable, event):
        ''' Re-add categorizable to its previous categories. ''' 
        if categorizable in self.__previous_categories:
            for previous_category in self.__previous_categories[categorizable]:
                self.link_category(previous_category, categorizable, event)

    def link_category(self, category, categorizable, event):
        ''' Make categorizable belong to category. '''
        category.addCategorizable(categorizable, event=event)
        categorizable.addCategory(category, event=event)
        
    def unlink_category(self, category, categorizable, event):
        ''' Make categorizable no longer belong to category. '''
        category.removeCategorizable(categorizable, event=event)
        categorizable.removeCategory(category, event=event)
