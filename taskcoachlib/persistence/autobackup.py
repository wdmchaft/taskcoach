'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
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

import os, shutil, glob, math
from taskcoachlib import patterns
from taskcoachlib.domain import date
                    

class AutoBackup(patterns.Observer):
    ''' If backups are on, AutoBackup creates a backup copy of the task 
        file before it is overwritten. To prevent the number of backups growing
        indefinitely, AutoBackup removes older backups. '''
        
    minNrOfBackupFiles = 3 # Keep at least three backup files.
    maxNrOfBackupFilesToRemoveAtOnce = 3 # Slowly reduce the number of backups
    
    def __init__(self, settings, copyfile=shutil.copyfile):
        super(AutoBackup, self).__init__()
        self.__settings = settings
        self.__copyfile = copyfile
        self.registerObserver(self.onTaskFileAboutToSave,
                              eventType='taskfile.aboutToSave')
            
    def onTaskFileAboutToSave(self, event):
        ''' Just before a task file is about to be saved, and backups are on,
            create a backup and remove extraneous backup files. '''
        for taskFile in event.sources():
            if self.needBackup(taskFile):
                self.createBackup(taskFile)
            self.removeExtraneousBackupFiles(taskFile)

    def needBackup(self, taskFile):
        return self.__settings.getboolean('file', 'backup') and taskFile.exists()

    def createBackup(self, taskFile):
        self.__copyfile(taskFile.filename(), self.backupFilename(taskFile))
    
    def removeExtraneousBackupFiles(self, taskFile, remove=os.remove, 
                                    glob=glob.glob):
        backupFiles = self.backupFiles(taskFile, glob)
        for _ in range(min(self.maxNrOfBackupFilesToRemoveAtOnce,
                           self.numberOfExtraneousBackupFiles(backupFiles))):
            try:
                remove(self.leastUniqueBackupFile(backupFiles))
            except OSError:
                pass # Ignore errors

    def numberOfExtraneousBackupFiles(self, backupFiles):
        return max(0, len(backupFiles) - self.maxNrOfBackupFiles(backupFiles))

    def maxNrOfBackupFiles(self, backupFiles):
        ''' The maximum number of backup files we keep depends on the age of
            the oldest backup file. The older the oldest backup file (that is
            never removed), the more backup files we keep. '''
        if not backupFiles:
            return 0
        age = date.DateTime.now() - self.backupDateTime(backupFiles[0])
        ageInMinutes = age.hours() * 60
        # We keep log(ageInMinutes) backups, but at least 3: 
        return max(self.minNrOfBackupFiles, int(math.log(max(1, ageInMinutes))))
    
    def leastUniqueBackupFile(self, backupFiles):
        ''' Find the backupFile that is closest (in time) to its neighbors,
            i.e. that is the least unique. Ignore the oldest and newest 
            backups. '''
        assert len(backupFiles) > self.minNrOfBackupFiles
        deltas = []
        for index in range(1, len(backupFiles)-1):
            delta = self.backupDateTime(backupFiles[index+1]) - \
                    self.backupDateTime(backupFiles[index-1])
            deltas.append((delta, backupFiles[index]))
        deltas.sort()
        return deltas[0][1]

    @staticmethod
    def backupFiles(taskFile, glob=glob.glob):
        root, ext = os.path.splitext(taskFile.filename())
        datePattern = '[0-9]'*8
        timePattern = '[0-9]'*6
        files = glob('%s.%s-%s.tsk.bak'%(root, datePattern, timePattern))
        files.sort()
        return files

    @staticmethod
    def backupFilename(taskFile, now=date.DateTime.now):
        ''' Generate a backup filename by adding '.bak' to the end and by 
            inserting a date-time string in the filename. '''
        now = now().strftime('%Y%m%d-%H%M%S')
        root, ext = os.path.splitext(taskFile.filename())
        if ext == '.bak':
            root, ext = os.path.splitext(root)
        return root + '.' + now + ext + '.bak'
                
    @staticmethod
    def backupDateTime(backupFilename):
        ''' Parse the date and time from the filename and return a DateTime 
            instance. '''
        dt = backupFilename.split('.')[-3]
        parts = (int(part) for part in (dt[0:4], dt[4:6], dt[6:8], 
                                        dt[9:11], dt[11:13], dt[13:14]))
        return date.DateTime(*parts)
