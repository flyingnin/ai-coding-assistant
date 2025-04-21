(function() {
    // DOM elements
    const startButton = document.getElementById('startButton');
    const goalInput = document.getElementById('goalInput');
    const projectInput = document.getElementById('projectInput');
    const pathInput = document.getElementById('pathInput');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const modeToggle = document.getElementById('modeToggle');
    const modeLabel = document.getElementById('modeLabel');
    const connectionStatus = document.getElementById('connectionStatus');
    const errorMessage = document.getElementById('errorMessage');
    const tokenCount = document.getElementById('tokenCount');
    const responseTime = document.getElementById('responseTime');
    const modelName = document.getElementById('modelName');

    // Settings
    const apiEndpoint = 'http://localhost:8000/start';
    const wsEndpoint = 'ws://localhost:8000/ws';
    let totalTokens = 0;
    let ws = null;
    let isGitLearningMode = false;
    let startTime = 0;
    let isWaitingForResponse = false;

    // Acquired from VS Code extension API
    const vscode = acquireVsCodeApi();

    // Initialize WebSocket connection
    function initWebSocket() {
        updateConnectionStatus('connecting');
        
        ws = new WebSocket(wsEndpoint);
        
        ws.onopen = () => {
            updateConnectionStatus('online');
            clearError();
            
            // Add initial system message
            addChatMessage("Hello! I'm your AI coding assistant. You can start a project or ask me questions about coding.", 'assistant');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleAIResponse(data);
            updatePerformanceMetrics(data);
        };
        
        ws.onerror = (error) => {
            showError('WebSocket error occurred. Check if backend is running.');
            updateConnectionStatus('offline');
        };
        
        ws.onclose = () => {
            updateConnectionStatus('offline');
            // Try to reconnect after 5 seconds
            setTimeout(() => {
                if (ws && ws.readyState === WebSocket.CLOSED) {
                    initWebSocket();
                }
            }, 5000);
        };
    }

    // Update connection status UI
    function updateConnectionStatus(status) {
        connectionStatus.className = `status-indicator ${status}`;
        const statusTextElement = connectionStatus.querySelector('.status-text');
        
        switch(status) {
            case 'online':
                statusTextElement.textContent = 'Connected';
                break;
            case 'connecting':
                statusTextElement.textContent = 'Connecting...';
                break;
            case 'offline':
                statusTextElement.textContent = 'Disconnected';
                break;
        }
    }

    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    // Clear error message
    function clearError() {
        errorMessage.textContent = '';
        errorMessage.style.display = 'none';
    }

    // Add a message to the chat UI
    function addChatMessage(message, sender, data = {}) {
        // Remove welcome message if it exists
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            chatMessages.removeChild(welcomeMessage);
        }
        
        // Remove typing indicator if it exists
        const typingIndicator = chatMessages.querySelector('.typing-indicator');
        if (typingIndicator) {
            chatMessages.removeChild(typingIndicator);
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        
        // Format code blocks if any
        let formattedMessage = message;
        if (sender === 'assistant') {
            formattedMessage = formatMessageWithCodeBlocks(message);
        }
        
        messageElement.innerHTML = formattedMessage;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // If this is an assistant message, stop waiting for response
        if (sender === 'assistant') {
            isWaitingForResponse = false;
            sendButton.disabled = false;
            chatInput.disabled = false;
        }
    }
    
    // Format message with code blocks
    function formatMessageWithCodeBlocks(message) {
        // Simple code block detection for demonstration
        // In a real implementation, you might want to use a more robust parser
        const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
        let formattedMessage = message.replace(codeBlockRegex, function(match, language, code) {
            const lang = language || '';
            return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Format inline code
        const inlineCodeRegex = /`([^`]+)`/g;
        formattedMessage = formattedMessage.replace(inlineCodeRegex, '<code>$1</code>');
        
        return formattedMessage;
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message assistant typing-indicator';
        typingElement.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Handle AI response
    function handleAIResponse(data) {
        const message = data.prompt || data.message || 'No response from AI';
        addChatMessage(message, 'assistant', data);
    }

    // Update performance metrics
    function updatePerformanceMetrics(data) {
        // Update token count if available
        if (data.tokens) {
            totalTokens += data.tokens;
            tokenCount.textContent = totalTokens;
        }

        // Calculate response time
        if (startTime > 0) {
            const endTime = Date.now();
            const latency = endTime - startTime;
            responseTime.textContent = `${latency} ms`;
            startTime = 0;
        }

        // Update model name if available
        if (data.model) {
            modelName.textContent = data.model;
        }
    }

    // Start the project by sending data to the backend
    function startProject() {
        // Validate inputs
        if (!goalInput.value.trim()) {
            showError('Please enter a coding goal');
            return;
        }
        
        if (!projectInput.value.trim()) {
            showError('Please enter a project name');
            return;
        }
        
        if (!pathInput.value.trim()) {
            showError('Please enter a codebase path');
            return;
        }

        // Clear any previous errors
        clearError();
        
        // Disable button to prevent multiple submissions
        startButton.disabled = true;
        
        // Record start time for response time calculation
        startTime = Date.now();
        
        // Show user's project request in chat
        const userMessage = `Start project "${projectInput.value.trim()}" with goal: ${goalInput.value.trim()}`;
        addChatMessage(userMessage, 'user');
        
        // Show typing indicator
        showTypingIndicator();
        
        // Set waiting for response
        isWaitingForResponse = true;
        
        // Prepare the request data
        const requestData = {
            goal: goalInput.value.trim(),
            project: projectInput.value.trim(),
            codebase_path: pathInput.value.trim(),
            git_learning_mode: isGitLearningMode
        };
        
        // Send the request to the backend
        fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            showError(`Failed to start project: ${error.message}`);
            isWaitingForResponse = false;
            
            // Remove typing indicator
            const typingIndicator = chatMessages.querySelector('.typing-indicator');
            if (typingIndicator) {
                chatMessages.removeChild(typingIndicator);
            }
        })
        .finally(() => {
            startButton.disabled = false;
        });
    }

    // Send a chat message to the AI
    function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message || isWaitingForResponse) return;
        
        // Clear the input
        chatInput.value = '';
        
        // Add the message to the chat
        addChatMessage(message, 'user');
        
        // Show typing indicator
        showTypingIndicator();
        
        // Disable input while waiting for response
        sendButton.disabled = true;
        chatInput.disabled = true;
        isWaitingForResponse = true;
        
        // Record start time for response time calculation
        startTime = Date.now();
        
        // Send the message to the WebSocket
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                message: message,
                git_learning_mode: isGitLearningMode
            }));
        } else {
            showError('WebSocket connection lost. Trying to reconnect...');
            initWebSocket();
            isWaitingForResponse = false;
            sendButton.disabled = false;
            chatInput.disabled = false;
        }
    }

    // Toggle between Git Learning Mode and Project Working Mode
    function toggleMode() {
        isGitLearningMode = modeToggle.checked;
        modeLabel.textContent = isGitLearningMode ? 'Git Learning Mode' : 'Project Working Mode';
        
        // Add mode change notification to chat
        addChatMessage(`Switched to ${isGitLearningMode ? 'Git Learning Mode' : 'Project Working Mode'}`, 'assistant');
        
        // Save the preference
        vscode.postMessage({
            command: 'setMode',
            mode: isGitLearningMode ? 'gitLearning' : 'projectWorking'
        });
    }

    // Initialize the application
    function init() {
        // Add event listeners
        startButton.addEventListener('click', startProject);
        modeToggle.addEventListener('change', toggleMode);
        sendButton.addEventListener('click', sendChatMessage);
        
        // Handle Enter key for chat
        chatInput.addEventListener('keydown', event => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatMessage();
            }
        });
        
        // Initialize WebSocket connection
        initWebSocket();
        
        // Listen for messages from the extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
                case 'updateMode':
                    isGitLearningMode = message.mode === 'gitLearning';
                    modeToggle.checked = isGitLearningMode;
                    modeLabel.textContent = isGitLearningMode ? 'Git Learning Mode' : 'Project Working Mode';
                    break;
                    
                case 'addPrompt':
                    handleAIResponse(message);
                    break;
                    
                case 'updateMetrics':
                    if (message.tokens) {
                        totalTokens = message.tokens;
                        tokenCount.textContent = totalTokens;
                    }
                    if (message.model) {
                        modelName.textContent = message.model;
                    }
                    break;
                    
                case 'connectionStatus':
                    updateConnectionStatus(message.status);
                    if (message.error) {
                        showError(message.error);
                    }
                    break;
            }
        });
    }

    // Initialize when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', init);
})(); 