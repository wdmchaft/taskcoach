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

from taskcoachlib.domain import date
from tests import test


class CommonRecurrenceTestsMixin(object):
    def testNextDateWithInfiniteDate(self):
        self.assertEqual(date.Date(), self.recur(date.Date()))

    def testCopy(self):
        copy = self.recur.copy()
        self.assertEqual(copy, self.recur)

    def testNotEqualToNone(self):
        self.assertNotEqual(None, self.recur)

    def testSetMaxRecurrenceCount(self):
        self.recur.max = 1
        self.recur(date.Today())
        self.failIf(self.recur)
        
    def testSetMaxRecurrenceCount_GetMultipleDates(self):
        self.recur.max = 1
        self.recur(date.Today(), next=False)
        self.failUnless(self.recur)

    def testCount(self):
        self.assertEqual(0, self.recur.count)
                

class NoRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence()
        
    def testNextDate(self):
        self.assertEqual(date.Today(), self.recur(date.Today()))
        
    def testBool(self):
        self.failIf(self.recur)

    def testSetMaxRecurrenceCount_GetMultipleDates(self):
        pass
    

class DailyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('daily')
                
    def testNextDate(self):
        self.assertEqual(date.Tomorrow(), self.recur(date.Today()))
        
    def testMultipleNextDates(self):
        self.assertEqual((date.Tomorrow(), date.Today()),
                         self.recur(date.Today(), date.Yesterday()))
        
    def testNextDateTwice(self):
        today = self.recur(date.Yesterday())
        self.assertEqual(date.Tomorrow(), self.recur(today))
        

class BiDailyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('daily', amount=2)
        
    def testEveryOtherDay(self):
        self.assertEqual(date.Tomorrow(), self.recur(date.Yesterday()))


class TriDailyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('daily', amount=3)
        
    def testEveryThirdDay(self):
        self.assertEqual(date.Date(2000,1,4), self.recur(date.Date(2000,1,1)))
            
        
class WeeklyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.January1 = date.Date(2000,1,1)
        self.January8 = date.Date(2000,1,8)
        self.January15 = date.Date(2000,1,15)
        self.recur = date.Recurrence('weekly')
        
    def testNextDate(self):
        self.assertEqual(self.January8, self.recur(self.January1))
        
    def testNextDateTwice(self):
        January8 = self.recur(self.January1)
        self.assertEqual(self.January15, self.recur(January8))


class BiWeeklyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('weekly', amount=2)
                
    def testEveryOtherWeek(self):
        self.assertEqual(date.Date(2000,1,15), self.recur(date.Date(2000,1,1)))


class MonthlyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('monthly')
        
    def testFirstDayOf31DayMonth(self):
        self.assertEqual(date.Date(2000,2,1), self.recur(date.Date(2000,1,1)))
        
    def testFirstDayOf30DayMonth(self):
        self.assertEqual(date.Date(2000,5,1), self.recur(date.Date(2000,4,1)))
        
    def testFirstDayOfDecember(self):
        self.assertEqual(date.Date(2001,1,1), self.recur(date.Date(2000,12,1)))
        
    def testLastDayOf31DayMonth(self):
        self.assertEqual(date.Date(2000,4,30), self.recur(date.Date(2000,3,31)))
        
    def testLastDayOf30DayMonth(self):
        self.assertEqual(date.Date(2000,5,30), self.recur(date.Date(2000,4,30)))
        

class BiMontlyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('monthly', amount=2)
        
    def testEveryOtherMonth(self):
        self.assertEqual(date.Date(2000,3,1), self.recur(date.Date(2000,1,1)))


class MonthlySameWeekDayRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('monthly', sameWeekday=True)
        
    def testFirstSaturdayOfTheMonth(self):
        self.assertEqual(date.Date(2008,7,5), self.recur(date.Date(2008,6,7)))
        
    def testSecondSaturdayOfTheMonth(self):
        self.assertEqual(date.Date(2008,7,12), self.recur(date.Date(2008,6,14)))

    def testThirdSaturdayOfTheMonth(self):
        self.assertEqual(date.Date(2008,7,19), self.recur(date.Date(2008,6,21)))

    def testFourthSaturdayOfTheMonth(self):
        self.assertEqual(date.Date(2008,7,26), self.recur(date.Date(2008,6,28)))

    def testFifthSaturdayOfTheMonth_ResultsInFourthSaterdayOfTheNextMonth(self):
        self.assertEqual(date.Date(2008,6,28), self.recur(date.Date(2008,5,31)))


class BiMonthlySameWeekDayRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('monthly', amount=2, sameWeekday=True)
        
    def testFourthSaturdayOfTheMonth(self):
        self.assertEqual(date.Date(2008,8,23), self.recur(date.Date(2008,6,28)))


class YearlyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('yearly')
        
    def testJanuary1(self):
        self.assertEqual(date.Date(2002,1,1), self.recur(date.Date(2001,1,1)))

    def testJanuary1_LeapYear(self):
        self.assertEqual(date.Date(2001,1,1), self.recur(date.Date(2000,1,1)))

    def testMarch1_LeapYear(self):
        self.assertEqual(date.Date(2001,3,1), self.recur(date.Date(2000,3,1)))
        
    def testMarch1_YearBeforeLeapYear(self):
        self.assertEqual(date.Date(2004,3,1), self.recur(date.Date(2003,3,1)))

    def testFebruary1_YearBeforeLeapYear(self):
        self.assertEqual(date.Date(2004,2,1), self.recur(date.Date(2003,2,1)))

    def testFebruary28(self):
        self.assertEqual(date.Date(2003,2,28), self.recur(date.Date(2002,2,28)))

    def testFebruary28_LeapYear(self):
        self.assertEqual(date.Date(2005,2,28), self.recur(date.Date(2004,2,28)))

    def testFebruary28_YearBeforeLeapYear(self):
        self.assertEqual(date.Date(2004,2,28), self.recur(date.Date(2003,2,28)))

    def testFebruary29(self):
        self.assertEqual(date.Date(2005,2,28), self.recur(date.Date(2004,2,29)))
                
        
class BiYearlyRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('yearly', amount=2)
        
    def testEveryOtherYear(self):
        self.assertEqual(date.Date(2004,3,1), self.recur(date.Date(2002,3,1)))
            

class YearlySameWeekDayRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('yearly', sameWeekday=True)
        
    def testFirstTuesdayOfTheYear(self):
        self.assertEqual(date.Date(2009,1,6), self.recur(date.Date(2008,1,1)))

    def testFirstWednesdayOfTheYear(self):
        self.assertEqual(date.Date(2009,1,7), self.recur(date.Date(2008,1,2)))

    def testFirstThursdayOfTheYear(self):
        self.assertEqual(date.Date(2009,1,1), self.recur(date.Date(2008,1,3)))

    def testFirstFridayOfTheYear(self):
        self.assertEqual(date.Date(2009,1,2), self.recur(date.Date(2008,1,4)))

    def testLastWednesdayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,30), 
                         self.recur(date.Date(2008,12,31)))

    def testLastTuesdayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,29), 
                         self.recur(date.Date(2008,12,30)))

    def testLastMondayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,28), 
                         self.recur(date.Date(2008,12,29)))

    def testLastSundayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,27), 
                         self.recur(date.Date(2008,12,28)))

    def testLastSaturdayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,26), 
                         self.recur(date.Date(2008,12,27)))

    def testLastFridayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,25), 
                         self.recur(date.Date(2008,12,26)))

    def testLastThursdayOfTheYear(self):
        self.assertEqual(date.Date(2009,12,24), 
                         self.recur(date.Date(2008,12,25)))

        
class MaxRecurrenceTest(test.TestCase, CommonRecurrenceTestsMixin):
    def setUp(self):
        self.recur = date.Recurrence('daily', max=4)
        
    def testFirst(self):
        self.assertEqual(date.Date(2000,1,2), 
                         self.recur(date.Date(2000,1,1), next=True))
        
    def testCountAfterFirst(self):
        self.recur(date.Date(2000,1,1), next=True)
        self.assertEqual(1, self.recur.count)
        
    def testLast(self):
        self.recur.count = 4
        self.assertEqual(None, self.recur(date.Date(2000,1,1), next=True))

