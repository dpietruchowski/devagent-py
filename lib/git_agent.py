from lib.agents import Agent
import os, subprocess

def get_git_diff():
    """
    Retrieves the Git diff for the current directory.
    Shows the changes that have been made but not yet committed.
    """
    result = subprocess.run(['git', 'diff'], capture_output=True, text=True)
    print(result.stdout)
    return result.stdout

def get_git_status():
    """
    Retrieves the Git status for the current directory.
    Shows the status.
    """
    result = subprocess.run(['git', 'status'], capture_output=True, text=True)
    print(result.stdout)
    return result.stdout

def commit_changes(message):
    """
    Stages all changes and commits them with the given message.
    Commits all modifications (including new, modified, or deleted files).
    """
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', message], check=True)

giter = Agent(
    name="Agent 007", 
    model="gpt-4o-mini", 
    system_prompt="""
    You are an intelligent agent that assists with Git version control tasks. Your responsibilities include analyzing Git diffs and committing changes based on those diffs.

    1. Use the `get_git_diff()` function to retrieve the latest changes (Git diff).
    2. Use the `commit_changes()` function to commit those changes with an appropriate message.

    Make sure to:
    - Retrieve the Git diff first, analyze the changes.
    - Ensure that the commit message is relevant to the changes and follows best practices (e.g., concise, clear, and descriptive).
    - If you need more information about the diff, analyze the output before committing the changes.
    - Only commit changes when you're confident that they are correct and ready to be saved.

    Your goal is to help automate the process of reviewing changes and committing them in a structured and efficient manner.
    """,
    tools=[get_git_diff, commit_changes]
)