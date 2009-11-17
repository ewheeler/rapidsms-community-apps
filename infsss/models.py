#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import datetime, date
from locations.models import Location  
from reporters.models import Reporter

#bogus
class LocationStatus(models.Model):
    location   = models.ForeignKey(Location)

    def __unicode__(self): 
        return "%s" % self.location.name
