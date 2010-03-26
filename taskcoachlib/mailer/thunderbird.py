'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2009 Jerome Laheurte <fraca7@free.fr>

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

import os, stat, re, imaplib, ConfigParser, wx
from taskcoachlib.i18n import _
from taskcoachlib import persistence


_RX_MAILBOX = re.compile('mailbox-message://(.*)@(.*)/(.*)#(\d+)')
_RX_IMAP    = re.compile('imap-message://([^@]+)@([^/]+)/(.*)#(\d+)')


def unquote(s):
    """Converts %nn sequences into corresponding characters. I
    couldn't find anything in the standard library to do this, but I
    probably didn't search hard enough."""

    rx = re.compile('%([0-9a-fA-F][0-9a-fA-F])')
    mt = rx.search(s)
    while mt:
        s = s[:mt.start(1) - 1] + chr(int(mt.group(1), 16)) + s[mt.end(1):]
        mt = rx.search(s)

    return s


def loadPreferences():
    """Reads Thunderbird's prefs.js file and return a dictionnary of
    configuration options."""

    config = {}

    def user_pref(key, value):
        config[key] = value

    for line in file(os.path.join(getDefaultProfileDir(), 'prefs.js'), 'r'):
        if line.startswith('user_pref('):
            # pylint: disable-msg=W0122
            exec line in { 'user_pref': user_pref, 'true': True, 'false': False }

    return config


def getThunderbirdDir():
    path = None

    if '__WXMAC__' in wx.PlatformInfo:
        path = os.path.join(os.environ['HOME'], 'Library', 'Thunderbird')
    elif os.name == 'posix':
        path = os.path.join(os.environ['HOME'], '.thunderbird')
        if not os.path.exists(path):
            path = os.path.join(os.environ['HOME'], '.mozilla-thunderbird')
    elif os.name == 'nt':
        if os.environ.has_key('APPDATA'):
            path = os.path.join(os.environ['APPDATA'], 'Thunderbird')
        elif os.environ.has_key('USERPROFILE'):
            path = os.path.join(os.environ['USERPROFILE'], 'Application Data', 'Thunderbird')
    else:
        raise EnvironmentError('Unsupported platform: %s' % os.name)

    if path is None:
        raise RuntimeError, 'Could not find Thunderbird data dir'

    return path

_PORTABLECACHE = None

def getDefaultProfileDir():
    """Returns Thunderbird's default profile directory"""

    global _PORTABLECACHE # pylint: disable-msg=W0603

    path = getThunderbirdDir()

    # Thunderbird Portable does not have a profiles.ini file, only one
    # profile. And there's only one way to know where it
    # is... Hackish.

    if os.name == 'nt' and not os.path.exists(path):
        if _PORTABLECACHE is not None:
            return _PORTABLECACHE

        from taskcoachlib.thirdparty import wmi

        for process in wmi.WMI().Win32_Process():
            if process.ExecutablePath.lower().endswith('thunderbirdportable.exe'):
                _PORTABLECACHE = os.path.join(os.path.split(process.ExecutablePath)[0], 'Data', 'profile')
                break
        else:
            raise RuntimeError, 'Could not find Thunderbird profile.'

        return _PORTABLECACHE

    parser = ConfigParser.RawConfigParser()
    parser.read([os.path.join(path, 'profiles.ini')])

    for section in parser.sections():
        if parser.has_option(section, 'Default') and int(parser.get(section, 'Default')):
            if int(parser.get(section, 'IsRelative')):
                return os.path.join(path, parser.get(section, 'Path'))
            return parser.get(section, 'Path')

    for section in parser.sections():
        if parser.get(section, 'Name') == 'default':
            if int(parser.get(section, 'IsRelative')):
                return os.path.join(path, parser.get(section, 'Path'))
            return parser.get(section, 'Path')

    raise ValueError('No default section in profiles.ini')


