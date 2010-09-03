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

import wx
from taskcoachlib import meta
from taskcoachlib.i18n import _


tips = [
_('''%(name)s is actively developed. Although the %(name)s developers try hard to prevent them, bugs do happen. So, backing up your work on a regular basis is strongly advised.''')%meta.metaDict,
_('''%(name)s has a mailinglist where you can discuss usage of %(name)s with fellow users, discuss and request features and complain about bugs. Go to %(url)s and join today!''')%meta.metaDict, 
_('''%(name)s has unlimited undo and redo. Any change that you make, be it editing a task description, or deleting an effort record, is undoable. Select 'Edit' -> 'Undo' and 'Edit' -> 'Redo' to go backwards and forwards through your edit history.''')%meta.metaDict, 
_('''%(name)s is available in a number of different languages. Select 'Edit' -> 'Preferences' to see whether your language is one of them. If your language is not available or the translation needs improvement, please consider helping with the translation of %(name)s. Visit %(url)s for more information about how you can help.''')%meta.metaDict,
_('''If you enter a URL (e.g. %(url)s) in a task or effort description, it becomes a link. Clicking on the link will open the URL in your default web browser.''')%meta.metaDict,
_('''You can drag and drop tasks in the tree view to rearrange parent-child relationships between tasks. The same goes for categories.'''),
_('''You can drag files from a file browser onto a task to create attachments. Dragging the files over a tab will raise the appropriate page, dragging the files over a collapsed task (the boxed + sign) in the tree view will expand the task to show its subtasks.'''),
_('''You can create any viewer layout you want by dragging and dropping the tabs. Unfortunately, due to a limitation of the current version of the graphical toolkit (wxPython), the layout cannot be saved for reuse in the next session.'''),
_('''What is actually printed when you select 'File' -> 'Print' depends on the current view. If the current view shows the task list, a list of tasks will be printed, if the current view shows effort grouped by month, that will be printed. The same goes for visible columns, sort order, filtered tasks, etc.'''),
_('''Left-click a column header to sort by that column. Click the column header again to change the sort order from ascending to descending and back again. Right-click a column header to hide that column or make additional columns visible.'''),
_('''You can turn off some features, such as notes and effort tracking, in the Preferences dialog. Features turned off are not accessible via the user interface, resulting in a 'smaller' user interface.'''),
_('''You can create a template from a task in order to reduce typing when repetitive patterns emerge.'''),
_('''Ctrl-Tab switches between tabs in edit dialogs.''')
]


class TipProvider(wx.PyTipProvider):
    def __init__(self, tipIndex):
        super(TipProvider, self).__init__(tipIndex)
        self.__tipIndex = tipIndex
        
    def GetTip(self): # pylint: disable-msg=W0221
        tip = tips[self.__tipIndex]
        self.__tipIndex += 1
        if self.__tipIndex >= len(tips):
            self.__tipIndex = 0
        return tip
    
    def GetCurrentTip(self): # pylint: disable-msg=W0221
        return self.__tipIndex

        
def showTips(parent, settings):
    tipProvider = TipProvider(settings.getint('window', 'tipsindex'))
    keepShowingTips = wx.ShowTip(parent, tipProvider)
    settings.set('window', 'tips', str(keepShowingTips))
    settings.set('window', 'tipsindex', str(tipProvider.GetCurrentTip()))

