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

'''
This module defines classes and functions to handle the VCalendar
format.
''' # pylint: disable-msg=W0105

from taskcoachlib.domain.base import Object
from taskcoachlib.domain import date
from taskcoachlib.i18n import _

import time, calendar, datetime

#{ Utility functions

def parseDateTime(fulldate):
    ''' Parses a datetime as seen in iCalendar files into a 
    L{taskcoachlib.domain.date.DateTime} object. '''

    dt, tm = fulldate.split('T')
    year, month, day = int(dt[:4]), int(dt[4:6]), int(dt[6:8])
    hour, minute, second = int(tm[:2]), int(tm[2:4]), int(tm[4:6])

    if fulldate.endswith('Z'):
        # GMT. Convert this to local time.
        localTime = time.localtime(calendar.timegm((year, month, day, hour, minute, second, 0, 0, -1)))
        year, month, day, hour, minute, second = localTime[:6]

    return date.DateTime(year, month, day, hour, minute, second)

def fmtDate(dt):
    ''' Formats a L{taskcoachlib.domain.date.Date} object to a string
    suitable for inclusion in an iCcalendar file. '''
    return '%04d%02d%02dT000000' % (dt.year, dt.month, dt.day)

def fmtDateTime(dt):
    ''' Formats a L{taskcoachlib.domain.date.DateTime} object to a string
    suitable for inclusion in an iCalendar file. '''
    return '%04d%02d%02dT%02d%02d%02d' % (dt.year, dt.month, dt.day,
                                          dt.hour, dt.minute, dt.second)

def quoteString(s):
    ''' The 'quoted-printable' codec doesn't encode \n, but tries to
    fold lines with \n instead of CRLF and generally does strange
    things that ScheduleWorld does not understand (me neither, to an
    extent). Same thing with \r. This function works around this. '''

    s = s.encode('UTF-8').encode('quoted-printable')
    s = s.replace('=\r', '')
    s = s.replace('=\n', '')
    s = s.replace('\r', '=0D')
    s = s.replace('\n', '=0A')
    return s

#}

#{ Parsing iCalendar files

class VCalendarParser(object):
    ''' Base parser class for iCalendar files. This uses the State
    pattern (in its Python incarnation, replacing the class of an
    object at runtime) in order to parse different objects in the
    VCALENDAR. Other states are

     - VTodoParser: parses VTODO objects.

    @ivar kwargs: While parsing, the keyword arguments for the
        domain object creation for the current (parsed) object.
    @ivar tasks: A list of dictionaries suitable to use as
        keyword arguments for task creation, representing all
        VTODO object in the parsed file. ''' # pylint: disable-msg=W0511

    def __init__(self, *args, **kwargs):
        super(VCalendarParser, self).__init__(*args, **kwargs)
        self.stateMap = { 'VCALENDAR': VCalendarParser,
                          'VTODO':     VTodoParser }
        self.tasks = []
        self.init()

    def init(self):
        ''' Called after a state change. '''
        self.kwargs = {} # pylint: disable-msg=W0201

    def setState(self, state):
        ''' Sets the state (class) of the parser object. '''
        self.__class__ = state
        self.init()

    def parse(self, lines):
        ''' Actually parses the file.
        @param lines: A list of lines. '''

        # TODO: avoid using indexes here, just iterate. This way the
        # method can accept a file object as argument.

        currentLine = lines[0]

        for line in lines[1:]:
            if line.startswith(' ') or line.startswith('\t'):
                currentLine += line[1:]
            else:
                if self.handleLine(currentLine):
                    return
                currentLine = line

        self.handleLine(currentLine)

    def handleLine(self, line):
        ''' Called by L{parse} for each line to parse. L{parse} is
        supposed to have handled the unfolding. '''

        if line.startswith('BEGIN:'):
            try:
                self.setState(self.stateMap[line[6:]])
            except KeyError:
                raise TypeError, 'Unrecognized vcal type: %s' % line[6:]
        elif line.startswith('END:'):
            if line[4:] == 'VCALENDAR':
                return True
            else:
                self.onFinish()
                self.setState(VCalendarParser)
        else:
            try:
                idx = line.index(':')
            except ValueError:
                raise RuntimeError, 'Malformed vcal line: %s' % line

            details, value = line[:idx].split(';'), line[idx + 1:]
            name, specs = details[0], details[1:]
            specs = dict([tuple(v.split('=')) for v in specs])

            if specs.has_key('ENCODING'):
                value = value.decode(specs['ENCODING'].lower())
            if specs.has_key('CHARSET'):
                value = value.decode(specs['CHARSET'].lower())
            else:
                # Some  servers only  specify CHARSET  when  there are
                # non-ASCII characters :)
                value = value.decode('ascii')

            # If  an item  name ends  with  'TMPL', it's  part of  the
            # template system and has to be eval()ed.

            if name.endswith('TMPL'):
                name = name[:-4]
                context = dict()
                context.update(datetime.__dict__)
                context.update(date.__dict__)
                context['_'] = _
                value = eval(value, context)
                if isinstance(value, datetime.datetime):
                    value = fmtDateTime(value)

            self.acceptItem(name, value)

        return False

    def onFinish(self):
        ''' This method is called when the current object ends. '''
        raise NotImplementedError

    def acceptItem(self, name, value):
        ''' Called on each new 'item', i.e. key/value pair. Default
        behaviour is to store the pair in the 'kwargs' instance
        variable (which is emptied in L{init}). '''
        self.kwargs[name.lower()] = value


