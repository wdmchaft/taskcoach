# -*- coding: UTF-8 -*-

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
from taskcoachlib import meta, widgets, notify
from taskcoachlib.domain import date
from taskcoachlib.i18n import _


class SettingsPageBase(widgets.BookPage):
    def __init__(self, *args, **kwargs):
        super(SettingsPageBase, self).__init__(*args, **kwargs)
        self._booleanSettings = []
        self._choiceSettings = []
        self._multipleChoiceSettings = []
        self._integerSettings = []
        self._colorSettings = []
        self._pathSettings = []
        self._textSettings = []
        
    def addBooleanSetting(self, section, setting, text, helpText=''):
        checkBox = wx.CheckBox(self, -1)
        checkBox.SetValue(self.getboolean(section, setting))
        self.addEntry(text, checkBox, helpText)
        self._booleanSettings.append((section, setting, checkBox))

    def addChoiceSetting(self, section, setting, text, choices, helpText=''):
        choice = wx.Choice(self, -1)
        for choiceValue, choiceText in choices:
            choice.Append(choiceText, choiceValue)
            if choiceValue == self.get(section, setting):
                choice.SetSelection(choice.GetCount()-1)
        if choice.GetSelection() == wx.NOT_FOUND: # force a selection if necessary
            choice.SetSelection(0)
        self.addEntry(text, choice, helpText)
        self._choiceSettings.append((section, setting, choice))
        
    def addMultipleChoiceSettings(self, section, setting, text, choices, helpText=''):
        ''' choices is a list of (number, text) tuples. '''
        multipleChoice = wx.CheckListBox(self, choices=[choice[1] for choice in choices])
        checkedNumbers = eval(self.get(section, setting))
        for index, choice in enumerate(choices):
            multipleChoice.Check(index, choice[0] in checkedNumbers)
        self.addEntry(text, multipleChoice, helpText, growable=True)
        self._multipleChoiceSettings.append((section, setting, multipleChoice, 
                                             [choice[0] for choice in choices]))
        
    def addIntegerSetting(self, section, setting, text, minimum=0, maximum=100,
            helpText=''):
        spin = widgets.SpinCtrl(self, min=minimum, max=maximum, size=(40, -1),
            initial=self.getint(section, setting))
        self.addEntry(text, spin, helpText)
        self._integerSettings.append((section, setting, spin))

    def addColorSetting(self, section, setting, text):
        colorButton = widgets.ColorSelect(self, -1, text,
            eval(self.get(section, setting)))
        self.addEntry(None, colorButton)
        self._colorSettings.append((section, setting, colorButton))

    def addPathSetting(self, section, setting, text, helpText=''):
        pathChooser = widgets.DirectoryChooser(self, wx.ID_ANY)
        pathChooser.SetPath(self.get(section, setting))
        self.addEntry(text, pathChooser, helpText)
        self._pathSettings.append((section, setting, pathChooser))

    def addTextSetting(self, section, setting, text, helpText=''):
        textChooser = wx.TextCtrl(self, wx.ID_ANY, self.get(section, setting))
        self.addEntry(text, textChooser, helpText)
        self._textSettings.append((section, setting, textChooser))

    def addText(self, label, text):
        self.addEntry(label, text)

    def ok(self):
        for section, setting, checkBox in self._booleanSettings:
            self.set(section, setting, str(checkBox.IsChecked()))
        for section, setting, choice in self._choiceSettings:
            self.set(section, setting, 
                              choice.GetClientData(choice.GetSelection()))
        for section, setting, multipleChoice, choices in self._multipleChoiceSettings:
            self.set(section, setting,
                     str([choices[index] for index in range(len(choices)) if multipleChoice.IsChecked(index)]))
        for section, setting, spin in self._integerSettings:
            self.set(section, setting, str(spin.GetValue()))
        for section, setting, colorButton in self._colorSettings:
            self.set(section, setting, str(colorButton.GetColour()))
        for section, setting, btn in self._pathSettings:
            self.set(section, setting, btn.GetPath())
        for section, setting, txt in self._textSettings:
            self.set(section, setting, txt.GetValue())

    def get(self, section, name):
        raise NotImplementedError

    def getint(self, section, name):
        return int(self.get(section, name))

    def getboolean(self, section, name):
        return self.get(section, name) == 'True'

    def set(self, section, name, value):
        raise NotImplementedError


