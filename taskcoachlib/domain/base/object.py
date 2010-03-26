# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2008 Jérôme Laheurte <fraca7@free.fr>

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

import time
from taskcoachlib import patterns
import attribute
from taskcoachlib.domain.attribute import icon


class SynchronizedObject(object):
    STATUS_NONE    = 0
    STATUS_NEW     = 1
    STATUS_CHANGED = 2
    STATUS_DELETED = 3

    def __init__(self, *args, **kwargs):
        self.__status = kwargs.pop('status', self.STATUS_NEW)
        super(SynchronizedObject, self).__init__(*args, **kwargs)

    @classmethod
    def markDeletedEventType(class_):
        return 'object.markdeleted'

    @classmethod
    def markNotDeletedEventType(class_):
        return 'object.marknotdeleted'
        
    def __getstate__(self):
        try:
            state = super(SynchronizedObject, self).__getstate__()
        except AttributeError:
            state = dict()

        state['status'] = self.__status
        return state

    def __setstate__(self, state, event=None):
        notify = event is None
        event = event or patterns.Event()
        try:
            super(SynchronizedObject, self).__setstate__(state, event)
        except AttributeError:
            pass
        if state['status'] != self.__status:
            if state['status'] == self.STATUS_CHANGED:
                self.markDirty(event=event)
            elif state['status'] == self.STATUS_DELETED:
                self.markDeleted(event)
            elif state['status'] == self.STATUS_NEW:
                self.markNew(event)
            elif state['status'] == self.STATUS_NONE:
                self.cleanDirty(event)
        if notify:
            event.send()

    def getStatus(self):
        return self.__status
        
    def markDirty(self, force=False, event=None):
        if not self.setStatusDirty(force):
            return
        notify = event is None
        event = event or patterns.Event()
        event.addSource(self, self.__status, 
                        type=self.markNotDeletedEventType())
        if notify:
            event.send()

    def setStatusDirty(self, force=False):
        oldStatus = self.__status
        if self.__status == self.STATUS_NONE or force:
            self.__status = self.STATUS_CHANGED
            return oldStatus == self.STATUS_DELETED
        else:
            return False

    def markNew(self, event=None):
        if not self.setStatusNew():
            return
        notify = event is None
        event = event or patterns.Event()
        event.addSource(self, self.__status,
                        type=self.markNotDeletedEventType())
        if notify:
            event.send()
            
    def setStatusNew(self):
        oldStatus = self.__status
        self.__status = self.STATUS_NEW
        return oldStatus == self.STATUS_DELETED

    def markDeleted(self, event=None):
        notify = event is None
        event = event or patterns.Event()
        self.setStatusDeleted()
        event.addSource(self, self.__status, type=self.markDeletedEventType())
        if notify:
            event.send()

    def setStatusDeleted(self):
        self.__status = self.STATUS_DELETED

    def cleanDirty(self, event=None):
        if not self.setStatusNone():
            return
        notify = event is None
        event = event or patterns.Event()
        event.addSource(self, self.__status, 
                        type=self.markNotDeletedEventType())
        if notify:
            event.send()
            
    def setStatusNone(self):
        oldStatus = self.__status
        self.__status = self.STATUS_NONE
        return oldStatus == self.STATUS_DELETED

    def isNew(self):
        return self.__status == self.STATUS_NEW

    def isModified(self):
        return self.__status == self.STATUS_CHANGED

    def isDeleted(self):
        return self.__status == self.STATUS_DELETED

        
