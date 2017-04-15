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


import itertools

##=========================================================================

##
# A Context is a glorified dictionary with utility functions and a type tag
class Context( dict ):

    DEFINITION_KEY = "%%DEFINITION%%"

    ##
    # Initialize the dictionary
    def __init__( self, *args, **kw ):
        dict.__init__( self, *args, **kw )

    ##
    # There is a *special* identifier for a "definition" of something,
    # and here we can access it
    def definition_binding(self):
        return self.get( self.DEFINITION_KEY, None )

    ##
    # bind the definition in this context
    def bind_definition(self,definition):
        self[ self.DEFINITION_KEY ] = definition

##=========================================================================

##
# A Representation is a particular output projection of a Concept.
# Generally Representations have a way to make themselves "human-friedly"
# via a unicode string
class Representation( object ):

    ##
    # Some canstant defining the levels of a representation
    LEVEL_HUMAN_SEMMANTICS = 50
    LEVEL_INPUT_MORPHISM = 30
    LEVEL_SYSTEM_INFORMATION = 10
    LEVEL_IDENTIFIER = 5
    LEVEL_UNKNOWN = 0

    ##
    # Initialize a Representation with the given string
    def __init__( self, raw, level = LEVEL_UNKNOWN ):
        self.raw = raw
        self.level = level

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
# Returns a the fully expanded representation
#
# This returns a structure with the following semantics:
#   1) a List means a choice of possible human_friendly() strings
#      that could be used to represent the concept at that point in
#      the structure.  This is essentially an OR constraint
#   2) A Tuple represents a structural constraint and means that
#      the concept has a given number of children. This constraints the
#      number of children of the concept to be this exact number
#   3) A String represents a human_friendly() result of a representation
#      and is a strict equality constraint on hte string
#
# Note: by design we always strart iwth a List since there can always be
#       a choice of size one :)
def fully_expand_representations( c ):
    
    res = []
    for r in c.representations:
        res.append( r.human_friendly() )
        
    # ok, we can also represent this as a lsit of it's constituents
    if len(c.constituent_concepts) > 0:
        child_res = []
        for c0 in c.constituent_concepts:
            child_res.append( fully_expand_representations( c0 ) )
        res.append( tuple(child_res) )
    return res

##=========================================================================

def flatten1( x ):
    if not isinstance( x, list ):
        return x
    res = []
    for a in x:
        if isinstance( a, list ):
            res.extend( a )
        else:
            res.append( a )
    return res

def flatten2( x ):
    if not isinstance( x, list ):
        return x
    res = []
    for a in x:
        if isinstance( a, list ):
            res.append( map( flatten, a ) )
        else:
            res.append( a )
    return res

def flatten(S):
    if not isinstance( S, list ):
        return S
    if S == []:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])


##
# "flatten" a set of fully expanded respresentations to bsaically get
# a list of flat choice paths. So every structure choice is removed and
# treated as a flat possiblity which only consists of equality choices.
def flatten_fully_expanded_representations( expanded_reps,
                                            current_path = [],
                                            acum = [] ):

    # If this is an atom, this is strange so raise error
    if not isinstance( expanded_reps, (list,tuple) ):
        raise RuntimeError( "Got atom which flattening expanded reps, should not happen" )

    # Ok, if we are a list of atoms (non-lists/tuples) then
    # we are a flat path so just add to accumulator the choice
    # and return
    if isinstance( expanded_reps, list ) and all(map(lambda x: not isinstance( x, (list,tuple) ), expanded_reps)):
        #logger.info( "Atom-flatten: returning {0}".format( [ expanded_reps ] ) )
        return [ expanded_reps ]

    # if we are a structure choice ( a tuple ) then we
    # just flatten each in order
    if isinstance( expanded_reps, tuple ):

        # grab flattene for each child
        child_flats = []
        for x in expanded_reps:
            res = flatten_fully_expanded_representations( x,
                                                          current_path = [],
                                                          acum = [] )
            child_flats.append( res )
            logger.info( "Tuple-Flat: child {0} ==> {1}".format(
                x, res ) )

        # now build up all product combinations of the flattened children
        child_prod = itertools.product( *child_flats )
        for p in child_prod:
            acum.append( current_path + list(p) )
            logger.info( "Tuple-Flat: prod = {0}".format( p ) )

        # return hte sulting acum
        logger.info( "Tuple-flat: result {0} ==> {1}".format(
            expanded_reps,
            acum ) )
        return acum

    # ok, we are a list but have list or tuples inside so split into
    # the atoms and the tuples
    atoms = filter(lambda x: not isinstance( x, (list,tuple) ), expanded_reps)
    lists = filter(lambda x: isinstance( x, list), expanded_reps )
    tuples = filter(lambda x: isinstance( x, tuple), expanded_reps )

    # ok, we do not expect any lsits so error if any found
    if len(lists) > 0:
        raise RuntimeError( "Can not handle nested lists in expanded rep: {0}".format( expanded_reps ) )

    # ok, the atoms are all tretes a a single list so grap the flattene
    # for them as a whole
    child_flats = []
    atom_flats = flatten_fully_expanded_representations( atoms,
                                                         current_path = [],
                                                         acum = [] )
    child_flats.extend( atom_flats )
    logger.info( "Mixed-Flat: atom-flats = {0}".format( atom_flats ) )

    # now each individual structure (tuple) is flattened and each will
    # be accumulated in
    for trep in tuples:
        res = flatten_fully_expanded_representations( trep,
                                                      current_path = [],
                                                      acum = [] )
        child_flats.extend( res )
        logger.info( "Mixed-Flat: tuple {0} ==> {1}".format(
            trep,
            res ) )

    # ok, now for each children's flattened we just accumulate
    # and return hte accumulation
    for p in child_flats:
        acum.append( current_path + p )
    return acum


