import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text
from xml.sax.saxutils import escape
import tiktoken

# 🔹 Wybierz developera: "code_manager" lub "agents"
ACTIVE_DEVELOPER = "agents"

if ACTIVE_DEVELOPER == "code_manager":
    from lib.code_manager.dev_agent import (
        developer,
        client,
        get_summary,
        generate_code_summary_from_file,
        get_code_from_file,
        modify_code_in_file,
        add_new_code,
    )
elif ACTIVE_DEVELOPER == "agents":
    from lib.agents.dev_agent import developer, client, get_file_tree
    # Dla kompatybilności definiujemy funkcje, które nie istnieją w tym agencie
    def get_summary():
        return None

    generate_code_summary_from_file = None
    get_code_from_file = None
    modify_code_in_file = None
    add_new_code = None
else:
    raise ValueError(f"Unknown ACTIVE_DEVELOPER: {ACTIVE_DEVELOPER}")

from lib.agents.git_agent import giter


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
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(filepath, arcname=os.path.basename(filepath))
                os.remove(filepath)

    return compress_old_logs


def set_conversation(conversation_text: str):
    """
    Saves the given conversation text to 'conversation.json'.
    """
    os.makedirs("data", exist_ok=True)
    with open("data/conversation.json", "w", encoding="utf-8") as f:
        f.write(conversation_text)
    print("Conversation saved to conversation.json")


def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)


def main():
    session = PromptSession(multiline=True)
    init_global_log()
    print("Will use model:", developer.model)

    summary = get_summary()
    if summary:
        developer.set_additional_system_prompt(summary)
        developer.clear()

    while True:
        try:
            with patch_stdout():            
                current_file_tree = get_file_tree()
                developer.set_additional_system_prompt(
                    "The file tree represents all files and directories in the project. "
                    "It is a nested dictionary where keys are file or folder names, "
                    "files have value None, and directories have nested dictionaries as their values. "
                    "Only use these files for reading or modification.\n\n"
                    f"Current project files:\n{current_file_tree}"
                )

                user_input = session.prompt("> ")

            if user_input.strip() == "summary":
                if generate_code_summary_from_file:
                    print(json.dumps(generate_code_summary_from_file("src/tests/files/example.h"), indent=4))
                else:
                    print("Summary feature is not available for this developer.")
                continue

            if user_input.strip() == "commit":
                response = giter.request(client, user_input)
                print_formatted_text(HTML(f"{response}"))
                continue

            if user_input.strip() == "reset":
                developer.soft_reset()
                continue

            if user_input.strip() == "clear":
                developer.clear()
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
