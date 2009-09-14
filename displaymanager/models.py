#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from itertools import groupby

from django.db import models
from django.core.urlresolvers import reverse

#The HeaderDisplay contains a list of fields/functions to display
#This should probably go in webUI
#Slightly wonky - but will improve later
class HeaderDisplay(models.Model): 
     klass  = models.CharField(max_length=100,blank=True) 
     title  = models.TextField(blank=True) 
     func   = models.CharField(max_length=100,blank=True)
     display   = models.CharField(max_length=100,blank=True)
     link   = models.CharField(max_length=100,default="")
     view  = models.CharField(max_length=100,blank=True,default="") 
     order  = models.IntegerField(max_length=3,default=0)
     params   = models.CharField(max_length=100,default="")
    
     filterorder   = models.CharField(max_length=100,default="id")
     annotate   = models.CharField(max_length=100,default="")
     aggregate   = models.CharField(max_length=100,default="")
     filter      = models.CharField(max_length=100,default="")
     Q      = models.CharField(max_length=100,default="")
     exclude   = models.CharField(max_length=100,default="")

     def __unicode__(self): 
        return self.title

     @classmethod
     def by_klass_view(cls,klass,view):
        return  HeaderDisplay.objects.filter(klass=klass,view=view).order_by("id") #order
     
     @classmethod
     def by_view(cls,view):
        return  HeaderDisplay.objects.filter(view=view).exclude(klass="FLOW").order_by("id") #order, flow except bogu
     
     @classmethod
     def get_section(cls,view):
        try:
            vals =  HeaderDisplay.objects.filter(view=view.upper()+"_SECTIONS")[0]
            return vals
        except:
            return ""
     
     @classmethod
     def next_flow(cls,klass,view):
        try:
            vals =[l.title for l in HeaderDisplay.by_klass_view("FLOW",view)]
            try:
                return vals.pop()
            except:
                return vals    
        except:
            return ""
