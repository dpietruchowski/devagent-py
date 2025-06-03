from .agents import Agent
from .memory import memory

from typing import List, Dict

def add_or_update_file(path, tags):
    """
    Adds or updates a file entry in the memory database.

    :param path: The file path relative to project root.
    :param tags: A list of lowercase tags describing the file content.

    :return: None
    """
    if isinstance(tags, str):
        tags = [tag.strip().lower() for tag in tags.split(",") if tag.strip()]
    elif isinstance(tags, list):
        tags = [tag.strip().lower() for tag in tags if isinstance(tag, str) and tag.strip()]
    else:
        tags = []
    print("add_or_update_file", path, tags)
    memory.add_or_update_file(path, tags)

memory_builder_agent = Agent(
    name="MemoryBuilder",
    model="gpt-4o-mini",
    system_prompt="""
    You are an assistant that analyzes C++ source code file content.

    Your task:
    Given the full content of a source code file and its path, extract
    a list of relevant tags describing the file content (e.g., database, logging, auth).

    Return the data as a Python dictionary with keys:
    - "file_path" (string)
    - "file_tags" (list of lowercase tags)

    Immediately call the tool 'add_or_update_file' with extracted path and tags
    to update the memory database.

    Do not include any functions or other details.
    Do not write any code or comments. Focus on concise, accurate metadata extraction.
    """,
    tools=[add_or_update_file]
)