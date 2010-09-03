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

import wx, os
from taskcoachlib import patterns
from taskcoachlib.domain import task, base, category
from taskcoachlib.i18n import _
import uicommand, viewer


class Menu(wx.Menu, uicommand.UICommandContainerMixin):
    def __init__(self, window):
        super(Menu, self).__init__()
        self._window = window
        
    def __len__(self):
        return self.GetMenuItemCount()

    def appendUICommand(self, uiCommand):
        return uiCommand.addToMenu(self, self._window)
    
    def appendMenu(self, text, subMenu, bitmap=None):
        subMenuItem = wx.MenuItem(self, id=wx.NewId(), text=text, subMenu=subMenu)
        if not bitmap and '__WXMSW__' in wx.PlatformInfo:
            # hack to force a 16 bit margin. SetMarginWidth doesn't work
            bitmap = 'nobitmap'
        if bitmap:
            subMenuItem.SetBitmap(wx.ArtProvider_GetBitmap(bitmap, 
                wx.ART_MENU, (16,16)))
        self.AppendItem(subMenuItem)

    def invokeMenuItem(self, menuItem):
        ''' Programmatically invoke the menuItem. This is mainly for testing 
            purposes. '''
        self._window.ProcessEvent(wx.CommandEvent( \
            wx.wxEVT_COMMAND_MENU_SELECTED, winid=menuItem.GetId()))
    
    def openMenu(self):
        ''' Programmatically open the menu. This is mainly for testing 
            purposes. '''
        # On Mac OSX, an explicit UpdateWindowUI is needed to ensure that
        # menu items are updated before the menu is opened. This is not needed
        # on other platforms, but it doesn't hurt either.
        self._window.UpdateWindowUI() 
        self._window.ProcessEvent(wx.MenuEvent(wx.wxEVT_MENU_OPEN, menu=self))


class DynamicMenu(Menu):
    ''' A menu that registers for events and then updates itself whenever the
        event is fired. '''
    def __init__(self, window, parentMenu=None, labelInParentMenu=''):
        ''' Initialize the menu. labelInParentMenu is needed to be able to
            find this menu in its parentMenu. '''
        super(DynamicMenu, self).__init__(window)
        self._parentMenu = parentMenu
        self._labelInParentMenu = self.__GetLabelText(labelInParentMenu)
        self.registerForMenuUpdate()
        self.updateMenu()
         
    def registerForMenuUpdate(self):
        ''' Subclasses are responsible for binding an event to onUpdateMenu so
            that the menu gets a chance to update itself at the right time. '''
        raise NotImplementedError

    def onUpdateMenu(self, event):
        ''' This event handler should be called at the right times so that
            the menu has a chance to update itself. '''
        # If this is called by wx, 'skip' the event so that other event
        # handlers get a chance too:
        if hasattr(event, 'Skip'):
            event.Skip()
        try: # Prepare for menu or window to be destroyed
            self.updateMenu()
        except wx.PyDeadObjectError:
            pass
        
    def updateMenu(self):
        ''' Updating the menu consists of two steps: updating the menu item
            of this menu in its parent menu, e.g. to enable or disable it, and
            updating the menu items of this menu. '''
        self.updateMenuItemInParentMenu()
        self.updateMenuItems()
        
    def clearMenu(self):
        ''' Remove all menu items. '''
        for menuItem in self.MenuItems:
            self.DestroyItem(menuItem)       
            
    def updateMenuItemInParentMenu(self):
        ''' Enable or disable the menu item in the parent menu, depending on
            what enabled() returns. '''
        if self._parentMenu:
            myId = self.myId()
            if myId != wx.NOT_FOUND:
                self._parentMenu.Enable(myId, self.enabled())

    def myId(self):
        ''' Return the id of our menu item in the parent menu. '''
        # I'd rather use wx.Menu.FindItem, but it seems that that
        # method currently does not work for menu items with accelerators
        # (wxPython 2.8.6 on Ubuntu). When that is fixed replace the 7
        # lines below with this one:
        # myId = self._parentMenu.FindItem(self._labelInParentMenu)
        for item in self._parentMenu.MenuItems:
            if self.__GetLabelText(item.GetText()) == self._labelInParentMenu:
                return item.Id
        return wx.NOT_FOUND

    def updateMenuItems(self):
        ''' Update the menu items of this menu. '''
        pass
    
    def enabled(self):
        ''' Return a boolean indicating whether this menu should be enabled in
            its parent menu. This method is called by 
            updateMenuItemInParentMenu(). It returns True by default. Override
            in a subclass as needed.'''
        return True
    
    @staticmethod
    def __GetLabelText(menuText):
        ''' Remove accelerators from the menuText. This is necessary because on
            some platforms '&' is changed into '_' so menuTexts would compare
            different even though they are really the same. '''
        return menuText.replace('&', '').replace('_', '')

            
