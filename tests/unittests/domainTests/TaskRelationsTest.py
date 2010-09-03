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
from taskcoachlib import config
from taskcoachlib.domain import task, date, effort

 
class CommonTaskRelationshipManagerTestsMixin(object):
    def setUp(self):
        task.Task.settings = settings = config.Settings(load=False)
        now = self.now = date.Now()
        self.yesterday = now - date.oneDay
        self.tomorrow = now + date.oneDay
        self.parent = task.Task('parent', startDateTime=now)
        self.child = task.Task('child', startDateTime=now)
        self.parent.addChild(self.child)
        self.child.setParent(self.parent)
        self.child2 = task.Task('child2', startDateTime=now)
        self.grandchild = task.Task('grandchild', startDateTime=now)
        settings.set('behavior', 'markparentcompletedwhenallchildrencompleted', 
            str(self.markParentCompletedWhenAllChildrenCompleted))
        self.taskList = task.TaskList([self.parent, self.child2, self.grandchild])
        
    # completion date
    
    def testMarkingOneOfTwoChildsCompletedNeverResultsInACompletedParent(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.failIf(self.parent.completed())

    def testMarkParentWithOneChildCompleted(self):
        self.parent.setCompletionDateTime()
        self.failUnless(self.child.completed())

    def testMarkParentWithTwoChildrenCompleted(self):
        self.parent.addChild(self.child2)        
        self.parent.setCompletionDateTime()
        self.failUnless(self.child.completed())
        self.failUnless(self.child2.completed())

    def testMarkParentNotCompleted(self):
        self.parent.setCompletionDateTime()
        self.failUnless(self.child.completed())
        self.parent.setCompletionDateTime(date.DateTime())
        self.failUnless(self.child.completed())

    def testMarkParentCompletedDoesNotChangeChildCompletionDate(self):
        self.parent.addChild(self.child2)        
        self.child.setCompletionDateTime(self.yesterday)
        self.parent.setCompletionDateTime()
        self.assertEqual(self.yesterday, self.child.completionDateTime())

    def testMarkChildNotCompleted(self):
        self.child.setCompletionDateTime()
        self.child.setCompletionDateTime(date.DateTime())
        self.failIf(self.parent.completed())
 
    def testAddCompletedChild(self):
        self.child2.setCompletionDateTime()
        self.parent.addChild(self.child2)
        self.failIf(self.parent.completed())

    def testAddUncompletedChild(self):
        self.child.setCompletionDateTime()
        self.parent.addChild(self.child2)
        self.failIf(self.parent.completed())
    
    def testAddUncompletedGrandchild(self):
        self.parent.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.failIf(self.parent.completed())

    def testMarkParentCompletedYesterday(self):
        self.parent.setCompletionDateTime(self.yesterday)
        self.assertEqual(self.yesterday, self.child.completionDateTime())

    def testMarkTaskCompletedStopsEffortTracking(self):
        self.child.addEffort(effort.Effort(self.child))
        self.child.setCompletionDateTime()
        self.failIf(self.child.isBeingTracked())
    
    # recurrence
        
    def testMarkParentCompletedStopsChildRecurrence(self):
        self.child.setRecurrence(date.Recurrence('daily'))
        self.parent.setCompletionDateTime()
        self.failIf(self.child.recurrence())
        
    def testRecurringChildIsCompletedWhenParentIsCompleted(self):
        self.child.setRecurrence(date.Recurrence('daily'))
        self.parent.setCompletionDateTime()
        self.failUnless(self.child.completed())
        
    def shouldMarkCompletedWhenAllChildrenCompleted(self, parent):
        return parent.shouldMarkCompletedWhenAllChildrenCompleted() == True or \
            (parent.shouldMarkCompletedWhenAllChildrenCompleted() == None and \
             self.markParentCompletedWhenAllChildrenCompleted == True)
        
    def testMarkLastChildCompletedMakesParentRecur(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDateTime(self.now)
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedStartDateTime = self.now + date.TimeDelta(days=7)
            self.assertAlmostEqual(expectedStartDateTime.toordinal(), 
                                   self.parent.startDateTime().toordinal())
        else:
            self.assertAlmostEqual(self.now.toordinal(), 
                                   self.parent.startDateTime().toordinal())

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildToo(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDateTime(self.now)
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedStartDateTime = self.now + date.TimeDelta(days=7)
            self.assertAlmostEqual(expectedStartDateTime.toordinal(), 
                                   self.child.startDateTime().toordinal())
        else:
            self.assertAlmostEqual(self.now.toordinal(), 
                                   self.child.startDateTime().toordinal())

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildIsNotCompleted(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDateTime()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.failIf(self.child.completed())
        else:
            self.failUnless(self.child.completed())

    def testMarkLastGrandChildCompletedMakesParentRecur(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime(self.now)
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedStartDateTime = self.now + date.TimeDelta(days=7)
            self.assertAlmostEqual(expectedStartDateTime.toordinal(), 
                                   self.parent.startDateTime().toordinal())
        else:
            self.assertAlmostEqual(self.now.toordinal(), 
                                   self.parent.startDateTime().toordinal())

    def testMarkLastGrandChildCompletedMakesParentRecur_AndThusGrandChildToo(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime(self.now)
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            expectedStartDateTime = self.now + date.TimeDelta(days=7)
            self.assertAlmostEqual(expectedStartDateTime.toordinal(), 
                                   self.grandchild.startDateTime().toordinal())
        else:
            self.assertAlmostEqual(self.now.toordinal(), 
                                   self.grandchild.startDateTime().toordinal())

    def testMarkLastChildCompletedMakesParentRecur_AndThusGrandChildIsNotCompleted(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDateTime()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.failIf(self.grandchild.completed())
        else:
            self.failUnless(self.grandchild.completed())

    # due date
        
    def testAddChildWithoutDueDateToParentWithoutDueDate(self):
        self.assertEqual(date.DateTime(), self.child.dueDateTime())
        self.assertEqual(date.DateTime(), self.parent.dueDateTime())

    def testAddChildWithDueDateToParentWithoutDueDate(self):
        self.child2.setDueDateTime(self.now.endOfDay())
        self.parent.addChild(self.child2)
        self.assertEqual(date.DateTime(), self.parent.dueDateTime())
        
    def testAddChildWithoutDueDateToParentWithDueDate(self):
        self.parent.setDueDateTime(self.tomorrow)
        self.parent.addChild(self.child2)
        self.assertEqual(date.DateTime(), self.parent.dueDateTime())
        
    def testAddChildWithDueDateSmallerThanParentDueDate(self):
        self.parent.setDueDateTime(self.tomorrow)
        self.child2.setDueDateTime(self.now.endOfDay())
        self.parent.addChild(self.child2)
        self.assertEqual(self.tomorrow, self.parent.dueDateTime())
        
    def testAddChildWithDueDateLargerThanParentDueDate(self):
        self.parent.setDueDateTime(self.now.endOfDay())
        self.child2.setDueDateTime(self.tomorrow)
        self.parent.addChild(self.child2)
        self.assertEqual(self.tomorrow, self.parent.dueDateTime())
        
    def testSetDueDateChildSmallerThanParent(self):
        self.child.setDueDateTime(self.now.endOfDay())
        self.assertEqual(date.DateTime(), self.parent.dueDateTime())
        
    def testSetDueDateParent(self):
        self.parent.setDueDateTime(self.now.endOfDay())
        self.assertEqual(self.parent.dueDateTime(), self.child.dueDateTime())
        
    def testSetDueDateParentLargerThanChild(self):
        self.parent.setDueDateTime(self.now.endOfDay())
        self.parent.setDueDateTime(date.DateTime())
        self.assertEqual(self.now.endOfDay(), self.child.dueDateTime())
        
    def testSetDueDateChildLargerThanParent(self):
        self.parent.setDueDateTime(self.now.endOfDay())
        self.child.setDueDateTime(self.tomorrow)
        self.assertEqual(self.tomorrow, self.parent.dueDateTime())

    # start date

    def testAddChildWithStartDateToParentWithStartDate(self):
        self.assertAlmostEqual(self.parent.startDateTime().toordinal(), 
                               self.child.startDateTime().toordinal())
        
    def testAddChildWithBiggerStartDateThanParent(self):
        self.child2.setStartDateTime(self.tomorrow)
        self.parent.addChild(self.child2)
        self.assertAlmostEqual(self.now.toordinal(), 
                               self.parent.startDateTime().toordinal())
        
    def testAddChildWithSmallerStartDateThanParent(self):
        self.child2.setStartDateTime(self.yesterday)
        self.parent.addChild(self.child2)
        self.assertEqual(self.child2.startDateTime(), self.parent.startDateTime())
        
    def testSetStartDateParentInfinite(self):
        self.parent.setStartDateTime(date.DateTime())
        self.assertEqual(date.DateTime(), self.child.startDateTime())
        
    def testSetStartDateParentBiggerThanChildStartDate(self):
        self.parent.setStartDateTime(self.tomorrow)
        self.assertEqual(self.tomorrow, self.child.startDateTime())
        
    def testSetChildStartDateInfinite(self):
        self.child.setStartDateTime(date.DateTime())
        self.assertAlmostEqual(self.now.toordinal(), 
                               self.parent.startDateTime().toordinal())
        
    def testSetChildStartDateEarlierThanParentStartDate(self):
        self.child.setStartDateTime(self.yesterday)
        self.assertEqual(self.yesterday, self.parent.startDateTime())


class MarkParentTaskCompletedTestsMixin(object):
    ''' Tests where we expect to parent task to be marked completed, based on
        the fact that all children are completed. This happens when the global
        setting is on and task is indifferent or the task specific setting is 
        on. '''
        
    def testMarkOnlyChildCompleted(self):
        self.child.setCompletionDateTime()
        self.failUnless(self.parent.completed())
        
    def testMarkOnlyGrandchildCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDateTime()
        self.failUnless(self.parent.completed())                        
              
    def testAddCompletedChildAsOnlyChild(self):
        self.grandchild.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.failUnless(self.child.completed())
        
    def testMarkChildCompletedYesterday(self):    
        self.child.setCompletionDateTime(self.yesterday)
        self.assertEqual(self.yesterday, self.parent.completionDateTime())
        
    def testRemoveLastUncompletedChild(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.parent.removeChild(self.child2)
        self.failUnless(self.parent.completed())
    
    
class DontMarkParentTaskCompletedTestsMixin(object):
    ''' Tests where we expect the parent task not to be marked completed when 
        all children are completed. This should be the case when the global
        setting is off and task is indifferent or when the task specific 
        setting is off. '''
  
    def testMarkOnlyChildCompletedDoesNotMarkParentCompleted(self):
        self.child.setCompletionDateTime()
        self.failIf(self.parent.completed())

    def testMarkOnlyGrandchildCompletedDoesNotMarkParentCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDateTime()
        self.failIf(self.parent.completed())    
 
    def testAddCompletedChildAsOnlyChildDoesNotMarkParentCompleted(self):
        self.grandchild.setCompletionDateTime()
        self.child.addChild(self.grandchild)
        self.failIf(self.child.completed())

    def testMarkChildCompletedYesterdayDoesNotAffectParentCompletionDate(self):    
        self.child.setCompletionDateTime(self.yesterday)
        self.assertEqual(date.DateTime(), self.parent.completionDateTime())

    def testRemoveLastUncompletedChildDoesNotMarkParentCompleted(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDateTime()
        self.parent.removeChild(self.child2)
        self.failIf(self.parent.completed())        


class MarkParentCompletedAutomaticallyIsOn(CommonTaskRelationshipManagerTestsMixin,
                                           MarkParentTaskCompletedTestsMixin,
                                           test.TestCase):
    markParentCompletedWhenAllChildrenCompleted = True


class MarkParentCompletedAutomaticallyIsOff(CommonTaskRelationshipManagerTestsMixin,
                                            DontMarkParentTaskCompletedTestsMixin,
                                            test.TestCase):
    markParentCompletedWhenAllChildrenCompleted = False
              

class MarkParentCompletedAutomaticallyIsOnButTaskSettingIsOff( \
        CommonTaskRelationshipManagerTestsMixin, test.TestCase,
        DontMarkParentTaskCompletedTestsMixin):
    markParentCompletedWhenAllChildrenCompleted = True
    
    def setUp(self):
        super(MarkParentCompletedAutomaticallyIsOnButTaskSettingIsOff, self).setUp()
        for eachTask in self.parent, self.child:
            eachTask.setShouldMarkCompletedWhenAllChildrenCompleted(False)


class MarkParentCompletedAutomaticallyIsOffButTaskSettingIsOn( \
        CommonTaskRelationshipManagerTestsMixin, test.TestCase,
        MarkParentTaskCompletedTestsMixin):
    markParentCompletedWhenAllChildrenCompleted = False

    def setUp(self):
        super(MarkParentCompletedAutomaticallyIsOffButTaskSettingIsOn, self).setUp()
        for eachTask in self.parent, self.child:
            eachTask.setShouldMarkCompletedWhenAllChildrenCompleted(True)
