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

from django.apps import apps
from django.utils import six
from django.db.models.fields.related import RelatedField, ForeignObjectRel
from sharded.db import models, SHARDED_DB_PREFIX
from sharded.exceptions import ShardCouldNotBeDetermined

class ShardedRouter(object):
    def __init__(self):
        self.sharded_tables = set()
        len_sharded_tables = -1
        while len_sharded_tables != len(self.sharded_tables):
            len_sharded_tables = len(self.sharded_tables)
            for model in filter(lambda m: m._meta.db_table not in self.sharded_tables, apps.get_models(include_auto_created=True, include_deferred=True)):
                for field in model._meta.get_fields(include_hidden=True):
                    if isinstance(field, (models.Sharded32Field,models.Sharded64Field)) or \
                    (isinstance(field, (RelatedField,ForeignObjectRel)) and \
                    (isinstance(field.related_model, six.string_types)==False and field.related_model._meta.db_table in self.sharded_tables)):
                        self.sharded_tables.add(model._meta.db_table)
    
    def db_for_read(self, model, **hints):
        if model._meta.db_table in self.sharded_tables:
            pk = model._meta.pk.name
            obj = hints.get('instance', None)
            if obj:
                if obj._state.db:
                    return obj._state.db
                else:
                    shard_id = getattr(obj, pk, None) or hints.get(pk, None)
            else:
                shard_id = hints.get(pk, None)
            if not shard_id:
                shards = set([int(hint) for hint in hints.values() if isinstance(hint, (models.Sharded32Model,models.Sharded64Model))])
                num_shards = len(shards)
                if num_shards == 1:
                    shard_id = shards.pop()
                elif num_shards > 1:
                    raise ShardCouldNotBeDetermined('Multiple possible shards for "%s.%s" model -- identified %s!' % (model._meta.app_label, model._meta.model_name, num_shards))
            if not shard_id:
                raise ShardCouldNotBeDetermined('Could not determine shard for "%s.%s" model' % (model._meta.app_label, model._meta.model_name))
            return SHARDED_DB_PREFIX + ('%03d' % ((long(shard_id) >> 16) & 255))
        return None
    
    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)
    
    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.db_table in self.sharded_tables and obj2._meta.db_table in self.sharded_tables:
            return True
        return None
