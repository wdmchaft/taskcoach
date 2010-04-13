'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>

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

import wx
from taskcoachlib import meta


defaults = { \
'view': { \
    'statusbar': 'True',
    'toolbar': '(22, 22)',
    'mainviewer': '0',               # Index of active viewer in main window
    'effortviewerintaskeditor': '0', # Index of active effort viewer in task editor
    'taskviewercount': '1',          # Number of task viewers in main window
    'categoryviewercount': '1',      # Number of category viewers in main window
    'noteviewercount': '0',          # Number of note viewers in main window
    'effortviewercount': '0',        # Number of effort viewers in main window
    'squaretaskviewercount': '0',
    'timelineviewercount': '0',
    'calendarviewercount': '0',
    'language': 'en_US',             # Language and locale
    'categoryfiltermatchall': 'False',
    'descriptionpopups': 'True',
    # The next three options are used in the effort dialog to populate the
    # drop down menu with start and stop times.
    'efforthourstart': '8',          # Earliest time, i.e. start of working day
    'efforthourend': '18',           # Last time, i.e. end of working day
    'effortminuteinterval': '15',    # Generate times with this interval
    'snoozetimes': "[5, 10, 15, 30, 60, 120, 1440]",
    'perspective': '',               # The layout of the viewers in the main window
    'tabbedmainwindow': 'False'},
'taskviewer': { \
    'title': '',                     # User supplied viewer title 
    'treemode': 'True',              # True = tree mode, False = list mode
    'sortby': 'dueDate',
    'sortascending': 'True',
    'sortbystatusfirst': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "['startDate', 'dueDate']",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28, 'notes': 28}",
    'columnautoresizing': 'True',
    'tasksdue': 'Unlimited',
    'hidecompletedtasks': 'False',
    'hideinactivetasks': 'False',
    'hideactivetasks': 'False',
    'hidecompositetasks': 'False' },
'squaretaskviewer': { \
    'title': '',
    'sortby': 'budget',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'tasksdue': 'Unlimited',
    'hidecompletedtasks': 'False',
    'hideinactivetasks': 'False',
    'hideactivetasks': 'False',
    'hidecompositetasks': 'False' },
'timelineviewer': { \
    'title': '',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'tasksdue': 'Unlimited',
    'hidecompletedtasks': 'False',
    'hideinactivetasks': 'False',
    'hideactivetasks': 'False',
    'hidecompositetasks': 'False' },
'calendarviewer': { \
    'title': '',
    'viewtype': '1',
    'viewdate': '',
    'gradient': 'False',
    'shownostart': 'False',
    'shownodue': 'False',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'tasksdue': 'Unlimited',
    'hidecompletedtasks': 'False',
    'hideinactivetasks': 'False',
    'hideactivetasks': 'False',
    'hidecompositetasks': 'False' },
'categoryviewer': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28, 'notes': 28}",
    'columnautoresizing': 'True' },
'categoryviewerintaskeditor': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28, 'notes': 28}",
    'columnautoresizing': 'True' },
'categoryviewerinnoteeditor': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28, 'notes': 28}",
    'columnautoresizing': 'True' },
'noteviewer': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{'attachments': 28}",
    'columnautoresizing': 'True' },
