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
from taskcoachlib import patterns
from taskcoachlib.domain import date


class MockTimer(object):
    def __init__(self):
        self.started = self.stopped = False
        
    def Start(self):
        self.started = True

    def Stop(self):
        self.stopped = True

        
class ClockTest(test.wxTestCase):
    def setUp(self):
        super(ClockTest, self).setUp()
        self.events = []
        self.clock = date.Clock()
         
    def tearDown(self):
        super(ClockTest, self).tearDown()
        date.Clock.deleteInstance() # pylint: disable-msg=E1101
        
    def onEvent(self, event):
        self.events.append(event)
                
    def testNotification(self):
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType='clock.second')
        self.clock.notifySecondObservers()
        self.assertEqual(1, len(self.events))
        
    def testSingleton(self):
        clock2 = date.Clock()
        self.failUnless(self.clock is clock2)
        
    def testRegisterForSpecificTime(self):
        realSoonNow = date.DateTime.now() + date.TimeDelta(seconds=2)
        patterns.Publisher().registerObserver(self.onEvent, 
            eventType=date.Clock.eventType(realSoonNow))
        self.clock._scheduledTimer._notify(now=realSoonNow) # pylint: disable-msg=W0212
        self.assertEqual(1, len(self.events))

    def testRegisterForDateChange_Midnight(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='clock.midnight')
        self.clock.notifyMidnightObservers(now=date.DateTime(2000,1,1,0,0,0))
        self.assertEqual(1, len(self.events))
        
    def testRegisterForDateChange_BeforeMidnight(self):
        self.clock.notifyMidnightObservers(now=date.DateTime(2000,1,1,23,59,58))
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='clock.midnight')
        self.clock.notifyMidnightObservers(now=date.DateTime(2000,1,2,0,0,0))
        self.assertEqual(1, len(self.events))

    def testRegisterForDateChange_ComputerHibernatedAtMidnight(self):
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='clock.midnight')
        self.clock.notifyMidnightObservers(now=date.DateTime(2000,1,1,1,10,15))
        self.assertEqual(1, len(self.events))

    def testStartClockOnFirstObserverRegisteredForSecond(self):
        self.clock._secondTimer = MockTimer()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='clock.second')
        self.failUnless(self.clock._secondTimer.started) # pylint: disable-msg=W0212

    def testStopClockOnLastObserverRemovedForSecond(self):
        self.clock._secondTimer = MockTimer()
        patterns.Publisher().registerObserver(self.onEvent,
            eventType='clock.second')
        patterns.Publisher().removeObserver(self.onEvent,
            eventType='clock.second')
        self.failUnless(self.clock._secondTimer.stopped) # pylint: disable-msg=W0212


class TimerTestCase(test.TestCase):
    expectedDateTime = 'Subclass responsibility'
    frequency = 'minute'
    
    def setUp(self):
        self.timerFired = False
        self.timer = date.clock.PeriodicTimer(self.onTimer, self.frequency)
        
    def onTimer(self, event=None): # pylint: disable-msg=W0613
        self.timerFired = True # pragma: no cover
        
    def assertStartOfNextPeriod(self, *args):
        dateTime = date.DateTime(*args) if len(args) > 1 else args[0] 
        self.assertEqual(self.expectedDateTime, 
                         self.timer._startOfNextPeriod(dateTime)) # pylint: disable-msg=W0212

        
class PeriodicTimerTest_EverySecond(TimerTestCase):
    frequency = 'second'
    expectedDateTime = date.DateTime(2000,1,1,10,0,0)
    
    def testNextWholeSecond(self):
        self.assertStartOfNextPeriod(2000,1,1,9,59,59,100)
        
    def testNextWholeSecond_NowIsOnTheSecond(self):
        self.assertStartOfNextPeriod(self.expectedDateTime - \
                                     date.TimeDelta(seconds=1))
        
    def testStartOnNextWholeSecond_NowIsAlmostOnTheSecond(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 9, 59, 59, 999999)

    def testStartOnNextWholeSecond_NowIsJustOverTheSecond(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 9, 59, 59, 1)
        
    def testStartOnNextWholeSecond_NowIsHalfwayTheSecond(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 9, 59, 59, 500000)


class PeriodicTimerTest_EveryMidnight(TimerTestCase):
    frequency = 'day'
    # The clock is 10 seconds late to make sure it fires on the right day:
    expectedDateTime = date.DateTime(2000,1,2,0,0,10)
    
    def testNextMidnight(self):
        self.assertStartOfNextPeriod(2000,1,1,10,10,10,100)
        
    def testNextMidnight_NowIsMidnigth(self):
        self.assertStartOfNextPeriod(self.expectedDateTime - \
                                     date.TimeDelta(days=1))
        
    def testNextMidnight_NowIsAlmostMidnight(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 23, 59, 59, 999999)

    def testNextMidnigth_NowIsJustOverMidnight(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 0, 0, 0, 1)
        
    def testNextMidnight_NowIsNoon(self):
        self.assertStartOfNextPeriod(2000, 1, 1, 12, 0, 0, 0)
        
    def testStartOnStartOfPeriod(self):
        self.timer._onceTimer._notify() # pylint: disable-msg=W0212
        

