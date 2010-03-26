'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2009 Frank Niessink <frank@niessink.com>
Copyright (C) 2007-2008 Jerome Laheurte <fraca7@free.fr>

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

import os, stat, tempfile
from taskcoachlib import persistence


if os.name == 'nt':
    from win32com.client import GetActiveObject

    def getCurrentSelection():
        obj = GetActiveObject('Outlook.Application')
        exp = obj.ActiveExplorer()
        sel = exp.Selection

        ret = []
        for n in xrange(1, sel.Count + 1):
            src = tempfile.NamedTemporaryFile(suffix='.eml') # Will be deleted automagically
            src.close()
            sel.Item(n).SaveAs(src.name, 0)
            src = file(src.name, 'rb')

            # Okay. In the case of HTML mails, Outlook doesn't put
            # a blank line between the last header line and the
            # body. This assumes that the last header is
            # Subject:. Hope it's true.

            # States:
            # 0       still in headers
            # 1       subject: header seen, blank line not written
            # 2       all headers seen, blank line written
            # 2       in body

            name = persistence.get_temp_file(suffix='.eml')
            dst = file(name, 'wb')
            try:
                s = 0
                for line in src:
                    if s == 0:
                        dst.write(line)
                        if line.lower().startswith('subject:'):
                            dst.write('X-Outlook-ID: %s\r\n' % str(sel.Item(n).EntryID))
                            s = 1
                    elif s == 1:
                        dst.write('\r\n')
                        if line.strip() != '':
                            dst.write(line)
                        s = 2
                    else:
                        dst.write(line)
            finally:
                dst.close()
                if os.name == 'nt':
                    os.chmod(name, stat.S_IREAD)
            ret.append(name)

        return ret
