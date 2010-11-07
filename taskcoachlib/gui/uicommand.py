# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>
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
from taskcoachlib import patterns, meta, command, help, widgets, persistence # pylint: disable-msg=W0622
from taskcoachlib.i18n import _
from taskcoachlib.domain import base, task, note, category, attachment, effort
from taskcoachlib.mailer import writeMail
from taskcoachlib.thirdparty.calendar import wxSCHEDULER_DAILY, wxSCHEDULER_WEEKLY, \
     wxSCHEDULER_MONTHLY, wxSCHEDULER_NEXT, wxSCHEDULER_PREV, wxSCHEDULER_TODAY, \
     wxSCHEDULER_HORIZONTAL, wxSCHEDULER_VERTICAL
import dialog, render, viewer, printer


''' User interface commands (subclasses of UICommand) are actions that can
    be invoked by the user via the user interface (menu's, toolbar, etc.).
    See the Taskmaster pattern described here: 
    http://www.objectmentor.com/resources/articles/taskmast.pdf 
''' # pylint: disable-msg=W0105


class UICommandContainerMixin(object):
    ''' Mixin with wx.Menu or wx.ToolBar (sub)class. '''

    def appendUICommands(self, *uiCommands):
        for uiCommand in uiCommands:
            if uiCommand is None:
                self.AppendSeparator()
            elif type(uiCommand) == type(()): # This only works for menu's
                menuTitle, menuUICommands = uiCommand[0], uiCommand[1:]
                self.appendSubMenuWithUICommands(menuTitle, menuUICommands)
            else:
                self.appendUICommand(uiCommand)

    def appendSubMenuWithUICommands(self, menuTitle, uiCommands):
        import menu
        subMenu = menu.Menu(self._window)
        self.appendMenu(menuTitle, subMenu)
        subMenu.appendUICommands(*uiCommands) # pylint: disable-msg=W0142
        

class UICommand(object):
    ''' Base user interface command. An UICommand is some action that can be 
        associated with menu's and/or toolbars. It contains the menutext and 
        helptext to be displayed, code to deal with wx.EVT_UPDATE_UI and 
        methods to attach the command to a menu or toolbar. Subclasses should 
        implement doCommand() and optionally override enabled(). '''
    
    def __init__(self, menuText='', helpText='', bitmap='nobitmap', 
             kind=wx.ITEM_NORMAL, id=None, bitmap2=None, *args, **kwargs): # pylint: disable-msg=W0622
        super(UICommand, self).__init__()
        menuText = menuText or '<%s>'%_('None')
        self.menuText = menuText if '&' in menuText else '&' + menuText
        self.helpText = helpText
        self.bitmap = bitmap
        self.bitmap2 = bitmap2
        self.kind = kind
        self.id = id or wx.NewId()
        self.toolbar = None
        self.menuItems = [] # uiCommands can be used in multiple menu's

    def __eq__(self, other):
        try:
            return self.menuText == other.menuText
        except AttributeError:
            return False

    def addToMenu(self, menu, window, position=None):
        menuItem = wx.MenuItem(menu, self.id, self.menuText, self.helpText, 
            self.kind)
        self.menuItems.append(menuItem)
        self.__addBitmapToMenuItem(menuItem)
        if position is None:
            menu.AppendItem(menuItem)
        else:
            menu.InsertItem(position, menuItem)
        self.bind(window, self.id)
        return self.id
    
    def __addBitmapToMenuItem(self, menuItem):
        if self.bitmap2 and self.kind == wx.ITEM_CHECK and '__WXGTK__' != wx.Platform:
            bitmap1 = self.__getBitmap(self.bitmap) 
            bitmap2 = self.__getBitmap(self.bitmap2)
            menuItem.SetBitmaps(bitmap1, bitmap2)
        elif self.bitmap and self.kind == wx.ITEM_NORMAL:
            menuItem.SetBitmap(self.__getBitmap(self.bitmap))
    
    def removeFromMenu(self, menu, window):
        for menuItem in self.menuItems:
            if menuItem.GetMenu() == menu:
                self.menuItems.remove(menuItem)
                menuId = menuItem.GetId()
                menu.Remove(menuId)
                break
        self.unbind(window, menuId)
        
    def appendToToolBar(self, toolbar):
        self.toolbar = toolbar
        bitmap = self.__getBitmap(self.bitmap, wx.ART_TOOLBAR, 
                                  toolbar.GetToolBitmapSize())
        toolbar.AddLabelTool(self.id, '',
            bitmap, wx.NullBitmap, self.kind, 
            shortHelp=wx.MenuItem.GetLabelFromText(self.menuText),
            longHelp=self.helpText)
        self.bind(toolbar, self.id)
        return self.id

    def bind(self, window, itemId):
        window.Bind(wx.EVT_MENU, self.onCommandActivate, id=itemId)
        window.Bind(wx.EVT_UPDATE_UI, self.onUpdateUI, id=itemId)

    def unbind(self, window, itemId):
        for eventType in [wx.EVT_MENU, wx.EVT_UPDATE_UI]:
            window.Unbind(eventType, id=itemId)
        
    def onCommandActivate(self, event, *args, **kwargs):
        ''' For Menu's and ToolBars, activating the command is not
            possible when not enabled, because menu items and toolbar
            buttons are disabled through onUpdateUI. For other controls such 
            as the ListCtrl and the TreeCtrl the EVT_UPDATE_UI event is not 
            sent, so we need an explicit check here. Otherwise hitting return 
            on an empty selection in the ListCtrl would bring up the 
            TaskEditor. '''
        if self.enabled(event):
            return self.doCommand(event, *args, **kwargs)
            
    def __call__(self, *args, **kwargs):
        return self.onCommandActivate(*args, **kwargs)
        
    def doCommand(self, event):
        raise NotImplementedError

    def onUpdateUI(self, event):
        event.Enable(bool(self.enabled(event)))
        if self.toolbar and (not self.helpText or self.menuText == '?'):
            self.updateToolHelp()
        
    def enabled(self, event): # pylint: disable-msg=W0613
        ''' Can be overridden in a subclass. '''
        return True

    def updateToolHelp(self):
        if not self.toolbar: return # Not attached to a toolbar or it's hidden
        shortHelp = wx.MenuItem.GetLabelFromText(self.getMenuText())
        if shortHelp != self.toolbar.GetToolShortHelp(self.id):
            self.toolbar.SetToolShortHelp(self.id, shortHelp)
        longHelp = self.getHelpText()
        if longHelp != self.toolbar.GetToolLongHelp(self.id):
            self.toolbar.SetToolLongHelp(self.id, longHelp)

    def mainWindow(self):
        return wx.GetApp().TopWindow
    
    def getMenuText(self):
        return self.menuText
    
    def getHelpText(self):
        return self.helpText

    def __getBitmap(self, bitmap, type=wx.ART_MENU, size=(16, 16)):
        return wx.ArtProvider_GetBitmap(bitmap, type, size)
    


class SettingsCommand(UICommand): # pylint: disable-msg=W0223
    ''' SettingsCommands are saved in the settings (a ConfigParser). '''

    def __init__(self, settings=None, setting=None, section='view', 
                 *args, **kwargs):
        self.settings = settings
        self.section = section
        self.setting = setting
        super(SettingsCommand, self).__init__(*args, **kwargs)


class BooleanSettingsCommand(SettingsCommand): # pylint: disable-msg=W0223
    def __init__(self, value=None, *args, **kwargs):
        self.value = value
        super(BooleanSettingsCommand, self).__init__(*args, **kwargs)
        
    def onUpdateUI(self, event):
        event.Check(self.isSettingChecked())
        super(BooleanSettingsCommand, self).onUpdateUI(event)

    def addToMenu(self, menu, window, position=None):
        menuId = super(BooleanSettingsCommand, self).addToMenu(menu, window, 
                                                              position)
        menuItem = menu.FindItemById(menuId)
        menuItem.Check(self.isSettingChecked())
        
    def isSettingChecked(self):
        raise NotImplementedError
    

class UICheckCommand(BooleanSettingsCommand):
    def __init__(self, *args, **kwargs):
        kwargs['bitmap'] = kwargs.get('bitmap', self.getBitmap())
        super(UICheckCommand, self).__init__(kind=wx.ITEM_CHECK, 
            *args, **kwargs)
        
    def isSettingChecked(self):
        return self.settings.getboolean(self.section, self.setting)

    def _isMenuItemChecked(self, event):
        # There's a bug in wxPython 2.8.3 on Windows XP that causes 
        # event.IsChecked() to return the wrong value in the context menu.
        # The menu on the main window works fine. So we first try to access the
        # context menu to get the checked state from the menu item itself.
        # This will fail if the event is coming from the window, but in that
        # case we can event.IsChecked() expect to work so we use that.
        try:
            return event.GetEventObject().FindItemById(event.GetId()).IsChecked()
        except AttributeError:
            return event.IsChecked()
        
    def doCommand(self, event):
        self.settings.set(self.section, self.setting, 
            str(self._isMenuItemChecked(event)))
        
    def getBitmap(self):
        # Using our own bitmap for checkable menu items does not work on
        # all platforms, most notably Gtk where providing our own bitmap causes
        # "(python:8569): Gtk-CRITICAL **: gtk_check_menu_item_set_active: 
        # assertion `GTK_IS_CHECK_MENU_ITEM (check_menu_item)' failed"
        return None


class UIRadioCommand(BooleanSettingsCommand):
    def __init__(self, *args, **kwargs):
        super(UIRadioCommand, self).__init__(kind=wx.ITEM_RADIO, bitmap='', 
                                             *args, **kwargs)
        
    def onUpdateUI(self, event):
        if self.isSettingChecked():
            super(UIRadioCommand, self).onUpdateUI(event)

    def isSettingChecked(self):
        return self.settings.get(self.section, self.setting) == str(self.value)

    def doCommand(self, event):
        self.settings.set(self.section, self.setting, str(self.value))


class IOCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.iocontroller = kwargs.pop('iocontroller', None)
        super(IOCommand, self).__init__(*args, **kwargs)


class TaskListCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.taskList = kwargs.pop('taskList', None)
        super(TaskListCommand, self).__init__(*args, **kwargs)
        
        
class EffortListCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.effortList = kwargs.pop('effortList', None)
        super(EffortListCommand, self).__init__(*args, **kwargs)


class CategoriesCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.categories = kwargs.pop('categories', None)
        super(CategoriesCommand, self).__init__(*args, **kwargs)


class NotesCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.notes = kwargs.pop('notes', None)
        super(NotesCommand, self).__init__(*args, **kwargs)


class AttachmentsCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.attachments = kwargs.pop('attachments', None)
        super(AttachmentsCommand, self).__init__(*args, **kwargs)


class ViewerCommand(UICommand): # pylint: disable-msg=W0223
    def __init__(self, *args, **kwargs):
        self.viewer = kwargs.pop('viewer', None)
        super(ViewerCommand, self).__init__(*args, **kwargs)

    def __eq__(self, other):
        return super(ViewerCommand, self).__eq__(other) and \
            self.viewer.settingsSection() == other.viewer.settingsSection()


# Mixins: 

class PopupButtonMixin(object):
    """ Mix this with a UICommand for a toolbar pop-up menu. """

    def doCommand(self, event): # pylint: disable-msg=W0613
        args = [self.createPopupMenu()]
        if self.toolbar:
            args.append(self.menuXY())
        self.mainWindow().PopupMenu(*args) # pylint: disable-msg=W0142

    def menuXY(self):
        ''' Location to pop up the menu. '''
        mouseX = wx.GetMousePosition()[0]
        windowX = self.mainWindow().GetPosition()[0]
        buttonWidth = self.toolbar.GetToolSize()[0]
        menuX = mouseX - windowX - 0.5 * buttonWidth
        toolbarHeight = self.toolbar.GetSize()[1]
        mouseY = wx.GetMousePosition()[1]
        windowY = self.mainWindow().GetPosition()[1]
        menuY = mouseY - windowY - 1.5 * toolbarHeight
        return menuX, menuY
    
    def createPopupMenu(self):
        raise NotImplementedError


class NeedsSelectionMixin(object):
    def enabled(self, event):
        return super(NeedsSelectionMixin, self).enabled(event) and \
            self.viewer.curselection()


class NeedsOneSelectedItemMixin(object):
    def enabled(self, event):
        return super(NeedsOneSelectedItemMixin, self).enabled(event) and \
            len(self.viewer.curselection()) == 1


class NeedsTaskViewerMixin(object):
    def enabled(self, event):
        return super(NeedsTaskViewerMixin, self).enabled(event) and \
            self.viewer.isShowingTasks()


class NeedsEffortViewerMixin(object):
    def enabled(self, event):
        return super(NeedsEffortViewerMixin, self).enabled(event) and \
            self.viewer.isShowingEffort()


class NeedsTaskOrEffortViewerMixin(object):
    def enabled(self, event):
        return super(NeedsTaskOrEffortViewerMixin, self).enabled(event) and \
            (self.viewer.isShowingTasks() or self.viewer.isShowingEffort())
            

class NeedsCategoryViewerMixin(object):
    def enabled(self, event):
        return super(NeedsCategoryViewerMixin, self).enabled(event) and \
            self.viewer.isShowingCategories()


class NeedsNoteViewerMixin(object):
    def enabled(self, event):
        return super(NeedsNoteViewerMixin, self).enabled(event) and \
            self.viewer.isShowingNotes()


class NeedsAttachmentViewerMixin(object):
    def enabled(self, event):
        return super(NeedsAttachmentViewerMixin, self).enabled(event) and \
            self.viewer.isShowingAttachments()


class NeedsSelectedTasksMixin(NeedsSelectionMixin):
    def enabled(self, event):
        return super(NeedsSelectedTasksMixin, self).enabled(event) and \
            self.viewer.curselectionIsInstanceOf(task.Task)


class NeedsSelectedTasksOrEffortsMixin(NeedsSelectionMixin):
    def enabled(self, event):
        return super(NeedsSelectedTasksOrEffortsMixin, self).enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or \
             self.viewer.curselectionIsInstanceOf(effort.Effort))


class NeedsOneSelectedTaskMixin(NeedsSelectedTasksMixin, NeedsOneSelectedItemMixin):
    pass


class NeedsSelectionWithAttachmentsMixin(NeedsSelectionMixin):
    def enabled(self, event):
        return super(NeedsSelectionWithAttachmentsMixin, self).enabled(event) and \
            any(item.attachments() for item in self.viewer.curselection() if not isinstance(item, effort.Effort))


class NeedsSelectedEffortMixin(NeedsSelectionMixin):
    def enabled(self, event):
        return super(NeedsSelectedEffortMixin, self).enabled(event) and \
            self.viewer.curselectionIsInstanceOf(effort.Effort)


class NeedsSelectedCategoryMixin(NeedsCategoryViewerMixin, NeedsSelectionMixin):
    pass


class NeedsOneSelectedCategoryMixin(NeedsCategoryViewerMixin, NeedsOneSelectedItemMixin):
    pass


class NeedsSelectedNoteMixin(NeedsNoteViewerMixin, NeedsSelectionMixin):
    pass


class NeedsOneSelectedNoteMixin(NeedsNoteViewerMixin, NeedsOneSelectedItemMixin):
    pass


class NeedsSelectedAttachmentsMixin(NeedsAttachmentViewerMixin, NeedsSelectionMixin):
    pass


class NeedsOneSelectedAttachmentMixin(NeedsAttachmentViewerMixin, NeedsOneSelectedItemMixin):
    pass


class NeedsSelectedCompositeMixin(NeedsSelectionMixin):
    def enabled(self, event):
        return super(NeedsSelectedCompositeMixin, self).enabled(event) and \
            (self.viewer.curselectionIsInstanceOf(task.Task) or \
             self.viewer.curselectionIsInstanceOf(note.Note) or \
             self.viewer.curselectionIsInstanceOf(category.Category))
    
    
class NeedsAtLeastOneTaskMixin(object):
    def enabled(self, event): # pylint: disable-msg=W0613
        return len(self.taskList) > 0

        
class NeedsItemsMixin(object):
    def enabled(self, event): # pylint: disable-msg=W0613
        return self.viewer.size() 


class NeedsTreeViewerMixin(object):
    def enabled(self, event):
        return super(NeedsTreeViewerMixin, self).enabled(event) and \
            self.viewer.isTreeViewer()

            
class NeedsListViewerMixin(object):
    def enabled(self, event):
        return super(NeedsListViewerMixin, self).enabled(event) and \
            (not self.viewer.isTreeViewer())


class NeedsDeletedItemsMixin(object):
    def enabled(self, event):
        return super(NeedsDeletedItemsMixin, self).enabled(event) and \
               self.iocontroller.hasDeletedItems()


# Commands:

