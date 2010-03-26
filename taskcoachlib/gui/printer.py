'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jerome Laheurte <fraca7@free.fr>
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
from taskcoachlib import persistence, patterns
from taskcoachlib.i18n import _


class PrinterSettings(object):
    __metaclass__ = patterns.Singleton

    edges = ('top', 'left', 'bottom', 'right')

    def __init__(self, settings):
        self.settings = settings
        self.printData = wx.PrintData()
        self.pageSetupData = wx.PageSetupDialogData(self.printData)
        self._initializeFromSettings()

    def updatePageSetupData(self, data):
        self.pageSetupData = wx.PageSetupDialogData(data)
        self.updatePrintData(data.GetPrintData())
        self._saveToSettings()

    def updatePrintData(self, printData):
        self.printData = wx.PrintData(printData)
        self.pageSetupData.SetPrintData(self.printData)
 
    def __getattr__(self, attr):
        try:
            return getattr(self.pageSetupData, attr)
        except AttributeError:
            return getattr(self.printData, attr)

    def _initializeFromSettings(self):
        ''' Load the printer settings from the user settings. '''
        margin = dict()
        for edge in self.edges:
            margin[edge] = self._getSetting('margin_'+edge)
        topLeft = wx.Point(margin['top'], margin['left'])
        bottomRight = wx.Point(margin['bottom'], margin['right'])
        self.SetMarginTopLeft(topLeft)
        self.SetMarginBottomRight(bottomRight)
        self.SetPaperId(self._getSetting('paper_id'))
        self.SetOrientation(self._getSetting('orientation'))

    def _saveToSettings(self):
        ''' Save the printer settings to the user settings. '''
        margin = dict()
        margin['top'], margin['left'] = self.GetMarginTopLeft()  
        margin['bottom'], margin['right'] = self.GetMarginBottomRight()  
        for edge in self.edges:
            self._setSetting('margin_'+edge, margin[edge])
        self._setSetting('paper_id', self.GetPaperId())
        self._setSetting('orientation', self.GetOrientation())

    def _getSetting(self, option):
        return self.settings.getint('printer', option)

    def _setSetting(self, option, value):
        self.settings.set('printer', option, str(value))


class HTMLPrintout(wx.html.HtmlPrintout):
    def __init__(self, htmlText, settings):
        super(HTMLPrintout, self).__init__()
        self.SetHtmlText(htmlText)
        self.SetFooter(_('Page') + ' @PAGENUM@/@PAGESCNT@', wx.html.PAGE_ALL)
        self.SetFonts('Arial', 'Courier')
        printerSettings = PrinterSettings(settings)
        top, left = printerSettings.pageSetupData.GetMarginTopLeft()
        bottom, right = printerSettings.pageSetupData.GetMarginBottomRight()
        self.SetMargins(top, bottom, left, right)

                
class DCPrintout(wx.Printout):
    def __init__(self, widget):
        self.widget = widget
        super(DCPrintout, self).__init__()
        
    def OnPrintPage(self, page): # pylint: disable-msg=W0613
        self.widget.Draw(self.GetDC())
        
    def GetPageInfo(self): # pylint: disable-msg=W0221
        return (1, 1, 1, 1)

        
def Printout(viewer, settings, printSelectionOnly=False, 
             twoPrintouts=False):
    widget = viewer.getWidget()
    if hasattr(widget, 'Draw'):
        def _printout():
            return DCPrintout(widget)
    else:
        htmlText = persistence.viewer2html(viewer, settings, 
                                           selectionOnly=printSelectionOnly)[0]
        def _printout():
            return HTMLPrintout(htmlText, settings)
    result = _printout()
    if twoPrintouts:
        result = (result, _printout())
    return result