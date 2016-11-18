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

from django.core.management.commands import migrate
from django.core.management import call_command
from sharded.db import connections, DEFAULT_DB_ALIAS, shards

class Command(migrate.Command):
    help = "Updates database schema on default DB and shards. Manages both apps with migrations and those without."
    
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("--all-shards", action="store_true", default=False, help="Migrate all the sharded databases.")
        parser.add_argument("--no-initshard", action="store_true", default=False, help="Do not call initshard.")
    
    def handle(self, **options):
        db = options.pop('database')
        migrate_all = options.pop('all_shards')
        no_initshard = options.pop('no_initshard')
        if db == DEFAULT_DB_ALIAS and migrate_all == True:
            cnxns = sorted(shards) + ['default',]
            for cnxn in cnxns:
                self.stdout.write(self.style.MIGRATE_HEADING("Migrating '" + cnxn + "' database"))
                if not no_initshard:
                    call_command('initshard', database=cnxn)
                super(Command, self).handle(database=cnxn, **options)
        else:
            if migrate_all:
                self.stdout.write(self.style.NOTICE("warning: --all-shards is ignored when --database is used."))
            if not no_initshard:
                call_command('initshard', database=db)
            super(Command, self).handle(database=db, **options)
