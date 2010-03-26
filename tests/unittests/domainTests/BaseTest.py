# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>

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
import test
from taskcoachlib import patterns
from taskcoachlib.domain import base


class SynchronizedObjectTest(test.TestCase):
    def setUp(self):
        self.object = base.SynchronizedObject()
        self.events = []
        
    def onEvent(self, event):
        self.events.append(event)
        
    def registerObserver(self, eventType): # pylint: disable-msg=W0221
        patterns.Publisher().registerObserver(self.onEvent, eventType)
        
    def assertObjectStatus(self, expectedStatus):
        self.assertEqual(expectedStatus, self.object.getStatus())
        
    def assertOneEventReceived(self, eventSource, eventType, *values):
        self.assertEqual([patterns.Event(eventType, eventSource, *values)], 
                         self.events)
    
    def testInitialStatus(self):
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NEW)
                         
    def testMarkDeleted(self):
        self.object.markDeleted()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_DELETED)
                         
    def testMarkDeletedNotification(self):
        self.registerObserver(self.object.markDeletedEventType())
        self.object.markDeleted()
        self.assertOneEventReceived(self.object,
            self.object.markDeletedEventType(), self.object.getStatus())
    
    def testMarkNewObjectAsNotDeleted(self):
        self.object.cleanDirty()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NONE)
    
    def testMarkDeletedObjectAsUndeleted(self):
        self.object.markDeleted()
        self.object.cleanDirty()
        self.assertObjectStatus(base.SynchronizedObject.STATUS_NONE) 

    def testMarkNotDeletedNotification(self):
        self.object.markDeleted()
        self.registerObserver(self.object.markNotDeletedEventType())
        self.object.cleanDirty()
        self.assertOneEventReceived(self.object, 
            self.object.markNotDeletedEventType(), self.object.getStatus()) 

    def testSetStateToDeletedCausesNotification(self):
        self.object.markDeleted()
        state = self.object.__getstate__()
        self.object.cleanDirty()
        self.registerObserver(self.object.markDeletedEventType())
        self.object.__setstate__(state)                
        self.assertOneEventReceived(self.object, 
            self.object.markDeletedEventType(), self.object.STATUS_DELETED)

    def testSetStateToNotDeletedCausesNotification(self):
        state = self.object.__getstate__()
        self.object.markDeleted()
        self.registerObserver(self.object.markNotDeletedEventType())
        self.object.__setstate__(state)                
        self.assertOneEventReceived(self.object, 
            self.object.markNotDeletedEventType(), self.object.STATUS_NEW)
                    
                    
class ObjectSubclass(base.Object):
    pass


