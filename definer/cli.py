import logging
logger = logging.getLogger( __name__ )

##
#
# A Command Line Interface for Interporeters.
#
# This is a simply interface which allows you to input raw
# data and then evaluate it using an interpreter.
# This also allows the user to see any prompts from the
# interpreter and to get metadata about prompts and interpreter

import re
import sys

import interpreter
import concept

##=========================================================================

##
# A command line interface
class CLI( object ):

    ##
    # Initialize with a simple interpreter
    # and given in/out streams
    def __init__( self ):
        self.interpreters = [ interpreter.InterpreterBase() ]
        self.current_interpreter_index = 0

    ##
    # A read-eval-print loop
    def repl( self,
              instream = sys.stdin,
              outstream = sys.stdout ):
        while self.current_interpreter_index is not None:
            self.read_eval_print( instream, outstream )

    ##
    # Read input from given stream and
    # evaluate it
    def read_eval_print( self,
                         instream = sys.stdin,
                         outstream = sys.stdout ):

        try:

            # prompt hte user by displaying the current
            # interpreter's current concept
            if self.current_interpreter_index is not None:
                self._show_header( self.interpreters[self.current_interpreter_index],
                                   outstream )
                self._discard_prompts( self.interpreters[self.current_interpreter_index])

            line = instream.readline()
            if line.startswith( ':/' ):

                # grab cli command and evaluate it
                cmdline = line[2:]
                self._evaluate_command_line( cmdline, instream, outstream )

            else:

                # send input to current interpreter
                self.interpreters[self.current_interpreter_index].interpret(line)

            # cleanup any done interpreters
            to_remove = []
            for i, p in enumerate( self.interpreters ):
                if p.is_done():
                    to_remove.append( i )
            if len(to_remove) == len(self.interpreters):
                self.current_interpreter_index = None

            # shift current interpretes to previous not done one
            while self.current_interpreter_index is not None and self.current_interpreter_index in to_remove:
                self.current_interpreter_index -= 1
                if self.current_interpreter_index < 0:
                    self.current_interpreter_index = len(self.interpreters) - 1

            # remove done interpreters
            for i in reversed( to_remove ):
                del self.interpreters[ i ]

        except:
            logger.exception("ERROR")


    ##
    # Discards all prompts for an interpreter by finishing them
    def _discard_prompts( self, interp ):
        for p in interp.state.prompts:
            p.finish()

    ##
    # Display hte header showing hte user what concept and propmts we are in
    def _show_header( self, interp, outstream ):
        outstream.write( "===\n" )
        self._show_concept( interp,
                            outstream )
        self._show_prompts( interp,
                            outstream )
        outstream.write( "===\n" )
        outstream.write( "> " )


    ##
    # Display the currnet concept
    def _show_concept( self, interp, outstream ):
        string = interp.state.current_concept.preferred_representation().human_friendly()
        outstream.write( string + "\n" )

    ##
    # Display any prompts
    def _show_prompts( self, interp, outstream ):
        for p in interp.state.prompts:
            string = p.state.current_concept.preferred_representation().human_friendly()
            outstream.write( "?> " + string + "\n\n" )


    ##
    # Evaluate a CLI command
    def _evaluate_command_line( self, cmdline, instream, outstream ):
        toks = re.split( r'\s+', cmdline )
        cmd = toks[0]
        if len(toks) > 1:
            args = toks[1:]
        else:
            args = []

        method = "_command_{0}".format( cmd )
        getattr( self, method )( args, instream, outstream )

    ##
    # List interpreters
    def _command_list( self, args, instream, outstream ):
        for i, interp in enumerate( self.interpreters ):
            s = "{0}".format( i )
            if i == self.current_interpreter_index:
                s += " *"
            else:
                s += "  "
            s += ": " + interp.state.current_concept.preferred_representation().human_friendly()
            outstream.write( s )
            outstream.write( "\n" )

    ##
    # Switch interpreter command
    def _command_switch( self, args, instream, outstream ):
        self.current_interpreter_index = int(args[0])

    ##
    # Finish the current interpreter
    def _command_finish( self, args, instream, outstream ):
        self.interpreters[self.current_interpreter_index].finish()

    ##
    # Creaete a new interpreted
    def _command_create( self, args, instream, outstream ):
        self.interpreters.append( interpreter.InterpreterBase() )

    ##
    # Shows the fully_expanded representation of the
    # current conept of the current interpreter
    def _command_show_expanded( self, args, instream, outstream ):
        c = self.interpreters[self.current_interpreter_index].state.current_concept
        for aidx in filter(lambda a: len(a.strip()) > 0, args):
            if aidx == ':':
                c = c.constituent_concepts
            else:
                idx = int(aidx)
                c = c.constituent_concepts[idx]
        if isinstance( c, list ):
            frep = map(concept.fully_expand_representations, c)
        else:
            frep = concept.fully_expand_representations( c )
        outstream.write( "{0}".format( frep ))
        outstream.write( "\n" )

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
