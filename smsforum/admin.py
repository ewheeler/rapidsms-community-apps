#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.contrib import admin
from apps.smsforum.models import *
from apps.contacts.models import Contact

class VillageAdmin(admin.ModelAdmin):
    def number_of_members(self, vil):
        return str(len(vil.flatten()))

    def members(self, vil):
        return ', '.join([m.get_signature() for m in vil.flatten(klass=Contact)])

    list_display = ('name', 'number_of_members', 'members')
   
    fields = ('name', '_children', 'location')
   
admin.site.register(Village, VillageAdmin)
