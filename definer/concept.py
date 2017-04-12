import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains the basic "Concept" abstraction.
# A concept has the following properties:
#    1) A parent concept
#    2) A Context
#    3) Constituent Concepts
#    4) A set of Representations
#    5) An identifier
#
# Furthermoe, Concepts allow the ability to "parse" input representations
# into Concepts.
#
# We can think of a concept as a set of local symbolic bindings along with
# a placement in the hierarchy of all such symbolic binding environments.
# Concepts allows us to be able to reason about the "well-defined-ness" of
# themselves by allowing a way to structure (constituents) and define
# (the Context and local bindings) symbols into a fully computable
# strucute.


##=========================================================================

##
# A Context is a glorified dictionary with utility functions and a type tag
class Context( dict ):

    ##
    # Initialize the dictionary
    def __init__( self, *args, **kw ):
        dict.__init__( self, *args, **kw )

    ##
    # There is a *special* identifier for a "definition" of something,
    # and here we can access it
    def definition_binding(self):
        return self.get( "%%DEFINITION%%", None )

##=========================================================================

##
# A Representation is a particular output projection of a Concept.
# Generally Representations have a way to make themselves "human-friedly"
# via a unicode string
class Representation( object ):

    ##
    # Initialize a Representation with the given string
    def __init__( self, raw ):
        self.raw = raw

    ##
    # Returns a human-friendly version of this Representation
    def human_friendly( self ):

        # convert to unicode
        s = unicode( self.raw )

        # add block if spaces inside string
        if " " in s:
            s = '[[' + s + ']]'

        return s

##=========================================================================

##=========================================================================

##
# returns a lsit of the human friendly representations at the *leaves*
# or edges of a concept
def leaves_human_reps( c, all_reps=False ):
    if not isinstance( c, ConceptBase ):
        return str(c)
    if len(c.constituent_concepts) > 0:
        return map(lambda x: leaves_human_reps(x,all_reps=all_reps),
                   c.constituent_concepts)
    res = tuple(map(lambda rep: rep.human_friendly(),
                    c.representations))
    if all_reps:
        return res
    return res[0]

##=========================================================================


##
# A Concept has certain properties:
#    1) parent concept
#    2) constituent concepts
#    3) a Context
#    4) a set of Representations
#    5) an identifier
#
# The most important thing for a Concept is that it can "parse"
# input into other Concepts.
#
# Also a Concept has a sense of
# what engine to use to merge group definitions into a single
# definition via it's choice of GroupPossibleDefinition subclass
# returned by the _group_possible_definition(...) method.
#
# Further, Concepts are all explicitly within a global graph
# using paret->child nad constituent relations
class ConceptBase( object ):

    ##
    # Create a concept with:
    #   a parent
    #   a set of consitituents
    #   a Context (optional)
    #   a list of Representations (optional)
    #   an Identifier (optional)
    def __init__( self,
                  parent_concept,
                  constituent_concepts,
                  context = Context(),
                  representations = [],
                  identifier = None ):
        self.parent_concept = parent_concept
        self.constituent_concepts = constituent_concepts
        self.context = context
        self.representations = representations
        self.identifier = identifier
        if self.identifier is None:
            self.identifier = id(self)

        # ensure we have a lsit of representations
        if self.representations is None:
            self.representations = []

        # always add the basic default rep
        srep = "#|{2} id={0}/{1}|#".format(
            self.identifier,
            id(self),
            type(self).__name__)
        self.representations.append( Representation( srep ) )

    ##
    # By default a stirng representation jsut uses the
    # first representations human_friendly
    def __str__(self):
        return self.representations[0].human_friendly()

    ##
    # Return true if this is a top-level concept
    def is_toplevel(self):
        return self.parent_concept is None

    ##
    # Method interface to "parse" input
    # and retunrs a List[ ConceptBase ]
    #
    # Subclasses must implement this
    def parse( self, raw ):
        raise NotImplementedError()


    ##
    # *The* binding lookup mechanism for Concepts :)
    #
    # This will look for hte bindings in:
    #    1) the Context of this Concept
    #    2) Any constituent Concepts
    #
    # This will return List[ Bindings ] with includes all
    # unshadowed bindings at this Concept level.
    # How does "shadowing" work:
    #   1) If this Concept has the binding, then it shadows everything and
    #      is the only binding returned
    #   2) Otherwise, all bindings on the constituents are returned :)
    def lookup_bindings( self,
                         identifier,
                         path = []):

        # Ok, the first check is in our direct context
        if identifier in self.context:
            
            # this context shadows everything, return jsut this binding
            return [ Binding( path = path + [self],
                              identifier=identifier,
                              value=self.context[ identifier ] ) ]

        # Ok, look at all constituents and grab their bindings
        bindings = []
        for c in self.constituent_concepts:
            binds = c.lookup_bindings( identifier, path + [self] )
            bindings.extend( binds )
        return bindings


    ##
    # Add a binding in this Concept.
    # Effecively sets the value at identifier in the Context
    def bind( self, identifier, value ):
        self.context[ identifier ] = value

    ##
    # We can ask for the "Definition" of this Concept.
    # Here we look at two things:
    #   1) if this Concept has a definition in it's Context we return
    #      it
    #   2) If *all* constituents have a definition then we return
    #      the list of all such definitions as a Definition
    def possible_definition(self):

        # check this context for a definition
        direct_def = self.context.definition_binding()
        if direct_def is not None:
            return direct_def

        # Ok, now try to get definitions from all constituents
        defs = []
        for c in self.constituent_concepts:
            cdef = c.possible_definition()
            if cdef is not None:
                defs.append( cdef )
            else:
                return None # not all constotuents have a definition so we don't

        # ok, all constituents have possible definitions, return them
        return self._group_possible_definition(defs)

    ##
    # Retruns a Definition subclass representing the definition from
    # a set of consitituent definitions.  This allows
    # Concept subclasses to have different GroupPossibleDefinition
    # subclasses being used to represent griup definitions
    def _group_possible_definition(self, defs):
        return GroupPossibleDefinition(
            concept=self,
            inner_definitions=defs)