class DynamicMenuThatGetsUICommandsFromViewer(DynamicMenu):
    def __init__(self, viewer, parentMenu=None, labelInParentMenu=''): # pylint: disable-msg=W0621
        self._uiCommands = None
        super(DynamicMenuThatGetsUICommandsFromViewer, self).__init__(\
            viewer, parentMenu, labelInParentMenu)

    def registerForMenuUpdate(self):
        # Refill the menu whenever the menu is opened, because the menu might 
        # depend on the status of the viewer:
        self._window.Bind(wx.EVT_MENU_OPEN, self.onUpdateMenu)
        
    def updateMenuItems(self):
        newCommands = self.getUICommands()
        try:
            if newCommands == self._uiCommands:
                return
        except wx._core.PyDeadObjectError: # pylint: disable-msg=W0212
            pass  # Old viewer was closed
        self.clearMenu()
        self.fillMenu(newCommands)
        self._uiCommands = newCommands
            
    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands) # pylint: disable-msg=W0142
        
    def getUICommands(self):
        raise NotImplementedError


class MainMenu(wx.MenuBar):
    def __init__(self, mainwindow, settings, iocontroller, viewerContainer,
                 taskFile):
        super(MainMenu, self).__init__()
        self.Append(FileMenu(mainwindow, settings, iocontroller,
                             viewerContainer), _('&File'))
        self.Append(EditMenu(mainwindow, settings, iocontroller, 
                             viewerContainer), _('&Edit'))
        self.Append(ViewMenu(mainwindow, settings, viewerContainer, taskFile),
                    _('&View'))
        self.Append(TaskMenu(mainwindow, settings, taskFile, viewerContainer),
                    _('&Task'))
        if settings.getboolean('feature', 'effort'):
            self.Append(EffortMenu(mainwindow, settings, taskFile, 
                        viewerContainer), _('Eff&ort'))
        self.Append(CategoryMenu(mainwindow, settings, taskFile.categories(),
                                 viewerContainer), _('&Category'))
        if settings.getboolean('feature', 'notes'):
            self.Append(NoteMenu(mainwindow, settings, taskFile,
                                 viewerContainer), _('&Note'))
        self.Append(HelpMenu(mainwindow, settings), _('&Help'))

       
class FileMenu(Menu):
    def __init__(self, mainwindow, settings, iocontroller, viewerContainer):
        super(FileMenu, self).__init__(mainwindow)
        self.__settings = settings
        self.__iocontroller = iocontroller
        self.__recentFileUICommands = []
        self.__separator = None
        self.appendUICommands(
            uicommand.FileOpen(iocontroller=iocontroller),
            uicommand.FileMerge(iocontroller=iocontroller),
            uicommand.FileClose(iocontroller=iocontroller),
            None,
            uicommand.FileSave(iocontroller=iocontroller),
            uicommand.FileSaveAs(iocontroller=iocontroller),
            uicommand.FileSaveSelection(iocontroller=iocontroller,
                                        viewer=viewerContainer))
        if not settings.getboolean('feature', 'syncml'):
            self.appendUICommands(uicommand.FilePurgeDeletedItems(iocontroller=iocontroller))
        self.appendUICommands(
            None,
            uicommand.FileSaveSelectedTaskAsTemplate(iocontroller=iocontroller,
                                                     viewer=viewerContainer),
            uicommand.FileAddTemplate(iocontroller=iocontroller),
            None,
            uicommand.PrintPageSetup(settings=settings),
            uicommand.PrintPreview(viewer=viewerContainer, settings=settings),
            uicommand.Print(viewer=viewerContainer, settings=settings),
            None)
        self.appendMenu(_('&Export'),
                        ExportMenu(mainwindow, iocontroller, viewerContainer),
                        'export')
        if settings.getboolean('feature', 'syncml'):
            try:
                import taskcoachlib.syncml.core # pylint: disable-msg=W0612
            except ImportError:
                pass
            else:
                self.appendUICommands(uicommand.FileSynchronize(iocontroller=iocontroller, settings=settings))
        self.__recentFilesStartPosition = len(self) 
        self.appendUICommands(None, uicommand.FileQuit())
        self._window.Bind(wx.EVT_MENU_OPEN, self.onOpenMenu)

    def onOpenMenu(self, event):
        if event.GetMenu() == self:
            self.__removeRecentFileMenuItems()
            self.__insertRecentFileMenuItems()        
        event.Skip()
    
    def __insertRecentFileMenuItems(self):
        recentFiles = self.__settings.getlist('file', 'recentfiles')
        if not recentFiles:
            return
        maximumNumberOfRecentFiles = self.__settings.getint('file', 
            'maxrecentfiles')
        recentFiles = recentFiles[:maximumNumberOfRecentFiles]
        self.__separator = self.InsertSeparator(self.__recentFilesStartPosition)
        for index, recentFile in enumerate(recentFiles):
            recentFileNumber = index + 1 # Only computer nerds start counting at 0 :-)
            recentFileMenuPosition = self.__recentFilesStartPosition + 1 + index
            recentFileOpenUICommand = uicommand.RecentFileOpen(filename=recentFile,
                index=recentFileNumber, iocontroller=self.__iocontroller)
            recentFileOpenUICommand.addToMenu(self, self._window, 
                recentFileMenuPosition)
            self.__recentFileUICommands.append(recentFileOpenUICommand)

    def __removeRecentFileMenuItems(self):
        for recentFileUICommand in self.__recentFileUICommands:
            recentFileUICommand.removeFromMenu(self, self._window)
        self.__recentFileUICommands = []
        if self.__separator:
            self.RemoveItem(self.__separator)
            self.__separator = None


