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

import wx, os, re, tempfile
from taskcoachlib.thirdparty import desktop, chardet
from taskcoachlib.i18n import _
from macmail import getSubjectOfMail
import urllib


def readMail(filename, readContent=True):
    subject = None
    content = ''
    encoding = None
    s = 0
    rx = re.compile('charset=([-0-9a-zA-Z]+)')

    for line in file(filename, 'r'):
        if s == 0:
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()
            if line.strip() == '':
                if not readContent:
                    break
                s = 1
            mt = rx.search(line)
            if mt:
                encoding = mt.group(1)
        elif s == 1:
            content += line

    if encoding is None:
        # Don't try to guess every time. When there are many e-mails
        # with big attachments, it may take *very* long.

        try:
            encoding = wx.Locale_GetSystemEncodingName()
            if not encoding:
                # This happens on Mac OS...
                encoding = 'UTF-8'
            content.decode(encoding)
        except UnicodeError:
            encoding = chardet.detect(content)['encoding']

    subject = _('Untitled e-mail') if subject is None else subject.decode(encoding)
    content = content.decode(encoding)
    return subject, content

def openMailWithOutlook(filename):
    id_ = None
    for line in file(filename, 'r'):
        if line.startswith('X-Outlook-ID:'):
            id_ = line[13:].strip()
            break
        elif line.strip() == '':
            break

    if id_ is None:
        return False

    from win32com.client import GetActiveObject
    app = GetActiveObject('Outlook.Application')
    app.ActiveExplorer().Session.GetItemFromID(id_).Display()

    return True

def openMail(filename):
    if os.name == 'nt':
        # Find out if Outlook is the so-called 'default' mailer.
        import _winreg
        key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                              r'mailto\shell\open\command')
        try:
            value, type_ = _winreg.QueryValueEx(key, '')
            if type_ in [_winreg.REG_SZ, _winreg.REG_EXPAND_SZ]:
                if 'outlook.exe' in value.lower():
                    try:
                        if openMailWithOutlook(filename):
                            return
                    except:
                        pass
        finally:
            _winreg.CloseKey(key)

    desktop.open(filename)

def writeMail(to, subject, body, open=desktop.open):
    def unicode_quote(s):
        # This is like urllib.quote but leaves out Unicode characters,
        # which urllib.quote does not support.
        chars = [c if ord(c) >= 128 else urllib.quote(c) for c in s]
        return ''.join(chars)

    # FIXME: Very  strange things happen on  MacOS X. If  there is one
    # non-ASCII character in the body, it works. If there is more than
    # one, it fails.  Maybe we should use Mail.app  directly ? What if
    # the user uses something else ?

    open(u'mailto:%s?subject=%s&body=%s' % (to, unicode_quote(subject),
                                                unicode_quote(body)))
