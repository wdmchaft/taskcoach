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

import datetime, timedelta, re

class DateTime(datetime.datetime):
    
    secondsPerMinute = 60
    minutesPerHour = 60
    hoursPerDay = 24
    secondsPerHour = minutesPerHour * secondsPerMinute
    secondsPerDay = hoursPerDay * secondsPerHour
    
    def weeknumber(self):
        return self.isocalendar()[1]

    def weekday(self):
        return self.isoweekday()
    
    def toordinal(self):
        ''' Return the ordinal number of the day, plus a fraction between 0 and
            1 for parts of the day. '''
        ordinal = super(DateTime, self).toordinal()
        seconds = self.hour * self.secondsPerHour + \
                  self.minute * self.secondsPerMinute + \
                  self.second
        return ordinal + (seconds / float(self.secondsPerDay))
        
    def startOfDay(self):
        return self.replace(hour=0, minute=0, second=0, microsecond=0)
        
    def endOfDay(self):
        return self.replace(hour=23, minute=59, second=59, microsecond=999999)

    def startOfWeek(self):
        days = self.weekday()
        monday = self - timedelta.TimeDelta(days=days-1)
        return DateTime(monday.year, monday.month, monday.day)
        
    def endOfWeek(self):
        days = self.weekday()
        sunday = self + timedelta.TimeDelta(days=7-days)
        return DateTime(sunday.year, sunday.month, sunday.day).endOfDay()
        
    def startOfMonth(self):
        return DateTime(self.year, self.month, 1)
        
    def endOfMonth(self):
        for lastday in [31,30,29,28]:
            try:
                return DateTime(self.year, self.month, lastday).endOfDay()
            except ValueError:
                pass
                
    def __sub__(self, other):
        ''' Make sure substraction returns a TimeDelta and not a datetime.timedelta '''
        result = super(DateTime, self).__sub__(other)
        if isinstance(result, datetime.timedelta):
            result = timedelta.TimeDelta(result.days, result.seconds, result.microseconds)
        return result

    def __add__(self, other):
        result = super(DateTime, self).__add__(other)
        return self.__class__(result.year, result.month, result.day, 
            result.hour, result.minute, result.second, result.microsecond)


DateTime.max = DateTime(datetime.datetime.max.year, 12, 31).endOfDay()
DateTime.min = DateTime(datetime.datetime.min.year, 1, 1).startOfDay()


def parseDateTime(string):
    if string in ('', 'None'):
        return None
    else:
        args = [int(arg) for arg in re.split('[-:. ]', string)]
        return DateTime(*args) # pylint: disable-msg=W0142
        

