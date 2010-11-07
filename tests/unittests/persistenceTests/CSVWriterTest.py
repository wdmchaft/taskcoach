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
from taskcoachlib import persistence, gui, config
from taskcoachlib.domain import task, effort, date


class CSVWriterTestCase(test.wxTestCase):
    treeMode = 'Subclass responsibility'
    
    def setUp(self):
        super(CSVWriterTestCase, self).setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.fd = StringIO.StringIO()
        self.writer = persistence.CSVWriter(self.fd)
        self.taskFile = persistence.TaskFile()
        self.task = task.Task('Task subject')
        self.taskFile.tasks().append(self.task)
        self.createViewer()
        
    def createViewer(self):
        self.settings.set('taskviewer', 'treemode', self.treeMode)
        # pylint: disable-msg=W0201
        self.viewer = gui.viewer.TaskViewer(self.frame, self.taskFile,
            self.settings)

    def __writeAndRead(self, selectionOnly):
        self.writer.write(self.viewer, self.settings, selectionOnly)
        return self.fd.getvalue()
    
    def expectInCSV(self, csvFragment, selectionOnly=False):
        csv = self.__writeAndRead(selectionOnly)
        self.failUnless(csvFragment in csv, 
                        '%s not in %s'%(csvFragment, csv))
    
    def expectNotInCSV(self, csvFragment, selectionOnly=False):
        csv = self.__writeAndRead(selectionOnly)
        self.failIf(csvFragment in csv, '%s in %s'%(csvFragment, csv))

    def selectItem(self, items):
        self.viewer.select(items)


class TaskTestsMixin(object):
    def testTaskSubject(self):
        self.expectInCSV('Task subject,')

    def testWriteSelectionOnly(self):
        self.expectNotInCSV('Task subject', selectionOnly=True)
        
    def testWriteSelectionOnly_SelectedChild(self):
        child = task.Task('Child', parent=self.task)
        self.taskFile.tasks().append(child)
        self.viewer.expandAll()
        self.selectItem([child])
        self.expectInCSV('Child,', selectionOnly=True)

    def testWriteSelectionOnly_SelectedParent(self):
        child = task.Task('Child', parent=self.task)
        self.taskFile.tasks().append(child)
        self.selectItem([self.task])
        self.expectNotInCSV('Child', selectionOnly=True)
                
        
class CSVListWriterTest(TaskTestsMixin, CSVWriterTestCase):
    treeMode = 'False'
        
    def testTaskDescription(self):
        self.task.setDescription('Task description')
        self.viewer.showColumnByName('description')
        self.expectInCSV(',Task description,')
    
    def testTaskDescriptionWithNewLine(self):
        self.task.setDescription('Line1\nLine2')
        self.viewer.showColumnByName('description')
        self.expectInCSV('"Line1\nLine2"')
                      

class CSVTreeWriterTest(TaskTestsMixin, CSVWriterTestCase):
    treeMode = 'True'


class EffortWriterTest(CSVWriterTestCase):
    def setUp(self):
        super(EffortWriterTest, self).setUp()
        now = date.DateTime.now()
        self.task.addEffort(effort.Effort(self.task, start=now,
                                          stop=now + date.TimeDelta(seconds=1)))

    def createViewer(self):
        # pylint: disable-msg=W0201
        self.viewer = gui.viewer.EffortViewer(self.frame, self.taskFile,
            self.settings)

    def testTaskSubject(self):
        self.expectInCSV('Task subject,')
        
    def testEffortDuration(self):
        self.expectInCSV(',0:00:01,')
        
    def testEffortPerDay(self):
        self.viewer.showEffortAggregation('day')
        self.expectInCSV('Total')

    def testEffortPerDay_SelectionOnly_EmptySelection(self):
        self.viewer.showEffortAggregation('day')
        self.expectNotInCSV('Total', selectionOnly=True)

    def testEffortPerDay_SelectionOnly_SelectAll(self):
        self.viewer.showEffortAggregation('day')
        self.viewer.widget.selectall()
        self.expectInCSV('Total', selectionOnly=True)
        