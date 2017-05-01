##
## Copyright Javier Velez <velezj@alum.mit.edu> May 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains the ase of UIs which dirve In/Out to interpreters

import sys

import interpreting

##========================================================================

##
# The basci UI which just displays the top-level nodes of prompts
# and feeds one line of input to the interpreter
class BasicUI( object ):

    ##
    # Creates a new UI with a new interpreter
    def __init__( self,
                  interpreter = interpreting.InterpreterBase('default') ):
        self.interpreter = interpreter

    ##
    # The bacis REPL
    def repl( self,
              in_stream = sys.stdin,
              out_stream = sys.stdout ):

        while not self.interpreter.is_done():
            
            # show the curent prompts
            self.show_prompts( out_stream )

            # finish the prompts since htis is a basic UI
            self.finish_prompts()
            
            # show the input prompt and grab input
            raw_in = self.grab_input( in_stream )
            
            # evalute/interpret the input
            self.interpreter.interpret_full( raw_in )

    ##
    # Show the prompts for the current interpreter
    def show_prompts( self, out_stream ):

        # first show any prompts
        for i, p in enumerate(self.interpreter.state.prompts):
            for j, node in enumerate(p.state.toplevel_nodes):
                out_stream.write( "{0:02d}.{1:02d}) {2}\n".format(
                    i, j, node.natural_token_structure.human_friendly() ) )
            out_stream.write( "\n" )

        # now show the current node
        cur_node_string = "None"
        if self.interpreter.state.current_node is not None:
            cur_node_string = self.interpreter.state.current_node.natural_token_structure.human_friendly()
        out_stream.write( cur_node_string )
        out_stream.write( "\n" )

        # show the interpreter name and prompt for input
        out_stream.write( "{0}>> ".format(self.interpreter.name) )

    ##
    # Finish and remove hte prompts
    def finish_prompts(self):
        for p in self.interpreter.state.prompts:
            p.finish()
        del self.interpreter.state.prompts[:]

    ##
    # read a line of input
    def grab_input( self, in_stream ):
        return in_stream.readline()
        

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
