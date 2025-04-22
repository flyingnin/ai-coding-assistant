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
    const projectWorkingSection = document.getElementById('projectWorkingSection');
    const gitLearningSection = document.getElementById('gitLearningSection');

    // Settings
    const apiEndpoint = 'http://127.0.0.1:9999/start';
    const wsEndpoint = 'ws://127.0.0.1:9999/ws';
    let totalTokens = 0;
    let ws = null;
    let isGitLearningMode = false;
    let startTime = 0;
    let isWaitingForResponse = false;
    let learningInProgress = false;

    // Acquired from VS Code extension API
    const vscode = acquireVsCodeApi();

    // Variables for reconnection
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const baseReconnectDelay = 1000; // 1 second

    // Initialize WebSocket connection
    function initWebSocket() {
        updateConnectionStatus('connecting');
        
        try {
            ws = new WebSocket(wsEndpoint);
            
            ws.onopen = () => {
                updateConnectionStatus('online');
                clearError();
                reconnectAttempts = 0; // Reset reconnect attempts on successful connection
                
                // Add initial system message
                addChatMessage("Hello! I'm your AI coding assistant. You can start a project or ask me questions about coding.", 'assistant');
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                    
                    // Handle different types of messages from backend
                    if (data.prompt) {
                        handleAIResponse({
                            prompt: data.prompt,
                            tokens: data.tokens || estimateTokenCount(data.prompt),
                            model: data.model || currentModel
                        });
                    } else if (data.message) {
                        handleAIResponse({
                            prompt: data.message,
                            tokens: data.tokens || estimateTokenCount(data.message),
                            model: data.model || currentModel
                        });
                    } else if (data.learning_progress) {
                        // Update learning progress UI if we're in that mode
                        if (isGitLearningMode) {
                            updateLearningProgress(data.learning_progress);
                        }
                    } else if (data.error) {
                        // Handle explicit error messages from the backend
                        showError(`Server error: ${data.error}`);
                    } else {
                        // Fallback for plain text responses
                        handleAIResponse({
                            prompt: typeof event.data === 'string' ? event.data : JSON.stringify(data),
                            tokens: 10
                        });
                    }
                } catch (err) {
                    console.error('Error parsing WebSocket message:', err);
                    
                    // Try to handle as plain text
                    handleAIResponse({
                        prompt: event.data,
                        tokens: estimateTokenCount(event.data)
                    });
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                const errorMessage = 'Connection to AI assistant failed. ';
                
                // Attempt to provide more specific error information
                if (navigator.onLine === false) {
                    showError(errorMessage + 'Your device appears to be offline. Please check your internet connection.');
                } else {
                    showError(errorMessage + 'Check if backend is running at port 9999.');
                }
                
                updateConnectionStatus('offline');
            };
            
            ws.onclose = () => {
                updateConnectionStatus('offline');
                // Implement exponential backoff for reconnection
                reconnectWithBackoff();
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            showError(`Failed to connect to backend at ${wsEndpoint}`);
            updateConnectionStatus('offline');
            // Attempt to reconnect after an error
            reconnectWithBackoff();
        }
    }

    // Reconnect with exponential backoff
    function reconnectWithBackoff() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            showError(`Maximum reconnection attempts (${maxReconnectAttempts}) reached. Please refresh the page.`);
            return;
        }
        
        reconnectAttempts++;
        const delay = Math.min(30000, baseReconnectDelay * Math.pow(1.5, reconnectAttempts - 1));
        
        console.log(`WebSocket reconnecting in ${delay/1000} seconds (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`);
        updateConnectionStatus('connecting');
        
        setTimeout(() => {
            if (ws && ws.readyState === WebSocket.CLOSED) {
                initWebSocket();
            }
        }, delay);
    }

    // More accurate token estimation using character encoding principles
    function estimateTokenCount(text) {
        if (!text) return 0;
        
        // A more sophisticated approach than simple character counting
        // Based on the fact that most tokenizers handle different character types differently
        
        // Count characters by category
        const alphanumericCount = (text.match(/[a-zA-Z0-9]/g) || []).length;
        const whitespaceCount = (text.match(/\s/g) || []).length;
        const punctuationCount = (text.match(/[.,?!:;'"()\[\]{}]/g) || []).length;
        const symbolCount = (text.match(/[^a-zA-Z0-9\s.,?!:;'"()\[\]{}]/g) || []).length;
        
        // Apply different weights based on token efficiency
        // Alphanumeric characters are most efficiently packed into tokens
        // Special symbols often take more token space
        const weightedCount = 
            alphanumericCount * 0.25 +         // ~4 chars per token
            whitespaceCount * 0.25 +           // ~4 spaces per token
            punctuationCount * 0.5 +           // ~2 punctuation marks per token
            symbolCount * 1.0;                 // ~1 symbol per token
            
        // Add a small base amount for overhead
        const estimatedTokens = Math.ceil(weightedCount) + 2;
        
        // Apply a minimum to avoid very short messages returning 0 tokens
        return Math.max(3, estimatedTokens);
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
        const errorContainer = document.getElementById('error-container');
        const errorMessage = document.getElementById('error-message');
        
        errorMessage.textContent = message;
        errorContainer.style.display = 'block';
        
        // Add troubleshooting suggestions based on error type
        const troubleshootingEl = document.createElement('div');
        troubleshootingEl.className = 'error-troubleshooting';
        
        if (message.includes('WebSocket') || message.includes('connect to backend')) {
            troubleshootingEl.innerHTML = `
                <p>Troubleshooting steps:</p>
                <ol>
                    <li>Check if the backend server is running</li>
                    <li>Verify the server is running on port 9999</li>
                    <li>Restart the backend service if needed</li>
                    <li>Ensure no firewall is blocking the connection</li>
                </ol>
                <button id="retry-connection" class="action-button">Retry Connection</button>
            `;
        } else if (message.includes('API key') || message.includes('authorization')) {
            troubleshootingEl.innerHTML = `
                <p>API authorization issues:</p>
                <ol>
                    <li>Check if your API key is correctly set in the backend</li>
                    <li>Verify the API key has not expired</li>
                    <li>Ensure you have sufficient credits in your account</li>
                </ol>
            `;
        } else if (message.includes('rate limit') || message.includes('too many requests')) {
            troubleshootingEl.innerHTML = `
                <p>Rate limit reached:</p>
                <ol>
                    <li>Wait a few minutes before trying again</li>
                    <li>Consider upgrading your API plan if this happens frequently</li>
                </ol>
            `;
        }
        
        // Replace any existing troubleshooting element
        const existingTroubleshooting = errorContainer.querySelector('.error-troubleshooting');
        if (existingTroubleshooting) {
            errorContainer.removeChild(existingTroubleshooting);
        }
        
        errorContainer.appendChild(troubleshootingEl);
        
        // Add event listener for retry button if present
        const retryButton = document.getElementById('retry-connection');
        if (retryButton) {
            retryButton.addEventListener('click', () => {
                clearError();
                updateConnectionStatus('connecting');
                initWebSocket();
            });
        }
    }

    // Clear error message
    function clearError() {
        const errorContainer = document.getElementById('error-container');
        errorContainer.style.display = 'none';
    }

    // Update GitHub learning progress display with detailed stats
    function updateLearningProgress(progress) {
        if (!isGitLearningMode) return;
        
        const progressBar = document.querySelector('.learning-progress-bar');
        const statusText = document.querySelector('.learning-status');
        const reposAnalyzed = document.getElementById('repos-analyzed');
        const filesProcessed = document.getElementById('files-processed');
        const linesProcessed = document.getElementById('lines-processed');
        const currentRepo = document.getElementById('current-repo');
        
        if (progressBar && statusText) {
            // Handle different types of progress updates
            if (typeof progress === 'object') {
                // Process detailed stats object
                if (progress.percentage !== undefined) {
                    progressBar.style.width = `${progress.percentage}%`;
                    statusText.textContent = `Learning in progress: ${progress.percentage}% complete`;
                }
                
                if (progress.repos_analyzed !== undefined && reposAnalyzed) {
                    reposAnalyzed.textContent = progress.repos_analyzed.toLocaleString();
                }
                
                if (progress.files_processed !== undefined && filesProcessed) {
                    filesProcessed.textContent = progress.files_processed.toLocaleString();
                }
                
                if (progress.lines_processed !== undefined && linesProcessed) {
                    linesProcessed.textContent = progress.lines_processed.toLocaleString();
                }
                
                if (progress.current_repo && currentRepo) {
                    currentRepo.textContent = progress.current_repo;
                }
                
                if (progress.status_message) {
                    statusText.textContent = progress.status_message;
                }
            } else if (typeof progress === 'number') {
                // If it's a simple numeric progress value (0-100)
                progressBar.style.width = `${progress}%`;
                statusText.textContent = `Learning in progress: ${progress}% complete`;
            } else if (typeof progress === 'string') {
                // If it's a simple status message
                statusText.textContent = progress;
            }
        }
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
    
    // Add system message to the chat UI
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system';
        messageElement.textContent = message;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
    
    // Show skeleton loader for AI response
    function showSkeletonLoader() {
        const skeletonDiv = document.createElement('div');
        skeletonDiv.className = 'chat-message assistant skeleton-message';
        skeletonDiv.id = 'skeleton-loader';
        
        // Create skeleton lines with different widths for natural look
        const lineCount = 4;
        for (let i = 0; i < lineCount; i++) {
            const skeletonLine = document.createElement('div');
            skeletonLine.className = 'skeleton-line';
            // Vary the width of each line for a more natural appearance
            skeletonLine.style.width = `${Math.floor(60 + Math.random() * 30)}%`;
            skeletonDiv.appendChild(skeletonLine);
        }
        
        chatMessages.appendChild(skeletonDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Remove skeleton loader
    function removeSkeletonLoader() {
        const skeletonLoader = document.getElementById('skeleton-loader');
        if (skeletonLoader) {
            skeletonLoader.remove();
        }
    }

    // Handle AI response from WebSocket or API
    function handleAIResponse(data) {
        // Remove skeleton loader if present
        removeSkeletonLoader();
        
        const message = data.prompt || data.message || 'No response from AI';
        
        // Update current model if provided
        if (data.model) {
            modelName.textContent = data.model;
        }
        
        addChatMessage(message, 'assistant', data);
        updatePerformanceMetrics(data);
        
        // Re-enable input
        sendButton.disabled = false;
        chatInput.disabled = false;
        isWaitingForResponse = false;
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

    // Start GitHub learning mode
    function startGitHubLearning() {
        // Show learning UI
        gitLearningSection.style.display = 'block';
        projectWorkingSection.style.display = 'none';
        
        // Add system message about learning mode
        addSystemMessage("GitHub Learning Mode activated. AI is analyzing repositories to improve coding assistance.");
        
        // Set learning in progress
        learningInProgress = true;
        
        // If WebSocket is connected, send learning mode command
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                command: 'start_learning',
                mode: 'github'
            }));
        }
        
        // Start animation for progress bar
        const progressBar = document.querySelector('.learning-progress-bar');
        if (progressBar) {
            progressBar.style.animation = 'loadingProgress 2s infinite';
        }
    }

    // Stop GitHub learning mode
    function stopGitHubLearning() {
        // Hide learning UI
        gitLearningSection.style.display = 'none';
        projectWorkingSection.style.display = 'block';
        
        // Add system message about leaving learning mode
        addSystemMessage("GitHub Learning Mode deactivated. Returning to Project Working Mode.");
        
        // Set learning not in progress
        learningInProgress = false;
        
        // If WebSocket is connected, send stop learning command
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                command: 'stop_learning',
                mode: 'github'
            }));
        }
    }

    // Start the project by sending data to the backend
    function startProject() {
        // Don't allow starting a project in learning mode
        if (isGitLearningMode) {
            showError('Please disable GitHub Learning Mode to start a project');
            return;
        }
        
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
        
        // Show skeleton loader
        showSkeletonLoader();
        
        // Set waiting for response
        isWaitingForResponse = true;
        
        // Prepare the request data (match backend expectations)
        const requestData = {
            goal: goalInput.value.trim(),
            project: projectInput.value.trim(),
            codebase_path: pathInput.value.trim()
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
        .then(data => {
            // Remove skeleton loader if present
            removeSkeletonLoader();
            
            if (data.success) {
                // Show the prompt in the chat
                handleAIResponse({
                    prompt: data.prompt,
                    tokens: data.tokens || estimateTokenCount(data.prompt),
                    model: data.model || modelName.textContent
                });
            } else {
                // Show error message
                handleAIResponse({
                    prompt: `Error: ${data.error || 'Unknown error occurred'}`,
                    tokens: 5
                });
            }
        })
        .catch(error => {
            showError(`Failed to start project: ${error.message}`);
            isWaitingForResponse = false;
            
            // Remove skeleton loader
            removeSkeletonLoader();
            
            // Show error in chat
            addChatMessage(`I encountered an error while trying to start the project: ${error.message}. Please make sure the backend server is running at http://127.0.0.1:9999.`, 'assistant');
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
        
        // Show skeleton loader instead of typing indicator
        showSkeletonLoader();
        
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
            
            // If we're in learning mode, no need for a response
            if (isGitLearningMode) {
                // Remove skeleton loader
                removeSkeletonLoader();
                
                addSystemMessage("Your message was received, but direct responses are limited in GitHub Learning Mode.");
                isWaitingForResponse = false;
                sendButton.disabled = false;
                chatInput.disabled = false;
            } else {
                // For project mode, try a regular POST request as fallback
                fetch(apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ goal: message })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.prompt) {
                        handleAIResponse({
                            prompt: data.prompt,
                            tokens: estimateTokenCount(data.prompt)
                        });
                    } else {
                        throw new Error("No prompt in response");
                    }
                })
                .catch(error => {
                    // Remove skeleton loader
                    removeSkeletonLoader();
                    
                    addChatMessage("I'm having trouble connecting to the backend server. Please check that it's running and try again.", 'assistant');
                    isWaitingForResponse = false;
                    sendButton.disabled = false;
                    chatInput.disabled = false;
                });
            }
        }
    }

    // Toggle between Git Learning Mode and Project Working Mode
    function toggleMode() {
        isGitLearningMode = modeToggle.checked;
        modeLabel.textContent = isGitLearningMode ? 'GitHub Learning Mode' : 'Project Working Mode';
        
        // Toggle UI sections
        if (isGitLearningMode) {
            startGitHubLearning();
        } else {
            stopGitHubLearning();
        }
        
        // Save the preference
        vscode.postMessage({
            command: 'setMode',
            mode: isGitLearningMode ? 'gitLearning' : 'projectWorking'
        });
    }

    // Initialize the application
    function init() {
        // Set initial UI state
        if (isGitLearningMode) {
            gitLearningSection.style.display = 'block';
            projectWorkingSection.style.display = 'none';
        } else {
            gitLearningSection.style.display = 'none';
            projectWorkingSection.style.display = 'block';
        }
        
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
                    modeLabel.textContent = isGitLearningMode ? 'GitHub Learning Mode' : 'Project Working Mode';
                    
                    // Update UI sections
                    if (isGitLearningMode) {
                        gitLearningSection.style.display = 'block';
                        projectWorkingSection.style.display = 'none';
                    } else {
                        gitLearningSection.style.display = 'none';
                        projectWorkingSection.style.display = 'block';
                    }
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
                    
                case 'learningProgress':
                    updateLearningProgress(message.progress);
                    break;
            }
        });
    }

    // Initialize when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', init);
})(); 