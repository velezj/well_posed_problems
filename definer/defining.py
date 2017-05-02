##
## Copyright Javier Velez <velezj@alum.mit.edu> April 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )

##
#
# This file ocntinas the core Definition concept and
# related classes

import ast
import symtable


##========================================================================
##========================================================================

##
# A Definition is a codified definition in terms of well-definedness.
# Subclasses include PythonDefinition (where we codify using python)
# as well as GroupPossibleDefinition subclasses hich represent
# ways of combining sub-part definitions into a well-defined single
# definition
class DefinitionBase( object ):

    ##
    # Create a new definition with the given node and source
    def __init__( self, node, source ):
        self.node = node
        self.source = source

    ##
    # returns true iff this definition is well defined (no free vars)
    #
    # Subclasses must implement this if the default does not work
    # Generally we would like ot implement get_not_well_defined()
    def is_well_defined(self):
        return len( self.get_not_well_defined() ) == 0

    ##
    # returns a List[ NotWellDefined ] objects determining the things that
    # are not well-defined in this definition
    #
    # Subclasses must override this
    def get_not_well_defined(self):
        return [ NotWellDefinedNode(
            definition=self,
            node=self.node ) ]

##========================================================================

##
# A Definition based on a group of definitions and a node
#
# This is a base class for such group-based definitions.
# Subclasses must implement a way to test is the set of
# gien definitions and the node together are well-defined
# by combining hte definitions "somehow" (hence subclasses :) )
class GroupPossibleDefinition( DefinitionBase ):

    ##
    # Creates a new definition with given set of definitions and concept
    def __init__( self, node, inner_definitions ):
        super( GroupPossibleDefinition, self ).__init__(
            node = node,
            source = None )
        self.inner_definitions = inner_definitions


##========================================================================
##========================================================================

##
# The base for NotWellDefined which represents something that is keeping
# a definition from being "well-defined"
class NotWellDefined( object ):

    ##
    # Every NotWellDefined is tried to a DefinitionBase definition
    def __init__( self,
                  definition ):
        self.definition = definition

    ##
    # A String representation
    def __str__(self):
        return "{0}[{1}]".format(
            type(self).__name__,
            self.definition.source )

##========================================================================

##
# A NotWellDefined where a particular Node itself is what is not
# well defined
class NotWellDefinedNode( NotWellDefined ):

    ##
    # Creates a NotWellDefined with given definition and node
    # that is not defined
    def __init__( self,
                  definition,
                  node ):
        NotWellDefined.__init__( self,
                                 definition )
        self.node = node

    ##
    # Returns a string representations
    def __str__( self ):
        return "NotWellDefined[Node: {0}]".format(
            map(lambda r: r.human_friendly(),
                self.node.representations ) )

##========================================================================

##
# A NotWellDefined where a Binding is not defined ut expected
class NotWellDefinedMissingBinding( NotWellDefined ):

    ##
    # Create a new NotWellDefined for given definition and
    # expected binding name
    def __init__( self,
                  definition,
                  binding_name ):
        NotWellDefined.__init__(self,definition)
        self.binding_name = binding_name

    ##
    # String representation
    def __str__(self):
        return "NotWellDefined[Missing-Binding: '{0}']".format(
            self.binding_name )

##========================================================================

##
# A NotWellDefined where we have too many bindings for a symbol
# and we expect only one
class NotWellDefinedAmbiguousBinding( NotWellDefined ):

    ##
    # Create a new NotWellDefined with the definition,
    # and binding name, and the bindings for it which are
    # anbiguous
    def __init__( self,
                  definition,
                  binding_name,
                  bindings ):
        NotWellDefined.__init__(self,definition)
        self.binding_name = binding_name
        self.bindings = bindings

    ##
    # A String repreentation of this not-well-defined
    def __str__(self):
        s = "NotWellDefined[Ambiguous-Binding for '{0}': ".format(
            self.binding_name )
        for b in self.bindings:
            s += "{0}={1} , ".format( b.identifier,
                                      b.value )
        s += "]"
        return s

##========================================================================

##
# A NotWellDefined that is because of a syntax error in hte source of
# the definition
class NotWellDefinedSyntaxError( NotWellDefined ):

    ##
    # Creates a NotWellDefined with the definition which has broken syntax
    def __init__(self,
                 definition ):
        NotWellDefined.__init__(self,definition)

##========================================================================
##========================================================================
##========================================================================
##========================================================================


##
# A Definition that assumes the source is python source code
# and treats well-definedness as having no free variables which are
# not bound in the given Nodes's context
class PythonDefinition( DefinitionBase ):

    ##
    # Creates a new python definition with given node
    # adn source
    def __init__( self,
                  node,
                  source ):
        super(PythonDefinition, self).__init__( node,
                                                source )
        self.free_vars = self._compute_free_variables()

    ##
    # return NotWellDefined objects for the reasons why this
    # Definition is not well-defined.
    # If it is well-defined this will return an empty list :)
    def get_not_well_defined(self):

        # if we wer unalbe to compute free variables then
        # this is a malformed python source and we return
        # a NotWellDefined as such
        if self.free_vars is None:
            return [
                NotWellDefinedSyntaxError(
                    definition = self ) ]

        # Ok, look for each of hte free variables and
        # see if we have exactly one binding for it.
        # Having too many is not good eaither
        nwds = []
        for v in self.free_vars:

            # grab dingins for free variable
            binds = self.node.lookup_bindings( v )

            # Ok, if 0 or more than one we are not well defined :)
            if len(binds) < 1:
                nwds.append( NotWellDefinedMissingBinding(
                    definition = self,
                    binding_name = v ) )
            elif len(binds) > 1:
                nwds.append( NotWellDefinedAmbiguousBinding(
                    definition = self,
                    binding_name = v,
                    bindings = binds ) )

        # ok, return all found NotWellDefined objects
        return nwds


    ##
    # Computes the "free variables" in this definitions.
    # This menas we parse the source as python and grab anything
    # that is either a free-variable or a global (not assigned)
    # in the toplevel :)
    #
    # Returns a list of the names of the free variables
    def _compute_free_variables(self):

        # ok, we will try parsing hte source and computing the
        # symboltable for the source
        try:
            st = symtable.symtable(
                code = self.source,
                filename = self.node.human_friendly(),
                compile_type = 'exec' )

            # Ok, now that we have the symbol table, find all
            # variables in toplevel denoted as "free" or "global"
            fvars = []
            for s in st.get_symbols():
                if s.is_free() or s.is_global():
                    fvars.append( s.get_name() )

            # return the found free varibles
            return fvars
            
        except:
            return None



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

