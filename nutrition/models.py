#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import datetime, date
from apps.locations.models import Location  
from apps.reporters.models import Reporter
from apps.logger.models import *

   
   

#This should go someplace else 
class Person(models.Model):
    P_TYPES=(
        ("Child","Child"),
        ("HSA","HSA"),
    )

    location    = models.ForeignKey(Location)
    reporter    = models.ForeignKey(Reporter)
    lastupdated = models.DateTimeField(auto_now_add=True)
    type        = models.CharField(max_length=10,choices=P_TYPES,default="Child") #bogus
    errors      = models.IntegerField(max_length=5,default=0) # this is an HSA field
    active      = models.BooleanField(default=True) #check this in view 

    def __unicode__(self): 
        #h = dict(P_TYPES)
        if self.type == "": self.type = "Child" #I dont think I need this anymore
        return "%s %s %s" % (self.type,self.reporter.id,self.location.name)
   
    def district(self):
        return self.location.parent

    def gmc(self):
        return self.location.name

    def gender(self):
        return self.reporter.gender
    
    def age(self):
        dob  = self.reporter.dob.strftime("%Y%m%d")
        last  = self.lastupdated.strftime("%Y%m%d")

        dob = datetime(int(dob[0:4]),int(dob[4:6]),1)
        last = datetime(int(last[0:4]),int(last[4:6]),int(last[6:8]))
        #dobs are wrong   in json
        return (last - dob).days/30

	def contact(self):
		return "to implement" #self.lastupdated.strftime("%Y-%m-%d %H:%m")


    #oops just saw this -patient only this should be its own class 
    def lastreport(self):
        return [n for n in Nutrition.objects.filter(patient=self.id).order_by("lastupdated")].pop()  
        #use django call i forget it
    
    def status(self):
        nutrition = self.lastreport()
        return nutrition.report() 

    def dateregistered(self):
        nutrition = self.lastreport()
        return nutrition.ts.strftime("%Y-%m-%d %H:%m")

	def contact(self):
		return self.lastupdated.strftime("%Y-%m-%d %H:%m")

    def smsmsgs(self):
		return sum([ 1 for i in IncomingMessage.objects.filter(alias=self.id)]) #what is the django count command again
         

    @classmethod #Again BOGUS hack
    def childheader(cls):
        return ["District","GMC","Id","Age","Gender","Status", "Last Report","Date Registered","Contact"] #should be reflected
    @classmethod
    def header(cls):
        return ["District","GMC","Id","Age","Gender", "SMS Msgs", "Errors","Contact"] #should be reflected



#Perhaps these tables should be a different type of model
class WastingTable(models.Model): 
    WASTING_TYPES = (
        ("None",1),
        ("Moderate",2),
        ("Severe",3),
    )
    height        = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_100    = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_85     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_80     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_75     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_70     = models.DecimalField(max_digits=4,decimal_places=1) 
    weight_60     = models.DecimalField(max_digits=4,decimal_places=1) 
    
    class Meta:
        verbose_name = "Wasting"

    def __unicode__(self): 
        return "%f-%s" % (self.height,self.id) #fix to correct formatting

    def wastingLevel(self,w):
        #alerts - 3 severe, 2 moderate, 1, nome
        if w <= weight_70: return 3
        if w <= weight_80: return 2
        return 1
        
class StuntingTable(models.Model): 
    age       = models.DecimalField(max_digits=4,decimal_places=1) 
    height    = models.DecimalField(max_digits=5,decimal_places=2) 
    gender    = models.CharField(max_length=1) 
    
    class Meta:
        verbose_name = "Stunting"
        
        #return "%s %s %s" % (self.age,self.height,self.gender)
    
    def __unicode__(self):
        return "age %s, height %s, gender %s" % (self.age,self.height,self.gender)

    def isStunted(self,h):
        return h <= height

class Nutrition(models.Model): 
    QUALITY_TYPES=(
        ("None",1),
        ("Clean",2),
        ("Error",3),
    )

    reporter  = models.ForeignKey(Person,null=True)
    patient   = models.ForeignKey(Person)
    height    = models.DecimalField(max_digits=4,decimal_places=1,null=True) 
    weight    = models.DecimalField(max_digits=4,decimal_places=1,null=True) 
    muac      = models.DecimalField(max_digits=4,decimal_places=2,null=True) 
    oedema    = models.BooleanField()
    diarrea   = models.BooleanField()
    ts        = models.DateTimeField(auto_now_add=True)
    quality   = models.IntegerField(max_length=1,choices=QUALITY_TYPES,default=1)

    class Meta:
        verbose_name = "Nutrition"

    def __unicode__(self):
        return "%s - %s" % (self.ts.strftime("%Y-%m-%d"), self.patient.id)
   
	def alertLevel(self):
		pass 


    #for reflection
    def received(self):
        return "%s" % (self.ts.strftime("%Y-%m-%d %H:%m"))

    def district(self): 
        return self.patient.location.parent
    
    def gmc(self): 
        return self.patient.location.name

    def reporter(self): 
        return self.reporter.reporter.id #phone number - ask adam how to get this

    def child(self): 
        return self.patient.id

    def dataquality(self): #rename quality - the train of being
        return dict(QUALITY_TYPES).keys()[self.quality-1]

    # should these go in view
    def isStunting(self):
        try: 
            stunting = StuntingTable.objects.filter(gender=self.patient.reporter.gender,age=self.patient.age())
        #crap improve
            for s in stunting:
                return self.height < s
        except:
            return False

    def isMalnurished(self):
        try:
            malnurished = WastingTable.objects.get(height=self.height)
            if self.weight <= malnurished.weight_70 : return "severe"
            if self.weight <= malnurished.weight_80 : return "moderate"
        except:
            return "" #log 
        return ""
        
    def report(self):
        malnutrition = self.isMalnurished() 
        if '' != malnutrition: malnutrition += " malnutrition"
        stunting = not(self.isStunting()) * " and stunting "
        return "%s%s" % (malnutrition,stunting,)
        
    @classmethod
    def header(cls):
        return ["District","GMC","Reporter","Child","Weight","Height","MUAC","Oedema","Diarrea","Quality","Received"] #should be reflection 
        
        
