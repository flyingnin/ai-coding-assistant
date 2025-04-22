# Context Management System for Cursor AI Assistant

This component adds context-aware AI capabilities to the Cursor AI Assistant by storing, retrieving, and utilizing code snippets from the user's codebase to enhance AI responses.

## Features

- **Vector Store**: ChromaDB-based storage for code embeddings
- **Context Manager**: Manages code snippets and retrieves relevant context
- **Context Service**: Service layer for integrating with the main application
- **Context-Aware Agent**: AI agent that uses code context to provide better assistance
- **CLI Tool**: Command-line interface for interacting with the context-aware agent

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenRouter API key (set in `.env` file)

### Installation

1. Ensure you have the required dependencies:
   ```
   pip install chromadb openrouter-python dotenv
   ```

2. Set your OpenRouter API key in `.env`:
   ```
   OPENROUTER_API_KEY=your-api-key-here
   ```

### Usage

#### CLI Tool

The `context_cli.py` script provides a command-line interface for the context-aware agent:

```
# Interactive mode
python context_cli.py interactive

# Add a file to context
python context_cli.py add-file path/to/file.py

# Add a directory to context
python context_cli.py add-dir path/to/directory

# Ask a question
python context_cli.py query "How do I implement the vector store?"

# Show stats
python context_cli.py stats
```

#### Integration with Cursor AI Assistant

The context management system integrates with the main Cursor AI Assistant through the following components:

1. **Context Service**: Connect to this service to use context functionality
2. **Context-Aware Agent**: Use this agent to get context-enhanced AI responses

To start the context service with the main application:

```
python cursor_ai_assistant.py --mode context
```

Or to run all services:

```
python cursor_ai_assistant.py --mode all
```

## Architecture

The context management system consists of the following components:

1. **Vector Store** (`utils/vector_store.py`): Manages the ChromaDB vector database
2. **Context Manager** (`context/manager.py`): Core logic for managing code snippets and embeddings
3. **Context Service** (`services/context_service.py`): Service layer for application integration
4. **Context-Aware Agent** (`agents/context_aware_agent.py`): AI agent using context for better responses
5. **CLI Tool** (`context_cli.py`): Command-line interface for interacting with the system

## Configuration

The system is configurable through various parameters:

- Vector DB path (default: `./data/vector_db`)
- Collection name (default: `cursor_code_context`)
- Embedding model (default: `openai/text-embedding-ada-002`)
- Context window size (default: 5 items)
- Max context tokens (default: 4000 tokens)

## Future Improvements

- Automatic code indexing when files change
- IDE plugin for context-aware suggestions
- Enhanced context processing for better relevance
- Support for multiple context collections for different projects 