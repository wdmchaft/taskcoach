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
from taskcoachlib import widgets
from taskcoachlib.domain import date


class CommonTestsMixin(object):
    def testGetValue(self):
        oneHour = date.Time(hour=1)
        self.timeCtrl.SetValue(oneHour)
        self.assertEqual(oneHour, self.timeCtrl.GetValue())

    def testChoicesStartTime(self):
        self.assertEqual('08:00:00' if self.showSeconds else '08:00', 
                         self.timeCtrl._choices()[0])
        
    def testChoicesendTime(self):
        self.assertEqual('18:00:00' if self.showSeconds else '18:00', 
                         self.timeCtrl._choices()[-1])

        
class TimeCtrlTestCase(test.wxTestCase):
    def setUp(self):
        super(TimeCtrlTestCase, self).setUp()
        self.timeCtrl = widgets.datectrl.TimeCtrl(self.frame, 
                                                  showSeconds=self.showSeconds)
        

class TimeCtrlTest_Seconds(CommonTestsMixin, TimeCtrlTestCase):
    showSeconds = True
        
    def testGetValue_SecondPrecision(self):
        oneHourAndTenSeconds = date.Time(hour=1, second=10)
        self.timeCtrl.SetValue(oneHourAndTenSeconds)
        self.assertEqual(oneHourAndTenSeconds, self.timeCtrl.GetValue())


class TimeCtrlTest_NoSeconds(CommonTestsMixin, TimeCtrlTestCase):
    showSeconds = False

    def testGetValue_SecondPrecision(self):
        oneHour = date.Time(hour=1)
        oneHourAndTenSeconds = date.Time(hour=1, second=10)
        self.timeCtrl.SetValue(oneHourAndTenSeconds)
        self.assertEqual(oneHour, self.timeCtrl.GetValue())
