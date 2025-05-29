from lib.agents import Agent
import os, subprocess, json

from lib.dev_agent import developer, client
from lib.git_agent import giter
from lib.memory import memory

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text
from xml.sax.saxutils import escape

def set_conversation(conversation_text: str):
    """
    Saves the given conversation text to 'conversation.txt'.

    :param conversation_text: The full text of the conversation to be saved.
    """
    with open("conversation.txt", "w", encoding="utf-8") as f:
        f.write(conversation_text)
    print("Conversation saved to conversation.txt")

def main():
    session = PromptSession(multiline=True)
    print("Will use model:", developer.model)

    while True:
        try:
            with patch_stdout():
                user_input = session.prompt("> ")

            if user_input.strip() == "commit":
                response = giter.request(client, user_input)
                print_formatted_text(HTML(f'{response}'))
                continue

            if user_input.strip() == "switch_model":
                developer.model = "gpt-4o-mini" if developer.model == "gpt-4o" else "gpt-4o"
                print("Will use model:", developer.model)
                continue

            response = developer.request(client, user_input)
            print()
            safe_response = escape(response)
            print(response)

            print(developer.messages)

            set_conversation(json.dumps(developer.get_user_assistant_messages()))

            developer.soft_reset()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break



if __name__ == "__main__":
    main()
