# -*- coding: utf-8 -*-

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

import wx, StringIO # We cannot use CStringIO since unicode strings are used below.
import test
from taskcoachlib import persistence, config
from taskcoachlib.domain import base, task, effort, date, category, note, attachment
from taskcoachlib.syncml.config import SyncMLConfigNode


class XMLWriterTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.fd = StringIO.StringIO()
        self.fd.name = 'testfile.tsk'
        self.writer = persistence.XMLWriter(self.fd)
        self.task = task.Task()
        self.taskList = task.TaskList([self.task])
        self.category = category.Category('Category')
        self.categoryContainer = category.CategoryList([self.category])
        self.note = note.Note()
        self.noteContainer = note.NoteContainer([self.note])
            
    def __writeAndRead(self):
        self.writer.write(self.taskList, self.categoryContainer, 
            self.noteContainer, SyncMLConfigNode('root'), u'GUID')
        return self.fd.getvalue()
    
    def expectInXML(self, xmlFragment):
        xml = self.__writeAndRead()
        self.failUnless(xmlFragment in xml, '%s not in %s'%(xmlFragment, xml))
    
    def expectNotInXML(self, xmlFragment):
        xml = self.__writeAndRead()
        self.failIf(xmlFragment in xml, '%s in %s'%(xmlFragment, xml))
    
    # tests
        
    def testVersion(self):
        from taskcoachlib import meta
        self.expectInXML('<?taskcoach release="%s"'%meta.data.version)

    def testGUID(self):
        self.expectInXML('<guid>\nGUID\n</guid>')

    def testTaskSubject(self):
        self.task.setSubject('Subject')
        self.expectInXML('subject="Subject"')

    def testTaskMarkedDeleted(self):
        self.task.markDeleted()
        self.expectInXML('status="3"')

    def testTaskSubjectWithUnicode(self):
        self.task.setSubject(u'ï¬Ÿï­Žï­–')
        self.expectInXML(u'subject="ï¬Ÿï­Žï­–"')
            
    def testTaskDescription(self):
        self.task.setDescription('Description')
        self.expectInXML('<description>\nDescription\n</description>\n')
        
    def testEmptyTaskDescriptionIsNotWritten(self):
        self.expectNotInXML('<description>')
        
    def testTaskStartDateTime(self):
        self.task.setStartDateTime(date.DateTime(2004,1,1,11,0,0))
        self.expectInXML('startdate="%s"'%str(self.task.startDateTime()))
        
    def testNoStartDateTime(self):
        self.task.setStartDateTime(date.DateTime())
        self.expectNotInXML('startdate=')
        
    def testTaskDueDateTime(self):
        self.task.setDueDateTime(date.DateTime(2004,1,1,10,5,5))
        self.expectInXML('duedate="%s"'%str(self.task.dueDateTime()))

    def testNoDueDateTime(self):
        self.expectNotInXML('duedate=')
                
    def testTaskCompletionDateTime(self):
        self.task.setCompletionDateTime(date.DateTime(2004,1,1,10,8,4))
        self.expectInXML('completiondate="%s"'%str(self.task.completionDateTime()))

    def testNoCompletionDateTime(self):
        self.expectNotInXML('completiondate=')
        
    def testChildTask(self):
        self.task.addChild(task.Task(subject='child'))
        self.expectInXML('subject="child"/>\n</task>\n<category')

    def testEffort(self):
        taskEffort = effort.Effort(self.task, date.DateTime(2004,1,1),
            date.DateTime(2004,1,2), description='description\nline 2')
        self.task.addEffort(taskEffort)
        self.expectInXML('<effort id="%s" start="%s" status="%d" stop="%s">\n'
                         '<description>\ndescription\nline 2\n</description>\n'
                         '</effort>'% \
            (taskEffort.id(), taskEffort.getStart(), base.SynchronizedObject.STATUS_NEW, taskEffort.getStop()))
        
    def testThatEffortTimesDoNotContainMilliseconds(self):
        self.task.addEffort(effort.Effort(self.task, 
            date.DateTime(2004,1,1,10,0,0,123456), 
            date.DateTime(2004,1,1,10,0,10,654310)))
        self.expectInXML('start="2004-01-01 10:00:00"')
        self.expectInXML('stop="2004-01-01 10:00:10"')
        
    def testThatEffortStartAndStopAreNotEqual(self):
        self.task.addEffort(effort.Effort(self.task, 
            date.DateTime(2004,1,1,10,0,0,123456), 
            date.DateTime(2004,1,1,10,0,0,654310)))
        self.expectInXML('start="2004-01-01 10:00:00"')
        self.expectInXML('stop="2004-01-01 10:00:01"')
            
    def testEmptyEffortDescriptionIsNotWritten(self):
        self.task.addEffort(effort.Effort(self.task, date.DateTime(2004,1,1),
            date.DateTime(2004,1,2)))
        self.expectNotInXML('<description>')
        
    def testActiveEffort(self):
        self.task.addEffort(effort.Effort(self.task, date.DateTime(2004,1,1)))
        self.expectInXML('<effort id="%s" start="%s" status="%d"/>'%(self.task.efforts()[0].id(), self.task.efforts()[0].getStart(), base.SynchronizedObject.STATUS_NEW))
                
    def testNoEffortByDefault(self):
        self.expectNotInXML('<efforts>')
        
    def testBudget(self):
        self.task.setBudget(date.TimeDelta(hours=1))
        self.expectInXML('budget="%s"'%str(self.task.budget()))
        
    def testNoBudget(self):
        self.expectNotInXML('budget')
        
    def testBudget_MoreThan24Hour(self):
        self.task.setBudget(date.TimeDelta(hours=25))
        self.expectInXML('budget="25:00:00"')
        
    def testOneCategoryWithoutTask(self):
        self.categoryContainer.append(category.Category('test', id="id"))
        self.expectInXML('<category id="id" status="1" subject="test"/>')
    
    def testOneCategoryWithOneTask(self):
        self.categoryContainer.append(category.Category('test', [self.task], id='id'))
        self.expectInXML('<category categorizables="%s" id="id" status="1" subject="test"/>'%self.task.id())
        
    def testTwoCategoriesWithOneTask(self):
        subjects = ['test', 'another']
        expectedResults = []
        for subject in subjects:
            cat = category.Category(subject, [self.task])
            self.categoryContainer.append(cat)
            expectedResults.append('<category categorizables="%s" id="%s" status="1" subject="%s"/>'%(self.task.id(), cat.id(), subject))
        for expectedResult in expectedResults:
            self.expectInXML(expectedResult)
        
    def testOneCategoryWithSubTask(self):
        child = task.Task()
        self.taskList.append(child)
        self.task.addChild(child)
        self.categoryContainer.append(category.Category('test', [child], id='id'))
        self.expectInXML('<category categorizables="%s" id="id" status="1" subject="test"/>'%child.id())
        
    def testSubCategoryWithoutTasks(self):
        parentCategory = category.Category(subject='parent')
        childCategory = category.Category(subject='child')
        parentCategory.addChild(childCategory)
        self.categoryContainer.extend([parentCategory, childCategory])
        self.expectInXML('<category id="%s" status="1" subject="parent">\n'
                         '<category id="%s" status="1" subject="child"/>\n</category>'%\
                         (parentCategory.id(), childCategory.id()))

    def testSubCategoryWithOneTask(self):
        parentCategory = category.Category(subject='parent')
        childCategory = category.Category(subject='child', categorizables=[self.task])
        parentCategory.addChild(childCategory)
        self.categoryContainer.extend([parentCategory, childCategory])
        self.expectInXML('<category id="%s" status="1" subject="parent">\n'
                         '<category categorizables="%s" id="%s" status="1" subject="child"/>\n'
                         '</category>'%(parentCategory.id(), self.task.id(), 
                                        childCategory.id()))
    
    def testFilteredCategory(self):
        filteredCategory = category.Category(subject='test', filtered=True, id='id')
        self.categoryContainer.extend([filteredCategory])
        self.expectInXML('<category filtered="True" id="id" status="1" subject="test"/>')

    def testCategoryWithDescription(self):
        aCategory = category.Category(subject='subject', description='Description', id='id')
        self.categoryContainer.append(aCategory)
        self.expectInXML('<category id="id" status="1" subject="subject">\n'
                         '<description>\nDescription\n</description>\n'
                         '</category>')
        
    def testCategoryWithUnicodeSubject(self):
        unicodeCategory = category.Category(subject=u'ï¬Ÿï­Žï­–', id='id')
        self.categoryContainer.extend([unicodeCategory])
        self.expectInXML(u'<category id="id" status="1" subject="ï¬Ÿï­Žï­–"/>')

    def testCategoryWithDeletedTask(self):
        aCategory = category.Category(subject='category', categorizables=[self.task], id='id')
        self.categoryContainer.append(aCategory)
        self.taskList.remove(self.task)
        self.expectInXML('<category id="id" status="1" subject="category"/>')
 
    def testDefaultPriority(self):
        self.expectNotInXML('priority')
        
    def testPriority(self):
        self.task.setPriority(5)
        self.expectInXML('priority="5"')
        
    def testTaskId(self):
        self.expectInXML('id="%s"'%self.task.id())
        
    def testCategoryId(self):
        aCategory = category.Category(subject='category')
        self.categoryContainer.append(aCategory)
        self.expectInXML('id="%s"'%aCategory.id())

    def testNoteId(self):
        self.expectInXML('id="%s"'%self.note.id())

    def testTwoTasks(self):
        self.task.setSubject('task 1')
        task2 = task.Task(subject='task 2')
        self.taskList.append(task2)
        self.expectInXML('subject="task 2"')

    def testDefaultHourlyFee(self):
        self.expectNotInXML('hourlyFee')
        
    def testHourlyFee(self):
        self.task.setHourlyFee(100)
        self.expectInXML('hourlyFee="100"')
        
    def testDefaultFixedFee(self):
        self.expectNotInXML('fixedFee')
        
    def testFixedFee(self):
        self.task.setFixedFee(1000)
        self.expectInXML('fixedFee="1000"')

    def testNoReminder(self):
        self.expectNotInXML('reminder')
        
    def testReminder(self):
        self.task.setReminder(date.DateTime(2005, 5, 7, 13, 15, 10))
        self.expectInXML('reminder="%s"'%str(self.task.reminder()))
        
    def testMarkCompletedWhenAllChildrenAreCompletedSetting_None(self):
        self.expectNotInXML('shouldMarkCompletedWhenAllChildrenCompleted')
            
    def testMarkCompletedWhenAllChildrenAreCompletedSetting_True(self):
        self.task.setShouldMarkCompletedWhenAllChildrenCompleted(True)
        self.expectInXML('shouldMarkCompletedWhenAllChildrenCompleted="True"')
            
    def testMarkCompletedWhenAllChildrenAreCompletedSetting_False(self):
        self.task.setShouldMarkCompletedWhenAllChildrenCompleted(False)
        self.expectInXML('shouldMarkCompletedWhenAllChildrenCompleted="False"')
              
    def testNote(self):
        self.noteContainer.append(note.Note(id='id'))
        self.expectInXML('<note id="id" status="%d"/>' % base.SynchronizedObject.STATUS_NEW)
        
    def testNoteWithSubject(self):
        self.noteContainer.append(note.Note(subject='Note', id='id'))
        self.expectInXML('<note id="id" status="%d" subject="Note"/>' % base.SynchronizedObject.STATUS_NEW)
        
    def testNoteWithDescription(self):
        self.noteContainer.append(note.Note(description='Description', id='id'))
        self.expectInXML('<note id="id" status="%d">\n'
                         '<description>\nDescription\n</description>\n'
                         '</note>' % base.SynchronizedObject.STATUS_NEW)
        
    def testNoteWithChild(self):
        child = note.Note(id='child')
        self.note.addChild(child)
        self.noteContainer.append(child)
        self.expectInXML('<note id="%s" status="%d">\n'
                         '<note id="child" status="%d"/>\n'
                         '</note>' % (self.note.id(),
                                      base.SynchronizedObject.STATUS_NEW,
                                      base.SynchronizedObject.STATUS_NEW))
        
    def testNoteWithCategory(self):
        cat = category.Category(subject='cat', id='catId')
        self.categoryContainer.append(cat)
        self.note.addCategory(cat)
        cat.addCategorizable(self.note)
        self.expectInXML('<category categorizables="%s" id="catId" status="1" subject="cat"/>'%self.note.id())

    def testCategoryForegroundColor(self):
        self.categoryContainer.append(category.Category(subject='test', fgColor=wx.RED))
        self.expectInXML('fgColor="(255, 0, 0, 255)"')

    def testCategoryBackgroundColor(self):
        self.categoryContainer.append(category.Category(subject='test', bgColor=wx.RED))
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedCategoryForegroundColor(self):
        parent = category.Category(subject='test', fgColor=wx.RED)
        child = category.Category(subject='child', id='id')
        parent.addChild(child)
        self.categoryContainer.append(parent)
        self.expectInXML('<category id="id" status="1" subject="child"/>')

    def testDontWriteInheritedCategoryBackgroundColor(self):
        parent = category.Category(subject='test', bgColor=wx.RED)
        child = category.Category(subject='child', id='id')
        parent.addChild(child)
        self.categoryContainer.append(parent)
        self.expectInXML('<category id="id" status="1" subject="child"/>')

    def testTaskForegroundColor(self):
        self.task.setForegroundColor(wx.RED)
        self.expectInXML('fgColor="(255, 0, 0, 255)"')
        
    def testTaskBackgroundColor(self):
        self.task.setBackgroundColor(wx.RED)
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedTaskForegroundColor(self):
        self.task.setForegroundColor(wx.RED)
        child = task.Task(subject='child', id='id',
                          startDateTime=date.DateTime())
        self.task.addChild(child)
        self.taskList.append(child)
        self.expectInXML('<task id="id" status="1" subject="child"/>')
        
    def testDontWriteInheritedTaskBackgroundColor(self):
        self.task.setBackgroundColor(wx.RED)
        child = task.Task(subject='child', id='id', 
                          startDateTime=date.DateTime())
        self.task.addChild(child)
        self.taskList.append(child)
        self.expectInXML('<task id="id" status="1" subject="child"/>')

    def testNoteForegroundColor(self):
        self.note.setForegroundColor(wx.RED)
        self.expectInXML('fgColor="(255, 0, 0, 255)"')

    def testNoteBackgroundColor(self):
        self.note.setBackgroundColor(wx.RED)
        self.expectInXML('bgColor="(255, 0, 0, 255)"')

    def testDontWriteInheritedNoteForegroundColor(self):
        parent = note.Note(fgColor=wx.RED)
        child = note.Note(subject='child', id='id')
        parent.addChild(child)
        self.noteContainer.append(parent)
        self.expectInXML('<note id="id" status="1" subject="child"/>')
        
    def testDontWriteInheritedNoteBackgroundColor(self):
        parent = note.Note(bgColor=wx.RED)
        child = note.Note(subject='child', id='id')
        parent.addChild(child)
        self.noteContainer.append(parent)
        self.expectInXML('<note id="id" status="1" subject="child"/>')
        
    def testNoRecurencce(self):
        self.expectNotInXML('recurrence')
        
    def testDailyRecurrence(self):
        self.task.setRecurrence(date.Recurrence('daily'))
        self.expectInXML('<recurrence unit="daily"/>')
        
    def testWeeklyRecurrence(self):
        self.task.setRecurrence(date.Recurrence('weekly'))
        self.expectInXML('<recurrence unit="weekly"/>')

    def testMonthlyRecurrence(self):
        self.task.setRecurrence(date.Recurrence('monthly'))
        self.expectInXML('<recurrence unit="monthly"/>')

    def testYearlyRecurrence(self):
        self.task.setRecurrence(date.Recurrence('yearly'))
        self.expectInXML('<recurrence unit="yearly"/>')
        
    def testRecurrenceCount(self):
        self.task.setRecurrence(date.Recurrence('daily', count=5))
        self.expectInXML('count="5"')

    def testMaxRecurrenceCount(self):
        self.task.setRecurrence(date.Recurrence('daily', max=5))
        self.expectInXML('max="5"')
        
    def testRecurrenceFrequency(self):
        self.task.setRecurrence(date.Recurrence('daily', amount=2))
        self.expectInXML('amount="2"')

    def testNoAttachments(self):
        self.expectNotInXML('attachment')
    
    # addAttachment, addNote, etc., are dynamically generated so pylint can't
    # find them. Disable the error message.
    # pylint: disable-msg=E1101
    
    def testTaskWithOneAttachment(self):
        self.task.addAttachments(attachment.FileAttachment('whatever.txt', id='foo'))
        self.expectInXML('<attachment id="foo" location="whatever.txt" status="1" subject="whatever.txt" type="file"/>')

    def testObjectWithAttachmentWithNote(self):
        att = attachment.FileAttachment('whatever.txt', id='foo')
        self.task.addAttachments(att)
        att.addNote(note.Note(subject='attnote', id='spam'))
        self.expectInXML('<attachment id="foo" location="whatever.txt" status="1" subject="whatever.txt" type="file">\n<note')

    def testNoteWithOneAttachment(self):
        self.note.addAttachments(attachment.FileAttachment('whatever.txt', id='foo'))
        self.expectInXML('<attachment id="foo" location="whatever.txt" status="1" subject="whatever.txt" type="file"/>')

    def testCategoryWithOneAttachment(self):
        cat = category.Category('cat')
        self.categoryContainer.append(cat)
        cat.addAttachments(attachment.FileAttachment('whatever.txt', id='foo'))
        self.expectInXML('<attachment id="foo" location="whatever.txt" status="1" subject="whatever.txt" type="file"/>')
        
    def testTaskWithTwoAttachments(self):
        attachments = [attachment.FileAttachment('whatever.txt'),
                       attachment.FileAttachment('/home/frank/attachment.doc')]
        for a in attachments:
            self.task.addAttachments(a)
        for att in attachments:
            self.expectInXML('<attachment id="%s" location="%s" status="1" subject="%s" type="file"/>' % (att.id(), att.location(), att.location()))
        
    def testTaskWithNote(self):
        self.task.addNote(self.note)
        self.expectInXML('>\n<note id="%s" status="1"/>\n</task>'%self.note.id())

    def testTaskWithNotes(self):
        anotherNote = note.Note(subject='Another note', id='id')
        self.task.addNote(self.note)
        self.task.addNote(anotherNote)
        self.expectInXML('>\n<note id="%s" status="1"/>\n'
            '<note id="id" status="1" subject="Another note"/>\n</task>'%self.note.id())
        
    def testTaskWithNestedNotes(self):
        subNote = note.Note(subject='Subnote', id='id')
        self.note.addChild(subNote)
        self.task.addNote(self.note)
        self.expectInXML('>\n<note id="%s" status="1">\n'
            '<note id="id" status="1" subject="Subnote"/>\n</note>\n</task>'%self.note.id())

    def testCategoryWithNote(self):
        self.category.addNote(self.note)
        self.expectInXML('>\n<note id="%s" status="1"/>\n</category>'%self.note.id())

    def testCategoryWithNotes(self):
        anotherNote = note.Note(subject='Another note', id='id')
        self.category.addNote(self.note)
        self.category.addNote(anotherNote)
        self.expectInXML('>\n<note id="%s" status="1"/>\n'
            '<note id="id" status="1" subject="Another note"/>\n</category>'%self.note.id())
        
    def testCategoryWithNestedNotes(self):
        subNote = note.Note(subject='Subnote', id='id')
        self.note.addChild(subNote)
        self.category.addNote(self.note)
        self.expectInXML('>\n<note id="%s" status="1">\n'
            '<note id="id" status="1" subject="Subnote"/>\n</note>\n</category>'%self.note.id())

    def testTaskDefaultExpansionState(self):
        # Don't write anything if the task is not expanded: 
        self.expectNotInXML('expandedContexts')

    def testTaskExpansionState(self):
        self.task.expand()
        self.expectInXML('''expandedContexts="('None',)"''')

    def testTaskExpansionState_SpecificContext(self):
        self.task.expand(context='Test')
        self.expectInXML('''expandedContexts="('Test',)"''')

    def testTaskExpansionState_MultipleContexts(self):
        self.task.expand(context='Test')
        self.task.expand(context='Another context')
        self.expectInXML('''expandedContexts="('Another context', 'Test')"''')

    def testCategoryExpansionState(self):
        cat = category.Category('cat')
        self.categoryContainer.append(cat)
        cat.expand()
        self.expectInXML('''expandedContexts="('None',)"''')

    def testNoteExpansionState(self):
        self.note.expand()
        self.expectInXML('''expandedContexts="('None',)"''')
        
    def testPercentageComplete(self):
        self.task.setPercentageComplete(50)
        self.expectInXML('''percentageComplete="50"''')

    def testPercentageComplete_Float(self):
        self.task.setPercentageComplete(50.0)
        self.expectInXML('''percentageComplete="50.0"''')
        
    def testExclusiveSubcategories(self):
        self.category.makeSubcategoriesExclusive()
        self.expectInXML('''exclusiveSubcategories="True"''')

    def testNonExclusiveSubcategoriesByDefault(self):
        self.expectNotInXML('''exclusiveSubcategories''')
        
    def testTaskFont(self):
        self.task.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"'%wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testNoTaskFontByDefault(self):
        self.expectNotInXML('font')
        
    def testNoteFont(self):
        self.note.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"'%wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testCategoryFont(self):
        self.category.setFont(wx.SWISS_FONT)
        self.expectInXML('font="%s"'%wx.SWISS_FONT.GetNativeFontInfoDesc())
        
    def testAttachmentFont(self):
        att = attachment.FileAttachment('whatever.txt', id='foo', font=wx.SWISS_FONT)
        self.task.addAttachments(att)
        self.expectInXML('<attachment font="%s" id="foo" '
                         'location="whatever.txt" status="1" '
                         'subject="whatever.txt" type="file"/>'%wx.SWISS_FONT.GetNativeFontInfoDesc())

    def testNonAsciiFontName(self):
        class FakeFont(object):
            def GetNativeFontInfoDesc(self):
                return u'微软雅黑'
        font = FakeFont()
        self.task.setFont(font)
        self.expectInXML(u'font="微软雅黑"')
        
    def testTaskIcon(self):
        self.task.setIcon('icon')
        self.expectInXML('icon="icon"')

    def testNoTaskIcon(self):
        self.expectNotInXML('icon')

    def testSelectedTaskIcon(self):
        self.task.setSelectedIcon('icon')
        self.expectInXML('selectedIcon="icon"')

    def testNoSelectedTaskIcon(self):
        self.expectNotInXML('selectedIcon')

    def testNoteIcon(self):
        self.note.setIcon('icon')
        self.expectInXML('icon="icon"')

    def testSelectedNoteIcon(self):
        self.note.setSelectedIcon('icon')
        self.expectInXML('selectedIcon="icon"')
        
    def testCategoryIcon(self):
        self.category.setIcon('icon')
        self.expectInXML('icon="icon"')

    def testSelectedCategoryIcon(self):
        self.category.setSelectedIcon('icon')
        self.expectInXML('selectedIcon="icon"')

    def testAttachmentIcon(self):
        att = attachment.FileAttachment('whatever.txt', id='foo', icon='icon')
        self.task.addAttachments(att)
        self.expectInXML('<attachment icon="icon" id="foo" '
                         'location="whatever.txt" status="1" '
                         'subject="whatever.txt" type="file"/>')

    def testSelectedAttachmentIcon(self):
        att = attachment.FileAttachment('whatever.txt', id='foo', selectedIcon='icon')
        self.task.addAttachments(att)
        self.expectInXML('<attachment id="foo" location="whatever.txt" '
                         'selectedIcon="icon" status="1" '
                         'subject="whatever.txt" type="file"/>')
