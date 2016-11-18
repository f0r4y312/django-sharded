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

from django.core.management.base import BaseCommand
from django.db import connections
from sharded import models

class Command(BaseCommand):
    shard_model = models.Shard
    
    def add_arguments(self, parser):
        parser.add_argument("shard_id", type=int, nargs='*', help="Shard ID(s) to update usage data.")
        parser.add_argument("--capacity", type=long, help="Capacity for all or specified shards in bytes.")
    
    def handle(self, *args, **options):
        verbosity = options["verbosity"]
        shard_ids = options.get("shard_id", None)
        capacity = options.get("capacity", None)
        for cnxn in connections.all():
            if cnxn.shard_id:
                self.shard_model.objects.get_or_create(id=cnxn.shard_id)
        shards = self.shard_model.objects.filter(id__in=shard_ids) if shard_ids else self.shard_model.objects.all()
        #NOTE: sliently skips over shards not found in database
        for shard in shards:
            alias = str(shard)
            if verbosity:
                print '%s:' % alias,
            cnxn = connections[alias]
            datname = cnxn.get_connection_params()['database']
            if verbosity:
                print 'datname=%s' % datname,
            cursor = cnxn.cursor()
            cursor.execute("SELECT pg_catalog.pg_database_size(pgdb.datname) FROM pg_catalog.pg_database pgdb WHERE datname=%s", [datname])
            updated_fields = []
            usage = cursor.fetchone()[0]
            if shard.usage != usage:
                shard.usage = usage
                updated_fields.append('usage')
            if capacity is not None:
                shard.capacity = capacity
                updated_fields.append('capacity')
            if updated_fields:
                shard.save(update_fields=updated_fields)
            if verbosity:
                print 'usage=%d' % shard.usage,
                print 'capacity=%d' % shard.capacity
