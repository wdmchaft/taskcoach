'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Frank Niessink <frank@niessink.com>

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


def extendedWithAncestors(selection):
    extendedSelection = selection[:]
    for item in selection:
        for ancestor in item.ancestors():
            if ancestor not in extendedSelection:
                extendedSelection.append(ancestor)
    return extendedSelection


class RowBuilder(object):
    def __init__(self, visibleColumns, isTree):
        self.__visibleColumns = visibleColumns
        if isTree:
            self.indent = lambda item: ' ' * len(item.ancestors())
        else:
            self.indent = lambda item: ''
        
    def headerRow(self):
        return [column.header() for column in self.__visibleColumns]
    
    def itemRow(self, item):
        row = [column.render(item) for column in self.__visibleColumns]
        row[0] = self.indent(item) + row[0]
        return row

    def itemRows(self, items):
        return [self.itemRow(item) for item in items]
    
    def rows(self, items):
        return [self.headerRow()] + self.itemRows(items)
    

def viewer2csv(viewer, selectionOnly=False):
    ''' Convert the items displayed by a viewer into a list of rows, where
        each row consists of a list of values. If the viewer is in tree mode, 
        indent the first value (typically the subject of the item) to 
        indicate the depth of the item in the tree. '''
    
    isTree = viewer.isTreeViewer()    
    rowBuilder = RowBuilder(viewer.visibleColumns(), isTree)
    items = viewer.visibleItems()
    if selectionOnly:
        items = [item for item in items if viewer.isselected(item)]
        if isTree:
            items = extendedWithAncestors(items)
    return rowBuilder.rows(items)