class FileOpen(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileOpen, self).__init__(menuText=_('&Open...\tCtrl+O'),
            helpText=_('Open a %s file')%meta.name, bitmap='fileopen',
            id=wx.ID_OPEN, *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.open()


class RecentFileOpen(IOCommand):
    def __init__(self, *args, **kwargs):
        self.__filename = kwargs.pop('filename')
        index = kwargs.pop('index')
        super(RecentFileOpen, self).__init__(menuText='%d %s'%(index, self.__filename),
            helpText=_('Open %s')%self.__filename, *args, **kwargs)
            
    def doCommand(self, event):
        self.iocontroller.open(self.__filename)

        
class FileMerge(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileMerge, self).__init__(menuText=_('&Merge...'),
            helpText=_('Merge tasks from another file with the current file'), 
            bitmap='merge', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.merge()


class FileClose(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileClose, self).__init__(menuText=_('&Close\tCtrl+W'),
            helpText=_('Close the current file'), bitmap='close',
            id=wx.ID_CLOSE, *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.close()


class FileSave(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileSave, self).__init__(menuText=_('&Save\tCtrl+S'),
            helpText=_('Save the current file'), bitmap='save',
            id=wx.ID_SAVE, *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.save()
        
    def enabled(self, event):
        return self.iocontroller.needSave()


class FileSaveAs(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileSaveAs, self).__init__(menuText=_('S&ave as...\tShift+Ctrl+S'),
            helpText=_('Save the current file under a new name'), 
            bitmap='saveas', id=wx.ID_SAVEAS, *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.saveas()
        

class FileSaveSelection(NeedsSelectedTasksMixin, IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileSaveSelection, self).__init__(menuText=_('Sa&ve selection...'),
            helpText=_('Save the selected tasks to a separate file'), 
            bitmap='saveselection', *args, **kwargs)
    
    def doCommand(self, event):
        self.iocontroller.saveselection(self.viewer.curselection()), 


class FileSaveSelectedTaskAsTemplate(NeedsOneSelectedTaskMixin, IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileSaveSelectedTaskAsTemplate, self).__init__(\
            menuText=_('Save selected task as &template'),
            helpText=_('Save the selected task as a task template'),
            bitmap='saveselection', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.saveastemplate(self.viewer.curselection()[0])


class FileAddTemplate(IOCommand):
    def __init__(self, *args, **kwargs):
        super(FileAddTemplate, self).__init__(\
            menuText=_('&Add template...'),
            helpText=_('Add a new template from a template file'),
            bitmap='fileopen', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.addtemplate()


class FileEditTemplates(SettingsCommand, UICommand):
    def __init__(self, *args, **kwargs):
        super(FileEditTemplates, self).__init__(\
            menuText=_('Edit templates...'),
            helpText=_('Edit existing templates'), *args, **kwargs)

    def doCommand(self, event):
        dlg = dialog.templates.TemplatesDialog(self.settings, self.mainWindow(), _('Edit templates'))
        dlg.Show()

class FilePurgeDeletedItems(NeedsDeletedItemsMixin, IOCommand):
    def __init__(self, *args, **kwargs):
        super(FilePurgeDeletedItems, self).__init__(\
            menuText=_('&Purge deleted items'),
            helpText=_('Actually delete deleted tasks and notes (see the SyncML chapter in Help'),
            bitmap='delete', *args, **kwargs)

    def doCommand(self, event):
        if (wx.MessageBox(_('''Purging deleted items is undoable.
If you're planning on enabling
the SyncML feature again with the
same server you used previously,
these items will probably come back.

Do you still want to purge?'''),
                          _('Warning'), wx.YES_NO) == wx.YES):
            self.iocontroller.purgeDeletedItems()


class PrintPageSetup(SettingsCommand, UICommand):
    def __init__(self, *args, **kwargs):
        super(PrintPageSetup, self).__init__(\
            menuText=_('&Page setup...\tShift+Ctrl+P'), 
            helpText=_('Setup the characteristics of the printer page'), 
            bitmap='pagesetup', id=wx.ID_PRINT_SETUP, *args, **kwargs)

    def doCommand(self, event):
        printerSettings = printer.PrinterSettings(self.settings)
        pageSetupDialog = wx.PageSetupDialog(self.mainWindow(), 
                                             printerSettings.pageSetupData)
        result = pageSetupDialog.ShowModal()
        if result == wx.ID_OK:
            printerSettings.updatePageSetupData(pageSetupDialog.GetPageSetupData())
        pageSetupDialog.Destroy()


class PrintPreview(ViewerCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(PrintPreview, self).__init__(\
            menuText=_('&Print preview'), 
            helpText=_('Show a preview of what the print will look like'), 
            bitmap='printpreview', id=wx.ID_PREVIEW, *args, **kwargs)

    def doCommand(self, event):
        printout, printout2 = printer.Printout(self.viewer, self.settings, 
                                               twoPrintouts=True)
        printerSettings = printer.PrinterSettings(self.settings)
        preview = wx.PrintPreview(printout, printout2, 
                                  printerSettings.printData)
        previewFrame = wx.PreviewFrame(preview, self.mainWindow(), 
            _('Print preview'), size=(750, 700))
        previewFrame.Initialize()
        previewFrame.Show()
      

class Print(ViewerCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(Print, self).__init__(\
            menuText=_('&Print...\tCtrl+P'), 
            helpText=_('Print the current file'), 
            bitmap='print', id=wx.ID_PRINT, *args, **kwargs)

    def doCommand(self, event): 
        printerSettings = printer.PrinterSettings(self.settings)
        printDialogData = wx.PrintDialogData(printerSettings.printData)
        printDialogData.EnableSelection(True)
        wxPrinter = wx.Printer(printDialogData)
        if not wxPrinter.PrintDialog(self.mainWindow()):
            return
        printout = printer.Printout(self.viewer, self.settings,
            printSelectionOnly=wxPrinter.PrintDialogData.Selection)
        # If the user checks the selection radio button, the ToPage property 
        # gets set to 1. Looks like a bug to me. The simple work-around is to
        # reset the ToPage property to the MaxPage value if necessary:
        if wxPrinter.PrintDialogData.Selection:
            wxPrinter.PrintDialogData.ToPage = wxPrinter.PrintDialogData.MaxPage
        wxPrinter.Print(self.mainWindow(), printout, prompt=False)
 
        
class FileExportAsHTML(IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileExportAsHTML, self).__init__(menuText=_('Export as &HTML...'), 
            helpText=_('Export the current view as HTML file'),
            bitmap='exportashtml', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.exportAsHTML(self.viewer)


class FileExportSelectionAsHTML(NeedsSelectionMixin, IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileExportSelectionAsHTML, self).__init__(menuText=_('Export selection as &HTML...'),
            helpText=_('Export the selection in the current view as HTML file'),
            bitmap='exportashtml', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.exportAsHTML(self.viewer, selectionOnly=True)


class FileExportAsCSV(IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileExportAsCSV, self).__init__(menuText=_('Export as &CSV...'),
            helpText=_('Export the current view in Comma Separated Values (CSV) format'),
            bitmap='exportascsv', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.exportAsCSV(self.viewer)


class FileExportSelectionAsCSV(NeedsSelectionMixin, IOCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(FileExportSelectionAsCSV, self).__init__(menuText=_('Export selection as &CSV...'),
            helpText=_('Export the selection in the current view in Comma Separated Values (CSV) format'),
            bitmap='exportascsv', *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.exportAsCSV(self.viewer, selectionOnly=True)


class FileExportAsICalendarBase(IOCommand, ViewerCommand):
    selectionOnly = False
    
    def __init__(self, *args, **kwargs):
        super(FileExportAsICalendarBase, self).__init__(menuText=self.menuText,
                                                        helpText=self.helpText,
                                                        bitmap='exportasvcal', 
                                                        *args, **kwargs)

    def doCommand(self, event):
        self.iocontroller.exportAsICalendar(self.viewer, 
                                            selectionOnly=self.selectionOnly)

    def enabled(self, event):
        enabled = super(FileExportAsICalendarBase, self).enabled(event)
        if enabled:
            return not (self.viewer.isShowingEffort() and self.viewer.isShowingAggregatedEffort())
        else:
            return False


class FileExportAsICalendar(NeedsTaskOrEffortViewerMixin, FileExportAsICalendarBase):
    menuText = _('Export as &iCalendar...')
    helpText = _('Export the items in the current viewer in iCalendar format')


class FileExportSelectionAsICalendar(NeedsSelectedTasksOrEffortsMixin, FileExportAsICalendarBase):
    selectionOnly = True
    menuText = _('Export selection as &iCalendar...')
    helpText = _('Export the selected items in the current viewer in iCalendar format')


class FileSynchronize(IOCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(FileSynchronize, self).__init__(menuText=_('S&yncML synchronization'),
            helpText=_('Synchronize with a SyncML server'),
            bitmap='arrows_looped_icon', *args, **kwargs)

    def doCommand(self, event):
        password = wx.GetPasswordFromUser(_('Please enter your password:'), 
                                          _('Task Coach SyncML password'))
        if password:
            self.iocontroller.synchronize(password)


class FileQuit(UICommand):
    def __init__(self, *args, **kwargs):
        super(FileQuit, self).__init__(menuText=_('&Quit\tCtrl+Q'), 
            helpText=_('Exit %s')%meta.name, bitmap='exit', 
            id=wx.ID_EXIT, *args, **kwargs)

    def doCommand(self, event):
        self.mainWindow().Close(force=True)


def getUndoMenuText():
    return '%s\tCtrl+Z'%patterns.CommandHistory().undostr(_('&Undo')) 

class EditUndo(UICommand):
    def __init__(self, *args, **kwargs):
        super(EditUndo, self).__init__(menuText=getUndoMenuText(),
            helpText=_('Undo the last command'), bitmap='undo',
            id=wx.ID_UNDO, *args, **kwargs)
            
    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Undo()
        else:
            patterns.CommandHistory().undo()

    def onUpdateUI(self, event):
        event.SetText(getUndoMenuText())
        super(EditUndo, self).onUpdateUI(event)

    def enabled(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanUndo()
        else:
            return patterns.CommandHistory().hasHistory() and \
                super(EditUndo, self).enabled(event)


def getRedoMenuText():
    return '%s\tCtrl+Y'%patterns.CommandHistory().redostr(_('&Redo')) 

class EditRedo(UICommand):
    def __init__(self, *args, **kwargs):
        super(EditRedo, self).__init__(menuText=getRedoMenuText(),
            helpText=_('Redo the last command that was undone'), bitmap='redo',
            id=wx.ID_REDO, *args, **kwargs)

    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Redo()
        else:
            patterns.CommandHistory().redo()

    def onUpdateUI(self, event):
        event.SetText(getRedoMenuText())
        super(EditRedo, self).onUpdateUI(event)

    def enabled(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanRedo()
        else:
            return patterns.CommandHistory().hasFuture() and \
                super(EditRedo, self).enabled(event)


class EditCut(NeedsSelectionMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):     
        super(EditCut, self).__init__(menuText=_('Cu&t\tCtrl+X'), 
            helpText=_('Cut the selected item(s) to the clipboard'), 
            bitmap='cut', *args, **kwargs)

    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Cut()
        else:
            cutCommand = command.CutCommand(self.viewer.presentation(),
                                            self.viewer.curselection())
            cutCommand.do()

    def enabled(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanCut()
        else:
            return super(EditCut, self).enabled(event)


class EditCopy(NeedsSelectionMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(EditCopy, self).__init__(menuText=_('&Copy\tCtrl+C'), 
            helpText=_('Copy the selected item(s) to the clipboard'), 
            bitmap='copy', *args, **kwargs)

    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Copy()
        else:
            copyCommand = command.CopyCommand(self.viewer.presentation(), 
                                              self.viewer.curselection())
            copyCommand.do()

    def enabled(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanCopy()
        else:
            return super(EditCopy, self).enabled(event)
        

class EditPaste(UICommand):
    def __init__(self, *args, **kwargs):
        super(EditPaste, self).__init__(menuText=_('&Paste\tCtrl+V'), 
            helpText=_('Paste item(s) from the clipboard'), bitmap='paste', 
            id=wx.ID_PASTE, *args, **kwargs)

    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.Paste()
        else:
            pasteCommand = command.PasteCommand()
            pasteCommand.do()
    
    def enabled(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            return windowWithFocus.CanPaste()
        else:
            return command.Clipboard() and super(EditPaste, self).enabled(event)


class EditPasteAsSubItem(NeedsSelectedCompositeMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(EditPasteAsSubItem, self).__init__(
            menuText=_('P&aste as subitem\tShift+Ctrl+V'), 
            helpText=_('Paste item(s) from the clipboard as subitem of the selected item'),
            bitmap='pasteintotask', *args, **kwargs)

    def doCommand(self, event):
        pasteCommand = command.PasteAsSubItemCommand(
            items=self.viewer.curselection())
        pasteCommand.do()

    def enabled(self, event):
        if not (super(EditPasteAsSubItem, self).enabled(event) and command.Clipboard()):
            return False
        targetClass = self.viewer.curselection()[0].__class__
        for item in command.Clipboard().peek():
            if item.__class__ != targetClass:
                return False
        return True


class EditPreferences(SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(EditPreferences, self).__init__(menuText=_('&Preferences...\tAlt+P'),
            helpText=_('Edit preferences'), bitmap='wrench_icon',
            id=wx.ID_PREFERENCES, *args, **kwargs)
            
    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        editor = dialog.preferences.Preferences(parent=self.mainWindow(), 
            title=_('Edit preferences'), settings=self.settings)
        editor.Show(show=show)


class EditSyncPreferences(IOCommand):
    def __init__(self, *args, **kwargs):
        super(EditSyncPreferences, self).__init__(menuText=_('&SyncML preferences...'),
            helpText=_('Edit SyncML preferences'), bitmap='arrows_looped_icon',
            *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        editor = dialog.syncpreferences.SyncMLPreferences(parent=self.mainWindow(),
            iocontroller=self.iocontroller,
            title=_('Edit SyncML preferences'))
        editor.Show(show=show)


class SelectAll(NeedsItemsMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(SelectAll, self).__init__(menuText=_('&All\tCtrl+A'),
            helpText=_('Select all items in the current view'), 
            bitmap='selectall', id=wx.ID_SELECTALL, *args, **kwargs)
        
    def doCommand(self, event):
        windowWithFocus = wx.Window.FindFocus()
        if isinstance(windowWithFocus, wx.TextCtrl):
            windowWithFocus.SetSelection(-1, -1) # Select all text
        else:
            self.viewer.selectall()


class ClearSelection(NeedsSelectionMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(ClearSelection, self).__init__(menuText=_('&Clear selection'), 
            helpText=_('Unselect all items'), *args, **kwargs)

    def doCommand(self, event):
        self.viewer.clearselection()


class ResetFilter(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(ResetFilter, self).__init__(menuText=_('&Clear all filters'),
            helpText=_('Show all items (reset all filters)'), 
            bitmap='viewalltasks', *args, **kwargs)
    
    def doCommand(self, event):
        self.viewer.resetFilter()


class ViewViewer(SettingsCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.taskFile = kwargs.pop('taskFile')
        self.viewerClass = kwargs.pop('viewerClass')
        kwargs.setdefault('bitmap', self.viewerClass.defaultBitmap) 
        super(ViewViewer, self).__init__(*args, **kwargs)
        
    def doCommand(self, event):
        viewer.addOneViewer(self.viewer, self.taskFile, self.settings, self.viewerClass)
        self.increaseViewerCount()
        
    def increaseViewerCount(self):
        setting = self.viewerClass.__name__.lower() + 'count'
        viewerCount = self.settings.getint('view', setting)
        self.settings.set('view', setting, str(viewerCount+1))
        
        
class ViewEffortViewerForSelectedTask(NeedsOneSelectedTaskMixin, SettingsCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.viewerClass = viewer.EffortViewer
        self.taskFile = kwargs.pop('taskFile')
        kwargs['bitmap'] = viewer.EffortViewer.defaultBitmap
        super(ViewEffortViewerForSelectedTask, self).__init__(*args, **kwargs)
        
    def doCommand(self, event):
        viewer.addOneViewer(self.viewer, self.taskFile, self.settings, 
                            self.viewerClass, tasksToShowEffortFor=task.TaskList(self.viewer.curselection()))
        

class RenameViewer(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(RenameViewer, self).__init__(menuText=_('&Rename viewer...'),
            helpText=_('Rename the selected viewer'), *args, **kwargs)
        
    def doCommand(self, event):
        activeViewer = self.viewer.activeViewer()
        viewerNameDialog = wx.TextEntryDialog(self.mainWindow(), 
            _('New title for the viewer:'), _('Rename viewer'), 
            activeViewer.title())
        if viewerNameDialog.ShowModal() == wx.ID_OK:
            activeViewer.setTitle(viewerNameDialog.GetValue())
        viewerNameDialog.Destroy()
        
        
class ActivateViewer(ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.direction = kwargs.pop('forward')
        super(ActivateViewer, self).__init__(*args, **kwargs)

    def doCommand(self, event):
        self.viewer.containerWidget.AdvanceSelection(self.direction)
        
    def enabled(self, event):
        return self.viewer.containerWidget.PageCount > 1
        

class HideCurrentColumn(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(HideCurrentColumn, self).__init__(menuText=_('&Hide this column'),
            helpText=_('Hide the selected column'), *args, **kwargs)
    
    def doCommand(self, event):
        columnPopupMenu = event.GetEventObject()
        self.viewer.hideColumn(columnPopupMenu.columnIndex)
        
    def enabled(self, event):
        # Unfortunately the event (an UpdateUIEvent) does not give us any
        # information to determine the current column, so we have to find 
        # the column ourselves. We use the current mouse position to do so.
        widget = self.viewer.getWidget() # Must use method to make sure viewer dispatch works!
        x, y = widget.ScreenToClient(wx.GetMousePosition())
        # Use wx.Point because CustomTreeCtrl assumes a wx.Point instance:
        columnIndex = widget.HitTest(wx.Point(x, y))[2]
        # The TreeListCtrl returns -1 for the first column sometimes,
        # don't understand why. Work around as follows:
        if columnIndex == -1:
            columnIndex = 0
        return self.viewer.isHideableColumn(columnIndex)


class ViewColumn(ViewerCommand, UICheckCommand):
    def isSettingChecked(self):
        return self.viewer.isVisibleColumnByName(self.setting)
    
    def doCommand(self, event):
        self.viewer.showColumnByName(self.setting, 
                                     self._isMenuItemChecked(event))


class ViewColumns(ViewerCommand, UICheckCommand):
    def isSettingChecked(self):
        for columnName in self.setting:
            if not self.viewer.isVisibleColumnByName(columnName):
                return False
        return True
    
    def doCommand(self, event):
        show = self._isMenuItemChecked(event)
        for columnName in self.setting:
            self.viewer.showColumnByName(columnName, show)
                        
    
class ViewExpandAll(NeedsTreeViewerMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(ViewExpandAll, self).__init__( \
            menuText=_('&Expand all items\tShift+Ctrl+E'),
            helpText=_('Expand all items with subitems'), *args, **kwargs)

    def enabled(self, event):
        return super(ViewExpandAll, self).enabled(event) and \
            self.viewer.isAnyItemExpandable()
                
    def doCommand(self, event):
        self.viewer.expandAll()
            

class ViewCollapseAll(NeedsTreeViewerMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(ViewCollapseAll, self).__init__( \
            menuText=_('&Collapse all items\tShift+Ctrl+C'),
            helpText=_('Collapse all items with subitems'), *args, **kwargs)
    
    def enabled(self, event):
        return super(ViewCollapseAll, self).enabled(event) and \
            self.viewer.isAnyItemCollapsable()
    
    def doCommand(self, event):
        self.viewer.collapseAll()


class ViewerSortByCommand(ViewerCommand, UIRadioCommand):        
    def isSettingChecked(self):
        return self.viewer.isSortedBy(self.value)
    
    def doCommand(self, event):
        self.viewer.sortBy(self.value)


class ViewerSortOrderCommand(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerSortOrderCommand, self).__init__(menuText=_('&Ascending'),
            helpText=_('Sort ascending (checked) or descending (unchecked)'),
            *args, **kwargs)

    def isSettingChecked(self):
        return self.viewer.isSortOrderAscending()
    
    def doCommand(self, event):
        self.viewer.setSortOrderAscending(self._isMenuItemChecked(event))
    
    
class ViewerSortCaseSensitive(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerSortCaseSensitive, self).__init__(\
            menuText=_('Sort &case sensitive'),
            helpText=_('When comparing text, sorting is case sensitive (checked) or insensitive (unchecked)'),
            *args, **kwargs)

    def isSettingChecked(self):
        return self.viewer.isSortCaseSensitive()
    
    def doCommand(self, event):
        self.viewer.setSortCaseSensitive(self._isMenuItemChecked(event))


class ViewerSortByTaskStatusFirst(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerSortByTaskStatusFirst, self).__init__(\
            menuText=_('Sort by status &first'),
            helpText=_('Sort tasks by status (active/inactive/completed) first'),
            *args, **kwargs)

    def isSettingChecked(self):
        return self.viewer.isSortByTaskStatusFirst()
    
    def doCommand(self, event):
        self.viewer.setSortByTaskStatusFirst(self._isMenuItemChecked(event))


class ViewerFilterByDueDateTime(ViewerCommand, UIRadioCommand):
    def isSettingChecked(self):
        return self.viewer.isFilteredByDueDateTime(self.value)
    
    def doCommand(self, event):
        self.viewer.setFilteredByDueDateTime(self.value)


class ViewerHideInactiveTasks(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerHideInactiveTasks, self).__init__(menuText=_('Hide &inactive tasks'), 
            helpText=_('Show/hide inactive tasks (tasks with a start date in the future)'),
            *args, **kwargs)
        
    def isSettingChecked(self):
        return self.viewer.isHidingInactiveTasks()
        
    def doCommand(self, event):
        self.viewer.hideInactiveTasks(self._isMenuItemChecked(event))


class ViewerHideActiveTasks(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerHideActiveTasks, self).__init__(menuText=_('Hide &active tasks'), 
            helpText=_('Show/hide active tasks (tasks with a start date in the past that are not completed)'),
            *args, **kwargs)
        
    def isSettingChecked(self):
        return self.viewer.isHidingActiveTasks()
        
    def doCommand(self, event):
        self.viewer.hideActiveTasks(self._isMenuItemChecked(event))

        
class ViewerHideCompletedTasks(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerHideCompletedTasks, self).__init__(menuText=_('Hide &completed tasks'), 
            helpText=_('Show/hide completed tasks'), *args, **kwargs)
         
    def isSettingChecked(self):
        return self.viewer.isHidingCompletedTasks()
        
    def doCommand(self, event):
        self.viewer.freeze()
        try:
            self.viewer.hideCompletedTasks(self._isMenuItemChecked(event))
        finally:
            self.viewer.thaw()


class ViewerHideCompositeTasks(ViewerCommand, UICheckCommand):
    def __init__(self, *args, **kwargs):
        super(ViewerHideCompositeTasks, self).__init__(menuText=_('Hide c&omposite tasks'),
            helpText=_('Show/hide tasks with subtasks in list mode'), 
            *args, **kwargs)
            
    def isSettingChecked(self):
        return self.viewer.isHidingCompositeTasks()
        
    def doCommand(self, event):
        self.viewer.hideCompositeTasks(self._isMenuItemChecked(event))

    def enabled(self, event):
        return not self.viewer.isTreeViewer()


class ObjectCommandBase(ViewerCommand): # pylint: disable-msg=W0223
    """ Base class for delete and edit L{UICommand}s.
    @cvar __containerName__: The name of the object list in
        the keyword arguments (e.g. 'notes', 'taskList'...)
    @cvar __bitmap__: Name of the bitmap for this command. """

    __containerName__ = None
    __bitmap__ = None

    def __init__(self, *args, **kwargs):
        kwargs['bitmap'] = self.__bitmap__
        super(ObjectCommandBase, self).__init__(*args, **kwargs)


class ObjectEdit(ObjectCommandBase):
    """ Base class for L{UICommand}s to edit objects. This will use the
    L{Viewer.editItemDialog} method to open an edit dialog. """

    __bitmap__ = 'edit'

    def __init__(self, *args, **kwargs):
        kwargs['menuText'] = kwargs[self.__containerName__].editItemMenuText
        kwargs['helpText'] = kwargs[self.__containerName__].editItemHelpText
        super(ObjectEdit, self).__init__(*args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        try:
            columnName = event.columnName
        except AttributeError:
            columnName = ''
        editor = self.viewer.editItemDialog(self.viewer.curselection(), 
                                            self.bitmap, columnName)
        editor.Show(show)


class ObjectDelete(ObjectCommandBase):
    """Base class for L{UICommand}s to delete objects. This will use
    the L{Viewer.deleteItemCommand} method to get the actual delete
    command."""

    __bitmap__ = 'delete'

    def __init__(self, *args, **kwargs):
        kwargs['menuText'] = kwargs[self.__containerName__].deleteItemMenuText
        kwargs['helpText'] = kwargs[self.__containerName__].deleteItemHelpText
        super(ObjectDelete, self).__init__(*args, **kwargs)

    def doCommand(self, event):
        deleteCommand = self.viewer.deleteItemCommand()
        deleteCommand.do()

        
class TaskNew(TaskListCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        self.taskKeywords = kwargs.pop('taskKeywords', dict())
        taskList = kwargs['taskList']
        if 'menuText' not in kwargs:
            kwargs['menuText'] = taskList.newItemMenuText
            kwargs['helpText'] = taskList.newItemHelpText
        super(TaskNew, self).__init__(bitmap='new', *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        newTaskDialog = dialog.editor.TaskEditor(self.mainWindow(), 
            command.NewTaskCommand(self.taskList, 
                categories=self.categoriesForTheNewTask(), 
                prerequisites=self.prerequisitesForTheNewTask(),
                dependencies=self.dependenciesForTheNewTask(), 
                **self.taskKeywords), 
            self.settings, self.taskList, self.mainWindow().taskFile, 
            bitmap=self.bitmap)
        newTaskDialog.Show(show)
        return newTaskDialog # for testing purposes

    def categoriesForTheNewTask(self):
        return self.mainWindow().taskFile.categories().filteredCategories()

    def prerequisitesForTheNewTask(self):
        return []

    def dependenciesForTheNewTask(self):
        return []
    

class TaskNewFromTemplate(TaskNew):
    def __init__(self, filename, *args, **kwargs):
        super(TaskNewFromTemplate, self).__init__(*args, **kwargs)
        self.__filename = filename
        templateTask = self.__readTemplate()
        self.menuText = '&' + templateTask.subject()

    def __readTemplate(self):
        return persistence.TemplateXMLReader(file(self.__filename,
                                                  'rU')).read()

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        # The task template is read every time because it's the
        # TemplateXMLReader that evaluates dynamic values (Now()
        # should be evaluated at task creation for instance).
        templateTask = self.__readTemplate()
        kwargs = templateTask.__getcopystate__()
        kwargs['categories'] = self.categoriesForTheNewTask()
        # pylint: disable-msg=W0142
        newTaskDialog = dialog.editor.TaskEditor(self.mainWindow(), 
            command.NewTaskCommand(self.taskList, **kwargs),
            self.settings, self.taskList, self.mainWindow().taskFile, 
            bitmap=self.bitmap)
        newTaskDialog.Show(show)
        return newTaskDialog # for testing purposes
   
   
class TaskNewFromTemplateButton(PopupButtonMixin, TaskListCommand, SettingsCommand):
    def createPopupMenu(self):
        import menu
        return menu.TaskTemplateMenu(self.mainWindow(), self.taskList, 
                                     self.settings)

    def getMenuText(self):
        return _('New task from &template')

    def getHelpText(self):
        return _('Create a new task from a template')


class NewTaskWithSelectedCategories(TaskNew, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(NewTaskWithSelectedCategories, self).__init__(\
            menuText=_('New task with selected &categories...'),
            helpText=_('Insert a new task with the selected categories checked'),
            *args, **kwargs)

    def categoriesForTheNewTask(self):
        return self.viewer.curselection()
    
    
class NewTaskWithSelectedTasksAsPrerequisites(NeedsSelectedTasksMixin, TaskNew, 
                                              ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(NewTaskWithSelectedTasksAsPrerequisites, self).__init__(
            menuText=_('New task with selected tasks as &prerequisites...'),
            helpText=_('Insert a new task with the selected tasks as prerequisite tasks'),
            *args, **kwargs)

    def prerequisitesForTheNewTask(self):
        return self.viewer.curselection()
    

class NewTaskWithSelectedTasksAsDependencies(NeedsSelectedTasksMixin, TaskNew,
                                             ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(NewTaskWithSelectedTasksAsDependencies, self).__init__(
            menuText=_('New task with selected tasks as &dependencies...'),
            helpText=_('Insert a new task with the selected tasks as dependent tasks'),
            *args, **kwargs)

    def dependenciesForTheNewTask(self):
        return self.viewer.curselection()
    
    
class TaskNewSubTask(NeedsOneSelectedTaskMixin, TaskListCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        taskList = kwargs['taskList']
        super(TaskNewSubTask, self).__init__(bitmap='newsub',
            menuText=taskList.newSubItemMenuText,
            helpText=taskList.newSubItemHelpText, *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        newSubItemDialog = self.viewer.newSubItemDialog(bitmap=self.bitmap)
        newSubItemDialog.Show(show)
        

class TaskEdit(ObjectEdit, NeedsSelectedTasksMixin, TaskListCommand):
    __containerName__ = 'taskList'


class TaskDelete(ObjectDelete, NeedsSelectedTasksMixin, TaskListCommand):
    __containerName__ = 'taskList'


class TaskToggleCompletion(NeedsSelectedTasksMixin, ViewerCommand):
    defaultMenuText = _('&Mark task completed\tCtrl+RETURN')
    defaultHelpText = _('Mark the selected task(s) completed')
    alternativeMenuText = _('&Mark task uncompleted\tCtrl+RETURN')
    alternativeHelpText = _('Mark the selected task(s) uncompleted')
    
    def __init__(self, *args, **kwargs):
        super(TaskToggleCompletion, self).__init__(bitmap='markuncompleted',
            bitmap2='markcompleted', menuText=self.defaultMenuText,
            helpText=self.defaultHelpText,
            kind=wx.ITEM_CHECK, *args, **kwargs)
        self.currentBitmap = None # Don't know yet what our bitmap is
                
    def doCommand(self, event):
        markCompletedCommand = command.MarkCompletedCommand( \
            self.viewer.presentation(), self.viewer.curselection())
        markCompletedCommand.do()
            
    def onUpdateUI(self, event):
        super(TaskToggleCompletion, self).onUpdateUI(event)
        allSelectedTasksAreCompleted = self.allSelectedTasksAreCompleted()
        self.updateToolState(allSelectedTasksAreCompleted)
        bitmapName = self.bitmap if allSelectedTasksAreCompleted else self.bitmap2
        if bitmapName != self.currentBitmap:
            self.currentBitmap = bitmapName
            self.updateToolBitmap(bitmapName)
            self.updateToolHelp()     
            self.updateMenuItems(allSelectedTasksAreCompleted)
    
    def updateToolState(self, allSelectedTasksAreCompleted):
        if not self.toolbar: return # Toolbar is hidden        
        if allSelectedTasksAreCompleted != self.toolbar.GetToolState(self.id): 
            self.toolbar.ToggleTool(self.id, allSelectedTasksAreCompleted)

    def updateToolBitmap(self, bitmapName):
        if not self.toolbar: return # Toolbar is hidden
        bitmap = wx.ArtProvider_GetBitmap(bitmapName, wx.ART_TOOLBAR, 
                                          self.toolbar.GetToolBitmapSize())
        # On wxGTK, changing the bitmap doesn't work when the tool is 
        # disabled, so we first enable it if necessary:
        disable = False
        if not self.toolbar.GetToolEnabled(self.id):
            self.toolbar.EnableTool(self.id, True)
            disable = True
        self.toolbar.SetToolNormalBitmap(self.id, bitmap)
        if disable:
            self.toolbar.EnableTool(self.id, False)     
    
    def updateMenuItems(self, allSelectedTasksAreCompleted):
        menuText = self.getMenuText(allSelectedTasksAreCompleted)
        helpText = self.getHelpText(allSelectedTasksAreCompleted)
        for menuItem in self.menuItems:
            menuItem.Check(allSelectedTasksAreCompleted)
            menuItem.SetItemLabel(menuText)
            menuItem.SetHelp(helpText)
        
    def getMenuText(self, allSelectedTasksAreCompleted=None): # pylint: disable-msg=W0221
        if allSelectedTasksAreCompleted is None:
            allSelectedTasksAreCompleted = self.allSelectedTasksAreCompleted()
        return self.alternativeMenuText if allSelectedTasksAreCompleted else self.defaultMenuText
        
    def getHelpText(self, allSelectedTasksAreCompleted=None): # pylint: disable-msg=W0221
        if allSelectedTasksAreCompleted is None:
            allSelectedTasksAreCompleted = self.allSelectedTasksAreCompleted()
        return self.alternativeHelpText if allSelectedTasksAreCompleted else self.defaultHelpText
        
    def allSelectedTasksAreCompleted(self):
        if super(TaskToggleCompletion, self).enabled(None) and \
           len(self.viewer.curselection()) < 20:
            for selectedTask in self.viewer.curselection():
                if not selectedTask.completed():
                    return False
            return True
        else:
            return False

    
class TaskMaxPriority(NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(TaskMaxPriority, self).__init__(
            menuText=_('&Maximize priority\tShift+Ctrl+I'),
            helpText=_('Make the selected task(s) the highest priority task(s)'), 
            bitmap='maxpriority', *args, **kwargs)
        
    def doCommand(self, event):
        maxPriority = command.MaxPriorityCommand(self.taskList, 
                                                 self.viewer.curselection())
        maxPriority.do()
    

class TaskMinPriority(NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(TaskMinPriority, self).__init__(
            menuText=_('&Minimize priority\tShift+Ctrl+D'),
            helpText=_('Make the selected task(s) the lowest priority task(s)'), 
            bitmap='minpriority', *args, **kwargs)
        
    def doCommand(self, event):
        minPriority = command.MinPriorityCommand(self.taskList, 
                                                 self.viewer.curselection())
        minPriority.do()


class TaskIncPriority(NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand):    
    def __init__(self, *args, **kwargs):
        super(TaskIncPriority, self).__init__(
            menuText=_('&Increase priority\tCtrl+I'),
            helpText=_('Increase the priority of the selected task(s)'), 
            bitmap='incpriority', *args, **kwargs)
        
    def doCommand(self, event):
        incPriority = command.IncPriorityCommand(self.taskList, 
                                                 self.viewer.curselection())
        incPriority.do()


class TaskDecPriority(NeedsSelectedTasksMixin, TaskListCommand, ViewerCommand):    
    def __init__(self, *args, **kwargs):
        super(TaskDecPriority, self).__init__(
            menuText=_('&Decrease priority\tCtrl+D'),
            helpText=_('Decrease the priority of the selected task(s)'), 
            bitmap='decpriority', *args, **kwargs)
        
    def doCommand(self, event):
        decPriority = command.DecPriorityCommand(self.taskList, 
                                                 self.viewer.curselection())
        decPriority.do()


class DragAndDropCommand(ViewerCommand):
    def onCommandActivate(self, dropItem, dragItem): # pylint: disable-msg=W0221
        ''' Override onCommandActivate to be able to accept two items instead
            of one event. '''
        self.doCommand(dropItem, dragItem)

    def doCommand(self, dropItem, dragItem): # pylint: disable-msg=W0221
        dragAndDropCommand = self.createCommand(dragItem, dropItem)
        if dragAndDropCommand.canDo():
            dragAndDropCommand.do()
            
    def createCommand(self, dragItem, dropItem):
        raise NotImplementedError
    

class TaskDragAndDrop(DragAndDropCommand, TaskListCommand):
    def createCommand(self, dragItem, dropItem):
        return command.DragAndDropTaskCommand(self.taskList, [dragItem], 
                                              drop=[dropItem])


class EditSubject(ViewerCommand):
    def onCommandActivate(self, item, newSubject): # pylint: disable-msg=W0221
        ''' Override onCommandActivate to tbe able to accept an item and the
            new subject. '''
        self.doCommand(item, newSubject)
        
    def doCommand(self, item, newSubject):
        if newSubject and newSubject != item.subject():
            editSubject = command.EditSubjectCommand(self.viewer.presentation(),
                                                     [item], subject=newSubject)
            editSubject.do()
        

class ToggleCategory(NeedsSelectionMixin, ViewerCommand):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category')
        subject = self.category.subject()
        # Would like to use wx.ITEM_RADIO for mutual exclusive categories, but
        # a menu with radio items always has to have at least of the items 
        # checked, while we allow none of the mutual exclusive categories to
        # be checked. Dynamically changing between wx.ITEM_CHECK and 
        # wx.ITEM_RADIO would be a work-around in theory, using wx.ITEM_CHECK 
        # when none of the mutual exclusive categories is checked and 
        # wx.ITEM_RADIO otherwise, but dynamically changing the type of menu 
        # items isn't possible. Hence, we use wx.ITEM_CHECK, even for mutual 
        # exclusive categories.
        kind = wx.ITEM_CHECK
        super(ToggleCategory, self).__init__(menuText='&' + subject,
            helpText=_('Toggle %s')%subject, kind=kind, *args, **kwargs)
        
    def doCommand(self, event):
        check = command.ToggleCategoryCommand(category=self.category,
                                              items=self.viewer.curselection())
        check.do()
        
    def onUpdateUI(self, event):
        super(ToggleCategory, self).onUpdateUI(event)
        if self.enabled(event):
            check = self.category in self.viewer.curselection()[0].categories()
            for menuItem in self.menuItems:
                menuItem.Check(check)

    def enabled(self, event):
        viewerHasSelection = super(ToggleCategory, self).enabled(event)
        viewerIsNotShowingCategories = not self.viewer.isShowingCategories()
        if viewerHasSelection and viewerIsNotShowingCategories:
            selectionCategories = self.viewer.curselection()[0].categories()
            for ancestor in self.category.ancestors():
                if ancestor.isMutualExclusive() and ancestor not in selectionCategories:
                    return False # Not all mutual exclusive ancestors are checked
            return True # All mutual exclusive ancestors are checked
        else:
            return False # Either viewer is not showing categories or no selection



class TaskToggleCategory(ToggleCategory):
    def enabled(self, event):
        return super(TaskToggleCategory, self).enabled(event) and \
            self.viewer.isShowingTasks()


class NoteToggleCategory(ToggleCategory):
    def enabled(self, event):        
        return super(NoteToggleCategory, self).enabled(event) and \
            self.viewer.isShowingNotes()
    

class MailItem(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(MailItem, self).__init__(bitmap='envelope_icon', *args, **kwargs)

    def doCommand(self, event, mail=writeMail, showerror=wx.MessageBox): # pylint: disable-msg=W0221
        items = self.viewer.curselection()
        subject = self.subject(items)
        body = self.body(items)
        self.mail(subject, body, mail, showerror)

    def subject(self, items):
        if len(items) > 1:
            return self.subjectForMultipleItems()
        else:
            return items[0].subject(recursive=True)
        
    def subjectForMultipleItems(self):
        raise NotImplementedError
        
    def body(self, items):
        if len(items) > 1:
            bodyLines = []
            for item in items:
                bodyLines.append(item.subject(recursive=True) + '\n')
                if item.description():
                    bodyLines.extend(item.description().splitlines())
                    bodyLines.append('\n')
        else:
            bodyLines = items[0].description().splitlines()
        return '\r\n'.join(bodyLines)        

    def mail(self, subject, body, mail, showerror):
        try:
            mail('', subject, body)
        except:
            # Try again with a dummy recipient:
            try:
                mail('recipient@domain.com', subject, body)
            except Exception, reason: # pylint: disable-msg=W0703
                showerror(_('Cannot send email:\n%s')%reason, 
                      caption=_('%s mail error')%meta.name, 
                      style=wx.ICON_ERROR)        
 

class TaskMail(NeedsSelectedTasksMixin, MailItem):
    def __init__(self, *args, **kwargs):
        super(TaskMail, self).__init__(menuText=_('&Mail task'),
            helpText=_('Mail the task, using your default mailer'),
            *args, **kwargs)

    def subjectForMultipleItems(self):
        return _('Tasks')


class NoteMail(NeedsSelectedNoteMixin, MailItem):
    def __init__(self, *args, **kwargs):
        super(NoteMail, self).__init__(menuText=_('&Mail note'),
            helpText=_('Mail the note, using your default mailer'),
            *args, **kwargs)

    def subjectForMultipleItems(self):
        return _('Notes')


class ItemAddNote(ViewerCommand, SettingsCommand):
    menuText=_('Add &note')
    helpText = 'Subclass responsibility'
    AddNoteCommand = lambda: 'Subclass responsibility'
    
    def __init__(self, *args, **kwargs):
        super(ItemAddNote, self).__init__(menuText=self.menuText,
            helpText=self.helpText, bitmap='new', *args, **kwargs)
            
    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        editDialog = dialog.editor.NoteEditor(self.mainWindow(), 
            self.AddNoteCommand(self.viewer.presentation(), 
                                self.viewer.curselection()),
            self.settings, self.viewer.presentation(),  
            self.mainWindow().taskFile, bitmap=self.bitmap)
        editDialog.Show(show)
        return editDialog # for testing purposes


class TaskAddNote(NeedsOneSelectedTaskMixin, ItemAddNote):
    helpText=_('Add a note to the selected task')
    AddNoteCommand = command.AddTaskNoteCommand 


class CategoryAddNote(NeedsOneSelectedCategoryMixin, ItemAddNote):
    helpText = _('Add a note to the selected category')
    AddNoteCommand = command.AddCategoryNoteCommand
        

class AttachmentAddNote(NeedsOneSelectedAttachmentMixin, ItemAddNote):
    helpText=_('Add a note to the selected attachment')
    AddNoteCommand = command.AddAttachmentNoteCommand
        

class EffortNew(NeedsAtLeastOneTaskMixin, ViewerCommand, EffortListCommand, 
                TaskListCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        effortList = kwargs['effortList']
        super(EffortNew, self).__init__(bitmap='new',  
            menuText=effortList.newItemMenuText, 
            helpText=effortList.newItemHelpText, *args, **kwargs)

    def doCommand(self, event, show=True):
        if self.viewer.isShowingTasks() and self.viewer.curselection():
            selectedTasks = self.viewer.curselection()
        elif self.viewer.isShowingEffort():
            selectedEfforts = self.viewer.curselection()
            if selectedEfforts:
                selectedTasks = [selectedEfforts[0].task()]
            else:
                selectedTasks = [self.firstTask(self.viewer.domainObjectsToView())]
        else:
            selectedTasks = [self.firstTask(self.taskList)]

        newEffortDialog = dialog.editor.EffortEditor(self.mainWindow(), 
            command.NewEffortCommand(self.effortList, selectedTasks),
            self.settings, self.effortList, self.mainWindow().taskFile, 
            bitmap=self.bitmap)
        if show:
            newEffortDialog.Show()
        return newEffortDialog

    @staticmethod    
    def firstTask(tasks):
        subjectDecoratedTasks = [(eachTask.subject(recursive=True), 
            eachTask) for eachTask in tasks]
        subjectDecoratedTasks.sort()
        return subjectDecoratedTasks[0][1]


class EffortEdit(ObjectEdit, NeedsSelectedEffortMixin, EffortListCommand):
    __containerName__ = 'effortList'


class EffortDelete(ObjectDelete, NeedsSelectedEffortMixin, EffortListCommand):
    __containerName__ = 'effortList'


class EffortStart(NeedsSelectedTasksMixin, ViewerCommand, TaskListCommand):
    ''' UICommand to start tracking effort for the selected task(s). '''
    
    def __init__(self, *args, **kwargs):
        super(EffortStart, self).__init__(bitmap='clock_icon',
            menuText=_('&Start tracking effort'), 
            helpText=_('Start tracking effort for the selected task(s)'), 
            *args, **kwargs)
    
    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, 
            self.viewer.curselection())
        start.do()
        
    def enabled(self, event):
        return super(EffortStart, self).enabled(event) and \
            any(task.active() and not task.isBeingTracked() \
                for task in self.viewer.curselection())


class EffortStartForTask(TaskListCommand):
    ''' UICommand to start tracking for a specific task. This command can
        be used to build a menu with separate menu items for all tasks. 
        See gui.menu.StartEffortForTaskMenu. '''
        
    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop('task')
        subject = self.task.subject() or _('(No subject)') 
        super(EffortStartForTask, self).__init__( \
            bitmap=self.task.icon(recursive=True), menuText='&'+subject,
            helpText=_('Start tracking effort for %s')%subject, 
            *args, **kwargs)
        
    def doCommand(self, event):
        start = command.StartEffortCommand(self.taskList, [self.task])
        start.do()
        
    def enabled(self, event):
        return not self.task.isBeingTracked() and not self.task.completed()      


class EffortStartButton(PopupButtonMixin, TaskListCommand):
    def __init__(self, *args, **kwargs):
        kwargs['taskList'] = base.filter.DeletedFilter(kwargs['taskList'])
        super(EffortStartButton, self).__init__(bitmap='clock_menu_icon',
            menuText=_('&Start tracking effort'),
            helpText=_('Select a task via the menu and start tracking effort for it'),
            *args, **kwargs)

    def createPopupMenu(self):
        import menu
        return menu.StartEffortForTaskMenu(self.mainWindow(), self.taskList)

    def enabled(self, event):
        return any(task.active() for task in self.taskList)
    

class EffortStop(TaskListCommand):
    def __init__(self, *args, **kwargs):
        super(EffortStop, self).__init__(bitmap='clock_stop_icon',
            menuText=_('St&op tracking effort'),
            helpText=_('Stop tracking effort for the active task(s)'), 
            *args, **kwargs)

    def doCommand(self, event):
        stop = command.StopEffortCommand(self.taskList)
        stop.do()

    def enabled(self, event):
        return any(task.isBeingTracked() for task in self.taskList)


class CategoryNew(CategoriesCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        categories = kwargs['categories']
        super(CategoryNew, self).__init__(bitmap='new', 
            menuText=categories.newItemMenuText,
            helpText=categories.newItemHelpText, *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        taskFile = self.mainWindow().taskFile
        newCategoryDialog = dialog.editor.CategoryEditor(self.mainWindow(), 
            command.NewCategoryCommand(self.categories),
            self.settings, taskFile.categories(), taskFile, bitmap=self.bitmap)
        newCategoryDialog.Show(show)
        

class CategoryNewSubCategory(NeedsOneSelectedCategoryMixin, CategoriesCommand, 
                             ViewerCommand):
    def __init__(self, *args, **kwargs):
        categories = kwargs['categories']
        super(CategoryNewSubCategory, self).__init__(bitmap='newsub', 
            menuText=categories.newSubItemMenuText, 
            helpText=categories.newSubItemHelpText, *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        newSubItemDialog = self.viewer.newSubItemDialog(bitmap=self.bitmap)
        newSubItemDialog.Show(show)


class CategoryDelete(ObjectDelete, NeedsSelectedCategoryMixin, CategoriesCommand):
    __containerName__ = 'categories'


class CategoryEdit(ObjectEdit, NeedsSelectedCategoryMixin, CategoriesCommand):
    __containerName__ = 'categories'


class CategoryDragAndDrop(DragAndDropCommand, CategoriesCommand):
    def createCommand(self, dragItem, dropItem):
        return command.DragAndDropCategoryCommand(self.categories, [dragItem], 
                                                  drop=[dropItem])


class NoteNew(NotesCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        notes = kwargs['notes']
        if 'menuText' not in kwargs:
            kwargs['menuText'] = notes.newItemMenuText
            kwargs['helpText'] = notes.newItemHelpText
        super(NoteNew, self).__init__(bitmap='new', *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        noteDialog = dialog.editor.NoteEditor(self.mainWindow(), 
            command.NewNoteCommand(self.notes,
                  categories=self.categoriesForTheNewNote()),
            self.settings, self.notes, self.mainWindow().taskFile,
            bitmap=self.bitmap)
        noteDialog.Show(show)
        return noteDialog # for testing purposes

    def categoriesForTheNewNote(self):
        return self.mainWindow().taskFile.categories().filteredCategories()
    

class NewNoteWithSelectedCategories(NoteNew, ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(NewNoteWithSelectedCategories, self).__init__(\
            menuText=_('New &note with selected categories...'),
            helpText=_('Insert a new note with the selected categories checked'),
            *args, **kwargs)

    def categoriesForTheNewNote(self):
        return self.viewer.curselection()


class NoteNewSubNote(NeedsOneSelectedNoteMixin, NotesCommand, ViewerCommand):
    def __init__(self, *args, **kwargs):
        notes = kwargs['notes']
        super(NoteNewSubNote, self).__init__(bitmap='newsub', 
            menuText=notes.newSubItemMenuText, 
            helpText=notes.newSubItemHelpText, *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        newSubItemDialog = self.viewer.newSubItemDialog(bitmap=self.bitmap)
        newSubItemDialog.Show(show)


class NoteDelete(ObjectDelete, NeedsSelectedNoteMixin, NotesCommand):
    __containerName__ = 'notes'


class NoteEdit(ObjectEdit, NeedsSelectedNoteMixin, NotesCommand):
    __containerName__ = 'notes'


class NoteDragAndDrop(DragAndDropCommand, NotesCommand):
    def createCommand(self, dragItem, dropItem):
        return command.DragAndDropNoteCommand(self.notes, [dragItem], 
                                              drop=[dropItem])
 
                                                        
class AttachmentNew(AttachmentsCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        attachments = kwargs['attachments']
        if 'menuText' not in kwargs:
            kwargs['menuText'] = attachments.newItemMenuText
            kwargs['helpText'] = attachments.newItemHelpText
        super(AttachmentNew, self).__init__(bitmap='new', *args, **kwargs)

    def doCommand(self, event, show=True): # pylint: disable-msg=W0221
        attachmentDialog = dialog.editor.AttachmentEditor(self.mainWindow(), 
            command.NewAttachmentCommand(self.attachments),
            self.settings, self.attachments, self.mainWindow().taskFile, 
            bitmap=self.bitmap)
        attachmentDialog.Show(show)
        return attachmentDialog # for testing purposes


class AttachmentDelete(ObjectDelete, NeedsSelectedAttachmentsMixin, AttachmentsCommand):
    __containerName__ = 'attachments'


class AttachmentEdit(ObjectEdit, NeedsSelectedAttachmentsMixin, AttachmentsCommand):
    __containerName__ = 'attachments'


class AddAttachment(NeedsSelectionMixin, ViewerCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(AddAttachment, self).__init__(menuText=_('&Add attachment'),          
            bitmap='paperclip_icon', *args, **kwargs)
        
    def doCommand(self, event):
        filename = widgets.AttachmentSelector()
        if not filename:
            return
        attachmentBase = self.settings.get('file', 'attachmentbase')
        if attachmentBase:
            filename = attachment.getRelativePath(filename, attachmentBase)
        addAttachmentCommand = command.AddAttachmentCommand( \
            self.viewer.presentation(), self.viewer.curselection(), 
            attachments=[attachment.FileAttachment(filename)])
        addAttachmentCommand.do()
        
    def enabled(self, event):
        return super(AddAttachment, self).enabled(event) and \
            not any(isinstance(item, effort.Effort) for item in self.viewer.curselection())


class AddTaskAttachment(NeedsTaskViewerMixin, AddAttachment):
    def __init__(self, *args, **kwargs):
        super(AddTaskAttachment, self).__init__(\
            helpText=_('Browse for files to add as attachment to the selected task(s)'),
            *args, **kwargs)


class AddCategoryAttachment(NeedsCategoryViewerMixin, AddAttachment):
    def __init__(self, *args, **kwargs):
        super(AddCategoryAttachment, self).__init__(\
            helpText=_('Browse for files to add as attachment to the selected categories'),
            *args, **kwargs)


class AddNoteAttachment(NeedsNoteViewerMixin, AddAttachment):
    def __init__(self, *args, **kwargs):
        super(AddNoteAttachment, self).__init__(\
            helpText=_('Browse for files to add as attachment to the selected note(s)'),
            *args, **kwargs)


def openAttachments(attachments, settings, showerror):
    attachmentBase = settings.get('file', 'attachmentbase')
    for eachAttachment in attachments:
        try:
            eachAttachment.open(attachmentBase)
        except Exception, instance: # pylint: disable-msg=W0703
            showerror(render.exception(Exception, instance), 
                      caption=_('Error opening attachment'), 
                      style=wx.ICON_ERROR)


class AttachmentOpen(NeedsSelectedAttachmentsMixin, ViewerCommand, AttachmentsCommand,
                     SettingsCommand):
    def __init__(self, *args, **kwargs):
        attachments = kwargs['attachments']
        super(AttachmentOpen, self).__init__(bitmap='fileopen',
            menuText=attachments.openItemMenuText,
            helpText=attachments.openItemHelpText, *args, **kwargs)

    def doCommand(self, event, showerror=wx.MessageBox): # pylint: disable-msg=W0221
        openAttachments(self.viewer.curselection(), self.settings, showerror)


class OpenAllAttachments(NeedsSelectionWithAttachmentsMixin, ViewerCommand, 
                         SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(OpenAllAttachments, self).__init__(\
           menuText=_('&Open all attachments'), 
           bitmap='paperclip_icon', *args, **kwargs)
        
    def doCommand(self, event, showerror=wx.MessageBox): # pylint: disable-msg=W0221
        allAttachments = []
        for item in self.viewer.curselection():
            allAttachments.extend(item.attachments())
        openAttachments(allAttachments, self.settings, showerror)


class OpenAllTaskAttachments(NeedsTaskViewerMixin, OpenAllAttachments):
    def __init__(self, *args, **kwargs):
        super(OpenAllTaskAttachments, self).__init__(\
            helpText=_('Open all attachments of the selected task(s)'),
            *args, **kwargs)


class OpenAllCategoryAttachments(NeedsCategoryViewerMixin, OpenAllAttachments):
    def __init__(self, *args, **kwargs):
        super(OpenAllCategoryAttachments, self).__init__(\
            helpText=_('Open all attachments of the selected categories'),
            *args, **kwargs)


class OpenAllNoteAttachments(NeedsNoteViewerMixin, OpenAllAttachments):
    def __init__(self, *args, **kwargs):
        super(OpenAllNoteAttachments, self).__init__(\
            helpText=_('Open all attachments of the selected note(s)'),
            *args, **kwargs)
            

class DialogCommand(UICommand):
    def __init__(self, *args, **kwargs):
        self._dialogTitle = kwargs.pop('dialogTitle')
        self._dialogText = kwargs.pop('dialogText')
        self._direction = kwargs.pop('direction', None)
        self.closed = True
        super(DialogCommand, self).__init__(*args, **kwargs)
        
    def doCommand(self, event):
        self.closed = False
        # pylint: disable-msg=W0201
        self.dialog = widgets.HTMLDialog(self._dialogTitle, self._dialogText, 
                                    bitmap=self.bitmap, 
                                    direction=self._direction)
        for event in wx.EVT_CLOSE, wx.EVT_BUTTON:
            self.dialog.Bind(event, self.onClose)
        self.dialog.Show()
        
    def onClose(self, event):
        self.closed = True
        self.dialog.Destroy()
        event.Skip()
        
    def enabled(self, event):
        return self.closed

        
class Help(DialogCommand):
    def __init__(self, *args, **kwargs):
        if '__WXMAC__' in wx.PlatformInfo:
            # Use default keyboard shortcut for Mac OS X:
            menuText = _('&Help contents\tCtrl+?') 
        else:
            # Use a letter, because 'Ctrl-?' doesn't work on Windows:
            menuText = _('&Help contents\tCtrl+H')
        super(Help, self).__init__(menuText=menuText,
            helpText=_('Help about the program'),
            bitmap='led_blue_questionmark_icon', dialogTitle=_('Help'),
            dialogText=help.helpHTML, id=wx.ID_HELP, *args, **kwargs)


class Tips(SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(Tips, self).__init__(menuText=_('&Tips'),
            helpText=_('Tips about the program'),
            bitmap='led_blue_questionmark_icon', *args, **kwargs)

    def doCommand(self, event):
        help.showTips(self.mainWindow(), self.settings)
        

class InfoCommand(DialogCommand):
    def __init__(self, *args, **kwargs):
        super(InfoCommand, self).__init__(bitmap='led_blue_information_icon',
                                          *args, **kwargs)
    
    
class HelpAbout(InfoCommand):
    def __init__(self, *args, **kwargs):
        super(HelpAbout, self).__init__(menuText=_('&About %s')%meta.name,
            helpText=_('Version and contact information about %s')%meta.name, 
            dialogTitle=_('Help: About %s')%meta.name, 
            dialogText=help.aboutHTML, id=wx.ID_ABOUT, *args, **kwargs)
        
  
class HelpLicense(InfoCommand):
    def __init__(self, *args, **kwargs):
        super(HelpLicense, self).__init__(menuText=_('&License'),
            helpText=_('%s license')%meta.name,
            dialogTitle=_('Help: %s license')%meta.name, 
            dialogText=meta.licenseHTML, direction=wx.Layout_LeftToRight, 
            *args, **kwargs)


class MainWindowRestore(UICommand):
    def __init__(self, *args, **kwargs):
        super(MainWindowRestore, self).__init__(menuText=_('&Restore'),
            helpText=_('Restore the window to its previous state'),
            bitmap='restore', *args, **kwargs)

    def doCommand(self, event):
        self.mainWindow().restore(event)
    

class Search(ViewerCommand, SettingsCommand):
    # Search can only be attached to a real viewer, not to a viewercontainer
    def __init__(self, *args, **kwargs):
        super(Search, self).__init__(*args, **kwargs)
        assert self.viewer.isSearchable()
                           
    def onFind(self, searchString, matchCase, includeSubItems, 
               searchDescription):
        self.viewer.setSearchFilter(searchString, matchCase, includeSubItems, 
                                    searchDescription)

    def appendToToolBar(self, toolbar):
        searchString, matchCase, includeSubItems, searchDescription = self.viewer.getSearchFilter()
        # pylint: disable-msg=W0201
        self.searchControl = widgets.SearchCtrl(toolbar, value=searchString,
            style=wx.TE_PROCESS_ENTER, matchCase=matchCase, 
            includeSubItems=includeSubItems, searchDescription=searchDescription,
            callback=self.onFind)
        toolbar.AddControl(self.searchControl)

    def doCommand(self, event):
        pass # Not used
    

class ToolbarChoiceCommandMixin(object):
    def appendToToolBar(self, toolbar):
        ''' Add our choice control to the toolbar. '''
        # pylint: disable-msg=W0201
        self.choiceCtrl = wx.Choice(toolbar, choices=self.choiceLabels)
        self.currentChoice = self.choiceCtrl.Selection
        self.choiceCtrl.Bind(wx.EVT_CHOICE, self.onChoice)
        toolbar.AddControl(self.choiceCtrl)
        
    def onChoice(self, event):
        ''' The user selected a choice from the choice control. '''
        choiceIndex = event.GetInt()
        if choiceIndex == self.currentChoice:
            return
        self.currentChoice = choiceIndex
        self.doChoice(self.choiceData[choiceIndex])
        
    def doChoice(self, choice):
        raise NotImplementedError
    
    def doCommand(self, event):
        pass # Not used
        
    def setChoice(self, choice):
        ''' Programmatically set the current choice in the choice control. '''
        index = self.choiceData.index(choice)
        self.choiceCtrl.Selection = index
        self.currentChoice = index


class ToolbarCountCommandMixin(object):
    def appendToToolBar(self, toolbar):
        self.spinCtrl = wx.SpinCtrl(toolbar, wx.ID_ANY, '1')
        self.currentValue = 1
        self.spinCtrl.SetRange(self.minValue, self.maxValue)
        self.spinCtrl.Bind(wx.EVT_SPINCTRL, self.onValue)
        self.spinCtrl.Bind(wx.EVT_TEXT, self.onValue)
        toolbar.AddControl(self.spinCtrl)

    def enable(self, enabled):
        self.spinCtrl.Enable(enabled)

    def onValue(self, event):
        try:
            value = int(self.spinCtrl.GetValue())
        except ValueError:
            pass
        else:
            if value != self.currentValue:
                self.currentValue = value
                self.doValue(value)

    def doValue(self, value):
        raise NotImplementedError

    def doCommand(self, event):
        pass

    def setValue(self, value):
        self.spinCtrl.SetValue(value)
        self.currentValue = value


class EffortViewerAggregationChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Effort details'), _('Effort per day'), 
                    _('Effort per week'), _('Effort per month')]
    choiceData = ['details', 'day', 'week', 'month']

    def doChoice(self, choice):
        self.viewer.showEffortAggregation(choice)
        

class TaskViewerTreeOrListChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Tree of tasks'), _('List of tasks')]
    choiceData = [True, False]
    
    def doChoice(self, choice):
        self.viewer.showTree(choice)
        

class CategoryViewerFilterChoice(ToolbarChoiceCommandMixin, SettingsCommand):
    choiceLabels = [_('Filter on all checked categories'),
                    _('Filter on any checked category')]
    choiceData = [True, False]

    def doChoice(self, choice):
        self.settings.set('view', 'categoryfiltermatchall', str(choice))


class SquareTaskViewerOrderChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Budget'), _('Time spent'), _('Fixed fee'), _('Revenue'), _('Priority')]
    choiceData = ['budget', 'timeSpent', 'fixedFee', 'revenue', 'priority']
    
    def doChoice(self, choice):
        self.viewer.orderBy(choice)


class CalendarViewerPeriodCount(ToolbarCountCommandMixin, ViewerCommand):
    minValue = 1
    maxValue = 100

    def doValue(self, value):
        self.viewer.SetPeriodCount(value)


class CalendarViewerTypeChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Day(s)'), _('Week(s)'), _('Month')]
    choiceData = [wxSCHEDULER_DAILY, wxSCHEDULER_WEEKLY, wxSCHEDULER_MONTHLY]

    def doChoice(self, choice):
        self.viewer.freeze()
        try:
            self.viewer.SetViewType(choice)
        finally:
            self.viewer.thaw()


class CalendarViewerOrientationChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Horizontal'), _('Vertical')]
    choiceData = [wxSCHEDULER_HORIZONTAL, wxSCHEDULER_VERTICAL]

    def doChoice(self, choice):
        self.viewer.freeze()
        try:
            self.viewer.SetViewOrientation(choice)
        finally:
            self.viewer.thaw()


class CalendarViewerNavigationCommand(ViewerCommand):
    def __init__(self, *args, **kwargs):
        super(CalendarViewerNavigationCommand, self).__init__( \
            menuText=self.menuText, helpText=self.helpText, bitmap=self.bitmap, 
            *args, **kwargs)

    def doCommand(self, event):
        self.viewer.freeze()
        try:
            self.viewer.SetViewType(self.calendarViewType)
        finally:
            self.viewer.thaw()


class CalendarViewerNextPeriod(CalendarViewerNavigationCommand):
    menuText = _('&Next period')
    helpText = _('Show next period')
    bitmap = 'next'
    calendarViewType = wxSCHEDULER_NEXT
    

class CalendarViewerPreviousPeriod(CalendarViewerNavigationCommand):
    menuText = _('&Previous period')
    helpText = _('Show previous period')
    bitmap = 'prev'
    calendarViewType = wxSCHEDULER_PREV
    

class CalendarViewerToday(CalendarViewerNavigationCommand):
    menuText = _('&Today')
    helpText = _('Show today')
    bitmap = 'calendar_icon'
    calendarViewType = wxSCHEDULER_TODAY


class CalendarViewerTaskFilterChoice(ToolbarChoiceCommandMixin, ViewerCommand):
    choiceLabels = [_('Start and due date'), _('Start date'), _('Due date'), _('All but unplanned'), _('All')]
    choiceData = [(False, False, False), (False, True, False), (True, False, False), (True, True, False), (True, True, True)]

    def doChoice(self, (showStart, showDue, showUnplanned)):
        self.viewer.freeze()
        try:
            self.viewer.SetShowNoStartDate(showStart)
            self.viewer.SetShowNoDueDate(showDue)
            self.viewer.SetShowUnplanned(showUnplanned)
        finally:
            self.viewer.thaw()


class ToggleAutoColumnResizing(UICheckCommand, ViewerCommand, SettingsCommand):
    def __init__(self, *args, **kwargs):
        super(ToggleAutoColumnResizing, self).__init__(\
            menuText=_('&Automatic column resizing'),
            helpText=_('When checked, automatically resize columns to fill'
                       ' available space'), 
            *args, **kwargs)
        wx.CallAfter(self.updateWidget)

    def updateWidget(self):
        self.viewer.getWidget().ToggleAutoResizing(self.isSettingChecked())

    def isSettingChecked(self):
        return self.settings.getboolean(self.viewer.settingsSection(),
                                        'columnautoresizing')
    
    def doCommand(self, event):
        self.settings.set(self.viewer.settingsSection(), 'columnautoresizing',
                          str(self._isMenuItemChecked(event)))
        self.updateWidget()
