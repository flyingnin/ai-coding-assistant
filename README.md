# AI Coding Assistant

A VS Code extension with AI-agents for automation of the entire coding process, enhanced with a FastAPI backend for multi-agent AI systems.

## About

This is primarily designed for people with little to no coding experience to use this extension in order to give Cursor (or any other IDE) dev-like orders, ensuring easy use and filling in the gaps of your coding knowledge by using different AI-agents.

## Backend Features

- Integration with OpenRouter to access meta-llama/Llama-2-7b-chat-hf
- Environment-based configuration for API keys
- Vector search with FAISS for concept retrieval
- Persistent memory with ChromaDB
- LangGraph-based workflow for agent orchestration

## Setup

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables**

Rename the `.env.example` file to `.env` and fill in your OpenRouter API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=meta-llama/Llama-2-7b-chat-hf:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

You can get an API key from [OpenRouter](https://openrouter.ai/).

3. **Run the server**

```bash
python backend.py
```

The server will start on http://0.0.0.0:5000

## API Endpoints

### Generate Prompt

```
POST /generate_prompt
```

Request body:
```json
{
  "query": "Your query here"
}
```

Response:
```json
{
  "prompt": "Generated response from the LLM"
}
```

## Architecture

The system uses a three-step workflow:
1. FAISS search for concept retrieval
2. Memory retrieval from ChromaDB
3. Reasoning using the LLM with both search results as context

## Development

Feel free to extend the system by:
- Adding more tools to the agent
- Implementing additional LangGraph nodes
- Creating new API endpoints for different functionalities
