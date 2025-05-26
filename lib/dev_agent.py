from lib.agents import Agent
from openai import OpenAI
from lib.memory import memory
from lib.mem_agent import memory_builder_agent
import os, subprocess
import ast

client = OpenAI()

def get_file_content(file_path):
    """
    Reads the content of a file. This function should be called when the model needs
    to retrieve the content of a specific file in the directory. It is used for reading
    text-based files and returning the data as a string.

    :param file_path: The path to the file to read.
    """
    print('get_file_content', file_path)
    with open(file_path, 'r') as file:
        content = file.read()
        if not memory.has_file_info(file_path):
            memory_builder_agent.request(client, f'File path: {file_path}, content: {content}')
        return content

def set_file_content(file_path, content):
    """
    Writes content to a file. This function should be called when the model needs
    to write data to a file. The provided content will be written to the file at the
    specified path, replacing any existing content.

    :param file_path: The path to the file to write to.
    :param content: The content to write to the file.
    """
    print('set_file_content', file_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as file:
        file.write(content)

def update_file_content(file_path, target_string, replacement_string):
    """
    Replaces all occurrences of a target string with a replacement string in a given file.

    :param file_path: The path to the file to be updated.
    :param target_string: The string to be replaced in the file content.
    :param replacement_string: The string to replace the target string with.
    """
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
    
    for root, dirs, files in os.walk(directory):
        current_dir = root_dict
        relative_path = os.path.relpath(root, directory)
        
        if relative_path != ".":
            for folder in relative_path.split(os.sep):
                current_dir = current_dir.setdefault(folder, {})
        
        current_dir.update({d: {} for d in dirs})
        current_dir.update({f: None for f in files})

    print(file_tree)
    return file_tree

tag_generator_agent = Agent(
    name="TagGenerator",
    model="gpt-4o-mini",
    system_prompt="""
    You are a tagging assistant for a memory system used in software development.

    Your task:
    Given a natural language prompt from a developer, return a list of 1 to 5 relevant lowercase tags.

    Rules:
    - Only output a valid Python list of strings.
    - Tags must be lowercase and concise (e.g. "database", "login", "http", "file", "parser").
    - Do not explain or include any extra text.
    - Do not include duplicates or empty tags.
    """
)

def query_memory(prompt: str):
    """
    Converts a natural language prompt into a list of tags using a tag generation agent,
    then queries the memory database for files and functions matching those tags.

    :param prompt: A natural language query describing what the developer is looking for.

    :return: A list of dictionaries containing file paths, tags, and matching functions.
            Returns an empty list if tag extraction fails or the response is invalid.
    """

    response = tag_generator_agent.request(client, prompt)

    try:
        tags = ast.literal_eval(response)
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            return []
    except:
        return []

    return memory.query_by_tags(tags)


developer = Agent(
    name="Agent 007", 
    model="gpt-4o-mini", 
    system_prompt="""
    You are a C++ developer. Use directory "src".

    Steps:
    1. When you need to find where something is implemented, first use query_memory with a natural language prompt.
    2. If query_memory does not return useful results, then use get_file_tree to inspect the directory structure.
    3. Find the appropriate file to modify.
    4. Use get_file_content to read the file content.
    5. Modify the content as needed.
    6. Use set_file_content to update the file.

    Important rules:
    - Use query_memory before get_file_tree to reduce overhead.
    - Do not use comments in code.
    """,
    tools=[get_file_content, set_file_content, query_memory, get_file_tree]
)