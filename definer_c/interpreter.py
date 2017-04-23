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

        # first, unlink the command concept from the concept
        # graph since we are going to fully use it and we
        # don't want it poluting the namespace
        c.unlink()

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

        logger.info( "[{name}]: Starting _resolve_concept_reference for concept '{0}'".format(
            c.debug_string(),
            name = id(self) ) )

        # Ok, grab teh fully expanded forms of representations for
        # this concept
        c_fully_expanded_reps = concept.fully_expand_representations( c )
        logger.info( "[{name}]:   fully expanded to: {0}".format(
            c_fully_expanded_reps,
            name=id(self) ) )

        # now, for each known concept, check if there is a match
        matching_concepts = []
        for c0 in self._all_concepts( state ):

            # no self references
            if c0 is c:
                continue

            logger.info( "[{name}]: checking match with {0}".format(
                c0.debug_string(),
                name=id(self) ) )

            # chekc if match
            if concept.any_rep_match( c_fully_expanded_reps,
                                      c0 ):
                logger.info( "[{name}]: match found!".format(
                    name=id(self) ) )
                matching_concepts.append( c0 )

        # log some things
        logger.info( "[{name}]: resolved #{0} refs for '{1}'".format(
            len(matching_concepts),
            c.preferred_representation().human_friendly(),
            name=id(self) ) )
        
        # return all the matches found
        return matching_concepts


    ##
    # Given a Concept and a State, checks for a "matchind" concept
    # that allows for the avility to be a sub-structure match.
    # Unlike _resolve_concept_reference which enforces  a strict
    # structure match, here we allow the Concept to be matched with
    # another that has the subset in hte right order in the structure
    # but could have more.
    #
    # The return value is a List[ List[ BreakMatchpoint ] ] objects,
    # where a BreakMatchpoint determines where in the substructure the match
    # occurs
    def _resolve_concept_substructure_reference( self, c, state ):

        logger.info( "[{name}]: Starting _resolve_concept_substructure_reference for concept '{0}'".format(
            c.debug_string(),
            name = id(self) ) )

        # Ok, grab teh fully expanded forms of representations for
        # this concept
        c_fully_expanded_reps = concept.fully_expand_representations( c )
        logger.info( "[{name}]:   fully expanded to: {0}".format(
            c_fully_expanded_reps,
            name=id(self) ) )

        # now, for each known concept, check if there is a match
        matching_concepts = []
        for c0 in self._all_concepts( state ):

            # no self references
            if c0 is c:
                continue

            logger.info( "[{name}]: checking match with {0}".format(
                c0.debug_string(),
                name=id(self) ) )

            # chekc if match
            m = concept.any_rep_substructure_matches( c_fully_expanded_reps,
                                                      c0 )
            if m is not None and len(m) > 0:
                logger.info( "[{name}]: #{0} matches found!".format(
                    len(m),
                    name=id(self) ) )
                matching_concepts.append( m )

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
    # Returns true iff the given SubstructureMatch represents a
    # lifttable substructure.
    #
    # Liftale substructures do *not* span partially multiple concepts.
    def _is_liftable_substructure_match( self, subm ):

        # ok, check the number of partial concepts
        num_partial = 0
        for r in subm.constituent_ranges:
            if r != SubstructureMatch.WHOLE_CONCEPT:
                num_partial += 1

        # we're good is no partial structures
        if num_partial == 0:
            return True

        # we're also good if hte partial matches are in only a single concept
        if len(subm.concepts) == 1:
            return True

        # otherwise we have a setting where we would have to "split"
        # across different concepts and merge into a new one, which
        # would break the concept graph single-parent constraint
        return False

    ##
    # "Lift" a substrcutre Match (if if can be lifted)
    #
    # returns a new Concept which has been added to the concept graph
    def _lift_substructure_match( self, subm ):
        if not self._is_liftable_substructure_match( subm ):
            return None

        # ok, check whether we even have to split a concept or jsut
        # add a parent layer
        if all(map(lambda r: r == SubstructureMatch.WHOLE_CONCEPT),
               subm.constituent_ranges ):

            # we jsut need to add a parent.
            # what a nice case we have here :) ... or not heheheh

            # ok, so we need to first find the latest common ancestor
            # for each of the wholly used nodes
            # Note: tehre is always a root so we always have one ancestor :)
            ancestors = map(lambda c: concept.ancestors(c),
                            subm.concepts)
            longest_common_ancestors = longest_common_prefix( ancestors )
            ancestral_parent = longest_common_ancestors[-1]

            # ok, now we need to choose the constituents of the *ancestor* as
            # the constituents of hte new concept
            ancestral_constituents = []
            for ancs in ancestors:
                pass 
            parent_c = basic_grammar_concept.BasicGrammarConcept(
                parent_concept = 

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
        arg_c = cmd.constituent_concepts[0]
        if len(arg_c.constituent_concepts) == 1:
            arg_c = arg_c.constituent_concepts[0]
        concept_refs = self._resolve_concept_reference(
            arg_c,
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
    # Performs the EnterPartial command.
    #
    # This will try to resolve the given argument as a Substructure match
    # (hence the "partial" part) and will
    # hange the current concept if a single reference was found
    # This will create a new Concept in the concept graph with the
    # substructure match if need be
    #
    # This new concept creation will only succeed *if* the substructure
    # consists of ranges only in the first and last concept so
    # that it can be "lifted" with no problems
    def _command_enter_partial( self, cmd, state ):

        logger.info( "[{name}]: COMMAND[enter_concept] started".format(
            name=id(self) ) )

        # ok, look for concept reference in the args
        arg_c = cmd.constituent_concepts[0]
        if len(arg_c.constituent_concepts) == 1:
            arg_c = arg_c.constituent_concepts[0]
        matches = self._resolve_concept_substructure_reference(
            arg_c,
            state )

        # show message if no concept reference found or too many
        if len(matches) == 0:
            state.prompts.append(
                MessagePrompt(
                    "Could not find concept to enter!",
                    self ) )
        elif len(matches) > 1:
            state.prompts.append(
                MessagePrompt(
                    "Concept to enter is Ambiguous found #{0} matches".format(
                        len(matches) ),
                    self ) )
        else:

            # ok, found a single match, see if we can create a new concept
            # for it

            # check if it is just a single concept, in which case
            # we can just change to it
            if self._substructure_match_is_whole( matches[0] ):
                
                state.current_concept = matches[0].concepts[0]
                logger.info( "Changing current_concept to '{0}'".format(
                    state.current_concept.preferred_representation().human_friendly()) )

            # ok, now check if it is a liftable substructure
            elif self._is_liftable_substructure_match( matches[0] ):

                # it is liftable, so lift it and assign new lifted concept
                # as current conceopt
                newc = self._lift_substructure_match( matches[0] )
                state.current_concept = newc
                logger.info( "Changing current_concept to '{0}'".format(
                    state.current_concept.preferred_representation().human_friendly()) )

            else:

                # we are not a single or liftable substructure!
                # this is an error
                state.prompts.append(
                    MessagePrompt(
                        "Found substructure is not liftable as a concept, concept graoh would break if substructure treated as a unit. Try selecting a higher parent structure to enter which encompases all children",
                        self ) )
                
                

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
