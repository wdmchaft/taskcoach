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

import xml.dom, os
from taskcoachlib import meta
from taskcoachlib.domain import date, task, note, category


class XMLWriter(object):
    def __init__(self, fd, versionnr=meta.data.tskversion):
        self.__fd = fd
        self.__versionnr = versionnr

    def write(self, taskList, categoryContainer,
              noteContainer, syncMLConfig, guid):
        domImplementation = xml.dom.getDOMImplementation()
        self.document = domImplementation.createDocument(None, 'tasks', None) # pylint: disable-msg=W0201
        pi = self.document.createProcessingInstruction('taskcoach', 
            'release="%s" tskversion="%d"'%(meta.data.version, 
            self.__versionnr))
        self.document.insertBefore(pi, self.document.documentElement)
        for rootTask in taskList.rootItems():
            self.document.documentElement.appendChild(self.taskNode(rootTask))
        for rootCategory in categoryContainer.rootItems():
            self.document.documentElement.appendChild(self.categoryNode(rootCategory, taskList, noteContainer))
        for rootNote in noteContainer.rootItems():
            self.document.documentElement.appendChild(self.noteNode(rootNote))
        if syncMLConfig:
            self.document.documentElement.appendChild(self.syncMLNode(syncMLConfig))
        if guid:
            self.document.documentElement.appendChild(self.textNode('guid', guid))
        self.document.writexml(self.__fd, newl='\n')

    def taskNode(self, task): # pylint: disable-msg=W0621
        node = self.baseCompositeNode(task, 'task', self.taskNode)
        node.setAttribute('status', str(task.getStatus()))
        if task.startDateTime() != date.DateTime():
            node.setAttribute('startdate', str(task.startDateTime()))
        if task.dueDateTime() != date.DateTime():
            node.setAttribute('duedate', str(task.dueDateTime()))
        if task.completionDateTime() != date.DateTime():
            node.setAttribute('completiondate', str(task.completionDateTime()))
        if task.percentageComplete() != 0:
            node.setAttribute('percentageComplete', str(task.percentageComplete()))
        if task.recurrence():
            node.appendChild(self.recurrenceNode(task.recurrence()))
        if task.budget() != date.TimeDelta():
            node.setAttribute('budget', self.budgetAsAttribute(task.budget()))
        if task.priority() != 0:
            node.setAttribute('priority', str(task.priority()))
        if task.hourlyFee() != 0:
            node.setAttribute('hourlyFee', str(task.hourlyFee()))
        if task.fixedFee() != 0:
            node.setAttribute('fixedFee', str(task.fixedFee()))
        if task.reminder() != None:
            node.setAttribute('reminder', str(task.reminder()))
        prerequisiteIds = ' '.join([prerequisite.id() for prerequisite in \
            task.prerequisites()])
        if prerequisiteIds:            
            node.setAttribute('prerequisites', prerequisiteIds)
        if task.shouldMarkCompletedWhenAllChildrenCompleted() != None:
            node.setAttribute('shouldMarkCompletedWhenAllChildrenCompleted', 
                              str(task.shouldMarkCompletedWhenAllChildrenCompleted()))
        for effort in task.efforts():
            node.appendChild(self.effortNode(effort))
        for eachNote in task.notes():
            node.appendChild(self.noteNode(eachNote))
        for attachment in task.attachments():
            node.appendChild(self.attachmentNode(attachment))
        return node

    def recurrenceNode(self, recurrence):
        node = self.document.createElement('recurrence')
        node.setAttribute('unit', recurrence.unit)
        if recurrence.amount > 1:
            node.setAttribute('amount', str(recurrence.amount))
        if recurrence.count > 0:
            node.setAttribute('count', str(recurrence.count))
        if recurrence.max > 0:
            node.setAttribute('max', str(recurrence.max))
        if recurrence.sameWeekday:
            node.setAttribute('sameWeekday', 'True')
        return node

    def effortNode(self, effort):
        node = self.document.createElement('effort')
        formattedStart = self.formatDateTime(effort.getStart())
        node.setAttribute('id', effort.id())
        node.setAttribute('status', str(effort.getStatus()))
        node.setAttribute('start', formattedStart)
        stop = effort.getStop()
        if stop != None:
            formattedStop = self.formatDateTime(stop)
            if formattedStop == formattedStart:
                # Make sure the effort duration is at least one second
                formattedStop = self.formatDateTime(stop + date.TimeDelta(seconds=1))
            node.setAttribute('stop', formattedStop)
        if effort.description():
            node.appendChild(self.textNode('description', effort.description()))
        return node
    
    def categoryNode(self, category, *categorizableContainers): # pylint: disable-msg=W0621
        def inCategorizableContainer(categorizable):
            for container in categorizableContainers:
                if categorizable in container:
                    return True
            return False
        node = self.baseCompositeNode(category, 'category', self.categoryNode, 
                                      categorizableContainers)
        if category.isFiltered():
            node.setAttribute('filtered', str(category.isFiltered()))
        if category.hasExclusiveSubcategories():
            node.setAttribute('exclusiveSubcategories', str(category.hasExclusiveSubcategories()))
        for eachNote in category.notes():
            node.appendChild(self.noteNode(eachNote))
        for attachment in category.attachments():
            node.appendChild(self.attachmentNode(attachment))
        # Make sure the categorizables referenced are actually in the 
        # categorizableContainer, i.e. they are not deleted
        categorizableIds = ' '.join([categorizable.id() for categorizable in \
            category.categorizables() if inCategorizableContainer(categorizable)])
        if categorizableIds:            
            node.setAttribute('categorizables', categorizableIds)
        return node
    
    def noteNode(self, note): # pylint: disable-msg=W0621
        node = self.baseCompositeNode(note, 'note', self.noteNode)
        for attachment in note.attachments():
            node.appendChild(self.attachmentNode(attachment))
        return node

    def __baseNode(self, item, nodeName):
        node = self.document.createElement(nodeName)
        node.setAttribute('id', item.id())
        node.setAttribute('status', str(item.getStatus()))
        if item.subject():
            node.setAttribute('subject', item.subject())
        if item.description():
            node.appendChild(self.textNode('description', item.description()))
        return node

    def baseNode(self, item, nodeName):
        ''' Create a node and add the attributes that all domain
            objects share, such as id, subject, description. '''
        node = self.__baseNode(item, nodeName)
        if item.foregroundColor():
            node.setAttribute('fgColor', str(item.foregroundColor()))
        if item.backgroundColor():
            node.setAttribute('bgColor', str(item.backgroundColor()))
        if item.font():
            node.setAttribute('font', unicode(item.font().GetNativeFontInfoDesc()))
        if item.icon():
            node.setAttribute('icon', str(item.icon()))
        if item.selectedIcon():
            node.setAttribute('selectedIcon', str(item.selectedIcon()))
        return node

    def baseCompositeNode(self, item, nodeName, childNodeFactory, childNodeFactoryArgs=()):
        ''' Same as baseNode, but also create child nodes by means of
            the childNodeFactory. '''
        node = self.__baseNode(item, nodeName)
        if item.foregroundColor(recursive=False):
            node.setAttribute('fgColor', str(item.foregroundColor(recursive=False)))
        if item.backgroundColor(recursive=False):
            node.setAttribute('bgColor', str(item.backgroundColor(recursive=False)))
        if item.font(recursive=False):
            node.setAttribute('font', unicode(item.font(recursive=False).GetNativeFontInfoDesc()))
        if item.icon(recursive=False):
            node.setAttribute('icon', str(item.icon(recursive=False)))
        if item.selectedIcon(recursive=False):
            node.setAttribute('selectedIcon', str(item.selectedIcon(recursive=False)))
        if item.expandedContexts():
            node.setAttribute('expandedContexts', 
                              str(tuple(sorted(item.expandedContexts()))))
        for child in item.children():
            node.appendChild(childNodeFactory(child, *childNodeFactoryArgs)) # pylint: disable-msg=W0142
        return node

    def attachmentNode(self, attachment):
        node = self.baseNode(attachment, 'attachment')
        node.setAttribute('type', attachment.type_)
        data = attachment.data()
        if data is None:
            node.setAttribute('location', attachment.location())
        else:
            dataNode = self.textNode('data', data.encode('base64'))
            dataNode.setAttribute('extension',
                                  os.path.splitext(attachment.location())[-1])
            node.appendChild(dataNode)
        for eachNote in attachment.notes():
            node.appendChild(self.noteNode(eachNote))
        return node

    def syncMLNode(self, syncMLConfig):
        node = self.document.createElement('syncmlconfig')
        self.__syncMLNode(syncMLConfig, node)
        return node

    def __syncMLNode(self, cfg, node):
        for name, value in cfg.properties():
            child = self.textNode('property', value)
            child.setAttribute('name', name)
            node.appendChild(child)

        for childCfg in cfg.children():
            child = self.document.createElement(childCfg.name)
            self.__syncMLNode(childCfg, child)
            node.appendChild(child)

    def budgetAsAttribute(self, budget):
        return '%d:%02d:%02d'%budget.hoursMinutesSeconds()
                
    def textNode(self, nodeName, text):
        node = self.document.createElement(nodeName)
        textNode = self.document.createTextNode(text)
        node.appendChild(textNode)
        return node

    def formatDateTime(self, dateTime):
        return dateTime.strftime('%Y-%m-%d %H:%M:%S')


class TemplateXMLWriter(XMLWriter):
    def write(self, tsk): # pylint: disable-msg=W0221
        super(TemplateXMLWriter, self).write(task.TaskList([tsk]),
                   category.CategoryList(),
                   note.NoteContainer(),
                   None, None)

    def taskNode(self, task): # pylint: disable-msg=W0621
        node = super(TemplateXMLWriter, self).taskNode(task)

        for name, getter in [('startdate', 'startDateTime'),
                             ('duedate', 'dueDateTime'),
                             ('completiondate', 'completionDateTime'),
                             ('reminder', 'reminder')]:
            dateTime = getattr(task, getter)()
            if dateTime not in (None, date.DateTime()):
                node.removeAttribute(name)
                delta = dateTime - date.Now()
                node.setAttribute(name + 'tmpl', 'Now() + %s' % repr(delta))

        return node
