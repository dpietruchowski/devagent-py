# dev-agent-py

A lightweight Python framework for building developer agents powered by GPT models and custom tool integrations.

## Features

- Define intelligent developer agents with customizable system prompts  
- Integrate with GPT models via OpenAI API  
- Modular architecture with support for custom tools and workflows  
- Flexible and extensible for diverse tasks beyond programming  
- Agent generates code files inside the `src` directory  
- `switch_model` command changes the GPT model dynamically  
- `commit` command automatically creates git commits  

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or on Windows
venv\Scripts\activate.bat
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic example of using the `Agent` class in `main.py`:

```python
from lib.agent import Agent
from openai import OpenAI

# Initialize your agent and GPT client here
agent = Agent(
    name="DevAgent",
    model="gpt-4o-mini",
    system_prompt="You are a developer assistant.",
    tools=[]
)

# Your usage logic here
```

Run the example:

```bash
python main.py
```

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

[MIT License](LICENSE)
