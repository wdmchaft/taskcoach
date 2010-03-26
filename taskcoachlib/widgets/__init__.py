'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2007 Jerome Laheurte <fraca7@free.fr>

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

from notebook import Notebook, Choicebook, Listbook, AUINotebook, BookPage, \
    BoxedBookPage, AuiManagedFrameWithNotebookAPI
from dialog import Dialog, NotebookDialog, ListbookDialog, HTMLDialog, \
    AttachmentSelector
from buttonbox import ButtonBox
from itemctrl import Column
from listctrl import ListCtrl
from treectrl import CheckTreeCtrl, TreeListCtrl
from squaremap import SquareMap
from timeline import Timeline
from datectrl import DateCtrl, DateTimeCtrl, DatePickerCtrl
from textctrl import SingleLineTextCtrl, SingleLineTextCtrlWithEnterButton, \
    MultiLineTextCtrl, StaticTextWithToolTip
from panel import PanelWithBoxSizer, BoxWithFlexGridSizer, BoxWithBoxSizer
from colorselect import ColorSelect
from searchctrl import SearchCtrl
from spinctrl import SpinCtrl
from tooltip import ToolTipMixin, SimpleToolTip
from dirchooser import DirectoryChooser
from fontpicker import FontPickerCtrl
from syncmlwarning import SyncMLWarningDialog
from calendar import Calendar
import masked
try:
    from wx.lib import sized_controls
except ImportError:
    try:
        from wxaddons import sized_controls
    except ImportError:
        from taskcoachlib.thirdparty import sized_controls
