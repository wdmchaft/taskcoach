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

import test
from taskcoachlib import config
from taskcoachlib.domain import task, date, effort

 
class CommonTaskRelationshipManagerTestsMixin(object):
    def setUp(self):
        task.Task.settings = settings = config.Settings(load=False)
        self.parent = task.Task('parent')
        self.child = task.Task('child')
        self.parent.addChild(self.child)
        self.child.setParent(self.parent)
        self.child2 = task.Task('child2')
        self.grandchild = task.Task('grandchild')
        settings.set('behavior', 'markparentcompletedwhenallchildrencompleted', 
            str(self.markParentCompletedWhenAllChildrenCompleted))
        self.taskList = task.TaskList([self.parent, self.child2, self.grandchild])
        
    # completion date
    
    def testMarkingOneOfTwoChildsCompletedNeverResultsInACompletedParent(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDate()
        self.failIf(self.parent.completed())

    def testMarkParentWithOneChildCompleted(self):
        self.parent.setCompletionDate()
        self.failUnless(self.child.completed())

    def testMarkParentWithTwoChildrenCompleted(self):
        self.parent.addChild(self.child2)        
        self.parent.setCompletionDate()
        self.failUnless(self.child.completed())
        self.failUnless(self.child2.completed())

    def testMarkParentNotCompleted(self):
        self.parent.setCompletionDate()
        self.failUnless(self.child.completed())
        self.parent.setCompletionDate(date.Date())
        self.failUnless(self.child.completed())

    def testMarkParentCompletedDoesNotChangeChildCompletionDate(self):
        self.parent.addChild(self.child2)        
        self.child.setCompletionDate(date.Yesterday())
        self.parent.setCompletionDate()
        self.assertEqual(date.Yesterday(), self.child.completionDate())

    def testMarkChildNotCompleted(self):
        self.child.setCompletionDate()
        self.child.setCompletionDate(date.Date())
        self.failIf(self.parent.completed())
 
    def testAddCompletedChild(self):
        self.child2.setCompletionDate()
        self.parent.addChild(self.child2)
        self.failIf(self.parent.completed())

    def testAddUncompletedChild(self):
        self.child.setCompletionDate()
        self.parent.addChild(self.child2)
        self.failIf(self.parent.completed())
    
    def testAddUncompletedGrandchild(self):
        self.parent.setCompletionDate()
        self.child.addChild(self.grandchild)
        self.failIf(self.parent.completed())

    def testMarkParentCompletedYesterday(self):
        self.parent.setCompletionDate(date.Yesterday())
        self.assertEqual(date.Yesterday(), self.child.completionDate())

    def testMarkTaskCompletedStopsEffortTracking(self):
        self.child.addEffort(effort.Effort(self.child))
        self.child.setCompletionDate()
        self.failIf(self.child.isBeingTracked())
    
    # recurrence
        
    def testMarkParentCompletedStopsChildRecurrence(self):
        self.child.setRecurrence(date.Recurrence('daily'))
        self.parent.setCompletionDate()
        self.failIf(self.child.recurrence())
        
    def testRecurringChildIsCompletedWhenParentIsCompleted(self):
        self.child.setRecurrence(date.Recurrence('daily'))
        self.parent.setCompletionDate()
        self.failUnless(self.child.completed())
        
    def shouldMarkCompletedWhenAllChildrenCompleted(self, parent):
        return parent.shouldMarkCompletedWhenAllChildrenCompleted() == True or \
            (parent.shouldMarkCompletedWhenAllChildrenCompleted() == None and \
             self.markParentCompletedWhenAllChildrenCompleted == True)
        
    def testMarkLastChildCompletedMakesParentRecur(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertEqual(date.Today() + date.TimeDelta(days=7), 
                             self.parent.startDate())
        else:
            self.assertEqual(date.Today(), self.parent.startDate())

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildToo(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertEqual(date.Today() + date.TimeDelta(days=7), 
                             self.child.startDate())
        else:
            self.assertEqual(date.Today(), self.child.startDate())

    def testMarkLastChildCompletedMakesParentRecur_AndThusChildIsNotCompleted(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.failIf(self.child.completed())
        else:
            self.failUnless(self.child.completed())

    def testMarkLastGrandChildCompletedMakesParentRecur(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertEqual(date.Today() + date.TimeDelta(days=7), 
                             self.parent.startDate())
        else:
            self.assertEqual(date.Today(), self.parent.startDate())

    def testMarkLastGrandChildCompletedMakesParentRecur_AndThusGrandChildToo(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.assertEqual(date.Today() + date.TimeDelta(days=7), 
                             self.grandchild.startDate())
        else:
            self.assertEqual(date.Today(), self.grandchild.startDate())

    def testMarkLastChildCompletedMakesParentRecur_AndThusGrandChildIsNotCompleted(self):
        self.parent.setRecurrence(date.Recurrence('weekly'))
        self.child.addChild(self.grandchild)
        self.grandchild.setParent(self.child)
        self.grandchild.setCompletionDate()
        if self.shouldMarkCompletedWhenAllChildrenCompleted(self.parent):
            self.failIf(self.grandchild.completed())
        else:
            self.failUnless(self.grandchild.completed())

    # due date
        
    def testAddChildWithoutDueDateToParentWithoutDueDate(self):
        self.assertEqual(date.Date(), self.child.dueDate())
        self.assertEqual(date.Date(), self.parent.dueDate())

    def testAddChildWithDueDateToParentWithoutDueDate(self):
        self.child2.setDueDate(date.Today())
        self.parent.addChild(self.child2)
        self.assertEqual(date.Date(), self.parent.dueDate())
        
    def testAddChildWithoutDueDateToParentWithDueDate(self):
        self.parent.setDueDate(date.Tomorrow())
        self.parent.addChild(self.child2)
        self.assertEqual(date.Date(), self.parent.dueDate())
        
    def testAddChildWithDueDateSmallerThanParentDueDate(self):
        self.parent.setDueDate(date.Tomorrow())
        self.child2.setDueDate(date.Today())
        self.parent.addChild(self.child2)
        self.assertEqual(date.Tomorrow(), self.parent.dueDate())
        
    def testAddChildWithDueDateLargerThanParentDueDate(self):
        self.parent.setDueDate(date.Today())
        self.child2.setDueDate(date.Tomorrow())
        self.parent.addChild(self.child2)
        self.assertEqual(date.Tomorrow(), self.parent.dueDate())
        
    def testSetDueDateChildSmallerThanParent(self):
        self.child.setDueDate(date.Today())
        self.assertEqual(date.Date(), self.parent.dueDate())
        
    def testSetDueDateParent(self):
        self.parent.setDueDate(date.Today())
        self.assertEqual(self.parent.dueDate(), self.child.dueDate())
        
    def testSetDueDateParentLargerThanChild(self):
        self.parent.setDueDate(date.Today())
        self.parent.setDueDate(date.Date())
        self.assertEqual(date.Today(), self.child.dueDate())
        
    def testSetDueDateChildLargerThanParent(self):
        self.parent.setDueDate(date.Today())
        self.child.setDueDate(date.Tomorrow())
        self.assertEqual(date.Tomorrow(), self.parent.dueDate())

    # start date

    def testAddChildWithStartDateToParentWithStartDate(self):
        self.assertEqual(date.Today(), self.parent.startDate())
        self.assertEqual(date.Today(), self.child.startDate())
        
    def testAddChildWithBiggerStartDateThanParent(self):
        self.child2.setStartDate(date.Tomorrow())
        self.parent.addChild(self.child2)
        self.assertEqual(date.Today(), self.parent.startDate())
        
    def testAddChildWithSmallerStartDateThanParent(self):
        self.child2.setStartDate(date.Yesterday())
        self.parent.addChild(self.child2)
        self.assertEqual(self.child2.startDate(), self.parent.startDate())
        
    def testSetStartDateParentInfinite(self):
        self.parent.setStartDate(date.Date())
        self.assertEqual(date.Date(), self.child.startDate())
        
    def testSetStartDateParentBiggerThanChildStartDate(self):
        self.parent.setStartDate(date.Tomorrow())
        self.assertEqual(date.Tomorrow(), self.child.startDate())
        
    def testSetChildStartDateInfinite(self):
        self.child.setStartDate(date.Date())
        self.assertEqual(date.Today(), self.parent.startDate())
        
    def testSetChildStartDateEarlierThanParentStartDate(self):
        self.child.setStartDate(date.Yesterday())
        self.assertEqual(date.Yesterday(), self.parent.startDate())


class MarkParentTaskCompletedTestsMixin(object):
    ''' Tests where we expect to parent task to be marked completed, based on
        the fact that all children are completed. This happens when the global
        setting is on and task is indifferent or the task specific setting is 
        on. '''
        
    def testMarkOnlyChildCompleted(self):
        self.child.setCompletionDate()
        self.failUnless(self.parent.completed())
        
    def testMarkOnlyGrandchildCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDate()
        self.failUnless(self.parent.completed())                        
              
    def testAddCompletedChildAsOnlyChild(self):
        self.grandchild.setCompletionDate()
        self.child.addChild(self.grandchild)
        self.failUnless(self.child.completed())
        
    def testMarkChildCompletedYesterday(self):    
        self.child.setCompletionDate(date.Yesterday())
        self.assertEqual(date.Yesterday(), self.parent.completionDate())
        
    def testRemoveLastUncompletedChild(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDate()
        self.parent.removeChild(self.child2)
        self.failUnless(self.parent.completed())
    
    
class DontMarkParentTaskCompletedTestsMixin(object):
    ''' Tests where we expect the parent task not to be marked completed when 
        all children are completed. This should be the case when the global
        setting is off and task is indifferent or when the task specific 
        setting is off. '''
  
    def testMarkOnlyChildCompletedDoesNotMarkParentCompleted(self):
        self.child.setCompletionDate()
        self.failIf(self.parent.completed())

    def testMarkOnlyGrandchildCompletedDoesNotMarkParentCompleted(self):
        self.child.addChild(self.grandchild)
        self.grandchild.setCompletionDate()
        self.failIf(self.parent.completed())    
 
    def testAddCompletedChildAsOnlyChildDoesNotMarkParentCompleted(self):
        self.grandchild.setCompletionDate()
        self.child.addChild(self.grandchild)
        self.failIf(self.child.completed())

    def testMarkChildCompletedYesterdayDoesNotAffectParentCompletionDate(self):    
        self.child.setCompletionDate(date.Yesterday())
        self.assertEqual(date.Date(), self.parent.completionDate())

    def testRemoveLastUncompletedChildDoesNotMarkParentCompleted(self):
        self.parent.addChild(self.child2)
        self.child.setCompletionDate()
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