##=========================================================================
##=========================================================================

## 
# A Binding consists of a path of Concepts, an identifier, and a value.
class Binding( object ):
    def __init__( self,
                  path,
                  identifier,
                  value ):
        self.path = path
        self.identifier = identifier
        self.value = value

    ##
    # returns the "direct" concept which knowns about this binding
    # This is the last in the path :)
    def direct_concept(self):
        if self.path is not None and len(self.path) > 0:
            return self.path[-1]
        return None

##=========================================================================
##=========================================================================

##
# A Definition is a codified python AST.
# Subclasses include WellFormedDefinition (where there are no free variables)
# as well as PossibleDefinition which does have free variables
class DefinitionBase( object ):

    ##
    # Create a new definition with the given concept and source
    def __init__( self, concept, source ):
        self.concept = concept
        self.source = source

    ##
    # returns true iff this definition is well defined (no free vars)
    #
    # Subclasses must implement this
    def is_well_defined(self):
        raise NotImplementedError()

##=========================================================================

##
# A Definition based on a group of definitions and a concept
#
# This is a base class for such group-based definitions.
# Subclasses must implement a way to test is the set of
# gien definitions and the concept together are well-defined
# by combining hte definitions "somehow" (hence subclasses :) )
class GroupPossibleDefinition( DefinitionBase ):

    ##
    # Creates a new definition with given set of definitions and concept
    def __init__( self, concept, inner_definitions ):
        self.concept = concept
        self.inner_definitions = inner_definitions

    ##
    # By default, group definitions are not well-defined.
    # Subclasses do all their work here :)
    def is_well_defined(self):
        return False

##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================

##
# A superclass for Concepts which have the most rudimentary of parse(...)
# functions that just reutrn BoxConcept with the input :)
class ParselessConcept( ConceptBase ):

    def parse( self, raw ):
        return [ BoxConcept( parent_concept = self,
                             value = raw ) ]

##=========================================================================

##
# The simplest of Concepts whic his completely "opaque" hence the "box".
# This is just an opaque value
class BoxConcept( ParselessConcept ):

    def __init__( self,
                  parent_concept,
                  value ):
        context = Context()
        context[ 'value' ] = value
        reps = []
        reps.append( Representation( "#|Box:{0}|#".format(value) ) )
        reps.append( Representation( "#|Box id={0}|#".format(id(self)) ) )
        ParselessConcept.__init__(
            parent_concept = parent_concept,
            constituents = [],
            context = context,
            representations = reps )
        self.value = value
        

##=========================================================================


##
# A CommandConcept is a Concept that is suited for the user trying
# to perform and action with the system (aka "run" a command :) )
#
class CommandConcept( ParselessConcept ):

    ##
    # Initialize with command name and arguments
    # along with a parent concept
    def __init__( self,
                  parent_concept,
                  command_identifier,
                  arg_concepts ):

        # ok, the identifier for this concept is based on the
        # command identifier
        identifier = ( command_identifier, id(self) )

        # the constituent are the arguments :)
        constituents = arg_concepts

        # Ok, the Context for this  command has the arguments bound
        # to an 'args' name
        context = Context()
        context[ 'args' ] = arg_concepts

        # a default representation with the command name and args
        reps = []
        reps.append( Representation(
            "{0}( {1} )".format(
                command_identifier,
                map(lambda c: c.representations[0].human_friendly(),
                    arg_concepts) ) ) )
        reps.append( Representations( "#|Command{0}|#".format(identifier) ) )

        # ok, create baseclass
        ConceptBase.__init__(
            self,
            parent_concept = parent_concept,
            constituent_concepts = constituents,
            identifier = identifier,
            context = context,
            representations = reps)

##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
