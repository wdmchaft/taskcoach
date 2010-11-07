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

from taskcoachlib import patterns


class Attribute(object):
    def __init__(self, value, owner, setEvent):
        self.__value = value
        self.__owner = owner
        self.__setEvent = setEvent
        
    def get(self):
        return self.__value
    
    @patterns.eventSource
    def set(self, value, event=None):
        if value == self.__value:
            return
        self.__value = value
        self.__setEvent(event)
           

class SetAttribute(object):
    def __init__(self, values, owner, addEvent=None, removeEvent=None, changeEvent=None):
        self.__set = set(values) if values else set()
        self.__owner = owner
        self.__addEvent = addEvent or self.__nullEvent
        self.__removeEvent = removeEvent or self.__nullEvent
        self.__changeEvent = changeEvent or self.__nullEvent
        
    def get(self):
        return self.__set.copy()
    
    @patterns.eventSource
    def set(self, values, event=None):
        if values == self.__set:
            return
        added = values - self.__set
        removed = self.__set - values
        self.__set = values
        if added:
            self.__addEvent(event, *added) # pylint: disable-msg=W0142
        if removed:
            self.__removeEvent(event, *removed) # pylint: disable-msg=W0142
        if added or removed:
            self.__changeEvent(event, *self.__set)

    @patterns.eventSource            
    def add(self, values, event=None):
        if values <= self.__set:
            return
        self.__set |= values
        self.__addEvent(event, *values) # pylint: disable-msg=W0142
        self.__changeEvent(event, *self.__set)
        
    @patterns.eventSource                    
    def remove(self, values, event=None):
        if values & self.__set == set():
            return
        self.__set -= values
        self.__removeEvent(event, *values) # pylint: disable-msg=W0142
        self.__changeEvent(event, *self.__set)
        
    def __nullEvent(self, *args, **kwargs):
        pass