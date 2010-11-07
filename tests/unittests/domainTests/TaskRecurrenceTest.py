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
from taskcoachlib.domain import task, date


class RecurringTaskTestCase(test.TestCase):
    def setUp(self):
        self.settings = task.Task.settings = config.Settings(load=False)
        self.yesterday = date.Now() - date.oneDay
        self.tomorrow = date.Now() + date.oneDay
        kwargs_list = self.taskCreationKeywordArguments()
        self.tasks = [task.Task(**kwargs) for kwargs in kwargs_list] # pylint: disable-msg=W0142
        self.task = self.tasks[0]
        for index, eachTask in enumerate(self.tasks):
            taskLabel = 'task%d'%(index+1)
            setattr(self, taskLabel, eachTask)
            
    def taskCreationKeywordArguments(self):
        return [dict(recurrence=self.createRecurrence())]
      
    def createRecurrence(self):
        raise NotImplementedError
    

class RecurringTaskWithChildTestCase(RecurringTaskTestCase):
    def taskCreationKeywordArguments(self):
        kwargs_list = super(RecurringTaskWithChildTestCase, self).taskCreationKeywordArguments()
        kwargs_list[0]['children'] = [task.Task(subject='child')]
        return kwargs_list

    def createRecurrence(self):
        raise NotImplementedError


class RecurringTaskWithRecurringChildTestCase(RecurringTaskTestCase):
    def taskCreationKeywordArguments(self):
        kwargs_list = super(RecurringTaskWithRecurringChildTestCase, self).taskCreationKeywordArguments()
        kwargs_list[0]['children'] = [task.Task(subject='child',
                                                recurrence=self.createRecurrence())]
        return kwargs_list

    def createRecurrence(self):
        raise NotImplementedError


class CommonRecurrenceTestsMixin(object):        
    def testSetRecurrenceViaConstructor(self):
        self.assertEqual(self.createRecurrence(), self.task.recurrence())

    def testMarkCompletedSetsNewStartDateIfItWasSetPreviously(self):
        startDateTime = self.task.startDateTime()
        self.task.setCompletionDateTime()
        self.assertEqual(self.createRecurrence()(startDateTime), self.task.startDateTime())

    def testMarkCompletedSetsNewDueDateIfItWasSetPreviously(self):
        self.task.setDueDateTime(self.tomorrow)
        self.task.setCompletionDateTime()
        self.assertEqual(self.createRecurrence()(self.tomorrow), self.task.dueDateTime())

    def testMarkCompletedDoesNotSetStartDateIfItWasNotSetPreviously(self):
        self.task.setStartDateTime(date.DateTime())
        self.task.setCompletionDateTime()
        self.assertEqual(date.DateTime(), self.task.startDateTime())

    def testMarkCompletedDoesNotSetDueDateIfItWasNotSetPreviously(self):
        self.task.setCompletionDateTime()
        self.assertEqual(date.DateTime(), self.task.dueDateTime())
                
    def testRecurringTaskIsNotCompletedWhenMarkedCompleted(self):
        self.task.setCompletionDateTime()
        self.failIf(self.task.completed())

    def testMarkCompletedDoesNotSetReminderIfItWasNotSetPreviously(self):
        self.task.setCompletionDateTime()
        self.assertEqual(None, self.task.reminder())
    
    def testMarkCompletedSetsNewReminderIfItWasSetPreviously(self):
        reminder = date.Now() + date.TimeDelta(seconds=10)
        self.task.setReminder(reminder)
        self.task.setCompletionDateTime()
        self.assertEqual(self.createRecurrence()(reminder), self.task.reminder())
        
    def testMarkCompletedResetPercentageComplete(self):
        self.task.setPercentageComplete(50)
        self.task.setCompletionDateTime()
        self.assertEqual(0, self.task.percentageComplete())
        
    def testCopyRecurrence(self):
        self.assertEqual(self.task.copy().recurrence(), self.task.recurrence())
                
        
class TaskWithWeeklyRecurrenceFixture(RecurringTaskTestCase,  
                                      CommonRecurrenceTestsMixin):
    def createRecurrence(self):
        return date.Recurrence('weekly')
        
        
class TaskWithDailyRecurrenceFixture(RecurringTaskTestCase, 
                                     CommonRecurrenceTestsMixin):
    def createRecurrence(self):
        return date.Recurrence('daily')


class TaskWithMonthlyRecurrenceFixture(RecurringTaskTestCase,
                                       CommonRecurrenceTestsMixin):
    def createRecurrence(self):
        return date.Recurrence('monthly')


