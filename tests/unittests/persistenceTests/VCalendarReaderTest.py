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
from taskcoachlib import persistence
from taskcoachlib.domain import date 


class VCalendarParserTest(test.TestCase):
    def setUp(self):
        self.parser = persistence.icalendar.ical.VCalendarParser()
        
    def testEmptyVCalender(self):
        self.parser.parse(['BEGIN:VCALENDAR', 'END:VCALENDAR'])
        self.failIf(self.parser.tasks)
           
    def testEmptyVTodo(self):
        self.parser.parse(['BEGIN:VTODO', 'END:VTODO'])
        self.assertEqual(dict(status=0, startDateTime=date.DateTime()), 
                         self.parser.tasks[0])
        
    def testSubject(self):
        self.parser.parse(['BEGIN:VTODO', 'SUBJECT:Test', 'END:VTODO'])
        self.assertEqual(dict(status=0, subject='Test', 
                              startDateTime=date.DateTime()), 
                         self.parser.tasks[0])
        
    def testDueDate(self):
        self.parser.parse(['BEGIN:VTODO', 'DUE:20100101T120000', 'END:VTODO'])
        self.assertEqual(dict(status=0, 
                              dueDateTime=date.DateTime(2010,1,1,12,0,0), 
                              startDateTime=date.DateTime()), 
                         self.parser.tasks[0])
