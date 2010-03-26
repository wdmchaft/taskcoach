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

import wx, time
from taskcoachlib import patterns
import dateandtime, date, timedelta


class Timer(wx.EvtHandler):
    """A timer that fires a callback. This is similar in
    functionnality to wx.PyTimer except for the fact that it works."""

    def __init__(self, callback=None):
        super(Timer, self).__init__()

        self.__callback = callback
        self.__timer = wx.Timer()
        self.__timer.Bind(wx.EVT_TIMER, self.__OnNotify)

    def Start(self, milliseconds, oneShot=True):
        self.__timer.Start(milliseconds, oneShot)

    def Stop(self):
        self.__timer.Stop()

    def __OnNotify(self, evt):
        self.Notify()

    def Notify(self):
        self.__callback()


class LargeIntervalTimer(Timer):
    ''' A timer that allows for unbounded large intervals, by dividing up the
        interval in pieces. '''
        
    maxMillisecondsPerInterval = 24 * 60 * 60 * 1000
    
    def Start(self, milliseconds): # pylint: disable-msg=W0221
        self.millisecondsToGo = milliseconds # pylint: disable-msg=W0201
        self.Notify()
        
    def Notify(self):
        if self.millisecondsToGo <= 0:
            super(LargeIntervalTimer, self).Notify()
        else:
            self._startInterval()

    def _startInterval(self):
        # To allow for arbitrary large intervals, we divide the interval 
        # into pieces of at most self.maxMilliseconds:
        nextInterval = min(self.millisecondsToGo, 
                           self.maxMillisecondsPerInterval)
        self.millisecondsToGo -= nextInterval
        super(LargeIntervalTimer, self).Start(nextInterval, oneShot=True)
        

class PeriodicTimer(Timer):
    ''' PeriodicTimer allows for scheduling a callback to be called on a
        periodic basis. '''

    periodsAllowed = ['year', 'month', 'day', 'hour', 'minute', 'second']
    
    def __init__(self, callback, period):
        assert period in self.periodsAllowed
        self._period = timedelta.TimeDelta(**{period+'s': 1}) # pylint: disable-msg=W0142
        self._resetToStartOfPeriodArguments = self._startOfPeriodArguments(period)
        self._onceTimer = OnceTimer(self._startFiringEveryPeriod)
        super(PeriodicTimer, self).__init__(callback)

    def Start(self, now=None): # pylint: disable-msg=W0221
        self._onceTimer.Start(self._startOfNextPeriod(now))
        
    def Stop(self): # pylint: disable-msg=W0221
        self._onceTimer.Stop()
        super(PeriodicTimer, self).Stop()
                
    def _startOfPeriodArguments(self, period):
        # Make sure that if the period is daily or more, we fire after the start
        # of the new day by adding 10 seconds to the start of the next period:
        startOfPeriod = dict(year=0, month=0, day=0, hour=0, minute=0,
                             second=10 if period in ['year', 'month', 'day'] else 0,
                             microsecond=0)
        keywordArguments = dict()
        periods = self.periodsAllowed + ['microsecond']
        smallerPeriods = periods[periods.index(period)+1:]
        for eachSmallerPeriod in smallerPeriods:
            keywordArguments[eachSmallerPeriod] = startOfPeriod[eachSmallerPeriod]
        return keywordArguments
    
    def _startFiringEveryPeriod(self, now=None): # pylint: disable-msg=W0613
        self.Notify()
        super(PeriodicTimer, self).Start(milliseconds=self._period.milliseconds(), 
                                         oneShot=False)

    def _startOfNextPeriod(self, now):
        now = now or dateandtime.DateTime.now()
        now = now.replace(**self._resetToStartOfPeriodArguments)
        return now + self._period

        
class OnceTimer(LargeIntervalTimer):
    ''' OnceTimer allows for scheduling a callback at a specific date and 
        time. '''
            
    def __init__(self, callback, dateTime=None, now=None):
        self.__callback = callback
        self.__requestedDateTime = None
        super(OnceTimer, self).__init__(self._notify)
        if dateTime:
            self.Start(dateTime, now)
        
    def Start(self, dateTime, now=None): # pylint: disable-msg=W0221
        self.__requestedDateTime = dateTime
        now = now or dateandtime.DateTime.now()
        timeDelta = dateTime - now
        super(OnceTimer, self).Start(timeDelta.milliseconds())

    def _notify(self, now=None):
        now = now or self.__requestedDateTime or dateandtime.DateTime.now()
        self.__callback(now)