class ExportMenu(Menu):
    def __init__(self, mainwindow, iocontroller, viewerContainer):
        super(ExportMenu, self).__init__(mainwindow)
        kwargs = dict(iocontroller=iocontroller, viewer=viewerContainer)
        # pylint: disable-msg=W0142
        self.appendUICommands(
            uicommand.FileExportAsHTML(**kwargs),
            uicommand.FileExportSelectionAsHTML(**kwargs),
            uicommand.FileExportAsCSV(**kwargs),
            uicommand.FileExportSelectionAsCSV(**kwargs),
            uicommand.FileExportAsICalendar(**kwargs),
            uicommand.FileExportSelectionAsICalendar(**kwargs))


class TaskTemplateMenu(DynamicMenu):
    def __init__(self, mainwindow, taskList, settings):
        self._uiCommands = None
        self.settings = settings
        self.taskList = taskList
        super(TaskTemplateMenu, self).__init__(mainwindow)

    def registerForMenuUpdate(self):
        self._window.Bind(wx.EVT_MENU_OPEN, self.onUpdateMenu)
        
    def updateMenuItems(self):
        newCommands = self.getUICommands()
        if newCommands != self._uiCommands:
            self.clearMenu()
            self.fillMenu(newCommands)
            self._uiCommands = newCommands
     
    def fillMenu(self, uiCommands):
        self.appendUICommands(*uiCommands) # pylint: disable-msg=W0142

    def getUICommands(self):
        path = self.settings.pathToTemplatesDir()
        commands = []
        for name in os.listdir(path):
            fullname = os.path.join(path, name)
            if name.endswith('.tsktmpl'):
                commands.append(uicommand.TaskNewFromTemplate(fullname,
                                  taskList=self.taskList, 
                                  settings=self.settings))
        return commands


class EditMenu(Menu):
    def __init__(self, mainwindow, settings, iocontroller, viewerContainer):
        super(EditMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditUndo(),
            uicommand.EditRedo(),
            None,
            uicommand.EditCut(viewer=viewerContainer, id=wx.ID_CUT),
            uicommand.EditCopy(viewer=viewerContainer, id=wx.ID_COPY),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=viewerContainer),
            None)
        # Leave sufficient room for command names in the Undo and Redo menu items:
        self.appendMenu(_('&Select')+' '*50,
                        SelectMenu(mainwindow, viewerContainer))
        self.appendUICommands(None, uicommand.EditPreferences(settings))
        if settings.getboolean('feature', 'syncml'):
            try:
                import taskcoachlib.syncml.core # pylint: disable-msg=W0612
            except ImportError:
                pass
            else:
                self.appendUICommands(uicommand.EditSyncPreferences(mainwindow=mainwindow,
                                                                    iocontroller=iocontroller))


class SelectMenu(Menu):
    def __init__(self, mainwindow, viewerContainer):
        super(SelectMenu, self).__init__(mainwindow)
        kwargs = dict(viewer=viewerContainer)
        # pylint: disable-msg=W0142
        self.appendUICommands(uicommand.SelectAll(**kwargs),
                              uicommand.ClearSelection(**kwargs))


