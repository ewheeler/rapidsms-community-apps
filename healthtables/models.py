#!/usr/bin/env pytho]
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import datetime, date


class GenericTableType(models.Model):
    name = models.CharField(max_length=10)

class GenericTable(models.Model):
    parent = models.ForeignKey(GenericTableType)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=100)

class WastingTable(models.Model): 
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
        return "%1.2f-%s" % (self.height,self.id) #fix to correct formatting

class StuntingTable(models.Model): 
    age       = models.DecimalField(max_digits=4,decimal_places=1) 
    height    = models.DecimalField(max_digits=5,decimal_places=2) 
    gender    = models.CharField(max_length=1) 
    
    class Meta:
        verbose_name = "Stunting"
        
    def __unicode__(self):
        return "age %s, height %s, gender %s" % (self.age,self.height,self.gender)

