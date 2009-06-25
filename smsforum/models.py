#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models
from apps.locations.models import Location
from apps.nodegraph.models import NodeSet


class Village(NodeSet):
    # security masks
    __SEC_MEMBER_ONLY_SEND=0x01
    __SEC_MODERATED=0x02
    __SEC_UNUSED_1=0x04
    __SEC_UNUSED_2=0x08 

    name = models.CharField(max_length=255,unique=True, blank=False)
    location = models.ForeignKey(Location, null=True, blank=True)

    # Security flags recorded, but not yet enforced
    _security =  models.PositiveSmallIntegerField(default=__SEC_MEMBER_ONLY_SEND)

    # some useful props
    def __get_sec_member_only_send(self):
        return bool(self._security & self.__SEC_MEMBER_ONLY_SEND)

    def __set_sec_member_only_send(self,val):
        if bool(val):
            self._security|=self.__SEC_MEMBER_ONLY_SEND
        else:
            self._security&=~self.__SEC_MEMBER_ONLY_SEND
    sec_member_only_send=property(__get_sec_member_only_send,__set_sec_member_only_send)

    def __get_sec_moderated(self):
        return bool(self._security & self.__SEC_MODERATED)

    def __set_sec_moderated(self,val):
        if bool(val):
            self._security|=self.__SEC_MODERATED
        else:
            self._security&=~self.__SEC_MODERATED
    sec_moderated=property(__get_sec_moderated,__set_sec_moderated)

    def __unicode__(self):
        return unicode(self.name)


class Community(Village):
    pass

#
# 'Statics' as module level
#
def VillagesForContact(contact):
    return contact.get_ancestors(max_alt=1,klass=Village)
    
   