class ViewMenu(Menu):
    def __init__(self, mainwindow, settings, viewerContainer, taskFile):
        super(ViewMenu, self).__init__(mainwindow)
        self.appendMenu(_('&New viewer'), 
            ViewViewerMenu(mainwindow, settings, viewerContainer, taskFile),
                'viewnewviewer')
        activateNextViewer = uicommand.ActivateViewer(viewer=viewerContainer,
            menuText=_('&Activate next viewer\tCtrl+PgDn'),
            helpText=_('Activate the next open viewer'), forward=True,
            bitmap='activatenextviewer')
        activatePreviousViewer = uicommand.ActivateViewer(viewer=viewerContainer,
            menuText=_('Activate &previous viewer\tCtrl+PgUp'),
            helpText=_('Activate the previous open viewer'), forward=False,
            bitmap='activatepreviousviewer')
        self.appendUICommands(
            activateNextViewer,
            activatePreviousViewer,
            uicommand.RenameViewer(viewer=viewerContainer),
            None)
        self.appendMenu(_('&Filter'), 
                        FilterMenu(mainwindow, self, _('&Filter')))
        self.appendMenu(_('&Sort'),
                        SortMenu(mainwindow, self, _('&Sort')))
        self.appendMenu(_('&Columns'), 
                        ColumnMenu(mainwindow, self, _('&Columns')))
        self.appendUICommands(None)
        self.appendMenu(_('&Tree options'), 
                        ViewTreeOptionsMenu(mainwindow, viewerContainer),
                        'treeview')
        self.appendUICommands(None)
        self.appendMenu(_('T&oolbar'), ToolBarMenu(mainwindow, settings))
        self.appendUICommands(uicommand.UICheckCommand(settings=settings,
            menuText=_('Status&bar'), helpText=_('Show/hide status bar'),
            setting='statusbar'))


class ViewViewerMenu(Menu):
    def __init__(self, mainwindow, settings, viewerContainer, taskFile):
        super(ViewViewerMenu, self).__init__(mainwindow)
        ViewViewer = uicommand.ViewViewer
        kwargs = dict(viewer=viewerContainer, taskFile=taskFile, settings=settings)
        # pylint: disable-msg=W0142
        viewViewerCommands = [\
            ViewViewer(menuText=_('&Task'),
                       helpText=_('Open a new tab with a viewer that displays tasks'),
                       viewerClass=viewer.TaskViewer, **kwargs),
            ViewViewer(menuText=_('Task &square map'),
                       helpText=_('Open a new tab with a viewer that displays tasks in a square map'),
                       viewerClass=viewer.SquareTaskViewer, **kwargs),
            ViewViewer(menuText=_('T&imeline'),
                       helpText=_('Open a new tab with a viewer that displays a timeline of tasks and effort'),
                       viewerClass=viewer.TimelineViewer, **kwargs),
            ViewViewer(menuText=_('&Calendar'),
                       helpText=_('Open a new tab with a viewer that displays tasks in a calendar'),
                       viewerClass=viewer.CalendarViewer, **kwargs),
            ViewViewer(menuText=_('&Category'),
                       helpText=_('Open a new tab with a viewer that displays categories'),
                       viewerClass=viewer.CategoryViewer, **kwargs)]
        if settings.getboolean('feature', 'effort'):
            viewViewerCommands.append(
                ViewViewer(menuText=_('&Effort'),
                       helpText=_('Open a new tab with a viewer that displays efforts'),
                       viewerClass=viewer.EffortViewer, **kwargs))
            viewViewerCommands.append(
                uicommand.ViewEffortViewerForSelectedTask(menuText=_('Effort for &one task'),
                        helpText=_('Open a new tab with a viewer that displays efforts for the selected task'),
                        viewerClass=viewer.EffortViewer, **kwargs))
        if settings.getboolean('feature', 'notes'):
            viewViewerCommands.append(
                ViewViewer(menuText=_('&Note'),
                       helpText=_('Open a new tab with a viewer that displays notes'),
                       viewerClass=viewer.NoteViewer, **kwargs))
        self.appendUICommands(*viewViewerCommands)
       
                                      
class ViewTreeOptionsMenu(Menu):
    def __init__(self, mainwindow, viewerContainer):
        super(ViewTreeOptionsMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.ViewExpandSelected(viewer=viewerContainer),
            uicommand.ViewCollapseSelected(viewer=viewerContainer),
            None,
            uicommand.ViewExpandAll(viewer=viewerContainer),
            uicommand.ViewCollapseAll(viewer=viewerContainer))


class FilterMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isFilterable() and \
            bool(self._window.viewer.getFilterUICommands())
    
    def getUICommands(self):
        return self._window.viewer.getFilterUICommands()
    
    
class ColumnMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.hasHideableColumns()
    
    def getUICommands(self):
        return self._window.viewer.getColumnUICommands()
        

class SortMenu(DynamicMenuThatGetsUICommandsFromViewer):
    def enabled(self):
        return self._window.viewer.isSortable()
    
    def getUICommands(self):
        return self._window.viewer.getSortUICommands()


