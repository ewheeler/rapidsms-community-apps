#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

# Models from other apps
from apps.locations.models import Location
from rapidsms import message,connection

# 
# A data model for simple interconnected graphs of nodes.
#
# There are two types of nodes: Sets and Leaves.
#
# The only distinction is:
# - Sets may contain other nodes (both Sets and Leaves)
# - Leaves may _not_ contain other nodes (they terminate the graph)
#
# Speaking concretely, A graph of Nodes can represent GROUPS of USERS where:
# - Groups are Sets and can contain other Groups and Users
#
# Data integrity policies/enforcement:
# - When requests a list of members for a Set, the model will break cycles.
#   So if you have Set A with itself as the only member (A<A--A contains A) asking for the
#   members of 'A' will not create an endless loop, and will return an empty list
#
#   In the case of A<B<A (A contains B contains A) A.members() returns B only
#
# ALL OTHER RULES MUST BE ENFORCED BY THE USER OF THE MODEL. 
# For example, there is no restriction on Leaves appearing in multiple Sets
# 
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

class AbstractNode(models.Model):
    """
    Abstract superclass for Nodes and NodeSets

    """

    """
    For testing only. If you want a real name, id, or any other data,
    make Node and NodeSet subclasses

    """
    debug_id = models.CharField(max_length=16,blank=True,null=True)
    
    def __unicode__(self):
        return self.debug_id

    class Meta:
        abstract=True


class Node(AbstractNode):
    """
    Abstract representation of a Node in the graph.
    
    Contains common properties of Set and Leaf.
    
    """

    # helpers 'cause directionality can be confusing
    def add_to_group(self,grp):
        grp._add_subnodes(self)

    def add_to_groups(self,*grps):
        for grp in grps:
            self.add_to_group(grp)

    def remove_from_group(self,grp):
        grp._remove_subnodes(self)

    def remove_from_groups(self,*grps):
        for grp in grps:
            self.remove_from_group(self)

    @property
    def groups(self):
        """The groups this node is a member of"""
        return list(self.nodeset_set.all())

class NodeSet(AbstractNode):
    """
    A node that has 'members', which is a set of nodes this node points too. 
    Named 'NodeSet' to distinguish from python type 'set'

    Because of awkwardness in mapping Python inheritence to SQL, need
    to hold 'Nodes' and 'NodeSets' in separate lists, but provide helpers
    to make this invisible to user.

    """

    _subgroups = models.ManyToManyField('self',symmetrical=False)
    _subleaves = models.ManyToManyField(Node)
    
    def __unicode__(self):
        """
        Prints the graph starting at this instance.

        Format is NodeSetName(subnode_set(*), subnode+)

        If nodes appear more than once in traversal, additional references are
        shown as *NodeSetName--e.g. pointer-to-NodeSetName.

        Given A->b,c,D->A, where CAPS are NodeSet and _lowers_ are Nodes, results are:

        A(D(*A),b,c)
        
        """

        buf=list()
        seen=set()
        def _recurse(node, index):
            if index>0:
                buf.append(u',')

            if node in seen:
                buf.append(u'*%s' % node.debug_id)
                return

            seen.add(node)
            buf.append(u'%s(' % node.debug_id)
            index=0
            for sub in node.subgroups:
                _recurse(sub,index)
                index+=1

            leaves=u','.join([unicode(l) for l in node.subleaves])
            if len(leaves)>0:
                if index>0:
                    buf.append(u',')
                buf.append(u'%s)' % leaves)

        _recurse(self,0)

        return u''.join(buf)

    #
    # helpers because directionality is confusing
    #
    def add_to_group(self,grp):
        grp._add_subnodes(self)

    def add_to_groups(self,*grps):
        """
        Add this instance to the listed groups

        """
        for grp in grps:
            self.add_to_group(grp)

    def remove_from_group(self,grp):
        grp._remove_subnodes(self)

    def remove_from_groups(self,*grps):
        for grp in grps:
            self.remove_from_group(grp)

    # safe to use, but calls above should be sufficient
    def _add_subnodes(self,*sub_nodes):
        """
        Add the passed nodes to this instance as 'subnodes'
        
        Can be NodeSets or Nodes
        
        """
        for n in sub_nodes:
            # distinguish between Nodes and NodeSets
            if isinstance(n, Node):
                self._subleaves.add(n)
            elif isinstance(n, NodeSet):
                self._subgroups.add(n)

    def _remove_subnodes(self, *subnodes):
        for n in subnodes:

            # distinguish between Nodes and NodeSets
            if isinstance(n, Node):
                self._subleaves.remove(n)
            elif isinstance(n, NodeSet):
                self._subgroups.remove(n)

    # and some shortcut properties
    @property
    def subgroups(self):
        """All the direct sub-NodeSets"""
        return list(self._subgroups.all())

    @property
    def subleaves(self):
        """All the direct sub-Nodes"""
        return list(self._subleaves.all())

    @property
    def subnodes(self):
        """A list of both the sub-NodeSets and sub-Nodes"""
        return self.subgroups+self.subleaves

    # full graph access methods
    def flatten(self, max_depth=None):
        """
        Flattens the graph from the given node to max_depth returning
        a set of all leaves.

        Breaks cycles.

        """

        if max_depth is not None:
            max_depth=int(max_depth)
            if max_depth<1:
                return

        # hold unique set of NodeSets we've visited to break cycles
        seen=set()
        leaves=set()
        # recursive function to do the flattening
        def _recurse(nodeset, depth, max_depth=None):
            # check terminating cases
            # - node is None (shouldn't happen but why not be safe?)                        
            # - reached max_depth
            # - seen this guy before (which breaks any cycles)
            if nodeset is None or \
                    (max_depth is not None and depth==max_depth) or \
                    nodeset in seen:
                return
            
            # ok, it's a valid nodeset, add to seen
            seen.add(nodeset)
            
            # add its subleaves to 'leaves'
            leaves.update(nodeset.subleaves)

            # recurse to its subgroups
            for ns in nodeset.subgroups:
                _recurse(ns, depth+1, max_depth=max_depth)
                
        # Now call recurse
        _recurse(self, 0, max_depth)
        
        return leaves

class Community(NodeSet):
    name = models.CharField(max_length=255,blank=True,null=True)
    pass


class Village(NodeSet):
    name = models.CharField(max_length=255,blank=True,null=True)
    location = models.ForeignKey(Location, related_name="reporters", null=True, blank=True)
    pass


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
    user_id = models.CharField(max_length=64)
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



