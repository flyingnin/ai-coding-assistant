# AI Coding Assistant Extension Source

This directory contains the source code for the AI Coding Assistant VS Code extension. The extension is structured using a modular approach to improve maintainability and readability.

## Directory Structure

- **api/**: Contains API-related code
  - `websocket.js`: Client for WebSocket communication with the backend

- **config/**: Contains configuration settings for the extension
  - `settings.js`: Default and override settings

- **utils/**: Contains utility functions and classes
  - `state.js`: State management for the extension

- **webview/**: Contains webview-related code
  - `panel.js`: Manages the webview panel

- `extension.js`: Main entry point of the extension

## Code Organization

The extension follows these design principles:

1. **Separation of Concerns**: Each component has a single responsibility
2. **Modularity**: Components can be modified independently
3. **Reusability**: Components can be reused in different parts of the application
4. **Testability**: Components can be easily tested in isolation

## Architecture

The extension uses a simple architecture:

1. `extension.js` is the entry point that initializes the extension and registers commands
2. `webview/panel.js` manages the webview UI
3. `utils/state.js` manages the state of the extension
4. `api/websocket.js` handles communication with the backend
5. `config/settings.js` provides configuration settings

## Backend Communication

The extension communicates with a backend server running at `http://127.0.0.1:9999` using:

- HTTP API for project initialization and status checks
- WebSocket for real-time communication

## User Interface

The UI is implemented using a webview that loads HTML, CSS, and JavaScript from the `frontend` directory. The UI is responsible for:

1. Displaying project settings and status
2. Providing a chat interface for interacting with the AI
3. Showing performance metrics (token usage, model)
4. Allowing users to switch between modes (Git Learning Mode and Project Working Mode)

## Extending the Extension

To add new features to the extension:

1. Add new files to the appropriate directory
2. Update existing files to use the new functionality
3. Update `extension.js` if needed to register new commands or initialize new components
4. Update the UI in the `frontend` directory if needed

## Building and Packaging

The extension can be built and packaged using the `vsce` tool:

```bash
npm run package
```

This will create a `.vsix` file that can be installed in VS Code. 