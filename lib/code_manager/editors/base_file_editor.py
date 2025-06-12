from typing import Type, Dict, Any

class BaseFileEditor:
    def __init__(self, parser):
        self.code = ""
        self.handlers = {}
        self.parser = parser

    def get_handler_map(self) -> Dict[str, Dict[str, Any]]:
        return self.parser.get_handler_map()

    def load(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            self.code = f.read()
        self.parse()

    def save(self, filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.code)

    def parse(self):
        self.parser.parse(self.code)
        self.handlers = self.parser.parse_handlers()

    def set_code_by_handler(self, handler, new_code: str):
        self.set_code(handler.get_start_line(), handler.get_end_line(), new_code)

    def set_code(self, start_line: int, end_line: int, new_code: str):
        lines = self.code.splitlines()
        lines[start_line - 1:end_line] = new_code.splitlines()
        self.code = "\n".join(lines)
        self.parse()

    def get_code(self, handler) -> str:
        lines = self.code.splitlines()
        start, end = handler.get_start_line(), handler.get_end_line()
        return "\n".join(lines[start - 1:end])

    def get_handlers_list(self, category: str, class_name: str = None):
        handlers = self.handlers.get(category, [])
        if class_name:
            return [h for h in handlers if h.class_name == class_name]
        return handlers

    def get_handler(self, name: str, category: str, class_name: str = None):
        handlers = self.handlers.get(category, [])
        if class_name:
            for handler in handlers:
                if handler.name == name and handler.class_name == class_name:
                    return handler
        else:
            for handler in handlers:
                if handler.name == name:
                    return handler
        return None

    def get_class_members_list(self, class_name: str, member_type: str):
        handlers = self.handlers.get(member_type, [])
        return [h.name for h in handlers if h.class_name == class_name]

    def get_class_handler(self, class_name: str, name: str, member_type: str):
        handlers = self.handlers.get(member_type, [])
        for h in handlers:
            if h.name == name and h.class_name == class_name:
                return h
        return None