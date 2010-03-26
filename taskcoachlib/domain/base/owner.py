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

from taskcoachlib import patterns


def DomainObjectOwnerMetaclass(name, bases, ns):
    """This metaclass makes a class an owner for some domain
    objects. The __ownedType__ attribute of the class must be a
    string. For each type, the following methods will be added to the
    class (here assuming a type of 'Foo'):

      - __init__, __getstate__, __setstate__, __getcopystate__, __setcopystate__
      - addFoo, removeFoo, addFoos, removeFoos
      - setFoos, foos
      - foosChangedEventType
      - modificationEventTypes
      - __notifyObservers"""

    # This  metaclass is  a function  instead  of a  subclass of  type
    # because as we're replacing __init__, we don't want the metaclass
    # to be inherited by children.

    klass = type(name, bases, ns)

    def constructor(instance, *args, **kwargs):
        # NB: we use a simple list here. Maybe we should use a container type.
        setattr(instance,'_%s__%ss' % (name, klass.__ownedType__.lower()),
                kwargs.pop(klass.__ownedType__.lower() + 's', []))
        super(klass, instance).__init__(*args, **kwargs)

    klass.__init__ = constructor

    def changedEventType(class_):
        return '%s.%ss' % (class_, klass.__ownedType__.lower())

    setattr(klass, '%ssChangedEventType' % klass.__ownedType__.lower(), 
            classmethod(changedEventType))
    
    def modificationEventTypes(class_):
        try:
            eventTypes = super(klass, class_).modificationEventTypes()
        except AttributeError:
            eventTypes = []
        return eventTypes + [changedEventType(class_)]
    
    klass.modificationEventTypes = classmethod(modificationEventTypes)

    def objects(instance):
        ownedObjects = getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower()))
        return [ownedObject for ownedObject in ownedObjects \
                if not ownedObject.isDeleted()]

    setattr(klass, '%ss' % klass.__ownedType__.lower(), objects)

    def setObjects(instance, newObjects, event=None):
        if newObjects == objects(instance):
            return
        notify = event is None
        event = event or patterns.Event()
        setattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower()), 
                                        newObjects)
        changedEvent(instance, event, *newObjects) # pylint: disable-msg=W0142
        if notify:
            event.send()

    setattr(klass, 'set%ss' % klass.__ownedType__, setObjects)

    def changedEvent(instance, event, *objects):
        event.addSource(instance, *objects, 
                        **dict(type=changedEventType(instance.__class__)))
    
    setattr(klass, '%ssChangedEvent' % klass.__ownedType__.lower(), changedEvent)

    def addObject(instance, ownedObject, event=None):
        notify = event is None
        event = event or patterns.Event()
        getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower())).append(ownedObject)
        changedEvent(instance, event, ownedObject)
        if notify:
            event.send()

    setattr(klass, 'add%s' % klass.__ownedType__, addObject)

    def addObjects(instance, *ownedObjects, **kwargs):
        event = kwargs.pop('event', None)
        if not ownedObjects:
            return
        notify = event is None
        event = event or patterns.Event()
        getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower())).extend(ownedObjects)
        changedEvent(instance, event, *ownedObjects)
        if notify:
            event.send()

    setattr(klass, 'add%ss' % klass.__ownedType__, addObjects)

    def removeObject(instance, ownedObject, event=None):
        notify = event is None
        event = event or patterns.Event()
        getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower())).remove(ownedObject)
        changedEvent(instance, event, ownedObject)
        if notify:
            event.send()

    setattr(klass, 'remove%s' % klass.__ownedType__, removeObject)

    def removeObjects(instance, *ownedObjects, **kwargs):
        event = kwargs.pop('event', None)
        if not ownedObjects:
            return
        notify = event is None
        event = event or patterns.Event()
        for ownedObject in ownedObjects:
            try:
                getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower())).remove(ownedObject)
            except ValueError:
                pass
        changedEvent(instance, event, *ownedObjects)
        if notify:
            event.send()
        
    setattr(klass, 'remove%ss' % klass.__ownedType__, removeObjects)

    def getstate(instance):
        try:
            state = super(klass, instance).__getstate__()
        except AttributeError:
            state = dict()
        state[klass.__ownedType__.lower() + 's'] = getattr(instance, '_%s__%ss' % (name, klass.__ownedType__.lower()))[:]
        return state

    klass.__getstate__ = getstate

    def setstate(instance, state, event=None):
        notify = event is None
        event = event or patterns.Event()
        try:
            super(klass, instance).__setstate__(state, event)
        except AttributeError:
            pass
        setObjects(instance, state[klass.__ownedType__.lower() + 's'], event)
        if notify:
            event.send()

    klass.__setstate__ = setstate

    def getcopystate(instance):
        try:
            state = super(klass, instance).__getcopystate__()
        except AttributeError:
            state = dict()
        state['%ss' % klass.__ownedType__.lower()] = \
            [ownedObject.copy() for ownedObject in objects(instance)]
        return state

    klass.__getcopystate__ = getcopystate

    return klass
