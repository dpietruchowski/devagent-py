from tree_sitter import Language
import tree_sitter_python as tspython
from .base_parser import BaseNodeHandler, BaseParser

PY_LANGUAGE = Language(tspython.language())

class PythonParser(BaseParser):
    def __init__(self, source_code: str):
        super().__init__(PY_LANGUAGE, source_code)

    def get_functions(self):
        query = """
        (function_definition
            name: (identifier) @name_node) @def_node
        """
        return self._get_handlers(query, ['def_node', 'name_node'], PythonFunctionHandler)

    def get_methods(self):
        class_query = "(class_definition) @class_def"
        methods = []
        class_matches = self._run_query(class_query)
        for _, captures in class_matches:
            class_nodes = captures.get("class_def", [])
            for class_node in class_nodes:
                method_query = """
                (function_definition
                    name: (identifier) @name_node) @def_node
                """
                methods.extend(self._get_handlers(
                    method_query,
                    ['def_node', 'name_node'],
                    PythonMethodHandler,
                    node=class_node,
                    extra_args={'class_node': class_node}
                ))
        return methods
    
    def get_class_objects(self):
        class_query = "(class_definition) @class_def"
        class_objects = []
        class_matches = self._run_query(class_query)
        for _, captures in class_matches:
            class_nodes = captures.get("class_def", [])
            for class_node in class_nodes:
                object_query = """
                (class_definition
                body: (block
                    (expression_statement
                    (assignment
                        left: (identifier) @name_node
                        right: (_) @value_node) ) @def_node
                )
                )
                """
                class_objects.extend(self._get_handlers(
                    object_query,
                    ['def_node', 'name_node'],
                    PythonClassObjectHandler,
                    node=class_node,
                    extra_args={'class_node': class_node}
                ))
        return class_objects


    def get_classes(self):
        query = """
        (class_definition
            name: (identifier) @name_node) @def_node
        """
        return self._get_handlers(query, ['def_node', 'name_node'], PythonClassHandler)

    def get_imports(self):
        query = """
        (import_statement) @def_node
        (import_from_statement) @def_node
        """
        return self._get_handlers(query, ['def_node'], PythonImportHandler)

    def get_global_objects(self):
        query = """
        (module
            (expression_statement
                (assignment
                    left: (identifier) @name_node
                    right: (_) @value_node)) @def_node)
        """
        return self._get_handlers(query, ['def_node', 'name_node'], PythonGlobalObjectHandler)


class PythonFunctionHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

class PythonClassHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

class PythonImportHandler(BaseNodeHandler):
    def __init__(self, def_node, code):
        super().__init__(def_node, code)

    def _extract_name(self):
        return self.get_code()

class PythonGlobalObjectHandler(BaseNodeHandler):
    def __init__(self, def_node, code, name_node=None):
        self.name_node = name_node
        super().__init__(def_node, code)

    def _extract_name(self):
        if self.name_node:
            return self.code[self.name_node.start_byte:self.name_node.end_byte].decode("utf-8")
        return None

class PythonMethodHandler(PythonFunctionHandler):
    def __init__(self, def_node, code, name_node=None, class_node=None):
        super().__init__(def_node, code, name_node)
        self.class_node = class_node
        self.class_name = self._extract_class_name()

    def _extract_class_name(self):
        if not self.class_node:
            return None
        name_node = self.class_node.child_by_field_name("name")
        if name_node:
            return self.code[name_node.start_byte:name_node.end_byte].decode("utf-8")
        return None

    def get_class_name(self):
        return self.class_name

class PythonClassObjectHandler(PythonGlobalObjectHandler):
    def __init__(self, def_node, code, name_node=None, class_node=None):
        super().__init__(def_node, code, name_node)
        self.class_node = class_node
        self.class_name = self._extract_class_name()

    def _extract_class_name(self):
        if not self.class_node:
            return None
        name_node = self.class_node.child_by_field_name("name")
        if name_node:
            return self.code[name_node.start_byte:name_node.end_byte].decode("utf-8")
        return None

    def get_class_name(self):
        return self.class_name