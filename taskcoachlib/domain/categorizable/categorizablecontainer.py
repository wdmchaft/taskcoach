'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>

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

from taskcoachlib.domain import base
from taskcoachlib import patterns


class CategorizableContainer(base.Collection):
    def extend(self, items, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CategorizableContainer, self).extend(items, event)
        for item in self._compositesAndAllChildren(items):
            for category in item.categories():
                category.addCategorizable(item, event=event)
        if notify:
            event.send()
                
    def removeItems(self, items, event=None):
        notify = event is None
        event = event or patterns.Event()
        super(CategorizableContainer, self).removeItems(items, event)
        for item in self._compositesAndAllChildren(items):
            for category in item.categories():
                category.removeCategorizable(item, event=event)
        if notify:
            event.send()