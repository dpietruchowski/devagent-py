from lib.agents.agents import Agent
from openai import OpenAI

from .editors.python_editor import PythonFileEditor
from .editors.cpp_editor import CppFileEditor
from .parsers.python_parser import *

import os

client = OpenAI()

editor_registry = {
    ".py": PythonFileEditor,
    ".cpp": CppFileEditor,
    ".h": CppFileEditor,
}

def get_editor_for_file(filename):
    ext = os.path.splitext(filename)[1]
    if ext not in editor_registry:
        raise ValueError(f"Unsupported file extension: {ext}")
    return editor_registry[ext]

def get_file_tree(directory):
    """
    Recursively gets the file tree of a given directory. This function should be called
    when the model needs to explore the directory structure and gather information about
    all the files and subdirectories. The function returns a nested dictionary of the
    directory structure, with file contents for each file.

    :param directory: The root directory path to get the file tree from.
    """
    file_tree = {os.path.basename(directory): {}}
    root_dict = file_tree[os.path.basename(directory)]
    exclude_dirs = [".git", "__pycache__"]
    
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        current_dir = root_dict
        relative_path = os.path.relpath(root, directory)
        
        if relative_path != ".":
            for folder in relative_path.split(os.sep):
                current_dir = current_dir.setdefault(folder, {})
        
        current_dir.update({d: {} for d in dirs})
        current_dir.update({f: None for f in files})

    print(file_tree)
    return file_tree

def generate_code_summary_from_file(filename: str):
    """
    Generate a summary of Python code structure from a file.

    :param filename: Path to the Python source file.
    :return: dict with keys 'imports', 'vars', 'funcs', 'classes'.
             'classes' maps class names to dicts with 'fields' and 'methods' lists.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)

    handler_map = editor.get_handler_map()
    summary = {}
    
    class_key = "classes"
    fields_key = "fields"
    methods_key = "methods"

    for key, handler_cls in handler_map.items():
        if key in {class_key, fields_key, methods_key}:
            continue
        summary[key] = editor.get_handlers_list(handler_cls)

    if class_key in handler_map:
        class_handler = handler_map[class_key]
        class_names = editor.get_handlers_list(class_handler)
        summary[class_key] = {}

        for cls_name in class_names:
            class_entry = {}

            if fields_key in handler_map:
                class_entry[fields_key] = editor.get_class_members_list(cls_name, handler_map[fields_key])
            if methods_key in handler_map:
                class_entry[methods_key] = editor.get_class_members_list(cls_name, handler_map[methods_key])

            summary[class_key][cls_name] = class_entry

    return summary

def modify_code_in_file(filename: str, node_type: str, name: str, new_code: str, class_name: str = None) -> None:
    """
    Modify code block identified by node type and name by replacing it with new code.

    :param filename: Path to the Python source file.
    :param node_type: One of 'imports', 'vars', 'funcs', 'classes', 'fields', 'methods'.
    :param name: Name of the function/class/method/field/import to modify.
    :param new_code: New code string to replace the old code.
    :param class_name: (optional) Name of the class if node is a class member.
    :return: None.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)
    handler_map = editor.get_handler_map()
    handler_cls = handler_map.get(node_type)
    if handler_cls is None:
        raise ValueError(f"Unknown node type '{node_type}'.")

    if class_name and node_type in {"fields", "methods"}:
        handler = editor.get_class_handler(class_name, name, handler_cls)
    else:
        handler = editor.get_handler(name, handler_cls)

    if handler is None:
        raise ValueError(f"Handler '{name}' of type '{node_type}' not found in file.")

    editor.set_code_by_handler(handler, new_code)
    editor.save(filename)

def get_code_from_file(filename: str, node_type: str, name: str, class_name: str = None) -> str | None:
    """
    Get code block from Python file identified by node type and name.

    :param filename: Path to the Python source file.
    :param node_type: One of 'imports', 'vars', 'funcs', 'classes', 'fields', 'methods'.
    :param name: Name of the function/class/method/field/import to get code from.
    :param class_name: (optional) Name of the class if node is a class member.
    :return: Code string or None if not found.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)
    handler_map = editor.get_handler_map()
    handler_cls = handler_map.get(node_type)
    if handler_cls is None:
        raise ValueError(f"Unknown node type '{node_type}'.")

    if class_name and node_type in {"fields", "methods"}:
        handler = editor.get_class_handler(class_name, name, handler_cls)
    else:
        handler = editor.get_handler(name, handler_cls)

    if handler is None:
        return None

    return editor.get_code(handler)

def add_new_code(filename: str, node_type: str, name: str, new_code: str, class_name: str = None):
    """
    :param filename: Target Python file
    :param node_type: One of 'classes', 'methods', 'fields', 'funcs', 'vars', 'imports'
    :param name: Name of the new code object
    :param new_code: Code to insert
    :param class_name: Required if adding to a class (for 'methods' or 'fields')
    :return: None
    """
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("")

    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)

    handler_map = editor.get_handler_map()

    class_key = "classes"
    fields_key = "fields"
    methods_key = "methods"

    if node_type == class_key:
        editor.code += "\n\n" + new_code
        editor.save(filename)
        return

    if node_type in {fields_key, methods_key} and class_name:
        class_handler_cls = handler_map[class_key]
        class_handler = editor.get_handler(class_name, class_handler_cls)
        if class_handler:
            original = class_handler.get_code()
            updated = original.rstrip() + "\n\n" + new_code
            editor.set_code_by_handler(class_handler, updated)
            editor.save(filename)
            return

    editor.code += "\n\n" + new_code
    editor.save(filename)

developer = Agent(
    name="Agent 007", 
    model="gpt-4o", 
    system_prompt = """
    You are a programming developer working in the 'src' directory.

    Use only the provided tools to work with files:
    - `get_file_tree()` to inspect the directory structure,
    - `generate_code_summary_from_file(filename)` to get code structure summaries,
    - `get_code_from_file(filename, node_type, name, class_name=None)` to read code fragments,
    - `modify_code_in_file(filename, node_type, name, new_code)` to update existing code,
    - `add_new_code(filename, node_type, name, new_code, class_name=None)` to insert new code (will create file if it doesn't exist).

    Steps:
    1. Use `get_file_tree()` to view the full directory structure.
    2. Select only the files that are relevant to the task.
    3. Use `generate_code_summary_from_file` to analyze those selected files.
    4. Use `get_code_from_file` to inspect specific code blocks if needed.
    5. Use `modify_code_in_file` to edit existing code blocks.
    6. Use `add_new_code` to insert new functions, classes, methods, fields, variables, or imports. It will create the file if it doesn't exist.

    Rules:
    - Never show code in responses to the user.
    - Do not include comments in code changes.
    - Prefer modifying only the specific method or function instead of replacing entire classes.
    - Keep responses short: one sentence summarizing the action.
    - Always check other files looking for types used in code if needed

    Goal:
    Efficiently locate, read, update, or insert code in source files using only the provided tools, analyzing only what is necessary.
    """,
    tools=[get_file_tree, generate_code_summary_from_file, modify_code_in_file, get_code_from_file, add_new_code]
)