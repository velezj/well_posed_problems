##
## Copyright Javier Velez <velezj@alum.mit.edu> April 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )


##
#
# This file contains utilitiesfor nodes.
# Most important is the Visitor pattern for searching the node graph

import collections

##========================================================================

##
# A simple inserter for a NodeVisitor which performsn Bread-First-Search
#
# Note: the *end* element of the q is the next one to be visited
def bfs_inserter( q, children ):
    for c in reversed(children):
        if c not in q:
            q.append( c )
    return q

##========================================================================

##
# An expander for the NodeVisitor which just expands both
# repreentations and parts, representations first
def all_children_expander( node ):
    return node.representations + node.parts

##========================================================================

 
##
# A Queue-Based Visitor pattern for the Node graph.
# This allows one to visit nodes in breadth-first, depth-first, or
# some order-first way by specifying the q-insertion function.
#
# This also allows for hooks into the stages of visiting a node graph:
#   1) Are we done ("termintor")
#   2) "Visit" the next node in the q (at end) and add to already_visited
#   3) "Expand Children"
#   4) "Insert" the not-already-visited children into the q
#
# Note: the *end* of hte q (last element) is popped and used at every visitation
class NodeVisitor( object ):

    ##
    # Creates a new node-visitor with the given
    # hooks and queue insertion function
    def __init__( self,
                  q_inserter = bfs_inserter,
                  visitor = None,
                  expander = all_children_expander,
                  terminator = None ):
        self.q_inserter = q_inserter
        self.visitor = visitor
        self.expander = expander
        self.terminator = terminator
        self.q = []
        self.already_visited = set([])

    ##
    # Start a visiting pattern from the given list of
    # nodes as "roots"
    def visit( self, roots ):

        # make sure roots is a list
        if not isinstance( roots, collections.Iterable ):
            roots = [ roots ]

        # ok, we add all roots to the q
        self.q.extend( roots )

        # now we just perform our loop
        while not self._is_done():

            # grab first node in q
            node = self.q.pop()
            self.already_visited.add( node )

            # visit hte node
            self._visit( node )

            # expand children
            children = self._expand_children( node )

            # filter children to those not alredy visited
            children = filter(lambda c: c not in self.already_visited, children)

            # add children to q
            self._add_children_to_q( children )

    ##
    # returns true iff the visiting is done.
    # This uses either the given termination function or
    # checks for an empty q
    def _is_done(self):

        # use temrinator if we hve it
        if self.terminator is not None:
            tres = self.terminator( self.q, self.already_visited )
            if tres:
                return tres

        # Ok, even if we have a terminator, if it returns false but
        # there is nothing in the q we are done
        return len(self.q) == 0

    ##
    # "visit" the given node.
    # Usually jsut forward to the given visitor
    def _visit(self, node):
        if self.visitor is not None:
            self.visitor( node )

    ##
    # Expand and return the children for a node.
    # Just forwards to the expander
    def _expand_children( self, node ):
        if self.expander is not None:
            children = self.expander( node )
            return children
        return []

    ##
    # Add the given children to the q.
    # This will invoke our q_inserter and replace the q
    def _add_children_to_q( self, children):
        if self.q_inserter is not None:
            self.q = self.q_inserter( self.q, children )

##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
##========================================================================
