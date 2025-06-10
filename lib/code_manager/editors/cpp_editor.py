from .base_file_editor import BaseFileEditor

from lib.code_manager.parsers.cpp_parser import CppParser

class CppFileEditor(BaseFileEditor):
    def __init__(self):
        super().__init__(CppParser())