#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from people.models import *

class PersonAdmin(admin.ModelAdmin):
    list_display = ('code', 'date_of_birth', 'gender', 'type', 'created_at')
    ordering = ['created_at']
    date_hierarchy = 'created_at'

admin.site.register(PersonType)
admin.site.register(Person, PersonAdmin)
