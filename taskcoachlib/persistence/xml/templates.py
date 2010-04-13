#-*- coding: UTF-8

from taskcoachlib.i18n import _

def getDefaultTemplates():
    templates = []
    templates.append(('dueTomorrow', '<?xml version="1.0" ?><?taskcoach release="0.71.0" tskversion="22"?><tasks><task duedatetmpl="Tomorrow()" startdatetmpl="Today()" status="2" subject="New task due tomorrow"/></tasks>\n'))
    _('New task due tomorrow')
    templates.append(('dueToday', '<?xml version="1.0" ?><?taskcoach release="0.71.0" tskversion="22"?><tasks><task duedatetmpl="Today()" startdatetmpl="Today()" status="2" subject="New task due today"/></tasks>\n'))
    _('New task due today')

    return templates
