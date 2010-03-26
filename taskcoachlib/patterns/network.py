'''
Task Coach - Your friendly task manager
Copyright (C) 2008 Jerome Laheurte <fraca7@free.fr>
Copyright (C) 2009 Frank Niessink <frank@niessink.com>

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

import asynchat, socket


class Acceptor(asynchat.async_chat):
    """Basic Acceptor using asynchat."""

    def __init__(self, handlerFactory, host, port):
        """@param handlerFactory: A callable used to instantiate connection
               handlers. Takes the socket and client address as parameters.
           @param host: Host to bind to.
           @param port: Port to bind to. If None, a free port between 4096
               and 8192 is used."""

        asynchat.async_chat.__init__(self)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if port is None:
            for port in xrange(4096, 8192):
                try:
                    self.bind((host, port))
                except socket.error:
                    pass
                else:
                    break
            else:
                raise RuntimeError, 'Could not find a free port to bind to.'
        else:
            self.bind((host, port))

        self.port = port

        self.listen(5)

        self.handlerFactory = handlerFactory

    def handle_accept(self):
        fp, addr = self.accept()
        self.handlerFactory(fp, addr)
