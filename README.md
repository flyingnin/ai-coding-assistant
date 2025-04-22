# AI Coding Assistant

A comprehensive AI-powered desktop application that helps users with little to no coding experience write code through guided assistance.

## Features

### 🧠 Intelligent Prompting
- Helps build effective AI prompts for coding tasks
- Uses multi-agent architecture to improve quality
- Auto-suggests improvements to prompts

### 🤖 Multiple AI Providers
- Supports OpenRouter, HuggingFace and others
- User-configurable API keys and model selection
- Performance recommendations for different tasks

### 📱 Desktop GUI
- Modern, animated interface for Windows (other platforms coming soon)
- Simple workflow for non-technical users
- Visual code explanations

### 📊 Context Awareness
- Remembers your projects and preferences
- Stores context for better assistance
- Uses ChromaDB for semantic search of past interactions

### 🔄 IDE Integration
- Works with popular code editors
- VS Code extension support
- Quick access to AI assistance

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ai-coding-assistant.git
cd ai-coding-assistant
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the provided `.env.example`:
```bash
cp .env.example .env
```

4. Edit the `.env` file to add your API keys.

## Usage

Start the full application:

```bash
python ai_coding_assistant.py
```

### Command-line options:

```
--mode {notification, automation, vscode, all}   Mode to run (default: all)
```

You can run specific components:
- `--mode notification`: Run only the AI notification agent
- `--mode automation`: Run only the cursor automation features
- `--mode vscode`: Run only the VS Code extension server
- `--mode all`: Run all components (default)

## Project Structure

The project is organized into the following structure:

```
ai-coding-assistant/
├── agents/                    # AI agent implementations
│   ├── __init__.py
│   └── ai_notification_agent.py
├── automation/                # Automation functionality
│   ├── __init__.py
│   └── cursor_automation.py
├── context/                   # Context tracking
│   ├── __init__.py
│   └── cursor_context.py
├── services/                  # Service implementations
│   ├── __init__.py
│   └── notification_service.py
├── ui/                        # User interface components
│   ├── __init__.py
│   └── vscode_extension.py
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── openrouter.py
├── __init__.py                # Package initialization
├── main.py                    # Main entry points
├── ai_coding_assistant.py     # Command-line interface
├── requirements.txt           # Project dependencies
└── README.md                  # This file
```

## Advanced Features

### ChromaDB Integration
- Local vector database for each user
- Project-specific contexts for better assistance
- Delete projects when no longer needed

### Model Selection
- Choose from a variety of AI models
- Configure different models for different agents
- Get recommendations for best performance

### ReAct Framework
- Reasoning and acting capabilities for AI agents
- Better understanding of user requirements
- More accurate code generation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Cursor IDE](https://cursor.sh/) for the amazing code editor
- [OpenRouter](https://openrouter.ai/) for AI model access
- [Pushover](https://pushover.net/) for the notification service
