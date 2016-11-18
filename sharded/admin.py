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

from django.contrib import admin
from django.contrib.admin.utils import get_limit_choices_to_from_path
from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from sharded import models

class ShardedFieldListFilter(admin.AllValuesFieldListFilter):
    model = None
    
    def __init__(self, field, request, params, model, model_admin, field_path):
        if self.model is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'model'." % self.__class__.__name__)
        super(ShardedFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        
        limit_choices_to = get_limit_choices_to_from_path(model, field_path)
        queryset = self.model.objects.filter(limit_choices_to)
        self.lookup_choices = [(obj.pk, str(obj)) for obj in queryset.distinct().order_by('pk')]
    
    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None and not self.lookup_val_isnull,
            'query_string': cl.get_query_string({},
                [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for pk_val, val in self.lookup_choices:
            yield {
                'selected': self.lookup_val == smart_text(pk_val),
                'query_string': cl.get_query_string({
                    self.lookup_kwarg: pk_val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }

class ShardAdmin(admin.ModelAdmin):
    list_display = ('id', 'usage', 'capacity')

admin.site.register(models.Shard, ShardAdmin)
