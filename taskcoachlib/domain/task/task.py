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

import wx
from taskcoachlib import patterns
from taskcoachlib.domain import base, date, categorizable, note, attachment
from taskcoachlib.domain.attribute import color


class Task(note.NoteOwner, attachment.AttachmentOwner, 
           categorizable.CategorizableCompositeObject):
    
    def __init__(self, subject='', description='', 
                 dueDateTime=None, startDateTime=None, completionDateTime=None,
                 budget=None, priority=0, id=None, hourlyFee=0, # pylint: disable-msg=W0622
                 fixedFee=0, reminder=None, categories=None,
                 efforts=None, shouldMarkCompletedWhenAllChildrenCompleted=None, 
                 recurrence=None, percentageComplete=0, prerequisites=None,
                 dependencies=None, *args, **kwargs):
        kwargs['id'] = id
        kwargs['subject'] = subject
        kwargs['description'] = description
        kwargs['categories'] = categories
        super(Task, self).__init__(*args, **kwargs)
        self.__dueDateTime = base.Attribute(dueDateTime or date.DateTime(), self, 
                                            self.dueDateTimeEvent)
        self.__startDateTime = base.Attribute(startDateTime or date.DateTime(), self, 
                                              self.startDateTimeEvent)
        self.__completionDateTime = base.Attribute(completionDateTime or date.DateTime(), 
                                                   self, self.completionDateTimeEvent)
        percentageComplete = 100 if self.__completionDateTime.get() != date.DateTime() else percentageComplete
        self.__percentageComplete = base.Attribute(percentageComplete, 
                                                   self, self.percentageCompleteEvent)
        self.__budget = base.Attribute(budget or date.TimeDelta(), self, 
                                       self.budgetEvent)
        self._efforts = efforts or []
        self.__priority = base.Attribute(priority, self, self.priorityEvent)
        self.__hourlyFee = base.Attribute(hourlyFee, self, self.hourlyFeeEvent)
        self.__fixedFee = base.Attribute(fixedFee, self, self.fixedFeeEvent)
        self.__reminder = base.Attribute(reminder, self, self.reminderEvent)
        self._recurrence = date.Recurrence() if recurrence is None else recurrence
        self.__prerequisites = base.SetAttribute(prerequisites or [], self, 
                                                 changeEvent=self.prerequisitesEvent)
        self.__dependencies = base.SetAttribute(dependencies or [], self, 
                                                changeEvent=self.dependenciesEvent)
        self._shouldMarkCompletedWhenAllChildrenCompleted = \
            shouldMarkCompletedWhenAllChildrenCompleted
        for effort in self._efforts:
            effort.setTask(self)
        for eventType in 'active', 'inactive', 'completed', 'duesoon', 'overdue':
            patterns.Publisher().registerObserver(self.__computeRecursiveForegroundColor, 'color.%stasks')
            
    @patterns.eventSource
    def __setstate__(self, state, event=None):
        super(Task, self).__setstate__(state, event=event)
        self.setStartDateTime(state['startDateTime'], event=event)
        self.setDueDateTime(state['dueDateTime'], event=event)
        self.setCompletionDateTime(state['completionDateTime'], event=event)
        self.setPercentageComplete(state['percentageComplete'], event=event)
        self.setRecurrence(state['recurrence'], event=event)
        self.setReminder(state['reminder'], event=event)
        self.setEfforts(state['efforts'], event=event)
        self.setBudget(state['budget'], event=event)
        self.setPriority(state['priority'], event=event)
        self.setHourlyFee(state['hourlyFee'], event=event)
        self.setFixedFee(state['fixedFee'], event=event)
        self.setPrerequisites(state['prerequisites'], event=event)
        self.setDependencies(state['dependencies'], event=event)
        self.setShouldMarkCompletedWhenAllChildrenCompleted( \
            state['shouldMarkCompletedWhenAllChildrenCompleted'], event=event)
        
    def __getstate__(self):
        state = super(Task, self).__getstate__()
        state.update(dict(dueDateTime=self.__dueDateTime.get(), 
            startDateTime=self.__startDateTime.get(),  
            completionDateTime=self.__completionDateTime.get(),
            percentageComplete=self.__percentageComplete.get(),
            children=self.children(), parent=self.parent(), 
            efforts=self._efforts, budget=self.__budget.get(), 
            priority=self.__priority.get(), 
            hourlyFee=self.__hourlyFee.get(), fixedFee=self.__fixedFee.get(), 
            recurrence=self._recurrence.copy(),
            reminder=self.__reminder.get(),
            prerequisites=self.__prerequisites.get(),
            dependencies=self.__dependencies.get(),
            shouldMarkCompletedWhenAllChildrenCompleted=\
                self._shouldMarkCompletedWhenAllChildrenCompleted))
        return state

    def __getcopystate__(self):
        state = super(Task, self).__getcopystate__()
        state.update(dict(dueDateTime=self.__dueDateTime.get(), 
            startDateTime=self.__startDateTime.get(), 
            completionDateTime=self.__completionDateTime.get(),
            percentageComplete=self.__percentageComplete.get(), 
            efforts=[effort.copy() for effort in self._efforts], 
            budget=self.__budget.get(), priority=self.__priority.get(), 
            hourlyFee=self.__hourlyFee.get(), fixedFee=self.__fixedFee.get(), 
            recurrence=self._recurrence.copy(),
            reminder=self.__reminder.get(), 
            shouldMarkCompletedWhenAllChildrenCompleted=\
                self._shouldMarkCompletedWhenAllChildrenCompleted))
        return state

    def allChildrenCompleted(self):
        ''' Return whether all children (non-recursively) are completed. '''
        children = self.children()
        return all(child.completed() for child in children) if children \
            else False        

    def newChild(self, subject='New subtask'): # pylint: disable-msg=W0221
        ''' Subtask constructor '''
        return super(Task, self).newChild(subject=subject, 
            dueDateTime=self.dueDateTime(), 
            startDateTime=max(date.Now(), self.startDateTime()), parent=self)

    @patterns.eventSource
    def addChild(self, child, event=None):
        if child in self.children():
            return
        super(Task, self).addChild(child, event=event)
        self.childChangeEvent(child, event)
        if self.shouldBeMarkedCompleted():
            self.setCompletionDateTime(child.completionDateTime(), event=event)
        elif self.completed() and not child.completed():
            self.setCompletionDateTime(date.DateTime(), event=event)
        if child.dueDateTime() > self.dueDateTime():
            self.setDueDateTime(child.dueDateTime(), event=event)           
        if child.startDateTime() < self.startDateTime():
            self.setStartDateTime(child.startDateTime(), event=event)

    @patterns.eventSource
    def removeChild(self, child, event=None):
        if child not in self.children():
            return
        super(Task, self).removeChild(child, event=event)
        self.childChangeEvent(child, event)    
        if self.shouldBeMarkedCompleted(): 
            # The removed child was the last uncompleted child
            self.setCompletionDateTime(date.Now(), event=event)
                    
    def childChangeEvent(self, child, event):
        childHasTimeSpent = child.timeSpent(recursive=True)
        childHasBudget = child.budget(recursive=True)
        childHasBudgetLeft = child.budgetLeft(recursive=True)
        childHasRevenue = child.revenue(recursive=True)
        childPriority = child.priority(recursive=True)
        # Determine what changes due to the child being added or removed:
        if childHasTimeSpent:
            self.timeSpentEvent(event, *child.efforts())
        if childHasRevenue:
            self.revenueEvent(event)
        if childHasBudget:
            self.budgetEvent(event)
        if childHasBudgetLeft or (childHasTimeSpent and \
                                  (childHasBudget or self.budget())):
            self.budgetLeftEvent(event)
        if childPriority > self.priority():
            self.priorityEvent(event)
        if child.isBeingTracked(recursive=True):
            activeEfforts = child.activeEfforts(recursive=True)
            if self.isBeingTracked(recursive=True):
                self.startTrackingEvent(event, *activeEfforts) # pylint: disable-msg=W0142
            else:
                self.stopTrackingEvent(event, *activeEfforts) # pylint: disable-msg=W0142
    
    @patterns.eventSource    
    def setSubject(self, subject, event=None):
        super(Task, self).setSubject(subject, event=event)
        # The subject of a dependency of our prerequisites has changed, notify:
        for prerequisite in self.prerequisites():
            event.addSource(prerequisite, subject, type='task.dependency.subject')
        # The subject of a prerequisite of our dependencies has changed, notify:
        for dependency in self.dependencies():
            event.addSource(dependency, subject, type='task.prerequisite.subject')

    # Due date
            
    def dueDateTime(self, recursive=False):
        if recursive:
            childrenDueDateTimes = [child.dueDateTime(recursive=True) for child in \
                                    self.children() if not child.completed()]
            return min(childrenDueDateTimes + [self.__dueDateTime.get()])
        else:
            return self.__dueDateTime.get()

    def setDueDateTime(self, dueDate, event=None):
        self.__dueDateTime.set(dueDate, event=event)
            
    def dueDateTimeEvent(self, event):
        dueDateTime = self.dueDateTime()
        event.addSource(self, dueDateTime, type='task.dueDateTime')
        for child in self.children():
            if child.dueDateTime() > dueDateTime:
                child.setDueDateTime(dueDateTime, event)
        if self.parent():
            parent = self.parent()
            if dueDateTime > parent.dueDateTime():
                parent.setDueDateTime(dueDateTime, event)
        self.recomputeAppearance()
    
    @staticmethod
    def dueDateTimeSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.dueDateTime(recursive=recursive)
    
    @classmethod
    def dueDateTimeSortEventTypes(class_):
        ''' The event types that influence the due date time sort order. '''
        return ('task.dueDateTime',)
    
    # Start date
    
    def startDateTime(self, recursive=False):
        if recursive:
            childrenStartDateTimes = [child.startDateTime(recursive=True) for child in \
                                      self.children() if not child.completed()]
            return min(childrenStartDateTimes + [self.__startDateTime.get()])
        else:
            return self.__startDateTime.get()

    def setStartDateTime(self, startDateTime, event=None):
        self.__startDateTime.set(startDateTime, event=event)
            
    def startDateTimeEvent(self, event):
        startDateTime = self.startDateTime()
        event.addSource(self, startDateTime, type='task.startDateTime')
        if not self.recurrence(recursive=True, upwards=True):
            for child in self.children():
                if startDateTime > child.startDateTime():
                    child.setStartDateTime(startDateTime, event)
            parent = self.parent()
            if parent and startDateTime < parent.startDateTime():
                parent.setStartDateTime(startDateTime, event)
        self.recomputeAppearance()
        
    @staticmethod
    def startDateTimeSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.startDateTime(recursive=recursive)
    
    @classmethod
    def startDateTimeSortEventTypes(class_):
        ''' The event types that influence the start date time sort order. '''
        return ('task.startDateTime',)

    def timeLeft(self, recursive=False):
        return self.dueDateTime(recursive) - date.Now()

    @staticmethod
    def timeLeftSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.timeLeft(recursive=recursive)
    
    @classmethod
    def timeLeftSortEventTypes(class_):
        ''' The event types that influence the time left sort order. '''
        return ('task.dueDateTime',)
                    
    # Completion date
            
    def completionDateTime(self, recursive=False):
        if recursive:
            childrenCompletionDateTimes = [child.completionDateTime(recursive=True) \
                for child in self.children() if child.completed()]
            return max(childrenCompletionDateTimes + [self.__completionDateTime.get()])
        else:
            return self.__completionDateTime.get()

    @patterns.eventSource
    def setCompletionDateTime(self, completionDateTime=None, event=None):
        completionDateTime = completionDateTime or date.Now()
        if completionDateTime == self.__completionDateTime.get():
            return
        if completionDateTime != date.DateTime() and self.recurrence():
            self.recur(event=event)
        else:
            parent = self.parent()
            if parent:
                oldParentPriority = parent.priority(recursive=True) 
            self.__completionDateTime.set(completionDateTime, event=event)
            if parent and parent.priority(recursive=True) != oldParentPriority:
                self.priorityEvent(event)              
            if completionDateTime != date.DateTime():
                self.setReminder(None, event)
            self.setPercentageComplete(100 if completionDateTime != date.DateTime() else 0, 
                                       event=event)
            if parent:
                if self.completed():
                    if parent.shouldBeMarkedCompleted():
                        parent.setCompletionDateTime(completionDateTime, event=event)
                else:
                    if parent.completed():
                        parent.setCompletionDateTime(date.DateTime(), event=event)
            if self.completed():
                for child in self.children():
                    if not child.completed():
                        child.setRecurrence(event=event)
                        child.setCompletionDateTime(completionDateTime, event=event)
                if self.isBeingTracked():
                    self.stopTracking(event=event)                    
        
    def completionDateTimeEvent(self, event):
        completionDateTime = self.completionDateTime()
        event.addSource(self, completionDateTime, type='task.completionDateTime')
        for task in [self] + list(self.dependencies()):
            task.recomputeAppearance()
        
    def shouldBeMarkedCompleted(self):
        ''' Return whether this task should be marked completed. It should be
            marked completed when 1) it's not completed, 2) all of its children
            are completed, 3) its setting says it should be completed when
            all of its children are completed. '''
        shouldMarkCompletedAccordingToSetting = \
            self.settings.getboolean('behavior', # pylint: disable-msg=E1101
                'markparentcompletedwhenallchildrencompleted')
        shouldMarkCompletedAccordingToTask = \
            self.shouldMarkCompletedWhenAllChildrenCompleted()
        return ((shouldMarkCompletedAccordingToTask == True) or \
                ((shouldMarkCompletedAccordingToTask == None) and \
                  shouldMarkCompletedAccordingToSetting)) and \
               (not self.completed()) and self.allChildrenCompleted()
      
    @staticmethod  
    def completionDateTimeSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.completionDateTime(recursive=recursive)

    @classmethod
    def completionDateTimeSortEventTypes(class_):
        ''' The event types that influence the completion date time sort order. '''
        return ('task.completionDateTime',)

    # Task state
    
    def completed(self):
        return self.completionDateTime() != date.DateTime()

    def overdue(self):
        return self.dueDateTime() < date.Now() and not self.completed()

    def inactive(self):
        if self.completed():
            return False # Completed tasks are never inactive
        if date.Now() < self.startDateTime() < date.DateTime():
            return True # Start at a specific future datetime, so inactive now
        if self.prerequisites():
            # We're inactive as long as not all prerequisites are completed
            return any([not prerequisite.completed() for prerequisite in self.prerequisites()])
        else:
            # We're inactive only if we have no startDateTime at all 
            return self.startDateTime() == date.DateTime()
        
    def active(self):
        return not self.inactive() and not self.completed()

    def dueSoon(self):
        hours = self.settings.getint('behavior', 'duesoonhours') # pylint: disable-msg=E1101
        return (0 <= self.timeLeft().hours() < hours and not self.completed())

   # effort related methods:

    def efforts(self, recursive=False):
        childEfforts = []
        if recursive:
            for child in self.children():
                childEfforts.extend(child.efforts(recursive=True))
        return self._efforts + childEfforts

    def isBeingTracked(self, recursive=False):
        return self.activeEfforts(recursive)

    def activeEfforts(self, recursive=False):
        return [effort for effort in self.efforts(recursive) \
            if effort.isBeingTracked()]
    
    @patterns.eventSource    
    def addEffort(self, effort, event=None):
        if effort in self._efforts:
            return
        wasTracking = self.isBeingTracked()
        self._efforts.append(effort)
        self.addEffortEvent(event, effort)
        if effort.isBeingTracked() and not wasTracking:
            self.startTrackingEvent(event, effort)
        self.timeSpentEvent(event, effort)
  
    def addEffortEvent(self, event, *efforts):
        event.addSource(self, *efforts, **dict(type='task.effort.add'))
          
    def startTrackingEvent(self, event, *efforts):    
        for ancestor in [self] + self.ancestors():
            event.addSource(ancestor, *efforts, 
                            **dict(type=ancestor.trackStartEventType()))

    @patterns.eventSource
    def removeEffort(self, effort, event=None):
        if effort not in self._efforts:
            return
        self._efforts.remove(effort)
        self.removeEffortEvent(event, effort)
        if effort.isBeingTracked() and not self.isBeingTracked():
            self.stopTrackingEvent(event, effort)
        self.timeSpentEvent(event, effort)
        
    def removeEffortEvent(self, event, *efforts):
        event.addSource(self, *efforts, **dict(type='task.effort.remove'))

    @patterns.eventSource
    def stopTracking(self, event=None):
        for effort in self.activeEfforts():
            effort.setStop(event=event)
                        
    def stopTrackingEvent(self, event, *efforts):
        for ancestor in [self] + self.ancestors():
            event.addSource(ancestor, *efforts, 
                            **dict(type=ancestor.trackStopEventType()))
        
    @patterns.eventSource
    def setEfforts(self, efforts, event=None):
        if efforts == self._efforts:
            return
        oldEfforts = self._efforts
        self._efforts = efforts
        self.removeEffortEvent(event, oldEfforts)
        self.addEffortEvent(event, efforts)

    @classmethod
    def trackStartEventType(class_):
        return '%s.track.start'%class_

    @classmethod
    def trackStopEventType(class_):
        return '%s.track.stop'%class_

    # Time spent
    
    def timeSpent(self, recursive=False):
        return sum((effort.duration() for effort in self.efforts(recursive)), 
                   date.TimeDelta())

    def timeSpentEvent(self, event, *efforts):
        event.addSource(self, *efforts, **dict(type='task.timeSpent'))
        for ancestor in self.ancestors():
            event.addSource(ancestor, *efforts, **dict(type='task.timeSpent'))
        if self.budget(recursive=True):
            self.budgetLeftEvent(event)
        if self.hourlyFee() > 0:
            self.revenueEvent(event)

    @staticmethod
    def timeSpentSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.timeSpent(recursive=recursive)
    
    @classmethod
    def timeSpentSortEventTypes(class_):
        ''' The event types that influence the time spent sort order. '''
        return ('task.timeSpent',)

    
    # Budget
    
    def budget(self, recursive=False):
        result = self.__budget.get()
        if recursive:
            for task in self.children():
                result += task.budget(recursive)
        return result
        
    def setBudget(self, budget, event=None):
        self.__budget.set(budget, event=event)
        
    def budgetEvent(self, event):
        event.addSource(self, self.budget(), type='task.budget')
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.budget(recursive=True), 
                            type='task.budget')
        self.budgetLeftEvent(event)
        
    @staticmethod
    def budgetSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.budget(recursive=recursive)
    
    @classmethod
    def budgetSortEventTypes(class_):
        ''' The event types that influence the budget sort order. '''
        return ('task.budget',)

    # Budget left
    
    def budgetLeft(self, recursive=False):
        budget = self.budget(recursive)
        return budget - self.timeSpent(recursive) if budget else budget

    def budgetLeftEvent(self, event):
        event.addSource(self, self.budgetLeft(), type='task.budgetLeft')
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.budgetLeft(recursive=True), 
                            type='task.budgetLeft')

    @staticmethod
    def budgetLeftSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.budgetLeft(recursive=recursive)

    @classmethod
    def budgetLeftSortEventTypes(class_):
        ''' The event types that influence the budget left sort order. '''
        return ('task.budgetLeft',)

    # Foreground color
    
    def foregroundColor(self, recursive=False):
        if not recursive:
            return super(Task, self).foregroundColor(recursive)
        try:
            return self.__recursiveForegroundColor
        except AttributeError:
            return self.__computeRecursiveForegroundColor()
        
    def __computeRecursiveForegroundColor(self, *args, **kwargs):
        fgColor = super(Task, self).foregroundColor(recursive=True)
        statusColor = self.statusColor()
        if statusColor == wx.BLACK:
            recursiveColor = fgColor
        elif fgColor == None:
            recursiveColor = statusColor
        else:
            recursiveColor = color.ColorMixer.mix((fgColor, statusColor))
        self.__recursiveForegroundColor = recursiveColor 
        return recursiveColor
    
    def statusColor(self):
        ''' Return the current color of task, based on its status (completed,
            overdue, duesoon, inactive, or active). '''
        if self.completed():
            status = 'completed'
        elif self.overdue(): 
            status = 'overdue'
        elif self.dueSoon():
            status = 'duesoon'
        elif self.inactive(): 
            status = 'inactive'
        else:
            status = 'active'
        return self.colorForStatus(status)
    
    @classmethod
    def colorForStatus(class_, status):
        return wx.Colour(*eval(class_.settings.get('color', '%stasks'%status))) # pylint: disable-msg=E1101
    
    def foregroundColorChangedEvent(self, event):
        super(Task, self).foregroundColorChangedEvent(event)
        fgColor = self.foregroundColor()
        for task in [self] + self.childrenWithoutOwnForegroundColor():
            for eachEffort in task.efforts():
                event.addSource(eachEffort, fgColor, 
                                type=eachEffort.foregroundColorChangedEventType())
        self.__computeRecursiveForegroundColor()
    
    # Background color
    
    def backgroundColorChangedEvent(self, event):
        super(Task, self).backgroundColorChangedEvent(event)
        bgColor = self.backgroundColor()
        for task in [self] + self.childrenWithoutOwnBackgroundColor():
            for eachEffort in task.efforts():
                event.addSource(eachEffort, bgColor, 
                                type=eachEffort.backgroundColorChangedEventType())

    # Icon
    
    def icon(self, recursive=False):
        myIcon = super(Task, self).icon(recursive=False)
        if not myIcon and recursive:
            try:
                myIcon = self.__recursiveIcon
            except AttributeError:
                myIcon = self.__computeRecursiveIcon()
        return self.pluralOrSingularIcon(myIcon)
    
    def iconChangedEvent(self, *args, **kwargs):
        super(Task, self).iconChangedEvent(*args, **kwargs)
        self.__computeRecursiveIcon()

    def __computeRecursiveIcon(self):
        self.__recursiveIcon =  self.categoryIcon() or self.__stateBasedIcon(False)
        return self.__recursiveIcon

    def selectedIcon(self, recursive=False):
        myIcon = super(Task, self).selectedIcon(recursive=False)
        if not myIcon and recursive:
            try:
                myIcon = self.__recursiveSelectedIcon
            except AttributeError:
                myIcon = self.__computeRecursiveSelectedIcon() 
        return self.pluralOrSingularIcon(myIcon)

    def selectedIconChangedEvent(self, *args, **kwargs):
        super(Task, self).selectedIconChangedEvent(*args, **kwargs)
        self.__computeRecursiveSelectedIcon()

    def __computeRecursiveSelectedIcon(self):
        self.__recursiveSelectedIcon = self.categorySelectedIcon() or self.__stateBasedIcon(selected=True)
        return self.__recursiveSelectedIcon

    stateColorMap = (('completed', '_green'), ('overdue', '_red'),
                     ('dueSoon', '_orange'), ('inactive', '_grey'))

    def __stateBasedIcon(self, selected=False):
        if self.isBeingTracked():
            taskIcon = 'clock'
        else:
            taskIcon = 'led'
            for state, stateColor in self.stateColorMap:
                if getattr(self, state)():
                    taskIcon += stateColor
                    break
            else:
                taskIcon += '_blue'
            taskIcon = self.pluralOrSingularIcon(taskIcon+'_icon')[:-len('_icon')]
            hasChildren = any(child for child in self.children() if not child.isDeleted())
            taskIcon += '_open' if selected and hasChildren else ''
        return taskIcon + '_icon'

    def recomputeAppearance(self):
        self.__computeRecursiveForegroundColor()
        self.__computeRecursiveIcon()
        self.__computeRecursiveSelectedIcon()
        
    # percentage Complete
    
    def percentageComplete(self, recursive=False):
        myPercentage = self.__percentageComplete.get()
        if recursive:
            # We ignore our own percentageComplete when we are marked complete
            # when all children are completed *and* our percentageComplete is 0
            percentages = []
            if myPercentage > 0 or not self.shouldMarkCompletedWhenAllChildrenCompleted():
                percentages.append(myPercentage)
            percentages.extend([child.percentageComplete(recursive) for child in self.children()])
            return sum(percentages)/len(percentages) if percentages else 0
        else:
            return myPercentage
        
    @patterns.eventSource
    def setPercentageComplete(self, percentage, event=None):
        if percentage == self.percentageComplete():
            return
        oldPercentage = self.percentageComplete()
        self.__percentageComplete.set(percentage, event=event)
        if percentage == 100 and oldPercentage != 100 and self.completionDateTime() == date.DateTime():
            self.setCompletionDateTime(date.Now(), event=event)
        elif oldPercentage == 100 and percentage != 100 and self.completionDateTime() != date.DateTime():
            self.setCompletionDateTime(date.DateTime(), event=event)
    
    def percentageCompleteEvent(self, event):
        event.addSource(self, self.percentageComplete(), 
                        type=self.percentageCompleteChangedEventType())
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.percentageComplete(recursive=True), 
                            type='task.percentageComplete')
    
    @staticmethod
    def percentageCompleteSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.percentageComplete(recursive=recursive)

    @classmethod
    def percentageCompleteSortEventTypes(class_):
        ''' The event types that influence the percentage complete sort order. '''
        return ('task.percentageComplete',)

    @classmethod
    def percentageCompleteChangedEventType(class_):
        return 'task.percentageComplete'
       
    # priority
    
    def priority(self, recursive=False):
        if recursive:
            childPriorities = [child.priority(recursive=True) \
                               for child in self.children() \
                               if not child.completed()]
            return max(childPriorities + [self.__priority.get()])
        else:
            return self.__priority.get()
        
    def setPriority(self, priority, event=None):
        self.__priority.set(priority, event=event)
        
    def priorityEvent(self, event):
        event.addSource(self, self.priority(), type='task.priority')
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.priority(recursive=True),
                            type='task.priority')
    
    @staticmethod
    def prioritySortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.priority(recursive=recursive)

    @classmethod
    def prioritySortEventTypes(class_):
        ''' The event types that influence the priority sort order. '''
        return ('task.priority',)
    
    # Hourly fee
    
    def hourlyFee(self, recursive=False): # pylint: disable-msg=W0613
        return self.__hourlyFee.get()
    
    def setHourlyFee(self, hourlyFee, event=None):
        self.__hourlyFee.set(hourlyFee, event=event)

    def hourlyFeeEvent(self, event):
        event.addSource(self, self.hourlyFee(), 
                        type=self.hourlyFeeChangedEventType())
        if self.timeSpent() > date.TimeDelta():
            for objectWithRevenue in [self] + self.efforts():
                objectWithRevenue.revenueEvent(event)
            
    @classmethod
    def hourlyFeeChangedEventType(class_):
        return '%s.hourlyFee'%class_
    
    @staticmethod # pylint: disable-msg=W0613
    def hourlyFeeSortFunction(**kwargs): 
        return lambda task: task.hourlyFee()

    @classmethod
    def hourlyFeeSortEventTypes(class_):
        ''' The event types that influence the hourly fee sort order. '''
        return (class_.hourlyFeeChangedEventType(),)
    
    # Fixed fee
                 
    def fixedFee(self, recursive=False):
        childFixedFees = sum(child.fixedFee(recursive) for child in 
                             self.children()) if recursive else 0
        return self.__fixedFee.get() + childFixedFees
    
    def setFixedFee(self, fixedFee, event=None):
        self.__fixedFee.set(fixedFee, event=event)
        
    def fixedFeeEvent(self, event):
        event.addSource(self, self.fixedFee(), type='task.fixedFee')
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.fixedFee(recursive=True),
                            type='task.fixedFee')
        self.revenueEvent(event)

    @staticmethod
    def fixedFeeSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.fixedFee(recursive=recursive)

    @classmethod
    def fixedFeeSortEventTypes(class_):
        ''' The event types that influence the fixed fee sort order. '''
        return ('task.fixedFee',)

    # Revenue        
        
    def revenue(self, recursive=False):
        childRevenues = sum(child.revenue(recursive) for child in 
                            self.children()) if recursive else 0
        return self.timeSpent().hours() * self.hourlyFee() + self.fixedFee() + \
               childRevenues

    def revenueEvent(self, event):
        event.addSource(self, self.revenue(), type='task.revenue')
        for ancestor in self.ancestors():
            event.addSource(ancestor, ancestor.revenue(recursive=True), 
                            type='task.revenue')

    @staticmethod
    def revenueSortFunction(**kwargs):            
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.revenue(recursive=recursive)

    @classmethod
    def revenueSortEventTypes(class_):
        ''' The event types that influence the revenue sort order. '''
        return ('task.revenue',)
    
    # reminder
    
    def reminder(self, recursive=False): # pylint: disable-msg=W0613
        if recursive:
            reminders = [child.reminder(recursive=True) for child in \
                         self.children()] + [self.__reminder.get()]
            reminders = [reminder for reminder in reminders if reminder]
            return min(reminders) if reminders else None
        else:
            return self.__reminder.get()

    def setReminder(self, reminderDateTime=None, event=None):
        if reminderDateTime == date.DateTime.max:
            reminderDateTime = None
        self.__reminder.set(reminderDateTime, event=event)
            
    def reminderEvent(self, event):
        event.addSource(self, self.reminder(), type='task.reminder')
    
    @staticmethod
    def reminderSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.reminder(recursive=recursive) or date.DateTime.max

    @classmethod
    def reminderSortEventTypes(class_):
        ''' The event types that influence the reminder sort order. '''
        return ('task.reminder',)

    # Recurrence
    
    def recurrence(self, recursive=False, upwards=False):
        if not self._recurrence and recursive and upwards and self.parent():
            return self.parent().recurrence(recursive, upwards)
        elif recursive and not upwards:
            recurrences = [child.recurrence() for child in self.children(recursive)]
            recurrences.append(self._recurrence)
            recurrences = [r for r in recurrences if r]
            return min(recurrences) if recurrences else self._recurrence
        else:
            return self._recurrence

    @patterns.eventSource
    def setRecurrence(self, recurrence=None, event=None):
        recurrence = recurrence or date.Recurrence()
        if recurrence == self._recurrence:
            return
        self._recurrence = recurrence
        event.addSource(self, recurrence, type='task.recurrence')

    @patterns.eventSource
    def recur(self, event=None):
        self.setCompletionDateTime(date.DateTime(), event=event)
        recur = self.recurrence(recursive=True, upwards=True)
        nextStartDateTime = recur(self.startDateTime(), next=False)
        self.setStartDateTime(nextStartDateTime, event=event)
        nextDueDateTime = recur(self.dueDateTime(), next=False)
        self.setDueDateTime(nextDueDateTime, event=event)
        self.setPercentageComplete(0, event=event)
        if self.reminder():
            nextReminder = recur(self.reminder(), next=False)
            self.setReminder(nextReminder, event=event)
        for child in self.children():
            if not child.recurrence():
                child.recur(event=event)
        self.recurrence()(next=True)

    @staticmethod
    def recurrenceSortFunction(**kwargs):
        recursive = kwargs.get('treeMode', False)
        return lambda task: task.recurrence(recursive=recursive)

    @classmethod
    def recurrenceSortEventTypes(class_):
        ''' The event types that influence the recurrence sort order. '''
        return ('task.recurrence',)
    
    # Prerequisites
    
    def prerequisites(self, recursive=False):
        prerequisites = self.__prerequisites.get() 
        if recursive:
            for child in self.children():
                prerequisites |= child.prerequisites(recursive)
        return prerequisites
    
    def setPrerequisites(self, prerequisites, event=None):
        self.__prerequisites.set(set(prerequisites), event=event)
        
    def addPrerequisites(self, prerequisites, event=None):
        self.__prerequisites.add(set(prerequisites), event=event)
        
    def removePrerequisites(self, prerequisites, event=None):
        self.__prerequisites.remove(set(prerequisites), event=event)

    def addTaskAsDependencyOf(self, prerequisites):
        for prerequisite in prerequisites:
            prerequisite.addDependencies([self])
            
    def removeTaskAsDependencyOf(self, prerequisites):
        for prerequisite in prerequisites:
            prerequisite.removeDependencies([self])
            
    def prerequisitesEvent(self, event, *prerequisites):
        event.addSource(self, *prerequisites, **dict(type='task.prerequisites'))
        self.recomputeAppearance()

    @staticmethod
    def prerequisitesSortFunction(**kwargs):
        ''' Return a sort key for sorting by prerequisites. Since a task can 
            have multiple prerequisites we first sort the prerequisites by their
            subjects. If the sorter is in tree mode, we also take the 
            prerequisites of the children of the task into account, after the 
            prerequisites of the task itself. '''
        def sortKeyFunction(task):
            def sortedSubjects(items):
                return sorted([item.subject(recursive=True) for item in items])
            prerequisites = task.prerequisites()
            sortedPrerequisiteSubjects = sortedSubjects(prerequisites)
            if kwargs.get('treeMode', False):
                childPrerequisites = task.prerequisites(recursive=True) - prerequisites
                sortedPrerequisiteSubjects.extend(sortedSubjects(childPrerequisites)) 
            return sortedPrerequisiteSubjects
        return sortKeyFunction

    @classmethod
    def prerequisitesSortEventTypes(class_):
        ''' The event types that influence the prerequisites sort order. '''
        return ('task.prerequisites')

    # Dependencies
    
    def dependencies(self, recursive=False):
        dependencies = self.__dependencies.get()
        if recursive:
            for child in self.children():
                dependencies |= child.dependencies(recursive)
        return dependencies

    def setDependencies(self, dependencies, event=None):
        self.__dependencies.set(set(dependencies), event=event)
    
    def addDependencies(self, dependencies, event=None):
        self.__dependencies.add(set(dependencies), event=event)
                
    def removeDependencies(self, dependencies, event=None):
        self.__dependencies.remove(set(dependencies), event=event)
        
    def addTaskAsPrerequisiteOf(self, dependencies):
        for dependency in dependencies:
            dependency.addPrerequisites([self])
            
    def removeTaskAsPrerequisiteOf(self, dependencies):
        for dependency in dependencies:
            dependency.removePrerequisites([self])        

    def dependenciesEvent(self, event, *dependencies):
        event.addSource(self, *dependencies, **dict(type='task.dependencies'))

    @staticmethod
    def dependenciesSortFunction(**kwargs):
        ''' Return a sort key for sorting by dependencies. Since a task can 
            have multiple dependencies we first sort the dependencies by their
            subjects. If the sorter is in tree mode, we also take the 
            dependencies of the children of the task into account, after the 
            dependencies of the task itself. '''
        def sortKeyFunction(task):
            def sortedSubjects(items):
                return sorted([item.subject(recursive=True) for item in items])
            dependencies = task.dependencies()
            sortedDependencySubjects = sortedSubjects(dependencies)
            if kwargs.get('treeMode', False):
                childDependencies = task.dependencies(recursive=True) - dependencies
                sortedDependencySubjects.extend(sortedSubjects(childDependencies)) 
            return sortedDependencySubjects
        return sortKeyFunction

    @classmethod
    def dependenciesSortEventTypes(class_):
        ''' The event types that influence the dependencies sort order. '''
        return ('task.dependencies',)
                
    # behavior
    
    @patterns.eventSource
    def setShouldMarkCompletedWhenAllChildrenCompleted(self, newValue, event=None):
        if newValue == self._shouldMarkCompletedWhenAllChildrenCompleted:
            return
        self._shouldMarkCompletedWhenAllChildrenCompleted = newValue
        event.addSource(self, newValue, 
                        type='task.setting.shouldMarkCompletedWhenAllChildrenCompleted')
        event.addSource(self, self.percentageComplete(recursive=True), 
                        type='task.percentageComplete')

    def shouldMarkCompletedWhenAllChildrenCompleted(self):
        return self._shouldMarkCompletedWhenAllChildrenCompleted
    
    @classmethod
    def modificationEventTypes(class_):
        eventTypes = super(Task, class_).modificationEventTypes()
        return eventTypes + ['task.dueDateTime', 'task.startDateTime', 
                             'task.completionDateTime', 
                             'task.effort.add', 'task.effort.remove', 
                             'task.budget', 'task.percentageComplete', 
                             'task.priority', 
                             class_.hourlyFeeChangedEventType(), 
                             'task.fixedFee',
                             'task.reminder', 'task.recurrence',
                             'task.prerequisites', 'task.dependencies',
                             'task.setting.shouldMarkCompletedWhenAllChildrenCompleted']
