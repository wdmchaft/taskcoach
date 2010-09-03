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
from taskcoachlib.domain import category, task


class CategoryContainerTest(test.TestCase):
    def setUp(self):
        self.categories = category.CategoryList()
        self.category = category.Category('category 1')
                
    def testAddExistingCategory_WithoutTasks(self):
        self.categories.append(self.category)
        self.categories.append(category.Category(self.category.subject()))
        self.assertEqual(2, len(self.categories))
        
    def testRemoveCategoryWithTask(self):
        aTask = task.Task()
        self.categories.append(self.category)
        self.category.addCategorizable(aTask)
        aTask.addCategory(self.category)
        self.categories.removeItems([self.category])
        self.failIf(aTask.categories())
