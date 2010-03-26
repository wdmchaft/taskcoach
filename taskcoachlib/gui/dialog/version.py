'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>

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
from wx.lib import hyperlink
from taskcoachlib import meta
from taskcoachlib.i18n import _
from taskcoachlib.widgets import sized_controls


class VersionDialog(sized_controls.SizedDialog):
    def __init__(self, *args, **kwargs):
        version = kwargs.pop('version')
        self.settings = kwargs.pop('settings')
        kwargs['title'] = kwargs.get('title', 
            _('New version of %(name)s available')%dict(name=meta.data.name))
        super(VersionDialog, self).__init__(*args, **kwargs)
        pane = self.GetContentsPane()
        pane.SetSizerType("vertical")
        panel = sized_controls.SizedPanel(pane)
        panel.SetSizerType('horizontal')
        messageInfo = dict(version=version, name=meta.data.name)
        message = _('Version %(version)s of %(name)s is available from')%messageInfo
        wx.StaticText(panel, label=message)
        hyperlink.HyperLinkCtrl(panel, label=meta.data.url)
        self.check = wx.CheckBox(pane, label=_('Notify me of new versions.'))
        self.check.SetValue(True)
        self.SetButtonSizer(self.CreateStdDialogButtonSizer(wx.OK))
        self.Fit()
        self.Bind(wx.EVT_CLOSE, self.onClose)
        
    def onClose(self, event):
        event.Skip()
        self.settings.set('version', 'notify', str(self.check.GetValue())) 