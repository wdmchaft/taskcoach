'''
Task Coach - Your friendly task manager
CCopyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>

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

import os, codecs, xml
from taskcoachlib import patterns
from taskcoachlib.domain import base, task, category, note, effort, attachment
from taskcoachlib.syncml.config import createDefaultSyncConfig
from taskcoachlib.thirdparty.guid import generate
from taskcoachlib.thirdparty import lockfile


def getTemporaryFileName(path):
    """All functions/classes in the standard library that can generate
    a temporary file, visible on the file system, without deleting it
    when closed are deprecated (there is tempfile.NamedTemporaryFile
    but its 'delete' argument is new in Python 2.6). This is not
    secure, not thread-safe, but it works."""

    idx = 0
    while True:
        name = os.path.join(path, 'tmp-%d' % idx)
        if not os.path.exists(name):
            return name
        idx += 1


class TaskFile(patterns.Observer):
    def __init__(self, *args, **kwargs):
        self.__filename = self.__lastFilename = ''
        self.__needSave = self.__loading = False
        self.__tasks = task.TaskList()
        self.__categories = category.CategoryList()
        self.__notes = note.NoteContainer()
        self.__efforts = effort.EffortList(self.tasks())
        self.__guid = generate()
        self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        super(TaskFile, self).__init__(*args, **kwargs)
        # Register for tasks, categories, efforts and notes being changed so we 
        # can monitor when the task file needs saving (i.e. is 'dirty'):
        for container in self.tasks(), self.categories(), self.notes():
            for eventType in container.modificationEventTypes():
                self.registerObserver(self.onDomainObjectAddedOrRemoved,
                                      eventType, eventSource=container)
            
        for eventType in (base.Object.markDeletedEventType(),
                          base.Object.markNotDeletedEventType()):
            self.registerObserver(self.onDomainObjectAddedOrRemoved, eventType)
            
        for eventType in task.Task.modificationEventTypes():
            self.registerObserver(self.onTaskChanged, eventType)
        for eventType in effort.Effort.modificationEventTypes():
            self.registerObserver(self.onEffortChanged, eventType)
        for eventType in note.Note.modificationEventTypes():
            self.registerObserver(self.onNoteChanged, eventType)
        for eventType in category.Category.modificationEventTypes():
            self.registerObserver(self.onCategoryChanged, eventType)
        for eventType in attachment.FileAttachment.modificationEventTypes() + \
                         attachment.URIAttachment.modificationEventTypes() + \
                         attachment.MailAttachment.modificationEventTypes(): 
            self.registerObserver(self.onAttachmentChanged, eventType) 

    def __str__(self):
        return self.filename()
    
    def __contains__(self, item):
        return item in self.tasks() or item in self.notes() or \
               item in self.categories() or item in self.efforts()

    def categories(self):
        return self.__categories
    
    def notes(self):
        return self.__notes
    
    def tasks(self):
        return self.__tasks
    
    def efforts(self):
        return self.__efforts

    def syncMLConfig(self):
        return self.__syncMLConfig

    def guid(self):
        return self.__guid

    def setSyncMLConfig(self, config):
        self.__syncMLConfig = config
        self.markDirty()

    def isEmpty(self):
        return 0 == len(self.categories()) == len(self.tasks()) == len(self.notes())
            
    def onDomainObjectAddedOrRemoved(self, event): # pylint: disable-msg=W0613
        self.markDirty()
        
    def onTaskChanged(self, event):
        if self.__loading:
            return
        changedTasks = [changedTask for changedTask in event.sources() \
                        if changedTask in self.tasks()]
        if changedTasks:
            self.markDirty()
            for changedTask in changedTasks:
                changedTask.markDirty()
            
    def onEffortChanged(self, event):
        if self.__loading:
            return
        changedEfforts = [changedEffort for changedEffort in event.sources() if \
                          changedEffort.task() in self.tasks()]
        if changedEfforts:
            self.markDirty()
            for changedEffort in changedEfforts:
                changedEffort.markDirty()
            
    def onCategoryChanged(self, event):
        if self.__loading:
            return
        changedCategories = [changedCategory for changedCategory in event.sources() if \
                             changedCategory in self.categories()]
        if changedCategories:
            self.markDirty()
            # Mark all categorizables belonging to the changed category dirty; 
            # this is needed because in SyncML/vcard world, categories are not 
            # first-class objects. Instead, each task/contact/etc has a 
            # categories property which is a comma-separated list of category
            # names. So, when a category name changes, every associated
            # categorizable changes.
            for changedCategory in changedCategories:
                for categorizable in changedCategory.categorizables():
                    categorizable.markDirty()
            
    def onNoteChanged(self, event):
        if self.__loading:
            return
        # A note may be in self.notes() or it may be a note of another 
        # domain object.
        self.markDirty()
        for changedNote in event.sources():
            changedNote.markDirty()
            
    def onAttachmentChanged(self, event):
        if self.__loading:
            return
        # Attachments don't know their owner, so we can't check whether the
        # attachment is actually in the task file. Assume it is.
        self.markDirty()
        for changedAttachment in event.sources():
            changedAttachment.markDirty()

    def setFilename(self, filename):
        if filename == self.__filename:
            return
        self.__lastFilename = filename or self.__filename
        self.__filename = filename
        patterns.Event('taskfile.filenameChanged', self, filename).send()

    def filename(self):
        return self.__filename
        
    def lastFilename(self):
        return self.__lastFilename
    
    def markDirty(self, force=False):
        if force or not self.__needSave:
            self.__needSave = True
            patterns.Event('taskfile.dirty', self, True).send()
                
    def markClean(self):
        if self.__needSave:
            self.__needSave = False
            patterns.Event('taskfile.dirty', self, False).send()
            
    def clear(self, regenerate=True):
        self.tasks().clear()
        self.categories().clear()
        self.notes().clear()
        if regenerate:
            self.__guid = generate()
            self.__syncMLConfig = createDefaultSyncConfig(self.__guid)
        
    def close(self):
        self.setFilename('')
        self.__guid = generate()
        self.clear()
        self.__needSave = False

    def _read(self, fd):
        return xml.XMLReader(fd).read()
        
    def exists(self):
        return os.path.isfile(self.__filename)
        
    def _openForRead(self):
        return file(self.__filename, 'rU')

    def _openForWrite(self):
        name = getTemporaryFileName(os.path.split(self.__filename)[0])
        return name, codecs.open(name, 'w', 'utf-8')
    
    def load(self, filename=None):
        self.__loading = True
        if filename:
            self.setFilename(filename)
        try:
            if self.exists():
                fd = self._openForRead()
                tasks, categories, notes, syncMLConfig, guid = self._read(fd)
                fd.close()
            else: 
                tasks = []
                categories = []
                notes = []
                guid = generate()
                syncMLConfig = createDefaultSyncConfig(guid)
            self.clear()
            self.categories().extend(categories)
            self.tasks().extend(tasks)
            self.notes().extend(notes)
            self.__syncMLConfig = syncMLConfig
            self.__guid = guid
        except:
            self.setFilename('')
            raise
        finally:
            self.__loading = False
            self.__needSave = False
        
    def save(self):
        patterns.Event('taskfile.aboutToSave', self).send()
        # When encountering a problem while saving (disk full,
        # computer on fire), if we were writing directly to the file,
        # it's lost. So write to a temporary file and rename it if
        # everything went OK.
        name, fd = self._openForWrite()
        try:
            xml.XMLWriter(fd).write(self.tasks(), self.categories(), self.notes(),
                                    self.syncMLConfig(), self.guid())
            fd.close()
            if os.path.exists(self.__filename): # Not using self.exists() because DummyFile.exists returns True
                os.remove(self.__filename)
            if name is not None: # Unit tests (AutoSaver)
                os.rename(name, self.__filename)
            self.__needSave = False
        except:
            if name is not None: # Same remark as above
                os.remove(name)
            raise

    def saveas(self, filename):
        self.setFilename(filename)
        self.save()

    def merge(self, filename):
        mergeFile = self.__class__()
        mergeFile.load(filename)
        self.__loading = True
        self.tasks().removeItems(self.objectsToOverwrite(self.tasks(), mergeFile.tasks()))
        categoryMap = dict()
        self.rememberCategoryLinks(categoryMap, self.tasks())
        self.tasks().extend(mergeFile.tasks().rootItems())
        self.notes().removeItems(self.objectsToOverwrite(self.notes(), mergeFile.notes()))
        self.rememberCategoryLinks(categoryMap, self.notes())
        self.notes().extend(mergeFile.notes().rootItems())
        self.categories().removeItems(self.objectsToOverwrite(self.categories(),
                                                              mergeFile.categories()))
        self.categories().extend(mergeFile.categories().rootItems())
        self.restoreCategoryLinks(categoryMap)
        mergeFile.close()
        self.__loading = False
        self.markDirty(force=True)

    def objectsToOverwrite(self, originalObjects, objectsToMerge):
        objectsToOverwrite = []
        for domainObject in objectsToMerge:
            try:
                objectsToOverwrite.append(originalObjects.getObjectById(domainObject.id()))
            except IndexError:
                pass
        return objectsToOverwrite
        
    def rememberCategoryLinks(self, categoryMap, categorizables):
        for categorizable in categorizables:
            for category in categorizable.categories():
                categoryMap.setdefault(category.id(), []).append(categorizable)
            
    def restoreCategoryLinks(self, categoryMap):
        categories = self.categories()
        for categoryId, categorizables in categoryMap.iteritems():
            category = categories.getObjectById(categoryId)
            for categorizable in categorizables:
                categorizable.addCategory(category)
                category.addCategorizable(categorizable)
        
    
    def needSave(self):
        return not self.__loading and self.__needSave

    def beginSync(self):
        self.__loading = True

    def endSync(self):
        self.__loading = False
        self.__needSave = True


class LockedTaskFile(TaskFile):
    ''' LockedTaskFile adds cooperative locking to the TaskFile. '''
    
    def __init__(self, *args, **kwargs):
        super(LockedTaskFile, self).__init__(*args, **kwargs)
        self.__lock = None
        
    def is_locked(self):
        return self.__lock and self.__lock.is_locked()

    def is_locked_by_me(self):
        return self.is_locked() and self.__lock.i_am_locking()
    
    def release_lock(self):
        if self.is_locked_by_me():
            self.__lock.release()
            
    def acquire_lock(self, filename):
        if not self.is_locked_by_me():
            self.__lock = lockfile.FileLock(filename)
            self.__lock.acquire(-1) # Fail immediately if we can't get a lock
            
    def break_lock(self, filename):
        self.__lock = lockfile.FileLock(filename)
        self.__lock.break_lock()
            
    def load(self, filename=None, lock=True, breakLock=False): # pylint: disable-msg=W0221
        ''' Lock the file before we load, if not already locked. '''
        filename = filename or self.filename()
        if lock and filename:
            if breakLock:
                self.break_lock(filename)
            self.acquire_lock(filename)
        return super(LockedTaskFile, self).load(filename)
    
    def save(self):
        ''' Lock the file before we save, if not already locked. '''
        self.acquire_lock(self.filename())
        return super(LockedTaskFile, self).save()
    
    def saveas(self, filename):
        ''' Unlock the file before we save it under another name. '''
        self.release_lock()
        return super(LockedTaskFile, self).saveas(filename)
    
    def close(self):
        ''' Unlock the file after we close it. '''
        result = super(LockedTaskFile, self).close()
        self.release_lock()
        return result
