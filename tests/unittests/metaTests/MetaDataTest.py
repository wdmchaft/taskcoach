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
from taskcoachlib import meta


class VersionNumberTest(test.TestCase):
    def testVersionHasMajorMinorAndPatchLevel(self):
        self.assertEqual(3, len(meta.data.version.split('.')))
        
    def testVersionComponentsAreIntegers(self):
        for component in meta.data.version.split('.'):
            self.assertEqual(component, str(int(component)))
            
    def testTskVersionIsInteger(self):
        self.assertEqual(type(0), type(meta.data.tskversion))
        
    def testMonthSpelling(self):
        self.failUnless(meta.data.release_month in meta.data.months)