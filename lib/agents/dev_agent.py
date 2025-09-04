from .agents import Agent
from openai import OpenAI
import os
import json
from typing import List, Dict, Any

client = OpenAI()

ROOT_DIRECTORY = os.getenv("PROJECT_PATH", os.getcwd())

def get_files_content(file_paths: List[str]):
    """
    Reads the content of multiple files in the project.
    This function can handle multiple files at once and returns their content as JSON.

    :param file_paths: A list of relative paths to the files within the project.
                       Each path should be a string representing the file location.
    :return: A JSON string containing objects with keys:
             file_path: The relative path of the file
             content: The content of the file
    """
    results = []
    for file_path in file_paths:
        abs_path = os.path.join(ROOT_DIRECTORY, file_path)
        print('get_files_content', abs_path)
        try:
            with open(abs_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            content = ""
        results.append({"file_path": file_path, "content": content})
    return json.dumps(results)

def set_files_content(files: List[Dict[str, Any]]):
    """
    Writes content to multiple files in the project.
    Creates the directory structure if it does not exist.

    :param files: A list of dictionaries representing the files to write.
            file_path: Relative path to the file
            content: Content to write
    """
    for f in files:
        abs_path = os.path.join(ROOT_DIRECTORY, f["file_path"])
        print('set_files_content', abs_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w') as file:
            file.write(f["content"])

def update_file_content(file_path, target_string, replacement_string):
    """
    Replaces all occurrences of a target string with a replacement string in a given file.

    :param file_path: The relative path to the file within the project.
    :param target_string: The string to be replaced.
    :param replacement_string: The string to replace the target with.
    """
    file_path = os.path.join(ROOT_DIRECTORY, file_path)
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        updated_content = content.replace(target_string, replacement_string)
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"File '{file_path}' updated successfully.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def get_file_tree():
    """
    Recursively gets the file tree of a given directory.
    Returns a nested dictionary representing the directory structure,
    where files have value None and directories have nested dicts.
    """
    file_tree = {}
    exclude_dirs = [".git", "__pycache__"]
    
    for root, dirs, files in os.walk(ROOT_DIRECTORY):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        current_dir = file_tree
        relative_path = os.path.relpath(root, ROOT_DIRECTORY)
        
        if relative_path != ".":
            for folder in relative_path.split(os.sep):
                current_dir = current_dir.setdefault(folder, {})
        
        current_dir.update({d: {} for d in dirs})
        current_dir.update({f: None for f in files})

    return file_tree

developer = Agent(
    name="Agent 007",
    model="gpt-5-mini",
    system_prompt="""
    You are a programming developer working on a software project.

    Steps:
    1. Identify all files that need modification.
    2. Ask for all required files at once using get_files_content.
    3. Modify the content as needed.
    4. Save all modified files at once using set_files_content.

    Rules:
    - Do not include comments in the code.
    - Never show code in responses to the user.
    - Respond with a brief summary of the action, in a single sentence maximum.

    Goal:
    Efficiently locate, edit, and update files in the project without asking for files one by one.
    """,
    tools=[get_files_content, set_files_content]
)
