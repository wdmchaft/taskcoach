#!/usr/bin/env python

"""
Simple desktop window enumeration for Python.

Copyright (C) 2007 Paul Boddie <paul@boddie.org.uk>

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

--------

Finding Open Windows on the Desktop
-----------------------------------

To obtain a list of windows, use the desktop.windows.list function as follows:

windows = desktop.windows.list()

Each window object can be inspected through a number of methods. For example:

name = window.name()
width, height = window.size()
x, y = window.position()
child_windows = window.children()

See the desktop.windows.Window class for more information.
"""

from desktop import _is_x11, _get_x11_vars, _readfrom, use_desktop

def _xwininfo(s):
    d = {}
    for line in s.split("\n"):
        fields = line.split(":")
        if len(fields) < 2:
            continue
        key, values = fields[0].strip(), fields[1:]
        d[key] = values
    return d

def _get_int_properties(d, properties):
    results = []
    for property in properties:
        results.append(int(d[property][0].strip()))
    return results

# Window classes.
# NOTE: X11 is the only supported desktop so far.

class Window:

    "A window on the desktop."

    def __init__(self, identifier):

        "Initialise the window with the given 'identifier'."

        self.identifier = identifier

    def __repr__(self):
        return "Window(%r)" % self.identifier

    def children(self):

        "Return a list of windows which are children of this window."

        s = _readfrom(_get_x11_vars() + "xwininfo -id %s -children" % self.identifier, shell=1)
        handles = []
        adding = 0
        for line in s.split("\n"):
            if not adding and line.endswith("children:"):
                adding = 1
            elif adding and line:
                handles.append(line.strip().split()[0])
        return [Window(handle) for handle in handles]

    def name(self):

        "Return the name of the window."

        s = _readfrom(_get_x11_vars() + "xwininfo -id %s -stats" % self.identifier, shell=1)
        for line in s.split("\n"):
            if line.startswith("xwininfo:"):

                # Format is 'xwininfo: Window id: <handle> "<name>"

                fields = line.split(":")
                handle_and_name = fields[2].strip()
                fields2 = handle_and_name.split(" ")

                # Get the "<name>" part, stripping off the quotes.

                return " ".join(fields2[1:]).strip('"')

        return None

    def size(self):

        "Return a tuple containing the width and height of this window."

        s = _readfrom(_get_x11_vars() + "xwininfo -id %s -stats" % self.identifier, shell=1)
        d = _xwininfo(s)
        return _get_int_properties(d, ["Width", "Height"])

    def position(self):

        "Return a tuple containing the upper left co-ordinates of this window."

        s = _readfrom(_get_x11_vars() + "xwininfo -id %s -stats" % self.identifier, shell=1)
        d = _xwininfo(s)
        return _get_int_properties(d, ["Absolute upper-left X", "Absolute upper-left Y"])

def list(desktop=None):

    """
    Return a list of windows for the current desktop. If the optional 'desktop'
    parameter is specified then attempt to use that particular desktop
    environment's mechanisms to look for windows.
    """

    # NOTE: The desktop parameter is currently ignored and X11 is tested for
    # NOTE: directly.

    if _is_x11():
        s = _readfrom(_get_x11_vars() + "xlsclients -a -l", shell=1)
        prefix = "Window "
        prefix_end = len(prefix)
        handles = []

        for line in s.split("\n"):
            if line.startswith(prefix):
                handles.append(line[prefix_end:-1]) # NOTE: Assume ":" at end.
    else:
        raise OSError, "Desktop '%s' not supported" % use_desktop(desktop)

    return [Window(handle) for handle in handles]

# vim: tabstop=4 expandtab shiftwidth=4
