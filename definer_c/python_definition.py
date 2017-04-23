import logging
logger = logging.getLogger( __name__ )

##
#
# This file contains a DefinitionBase subclass that accepts python source
# and checks for well-definedness using the idea of "free variables"
# in source code.

import concept as concept_module

import ast
import symtable

##=========================================================================

##
# A Definition that assumes the source is python source code
# and treats well-definedness as having no free variables which are
# not bound in the given Concept's context
class PythonDefinition( concept_module.DefinitionBase ):

    ##
    # Creates a new python definition with given concept
    # adn source
    def __init__( self,
                  concept,
                  source ):
        concept_module.DefinitionBase.__init__( self,
                                                concept,
                                                source )
        self.free_vars = self._compute_free_variables()

    ##
    # return NotWellDefined objects for the reasons why this
    # Definition is not well-defined.
    # If it is well-defined this will return an empty list :)
    def get_not_well_defined(self):

        # if we wer unalbe to compute free variables then
        # this is a malformed python source and we return
        # a NotWellDefined as such
        if self.free_vars is None:
            return [
                concept_module.NotWellDefinedSyntaxError(
                    definition = self ) ]

        # Ok, look for each of hte free variables and
        # see if we have exactly one binding for it.
        # Having too many is not good eaither
        nwds = []
        for v in self.free_vars:

            # grab dingins for free variable
            binds = self.concept.lookup_bindings( v )

            # Ok, if 0 or more than one we are not well defined :)
            if len(binds) < 1:
                nwds.append( concept_module.NotWellDefinedMissingBinding(
                    definition = self,
                    binding_name = v ) )
            elif len(binds) > 1:
                nwds.append( concept_module.NotWellDefinedAmbiguousBinding(
                    definition = self,
                    binding_name = v,
                    bindings = binds ) )

        # ok, return all found NotWellDefined objects
        return nwds


    ##
    # Computes the "free variables" in this definitions.
    # This menas we parse the source as python and grab anything
    # that is either a free-variable or a global (not assigned)
    # in the toplevel :)
    #
    # Returns a list of the names of the free variables
    def _compute_free_variables(self):

        # ok, we will try parsing hte source and computing the
        # symboltable for the source
        try:
            st = symtable.symtable(
                code = self.source,
                filename = self.concept.representations[0].human_friendly(),
                compile_type = 'exec' )

            # Ok, now that we have the symbol table, find all
            # variables in toplevel denoted as "free" or "global"
            fvars = []
            for s in st.get_symbols():
                if s.is_free() or s.is_global():
                    fvars.append( s.get_name() )

            # return the found free varibles
            return fvars
            
        except:
            return None

##=========================================================================
##=========================================================================

def describe_symbol(sym):
    assert type(sym) == symtable.Symbol
    print "Symbol:", sym.get_name()

    for prop in [
            'referenced', 'imported', 'parameter',
            'global', 'declared_global', 'local',
            'free', 'assigned', 'namespace']:
        if getattr(sym, 'is_' + prop)():
            print '    is', prop

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