class SettingsPage(SettingsPageBase):
    def __init__(self, settings=None, *args, **kwargs):
        self.settings = settings
        super(SettingsPage, self).__init__(*args, **kwargs)
        
    def addEntry(self, text, control, helpText='', **kwargs): # pylint: disable-msg=W0221
        if helpText == 'restart':
            helpText = _('This setting will take effect\nafter you restart %s')%meta.name
        super(SettingsPage, self).addEntry(text, control, helpText, **kwargs)

    def get(self, section, name):
        return self.settings.get(section, name)

    def getint(self, section, name):
        return self.settings.getint(section, name)

    def getboolean(self, section, name):
        return self.settings.getboolean(section, name)

    def set(self, section, name, value):
        self.settings.set(section, name, value)


class SavePage(SettingsPage):
    pageName = 'save'
    pageTitle = _('Files')
    pageIcon = 'save'
    
    def __init__(self, *args, **kwargs):
        super(SavePage, self).__init__(columns=3, *args, **kwargs)
        self.addBooleanSetting('file', 'autosave', 
            _('Auto save after every change'))
        self.addBooleanSetting('file', 'backup', 
            _('Create a backup copy before\noverwriting a %s file')%meta.name)
        self.addBooleanSetting('file', 'saveinifileinprogramdir',
            _('Save settings (%s.ini) in the same\ndirectory as the program') \
              %meta.filename, 
            _('(For running %s\nfrom a removable medium)')%meta.name)
        self.addPathSetting('file', 'attachmentbase', _('Attachment base directory'),
                            _('When adding an attachment, try to make\nits path relative to this one.'))
        self.fit()
            
               
class WindowBehaviorPage(SettingsPage):
    pageName = 'window'
    pageTitle = _('Window behavior')
    pageIcon = 'windows'
    
    def __init__(self, *args, **kwargs):
        super(WindowBehaviorPage, self).__init__(columns=3, *args, **kwargs)
        self.addBooleanSetting('window', 'splash', 
            _('Show splash screen on startup'))
        self.addBooleanSetting('window', 'tips', 
            _('Show tips window on startup'))
        self.addChoiceSetting('window', 'starticonized',
            _('Start with the main window iconized'),
            [('Never', _('Never')), ('Always', _('Always')), 
             ('WhenClosedIconized', 
              _('If it was iconized last session'))])
        self.addBooleanSetting('version', 'notify',
            _('Check for new version of %(name)s on startup')%meta.data.metaDict)
        self.addBooleanSetting('window', 'hidewheniconized', 
            _('Hide main window when iconized'))
        self.addBooleanSetting('window', 'hidewhenclosed', 
            _('Minimize main window when closed'))
        self.addBooleanSetting('window', 'blinktaskbariconwhentrackingeffort',
            _('Make clock in the task bar tick when tracking effort'))
        self.addBooleanSetting('view', 'descriptionpopups',
            _('Show a popup with the description of an item\nwhen hovering over it'))
        self.fit()


