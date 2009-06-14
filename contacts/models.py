#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

from rapidsms import message,connection
from apps.nodegraph.models import *

# 
# Definition of Contacts (people) and ChannelConnections (ways to contact 
# those people) that depends on nodegraph 
#

#
# Choice constants
#

CHOICE_VALUES={
    'male':'m',
    'female':'f'
}

GENDER_CHOICES=(
    (CHOICE_VALUES['male'], 'male'),
    (CHOICE_VALUES['female'],'female')
)


#    
# reimplementing stuff from Reporters to work with Node classes. 
# bascically this should be agreed on and moved to core
# TODO: harmonize
#
class Contact(Node):
    """
    Represents a person or other contact that can send and recive
    messages to this system.

    Minimum requirement for utility is that one ChannelConnection
    (a way to reach this contact, e.g. a phone number and a modem
    backend) is created with this contact as a ForeignKey

    given_name -- May be multiple names in single string, e.g. "Jeffrey Louis"
    family_name -- May be multiple names in single string, e.g. "Wishnie Edwards"

    That is, it's up to the users of the system to define what goes in those fields.
    But in general *given_name* should identify individuals and *family_name*
    identifies families.

    unique_id -- A uniqued field that can hold a unique id across all Contacts.
    It is not required but useful for storing things that a national id (e.g. SocSec number)

    """
    # channel_connections[] -- via ForeignKey in ChannelConnection
    given_name = models.CharField(max_length=255,blank=True)
    family_name =  models.CharField(max_length=255,blank=True)
    unique_id = models.CharField(max_length=255,unique=True,null=True,blank=True)
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,blank=True) 
    age_months = models.IntegerField(null=True,blank=True)
    # locale via ForeignKey in LocalePreference
    
    """ Permissions for the webUI
    class Meta:
        ordering = ["last_name", "first_name"]

        # define a permission for this app to use the @permission_required
        # decorator in reporter's views
        # in the admin's auth section, we have a group called 'manager' whose
        # users have this permission -- and are able to see this section
        permissions = (
            ("can_view", "Can view"),
        )
    """
    
    def __unicode__(self):
        return self.signature()

    """
    def __json__(self):
    return {
        "pk":         self.pk,
        "identity":   self.identity,
        "first_name": self.first_name,
        "last_name":  self.last_name,
        "str":        unicode(self) }
    """
    
    @property
    def age_years(self):
        if self.age_months is None:
            return None
        return self.age_months*12

    @age_years.setter
    def age_years(self,value):
        self.age_months=value*12

    @property
    def locales(self):
        """Return priority ordered list of locales"""
        pass

    def add_locale(self,locale_str, priority=0):
        """
        Add a locale preference. NO VALIDATION.

        If added at same priority as existing locale, it
        overwrites the existing one.

        """
        pass

    def remove_locale(self,locale_srt):
        """Remove the locale from the list"""
        pass

    def signature(self):
        if len(self.given_name)==0:
            if len(self.family_name)==0:
                connection = ChannelConnection.objects.get(contact=self)
                return ( "%s" % connection.user_identifier )
            return ( "%s" % self.family_name )
        return (("%s %s") % (self.given_name + self.family_name))
    
class Locale(models.Model):
    """
    Holds a 'locale' string in ISO 639.2 form of xxx_CC@variation

    TODO: Read a list in via a text file and make this a choice.
    TODO: Validation and pre-built locales
    """
    locale_string = models.CharField(max_length=20,unique=True)

    class Meta:
        ordering = ('locale_string',)
    

class LocalePreference(models.Model):
    """
    Preference order for a Contact's locales (languages).

    I LOVE the relational model! Two joins just to get an
    ordered list!

    priority -- 0 is highest priority. Only one locale per priority

    """
    priority = models.PositiveSmallIntegerField(default=0,unique=True)
    locale = models.ForeignKey(Locale)
    contact = models.ForeignKey(Contact)

    class Meta:
        unique_together = ('locale','contact')
        ordering = ('priority',)


#basically a PersistentBackend
class CommunicationChannel(models.Model):
    """
    Info to identify backend instances.

    And example of multiple comm-channels would be
    channels to each of several Mobile carriers.

    E.g. a modem communicating with Zain and another to MTN

    """
    slug  = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=255, blank=True)
    

# basically persistent connection
class ChannelConnection(models.Model):
    """
    Maps phone# to communication channel

    """
    user_identifier = models.CharField(max_length=64)
    communication_channel = models.ForeignKey(CommunicationChannel)

    # always associated with a Contact, though contact
    # may be _blank_
    contact = models.ForeignKey(Contact) 

    class Meta:
        unique_together = ('user_id', 'communication_channel')



#
# Module level methods (more or less equiv to Java static methods)
# Read online that this is a cleaner way to do this thatn @classmethod
# or @staticmethod which can have weird calling behavior
#

def CommunicationChannelFromMessage(msg, save=True):
    """
    Create a ChannelConnection object from a Message.

    If 'save' is True, object is saved to DB before 
    returning.

    """

    slug = msg.connection.backend.slug

    cc=CommunicationChannel.objects.get(slug__isexact=slug)
    if cc is None:
        # make one
        cc=CommunicationChannel(slug)
        if save:
            cc.save()

    return cc
    pass


def ContactFromMessage(msg,save=True):
    return ChannelConnectionFromMessage(msg,save).contact


def ChannelConnectionFromMessage(msg,save=True):
    """
    Create, or retrieve, a ChannelConnection from
    a message.

    E.g. Phone# + Service Provider backend

    """
    # Get the comm channel
    comm_c=CommunicationChannelFromMessage(msg)
    u_id=msg.connection.identity

    # try to get an existing ChannelConnection
    chan_con=ChannelConnection.objects.get(user_id__exact=u_id, \
                                               communication_channel__exact=comm_c)

    if chan_con is None:
        # didn't find an existing connection, which means this specific
        # CommunicationChannel (e.g. service provider) and id (e.g. phone number)
        # combo aren't known, so we need a blank Contact for this combo.
        contact=Contact(debug_id=u_id)
        chan_con=ChannelConnection(user_id=u_id,\
                                       communication_channel=comm_c,\
                                       contact=contact)
        if save:
            chan_con.save()

    return chan_con



