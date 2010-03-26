'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>

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
from taskcoachlib import config
from taskcoachlib.domain import task, effort, date


class DummyTaskList(task.TaskList):
    def __init__(self, *args, **kwargs):
        self.treeMode = 'not set'
        super(DummyTaskList, self).__init__(*args, **kwargs)
        
    def setTreeMode(self, treeMode):
        self.treeMode = treeMode


class TaskSorterTest(test.TestCase):
    def setUp(self):
        a = self.a = task.Task('a')
        b = self.b = task.Task('b')
        c = self.c = task.Task('c')
        d = self.d = task.Task('d')
        self.list = task.TaskList([d, b, c, a])
        self.sorter = task.sorter.Sorter(self.list)

    def testInitiallyEmpty(self):
        sorter = task.sorter.Sorter(task.TaskList())
        self.assertEqual(0, len(sorter))

    def testLength(self):
        self.assertEqual(4, len(self.sorter))

    def testGetItem(self):
        self.assertEqual(self.a, self.sorter[0])

    def testOrder(self):
        self.assertEqual([self.a, self.b, self.c, self.d], list(self.sorter))

    def testRemoveItem(self):
        self.sorter.remove(self.c)
        self.assertEqual([self.a, self.b, self.d], list(self.sorter))
        self.assertEqual(3, len(self.list))

    def testAppend(self):
        e = task.Task('e')
        self.list.append(e)
        self.assertEqual(5, len(self.sorter))
        self.assertEqual(e, self.sorter[-1])

    def testChange(self):
        self.a.setSubject('z')
        self.assertEqual([self.b, self.c, self.d, self.a], list(self.sorter))


class TaskSorterSettingsTest(test.TestCase):        
    def setUp(self):
        self.taskList = task.TaskList()
        self.sorter = task.sorter.Sorter(self.taskList)        
        self.task1 = task.Task(subject='A', dueDate=date.Tomorrow())
        self.task2 = task.Task(subject='B', dueDate=date.Today())
        self.taskList.extend([self.task1, self.task2])

    def testSortDueDate(self):
        self.sorter.sortBy('dueDate')
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        
    def testSortBySubject(self):
        self.sorter.sortBy('subject')
        self.assertEqual([self.task1, self.task2], list(self.sorter))
        
    def testSortBySubject_TurnOff(self):
        self.sorter.sortBy('subject')
        self.sorter.sortBy('dueDate')
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        
    def testSortByCompletionStatus(self):
        self.task2.setCompletionDate(date.Today())
        self.assertEqual([self.task1, self.task2], list(self.sorter))
        
    def testSortByInactiveStatus(self):
        self.task2.setStartDate(date.Tomorrow())
        self.assertEqual([self.task1, self.task2], list(self.sorter))
    
    def testSortBySubjectDescending(self):
        self.sorter.sortBy('subject')
        self.sorter.sortAscending(False)
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        
    def testSortByStartDate(self):
        self.sorter.sortBy('startDate')
        self.task1.setDueDate(date.Yesterday())
        self.task2.setStartDate(date.Yesterday())
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        
    def testDescending(self):
        self.sorter.sortBy('dueDate')
        self.sorter.sortAscending(False)
        self.assertEqual([self.task1, self.task2], list(self.sorter))
        
    def testByDueDateWithoutFirstSortingByStatus(self):
        self.sorter.sortBy('dueDate')
        self.sorter.sortByTaskStatusFirst(False)
        self.task2.setCompletionDate(date.Today())
        self.assertEqual([self.task2, self.task1], list(self.sorter))

    def testSortBySubjectWithFirstSortingByStatus(self):
        self.sorter.sortByTaskStatusFirst(True)
        self.sorter.sortBy('subject')
        self.task1.setCompletionDate(date.Today())
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        
    def testSortBySubjectWithoutFirstSortingByStatus(self):
        self.sorter.sortByTaskStatusFirst(False)
        self.sorter.sortBy('subject')
        self.task1.setCompletionDate(date.Today())
        self.assertEqual([self.task1, self.task2], list(self.sorter))
                
    def testSortCaseSensitive(self):
        self.sorter.sortCaseSensitive(True)
        self.sorter.sortBy('subject')
        task3 = task.Task('a')
        self.taskList.append(task3)
        self.assertEqual([self.task1, self.task2, task3], list(self.sorter))

    def testSortCaseInsensitive(self):
        self.sorter.sortCaseSensitive(False)
        self.sorter.sortBy('subject')
        task3 = task.Task('a')
        self.taskList.append(task3)
        self.assertEqual([self.task1, task3, self.task2], list(self.sorter))
    
    def testSortByTotalTimeLeftAscending(self):
        self.sorter.sortAscending(True)
        self.sorter.sortBy('totaltimeLeft')
        self.assertEqual([self.task2, self.task1], list(self.sorter))

    def testSortByTotalTimeLeftDescending(self):
        self.sorter.sortAscending(False)
        self.sorter.sortBy('totaltimeLeft')
        self.assertEqual([self.task1, self.task2], list(self.sorter))

    def testSortByBudgetAscending(self):
        self.sorter.sortAscending(True)
        self.sorter.sortBy('budget')
        self.task1.setBudget(date.TimeDelta(100))
        self.assertEqual([self.task2, self.task1], list(self.sorter))

    def testSortByBudgetDescending(self):
        self.sorter.sortAscending(False)
        self.sorter.sortBy('budget')
        self.task1.setBudget(date.TimeDelta(100))
        self.assertEqual([self.task1, self.task2], list(self.sorter))

    def testSortByTimeSpentAscending(self):
        self.sorter.sortAscending(True)
        self.sorter.sortBy('timeSpent')
        self.task1.addEffort(effort.Effort(self.task1,
            date.DateTime(2005,1,1,10,0,0), date.DateTime(2005,1,1,11,0,0)))
        self.assertEqual([self.task2, self.task1], list(self.sorter))

    def testSortByTimeSpentDescending(self):
        self.sorter.sortAscending(False)
        self.sorter.sortBy('timeSpent')
        self.task1.addEffort(effort.Effort(self.task1,
            date.DateTime(2005,1,1,10,0,0), date.DateTime(2005,1,1,11,0,0)))
        self.assertEqual([self.task1, self.task2], list(self.sorter))

    def testAlwaysKeepSubscriptionToCompletionDate(self):
        ''' TaskSorter should keep a subscription to task.completionDate 
            even when the completion date is not the sort key, because sorting
            on task status (active, completed, etc.) depends on the completion
            date. '''
        self.sorter.sortBy('completionDate')
        self.sorter.sortBy('subject')
        self.task1.setCompletionDate()
        self.assertEqual([self.task2, self.task1], list(self.sorter))

    def testAlwaysKeepSubscriptionToStartDate(self):
        ''' TaskSorter should keep a subscription to task.startDate 
            even when the start date is not the sort key, because sorting
            on task status (active, completed, etc.) depends on the start
            date. '''
        self.sorter.sortBy('startDate')
        self.sorter.sortBy('subject')
        self.task1.setStartDate(date.Tomorrow())
        self.assertEqual([self.task2, self.task1], list(self.sorter))
        

class TaskSorterTreeModeTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.taskList = DummyTaskList()
        self.sorter = task.sorter.Sorter(self.taskList, treeMode=True)        
        self.parent1 = task.Task(subject='parent 1')
        self.child1 = task.Task(subject='child 1')
        self.parent1.addChild(self.child1)
        self.parent2 = task.Task(subject='parent 2')
        self.child2 = task.Task(subject='child 2')
        self.parent2.addChild(self.child2)
        self.taskList.extend([self.parent1, self.parent2])

    def testDefaultSortOrder(self):
        self.assertEqual([self.parent1, self.child1, self.parent2, self.child2],
            list(self.sorter))
        
    def testSortByDueDate(self):
        self.sorter.sortBy('dueDate')
        self.child2.setDueDate(date.Today())
        self.failUnless(list(self.sorter).index(self.parent2) < \
            list(self.sorter).index(self.parent1))

    def testSortByPriority(self):
        self.sorter.sortBy('priority')
        self.sorter.sortAscending(False)
        self.parent1.setPriority(5)
        self.child2.setPriority(10)
        self.failUnless(list(self.sorter).index(self.parent1) < \
            list(self.sorter).index(self.parent2))

    def testSortByTotalPriority(self):
        self.sorter.sortBy('totalpriority')
        self.sorter.sortAscending(False)
        self.parent1.setPriority(5)
        self.child2.setPriority(10)
        self.failUnless(list(self.sorter).index(self.parent2) < \
            list(self.sorter).index(self.parent1))
        
    def testSetSorterToListMode(self):
        self.sorter.setTreeMode(False)
        self.assertEqual([self.child1, self.child2, self.parent1, self.parent2],
            list(self.sorter))

    def testTreeModeDelegation_True(self):
        self.sorter.setTreeMode(True)
        self.assertEqual(True, self.taskList.treeMode)
        
    def testTreeModeDelegation_False(self):
        self.sorter.setTreeMode(False)
        self.assertEqual(False, self.taskList.treeMode)

        
            
class EffortSorterTest(test.TestCase):
    def setUp(self):
        task.Task.settings = config.Settings(load=False)
        self.taskList = task.TaskList()
        self.effortList = effort.EffortList(self.taskList)
        self.sorter = effort.EffortSorter(self.effortList)
        self.task = task.Task('Task')
        self.oldestEffort = effort.Effort(self.task,
            date.DateTime(2004,1,1), date.DateTime(2004,1,2))
        self.newestEffort = effort.Effort(self.task,
            date.DateTime(2004,2,1), date.DateTime(2004,2,2))
        self.task.addEffort(self.oldestEffort)
        self.task.addEffort(self.newestEffort)
        self.taskList.append(self.task)

    def testDescending(self):
        self.assertEqual([self.newestEffort, self.oldestEffort], self.sorter)

    def testResort(self):
        self.oldestEffort.setStart(date.DateTime(2004,3,1))
        self.assertEqual([self.oldestEffort, self.newestEffort], self.sorter)

    def testCreateWhenEffortListIsFilled(self):
        sorter = effort.EffortSorter(self.effortList)
        self.assertEqual([self.newestEffort, self.oldestEffort], sorter)

    def testAddEffort(self):
        evenNewerEffort = effort.Effort(self.task,
            date.DateTime(2005,1,1), date.DateTime(2005,1,2))
        self.task.addEffort(evenNewerEffort)
        self.assertEqual([evenNewerEffort, self.newestEffort, 
            self.oldestEffort], self.sorter)
        
    def testTaskEffortComesBeforeChildEffort(self):
        child = task.Task('Child')
        child.setParent(self.task)
        self.task.addChild(child)
        self.taskList.append(child)
        childEffort = effort.Effort(child, date.DateTime(2004,1,1), 
                                      date.DateTime(2008,1,2))
        child.addEffort(childEffort)
        self.assertEqual([self.newestEffort, childEffort, self.oldestEffort],
            self.sorter)

