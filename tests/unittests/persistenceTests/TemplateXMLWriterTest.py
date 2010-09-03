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

import test, StringIO
from taskcoachlib import persistence
from taskcoachlib.domain import task, date


class TemplateXMLWriterTestCase(test.TestCase):
    def setUp(self):
        self.fd = StringIO.StringIO()
        self.fd.name = 'testfile.tsk'
        self.writer = persistence.TemplateXMLWriter(self.fd)
        self.task = task.Task()
        
    def __writeAndRead(self):
        self.writer.write(self.task)
        return self.fd.getvalue()
    
    def expectInXML(self, xmlFragment):
        xml = self.__writeAndRead()
        self.failUnless(xmlFragment in xml, '%s not in %s'%(xmlFragment, xml))
    
    def expectNotInXML(self, xmlFragment):
        xml = self.__writeAndRead()
        self.failIf(xmlFragment in xml, '%s in %s'%(xmlFragment, xml))
        
    # tests
    
    def testDefaultTask(self):
        self.expectInXML('<tasks>\n<task id="%s" status="1"/>\n</tasks>'%self.task.id())
        
    def testTaskWithStartDateTime(self):
        self.task.setStartDateTime(date.Now())
        self.expectInXML('startdatetmpl="Now() + TimeDelta(')
        
    def testTaskWithDueDateTime(self):
        self.task.setDueDateTime(date.Now())
        self.expectInXML('duedatetmpl="Now() + TimeDelta(')
        
    def testTaskWithCompletionDateTime(self):
        self.task.setCompletionDateTime(date.Now())
        self.expectInXML('completiondatetmpl="Now() + TimeDelta(')
        
    def testTaskWithReminder(self):
        self.task.setReminder(date.Now() + date.TimeDelta(seconds=10))
        self.expectInXML('remindertmpl="Now() + TimeDelta(')
