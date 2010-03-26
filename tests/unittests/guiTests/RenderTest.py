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

import test
from taskcoachlib import config
from taskcoachlib.gui import render
from taskcoachlib.i18n import _
from taskcoachlib.domain import task, date, effort



class RenderDaysLeftTest(test.TestCase):
    def testOneDayLeft(self):
        self.assertEqual('1', render.daysLeft(date.TimeDelta(days=1), False))
        
    def testDueToday(self):
        self.assertEqual('0', render.daysLeft(date.TimeDelta(days=0), False))

    def testOneDayLate(self):
        self.assertEqual('-1', render.daysLeft(date.TimeDelta(days=-1), False))

    def testInfiniteTimeLeft(self):
        self.assertEqual('Infinite', render.daysLeft(date.TimeDelta.max, False))

    def testCompletedTask(self):
        self.assertEqual('', render.daysLeft(date.TimeDelta.max, True))
        

class RenderTimeSpentTest(test.TestCase):
    def testZeroTime(self):
        self.assertEqual('', render.timeSpent(date.TimeDelta()))
        
    def testOneSecond(self):
        self.assertEqual('0:00:01', 
            render.timeSpent(date.TimeDelta(seconds=1)))
            
    def testTenHours(self):
        self.assertEqual('10:00:00', 
            render.timeSpent(date.TimeDelta(hours=10)))
            
    def testNegativeHours(self):
        self.assertEqual('-1:00:00', render.timeSpent(date.TimeDelta(hours=-1)))
        
    def testNegativeSeconds(self):
        self.assertEqual('-0:00:01', render.timeSpent(date.TimeDelta(seconds=-1)))


class RenderWeekNumberTest(test.TestCase):
    def testWeek1(self):
        self.assertEqual('2005-1', render.weekNumber(date.DateTime(2005,1,3)))
        
    def testWeek53(self):
        self.assertEqual('2004-53', render.weekNumber(date.DateTime(2004,12,31)))
        
        
class RenderRecurrenceTest(test.TestCase):
    def testNoRecurrence(self):
        self.assertEqual('', render.recurrence(date.Recurrence()))
        
    def testDailyRecurrence(self):
        self.assertEqual(_('Daily'), render.recurrence(date.Recurrence('daily')))
        
    def testWeeklyRecurrence(self):
        self.assertEqual(_('Weekly'), render.recurrence(date.Recurrence('weekly')))
        
    def testMonthlyRecurrence(self):
        self.assertEqual(_('Monthly'), render.recurrence(date.Recurrence('monthly')))

    def testYearlyRecurrence(self):
        self.assertEqual(_('Yearly'), render.recurrence(date.Recurrence('yearly')))

    def testEveryOtherDay(self):
        self.assertEqual(_('Every other day'), 
                         render.recurrence(date.Recurrence('daily', amount=2)))
        
    def testEveryOtherWeek(self):
        self.assertEqual(_('Every other week'), 
                         render.recurrence(date.Recurrence('weekly', amount=2)))
        
    def testEveryOtherMonth(self):
        self.assertEqual(_('Every other month'), 
                         render.recurrence(date.Recurrence('monthly', amount=2)))
        
    def testEveryOtherYear(self):
        self.assertEqual(_('Every other year'), 
                         render.recurrence(date.Recurrence('yearly', amount=2)))
        
    def testThreeDaily(self):
        self.assertEqual('Every 3 days', 
                         render.recurrence(date.Recurrence('daily', amount=3))) 
        
    def testThreeWeekly(self):
        self.assertEqual('Every 3 weeks', 
                         render.recurrence(date.Recurrence('weekly', amount=3))) 
        
    def testThreeMonthly(self):
        self.assertEqual('Every 3 months', 
                         render.recurrence(date.Recurrence('monthly', 3))) 
        
    def testThreeYearly(self):
        self.assertEqual('Every 3 years', 
                         render.recurrence(date.Recurrence('yearly', 3)))
                
        
class RenderException(test.TestCase):
    def testRenderException(self):
        instance = Exception()
        self.assertEqual(unicode(instance), 
                         render.exception(Exception, instance))

    def testRenderUnicodeDecodeError(self):
        try:
            'abc'.encode('utf-16').decode('utf-8')
        except UnicodeDecodeError, instance:
            self.assertEqual(unicode(instance), 
                             render.exception(UnicodeDecodeError, instance))
            
    def testExceptionThatCannotBePrinted(self):
        """win32all exceptions may contain localized error
        messages. But Exception.__str__ does not handle non-ASCII
        characters in the args instance variable; calling
        unicode(instance) is just like calling str(instance) and
        raises an UnicodeEncodeError."""

        e = Exception(u'é')
        try:
            render.exception(Exception, e)
        except UnicodeEncodeError: # pragma: no cover
            self.fail() 


class RenderMultilineText(test.TestCase):
    def testRenderOneLine(self):
        self.assertEqual('line1', render.multilineText('line1'))
        
    def testRenderTwoLines(self):
        self.assertEqual('line1\nline2', render.multilineText('line1\nline2'))
        
    def testRenderThreeLines(self):
        self.assertEqual('line1\nline2\nline3', 
                         render.multilineText('line1\nline2\nline3'))

    def testRenderFourLines(self):
        self.assertEqual('line1\nline2\n...', 
                         render.multilineText('line1\nline2\nline3\nline4'))
        