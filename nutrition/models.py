#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import date
from apps.locations.models import Location  
from apps.reporters.models import Reporter

#This should go someplace else 
class LocationReporter(models.Model):
    location   = models.ForeignKey(Reporter)
    reporter   = models.ForeignKey(Location)

#Perhaps these tables should be a different type of model
class WastingTable(models.Model): 
    WASTING_TYPES = (
        (1, "None"),
        (2, "Moderate"),
        (3, "Severe"),
    )
    height        = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_100    = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_85     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_80     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_75     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_70     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_60     = models.DecimalField(max_digits=4,decimal_places=1) 

    def __unicode__(self): 
        return "%s %s %s %s %s %s %s" % (height,weight_100,weight_85, weight_80,weight_75, weight_70, weight_60)

    def wastingLevel(self,w):
        #alerts - 3 severe, 2 moderate, 1, nome
        if w <= weight_70: return 3
        if w <= weight_80: return 2
        return 1
        
class StuntingTable(models.Model): 
    age       = models.DecimalField(max_digits=4,decimal_places=1) 
    height    = models.DecimalField(max_digits=5,decimal_places=2) 
    gender    = models.CharField(max_length=1) 
    
    def __unicode__(self): 
        return "%s %s %s" % (age,height,gender)
    
    def isStunted(self,h):
        return h <= height

class Nutrition(models.Model): 
    QUALITY_TYPES=(
        ("None",1),
        ("Clean",2),
        ("Error",3),
    )

    reporter  = models.ForeignKey(LocationReporter,null=True)
    patient   = models.ForeignKey(Reporter)
    location  = models.ForeignKey(Location) #redundant but in specs (why cant I a have 2 foreign keys of the same type 
    height    = models.DecimalField(max_digits=4,decimal_places=1,blank=True) 
    weight    = models.DecimalField(max_digits=4,decimal_places=1,blank=True) 
    muac      = models.DecimalField(max_digits=4,decimal_places=2,blank=True) 
    oedema    = models.BooleanField()
    diarrea   = models.BooleanField()
    ts        = models.DateTimeField(auto_now_add=True)
    quality   = models.IntegerField(max_length=1,choices=QUALITY_TYPES,default=1)

    def __unicode__(self):
		# these are not all strings  :)
        return "%s %s %s %s %s %s %s %s %s %s %s %s" % \
			(self.patient.alias, self.reporter.reporter.id, self.reporter.location.title, self.patient.gender, self.age(), self.height, self.weight, self.muac, self.oedima, self.diarreah, self.alertself.ts.month,self.ts.year, ts.strftime("%Y-%m-%d %H:%M:%S"))
   
	def alertLevel(self):
		metric = weight/height #check stanley
		return (metriic >= 70) * 2 + ((metric < 70) and (metric  > 30))* 1

	def age(self):
		return (self.datetime - self.patient.dob).days/30

