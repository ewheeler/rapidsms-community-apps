#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import date
from apps.locations.models import Location, ReporterLocation 
from apps.reporter.models import Reporter


class Nutrition(models.Model): 

	patient   = models.ForeignKey(Reporter)
	reporter  = models.ForeignKey(ReporterLocation)
	height    = models.DecimalField(max_digits=3,decimal_places=1) 
	weight    = models.DecimalField(max_digits=3,decimal_places=1) 
	muac      = models.DecimalField(max_digits=2,decimal_places=2) 
	oedema    = models.BooleanField()
	diarrea   = models.BooleanField()
	ts        = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		# these are not all strings  :)
		return "%s %s %s %s %s %s %s %s %s %s %s %s" % \
			(self.patient.alias, self.reporter.reporter.id, self.reporter.location.title, self.patient.gender, self.age(), self.height, self.weight, self.muac, self.oedima, self.diarreah, self.alertself.ts.month,self.ts.year, ts.strftime("%Y-%m-%d %H:%M:%S"))
   
	def alertLevel(self):
		metric = weight/height #check stanley
		return (metriic >= 70) * 2 + ((metric < 70) and (metric  > 30))* 1

	def age(self):
		return (self.datetime - self.patient.dob).days/30

