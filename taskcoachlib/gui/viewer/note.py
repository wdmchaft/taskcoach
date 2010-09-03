# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Thomas Sonne Olesen <tpo@sonnet.dk>

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
from taskcoachlib import patterns, command, widgets, domain
from taskcoachlib.domain import note
from taskcoachlib.i18n import _
from taskcoachlib.gui import uicommand, menu, dialog
import base, mixin

class BaseNoteViewer(mixin.AttachmentDropTargetMixin, 
                     mixin.SearchableViewerMixin, 
                     mixin.SortableViewerForNotesMixin,
                     mixin.AttachmentColumnMixin, 
                     base.SortableViewerWithColumns, base.TreeViewer):
    SorterClass = note.NoteSorter
    defaultTitle = _('Notes')
    defaultBitmap = 'note_icon'
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'noteviewer')
        self.notesToShow = kwargs.get('notesToShow', None)
        super(BaseNoteViewer, self).__init__(*args, **kwargs)
        for eventType in (note.Note.subjectChangedEventType(),
                          note.Note.foregroundColorChangedEventType(),
                          note.Note.backgroundColorChangedEventType(),
                          note.Note.fontChangedEventType(),
                          note.Note.iconChangedEventType(),
                          note.Note.selectedIconChangedEventType()):
            patterns.Publisher().registerObserver(self.onAttributeChanged, 
                                                  eventType)

    def onEveryMinute(self, event):
        pass

    def domainObjectsToView(self):
        if self.notesToShow is None:
            return self.taskFile.notes()
        else:
            return self.notesToShow

    def curselectionIsInstanceOf(self, class_):
        return class_ == note.Note

    def createWidget(self):
        imageList = self.createImageList() # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = menu.NotePopupMenu(self.parent, self.settings,
            self.presentation(), self.taskFile.categories(), self)
        columnPopupMenu = menu.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        widget = widgets.TreeListCtrl(self, self.columns(), self.onSelect,
            uicommand.NoteEdit(viewer=self, notes=self.presentation()),
            uicommand.NoteDragAndDrop(viewer=self, notes=self.presentation()),
            uicommand.EditSubject(viewer=self),
            itemPopupMenu, columnPopupMenu,
            **self.widgetCreationKeywordArguments())
        widget.AssignImageList(imageList) # pylint: disable-msg=E1101
        return widget
    
    def createFilter(self, notes):
        notes = super(BaseNoteViewer, self).createFilter(notes)
        return domain.base.DeletedFilter(notes)

    def createToolBarUICommands(self):
        commands = super(BaseNoteViewer, self).createToolBarUICommands()
        commands[-2:-2] = [None,
                           uicommand.NoteNew(notes=self.presentation(),
                                             settings=self.settings),
                           uicommand.NoteNewSubNote(notes=self.presentation(),
                                                    viewer=self),
                           uicommand.NoteEdit(notes=self.presentation(),
                                              viewer=self),
                           uicommand.NoteDelete(notes=self.presentation(),
                                                viewer=self)]
        return commands

    def createColumnUICommands(self):
        return [\
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            uicommand.ViewColumn(menuText=_('&Description'),
                helpText=_('Show/hide description column'),
                setting='description', viewer=self),
            uicommand.ViewColumn(menuText=_('&Attachments'),
                helpText=_('Show/hide attachments column'),
                setting='attachments', viewer=self),
            uicommand.ViewColumn(menuText=_('&Categories'),
                helpText=_('Show/hide categories column'),
                setting='categories', viewer=self),
            uicommand.ViewColumn(menuText=_('Overall categories'),
                helpText=_('Show/hide overall categories column'),
                setting='totalCategories', viewer=self)]

    def _createColumns(self):
        columns = [widgets.Column(name, columnHeader,
                width=self.getColumnWidth(name), 
                resizeCallback=self.onResizeColumn,
                renderCallback=renderCallback, 
                sortCallback=uicommand.ViewerSortByCommand(viewer=self, 
                    value=name.lower(), menuText=sortMenuText, 
                    helpText=sortHelpText),
                imageIndexCallback=self.subjectImageIndex,
                *eventTypes) \
            for name, columnHeader, sortMenuText, sortHelpText, eventTypes, renderCallback in \
            ('subject', _('Subject'), _('&Subject'), _('Sort notes by subject'), 
                (note.Note.subjectChangedEventType(),), 
                lambda note: note.subject(recursive=False)),
            ('description', _('Description'), _('&Description'), 
                _('Sort notes by description'), 
                (note.Note.descriptionChangedEventType(),), 
                lambda note: note.description()),
            ('categories', _('Categories'), _('&Categories'), 
                _('Sort notes by categories'), 
                (note.Note.categoryAddedEventType(), 
                 note.Note.categoryRemovedEventType(), 
                 note.Note.categorySubjectChangedEventType()), 
                self.renderCategory),
            ('totalCategories', _('Overall categories'), 
                _('&Overall categories'), _('Sort notes by overall categories'),
                 (note.Note.totalCategoryAddedEventType(),
                  note.Note.totalCategoryRemovedEventType(),
                  note.Note.totalCategorySubjectChangedEventType()), 
                 self.renderCategory)]
        attachmentsColumn = widgets.Column('attachments', '', 
            note.Note.attachmentsChangedEventType(), # pylint: disable-msg=E1101
            width=self.getColumnWidth('attachments'),
            alignment=wx.LIST_FORMAT_LEFT,
            imageIndexCallback=self.attachmentImageIndex,
            headerImageIndex=self.imageIndex['paperclip_icon'],
            renderCallback=lambda note: '')
        columns.insert(2, attachmentsColumn)
        return columns

    def getImageIndices(self, note):
        bitmap = note.icon(recursive=True)
        bitmap_selected = note.selectedIcon(recursive=True) or bitmap
        return self.imageIndex[bitmap] if bitmap else -1, self.imageIndex[bitmap_selected] if bitmap_selected else -1

    def subjectImageIndex(self, note, which):
        normalImageIndex, expandedImageIndex = self.getImageIndices(note)
        expanded = which in [wx.TreeItemIcon_Expanded,
                             wx.TreeItemIcon_SelectedExpanded]
        return expandedImageIndex if expanded else normalImageIndex
    
    def getItemTooltipData(self, item, column=0):
        if self.settings.getboolean('view', 'descriptionpopups'):
            lines = [line.rstrip('\r') for line in item.description().split('\n')] 
            result = [(None, lines)] if lines and lines != [''] else [] 
            result.append(('paperclip_icon', sorted([unicode(attachment) for attachment in item.attachments()])))
            return result
        else:
            return []
                    
    def isShowingNotes(self):
        return True

    def statusMessages(self):
        status1 = _('Notes: %d selected, %d total')%\
            (len(self.curselection()), len(self.presentation()))
        status2 = _('Status: n/a')
        return status1, status2

    def newItemDialog(self, *args, **kwargs):
        kwargs['categories'] = self.taskFile.categories().filteredCategories()
        return super(BaseNoteViewer, self).newItemDialog(*args, **kwargs)
    
    def deleteItemCommand(self):
        return command.DeleteNoteCommand(self.presentation(), self.curselection(),
                  shadow=self.settings.getboolean('feature', 'syncml'))
        
    def itemEditorClass(self):
        return dialog.editor.NoteEditor

    def newItemCommandClass(self):
        return command.NewNoteCommand
    
    def newSubItemCommandClass(self):
        return command.NewSubNoteCommand

    def editItemCommandClass(self):
        return command.EditNoteCommand


class NoteViewer(mixin.FilterableViewerForNotesMixin, BaseNoteViewer): 
    pass
