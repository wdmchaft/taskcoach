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
import note


class NoteSorter(base.TreeSorter):
    DomainObjectClass = note.Note
    EventTypePrefix = 'note'
                        
    def createSortKeyFunction(self):
        sortKeyName = self._sortKey
        if not self._sortCaseSensitive and sortKeyName in ('subject', 'description'):
            prepareSortValue = lambda stringOrUnicode: stringOrUnicode.lower()
        elif sortKeyName in ('categories', 'totalCategories'):
            prepareSortValue = lambda categories: sorted([category.subject(recursive=True) for category in categories])
        else:
            prepareSortValue = lambda value: value
        kwargs = {}
        if sortKeyName.startswith('total'):
            kwargs['recursive'] = True
            sortKeyName = sortKeyName.replace('total', '')
            sortKeyName = sortKeyName[0].lower() + sortKeyName[1:]
        # pylint: disable-msg=W0142
        return lambda note: [prepareSortValue(getattr(note, 
            sortKeyName)(**kwargs))]
    


