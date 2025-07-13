import logging
from typing import Type, Dict, Any

class BaseFileEditor:
    def __init__(self, parser):
        self.code = ""
        self.handlers = {}
        self.parser = parser
        logging.debug(f"Initialized BaseFileEditor with parser: {parser}")

    def get_handler_map(self) -> Dict[str, Dict[str, Any]]:
        handler_map = self.parser.get_handler_map()
        logging.debug(f"Retrieved handler map: {handler_map}")
        return handler_map

    def load(self, filepath: str):
        logging.debug(f"Loading file: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            self.code = f.read()
        logging.debug(f"Loaded code ({len(self.code)} characters)")
        self.parse()

    def save(self, filepath: str):
        logging.debug(f"Saving file: {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.code)
        logging.debug(f"File saved successfully")

    def parse(self):
        logging.debug("Parsing code")
        self.parser.parse(self.code)
        self.handlers = self.parser.parse_handlers()
        logging.debug(f"Parsed handlers: {self.handlers}")

    def set_code_by_handler(self, handler, new_code: str):
        logging.debug(f"Setting code by handler: {handler}, new_code length: {len(new_code)}")
        self.set_code(handler.get_start_line(), handler.get_end_line(), new_code)

    def set_code(self, start_line: int, end_line: int, new_code: str):
        logging.debug(f"Setting code from line {start_line} to {end_line}, new_code length: {len(new_code)}")
        lines = self.code.splitlines()
        logging.debug(f"Current number of lines in code: {len(lines)}")
        lines[start_line - 1:end_line] = new_code.splitlines()
        self.code = "\n".join(lines)
        logging.debug("Code updated, now parsing updated code")
        self.parse()

    def get_code(self, handler) -> str:
        lines = self.code.splitlines()
        start, end = handler.get_start_line(), handler.get_end_line()
        code_snippet = "\n".join(lines[start - 1:end])
        logging.debug(f"Retrieved code for handler from line {start} to {end}, length: {len(code_snippet)}")
        return code_snippet

    def get_handlers_list(self, category: str, class_name: str = None):
        handlers = self.handlers.get(category, [])
        if class_name:
            filtered = [h for h in handlers if h.class_name == class_name]
            logging.debug(f"Retrieved handlers list for category '{category}' and class '{class_name}': {len(filtered)} found")
            return filtered
        logging.debug(f"Retrieved handlers list for category '{category}': {len(handlers)} found")
        return handlers

    def get_handler(self, name: str, category: str, class_name: str = None):
        handlers = self.handlers.get(category, [])
        logging.debug(f"Searching for handler '{name}' in category '{category}' with class '{class_name}'")
        if class_name:
            for handler in handlers:
                if handler.name == name and handler.class_name == class_name:
                    logging.debug(f"Found handler: {handler}")
                    return handler
        else:
            for handler in handlers:
                if handler.name == name:
                    logging.debug(f"Found handler: {handler}")
                    return handler
        logging.debug(f"Handler '{name}' not found")
        return None

    def get_class_members_list(self, class_name: str, member_type: str):
        handlers = self.handlers.get(member_type, [])
        members = [h.name for h in handlers if h.class_name == class_name]
        logging.debug(f"Retrieved members of type '{member_type}' for class '{class_name}': {members}")
        return members

    def get_class_handler(self, class_name: str, name: str, member_type: str):
        handlers = self.handlers.get(member_type, [])
        for h in handlers:
            if h.name == name and h.class_name == class_name:
                logging.debug(f"Found class handler: {h}")
                return h
        logging.debug(f"Class handler '{name}' of type '{member_type}' in class '{class_name}' not found")
        return None
