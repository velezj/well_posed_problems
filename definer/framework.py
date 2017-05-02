##
## Copyright Javier Velez <velezj@alum.mit.edu> April 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )


##
#
# This file represents the basic framework of Nodes, Context
# and such used for the definer system

import collections

##========================================================================

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


##========================================================================
##========================================================================

##
# A NodePath is a serie of steps thorugh a node graph.
# This is an *immutable* functional object that is usyually used to
# accumulate a path as we are traversing the node graph.
#
# This essentially represents a List[ step ] where
#   step := ( direction, Node }
#   direciton := None | ( list_id, Node )
#   list_id := 'pieces' |
#              'parental_piece' |
#              'representations' |
#              'parental_representaiton'
class NodePath( object ):

    ##
    # A step class. All subclasses conform to this
    Step = collections.namedtuple( 'Step',
                                   [ 'direction',
                                     'node' ] )

    ##
    # A "Direct" step which has no direction
    #
    # Create this step with just the node
    class DirectStep( Step ):
        __slots__ = ()
        def __new__( cls, node ):
            self = super( NodePath.DirectStep, cls ).__new__( cls, None, node )
            return self

    ##
    # A step into a "piece" of a node
    class PieceStep( Step ):
        __slots__ = ()
        def __new__( cls, node, piece ):
            self = super( NodePath.PieceStep, cls ).__new__(
                cls,
                ( 'pieces', node ) ,
                piece )
            return self

    ##
    # A step into a "representation" of a node
    class RepresentationStep( Step ):
        __slots__ = ()
        def __new__( cls, node, rep ):
            self = super( NodePath.RepresentationStep, cls ).__new__(
                cls,
                ( 'representations', node ) ,
                rep )
            return self


    ##
    # A step into a "parental representation" of a node
    class ParentalRepresentationStep( Step ):
        __slots__ = ()
        def __new__( cls, node, parental_rep ):
            self = super( NodePath.ParentalRepresentationStep, cls ).__new__(
                cls,
                ( 'is_representation_of', node ) ,
                parental_rep )
            return self

    ##
    # A step into a "parental piece" of a node
    class ParentalPieceStep( Step ):
        __slots__ = ()
        def __new__( cls, node, parental_piece ):
            self = super( NodePath.ParentalPieceStep, cls ).__new__(
                cls,
                ( 'is_piece_of', node ) ,
                parental_piece )
            return self


    ##
    # Creates an empty node path
    def __init__( self, steps = [] ):
        self.steps = steps

    ##
    # Access the start node of the path (if any)
    def start_node(self):
        if len(self.steps) > 0:
            return self.steps[0].node
        return None

    ##
    # Access the end of the path (if any)
    def end_node(self):
        if len(self.steps) > 0:
            return self.steps[-1].node
        return None

    ##
    # Add a new "direct" step, which is a visiting of a node
    # without a given direction.  These are usually at the
    # ends of a NodePath representing a goal or  start
    def add_direct_step( self, node ):
        s = list(self.steps)
        s.append( NodePath.DirectStep( node ) )
        return NodePath( s )

    ##
    # Add a new step taken into a piece of a node
    def add_piece_step( self, node, piece ):
        s = list(self.steps)
        s.append( NodePath.PieceStep( node, piece ) )
        return NodePath( s )

    ##
    # Add a new step taken into a representation of a node
    def add_representation_step( self, node, rep ):
        s = list(self.steps)
        s.append( NodePath.RepresentationStep( node, rep ) )
        return NodePath( s )

    ##
    # Add a new step taken into a parental representation of node
    def add_parental_representation_step( self, node, parental_rep ):
        s = list(self.steps)
        s.append( NodePath.ParentalRepresentationStep( node, parental_rep ) )
        return NodePath( s )

    ##
    # Add a new step taken into a parental piece of node
    def add_parental_piece_step( self, node, parental_piece ):
        s = list(self.steps)
        s.append( NodePath.ParentalPieceStep( node, parental_piece ) )
        return NodePath( s )


    ##
    # A more readable representation
    def __str__(self):
        return "Path{0}".format( self.steps )
    def __repr__(self):
        return self.__str__()

    ##
    # Equality and has based on the internal list :)
    def __eq__( self, a ):
        if not isinstance(a, NodePath):
            return False
        return self.steps == a.steps
    def __hash__( self ):
        return hash( tuple(self.steps) )

##========================================================================

