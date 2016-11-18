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

from django.conf import settings
from django.db import connections, DEFAULT_DB_ALIAS

SHARDED_DB_PREFIX = getattr(settings, 'SHARDED_DB_PREFIX', 'shard_')

shards = sorted(filter(lambda cnxn: cnxn.startswith(SHARDED_DB_PREFIX), connections))
