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
from taskcoachlib.gui.dialog import entry 
from taskcoachlib.domain import date


class DateEntryTest(test.wxTestCase):
    def setUp(self):
        super(DateEntryTest, self).setUp()
        self.dateEntry = entry.DateEntry(self.frame)
        self.date = date.Date(2004, 1, 1)

    def testCreate(self):
        self.assertEqual(date.Date(), self.dateEntry.get())

    def testSet(self):
        self.dateEntry.set(date.Today())
        self.assertEqual(date.Today(), self.dateEntry.get())

    def testReset(self):
        self.dateEntry.set()
        self.assertEqual(date.Date(), self.dateEntry.get())

    def testValidDate(self):
        self.dateEntry.set(self.date)
        self.assertEqual(self.date, self.dateEntry.get())

    def testValidDateWithDefaultDate(self):
        self.dateEntry.set(self.date)
        self.assertEqual(self.date, self.dateEntry.get(date.Today()))

    def testInvalidDate(self):
        self.dateEntry.set('bla')
        self.assertEqual(date.Date(), self.dateEntry.get())

    def testInvalidDateWithDefaultDate(self):
        self.dateEntry.set('bla')
        self.assertEqual(date.Tomorrow(), self.dateEntry.get(date.Tomorrow()))


class DateEntryConstructorTest(test.wxTestCase):
    def testCreateWithDate(self):
        dateEntry = entry.DateEntry(self.frame, date.Tomorrow())
        self.assertEqual(date.Tomorrow(), dateEntry.get())

