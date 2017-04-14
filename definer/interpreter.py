import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains the base mechanism for an Interpreter of Concepts.
# This is the main UI funcitonality which keeps a running state
# of Concepts input/seen so far as well as allows the user to
# perform actions such as adding bindings and testing of
# well-definedness
#
# The main idea behind an interpreter are:
#   1) The State of the system (including the current Concept scope)
#   2) An ability to perform actions based on CommandConcepts
#   3) A way to match input Concepts with previous concepts
#      to keep a set of seen concepts
#   4) A way to interact with the user with prompts

import copy

import concept
import basic_grammar_concept

##=========================================================================
##=========================================================================

##
# The base interpreter.
#
# The State is very simple:
#    1) the current concept
#    2) The set of top-level concepts
#    3) A list of prompts (InterpreterBase instances :) )
class InterpreterBase( object ):

    ##
    # The State class for this interpreter
    class State( object ):

        ##
        # Creates a new state with given current concept,
        # given top-level concepts and prompt
        def __init__( self,
                      current_concept = None,
                      top_level_concepts = [],
                      prompts = [] ):
            self.current_concept = current_concept
            self.top_level_concepts = top_level_concepts
            self.prompts = prompts

        ##
        # Shallow copy of state
        def shallow_copy(self):
            return State( self.current_concept,
                          copy.copy( self.top_level_concepts ),
                          copy.copy( self.prompts ) ) 

        ##
        # Creates a new initial state
        @classmethod
        def initial_state(cls):
            c = basic_grammar_concept.BasicGrammarConcept(
                parent_concept = None,
                constituent_concepts = [] 
            )
            return cls( current_concept = c,
                        top_level_concepts = [ c ],
                        prompts = [] )


    ##
    # Creates a new Interpreter with given initial prompt and
    # state
    def __init__( self,
                  init_state = State.initial_state() ):
        self.state = init_state

    ##
    # An interpreter is "done" when it's state is None
    def is_done(self):
        return self.state is None

    ##
    # Finish this prompt by setting it's state to None
    def finish(self):
        self.state = None

    ##
    # Interpret hte given raw user input
    def interpret( self,
                   raw ):
        self._interpret_raw( raw, self.state )
        self.remove_done_prompts()

    ##
    # Removes any prompts from the state which are done
    def remove_done_prompts(self):
        to_remove = []
        for i, p in enumerate( self.state.prompts ):
            if p.is_done():
                to_remove.append( i )
        for i in reversed(to_remove):
            del self.state.prompts[i]
            

    ##
    # Interpret raw input given a State
    def _interpret_raw( self, raw, state ):

        # Ok, grab the current concept from state and use it
        # to parse the raw input
        logger.info( "[{name}] going to parse '{0}'".format(
            raw,
            name = id(self) ) )
        c = state.current_concept
        parsed_concepts = c.parse( raw )
        logger.info( "[{name}] parsed #{0} concepts".format(
            len(parsed_concepts),
            name = id(self) ) )


        # Ok, now interpret each concept in turn
        for c in parsed_concepts:
            self._interpret_concept( c, state )

    ##
    # The main evaluation of a concept.
    #
    # This will change given state.
    def _interpret_concept( self, c, state ):
        
        # we really only care about CommandConcepts
        if not isinstance( c, concept.CommandConcept ):
            return

        # Ok, dispatch based on the command here for subclasses
        method_name = "_command_{0}".format( c.command_identifier )
        if hasattr( self, method_name ):
            getattr( self, method_name )( c, state )
        else:

            # ok, we do not have a method for this command
            # so we will treat it as a syntax error :)
            # This will just have a very simple prompt telling
            # the user of the error
            state.prompts.append(
                MessagePrompt(
                    "Error: Unknown command '{0}'".format(
                        c.command_identifier ),
                    self ) )

                            
                    

    ##
    # Given a Concept and a State,
    # searches the State for a "matching" concept.
    # This matching is done via the Representations of the concepts.
    # This allows us to resolve references input by the
    # user by saying that two concepts are *the same*
    #
    # We resolve references by:
    #    1) Look for eactly hte same structural representations of two concepts
    #    2) If the structures are the same, then look for the same
    #       representation-as-a-string equality
    #
    # Returns all matching concepts
    def _resolve_concept_reference( self, c, state ):

        # Ok, grab teh fully expanded forms of representations for
        # this concept
        c_fully_expanded_reps = concept.fully_expand_representations( c )

        # now, for each known concept, check if there is a match
        matching_concepts = []
        for c0 in self._all_concepts( state ):

            # chekc if match
            if concept.any_rep_match( c_fully_expanded_reps,
                                      c0 ):
                matching_concepts.append( c0 )

        # log some things
        logger.info( "[{name}]: resolved #{0} refs for '{1}'".format(
            len(matching_concepts),
            c.preferred_representation().human_friendly(),
            name=id(self) ) )
        
        # return all the matches found
        return matching_concepts



    ##
    # retunrs all of the concepts in the given state.
    # This will be a flattented list of all the concept including
    # intermediate concepts which have children
    def _all_concepts( self, state ):

        def _dfs( c, q ):
            res = []
            if c not in q:
                res.append( c )
                q.add( c ) 
                for c0 in c.constituent_concepts:
                    res.extend( _dfs( c0, q ) )
            return res

        q = set([])
        res = []
        for c in state.top_level_concepts:
            res.extend( _dfs( c, q ) )
        return res


    ##
    # Interpret an EnterConcept command
    #
    # This tries to match the argument concept with any known
    # concepts and sets the matching concept to the current_concept
    # in the state
    def _command_enter_concept( self, cmd, state ):

        logger.info( "[{name}]: COMMAND[enter_concept] started".format(
            name=id(self) ) )

        # ok, look for concept reference in the args
        concept_refs = self._resolve_concept_reference(
            cmd.constituent_concepts[0],
            state )

        # show message if no concept reference found or too many
        if len(concept_refs) == 0:
            state.prompts.append(
                MessagePrompt(
                    "Could not find concept to enter!",
                    self ) )
        elif len(concept_refs) > 1:
            state.prompts.append(
                MessagePrompt(
                    "Concept to enter is Ambiguous found #{0} matches".format(
                        len(concept_refs) ),
                    self ) )
        else:

            # ok, found a single match, change the current concept to it
            state.current_concept = concept_refs[0]
            logger.info( "Changing current_concept to '{0}'".format(
                state.current_concept.preferred_representation().human_friendly()) )
            

    ##
    # Performs the LeaveConcept command
    #
    # This just sets the current concept to hte parent of the
    # current concept
    def _command_leave_concept( self, cmd, state ):

        logger.info( "[{name}]: COMMAND[leave_concept] started".format(
            name=id(self) ) )

        if state.current_concept.parent_concept is not None:
            state.current_concept = state.current_concept.parent_concept
            logger.info( "Changing current_concept to parent: '{0}'".format(
                state.current_concept.preferred_representation().human_friendly()) )
        else:

            # hmm, it's an error to leave but we're going to ignore it :)
            logger.info( "Ignoring trying to leave_concept with a current top-leve lconcept, curret_concept stays the same since it it topmost and has no parent" )

    ##
    # Perofmrs a binding in hte current concept's context
    def _command_bind( self, cmd, state ):

        logger.info( "[{name}]: COMMAND[bind] started".format(
            name=id(self) ) )

        # make sure we have exactly two args
        if len(cmd.constituent_concepts[0].constituent_concepts) != 2:
            state.prompts.append(
                MessagePrompt(
                    "Error: bind must be given exactly two arguments: a symbol and a value",
                    self ) )
        else:

            # ok, now we will resolve references
            symbol_concept = cmg.constituent_concepts[0].constituent_concepts[0]
            value_concept = cmd.constituent_concepts[0].constituent_concepts[1]

            # resolve symbol reference, set ot None if error
            symbol_refs = self._resolve_concept_reference(
                symbol_concept,
                state )
            if len(symbol_refs) == 1:
                symbol_concept = symbol_refs[0]
            elif len(symbol_refs) > 1:
                state.prompts.append(
                    MessagePrompt(
                        "Ambiguous concept reference as first argument of bind ocmmand, mathched '{0}' with #{1} matches".format(
                            symbol_concept.preferred_representation.human_friendly(),
                            len(symbol_refs) ) ) )
                symbol_concept = None

            # resolve value concept, set to None if error
            value_refs = self._resolve_concept_reference(
                value_concept,
                state )
            if len(value_refs) == 1:
                value_concept = value_refs[0]
            elif len(value_refs) > 1:
                state.prompts.append(
                    MessagePrompt(
                        "Ambiguous concept reference as second argument of bind ocmmand, mathched '{0}' with #{1} matches".format(
                            value_concept.preferred_representation.human_friendly(),
                            len(value_refs) ) ) )
                value_concept = None

            # perform bind if we had no error
            if symbol_concept is not None and value_concept is not None:
                
                # ok, grab the preffered representaiton of the symbol to bind to
                symbol_string = symbol_concept.preferred_representation().human_friendly()

                state.curret_concept.bind( symbol_string,
                                           value_concept )
                logger.info( "Created binding '{0}' => {1}".format(
                    symbol_string,
                    value_concept.preferred_representation().human_friendly()))
            
            
##=========================================================================
##=========================================================================

##
# A simple prompt which just contains a single message and nothing
# can be done iwth it
class MessagePrompt( InterpreterBase ):

    ##
    # Just contains a message and  parent interpreter
    def __init__( self,
                  message,
                  parent_interpreter ):
        self.parent_interpreter = parent_interpreter
        c = concept.BoxConcept(
            parent_concept = parent_interpreter.state.current_concept,
            value = message )
        state = InterpreterBase.State(
            current_concept = c,
            top_level_concepts = [ c ] )
        InterpreterBase.__init__( self, state )

        

##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
##=========================================================================