class ToolBarMenu(Menu):
    def __init__(self, mainwindow, settings):
        super(ToolBarMenu, self).__init__(mainwindow)
        toolbarCommands = []
        for value, menuText, helpText in \
            [(None, _('&Hide'), _('Hide the toolbar')),
             ((16, 16), _('&Small images'), _('Small images (16x16) on the toolbar')),
             ((22, 22), _('&Medium-sized images'), _('Medium-sized images (22x22) on the toolbar')),
             ((32, 32), _('&Large images'), _('Large images (32x32) on the toolbar'))]:
            toolbarCommands.append(uicommand.UIRadioCommand(settings=settings,
                setting='toolbar', value=value, menuText=menuText,
                helpText=helpText))
        # pylint: disable-msg=W0142
        self.appendUICommands(*toolbarCommands)


class TaskMenu(Menu):
    def __init__(self, mainwindow, settings, taskFile, viewerContainer):
        super(TaskMenu, self).__init__(mainwindow)
        tasks = taskFile.tasks()
        categories = taskFile.categories()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings))
        self.appendMenu(_('New task &from template'),
                        TaskTemplateMenu(mainwindow, taskList=tasks, 
                                         settings=settings),
                        'newtmpl')
        self.appendUICommands(uicommand.TaskNewSubTask(taskList=tasks,
                                     viewer=viewerContainer),
            None,
            uicommand.TaskEdit(taskList=tasks, viewer=viewerContainer),
            uicommand.TaskToggleCompletion(viewer=viewerContainer),
            uicommand.TaskIncPriority(taskList=tasks, viewer=viewerContainer),
            uicommand.TaskDecPriority(taskList=tasks, viewer=viewerContainer),
            uicommand.TaskMaxPriority(taskList=tasks, viewer=viewerContainer),
            uicommand.TaskMinPriority(taskList=tasks, viewer=viewerContainer),
            None,
            uicommand.TaskDelete(taskList=tasks, viewer=viewerContainer),
            None,
            uicommand.TaskMail(viewer=viewerContainer),
            uicommand.AddTaskAttachment(taskList=tasks,
                                        viewer=viewerContainer,
                                        settings=settings),
            uicommand.OpenAllTaskAttachments(viewer=viewerContainer,
                                             settings=settings))
        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                uicommand.TaskAddNote(viewer=viewerContainer,
                                      settings=settings)
                )
        self.appendMenu(_('&Toggle category'),
                        ToggleCategoryMenu(mainwindow, categories=categories,
                                           viewer=viewerContainer),
                        'folder_blue_arrow_icon')
            
            
class EffortMenu(Menu):
    def __init__(self, mainwindow, settings, taskFile, viewerContainer):
        super(EffortMenu, self).__init__(mainwindow)
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        self.appendUICommands(
            uicommand.EffortNew(viewer=viewerContainer, effortList=efforts,
                                taskList=tasks, settings=settings),
            uicommand.EffortEdit(viewer=viewerContainer, effortList=efforts),
            uicommand.EffortDelete(viewer=viewerContainer, effortList=efforts),
            None,
            uicommand.EffortStart(viewer=viewerContainer, taskList=tasks),
            uicommand.EffortStop(taskList=tasks))
       

class CategoryMenu(Menu):
    def __init__(self, mainwindow, settings, categories, viewerContainer):
        super(CategoryMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.CategoryNew(categories=categories, settings=settings),
            uicommand.CategoryNewSubCategory(viewer=viewerContainer,
                                             categories=categories),
            uicommand.CategoryEdit(viewer=viewerContainer,
                                   categories=categories),
            uicommand.CategoryDelete(viewer=viewerContainer,
                                     categories=categories),
            None,
            uicommand.AddCategoryAttachment(viewer=viewerContainer,
                                            settings=settings),
            uicommand.OpenAllCategoryAttachments(viewer=viewerContainer,
                                                 settings=settings))
        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                uicommand.CategoryAddNote(viewer=viewerContainer,
                                          settings=settings)
                )

        
class NoteMenu(Menu):
    def __init__(self, mainwindow, settings, taskFile, viewerContainer):
        super(NoteMenu, self).__init__(mainwindow)
        notes = taskFile.notes()
        categories = taskFile.categories()
        self.appendUICommands(
            uicommand.NoteNew(notes=notes, settings=settings),
            uicommand.NoteNewSubNote(viewer=viewerContainer, notes=notes),
            uicommand.NoteEdit(viewer=viewerContainer, notes=notes),
            uicommand.NoteDelete(viewer=viewerContainer, notes=notes),
            uicommand.NoteMail(viewer=viewerContainer),
            None,
            uicommand.AddNoteAttachment(viewer=viewerContainer,
                                        settings=settings),
            uicommand.OpenAllNoteAttachments(viewer=viewerContainer,
                                             settings=settings))
        self.appendMenu(_('&Toggle category'),
                        ToggleCategoryMenu(mainwindow, categories=categories,
                                           viewer=viewerContainer),
                        'folder_blue_arrow_icon')

        
