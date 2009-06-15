#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.core.urlresolvers import reverse

from apps.locations.models import *
from apps.nodegraph.models import NodeSet

#
# NEW STYLE COMMUNITIES/VILLAGES
#

class Community(NodeSet):
    name = models.CharField(max_length=255,unique=True, blank=False)
    pass


class Village(NodeSet):
    name = models.CharField(max_length=255,unique=True, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True)
    pass

#
# 'Statics' as module level
#
def VillagesForContact(contact):
    return contact.get_immediate_ancestors(klass=Village)
    
   
