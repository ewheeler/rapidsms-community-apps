#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from apps.harvard.models import *

admin.site.register(HarvardReporter)
admin.site.register(StudyParticipant)
admin.site.register(HarvardReport)
