import inspect
import json
import re
import logging

import typing
from typing import get_origin, get_args
from typing import List, Dict

"""
Docstring format for automatic parsing:

1. Write the function description first; it can span multiple lines.
2. For each parameter, start a line with `:param param_name:` followed by its description.
   - Parameter descriptions can also span multiple lines.
   - If a parameter is a dictionary, list its keys on separate indented lines as:
       key: description
     (all key types are assumed to be string)
3. Optionally, use `:return:` to describe the return value; return descriptions can also span multiple lines, and dictionary keys can be listed similarly.
"""

def parse_param_docstring(docstring: str):
    param_descriptions = {}
    lines = docstring.splitlines()
    current_param = None

    for line in lines:
        line = line.rstrip()
        param_match = re.match(r'^\s*:param (\w+):\s*(.*)', line)
        return_match = re.match(r'^\s*:return:', line)

        if param_match:
            current_param, desc = param_match.groups()
            param_descriptions[current_param] = desc.strip()
        elif return_match:
            current_param = None
        elif current_param:
            param_descriptions[current_param] += ';' + line.strip()

    print("PARAM DESCRIPTIONS:", param_descriptions)
    return param_descriptions

def parse_description_docstring(docstring: str) -> str:
    lines = docstring.strip().splitlines()
    description_lines = []

    for line in lines:
        if re.match(r'^\s*:param', line) or re.match(r'^\s*:return', line):
            break
        description_lines.append(line.strip())

    description = ' '.join([l for l in description_lines if l]).strip()
    print("FUNCTION DESCRIPTION:", description)
    return description


def python_type_to_string(python_type):
    if isinstance(python_type, str):
        return {"type": {"str": "string", "int": "integer", "float": "number"}.get(python_type, "string")}
    
    origin = get_origin(python_type)
    args = get_args(python_type)

    if python_type is str:
        return {"type": "string"}
    if python_type is int:
        return {"type": "integer"}
    if python_type is float:
        return {"type": "number"}

    if origin in (list, typing.List):
        inner = args[0] if args else str
        return {"type": "array", "items": python_type_to_string(inner)}

    if origin in (dict, typing.Dict):
        return {"type": "object"}

    return {"type": "string"}

def extract_dict_properties_and_clean_description(param_desc: str):
    lines = [l.strip() for l in param_desc.split(';') if l.strip()]
    main_desc_lines = []
    properties = {}
    for line in lines:
        key_match = re.match(r'^(\w+)\s*:\s*(.+)', line)
        if key_match:
            key, desc = key_match.groups()
            properties[key] = {"type": "string", "description": desc.strip()}
        else:
            main_desc_lines.append(line)
    main_desc = ' '.join(main_desc_lines).strip()
    return main_desc, properties

def function_to_dict(fun):
    fun_doc = fun.__doc__ or ""
    sig = inspect.signature(fun)
    param_descs = parse_param_docstring(fun_doc)
    func_description = parse_description_docstring(fun_doc)

    parameters = {"type": "object", "required": [], "properties": {}, "additionalProperties": False}

    for name, param in sig.parameters.items():
        raw_desc = param_descs.get(name, f"No description provided for {name}")
        main_desc, props = extract_dict_properties_and_clean_description(raw_desc)
        parameters["required"].append(name)

        schema = {"type": "string"}
        origin = get_origin(param.annotation)
        args = get_args(param.annotation)

        if origin in (list, typing.List) and args:
            inner_schema = {"type": "string"}
            if props:
                inner_schema = {"type": "object", "properties": props, "required": list(props.keys())}
            schema = {"type": "array", "items": inner_schema}

        elif props:
            schema = {"type": "object", "properties": props, "required": list(props.keys())}

        parameters["properties"][name] = {"description": main_desc, **schema}

    output = {
        "type": "function",
        "function": {
            "name": fun.__name__,
            "description": func_description,
            "strict": True,
            "parameters": parameters
        }
    }
    print(output)
    return output

def functions_to_dict(functions):
    return [function_to_dict(fun) for fun in functions]

# Example function
def find_file(directory: str, filename: str, recursive: bool = False):
    """
    This is a reST style.

    :param directory: path to the directory
    :param filename: path to file name
    :param recursive: recursive search
    """
    pass