'noteviewerintaskeditor': {
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'columns': "['subject']",
    'columnsalwaysvisible': "['subject']",
    'columnwidths': "{}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False' },
'effortviewer': { \
    'title': '',
    'aggregation': 'details', # 'details' (default), 'day', 'week', or 'month'
    'columns': "['timeSpent', 'revenue']",
    'columnsalwaysvisible': "['period', 'task']",
    'columnwidths': "{'monday': 70, 'tuesday': 70, 'wednesday': 70, 'thursday': 70, 'friday': 70, 'saturday': 70, 'sunday': 70}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False' },
'effortviewerintaskeditor': { \
    'aggregation': 'details', # 'details' (default), 'day', 'week', or 'month'
    'columns': "['timeSpent', 'revenue']",
    'columnsalwaysvisible': "['period', 'task']",
    'columnwidths': "{}",
    'columnautoresizing': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False' },
'attachmentviewer': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['type', 'subject']",
    'columnwidths': "{'notes': 28, 'type': 28}",
    'columnautoresizing': 'True' },
'attachmentviewerintaskeditor': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['type', 'subject']",
    'columnwidths': "{'notes': 28, 'type': 28}",
    'columnautoresizing': 'True' },
'attachmentviewerinnoteeditor': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['type', 'subject']",
    'columnwidths': "{'notes': 28, 'type': 28}",
    'columnautoresizing': 'True' },
'attachmentviewerincategoryeditor': { \
    'title': '',
    'sortby': 'subject',
    'sortascending': 'True',
    'sortcasesensitive': 'True',
    'searchfilterstring': '',
    'searchfiltermatchcase': 'False',
    'searchfilterincludesubitems': 'False',
    'searchdescription': 'False',
    'columns': "[]",
    'columnsalwaysvisible': "['type', 'subject']",
    'columnwidths': "{'notes': 28, 'type': 28}",
    'columnautoresizing': 'True' },
'window': { \
    'size': '(700, 500)', # Default size of the main window
    'position': '(-1, -1)', # Position of the main window, undefined by default
    'iconized': 'False', # Don't start up iconized by default
    'maximized': 'False', # Don't start up maximized by default
    'starticonized': 'WhenClosedIconized', # 'Never', 'Always', 'WhenClosedIconized'
    'splash': 'True', # Show a splash screen while starting up
    'hidewheniconized': 'False', # Don't hide the window from the task bar
    'hidewhenclosed': 'False', # Close window quits the application
    'tips': 'True', # Show tips after starting up
    'tipsindex': '0', # Start at the first tip
    'blinktaskbariconwhentrackingeffort': 'True' },
'file': { \
    'recentfiles': '[]',
    'maxrecentfiles': '9',
    'lastfile': '',
    'autosave': 'False',
    'backup': 'False',
    'saveinifileinprogramdir': 'False',
    'attachmentbase': '',
    'inifileloaded': 'True',
    'inifileloaderror': ''
    },
'color': { \
    'activetasks': '(0, 0, 0, 255)',
    'completedtasks': '(0, 255, 0, 255)',
    'overduetasks': '(255, 0, 0, 255)',
    'inactivetasks': '(192, 192, 192, 255)',
    'duesoontasks': '(255, 128, 0, 255)' },
'editor': { \
    'maccheckspelling': 'True' },
'version': { \
    'python': '', # Filled in by the Settings class when saving the settings
    'wxpython': '', # Idem
    'pythonfrozen': '', # Idem
    'current': meta.data.version,
    'notified': meta.data.version,
    'notify': 'True' },
'behavior': { \
    'markparentcompletedwhenallchildrencompleted': 'True',
    'duesoondays': '1' },
'feature': { \
    'notes': 'True',
    'effort': 'True',
    'syncml': 'False',
    'iphone': 'False',
    'notifier': 'Native' },
'syncml': { \
    'url': '',
    'username': '',
    'preferredsyncmode': 'TWO_WAY',
    'verbose': 'True',
    'taskdbname': 'task',
    'notedbname': 'note',
    'synctasks': 'False',
    'syncnotes': 'False',
    'showwarning': 'True',
    },
'iphone': { \
    'password': '',
    'service': '',
    'synccompleted': 'True',
    'showlog': 'False',
    },
'printer': { \
    'margin_left': '0',
    'margin_top': '0',
    'margin_bottom': '0',
    'margin_right': '0',
    'paper_id': '0',
    'orientation': str(wx.PORTRAIT),
    },
}

minimum = { \
'view': { \
    'taskviewercount': '1' }
}
