# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jérôme Laheurte <fraca7@free.fr>
Copyright (C) 2008 Rob McMullen <rob.mcmullen@gmail.com>
Copyright (C) 2008 Carl Zmola <zmola@acm.org>

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

import wx, os.path
from taskcoachlib import widgets, patterns
from taskcoachlib.gui import render, viewer, artprovider
from taskcoachlib.widgets import draganddrop
from taskcoachlib.i18n import _
from taskcoachlib.domain import task, category, date, note, attachment
from taskcoachlib.gui.dialog import entry


def createDateTimeCtrl(parent, value, settings, callback=None, noneAllowed=True, **kwargs):
    ''' Factory function for creating a DateTimeCtrl widget using the user
        settings for earliest and latest times and interval. '''
    starthour = settings.getint('view', 'efforthourstart')
    endhour = settings.getint('view', 'efforthourend')
    interval = settings.getint('view', 'effortminuteinterval')
    return widgets.DateTimeCtrl(parent, value, callback, noneAllowed=noneAllowed,
        starthour=starthour, endhour=endhour, interval=interval, **kwargs)


class Page(object):
    def entries(self):
        ''' A mapping of names of columns to entries on this editor page. '''
        return dict()
    
    def setFocusOnEntry(self, columnName):
        try:
            theEntry = self.entries()[columnName]
        except KeyError:
            return
        try:
            theEntry.SetSelection(-1, -1) # Select all text
        except (AttributeError, TypeError):
            pass # Not a TextCtrl
        theEntry.SetFocus()

    def ok(self):
        pass
       
        
class PageWithHeaders(Page, widgets.PanelWithBoxSizer):
    headerForNonRecursiveAttributes = 'Subclass responsibility'
    headerForRecursiveAttributes = 'Subclass responsibility'
    
    def __init__(self, parent, item, *args, **kwargs):
        super(PageWithHeaders, self).__init__(parent, *args, **kwargs) 
        self.item = item

    def addHeaders(self, box):
        headers = ['', self.headerForNonRecursiveAttributes]
        if self.item.children():
            headers.append(self.headerForRecursiveAttributes)
        else:
            headers.append('')
        for header in headers:
            box.add(header)


class PageWithViewerMixin(object):
    def __init__(self, *args, **kwargs):
        super(PageWithViewerMixin, self).__init__(*args, **kwargs)
        self.TopLevelParent.Bind(wx.EVT_CLOSE, self.onClose)
        
    def onClose(self, event):
        # Don't notify the viewer about any changes anymore, it's about
        # to be deleted.
        self.viewer.detach()
        event.Skip()
        
        
class TaskHeadersMixin(object):
    headerForNonRecursiveAttributes = _('For this task')
    headerForRecursiveAttributes = _('For this task including all subtasks')
    

class NoteHeadersMixin(object):
    headerForNonRecursiveAttributes = _('For this note')
    headerForRecursiveAttributes = _('For this note including all subnotes')


class SubjectPage(Page, widgets.BookPage):
    def __init__(self, item, *args, **kwargs):
        self.item = item
        super(SubjectPage, self).__init__(columns=2, *args, **kwargs)
        self.addEntries()
        self.fit()
        
    def addEntries(self):
        self.addSubjectEntry()
        self.addDescriptionEntry()
        
    def addSubjectEntry(self):
        # pylint: disable-msg=W0201
        self._subjectEntry = widgets.SingleLineTextCtrl(self, self.item.subject())
        self.addEntry(_('Subject'), self._subjectEntry, 
                      flags=[None, wx.ALL|wx.EXPAND])

    def addDescriptionEntry(self):
        # pylint: disable-msg=W0201
        self._descriptionEntry = widgets.MultiLineTextCtrl(self, 
            self.item.description())
        self._descriptionEntry.SetSizeHints(300, 150)
        self.addEntry(_('Description'), self._descriptionEntry,
            flags=[None, wx.ALL|wx.EXPAND], growable=True)

    def setSubject(self, subject):
        self._subjectEntry.SetValue(subject)

    def setDescription(self, description):
        self._descriptionEntry.SetValue(description)

    def ok(self):
        self.item.setSubject(self._subjectEntry.GetValue())
        self.item.setDescription(self._descriptionEntry.GetValue())
        super(SubjectPage, self).ok()
                        
    def entries(self):
        return dict(subject=self._subjectEntry, 
                    description=self._descriptionEntry)

    
class TaskSubjectPage(SubjectPage):
    def __init__(self, parent, theTask, *args, **kwargs):
        super(TaskSubjectPage, self).__init__(theTask, parent, *args, **kwargs)
        
    def addEntries(self):
        super(TaskSubjectPage, self).addEntries()
        self.addPriorityEntry()
         
    def addPriorityEntry(self):
        priority = self.item.priority()
        # pylint: disable-msg=W0201
        self._prioritySpinner = widgets.SpinCtrl(self, value=str(priority),
            initial=priority, size=(100, -1))
        self.addEntry(_('Priority'), self._prioritySpinner, 
                      flags=[None, wx.ALL])
    
    def ok(self):
        self.item.setPriority(self._prioritySpinner.GetValue())
        super(TaskSubjectPage, self).ok()
 
    def entries(self):
        entries = super(TaskSubjectPage, self).entries()
        entries['priority'] = entries['totalPriority'] = self._prioritySpinner
        return entries
            

class CategorySubjectPage(SubjectPage):
    def __init__(self, parent, theCategory, *args, **kwargs):
        super(CategorySubjectPage, self).__init__(theCategory, parent, 
                                                  *args, **kwargs)

    def addEntries(self):
        super(CategorySubjectPage, self).addEntries()
        self.addExclusiveSubcategoriesEntry()
       
    def addExclusiveSubcategoriesEntry(self):
        exclusive = self.item.hasExclusiveSubcategories()
        self._exclusiveSubcategoriesCheckBox = \
            wx.CheckBox(self, label=_('Mutually exclusive'))
        self._exclusiveSubcategoriesCheckBox.SetValue(exclusive)
        self.addEntry(_('Subcategories'), self._exclusiveSubcategoriesCheckBox,
                      flags=[None, wx.ALL])

    def ok(self):
        self.item.makeSubcategoriesExclusive(self._exclusiveSubcategoriesCheckBox.GetValue())
        super(CategorySubjectPage, self).ok()
        

