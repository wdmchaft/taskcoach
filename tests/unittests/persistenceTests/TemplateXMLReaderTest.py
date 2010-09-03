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

import StringIO
import test
from taskcoachlib import persistence


class TemplateXMLReaderTestCase(test.TestCase):
    tskversion = 24
    
    def setUp(self):
        self.fd = StringIO.StringIO()
        self.fd.name = 'testfile.tsk'
        self.reader = persistence.TemplateXMLReader(self.fd)
        
    def writeAndRead(self, xml):
        xml = '<?taskcoach release="whatever" tskversion="%d"?>\n'%self.tskversion + xml
        self.fd.write(xml)
        self.fd.seek(0)
        return self.reader.read()
        
    def testMissingSubject(self):
        template = self.writeAndRead('<tasks><task status="0" /></tasks>')
        self.assertEqual('', template.subject())    
    
    def testSubject(self):
        template = self.writeAndRead('<tasks><task status="0" subject="Subject"/></tasks>')
        self.assertEqual('Subject', template.subject())    