class FireOnceTest(TimerTestCase):                
    def testFireOnce(self):
        now = date.DateTime.now()
        date.clock.OnceTimer(self.onTimer, now)
        self.failUnless(self.timerFired)
        
    def testFireOnceInTheFarFuture(self):
        target = date.DateTime.max
        now = date.DateTime.min
        timer = date.clock.OnceTimer(self.onTimer, target, now=now)
        self.failUnless(timer.millisecondsToGo > timer.maxMillisecondsPerInterval)
        timer.Stop()
        
        
class ScheduledTimerTest(test.TestCase):
    def setUp(self):
        self.timer = date.clock.ScheduledTimer(self.onAlarm)
        self.alarmTime = date.DateTime(2008,1,1,10,0,0)
        self.alarmFired = 0
        
    def onAlarm(self, *args): # pylint: disable-msg=W0613
        self.alarmFired += 1
        
    def scheduleFutureAlarm(self, alarmTime=None):
        alarmTime = alarmTime or self.alarmTime
        self.timer.schedule(alarmTime, now=self.alarmTime-date.oneDay)

    def schedulePastAlarm(self):
        self.timer.schedule(self.alarmTime, now=self.alarmTime+date.oneDay)
        
    def testNoAlarmsScheduledByDefault(self):
        self.assertEqual([], self.timer.scheduled())
        
    def testScheduleFutureAlarm(self):
        self.scheduleFutureAlarm()
        self.assertEqual([self.alarmTime], self.timer.scheduled())

    # pylint: disable-msg=W0212
    
    def testInvocationOfFutureAlarm(self):
        self.scheduleFutureAlarm()
        self.timer._notify() 
        self.assertEqual(1, self.alarmFired)

    def testInvokedAlarmIsRemovedFromScheduledAlarms(self):
        self.scheduleFutureAlarm()
        self.timer._notify()
        self.assertEqual([], self.timer.scheduled())
    
    def testScheduleTwoFutureAlarmsForTheSameTime(self):
        self.scheduleFutureAlarm()
        self.scheduleFutureAlarm()
        self.assertEqual([self.alarmTime, self.alarmTime], 
                         self.timer.scheduled())

    def testInvocationOfTwoFutureAlarmsForTheSameTime(self):
        self.scheduleFutureAlarm()
        self.scheduleFutureAlarm()
        self.timer._notify()
        self.assertEqual(2, self.alarmFired)

    def testScheduleTwoFutureAlarmsForDifferentTimes(self):
        self.scheduleFutureAlarm()
        secondAlarmTime = self.alarmTime+date.TimeDelta(seconds=10)
        self.scheduleFutureAlarm(secondAlarmTime)
        self.assertEqual([self.alarmTime, secondAlarmTime], 
                         self.timer.scheduled())

    def testAfterSchedulingTwoFutureAlarmsForDifferentTimesTheFirstOneIsScheduled(self):
        self.scheduleFutureAlarm()
        secondAlarmTime = self.alarmTime+date.TimeDelta(seconds=10)
        self.scheduleFutureAlarm(secondAlarmTime)
        self.assertEqual(0, self.timer.millisecondsToGo)

    def testInvocationOfTwoFutureAlarmsForDifferentTimes(self):
        self.scheduleFutureAlarm()
        secondAlarmTime = self.alarmTime+date.TimeDelta(seconds=10)
        self.scheduleFutureAlarm(secondAlarmTime)
        self.timer._notify(now=self.alarmTime-date.oneDay)
        self.assertEqual(1, self.alarmFired)
        self.timer._notify(now=self.alarmTime-date.oneDay)
        self.assertEqual(2, self.alarmFired)

    def testAfterSchedulingTwoFutureAlarmsForDifferentTimesAndFiringTheFirstOneTheSecondOneIsScheduled(self):
        self.scheduleFutureAlarm()
        secondAlarmTime = self.alarmTime+date.TimeDelta(seconds=10)
        self.scheduleFutureAlarm(secondAlarmTime)
        self.timer._notify(now=self.alarmTime-date.oneDay)
        self.assertEqual(10000, self.timer.millisecondsToGo)

    def testCallbackScheduledInThePastIsCalledImmediately(self):
        self.schedulePastAlarm()
        self.assertEqual(1, self.alarmFired)

    def testCallbackScheduledNowIsCalledImmediately(self):
        self.timer.schedule(self.alarmTime, now=self.alarmTime)
        self.assertEqual(1, self.alarmFired)
        
    def testCallbackScheduledInThePastIsNotActuallyScheduled(self):
        self.schedulePastAlarm()
        self.assertEqual([], self.timer.scheduled())
        
    def testScheduledFutureAlarmIsCalled(self):
        self.scheduleFutureAlarm()
        self.timer.Notify()
        self.failUnless(self.alarmFired)
