# -*- coding: utf-8 -*-

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
from taskcoachlib import meta, patterns, widgets, help # pylint: disable-msg=W0622
from taskcoachlib.i18n import _
from taskcoachlib.gui.threads import DeferredCallMixin, synchronized
from taskcoachlib.gui.dialog.iphone import IPhoneSyncTypeDialog
from taskcoachlib.gui.iphone import IPhoneSyncFrame
from taskcoachlib.powermgt import PowerStateMixin
import taskcoachlib.thirdparty.aui as aui
import viewer, toolbar, uicommand, remindercontroller, artprovider


class WindowDimensionsTracker(object):
    ''' Track the dimensions (position and size) of a window in the 
        settings. '''
    def __init__(self, window, settings, *args, **kwargs):
        super(WindowDimensionsTracker, self).__init__(*args, **kwargs)
        self._settings = settings
        self._section = 'window'
        self._window = window
        self.setDimensions()
        self._window.Bind(wx.EVT_SIZE, self.onChangeSize)
        self._window.Bind(wx.EVT_MOVE, self.onChangePosition)
        self._window.Bind(wx.EVT_MAXIMIZE, self.onMaximize)
        if self.startIconized():
            if wx.Platform in ('__WXMAC__', '__WXGTK__'):
                # Need to show the window on Mac OS X first, otherwise it   
                # won't be properly minimized. On wxGTK we need to show the
                # window first, otherwise clicking the task bar icon won't
                # show it.
                self._window.Show()
            self._window.Iconize(True)
            if wx.Platform != '__WXMAC__':
                # Seems like hiding the window after it's been
                # iconized actually closes it on Mac OS...
                wx.CallAfter(self._window.Hide)

    def startIconized(self):
        startIconized = self._settings.get(self._section, 'starticonized')
        if startIconized == 'Always':
            return True
        if startIconized == 'Never':
            return False
        return self.getSetting('iconized') 
        
    def setSetting(self, setting, value):
        self._settings.set(self._section, setting, str(value))
        
    def getSetting(self, setting):
        return eval(self._settings.get(self._section, setting))
        
    def setDimensions(self):
        width, height = self.getSetting('size')
        if wx.Platform == '__WXMAC__':
            # Under MacOS 10.5 and 10.4, when setting the size, the actual window height
            # is increased by 29 pixels. Dunno why, but it's highly annoying.
            height -= 29
        x, y = self.getSetting('position')
        self._window.SetDimensions(x, y, width, height)
        if self.getSetting('maximized'):
            self._window.Maximize()
        # Check that the window is on a valid display and move if necessary:
        if wx.Display.GetFromWindow(self._window) == wx.NOT_FOUND:
            self._window.SetDimensions(0, 0, width, height)

    def onChangeSize(self, event):
        # Ignore the EVT_SIZE when the window is maximized or iconized. 
        # Note how this depends on the EVT_MAXIMIZE being sent before the 
        # EVT_SIZE.
        maximized = self._window.IsMaximized()
        if not maximized and not self._window.IsIconized():
            self.setSetting('size', event.GetSize())
        # Jerome, 2008/07/12: On my system (KDE 3.5.7), EVT_MAXIMIZE
        # is not triggered, so set 'maximized' to True here as well as in 
        # onMaximize:
        self.setSetting('maximized', maximized)
        event.Skip()
        
    def onChangePosition(self, event):
        # Ignore the EVT_MOVE when the window is maximized. Note how this
        # depends on the EVT_MAXIMIZE being sent before the EVT_MOVE.
        if not self._window.IsMaximized():
            self.setSetting('position', self._window.GetPosition())
            self.setSetting('maximized', False)
        event.Skip()
        
    def onMaximize(self, event):
        self.setSetting('maximized', True)
        event.Skip()
                
    def savePosition(self):
        iconized = self._window.IsIconized()
        self.setSetting('iconized', iconized)
        if not iconized:
            self.setSetting('position', self._window.GetPosition())
        

