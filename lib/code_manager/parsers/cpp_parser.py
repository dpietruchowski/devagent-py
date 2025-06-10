

from tree_sitter import Language
from .base_parser import BaseNodeHandler, BaseParser
import tree_sitter_cpp as tscpp
import re

CPP_LANGUAGE = Language(tscpp.language())

class CppParser(BaseParser):
    def __init__(self):
        super().__init__(CPP_LANGUAGE)

    def get_handler_map(self):
        return {
            "imports": CppImportHandler,
            "vars": CppGlobalObjectHandler,
            "funcs": CppFunctionHandler,
            "classes": CppClassHandler,
            "fields": CppClassObjectHandler,
            "methods": CppMethodHandler,
        }

    def get_functions(self):
        query = """
        (declaration
            declarator: (function_declarator
                declarator: (identifier) @name_node
                parameters: (parameter_list)
            ) @def_node
        )
        """
        return self._get_handlers(query, ['def_node', 'name_node'], CppFunctionHandler)

    def get_methods(self):
        class_query = """
        (class_specifier
            name: (type_identifier) @class_name
            body: (field_declaration_list) @class_body) @class_node
        """

        declaration_query = """
        (field_declaration
            declarator: (function_declarator
                declarator: (field_identifier) @name_node)) @def_node
        """

        definition_query = """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name_node)
            body: (compound_statement) @def_node) @method_node
        """

        methods = []
        class_matches = self._run_query(class_query)

        for _, captures in class_matches:
            class_name = captures.get('class_name', [])[0]
            class_body = captures.get('class_body', [])[0]

            if class_body:
                methods.extend(self._get_handlers(
                    declaration_query,
                    ['def_node', 'name_node'],
                    CppMethodHandler,
                    node=class_body,
                    extra_args={'class_node': class_name}
                ))

        methods.extend(self._get_handlers(
            definition_query,
            ['def_node', 'name_node'],
            CppMethodHandler,
        ))

        return methods

    def get_class_objects(self):
        class_query = """
        (class_specifier
            name: (type_identifier) @class_name
            body: (field_declaration_list) @class_body
        ) @class_node
        """
        field_query = """
        (field_declaration
            type: (_) @type_node
            declarator: (field_identifier) @name_node
        ) @def_node
        """
        class_objects = []
        class_matches = self._run_query(class_query)
        for _, captures in class_matches:
            class_name = captures.get('class_name', [])[0]
            class_body = captures.get('class_body', [])[0]
            if class_body:
                class_objects.extend(self._get_handlers(
                    field_query,
                    ['def_node', 'name_node'],
                    CppClassObjectHandler,
                    node=class_body,
                    extra_args={'class_node': class_name}
                ))
        return class_objects

    def get_classes(self):
        query = """
        (class_specifier
            name: (type_identifier) @name_node
        ) @def_node
        """
        return self._get_handlers(query, ['def_node', 'name_node'], CppClassHandler)

    def get_imports(self):
        query = """
        (preproc_include) @def_node
        """
        return self._get_handlers(query, ['def_node'], CppImportHandler)

    def get_global_objects(self):
        query = """
        (declaration
            declarator: (init_declarator
                declarator: (identifier) @name_node)) @def_node
        """
        return self._get_handlers(query, ['def_node', 'name_node'], CppGlobalObjectHandler)


class CppFunctionHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

class CppClassHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

class CppImportHandler(BaseNodeHandler):
    def __init__(self, def_node, code):
        super().__init__(def_node, code)

    def _extract_name(self):
        return self.get_code()

class CppGlobalObjectHandler(BaseNodeHandler):
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

class CppClassObjectHandler(CppGlobalObjectHandler):
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