##=========================================================================


##
# Gien a fully expanded list of representations and
# a concept, returns true iff the concept matches the
# expanded reps (any of them)
def any_rep_match( expanded_reps, c ):

    # o, in hte expanded reps a List is treated as a choice (so any one
    # inside must match) and a Tuple is treated as a structure so *all* must
    # match and exactly match

    # structure check
    if isinstance( expanded_reps, tuple ):

        # length of sturecture must match number of chicldren
        if len( expanded_reps ) != len(c.constituent_concepts):
            return False

        # ok, lengths match so structure matches, let's dive in
        # to their euality checks
        for erep, c0 in zip( expanded_reps,
                             c.constituent_concepts ):
            match = any_rep_match( erep,
                                   c0 )
            if not match:
                return False

        # ok, structure matched and inner matched so yes
        return True

    # choice check
    if isinstance( expanded_reps, list ):

        # return true if any of them match
        for erep in expanded_reps:
            match = any_rep_match( erep, c )
            if match:
                return True

        # ok, none of them matched so no match
        return False

    # neither tuple nor list, so this is an equality ocnstrain check
    # on the concept's representations.  See if *any* of the
    # representations match
    for r in c.representations:
        string = r.human_friendly()
        match = ( expanded_reps == string )
        if match:
            return True

    # ok, getting here means no representaion equaility matched using
    # the human_friendly stirng, so no match
    return False

##=========================================================================

##
# A class representing a substrcutre matching.
# This includes all of the concepts and the start and end
# constituents to use for each concept
class SubstructureMatch( object ):

    WHOLE_CONCEPT = "+whole+"

    ##
    # Creates a new match result with the given ordered concepts and
    # their constituent ranges.
    #
    # THe ranges can be Tuple(start index, end index) or WHOLE_CONCEPT
    # which means use hte entire concept
    def __init__( self,
                  concepts,
                  constituent_ranges ):
        self.concepts = concepts
        self.constituent_ranges = constituent_ranges

##=========================================================================