class MainWindow(DeferredCallMixin, PowerStateMixin, widgets.AuiManagedFrameWithNotebookAPI):
    pageClosedEvent = aui.EVT_AUI_PANE_CLOSE
    
    def __init__(self, iocontroller, taskFile, settings,
                 splash=None, *args, **kwargs):
        super(MainWindow, self).__init__(None, -1, '', *args, **kwargs)
        self.dimensionsTracker = WindowDimensionsTracker(self, settings)
        self.iocontroller = iocontroller
        self.taskFile = taskFile
        self.settings = settings
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.splash = splash
        self.createWindowComponents()
        self.initWindowComponents()
        self.initWindow()
        self.registerForWindowComponentChanges()
        wx.CallAfter(self.closeSplash)
        wx.CallAfter(self.showTips)

        if settings.getboolean('feature', 'syncml'):
            try:
                import taskcoachlib.syncml.core # pylint: disable-msg=W0612
            except ImportError:
                if settings.getboolean('syncml', 'showwarning'):
                    dlg = widgets.SyncMLWarningDialog(self)
                    try:
                        if dlg.ShowModal() == wx.ID_OK:
                            settings.setboolean('syncml', 'showwarning', False)
                    finally:
                        dlg.Destroy()

        self.bonjourRegister = None

        if settings.getboolean('feature', 'iphone'):
            try:
                from taskcoachlib.thirdparty import pybonjour # pylint: disable-msg=W0612
                from taskcoachlib.iphone import IPhoneAcceptor, BonjourServiceRegister

                acceptor = IPhoneAcceptor(self, settings, iocontroller)
                self.bonjourRegister = BonjourServiceRegister(settings, acceptor.port)
            except:
                from taskcoachlib.gui.dialog.iphone import IPhoneBonjourDialog

                dlg = IPhoneBonjourDialog(self, wx.ID_ANY, _('Warning'))
                try:
                    dlg.ShowModal()
                finally:
                    dlg.Destroy()

    def createWindowComponents(self):
        self.createViewerContainer()
        viewer.addViewers(self.viewer, self.taskFile, self.settings)
        self.createStatusBar()
        self.createMenuBar()
        self.createTaskBarIcon()
        self.createReminderController()
        
    def createViewerContainer(self):
        self.viewer = viewer.ViewerContainer(self, self.settings, 'mainviewer') 
        
    def createStatusBar(self):
        import status
        self.SetStatusBar(status.StatusBar(self, self.viewer))
        
    def createMenuBar(self):
        import menu
        self.SetMenuBar(menu.MainMenu(self, self.settings, self.iocontroller, 
                                      self.viewer, self.taskFile))
    
    def createReminderController(self):
        self.reminderController = \
            remindercontroller.ReminderController(self, self.taskFile.tasks(), 
                self.settings)
        
    def AddPage(self, page, caption, *args):
        name = page.settingsSection()
        super(MainWindow, self).AddPage(page, caption, name)

    def initWindow(self):
        wx.GetApp().SetTopWindow(self)
        self.setTitle(self.taskFile.filename())
        self.SetIcons(artprovider.iconBundle('taskcoach'))
        self.displayMessage(_('Welcome to %(name)s version %(version)s')% \
            {'name': meta.name, 'version': meta.version}, pane=1)

    def initWindowComponents(self):
        self.onShowToolBar()
        # We use CallAfter because otherwise the statusbar will appear at the 
        # top of the window when it is initially hidden and later shown.
        wx.CallAfter(self.onShowStatusBar)
        self.restorePerspective()
            
    def restorePerspective(self):
        perspective = self.settings.get('view', 'perspective')
        viewerTypes = viewer.viewerTypes()
        for viewerType in viewerTypes:
            if self.perspectiveAndSettingsHaveDifferentViewerCount(viewerType):
                # Different viewer counts may happen when the name of a viewer 
                # is changed between versions
                perspective = ''
                break

        self.manager.LoadPerspective(perspective)
        for pane in self.manager.GetAllPanes():
            # Prevent zombie panes by making sure all panes are visible
            if not pane.IsShown():
                pane.Show()
            # Ignore the titles that are saved in the perspective, they may be
            # incorrect when the user changes translation:
            if hasattr(pane.window, 'title'):
                pane.Caption(pane.window.title())
        self.manager.Update()
        
    def perspectiveAndSettingsHaveDifferentViewerCount(self, viewerType):
        perspective = self.settings.get('view', 'perspective')
        perspectiveViewerCount = perspective.count('name=%s'%viewerType)
        settingsViewerCount = self.settings.getint('view', '%scount'%viewerType)
        return perspectiveViewerCount != settingsViewerCount
    
    def registerForWindowComponentChanges(self):
        patterns.Publisher().registerObserver(self.onFilenameChanged, 
            eventType='taskfile.filenameChanged', eventSource=self.taskFile)
        patterns.Publisher().registerObserver(self.onShowStatusBar, 
            eventType='view.statusbar')
        patterns.Publisher().registerObserver(self.onShowToolBar, 
            eventType='view.toolbar')
        self.Bind(self.pageClosedEvent, self.onCloseToolBar)

    def showTips(self):
        if self.settings.getboolean('window', 'tips'):
            help.showTips(self, self.settings)
            
    def closeSplash(self):
        if self.splash:
            self.splash.Destroy()
                         
    def onShowStatusBar(self, event=None): # pylint: disable-msg=W0613
        self.showStatusBar(self.settings.getboolean('view', 'statusbar'))

    def onShowToolBar(self, event=None): # pylint: disable-msg=W0613
        self.showToolBar(eval(self.settings.get('view', 'toolbar')))

    def createTaskBarIcon(self):
        if self.canCreateTaskBarIcon():
            import taskbaricon, menu
            self.taskBarIcon = taskbaricon.TaskBarIcon(self, 
                self.taskFile.tasks(), self.settings)
            self.taskBarIcon.setPopupMenu(menu.TaskBarMenu(self.taskBarIcon,
                self.settings, self.taskFile, self.viewer))
        self.Bind(wx.EVT_ICONIZE, self.onIconify)

    def canCreateTaskBarIcon(self):
        try:
            import taskbaricon # pylint: disable-msg=W0612
            return True
        except:
            return False # pylint: disable-msg=W0702
        
    def onFilenameChanged(self, event):
        self.setTitle(event.value())

    def setTitle(self, filename):
        title = meta.name
        if filename:
            title += ' - %s'%filename
        self.SetTitle(title)
        
    def displayMessage(self, message, pane=0):
        self.GetStatusBar().SetStatusText(message, pane)

    def quit(self, force=False):
        if not self.iocontroller.close(force=force):
            return
        # Remember what the user was working on: 
        self.settings.set('file', 'lastfile', self.taskFile.lastFilename())
        self.saveViewerCounts()
        self.savePerspective()
        self.dimensionsTracker.savePosition()
        self.settings.save()
        if hasattr(self, 'taskBarIcon'):
            self.taskBarIcon.RemoveIcon()
        if self.bonjourRegister is not None:
            self.bonjourRegister.stop()
        wx.GetApp().ProcessIdle()
        wx.GetApp().ExitMainLoop()

        # For PowerStateMixin

        self.OnQuit()

    def saveViewerCounts(self):
        ''' Save the number of viewers for each viewer type. '''
        counts = {}
        for viewer in self.viewer:
            setting = viewer.__class__.__name__.lower() + 'count'
            counts[setting] = counts.get(setting, 0) + 1
        for key, value in counts.items():
            self.settings.set('view', key, str(value))
            
    def savePerspective(self):
        perspective = self.manager.SavePerspective()
        self.settings.set('view', 'perspective', perspective)
        
    def onClose(self, event):
        if event.CanVeto() and self.settings.getboolean('window', 
                                                        'hidewhenclosed'):
            event.Veto()
            self.Iconize()
        else:
            self.quit()

    def restore(self, event): # pylint: disable-msg=W0613
        if self.settings.getboolean('window', 'maximized'):
            self.Maximize()
        self.Iconize(False)
        self.Show()
        self.Raise()
        self.Refresh()

    def onIconify(self, event):
        if event.Iconized() and self.settings.getboolean('window', 
                                                         'hidewheniconized'):
            self.Hide()
        else:
            event.Skip()
            
    def showStatusBar(self, show=True):
        # FIXME: First hiding the statusbar, then hiding the toolbar, then
        # showing the statusbar puts it in the wrong place (only on Linux?)
        self.GetStatusBar().Show(show)
        self.SendSizeEvent()
        
    def getToolBarUICommands(self):
        ''' UI commands to put on the toolbar of this window. ''' 
        uiCommands = [
                uicommand.FileOpen(iocontroller=self.iocontroller), 
                uicommand.FileSave(iocontroller=self.iocontroller), 
                uicommand.Print(viewer=self.viewer, settings=self.settings), 
                None, 
                uicommand.EditUndo(), 
                uicommand.EditRedo()]
        if self.settings.getboolean('feature', 'effort'):
            uiCommands.extend([ 
                None, 
                uicommand.EffortStartButton(taskList=self.taskFile.tasks()), 
                uicommand.EffortStop(taskList=self.taskFile.tasks())])
        return uiCommands
        
    def showToolBar(self, size):
        # Current version of wxPython (2.7.8.1) has a bug 
        # (https://sourceforge.net/tracker/?func=detail&atid=109863&aid=1742682&group_id=9863)
        # that makes adding controls to a toolbar not working. Also, when the 
        # toolbar is visible it's nearly impossible to enter text into text
        # controls. Immediately after you click on a text control the focus
        # is removed. We work around it by not having AUI manage the toolbar
        # on Mac OS X:
        if '__WXMAC__' in wx.PlatformInfo:
            if self.GetToolBar():
                self.GetToolBar().Destroy()
            if size is not None:
                self.SetToolBar(toolbar.ToolBar(self, size=size))
            self.SendSizeEvent()
        else:
            currentToolbar = self.manager.GetPane('toolbar')
            if currentToolbar.IsOk():
                self.manager.DetachPane(currentToolbar.window)
                currentToolbar.window.Destroy()
            if size:
                bar = toolbar.ToolBar(self, size=size)
                self.manager.AddPane(bar, aui.AuiPaneInfo().Name('toolbar').
                                     Caption('Toolbar').ToolbarPane().Top().DestroyOnClose().
                                     LeftDockable(False).RightDockable(False))
            self.manager.Update()

    def onCloseToolBar(self, event):
        if event.GetPane().IsToolbar():
            self.settings.set('view', 'toolbar', 'None')
        event.Skip()

    # Power management

    def OnPowerState(self, state):
        patterns.observer.Event('powermgt.%s' % {self.POWERON: 'on', self.POWEROFF: 'off'}[state],
                                self).send()

    # iPhone-related methods. These are called from the asyncore thread so they're deferred.

    @synchronized
    def createIPhoneProgressFrame(self):
        return IPhoneSyncFrame(self.settings, _('iPhone/iPod'),
                               icon=wx.ArtProvider.GetBitmap('taskcoach', wx.ART_FRAME_ICON, (16, 16)),
                               parent=self)

    @synchronized
    def getIPhoneSyncType(self, guid):
        if guid == self.taskFile.guid():
            return 0 # two-ways

        dlg = IPhoneSyncTypeDialog(self, wx.ID_ANY, _('Synchronization type'))
        try:
            dlg.ShowModal()
            return dlg.value
        finally:
            dlg.Destroy()

    @synchronized
    def notifyIPhoneProtocolFailed(self):
        # This should actually never happen.
        wx.MessageBox(_('''An iPhone or iPod Touch device tried to synchronize with this\n'''
                      '''task file, but the protocol negotiation failed. Please file a\n'''
                      '''bug report.'''),
                      _('Error'), wx.OK)

    # The notification system is not thread-save; adding or modifying tasks
    # or categories from the asyncore thread crashes the app.

    @synchronized
    def clearTasks(self):
        self.taskFile.clear(False)

    @synchronized
    def restoreTasks(self, categories, tasks):
        self.taskFile.clear(False)
        self.taskFile.categories().extend(categories)
        self.taskFile.tasks().extend(tasks)

    @synchronized
    def addIPhoneCategory(self, category):
        self.taskFile.categories().append(category)

    @synchronized
    def removeIPhoneCategory(self, category):
        self.taskFile.categories().remove(category)

    @synchronized
    def modifyIPhoneCategory(self, category, name):
        category.setSubject(name)

    @synchronized
    def addIPhoneTask(self, task, categories):
        self.taskFile.tasks().append(task)
        for category in categories:
            task.addCategory(category)
            category.addCategorizable(task)

    @synchronized
    def removeIPhoneTask(self, task):
        self.taskFile.tasks().remove(task)

    @synchronized
    def addIPhoneEffort(self, task, effort):
        if task is not None:
            task.addEffort(effort)

    @synchronized
    def modifyIPhoneEffort(self, effort, subject, started, ended):
        effort.setSubject(subject)
        effort.setStart(started)
        effort.setStop(ended)

    @synchronized
    def modifyIPhoneTask(self, task, subject, description, startDateTime, 
                         dueDateTime, completionDateTime, reminderDateTime,
                         recurrence, priority, categories):
        task.setSubject(subject)
        task.setDescription(description)
        task.setStartDateTime(startDateTime)
        task.setDueDateTime(dueDateTime)
        task.setCompletionDateTime(completionDateTime)
        task.setReminder(reminderDateTime)
        task.setRecurrence(recurrence)
        task.setPriority(priority)

        if categories is not None: # Protocol v2
            for category in task.categories():
                task.removeCategory(category)
                category.removeCategorizable(task)

            for category in categories:
                task.addCategory(category)
                category.addCategorizable(task)
