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

from django.db.models import fields
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

#NOTE: Need to inherit from AutoField because django.db.models.base:819
class Sharded32Field(fields.AutoField, fields.IntegerField):
    description = _("Integer with shard id encoded")
    
    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(Sharded32Field, self).__init__(*args, **kwargs)
    
    def db_type_suffix(self, connection):
        return 'DEFAULT next_id32()'
    
    def get_internal_type(self):
        return fields.IntegerField.get_internal_type(self)
    
    def to_python(self, value):
        return fields.IntegerField.to_python(self, value)

class Sharded64Field(fields.AutoField, fields.BigIntegerField):
    description = _("BigInteger with shard id and timestamp encoded")
    
    def __init__(self, *args, **kwargs):
        kwargs['primary_key'] = True
        super(Sharded64Field, self).__init__(*args, **kwargs)
    
    def db_type_suffix(self, connection):
        return 'DEFAULT next_id64()'
    
    def get_internal_type(self):
        return fields.BigIntegerField.get_internal_type(self)
    
    def to_python(self, value):
        return fields.BigIntegerField.to_python(self, value)

#NOTE: Must subclass ForeignKey, OneToOneField and ManyToManyField because django.db.models.fields.related:1981
class ShardedForeignObjectMixin(object):
    def db_type(self, connection):
        rel_field = self.related_field
        if isinstance(rel_field, (Sharded32Field,Sharded64Field)):
            return rel_field.db_type(connection=connection)
        return super(ShardedForeignObjectMixin, self).db_type(connection)

class ForeignKey(ShardedForeignObjectMixin, fields.related.ForeignKey):
    pass

class OneToOneField(ShardedForeignObjectMixin, fields.related.OneToOneField):
    pass

class SingleRelatedObjectDescriptorReturnsNone(fields.related.SingleRelatedObjectDescriptor):
    def __get__(self, instance, instance_type=None):
        try:
            return super(SingleRelatedObjectDescriptorReturnsNone, self).__get__(instance, instance_type=instance_type)
        except ObjectDoesNotExist:
            return None

class OneToOneOrNoneField(OneToOneField):
    related_accessor_class = SingleRelatedObjectDescriptorReturnsNone
