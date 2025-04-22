# AI Coding Assistant

A VS Code extension that harnesses the power of AI agents for automating the coding process, helping users with no coding experience to build software by giving developer-like instructions.

## Features

- **Interactive UI**: Beautiful and easy-to-use interface for working with AI agents
- **Mode Toggle**: Switch between "Git Learning Mode" and "Project Working Mode"
- **Performance Tracking**: Monitor token usage and model performance
- **Real-time Updates**: Connect to AI agents via WebSocket for instant prompts
- **Custom Projects**: Specify your own codebase path and project details

## Requirements

- VS Code 1.60.0 or higher
- Backend server running at http://127.0.0.1:9999 (FastAPI backend in D:\ai-assistant)
- Mistral-7B-Instruct model for AI agents
- FAISS/ChromaDB for vector storage
- LangGraph for workflows

## Getting Started

1. Launch VS Code
2. Start the backend server (FastAPI server in D:\ai-assistant)
3. Press `Ctrl+Shift+P` and run the "AI Coding: Start" command
4. Fill in your project details in the webview panel
5. Choose between Git Learning Mode or Project Working Mode
6. Click "Start Project" to begin

## Configuration

The extension connects to:
- HTTP API: http://127.0.0.1:9999/start
- WebSocket: ws://127.0.0.1:9999/ws

## Project Structure

The extension is structured as follows:

```
ai-coding-assistant/
├── src/                        # Source code
│   ├── api/                    # API-related code
│   │   └── websocket.js        # WebSocket client
│   ├── config/                 # Configuration
│   │   └── settings.js         # Settings provider
│   ├── utils/                  # Utilities
│   │   └── state.js            # State management
│   ├── webview/                # Webview-related code
│   │   └── panel.js            # Webview panel management
│   ├── extension.js            # Extension entry point
│   └── README.md               # Source documentation
├── frontend/                   # Frontend assets
│   ├── webview.html            # HTML content
│   ├── webview.js              # Frontend JavaScript
│   └── styles.css              # CSS styles
├── resources/                  # Resources
│   ├── icon.png                # Extension icon
│   └── icon.svg                # Vector version of icon
├── .vscode/                    # VS Code settings
├── package.json                # Extension manifest
├── package-lock.json           # NPM lock file
├── README.md                   # This file
├── SETUP.md                    # Setup instructions
└── LICENSE                     # License information
```

## How It Works

This extension bridges VS Code with a powerful AI backend that uses:
- Mistral-7B-Instruct for AI agents
- FAISS/ChromaDB for vector storage
- LangGraph for workflows
- GAT for codebase analysis
- GitHub for continuous learning

## Backend Features

- Integration with multiple language models including Mistral-7B-Instruct
- Environment-based configuration for API keys
- Vector search with FAISS for concept retrieval
- Persistent memory with ChromaDB
- LangGraph-based workflow for agent orchestration

## Backend Setup

See [SETUP.md](SETUP.md) for detailed setup instructions.

## Architecture

The system uses a multi-step workflow:
1. FAISS search for concept retrieval
2. Memory retrieval from ChromaDB
3. Reasoning using the LLM with both search results as context
4. Code generation and project management using LangGraph

## Development

To work on this extension:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-coding-assistant.git
cd ai-coding-assistant
```

2. Install dependencies:
```bash
npm install
```

3. Open in VS Code:
```bash
code .
```

4. Make your changes in the `src` directory

5. Test by pressing F5 to run the extension in development mode

## Building the Extension

To build the extension:

```bash
npm run package
```

This will create a `.vsix` file that can be installed in VS Code.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This extension is licensed under the [MIT License](LICENSE).

## More Information

For more details about how to use this extension or to report issues, please visit the [GitHub repository](https://github.com/flyingnin/ai-coding-assistant).
