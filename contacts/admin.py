#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.contrib import admin
from apps.contacts.models import *

class ContactAdmin(admin.ModelAdmin):
    list_display = ('id','given_name','family_name')

admin.site.register(Contact, ContactAdmin)
