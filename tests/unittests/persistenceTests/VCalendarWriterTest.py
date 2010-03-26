'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jerome Laheurte <fraca7@free.fr>

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

import test, cStringIO
from taskcoachlib import persistence, gui, config, meta
from taskcoachlib.domain import task, effort, date


class VCalTestCase(test.wxTestCase):
    selectionOnly = 'Subclass responsibility'
    
    def setUp(self):
        super(VCalTestCase, self).setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.fd = cStringIO.StringIO()
        self.writer = persistence.iCalendarWriter(self.fd)
        self.taskFile = persistence.TaskFile()

    def writeAndRead(self):
        self.writer.write(self.viewer, self.settings, self.selectionOnly)
        return self.fd.getvalue().split('\r\n')[:-1]

    def selectItems(self, items):
        self.viewer.widget.select(items)
        
    def numberOfSelectedItems(self):
        return len(self.viewer.curselection())
    
    def numberOfVisibleItems(self):
        return self.viewer.size()
    
    
class VCalendarCommonTestsMixin(object):        
    def testStart(self):
        self.assertEqual('BEGIN:VCALENDAR', self.vcalFile[0])
        
    def testVersion(self):
        self.assertEqual('VERSION:2.0', self.vcalFile[1])

    def testProdId(self):
        domain = meta.url[len('http://'):-1]
        self.assertEqual('PRODID:-//%s//NONSGML %s V%s//EN'%(domain,
            meta.name, meta.version), self.vcalFile[2])

    def testEnd(self):
        self.assertEqual('END:VCALENDAR', self.vcalFile[-1])


class VCalEffortWriterTestCase(VCalTestCase):
    def setUp(self):
        super(VCalEffortWriterTestCase, self).setUp()        
        self.task1 = task.Task('Task 1')
        self.effort1 = effort.Effort(self.task1, description='Description',
                                     start=date.DateTime(2000,1,1,1,1,1),
                                     stop=date.DateTime(2000,2,2,2,2,2))
        self.effort2 = effort.Effort(self.task1)
        self.task1.addEffort(self.effort1)
        self.task1.addEffort(self.effort2)
        self.taskFile.tasks().extend([self.task1])
        self.viewer = gui.viewer.EffortViewer(self.frame, self.taskFile,
                                              self.settings)
        self.viewer.widget.select([self.effort1])
        self.vcalFile = self.writeAndRead()


class VCalEffortCommonTestsMixin(VCalendarCommonTestsMixin):
    def testBeginVEvent(self):
        self.assertEqual(self.expectedNumberOfItems(), 
                         self.vcalFile.count('BEGIN:VEVENT'))

    def testEndVEvent(self):
        self.assertEqual(self.expectedNumberOfItems(), 
                         self.vcalFile.count('END:VEVENT'))
        
    def testEffortSubject(self):
        self.failUnless('SUMMARY:Task 1' in self.vcalFile)

    def testEffortDescription(self):
        self.failUnless('DESCRIPTION:Description' in self.vcalFile)
        
    def testEffortStart(self):
        self.failUnless('DTSTART:20000101T010101' in self.vcalFile)

    def testEffortEnd(self):
        self.failUnless('DTEND:20000202T020202' in self.vcalFile)
        
    def testEffortId(self):
        self.failUnless('UID:%s'%self.effort1.id() in self.vcalFile)

    
class VCalEffortWriterTest(VCalEffortWriterTestCase,
                           VCalEffortCommonTestsMixin):
    selectionOnly = False
    
    def expectedNumberOfItems(self):
        return self.numberOfVisibleItems()
        

class VCalEffortWriterSelectionOnlyTest(VCalEffortWriterTestCase,
                                        VCalEffortCommonTestsMixin):
    selectionOnly = True

    def expectedNumberOfItems(self):
        return self.numberOfSelectedItems()
            

class VCalTaskWriterTestCase(VCalTestCase):
    treeMode = 'Subclass responsibility'
    
    def setUp(self):
        super(VCalTaskWriterTestCase, self).setUp() 
        self.task1 = task.Task('Task subject 1')
        self.task2 = task.Task('Task subject 2')
        self.taskFile.tasks().extend([self.task1, self.task2])
        self.settings.set('taskviewer', 'treemode', self.treeMode)
        self.viewer = gui.viewer.TaskViewer(self.frame, self.taskFile,
            self.settings)
        self.selectItems([self.task2])
        self.vcalFile = self.writeAndRead()
        
        
class VCalTaskCommonTestsMixin(VCalendarCommonTestsMixin):
    def testTaskSubject(self):
        self.failUnless('SUMMARY:Task subject 2' in self.vcalFile)

    def testNumber(self):
        self.assertEqual(self.expectedNumberOfItems(),
                         self.vcalFile.count('BEGIN:VTODO'))

    def testTaskId(self):
        self.failUnless('UID:%s'%self.task2.id() in self.vcalFile)


class TestSelectionOnlyMixin(VCalTaskCommonTestsMixin):
    selectionOnly = True

    def expectedNumberOfItems(self):
        return self.numberOfSelectedItems()  


class TestSelectionList(TestSelectionOnlyMixin, VCalTaskWriterTestCase):
    treeMode = 'False'

class TestSelectionTree(TestSelectionOnlyMixin, VCalTaskWriterTestCase):
    treeMode = 'True'


class TestNotSelectionOnlyMixin(VCalTaskCommonTestsMixin):
    selectionOnly = False

    def expectedNumberOfItems(self):
        return self.numberOfVisibleItems()


class TestNotSelectionList(TestNotSelectionOnlyMixin, VCalTaskWriterTestCase):
    treeMode = 'False'

class TestNotSelectionTree(TestNotSelectionOnlyMixin, VCalTaskWriterTestCase):
    treeMode = 'True'
    

class FoldTest(test.TestCase):
    def setUp(self):
        super(FoldTest, self).setUp()
        self.fold = persistence.icalendar.ical.fold

    def testEmptyText(self):
        self.assertEqual('', self.fold([]))
        
    def testDontFoldAShortLine(self):
        self.assertEqual('Short line\r\n', self.fold(['Short line']))
        
    def testFoldALongLine(self):
        self.assertEqual('Long \r\n line\r\n', self.fold(['Long line'], 
                                                         linewidth=5))
        
    def testFoldAReallyLongLine(self):
        self.assertEqual('Long\r\n  li\r\n ne\r\n', self.fold(['Long line'], 
                                                              linewidth=4))
        
    def testFoldTwoShortLines(self):
        self.assertEqual('Short line\r\n'*2, self.fold(['Short line']*2))
        
    def testFoldTwoLongLines(self):
        self.assertEqual('Long \r\n line\r\n'*2, self.fold(['Long line']*2, 
                                                         linewidth=5))
    
