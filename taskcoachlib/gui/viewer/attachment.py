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

import os, wx
from taskcoachlib import command, widgets
from taskcoachlib.domain import attachment
from taskcoachlib.i18n import _
from taskcoachlib.gui import uicommand, menu, dialog 
import base, mixin


class AttachmentViewer(mixin.AttachmentDropTargetMixin, base.ViewerWithColumns,
                       mixin.SortableViewerForAttachmentsMixin, 
                       mixin.SearchableViewerMixin, mixin.NoteColumnMixin,
                       base.ListViewer):
    SorterClass = attachment.AttachmentSorter
    viewerImages = base.ListViewer.viewerImages + ['fileopen', 'fileopen_red']

    def __init__(self, *args, **kwargs):
        self.attachments = kwargs.pop('attachmentsToShow')
        kwargs.setdefault('settingssection', 'attachmentviewer')
        super(AttachmentViewer, self).__init__(*args, **kwargs)
        
    def domainObjectsToView(self):
        return self.attachments

    def isShowingAttachments(self):
        return True
    
    def curselectionIsInstanceOf(self, class_):
        return class_ == attachment.Attachment

    def _addAttachments(self, attachments, index, **itemDialogKwargs):
        self.presentation().extend(attachments)

    def createWidget(self):
        imageList = self.createImageList()
        itemPopupMenu = menu.AttachmentPopupMenu(self.parent, self.settings,
            self.presentation(), self)
        columnPopupMenu = menu.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        self._columns = self._createColumns()
        widget = widgets.ListCtrl(self, self.columns(), self.onSelect,
            uicommand.AttachmentEdit(viewer=self, attachments=self.presentation()),
            itemPopupMenu, columnPopupMenu,
            resizeableColumn=1, **self.widgetCreationKeywordArguments())
        widget.SetColumnWidth(0, 150)
        widget.AssignImageList(imageList, wx.IMAGE_LIST_SMALL)
        return widget

    def _createColumns(self):
        return [widgets.Column('type', _('Type'), 
                               '',
                               width=self.getColumnWidth('type'),
                               imageIndexCallback=self.typeImageIndex,
                               renderCallback=lambda item: '',
                               resizeCallback=self.onResizeColumn),
                widgets.Column('subject', _('Subject'), 
                               attachment.Attachment.subjectChangedEventType(), 
                               sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                   value='subject',
                                   menuText=_('Sub&ject'), helpText=_('Sort by subject')),
                               width=self.getColumnWidth('subject'), 
                               renderCallback=lambda item: item.subject(),
                               resizeCallback=self.onResizeColumn),
                widgets.Column('description', _('Description'),
                               attachment.Attachment.subjectChangedEventType(),
                               sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                                   value='description',
                                   menuText=_('&Description'), helpText=_('Sort by description')),
                               width=self.getColumnWidth('description'),
                               renderCallback=lambda item: item.description(),
                               resizeCallback=self.onResizeColumn),
                widgets.Column('notes', '', 
                               attachment.Attachment.notesChangedEventType(), # pylint: disable-msg=E1101
                               width=self.getColumnWidth('notes'),
                               alignment=wx.LIST_FORMAT_LEFT,
                               imageIndexCallback=self.noteImageIndex,
                               headerImageIndex=self.imageIndex['note_icon'],
                               renderCallback=lambda item: '',
                               resizeCallback=self.onResizeColumn),
                ]

    def createColumnUICommands(self):
        return [\
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            uicommand.ViewColumn(menuText=_('&Description'),
                helpText=_('Show/hide description column'),
                setting='description', viewer=self),
            uicommand.ViewColumn(menuText=_('&Notes'),
                helpText=_('Show/hide notes column'),
                setting='notes', viewer=self)]

    def createToolBarUICommands(self):
        commands = super(AttachmentViewer, self).createToolBarUICommands()
        commands[-2:-2] = [None,
                           uicommand.AttachmentNew(attachments=self.presentation(),
                                                   settings=self.settings),
                           uicommand.AttachmentEdit(attachments=self.presentation(),
                                                    viewer=self),
                           uicommand.AttachmentDelete(attachments=self.presentation(),
                                                      viewer=self),
                           None,
                           uicommand.AttachmentOpen(attachments=attachment.AttachmentList(),
                                                    viewer=self)]
        return commands

    def typeImageIndex(self, anAttachment, which): # pylint: disable-msg=W0613
        if anAttachment.type_ == 'file':
            if os.path.exists(anAttachment.normalizedLocation()):
                return self.imageIndex['fileopen']
            return self.imageIndex['fileopen_red']

        try:
            return self.imageIndex[{ 'uri': 'earth_blue_icon',
                                     'mail': 'email'}[anAttachment.type_]]
        except KeyError:
            return -1
    
    def deleteItemCommand(self):
        return command.DeleteAttachmentCommand(self.presentation(), self.curselection())
    
    def itemEditorClass(self):
        return dialog.editor.AttachmentEditor

    def newItemCommandClass(self):
        return command.NewAttachmentCommand
    
    def editItemCommandClass(self):
        return command.EditAttachmentCommand

    def deleteItemCommandClass(self):
        return command.DeleteAttachmentCommand
