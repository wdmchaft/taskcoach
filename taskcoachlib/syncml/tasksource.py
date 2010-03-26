'''
Task Coach - Your friendly task manager
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2009 Frank Niessink <frank@niessink.com>

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

from taskcoachlib.syncml import basesource
from taskcoachlib.domain.task import Task
from taskcoachlib.domain.category import Category
from taskcoachlib.persistence.icalendar import ical

from taskcoachlib.i18n import _

import wx, inspect

class TaskSource(basesource.BaseSource):
    CONFLICT_STARTDATE        = 0x01
    CONFLICT_DUEDATE          = 0x02
    CONFLICT_DESCRIPTION      = 0x04
    CONFLICT_SUBJECT          = 0x08
    CONFLICT_PRIORITY         = 0x10
    CONFLICT_CATEGORIES       = 0x20
    CONFLICT_COMPLETIONDATE   = 0x40

    def __init__(self, callback, taskList, categoryList, *args, **kwargs):
        super(TaskSource, self).__init__(callback, taskList, *args, **kwargs)

        self.categoryList = categoryList

    def updateItemProperties(self, item, task):
        item.data = 'BEGIN:VCALENDAR\r\nVERSION: 1.0\r\n' + \
                    vcal.VCalFromTask(task) + \
                    'END:VCALENDAR'
        item.dataType = 'text/x-vcalendar'

    def compareItemProperties(self, local, remote):
        result = 0

        if local.startDate() != remote.startDate():
            result |= self.CONFLICT_STARTDATE
        if local.dueDate() != remote.dueDate():
            result |= self.CONFLICT_DUEDATE
        if local.description() != remote.description():
            result |= self.CONFLICT_DESCRIPTION
        if local.subject() != remote.subject():
            result |= self.CONFLICT_SUBJECT
        if local.priority() != remote.priority():
            result |= self.CONFLICT_PRIORITY
        if local.completionDate() != remote.completionDate():
            result |= self.CONFLICT_COMPLETIONDATE

        localCategories = map(unicode, local.categories(True))
        remoteCategories = map(unicode, remote.categories())

        localCategories.sort()
        remoteCategories.sort()

        if localCategories != remoteCategories:
            result |= self.CONFLICT_CATEGORIES

        return result

    def _parseObject(self, item):
        parser = ical.VCalendarParser()
        parser.parse(map(lambda x: x.rstrip('\r'), item.data.split('\n')))

        categories = parser.tasks[0].pop('categories', [])

        kwargs = dict([(k, v) for k, v in parser.tasks[0].items() if k in inspect.getargspec(Task.__init__)[0]])
        task = Task(**kwargs)

        for category in categories:
            categoryObject = self.categoryList.findCategoryByName(category)
            if categoryObject is None:
                categoryObject = Category(category)
                self.categoryList.extend([categoryObject])
            task.addCategory(categoryObject)

        return task

    def doAddItem(self, task):
        for category in task.categories():
            category.addCategorizable(task)

        return 201

    def doUpdateItem(self, task, local):
        local.setStartDate(task.startDate())
        local.setDueDate(task.dueDate())
        local.setDescription(task.description())
        local.setSubject(task.subject())
        local.setPriority(task.priority())
        local.setCompletionDate(task.completionDate())

        for category in local.categories():
            category.removeCategorizable(local)

        local.setCategories(task.categories())

        for category in local.categories():
            category.addCategorizable(local)

        return 200 # FIXME

    def doResolveConflict(self, task, local, result):
        resolved = self.callback.resolveTaskConflict(result, local, task)

        if resolved.has_key('subject'):
            local.setSubject(resolved['subject'])
        if resolved.has_key('description'):
            local.setDescription(resolved['description'])
        if resolved.has_key('startDate'):
            local.setStartDate(resolved['startDate'])
        if resolved.has_key('dueDate'):
            local.setDueDate(resolved['dueDate'])
        if resolved.has_key('priority'):
            local.setPriority(resolved['priority'])
        if resolved.has_key('completionDate'):
            local.setCompletionDate(resolved['completionDate'])
        if resolved.has_key('categories'):
            # Ahah,      tricky       part.      This      is      why
            # callback.resolvedXXXConflict return dictionaries instead
            # of Task object.

            for category in local.categories().copy():
                category.removeCategorizable(local)
                local.removeCategory(category)

            for category in resolved['categories'].split(','):
                categoryObject = self.categoryList.findCategoryByName(category)
                if categoryObject is None:
                    categoryObject = Category(category)
                    self.categoryList.extend([categoryObject])
                local.addCategory(categoryObject)

            for category in local.categories():
                category.addCategorizable(local)

        return local

    def objectRemovedOnServer(self, task):
        return wx.MessageBox(_('Task "%s" has been deleted on server,\n') % task.subject() + \
                             _('but locally modified. Should I keep the local version?'),
                             _('Synchronization conflict'), wx.YES_NO) == wx.YES

    def objectRemovedOnClient(self, task):
        return wx.MessageBox(_('Task "%s" has been locally deleted,\n') % task.subject() + \
                             _('but modified on server. Should I keep the remote version?'),
                             _('Synchronization conflict'), wx.YES_NO) == wx.YES
