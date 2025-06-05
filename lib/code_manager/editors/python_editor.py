from typing import Type

from .base_file_editor import BaseFileEditor

from lib.code_manager.parsers.python_parser import PythonParser

class PythonFileEditor(BaseFileEditor):
    def __init__(self):
        super().__init__(PythonParser())