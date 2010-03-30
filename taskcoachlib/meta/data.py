# -*- coding: utf-8 -*-

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2008-2009 Jérôme Laheurte <fraca7@free.fr>

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

import os, re

try:
    from taskcoachlib.meta.revision import revision # pylint: disable-msg=F0401,W0611
except ImportError:
    revision = 'release'

# Edit these for every release:

# The buildbot sets TCVERSION when building snapshots.
version = os.environ.get('TCVERSION', '1.0.1')
tskversion = 29 # Current version number of the task file format
release_day = '26' # Day number of the release, 1-31, as string
release_month = 'March' # Month of the release in plain English 
release_year = '2010' # Year of the release as string
release_status = 'stable' # One of 'alpha', 'beta', 'stable'

# No editing needed below this line for doing a release.

months = ['January', 'February', 'March', 'April', 'May', 'June', 
          'July', 'August', 'September', 'October', 'November', 'December']
release_month_nr = '%02d'%(months.index(release_month) + 1)
release_day_nr = '%02d'%int(release_day)
date = release_month + ' ' + release_day + ', ' + release_year

name = 'Task Coach'
description = 'Your friendly task manager'
long_description = '%(name)s is a simple open source todo manager to manage' \
' personal tasks and todo lists. It grew out of a frustration that ' \
'well-known task managers, such as those provided with Outlook or Lotus ' \
'Notes, do not provide facilities for composite tasks. Often, tasks and ' \
'other things todo consist of several activities. %(name)s is designed ' \
'to deal with composite tasks. '%dict(name=name)
keywords = 'task manager, todo list, pim, time registration, track effort'
author_first, author_last = 'Frank', 'Niessink' # Needed for PAD file
author = '%s %s and Jerome Laheurte'%(author_first, author_last)
author_unicode = u'%s %s and Jérôme Laheurte'%(author_first, author_last)
author_email = 'developers@taskcoach.org'

filename = name.replace(' ', '')
filename_lower = filename.lower()

url = 'http://www.taskcoach.org/' # Don't remove the trailing slash, other code is assuming it will be there
screenshot = url + 'screenshots/0.71.2-Windows_XP-Tasks_categories_and_effort.png'
icon = url + 'taskcoach.png'
pad = url + 'pad.xml'
version_url = url + 'version.txt'
download = url + 'download.html'
dist_download_prefix = 'http://downloads.sourceforge.net/%s'%filename_lower

announcement_addresses = 'taskcoach@yahoogroups.com, python-announce-list@python.org, johnhaller@portableapps.com'

copyright = 'Copyright (C) 2004-%s %s'%(release_year, author) # pylint: disable-msg=W0622
license_title = 'GNU General Public License'
license_version = '3'
license_title_and_version = '%s version %s'%(license_title, license_version) 
license = '%s or any later version'%license_title_and_version # pylint: disable-msg=W0622
license_title_and_version_abbrev = 'GPLv%s'%license_version
license_abbrev = '%s+'%license_title_and_version_abbrev
license_notice = '''%(name)s is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

%(name)s is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.'''%dict(name=name)

license_notice_html = '<p>%s</p>'%license_notice.replace('\n\n', '</p><p>')
license_notice_html = re.sub(r'<http([^>]*)>', r'<a href="http\1" target="_blank">http\1</a>', license_notice_html)

platform = 'Any'
pythonversion = '2.5'
wxpythonversionnumber = '2.8.9.1'
wxpythonversion = '%s-unicode'%wxpythonversionnumber

languages = {
    'English': None, 
    'Arabic': 'ar',
    'Basque': 'eu',
    'Bosnian': 'bs',
    'Breton': 'br',
    'Bulgarian': 'bg',
    'Catalan': 'ca',
    'Chinese (Simplified)': 'zh_CN',
    'Chinese (Traditional)': 'zh_TW',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Finnish': 'fi',
    'French': 'fr', 
    'Galician': 'gl',
    'German': 'de',
    'German (Low)': 'nds',
    'Greek': 'el',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Indonesian': 'id',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Latvian': 'lv',
    'Lithuanian': 'lt',
    'Marathi': 'mr',
    'Mongolian': 'mn',
    'Norwegian (Bokmal)': 'nb',
    'Norwegian (Nynorsk)': 'nn',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Portuguese (Brazilian)': 'pt_BR',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Slovak': 'sk',
    'Slovene': 'sl',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Telugu': 'te',
    'Thai': 'th',
    'Turkish': 'tr',
    'Ukranian': 'uk',
    'Vietnamese': 'vi'}
languages_list = ','.join(languages.keys())

def __createDict(localsDict):
    ''' Provide the local variables as a dictionary for use in string
        formatting. '''
    metaDict = {} # pylint: disable-msg=W0621
    for key in localsDict:
        if not key.startswith('__'):
            metaDict[key] = localsDict[key]
    return metaDict

metaDict = __createDict(locals())

