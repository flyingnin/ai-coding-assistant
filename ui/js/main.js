(function() {
    // DOM Elements
    const modeToggle = document.getElementById('modeToggle');
    const modeLabel = document.getElementById('modeLabel');
    const standardModeSection = document.getElementById('standardModeSection');
    const contextModeSection = document.getElementById('contextModeSection');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const connectionStatus = document.getElementById('connectionStatus');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const retryConnection = document.getElementById('retry-connection');
    const askButton = document.getElementById('askButton');
    const queryInput = document.getElementById('queryInput');
    const modelSelect = document.getElementById('modelSelect');
    const addFileButton = document.getElementById('addFileButton');
    const addDirButton = document.getElementById('addDirButton');
    const filePath = document.getElementById('filePath');
    
    // Performance metrics
    const tokenCount = document.getElementById('tokenCount');
    const responseTime = document.getElementById('responseTime');
    const contextCount = document.getElementById('contextCount');
    
    // Context stats
    const filesIndexed = document.getElementById('files-indexed');
    const languagesCount = document.getElementById('languages-count');
    const snippetsCount = document.getElementById('snippets-count');

    // WebSocket connection
    let ws = null;
    const wsEndpoint = 'ws://127.0.0.1:9999';
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 2000;
    
    // State variables
    let totalTokens = 0;
    let startTime = 0;
    let isWaitingForResponse = false;
    let isContextMode = false;

    // Initialize the application
    function init() {
        setupEventListeners();
        initWebSocket();
        
        // Add initial welcome message if needed
        if (chatMessages.children.length <= 1) { // Only has welcome message
            addSystemMessage('Connected to Cursor AI Assistant. Type a message to start.');
        }
    }

    // Set up all event listeners
    function setupEventListeners() {
        // Mode toggle
        modeToggle.addEventListener('change', toggleMode);
        
        // Send button
        sendButton.addEventListener('click', sendChatMessage);
        
        // Chat input (Enter to send, Shift+Enter for new line)
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
        
        // Ask button
        askButton.addEventListener('click', function() {
            const query = queryInput.value.trim();
            if (query) {
                addUserMessage(query);
                sendQuery(query);
                queryInput.value = '';
            }
        });
        
        // Context mode buttons
        addFileButton.addEventListener('click', function() {
            const path = filePath.value.trim();
            if (path) {
                addToContext('file', path);
                filePath.value = '';
            }
        });
        
        addDirButton.addEventListener('click', function() {
            const path = filePath.value.trim();
            if (path) {
                addToContext('directory', path);
                filePath.value = '';
            }
        });
        
        // Retry connection
        retryConnection.addEventListener('click', function() {
            initWebSocket();
        });
    }

    // Initialize WebSocket connection
    function initWebSocket() {
        updateConnectionStatus('connecting');
        
        try {
            ws = new WebSocket(wsEndpoint);
            
            ws.onopen = () => {
                updateConnectionStatus('online');
                clearError();
                reconnectAttempts = 0;
                getContextStats(); // Get initial stats
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleServerMessage(data);
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                    // Handle as plain text
                    handleAIResponse(event.data);
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                showError('Failed to connect to the backend service. Please make sure it is running.');
                updateConnectionStatus('offline');
            };
            
            ws.onclose = () => {
                updateConnectionStatus('offline');
                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        reconnectAttempts++;
                        initWebSocket();
                    }, reconnectDelay);
                } else {
                    showError('Connection lost. Maximum reconnection attempts reached.');
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            showError(`Failed to connect: ${error.message}`);
            updateConnectionStatus('offline');
        }
    }

    // Handle different message types from the server
    function handleServerMessage(data) {
        // Handle AI response
        if (data.response) {
            handleAIResponse(data.response);
            updatePerformanceMetrics(data);
        }
        // Handle context status update
        else if (data.context_stats) {
            updateContextStats(data.context_stats);
        }
        // Handle file/directory added confirmation
        else if (data.context_added) {
            addSystemMessage(`Added ${data.context_added.type}: ${data.context_added.path}`);
            getContextStats(); // Update stats after adding
        }
        // Handle errors
        else if (data.error) {
            showError(data.error);
            removeTypingIndicator();
        }
        // Other message types
        else {
            console.log('Received data:', data);
        }
    }

    // Toggle between standard and context modes
    function toggleMode() {
        isContextMode = modeToggle.checked;
        
        if (isContextMode) {
            standardModeSection.style.display = 'none';
            contextModeSection.style.display = 'block';
            modeLabel.textContent = 'Context Mode: ON';
            getContextStats(); // Update context stats when switching to context mode
        } else {
            standardModeSection.style.display = 'block';
            contextModeSection.style.display = 'none';
            modeLabel.textContent = 'Context Mode: OFF';
        }
        
        // Add system message about mode change
        const modeMessage = isContextMode ? 
            'Context Mode enabled. AI responses will use your codebase context.' : 
            'Standard Mode enabled. AI will respond without code context.';
        
        addSystemMessage(modeMessage);
    }

    // Send a chat message
    function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message || isWaitingForResponse) return;
        
        addUserMessage(message);
        
        if (isContextMode) {
            sendContextQuery(message);
        } else {
            sendQuery(message);
        }
        
        chatInput.value = '';
    }

    // Send a query to the backend
    function sendQuery(query) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showError('Not connected to backend. Please wait or try reconnecting.');
            return;
        }
        
        startTime = Date.now();
        isWaitingForResponse = true;
        showTypingIndicator();
        
        const message = {
            type: 'query',
            query: query,
            model: modelSelect.value
        };
        
        ws.send(JSON.stringify(message));
    }

    // Send a context-aware query to the backend
    function sendContextQuery(query) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showError('Not connected to backend. Please wait or try reconnecting.');
            return;
        }
        
        startTime = Date.now();
        isWaitingForResponse = true;
        showTypingIndicator();
        
        const message = {
            type: 'context_query',
            query: query,
            model: modelSelect.value
        };
        
        ws.send(JSON.stringify(message));
    }

    // Add file or directory to context
    function addToContext(type, path) {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            showError('Not connected to backend. Please wait or try reconnecting.');
            return;
        }
        
        addSystemMessage(`Adding ${type}: ${path}...`);
        
        const message = {
            type: 'add_context',
            context_type: type,
            path: path
        };
        
        ws.send(JSON.stringify(message));
    }

    // Get context statistics
    function getContextStats() {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        
        const message = {
            type: 'get_context_stats'
        };
        
        ws.send(JSON.stringify(message));
    }

    // Update context statistics
    function updateContextStats(stats) {
        filesIndexed.textContent = stats.files_indexed || 0;
        languagesCount.textContent = stats.languages_count || 0;
        snippetsCount.textContent = stats.snippets_count || 0;
        
        // Also update the context count in performance panel
        contextCount.textContent = stats.snippets_count || 0;
    }

    // Add a user message to the chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        messageElement.innerHTML = formatMessageWithCodeBlocks(escapeHtml(message));
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    // Add an AI response to the chat
    function addAIMessage(message) {
        removeTypingIndicator();
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message assistant';
        messageElement.innerHTML = formatMessageWithCodeBlocks(escapeHtml(message));
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
        
        isWaitingForResponse = false;
    }

    // Add a system message to the chat
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system';
        messageElement.textContent = message;
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    // Handle AI response
    function handleAIResponse(response) {
        removeTypingIndicator();
        addAIMessage(response);
        
        // Calculate response time
        const responseTimeMs = Date.now() - startTime;
        
        // Update metrics
        updatePerformanceMetrics({
            response_time: responseTimeMs,
            tokens: estimateTokenCount(response)
        });
    }

    // Format message with code blocks
    function formatMessageWithCodeBlocks(message) {
        // Replace ```language ... ``` with proper code blocks
        return message.replace(/```(\w*)([\s\S]*?)```/g, function(match, language, code) {
            language = language.trim();
            code = code.trim();
            return `<pre><code class="language-${language}">${code}</code></pre>`;
        });
    }

    // Show typing indicator
    function showTypingIndicator() {
        removeTypingIndicator(); // Remove existing one first
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        typingIndicator.id = 'typing-indicator';
        
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Show skeleton loading for AI response
    function showSkeletonLoader() {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-message';
        skeleton.id = 'skeleton-loader';
        skeleton.innerHTML = `
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
            <div class="skeleton-line"></div>
        `;
        
        chatMessages.appendChild(skeleton);
        scrollToBottom();
    }

    // Remove skeleton loader
    function removeSkeletonLoader() {
        const skeleton = document.getElementById('skeleton-loader');
        if (skeleton) {
            skeleton.remove();
        }
    }

    // Update connection status UI
    function updateConnectionStatus(status) {
        connectionStatus.className = `status-indicator ${status}`;
        const statusText = connectionStatus.querySelector('.status-text');
        
        switch (status) {
            case 'online':
                statusText.textContent = 'Connected';
                break;
            case 'connecting':
                statusText.textContent = 'Connecting...';
                break;
            case 'offline':
                statusText.textContent = 'Disconnected';
                break;
        }
    }

    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.style.display = 'block';
        
        // Also add as system message
        addSystemMessage(`Error: ${message}`);
    }

    // Clear error message
    function clearError() {
        errorContainer.style.display = 'none';
    }

    // Update performance metrics
    function updatePerformanceMetrics(data) {
        if (data.tokens) {
            totalTokens += data.tokens;
            tokenCount.textContent = totalTokens;
        }
        
        if (data.response_time) {
            responseTime.textContent = `${data.response_time} ms`;
        }
        
        if (data.context_count) {
            contextCount.textContent = data.context_count;
        }
    }

    // Estimate token count based on text length
    function estimateTokenCount(text) {
        if (!text) return 0;
        
        // A simple estimation based on character count
        // On average, 1 token is roughly 4 characters for English text
        return Math.ceil(text.length / 4);
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

    // Scroll chat to bottom with animation
    function scrollToBottom() {
        // Use smooth scrolling behavior for animation
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }

    // Start the application
    document.addEventListener('DOMContentLoaded', init);
})(); 