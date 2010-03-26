'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2008 Frank Niessink <frank@niessink.com>

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

# Module for metaclasses that are not widely recognized patterns.

class NumberedInstances(type):
    ''' A metaclass that numbers class instances. Use by defining the metaclass 
        of a class NumberedInstances, e.g.: 
        class Numbered:
            __metaclass__ = NumberedInstances 
        Each instance of class Numbered will have an attribute instanceNumber
        that is unique. '''
        
    count = dict()
        
    def __call__(class_, *args, **kwargs):
        kwargs['instanceNumber'] = NumberedInstances.count.setdefault(class_, 0)
        instance = super(NumberedInstances, class_).__call__(*args, **kwargs)
        NumberedInstances.count[class_] += 1
        return instance
    
