#!/usr/bin/env pytho]
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import datetime, date

from apps.locations.models import Location
from apps.reporters.models import Reporter
from apps.logger.models import *


class PersonBase(models.Model): 
    GENDER_TYPES= (
        ('M','Male'),
        ('F','Female'),
    )
    location     = models.ForeignKey(Location)
    reporter     = models.ForeignKey(Reporter)
    short_id     = models.CharField(max_length=3,default=0)
    gender       = models.CharField(max_length=1, choices=GENDER_TYPES,blank=True,default="")
    dob          = models.DateTimeField(default=datetime.now())
    lastupdated  = models.DateTimeField(default=datetime.now())
    registered   = models.DateTimeField(default=datetime.now())
    active       = models.BooleanField(default=True) 
    

    
    class Meta:
       verbose_name = "Person"

    def __unicode__(self): 
        return "%s" % (self.id) 


    def free_short_ids(self):
       l = 0 
       for i in PersonBase.objects.filter(active=True,location=self.location).order_by('short_id'):
            if i.short_id != l +1 : return i.short_id
            
    def age(self):
        return PersonBase.dob_to_age(self.dob)

    def savesms(self):
        self.lastupdated = datetime.now()
        self.save()
    
    def contact(self):
        try:
            return  PersistantConnection.objects.get(reporter=reporter).identity
        except:
            return ""
    
    #ARE THESE FUNCTIONS NECESSARY
    def fmt_dob(self):
        return self.dob.strftime("%Y-%m-%d %H:%m")

    def fmt_lastupdated(self):
        return self.lastupdated.strftime("%Y-%m-%d %H:%m")

    def fmt_registered(self):
        return self.registered.strftime("%Y-%m-%d %H:%m")

    #is this the correct place for these classes
    @classmethod
    def age_to_dob(cls,age,unit=30):
        return  datetime.now() - timedelta(age * unit)
        
    @classmethod
    def dob_to_age(cls,dob,unit=30):
        return (dob + datetime.now()).days/unit
    

