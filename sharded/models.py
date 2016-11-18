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

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from sharded.db import SHARDED_DB_PREFIX

class ShardManager(models.Manager):
    def most_free_shard(self):
        return self.annotate(free=models.F('capacity') - models.F('usage')).order_by('free','id').first()

@python_2_unicode_compatible
class Shard(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    usage = models.BigIntegerField(default=0)
    capacity = models.BigIntegerField(default=0)
    
    objects = ShardManager()
    
    def __str__(self):
        return SHARDED_DB_PREFIX + ("%03d" % self.id)
