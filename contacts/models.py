#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime,timedelta

from django.db import models
from rapidsms.message import Message
from rapidsms.connection import Connection
from apps.nodegraph.models import *

# 
# Definition of Contacts (people) and ChannelConnections (ways to contact 
# those people) that depends on nodegraph 
#

#
# Module Constants
#

class quota_type():
    SEND='send'
    RECEIVE='receive'

class permission_type():
    SEND='send'
    RECEIVE='receive'
    IGNORE='ignore'

CHOICE_VALUES={
    'male':'m',
    'female':'f'
}

GENDER_CHOICES=(
    (CHOICE_VALUES['male'], 'male'),
    (CHOICE_VALUES['female'],'female')
)


class QuotaException(Exception):
    """
    Exception for going over a send or receive quote

    """

    def __init__(self,message='',type=quota_type.SEND,period_remain=None):
        self.message=message
        self.type=type
        self.remain=period_remain
        self.ts=datetime.utcnow()
        
    def __unicode__(self):
        msg=u'%s(%s): %s at %s' % (self.__class__.__name__,self.type,str(self.ts))
        if self.period_remain is not None:
            msg+=u'. %d minutes in quota period' % (self.remain.days*86400 + self.remain.seconds)
        return msg

class PermissionException(Exception):
    """
    Exception for going over a send or receive permissions

    """
    def __init__(self,message='',type=permission_type.SEND):
        self.message=message
        self.type=type
        
    def __unicode__(self):
        return u'%s: user does not have %s permission.' % (self.__class__.__name__,self.type)
    

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

    national_id -- A uniqued field that can hold a unique id across all Contacts.
    It is not required but useful for storing things that a national id (e.g. SocSec number)

    """

    # permission masks
    __PERM_RECEIVE=0x01
    __PERM_SEND=0x02
    __PERM_IGNORE=0x04

    #
    # Table columns
    #

    # when Contact was first created (not modifiable, Django sets this)
    first_seen = models.DateTimeField(auto_now_add=True)

    # First name, or names, e.g. 'Jeffrey Louis'
    given_name = models.CharField(max_length=255,blank=True)

    # Last name, or names, e.g. Wishnie Luk
    family_name = models.CharField(max_length=255,blank=True)

    # How the Contact wants to be addressed in the context
    # of sending and receiving messages, e.g. Jeff W.
    common_name = models.CharField(max_length=255,blank=True)

    # a unique (but nullable field) that can be used for any
    # gloabbly unique info for the Contact. E.g. a National ID
    # where availble, or a system username
    unique_id = models.CharField(max_length=255,unique=True,null=True,blank=True)

    # 'm' or 'f'
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,blank=True) 

    # store age in months in case you want to track people under 1yr old
    # or older people in more detail. The property 'age_years' lets
    # you retrieve and store this in years
    age_months = models.IntegerField(null=True,blank=True)

    # User's prefered locale, in v2 3-letter style (e.g. 'eng'=='en')
    _locale = models.CharField(max_length=10,null=True,blank=True)

    # channel_connections[] -- is available via ForeignKey in ChannelConnection
    
    # Permissions and  Quota
    # ----------------------
    # There are 3 permissions stored in a bit mask. Properties on the 
    # contact object give simple 'perm_XXX' access to setting and reading these.
    # you shouldn't have to muck with '_permissions' directly.
    #
    # The permissions are:
    # - 'CAN_RECEIVE' -- contact can receive messages sent by RapidSMS
    # - 'CAN_SEND' -- contact can send messages to RapidSMS (ok, we
    #                 can't really stop them from sending, but we _can_
    #                 reject them when received)
    # - 'IGNORE' -- Ignore should be interpreted by Apps as 'ignore this contact
    #               entirely'. E.g. if a Contact has IGNORE, just return False
    #               from 'App.handle' and do not respond.
    #
    # There are two quotas: Send and Receive, interpreted just like the 
    # permissions. They are expressed as '# messages/N-minutes (period)'
    # If 'period' is 0, it is interpreted as unlimited and '# messages is ignored'
    #
    # Permissions are global and can restrict access to RapidSMS beyond the 
    # quotas. E.g. a user with quota to receive messages but without the 'can send'
    # permission is not allowed to send messages to the system.
    #
    _permissions = models.PositiveSmallIntegerField(default=__PERM_RECEIVE | __PERM_SEND)

    # TODO --normalize into a quota sub-table with 'send' and 'receive' entries?
    # worth it if we come up with more quota types, but won't worry about for now
    _quota_send_max = models.PositiveSmallIntegerField(default=0)
    _quota_send_period = models.PositiveSmallIntegerField(default=0)
    _quota_send_period_begin = models.DateTimeField(null=True,blank=True)
    _quota_send_seen = models.PositiveSmallIntegerField(default=0) # num messages seen in current period
    _quota_receive_max = models.PositiveSmallIntegerField(default=0)
    _quota_receive_period = models.PositiveSmallIntegerField(default=0)
    _quota_receive_quota_period_begin = models.DateTimeField(null=True,blank=True)
    _quota_receive_seen = models.PositiveSmallIntegerField(default=0) # num messages seen in current period

    
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
        return unicode(self.signature)

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
    def locale(self):
        return self._locale

    @locale.setter
    def locale(self,val):
        if val is None:
            raise("Locale can't be None!")
        self._locale=val
        self.save()

    #
    # Use the following to make sure quotas are enforced!!
    #
    def send_to(self,text,com_channel=None):
        """
        Send a message to the Contact.

        - com_channel -- if this is a specific communication_channel, 
        send on this channel only. Iif it is None, send on ALL channels. 
        If it is the token 'preferred', send on the preferred channel only
        
        NOTE: Preferred is not currently implemented!
        
        """
        if not self.under_quota_receive:
            # NOTE: to be strict we'd check this in the loop
            # but for efficiency we'll count all messages sent on all
            # channels as one message against the quota.
            #
            # When we need something more complicated than this,
            # quotas will need to move to CommunicationChannel so that
            # e.g. we can have 1 quota for SMS and another for Email
            raise QuotaException('User over send quota',quota_type.SEND)

        connections=[]
        if com_channel is not None:
            connections.append(com_channel)
        else:
            connections=self.channel_connections.all()

        try:
            for conn in connections:
                comm_chan=conn.communication_channel
                self._quota_receive_seen+=1
                Message(conn.connection, text).send()
        finally:
            self.save()

    def sent_message_accepted(self,msg):
        """
        Let the system know that RapidSMS accepted a message
        sent by the Contact, and increment their 'send' quota

        """
        if not self.under_quota_send:
            raise QuotaException('User over receive quota',quota_type.SEND)

        self._quota_send_seen+=1
        self.save()

    @property
    def age_years(self):
        if self.age_months is None:
            return None
        return self.age_months*12

    @age_years.setter
    def age_years(self,value):
        self.age_months=value*12

    @property
    def can_receive(self):
        """
        Returns a _SINGLE_ 'True/False' representing
        
        Both permissions and quota_type. 

        E.g. True if-and-only-if user has both send
        permission and quota_type.

        """
        return self.perm_receive and self.under_quota_receive

    @property
    def can_send(self):
        """
        Returns a _SINGLE_ 'True/False' representing
        
        Both permissions and quota_type. 

        E.g. True if-and-only-if user has both send
        permission and quota_type.

        """
        return self.perm_send and self.under_quota_send


    @property
    def perm_receive(self):
        return bool(self._permissions & self.__PERM_RECEIVE)

    @perm_receive.setter
    def perm_receive(self,val):
        if bool(val):
            self._permissions|=self.__PERM_RECEIVE
        else:
            self._permissions&=~self.__PERM_RECEIVE

    @property
    def perm_send(self):
        """
        Returns state of 'send' permission, regardless
        of quota_type.

        """
        return bool(self._permissions & self.__PERM_SEND)

    @perm_send.setter
    def perm_send(self,val):
        if bool(val):
            self._permissions|=self.__PERM_SEND
        else:
            self._permissions&=~self.__PERM_SEND

    @property
    def perm_ignore(self):
        return bool(self._permissions & self.__PERM_IGNORE)

    @perm_ignore.setter
    def perm_ignore(self,val):
        if bool(val):
            self._permissions|=self.__PERM_IGNORE
        else:
            self._permissions&=~self.__PERM_IGNORE

    # quota manipulators
    def __check_quota_period(self, type=quota_type.SEND):
        """
        Checks to see if quota period has expired and resets
        quota levels if it has.

        returns: True if the quota period was reset and False otherwise
                 (including the case where there is no quota set)
        
        """
        remain=self.__quota_period_remain(type)
        
        if remain is not None and \
                abs(remain) != remain:
            # we have a quota, and are beyond time period, and should
            # reset the period
            setattr(self,'_quota_%s_period_begin' % type, datetime.utcnow())
            setattr(self, '_quota_%s_seen' % type, 0)
            self.save()
            return True
        else:
            return False

    def set_quota(self, type=quota_type.SEND, max=15, \
                      period=timedelta(seconds=15*60)):
        """
        Set's quota and resets current period and count.

        """
        setattr(self,'_quota_%s_max' % type,max)
        setattr(self,'_quota_%s_period' % type,period)
        setattr(self,'_quota_%s_period_begin' % type, None)
        setattr(self,'_quota_%s_seen' % type, 0)

    @property
    def quota_send(self):
        """
        returns a tuple of (max, period)

        """
        return (self._quota_send_max,self._quota_send_priod)

    @quota_send.setter
    def quota_send(self,val):
        """
        Takes a tupe (int: max, timedelta: period)
        or None to turn off quota
        
        """
        if val is None:
            self.set_quota_send(quota_type.SEND,period=0)
        else:
            self.set_quota(quota_type.SEND,val[0],val[1])

    @property
    def quota_receive(self):
        """
        returns a tuple of (max, period)

        """
        return (self._quota_receive_max,self._quota_receive_period)

    @quota_receive.setter
    def quota_receive(self,val):
        if val is None:
            self.set_quota_send(quota_type.RECEIVE,period=0)
        else:
            self.set_quota(quota_type.RECEIVE,val[0],val[1])

    def get_has_quota(self,type=quota_type.SEND):
        period=getattr(self, '_quota_%s_period' % type)
        return period!=0

    @property
    def has_quota_send(self):
        return self.get_has_quota(quota_type.SEND)

    @property
    def has_quota_receive(self):
        return self.get_has_quota(quota_type.RECEIVE)

    def get_quota_head_room(self,type=quota_type.SEND):
        """
        how many more messages can go under current quota
        OR None if infinite quota.

        """
        if not getattr(self,'has_quota_%s' % type):
            return None

        # check and reset time period if needed before doing anything
        self.__check_quota_period(type)

        seen=getattr(self,'_quota_%s_seen' % type)
        max=getattr(self,'_quota_%s_max' % type)
        room=max-seen
        if max-seen>=0:
            return max
        else:
            return 0

    def __get_quota_period_remain(self,type=quota_type.SEND):
        """
        Return a timedelta object of remaining time
        in current period or None if infinite (no quota)

        Private version is also called by __check_quota_period

        """
        if not getattr(self,'has_quota_%s' % type):
            return None
        
        num_seen=getattr(self,'_quota_%s_seen' % type)
        period_begin=getattr(self,'_quota_%s_period_begin' % type)
        period=gettattr(self,'_quota_%s_period' % type)
        return (datetime.utcnow()+period)-period_begin
        
    def get_quota_period_remain(self,type=quota_type.SEND):
        """
        Return a timedelta object of remaining time
        in current period or None if infinite (no quota)

        """
        # check and reset time period if needed before doing anything
        self.__check_quota_period(type)
        return __get_quota_period_remain(type)
        
    @property
    def under_quota_send(self):
        """Return number of messages under quota or 0 if over"""
        under=self.get_quota_head_room(type=quota_type.SEND)
        if under is None:
            return True
        return bool(under)

    @property
    def under_quota_receive(self):
        """Return number of messages under quota or 0 if over"""
        under=self.get_quota_head_room(type=quota_type.RECEIVE)
        if under is None:
            return True
        return bool(under)

    @property
    def period_remain_quota_send(self):
        return self.get_quota_period_remain(self,quota_type.SEND)

    @property
    def period_remain_quota_receive(self):
        return self.get_quota_period_remain(self,quota_type.RECEIVE)

    @property
    def signature(self):
        if len(self.given_name)==0:
            if len(self.family_name)==0:
                rs = ChannelConnection.objects.filter(contact=self)
                if len(rs)==0:
                    return self.id
                else:
                    return ( "%s" % rs[0].user_identifier )
            return ( "%s" % self.family_name )
        return (("%s %s") % (self.given_name + self.family_name))
    

#basically a PersistentBackend
class CommunicationChannel(models.Model):
    """
    Info to identify backend instances.

    And example of multiple comm-channels would be
    channels to each of several Mobile carriers.

    E.g. a modem communicating with Zain and another to MTN

    """
    backend_slug = models.CharField(max_length=30,primary_key=True)
    title = models.CharField(max_length=255,blank=True)

    class Meta:
        unique_together = ('backend_slug','title')
            

# basically persistent connection
class ChannelConnection(models.Model):
    """
    Maps phone# to communication channel

    """
    user_identifier = models.CharField(max_length=64)
    communication_channel = models.ForeignKey(CommunicationChannel)

    # always associated with a Contact, though contact
    # may be _blank_
    contact = models.ForeignKey(Contact,related_name='channel_connections') 

    def __unicode__(self):
        return u"UserID: %s, Contact DebugID: %s, Backend: %s" % \
            (self.user_identifier, self.contact.debug_id, self.communication_channel.backend_slug)

    def __repr__(self):
        return 'ChannelConnection(%s,%s)' % \
            (self.user_identifier, self.communication_channel.backend_slug)

    @property
    def connection(self):
        return Connection(self.communication_channel.backend_slug, \
                              self.user_identifier)

    class Meta:
        unique_together = ('user_identifier', 'communication_channel')

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

    rs=CommunicationChannel.objects.filter(backend_slug=slug)
    cc=None
    if len(rs)==0:
        cc=CommunicationChannel(backend_slug=slug)
        if save:
            cc.save()
    else:
        cc=rs[0]
        
    return cc


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
    chan_con=None
    rs=ChannelConnection.objects.filter(user_identifier__exact=u_id, \
                                            communication_channel__exact=comm_c)
    if len(rs)==0:
        # didn't find an existing connection, which means this specific
        # CommunicationChannel (e.g. service provider) and id (e.g. phone number)
        # combo aren't known, so we need a blank Contact for this combo.
        contact=Contact(debug_id=u_id)
        contact.save()
        chan_con=ChannelConnection(user_identifier=u_id,\
                                       communication_channel=comm_c,\
                                       contact=contact)
        if save:
            chan_con.save()
    else:
        chan_con=rs[0]
    return chan_con



