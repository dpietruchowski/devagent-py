from typing import Type
from lib.code_manager.parsers.python_parser import PythonParser

class PythonFileEditor:
    def __init__(self):
        self.code = ""
        self.handlers = []
        self.parser = None

    def load(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.code = f.read()
        self.parse()

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.code)

    def parse(self):
        self.parser = PythonParser(self.code)
        self.handlers = []
        self.handlers.extend(self.parser.get_functions())
        self.handlers.extend(self.parser.get_methods())
        self.handlers.extend(self.parser.get_classes())
        self.handlers.extend(self.parser.get_imports())
        self.handlers.extend(self.parser.get_global_objects())
        self.handlers.extend(self.parser.get_class_objects())

    def set_code_by_handler(self, handler, new_code):
        self.set_code(handler.get_start_line(), handler.get_end_line(), new_code)

    def set_code(self, start_line, end_line, new_code):
        lines = self.code.splitlines()
        lines[start_line-1:end_line] = new_code.splitlines()
        self.code = "\n".join(lines)
        self.parse()

    def get_code(self, handler) -> str:
        lines = self.code.splitlines()
        start, end = handler.get_start_line(), handler.get_end_line()
        return "\n".join(lines[start - 1:end])

    def get_handlers_list(self, handler_cls: Type):
        return [h.name for h in self.handlers if isinstance(h, handler_cls)]

    def get_handler(self, name: str, handler_cls: Type):
        for handler in self.handlers:
            if isinstance(handler, handler_cls) and handler.name == name:
                return handler
        return None

    def get_class_members_list(self, class_name: str, handler_cls: Type):
        return [h.name for h in self.handlers
                if isinstance(h, handler_cls) and hasattr(h, 'get_class_name') and h.get_class_name() == class_name]

    def get_class_handler(self, class_name: str, name: str, handler_cls: Type):
        for handler in self.handlers:
            if isinstance(handler, handler_cls) and handler.name == name and hasattr(handler, 'get_class_name') and handler.get_class_name() == class_name:
                return handler
        return None