==============
Django Sharded
==============

Django Sharded adds ShardedModel, related fields, querysets, managers and
a shard-aware database router to quickly get started with sharded databases.

You can start with one shard and add more shards later. A maximum of 255 shards are supported.

`sharded.db.models` is a drop-in replacement for `django.db.models` to help avoid import clutter.

At the moment, this package has been designed and tested to work only with PostgreSQL.

Quick start
-----------

1. Add `sharded` as the first entry to your `INSTALLED_APPS` setting::

    INSTALLED_APPS = [
        'sharded',
        ...
    ]

2. Run `python manage.py migrate` to add `sharded.Shard` model to `default` database

3. [OPTIONAL] Set a value for `SHARDED_DB_PREFIX`. Default prefix is `shard\_`::

    SHARDED_DB_PREFIX = 'shard_'

4. Add `sharded.db.routers.ShardedRouter` to `DATABASE_ROUTERS` setting::

    DATABASE_ROUTERS = ['sharded.db.routers.ShardedRouter',]

5. Setup all available shards::

    #NOTE: Django Sharded accesses each shard using the name format '%s%03d' % (SHARDED_DB_PREFIX, n)
    DATABASES['shard_001'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'shard',
        'USER': 'prjdbuser',
        'PASSWORD': 'supersecretpassword',
        'HOST': 'host.for.shard-001.com',
        'PORT': '5432',
    }
    DATABASES['shard_002'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'shard_002',
        'USER': 'prjdbuser',
        'PASSWORD': 'supersecretpassword',
        'HOST': 'host.for.shard-002.com',
        'PORT': '5432',
    }
    DATABASES['shard_003'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'shard_003',
        'USER': 'prjdbuser',
        'PASSWORD': 'supersecretpassword',
        'HOST': 'host.for.shard-002.com',
        'PORT': '5432',
    }
    DATABASES['shard_004'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'shard',
        'USER': 'prjdbuser',
        'PASSWORD': 'supersecretpassword',
        'HOST': 'host.for.shard-004.com',
        'PORT': '5432',
    }
    
    #NOTE: If you use 'dj-database-url' or 'django-connection-url' (shameless self-plug),
    #      you can simplify the above using env vars like DATABASE_SHARD_nnn_URL
    import connection_url
    for shard in xrange(1,256):
        shard = '%s%03d' % ('shard_', shard) #TODO: Use SHARDED_DB_PREFIX if you've customized it above
        shard_env = 'DATABASE_' + shard.upper() + '_URL'
        if shard_env not in os.environ:
            break
        DATABASES.setdefault(shard, connection_url.config(shard_env))

6. Run `python manage.py initshard <1..255>` with optional parameters to initialize the shard

7. Run `python manage.py updateshard <1..255> --capacity <in_bytes>` to keep track of available capacity in the shard

8. Use `ShardedModel` as base for models that require sharding. Related models will automatically be included in the same shard and the ForeignKey field will also automatically use a big integer column::

    from sharded.db import models
    from sharded.models import Shard
    
    class HelloManager(models.ShardedManager):
        use_for_related_fields = True
    
        def create(self, **kwargs):
            if not self._db:
                self._db = str(Shard.objects.most_free_shard())
            return super(HelloManager, self).create(**kwargs)

    class Hello(models.ShardedModel):
        a_random_field = models.IntegerField()
        
        objects = HelloManager()
    
    class Foo(models.Model):
        hello = models.ForeignKey(Hello)
    
    class Bar(models.Model):
        hello = models.OneToOneField(Hello)
    
    class Baz(models.ShardedModel):
        hello = models.ForeignKey(Hello)
    
    class Herp(models.Model): #Unsharded model
        derp = models.CharField(max_length=8)

9. Run `python manage.py makemigrations` and then, `python manage.py migrate --all` to apply migrations across all shards

10. Add a cronjob to run `python manage.py updateshard` to update shard usage levels at regular intervals