class ObjectTest(test.TestCase):
    def setUp(self):
        self.object = base.Object()
        self.subclassObject = ObjectSubclass()
        self.eventsReceived = []
        for eventType in (self.object.subjectChangedEventType(), 
                          self.object.descriptionChangedEventType(),
                          self.object.foregroundColorChangedEventType(),
                          self.object.backgroundColorChangedEventType(),
                          self.object.fontChangedEventType(),
                          self.object.iconChangedEventType(),
                          self.object.selectedIconChangedEventType()):
            patterns.Publisher().registerObserver(self.onEvent, eventType)

    def onEvent(self, event):
        self.eventsReceived.append(event)

    # Id tests:
        
    def testSetIdOnCreation(self):
        domainObject = base.Object(id='123')
        self.assertEqual('123', domainObject.id())
        
    def testIdIsAString(self):
        self.assertEqual(type(''), type(self.object.id()))
        
    def testDifferentObjectsHaveDifferentIds(self):
        self.assertNotEqual(base.Object().id(), self.object.id())
        
    def testCopyHasDifferentId(self):
        objectId = self.object.id() # Force generation of id
        copy = self.object.copy()
        self.assertNotEqual(copy.id(), objectId)
                
    # Subject tests:
        
    def testSubjectIsEmptyByDefault(self):
        self.assertEqual('', self.object.subject())
        
    def testSetSubjectOnCreation(self):
        domainObject = base.Object(subject='Hi')
        self.assertEqual('Hi', domainObject.subject())
        
    def testSetSubject(self):
        self.object.setSubject('New subject')
        self.assertEqual('New subject', self.object.subject())
        
    def testSetSubjectCausesNotification(self):
        self.object.setSubject('New subject')
        self.assertEqual(patterns.Event( \
            self.object.subjectChangedEventType(), self.object, 'New subject'), 
            self.eventsReceived[0])
        
    def testSetSubjectUnchangedDoesNotCauseNotification(self):
        self.object.setSubject('')
        self.failIf(self.eventsReceived)
        
    def testSubjectChangedNotificationIsDifferentForSubclass(self):
        self.subclassObject.setSubject('New')
        self.failIf(self.eventsReceived)
    
    # Description tests:
    
    def testDescriptionIsEmptyByDefault(self):
        self.failIf(self.object.description())
        
    def testSetDescriptionOnCreation(self):
        domainObject = base.Object(description='Hi')
        self.assertEqual('Hi', domainObject.description())
        
    def testSetDescription(self):
        self.object.setDescription('New description')
        self.assertEqual('New description', self.object.description())
        
    def testSetDescriptionCausesNotification(self):
        self.object.setDescription('New description')
        self.assertEqual(patterns.Event( \
            self.object.descriptionChangedEventType(), self.object, 
            'New description'), 
            self.eventsReceived[0])

    def testSetDescriptionUnchangedDoesNotCauseNotification(self):
        self.object.setDescription('')
        self.failIf(self.eventsReceived)

    def testDescriptionChangedNotificationIsDifferentForSubclass(self):
        self.subclassObject.setDescription('New')
        self.failIf(self.eventsReceived)
            
    # State tests:
    
    def testGetState(self):
        self.assertEqual(dict(subject='', description='', id=self.object.id(),
                              status=self.object.getStatus(), fgColor=None,
                              bgColor=None, font=None, icon='', selectedIcon=''),
                         self.object.__getstate__())

    def testSetState(self):
        newState = dict(subject='New', description='New', id=None,
                        status=self.object.STATUS_DELETED, 
                        fgColor=wx.GREEN, bgColor=wx.RED, font=wx.SWISS_FONT,
                        icon='icon', selectedIcon='selectedIcon')
        self.object.__setstate__(newState)
        self.assertEqual(newState, self.object.__getstate__())
        
    def testSetState_SendsOneNotification(self):
        newState = dict(subject='New', description='New', id=None,
                        status=self.object.STATUS_DELETED, 
                        fgColor=wx.GREEN, bgColor=wx.RED, font=wx.SWISS_FONT,
                        icon='icon', selectedIcon='selectedIcon')
        self.object.__setstate__(newState)
        self.assertEqual(1, len(self.eventsReceived))
        
    # Copy tests:
        
    def testCopy_SubjectIsCopied(self):
        self.object.setSubject('New subject')
        copy = self.object.copy()
        self.assertEqual(copy.subject(), self.object.subject())

    def testCopy_DescriptionIsCopied(self):
        self.object.setDescription('New description')
        copy = self.object.copy()
        self.assertEqual(copy.description(), self.object.description())

    def testCopy_ForegroundColorIsCopied(self):
        self.object.setForegroundColor(wx.RED)
        copy = self.object.copy()
        self.assertEqual(copy.foregroundColor(), self.object.foregroundColor())

    def testCopy_BackgroundColorIsCopied(self):
        self.object.setBackgroundColor(wx.RED)
        copy = self.object.copy()
        self.assertEqual(copy.backgroundColor(), self.object.backgroundColor())
        
    def testCopy_FontIsCopied(self):
        self.object.setFont(wx.SWISS_FONT)
        copy = self.object.copy()
        self.assertEqual(copy.font(), self.object.font())

    def testCopy_IconIsCopied(self):
        self.object.setIcon('icon')
        copy = self.object.copy()
        self.assertEqual(copy.icon(), self.object.icon())
        
    def testCopy_ShouldUseSubclassForCopy(self):
        copy = self.subclassObject.copy()
        self.assertEqual(copy.__class__, self.subclassObject.__class__)

    # Color tests
    
    def testDefaultForegroundColor(self):
        self.assertEqual(None, self.object.foregroundColor())
        
    def testSetForegroundColor(self):
        self.object.setForegroundColor(wx.GREEN)
        self.assertEqual(wx.GREEN, self.object.foregroundColor())
    
    def testSetForegroundColorWithTupleColor(self):
        self.object.setForegroundColor((255, 0, 0, 255))
        self.assertEqual(wx.RED, self.object.foregroundColor())

    def testSetForegroundColorOnCreation(self):
        domainObject = base.Object(fgColor=wx.GREEN)
        self.assertEqual(wx.GREEN, domainObject.foregroundColor())
    
    def testForegroundColorChangedNotification(self):
        self.object.setForegroundColor(wx.BLACK)
        self.assertEqual(1, len(self.eventsReceived))

    def testDefaultBackgroundColor(self):
        self.assertEqual(None, self.object.backgroundColor())
    
    def testSetBackgroundColor(self):
        self.object.setBackgroundColor(wx.RED)
        self.assertEqual(wx.RED, self.object.backgroundColor())

    def testSetBackgroundColorWithTupleColor(self):
        self.object.setBackgroundColor((255, 0, 0, 255))
        self.assertEqual(wx.RED, self.object.backgroundColor())

    def testSetBackgroundColorOnCreation(self):
        domainObject = base.Object(bgColor=wx.GREEN)
        self.assertEqual(wx.GREEN, domainObject.backgroundColor())
    
    def testBackgroundColorChangedNotification(self):
        self.object.setBackgroundColor(wx.BLACK)
        self.assertEqual(1, len(self.eventsReceived))
        
    # Font tests:
    
    def testDefaultFont(self):
        self.assertEqual(None, self.object.font())
        
    def testSetFont(self):
        self.object.setFont(wx.SWISS_FONT)
        self.assertEqual(wx.SWISS_FONT, self.object.font())

    def testSetFontOnCreation(self):
        domainObject = base.Object(font=wx.SWISS_FONT)
        self.assertEqual(wx.SWISS_FONT, domainObject.font())

    def testFontChangedNotification(self):
        self.object.setFont(wx.SWISS_FONT)
        self.assertEqual(1, len(self.eventsReceived))

    # Icon tests:

    def testDefaultIcon(self):
        self.assertEqual('', self.object.icon())

    def testSetIcon(self):
        self.object.setIcon('icon')
        self.assertEqual('icon', self.object.icon())

    def testSetIconOnCreation(self):
        domainObject = base.Object(icon='icon')
        self.assertEqual('icon', domainObject.icon())

    def testIconChangedNotification(self):
        self.object.setIcon('icon')
        self.assertEqual(1, len(self.eventsReceived))

    def testDefaultSelectedIcon(self):
        self.assertEqual('', self.object.selectedIcon())

    def testSetSelectedIcon(self):
        self.object.setSelectedIcon('selected')
        self.assertEqual('selected', self.object.selectedIcon())

    def testSelectedIconAfterSettingRegularIconOnly(self):
        self.object.setIcon('icon')
        self.assertEqual('', self.object.selectedIcon())

    def testSetSelectedIconOnCreation(self):
        domainObject = base.Object(selectedIcon='icon')
        self.assertEqual('icon', domainObject.selectedIcon())

    def testSelectedIconChangedNotification(self):
        self.object.setSelectedIcon('icon')
        self.assertEqual(1, len(self.eventsReceived))

    # Event types:
    
    def testModificationEventTypes(self):
        self.assertEqual([self.object.subjectChangedEventType(),
                          self.object.descriptionChangedEventType(),
                          self.object.foregroundColorChangedEventType(),
                          self.object.backgroundColorChangedEventType(),
                          self.object.fontChangedEventType(),
                          self.object.iconChangedEventType(),
                          self.object.selectedIconChangedEventType()],
                         self.object.modificationEventTypes())