class LanguagePage(SettingsPage):
    pageName = 'language'
    pageTitle = _('Language')
    pageIcon = 'person_talking_icon'
    
    def __init__(self, *args, **kwargs):
        super(LanguagePage, self).__init__(columns=3, *args, **kwargs) 
        choices = \
            [('', _('Let the system determine the language')),
             ('ar', u'الْعَرَبيّة (Arabic)'),
             ('eu_ES', 'Euskal Herria (Basque)'),
             ('bs_BA', u'босански (Bosnian)'),
             ('pt_BR', u'Português brasileiro (Brazilian Portuguese)'),
             ('br_FR', 'Brezhoneg (Breton)'),
             ('bg_BG', u'български (Bulgarian)'),
             ('ca_ES', u'Català (Catalan)'),
             ('zh_CN', u'简体中文 (Simplified Chinese)'),
             ('zh_TW', u'正體字 (Traditional Chinese)'),
             ('cs_CS', u'Čeština (Czech)'),
             ('da_DA', 'Dansk (Danish)'),
             ('nl_NL', 'Nederlands (Dutch)'),
             ('en_AU', 'English (Australia)'),
             ('en_CA', 'English (Canada)'), 
             ('en_GB', 'English (UK)'),
             ('en_US', 'English (US)'), 
             ('eo', 'Esperanto'),
             ('et_EE', 'Eesti keel (Estonian)'),
             ('fi_FI', 'Suomi (Finnish)'),
             ('fr_FR', u'Français (French)'),
             ('gl_ES', 'Galego (Galician)'),
             ('de_DE', 'Deutsch (German)'),
             ('nds_DE', 'Niederdeutsche Sprache (Low German)'),
             ('el_GR', u'ελληνικά (Greek)'),
             ('he_IL', u'עברית (Hebrew)'),
             ('hi_IN', u'हिन्दी, हिंदी (Hindi)'),
             ('hu_HU', 'Magyar (Hungarian)'),
             ('id_ID', 'Bahasa Indonesia (Indonesian)'),
             ('it_IT', 'Italiano (Italian)'),
             ('ja_JP', u'日本語 (Japanese)'),
             ('ko_KO', u'한국어/조선말 (Korean)'),
             ('lv_LV', u'Latviešu (Latvian)'),
             ('lt_LT', u'Lietuvių kalba (Lithuanian)'),
             ('mr_IN', u'मराठी Marāṭhī (Marathi)'),
             ('mn_CN', u'Монгол бичиг (Mongolian)'),
             ('nb_NO', u'Bokmål (Norwegian Bokmal)'),
             ('nn_NO', u'Nynorsk (Norwegian Nynorsk)'),
             ('fa_IR', u'فارسی (Persian)'),
             ('pl_PL', u'Język polski (Polish)'),
             ('pt_PT', u'Português (Portuguese)'),
             ('ro_RO', u'Română (Romanian)'),
             ('ru_RU', u'Русский (Russian)'),
             ('sk_SK', u'Slovenčina (Slovak)'),
             ('sl_SI', u'Slovenski jezik (Slovene)'),
             ('es_ES', u'Español (Spanish)'),
             ('sv_SE', 'Svenska (Swedish)'),
             ('te_IN', u'తెలుగు (Telugu)'),
             ('th_TH', u'ภาษาไทย (Thai)'),
             ('tr_TR', u'Türkçe (Turkish)'),
             ('uk_UA', u'украї́нська мо́ва (Ukranian)'),
             ('vi_VI', u'tiếng Việt (Vietnamese)')]
        self.addChoiceSetting('view', 'language_set_by_user', _('Language'), 
                              choices, helpText='restart')
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        text = wx.StaticText(panel, 
            label=_('''If your language is not available, or the translation needs 
improving, please consider helping. See:'''))
        sizer.Add(text)
        url = meta.url + 'i18n.html'
        urlCtrl = wx.HyperlinkCtrl(panel, -1, label=url, url=url)
        sizer.Add(urlCtrl)
        panel.SetSizerAndFit(sizer)
        self.addText(_('Language not found?'), panel)
        self.fit()

    def ok(self):
        super(LanguagePage, self).ok()
        self.set('view', 'language', self.get('view', 'language_set_by_user'))
        

class ColorsPage(SettingsPage):
    pageName = 'colors'
    pageTitle = _('Colors')
    pageIcon = 'palette_icon'
    
    def __init__(self, *args, **kwargs):
        super(ColorsPage, self).__init__(columns=1, growableColumn=-1, *args, **kwargs)
        for setting, label in \
            [('activetasks', _('Click this button to change the color of active tasks')), 
             ('inactivetasks', _('Click this button to change the color of inactive tasks')),
             ('completedtasks', _('Click this button to change the color of completed tasks')),
             ('overduetasks', _('Click this button to change the color of over due tasks')),
             ('duesoontasks', _('Click this button to change the color of tasks due soon'))]:
            self.addColorSetting('color', setting, label)
        self.fit()


class FeaturesPage(SettingsPage):
    pageName = 'features'
    pageTitle = _('Features')
    pageIcon = 'cogwheel_icon'
    
    def __init__(self, *args, **kwargs):
        super(FeaturesPage, self).__init__(columns=3, *args, **kwargs)
        self.addBooleanSetting('feature', 'effort', 
            _('Allow for tracking effort'), helpText='restart')
        self.addBooleanSetting('feature', 'notes', _('Allow for taking notes'),
            helpText='restart')

        names = [] # There's at least one, the universal one
        for name in notify.AbstractNotifier.names():
            names.append((name, name))

        self.addChoiceSetting('feature', 'notifier', _('Notification system'), names,
                              helpText=_('Notification system to use for reminders (Growl, Snarl, etc)'))

        try:
            import taskcoachlib.syncml.core
        except ImportError:
            pass
        else:
            self.addBooleanSetting('feature', 'syncml', _('Enable SyncML'),
                helpText='restart')
        self.addBooleanSetting('feature', 'iphone', _('Enable iPhone synchronization'),
            helpText='restart')
        self.addIntegerSetting('view', 'efforthourstart',
            _('Hour of start of work day'), minimum=0, maximum=23)
        self.addIntegerSetting('view', 'efforthourend',
            _('Hour of end of work day'), minimum=1, maximum=24)
        self.addBooleanSetting('calendarviewer', 'gradient',
            _('Use gradients in calendar views.\nThis may slow down Task Coach.'),
            helpText='restart')
        self.addChoiceSetting('view', 'effortminuteinterval',
            _('Minutes between task start/end times'),
            [('5', '5'), ('10', '10'), ('15', '15'), ('20', '20'), ('30', '30')])
        self.fit()
        