class ScheduledTimer(OnceTimer):
    def __init__(self, callback):
        self._schedule = []
        super(ScheduledTimer, self).__init__(callback)
        
    def schedule(self, dateTime, now=None):
        earliestDateTime = self._earliestDateTimeScheduled()  
        self._schedule.append(dateTime)
        if dateTime < earliestDateTime:
            self.restartTimer(now)
    
    def scheduled(self):
        return self._schedule
    
    def _notify(self, now=None):
        super(ScheduledTimer, self)._notify(now)
        self._schedule.remove(self._earliestDateTimeScheduled())
        self.restartTimer(now)
                
    def restartTimer(self, now=None):
        self.Stop()
        if self._schedule:
            self.Start(self._earliestDateTimeScheduled(), now)

    def _earliestDateTimeScheduled(self):
        if self._schedule:
            return min(self._schedule)
        else:
            return dateandtime.DateTime.max


class Clock(patterns.Observer):
    __metaclass__ = patterns.Singleton
    
    timeFormat = '%Y%m%d-%H%M%S'
    
    def __init__(self, *args, **kwargs):
        super(Clock, self).__init__(*args, **kwargs)
        self._lastMidnightNotified = date.Today()
        self._createTimers()
        self._watchForClockObservers()
        
    def _createTimers(self):
        # pylint: disable-msg=W0201
        self._secondTimer = PeriodicTimer(self.notifySecondObservers, 'second')
        self._midnightTimer = PeriodicTimer(self.notifyMidnightObservers, 'day')
        self._midnightTimer.Start()
        self._scheduledTimer = ScheduledTimer(self.notifySpecificTimeObservers)
                
    def _watchForClockObservers(self):
        self.registerObserver(self.onFirstObserverRegisteredForSecond, 
            'publisher.firstObserverRegisteredFor.clock.second')
        self.registerObserver(self.onLastObserverRemovedForSecond, 
            'publisher.lastObserverRemovedFor.clock.second')
        self.registerObserver(self.onFirstObserverRegisteredFor,
            'publisher.firstObserverRegisteredFor')
                
    def onFirstObserverRegisteredForSecond(self, event): # pylint: disable-msg=W0613
        self._secondTimer.Start()
        
    def onLastObserverRemovedForSecond(self, event): # pylint: disable-msg=W0613
        self._secondTimer.Stop()
    
    def onFirstObserverRegisteredFor(self, event):
        if event.value().startswith('clock.time.'):
            dateTimeString = event.value().split('.')[-1]
            dateTimeTuple = time.strptime(dateTimeString, self.timeFormat)[:6]
            dateTime = dateandtime.DateTime(*dateTimeTuple) # pylint: disable-msg=W0142
            self._scheduledTimer.schedule(dateTime)
            
    def notifySecondObservers(self, now=None):
        now = now or dateandtime.DateTime.now()
        patterns.Event('clock.second', self, now).send()

    def notifySpecificTimeObservers(self, now=None):
        now = now or dateandtime.DateTime.now()
        patterns.Event(Clock.eventType(now), self, now).send()

    def notifyMidnightObservers(self, now=None):
        now = now or dateandtime.DateTime.now()
        patterns.Event('clock.midnight', self, now).send()        

    def reset(self):
        self._lastMidnightNotified = date.Today()
        self._secondTimer.Stop()
        self._scheduledTimer.Stop()
        self._midnightTimer.Stop()
    
    @classmethod    
    def eventType(class_, dateTime):
        return 'clock.time.%s'%dateTime.strftime(class_.timeFormat)


_clock = Clock() # make sure the clock is instantiated at least once


class ClockObserver(patterns.Observer):    
    def startClock(self):
        self.registerObserver(self.onEverySecond, eventType='clock.second')
        
    def stopClock(self):
        self.removeObserver(self.onEverySecond, eventType='clock.second')

    def isClockStarted(self):
        return self.onEverySecond in \
            patterns.Publisher().observers(eventType='clock.second')
        
    def onEverySecond(self, *args, **kwargs):
        raise NotImplementedError # pragma: no cover
