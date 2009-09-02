#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import django
from django.contrib import admin
import follow.models

for m in django.db.models.loading.get_models(follow.models):
    admin.site.register(m)
