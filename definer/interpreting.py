##
## Copyright Javier Velez <velezj@alum.mit.edu> April 2017
## All Rights Reserved
##

import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains the Interpreter interface for actually
# computing and evaluating a parsed input

import parsing
import framework
import node_utilities


##========================================================================

##
# The base interpreter class.
#
# This has a State which includes the following:
#    1) top-level Nodes
#    2) Prompts
#    3) current Node
class InterpreterBase( object ):

    ##
    # The state class
    class State( object ):

        ##
        # Create a new state with given top-level nodes
        # and prompts
        def __init__( self,
                      current_node = None,
                      toplevel_nodes = [],
                      prompts = [] ):
            self.current_node = current_node
            self.toplevel_nodes = list(toplevel_nodes)
            self.prompts = list(prompts)


    ##
    # Creates a new interpreter with a name and parser and state
    def __init__( self,
                  name,
                  parser = parsing.Parser(),
                  state = None ):
        self.name = name
        self.parser = parser
        self.state = state
        self.command_callbacks = {}


    ##
    # returns true if this interpreter is done
    def is_done(self):
        return self.state is None

    ##
    # Finished this interpreter
    def finish( self ):
        self.state = None

    ##
    # Add a new top-level node to state
    def add_toplevel_node( self, node ):
        if self.state is not None:
            self.state.toplevel_nodes.append( node )
        else:
            raise RuntimeError( "Can not add top-level node to finished/done interpreted with None state!" )

    ##
    # Add a command callback
    # which will be called when a given command (by name) is evaluated
    #
    # Callback is f( InterpreterBase, cmd_id, string ) => None
    # where cmd_id is hte name of the command and the second argument
    # is the full line string given to the command (unparsed :) )
    def add_command_callback( self,
                              cmd,
                              callback ):
        if cmd not in self.command_callbacks:
            self.command_callbacks[ cmd ] = []
        self.command_callbacks[ cmd ].append( callback )

    ##
    # Interpret a full input.
    # This will first parse the input then interpret the
    # parsed results, changing the state
    def interpret_full( self, raw ):

        # it's an error if we have no state
        if self.state is None:
            raise RuntimeError( "Unable to interprent when state is None" )

        # first parse the input
        model = self.parser.parse_full( raw )

        # now interpret each model expression
        for expr in model.expressions:
            self._evaluate_expression( expr )

    ##
    # Evaluates a single expression parsed from input
    def _evaluate_expression( self, expr ):

        # Dispatch based on expression type
        if self._expression_is_statement( expr ):
            self._evaluate_statement( expr )
        elif self._expression_is_command( expr ):
            self._evaluate_command( expr )
        elif self._expression_is_bind( expr ):
            self._evaluate_bind( expr )
        elif self._expression_is_context_expression( expr ):
            self._evaluate_context_expression( expr )
        else:
            self.error_prompt( "Unknown expression type '{0}'".format( expr ) )


    ##
    # returns true if this is a Statement expression
    def _expression_is_statement( self, expr ):
        return expr.__class__.__name__ == 'Statement'
    
    ##
    # returns true if this is a Command expression
    def _expression_is_command( self, expr ):
        return expr.__class__.__name__.endswith( 'Command' )

    ##
    # returns true if this is a Bind expression
    def _expression_is_bind( self, expr ):
        return expr.__class__.__name__ == 'BindExpression'

    ##
    # returns true if this is a ContextExpression expression
    def _expression_is_context_expression( self, expr ):
        return expr.__class__.__name__ == 'ContextExpression'

    ##
    # Evaluate a Command expression
    def _evaluate_command( self, expr ):

        # grab the command identifier
        cmd = expr.cmd

        # ok, see if we have a registerd callbacks
        if cmd in self.command_callbacks:

            for cb in self.command_callbacks[ cmd ]:
                cb( self, cmd, expr.arg )

        else:
            
            # now, lookup a method in this object
            methodname = "_execute_{0}".format( cmd )
            if not hasattr( self,
                            methodname ):
                self.error_prompt( "Unknwon Command encountered '{0}'".format(
                    cmd ) )

            # ok, grab the method and call it
            if hasattr( self, methodname ):
                executor = getattr( self,
                                    methodname )
                executor( cmd, expr.arg )
            else:

                # signal error of unknown command
                self.error_prompt( "Unknown command '{0}'".format( cmd ) )


    ##
    # Evaluate a Bind expression
    def _evaluate_bind( self, expr ):

        # ok, we will jsut use hte current Node's context
        # and apply the binding
        if self.state.current_node is None:
            self.error_prompt( "Can not evalute bind expression for identifier '{0}', not current Node to grab a Context from!".format( expr.slot ) )
            return

        # ok, now we will parse the bind expression value to see if
        # it is a Plain-ol-datatype or a Reference
        value = expr.binding

        # ok, PODs are easy
        if isinstance( value, (str,unicode,bool,int,float)):

            # jsut bind in contenxt of current node
            self.state.current_node.bind(
                expr.slot,
                value )
            self.message_prompt( "Added POD Binding '{0}' = '{1}'".format(
                expr.slot,
                value ) )

        # Ok, see if we are an explicit reference
        elif value.__class__.__name__ == 'ExplicitNodeReference':

            # ok, find the node we are ferering to by id
            node = self._find_node_by_id( value.id )

            # if no node, this is an error
            if node is None:
                self.error_prompt( "Unable to find Node referenced by slot '{0}' with id '{1}'".format( expr.slot, value.id ) )
                return

            # Ok, found node so make binding
            self.state.current_node.bind(
                expr.slot,
                node )
            self.message_prompt( "Added binding of explicit node, slot '{0}' = node id={1}".format(
                expr.slot,
                node.node_id() ) )

        # Check if we are an implciit reference
        elif value.__class__.__name__ == 'ImplicitReference':

            # try to find a node for hte implicit reference
            nodes = self.find_nodes_by_implicit_reference( value.ref )

            # if no node, this is an error
            if nodes is None or len(nodes) == 0:
                self.error_prompt( "Unable to find Node referenced (implicitly) for slot '{0}' as '{1}'".format( expr.slot, value.ref ) )
                return

            # if more than one node, this is ambiguous
            if len(nodes) > 1:
                self.error_prompt( "Found #{0} matching nodes for implicit reference slot '{1}' as '{2}'".format(
                    len(nodes),
                    expr.slot,
                    value.ref ) )
                return
            
            # Ok, found node so make binding
            self.state.current_node.bind(
                expr.slot,
                nodes[0] )
            self.message_prompt( "Added binding from implicit references, slot '{0)' = node id={1}".format(
                expr.slot,
                nodes[0].node_id() ) )
            
        else:

            # unknown binding type
            self.error_prompt( "Unknwon binding type '{0}', slot={1}, binding={2}".format( expr, expr,slot, expr.binding ) )
            return



    ##
    # Evaluates a statement
    def _evaluate_statement( self, expr ):

        # ok, we will by default simply
        # covert the statement into a node and add
        # it as a representation of the current node.
        # If no current node, ti will become the current
        # node and be a top-level node
        node = self._statement_to_node( expr )
        if self.state.current_node is not None:
            self.state.current_node.add_representation( node )
        else:
            self.add_toplevel_node( node )
            self.state.current_node = node

    ##
    # Convert from a Statement to a Node representing it
    def _statement_to_node( self, expr ):

        return framework.Node(
            self._statement_to_token_structure( expr ) )

    ##
    # Convert a Statment to a TokenStructure
    def _statement_to_token_structure( self, expr ):

        # We will convert ubsstatments into TokenSequences :)
        if isinstance( expr, list):
            toks = map(lambda t: self._statement_to_token_structure( t ), expr )
            return framework.TokenStructure( toks )

        # A statement should become a tokensequence of hte parts
        if expr.__class__.__name__ == 'Statement':

            # special case where we only have a single Statement as part
            # we will flatten this
            if len( expr.parts ) == 1 and expr.parts[0].__class__.__name__ == 'Statement':
                return self._statement_to_token_structure( expr.parts[0] )

            # we jsut return the tokensewuence of the parts
            return self._statement_to_token_structure( expr.parts )

        # Ok, not a list or a Statment menas we are a token, pass thorugh
        return expr


    ##
    # Evaluate a ContextExpression
    def _evaluate_context_expression( self, expr ):

        if self.state.current_node is None:
            self.error_prompt( "We cannot have a ContextExpression or Definition without having a current node" )
            return

        # Ok, we will simply attach the expression as
        # a python definition to the current node
        pydef = defining.PythonDefinition(expr.body)
        self.state.current_node.bind_definition( pydef )
        self.message_prompt( "Bound definition of current node" )

    ##
    # Add a new message prompt for an error
    def error_prompt( self, message, name="Error" ):
        self.state.prompts.append( ErrorPrompt(
            parent = self,
            message = message,
            name = name ) )

    ##
    # A a message prompt
    def message_prompt( self, message, name = 'Message' ):
        self.state.prompts.append( MessagePrompt(
            parent = self,
            message = message,
            name = name ) )


    ##
    # Find a node by a given id.
    # We return the found node, or None
    def _find_node_by_id( self, node_id ):

        # we will simply walk the node graph, returning when
        # we have found a node with the given id
        found_node = None
        def _visit(node):
            if node.node_id() == node_id:
                found_node = node
        def _terminate( q, visited):
            return found_node is not None
        node_visitor = node_utilities.NodeVisitor(
            visitor=_visit,
            terminator=_terminate )
        node_visitor.visit( self.state.toplevel_nodes )

        # ok, return found_node
        return found_node

    ##
    # Find a node by an 'implicit" reference.
    # This will find a set of nodes which have the same TokenStructure
    # as the given reference
    def find_nodes_by_implicit_reference( self, reference ):

        # ok, so a reference is a Statement so first grab the
        # TokenStructure for the references
        ref_token_structure = self._statement_to_token_structure( reference )

        # now we will find all nodes in the node graph with the
        # exct same token structure
        found_nodes = []
        def _visit(node):
            if node.natural_token_structure == ref_token_structure:
                found_nodes.append( node )
        node_visitor = node_utilities.NodeVisitor(
            visitor=_visit )
        node_visitor.visit( self.state.toplevel_nodes )

        # ok, return hte nodes
        return found_nodes


    ##
    # The 'Finish' command.
    # It just finished this interpreter
    def _execute_finish( self, cmd, arg ):
        self.finish()

    ##
    # The 'Enter' command.
    # This will take as na argument a Reference (will pe parsed that way)
    # and will change the current node to that node
    def _execute_enter( self, cmd, arg ):

        # ok, see what type of reference we have
        if arg.__class__.__name__ == 'ExplicitNodeReference':

            # ok, find the node we are ferering to by id
            node = self._find_node_by_id( arg.id )

            # if we cannot find a node, we cannot enter it
            if node is None:
                self.error_prompt( "Cannot enter node referenced by id '{0}', node not found in node-graph".format( arg.id ) )
                return

            # ok, set the current node to this node
            self.state.current_node = node
            self.message_prompt( "Changed current node to id={0}".format(
                self.state.current_node.node_id() ) )

        elif arg.__class__.__name__ == 'ImplicitReference':

            # ok, so here we will try to find all the nodes referenced
            nodes = self.find_nodes_by_implicit_reference( arg.ref )

            # if we have more than one node matching, this in ambiguous
            if len(nodes) > 1:
                self.error_prompt( "Anbiguous reference for entering node, found #{0} nodes which match implicit reference '{1}'".format(
                    len(nodes),
                    parsing.expression_full_string( arg.ref ) ) )
                return

            # if we find exactly one node, then we just change current node
            if len(nodes) == 1:
                self.state.current_node = nodes[0]
                self.message_prompt( "Found single node from implicit reference, changed current node to id={0}".format(
                    self.state.current_node.node_id() ) )

            else:
                # ok, having no found references means we want to make a new *piece*
                # so let's make it
                piece = framework.Node(
                    self._statement_to_token_structure( arg.ref ) )
                self.state.current_node.add_piece( piece )

                # now we also want to set that piece as the current node :)
                self.state.current_node = piece
                self.message_prompt( "Created new piece from implicit reference and changed current node to it, id={0}".format(
                    self.state.current_node.node_id() ) )

        else:

            self.error_prompt( "Unknown argument given to enter command! '{0}'".format( arg ) )
            return
            
        
##========================================================================

##
# A Prompt is just an InterpreterBase that also has a parent .
# Subclasses of Prompts will have functionality for things like
# message reporting as well as questions (yes/no or otherwise)
class PromptBase( InterpreterBase ):

    ##
    # Creates a new PromptBase with given interpreter as parent
    def __init__( self,
                  name,
                  parent,
                  parser = None ):
        self.parent = parent
        super( PromptBase, self ).__init__(
            name,
            state = InterpreterBase.State(),
            parser = parser )

    

##========================================================================

##
# A MessagePrompt which is just used to display something
# to user
class MessagePrompt( PromptBase ):

    ##
    # creates a new message prompt with given message
    def __init__( self,
                  name,
                  message,
                  parent ):
        super( MessagePrompt, self ).__init__(
            name = name,
            parent = parent,
            parser = None )
        self.message = message
        self.add_toplevel_node( framework.message_node( message ) ) 

##========================================================================

##
# As ErrorPrompt which is just used to diplay na error to hte user
class ErrorPrompt( MessagePrompt ):

    ##
    # creates a new prompt with given error message
    def __init__( self,
                  name,
                  message,
                  parent ):
        super( ErrorPrompt, self ).__init__(
            name = name,
            message = message,
            parent = parent)

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
