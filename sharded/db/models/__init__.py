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

from django.db.models import *
from django.db import connections
from sharded.db.models.manager import ShardedManager
from sharded.db.models.fields import Sharded32Field, Sharded64Field, ForeignKey, OneToOneField, OneToOneOrNoneField
from sharded.db.models.query import ShardedQuerySet, ShardedValuesQuerySet, ShardedValuesListQuerySet

class ShardedModelMixin(object):
    def __int__(self):
        return self.id
    
    def cursor(self):
        return connections[self._state.db].cursor()

class Sharded32Model(ShardedModelMixin, Model):
    id = Sharded32Field()
    
    objects = ShardedManager()
    
    class Meta:
        abstract = True

class Sharded64Model(ShardedModelMixin, Model):
    id = Sharded64Field()
    
    objects = ShardedManager()
    
    class Meta:
        abstract = True

ShardedModel = Sharded64Model
