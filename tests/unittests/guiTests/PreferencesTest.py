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

import test
from taskcoachlib import gui, config


class PreferencesTest(test.wxTestCase):
    def setUp(self):
        super(PreferencesTest, self).setUp()
        self.settings = config.Settings(load=False)
        self.preferences = gui.Preferences(parent=self.frame, title='Test',
            settings=self.settings, raiseDialog=False)
        self.originalColor = self.settings.get('color', 'activetasks')
        self.newColor = (1, 2, 29)
        
    # pylint: disable-msg=W0212
    
    def testCancel(self):
        self.preferences[4]._colorSettings[0][2].SetColour(self.newColor)
        self.preferences.cancel()
        self.assertEqual(self.originalColor, self.settings.get('color', 'activetasks'))
        
    def testOk(self):
        self.preferences[4]._colorSettings[0][2].SetColour(self.newColor)
        self.preferences.ok()
        self.assertEqual(self.newColor, 
            eval(self.settings.get('color', 'activetasks'))[:3])
        
