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
    Generate a summary of code structure from a file.

    :param filename: Path to the source file.
    :return: Dict with categories (e.g., imports, funcs, vars, classes) as keys.
             Class entries contain nested dicts with class-level categories and members.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)
    
    return editor.parser.structure_by_class()

def modify_code_in_file(filename: str, category: str, name: str, new_code: str, class_name: str = None) -> None:
    """
    Modify a code block identified by category and name by replacing it with new code.

    :param filename: Path to the Python source file.
    :param category: Category of the code block (e.g. 'imports', 'vars', 'funcs', 'classes', 'fields', 'methods').
    :param name: Name of the function/class/method/field/import to modify.
    :param new_code: New code string to replace the old code.
    :param class_name: (optional) Name of the class if the code block is a class member.
    :return: None.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)

    handler = editor.get_handler(name, category, class_name)

    if handler is None:
        raise ValueError(f"Handler '{name}' of category '{category}' not found in file.")

    editor.set_code_by_handler(handler, new_code)
    editor.save(filename)

def get_code_from_file(filename: str, category: str, name: str, class_name: str = None) -> str | None:
    """
    Get code block by name and category from file.

    :param filename: Path to the source file.
    :param category: Handler category (e.g., funcs, vars, imports, methods, etc.).
    :param name: Name of the code block (e.g., function or method name).
    :param class_name: Optional class name for class-level members.
    :return: Code block as string, or None if not found.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)

    handler = editor.get_handler(name=name, category=category, class_name=class_name)
    if handler:
        return editor.get_code(handler)
    return None

def add_new_code(filename: str, category: str, name: str, new_code: str, class_name: str = None):
    """
    Add a new code block to the file after the last existing block of the given category.

    :param filename: Path to the source file.
    :param category: Handler category (e.g., funcs, vars, imports, methods, etc.).
    :param name: Name of the new code block.
    :param new_code: Code to be inserted.
    :param class_name: Optional class name if the category is class-level.
    """
    editor_cls = get_editor_for_file(filename)
    editor = editor_cls()
    editor.load(filename)

    if class_name:
        handlers = editor.handlers.get("classes", {}).get(class_name, {}).get(category, [])
    else:
        handlers = editor.handlers.get(category, [])

    if handlers:
        last_handler = max(handlers, key=lambda h: h.get_end_line())
        insert_line = last_handler.get_end_line() + 1
    else:
        insert_line = len(editor.code.splitlines()) + 1

    lines = editor.code.splitlines()
    new_code_lines = new_code.splitlines()
    updated_lines = lines[:insert_line - 1] + new_code_lines + lines[insert_line - 1:]
    editor.code = "\n".join(updated_lines)
    editor.parse()
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
- Always check other files looking for types used in code if needed.
- When modifying code, preserve the original indentation and formatting style exactly; do not change the indentation level or alter how the new code is indented relative to the existing block.

Goal:
Efficiently locate, read, update, or insert code in source files using only the provided tools, analyzing only what is necessary.
    """,
    tools=[get_file_tree, generate_code_summary_from_file, modify_code_in_file, get_code_from_file, add_new_code]
)