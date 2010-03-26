'''
Task Coach - Your friendly task manager
Copyright (C) 2008-2010 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2010 Frank Niessink <frank@niessink.com>

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

# pylint: disable-msg=W0201,E1101
 
from taskcoachlib.patterns.network import Acceptor
from taskcoachlib.domain.date import Date, parseDate, DateTime, parseDateTime

from taskcoachlib.domain.category import Category
from taskcoachlib.domain.task import Task
from taskcoachlib.domain.effort import Effort

from taskcoachlib.i18n import _

import wx, asynchat, threading, asyncore, struct, \
    random, time, hashlib, cStringIO, socket, os, sys

# Default port is 8001.
#
# Integers are sent as 32 bits signed, network byte order.
# Strings are sent as their length (as integer), then data (UTF-8
# encoded). The length is computed after encoding.
# Dates are sent as strings, formatted YYYY-MM-DD.
#
# The exact workflow for both desktop and device is documented as Dia
# diagrams, in the "Design" subdirectory of the iPhone sources.

###############################################################################
#{ Support classes: object serialisation & packing

class BaseItem(object):
    """This is the base class of the network packet system. Each
    subclass maps to a particular type of data.

    @ivar state: convenience instance variable which starts as 0, used
        in subclasses to implement simple FSA."""

    def __init__(self):
        super(BaseItem, self).__init__()

        self.start()

    def start(self):
        """This method should reinitialize the instance."""
        self.state = 0
        self.value = None

    def expect(self):
        """This should return the number of bytes that are needed
        next. When this much bytes are finally available, they'll be
        passed to L{feed}. Return None if you're finished."""

        raise NotImplementedError

    def feed(self, data):
        """The bytes requested from L{expect} are available ('data'
        parameter)."""

        raise NotImplementedError

    def pack(self, value):
        """Unserialization. This should return a byte buffer
        representing 'value'."""

        raise NotImplementedError


class IntegerItem(BaseItem):
    """Integers. Packed as 32-bits, signed, big endian. Underlying
    type: int."""

    def expect(self):
        if self.state == 0:
            return 4
        else:
            return None

    def feed(self, data):
        self.value, = struct.unpack('!i', data)
        self.state = 1

    def pack(self, value):
        return struct.pack('!i', value)


class DataItem(BaseItem):
    """A bunch of bytes, the count being well known"""

    def __init__(self, count):
        super(DataItem, self).__init__()

        self.__count = count

    def expect(self):
        if self.state == 0:
            return self.__count
        else:
            return None

    def feed(self, data):
        if self.state == 0:
            self.value = data
            self.state = 1

    def pack(self, value):
        return value


class StringItem(BaseItem):
    """Strings. Encoded in UTF-8. Packed as their length (encoded),
    then the data. Underlying type: unicode."""

    def expect(self):
        if self.state == 0:
            return 4
        elif self.state == 1:
            return self.length
        else:
            return None

    def feed(self, data):
        if self.state == 0:
            self.length, = struct.unpack('!i', data)
            if self.length:
                self.state = 1
            else:
                self.value = u''
                self.state = 2
        elif self.state == 1:
            self.value = data.decode('UTF-8')
            self.state = 2

    def pack(self, value):
        v = value.encode('UTF-8')
        return struct.pack('!i', len(v)) + v


class FixedSizeStringItem(StringItem):
    """Same as L{StringItem}, but cannot be empty. Underlying type:
    unicode or NoneType."""

    def feed(self, data):
        super(FixedSizeStringItem, self).feed(data)

        if self.state == 2:
            if not self.value:
                self.value = None

    def pack(self, value):
        if value is None:
            return struct.pack('!i', 0)
        return super(FixedSizeStringItem, self).pack(value)


class DateItem(FixedSizeStringItem):
    """Date, in YYYY-MM-DD format. Underlying type:
    taskcoachlib.domain.date.Date."""

    def feed(self, data):
        super(DateItem, self).feed(data)

        if self.state == 2:
            if self.value is None:
                self.value = Date()
            else:
                self.value = parseDate(self.value)

    def pack(self, value):
        if value == Date():
            return super(DateItem, self).pack(None)
        else:
            return super(DateItem, self).pack('%04d-%02d-%02d' % (value.year, value.month, value.day))


class DateTimeItem(FixedSizeStringItem):
    """Date and time, YYYY-MM-DD HH:MM:SS"""

    def feed(self, data):
        super(DateTimeItem, self).feed(data)

        if self.state == 2:
            if self.value is not None:
                self.value = parseDateTime(self.value)

    def pack(self, value):
        if value is None:
            return super(DateTimeItem, self).pack(None)
        else:
            return super(DateTimeItem, self).pack('%04d-%02d-%02d %02d:%02d:%02d' % (value.year, value.month,
                                                                                     value.day, value.hour,
                                                                                     value.minute, value.second))


class CompositeItem(BaseItem):
    """A succession of several types. Underlying type: tuple. An
    exception is made if there is only 1 child, the type is then the
    same as it."""

    def __init__(self, items, *args, **kwargs):
        self._items = items

        super(CompositeItem, self).__init__(*args, **kwargs)

    def append(self, item):
        self._items.append(item)

    def start(self):
        super(CompositeItem, self).start()

        self.value = []

        for item in self._items:
            item.start()

    def expect(self):
        if self.state < len(self._items):
            expect = self._items[self.state].expect()

            if expect is None:
                self.value.append(self._items[self.state].value)
                self.state += 1
                return self.expect()

            return expect
        else:
            if len(self._items) == 1:
                self.value = self.value[0]
            else:
                self.value = tuple(self.value)
            return None

    def feed(self, data):
        self._items[self.state].feed(data)

    def pack(self, *values):
        if len(self._items) == 1:
            return self._items[0].pack(values[0])
        else:
            return ''.join([self._items[idx].pack(v) \
                            for idx, v in enumerate(values)])

    def __str__(self):
        return 'CompositeItem([%s])' % ', '.join(map(str, self._items))


class ListItem(BaseItem):
    """A list of items. Underlying type: list."""

    def __init__(self, item, *args, **kwargs):
        self._item = item

        super(ListItem, self).__init__(*args, **kwargs)

    def start(self):
        super(ListItem, self).start()

        self.value = []

        self._item.start()

    def append(self, item):
        self._item.append(item)

    def expect(self):
        if self.state == 0:
            return 4
        elif self.state == 1:
            expect = self._item.expect()

            if expect is None:
                self.value.append(self._item.value)
                self.__count -= 1
                if self.__count == 0:
                    return None
                self._item.start()
                return self.expect()
            else:
                return expect
        elif self.state == 2:
            return None

    def feed(self, data):
        if self.state == 0:
            self.__count, = struct.unpack('!i', data)
            if self.__count:
                self._item.start()
                self.state = 1
            else:
                self.state = 2
        elif self.state == 1:
            self._item.feed(data)

    def pack(self, value):
        return struct.pack('!i', len(value)) + \
               ''.join([self._item.pack(v) for v in value])

    def __str__(self):
        return 'ListItem(%s)' % str(self._item)


class ItemParser(object):
    """Utility to avoid instantiating the Item classes by
    hand. parse('is[zi]') will hold a CompositeItem([IntegerItem(),
    StringItem(), ListItem(CompositeItem([FixedSizeStringItem(),
    IntegerITem()]))])."""

    # Special case for DataItem.

    formatMap = { 'i': IntegerItem,
                  's': StringItem,
                  'z': FixedSizeStringItem,
                  'd': DateItem,
                  't': DateTimeItem }

    def __init__(self):
        super(ItemParser, self).__init__()

    @classmethod
    def registerItemType(klass, character, itemClass):
        """Register a new type of item. 'character' must be a
        single-character string, not already associated with an
        item. 'itemClass' should be a L{BaseItem} subclass. Its
        constructor must not take any parameter."""

        if len(character) != 1:
            raise ValueError('character must be a single character, not "%s".' % character)

        if character in klass.formatMap:
            raise ValueError('"%s" is already registered.' % character)

        klass.formatMap[character] = itemClass

    def parse(self, format):
        if format.startswith('['):
            return ListItem(self.parse(format[1:-1]))

        current = CompositeItem([])
        stack = []
        count = None

        for character in format:
            if character == '[':
                item = ListItem(CompositeItem([]))
                stack.append(current)
                current.append(item)
                current = item
            elif character == ']':
                current = stack.pop()
            elif character == 'b':
                if count is None:
                    raise ValueError('Wrong format string: %s' % format)
                current.append(DataItem(count))
                count = None
            elif character.isdigit():
                if count is None:
                    count = int(character)
                else:
                    count *= 10
                    count += int(character)
            else:
                current.append(self.formatMap[character]())

        assert len(stack) == 0

        return current


class State(object):
    def __init__(self, disp):
        super(State, self).__init__()

        self.__disp = disp

    def init(self, format, count):
        self.__format = format
        self.__count = count

        self.__data = cStringIO.StringIO()

        if format is None:
            self.__item = None
        else:
            self.__item = ItemParser().parse(format)

            if self.__count == 0:
                self.finished()
            else:
                self.__disp.set_terminator(self.__item.expect())

    def setState(self, klass, *args, **kwargs):
        self.__class__ = klass
        self.init(*args, **kwargs)

    def data(self):
        return self.__data.getvalue()

    def disp(self):
        return self.__disp

    def collect_incoming_data(self, data):
        if self.__format is not None:
            self.__data.write(data)

    def found_terminator(self):
        if self.__format is not None:
            self.__item.feed(self.__data.getvalue())
            self.__data = cStringIO.StringIO()

            length = self.__item.expect()
            if length is None:
                value = self.__item.value

                self.__count -= 1
                if self.__count:
                    self.__item.start()
                    self.__disp.set_terminator(self.__item.expect())

                self.handleNewObject(value)

                if not self.__count:
                    self.finished()
            else:
                self.__disp.set_terminator(length)

    def pack(self, format, *values):
        """Send a value."""

        self.__disp.push(ItemParser().parse(format).pack(*values))

    def handleClose(self):
        pass

    def handleNewObject(self, obj):
        raise NotImplementedError

    def finished(self):
        raise NotImplementedError

###############################################################################
# Actual protocol

class IPhoneAcceptor(Acceptor):
    def __init__(self, window, settings, iocontroller):
        def factory(fp, addr):
            password = settings.get('iphone', 'password')

            if password:
                return IPhoneHandler(window, settings, iocontroller, fp)

            wx.MessageBox(_('''An iPhone or iPod Touch tried to connect to Task Coach,\n'''
                            '''but no password is set. Please set a password in the\n'''
                            '''iPhone section of the configuration and try again.'''),
                          _('Error'), wx.OK)

        Acceptor.__init__(self, factory, '', None)

        thread = threading.Thread(target=asyncore.loop)
        thread.setDaemon(True)
        thread.start()


class IPhoneHandler(asynchat.async_chat):
    def __init__(self, window, settings, iocontroller, fp):
        asynchat.async_chat.__init__(self, fp)

        self.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

        self.window = window
        self.settings = settings
        self.iocontroller = iocontroller

        self.state = BaseState(self)

        self.state.setState(InitialState, 4)

        random.seed(time.time())

    def log(self, msg, *args):
        if self.state.dlg is not None:
            self.state.dlg.AddLogLine(msg % args)

    def collect_incoming_data(self, data):
        self.state.collect_incoming_data(data)

    def found_terminator(self):
        self.state.found_terminator()

    def handle_close(self):
        self.state.handleClose()
        self.close()

    def handle_error(self):
        if self.state.dlg is not None:
            import traceback, StringIO
            bf = StringIO.StringIO()
            traceback.print_exc(file=bf)

            self.state.dlg.AddLogLine(bf.getvalue())

        asynchat.async_chat.handle_error(self)
        self.close()
        self.state.handleClose()


class BaseState(State):
    def __init__(self, disp, *args, **kwargs):
        self.oldTasks = disp.window.taskFile.tasks().copy()
        self.oldCategories = disp.window.taskFile.categories().copy()

        self.dlg = None

        self.syncCompleted = disp.settings.getboolean('iphone', 'synccompleted')

        super(BaseState, self).__init__(disp, *args, **kwargs)

    def isTaskEligible(self, task):
        """Returns True if a task should be considered when syncing with an iPhone/iPod Touch
        device. Right now, a task is eligible if

         * It's a leaf task (no children)
         * Or it has a reminder
         * Or it's overdue
         * Or it belongs to a category named 'iPhone'

         This will probably be more configurable in the future."""

        if task.completed() and not self.syncCompleted:
            return False

        if task.isDeleted():
            return False

        if len(task.children()) == 0:
            return True

        if task.reminder() is not None:
            return True

        if task.overdue():
            return True

        for category in task.categories():
            if category.subject() == 'iPhone':
                return True

        return False

    def handleClose(self):
        if self.dlg is not None:
            self.dlg.Finished()

        # Rollback
        self.disp().window.restoreTasks(self.oldCategories, self.oldTasks)


class InitialState(BaseState):
    def init(self, version):
        self.version = version

        super(InitialState, self).init('i', 1)

        self.dlg = self.disp().window.createIPhoneProgressDialog()
        self.dlg.Started()

        self.pack('i', version)

    def handleNewObject(self, accepted):
        if accepted:
            self.disp().log(_('Protocol version: %d'), self.version)
            self.setState(PasswordState)
        else:
            if self.version == 1:
                # Do not close the connection because it causes an error on the
                # device. It will do it itself.
                self.disp().window.notifyIPhoneProtocolFailed()
            else:
                self.disp().log(_('Rejected protocol version %d'), self.version)
                self.setState(InitialState, self.version - 1)

    def finished(self):
        pass


class PasswordState(BaseState):
    def init(self):
        super(PasswordState, self).init('20b', 1)

        self.hashData = ''.join([struct.pack('B', random.randint(0, 255)) for i in xrange(512)])
        self.pack('20b', self.hashData)

    def handleNewObject(self, hash):
        local = hashlib.sha1()
        local.update(self.hashData + self.disp().settings.get('iphone', 'password').encode('UTF-8'))

        if hash == local.digest():
            self.disp().log(_('Hash OK.'))
            self.pack('i', 1)
            self.setState(DeviceNameState)
        else:
            self.disp().log(_('Hash KO.'))
            self.pack('i', 0)
            self.setState(PasswordState)

    def finished(self):
        pass


class DeviceNameState(BaseState):
    def init(self):
        super(DeviceNameState, self).init('s', 1)

    def handleNewObject(self, name):
        self.disp().log(_('Device name: %s'), name)
        self.deviceName = name
        self.dlg.SetDeviceName(name)
        self.setState(GUIDState)


class GUIDState(BaseState):
    def init(self):
        if self.version >= 4:
            super(GUIDState, self).init('i', 1)
            self.pack('s', self.disp().window.taskFile.guid())
        else:
            super(GUIDState, self).init('z', 1)

    def handleNewObject(self, guid):
        self.disp().log(_('GUID: %s'), guid)

        if self.version >= 4:
            self.setState(TaskFileNameState)
        else:
            type_ = self.disp().window.getIPhoneSyncType(guid)

            self.pack('i', type_)

            if type_ != 3:
                self.dlg = self.disp().window.createIPhoneProgressDialog(self.deviceName)
                self.dlg.Started()

            if type_ == 0:
                self.setState(TwoWayState)
            elif type_ == 1:
                self.setState(FullFromDesktopState)
            elif type_ == 2:
                self.setState(FullFromDeviceState)

            # On cancel, the other end will close the connection

    def finished(self):
        pass


class TaskFileNameState(BaseState):
    def init(self):
        super(TaskFileNameState, self).init('i', 1)

        filename = self.disp().iocontroller.filename()
        if filename:
            filename = os.path.splitext(os.path.split(filename)[1])[0]
        self.disp().log(_('Sending file name: %s'), filename)
        self.pack('z', filename)

    def handleNewObject(self, response):
        self.setState(TwoWayState)

    def finished(self):
        pass


class FullFromDesktopState(BaseState):
    def init(self):
        self.disp().log(_('Full from desktop.'))

        if self.version >= 4:
            allEfforts = self.disp().window.taskFile.efforts()

            if self.syncCompleted:
                self.tasks = list([task for task in self.disp().window.taskFile.tasks().allItemsSorted() if not task.isDeleted()])
                self.efforts = list([effort for effort in  allEfforts \
                                  if effort.task() is None or not effort.task().isDeleted()])
            else:
                self.tasks = list([task for task in self.disp().window.taskFile.tasks().allItemsSorted() if not (task.isDeleted() or task.completed())])
                self.efforts = list([effort for effort in allEfforts \
                                  if effort.task() is None or not (effort.task().isDeleted() or effort.task().completed())])
        else:
            self.tasks = filter(self.isTaskEligible, self.disp().window.taskFile.tasks())
        self.categories = list([cat for cat in self.disp().window.taskFile.categories().allItemsSorted() if not cat.isDeleted()])

        if self.version >= 4:
            self.pack('iii', len(self.categories), len(self.tasks), len(self.efforts))
            self.total = len(self.categories) + len(self.tasks) + len(self.efforts)
        else:
            self.pack('ii', len(self.categories), len(self.tasks))
            self.total = len(self.categories) + len(self.tasks)

        self.count = 0

        self.setState(FullFromDesktopCategoryState)


class FullFromDesktopCategoryState(BaseState):
    def init(self):
        super(FullFromDesktopCategoryState, self).init('i', len(self.categories))

        self.disp().log(_('%d categories'), len(self.categories))

        if self.categories:
            self.sendObject()

    def sendObject(self):
        if self.categories:
            category = self.categories.pop(0)
            self.disp().log(_('Send category %s'), category.id())
            self.pack('ssz', category.subject(), category.id(),
                      None if category.parent() is None else category.parent().id())

    def handleNewObject(self, code):
        self.disp().log(_('Response: %d'), code)
        self.count += 1
        self.dlg.SetProgress(self.count, self.total)
        self.sendObject()

    def finished(self):
        self.setState(FullFromDesktopTaskState)


class FullFromDesktopTaskState(BaseState):
    def init(self):
        super(FullFromDesktopTaskState, self).init('i', len(self.tasks))

        self.disp().log(_('%d tasks'), len(self.tasks))

        if self.tasks:
            self.sendObject()

    def sendObject(self):
        if self.tasks:
            task = self.tasks.pop(0)
            self.disp().log(_('Send task %s'), task.id())
            if self.version < 4:
                self.pack('sssddd[s]',
                          task.subject(),
                          task.id(),
                          task.description(),
                          task.startDate(),
                          task.dueDate(),
                          task.completionDate(),
                          [category.id() for category in task.categories()])
            else:
                self.pack('sssdddz[s]',
                          task.subject(),
                          task.id(),
                          task.description(),
                          task.startDate(),
                          task.dueDate(),
                          task.completionDate(),
                          task.parent().id() if task.parent() is not None else None,
                          [category.id() for category in task.categories()])

    def handleNewObject(self, code):
        self.disp().log(_('Response: %d'), code)
        self.count += 1
        self.dlg.SetProgress(self.count, self.total)
        self.sendObject()

    def finished(self):
        if self.version >= 4:
            self.setState(FullFromDesktopEffortState)
        else:
            self.setState(SendGUIDState)


class FullFromDesktopEffortState(BaseState):
    def init(self):
        super(FullFromDesktopEffortState, self).init('i', len(self.efforts))

        self.disp().log(_('%d efforts'), len(self.efforts))

        if self.efforts:
            self.sendObject()

    def sendObject(self):
        if self.efforts:
            effort = self.efforts.pop(0)
            self.disp().log(_('Send effort %s'), effort.id())
            self.pack('ssztt',
                      effort.id(),
                      effort.subject(),
                      effort.task().id() if effort.task() is not None else None,
                      effort.getStart(),
                      effort.getStop())

    def handleNewObject(self, code):
        self.count += 1
        self.dlg.SetProgress(self.count, self.total)
        self.sendObject()

    def finished(self):
        self.setState(SendGUIDState)


class FullFromDeviceState(BaseState):
    def init(self):
        self.disp().window.clearTasks()

        super(FullFromDeviceState, self).init('ii', 1)

    def handleNewObject(self, (categoryCount, taskCount)):
        self.categoryCount = categoryCount
        self.taskCount = taskCount

        self.total = categoryCount + taskCount
        self.count = 0

        self.setState(FullFromDeviceCategoryState)

    def finished(self):
        pass


class FullFromDeviceCategoryState(BaseState):
    def init(self):
        self.categoryMap = {}

        super(FullFromDeviceCategoryState, self).init('s' if self.version < 3 else 'sz', self.categoryCount)

    def handleNewObject(self, args):
        if self.version < 3:
            name = args
            parentId = None
        else:
            name, parentId = args

        if parentId is None:
            category = Category(name)
        else:
            category = self.categoryMap[parentId].newChild(name)

        self.disp().window.addIPhoneCategory(category)

        self.pack('s', category.id())
        self.categoryMap[category.id()] = category

        self.count += 1
        self.dlg.SetProgress(self.count, self.total)

    def finished(self):
        self.setState(FullFromDeviceTaskState)


class FullFromDeviceTaskState(BaseState):
    def init(self):
        super(FullFromDeviceTaskState, self).init('ssddd[s]', self.taskCount)

    def handleNewObject(self, (subject, description, startDate, dueDate, completionDate, categories)):
        task = Task(subject=subject, description=description, startDate=startDate,
                    dueDate=dueDate, completionDate=completionDate)

        self.disp().window.addIPhoneTask(task, [self.categoryMap[id_] for id_ in categories])

        self.count += 1
        self.dlg.SetProgress(self.count, self.total)

        self.pack('s', task.id())

    def finished(self):
        self.setState(SendGUIDState)


class TwoWayState(BaseState):
    def init(self):
        self.categoryMap = dict([(category.id(), category) for category in self.disp().window.taskFile.categories()])
        self.taskMap = dict([(task.id(), task) for task in self.disp().window.taskFile.tasks()])
        self.effortMap = dict([(effort.id(), effort) for effort in self.disp().window.taskFile.efforts()])

        if self.version < 3:
            super(TwoWayState, self).init('iiii', 1)
        elif self.version < 4:
            super(TwoWayState, self).init('iiiiii', 1)
        else:
            super(TwoWayState, self).init('iiiiiiiii', 1)

    def handleNewObject(self, args):
        if self.version < 3:
            (self.newCategoriesCount,
             self.newTasksCount,
             self.deletedTasksCount,
             self.modifiedTasksCount) = args
        elif self.version < 4:
            (self.newCategoriesCount,
             self.newTasksCount,
             self.deletedTasksCount,
             self.modifiedTasksCount,
             self.deletedCategoriesCount,
             self.modifiedCategoriesCount) = args
        else:
            (self.newCategoriesCount,
             self.newTasksCount,
             self.deletedTasksCount,
             self.modifiedTasksCount,
             self.deletedCategoriesCount,
             self.modifiedCategoriesCount,
             self.newEffortsCount,
             self.modifiedEffortsCount,
             self.deletedEffortsCount) = args

            self.disp().log(_('%d new categories'), self.newCategoriesCount)
            self.disp().log(_('%d new tasks'), self.newTasksCount)
            self.disp().log(_('%d new efforts'), self.newEffortsCount)
            self.disp().log(_('%d modified categories'), self.modifiedCategoriesCount)
            self.disp().log(_('%d modified tasks'), self.modifiedTasksCount)
            self.disp().log(_('%d modified efforts'), self.modifiedEffortsCount)
            self.disp().log(_('%d deleted categories'), self.deletedCategoriesCount)
            self.disp().log(_('%d deleted tasks'), self.deletedTasksCount)
            self.disp().log(_('%d deleted efforts'), self.deletedEffortsCount)

        self.setState(TwoWayNewCategoriesState)


class TwoWayNewCategoriesState(BaseState):
    def init(self):
        super(TwoWayNewCategoriesState, self).init(('s' if self.version < 3 else 'sz'), self.newCategoriesCount)

    def handleNewObject(self, args):
        if self.version < 3:
            name = args
            parentId = None
        else:
            name, parentId = args
            self.disp().log(_('New category (parent: %s)'), parentId)

        if parentId is None:
            category = Category(name)
        else:
            category = self.categoryMap[parentId].newChild(name)

        self.disp().window.addIPhoneCategory(category)

        self.categoryMap[category.id()] = category
        self.pack('s', category.id())

    def finished(self):
        if self.version < 3:
            self.setState(TwoWayNewTasksState)
        else:
            self.setState(TwoWayDeletedCategoriesState)


class TwoWayDeletedCategoriesState(BaseState):
    def init(self):
        super(TwoWayDeletedCategoriesState, self).init('s', self.deletedCategoriesCount)

    def handleNewObject(self, catId):
        try:
            category = self.categoryMap.pop(catId)
        except KeyError:
            # Deleted on desktop
            pass
        else:
            self.disp().log(_('Delete category %s'), category.id())
            self.disp().window.removeIPhoneCategory(category)

    def finished(self):
        self.setState(TwoWayModifiedCategoriesState)


class TwoWayModifiedCategoriesState(BaseState):
    def init(self):
        super(TwoWayModifiedCategoriesState, self).init('ss', self.modifiedCategoriesCount)

    def handleNewObject(self, (name, catId)):
        try:
            category = self.categoryMap[catId]
        except KeyError:
            pass
        else:
            self.disp().log(_('Modify category %s'), category.id())
            self.disp().window.modifyIPhoneCategory(category, name)

    def finished(self):
        if self.version < 4:
            self.setState(TwoWayNewTasksState)
        else:
            self.setState(TwoWayNewTasksState4)


class TwoWayNewTasksState(BaseState):
    def init(self):
        super(TwoWayNewTasksState, self).init('ssddd[s]', self.newTasksCount)

    def handleNewObject(self, (subject, description, startDate, dueDate, completionDate, categories)):
        task = Task(subject=subject, description=description, startDate=startDate,
                    dueDate=dueDate, completionDate=completionDate)

        self.disp().window.addIPhoneTask(task, [self.categoryMap[catId] for catId in categories])
        self.disp().log(_('New task %s'), task.id())

        self.taskMap[task.id()] = task
        self.pack('s', task.id())

    def finished(self):
        self.setState(TwoWayDeletedTasksState)


class TwoWayNewTasksState4(BaseState):
    def init(self):
        super(TwoWayNewTasksState4, self).init('ssdddz[s]', self.newTasksCount)

    def handleNewObject(self, (subject, description, startDate, dueDate, completionDate, parentId, categories)):
        parent = self.taskMap[parentId] if parentId else None

        task = Task(subject=subject, description=description, startDate=startDate,
                    dueDate=dueDate, completionDate=completionDate, parent=parent)

        self.disp().window.addIPhoneTask(task, [self.categoryMap[catId] for catId in categories])
        self.disp().log(_('New task %s'), task.id())

        self.taskMap[task.id()] = task
        self.pack('s', task.id())

    def finished(self):
        self.setState(TwoWayDeletedTasksState)


class TwoWayDeletedTasksState(BaseState):
    def init(self):
        super(TwoWayDeletedTasksState, self).init('s', self.deletedTasksCount)

    def handleNewObject(self, taskId):
        try:
            task = self.taskMap.pop(taskId)
        except KeyError:
            pass
        else:
            self.disp().log(_('Delete task %s'), task.id())
            self.disp().window.removeIPhoneTask(task)

    def finished(self):
        self.setState(TwoWayModifiedTasks)


class TwoWayModifiedTasks(BaseState):
    def init(self):
        super(TwoWayModifiedTasks, self).init(('sssddd' if self.version < 2 else 'sssddd[s]'), self.modifiedTasksCount)

    def handleNewObject(self, args):
        if self.version < 2:
            subject, taskId, description, startDate, dueDate, completionDate = args
            categories = None
        else:
            subject, taskId, description, startDate, dueDate, completionDate, categories = args
            categories = [self.categoryMap[catId] for catId in categories]

        try:
            task = self.taskMap[taskId]
        except KeyError:
            pass
        else:
            self.disp().log(_('Modify task %s'), task.id())
            self.disp().window.modifyIPhoneTask(task, subject, description, startDate, dueDate, completionDate, categories)

    def finished(self):
        if self.version < 4:
            self.setState(FullFromDesktopState)
        else:
            self.setState(TwoWayNewEffortsState)


class TwoWayNewEffortsState(BaseState):
    def init(self):
        super(TwoWayNewEffortsState, self).init('sztt', self.newEffortsCount)

    def handleNewObject(self, (subject, taskId, started, ended)):
        task = None
        if taskId is not None:
            try:
                task = self.taskMap[taskId]
            except KeyError:
                pass

        effort = Effort(task, started, ended, subject=subject)
        self.disp().window.addIPhoneEffort(task, effort)
        self.disp().log(_('New effort %s'), effort.id())

        self.pack('s', effort.id())

        self.effortMap[effort.id()] = effort

    def finished(self):
        self.setState(TwoWayModifiedEffortsState)


class TwoWayModifiedEffortsState(BaseState):
    def init(self):
        super(TwoWayModifiedEffortsState, self).init('sstt', self.modifiedEffortsCount)

    def handleNewObject(self, (id_, subject, started, ended)):
        # Actually, the taskId cannot be modified on the device, which saves
        # us some headaches.

        try:
            effort = self.effortMap[id_]
        except KeyError:
            pass
        else:
            self.disp().log(_('Modify effort %s'), effort.id())
            self.disp().window.modifyIPhoneEffort(effort, subject, started, ended)

    def finished(self):
        # Efforts cannot be deleted on the iPhone yet.
        self.setState(FullFromDesktopState)


class SendGUIDState(BaseState):
    def init(self):
        super(SendGUIDState, self).init('i', 1)

        self.disp().log(_('Sending GUID: %s'), self.disp().window.taskFile.guid())
        self.pack('s', self.disp().window.taskFile.guid())

    def handleNewObject(self, code):
        pass

    def finished(self):
        self.disp().log(_('Finished.'))
        self.disp().close_when_done()
        self.dlg.Finished()

    def handleClose(self):
        pass
