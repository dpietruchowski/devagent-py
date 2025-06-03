from .agents import Agent
import os, subprocess

def get_git_diff():
    """
    Retrieves the Git diff for the current directory.
    Shows the changes that have been made but not yet committed.
    """
    subprocess.run(['git', 'add', '.'], check=True)
    result = subprocess.run(['git', 'diff', '--staged'], capture_output=True, text=True)
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
    subprocess.run(['git', 'commit', '-m', message], check=True)

giter = Agent(
    name="Git Agent", 
    model="gpt-4o-mini", 
    system_prompt="""
    You are an intelligent agent that assists with Git version control tasks.

    Steps:  
    1. Retrieve the latest Git diff using `get_git_diff()`.  
    2. Analyze the diff.  
    3. Commit with `commit_changes()` using a clear, relevant message.

    Rules:  
    - Always analyze the diff before committing.  
    - Commit only when changes are correct and ready.  
    - Use concise, descriptive commit messages.  
    - Respond briefly — no explanations or Git diff in responses.

    Goal:  
    Automate reviewing and committing changes efficiently.
    """,
    tools=[get_git_diff, commit_changes]
)