class TaskBehaviorPage(SettingsPage):
    pageName = 'task'
    pageTitle = _('Task behavior')
    pageIcon = 'cogwheel_icon'
    
    def __init__(self, *args, **kwargs):
        super(TaskBehaviorPage, self).__init__(columns=3, *args, **kwargs)
        self.addBooleanSetting('behavior', 'markparentcompletedwhenallchildrencompleted',
            _('Mark parent task completed when all children are completed'))
        self.addIntegerSetting('behavior', 'duesoonhours', 
            _("Number of hours that tasks are considered to be 'due soon'"), 
            minimum=0, maximum=90)
        self.addMultipleChoiceSettings('view', 'snoozetimes', 
            _('Snooze times to offer in task reminder dialog'), 
            date.snoozeChoices[1:]) # Don't offer "Don't snooze" as a choice
        self.fit()


class IPhonePage(SettingsPage):
    pageName = 'iphone'
    pageTitle = _('iPhone')
    pageIcon = 'computer_handheld_icon'
    
    def __init__(self, *args, **kwargs):
        super(IPhonePage, self).__init__(columns=3, *args, **kwargs)
        self.addTextSetting('iphone', 'password',
            _('Password for synchronization with iPhone'))
        self.addTextSetting('iphone', 'service',
            _('Bonjour service name'), helpText='restart')
        self.addBooleanSetting('iphone', 'synccompleted',
            _('Upload completed tasks to device'), helpText=_('Upload completed tasks to device'))
        self.addBooleanSetting('iphone', 'showlog',
            _('Show sync log'), helpText=_('Show the synchronization log'))
        self.fit()

        
class EditorPage(SettingsPage):
    pageName = 'editor'
    pageTitle = _('Editor')
    pageIcon = 'edit'
    
    def __init__(self, *args, **kwargs):
        super(EditorPage, self).__init__(columns=2, *args, **kwargs)
        self.addBooleanSetting('editor', 'maccheckspelling',
            _('Check spelling in editors'))
        self.fit()
        
    def ok(self):
        super(EditorPage, self).ok()
        widgets.MultiLineTextCtrl.CheckSpelling = \
            self.settings.getboolean('editor', 'maccheckspelling')


class Preferences(widgets.NotebookDialog):
    allPageNames = ['window', 'task', 'save', 'language', 'colors', 'features',
                    'iphone', 'editor']
    pages = dict(window=WindowBehaviorPage, task=TaskBehaviorPage, 
                 save=SavePage, language=LanguagePage, colors=ColorsPage, 
                 features=FeaturesPage, iphone=IPhonePage, editor=EditorPage)
    
    def __init__(self, settings=None, *args, **kwargs):
        self.settings = settings
        super(Preferences, self).__init__(bitmap='wrench_icon', *args, **kwargs)
        self.TopLevelParent.Bind(wx.EVT_CLOSE, self.onClose)        
        if '__WXMAC__' in wx.PlatformInfo:
            self.CentreOnParent()

    def addPages(self):
        self.SetMinSize((300, 430))
        for pageName in self.allPageNamesInUserOrder():
            if self.shouldCreatePage(pageName):
                page = self.createPage(pageName)
                self._interior.AddPage(page, page.pageTitle, page.pageIcon)

    def allPageNamesInUserOrder(self):
        ''' Return all pages names in the order stored in the settings. The
            settings may not contain all pages (e.g. because a feature was
            turned off by the user) so we add the missing pages if necessary. '''
        pageNamesInUserOrder = self.settings.getlist('editor', 'preferencespages')
        remainingPageNames = self.allPageNames[:]
        for pageName in pageNamesInUserOrder:
            remainingPageNames.remove(pageName)
        return pageNamesInUserOrder + remainingPageNames
                    
    def shouldCreatePage(self, pageName):
        if pageName == 'iphone':
            return self.settings.getboolean('feature', 'iphone')
        elif pageName == 'editor':
            return '__WXMAC__' in wx.PlatformInfo
        else:
            return True

    def createPage(self, pageName):
        return self.pages[pageName](parent=self._interior, settings=self.settings)

    def onClose(self, event):
        event.Skip()
        pageNames = [page.pageName for page in self]
        self.settings.setlist('editor', 'preferencespages', pageNames)
