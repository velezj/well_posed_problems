##
## Copyright Javier Velez <velezj@alum.mit.edu> April 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains the parsing interface to go from
# raw input into a Script structure

import textx.metamodel

##========================================================================

##
# A Parser is just an encompsulation of a grammar and can
# also parse raw input
class Parser( object ):

    ##
    # Create a new parser with given grammar
    def __init__( self,
                  grammar_file = 'grammar.tx' ):
        self.grammar_file = grammar_file
        self.metamodel = textx.metamodel.metamodel_from_file( 'grammar.tx' )

    ##
    # Parse a full string of raw input.
    # This must be the full input, not a partial parse
    def parse_full( self, raw ):
        
        # We just apply our grammar
        model = self.metamodel.model_from_str( raw )
        return model


##========================================================================
