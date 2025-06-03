from lib.agents.agents import Agent
import os, subprocess, json

from lib.code_manager.dev_agent import developer, client
from lib.agents.git_agent import giter

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text
from xml.sax.saxutils import escape

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def init_global_log():
    os.makedirs("log", exist_ok=True)
    start_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"log/data_{start_time}.log"

    handler = RotatingFileHandler(log_filename, maxBytes=1 * 1024 * 1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    def compress_old_logs():
        import zipfile
        import glob
        log_files = glob.glob("log/data_*.log.*")
        for filepath in log_files:
            zip_path = filepath + ".zip"
            if not os.path.exists(zip_path):
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(filepath, arcname=os.path.basename(filepath))
                os.remove(filepath)

    return compress_old_logs

def set_conversation(conversation_text: str):
    """
    Saves the given conversation text to 'conversation.txt'.

    :param conversation_text: The full text of the conversation to be saved.
    """
    os.makedirs("data", exist_ok=True)
    with open("data/conversation.json", "w", encoding="utf-8") as f:
        f.write(conversation_text)
    print("Conversation saved to conversation.json")

def main():
    session = PromptSession(multiline=True)
    init_global_log()
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
                new_model = "gpt-4o-mini" if developer.model == "gpt-4o" else "gpt-4o"
                developer.set_model(new_model)
                print("Will use model:", developer.model)
                continue

            response = developer.request(client, user_input)
            print()
            safe_response = escape(response)
            print(response)

            set_conversation(json.dumps(developer.messages))

            # developer.soft_reset()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break



if __name__ == "__main__":
    main()