class HelpMenu(Menu):
    def __init__(self, mainwindow, settings):
        super(HelpMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.Help(),
            uicommand.Tips(settings=settings),
            None,
            uicommand.HelpAbout(),
            uicommand.HelpLicense())


class TaskBarMenu(Menu):
    def __init__(self, taskBarIcon, settings, taskFile, viewerContainer):
        super(TaskBarMenu, self).__init__(taskBarIcon)
        tasks = taskFile.tasks()
        efforts = taskFile.efforts()
        self.appendUICommands(
            uicommand.TaskNew(taskList=tasks, settings=settings))
        if settings.getboolean('feature', 'effort'):
            self.appendUICommands(
                uicommand.EffortNew(viewer=viewerContainer, effortList=efforts,
                                    taskList=tasks, settings=settings))
        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                uicommand.NoteNew(notes=taskFile.notes(), settings=settings))
        if settings.getboolean('feature', 'effort'):
            self.appendUICommands(None) # Separator
            label = _('&Start tracking effort')
            self.appendMenu(label,
                StartEffortForTaskMenu(taskBarIcon, 
                                       base.filter.DeletedFilter(tasks), 
                                       self, label), 'clock_icon')
            self.appendUICommands(uicommand.EffortStop(taskList=tasks))
        self.appendUICommands(
            None,
            uicommand.MainWindowRestore(),
            uicommand.FileQuit())
        

class ToggleCategoryMenu(DynamicMenu):
    def __init__(self, mainwindow, categories, viewer): # pylint: disable-msg=W0621
        self.categories = categories
        self.viewer = viewer
        if viewer.isViewerContainer():
            self.uiCommandClass = uicommand.ToggleCategory
        elif viewer.isShowingTasks():
            self.uiCommandClass = uicommand.TaskToggleCategory
        else:
            self.uiCommandClass = uicommand.NoteToggleCategory
        super(ToggleCategoryMenu, self).__init__(mainwindow)
        
    def registerForMenuUpdate(self):
        for eventType in (self.categories.addItemEventType(), 
                          self.categories.removeItemEventType()):
            patterns.Publisher().registerObserver(self.onUpdateMenu,
                                                  eventType=eventType,
                                                  eventSource=self.categories)
        patterns.Publisher().registerObserver(self.onUpdateMenu, 
            eventType=category.Category.subjectChangedEventType())
           
    def updateMenuItems(self):
        self.clearMenu()
        self.addMenuItemsForCategories(self.categories.rootItems(), self)
            
    def addMenuItemsForCategories(self, categories, menu):
        categories = categories[:]
        categories.sort(key=lambda category: category.subject())
        for category in categories:
            uiCommand = self.uiCommandClass(category=category, viewer=self.viewer)
            uiCommand.addToMenu(menu, self._window)
        categoriesWithChildren = [category for category in categories if category.children()]
        if categoriesWithChildren:
            menu.AppendSeparator()
            for category in categoriesWithChildren:
                subMenu = wx.Menu()
                self.addMenuItemsForCategories(category.children(), subMenu)
                menu.AppendSubMenu(subMenu, self.subMenuLabel(category))            
    
    @staticmethod
    def subMenuLabel(category): # pylint: disable-msg=W0621
        return _('%s (subcategories)')%category.subject()
    
    def enabled(self):
        return bool(self.categories)
    
                   
