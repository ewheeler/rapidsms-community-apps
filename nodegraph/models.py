#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models

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

class AbstractNode(models.Model):
    """
    Abstract superclass for Nodes and NodeSets

    """

    name = models.CharField(max_length=255)

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
            self.add_to_group(self)

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
                buf.append(u'*%s' % node.name)
                return

            seen.add(node)
            buf.append(u'%s(' % node.name)
            index=0
            for sub in node.subgroups:
                _recurse(sub,index)
                index+=1

            leaves=u','.join([l.name for l in node.subleaves])
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
                

    


    
