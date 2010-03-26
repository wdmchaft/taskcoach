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
from taskcoachlib.gui import splash, icons


class SplashTest(test.wxTestCase):
    def setUp(self):
        super(SplashTest, self).setUp()
        self.splashScreen = splash.SplashScreen()
        self.splashScreen.Hide()

    def tearDown(self):
        self.splashScreen.Destroy()
        super(SplashTest, self).tearDown()

    def bitmapData(self, bitmap):
        return bitmap.ConvertToImage().GetData()

    def assertEqualBitmaps(self, expectedBitmap, actualBitmap):
        self.assertEqual(self.bitmapData(expectedBitmap), 
                         self.bitmapData(actualBitmap))

    def testTimeout(self):
        self.assertEqual(4000, self.splashScreen.GetTimeout())

    def testBitmap(self):
        expectedBitmap = icons.catalog['splash'].getBitmap()
        actualBitmap = self.splashScreen.GetSplashWindow().GetBitmap()
        self.assertEqualBitmaps(expectedBitmap, actualBitmap)
