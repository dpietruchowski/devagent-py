from .base_file_editor import BaseFileEditor

from lib.code_manager.parsers.cpp_source_parser import CppSourceParser

class CppSourceFileEditor(BaseFileEditor):
    def __init__(self):
        super().__init__(CppSourceParser())