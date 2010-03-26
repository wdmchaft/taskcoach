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

''' Utilities for recurring dates. ''' # pylint: disable-msg=W0105

import calendar
import timedelta, date


class Recurrence(object):
    def __init__(self, unit='', amount=1, sameWeekday=False, max=0, count=0): # pylint: disable-msg=W0622
        assert unit in ['', 'daily', 'weekly', 'monthly', 'yearly']
        assert amount >= 1
        self.unit = unit
        self.amount = amount
        self.sameWeekday = sameWeekday
        self.max = max # Maximum number of recurrences we give out, 0 == infinite
        self.count = count # Actual number of recurrences given out so far
                
    def __call__(self, *dates, **kwargs):
        result = [self._nextDate(aDate) for aDate in dates]
        if kwargs.get('next', True):
            # By default we expect our clients to call us once, but we allow
            # the client to tell us to expect more calls
            self.count += 1
            if self.count >= self.max and self.max != 0:
                self.unit = '' # We're done with recurring
                return
        if len(result) > 1:
            return tuple(result)
        elif len(result) == 1:
            return result[0]
        else:
            return
        
    def _nextDate(self, aDate, amount=0):
        if date.Date() == aDate or not self.unit:
            return aDate 
        amount = amount or self.amount
        if amount > 1:
            aDate = self._nextDate(aDate, amount-1)
        if self.unit == 'yearly':
            return self._addYear(aDate)
        elif self.unit == 'monthly':
            return self._addMonth(aDate)
        else:
            return self._addDays(aDate)

    def _addDays(self, aDate):
        nrOfDays = dict(daily=1, weekly=7)[self.unit]
        return aDate + timedelta.TimeDelta(days=nrOfDays)

    def _addMonth(self, aDate):
        year, month, day = aDate.year, aDate.month, aDate.day
        if month == 12: # If December, move to January next year
            year += 1
            month = 1
        else:
            month += 1
        if self.sameWeekday:
            weekday = aDate.weekday()
            weekNr = min(3, (day - 1) / 7) # In what week of the month falls aDate, allowable range 0-3 
            day = weekNr * 7 + 1 # The earliest possible day that is on the same weekday as aDate
            result = date.Date(year, month, day)
            while result.weekday() != weekday:
                day += 1
                result = date.Date(year, month, day)
            return result
        else:
            while True: # Find a valid date in the next month
                try:
                    return date.Date(year, month, day)
                except ValueError:
                    day -= 1

    def _addYear(self, aDate):
        if (calendar.isleap(aDate.year) and aDate.month <= 2 and aDate.day <=28) or \
           (calendar.isleap(aDate.year + 1) and aDate.month >=3): 
            days = 366
        else:
            days = 365
        newDate = aDate + timedelta.TimeDelta(days=days)
        if self.sameWeekday:
            # Find the nearest date in newDate's year that is on the right 
            # weekday:
            weekday, year = aDate.weekday(), newDate.year
            oneDay = timedelta.TimeDelta(days=1)
            newEarlierDate = newLaterDate = newDate
            while newEarlierDate.weekday() != weekday:
                newEarlierDate = newEarlierDate - oneDay
            while newLaterDate.weekday() != weekday:
                newLaterDate = newLaterDate + oneDay
            if newEarlierDate.year != year:
                newDate = newLaterDate
            else:
                newDate = newEarlierDate
        return newDate

    def copy(self):
        return self.__class__(self.unit, self.amount, self.sameWeekday, 
                              self.max)
    
    def __eq__(self, other):
        try:
            return self.unit == other.unit and self.amount == other.amount and \
                   self.sameWeekday == other.sameWeekday and \
                   self.max == other.max
        except AttributeError:
            return False
 
    def __nonzero__(self):
        return bool(self.unit)
