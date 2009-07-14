#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime
from django.db import models, transaction
from apps.locations.models import Location
from apps.nodegraph.models import NodeSet, Node
from apps.contacts.models import Contact

class Village(NodeSet):
    # security masks
    __SEC_BLAST_MEMBER_ONLY = 0x01
    __SEC_BLAST_MODERATED = 0x02
    __SEC_BLAST_PWD_PROTECTED = 0x04
    __SEC_JOIN_MODERATED = 0x08 
    __SEC_JOIN_PWD_PROTECTED = 0x10 
    __SEC_ADMIN_CMDS_PWD_PROTECTED = 0x20

    name = models.CharField(max_length=255, blank=False, unique=True, \
                                verbose_name="Village Name")
    location = models.ForeignKey(Location, null=True, blank=True)
    # Security flags recorded, but not yet enforced
    _security = models.PositiveSmallIntegerField(\
        default=__SEC_BLAST_MEMBER_ONLY | __SEC_ADMIN_CMDS_PWD_PROTECTED)
    _join_cmd_pwd = models.CharField(max_length=10, default='0000')
    _admin_cmds_pwd = models.CharField(max_length=10, default='1212')

    def __unicode__(self):
        return unicode(self.name)
    
    @transaction.commit_on_success
    def add_member(self, person):
        person.add_to_parent(self)
        MembershipLog(nodeset=self, node=person, action='C').save()

    @transaction.commit_on_success
    def remove_member(self, person):
        person.remove_from_parent(self)
        MembershipLog(nodeset=self, node=person, action='D').save()
    
    ##############
    # properties #
    ##############
    
    def __get_sec_blast_member_only(self):
        return bool(self._security & self.__SEC_BLAST_MEMBER_ONLY)

    def __set_sec_blast_member_only(self, val):
        if bool(val):
            self._security |= self.__SEC_BLAST_MEMBER_ONLY
        else:
            self._security &= ~self.__SEC_BLAST_MEMBER_ONLY
    sec_blast_member_only = property(__get_sec_blast_member_only, \
                                      __set_sec_blast_member_only)

    def __get_sec_blast_moderated(self):
        return bool(self._security & self.__SEC_BLAST_MODERATED)

    def __set_sec_blast_moderated(self, val):
        if bool(val):
            self._security |= self.__SEC_BLAST_MODERATED
        else:
            self._security &= ~self.__SEC_BLAST_MODERATED
    sec_blast_moderated = property(__get_sec_blast_moderated, \
                               __set_sec_blast_moderated)

    def __get_sec_blast_pwd_protected(self):
        return bool(self._security & self.__SEC_BLAST_PWD_PROTECTED)

    def __set_sec_blast_pwd_protected(self, val):
        if bool(val):
            self._security |= self.__SEC_BLAST_PWD_PROTECTED
        else:
            self._security &= ~self.__SEC_BLAST_PWD_PROTECTED
    sec_pwd_protect_blast = property(__get_sec_blast_pwd_protected, \
                               __set_sec_blast_pwd_protected)

    def __get_sec_join_moderated(self):
        return bool(self._security & self.__SEC_BLAST_PWD_PROTECTED)

    def __set_sec_join_moderated(self, val):
        if bool(val):
            self._security |= self.__SEC_JOIN_MODERATED
        else:
            self._security &= ~self.__SEC_JOIN_MODERATED
    sec_pwd_protect_blast = property(__get_sec_join_moderated, \
                               __set_sec_join_moderated)

    def __get_sec_join_pwd_protected(self):
        return bool(self._security & self.__SEC_BLAST_PWD_PROTECTED)

    def __set_sec_join_pwd_protected(self, val):
        if bool(val):
            self._security |= self.__SEC_JOIN_PWD_PROTECTED
        else:
            self._security &= ~self.__SEC_JOIN_PWD_PROTECTED
    sec_pwd_protect_blast = property(__get_sec_join_pwd_protected, \
                               __set_sec_join_pwd_protected)

    def __get_sec_admin_cmds_pwd_protected(self):
        return bool(self._security & self.__SEC_BLAST_PWD_PROTECTED)

    def __set_sec_admin_cmds_pwd_protected(self, val):
        if bool(val):
            self._security |= self.__SEC_ADMIN_CMDS_PWD_PROTECTED
        else:
            self._security &= ~self.__SEC_ADMIN_CMDS_PWD_PROTECTED
    sec_pwd_protect_blast = property(__get_sec_admin_cmds_pwd_protected, \
                               __set_sec_admin_cmds_pwd_protected)

'''
class VillageName(models.Model):
    name = models.CharField(max_length=255, blank=False)
    primary = models.BooleanField(default=False)
    village = models.ForeignKey(Village, related_name='names')

    class Meta:
        unique_together = ('village', 'name')
'''

class Community(Village):
    pass

#
# 'Statics' as module level
#
def villages_for_contact(contact):
    return contact.get_ancestors(max_alt=1, klass=Village)
    
# we don't currently log 'updates'
# but maybe one day we'll want to...
ACTION = (
    ('C', 'Create'),
    ('U', 'Update'),
    ('D', 'Delete'),
)

class MembershipLog(models.Model):
    date = models.DateTimeField(null=False, default = datetime.now )
    nodeset = models.ForeignKey(NodeSet,null=True, related_name='parent') #can reference a deleted nodeset
    node = models.ForeignKey(Node,null=True, related_name='child') #can reference a deleted node
    action = models.CharField(max_length=1, choices=ACTION, null=False)