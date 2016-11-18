# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Shard',
            fields=[
                ('id', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('usage', models.BigIntegerField(default=0)),
                ('capacity', models.BigIntegerField(default=0)),
            ],
        ),
    ]
