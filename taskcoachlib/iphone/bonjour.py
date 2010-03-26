'''
Task Coach - Your friendly task manager
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

from taskcoachlib.thirdparty import pybonjour
import select, threading

class BonjourServiceRegister(object):
    def __init__(self, settings, port):
        super(BonjourServiceRegister, self).__init__()

        self.name = settings.get('iphone', 'service')
        self.__stopped = False

        # This ID is registered, see http://www.dns-sd.org/ServiceTypes.html

        sdRef = pybonjour.DNSServiceRegister(name=self.name or None,
                                             regtype='_taskcoachsync._tcp',
                                             port=port,
                                             callBack=self.__registerCallback)

        self.__thread = threading.Thread(target=self.__run, args=(sdRef,))
        self.__thread.start()

    def __registerCallback(self, sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            self.name = name
        else:
            # Should do something...
            pass

    def __run(self, sdRef):
        try:
            while not self.__stopped:
                ready = select.select([sdRef], [], [], 1.0)
                if sdRef in ready[0]:
                    pybonjour.DNSServiceProcessResult(sdRef)
        except Exception, e:
            pass # XXXTODO

    def stop(self):
        self.__stopped = True
        self.__thread.join()
