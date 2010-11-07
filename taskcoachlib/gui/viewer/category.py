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
from taskcoachlib import patterns, command, widgets
from taskcoachlib.domain import category 
from taskcoachlib.i18n import _
from taskcoachlib.gui import uicommand, menu, dialog, render
import base, mixin


class BaseCategoryViewer(mixin.AttachmentDropTargetMixin, 
                         mixin.SortableViewerForCategoriesMixin, 
                         mixin.SearchableViewerMixin, 
                         mixin.NoteColumnMixin, mixin.AttachmentColumnMixin,
                         base.SortableViewerWithColumns, base.TreeViewer):
    SorterClass = category.CategorySorter
    defaultTitle = _('Categories')
    defaultBitmap = 'folder_blue_arrow_icon'
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('settingsSection', 'categoryviewer')
        super(BaseCategoryViewer, self).__init__(*args, **kwargs)
        for eventType in (category.Category.subjectChangedEventType(),
                          category.Category.filterChangedEventType(),
                          category.Category.foregroundColorChangedEventType(),
                          category.Category.backgroundColorChangedEventType(),
                          category.Category.fontChangedEventType(),
                          category.Category.iconChangedEventType(),
                          category.Category.selectedIconChangedEventType(),
                          category.Category.exclusiveSubcategoriesChangedEventType()):
            patterns.Publisher().registerObserver(self.onAttributeChanged, 
                eventType)

    def onEveryMinute(self, event):
        pass

    def domainObjectsToView(self):
        return self.taskFile.categories()
    
    def curselectionIsInstanceOf(self, class_):
        return class_ == category.Category
    
    def createWidget(self):
        imageList = self.createImageList() # Has side-effects
        self._columns = self._createColumns()
        itemPopupMenu = self.createCategoryPopupMenu()
        columnPopupMenu = menu.ColumnPopupMenu(self)
        self._popupMenus.extend([itemPopupMenu, columnPopupMenu])
        widget = widgets.CheckTreeCtrl(self, self._columns,
            self.onSelect, self.onCheck,
            uicommand.CategoryEdit(viewer=self, categories=self.presentation()),
            uicommand.CategoryDragAndDrop(viewer=self, categories=self.presentation()),
            uicommand.EditSubject(viewer=self),
            itemPopupMenu, columnPopupMenu,
            **self.widgetCreationKeywordArguments())
        widget.AssignImageList(imageList) # pylint: disable-msg=E1101
        return widget

    def createCategoryPopupMenu(self, localOnly=False):
        return menu.CategoryPopupMenu(self.parent, self.settings, self.taskFile,
                                      self, localOnly)

    def _createColumns(self):
        # pylint: disable-msg=W0142
        kwargs = dict(renderDescriptionCallback=lambda category: category.description(),
                      resizeCallback=self.onResizeColumn)
        columns = [widgets.Column('subject', _('Subject'), 
                       category.Category.subjectChangedEventType(),  
                       sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                           value='subject'),
                       imageIndexCallback=self.subjectImageIndex,
                       width=self.getColumnWidth('subject'), 
                       **kwargs),
                   widgets.Column('description', _('Description'), 
                       category.Category.descriptionChangedEventType(), 
                       sortCallback=uicommand.ViewerSortByCommand(viewer=self,
                           value='description'),
                       renderCallback=lambda category: category.description(), 
                       width=self.getColumnWidth('description'), 
                       **kwargs),
                   widgets.Column('attachments', '', 
                       category.Category.attachmentsChangedEventType(), # pylint: disable-msg=E1101
                       width=self.getColumnWidth('attachments'),
                       alignment=wx.LIST_FORMAT_LEFT,
                       imageIndexCallback=self.attachmentImageIndex,
                       headerImageIndex=self.imageIndex['paperclip_icon'],
                       renderCallback=lambda category: '', **kwargs)]
        if self.settings.getboolean('feature', 'notes'):
            columns.append(widgets.Column('notes', '', 
                       category.Category.notesChangedEventType(), # pylint: disable-msg=E1101
                       width=self.getColumnWidth('notes'),
                       alignment=wx.LIST_FORMAT_LEFT,
                       imageIndexCallback=self.noteImageIndex,
                       headerImageIndex=self.imageIndex['note_icon'],
                       renderCallback=lambda category: '', **kwargs))
        return columns

    def getImageIndices(self, category):
        bitmap = category.icon(recursive=True)
        bitmap_selected = category.selectedIcon(recursive=True) or bitmap
        return self.imageIndex[bitmap] if bitmap else -1, self.imageIndex[bitmap_selected] if bitmap_selected else -1

    def subjectImageIndex(self, category, which):
        normalImageIndex, expandedImageIndex = self.getImageIndices(category)
        expanded = which in [wx.TreeItemIcon_Expanded,
                             wx.TreeItemIcon_SelectedExpanded]
        return expandedImageIndex if expanded else normalImageIndex
    
    def createToolBarUICommands(self):
        commands = super(BaseCategoryViewer, self).createToolBarUICommands()
        commands[-2:-2] = [None,
                           uicommand.CategoryNew(categories=self.presentation(),
                                                 settings=self.settings),
                           uicommand.CategoryNewSubCategory(categories=self.presentation(),
                                                            viewer=self),
                           uicommand.CategoryEdit(categories=self.presentation(),
                                                  viewer=self),
                           uicommand.CategoryDelete(categories=self.presentation(),
                                                    viewer=self)]
        return commands

    def createColumnUICommands(self):
        commands = [\
            uicommand.ToggleAutoColumnResizing(viewer=self,
                                               settings=self.settings),
            None,
            uicommand.ViewColumn(menuText=_('&Description'),
                helpText=_('Show/hide description column'),
                setting='description', viewer=self),
            uicommand.ViewColumn(menuText=_('&Attachments'),
                helpText=_('Show/hide attachments column'),
                setting='attachments', viewer=self)]
        if self.settings.getboolean('feature', 'notes'):
            commands.append(uicommand.ViewColumn(menuText=_('&Notes'),
                helpText=_('Show/hide notes column'),
                setting='notes', viewer=self))
        return commands

    def onAttributeChanged(self, event):
        if category.Category.exclusiveSubcategoriesChangedEventType() in event.types():
            # We need to refresh the children of the changed item as well 
            # because they have to use radio buttons instead of checkboxes, or
            # vice versa:
            items = event.sources()
            for item in items.copy():
                items |= set(item.children())
            self.widget.RefreshItems(*items) 
        else:
            super(BaseCategoryViewer, self).onAttributeChanged(event)
        
    def onCheck(self, event):
        categoryToFilter = self.widget.GetItemPyData(event.GetItem())
        categoryToFilter.setFiltered(event.GetItem().IsChecked())
        self.onSelect(event) # Notify status bar
        
    def getIsItemChecked(self, item):
        if isinstance(item, category.Category):
            return item.isFiltered()
        return False

    def getItemParentHasExclusiveChildren(self, item):
        parent = item.parent()
        return parent and parent.hasExclusiveSubcategories()
    
    def isShowingCategories(self):
        return True

    def statusMessages(self):
        status1 = _('Categories: %d selected, %d total')%\
            (len(self.curselection()), len(self.presentation()))
        filteredCategories = self.presentation().filteredCategories()
        status2 = _('Status: %d filtered')%len(filteredCategories)
        return status1, status2
        
    def itemEditorClass(self):
        return dialog.editor.CategoryEditor

    def newItemCommandClass(self):
        return command.NewCategoryCommand
    
    def editItemCommandClass(self):
        return command.EditCategoryCommand
    
    def newSubItemCommandClass(self):
        return command.NewSubCategoryCommand

    def deleteItemCommandClass(self):
        return command.DeleteCategoryCommand
    

class CategoryViewer(BaseCategoryViewer):
    def __init__(self, *args, **kwargs):
        super(CategoryViewer, self).__init__(*args, **kwargs)
        self.filterUICommand.setChoice(self.settings.getboolean('view',
            'categoryfiltermatchall'))

    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this viewer. '''
        toolBarUICommands = super(CategoryViewer, self).getToolBarUICommands()
        toolBarUICommands.insert(-2, None) # Separator
        # pylint: disable-msg=W0201
        self.filterUICommand = \
            uicommand.CategoryViewerFilterChoice(settings=self.settings)
        toolBarUICommands.insert(-2, self.filterUICommand)
        return toolBarUICommands
