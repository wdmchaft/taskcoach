'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>

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


class BaseTextCtrlTest(test.wxTestCase):
    def testRemoveAnyControlCharactersEnteredByUser(self):
        textctrl = widgets.textctrl.BaseTextCtrl(self.frame, 
                                                 u'T\x02\x01est\x09')
        self.assertEqual(u'Test\t', textctrl.GetValue())    
    
    
class MultiLineTextCtrlTest(test.wxTestCase):
    def testOpenWebbrowserOnURLClick(self):
        textctrl = widgets.MultiLineTextCtrl(self.frame)
        textctrl.AppendText('test http://test.com/ test')
        # FIXME: simulate a mouseclick on the url
        
    def testSetInsertionPointAtStart(self):
        textctrl = widgets.MultiLineTextCtrl(self.frame, text='Hiya')
        self.assertEqual(0, textctrl.GetInsertionPoint())
        

class SingleLineTextCtrlWithEnterButtonTest(test.wxTestCase):
    def setUp(self):
        super(SingleLineTextCtrlWithEnterButtonTest, self).setUp()
        self.textCtrl = widgets.SingleLineTextCtrlWithEnterButton(self.frame, 
            label='Text', onEnter=self.onEnter)
        self.enteredText = ''
            
    def onEnter(self, text):
        self.enteredText = text
        
    def testDontAllowEnterWhenTheTextCtrlIsEmpty(self):
        self.failIf(self.textCtrl.isButtonEnabled())
        
    def testAllowEnterWhenTheTextCtrlIsNotEmpty(self):
        self.textCtrl.SetValue('Some text')
        self.failUnless(self.textCtrl.isButtonEnabled())
        
    def testCallback(self): 
        self.textCtrl.SetValue('Some text')
        self.textCtrl.onEnter()
        self.assertEqual('Some text', self.enteredText)
    
    def testAfterCallbackTheTextCtrlIsCleared(self):
        self.textCtrl.SetValue('Some text')
        self.textCtrl.onEnter()
        self.failIf(self.textCtrl.isButtonEnabled())
        
