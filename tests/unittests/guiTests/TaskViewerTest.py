'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>

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

import wx, os
import test
from taskcoachlib import gui, config, persistence, command, patterns
from taskcoachlib.gui import render
from taskcoachlib.i18n import _
from taskcoachlib.domain import task, date, effort, category, attachment


class TaskViewerUnderTest(gui.viewer.task.TaskViewer): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        super(TaskViewerUnderTest, self).__init__(*args, **kwargs)
        self.events = []
    
    def onAttributeChanged(self, event):
        super(TaskViewerUnderTest, self).onAttributeChanged(event)
        self.events.append(event)
        

class TaskViewerTestCase(test.wxTestCase):
    treeMode = 'Subclass responsibility'
    
    def setUp(self):
        super(TaskViewerTestCase, self).setUp()
        task.Task.settings = self.settings = config.Settings(load=False)
        self.task = task.Task(subject='task')
        self.child = task.Task(subject='child')
        self.child.setParent(self.task)
        self.taskFile = persistence.TaskFile()
        self.taskList = self.taskFile.tasks()
        self.viewer = TaskViewerUnderTest(self.frame, self.taskFile, 
                                          self.settings)
        self.viewer.sortBy('subject')
        self.viewer.setSortOrderAscending()
        self.viewer.setSortByTaskStatusFirst(True)
        self.viewer.showTree(self.treeMode)
        self.newColor = (100, 200, 100, 255)
        attachment.Attachment.attdir = os.getcwd()

    def tearDown(self):
        super(TaskViewerTestCase, self).tearDown()
        attachment.Attachment.attdir = None

        for name in os.listdir('.'):
            if os.path.isdir(name) and name.endswith('_attachments'):
                os.rmdir(name) # pragma: no cover
        if os.path.isfile('test.mail'):
            os.remove('test.mail')
        
    def assertItems(self, *tasks):
        self.viewer.widget.expandAllItems()
        self.assertEqual(self.viewer.size(), len(tasks))
        for index, eachTask in enumerate(tasks):
            self.assertItem(index, eachTask)
            
    def assertItem(self, index, aTask):
        if type(aTask) == type((), ):
            aTask, nrChildren = aTask
        else:
            nrChildren = 0
        subject = aTask.subject(recursive=not self.viewer.isTreeViewer())
        treeItem = self.viewer.widget.GetItemChildren(recursively=True)[index]
        self.assertEqual(subject, self.viewer.widget.GetItemText(treeItem))
        self.assertEqual(nrChildren, 
            self.viewer.widget.GetChildrenCount(treeItem, recursively=False))

    def firstItem(self):
        widget = self.viewer.widget
        return widget.GetFirstChild(widget.GetRootItem())[0]

    def getItemText(self, row, column):
        assert row==0
        return self.viewer.widget.GetItemText(self.firstItem(), column)
                                             
    def getFirstItemTextColor(self):
        return self.viewer.widget.GetItemTextColour(self.firstItem())
    
    def getFirstItemBackgroundColor(self):
        return self.viewer.widget.GetItemBackgroundColour(self.firstItem())

    def getFirstItemFont(self):
        return self.viewer.widget.GetItemFont(self.firstItem())

    def showColumn(self, columnName, show=True):
        self.viewer.showColumnByName(columnName, show)
    
    def assertColor(self, expectedColor=None):
        expectedColor = expectedColor or wx.Colour(*self.newColor)
        self.assertEqual(expectedColor, self.getFirstItemTextColor())
        
    def assertBackgroundColor(self):
        self.assertEqual(wx.Colour(*self.newColor), 
                         self.getFirstItemBackgroundColor())
                         
    def setColor(self, setting):
        self.settings.set('color', setting, str(self.newColor))        
        

