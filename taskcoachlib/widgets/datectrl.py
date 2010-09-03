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
import combo
from taskcoachlib.domain import date


class Panel(wx.Panel):
    def __init__(self, parent, callback=None, *args, **kwargs):
        super(Panel, self).__init__(parent, *args, **kwargs)
        self._controls = self._createControls(callback)
        self._layout()
        if '__WXGTK__' == wx.Platform:
            # Many EVT_CHILD_FOCUS are sent on wxGTK, see 
            # http://trac.wxwidgets.org/ticket/11305. Ignore these events
            self.Bind(wx.EVT_CHILD_FOCUS, self.onChildFocus)

    def onChildFocus(self, event):
        pass
        
    def _createControls(self, callback):
        raise NotImplementedError
                
    def _layout(self):
        self._sizer = wx.BoxSizer(wx.HORIZONTAL) # pylint: disable-msg=W0201
        for control in self._controls:
            self._sizer.Add(control, border=2, 
                            flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.SetSizerAndFit(self._sizer)


class _BetterDatePickerCtrl(wx.DatePickerCtrl):
    ''' The default DatePickerControl on Mac OS X and Linux doesn't disable
        the calendar drop down button. This class fixes that and keyboard
        navigation. '''

    def __init__(self, *args, **kwargs):
        super(_BetterDatePickerCtrl, self).__init__(*args, **kwargs)
        if wx.Platform != '__WXMSW__':
            comboCtrl = self.GetChildren()[0]
            comboCtrl.Bind(wx.EVT_KEY_DOWN, self.onKey)

    def onKey(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_RETURN:
            # Move to the next field so that the contents of the text control,
            # that might be edited by the user, are updated by the datepicker:
            self.GetParent().Navigate() 
            # Next, click the default button of the dialog:
            button = self.getTopLevelWindow().GetDefaultItem() # pylint: disable-msg=E1103
            click = wx.CommandEvent()
            click.SetEventType(wx.EVT_BUTTON.typeId)
            wx.PostEvent(button, click)
        elif keyCode == wx.WXK_TAB:
            self.GetParent().Navigate(not event.ShiftDown())
        else:
            event.Skip()

    def getTopLevelWindow(self):
        window = self
        while not window.IsTopLevel():
            window = window.GetParent()
        return window

    def Disable(self): # pylint: disable-msg=W0221
        super(_BetterDatePickerCtrl, self).Disable()
        for child in self.Children:
            child.Disable()
            
    def Enable(self, enable=True): # pylint: disable-msg=W0221
        super(_BetterDatePickerCtrl, self).Enable(enable)
        for child in self.Children:
            child.Enable(enable)
            

class _DatePickerCtrlThatFixesAllowNoneStyle(Panel):
    def __init__(self, parent, *args, **kwargs):
        self.__args = args
        self.__kwargs = kwargs
        super(_DatePickerCtrlThatFixesAllowNoneStyle, self).__init__(parent)
        
    def _createControls(self, callback):
        # pylint: disable-msg=W0201
        self.__check = wx.CheckBox(self)
        self.__check.Bind(wx.EVT_CHECKBOX, self.onCheck)
        self.__datePicker = _BetterDatePickerCtrl(self, *self.__args, 
                                                  **self.__kwargs)
        self.__datePicker.Disable()
        return [self.__check, self.__datePicker]

    def onCheck(self, event):
        self.__datePicker.Enable(event.IsChecked())
        event.Skip()

    def GetValue(self):
        if self.__datePicker.IsEnabled():
            return self.__datePicker.GetValue()
        else:
            return wx.DateTime()

    def SetValue(self, value):
        if value.IsValid():
            self.__datePicker.Enable()
            self.__check.SetValue(True)
            self.__datePicker.SetValue(value)
        else:
            self.__datePicker.Disable()
            self.__check.SetValue(False)

    def IsEnabled(self): # pylint: disable-msg=W0221
        return self.__datePicker.IsEnabled()


def styleDP_ALLOWNONEIsBroken():
    # DP_ALLOWNONE is not supported on Mac OS and Linux, and currently 
    # (wxPython 2.8.1), Windows because one can't set the date to None, 
    # despite style=wx.DP_ALLOWNONE:
    return not ('__WXMSW__' in wx.PlatformInfo)


def DatePickerCtrl(*args, **kwargs):
    ''' Factory function that returns _DatePickerCtrlThatFixesAllowNoneStyle 
        when necessary and wx.DatePickerCtrl otherwise. '''

    def styleIncludesDP_ALLOWNONE(style):
        return (style & wx.DP_ALLOWNONE) == wx.DP_ALLOWNONE 

    style = kwargs.get('style', wx.DP_DEFAULT)
    if styleIncludesDP_ALLOWNONE(style) and styleDP_ALLOWNONEIsBroken():
        kwargs['style'] = kwargs['style'] & ~wx.DP_ALLOWNONE
        DatePickerCtrlClass = _DatePickerCtrlThatFixesAllowNoneStyle
    else:
        DatePickerCtrlClass = wx.DatePickerCtrl
    return DatePickerCtrlClass(*args, **kwargs)


def date2wxDateTime(value):
    wxDateTime = wx.DateTime()
    try: # prepare for a value that is not a Python datetime instance
        if value < date.Date():
            wxDateTime.Set(value.day, value.month-1, value.year)
    except (TypeError, AttributeError):
        pass
    return wxDateTime
    

def wxDateTime2Date(wxDateTime):
    if wxDateTime.IsValid():
        return date.Date(wxDateTime.GetYear(), wxDateTime.GetMonth()+1,
            wxDateTime.GetDay())
    else:
        return date.Date()

    
class DateCtrl(Panel):
    def __init__(self, parent, callback=None, noneAllowed=True, *args, 
                 **kwargs):
        self._noneAllowed = noneAllowed
        super(DateCtrl, self).__init__(parent, callback, *args, **kwargs)
        self._callback = callback
        self.Bind(wx.EVT_DATE_CHANGED, self._callback)
        
    def _createControls(self, callback):
        options = dict(style=wx.DP_DROPDOWN, dt=wx.DateTime_Today())
        if self._noneAllowed:
            options['style'] |= wx.DP_ALLOWNONE
        if '__WXMSW__' in wx.PlatformInfo:
            options['size'] = (100, -1)
        elif '__WXGTK__' in wx.PlatformInfo:
            options['size'] = (110, -1)
        return [DatePickerCtrl(self, **options)] # pylint: disable-msg=W0142

    def SetValue(self, value):
        wxDate = date2wxDateTime(value)
        if wxDate.IsValid() or self._noneAllowed:
            self._controls[0].SetValue(wxDate)

    def GetValue(self):
        return wxDateTime2Date(self._controls[0].GetValue())
        

class TimeCtrl(Panel):
    def __init__(self, parent, callback=None, starthour=8, endhour=18, 
                 interval=15, showSeconds=False, *args, **kwargs):
        self._starthour = starthour
        self._endhour = endhour
        self._interval = interval
        self._showSeconds = showSeconds
        super(TimeCtrl, self).__init__(parent, callback, *args, **kwargs)
        
    def SetValue(self, time):
        formattedTime = self._formatTime(date.Now() if time is None else time)
        self._controls[0].SetValue(formattedTime)
    
    def _createControls(self, callback):
        control = combo.ComboCtrl(self, choices=self._choices(), 
                                  size=(100 if self._showSeconds else 75,-1))
        control.Bind(wx.EVT_TEXT, callback)
        control.Bind(wx.EVT_COMBOBOX, callback)
        return [control]
        
    def _choices(self):
        choices = []
        for hour in range(self._starthour, self._endhour):
            for minute in range(0, 60, self._interval):
                choices.append(self._formatTime(date.Time(hour, minute)))
        return choices
    
    def _formatTime(self, time):
        formattedTime = '%02d:%02d'%(time.hour, time.minute)
        if self._showSeconds:
            formattedTime += ':%02d'%time.second
        return formattedTime
        
    def GetValue(self):
        value = self._controls[0].GetValue()
        try:
            timeComponents = [int(component) for component in value.split(':')]
            return date.Time(*timeComponents) # pylint: disable-msg=W0142
        except ValueError:
            return date.Time()            
    
    def Enable(self, enable=True): # pylint: disable-msg=W0221
        self._controls[0].Enable(enable)
        

class DateTimeCtrl(Panel):
    def __init__(self, parent, callback=None, noneAllowed=True,
                 starthour=8, endhour=18, interval=15, showSeconds=False,
                 *args, **kwargs):
        self._noneAllowed = noneAllowed
        self._starthour = starthour
        self._endhour = endhour
        self._interval = interval
        self._showSeconds = showSeconds
        super(DateTimeCtrl, self).__init__(parent, callback, *args, **kwargs)
        self._callback = callback or self.__nullCallback           
        
    def __nullCallback(self, *args, **kwargs):
        pass
        
    def _createControls(self, callback): 
        # pylint: disable-msg=W0201
        self._dateCtrl = DateCtrl(self, self._dateCtrlCallback, 
            self._noneAllowed)
        self._dateCtrl.Bind(wx.EVT_CHECKBOX, self.onEnableDatePicker)
        self._timeCtrl = TimeCtrl(self, self._timeCtrlCallback,
                                  self._starthour, self._endhour, self._interval,
                                  self._showSeconds)
        return [self._dateCtrl, self._timeCtrl]
        
    def onEnableDatePicker(self, event):
        self._timeCtrl.Enable(event.IsChecked())
        self._callback(event)

    def _timeCtrlCallback(self, *args, **kwargs):
        self._callback(*args, **kwargs)
        
    def _dateCtrlCallback(self, *args, **kwargs):
        # If user disables dateCtrl, disable timeCtrl too and vice versa:
        self._timeCtrl.Enable(self._isDateCtrlEnabled())
        self._callback(*args, **kwargs)

    def _isDateCtrlEnabled(self):
        return self._dateCtrl.GetValue() != date.Date()
        
    def SetValue(self, dateTime):
        if dateTime is None:
            datePart = timePart = None
        else:
            datePart = dateTime.date()
            timePart = dateTime.time()
        self._dateCtrl.SetValue(datePart)
        self._timeCtrl.SetValue(timePart)
        self._timeCtrl.Enable(self._isDateCtrlEnabled())
        
    def GetValue(self):
        dateValue = self._dateCtrl.GetValue()
        if dateValue == date.Date():
            return date.DateTime()
        else:
            return date.DateTime.combine(dateValue, self._timeCtrl.GetValue())

    def setCallback(self, callback):
        self._callback = callback
