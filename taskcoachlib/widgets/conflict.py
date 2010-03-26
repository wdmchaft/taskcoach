'''
Task Coach - Your friendly task manager
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>

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

from taskcoachlib.i18n import _
from taskcoachlib.widgets import datectrl
from taskcoachlib.syncml.notesource import NoteSource
from taskcoachlib.syncml.tasksource import TaskSource

import wx

class FieldMixin(object):
    def __init__(self, *args, **kwargs):
        self.callback = kwargs.pop('callback', None)

        super(FieldMixin, self).__init__(*args, **kwargs)

    def OnChange(self, evt):
        if self.callback is not None:
            self.callback(self.GetId())


class OneLineTextField(FieldMixin, wx.TextCtrl):
    def __init__(self, *args, **kwargs):
        super(OneLineTextField, self).__init__(*args, **kwargs)

        wx.EVT_TEXT(self, wx.ID_ANY, self.OnChange)


class MultipleLinesTextField(OneLineTextField):
    def __init__(self, *args, **kwargs):
        kwargs['style'] = kwargs.get('style', 0) | wx.TE_MULTILINE

        super(MultipleLinesTextField, self).__init__(*args, **kwargs)


class IntegerField(FieldMixin, wx.SpinCtrl):
    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)

        wx.EVT_SPINCTRL(self, wx.ID_ANY, self.OnChange)

    def ChangeValue(self, value):
        self.SetValue(value)


class DateField(FieldMixin, datectrl.DateCtrl):
    def __init__(self, parent, *args, **kwargs):
        super(DateField, self).__init__(parent, self.OnChange, *args, **kwargs)

    def ChangeValue(self, value):
        # FIXME: under  WXGTK at  least (didn't try  other platforms),
        # checking/unchecking  the  check  box  does not  trigger  the
        # change event.
        self.SetValue(value)


class BaseConflictPanel(wx.Panel):
    def __init__(self, flags, local, remote, *args, **kwargs):
        super(BaseConflictPanel, self).__init__(*args, **kwargs)

        self.flags = flags
        self.local = local
        self.remote = remote

        self.fields = dict()
        self.sizer = wx.FlexGridSizer(0, 7)

        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Field name')), 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Local')), 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        self.sizer.Add((0, 0))
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Remote')), 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        self.sizer.Add((0, 0))
        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Fusion')), 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        self.sizer.Add((0, 0))

        self.sizer.AddGrowableCol(1)
        self.sizer.AddGrowableCol(3)
        self.sizer.AddGrowableCol(5)

        self.SetSizer(self.sizer)

    def AddConflictItem(self, name, type_, local, remote, canMerge=True):
        id_ = wx.NewId()

        localWidget = type_(self, id_)
        localWidget.SetValue(local)
        localWidget.Enable(False)

        remoteWidget = type_(self, id_)
        remoteWidget.SetValue(remote)
        remoteWidget.Enable(False)

        fusionWidget = type_(self, id_, callback=self.OnFusionChanged)
        fusionWidget.SetValue(local)
        if not canMerge:
            fusionWidget.Enable(False)

        btnLocal = wx.RadioButton(self, id_, u'', style=wx.RB_GROUP)
        btnRemote = wx.RadioButton(self, id_, u'')

        if canMerge:
            btnFusion = wx.RadioButton(self, id_, u'')
        else:
            btnFusion = None

        wx.EVT_RADIOBUTTON(btnLocal, id_, self.OnLocalSelected)
        wx.EVT_RADIOBUTTON(btnRemote, id_, self.OnRemoteSelected)

        self.sizer.Add(wx.StaticText(self, wx.ID_ANY, name), 0, wx.ALIGN_CENTRE|wx.ALL, 3)
        self.sizer.Add(localWidget, 0, wx.EXPAND|wx.ALL, 3)
        self.sizer.Add(btnLocal)
        self.sizer.Add(remoteWidget, 0, wx.EXPAND|wx.ALL, 3)
        self.sizer.Add(btnRemote)
        self.sizer.Add(fusionWidget, 0, wx.EXPAND|wx.ALL, 3)

        if canMerge:
            self.sizer.Add(btnFusion)
        else:
            self.sizer.Add((0, 0))

        self.fields[id_] = (localWidget, remoteWidget, fusionWidget, btnFusion)

        return id_

    def OnLocalSelected(self, evt):
        if self.fields.has_key(evt.GetId()):
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[evt.GetId()]
            fusionWidget.ChangeValue(localWidget.GetValue())

    def OnRemoteSelected(self, evt):
        if self.fields.has_key(evt.GetId()):
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[evt.GetId()]
            fusionWidget.ChangeValue(remoteWidget.GetValue())

    def OnFusionChanged(self, id_):
        if self.fields.has_key(id_):
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[id_]
            btnFusion.SetValue(True)


class NoteConflictPanel(BaseConflictPanel):
    def __init__(self, *args, **kwargs):
        super(NoteConflictPanel, self).__init__(*args, **kwargs)

        if self.flags & NoteSource.CONFLICT_SUBJECT:
            self.idSubject = self.AddConflictItem(_('Subject'),
                                                  OneLineTextField,
                                                  self.local.subject(),
                                                  self.remote.subject())
        if self.flags & NoteSource.CONFLICT_DESCRIPTION:
            self.idDescription = self.AddConflictItem(_('Description'),
                                                      MultipleLinesTextField,
                                                      self.local.description(),
                                                      self.remote.description())

    def getResolved(self):
        resolved = {}

        if self.flags & NoteSource.CONFLICT_SUBJECT:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idSubject]
            resolved['subject'] = fusionWidget.GetValue()
        if self.flags & NoteSource.CONFLICT_DESCRIPTION:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idDescription]
            resolved['description'] = fusionWidget.GetValue()

        return resolved


class TaskConflictPanel(BaseConflictPanel):
    def __init__(self, *args, **kwargs):
        super(TaskConflictPanel, self).__init__(*args, **kwargs)

        if self.flags & TaskSource.CONFLICT_SUBJECT:
            self.idSubject = self.AddConflictItem(_('Subject'),
                                                  OneLineTextField,
                                                  self.local.subject(),
                                                  self.remote.subject())
        if self.flags & TaskSource.CONFLICT_DESCRIPTION:
            self.idDescription = self.AddConflictItem(_('Description'),
                                                      MultipleLinesTextField,
                                                      self.local.description(),
                                                      self.remote.description())
        if self.flags & TaskSource.CONFLICT_STARTDATE:
            self.idStartDate = self.AddConflictItem(_('Start date'),
                                                    DateField,
                                                    self.local.startDate(),
                                                    self.remote.startDate())
        if self.flags & TaskSource.CONFLICT_DUEDATE:
            self.idDueDate = self.AddConflictItem(_('Due date'),
                                                  DateField,
                                                  self.local.dueDate(),
                                                  self.remote.dueDate())
        if self.flags & TaskSource.CONFLICT_COMPLETIONDATE:
            self.idCompletionDate = self.AddConflictItem(_('Completion date'),
                                                         DateField,
                                                         self.local.completionDate(),
                                                         self.remote.completionDate())
        if self.flags & TaskSource.CONFLICT_PRIORITY:
            self.idPriority = self.AddConflictItem(_('Priority'),
                                                   IntegerField,
                                                   self.local.priority(),
                                                   self.remote.priority())
        if self.flags & TaskSource.CONFLICT_CATEGORIES:
            self.idCategories = self.AddConflictItem(_('Categories'),
                                                     OneLineTextField,
                                                     ','.join(map(unicode, self.local.categories())),
                                                     ','.join(map(unicode, self.remote.categories())),
                                                     False)

    def getResolved(self):
        resolved = {}

        if self.flags & TaskSource.CONFLICT_SUBJECT:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idSubject]
            resolved['subject'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_DESCRIPTION:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idDescription]
            resolved['description'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_STARTDATE:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idStartDate]
            resolved['startDate'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_DUEDATE:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idDueDate]
            resolved['dueDate'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_PRIORITY:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idPriority]
            resolved['priority'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_CATEGORIES:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idCategories]
            resolved['categories'] = fusionWidget.GetValue()
        if self.flags & TaskSource.CONFLICT_COMPLETIONDATE:
            localWidget, remoteWidget, fusionWidget, btnFusion = self.fields[self.idCompletionDate]
            resolved['completionDate'] = fusionWidget.GetValue()

        return resolved


class ConflictDialog(wx.Dialog):
    def __init__(self, type_, flags, local, remote, *args, **kwargs):
        kwargs['style'] = kwargs.get('style', wx.CAPTION) | wx.RESIZE_BORDER

        super(ConflictDialog, self).__init__(*args, **kwargs)

        self.panel = type_(flags, local, remote, self, wx.ID_ANY)

        btnOK = wx.Button(self, wx.ID_ANY, _('OK'))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND|wx.ALL, 3)
        sizer.Add(btnOK, 0, wx.ALL|wx.ALIGN_CENTRE, 3)

        self.SetSizer(sizer)
        self.Fit()

        wx.EVT_BUTTON(btnOK, wx.ID_ANY, self.OnOK)

    def OnOK(self, evt):
        self.resolved = self.panel.getResolved()
        self.EndModal(wx.ID_OK)
