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

import datetime

class TimeDelta(datetime.timedelta):
    millisecondsPerSecond = 1000
    millisecondsPerDay = 24 * 60 * 60 * millisecondsPerSecond
    millisecondsPerMicroSecond = 1/1000.
    
    def hoursMinutesSeconds(self):
        ''' Return a tuple (hours, minutes, seconds). Note that the caller
            is responsible for checking whether the TimeDelta instance is
            positive or negative. '''
        if self < TimeDelta():
            seconds = 3600*24 - self.seconds
            days = abs(self.days) - 1
        else:
            seconds = self.seconds
            days = self.days
        hours, seconds = seconds/3600, seconds%3600
        minutes, seconds = seconds/60, seconds%60
        hours += days*24
        return hours, minutes, seconds
    
    def hours(self):
        ''' Return hours as float. '''
        hours, minutes, seconds = self.hoursMinutesSeconds()
        return hours + (minutes / 60.) + (seconds / 3600.)
        
    def milliseconds(self):
        ''' Timedelta expressed in number of milliseconds. '''
        return int(round((self.days * self.millisecondsPerDay) + \
                         (self.seconds * self.millisecondsPerSecond) + \
                         (self.microseconds * self.millisecondsPerMicroSecond)))
        
    def __add__(self, other):
        ''' Make sure we return a TimeDelta instance and not a 
            datetime.timedelta instance '''
        timeDelta = super(TimeDelta, self).__add__(other)
        return self.__class__(timeDelta.days, 
                              timeDelta.seconds,
                              timeDelta.microseconds)
    
    def __sub__(self, other):
        timeDelta = super(TimeDelta, self).__sub__(other)
        return self.__class__(timeDelta.days, 
                              timeDelta.seconds, 
                              timeDelta.microseconds)

zeroHour = TimeDelta(hours=0)
oneHour = TimeDelta(hours=1)
twoHours = TimeDelta(hours=2)
threeHours = TimeDelta(hours=3)
oneDay = TimeDelta(days=1)
oneYear = TimeDelta(days=365)

def parseTimeDelta(string):
    try:
        hours, minutes, seconds = [int(x) for x in string.split(':')]
    except ValueError:
        hours, minutes, seconds = 0, 0, 0 
    return TimeDelta(hours=hours, minutes=minutes, seconds=seconds)