class VTodoParser(VCalendarParser):
    ''' This is the state responsible for parsing VTODO objects. ''' # pylint: disable-msg=W0511

    def onFinish(self):
        if not self.kwargs.has_key('startDateTime'):
            # This means no start date, but the task constructor will
            # take today by default, so force.
            self.kwargs['startDateTime'] = date.DateTime()

        if self.kwargs.has_key('vcardStatus'):
            if self.kwargs['vcardStatus'] == 'COMPLETED' and \
                   not self.kwargs.has_key('completionDateTime'):
                # Some servers only give the status, and not the date (SW)
                if self.kwargs.has_key('last-modified'):
                    self.kwargs['completionDateTime'] = parseDateTime(self.kwargs['last-modified'])
                else:
                    self.kwargs['completionDateTime'] = date.Now()

        self.kwargs['status'] = Object.STATUS_NONE
        self.tasks.append(self.kwargs)

    def acceptItem(self, name, value):
        if name == 'DTSTART':
            self.kwargs['startDateTime'] = parseDateTime(value)
        elif name == 'DUE':
            self.kwargs['dueDateTime'] = parseDateTime(value)
        elif name == 'COMPLETED':
            self.kwargs['completionDateTime'] = parseDateTime(value)
        elif name == 'UID':
            self.kwargs['id'] = value.decode('UTF-8')
        elif name == 'PRIORITY':
            # Okay. Seems that in vcal,  the priority ranges from 1 to
            # 3, but what it means depends on the other client...

            self.kwargs['priority'] = int(value) - 1
        elif name == 'SUMMARY':
            self.kwargs['subject'] = value
        elif name == 'CATEGORIES':
            self.kwargs['categories'] = value.split(',')
        elif name == 'STATUS':
            self.kwargs['vcardStatus'] = value
        else:
            super(VTodoParser, self).acceptItem(name, value)

#}

#==============================================================================
#{ Generating iCalendar files.

def VCalFromTask(task, encoding=True):
    ''' This function returns a string representing the task in
        iCalendar format. '''

    encoding = ';CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE' if encoding else ''
    quote = quoteString if encoding else lambda s: s

    components = []
    components.append('BEGIN:VTODO') # pylint: disable-msg=W0511
    components.append('UID:%s' % task.id().encode('UTF-8'))

    if task.startDateTime() != date.DateTime():
        components.append('DTSTART:%s'%fmtDateTime(task.startDateTime()))

    if task.dueDateTime() != date.DateTime():
        components.append('DUE:%s'%fmtDateTime(task.dueDateTime()))

    if task.completionDateTime() != date.DateTime():
        components.append('COMPLETED:%s'%fmtDateTime(task.completionDateTime()))

    if task.categories(True):
        categories = ','.join([quote(unicode(c)) for c in task.categories(True)])
        components.append('CATEGORIES%s:%s'%(encoding, categories))

    if task.completed():
        components.append('STATUS:COMPLETED')
    elif task.active():
        components.append('STATUS:NEEDS-ACTION')
    else:
        components.append('STATUS:CANCELLED') # Hum...

    components.append('DESCRIPTION%s:%s'%(encoding, quote(task.description())))
    components.append('PRIORITY:%d'%min(3, task.priority() + 1))
    components.append('SUMMARY%s:%s'%(encoding, quote(task.subject())))
    components.append('END:VTODO') # pylint: disable-msg=W0511

    return fold(components)

#}

def VCalFromEffort(effort, encoding=True):
    encoding = ';CHARSET=UTF-8;ENCODING=QUOTED-PRINTABLE' if encoding else ''
    quote = quoteString if encoding else lambda s: s
    components = []
    components.append('BEGIN:VEVENT')
    components.append('UID:%s' % effort.id().encode('UTF-8'))
    components.append('SUMMARY%s:%s'%(encoding, quote(effort.subject())))
    components.append('DESCRIPTION%s:%s'%(encoding, quote(effort.description())))
    components.append('DTSTART:%s'%fmtDateTime(effort.getStart()))
    if effort.getStop():
        components.append('DTEND:%s'%fmtDateTime(effort.getStop()))
    components.append('END:VEVENT')
    return fold(components)


def fold(components, linewidth=75, eol='\r\n', indent=' '):
    lines = []
    # The iCalendar standard doesn't clearly state whether the maximum line 
    # width includes the indentation or not. We keep on the safe side:
    indentedlinewidth = linewidth - len(indent)
    for component in components:
        componentLines = component.split('\n')
        firstLine = componentLines[0]
        firstLine, remainderFirstLine = firstLine[:linewidth], firstLine[linewidth:]
        lines.append(firstLine)
        while remainderFirstLine:
            nextLine, remainderFirstLine = remainderFirstLine[:indentedlinewidth], remainderFirstLine[indentedlinewidth:]
            lines.append(indent + nextLine)
        for line in componentLines[1:]:
            nextLine, remainder = line[:linewidth], line[linewidth:]
            lines.append(indent + nextLine)
            while remainder:
                nextLine, remainder = remainder[:indentedlinewidth], remainder[indentedlinewidth:]
                lines.append(indent + nextLine)
    return eol.join(lines) + eol if lines else ''
