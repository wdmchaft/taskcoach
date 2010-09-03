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

import wx
import test
from taskcoachlib import widgets


class DatePickerCtrlThatFixesAllowNoneStyleTest(test.wxTestCase):
    def setUp(self):
        super(DatePickerCtrlThatFixesAllowNoneStyleTest, self).setUp()
        # pylint: disable-msg=W0212
        self.datePicker = \
            widgets.datectrl._DatePickerCtrlThatFixesAllowNoneStyle(self.frame)

    def testCtrlIsDisabledInitially(self):
        self.failIf(self.datePicker.IsEnabled())
        
    def testSetValidValueEnablesCtrl(self):
        today = wx.DateTime()
        today.SetToCurrent()
        self.datePicker.SetValue(today)
        self.failUnless(self.datePicker.IsEnabled())

    def testSetInvalidValueDisablesCtrl(self):
        invalid = wx.DateTime()
        self.datePicker.SetValue(invalid)
        self.failIf(self.datePicker.IsEnabled())


class DatePickerCtrlWithStyleDP_ALLOWNONETest(test.wxTestCase):
    def setUp(self):
        super(DatePickerCtrlWithStyleDP_ALLOWNONETest, self).setUp()
        self.datePicker = widgets.DatePickerCtrl(self.frame, 
            style=wx.DP_ALLOWNONE)

    def testInitialValueIsNotValid(self):
        value = self.datePicker.GetValue()
        self.failIf(value.IsValid())

    def testSetValue(self):
        someDate = wx.DateTime()
        someDate.SetToCurrent()
        someDate.ResetTime()
        self.datePicker.SetValue(someDate)
        value = self.datePicker.GetValue()
        self.failUnless(value.IsSameDate(someDate))

    def testSetValueInvalid(self):
        invalid = wx.DateTime()
        self.datePicker.SetValue(invalid)
        value = self.datePicker.GetValue()
        self.failIf(value.IsValid())


class DatePickerCtrlFactoryTest(test.wxTestCase):
    def isWxDatePickerCtrl(self, instance):
        return isinstance(instance, wx.DatePickerCtrl)

    def testFactoryFunctionNoStyle(self):
        dpc = widgets.DatePickerCtrl(self.frame)
        self.failUnless(self.isWxDatePickerCtrl(dpc))

    def testFactoryFunctionStyleIncludesDP_ALLOWNONE(self):
        dpc = widgets.DatePickerCtrl(self.frame, style=wx.DP_ALLOWNONE)
        # style=wx.DP_ALLOWNONE is broken on some platforms/wxPython versions:
        if widgets.datectrl.styleDP_ALLOWNONEIsBroken(): # pragma: no cover
            self.failIf(self.isWxDatePickerCtrl(dpc))
        else: # pragma: no cover
            self.failUnless(self.isWxDatePickerCtrl(dpc))
            
            
class StyleTest(test.TestCase):            
    def testGettingStyleFromOrredSetOfStyles(self):
        for style, allowNoneIncluded in [(wx.DP_DEFAULT, False), 
                (wx.DP_DEFAULT | wx.DP_SHOWCENTURY, False),
                (wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE, True),
                (wx.DP_ALLOWNONE, True),
                (wx.DP_DEFAULT | wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE, True)]:
            self.assertEqual(allowNoneIncluded, 
                self.isOptionIncluded(style, wx.DP_ALLOWNONE))

    def isOptionIncluded(self, options, option):
        return (options & option) == option


