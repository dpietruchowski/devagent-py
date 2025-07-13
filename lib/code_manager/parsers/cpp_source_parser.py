from tree_sitter import Language
from .base_parser import BaseNodeHandler, BaseParser, register_handler
import tree_sitter_cpp as tscpp
import re

CPP_LANGUAGE = Language(tscpp.language())


def is_global_node(node):
    parent = node.parent
    while parent:
        if parent.type in ["function_definition", "compound_statement"]:
            return False
        parent = parent.parent
    return True

class CppSourceParser(BaseParser):
    def __init__(self):
        super().__init__(CPP_LANGUAGE)

    @register_handler("includes", class_level=False)
    def get_includes(self):
        query = """
        (preproc_include) @def_node
        """
        return self._extract_handlers(query, ['def_node'], CppIncludeHandler)
    
    @register_handler("functions", class_level=False)
    def get_functions(self):
        query = """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name_node
                parameters: (parameter_list)
            )
        )  @def_node
        """
        return self._extract_handlers(query, ['def_node', 'name_node'], CppFunctionHandler)
    
    @register_handler("methods", class_level=True)
    def get_methods(self):
        query = """
        (function_definition
          declarator: (function_declarator
            declarator: (qualified_identifier
              scope: (namespace_identifier) @class_node
              name: (identifier) @name_node
            )
          )
        ) @def_node
        """
        return self._extract_handlers(query, ['def_node', 'name_node', 'class_node'], CppMethodHandler)
    
    @register_handler("static_members", class_level=True)
    def get_static_members(self):
        class_var_query = """
        (declaration
        declarator: (init_declarator
            declarator: (qualified_identifier
            scope: (namespace_identifier) @class_node
            name: (identifier) @name_node
            )
        ) @def_node
        )
        """

        vars = []
        vars.extend(self._extract_handlers(class_var_query, ['def_node', 'name_node', 'class_node'], CppGlobalVarHandler))

        return vars
    
    @register_handler("global_vars", class_level=False)
    def get_global_vars(self):
        global_var_query = """
        (declaration
            type: (_) @type_node
            declarator: (init_declarator
                declarator: (identifier) @name_node
            )
        ) @def_node
        """

        results = []
        matches = self._extract_nodes(global_var_query, capture_keys=['def_node', 'name_node'])

        for match in matches:
            def_node = match['def_node'][0]
            name_node = match['name_node'][0]
            if is_global_node(def_node):
                results.append(CppGlobalVarHandler(def_node, self.code, name_node=name_node))

        return results


class CppIncludeHandler(BaseNodeHandler):
    def __init__(self, def_node, code):
        super().__init__(def_node, code)

    def _extract_name(self):
        return self.get_code()
    
class CppFunctionHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None
    
class CppMethodHandler(CppFunctionHandler):
    def __init__(self, def_node, code, name_node=None, class_node=None):
        super().__init__(def_node, code, name_node)
        self.class_node = class_node
        self.class_name = self._extract_class_name()

    def _extract_class_name(self):
        if not self.class_node:
            return None
        class_name_node = self.class_node
        if class_name_node:
            return self.code[class_name_node.start_byte:class_name_node.end_byte].decode("utf-8")
        return None

    def get_class_name(self):
        return self.class_name
    
class CppGlobalVarHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None, class_node=None):
        self.name_node = name_node
        self.class_node = class_node
        super().__init__(def_node, code)
        self.name = self._extract_name()
        self.class_name = self._extract_class_name()

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

    def _extract_class_name(self):
        if self.class_node:
            return self.code[self.class_node.start_byte:self.class_node.end_byte].decode("utf-8")
        return None

    def get_name(self):
        return self.name

    def get_class_name(self):
        return self.class_name