class CompositeObjectTest(test.TestCase):
    def setUp(self):
        self.compositeObject = base.CompositeObject()
        self.child = None
        self.eventsReceived = []
        
    def onEvent(self, event):
        self.eventsReceived.append(event)
        
    def addChild(self, **kwargs):
        self.child = base.CompositeObject(**kwargs)
        self.compositeObject.addChild(self.child)
        self.child.setParent(self.compositeObject)
        
    def testIsExpanded(self):
        self.failIf(self.compositeObject.isExpanded())
        
    def testExpand(self):
        self.compositeObject.expand()
        self.failUnless(self.compositeObject.isExpanded())
        
    def testCollapse(self):
        self.compositeObject.expand()
        self.compositeObject.expand(False)
        self.failIf(self.compositeObject.isExpanded())
        
    def testSetExpansionStateViaConstructor(self):
        compositeObject = base.CompositeObject(expandedContexts=['None'])
        self.failUnless(compositeObject.isExpanded())

    def testSetExpansionStatesViaConstructor(self):
        compositeObject = base.CompositeObject(expandedContexts=['context1',
            'context2'])
        self.assertEqual(['context1', 'context2'],
                         sorted(compositeObject.expandedContexts()))

    def testExpandInContext_DoesNotChangeExpansionStateInDefaultContext(self):
        self.compositeObject.expand(context='some_viewer')
        self.failIf(self.compositeObject.isExpanded())

    def testExpandInContext_DoesChangeExpansionStateInGivenContext(self):
        self.compositeObject.expand(context='some_viewer')
        self.failUnless(self.compositeObject.isExpanded(context='some_viewer'))

    def testIsExpandedInUnknownContext_ReturnsFalse(self):
        self.failIf(self.compositeObject.isExpanded(context='whatever'))

    def testGetContextsWhereExpanded(self):
        self.assertEqual([], self.compositeObject.expandedContexts())
        
    def testRecursiveSubject(self):
        self.compositeObject.setSubject('parent')
        self.addChild(subject='child')
        self.assertEqual(u'parent -> child', self.child.subject(recursive=True))

    def testSubItemUsesParentForegroundColor(self):
        self.addChild()
        self.compositeObject.setForegroundColor(wx.RED)
        self.assertEqual(wx.RED, self.child.foregroundColor(recursive=True))

    def testSubItemDoesNotUseParentForegroundColorIfItHasItsOwnForegroundColor(self):
        self.addChild(fgColor=wx.RED)
        self.compositeObject.setForegroundColor(wx.BLUE)        
        self.assertEqual(wx.RED, self.child.foregroundColor(recursive=True))

    def testForegroundColorChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.foregroundColorChangedEventType(),
            eventSource=self.child)
        self.compositeObject.setForegroundColor(wx.RED)
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentBackgroundColor(self):
        self.addChild()
        self.compositeObject.setBackgroundColor(wx.RED)
        self.assertEqual(wx.RED, self.child.backgroundColor(recursive=True))
        
    def testSubItemDoesNotUseParentBackgroundColorIfItHasItsOwnBackgroundColor(self):
        self.addChild(bgColor=wx.RED)
        self.compositeObject.setBackgroundColor(wx.BLUE)        
        self.assertEqual(wx.RED, self.child.backgroundColor(recursive=True))
        
    def testBackgroundColorChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.backgroundColorChangedEventType(),
            eventSource=self.child)
        self.compositeObject.setBackgroundColor(wx.RED)
        self.assertEqual(1, len(self.eventsReceived))
        
    def testSubItemUsesParentFont(self):
        self.addChild()
        self.compositeObject.setFont(wx.ITALIC_FONT)
        self.assertEqual(wx.ITALIC_FONT, self.child.font(recursive=True))
        
    def testSubItemDoesNotUseParentFontIfItHasItsOwnFont(self):
        self.addChild(font=wx.SWISS_FONT)
        self.compositeObject.setFont(wx.ITALIC_FONT)
        self.assertEqual(wx.SWISS_FONT, self.child.font(recursive=True))
        
    def testFontChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.fontChangedEventType(), 
            eventSource=self.child)
        self.compositeObject.setFont(wx.SWISS_FONT)
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentIcon(self):
        self.addChild()
        self.compositeObject.setIcon('icon')
        self.assertEqual('icon', self.child.icon(recursive=True))

    def testSubItemDoesNotUseParentIconIfItHasItsOwnIcon(self):
        self.addChild(icon='childIcon')
        self.compositeObject.setIcon('icon')
        self.assertEqual('childIcon', self.child.icon(recursive=True))

    def testIconChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.iconChangedEventType(),
            eventSource=self.child)
        self.compositeObject.setIcon('icon')
        self.assertEqual(1, len(self.eventsReceived))

    def testSubItemUsesParentSelectedIcon(self):
        self.addChild()
        self.compositeObject.setSelectedIcon('icon')
        self.assertEqual('icon', self.child.selectedIcon(recursive=True))

    def testSubItemDoesNotUseParentSelectedIconIfItHasItsOwnSelectedIcon(self):
        self.addChild(selectedIcon='childIcon')
        self.compositeObject.setSelectedIcon('icon')
        self.assertEqual('childIcon', self.child.selectedIcon(recursive=True))

    def testSubItemUsesParentSelectedIconEvenIfItHasItsOwnIcon(self):
        self.addChild(icon='childIcon')
        self.compositeObject.setSelectedIcon('icon')
        self.assertEqual('icon', self.child.selectedIcon(recursive=True))

    def testSelectedIconChangedNotification(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.selectedIconChangedEventType(),
            eventSource=self.child)
        self.compositeObject.setSelectedIcon('icon')
        self.assertEqual(1, len(self.eventsReceived))

    def testCompositeWithChildrenUsesPluralIconIfAvailable(self):
        self.compositeObject.setIcon('book_icon')
        self.assertEqual('book_icon', self.compositeObject.icon(recursive=True))
        self.addChild()
        self.assertEqual('books_icon', self.compositeObject.icon(recursive=True))
        self.assertEqual('book_icon', self.compositeObject.icon(recursive=False))

    def testCompositeWithChildrenUsesPluralSelectedIconIfAvailable(self):
        self.compositeObject.setSelectedIcon('book_icon')
        self.assertEqual('book_icon', self.compositeObject.selectedIcon(recursive=True))
        self.addChild()
        self.assertEqual('books_icon', self.compositeObject.selectedIcon(recursive=True))
        self.assertEqual('book_icon', self.compositeObject.selectedIcon(recursive=False))

    def testCompositeWithoutChildrenUsesSingularIconIfAvailable(self):
        self.compositeObject.setIcon('books_icon')
        self.assertEqual('books_icon', self.compositeObject.icon(recursive=False))
        self.assertEqual('book_icon', self.compositeObject.icon(recursive=True))

    def testCompositeWithoutChildrenUsesSingularSelectedIconIfAvailable(self):
        self.compositeObject.setSelectedIcon('books_icon')
        self.assertEqual('books_icon', self.compositeObject.selectedIcon(recursive=False))
        self.assertEqual('book_icon', self.compositeObject.selectedIcon(recursive=True))

    def testChildOfCompositeUsesSingularIconIfAvailable(self):
        self.compositeObject.setIcon('books_icon')
        self.addChild()
        self.assertEqual('book_icon', self.child.icon(recursive=True))

    def testChildOfCompositeUsesSingularSelectedIconIfAvailable(self):
        self.compositeObject.setSelectedIcon('books_icon')
        self.addChild()
        self.assertEqual('book_icon', self.child.selectedIcon(recursive=True))

    def testCopy(self):
        self.compositeObject.expand(context='some_viewer')
        copy = self.compositeObject.copy()
        # pylint: disable-msg=E1101
        self.assertEqual(copy.expandedContexts(),
                         self.compositeObject.expandedContexts())
        self.compositeObject.expand(context='another_viewer')
        self.failIf('another_viewer' in copy.expandedContexts())
        
    def testMarkDeleted(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.markDeletedEventType())
        self.compositeObject.markDeleted()
        expectedEvent = patterns.Event(base.CompositeObject.markDeletedEventType(),
                                       self.compositeObject, base.CompositeObject.STATUS_DELETED)
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_DELETED)
        self.assertEqual([expectedEvent], self.eventsReceived)
        
    def testMarkDirty(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType())
        self.compositeObject.markDeleted()
        self.compositeObject.markDirty(force=True)
        expectedEvent = patterns.Event(base.CompositeObject.markNotDeletedEventType(),
                                       self.compositeObject, base.CompositeObject.STATUS_CHANGED)
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_CHANGED)
        self.assertEqual([expectedEvent], self.eventsReceived)

    def testMarkNew(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType())
        self.compositeObject.markDeleted()
        self.compositeObject.markNew()
        expectedEvent = patterns.Event(base.CompositeObject.markNotDeletedEventType(),
                                       self.compositeObject, base.CompositeObject.STATUS_NEW)
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_NEW)
        self.assertEqual([expectedEvent], self.eventsReceived)
        
    def testCleanDirty(self):
        self.addChild()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=base.CompositeObject.markNotDeletedEventType())
        self.compositeObject.markDeleted()
        self.compositeObject.cleanDirty()
        expectedEvent = patterns.Event(base.CompositeObject.markNotDeletedEventType(),
                                       self.compositeObject, base.CompositeObject.STATUS_NONE)
        expectedEvent.addSource(self.child, base.CompositeObject.STATUS_NONE)
        self.assertEqual([expectedEvent], self.eventsReceived)
        
    def testModificationEventTypes(self):
        self.assertEqual([self.compositeObject.addChildEventType(),
                          self.compositeObject.removeChildEventType(),
                          self.compositeObject.subjectChangedEventType(),
                          self.compositeObject.descriptionChangedEventType(),
                          self.compositeObject.foregroundColorChangedEventType(),
                          self.compositeObject.backgroundColorChangedEventType(),
                          self.compositeObject.fontChangedEventType(),
                          self.compositeObject.iconChangedEventType(),
                          self.compositeObject.selectedIconChangedEventType(),
                          self.compositeObject.expansionChangedEventType()], 
                         self.compositeObject.modificationEventTypes())


class BaseCollectionTest(test.TestCase):
    def setUp(self):
        self.collection = base.Collection()
        
    def testLookupByIdWhenCollectionIsEmptyRaisesIndexError(self):
        try:
            self.collection.getObjectById('id')
            self.fail()
        except IndexError:
            pass
        
    def testLookupIdWhenObjectIsInCollection(self):
        domainObject = base.CompositeObject()
        self.collection.append(domainObject)
        self.assertEqual(domainObject, 
                         self.collection.getObjectById(domainObject.id()))