class Object(SynchronizedObject):
    def __init__(self, *args, **kwargs):
        self.__subject = attribute.Attribute(kwargs.pop('subject', ''), self, 
                                             self.subjectChangedEvent)
        self.__description = attribute.Attribute(kwargs.pop('description', ''), 
                                                 self,
                                                 self.descriptionChangedEvent)
        self.__fgColor = attribute.Attribute(kwargs.pop('fgColor', None), self, 
                                             self.foregroundColorChangedEvent)
        self.__bgColor = attribute.Attribute(kwargs.pop('bgColor', None), self,
                                             self.backgroundColorChangedEvent)
        self.__font = attribute.Attribute(kwargs.pop('font', None), self,
                                          self.fontChangedEvent)
        self.__icon = attribute.Attribute(kwargs.pop('icon', ''), self,
                                          self.iconChangedEvent)
        self.__selectedIcon = attribute.Attribute(kwargs.pop('selectedIcon', ''), self,
                                                  self.selectedIconChangedEvent)
        self.__id = kwargs.pop('id', None) or '%s:%s'%(id(self), time.time())
        # FIXME: Not a valid XML id
        # FIXME: When dropping support for python 2.4, use the uuid module
        super(Object, self).__init__(*args, **kwargs)
        
    def __repr__(self):
        return self.subject()

    def __getstate__(self):
        try:
            state = super(Object, self).__getstate__()
        except AttributeError:
            state = dict()
        state.update(dict(id=self.__id, subject=self.__subject.get(), 
                          description=self.__description.get(),
                          fgColor=self.__fgColor.get(),
                          bgColor=self.__bgColor.get(),
                          font=self.__font.get(),
                          icon=self.__icon.get(),
                          selectedIcon=self.__selectedIcon.get()))
        return state
    
    def __setstate__(self, state, event=None):
        notify = event is None
        event = event or patterns.Event()
        try:
            super(Object, self).__setstate__(state, event)
        except AttributeError:
            pass
        self.setId(state['id'])
        self.setSubject(state['subject'], event)
        self.setDescription(state['description'], event)
        self.setForegroundColor(state['fgColor'], event)
        self.setBackgroundColor(state['bgColor'], event)
        self.setFont(state['font'], event)
        self.setIcon(state['icon'], event)
        self.setSelectedIcon(state['selectedIcon'], event)
        if notify:
            event.send()

    def __getcopystate__(self):
        ''' Return a dictionary that can be passed to __init__ when creating
            a copy of the object. 
            
            E.g. copy = obj.__class__(**original.__getcopystate__()) '''
        try:
            state = super(Object, self).__getcopystate__()
        except AttributeError:
            state = dict()
        # Note: we don't put the id in the state dict, because a copy should
        # get a new id:
        state.update(dict(\
            subject=self.__subject.get(), description=self.__description.get(),
            fgColor=self.__fgColor.get(), bgColor=self.__bgColor.get(),
            font=self.__font.get(), icon=self.__icon.get(),
            selectedIcon=self.__selectedIcon.get()))
        return state
    
    def copy(self):
        return self.__class__(**self.__getcopystate__())
 
    # Id:
       
    def id(self):
        return self.__id
    
    def setId(self, id_):
        self.__id = id_
        
    # Subject:
    
    def subject(self):
        return self.__subject.get()
    
    def setSubject(self, subject, event=None):
        self.__subject.set(subject, event)
        
    def subjectChangedEvent(self, event):
        event.addSource(self, self.subject(), type=self.subjectChangedEventType())
    
    @classmethod    
    def subjectChangedEventType(class_):
        return '%s.subject'%class_
    
    # Description:
    
    def description(self):
        return self.__description.get()
    
    def setDescription(self, description, event=None):
        self.__description.set(description, event)
        
    def descriptionChangedEvent(self, event):
        event.addSource(self, self.description(), 
                        type=self.descriptionChangedEventType())
            
    @classmethod    
    def descriptionChangedEventType(class_):
        return '%s.description'%class_
    
    # Color:
    
    def setForegroundColor(self, color, event=None):
        self.__fgColor.set(color, event)
    
    def foregroundColor(self, recursive=False): # pylint: disable-msg=W0613
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__fgColor.get()

    def foregroundColorChangedEvent(self, event):
        event.addSource(self, self.foregroundColor(), 
                        type=self.foregroundColorChangedEventType())

    @classmethod
    def foregroundColorChangedEventType(class_):
        return '%s.fgColor'%class_
    
    def setBackgroundColor(self, color, event=None):
        self.__bgColor.set(color, event)
        
    def backgroundColor(self, recursive=False): # pylint: disable-msg=W0613
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__bgColor.get()

    def backgroundColorChangedEvent(self, event):
        event.addSource(self, self.backgroundColor(), 
                        type=self.backgroundColorChangedEventType())

    @classmethod
    def backgroundColorChangedEventType(class_):
        return '%s.bgColor'%class_
    
    # Font:
    
    def font(self, recursive=False): # pylint: disable-msg=W0613
        # The 'recursive' argument isn't actually used here, but some
        # code assumes composite objects where there aren't. This is
        # the simplest workaround.
        return self.__font.get()
    
    def setFont(self, font, event=None):
        self.__font.set(font, event)
        
    def fontChangedEvent(self, event):
        event.addSource(self, self.font(), type=self.fontChangedEventType())

    @classmethod    
    def fontChangedEventType(class_):
        return '%s.font'%class_

    # Icons:

    def icon(self):
        return self.__icon.get()

    def setIcon(self, icon, event=None):
        self.__icon.set(icon, event)

    def iconChangedEvent(self, event):
        event.addSource(self, self.icon(), type=self.iconChangedEventType())

    @classmethod
    def iconChangedEventType(class_):
        return '%s.icon'%class_

    def selectedIcon(self):
        return self.__selectedIcon.get()

    def setSelectedIcon(self, icon, event=None):
        self.__selectedIcon.set(icon, event)

    def selectedIconChangedEvent(self, event):
        event.addSource(self, self.selectedIcon(),
                        type=self.selectedIconChangedEventType())

    @classmethod
    def selectedIconChangedEventType(class_):
        return '%s.selectedIcon'%class_
    
    # Event types:
    
    @classmethod
    def modificationEventTypes(class_):
        try:
            eventTypes = super(Object, class_).modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [class_.subjectChangedEventType(),
                             class_.descriptionChangedEventType(),
                             class_.foregroundColorChangedEventType(),
                             class_.backgroundColorChangedEventType(),
                             class_.fontChangedEventType(),
                             class_.iconChangedEventType(),
                             class_.selectedIconChangedEventType()]


