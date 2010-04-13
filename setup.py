#!/usr/bin/env python

'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>
Copyright (C) 2008-2009 Jerome Laheurte <fraca7@free.fr>

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

import platform, os
from distutils.core import setup
from taskcoachlib import meta

# Import this here so that py2exe and py2app can find the _pysyncml module:
try:
    import taskcoachlib.syncml.core
    executable = '/usr/bin/python2.5' # We only have pysyncml for python 2.5
except ImportError:
    executable = None # No need to force a specific python version
    print 'WARNING: SyncML is not supported on your platform.'


def findPackages(base):
    result = [base.replace('/', '.')]

    for name in os.listdir(base):
        fname = os.path.join(base, name)
        if os.path.isdir(fname) and \
               os.path.exists(os.path.join(fname, '__init__.py')):
            result.extend(findPackages(fname))

    return result


setupOptions = { 
    'name': meta.filename,
    'author': meta.author,
    'author_email': meta.author_email,
    'description': meta.description,
    'long_description': meta.long_description,
    'version': meta.version,
    'url': meta.url,
    'license': meta.license,
    'download_url': meta.download,
    'packages': findPackages('taskcoachlib') + findPackages('buildlib'),
    'scripts': ['taskcoach.py'],
    'classifiers': [\
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Office/Business :: Scheduling']}

if executable:
    # Force a specific Python version if necessary:
    setupOptions['options'] =  dict(build=dict(executable=executable))

# Add available translations:
languages = sorted(meta.data.languages.keys())
for language in languages:
    setupOptions['classifiers'].append('Natural Language :: %s'%language)

# Add data files for Debian-based systems:
current_dist = [dist.lower() for dist in platform.dist()]
if 'debian' in current_dist or 'ubuntu' in current_dist:
    setupOptions['data_files'] = [\
        ('share/applications', ['build.in/fedora/taskcoach.desktop']), 
        ('share/pixmaps', ['icons.in/taskcoach.png'])]

system = platform.system()
if system == 'Linux':
    setupOptions['package_data'] = {'taskcoachlib': ['bin.in/linux/_pysyncml.so']}
elif system == 'Windows':
    setupOptions['scripts'].append('taskcoach.pyw')
else:
    # When packaging for MacOS, choose the right binary depending on
    # the platform word size. Actually, we're always packaging on 32
    # bits.
    import sys, struct
    if struct.calcsize('L') == 4:
        sys.path.insert(0, os.path.join('taskcoachlib', 'bin.in', 'macos', 'IA32'))
        sys.path.insert(0, os.path.join('extension', 'macos', 'bin-ia32'))
    else:
        sys.path.insert(0, os.path.join('taskcoachlib', 'bin.in', 'macos', 'IA64'))
        sys.path.insert(0, os.path.join('extension', 'macos', 'bin-ia32'))
    import _growl
    import _growlImage
    import _powermgt

if __name__ == '__main__':
    setup(**setupOptions)