##
# Gien a fully expanded list of representations and
# a concept, returns a lsit of SubstructeMatch entries
# which represent points where any of the expanded reps
# match part of the concept
#
def any_rep_substructure_match( expanded_reps, c, include_child_submatches = True ):

    # o, in hte expanded reps a List is treated as a choice (so any one
    # inside must match) and a Tuple is treated as a structure.
    # Since this is a substructure match we ignore the structure elements
    # and only consider the *order* of the structure not it's size/bounds

    # Ok, we will bascially iterate over the possible substructures
    # of the concept and see if we substructure match it :)
    res = []

    # first try a full match
    full_match = any_rep_match( expanded_reps, c )
    if full_match:

        # build up a SubstructureMatch entry for the full match
        res.append( SubstructureMatch(
            concepts = [ c ],
            constituent_ranges = [ SubstructureMatch.WHOLE_CONCEPT ] ) )

    # Ok, if we found a full match and we do not want children submatches
    # then we are done
    if full_match and not include_child_submatches:
        return res

    # ok, iterate over two things:
    #   1) the children concepts themselves and find any matches
    #   2) suffixes of hte children as a concept and find any matches
    # We are going to *approximate this* by flattening both the
    # expanded representation and the concept and looking for
    # suffixes
    flattened_expanded_reps = flatten_fully_expanded_representations( expanded_reps )
    flattened_c = flatten_fully_expanded_reps( fully_expand_representations( c ) )
    

    # structure check
    if isinstance( expanded_reps, tuple ):

        # length of sturecture must match number of chicldren
        if len( expanded_reps ) != len(c.constituent_concepts):
            return False

        # ok, lengths match so structure matches, let's dive in
        # to their euality checks
        for erep, c0 in zip( expanded_reps,
                             c.constituent_concepts ):
            match = any_rep_match( erep,
                                   c0 )
            if not match:
                return False

        # ok, structure matched and inner matched so yes
        return True

    # choice check
    if isinstance( expanded_reps, list ):

        # return true if any of them match
        for erep in expanded_reps:
            match = any_rep_match( erep, c )
            if match:
                return True

        # ok, none of them matched so no match
        return False

    # neither tuple nor list, so this is an equality ocnstrain check
    # on the concept's representations.  See if *any* of the
    # representations match
    for r in c.representations:
        string = r.human_friendly()
        match = ( expanded_reps == string )
        if match:
            return True

    # ok, getting here means no representaion equaility matched using
    # the human_friendly stirng, so no match
    return False

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
#
# The Representations in the concept are stored in "most preffered" to
# least preffered order, so by default the first representation will
# be used whenever a single representation of the concept is needed
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
                  representations = None,
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
        srep = "#|id={0}|#".format(
            self.identifier )
        self.representations.append( Representation(
            srep,
            level=Representation.LEVEL_IDENTIFIER) )
        srep = "#|{1} id={0}|#".format(
            self.identifier,
            type(self).__name__)
        self.representations.append( Representation(
            srep,
            level=Representation.LEVEL_IDENTIFIER) )

        # add ourselves to parent if not alreayd there
        if parent_concept is not None and self not in parent_concept.constituent_concepts:
            parent_concept.constituent_concepts.append( self )
        

    ##
    # Returns the single most "preferred" representation
    # Fir now it's just the first one in list
    def preferred_representation(self):
        return self.representations[0]

    ##
    # By default a stirng representation jsut uses the
    # first representations human_friendly
    def __str__(self):
        return self.preferred_representation().human_friendly()

    ##
    # Returns a debug string representing this concept
    def debug_string(self):
        leaves = leaves_human_reps( self )
        return "{0}[id={1} leaves={2}]".format(
            type(self).__name__,
            self.identifier,
            leaves )

    ##
    # Return true if this is a top-level concept
    def is_toplevel(self):
        return self.parent_concept is None

    ##
    # Removes this concept from the concept graph
    # by removing itself from it's parent constituents list
    # and by setting it's parent ot None
    def unlink( self ):
        if self.parent_concept is not None:
            if self in self.parent_concept.constituent_concepts:
                self.parent_concept.constituent_concepts.remove( self )
        self.parent_concept = None
    
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

        # if we have no constituents, return base definition
        if len(self.constituent_concepts) == 0:
            return DefinitionBase(
                concept = self,
                source = None )

        # Ok, now try to get definitions from all constituents
        defs = []
        for c in self.constituent_concepts:
            cdef = c.possible_definition()
            defs.append( cdef )
            
        # ok, all constituents have possible definitions so return a group
        # definitionf with them
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
        return [ NotWellDefinedConcept(
            definition=self,
            concept=self.concept ) ]

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


##=========================================================================
##=========================================================================

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

##=========================================================================

##
# A NotWellDefined where a particular Concept itself is what is not
# well defined
class NotWellDefinedConcept( NotWellDefined ):

    ##
    # Creates a NotWellDefined with given definition and concept
    # that is not defined
    def __init__( self,
                  definition,
                  concept ):
        NotWellDefined.__init__( self,
                                 definition )
        self.concept = concept

    ##
    # Returns a string representations
    def __str__( self ):
        return "NotWellDefined[Concept: {0}]".format(
            map(lambda r: r.human_friendly(),
                self.concept.representations ) )

##=========================================================================

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

##=========================================================================

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

##=========================================================================

##
# A NotWellDefined that is because of a syntax error in hte source of
# the definition
class NotWellDefinedSyntaxError( NotWellDefined ):

    ##
    # Creates a NotWellDefined with the definition which has broken syntax
    def __init__(self,
                 definition ):
        NotWellDefined.__init__(self,definition)

##=========================================================================
##=========================================================================
##=========================================================================

##
# A superclass for Concepts which have the most rudimentary of parse(...)
# functions that just reutrn BoxConcept with the input :)
class ParselessConcept( ConceptBase ):

    def __init__( self, *args, **kw ):
        ConceptBase.__init__( self, *args, **kw )

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
        reps.append( Representation(
            "{0}".format(value),
            level=Representation.LEVEL_INPUT_MORPHISM ))
        reps.append( Representation(
            "#|Box:{0}|#".format(value),
            level=Representation.LEVEL_SYSTEM_INFORMATION) )
        ParselessConcept.__init__(
            self,
            parent_concept = parent_concept,
            constituent_concepts = [],
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

        self.command_identifier = command_identifier

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
                map(lambda c: c.preferred_representation().human_friendly(),
                    arg_concepts) ),
            level = Representation.LEVEL_HUMAN_SEMMANTICS ) )

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
