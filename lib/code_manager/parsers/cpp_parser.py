

from tree_sitter import Language
from .base_parser import BaseNodeHandler, BaseParser, register_handler
import tree_sitter_cpp as tscpp
import re

CPP_LANGUAGE = Language(tscpp.language())

class CppParser(BaseParser):
    def __init__(self):
        super().__init__(CPP_LANGUAGE)

    @register_handler("functions", class_level=False)
    def get_functions(self):
        query = """
        (declaration
            declarator: (function_declarator
                declarator: (identifier) @name_node
                parameters: (parameter_list)
            ) @def_node
        )
        """
        handlers = self._extract_handlers(query, ['def_node', 'name_node'], CppFunctionHandler)
    
        return [h for h in handlers if h.name != "Q_PROPERTY"]

    @register_handler("properties", class_level=True)
    def get_properties(self):
        class_query = """
        (class_specifier
            name: (type_identifier) @class_name
            body: (field_declaration_list) @class_body
        ) @class_node
        """
        property_query = """
        (field_declaration
            declarator: (function_declarator
                declarator: (field_identifier) @name_node
            ) @def_node
        )
        """
        properties = []
        class_matches = self._run_query(class_query)

        for _, captures in class_matches:
            class_name = captures.get('class_name', [])[0]
            class_body = captures.get('class_body', [])[0]
            if class_body:
                properties.extend(self._extract_handlers(
                    property_query,
                    ['def_node', 'name_node'],
                    CppPropertyHandler,
                    node=class_body,
                    extra_args={'class_node': class_name}
                ))
        return properties

    @register_handler("methods", class_level=True)
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
                methods.extend(self._extract_handlers(
                    declaration_query,
                    ['def_node', 'name_node'],
                    CppMethodHandler,
                    node=class_body,
                    extra_args={'class_node': class_name}
                ))

        methods.extend(self._extract_handlers(
            definition_query,
            ['def_node', 'name_node'],
            CppMethodHandler,
        ))

        return methods

    @register_handler("fields", class_level=True)
    def get_fields(self):
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
                class_objects.extend(self._extract_handlers(
                    field_query,
                    ['def_node', 'name_node'],
                    CppClassObjectHandler,
                    node=class_body,
                    extra_args={'class_node': class_name}
                ))
        return class_objects

    @register_handler("classes", class_level=False)
    def get_classes(self):
        query = """
        (class_specifier
            name: (type_identifier) @name_node
        ) @def_node
        """
        return self._extract_handlers(query, ['def_node', 'name_node'], CppClassHandler)

    @register_handler("imports", class_level=False)
    def get_imports(self):
        query = """
        (preproc_include) @def_node
        """
        return self._extract_handlers(query, ['def_node'], CppImportHandler)

    @register_handler("vars", class_level=False)
    def get_vars(self):
        query = """
        (declaration
            declarator: (init_declarator
                declarator: (identifier) @name_node)) @def_node
        """
        return self._extract_handlers(query, ['def_node', 'name_node'], CppGlobalObjectHandler)


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
    
class CppPropertyHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None, class_node=None):
        super().__init__(def_node, code)
        self.name_node = name_node
        self.class_node = class_node
        self.class_name = self._extract_class_name()
        self.name = self._extract_name()

    def _extract_name(self):
        code = self.get_code()
        if not code.strip().startswith("Q_PROPERTY"):
            return None
        match = re.match(r"Q_PROPERTY\s*\(\s*(\w+)\s+(\w+)", code)
        if match:
            return match.group(2)
        return None

    def _extract_class_name(self):
        if not self.class_node:
            return None
        return self.code[self.class_node.start_byte:self.class_node.end_byte].decode("utf-8")

    def get_class_name(self):
        return self.class_name