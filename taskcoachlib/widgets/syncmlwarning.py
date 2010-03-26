
import wx

from taskcoachlib.i18n import _

class SyncMLWarningDialog(wx.Dialog):
    def __init__(self, parent):
        super(SyncMLWarningDialog, self).__init__(parent, wx.ID_ANY, _('Compatibility warning'))

        textWidget = wx.StaticText(self, wx.ID_ANY,
                                   _('The SyncML feature is disabled, because the module\n'
                                     'could not be loaded. This may be because your platform\n'
                                     'is not supported, or under Windows, you may be missing\n'
                                     'some mandatory DLLs. Please see the SyncML section of\n'
                                     'the online help for details (under "Troubleshooting").'))
        self.checkbox = wx.CheckBox(self, wx.ID_ANY, _('Never show this dialog again'))
        self.checkbox.SetValue(True)
        button = wx.Button(self, wx.ID_ANY, _('OK'))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(textWidget, 0, wx.ALL, 10)
        sizer.Add(self.checkbox, 0, wx.ALL, 3)
        sizer.Add(button, 0, wx.ALL|wx.ALIGN_CENTRE, 3)

        self.SetSizer(sizer)

        wx.EVT_BUTTON(button, wx.ID_ANY, self.OnOK)
        wx.EVT_CLOSE(self, self.OnOK)

        self.Fit()

    def OnOK(self, event):
        if self.checkbox.IsChecked():
            self.EndModal(wx.ID_OK)
        else:
            self.EndModal(wx.ID_CANCEL)
