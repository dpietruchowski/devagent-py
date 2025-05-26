import inspect
import json
import re

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
        self.handle_tool_calls_count = 0
        self.name = name
        self.model = model
        self.tools = tools
        self.tools_dict = functions_to_dict(tools)

        if system_prompt is not None:
            self.system_prompt = system_prompt
        elif system_prompt_file is not None:
            with open(system_prompt_file, 'r', encoding='utf-8') as file:
                self.system_prompt = file.read()
        else:
            raise ValueError("You must specify either 'system_prompt' or 'system_prompt_file'.")

        self.clear()

    def request(self, client, message):
        self.messages.append({"role": "user", "content": message})
        self.handle_tool_calls_count = 0

        return self.create_completion(client)

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
        print("###### Token usage:", completion.usage.total_tokens, self.token_usage, "########")

        if completion.choices[0].finish_reason == "tool_calls":
            print("Model made a tool call.")
            self.messages.append(completion.choices[0].message)
            return self.handle_tool_calls(client, completion.choices[0].message.tool_calls)

        response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})

        return response

    def clear(self):
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
    
    def handle_tool_calls(self, client, tool_calls):
        if self.handle_tool_calls_count > self.max_handle_tool_calls:
            print("Too many tool_calls count", self.handle_tool_calls_count)
            return ""

        for tool_call in tool_calls:
            function = find_function_by_name(self.tools, tool_call.function.name)
            if not function:
                print("Function not found.")
                continue

            arguments = json.loads(tool_call.function.arguments)
            if isinstance(arguments, list):
                ret = function(*arguments)
            elif isinstance(arguments, dict):
                ret = function(**arguments)
            else:
                print("Invalid arguments format")

            self.messages.append({
                "role": "tool",
                "content": json.dumps(ret),
                "tool_call_id": tool_call.id
            })

        return self.create_completion(client)