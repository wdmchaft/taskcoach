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
from taskcoachlib import persistence, config
from taskcoachlib.domain import task, category, date


class DummySettings(dict):
    def __init__(self):
        super(DummySettings, self).__init__()
        self.maxnrofbackups = 5
        
    def set(self, section, setting, value): # pylint: disable-msg=W0613
        self[setting] = value
        
    def getboolean(self, section, setting): # pylint: disable-msg=W0613
        return self.get(setting, 'False') == 'True'


class DummyFile(object):
    name = 'testfile.tsk'

    def close(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass
    
    
class DummyTaskFile(persistence.TaskFile):
    def __init__(self, *args, **kwargs):
        self.saveCalled = 0
        super(DummyTaskFile, self).__init__(*args, **kwargs)
        
    def _read(self, *args, **kwargs): # pylint: disable-msg=W0613,W0221
        if self._throw:
            raise IOError
        else:
            return [task.Task()], [category.Category('category')], [], None, None
        
    def exists(self, *args, **kwargs): # pylint: disable-msg=W0613
        return True
        
    def _openForRead(self, *args, **kwargs): # pylint: disable-msg=W0613
        return DummyFile()
        
    def _openForWrite(self, *args, **kwargs): # pylint: disable-msg=W0613
        return None, DummyFile()
    
    def save(self, *args, **kwargs):
        self.saveCalled += 1
        super(DummyTaskFile, self).save(*args, **kwargs)

    def load(self, filename=None, throw=False, *args, **kwargs): # pylint: disable-msg=W0221
        self._throw = throw # pylint: disable-msg=W0201
        return super(DummyTaskFile, self).load(filename, *args, **kwargs)


class AutoSaverTestCase(test.TestCase):
    def setUp(self):
        self.settings = DummySettings()
        self.taskFile = DummyTaskFile()
        self.autoSaver = persistence.AutoSaver(self.settings)
        
    def tearDown(self):
        super(AutoSaverTestCase, self).tearDown()
        del self.autoSaver # Make sure AutoSaver is not observing task files
        
    def testCreate(self):
        self.failIf(self.taskFile.saveCalled)
        
    def testFileChanged_ButNoFilenameAndAutoSaveOff(self):
        self.taskFile.tasks().append(task.Task())
        self.failIf(self.taskFile.saveCalled)
        
    def testFileChanged_ButAutoSaveOff(self):
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.tasks().append(task.Task())
        self.failIf(self.taskFile.saveCalled)
                
    def testFileChanged_ButNoFilename(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.tasks().append(task.Task())
        self.failIf(self.taskFile.saveCalled)
        
    def testFileChanged(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.tasks().append(task.Task())
        self.assertEqual(1, self.taskFile.saveCalled)
        
    def testSaveAsDoesNotTriggerAutoSave(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.saveas('newfilename.tsk')
        self.assertEqual(1, self.taskFile.saveCalled)
              
    def testCloseDoesNotTriggerAutoSave(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.tasks().append(task.Task())
        self.taskFile.close()
        self.assertEqual(1, self.taskFile.saveCalled)
        
    def testLoadDoesNotTriggerAutoSave(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.load()
        self.failIf(self.taskFile.saveCalled)

    def testLoadWithExceptionDoesNotTriggerAutoSave(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        try:
            self.taskFile.load(throw=True)
        except IOError:
            pass
        self.failIf(self.taskFile.saveCalled)
        
    def testMergeDoesTriggerAutoSave(self):
        self.settings.set('file', 'autosave', 'True')
        self.taskFile.setFilename('whatever.tsk')
        self.taskFile.merge('another-non-existing-file.tsk')
        self.assertEqual(1, self.taskFile.saveCalled)
