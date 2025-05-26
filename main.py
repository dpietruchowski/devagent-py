from lib.agents import Agent
from openai import OpenAI
import os, subprocess

from lib.dev_agent import developer
from lib.git_agent import giter

client = OpenAI()

def main():
    print("Will use model:", developer.model)

    while True:
        try:
            user_input = input("> ")

            if user_input == "commit":
                response = giter.request(client, user_input)
                print("< " + response)
                continue

            if user_input == "switch_model":
                developer.model = "gpt-4o-mini" if developer.model == "gpt-4o" else "gpt-4o"
                print("Will use model:", developer.model)
                continue

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
