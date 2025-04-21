# AI Coding Assistant - Setup Guide

This guide helps you set up the AI Coding Assistant VS Code extension and its backend components.

## Prerequisites

- [Node.js](https://nodejs.org/) (v14 or higher)
- [Python](https://www.python.org/) (v3.8 or higher) 
- [VS Code](https://code.visualstudio.com/) (v1.60.0 or higher)
- [Git](https://git-scm.com/)

## Extension Setup (D:\ai-coding-assistant)

1. Clone the extension repository:
   ```bash
   git clone https://github.com/flyingnin/ai-coding-assistant.git D:\ai-coding-assistant
   cd D:\ai-coding-assistant
   ```

2. Install the dependencies:
   ```bash
   npm install
   ```

3. Create the necessary directories if they don't exist:
   ```bash
   mkdir -p frontend resources
   ```

4. Generate the extension files as described in this repository.

5. Package the extension:
   ```bash
   npm run package # or use vsce if available: vsce package
   ```

6. Install the extension in VS Code:
   - Go to Extensions (Ctrl+Shift+X)
   - Click the "..." button at the top
   - Select "Install from VSIX..."
   - Navigate to your .vsix file and install

## Backend Setup (D:\ai-assistant)

1. Clone the backend repository (if available) or create a new directory:
   ```bash
   mkdir -p D:\ai-assistant
   cd D:\ai-assistant
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install fastapi uvicorn websockets langchain faiss-cpu chromadb mistralai
   pip install openai langchainhub langgraph
   ```

4. Create a basic FastAPI server with the required endpoints:
   - Create a file `main.py` that implements:
     - `/start` endpoint (POST) accepting JSON with {goal, project, codebase_path}
     - `/ws` WebSocket endpoint

5. Run the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## Using the Extension

1. Start the backend server from D:\ai-assistant:
   ```bash
   cd D:\ai-assistant
   venv\Scripts\activate  # On Windows
   uvicorn main:app --reload --port 8000
   ```

2. Open VS Code and start the extension:
   - Press `Ctrl+Shift+P`
   - Type and select "AI Coding: Start"
   - The webview UI will open

3. In the UI:
   - Enter your coding goal (e.g., "Build a study tracker app")
   - Enter a project name (e.g., "StudyTracker")
   - Enter the codebase path (e.g., "D:\project")
   - Choose between Git Learning Mode or Project Working Mode
   - Click "Start Project"

4. Monitor the AI agent's output in the scrollable section and track performance metrics.

## Troubleshooting

- **Connection Issues**: Ensure the backend server is running at http://localhost:8000
- **WebSocket Errors**: Check that your backend correctly implements the WebSocket protocol
- **Path Issues**: Ensure file paths are correctly specified in both frontend and backend
- **UI Not Loading**: Check the VS Code Developer Tools (Help > Toggle Developer Tools) for errors

## Advanced Configuration

For advanced configuration options, edit the following files:
- `extension.js`: Main extension functionality
- `frontend/webview.js`: WebSocket and API handling
- `frontend/styles.css`: UI styling

## Example Backend Code (main.py)

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected WebSocket clients
connected_clients = []

class ProjectRequest(BaseModel):
    goal: str
    project: str
    codebase_path: str
    git_learning_mode: bool = False

@app.post("/start")
async def start_project(request: ProjectRequest):
    # In a real implementation, this would initiate your AI workflow
    print(f"Starting project: {request.project}")
    print(f"Goal: {request.goal}")
    print(f"Codebase path: {request.codebase_path}")
    print(f"Git learning mode: {request.git_learning_mode}")
    
    # Send initial message to all connected clients
    if connected_clients:
        for client in connected_clients:
            await client.send_text(json.dumps({
                "prompt": f"Starting new project: {request.project}",
                "tokens": 10,
                "model": "Mistral-7B-Instruct"
            }))
    
    return {"status": "success", "message": "Project started"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "prompt": "Connected to AI Coding Assistant",
            "tokens": 5,
            "model": "Mistral-7B-Instruct"
        }))
        
        # Keep the connection alive and simulate AI messages
        while True:
            data = await websocket.receive_text()
            # In a real implementation, process incoming messages
            
            # For demonstration, send a response after a delay
            await asyncio.sleep(2)
            await websocket.send_text(json.dumps({
                "prompt": "Processing your request...",
                "tokens": 15,
                "model": "Mistral-7B-Instruct"
            }))
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This file provides a basic starting point for your backend implementation. 