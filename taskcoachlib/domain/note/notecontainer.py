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

from taskcoachlib.domain import categorizable
from taskcoachlib.i18n import _


class NoteContainer(categorizable.CategorizableContainer):
    newItemMenuText = _('New note...')
    newItemHelpText =  _('Insert a new note')
    editItemMenuText = _('Edit note...')
    editItemHelpText = _('Edit the selected notes')
    deleteItemMenuText = _('Delete note')
    deleteItemHelpText = _('Delete the selected notes')
    newSubItemMenuText = _('New subnote...')
    newSubItemHelpText = _('Insert a new subnote')
