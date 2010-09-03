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


class Numbered:
    __metaclass__ = patterns.NumberedInstances
    
    def __init__(self, instanceNumber=-1):
        self.instanceNumber = instanceNumber
    

class SubclassOfNumbered(Numbered):
    pass


class NumberedInstancesTestsMixin(object):
    ''' The tests below should work for a class with NumberedInstances as 
        metaclass as well as for a subclass of a class with NumberedInstances
        as metaclass. '''
        
    def testCounterIncreasesAfterEachInstantation(self):
        for count in range(3):
            self.assertEqual(count, 
                patterns.NumberedInstances.count.get(self.classUnderTest, 0))
            self.classUnderTest()
        
    def testInstanceNumberIsSet(self):
        for count in range(3):
            self.assertEqual(count, self.classUnderTest().instanceNumber)


class NumberedInstancesTest(NumberedInstancesTestsMixin, 
                            test.TestCase):
    classUnderTest = Numbered


class SubclassOfNumberedInstancesTest(NumberedInstancesTestsMixin, 
                                      test.TestCase):
    classUnderTest = SubclassOfNumbered

    def testSubclassInstancesHaveTheirOwnNumbers(self):
        SubclassOfNumbered()
        self.assertEqual(0, patterns.NumberedInstances.count.get(Numbered, 0))


