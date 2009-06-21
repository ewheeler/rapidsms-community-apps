#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from django.core.urlresolvers import reverse

from apps.locations.models import *
from apps.nodegraph.models import NodeSet
from apps.logger.models import IncomingMessage

class Community(NodeSet):
    name = models.CharField(max_length=255,unique=True, blank=False)
    pass

    def __unicode__(self):
        return unicode(self.name)


class Village(NodeSet):
    name = models.CharField(max_length=255,unique=True, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True)
    pass

    def __unicode__(self):
        return unicode(self.name)

#
# 'Statics' as module level
#
def VillagesForContact(contact):
    return contact.get_immediate_ancestors(klass=Village)
    
   