##
# A Node is a particular concept.
# It internally has a set of representations (also nodes) which
# are alternatives to this node. It also contians a set of
# "pieces" which are nodes that are not strictly alternatives to the
# node but may be subparts of it.
# Every node also has a "natural token structure" (which may be None)
# that is how hte node was created
#
# Nodes all have a Context associanted and most impoirtantly know
# how to lookup bindings within themselves and their parents
class Node( object ):

    ##
    # Creates a new Node
    def __init__( self,
                  natural_token_structure,
                  representations = [],
                  pieces = [],
                  is_representation_of = [],
                  is_piece_of = [],
                  context = None ):
        self.natural_token_structure = natural_token_structure
        self.representations = list(representations)
        self.pieces = list(pieces)
        self.is_representation_of = list(is_representation_of)
        self.is_piece_of = list(is_piece_of)
        self.context = context
        if self.context is None:
            self.context = Context()

    ##
    # returns the id of this node
    def node_id(self):
        return id(self)

    ##
    # Adds the given node as a representation
    def add_representation( self, node ):

        # ok, add to this node's list (if not already tehre)
        # and also add to the given node's is_representation_of
        if node not in self.representations:
            self.representations.append( node )
        if self not in node.is_representation_of:
            node.is_representation_of.append( self )
            

    ##
    # Add the given node as a piece of this node
    def add_piece( self, node ):
        if node not in self.pieces:
            self.pieces.append( node )
        if self not in node.is_piece_of:
            node.is_piece_of.append( self )

    ##
    # Binds a given identifier to a given value in this
    # node's context
    def bind( self,
              identifier,
              value ):
        self.context[ identifier ] = value

    ##
    # Binds hte definition for this node
    def bind_definition( self, definition ):
        self.context.bind_definition( definition )

    ##
    # Lookup any bindings for an identifier
    #
    # Here we define the conceopt of a 'shadowing' of
    # a binding. This will return a list of the possible
    # bindings for an identifier that are not shadowed.
    #
    # The lookup procedure is as follows:
    # 1) if the identifier is directly bound in this node,
    #    then this binding shadows all others and is the only
    #    one returned
    # 2) Any bindings in the *pieces* of this node
    #    are searched for and all such bindings are returned.
    #    So piece bindings do not shadow each other but do shadow
    #    any parental bindings
    # 3) If there are no bindings in the pieces either, we will
    #    lookup the bindings in any of our parental representation
    #    nodes ( the is_representation_of list) and return all such
    #    bindings. So representational parents do not shadow each
    #    other. Also search the parent pieces as well. All
    #    aprental relations (pieces and representations) are non-shadowing
    #    of each other :)
    #
    # The return result is always a list (but may be empty)
    # if Binding objects
    def lookup_bindings( self, identifier, path_acum = NodePath() ):

        # ok, search for direct binding and return if found
        if identifier in self.context:
            return [ Binding(
                path = path_acum.add_direct_step( self ),
                identifier = identifier,
                value = self.context[ identifier ] ) ]

        # Ok, search the pieces
        bindings = []
        for piece in self.pieces:
            piece_bindings = piece.lookup_bindings(
                identifier,
                path_acum = path_acum.add_piece_step( self, piece ) )
            bindings.extend( piece_bindings )

        # return these bindings if any found in pieces
        if len(bindings) > 0:
            return bindings

        # Ok, no binding in hte pieces means we search our
        # parental representations *and* out parental pieces
        for parental_rep in self.is_representation_of:
            parental_bindings = parental_rep.lookup_bindings(
                identifier = identifier,
                path_acum = path_acum.add_parental_representation_step(
                    self,
                    parental_rep ) )
            bindings.extend( parental_bindings )
        for parental_pieces in self.is_piece_of:
            parental_bindings = parental_piece.lookup_bindings(
                identifier = identifier,
                path_acum = path_acum.add_parental_piece_step(
                    self,
                    parental_piece ) )
            bindings.extend( parental_bindings )

        # Ok, return any bindings from parental representations
        return bindings


    ##
    # A more human firendly representation
    def __str__(self):
        s = "Node<{0} #{1}reps, #{2}pieces id={3}>".format(
            self.natural_token_structure,
            len(self.representations),
            len(self.pieces),
            id(self) )
        return s
    def __repr__(self):
        return self.__str__()

    ##
    # returns a human-friendly representation of this node
    def human_friendly( self ):
        return "Node[{0}]".format( self.natural_token_structure.human_friendly() )

##========================================================================

##
# A indings represents an identifier/value pair along with
# the path taken to look it up.
Binding = collections.namedtuple( "Binding",
                                  [ 'path',
                                    'identifier',
                                    'value' ] )

##========================================================================
##========================================================================

##
# A TokenStructure is a structured ordered list of Tokens.
# These tokens are either strings or other TokenStructure objects
# This is just a type-defined List-of-List object
#
# TokenStructure objects are *immutable* and functional
class TokenStructure( object ):

    __slots__ = ( 'tokens', )

    ##
    # Creates a new sturcture with given tokens
    def __init__( self, tokens ):
        self.tokens = tokens

    ##
    # add a token, returning new structure
    # Token should be either a string or a TokenStructure 
    def add_token( self, tok ):
        t = list(self.tokens)
        t.append( tok )
        return TokenStructure( t )

    ##
    # A nice representation
    def __str__(self):
        s = "Tokens["
        s += "{0}".format( self.tokens )
        s += "]"
        return s
    def __repr__(self):
        return self.__str__()

    ##
    # A Human-friendly representation
    def human_friendly( self ):
        s = ' '.join(
            map(lambda t: "{0}".format(t) if not isinstance(t,TokenStructure) else t.human_friendly(),
                self.tokens ) )
        return s

    ##
    # Equality and has based on the internal list :)
    def __eq__( self, a ):
        if not isinstance(a, TokenStructure):
            return False
        return self.tokens == a.tokens
    def __hash__( self ):
        return hash( tuple(self.tokens) )

    
##========================================================================

##
# An atomic token-structure for a message
def message_token_structure( message ):
    return TokenStructure( [ message ] )

##========================================================================

##
# A top-level node that is just a message
def message_node( message ):
    return Node( message_token_structure( message ) )

##========================================================================
##========================================================================

##
#
def test_nodes_0():

    # create some nodes
    n0 = Node(TokenStructure([0]))
    n0.bind( 'j', 0 )
    for i in xrange( 1, 10 ):
        n = Node( TokenStructure( [ i ] ) )
        n0.add_representation( n )
        n.bind( 'i', i )

    # find the bindings
    bindings = n0.lookup_bindings( 'i' )

    logger.info( "Bindings for 'i': {0}".format( bindings ) )
    return n0

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
##========================================================================