class TaskWithYearlyRecurrenceFixture(RecurringTaskTestCase,
                                      CommonRecurrenceTestsMixin):
    def createRecurrence(self):
        return date.Recurrence('yearly')
       

class TaskWithDailyRecurrenceThatHasRecurredFixture( \
        RecurringTaskTestCase, CommonRecurrenceTestsMixin):
    initialRecurrenceCount = 3
    
    def createRecurrence(self):
        return date.Recurrence('daily', count=self.initialRecurrenceCount)
    


class TaskWithDailyRecurrenceThatHasMaxRecurrenceCountFixture( \
        RecurringTaskTestCase, CommonRecurrenceTestsMixin):
    maxRecurrenceCount = 2
    
    def createRecurrence(self):
        return date.Recurrence('daily', max=self.maxRecurrenceCount)

    def testRecurLessThanMaxRecurrenceCount(self):
        for _ in range(self.maxRecurrenceCount):
            self.task.setCompletionDateTime()
        self.failIf(self.task.completed())
          
    def testRecurExactlyMaxRecurrenceCount(self):
        for _ in range(self.maxRecurrenceCount + 1):
            self.task.setCompletionDateTime()
        self.failUnless(self.task.completed())


class CommonRecurrenceTestsMixinWithChild(CommonRecurrenceTestsMixin):
    # pylint: disable-msg=E1101
    
    def testChildStartDateRecursToo(self):    
        self.task.setCompletionDateTime()
        self.assertAlmostEqual(self.task.startDateTime().toordinal(), 
                               self.task.children()[0].startDateTime().toordinal())

    def testChildDueDateRecursToo_ParentAndChildHaveNoDueDate(self):
        self.task.setCompletionDateTime()
        self.assertAlmostEqual(self.task.dueDateTime().toordinal(), 
                               self.task.children()[0].dueDateTime().toordinal())

    def testChildDueDateRecursToo_ParentAndChildHaveSameDueDate(self):
        child = self.task.children()[0]
        self.task.setDueDateTime(self.tomorrow)
        child.setDueDateTime(self.tomorrow)
        self.task.setCompletionDateTime()
        self.assertAlmostEqual(self.task.dueDateTime().toordinal(), 
                               self.task.children()[0].dueDateTime().toordinal())

    def testChildDueDateRecursToo_ChildHasEarlierDueDate(self):
        child = self.task.children()[0]
        self.task.setDueDateTime(self.tomorrow)
        child.setDueDateTime(date.Now())
        self.task.setCompletionDateTime()
        self.assertEqual(self.createRecurrence()(date.Today()),
                         self.task.children()[0].dueDateTime())


class CommonRecurrenceTestsMixinWithRecurringChild(CommonRecurrenceTestsMixin):
    # pylint: disable-msg=E1101
    
    def testChildDoesNotRecurWhenParentDoes(self):
        origStartDateTime = self.task.children()[0].startDateTime()
        self.task.setCompletionDateTime()
        self.assertEqual(origStartDateTime, 
                         self.task.children()[0].startDateTime())
        
    def testDownwardsRecursiveRecurrence(self):
        expectedRecurrence = min([self.task.recurrence(), 
                                  self.task.children()[0].recurrence()]) 
        self.assertEqual(expectedRecurrence, 
                         self.task.recurrence(recursive=True, upwards=False))
        
        
class TaskWithWeeklyRecurrenceWithChildFixture(RecurringTaskWithChildTestCase,
                                               CommonRecurrenceTestsMixinWithChild):
    def createRecurrence(self):
        return date.Recurrence('weekly')
    

class TaskWithDailyRecurrenceWithChildFixture(RecurringTaskWithChildTestCase,
                                             CommonRecurrenceTestsMixinWithChild):
    def createRecurrence(self):
        return date.Recurrence('daily')
    
    
class TaskWithWeeklyRecurrenceWithRecurringChildFixture(\
    RecurringTaskWithRecurringChildTestCase, 
    CommonRecurrenceTestsMixinWithRecurringChild):
    
    def createRecurrence(self):
        return date.Recurrence('weekly')

    
class TaskWithDailyRecurrenceWithRecurringChildFixture(\
    RecurringTaskWithRecurringChildTestCase, 
    CommonRecurrenceTestsMixinWithRecurringChild):
    
    def createRecurrence(self):
        return date.Recurrence('daily')
