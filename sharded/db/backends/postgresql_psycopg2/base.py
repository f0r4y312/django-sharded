"""
Copyright 2016 Vimal Aravindashan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import re

from django.db.backends.postgresql_psycopg2.base import *
from django.db.backends.postgresql_psycopg2.base import DatabaseSchemaEditor as PostgresDatabaseSchemaEditor
from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as PostgresDatabaseWrapper

class DatabaseSchemaEditor(PostgresDatabaseSchemaEditor):
    def skip_default(self, field):
        from sharded.db import models
        return isinstance(field, (models.Sharded32Field,models.Sharded64Field))

class DatabaseWrapper(PostgresDatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor
    
    @cached_property
    def shard_id(self):
        from sharded.db import SHARDED_DB_PREFIX
        shard_id = re.match(SHARDED_DB_PREFIX + "(\d{1,3})", self.alias)
        return 0 if not shard_id else int(shard_id.group(1))
