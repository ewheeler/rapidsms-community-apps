#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from apps.quickforms.models import *

admin.site.register(Form)
admin.site.register(Field)
admin.site.register(FormEntry)
admin.site.register(FieldEntry)
admin.site.register(Keyword)
admin.site.register(Action)