class CommonTestsMixin(object):
    def testCreate(self):
        self.assertItems()
        
    def testAddTask(self):
        self.taskList.append(self.task)
        self.assertItems(self.task)

    def testRemoveTask(self):
        self.taskList.append(self.task)
        self.taskList.remove(self.task)
        self.assertItems()

    def testUndoRemoveTaskWithSubtask(self):
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        self.viewer.widget.select([self.task])
        deleteItem = self.viewer.deleteItemCommand()
        deleteItem.do()
        deleteItem.undo()
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), self.child)
        else:
            self.assertItems(self.child, self.task)

    def testCurrent(self):
        self.taskList.append(self.task)
        self.viewer.widget.select([self.task])
        self.assertEqual([self.task], self.viewer.curselection())

    def testDeleteSelectedTask(self):
        self.taskList.append(self.task)
        self.viewer.widget.selectall()
        self.taskList.removeItems(self.viewer.curselection())
        self.assertItems()

    def testSelectedTaskStaysSelectedWhenStartingEffortTracking(self):
        self.taskList.append(self.task)
        self.viewer.widget.select([self.task])
        self.assertEqual([self.task], self.viewer.curselection())
        self.task.addEffort(effort.Effort(self.task))
        self.assertEqual([self.task], self.viewer.curselection())
        
    def testChildOrder(self):
        child1 = task.Task(subject='1')
        self.task.addChild(child1)
        child2 = task.Task(subject='2')
        self.task.addChild(child2)
        self.taskList.append(self.task)
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 2), child1, child2)
        else:
            self.assertItems(child1, child2, self.task)

    def testChildSubjectRendering(self):
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), self.child)
        else:
            self.assertItems(self.child, self.task)
           
    def testSortOrder(self):
        self.task.addChild(self.child)
        task2 = task.Task(subject='zzz')
        self.taskList.extend([self.task, task2])
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), self.child, task2)
        else:
            self.assertItems(self.child, self.task, task2)

    def testMarkCompleted(self):
        task2 = task.Task(subject='task2')
        self.taskList.extend([self.task, task2])
        self.assertItems(self.task, task2)
        self.task.setCompletionDate()
        self.assertItems(task2, self.task)
        
    def testMakeInactive(self):
        task2 = task.Task(subject='task2')
        self.taskList.extend([self.task, task2])
        self.assertItems(self.task, task2)
        self.task.setStartDate(date.Tomorrow())
        self.assertItems(task2, self.task)
                        
    def testViewDueTodayHidesTasksNotDueToday(self):
        self.viewer.setFilteredByDueDate('Today')
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        self.assertItems()
        
    def testViewDueTodayShowsTasksWhoseChildrenAreDueToday(self):
        self.viewer.setFilteredByDueDate('Today')
        child = task.Task(subject='child', dueDate=date.Today())
        self.task.addChild(child)
        self.taskList.append(self.task)
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), child)
        else:
            self.assertItems(child)
        
    def testFilterCompletedTasks(self):
        self.viewer.hideCompletedTasks()
        completedChild = task.Task(completionDate=date.Today())
        notCompletedChild = task.Task()
        self.task.addChild(notCompletedChild)
        self.task.addChild(completedChild)
        self.taskList.append(self.task)
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), notCompletedChild)
        else:
            self.assertItems(notCompletedChild, self.task)
            
    def testUndoMarkCompletedWhenFilteringCompletedTasks(self):
        self.viewer.hideCompletedTasks()
        child1 = task.Task('child1')
        child2 = task.Task('child2')
        grandChild = task.Task('grandChild')
        self.task.addChild(child1)
        self.task.addChild(child2)
        child2.addChild(grandChild)
        self.taskList.append(self.task)
        self.assertEqual(4, self.viewer.size())
        markCompletedCommand = command.MarkCompletedCommand(self.taskList, 
                                                            [grandChild])
        markCompletedCommand.do()
        self.assertEqual(2, self.viewer.size())
        patterns.CommandHistory().undo()
        self.assertEqual(4, self.viewer.size())
            
    def testSubjectColumnIsVisible(self):
        self.assertEqual(_('Subject'), self.viewer.widget.GetColumn(0).GetText())
    
    def testStartDateColumnIsVisibleByDefault(self):
        self.assertEqual(_('Start date'), self.viewer.widget.GetColumn(1).GetText())
        
    def testDueDateColumnIsVisibleByDefault(self):
        self.assertEqual(_('Due date'), self.viewer.widget.GetColumn(2).GetText())

    def testThreeColumnsByDefault(self):
        self.assertEqual(3, self.viewer.widget.GetColumnCount())
    
    def testTurnOffStartDateColumn(self):
        self.showColumn('startDate', False)
        self.assertEqual(_('Due date'), self.viewer.widget.GetColumn(1).GetText())
        self.assertEqual(2, self.viewer.widget.GetColumnCount())
        
    def testShowSort_Subject(self):
        self.assertNotEqual(-1, self.viewer.widget.GetColumn(0).GetImage())
        self.assertEqual(-1, self.viewer.widget.GetColumn(1).GetImage())
    
    def testForegroundColorWhenTaskIsCompleted(self):
        self.taskList.append(self.task)
        self.task.setCompletionDate()
        newColor = self.task.statusColor()
        newColor = wx.Colour(newColor.Red(), newColor.Green(), newColor.Blue())
        self.assertColor(newColor)

    def testTurnOnHourlyFeeColumn(self):
        self.showColumn('hourlyFee')
        self.assertEqual(_('Hourly fee'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOnFixedFeeColumn(self):
        self.showColumn('fixedFee')
        self.assertEqual(_('Fixed fee'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOnTotalFixedFeeColumn(self):
        self.showColumn('totalFixedFee')
        self.assertEqual(_('Total fixed fee'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOnFixedFeeColumnWithItemsInTheList(self):
        taskWithFixedFee = task.Task(fixedFee=100)
        self.taskList.append(taskWithFixedFee)
        self.showColumn('fixedFee')
        self.assertEqual(_('Fixed fee'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOnPriorityColumn(self):
        self.showColumn('priority')
        self.assertEqual(_('Priority'), 
                         self.viewer.widget.GetColumn(3).GetText())
        
    def testTurnOffPriorityColumn(self):
        self.showColumn('priority')
        self.showColumn('priority', False)
        self.assertEqual(3, self.viewer.widget.GetColumnCount())
        
    def testTurnOnPercentageCompleteColumn(self):
        self.showColumn('percentageComplete')
        self.assertEqual(_('% complete'), 
                         self.viewer.widget.GetColumn(3).GetText())
        
    def testTurnOffPercentageCompleteColumn(self):
        self.showColumn('percentageComplete')
        self.showColumn('percentageComplete', False)
        self.assertEqual(3, self.viewer.widget.GetColumnCount())

    def testTurnOnAveragePercentageCompleteColumn(self):
        self.showColumn('totalPercentageComplete')
        self.assertEqual(_('Overall % complete'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOffAveragePercentageCompleteColumn(self):
        self.showColumn('totalPercentageComplete')
        self.showColumn('totalPercentageComplete', False)
        self.assertEqual(3, self.viewer.widget.GetColumnCount())
        
    def testRenderPercentageComplete_0(self):
        uncompletedTask = task.Task()
        self.taskList.append(uncompletedTask)
        self.showColumn('percentageComplete')
        self.assertEqual('', self.getItemText(0,3))

    def testRenderPercentageComplete_100(self):
        completedTask = task.Task(completionDate=date.Today())
        self.taskList.append(completedTask)
        self.showColumn('percentageComplete')
        self.assertEqual('100%', self.getItemText(0,3))
        
    def testTurnOnRecurrenceColumn(self):
        self.showColumn('recurrence')
        self.assertEqual(_('Recurrence'), 
                         self.viewer.widget.GetColumn(3).GetText())

    def testTurnOffRecurrenceColumn(self):
        self.showColumn('recurrence')
        self.showColumn('recurrence', False)
        self.assertEqual(3, self.viewer.widget.GetColumnCount())
        
    def testRenderRecurrence(self):
        taskWithRecurrence = task.Task(recurrence=date.Recurrence('weekly', amount=2))
        self.showColumn('recurrence')
        self.taskList.append(taskWithRecurrence)
        self.assertEqual('Every other week', self.getItemText(0,3))

    def testOneDayLeft(self):
        self.showColumn('timeLeft')
        self.task.setDueDate(date.Tomorrow())
        self.taskList.append(self.task)
        self.assertEqual(render.daysLeft(self.task.timeLeft(), False), 
            self.getItemText(0, 3))
        
    def testReverseSortOrderWithGrandchildren(self):
        self.task.addChild(self.child)
        grandchild = task.Task(subject='grandchild')
        self.child.addChild(grandchild)
        task2 = task.Task(subject='zzz')
        self.taskList.extend([self.task, task2])
        self.viewer.setSortOrderAscending(False)
        if self.viewer.isTreeViewer():
            self.assertItems(task2, (self.task, 1), (self.child, 1), grandchild)
        else:
            self.assertItems(task2, self.task, grandchild, self.child)
                
    def testReverseSortOrder(self):
        self.task.addChild(self.child)
        task2 = task.Task(subject='zzz')
        self.taskList.extend([self.task, task2])
        self.viewer.setSortOrderAscending(False)
        if self.viewer.isTreeViewer():
            self.assertItems(task2, (self.task, 1), self.child)
        else:
            self.assertItems(task2, self.task, self.child)

    def testSortByDueDate(self):
        self.task.addChild(self.child)
        task2 = task.Task(subject='zzz')
        child2 = task.Task(subject='child 2')
        task2.addChild(child2)
        child2.setParent(task2)
        self.taskList.extend([self.task, task2])
        if self.viewer.isTreeViewer():
            self.assertItems((self.task, 1), self.child, (task2, 1), child2)
        else:
            self.assertItems(self.child, child2, self.task, task2) 
        child2.setDueDate(date.Today())
        self.viewer.sortBy('dueDate')
        if self.viewer.isTreeViewer():
            self.assertItems((task2, 1), child2, (self.task, 1), self.child)
        else:    
            self.assertItems(child2, self.child, self.task, task2)
    
    def testChangeActiveTaskForegroundColor(self):
        self.taskList.append(task.Task(subject='test'))
        self.setColor('activetasks')
        self.assertColor()
    
    def testChangeInactiveTaskForegroundColor(self):
        self.setColor('inactivetasks')
        self.taskList.append(task.Task(startDate=date.Tomorrow()))
        self.assertColor()
    
    def testChangeCompletedTaskForegroundColor(self):
        self.setColor('completedtasks')
        self.taskList.append(task.Task(completionDate=date.Today()))
        self.assertColor()

    def testChangeDueSoonTaskForegroundColor(self):
        self.setColor('duesoontasks')
        self.taskList.append(task.Task(dueDate=date.Today()))
        self.assertColor()

    def testChangeOverDueTaskForegroundColor(self):
        self.setColor('overduetasks')
        self.taskList.append(task.Task(dueDate=date.Yesterday()))
        self.assertColor()
            
    def testStatusMessage_EmptyTaskList(self):
        self.assertEqual(('Tasks: 0 selected, 0 visible, 0 total', 
            'Status: 0 over due, 0 inactive, 0 completed'),
            self.viewer.statusMessages())
    
    def testOnDropFiles(self):
        aTask = task.Task()
        self.taskList.append(aTask)
        self.viewer.onDropFiles(aTask, ['filename'])
        self.assertEqual([attachment.FileAttachment('filename')],
                         self.viewer.presentation()[0].attachments())

    def testOnDropURL(self):
        aTask = task.Task()
        self.taskList.append(aTask)
        self.viewer.onDropURL(aTask, 'http://www.example.com/')
        self.assertEqual([attachment.URIAttachment('http://www.example.com/')],
                         self.viewer.presentation()[0].attachments())

    def testOnDropMail(self):
        file('test.mail', 'wb').write('Subject: foo\r\n\r\nBody\r\n')
        aTask = task.Task()
        self.taskList.append(aTask)
        self.viewer.onDropMail(aTask, 'test.mail')
        self.assertEqual([attachment.MailAttachment('test.mail')],
                         self.viewer.presentation()[0].attachments())
        
    def testCategoryBackgroundColor(self):
        cat = category.Category('category with background color', bgColor=self.newColor)
        cat.addCategorizable(self.task)
        self.task.addCategory(cat)
        self.taskList.append(self.task)
        self.assertBackgroundColor()
        
    def testNewItem(self):
        self.taskFile.categories().append(category.Category('cat', filtered=True))
        dialog = self.viewer.newItemDialog(bitmap='new')
        tree = dialog[0][3].viewer.widget
        firstChild = tree.GetFirstChild(tree.GetRootItem())[0]
        self.failUnless(firstChild.IsChecked())
        
    def testMidnightStatusUpdate(self):
        self.taskList.append(task.Task(subject='test', dueDate=date.Tomorrow()))
        tomorrow = date.Tomorrow()
        midnight = date.DateTime(tomorrow.year, tomorrow.month, tomorrow.day)
        originalToday = date.Today
        date.Today = date.Tomorrow # Make it tomorrow
        date.Clock().notifyMidnightObservers(now=midnight)
        expectedColor = wx.Colour(255,128,0)
        self.assertColor(expectedColor)
        date.Today = originalToday

    def testFont(self):
        self.taskList.append(task.Task(font=wx.SWISS_FONT))
        self.assertEqual(wx.SWISS_FONT, self.getFirstItemFont())
        

class TreeOrListModeTestsMixin(object):        
    def testModeIsSavedInSettings(self):
        self.assertEqual(self.treeMode, 
            self.settings.getboolean(self.viewer.settingsSection(), 'treemode'))

    def testRenderSubject(self):
        self.task.addChild(self.child)
        if self.treeMode:
            expectedSubject = 'child'
        else:
            expectedSubject = 'task -> child'
        self.assertEqual(expectedSubject, self.viewer.renderSubject(self.child))
                         
    def testItemOrder(self):
        self.task.addChild(self.child)
        self.taskList.append(self.task)        
        if self.treeMode:
            self.assertItems((self.task, 1), self.child)
        else:
            self.assertItems(self.child, self.task)
                         
    def testItemOrderAfterSwitch(self):
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        self.viewer.showTree(not self.treeMode)
        if self.treeMode:
            self.assertItems(self.child, self.task)
        else:
            self.assertItems((self.task, 1), self.child)

    def testItemOrderAfterSwitchWhenOrderDoesNotChange(self):
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        self.task.setSubject('a') # task comes before child
        self.viewer.showTree(not self.treeMode)
        if self.treeMode:
            self.assertItems(self.task, self.child)
        else:
            self.assertItems((self.task, 1), self.child)
            

class ColumnsTestsMixin(object):        
    def testGetTimeSpent(self):
        self.taskList.append(self.task)
        self.task.addEffort(effort.Effort(self.task, date.DateTime(2000,1,1),
                                                     date.DateTime(2000,1,2)))
        self.showColumn('timeSpent')
        timeSpent = self.getItemText(0, 3)
        self.assertEqual("24:00:00", timeSpent)

    def testGetTotalTimeSpent(self):
        self.taskList.append(self.task)
        self.task.addEffort(effort.Effort(self.task, date.DateTime(2000,1,1),
                                                     date.DateTime(2000,1,2)))
        self.showColumn('totalTimeSpent')
        totalTimeSpent = self.getItemText(0, 3)
        self.assertEqual("24:00:00", totalTimeSpent)
        
    def testGetSelection(self):
        taskA = task.Task('a')
        taskB = task.Task('b')
        self.viewer.presentation().extend([taskA, taskB])
        self.viewer.widget.select([taskA])
        self.assertEqual([taskA], self.viewer.curselection())

    def testGetSelection_AfterResort(self):
        taskA = task.Task('a')
        taskB = task.Task('b')
        self.viewer.presentation().extend([taskA, taskB])
        self.viewer.widget.select([taskA])
        self.viewer.onSelect([taskA])
        self.viewer.setSortOrderAscending(False)
        self.assertEqual([taskA], self.viewer.curselection())
        
    def testChangeSubject(self):
        self.taskList.append(self.task)
        self.task.setSubject('New subject')
        self.assertEqual(task.Task.subjectChangedEventType(), 
                         self.viewer.events[0].type())

    def testChangeStartDateWhileColumnShown(self):
        self.taskList.append(self.task)
        self.task.setStartDate(date.Yesterday())
        self.assertEqual('task.startDate', self.viewer.events[0].type())

    def testStartTracking(self):
        self.taskList.append(self.task)
        self.task.addEffort(effort.Effort(self.task))
        self.assertEqual(self.task.trackStartEventType(), self.viewer.events[0].type())

    def testChangeStartDateWhileColumnNotShown(self):
        self.taskList.append(self.task)
        self.showColumn('startDate', False)
        self.task.setStartDate(date.Yesterday())
        self.assertEqual(1, len(self.viewer.events))

    def testChangeDueDate(self):
        self.taskList.append(self.task)
        self.task.setDueDate(date.Today())
        self.assertEqual('task.dueDate', self.viewer.events[0].type())

    def testChangeCompletionDateWhileColumnNotShown(self):
        self.taskList.append(self.task)
        self.task.setCompletionDate(date.Today())
        # We still get an event for the subject column:
        self.assertEqual('task.completionDate', self.viewer.events[0].type())

    def testChangeCompletionDateWhileColumnShown(self):
        self.taskList.append(self.task)
        self.showColumn('completionDate')
        self.task.setCompletionDate(date.Today())
        self.assertEqual('task.completionDate', self.viewer.events[0].type())

    def testChangePriorityWhileColumnNotShown(self):
        self.taskList.append(self.task)
        self.task.setPriority(10)
        self.failIf(self.viewer.events)

    def testChangePriorityWhileColumnShown(self):
        self.taskList.append(self.task)
        self.showColumn('priority')
        self.task.setPriority(10)
        self.assertEqual('task.priority', self.viewer.events[0].type())

    def testChangeTotalPriorityWhileColumnNotShown(self):
        self.taskList.append(self.task)
        self.task.addChild(self.child)
        self.child.setPriority(10)
        self.failIf(self.viewer.events)

    def testChangeTotalPriorityWhileColumnShown(self):
        self.showColumn('totalPriority')
        self.task.addChild(self.child)
        self.taskList.append(self.task)
        self.child.setPriority(10)
        self.assertEqual('task.totalPriority', self.viewer.events[0].type())
        
    def testChangeHourlyFeeWhileColumnShown(self):
        self.showColumn('hourlyFee')
        self.taskList.append(self.task)
        self.task.setHourlyFee(100)
        self.assertEqual(render.monetaryAmount(100.), self.getItemText(0, 3))
        
    def testChangeFixedFeeWhileColumnShown(self):
        self.showColumn('fixedFee')
        self.taskList.append(self.task)
        self.task.setFixedFee(200)
        self.assertEqual(render.monetaryAmount(200.), self.getItemText(0, 3))

    def testChangeTotalFixedFeeWhileColumnShown(self):
        self.showColumn('totalFixedFee')
        self.taskList.append(self.task)
        self.taskList.append(self.child)
        self.task.addChild(self.child)
        self.task.setFixedFee(100)
        self.child.setFixedFee(200)
        self.viewer.setSortOrderAscending(False)
        self.assertEqual(render.monetaryAmount(300.), self.getItemText(0, 3))
        
    # Test all attributes...


class TaskViewerInTreeModeTest(CommonTestsMixin, ColumnsTestsMixin, 
                               TreeOrListModeTestsMixin, TaskViewerTestCase):
    treeMode = True


class TaskViewerInListModeTest(CommonTestsMixin, ColumnsTestsMixin, 
                               TreeOrListModeTestsMixin, TaskViewerTestCase):
    treeMode = False
        