# Example function
def process_files(files: List[Dict], output_dir: str, overwrite: bool = False):
    """
    Processes multiple files and saves the results to the specified output directory.

    :param files: A list of dictionaries with keys describing the input files
        file_path: Relative path to the input file
        content: Content of the input file
    :param output_dir: Directory where the processed files will be saved
    :param overwrite: Whether to overwrite existing files in the output directory
    :return: A summary dictionary with processing results
        processed_count: Number of files successfully processed
        skipped_count: Number of files skipped
    """
    pass

def find_function_by_name(tools, func_name):
    for func in tools:
        if func.__name__ == func_name:
            return func
    return None

class Agent:
    max_handle_tool_calls = 5

    def __init__(self, name, model, system_prompt=None, system_prompt_file=None, tools = []):
        self.token_usage = 0
        self.cached_token_usage = 0
        self.handle_tool_calls_count = 0
        self.name = name
        self.model = model
        self.tools = tools
        self.tools_dict = functions_to_dict(tools)
        self.log_info(f"Initialized with model: {self.model}")

        if system_prompt is not None:
            self.system_prompt = system_prompt
        elif system_prompt_file is not None:
            with open(system_prompt_file, 'r', encoding='utf-8') as file:
                self.system_prompt = file.read()
        else:
            raise ValueError("You must specify either 'system_prompt' or 'system_prompt_file'.")

        self.clear()

    def set_additional_system_prompt(self, prompt):
        self.additional_system_prompt = prompt
        self.update_system_message()

    def log_info(self, message):
        logging.info(f"[{self.name}] {message}")

    def log_error(self, message):
        logging.error(f"[{self.name}] {message}")

    def log_warning(self, message):
        logging.warning(f"[{self.name}] {message}")

    def set_model(self, model):
        self.model = model
        self.log_info(f"Model set to: {self.model}")

    def request(self, client, message):
        self.messages.append({"role": "user", "content": message})
        self.handle_tool_calls_count = 0
        self.log_info(f"User request: {message}")
        return self.create_completion(client)

    def get_user_assistant_messages(self):
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.messages
            if msg.get('role') in {'user', 'assistant'} and msg.get('content')
        ]

    def create_completion(self, client):
        if self.tools_dict:
            completion = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools_dict
            )
        else:
            completion = client.chat.completions.create(
                model=self.model,
                messages=self.messages,
            )

        self.token_usage += completion.usage.total_tokens
        self.cached_token_usage += completion.usage.cached_tokens if 'cached_tokens' in completion.usage else 0
        self.log_info(f"Token usage updated: {completion.usage.total_tokens}, Total tokens used: {self.token_usage}, Cached tokens: {self.cached_token_usage}")

        if completion.choices[0].finish_reason == "tool_calls":
            self.log_info("The model has initiated a tool call.")
            self.messages.append(completion.choices[0].message.dict())
            return self.handle_tool_calls(client, completion.choices[0].message.tool_calls)

        response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        self.log_info(f"Assistant response: {response}")

        return response
    
    def combined_system_prompt(self):
        combined_prompt = self.system_prompt
        if hasattr(self, 'additional_system_prompt') and self.additional_system_prompt:
            combined_prompt += "\n\n" + self.additional_system_prompt
        return combined_prompt
    
    def update_system_message(self):
        combined_prompt = self.combined_system_prompt()

        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = combined_prompt

    def clear(self):
        combined_prompt = self.combined_system_prompt()

        self.messages = [
            {"role": "system", "content": combined_prompt}
        ]

    def soft_reset(self):
        user_assistans_messages = self.get_user_assistant_messages()
        self.clear()
        self.messages.extend(user_assistans_messages)
    
    def handle_tool_calls(self, client, tool_calls):
        if self.handle_tool_calls_count > self.max_handle_tool_calls:
            self.log_error(f"Exceeded maximum tool calls limit: {self.handle_tool_calls_count}")
            return ""

        for tool_call in tool_calls:
            function = find_function_by_name(self.tools, tool_call.function.name)
            if not function:
                self.log_error("Tool call failed: Function not found.")
                continue

            arguments = json.loads(tool_call.function.arguments)
            if isinstance(arguments, list):
                ret = function(*arguments)
            elif isinstance(arguments, dict):
                ret = function(**arguments)
            else:
                self.log_error("Invalid arguments format received for the tool call.")
            self.log_info(f"Call tool {tool_call.function.name} with arguments: {arguments}")
            self.log_info(f"Tool {tool_call.function.name} result: {ret}")
            self.messages.append({
                "role": "tool",
                "content": json.dumps(ret),
                "tool_call_id": tool_call.id
            })

        return self.create_completion(client)