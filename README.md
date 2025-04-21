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

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables**

Rename the `.env.example` file to `.env` and fill in your API keys:

```env
API_KEY=your_api_key_here
MODEL=Mistral-7B-Instruct
API_BASE_URL=https://your-api-url.com/api/v1
```

3. **Run the server**

```bash
python backend.py
```

The server will start on http://localhost:8000

## Architecture

The system uses a multi-step workflow:
1. FAISS search for concept retrieval
2. Memory retrieval from ChromaDB
3. Reasoning using the LLM with both search results as context
4. Code generation and project management using LangGraph

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This extension is licensed under the [MIT License](LICENSE).

## More Information

For more details about how to use this extension or to report issues, please visit the [GitHub repository](https://github.com/flyingnin/ai-coding-assistant).
