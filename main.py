from agents import Agent
from openai import OpenAI
import os, subprocess

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
        return file.read()

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


developer = Agent(
    name="Agent 007", 
    model="gpt-4o-mini", 
    system_prompt="""
    You are cpp developer. Use directory "src".
    Steps:
    1. Check directory structure
    2. Find proper file to modify
    3. Use get_file_content to get content
    4. Modify the content.
    5. Use set_file_content to update file
    Remember to not use comments in code
    """,
    tools=[get_file_content, set_file_content, get_file_tree]
)

def main():
    print("Will use model:", developer.model)

    while True:
        try:
            user_input = input("> ")

            response = developer.request(client, user_input)
            print()
            print("< " + response)
            developer.clear()

        except (KeyboardInterrupt, EOFError):
            # Przerwij pętlę, gdy Ctrl+C lub Ctrl+D
            print("\nExiting chat.")
            break



if __name__ == "__main__":
    main()
