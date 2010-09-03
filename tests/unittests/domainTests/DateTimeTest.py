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

import test, datetime
from taskcoachlib.domain import date


class PyDateTimeTest(test.TestCase):
    def testReplaceCannotBeEasilyUsedToFindTheLastDayofTheMonth(self):
        testDate = datetime.date(2004, 4, 1) # April 1st, 2004
        try:
            lastDayOfApril = testDate.replace(day=31)
            self.fail('Surprise! datetime.date.replace works as we want!') # pragma: no cover
            self.assertEqual(datetime.date(2004, 4, 30), lastDayOfApril) # pragma: no cover
        except ValueError:
            pass


class DateTimeTest(test.TestCase):
    def testWeekNumber(self):
        self.assertEqual(53, date.DateTime(2005,1,1).weeknumber())
        self.assertEqual(1, date.DateTime(2005,1,3).weeknumber())   
        
    def testStartOfDay(self):
        startOfDay = date.DateTime(2005,1,1,0,0,0,0)
        noonish = date.DateTime(2005,1,1,12,30,15,400)
        self.assertEqual(startOfDay, noonish.startOfDay())
        
    def testEndOfDay(self):
        endOfDay = date.DateTime(2005,1,1,23,59,59,999999)
        noonish = date.DateTime(2005,1,1,12,30,15,400)
        self.assertEqual(endOfDay, noonish.endOfDay())
        
    def testStartOfWeek(self):
        startOfWeek = date.DateTime(2005,3,28,0,0,0,0)
        midweek = date.DateTime(2005,3,31,12,30,15,400)
        self.assertEqual(startOfWeek, midweek.startOfWeek())

    def testEndOfWeek(self):
        endOfWeek = date.DateTime(2005,4,3,23,59,59,999999)
        midweek = date.DateTime(2005,3,31,12,30,15,400)
        self.assertEqual(endOfWeek, midweek.endOfWeek())
        
    def testEndOfWorkWeek(self):
        endOfWorkWeek = date.DateTime(2010,5,7,23,59,59,999999)
        midweek = date.DateTime(2010,5,5,12,30,15,200000)
        self.assertEqual(endOfWorkWeek, midweek.endOfWorkWeek())

    def testEndOfWorkWeek_OnSaturday(self):
        endOfWorkWeek = date.DateTime(2010,5,7,23,59,59,999999)
        midweek = date.DateTime(2010,5,1,12,30,15,200000)
        self.assertEqual(endOfWorkWeek, midweek.endOfWorkWeek())
        
    def testStartOfMonth(self):
        startOfMonth = date.DateTime(2005,4,1)
        midMonth = date.DateTime(2005,4,15,12,45,1,999999)
        self.assertEqual(startOfMonth, midMonth.startOfMonth())
        
    def testEndOfMonth(self):
        endOfMonth = date.DateTime(2005,4,30).endOfDay()
        midMonth = date.DateTime(2005,4,15,12,45,1,999999)
        self.assertEqual(endOfMonth, midMonth.endOfMonth())

    def testEndOfYear_AtMidYear(self):
        endOfYear = date.DateTime(2010,12,31,23,59,59,999999)
        midYear = date.DateTime(2010,6,30,0,0,0)
        self.assertEqual(endOfYear, midYear.endOfYear())

    def testEndOfYear_AtEndOfYear(self):
        endOfYear = date.DateTime(2010,12,31,23,59,59,999999)
        self.assertEqual(endOfYear, endOfYear.endOfYear())
        
    def testOrdinalOfDateTimeAtMidnightEqualsOrdinalOfDate(self):
        self.assertEqual(date.Date(2000, 1, 1).toordinal(), 
                         date.DateTime(2000, 1, 1).toordinal())

    def testOrdinalOfDateTimeAtNoon(self):
        self.assertEqual(date.Date(2000, 1, 1).toordinal() + 0.5, 
                         date.DateTime(2000, 1, 1, 12, 0, 0).toordinal())


class TimeTest(test.TestCase):
    def testNow(self):
        date.Time.now()


class TimeDeltaTest(test.TestCase):
    def testHours(self):
        timedelta = date.TimeDelta(hours=2, minutes=15)
        self.assertEqual(2.25, timedelta.hours())
        
    def testMillisecondsInOneSecond(self):
        timedelta = date.TimeDelta(seconds=1)
        self.assertEqual(1000, timedelta.milliseconds())

    def testMillisecondsInOneHour(self):
        timedelta = date.TimeDelta(hours=1)
        self.assertEqual(60*60*1000, timedelta.milliseconds())

    def testMillisecondsInOneDay(self):
        timedelta = date.TimeDelta(days=1)
        self.assertEqual(24*60*60*1000, timedelta.milliseconds())

    def testMillisecondsInOneMicrosecond(self):
        timedelta = date.TimeDelta(microseconds=1)
        self.assertEqual(0, timedelta.milliseconds())

    def testMillisecondsIn500Microseconds(self):
        timedelta = date.TimeDelta(microseconds=500)
        self.assertEqual(1, timedelta.milliseconds())
