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

import test, time, datetime
from taskcoachlib.domain import date


class DateTest(test.TestCase):
    def testCreateNormalDate(self):
        adate = date.Date(2003, 1, 1)
        self.assertEqual(2003, adate.year)
        self.assertEqual(1, adate.month)
        self.assertEqual(1, adate.day)
        self.assertEqual(3, adate.weekday())
        self.assertEqual('2003-01-01', str(adate))

    def testCreateInvalidDate(self):
        self.assertRaises(ValueError, date.Date, 2003, 2, 31)
        self.assertRaises(ValueError, date.Date, 2003, 12, 32)
        self.assertRaises(ValueError, date.Date, 2003, 13, 1)
        self.assertRaises(ValueError, date.Date, 2003, 2, -1)
        self.assertRaises(ValueError, date.Date, 2003, 2, 0)

    def testCreateInfiniteDate(self):
        adate = date.Date()
        self.assertEqual(None, adate.year)
        self.assertEqual(None, adate.month)
        self.assertEqual(None, adate.day)
        self.assertEqual(None, adate.weekday())
        self.assertEqual(None, adate.weeknumber())
        self.assertEqual('', str(adate))

    def testCreateInfiniteDateWithMaxValues(self):
        maxDate = datetime.date.max
        infinite = date.Date(maxDate.year, maxDate.month, maxDate.day)
        self.failUnless(infinite is date.Date())

    def testInfiniteDateIsSingleton(self):
        self.failUnless(date.Date() is date.Date())
        
    def testAddTimeDeltaToInfiniteDate(self):
        self.assertEqual(date.Date(), date.Date() + date.TimeDelta(days=2))

    def testWeeknumber(self):
        adate = date.Date(2002, 1, 5)
        self.assertEqual(1, adate.weeknumber())
        adate = date.Date(2002, 12, 24)
        self.assertEqual(52, adate.weeknumber())
        adate = date.Date(2002, 12, 31)
        self.assertEqual(1, adate.weeknumber())

    def testCompare_TwoInfiniteDates(self):
        date1 = date.Date()
        date2 = date.Date()
        self.assertEquals(date1, date2)

    def testCompare_TwoNormalDates(self):
        date1 = date.Date(2003,1,1)
        date2 = date.Date(2003,4,5)
        self.failUnless(date1 < date2)
        self.failUnless(date2 > date1)
        self.failIf(date1 == date2)

    def testCompare_OneNormalDate(self):
        date1 = date.Date(2003,1,1)
        date2 = date.Date(2003,1,1)
        self.assertEquals(date1, date2)

    def testCompare_NormalDateWithInfiniteDate(self):
        date1 = date.Date()
        date2 = date.Date(2003,1,1)
        self.failUnless(date2 < date1)
        self.failUnless(date1 > date2)

    def testAddDay(self):
        tomorrow = date.Today() + date.oneDay
        self.assertEqual(date.Tomorrow(), tomorrow)
        self.failUnless(isinstance(tomorrow, date.date.RealDate))
        
    def testAddManyDays(self):
        self.assertEqual(date.Date(2003,1,1), 
            date.Date(2002,1,1) + date.oneYear)

    def testSubstractDay(self):
        self.assertEqual(date.Yesterday(), date.Today() - date.oneDay)

    def testNextSunday(self):
        self.assertEqual(date.Date(2004, 2, 29).nextSunday(), 
            date.Date(2004, 2, 29))
        self.assertEqual(date.Date(2004, 3, 1).nextSunday(), 
            date.Date(2004, 3, 7))

    def testSubstractTwoDates_ZeroDifference(self):
        self.assertEqual(date.TimeDelta(), date.Today() - date.Today())

    def testSubstractTwoDates_OneDifference(self):
        self.assertEqual(date.TimeDelta(days=1), 
            date.Tomorrow() - date.Today())

    def testSubstractTwoDates_MinusOneDifference(self):
        self.assertEqual(date.TimeDelta(days=-1), 
            date.Today() - date.Tomorrow())

    def testSubstractTwoDates_YearDifference(self):
        self.assertEqual(date.TimeDelta(days=365), 
            date.Today() + date.oneYear - date.Today())

    def testSubstractTwoDates_Infinite(self):
        self.assertEqual(date.TimeDelta.max, date.Date() - date.Today())

    def testSubstractTwoDates_BothInfinite(self):
        self.assertEqual(date.TimeDelta(days=0), date.Date() - date.Date())
        
        
class FactoriesTest(test.TestCase):
    def testToday(self):
        today = date.Today()
        localtime = time.localtime()
        self.assertEqual(date.Date(*localtime[0:3]), today)

    def testTomorrow(self):
        self.assertEqual(date.Today() + date.oneDay, date.Tomorrow())

    def testYesterday(self):
        self.assertEqual(date.Today() - date.oneDay, date.Yesterday())

    def testParseDate(self):
        parsed = date.parseDate("2004-1-1")
        self.assertEqual(date.Date(2004, 1, 1), parsed)

    def testParseDate_WithNone(self):
        parsed = date.parseDate("None")
        self.assertEqual(date.Date(), parsed)

    def testParseDate_WithNonsense(self):
        parsed = date.parseDate("Yoyo-Yo")
        self.assertEqual(date.Date(), parsed)

    def testParseDate_WithDifferentDefaultDate(self):
        parsed = date.parseDate("Yoyo-Yo", date.Today())
        self.assertEqual(date.Today(), parsed)

    def testNextSunday(self):
        self.assertEqual(date.Today().nextSunday(), date.NextSunday())

    def testNextFriday(self):
        self.assertEqual(date.Today().nextFriday(), date.NextFriday())

    def testLastDayOfCurrentMonth_InFebruary2004(self):
        expected = date.Date(2004, 2, 29)
        actual = date.LastDayOfCurrentMonth(localtime=lambda: (2004, 2, 1))
        self.assertEqual(expected, actual)

    def testLastDayOfCurrentMonth_InDecember(self):
        expected = date.Date(2003, 12, 31)
        actual = date.LastDayOfCurrentMonth(localtime=lambda: (2003, 12, 1))
        self.assertEqual(expected, actual)

    def testLastDayOfCurrentYear(self):
        today = date.Today()
        expected = date.Date(today.year, 12, 31) 
        self.assertEqual(expected, date.LastDayOfCurrentYear()) 