class StartEffortForTaskMenu(DynamicMenu):
    def __init__(self, taskBarIcon, tasks, parentMenu=None, labelInParentMenu=''):
        self.tasks = tasks
        super(StartEffortForTaskMenu, self).__init__(taskBarIcon, parentMenu, 
                                                     labelInParentMenu)

    def registerForMenuUpdate(self):
        for eventType in (self.tasks.addItemEventType(), 
                          self.tasks.removeItemEventType()):
            patterns.Publisher().registerObserver(self.onUpdateMenu,
                                                  eventType=eventType,
                                                  eventSource=self.tasks)
        for eventType in (task.Task.subjectChangedEventType(),
                          task.Task.trackStartEventType(), 
                          task.Task.trackStopEventType(),
                          'task.startDateTime', 'task.dueDateTime', 
                          'task.completionDateTime'):
            patterns.Publisher().registerObserver(self.onUpdateMenu, eventType)
    
    def updateMenuItems(self):
        self.clearMenu()
        activeRootTasks = self._activeRootTasks()
        activeRootTasks.sort(key=lambda task: task.subject())
        for activeRootTask in activeRootTasks:
            self.addMenuItemForTask(activeRootTask, self)
                
    def addMenuItemForTask(self, task, menu): # pylint: disable-msg=W0621
        uiCommand = uicommand.EffortStartForTask(task=task, taskList=self.tasks)
        uiCommand.addToMenu(menu, self._window)
        activeChildren = [child for child in task.children() if \
                          child in self.tasks and child.active()]
        if activeChildren:
            activeChildren.sort(key=lambda task: task.subject())
            subMenu = wx.Menu()
            for child in activeChildren:
                self.addMenuItemForTask(child, subMenu)
            menu.AppendSubMenu(subMenu, _('%s (subtasks)')%task.subject())
                        
    def enabled(self):
        return bool(self._activeRootTasks())

    def _activeRootTasks(self):
        return [rootTask for rootTask in self.tasks.rootItems() \
                if rootTask.active()]
    

class TaskPopupMenu(Menu):
    def __init__(self, mainwindow, settings, tasks, efforts, categories, taskViewer):
        super(TaskPopupMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=taskViewer),
            uicommand.EditCopy(viewer=taskViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=taskViewer),
            None,
            uicommand.TaskNew(taskList=tasks, settings=settings))
        self.appendMenu(_('New task &from template'),
                        TaskTemplateMenu(mainwindow, taskList=tasks, 
                                         settings=settings),
                        'newtmpl')
        self.appendUICommands(
            uicommand.TaskNewSubTask(taskList=tasks, viewer=taskViewer),
            None,
            uicommand.TaskEdit(taskList=tasks, viewer=taskViewer),
            uicommand.TaskToggleCompletion(viewer=taskViewer),
            uicommand.TaskIncPriority(taskList=tasks, viewer=taskViewer),
            uicommand.TaskDecPriority(taskList=tasks, viewer=taskViewer),
            uicommand.TaskMaxPriority(taskList=tasks, viewer=taskViewer),
            uicommand.TaskMinPriority(taskList=tasks, viewer=taskViewer),
            None,
            uicommand.TaskDelete(taskList=tasks, viewer=taskViewer),
            None,
            uicommand.TaskMail(viewer=taskViewer),
            uicommand.AddTaskAttachment(taskList=tasks, viewer=taskViewer,
                                        settings=settings),
            uicommand.OpenAllTaskAttachments(viewer=taskViewer,
                                             settings=settings)
            )
        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                uicommand.TaskAddNote(viewer=taskViewer,
                                      settings=settings))
        self.appendMenu(_('&Toggle category'),
                        ToggleCategoryMenu(mainwindow, categories=categories,
                                           viewer=taskViewer),
                        'folder_blue_arrow_icon')
        if settings.getboolean('feature', 'effort'):
            self.appendUICommands(
                None,
                uicommand.EffortNew(viewer=taskViewer, effortList=efforts,
                                    taskList=tasks, settings=settings),
                uicommand.EffortStart(viewer=taskViewer, taskList=tasks),
                uicommand.EffortStop(taskList=tasks))
        if taskViewer.isTreeViewer():
            self.appendUICommands(None,
                uicommand.ViewExpandSelected(viewer=taskViewer),
                uicommand.ViewCollapseSelected(viewer=taskViewer))


class EffortPopupMenu(Menu):
    def __init__(self, mainwindow, tasks, settings, efforts, effortViewer):
        super(EffortPopupMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=effortViewer),
            uicommand.EditCopy(viewer=effortViewer),
            uicommand.EditPaste(),
            None,
            uicommand.EffortNew(viewer=effortViewer, effortList=efforts,
                                taskList=tasks, settings=settings),
            uicommand.EffortEdit(viewer=effortViewer, effortList=efforts),
            uicommand.EffortDelete(viewer=effortViewer, effortList=efforts),
            None,
            uicommand.EffortStop(taskList=tasks))


