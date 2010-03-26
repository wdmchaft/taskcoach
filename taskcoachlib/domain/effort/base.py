'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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


class BaseEffort(object):
    def __init__(self, task, start, stop, *args, **kwargs):
        self._task = task
        self._start = start
        self._stop = stop
        super(BaseEffort, self).__init__(*args, **kwargs)
      
    def task(self):
        return self._task

    def getStart(self):
        return self._start

    def getStop(self):
        return self._stop

    def subject(self, *args, **kwargs):
        return self._task.subject(*args, **kwargs)

    def categories(self, recursive=False):
        return self._task.categories(recursive)

    def foregroundColor(self, recursive=False):
        return self.task().foregroundColor(recursive)
    
    def backgroundColor(self, recursive=False):
        return self.task().backgroundColor(recursive)
    
    def font(self, recursive=False):
        return self.task().font(recursive)
    
    def duration(self, recursive=False):
        raise NotImplementedError

    @classmethod
    def trackStartEventType(class_):
        return 'effort.track.start' 
        # We don't use '%s.effort...'%class_ because we need Effort and 
        # CompositeEffort to use the same event types. This is needed to make
        # UpdatePerSecondViewer work regardless whether EffortViewer is in
        # aggregate mode or not.
    
    @classmethod
    def trackStopEventType(class_):
        return 'effort.track.stop'
    