class ThunderbirdMailboxReader(object):
    """Extracts an e-mail from a Thunderbird file. Behaves like a
    stream object to read this e-mail."""

    def __init__(self, url):
        """url is the internal reference to the mail, as collected
        through drag-n-drop."""

        mt = _RX_MAILBOX.search(url)
        if mt is None:
            raise RuntimeError(_('Malformed Thunderbird internal ID: %s. Please file a bug report.') % url)

        self.url = url

        # The url has the form
        # mailbox-message://<username>@<hostname>//<filename>#<id>. Or
        # so I hope.

        config = loadPreferences()

        self.user = unquote(mt.group(1))
        self.server = unquote(mt.group(2))
        self.path = unquote(mt.group(3)).split('/')
        self.offset = long(mt.group(4))

        for i in xrange(200):
            base = 'mail.server.server%d' % i
            if config.has_key('%s.userName' % base):
                if config['%s.userName' % base] == self.user and config['%s.hostname' % base] == self.server:
                    self.filename = os.path.join(config['%s.directory' % base], *tuple(self.path))
                    break
        else:
            raise RuntimeError(_('Could not find directory for ID %s. Please file a bug report.') % url)

        self.fp = file(self.filename, 'rb')
        self.fp.seek(self.offset)

        self.done = False

    def read(self):
        """Buffer-like read() method"""

        if self.done:
            return ''

        lines = []

        # In theory, the message ends with a single dot. As always, in
        # theory, theory is like practice but in practice...

        starting = True

        for line in self.fp:
            if not starting:
                if line.startswith('From '):
                    break
            lines.append(line)
            starting = False

        self.done = True
        return ''.join(lines)

    def __iter__(self):
        class Iterator(object):
            def __init__(self, fp):
                self.fp = fp

            def __iter__(self):
                return self

            def next(self):
                line = self.fp.readline()
                if line.strip() == '.':
                    raise StopIteration
                return line

        return Iterator(self.fp)

    def saveToFile(self, fp):
        fp.write(self.read())


class ThunderbirdImapReader(object):
    _PASSWORDS = {}

    def __init__(self, url):
        mt = _RX_IMAP.search(url)

        self.url = url

        self.user = unquote(mt.group(1))
        self.server = mt.group(2) 
        self.box = mt.group(3)
        self.uid = int(mt.group(4))

        config = loadPreferences()

        port = None
        stype = None
        isSecure = False
        # We iterate over a maximum of 100 mailservers. You'd think that
        # mailservers would be numbered consecutively, but apparently
        # that is not always the case, so we cannot assume that because
        # serverX does not exist, serverX+1 won't either. 
        for serverIndex in range(100): 
            name = 'mail.server.server%d' % serverIndex
            if config.has_key(name + '.hostname') and \
               config[name + '.hostname'] == self.server and \
               config[name + '.type'] == 'imap':
                if config.has_key(name + '.port'):
                    port = int(config[name + '.port'])
                if config.has_key(name + '.socketType'):
                    stype = config[name + '.socketType']
                if config.has_key(name + '.isSecure'):
                    isSecure = int(config[name + '.isSecure'])
                break

        self.ssl = bool(stype == 3 or isSecure)
        # When dragging mail from Thunderbird that uses Gmail via IMAP the
        # server reported is imap.google.com, but for a direct connection we
        # need to connect with imap.gmail.com:
        self.server = 'imap.gmail.com' if self.server == 'imap.google.com' else self.server 
        self.port = port or {True: 993, False: 143}[self.ssl]

    def _getMail(self):
        if self.ssl:
            cn = imaplib.IMAP4_SSL(self.server, self.port)
        else:
            cn = imaplib.IMAP4(self.server, self.port)

        if self._PASSWORDS.has_key((self.server, self.user, self.port)):
            pwd = self._PASSWORDS[(self.server, self.user, self.port)]
        else:
            pwd = wx.GetPasswordFromUser(_('Please enter password for user %(user)s on %(server)s:%(port)d') % \
                                         dict(user=self.user, server=self.server, port=self.port))
            if pwd == '':
                raise ValueError('User canceled')

        while True:
            try:
                response, params = cn.login(self.user, pwd)
            except cn.error, e:
                response = 'KO'
                errmsg, = e.args

            if response == 'OK':
                break

            pwd = wx.GetPasswordFromUser(_('Login failed (%s). Please try again.') % errmsg)
            if pwd == '':
                raise ValueError('User canceled')

        self._PASSWORDS[(self.server, self.user, self.port)] = pwd

        response, params = cn.select(self.box)

        if response != 'OK':
            raise ValueError('Could not select inbox %s' % self.box)

        response, params = cn.uid('FETCH', str(self.uid), '(RFC822)')

        if response != 'OK':
            raise ValueError('No such mail: %d' % self.uid)

        return params[0][1]

    def saveToFile(self, fp):
        fp.write(self._getMail())

#==============================================================================


def getMail(id_):
    if id_.startswith('mailbox-message://'):
        reader = ThunderbirdMailboxReader(id_)
    elif id_.startswith('imap-message://'):
        reader = ThunderbirdImapReader(id_)
    else:
        raise TypeError('Not supported: %s' % id_)

    filename = persistence.get_temp_file(suffix='.eml')
    reader.saveToFile(file(filename, 'wb'))

    if os.name == 'nt':
        os.chmod(filename, stat.S_IREAD)

    return filename
