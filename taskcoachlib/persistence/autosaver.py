'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>

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

from taskcoachlib import patterns


class AutoSaver(patterns.Observer):
    ''' AutoSaver observes task files. If a task file is changed by the user 
        (gets 'dirty') and auto save is on, AutoSaver saves the task file. '''
        
    def __init__(self, settings, *args, **kwargs):
        super(AutoSaver, self).__init__(*args, **kwargs)
        self.__settings = settings
        self.registerObserver(self.onTaskFileDirty, eventType='taskfile.dirty')
            
    def onTaskFileDirty(self, event):
        ''' When a task file gets dirty and auto save is on, save it. '''
        for taskFile in event.sources():
            if self._needSave(taskFile):
                taskFile.save()

    def _needSave(self, taskFile):
        return taskFile.filename() and taskFile.needSave() and \
            self.__settings.getboolean('file', 'autosave')