class CategoryPopupMenu(Menu):
    def __init__(self, mainwindow, settings, taskFile, categoryViewer, localOnly=False):
        super(CategoryPopupMenu, self).__init__(mainwindow)
        categories = categoryViewer.presentation()
        tasks = taskFile.tasks()
        notes = taskFile.notes()
        self.appendUICommands(
            uicommand.EditCut(viewer=categoryViewer),
            uicommand.EditCopy(viewer=categoryViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=categoryViewer))
        if not localOnly:
            self.appendUICommands(
                None,
                uicommand.NewTaskWithSelectedCategories(taskList=tasks,
                                                        settings=settings,
                                                        categories=categories,
                                                        viewer=categoryViewer))
            if settings.getboolean('feature', 'notes'):
                self.appendUICommands(
                    uicommand.NewNoteWithSelectedCategories(notes=notes,
                        settings=settings, categories=categories,
                        viewer=categoryViewer))
        self.appendUICommands(
            None,
            uicommand.CategoryNew(categories=categories, settings=settings),
            uicommand.CategoryNewSubCategory(viewer=categoryViewer,
                                             categories=categories),
            uicommand.CategoryEdit(viewer=categoryViewer,
                                   categories=categories),
            uicommand.CategoryDelete(viewer=categoryViewer,
                                     categories=categories),
            None,
            uicommand.AddCategoryAttachment(viewer=categoryViewer,
                                            settings=settings),
            uicommand.OpenAllCategoryAttachments(viewer=categoryViewer,
                                                 settings=settings))
        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                uicommand.CategoryAddNote(viewer=categoryViewer,
                                          settings=settings))
        self.appendUICommands(
            None,
            uicommand.ViewExpandSelected(viewer=categoryViewer),
            uicommand.ViewCollapseSelected(viewer=categoryViewer))


class NotePopupMenu(Menu):
    def __init__(self, mainwindow, settings, notes, categories, noteViewer):
        super(NotePopupMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=noteViewer),
            uicommand.EditCopy(viewer=noteViewer),
            uicommand.EditPaste(),
            uicommand.EditPasteAsSubItem(viewer=noteViewer),
            None,
            uicommand.NoteNew(notes=notes, settings=settings),
            uicommand.NoteNewSubNote(viewer=noteViewer, notes=notes),
            uicommand.NoteEdit(viewer=noteViewer, notes=notes),
            uicommand.NoteDelete(viewer=noteViewer, notes=notes),
            None,
            uicommand.NoteMail(viewer=noteViewer),
            None,
            uicommand.AddNoteAttachment(viewer=noteViewer, settings=settings),
            uicommand.OpenAllNoteAttachments(viewer=noteViewer,
                                             settings=settings))
        self.appendMenu(_('&Toggle category'),
                        ToggleCategoryMenu(mainwindow, categories=categories,
                                           viewer=noteViewer),
                        'folder_blue_arrow_icon')
        self.appendUICommands(
            None,
            uicommand.ViewExpandSelected(viewer=noteViewer),
            uicommand.ViewCollapseSelected(viewer=noteViewer))


class ColumnPopupMenuMixin(object):
    ''' Mixin class for column header popup menu's. These menu's get the
        column index property set by the control popping up the menu to
        indicate which column the user clicked. See
        widgets._CtrlWithColumnPopupMenuMixin. '''

    def __setColumn(self, columnIndex):
        self.__columnIndex = columnIndex # pylint: disable-msg=W0201

    def __getColumn(self):
        return self.__columnIndex

    columnIndex = property(__getColumn, __setColumn)

    def getUICommands(self):
        if not self._window: # Prevent PyDeadObject exception when running tests
            return []
        return [uicommand.HideCurrentColumn(viewer=self._window), None] + \
            self._window.getColumnUICommands()


class ColumnPopupMenu(ColumnPopupMenuMixin, Menu):
    ''' Column header popup menu. '''

    def __init__(self, window):
        super(ColumnPopupMenu, self).__init__(window)
        wx.CallAfter(self.appendUICommands, *self.getUICommands())


class EffortViewerColumnPopupMenu(ColumnPopupMenuMixin,
                                  DynamicMenuThatGetsUICommandsFromViewer):
    ''' Column header popup menu. '''
    
    def registerForMenuUpdate(self):
        self._window.Bind(wx.EVT_UPDATE_UI, self.onUpdateMenu)
            

class AttachmentPopupMenu(Menu):
    def __init__(self, mainwindow, settings, attachments, attachmentViewer):
        super(AttachmentPopupMenu, self).__init__(mainwindow)
        self.appendUICommands(
            uicommand.EditCut(viewer=attachmentViewer),
            uicommand.EditCopy(viewer=attachmentViewer),
            uicommand.EditPaste(),
            None,
            uicommand.AttachmentNew(attachments=attachments, settings=settings),
            uicommand.AttachmentEdit(viewer=attachmentViewer, attachments=attachments),
            uicommand.AttachmentDelete(viewer=attachmentViewer, attachments=attachments),
            uicommand.AttachmentOpen(viewer=attachmentViewer, attachments=attachments),
            )

        if settings.getboolean('feature', 'notes'):
            self.appendUICommands(
                None,
                uicommand.AttachmentAddNote(viewer=attachmentViewer,
                                            settings=settings))