class NoteSubjectPage(SubjectPage):
    def __init__(self, parent, theNote, *args, **kwargs):
        super(NoteSubjectPage, self).__init__(theNote, parent, *args, **kwargs)
            

class AttachmentSubjectPage(SubjectPage):
    def __init__(self, parent, theAttachment, basePath, *args, **kwargs):
        super(AttachmentSubjectPage, self).__init__(theAttachment, parent, 
                                                    *args, **kwargs)
        self.basePath = basePath
        
    def addEntries(self):
        # Override addEntries to insert a location entry between the subject
        # and description entries 
        self.addSubjectEntry()
        self.addLocationEntry()
        self.addDescriptionEntry()

    def addLocationEntry(self):
        panel = wx.Panel(self, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        # pylint: disable-msg=W0201
        self._locationEntry = widgets.SingleLineTextCtrl(panel,
                                                         self.item.location())
        sizer.Add(self._locationEntry, 1, wx.ALL, 3)
        if self.item.type_ == 'file':
            button = wx.Button(panel, wx.ID_ANY, _('Browse'))
            sizer.Add(button, 0, wx.ALL, 3)
            wx.EVT_BUTTON(button, wx.ID_ANY, self.onSelectLocation)
        panel.SetSizer(sizer)
        self.addEntry(_('Location'), panel, flags=[None, wx.ALL|wx.EXPAND])

    def ok(self):
        self.item.setLocation(self._locationEntry.GetValue())
        super(AttachmentSubjectPage, self).ok()

    def onSelectLocation(self, event): # pylint: disable-msg=W0613
        if self.item.type_ == 'file':
            basePath = os.path.split(self.item.normalizedLocation())[0]
        else:
            basePath = os.getcwd()

        filename = widgets.AttachmentSelector(default_path=basePath)

        if filename:
            if self.basePath:
                filename = attachment.getRelativePath(filename, self.basePath)
            self._subjectEntry.SetValue(os.path.split(filename)[-1])
            self._locationEntry.SetValue(filename)


class AppearancePage(Page, widgets.BookPage):
    def __init__(self, item, *args, **kwargs):
        self.item = item
        super(AppearancePage, self).__init__(columns=5, *args, **kwargs)
        self.addEntries()
        self.fit()
        
    def addEntries(self):
        self.addColorEntry()
        self.addFontEntry()
        self.addIconEntry()
        
    def addColorEntry(self):
        # pylint: disable-msg=W0201,W0142
        self._fgColorCheckBox = wx.CheckBox(self, label=_('Use foreground color:'))
        self._bgColorCheckBox = wx.CheckBox(self, label=_('Use background color:'))
        currentFgColor = self.item.foregroundColor(recursive=False)
        currentBgColor = self.item.backgroundColor(recursive=False)
        self._fgColorCheckBox.SetValue(currentFgColor is not None)
        self._fgColorCheckBox.Bind(wx.EVT_CHECKBOX, self.onFgColourCheckBoxChecked)
        self._bgColorCheckBox.SetValue(currentBgColor is not None)
        # wx.ColourPickerCtrl on Mac OS X expects a wx.Color and fails on tuples
        # so convert the tuples to a wx.Color:
        currentFgColor = wx.Color(*currentFgColor) if currentFgColor else wx.BLACK
        currentBgColor = wx.Color(*currentBgColor) if currentBgColor else wx.WHITE
        self._fgColorButton = wx.ColourPickerCtrl(self, col=currentFgColor)
        self._bgColorButton = wx.ColourPickerCtrl(self, col=currentBgColor)
        self._fgColorButton.Bind(wx.EVT_COLOURPICKER_CHANGED, self.onFgColourPicked)
        self._bgColorButton.Bind(wx.EVT_COLOURPICKER_CHANGED, self.onBgColourPicked)
        self.addEntry(_('Color'), self._fgColorCheckBox, self._fgColorButton, 
                      self._bgColorCheckBox, self._bgColorButton,
                      flags=[None, None, wx.ALL, None, wx.ALL])

    def onFgColourCheckBoxChecked(self, event):
        ''' User toggled the foreground colour check box. Update the colour
            of the font colour button. '''
        self._fontButton.SetColour(self._fgColorButton.GetColour() if \
                                   event.IsChecked() else wx.NullColour)

    def onFgColourPicked(self, event):
        ''' User picked a foreground colour. Check the foreground colour check
            box and update the font colour button. '''
        self._fgColorCheckBox.SetValue(True)
        self._fontButton.SetColour(self._fgColorButton.GetColour())

    def onBgColourPicked(self, event):
        ''' User picked a background colour. Check the background colour check
            box. '''
        self._bgColorCheckBox.SetValue(True)

    def addFontEntry(self):
        self._fontCheckBox = wx.CheckBox(self, label=_('Use font:'))
        currentFont = self.item.font()
        currentColor = self._fgColorButton.GetColour()
        self._fontCheckBox.SetValue(currentFont is not None)
        defaultFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self._fontButton = widgets.FontPickerCtrl(self,
            font=currentFont or defaultFont, colour=currentColor)
        self._fontButton.Bind(wx.EVT_FONTPICKER_CHANGED,
                              self.onFontPickerChanged)
        self.addEntry(_('Font'), self._fontCheckBox, self._fontButton,
                      flags=[None, None, wx.ALL])

    def onFontPickerChanged(self, event):
        ''' User picked a font. Check the font check box and change the
            foreground color if needed. '''
        self._fontCheckBox.SetValue(True)
        if self._fontButton.GetSelectedColour() != self._fgColorButton.GetColour():
            self._fgColorCheckBox.SetValue(True)
            self._fgColorButton.SetColour(self._fontButton.GetSelectedColour())

    def addIconEntry(self):
        self._iconEntry = wx.combo.BitmapComboBox(self, style=wx.CB_READONLY)
        size = (16, 16)
        imageNames = sorted(artprovider.chooseableItemImages.keys())
        for imageName in imageNames:
            label = artprovider.chooseableItemImages[imageName]
            bitmap = wx.ArtProvider_GetBitmap(imageName, wx.ART_MENU, size)
            self._iconEntry.Append(label, bitmap, clientData=imageName)
        icon = self.item.icon()
        currentSelectionIndex = imageNames.index(icon)
        self._iconEntry.SetSelection(currentSelectionIndex)
        self.addEntry(_('Icon'), self._iconEntry, flags=[None, wx.ALL|wx.EXPAND])

    def ok(self):
        fgColorChecked = self._fgColorCheckBox.IsChecked()
        bgColorChecked = self._bgColorCheckBox.IsChecked()
        fgColor = self._fgColorButton.GetColour() if fgColorChecked else None
        bgColor = self._bgColorButton.GetColour() if bgColorChecked else None
        self.item.setForegroundColor(fgColor)
        self.item.setBackgroundColor(bgColor)
        fontChecked = self._fontCheckBox.IsChecked()
        font = self._fontButton.GetSelectedFont() if fontChecked else None
        self.item.setFont(font)
        icon = self._iconEntry.GetClientData(self._iconEntry.GetSelection())
        selectedIcon = icon.strip('_icon') + '_open_icon' if (icon.startswith('folder') and icon.count('_') == 2) else icon
        self.item.setIcon(icon)
        self.item.setSelectedIcon(selectedIcon)
        super(AppearancePage, self).ok()


class DatesPage(TaskHeadersMixin, PageWithHeaders):
    def __init__(self, parent, theTask, settings, *args, **kwargs):
        super(DatesPage, self).__init__(parent, theTask, *args, **kwargs)
        self._settings = settings
        datesBox = self.addDatesBox(theTask)
        reminderBox = self.addReminderBox(theTask)
        recurrenceBox = self.addRecurrenceBox(theTask)

        for box in datesBox, reminderBox, recurrenceBox:
            box.fit()
            self.add(box, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        self.fit()
    
    def addDatesBox(self, theTask):
        datesBox = widgets.BoxWithFlexGridSizer(self, label=_('Dates'), cols=3)
        self.addHeaders(datesBox)
        for label, taskMethodName in [(_('Start date'), 'startDate'),
                                      (_('Due date'), 'dueDate'),
                                      (_('Completion date'), 'completionDate')]:
            datesBox.add(label)
            taskMethod = getattr(theTask, taskMethodName)
            dateEntry = entry.DateEntry(datesBox, taskMethod(),
                                        callback=self.onDateChanged)
            setattr(self, '_%sEntry'%taskMethodName, dateEntry)
            datesBox.add(dateEntry)
            if theTask.children():
                recursiveDateEntry = entry.DateEntry(datesBox,
                    taskMethod(recursive=True), readonly=True)
            else:
                recursiveDateEntry = (0, 0)
            datesBox.add(recursiveDateEntry)
        return datesBox
        
    def addReminderBox(self, theTask):
        reminderBox = widgets.BoxWithFlexGridSizer(self, label=_('Reminder'), 
                                                   cols=2)
        reminderBox.add(_('Reminder'))
        # pylint: disable-msg=W0201
        self._reminderDateTimeEntry = createDateTimeCtrl(reminderBox,
            theTask.reminder(), self._settings)
        # If the user has not set a reminder, make sure that the default 
        # date time in the reminder entry is a reasonable suggestion:
        if self._reminderDateTimeEntry.GetValue() == date.DateTime.max:
            self.suggestReminder()
        reminderBox.add(self._reminderDateTimeEntry)
        return reminderBox
        
    def addRecurrenceBox(self, theTask):
        # pylint: disable-msg=W0201
        recurrenceBox = widgets.BoxWithFlexGridSizer(self,
            label=_('Recurrence'), cols=2)
        recurrenceBox.add(_('Recurrence'))
        panel = wx.Panel(recurrenceBox)
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._recurrenceEntry = wx.Choice(panel, 
            choices=[_('None'), _('Daily'), _('Weekly'), _('Monthly'), _('Yearly')])        
        self._recurrenceEntry.Bind(wx.EVT_CHOICE, self.onRecurrenceChanged)
        panelSizer.Add(self._recurrenceEntry, flag=wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((3,-1))
        staticText = wx.StaticText(panel, label=_(', every'))
        panelSizer.Add(staticText, flag=wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((3,-1))
        self._recurrenceFrequencyEntry = widgets.SpinCtrl(panel, size=(50,-1), 
                                                          initial=1, min=1)
        panelSizer.Add(self._recurrenceFrequencyEntry, flag=wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((3,-1))
        self._recurrenceStaticText = wx.StaticText(panel, label='reserve some space')
        panelSizer.Add(self._recurrenceStaticText, flag=wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((3, -1))
        self._recurrenceSameWeekdayCheckBox = wx.CheckBox(panel, 
            label=_('keeping dates on the same weekday'))
        panelSizer.Add(self._recurrenceSameWeekdayCheckBox, proportion=1, 
                       flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        panel.SetSizerAndFit(panelSizer)
        self._recurrenceSizer = panelSizer

        recurrenceBox.add(panel)
        recurrenceBox.add(_('Maximum number\nof recurrences'))
        panel = wx.Panel(recurrenceBox)
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._maxRecurrenceCheckBox = wx.CheckBox(panel)
        self._maxRecurrenceCheckBox.Bind(wx.EVT_CHECKBOX, self.onMaxRecurrenceChecked)
        panelSizer.Add(self._maxRecurrenceCheckBox, flag=wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((3,-1))
        self._maxRecurrenceCountEntry = widgets.SpinCtrl(panel, size=(50,-1), 
                                                         initial=1, min=1)
        panelSizer.Add(self._maxRecurrenceCountEntry)
        panel.SetSizerAndFit(panelSizer)
        recurrenceBox.add(panel)

        self.setRecurrence(theTask.recurrence())
        return recurrenceBox
    
    def entries(self):
        # pylint: disable-msg=E1101
        return dict(startDate=self._startDateEntry, dueDate=self._dueDateEntry,
                    completionDate=self._completionDateEntry, 
                    timeLeft=self._dueDateEntry, 
                    reminder=self._reminderDateTimeEntry, 
                    recurrence=self._recurrenceEntry)
    
    def onRecurrenceChanged(self, event):
        event.Skip()
        recurrenceOn = event.String != _('None')
        self._maxRecurrenceCheckBox.Enable(recurrenceOn)
        self._recurrenceFrequencyEntry.Enable(recurrenceOn)
        self._maxRecurrenceCountEntry.Enable(recurrenceOn and \
            self._maxRecurrenceCheckBox.IsChecked())
        self.updateRecurrenceLabel()

    def onMaxRecurrenceChecked(self, event):
        event.Skip()
        maxRecurrenceOn = event.IsChecked()
        self._maxRecurrenceCountEntry.Enable(maxRecurrenceOn)

    def onDateChanged(self, event):
        ''' Called when one of the DateEntries is changed by the user. Update
            the suggested reminder if no reminder was set by the user. '''
        event.Skip()
        if self._reminderDateTimeEntry.GetValue() == date.DateTime.max:
            self.suggestReminder()

    def ok(self):
        # Funny things happen with the date pickers without this (to
        # reproduce: create a task, enter the start date by hand,
        # click OK; the date is the current date instead of the one
        # typed in).
        wx.CallAfter(self._ok)

    def _ok(self):
        recurrenceDict = {0: '', 1: 'daily', 2: 'weekly', 3: 'monthly', 4: 'yearly'}
        kwargs = dict(unit=recurrenceDict[self._recurrenceEntry.Selection])
        if self._maxRecurrenceCheckBox.IsChecked():
            kwargs['max'] =self._maxRecurrenceCountEntry.Value
        kwargs['amount'] = self._recurrenceFrequencyEntry.Value
        kwargs['sameWeekday'] = self._recurrenceSameWeekdayCheckBox.IsChecked()
        # pylint: disable-msg=E1101,W0142
        self.item.setRecurrence(date.Recurrence(**kwargs))
        self.item.setStartDate(self._startDateEntry.get())
        self.item.setDueDate(self._dueDateEntry.get())
        self.item.setCompletionDate(self._completionDateEntry.get())
        self.item.setReminder(self._reminderDateTimeEntry.GetValue())

    def setReminder(self, reminder):
        self._reminderDateTimeEntry.SetValue(reminder)

    def setRecurrence(self, recurrence):
        index = {'': 0, 'daily': 1, 'weekly': 2, 'monthly': 3, 'yearly': 4}[recurrence.unit]
        self._recurrenceEntry.Selection = index
        self._maxRecurrenceCheckBox.Enable(bool(recurrence))
        self._maxRecurrenceCheckBox.SetValue(recurrence.max > 0)
        self._maxRecurrenceCountEntry.Enable(recurrence.max > 0)
        if recurrence.max > 0:
            self._maxRecurrenceCountEntry.Value = recurrence.max
        self._recurrenceFrequencyEntry.Enable(bool(recurrence))
        if recurrence.amount > 1:
            self._recurrenceFrequencyEntry.Value = recurrence.amount
        if recurrence.unit in ('monthly', 'yearly'):
            self._recurrenceSameWeekdayCheckBox.Value = recurrence.sameWeekday
        else:
            # If recurrence is not monthly or yearly, set same week day to False
            self._recurrenceSameWeekdayCheckBox.Value = False
        self.updateRecurrenceLabel()

    def updateRecurrenceLabel(self):
        recurrenceDict = {0: _('period,'), 1: _('day(s),'), 2: _('week(s),'),
                          3: _('month(s),'), 4: _('year(s),')}
        recurrenceLabel = recurrenceDict[self._recurrenceEntry.Selection]
        self._recurrenceStaticText.SetLabel(recurrenceLabel)
        self._recurrenceSameWeekdayCheckBox.Enable(self._recurrenceEntry.Selection in (3,4))
        self._recurrenceSizer.Layout()

    def suggestReminder(self):
        ''' suggestReminder populates the reminder entry with a reasonable
            suggestion for a reminder date and time, but does not enable the
            reminder entry. '''
        # The suggested date for the reminder is the first date from the
        # list of candidates that is a real date:
        # pylint: disable-msg=E1101
        candidates = [self._dueDateEntry.get(), self._startDateEntry.get(),
                      date.Tomorrow()]
        suggestedDate = [candidate for candidate in candidates \
                         if date.Today() <= candidate < date.Date()][0]
        # Add a suggested time of 8:00 AM:
        suggestedDateTime = date.DateTime(suggestedDate.year,
                                          suggestedDate.month,
                                          suggestedDate.day, 8, 0, 0)
        # Now, make sure the suggested date time is set in the control
        self.setReminder(suggestedDateTime)
        # And then disable the control (because the SetValue in the
        # previous statement enables the control)
        self.setReminder(None)
        # Now, when the user clicks the check box to enable the
        # control it will show the suggested date time


class ProgressPage(TaskHeadersMixin, PageWithHeaders):
    def __init__(self, parent, theTask, *args, **kwargs):
        super(ProgressPage, self).__init__(parent, theTask, *args, **kwargs)
        # Boxes:
        progressBox = widgets.BoxWithFlexGridSizer(self, label=_('Progress'), cols=2)
        # Editable entries:
        self._percentageCompleteOldValue = theTask.percentageComplete()
        self._percentageCompleteEntry = entry.PercentageEntry(progressBox, 
                                            self._percentageCompleteOldValue)
        # Readonly entries:
        # None
        # Fill the boxes:
        for eachEntry in [_('Percentage complete'), self._percentageCompleteEntry]:
            progressBox.add(eachEntry, flag=wx.ALIGN_RIGHT)
            
        for box in progressBox,:
            box.fit()
            self.add(box, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        self.fit()
        
    def entries(self):
        return dict(percentageComplete=self._percentageCompleteEntry)
        
    def ok(self):
        newValue = self._percentageCompleteEntry.get()
        if newValue != self._percentageCompleteOldValue:
            self.item.setPercentageComplete(newValue)


class BudgetPage(TaskHeadersMixin, PageWithHeaders):
    def __init__(self, parent, theTask, *args, **kwargs):
        super(BudgetPage, self).__init__(parent, theTask, *args, **kwargs)
        # Boxes:
        budgetBox = widgets.BoxWithFlexGridSizer(self, label=_('Budget'), cols=3)
        revenueBox = widgets.BoxWithFlexGridSizer(self, label=_('Revenue'), cols=3)
        # Editable entries:
        self._budgetEntry = entry.TimeDeltaEntry(budgetBox, theTask.budget())
        self._hourlyFeeEntry = entry.AmountEntry(revenueBox, theTask.hourlyFee())
        self._fixedFeeEntry = entry.AmountEntry(revenueBox, theTask.fixedFee())
        # Readonly entries:
        if theTask.children():
            recursiveBudget = render.budget(theTask.budget(recursive=True))
            recursiveTimeSpent = render.timeSpent(theTask.timeSpent(recursive=True))
            recursiveBudgetLeft = render.budget(theTask.budgetLeft(recursive=True))
            recursiveFixedFee = render.monetaryAmount(theTask.fixedFee(recursive=True))
            recursiveRevenue = render.monetaryAmount(theTask.revenue(recursive=True))
        else:
            recursiveBudget = recursiveTimeSpent = recursiveBudgetLeft = \
            recursiveFixedFee = recursiveRevenue = ''
        # Fill the boxes:
        self.addHeaders(budgetBox)
        for eachEntry in [_('Budget'), self._budgetEntry, recursiveBudget,
                          _('Time spent'), render.budget(theTask.timeSpent()), 
                          recursiveTimeSpent, _('Budget left'), 
                          render.budget(theTask.budgetLeft()),
                          recursiveBudgetLeft]:
            budgetBox.add(eachEntry, flag=wx.ALIGN_RIGHT)

        self.addHeaders(revenueBox)
        for eachEntry in [_('Hourly fee'), self._hourlyFeeEntry, '',
                          _('Fixed fee'), self._fixedFeeEntry, 
                          recursiveFixedFee, _('Revenue'), 
                          render.monetaryAmount(theTask.revenue()), 
                          recursiveRevenue]:
            revenueBox.add(eachEntry, flag=wx.ALIGN_RIGHT)

        for box in budgetBox, revenueBox:
            box.fit()
            self.add(box, proportion=0, flag=wx.EXPAND|wx.ALL, border=5)
        self.fit()
        
    def entries(self):
        return dict(budget=self._budgetEntry, 
                    totalBudget=self._budgetEntry,
                    budgetLeft=self._budgetEntry, 
                    totalBudgetLeft=self._budgetEntry, 
                    hourlyFee=self._hourlyFeeEntry, 
                    fixedFee=self._fixedFeeEntry, 
                    totalFixedFee=self._fixedFeeEntry, 
                    revenue=self._hourlyFeeEntry, 
                    totalRevenue=self._hourlyFeeEntry)
        
    def ok(self):
        self.item.setBudget(self._budgetEntry.get())
        self.item.setHourlyFee(self._hourlyFeeEntry.get())
        self.item.setFixedFee(self._fixedFeeEntry.get())
        

class EffortPage(TaskHeadersMixin, PageWithViewerMixin, PageWithHeaders):
    def __init__(self, parent, theTask, taskFile, settings, *args, **kwargs):
        super(EffortPage, self).__init__(parent, theTask, *args, **kwargs)
        self.viewer = viewer.EffortViewer(self, taskFile,
            settings, settingsSection='effortviewerintaskeditor',
            tasksToShowEffortFor=task.TaskList([theTask]))
        self.add(self.viewer, proportion=1, flag=wx.EXPAND|wx.ALL, 
                 border=5)
        
        self.fit()

    def entries(self):
        return dict(timeSpent=self.viewer, totalTimeSpent=self.viewer)
        

class LocalDragAndDropFixMixin(object):
    def __init__(self, *args, **kwargs):
        super(LocalDragAndDropFixMixin, self).__init__(*args, **kwargs)

        # For  a reason  that completely  escapes me,  under  MSW, the
        # viewers don't act  as drop targets in the  notebook. So make
        # the containing panel do.

        if '__WXMSW__' in wx.PlatformInfo:
            dropTarget = draganddrop.DropTarget(self.onDropURL,
                                                self.onDropFiles,
                                                self.onDropMail)
            self.SetDropTarget(dropTarget)


class LocalCategoryViewer(LocalDragAndDropFixMixin, viewer.BaseCategoryViewer):
    def __init__(self, item, *args, **kwargs):
        self.item = item
        super(LocalCategoryViewer, self).__init__(*args, **kwargs)
        self.widget.ExpandAll()
    
    def getIsItemChecked(self, item):
        if isinstance(item, category.Category):
            return item in self.item.categories()
        return False

    def createCategoryPopupMenu(self): # pylint: disable-msg=W0221
        return super(LocalCategoryViewer, self).createCategoryPopupMenu(True)

    def onCheck(self, event):
        # We don't want the 'main' category viewer to be affected by
        # what's happening here.
        pass


class CategoriesPage(PageWithViewerMixin, PageWithHeaders):
    def __init__(self, parent, item, taskFile, settings, *args, **kwargs):
        super(CategoriesPage, self).__init__(parent, item, *args, **kwargs)
        self.__categories = category.CategorySorter(taskFile.categories())
        categoriesBox = widgets.BoxWithBoxSizer(self, label=_('Categories'))
        self.viewer = LocalCategoryViewer(item, categoriesBox,
                                          taskFile, settings,
                                          settingsSection=self.settingsSection())
        categoriesBox.add(self.viewer, proportion=1, flag=wx.EXPAND|wx.ALL)
        categoriesBox.fit()
        self.add(categoriesBox)
        self.fit()
    
    def settingsSection(self):
        raise NotImplementedError
    
    def entries(self):
        return dict(categories=self.viewer, totalCategories=self.viewer) 

    def ok(self):
        treeCtrl = self.viewer.widget
        treeCtrl.ExpandAll()
        for categoryNode in treeCtrl.GetItemChildren(recursively=True):
            categoryObject = treeCtrl.GetItemPyData(categoryNode)
            if categoryNode.IsChecked():
                categoryObject.addCategorizable(self.item)
                self.item.addCategory(categoryObject)
            else:
                categoryObject.removeCategorizable(self.item)
                self.item.removeCategory(categoryObject)


class TaskCategoriesPage(TaskHeadersMixin, CategoriesPage):
    def settingsSection(self):
        return 'categoryviewerintaskeditor'


class NoteCategoriesPage(TaskHeadersMixin, CategoriesPage):
    def settingsSection(self):
        return 'categoryviewerinnoteeditor'


class LocalAttachmentViewer(LocalDragAndDropFixMixin, viewer.AttachmentViewer):
    pass


class AttachmentsPage(PageWithViewerMixin, PageWithHeaders):
    def __init__(self, parent, item, settings, taskFile, *args, **kwargs):
        settingsSection = kwargs.pop('settingsSection')
        super(AttachmentsPage, self).__init__(parent, item, *args, **kwargs)
        self.attachmentsList = attachment.AttachmentList(item.attachments())
        attachmentsBox = widgets.BoxWithBoxSizer(self, label=_('Attachments'))
        self.viewer = LocalAttachmentViewer(attachmentsBox,
                                            taskFile, settings,
                                            settingsSection=settingsSection,
                                            attachmentsToShow=self.attachmentsList)
        attachmentsBox.add(self.viewer, proportion=1, flag=wx.EXPAND|wx.ALL)
        attachmentsBox.fit()
        self.add(attachmentsBox)
        self.fit()

    def entries(self):
        return dict(attachments=self.viewer)

    def ok(self):
        self.item.setAttachments(self.attachmentsList)
        super(AttachmentsPage, self).ok()


class LocalNoteViewer(LocalDragAndDropFixMixin, viewer.BaseNoteViewer):
    pass


class NotesPage(PageWithViewerMixin, PageWithHeaders):
    def __init__(self, parent, item, settings, taskFile, *args, **kwargs):
        super(NotesPage, self).__init__(parent, item, *args, **kwargs)
        notesBox = widgets.BoxWithBoxSizer(self, label=_('Notes'))
        self.notes = note.NoteContainer(item.notes())
        self.viewer = LocalNoteViewer(notesBox, taskFile, settings, 
            settingsSection='noteviewerintaskeditor',
            notesToShow=self.notes)
        notesBox.add(self.viewer, flag=wx.EXPAND|wx.ALL, proportion=1)
        notesBox.fit()
        self.add(notesBox, proportion=1, flag=wx.EXPAND|wx.ALL, border=5)
        self.fit()
    
    def entries(self):
        return dict(notes=self.viewer)
                
    def ok(self):
        self.item.setNotes(list(self.notes.rootItems()))


class BehaviorPage(TaskHeadersMixin, PageWithHeaders):
    def __init__(self, parent, theTask, *args, **kwargs):
        super(BehaviorPage, self).__init__(parent, theTask, *args, **kwargs)
        behaviorBox = widgets.BoxWithFlexGridSizer(self,
            label=_('Task behavior'), cols=2)
        choice = self._markTaskCompletedEntry = wx.Choice(behaviorBox)
        for choiceValue, choiceText in \
                [(None, _('Use application-wide setting')),
                 (False, _('No')), (True, _('Yes'))]:
            choice.Append(choiceText, choiceValue)
            if choiceValue == theTask.shouldMarkCompletedWhenAllChildrenCompleted():
                choice.SetSelection(choice.GetCount()-1)
        if choice.GetSelection() == wx.NOT_FOUND:
            # Force a selection if necessary:
            choice.SetSelection(0)
        behaviorBox.add(_('Mark task completed when all children are'
                          ' completed?'))
        behaviorBox.add(choice)
        behaviorBox.fit()
        self.add(behaviorBox, border=5)
        self.fit()

    def ok(self):
        self.item.setShouldMarkCompletedWhenAllChildrenCompleted( \
            self._markTaskCompletedEntry.GetClientData( \
                self._markTaskCompletedEntry.GetSelection()))


class TaskEditBook(widgets.Listbook):
    def __init__(self, parent, theTask, taskFile, settings, *args, **kwargs):
        super(TaskEditBook, self).__init__(parent)
        self.AddPage(TaskSubjectPage(self, theTask), _('Description'), 'pencil_icon')
        self.AddPage(DatesPage(self, theTask, settings), _('Dates'), 'calendar_icon')
        self.AddPage(ProgressPage(self, theTask), _('Progress'), 'progress')
        self.AddPage(TaskCategoriesPage(self, theTask, taskFile, settings), 
                     _('Categories'), 'folder_blue_arrow_icon')
        if settings.getboolean('feature', 'effort'):
            self.AddPage(BudgetPage(self, theTask),
                         _('Budget'), 'calculator_icon')
            self.AddPage(EffortPage(self, theTask, taskFile, settings), 
                         _('Effort'), 'clock_icon')
        if settings.getboolean('feature', 'notes'):
            self.AddPage(NotesPage(self, theTask, settings, taskFile), 
                         _('Notes'), 'note_icon')
        self.AddPage(AttachmentsPage(self, theTask, settings, taskFile, 
                                     settingsSection='attachmentviewerintaskeditor'), 
                     _('Attachments'), 'paperclip_icon')
        self.AddPage(AppearancePage(theTask, self), _('Appearance'),
                     'palette_icon')
        self.AddPage(BehaviorPage(self, theTask), _('Behavior'), 'cogwheel_icon')
        self.item = theTask


class EffortEditBook(Page, widgets.BookPage):
    def __init__(self, parent, effort, editor, effortList, taskList, settings,
                 *args, **kwargs):
        super(EffortEditBook, self).__init__(parent, columns=3, *args, **kwargs)
        self._editor = editor
        self.item = self._effort = effort
        self._effortList = effortList
        if effort.task() in taskList:
            self._taskList = taskList
        else:
            self._taskList = task.TaskList(taskList)
            self._taskList.append(effort.task())
        self._settings = settings
        self.addTaskEntry()
        self.addStartAndStopEntries()
        self.addDescriptionEntry()
        self.fit()

    def addTaskEntry(self):
        ''' Add an entry for changing the task that this effort record
            belongs to. '''
        # pylint: disable-msg=W0201
        self._taskEntry = entry.TaskComboTreeBox(self,
            rootTasks=self._taskList.rootItems(),
            selectedTask=self._effort.task())
        self.addEntry(_('Task'), self._taskEntry,
                      flags=[None, wx.ALL|wx.EXPAND])

    def addStartAndStopEntries(self):
        # pylint: disable-msg=W0201
        self._startEntry = createDateTimeCtrl(self, self._effort.getStart(),
            self._settings, self.onPeriodChanged, noneAllowed=False, showSeconds=True)
        startFromLastEffortButton = wx.Button(self,
            label=_('Start tracking from last stop time'))
        self.Bind(wx.EVT_BUTTON, self.onStartFromLastEffort,
            startFromLastEffortButton)
        if self._effortList.maxDateTime() is None:
            startFromLastEffortButton.Disable()

        self._stopEntry = createDateTimeCtrl(self, self._effort.getStop(),
            self._settings, self.onPeriodChanged, noneAllowed=True, showSeconds=True)
        flags = [None, wx.ALIGN_RIGHT|wx.ALL, wx.ALIGN_LEFT|wx.ALL, None]
        self.addEntry(_('Start'), self._startEntry,
            startFromLastEffortButton,  flags=flags)
        self.addEntry(_('Stop'), self._stopEntry, '', flags=flags)

    def onStartFromLastEffort(self, event): # pylint: disable-msg=W0613
        self._startEntry.SetValue(self._effortList.maxDateTime())
        self.preventNegativeEffortDuration()

    def addDescriptionEntry(self):
        # pylint: disable-msg=W0201
        self._descriptionEntry = widgets.MultiLineTextCtrl(self,
            self._effort.description())
        self._descriptionEntry.SetSizeHints(300, 150)
        self.addEntry(_('Description'), self._descriptionEntry,
            flags=[None, wx.ALL|wx.EXPAND], growable=True)

    def ok(self):
        self._effort.setTask(self._taskEntry.GetSelection())
        self._effort.setStart(self._startEntry.GetValue())
        self._effort.setStop(self._stopEntry.GetValue())
        self._effort.setDescription(self._descriptionEntry.GetValue())

    def onPeriodChanged(self, *args, **kwargs): # pylint: disable-msg=W0613
        if not hasattr(self, '_stopEntry'): # Check that both entries exist
            return
        # We use CallAfter to give the DatePickerCtrl widgets a chance
        # to update themselves
        wx.CallAfter(self.preventNegativeEffortDuration)

    def preventNegativeEffortDuration(self):
        if self._startEntry.GetValue() > self._stopEntry.GetValue():
            self._editor.disableOK()
        else:
            self._editor.enableOK()

    # Fake a Book interface:
    
    def GetPageCount(self):
        return 1 # EffortEditBook has no pages.
    
    def ChangeSelection(self, pageIndex):
        pass
    
    def __getitem__(self, index):
        return self
    
    def entries(self):
        return dict(period=self._stopEntry, task=self._taskEntry,
                    description=self._descriptionEntry,
                    timeSpent=self._stopEntry, totalTimeSpent=self._stopEntry,
                    revenue=self._taskEntry, totalRevenue=self._taskEntry)
    
    
class CategoryEditBook(widgets.Listbook):
    def __init__(self, parent, theCategory, settings, taskFile, *args, **kwargs):
        self.item = theCategory
        super(CategoryEditBook, self).__init__(parent, *args, **kwargs)
        self.AddPage(CategorySubjectPage(self, theCategory), 
                     _('Description'), 'pencil_icon')
        if settings.getboolean('feature', 'notes'):
            self.AddPage(NotesPage(self, theCategory, settings, taskFile), 
                         _('Notes'), 'note_icon')
        self.AddPage(AttachmentsPage(self, theCategory, settings, taskFile, 
                                     settingsSection='attachmentviewerincategoryeditor'), 
                     _('Attachments'), 'paperclip_icon')
        self.AddPage(AppearancePage(theCategory, self), _('Appearance'),
                     'palette_icon')


class NoteEditBook(widgets.Listbook):
    def __init__(self, parent, theNote, settings, categories, taskFile, *args, **kwargs):
        self.item = theNote
        super(NoteEditBook, self).__init__(parent, *args, **kwargs)
        self.AddPage(NoteSubjectPage(self, theNote), _('Description'), 'pencil_icon')
        self.AddPage(NoteCategoriesPage(self, theNote, taskFile, settings), 
                     _('Categories'), 'folder_blue_arrow_icon')
        self.AddPage(AttachmentsPage(self, theNote, settings, taskFile,
                                     settingsSection='attachmentviewerinnoteeditor'),
                     _('Attachments'), 'paperclip_icon')
        self.AddPage(AppearancePage(theNote, self), _('Appearance'),
                     'palette_icon')


class AttachmentEditBook(widgets.Listbook):
    def __init__(self, parent, theAttachment, settings, taskFile,
                 *args, **kwargs):
        self.item = theAttachment
        super(AttachmentEditBook, self).__init__(parent, *args, **kwargs)
        self.AddPage(AttachmentSubjectPage(self, theAttachment,
                                           settings.get('file', 'attachmentbase')), 
                     _('Description'), 'pencil_icon')
        if settings.getboolean('feature', 'notes'):
            self.AddPage(NotesPage(self, theAttachment, settings, taskFile), 
                         _('Notes'), 'note_icon')
        self.AddPage(AppearancePage(theAttachment, self), _('Appearance'),
                     'palette_icon')


class EditorWithCommand(widgets.NotebookDialog):
    def __init__(self, parent, command, container, *args, **kwargs):
        self._command = command
        super(EditorWithCommand, self).__init__(parent, command.name(), 
                                                *args, **kwargs)
        columnName = kwargs.get('columnName', '')
        if columnName:
            self.setFocus(columnName)
        else:
            self.setFocusOnFirstEntry()
        patterns.Publisher().registerObserver(self.onItemRemoved, 
            eventType=container.removeItemEventType(), eventSource=container)

    def setFocus(self, columnName):
        ''' Select the correct page of the editor and correct control on a page
            based on the column that the user double clicked. '''
        page = 0
        for pageIndex in range(self[0].GetPageCount()):
            if columnName in self[0][pageIndex].entries():
                page = pageIndex
                break
        self[0].ChangeSelection(page)
        self[0][page].setFocusOnEntry(columnName)
        
    def setFocusOnFirstEntry(self):
        firstEntry = self[0][0]._subjectEntry
        firstEntry.SetSelection(-1, -1) # Select all text
        firstEntry.SetFocus()

    def addPages(self):
        for item in self._command.items:
            self.addPage(item)
            
    def addPage(self, item):
        raise NotImplementedError

    def cancel(self, *args, **kwargs): # pylint: disable-msg=W0221
        patterns.Publisher().removeObserver(self.onItemRemoved)
        super(EditorWithCommand, self).cancel(*args, **kwargs)
        
    def ok(self, *args, **kwargs):
        patterns.Publisher().removeObserver(self.onItemRemoved)
        super(EditorWithCommand, self).ok(*args, **kwargs)
        self._command.do()
        
    def onItemRemoved(self, event):
        ''' The item we're editing or one of its ancestors has been removed. 
            Close the tab of the item involved and close the whole editor if 
            there are no tabs left. '''
        if not self:
            return # Prevent _wxPyDeadObject TypeError
        pagesToCancel = [] # Collect the pages to cancel so we don't modify the 
                           # book widget while we iterate over it
        for item in event.values():
            pagesToCancel.extend([page for page in self \
                                  if self.isPageDisplayingItemOrChildOfItem(page, item)])
        self.cancelPages(pagesToCancel)
        if len(list(self)) == 0:
            self.cancel()
            
    def isPageDisplayingItemOrChildOfItem(self, page, item):
        return item in [page.item] + page.item.ancestors()


class TaskEditor(EditorWithCommand):
    def __init__(self, parent, command, settings, tasks, taskFile, bitmap='edit', 
                 *args, **kwargs):
        self._settings = settings
        self._taskFile = taskFile
        super(TaskEditor, self).__init__(parent, command, tasks, 
                                         bitmap, *args, **kwargs)

    def addPage(self, theTask):
        page = TaskEditBook(self._interior, theTask, self._taskFile, 
                            self._settings)
        self._interior.AddPage(page, theTask.subject())
        

class EffortEditor(EditorWithCommand):
    def __init__(self, parent, command, settings, efforts, taskFile, 
                 *args, **kwargs):
        self._taskFile = taskFile
        self._settings = settings
        super(EffortEditor, self).__init__(parent, command, efforts, 
                                           *args, **kwargs)

    def setFocusOnFirstEntry(self):
        pass
        
    def addPages(self):
        # Override this method to make sure we use the efforts, not the task
        for effort in self._command.efforts:
            self.addPage(effort)

    def addPage(self, effort):
        page = EffortEditBook(self._interior, effort, self, self._taskFile.efforts(),
            self._taskFile.tasks(), self._settings)
        self._interior.AddPage(page, effort.task().subject())

    def isPageDisplayingItemOrChildOfItem(self, page, item):
        if hasattr(item, 'setTask'):
            return page.item == item # Regular effort
        else:
            return item.mayContain(page.item) # Composite effort


class CategoryEditor(EditorWithCommand):
    def __init__(self, parent, command, settings, categories, taskFile, 
                 *args, **kwargs):
        self._settings = settings
        self._taskFile = taskFile
        super(CategoryEditor, self).__init__(parent, command, categories, 
                                             *args, **kwargs)

    def addPage(self, theCategory):
        page = CategoryEditBook(self._interior, theCategory,
                                self._settings, self._taskFile)
        self._interior.AddPage(page, theCategory.subject())


class NoteEditor(EditorWithCommand):
    def __init__(self, parent, command, settings, notes, taskFile, *args, **kwargs):
        self._settings = settings
        self._taskFile = taskFile
        super(NoteEditor, self).__init__(parent, command, notes, *args, **kwargs)

    def addPages(self):
        # Override this method to make sure we use the notes, not the note owner
        for eachNote in self._command.notes:
            self.addPage(eachNote)

    def addPage(self, theNote):
        page = NoteEditBook(self._interior, theNote, self._settings, 
                            self._taskFile.categories(), self._taskFile)
        self._interior.AddPage(page, theNote.subject())


class AttachmentEditor(EditorWithCommand):
    def __init__(self, parent, command, settings, attachments, taskFile, *args, **kwargs):
        self._settings = settings
        self._taskFile = taskFile
        super(AttachmentEditor, self).__init__(parent, command, attachments, *args, **kwargs)

    def addPage(self, theAttachment):
        page = AttachmentEditBook(self._interior, theAttachment, self._settings,
                                  self._taskFile)
        self._interior.AddPage(page, theAttachment.subject())
