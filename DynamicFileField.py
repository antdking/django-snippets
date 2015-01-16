"""
Copyright (C) 2015 Fastboot Mobile, LLC. (http://fastbootmobile.com)

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

============================================================================

DESCRIPTION: For django, this code snippet extends the FileField to allow for 
changing the backend storage at run time on a per file basis.

Created for Fastboot Mobile by: Anthony King <anthonydking@gmail.com>

"""

import os

from django.db.models.fields import files


class _FieldFile(files.FieldFile):
    def __init__(self, instance, field, name):
        super(_FieldFile, self).__init__(instance, field, name)
        if callable(field.runtime_storage):
            self.storage = field.runtime_storage(self.instance)


class _FileDescriptor(files.FileDescriptor):

    def __get__(self, instance=None, owner=None):
        f = super(_FileDescriptor, self).__get__(instance=instance,
                                                 owner=owner)

        # We don't care about other type
        if not isinstance(f, _FieldFile):
            return f

        # This is unlikely to happen since the superclass function
        # does this already, and _FieldFile is an instance of file.FieldFile.
        if not hasattr(f, 'field'):
            f.instance = instance
            f.field = self.field
            f.storage = self.field.storage

        # Now we assign our runtime storage backend. if applicable
        if callable(self.field.runtime_storage):
            f.storage = self.field.runtime_storage(instance)

        return f


class DynamicFileField(files.FileField):

    attr_class = _FieldFile

    descriptor_class = _FileDescriptor

    def __init__(self, verbose_name=None, name=None, upload_to='',
                 storage=None, runtime_storage=None, **kwargs):
        self.runtime_storage = runtime_storage
        super(DynamicFileField, self).__init__(verbose_name, name,
                                               upload_to, storage, **kwargs)

    def get_filename(self, filename, instance=None):
        if callable(self.runtime_storage):
            if instance:
                storage = self.runtime_storage(instance)
                return os.path.normpath(storage.get_valid_name(
                    os.path.basename(filename)))
        return os.path.normpath(self.storage.get_valid_name(
            os.path.basename(filename)))

    def generate_filename(self, instance, filename):
        return os.path.join(self.get_directory_name(),
                            self.get_filename(filename, instance=instance))
