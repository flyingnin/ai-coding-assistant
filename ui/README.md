# Cursor AI Assistant UI

This is the frontend user interface for the Cursor AI Assistant, a context-aware coding assistant that uses your codebase to provide more relevant and accurate AI responses.

## Features

- Clean, modern dark theme interface
- Toggle between standard and context-aware modes
- Add individual files or entire directories to context
- Real-time performance metrics
- Code syntax highlighting in messages
- Smooth scrolling animations
- Responsive design

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js (optional, for development)
- OpenRouter API key (for AI functionality)

### Running the UI

1. Make sure you have installed all required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Start the UI server:
   ```
   python ui_server.py
   ```

3. Open the UI in your browser:
   ```
   http://127.0.0.1:9999
   ```
   Or open `ui/index.html` directly in a browser.

## Usage

### Standard Mode

In standard mode, you can ask questions directly to the AI without any additional context. The AI will respond based on its general knowledge.

1. Type your question in the input field
2. Click "Send" or press Enter
3. View the AI's response in the chat

### Context Mode

Context mode enhances AI responses by using your codebase as additional context.

1. Toggle Context Mode ON
2. Add files or directories to context using the input field and buttons
3. Ask questions about your codebase
4. The AI will use your code as context to provide more relevant responses

## Architecture

The UI consists of:

1. **Frontend:**
   - HTML structure (`index.html`)
   - CSS styling (`css/styles.css`) with responsive design
   - JavaScript functionality (`js/main.js`) for interactivity

2. **Backend:**
   - WebSocket server (`ui_server.py`) to handle communication
   - Integration with the Context-Aware Agent
   - File processing for context enhancement

## WebSocket API

The UI communicates with the backend using a WebSocket API:

- `query`: Send a standard query to the AI
- `context_query`: Send a context-aware query to the AI
- `add_context`: Add a file or directory to context
- `get_context_stats`: Get statistics about the current context

## Customization

You can customize the UI by:

- Modifying `css/styles.css` to change the theme or appearance
- Adding new features to `js/main.js`
- Extending the server API in `ui_server.py`

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details. 