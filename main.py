from lib.agents import Agent
from openai import OpenAI
import os, subprocess

from lib.dev_agent import developer

client = OpenAI()

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
