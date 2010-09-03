# -*- coding: utf-8 -*-

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

from taskcoachlib.i18n import _
from taskcoachlib.domain import attachment
import base


class NewAttachmentCommand(base.NewItemCommand):
    singular_name = _('New attachment')
    
    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', _('New attachment'))
        description = kwargs.pop('description', '')
        location = kwargs.pop('location', '')
        super(NewAttachmentCommand, self).__init__(*args, **kwargs)
        self.items = self.attachments = self.createNewAttachments(subject=subject,
                          description=description, location=location)

    def createNewAttachments(self, **kwargs):
        return [attachment.FileAttachment(**kwargs)]


class EditAttachmentCommand(base.EditCommand):
    plural_name = _('Edit attachments')
    singular_name = _('Edit attachment "%s"')
    
    def __init__(self, *args, **kwargs):
        super(EditAttachmentCommand, self).__init__(*args, **kwargs)
        self.attachments = self.items

    def getItemsToSave(self):
        return self.items


class DeleteAttachmentCommand(base.DeleteCommand):
    plural_name = _('Delete attachments')
    singular_name = _('Delete attachment "%s"')


class AddAttachmentNoteCommand(base.AddNoteCommand):
    plural_name = _('Add note to attachments')
