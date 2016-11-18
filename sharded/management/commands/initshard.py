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

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections
from django.utils import six

#shard_id32: 8-bits seq id MSB, 8-bits shard id, 16-bits seq id LSB
#shard_id64: 40-bits timestamp, 8-bits shard id, 16-bits seq id

class Command(BaseCommand):
    min_epoch_40bit = 1099511627776
    max_cache = 65535
    
    def add_arguments(self, parser):
        parser.add_argument("shard_id", type=int, nargs='?', help="Shard ID to use for the database. Max possible shards is 255.")
        parser.add_argument("--epoch", type=long, default=self.min_epoch_40bit, help="Offset value for custom epoch. Must be greater than or equal to %d to set bit 41 to zero." % self.min_epoch_40bit)
        parser.add_argument("--cache", type=int, default=7, help="The optional clause CACHE for PostgreSQL CREATE SEQUENCE. Defaults to 7.")
        parser.add_argument("--replace", action="store_true", default=False, help="Replace sequences/functions if they exists.")
        parser.add_argument("--database", type=str, default="default", help="Nominates a database to synchronize. Defaults to the \"default\" database.")
    
    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        database = options["database"]
        self.connection = connections[database]
        shard_id = options["shard_id"]
        epoch = options["epoch"]
        cache = options["cache"]
        replace = options["replace"]
        if shard_id is None:
            options["shard_id"] = shard_id = self.connection.shard_id
        if shard_id < 0 or shard_id > 255:
            raise CommandError("shard_id cannot be negative or larger than unsigned 8-bit integer")
        if epoch < self.min_epoch_40bit:
            raise CommandError("epoch cannot be less than %lu" % self.min_epoch_40bit)
        if cache > self.max_cache:
            raise CommandError("sequence cache cannot be greater than %d" % self.max_cache)
        
        init_shard32 = [
            "DROP SEQUENCE IF EXISTS shard_id32_seq;",
            "CREATE SEQUENCE shard_id32_seq MAXVALUE 8388607;",
            "CREATE OR REPLACE FUNCTION next_id32(seq_id int = nextval('shard_id32_seq'::regclass), OUT id int) AS $$ "
            "DECLARE "
            "    shard_id int := %(shard_id)d; "
            "BEGIN "
            "    SELECT ((seq_id & 8323072) << 8) | (shard_id << 16) | (seq_id & 65535) into id; "
            "END; "
            "$$ LANGUAGE PLPGSQL;",
            "CREATE OR REPLACE FUNCTION shard_id32(id int, OUT shard_id int) AS $$ "
            "BEGIN "
            "    SELECT (id >> 16) & 255 INTO shard_id; "
            "END; "
            "$$ LANGUAGE PLPGSQL;",
        ]
        init_shard64 = [
            "DROP SEQUENCE IF EXISTS shard_id64_seq;",
            "CREATE SEQUENCE shard_id64_seq MAXVALUE 65535 CACHE %(cache)d CYCLE;",
            "CREATE OR REPLACE FUNCTION next_id64(ts timestamp with time zone = clock_timestamp(), seq_id bigint = nextval('shard_id64_seq'::regclass), OUT id bigint) AS $$ "
            "DECLARE "
            "    epoch_40bit bigint := %(epoch)lu; "
            "    shard_id int := %(shard_id)d; "
            "BEGIN "
            "    SELECT ((trunc(extract(epoch from ts) * 1000) - epoch_40bit)::bigint << 24) | (shard_id << 16) | (seq_id & 65535) into id; "
            "END; "
            "$$ LANGUAGE PLPGSQL;",
            "CREATE OR REPLACE FUNCTION shard_id64(id bigint, OUT shard_id int) AS $$ "
            "BEGIN "
            "    SELECT (id >> 16) & 255 INTO shard_id; "
            "END; "
            "$$ LANGUAGE PLPGSQL;",
            "CREATE OR REPLACE FUNCTION timestamp_id64(id bigint, OUT ts TIMESTAMP WITH TIME ZONE) AS $$ "
            "DECLARE "
            "    epoch_40bit bigint := %(epoch)lu; "
            "BEGIN "
            "    SELECT TIMESTAMP WITH TIME ZONE 'epoch' + (epoch_40bit + (id >> 24)) * INTERVAL '1 millisecond' INTO ts; "
            "END; "
            "$$ LANGUAGE PLPGSQL;",
        ]
        status = {0:"OK", 1:"EXISTS"}
        for name,init in [('shard_id32',init_shard32), ('shard_id64',init_shard64)]:
            self.stdout.write("Initializing '%s'... " % name, ending='')
            self.stdout.write(status.get(self.init_shard(None if replace else name, init, **options),"FAILED"))
    
    @transaction.atomic
    def init_shard(self, if_exists, init_sql, **kwargs):
        cursor = self.connection.cursor()
        if isinstance(if_exists, six.string_types):
            cursor.execute("SELECT COUNT(*) FROM pg_proc WHERE proname=%s", [if_exists])
            if cursor.fetchone()[0]:
                return 1
            else:
                if_exists = None
        if not if_exists:
            for sql in init_sql:
                sql = sql % kwargs
                if self.verbosity >= 2:
                    self.stdout.write(sql)
                cursor.execute(sql)
                #TODO: check return value of execute/catch db errors and return appropriately
        return 0
