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

''' render.py - functions to render various objects, like date, time, 
etc. ''' # pylint: disable-msg=W0105

import locale, codecs
from taskcoachlib.i18n import _
from taskcoachlib.domain import date as datemodule
 
# pylint: disable-msg=W0621

def priority(priority):
    ''' Render an (integer) priority '''
    return str(priority)
    
def timeLeft(timeLeft, completedTask):
    if completedTask:
        return ''
    if timeLeft == datemodule.TimeDelta.max:
        return _('Infinite')
    sign = '-' if timeLeft.days < 0 else ''
    timeLeft = abs(timeLeft)
    if timeLeft.days > 0:
        days = _('%d days')%timeLeft.days if timeLeft.days > 1 else _('1 day')
        days += ', '
    else:
        days = '' 
    hours_and_minutes = ':'.join(str(timeLeft).split(':')[:-1]).split(', ')[-1]
    return sign + days + hours_and_minutes

def timeSpent(timeSpent):
    ''' render time spent (of type date.TimeDelta) as
    "<hours>:<minutes>:<seconds>" '''
    if timeSpent == datemodule.TimeDelta():
        return ''
    if timeSpent < datemodule.TimeDelta():
        sign = '-'
    else:
        sign = ''
    return sign + '%d:%02d:%02d'%timeSpent.hoursMinutesSeconds()

def recurrence(recurrence):
    if not recurrence:
        return ''
    if recurrence.amount > 2:
        labels = [_('Every %(frequency)d days'), _('Every %(frequency)d weeks'),
                  _('Every %(frequency)d months'), _('Every %(frequency)d years')] 
    elif recurrence.amount == 2:
        labels = [_('Every other day'), _('Every other week'),
                  _('Every other month'), _('Every other year')]
    else:
        labels = [_('Daily'), _('Weekly'), _('Monthly'), _('Yearly')] 
    mapping = dict(zip(['daily', 'weekly', 'monthly', 'yearly'], labels))
    return mapping.get(recurrence.unit, recurrence.amount)%dict(frequency=recurrence.amount)

def budget(aBudget):
    ''' render budget (of type date.TimeDelta) as
    "<hours>:<minutes>:<seconds>". '''
    return timeSpent(aBudget)

try:
    dateFormat = '%x' # Apparently, this may produce invalid utf-8 so test
    codecs.utf_8_decode(datemodule.Now().strftime(dateFormat))
except UnicodeDecodeError:
    dateFormat = '%Y-%m-%d'
timeFormat = '%H:%M' # Alas, %X includes seconds
dateTimeFormat = ' '.join([dateFormat, timeFormat])

def date(date): 
    ''' render a date (of type date.Date) '''
    if str(date) == '':
        return ''
    return date.strftime(dateFormat)   
        
def dateTime(dateTime):
    if not dateTime or dateTime == datemodule.DateTime():
        return ''
    timeIsMidnight = (dateTime.hour, dateTime.minute) in ((0, 0), (23, 59))
    format = dateFormat if timeIsMidnight else dateTimeFormat
    return dateTime.strftime(format)

def dateTimePeriod(start, stop):
    if stop is None:
        return '%s - %s'%(dateTime(start), _('now'))
    elif start.date() == stop.date():
        return '%s %s - %s'%(date(start.date()), time(start), time(stop))
    else:
        return '%s - %s'%(dateTime(start), dateTime(stop))
            
def time(dateTime):
    return dateTime.strftime(timeFormat)
    
def month(dateTime):
    return dateTime.strftime('%Y %B')
    
def weekNumber(dateTime):
    # Would have liked to use dateTime.strftime('%Y-%U'), but the week number 
    # is one off in 2004
    return '%d-%d'%(dateTime.year, dateTime.weeknumber())
    
def monetaryAmount(aFloat):
    ''' Render a monetary amount, using the user's locale. '''
    return '' if round(aFloat, 2) == 0 else \
        locale.format('%.2f', aFloat, monetary=True)
        
def percentage(aFloat):
    ''' Render a percentage. '''
    return '' if round(aFloat, 0) == 0 else '%.0f%%'%aFloat

def exception(exception, instance):
    ''' Safely render an exception, being prepared for new exceptions. '''

    try:
        # In this order. Python 2.6 fixed the unicode exception problem.
        return unicode(instance)
    except UnicodeEncodeError:
        return '<class %s>' % str(exception)
