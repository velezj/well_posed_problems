import logging
logger = logging.getLogger( __name__ )

##
#
# This file contians a particular Concept subclass which uses a
# defined TextX basic grammar to parrse user input into Concepts.
#
# This is the default classic Concept

import concept
import python_definition

from textx import metamodel


##=========================================================================

##
# Defines a Concept which uses the "basic_grammar.tx" TextX grammar
# to parse user input
class BasicGrammarConcept( concept.ConceptBase ):

    ##
    # Creates a new concept with the given arguments (from ConceptBase)
    def __init__( self,
                  *args,
                  **kw):
        concept.ConceptBase.__init__( self, *args, **kw )
        grammar_file = kw.get( 'grammar_file', 'basic_grammar.tx' )
        self.mm = metamodel.metamodel_from_file( grammar_file )

    ##
    # Parse a raw user input into Concepts.
    #
    # This will use the TextX basic grammar and parse the input
    # assuming it is a basic_grammar.Program.
    # Each basic_grammar.Symbol is treated as a Concept itself.
    # basic_grammar.Command are treated as CommandConcept instances.
    # basic_grammar.ContextSwitch are treated as
    # BasicGrammarConcept with a definition set
    def parse( self, raw ):

        # ok, grab the parsed model from the raw input
        model = self.mm.model_from_str( raw )

        # ok, transform parsing model to concepts
        concepts = []
        for expr in model.expressions:
            stype = expr.__class__.__name__
            if stype == 'Statement':
                res = self._concepts_from_statement( expr, self )
                concepts.extend( res )
            elif stype == 'ContextSwitch':
                res = self._concepts_from_context_switch( expr, self )
                concepts.extend( res )
            elif stype == 'Command':
                res = self._concepts_from_command( expr, self )
                concepts.extend( res )
            else:
                raise RuntimeError( "Unknown basic_gramma object '{0}'".format( expr ) )

        # return the parsed concepts
        return concepts


    ##
    # Parse a basic_grammar.Statement into a list of concepts
    def _concepts_from_statement( self, statement, parent ):
        res = []
        # first create a concept for hte statement and
        # use it as the parent of all symbol concepts
        state_parent = BasicGrammarConcept(
            parent_concept = parent,
            constituent_concepts = [] )

        # create the symbol concepts, linked to prent statement
        for symbol in statement.parts:
            c = self._symbol_concepts( symbol, state_parent )
            res.extend( c )

        # return the statement concept
        return [ state_parent ]

    ##
    # return a list of concepts for hte given symbol
    # using given parent
    def _symbol_concepts( self, symbol, parent ):
        stype = symbol.__class__.__name__
        if stype == 'TokenSymbol' or isinstance( symbol, (str,unicode) ) :
            return [ self._token_symbol_concept( symbol, parent ) ] 
        elif stype == 'BlockSymbol':
            return self._block_symbol_concepts( symbol, parent )
        else:
            raise RuntimeError( "Unknown basic_grammar.Symbol subtype '{0}'".format( symbol ) )

    ##
    # Returns a new single concept fromgiven symbol (a string)
    # with given parent
    def _token_symbol_concept( self, symbol, parent ):
                        
        reps = []
        reps.append( concept.Representation(
            symbol,
            level=concept.Representation.LEVEL_INPUT_MORPHISM) )
        reps.append( concept.Representation(
            "#|Symbol:{0}|#".format( symbol ),
            level = concept.Representation.LEVEL_SYSTEM_INFORMATION ) )
        c = BasicGrammarConcept(
            parent_concept = parent,
            constituent_concepts = [],
            context = concept.Context(),
            representations = reps)
        return c

    ##
    # Returns a new single concept for this basic_grammar.BlockSymbol
    # using given parent ocncept
    def _block_symbol_concepts( self, symbol, parent ):        
        # ok, a block symbol is in fact jsut a statement so recurse
        res = self._concepts_from_statement( symbol.statement, parent )
        return res

    ##
    # returns a lsit of concepts from a basic_grammar.Command
    def _concepts_from_command( self, command, parent ):

        # ok, we create a top-level concept that is the
        # command itself
        # and create the concepts for the arguments
        cmd = concept.CommandConcept(
            parent_concept = parent,
            command_identifier = command.cmd,
            arg_concepts = [] )
        arg_concepts = self._concepts_from_statement( command.args, cmd )
        return [ cmd ]

    ##
    # returns a list of concepts from a basic_grammar.ContextSwitch
    def _concepts_from_context_switch( self, context_switch, parent ):

        # Ok, a ContextSwitch is treated a a PythonDefinition
        # so we create a concept with a definition in it
        if not ( context_switch.context == 'python' or context_switch.context == '' or context_switch.context is None):
            raise RuntimeError( "Unknown contexts in ContextSwitch: '{0}'".format( context_switch.context ) )


        c = concept.BoxConcept(
            parent_concept = parent,
            value = context_switch )
        python_def = python_definition.PythonDefinition(
            concept = c,
            source = context_switch.body )
        c.context.bind_definition( python_def )

        return [ c ]
    
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
##=========================================================================
##=========================================================================
