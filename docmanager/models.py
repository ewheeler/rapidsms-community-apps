#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.contrib.auth import models as auth_models
from django.core.exceptions import ObjectDoesNotExist 
from datetime import datetime, date

#Add a document manager class that pegs docs with projects - although later

class TextBlock(models.Model): 
    name  = models.CharField(max_length=10)
    title = models.CharField(max_length=100) #should be choices
    text  = models.TextField()

    def __unicode__(self): 
        return "%s %s" % (self.name,self.title)

class File(models.Model):
    file = models.FileField(upload_to="./")
    title = models.CharField(max_length=100) #description maybe rename yoda
    
    def __unicode__(self): 
        return "%s" % (self.title)
