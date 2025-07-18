import inspect
import json
import re
import logging

def parse_param_docstring(docstring):
    param_descriptions = {}
    param_pattern = re.compile(r":param (\w+): (.+)")
    for match in param_pattern.findall(docstring):
        param_name, description = match
        param_descriptions[param_name] = description.strip()
    return param_descriptions

def parse_description_docstring(docstring):
    lines = docstring.strip().splitlines()
    description_lines = []
    for line in lines:
        if re.match(r'^\s*:\w+\s', line):
            break
        print(line)
        description_lines.append(line.strip())
    return ' '.join(description_lines).strip()

def python_type_to_string(python_type):
    if python_type == "str":
        return "string"
    return python_type

def function_to_dict(fun):
    fun_name = fun.__name__
    fun_doc = fun.__doc__
    sig = inspect.signature(fun)
    parameters = {
        "type": "object",
        "required": [],
        "properties": {},
        "additionalProperties": False
    }
    param_descriptions = parse_param_docstring(fun_doc)
    description = parse_description_docstring(fun_doc)
    for param_name, param in sig.parameters.items():
        param_info = {
            "description": param_descriptions.get(param_name, f"No description provided for {param_name}"), 
        }
        parameters["required"].append(param_name)
        if param.annotation is not param.empty:
            type_annotation = str(param.annotation).replace("<class '", "").replace("'>", "")
            param_info["type"] = python_type_to_string(type_annotation)
        else:
            param_info["type"] = "string"
        parameters["properties"][param_name] = param_info
    output = {
        "type": "function",
        "function": {
            "name": fun_name,
            "description": description,
            "strict": True,
            "parameters": parameters
        }
    }
    return output

def functions_to_dict(functions):
    functions_info = [function_to_dict(fun) for fun in functions]
    return functions_info

# Example function
def find_file(directory: str, filename: str, recursive: bool = False):
    """
    This is a reST style.

    :param directory: path to the directory
    :param filename: path to file name
    :param recursive: recursive search
    """
    pass

def find_function_by_name(tools, func_name):
    for func in tools:
        if func.__name__ == func_name:
            return func
    return None

def call_function_with_arguments(func, arguments_json):
        if func:
            if isinstance(arguments, list):
                func(*arguments)
            elif isinstance(arguments, dict):
                func(**arguments)
            else:
                print("Invalid arguments format")
        else:
            print("Function not found.")

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

    def clear(self):
        combined_prompt = self.system_prompt
        if hasattr(self, 'additional_system_prompt') and self.additional_system_prompt:
            combined_prompt += "\n" + self.additional_system_prompt

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