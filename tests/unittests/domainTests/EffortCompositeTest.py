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

import test
from taskcoachlib import patterns, config
from taskcoachlib.domain import task, effort, date


class CompositeEffortTest(test.TestCase):
    def setUp(self):
        self.task = task.Task(subject='task')
        self.effort1 = effort.Effort(self.task, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.effort2 = effort.Effort(self.task, 
            date.DateTime(2004,1,1,13,0,0), date.DateTime(2004,1,1,14,0,0))
        self.effort3 = effort.Effort(self.task, 
            date.DateTime(2004,1,11,13,0,0), date.DateTime(2004,1,11,14,0,0))
        self.trackedEffort = effort.Effort(self.task, 
            date.DateTime(2004,1,1,9,0,0))
        self.composite = effort.CompositeEffort(self.task,
            date.DateTime(2004,1,1,0,0,0), date.DateTime(2004,1,1,23,59,59))
        self.events = []
    
    def onEvent(self, event):
        self.events.append(event)

    def testInitialLength(self):
        self.assertEqual(0, len(self.composite))

    def testInitialDuration(self):
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testInitialTrackingState(self):
        self.failIf(self.composite.isBeingTracked())

    def testInitialTrackingStateWhenTaskIsTracked(self):
        self.task.addEffort(self.trackedEffort)
        composite = effort.CompositeEffort(self.task, 
            self.composite.getStart(), self.composite.getStop())
        self.failUnless(composite.isBeingTracked())
        
    def testDurationForSingleEffort(self):
        self.task.addEffort(self.effort1)
        self.assertEqual(self.effort1.duration(), self.composite.duration())

    def testAddEffortOutsidePeriodToTask(self):
        effortOutsidePeriod = effort.Effort(self.task, 
            date.DateTime(2004,1,11,13,0,0), date.DateTime(2004,1,11,14,0,0))
        self.task.addEffort(effortOutsidePeriod)
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testAddEffortWithStartTimeEqualToStartOfPeriodToTask(self):
        effortSameStartTime = effort.Effort(self.task, 
            date.DateTime(2004,1,1,0,0,0), date.DateTime(2004,1,1,14,0,0))
        self.task.addEffort(effortSameStartTime)
        self.assertEqual(effortSameStartTime.duration(), 
            self.composite.duration())

    def testAddEffortWithStartTimeEqualToEndOfPeriodToTask(self):
        effortSameStopTime = effort.Effort(self.task, 
            date.DateTime(2004,1,1,23,59,59), date.DateTime(2004,1,2,1,0,0))
        self.task.addEffort(effortSameStopTime)
        self.assertEqual(effortSameStopTime.duration(), 
            self.composite.duration())

    def testAddTrackedEffortToTask(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStartEventType())
        self.task.addEffort(self.trackedEffort)
        self.assertEqual(patterns.Event(self.composite.trackStartEventType(), 
            self.composite, self.trackedEffort), 
            self.events[0])

    def testAddTrackedEffortToTaskDoesNotCauseListEmptyNotification(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.composite.empty')
        self.task.addEffort(effort.Effort(self.task, self.composite.getStart()))
        self.failIf(self.events)

    def testAddSecondTrackedEffortToTask(self):
        self.task.addEffort(self.trackedEffort)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStartEventType())
        self.task.addEffort(self.trackedEffort)
        self.failIf(self.events)

    def testAddEffortNotification(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.duration')
        self.task.addEffort(self.effort1)
        self.assertEqual(patterns.Event('effort.duration', self.composite,
            self.composite.duration()), self.events[0])

    def testRemoveEffortFromTask(self):
        self.task.addEffort(self.effort1)
        self.task.removeEffort(self.effort1)
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testRemoveEffortNotification(self):
        self.task.addEffort(self.effort1)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.composite.empty')
        self.task.removeEffort(self.effort1)
        self.assertEqual(patterns.Event('effort.composite.empty', 
            self.composite), self.events[0])

    def testRemoveTrackedEffortFromTask(self):
        self.task.addEffort(self.trackedEffort)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStopEventType())
        self.task.removeEffort(self.trackedEffort)
        self.assertEqual(patterns.Event(self.composite.trackStopEventType(), 
            self.composite, self.trackedEffort), 
            self.events[0])

    def testRemoveFirstFromTwoTrackedEffortsFromTask(self):
        self.task.addEffort(self.trackedEffort)
        self.task.addEffort(self.trackedEffort.copy())
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=effort.Effort.trackStopEventType())
        self.task.removeEffort(self.trackedEffort)
        self.failIf(self.events)

    def testDuration(self):
        self.task.addEffort(self.effort1)
        self.assertEqual(self.effort1.duration(), self.composite.duration())

    def testDurationTwoEfforts(self):
        self.task.addEffort(self.effort1)
        self.task.addEffort(self.effort2)
        self.assertEqual(self.effort1.duration() + self.effort2.duration(), 
            self.composite.duration())

    def testRevenue(self):
        self.task.setHourlyFee(100)
        self.task.addEffort(self.effort1)
        self.assertEqual(100, self.composite.revenue())

    def testRevenueTwoEfforts(self):
        self.task.setHourlyFee(100)
        self.task.addEffort(self.effort1)
        self.task.addEffort(self.effort2)
        self.assertEqual(200, self.composite.revenue())

    def testThatAnHourlyFeeChangeCausesARevenueNotification(self):
        self.task.addEffort(self.effort1)
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType='effort.revenue')
        self.task.setHourlyFee(100)
        self.failUnless(patterns.Event('effort.revenue', self.composite,
            100.0) in self.events)

    def testIsBeingTracked(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStop(date.DateTime())
        self.failUnless(self.composite.isBeingTracked())

    def testNotificationForStartTracking(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStartEventType())
        self.task.addEffort(self.effort1)
        self.effort1.setStop(date.DateTime())
        self.failUnless(patterns.Event(self.composite.trackStartEventType(), 
            self.composite, self.effort1) in self.events)

    def testNoNotificationForStartTrackingIfActiveEffortOutsidePeriod(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.effort3.trackStartEventType())
        self.task.addEffort(self.effort3)
        self.effort3.setStop(date.DateTime())
        self.assertEqual([patterns.Event(self.effort3.trackStartEventType(),
                                         self.effort3)],
            self.events)

    def testNotificationForStopTracking(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStop(date.DateTime())
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType=self.composite.trackStopEventType())
        self.effort1.setStop()
        self.failUnless(patterns.Event(self.composite.trackStopEventType(), 
            self.composite, self.effort1) in self.events)

    def testNoNotificationForStopTrackingIfActiveEffortOutsidePeriod(self):
        self.task.addEffort(self.effort3)
        self.effort3.setStop(date.DateTime())
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.effort3.trackStopEventType())
        self.effort3.setStop()
        self.assertEqual([patterns.Event(self.effort3.trackStopEventType(),
                                         self.effort3)], 
            self.events)

    def testChangeStartTimeOfEffort_KeepWithinPeriod(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStart(self.effort1.getStart() + date.TimeDelta(hours=1))
        self.assertEqual(self.effort1.duration(), self.composite.duration())

    def testChangeStartTimeOfEffort_KeepWithinPeriod_Notification(self):
        self.task.addEffort(self.effort1)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.duration')
        self.effort1.setStart(self.effort1.getStart() + date.TimeDelta(hours=1))
        self.failUnless(patterns.Event('effort.duration', 
            self.composite, self.composite.duration()) in self.events)

    def testChangeStartTimeOfEffort_MoveOutsidePeriode(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStart(self.effort1.getStart() + date.TimeDelta(days=2))
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testChangeStopTimeOfEffort_KeepWithinPeriod(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStop(self.effort1.getStop() + date.TimeDelta(hours=1))
        self.assertEqual(self.effort1.duration(), self.composite.duration())

    def testChangeStopTimeOfEffort_MoveOutsidePeriod(self):
        self.task.addEffort(self.effort1)
        self.effort1.setStop(self.effort1.getStop() + date.TimeDelta(days=2))
        self.assertEqual(self.effort1.duration(), self.composite.duration())

    def testChangeStartTimeOfEffort_Notification(self):
        self.task.addEffort(self.effort1)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.duration')
        self.effort1.setStop(self.effort1.getStop() + date.TimeDelta(hours=1))
        expectedEvent = patterns.Event('effort.duration', self.composite, 
            self.composite.duration())
        #expectedEvent.addSource(self.effort1, self.effort1.duration(), type='effort.duration')
        self.failUnless(expectedEvent in self.events)

    def testChangeStartTimeOfEffort_MoveInsidePeriod(self):
        self.task.addEffort(self.effort3)
        self.effort3.setStart(self.composite.getStart())
        self.assertEqual(self.effort3.duration(), self.composite.duration())

    def testEmptyNotification(self):
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType='effort.composite.empty')
        self.task.addEffort(self.effort1)
        self.task.removeEffort(self.effort1)
        self.assertEqual([patterns.Event('effort.composite.empty',
            self.composite)], self.events)
        
    def testChangeTask(self):
        self.task.addEffort(self.effort1)
        self.effort1.setTask(task.Task())
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testChangeTask_EmptyNotification(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.composite.empty')
        self.task.addEffort(self.effort1)
        self.effort1.setTask(task.Task())
        self.assertEqual([patterns.Event('effort.composite.empty', 
             self.composite)], self.events)
        
    def testGetDescription_ZeroEfforts(self):
        self.assertEqual('', self.composite.description())
        
    def testGetDescription_OneEffort(self):
        self.task.addEffort(self.effort1)
        for description in ('', 'Description'):
            self.effort1.setDescription(description)
            self.assertEqual(description, self.composite.description())
        
    def testGetDescription_TwoEfforts(self):
        self.task.addEffort(self.effort1)
        self.task.addEffort(self.effort2)
        for description1, description2 in (('', ''), ('descripion1', ''), 
                                           ('', 'description2'), 
                                           ('description1', 'description2')):
            self.effort1.setDescription(description1)
            self.effort2.setDescription(description2)
            if description1 and description2:
                seperator = '\n'
            else:
                seperator = ''
            expectedDescription = description1 + seperator + description2
            self.assertEqual(expectedDescription, self.composite.description())


class CompositeEffortWithSubTasksTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.task = task.Task(subject='task')
        self.child = task.Task(subject='child')
        self.child2 = task.Task(subject='child2')
        self.task.addChild(self.child)
        self.taskEffort = effort.Effort(self.task, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.childEffort = effort.Effort(self.child, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.child2Effort = effort.Effort(self.child2, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.trackedEffort = effort.Effort(self.child, 
            date.DateTime(2004,1,1,9,0,0))
        self.composite = effort.CompositeEffort(self.task,
            date.DateTime(2004,1,1,0,0,0), date.DateTime(2004,1,1,23,59,59))
        self.events = []

    def onEvent(self, event):
        self.events.append(event)

    def testAddEffortToChildTaskNotification(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.duration')
        self.child.addEffort(self.childEffort)
        self.assertEqual(patterns.Event('effort.duration', self.composite,
            self.composite.duration(recursive=True)), self.events[0])

    def testAddTrackedEffortToChildTask(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStartEventType())
        self.child.addEffort(self.trackedEffort)
        self.assertEqual(patterns.Event(self.composite.trackStartEventType(), 
            self.composite, self.trackedEffort), self.events[0])

    def testRemoveEffortFromChildTask(self):
        self.child.addEffort(self.childEffort)
        self.child.removeEffort(self.childEffort)
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testRemoveEffortFromChildNotification(self):
        self.child.addEffort(self.childEffort)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.composite.empty')
        self.child.removeEffort(self.childEffort)
        self.assertEqual(patterns.Event('effort.composite.empty', 
            self.composite), self.events[0])

    def testRemoveTrackedEffortFromChildTask(self):
        self.child.addEffort(self.trackedEffort)
        patterns.Publisher().registerObserver(self.onEvent,
            eventType=self.composite.trackStopEventType())
        self.child.removeEffort(self.trackedEffort)
        self.assertEqual(patterns.Event(self.composite.trackStopEventType(), 
            self.composite, self.trackedEffort), self.events[0])

    def testDuration(self):
        self.child.addEffort(self.childEffort)
        self.assertEqual(date.TimeDelta(), self.composite.duration())

    def testRecursiveDuration(self):
        self.child.addEffort(self.childEffort)
        self.assertEqual(self.childEffort.duration(), 
            self.composite.duration(recursive=True))

    def testDurationWithTaskAndChildEffort(self):
        self.task.addEffort(self.taskEffort)
        self.child.addEffort(self.childEffort)
        self.assertEqual(self.taskEffort.duration() + \
            self.childEffort.duration(), 
            self.composite.duration(recursive=True))

    def testAddEffortToNewChild(self):
        self.task.addChild(self.child2)
        self.child2.addEffort(self.child2Effort)
        self.assertEqual(self.child2Effort.duration(), 
            self.composite.duration(recursive=True))

    def testAddChildWithEffort(self):
        self.child2.addEffort(self.child2Effort)
        self.task.addChild(self.child2)
        self.assertEqual(self.child2Effort.duration(), 
            self.composite.duration(recursive=True))

    def testAddEffortToGrandChild(self):
        self.task.addChild(self.child2)
        grandChild = task.Task(subject='grandchild')
        self.child2.addChild(grandChild)
        grandChildEffort = effort.Effort(grandChild, self.composite.getStart(), 
            self.composite.getStart() + date.TimeDelta(hours=1))
        grandChild.addEffort(grandChildEffort)
        self.assertEqual(grandChildEffort.duration(),
            self.composite.duration(recursive=True))

    def testAddGrandChildWithEffort(self):
        self.task.addChild(self.child2)
        grandChild = task.Task(subject='grandchild')
        grandChildEffort = effort.Effort(grandChild, self.composite.getStart(),
            self.composite.getStart()+date.TimeDelta(hours=1))
        grandChild.addEffort(grandChildEffort)
        self.child2.addChild(grandChild)
        self.assertEqual(grandChildEffort.duration(),
            self.composite.duration(recursive=True))

    def testRemoveEffortFromAddedChild(self):
        self.task.addChild(self.child2)
        self.child2.addEffort(self.child2Effort)
        self.child2.removeEffort(self.child2Effort)
        self.assertEqual(date.TimeDelta(), 
            self.composite.duration(recursive=True))

    def testRemoveChildWithEffort(self):
        self.child.addEffort(self.childEffort)
        self.task.removeChild(self.child)
        self.assertEqual(date.TimeDelta(), 
            self.composite.duration(recursive=True))

    def testRemoveChildWithEffortCausesEmptyNotification(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='effort.composite.empty')
        self.child.addEffort(self.childEffort)
        self.task.removeChild(self.child)
        self.assertEqual(patterns.Event('effort.composite.empty',
            self.composite), self.events[0])

    def testChangeStartTimeOfChildEffort_MoveInsidePeriod(self):
        childEffort = effort.Effort(self.child)
        self.child.addEffort(childEffort)
        childEffort.setStart(self.composite.getStart())
        # Make sure the next assertEqual cannot fail due to duration() being 
        # called twice:
        childEffort.setStop() 
        self.assertEqual(childEffort.duration(),
            self.composite.duration(recursive=True))

    def testChangeTask(self):
        self.child.addEffort(self.childEffort)
        self.childEffort.setTask(task.Task())
        self.assertEqual(date.TimeDelta(), 
            self.composite.duration(recursive=True))


class CompositeEffortWithSubTasksRevenueTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.task = task.Task(subject='task')
        self.child = task.Task(subject='child')
        self.task.addChild(self.child)
        self.taskEffort = effort.Effort(self.task, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.childEffort = effort.Effort(self.child, 
            date.DateTime(2004,1,1,11,0,0), date.DateTime(2004,1,1,12,0,0))
        self.composite = effort.CompositeEffort(self.task,
            date.DateTime(2004,1,1,0,0,0), date.DateTime(2004,1,1,23,59,59))
        self.task.addEffort(self.taskEffort)
        self.child.addEffort(self.childEffort)
        self.events = []
                
    def onEvent(self, event):
        self.events.append(event)
 
    def testRevenueWhenParentHasHourlyFee(self):
        self.task.setHourlyFee(100)
        self.assertEqual(self.taskEffort.duration().hours()*100,
            self.composite.revenue())

    def testRecursiveRevenueWhenParentHasHourlyFee(self):
        self.task.setHourlyFee(100)
        self.assertEqual(self.taskEffort.duration().hours()*100,
            self.composite.revenue(recursive=True))

    def testRevenueWhenChildHasHourlyFee(self):
        self.child.setHourlyFee(100)
        self.assertEqual(0, self.composite.revenue())

    def testRecursiveRevenueWhenChildHasHourlyFee(self):
        self.child.setHourlyFee(100)
        self.assertEqual(self.childEffort.duration().hours()*100, 
            self.composite.revenue(recursive=True))

    def testRevenueWhenChildAndParentHaveHourlyFees(self):
        self.child.setHourlyFee(100)
        self.task.setHourlyFee(200)
        self.assertEqual(self.taskEffort.duration().hours()*200, 
            self.composite.revenue())

    def testRecursiveRevenueWhenChildAndParentHaveHourlyFees(self):
        self.child.setHourlyFee(100)
        self.task.setHourlyFee(200)
        self.assertEqual(self.taskEffort.duration().hours()*200 + \
            self.childEffort.duration().hours()*100, 
            self.composite.revenue(recursive=True))

    def testRevenueWhenParentHasFixedFee(self):
        self.task.setFixedFee(1000)
        self.assertEqual(0, self.composite.revenue())

    def testRecursiveRevenueWhenParentHasFixedFee(self):
        self.task.setFixedFee(1000)
        self.assertEqual(0, self.composite.revenue(recursive=True))

    def testRevenueWhenChildHasFixedFee(self):
        self.child.setFixedFee(1000)
        self.assertEqual(0, self.composite.revenue())

    def testRecursiveRevenueWhenChildHasFixedFee(self):
        self.child.setFixedFee(1000)
        self.assertEqual(0, self.composite.revenue(recursive=True))

    def testRevenueWhenParentHasFixedFeeAndMultipleEfforts(self):
        self.task.setFixedFee(1000)
        self.task.addEffort(effort.Effort(self.task, 
            date.DateTime(2005,12,12,10,0,0), date.DateTime(2005,12,12,12,0,0)))
        self.assertEqual(0, self.composite.revenue())

    def testRevenueWhenChildHasFixedFeeAndMultipleEfforts(self):
        self.child.setFixedFee(1000)
        self.child.addEffort(effort.Effort(self.child, 
            date.DateTime(2005,12,12,10,0,0), date.DateTime(2005,12,12,12,0,0)))
        self.assertEqual(0, self.composite.revenue())

    def testRecursiveRevenueWhenChildHasFixedFeeAndMultipleEfforts(self):
        self.child.setFixedFee(1000)
        self.child.addEffort(effort.Effort(self.child, 
            date.DateTime(2005,12,12,10,0,0), date.DateTime(2005,12,12,12,0,0)))
        self.assertEqual(0, self.composite.revenue(recursive=True))

    def testRevenueWithMixture(self):
        self.child.setFixedFee(100)
        self.task.setHourlyFee(1000)
        self.assertEqual(1000, self.composite.revenue(recursive=True))

    def testThatAnHourlyFeeChangeCausesARevenueNotification(self):
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType='effort.revenue')
        self.child.setHourlyFee(100)
        self.failUnless(patterns.Event('effort.revenue', self.composite,
            100.0) in self.events)
        
        