class CompositeObject(Object, patterns.ObservableComposite):
    def __init__(self, *args, **kwargs):
        self.__expandedContexts = set()
        for context in kwargs.pop('expandedContexts', []):
            self.__expandedContexts.add(context)
        super(CompositeObject, self).__init__(*args, **kwargs)

    def __getcopystate__(self):
        state = super(CompositeObject, self).__getcopystate__()
        state.update(dict(expandedContexts=self.expandedContexts()))
        return state

    # Subject:
    
    def subject(self, recursive=False): # pylint: disable-msg=W0221
        subject = super(CompositeObject, self).subject()
        if recursive and self.parent():
            subject = u'%s -> %s'%(self.parent().subject(recursive=True), subject)
        return subject
        
    # Description:
        
    def description(self, recursive=False): # pylint: disable-msg=W0221,W0613
        # Allow for the recursive flag, but ignore it
        return super(CompositeObject, self).description()
        
    # Expansion state:

    # Note: expansion state is stored by context. A context is a simple string
    # identifier (without comma's) to distinguish between different contexts,
    # i.e. viewers. A composite object may be expanded in one context and
    # collapsed in another.
    
    def isExpanded(self, context='None'):
        ''' Returns a boolean indicating whether the composite object is 
            expanded in the specified context. ''' 
        return context in self.__expandedContexts

    def expandedContexts(self):
        ''' Returns a list of contexts where this composite object is 
            expanded. ''' 
        return list(self.__expandedContexts)
    
    def expand(self, expand=True, context='None', event=None):
        ''' Expands (or collapses) the composite object in the specified 
            context. ''' 
        if expand == self.isExpanded(context):
            return
        notify = event is None
        event = event or patterns.Event()
        if expand:
            self.__expandedContexts.add(context)
        else:
            self.__expandedContexts.discard(context)
        self.expansionChangedEvent(event)
        if notify:
            event.send()

    @classmethod
    def expansionChangedEventType(class_):
        return '%s.expanded'%class_

    def expansionChangedEvent(self, event):
        event.addSource(self, type=self.expansionChangedEventType())
    
    # Color:

    def foregroundColor(self, recursive=True):
        myFgColor = super(CompositeObject, self).foregroundColor()
        if not myFgColor and recursive and self.parent():
            return self.parent().foregroundColor(recursive=True)
        else:
            return myFgColor

    def foregroundColorChangedEvent(self, event):
        super(CompositeObject, self).foregroundColorChangedEvent(event)
        children = self.childrenWithoutOwnForegroundColor()
        fgColor = self.foregroundColor(recursive=False)
        for child in children:
            event.addSource(child, fgColor, type=child.foregroundColorChangedEventType())

    def childrenWithoutOwnForegroundColor(self, parent=None):
        parent = parent or self
        children = []
        for child in parent.children():
            if child.foregroundColor(recursive=False) is None:
                children.extend([child] + self.childrenWithoutOwnForegroundColor(child))
        return children
        
    def backgroundColor(self, recursive=True):
        myBgColor = super(CompositeObject, self).backgroundColor()
        if not myBgColor and recursive and self.parent():
            return self.parent().backgroundColor(recursive=True)
        else:
            return myBgColor
                
    def backgroundColorChangedEvent(self, event):
        super(CompositeObject, self).backgroundColorChangedEvent(event)
        children = self.childrenWithoutOwnBackgroundColor()
        bgColor = self.backgroundColor(recursive=False)
        for child in children:
            event.addSource(child, bgColor, type=child.backgroundColorChangedEventType())

    def childrenWithoutOwnBackgroundColor(self, parent=None):
        parent = parent or self
        children = []
        for child in parent.children():
            if child.backgroundColor(recursive=False) is None:
                children.extend([child] + self.childrenWithoutOwnBackgroundColor(child))
        return children
    
    # Font:
    
    def font(self, recursive=False):
        myFont = super(CompositeObject, self).font()
        if not myFont and recursive and self.parent():
            return self.parent().font(recursive=True)
        else:
            return myFont

    def fontChangedEvent(self, event):
        super(CompositeObject, self).fontChangedEvent(event)
        children = self.childrenWithoutOwnFont()
        font = self.font(recursive=False)
        for child in children:
            event.addSource(child, font, type=child.fontChangedEventType())
            
    def childrenWithoutOwnFont(self, parent=None):
        parent = parent or self
        children = []
        for child in parent.children():
            if child.font(recursive=False) is None:
                children.extend([child] + self.childrenWithoutOwnFont(child))
        return children

    # Icon:

    def icon(self, recursive=False):
        myIcon = super(CompositeObject, self).icon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().icon(recursive=True)
        return self.pluralOrSingularIcon(myIcon)

    def iconChangedEvent(self, event):
        super(CompositeObject, self).iconChangedEvent(event)
        children = self.childrenWithoutOwnIcon()
        icon = self.icon(recursive=False)
        for child in children:
            event.addSource(child, icon, type=child.iconChangedEventType())

    def childrenWithoutOwnIcon(self, parent=None):
        parent = parent or self
        children = []
        for child in parent.children():
            if not child.icon(recursive=False):
                children.extend([child] + self.childrenWithoutOwnIcon(child))
        return children

    def selectedIcon(self, recursive=False):
        myIcon = super(CompositeObject, self).selectedIcon()
        if not recursive:
            return myIcon
        if not myIcon and self.parent():
            myIcon = self.parent().selectedIcon(recursive=True)
        return self.pluralOrSingularIcon(myIcon)

    def selectedIconChangedEvent(self, event):
        super(CompositeObject, self).selectedIconChangedEvent(event)
        children = self.childrenWithoutOwnSelectedIcon()
        icon = self.selectedIcon(recursive=False)
        for child in children:
            event.addSource(child, icon, type=child.selectedIconChangedEventType())

    def childrenWithoutOwnSelectedIcon(self, parent=None):
        parent = parent or self
        children = []
        for child in parent.children():
            if not child.selectedIcon(recursive=False):
                children.extend([child] + self.childrenWithoutOwnSelectedIcon(child))
        return children

    def pluralOrSingularIcon(self, myIcon):
        hasChildren = any(child for child in self.children() if not child.isDeleted())
        mapping = icon.itemImagePlural if hasChildren else icon.itemImageSingular
        return mapping.get(myIcon, myIcon)
    
    # Event types:

    @classmethod
    def modificationEventTypes(class_):
        return super(CompositeObject, class_).modificationEventTypes() + \
            [class_.expansionChangedEventType()]

    # Override SynchronizedObject methods to also mark child objects

    def markDeleted(self, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CompositeObject, self).markDeleted(event)
        for child in self.children():
            child.markDeleted(event)
        if notify:
            event.send()
            
    def markNew(self, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CompositeObject, self).markNew(event)
        for child in self.children():
            child.markNew(event)
        if notify:
            event.send()

    def markDirty(self, force=False, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CompositeObject, self).markDirty(force, event)
        for child in self.children():
            child.markDirty(force, event)
        if notify:
            event.send()
            
    def cleanDirty(self, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CompositeObject, self).cleanDirty(event)
        for child in self.children():
            child.cleanDirty(event)
        if notify:
            event.send()
