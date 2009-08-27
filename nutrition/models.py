#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import date
from apps.locations.models import Location

#This is not normalized - but there is a max of 500 GMCs so I think its ok  I need  soup dumplings
class Patient(models.Model): 
 	#enums/choices whatever probably not necessary but we will leave for now
	GENDER_TYPES = (
		('M', 'M'),
		('F', 'F'),
	)
	SYSTEM_TYPES = (
		('INFSSS',1),
		('MCHD',2),
		('All',3),
	) #possible expansion for multiple health projects in malawi - not thrilled with solution - the all sort of sucks, csv?
	#do we want to include mother or child/family relation?  or is this obvious from age?  I will leave it out for now not necessary for INFSSS

	#id = models.CharField(max_length=7) #explicit - bec we need to normalize with existing system
	gender = models.CharField(max_length=1,choices=GENDER_TYPES)
	system = models.IntegerField(max_length=1,choices=SYSTEM_TYPES)
	reg_date = models.DateTimeField(auto_now_add=True)
	dob = models.DateTimeField() #this should be calculated on the fly the first time age is entered/patient registered, then we dont have to keep entering age - we can automatically calculate it

    

class INFSSS(models.Model): 
	GENDER_TYPES = (
		('M', 'M'),
		('F', 'F'),
	)

	patient = models.ForeignKey(Patient)
	location = models.ForeignKey(Location)

	 #to do - intelligent data conversion in app layer - decimal are big but i want stats - not have to convert
	height = models.DecimalField(max_digits=3,decimal_places=1) 
	weight = models.DecimalField(max_digits=3,decimal_places=1) 
	muac = models.DecimalField(max_digits=2,decimal_places=2) 
	oedema = models.BooleanField()
	diarrea = models.BooleanField()
	datetime = models.DateTimeField(auto_now_add=True)

        

	def __unicode__(self):
		# these are not all strings  :)
		return "%s %s %s %s %s %s %s %s %s %s %s %s" % \
			(self.patient_id.id, self.gmc_id.id, self.gender, self.age(), self.height, self.weight, self.muac, self.oedima, self.diarreah, self.datetime.month,self.datetime.year, datetime.strftime("%Y-%m-%d %H:%M:%S"))
    
	def malnurished_metric(self):
		return self.height/self.weight * 10 # stanley

	def age(self):
		return (self.datetime - patient.dob).days/30

	def malnurishedLevel(self): 
		return (self.malnurished_metric() >= 70) * 2 + ((self.malnurished_metric() < 70) and (self.malnurished_metric() > 30))* 1

	def isSeverlyMalnurished(self): 
		return (self.malnurished_metric() >= 70)
	
	def header(self): # move to view 
		return "Region District ChildID Sex Age Weight Height MUAC Oedema Diarrhoea GMC DisName Month Year TS"
	

