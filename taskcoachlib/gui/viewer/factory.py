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

import effort, task, category, note


def viewerTypes():
    return 'timelineviewer', 'squaretaskviewer', 'taskviewer', 'noteviewer', 'categoryviewer', 'effortviewer', 'calendarviewer'


class addViewers(object):
    ''' addViewers is a class masquerading as a method. It's a class because
        that makes it easier to split the work over different methods that
        use the same instance variables. '''  
    
    def __init__(self, viewerContainer, taskFile, settings):
        self.viewerContainer = viewerContainer
        self.settings = settings
        self.viewerInitArgs = (viewerContainer.containerWidget, taskFile, 
                               settings)
        self.addAllViewers()
        
    def addAllViewers(self):
        self.addViewers(task.TaskViewer)
        self.addViewers(task.SquareTaskViewer)
        self.addViewers(task.TimelineViewer)
        self.addViewers(task.CalendarViewer)
        if self.settings.getboolean('feature', 'effort'):
            self.addViewers(effort.EffortViewer)
        self.addViewers(category.CategoryViewer)
        if self.settings.getboolean('feature', 'notes'):
            self.addViewers(note.NoteViewer)

    def addViewers(self, viewerClass):
        numberOfViewersToAdd = self.numberOfViewersToAdd(viewerClass)
        for _ in range(numberOfViewersToAdd):
            viewerInstance = viewerClass(*self.viewerInitArgs, 
                                         **self.viewerKwargs(viewerClass))
            self.viewerContainer.addViewer(viewerInstance)
    
    def numberOfViewersToAdd(self, viewerClass):
        return self.settings.getint('view', viewerClass.__name__.lower() + 'count')

    def viewerKwargs(self, viewerClass): # pylint: disable-msg=W0613
        return dict()
    

class addOneViewer(addViewers):
    def __init__(self, viewerContainer, taskFile, settings, viewerClass, **kwargs):
        self.viewerClass = viewerClass
        self.kwargs = kwargs
        super(addOneViewer, self).__init__(viewerContainer, taskFile, settings)
        
    def numberOfViewersToAdd(self, viewerClass):
        return 1 if viewerClass == self.viewerClass else 0
        
    def viewerKwargs(self, viewerClass):
        return self.kwargs
