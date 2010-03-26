# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2007 Jérôme Laheurte <fraca7@free.fr>

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

import StringIO, wx
import test
from taskcoachlib import persistence
from taskcoachlib import config
from taskcoachlib.domain import task, category, effort, date, note, attachment
from taskcoachlib.syncml.config import SyncMLConfigNode


class IntegrationTestCase(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.fd = StringIO.StringIO()
        self.fd.name = 'testfile.tsk'
        self.reader = persistence.XMLReader(self.fd)
        self.writer = persistence.XMLWriter(self.fd)
        self.taskList = task.TaskList()
        self.categories = category.CategoryList()
        self.notes = note.NoteContainer()
        self.syncMLConfig = SyncMLConfigNode('root')
        self.guid = u'GUID'
        self.fillContainers()
        tasks, categories, notes, syncMLConfig, guid = self.readAndWrite()
        self.tasksWrittenAndRead = task.TaskList(tasks)
        self.categoriesWrittenAndRead = category.CategoryList(categories)
        self.notesWrittenAndRead = note.NoteContainer(notes)
        self.syncMLConfigWrittenAndRead = syncMLConfig
        self.guidWrittenAndRead = guid

    def fillContainers(self):
        pass

    def readAndWrite(self):
        self.fd.seek(0)
        self.writer.write(self.taskList, self.categories, self.notes, self.syncMLConfig, self.guid)
        self.fd.seek(0)
        return self.reader.read()


class IntegrationTest_EmptyList(IntegrationTestCase):
    def testEmptyTaskList(self):
        self.assertEqual([], self.tasksWrittenAndRead)
        
    def testNoCategories(self):
        self.assertEqual([], self.categoriesWrittenAndRead)
        
        
class IntegrationTest(IntegrationTestCase):
    def fillContainers(self):
        # pylint: disable-msg=W0201
        self.description = 'Description\nLine 2'
        self.task = task.Task(subject='Subject', description=self.description, 
            startDate=date.Yesterday(), dueDate=date.Tomorrow(), 
            completionDate=date.Yesterday(), budget=date.TimeDelta(hours=1), 
            priority=4, hourlyFee=100.5, fixedFee=1000, 
            recurrence=date.Recurrence('weekly', max=10, count=5, amount=2),
            reminder=date.DateTime(2004,1,1), fgColor=wx.BLUE, bgColor=wx.RED,
            font=wx.NORMAL_FONT, expandedContexts=['viewer1'], icon='icon',
            selectedIcon='selectedIcon',
            shouldMarkCompletedWhenAllChildrenCompleted=True,
            percentageComplete=2/3.)
        self.child = task.Task()
        self.task.addChild(self.child)
        self.grandChild = task.Task()
        self.child.addChild(self.grandChild)
        self.task.addEffort(effort.Effort(self.task, start=date.DateTime(2004,1,1), 
            stop=date.DateTime(2004,1,2), description=self.description))
        self.category = category.Category('test', [self.task], filtered=True,
                                          description='Description', 
                                          exclusiveSubcategories=True)
        self.categories.append(self.category)
        # pylint: disable-msg=E1101
        self.task.addAttachments(attachment.FileAttachment('/home/frank/whatever.txt'))
        self.task.addNote(note.Note(subject='Task note'))
        self.task2 = task.Task('Task 2', priority=-1954)
        self.taskList.extend([self.task, self.task2])
        self.note = note.Note(subject='Note', description='Description', 
                              children=[note.Note(subject='Child')])
        self.notes.append(self.note)
        self.category.addCategorizable(self.note)

    def getTaskWrittenAndRead(self, targetId):
        # pylint: disable-msg=W0621
        return [task for task in self.tasksWrittenAndRead if task.id() == targetId][0]

    def assertAttributeWrittenAndRead(self, aTask, attribute):
        taskWrittenAndRead = self.getTaskWrittenAndRead(aTask.id())
        self.assertEqual(getattr(aTask, attribute)(), 
                         getattr(taskWrittenAndRead, attribute)())
                         
    def assertContainedDomainObjectsWrittenAndRead(self, aTask, attribute):
        taskWrittenAndRead = self.getTaskWrittenAndRead(aTask.id())
        self.assertEqual([obj.id() for obj in getattr(aTask, attribute)()], 
                         [obj.id() for obj in getattr(taskWrittenAndRead, attribute)()])
               
    def testSubject(self):
        self.assertAttributeWrittenAndRead(self.task, 'subject')

    def testDescription(self):
        self.assertAttributeWrittenAndRead(self.task, 'description')

    def testForegroundColor(self):
        self.assertAttributeWrittenAndRead(self.task, 'foregroundColor')

    def testBackgroundColor(self):
        self.assertAttributeWrittenAndRead(self.task, 'backgroundColor')

    def testFont(self):
        self.assertAttributeWrittenAndRead(self.task, 'font')

    def testIcon(self):
        self.assertAttributeWrittenAndRead(self.task, 'icon')
        
    def testExpansionState(self):
        self.assertAttributeWrittenAndRead(self.task, 'isExpanded')
         
    def testStartDate(self):
        self.assertAttributeWrittenAndRead(self.task, 'startDate')
                
    def testDueDate(self):
        self.assertAttributeWrittenAndRead(self.task, 'dueDate')
 
    def testCompletionDate(self):
        self.assertAttributeWrittenAndRead(self.task, 'completionDate')
        
    def testPercentageComplete(self):
        self.assertAttributeWrittenAndRead(self.task, 'percentageComplete')
 
    def testBudget(self):
        self.assertAttributeWrittenAndRead(self.task, 'budget')
        
    def testBudget_MoreThan24Hour(self):
        self.task.setBudget(date.TimeDelta(hours=25))
        self.tasksWrittenAndRead = task.TaskList(self.readAndWrite()[0])
        self.assertAttributeWrittenAndRead(self.task, 'budget')
        
    def testEffort(self):
        self.assertAttributeWrittenAndRead(self.task, 'timeSpent')
        
    def testEffortDescription(self):
        self.assertEqual(self.task.efforts()[0].description(), 
            self.getTaskWrittenAndRead(self.task.id()).efforts()[0].description())
        
    def testChildren(self):
        self.assertEqual(len(self.task.children()), 
            len(self.getTaskWrittenAndRead(self.task.id()).children()))
        
    def testGrandChildren(self):
        self.assertEqual(len(self.task.children(recursive=True)),  
            len(self.getTaskWrittenAndRead(self.task.id()).children(recursive=True)))
       
    def testCategory(self):
        categorizables = list(self.categoriesWrittenAndRead)[0].categorizables()
        categorizableIds = set([item.id() for item in categorizables])
        self.assertEqual(set([self.task.id(), self.note.id()]), 
                         categorizableIds)

    def testFilteredCategory(self):
        self.failUnless(list(self.categoriesWrittenAndRead)[0].isFiltered())

    def testExclusiveSubcategories(self):
        self.failUnless(list(self.categoriesWrittenAndRead)[0].hasExclusiveSubcategories())
        
    def testPriority(self):
        self.assertAttributeWrittenAndRead(self.task, 'priority')
        
    def testNegativePriority(self):
        self.assertAttributeWrittenAndRead(self.task2, 'priority')
        
    def testHourlyFee(self):
        self.assertAttributeWrittenAndRead(self.task, 'hourlyFee')

    def testFixedFee(self):
        self.assertAttributeWrittenAndRead(self.task, 'fixedFee')

    def testReminder(self):
        self.assertAttributeWrittenAndRead(self.task, 'reminder')
        
    def testNoReminder(self):
        self.assertAttributeWrittenAndRead(self.task2, 'reminder')
        
    def testMarkCompletedWhenAllChildrenCompletedSetting_True(self):
        self.assertAttributeWrittenAndRead(self.task, 
            'shouldMarkCompletedWhenAllChildrenCompleted')
 
    def testMarkCompletedWhenAllChildrenCompletedSetting_None(self):
        self.assertAttributeWrittenAndRead(self.task2, 
            'shouldMarkCompletedWhenAllChildrenCompleted')
 
    def testAttachment(self):
        self.assertAttributeWrittenAndRead(self.task, 'attachments')

    def testRecurrence(self):
        self.assertAttributeWrittenAndRead(self.task, 'recurrence')
                            
    def testNote(self):
        self.assertEqual(len(self.notes), len(self.notesWrittenAndRead))

    def testRootNote(self):
        self.assertEqual(self.notes.rootItems()[0].subject(), 
            self.notesWrittenAndRead.rootItems()[0].subject())
        
    def testChildNote(self):
        self.assertEqual(self.notes.rootItems()[0].children()[0].subject(), 
            self.notesWrittenAndRead.rootItems()[0].children()[0].subject())
        
    def testCategoryDescription(self):
        self.assertEqual(list(self.categories)[0].description(), 
                         list(self.categoriesWrittenAndRead)[0].description())

    def testNoteId(self):
        self.assertEqual(self.notes.rootItems()[0].id(),
                         self.notesWrittenAndRead.rootItems()[0].id())
        
    def testCategoryId(self):
        self.assertEqual(self.category.id(),
                         list(self.categoriesWrittenAndRead)[0].id())
        
    def testNoteWithCategory(self):
        self.failUnless(self.notesWrittenAndRead.rootItems()[0] in \
                        list(self.categoriesWrittenAndRead)[0].categorizables())
        
    def testTaskNote(self):
        self.assertContainedDomainObjectsWrittenAndRead(self.task, 'notes')

    def testSyncMLConfig(self):
        self.assertEqual(self.syncMLConfigWrittenAndRead.name,
                         self.syncMLConfig.name)

    def testGUID(self):
        self.assertEqual(self.guidWrittenAndRead, self.guid)
