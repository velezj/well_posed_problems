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

import collections

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
##========================================================================

##
# returns a full stirng repreentation of a parsed expression
def expression_full_string( expr ):

    # ok, if we are a sequence then return string representation of
    # mapping with expression_full_string
    if isinstance( expr, (list,tuple) ):
        res = map(expression_full_string, expr )
        s = u"["
        for i, v in enumerate(res):
            s += v
            if i < len(res) - 1:
                s += u","
        s += u"]"
        return s

    # ok, check if we are not an instance of a textx class, in which case
    # we will return the string representation of this object
    if not isinstance( expr, textx.metamodel.TextXClass ):
        return unicode( expr )

    # Ok, we are a textx class so find all the fields (if any) and
    # return them as a dictionary tring representation
    fields = expr._tx_attrs
    field_map = collections.OrderedDict()
    for f in fields:
        v = getattr( expr, f )
        field_map[ f ] = expression_full_string( v )
    s = u"EXPR["
    for i, (f, v) in enumerate(field_map.iteritems()):
        s += u"{0}={1}".format( f, v )
        if i < len(field_map) - 1:
            s += u"  "
    s += u"]"
    return s

##========================================================================
##========================================================================
##========================================================================
