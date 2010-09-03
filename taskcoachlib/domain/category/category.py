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
from taskcoachlib.domain import base, note, attachment


class Category(attachment.AttachmentOwner, note.NoteOwner, base.CompositeObject):
    def __init__(self, subject, categorizables=None, children=None, 
                 filtered=False, parent=None, description='',  
                 exclusiveSubcategories=False, *args, **kwargs):
        super(Category, self).__init__(subject=subject, children=children or [], 
                                       parent=parent, description=description,
                                       *args, **kwargs)
        self.__categorizables = base.SetAttribute(set(categorizables or []),
                                                  self,
                                                  self.categorizableAddedEvent,
                                                  self.categorizableRemovedEvent)
        self.__filtered = filtered
        self.__exclusiveSubcategories = exclusiveSubcategories
            
    @classmethod
    def filterChangedEventType(class_):
        ''' Event type to notify observers that categorizables belonging to
            this category are filtered or not. '''
        return 'category.filter'
    
    @classmethod
    def categorizableAddedEventType(class_):
        ''' Event type to notify observers that categorizables have been added
            to this category. '''
        return 'category.categorizable.added'
    
    @classmethod
    def categorizableRemovedEventType(class_):
        ''' Event type to notify observers that categorizables have been removed
            from this category. ''' 
        return 'category.categorizable.removed'
    
    @classmethod
    def exclusiveSubcategoriesChangedEventType(class_):
        ''' Event type to notify observers that subcategories have become
            exclusive (or vice versa). '''
        return 'category.exclusiveSubcategories'
    
    @classmethod
    def modificationEventTypes(class_):
        eventTypes = super(Category, class_).modificationEventTypes()
        return eventTypes + [class_.filterChangedEventType(),
                             class_.categorizableAddedEventType(),
                             class_.categorizableRemovedEventType(),
                             class_.exclusiveSubcategoriesChangedEventType()]
                
    def __getstate__(self):
        state = super(Category, self).__getstate__()
        state.update(dict(categorizables=self.__categorizables.get(), 
                          filtered=self.__filtered),
                          exclusiveSubcategories=self.__exclusiveSubcategories)
        return state
    
    @patterns.eventSource    
    def __setstate__(self, state, event=None):
        super(Category, self).__setstate__(state, event=event)
        self.setCategorizables(state['categorizables'], event=event)
        self.setFiltered(state['filtered'], event=event)
        self.makeSubcategoriesExclusive(state['exclusiveSubcategories'], event=event)

    def __getcopystate__(self):
        state = super(Category, self).__getcopystate__()
        state.update(dict(categorizables=self.__categorizables.get(), 
                          filtered=self.__filtered))
        return state
            
    def subjectChangedEvent(self, event):
        super(Category, self).subjectChangedEvent(event)
        self.categorySubjectChangedEvent(event)
    
    def categorySubjectChangedEvent(self, event):
        subject = self.subject()
        for eachCategorizable in self.categorizables(recursive=True):
            eachCategorizable.categorySubjectChangedEvent(event, subject)
            eachCategorizable.totalCategorySubjectChangedEvent(event, subject)      
                    
    def categorizables(self, recursive=False):
        result = self.__categorizables.get()
        if recursive:
            for child in self.children():
                result |= child.categorizables(recursive)
        return result
    
    def addCategorizable(self, *categorizables, **kwargs):
        self.__categorizables.add(set(categorizables), event=kwargs.pop('event', None))
        
    def categorizableAddedEvent(self, event, *categorizables):
        event.addSource(self, *categorizables, 
                        **dict(type=self.categorizableAddedEventType()))
            
    def removeCategorizable(self, *categorizables, **kwargs):
        self.__categorizables.remove(set(categorizables), event=kwargs.pop('event', None))
        
    def categorizableRemovedEvent(self, event, *categorizables):
        event.addSource(self, *categorizables,
                        **dict(type=self.categorizableRemovedEventType()))
    
    def setCategorizables(self, categorizables, event=None):
        self.__categorizables.set(set(categorizables), event=event)
            
    def isFiltered(self):
        return self.__filtered
    
    @patterns.eventSource
    def setFiltered(self, filtered=True, event=None):
        if filtered == self.__filtered:
            return
        self.__filtered = filtered
        self.filterChangedEvent(event)
                    
    def filterChangedEvent(self, event):
        event.addSource(self, self.isFiltered(), 
                        type=self.filterChangedEventType())
                                
    def contains(self, categorizable, treeMode=False):
        ''' Return whether the categorizable belongs to this category. If an
            ancestor of the categorizable belong to this category, the 
            categorizable itself belongs to this category too. '''
        containedCategorizables = self.categorizables(recursive=True)
        if treeMode:
            categorizablesToInvestigate = categorizable.family()
        else:
            categorizablesToInvestigate = [categorizable] + categorizable.ancestors()
        for categorizableToInvestigate in categorizablesToInvestigate:
            if categorizableToInvestigate in containedCategorizables:
                return True
        return False

    def foregroundColorChangedEvent(self, event):
        ''' Override to include all categorizables (recursively) in the event 
            that belong to this category since their foreground colors (may) 
            have changed too. ''' 
        super(Category, self).foregroundColorChangedEvent(event)
        for categorizable in self.categorizables(recursive=True):
            categorizable.foregroundColorChangedEvent(event)

    def backgroundColorChangedEvent(self, event):
        ''' Override to include all categorizables (recursively) in the event 
            that belong to this category since their background colors (may) 
            have changed too. ''' 
        super(Category, self).backgroundColorChangedEvent(event)
        for categorizable in self.categorizables(recursive=True):
            categorizable.backgroundColorChangedEvent(event)
            
    def fontChangedEvent(self, event):
        ''' Override to include all categorizables (recursively) in the event 
            that belong to this category since their font (may) have changed 
            too. ''' 
        super(Category, self).fontChangedEvent(event)
        for categorizable in self.categorizables(recursive=True):
            categorizable.fontChangedEvent(event)

    def iconChangedEvent(self, event):
        ''' Override to include all categorizables (recursively) in the event
            that belong to this category since their icon (may) have changed
            too. '''
        super(Category, self).iconChangedEvent(event)
        for categorizable in self.categorizables(recursive=True):
            categorizable.iconChangedEvent(event)

    def selectedIconChangedEvent(self, event):
        ''' Override to include all categorizables (recursively) in the event
            that belong to this category since their selected icon (may) have
            changed too. '''
        super(Category, self).selectedIconChangedEvent(event)
        for categorizable in self.categorizables(recursive=True):
            categorizable.selectedIconChangedEvent(event)

    def hasExclusiveSubcategories(self):
        return self.__exclusiveSubcategories
    
    def isMutualExclusive(self):
        parent = self.parent()
        return parent and parent.hasExclusiveSubcategories()
    
    @patterns.eventSource
    def makeSubcategoriesExclusive(self, exclusive=True, event=None):
        if exclusive == self.hasExclusiveSubcategories():
            return
        self.__exclusiveSubcategories = exclusive
        self.exclusiveSubcategoriesEvent(event)
        for child in self.children():
            child.setFiltered(False, event=event)
            
    def exclusiveSubcategoriesEvent(self, event):
        event.addSource(self, self.hasExclusiveSubcategories(), 
                        type=self.exclusiveSubcategoriesChangedEventType())