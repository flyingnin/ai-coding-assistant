(function() {
    // DOM elements
    const startButton = document.getElementById('startButton');
    const goalInput = document.getElementById('goalInput');
    const projectInput = document.getElementById('projectInput');
    const pathInput = document.getElementById('pathInput');
    const promptsContainer = document.getElementById('promptsContainer');
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

    // Acquired from VS Code extension API
    const vscode = acquireVsCodeApi();

    // Initialize WebSocket connection
    function initWebSocket() {
        updateConnectionStatus('connecting');
        
        ws = new WebSocket(wsEndpoint);
        
        ws.onopen = () => {
            updateConnectionStatus('online');
            clearError();
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            addPromptToUI(data.prompt || data.message, data);
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
                if (ws.readyState === WebSocket.CLOSED) {
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

    // Add a prompt to the UI
    function addPromptToUI(prompt, data = {}) {
        const promptElement = document.createElement('div');
        promptElement.className = 'prompt-item';
        promptElement.textContent = prompt;

        // If there's any additional data, we could show it or use it
        if (data.type) {
            promptElement.dataset.type = data.type;
        }

        promptsContainer.appendChild(promptElement);
        promptsContainer.scrollTop = promptsContainer.scrollHeight;
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
        .then(data => {
            addPromptToUI(`Project started: ${requestData.project}`);
        })
        .catch(error => {
            showError(`Failed to start project: ${error.message}`);
        })
        .finally(() => {
            startButton.disabled = false;
        });
    }

    // Toggle between Git Learning Mode and Project Working Mode
    function toggleMode() {
        isGitLearningMode = modeToggle.checked;
        modeLabel.textContent = isGitLearningMode ? 'Git Learning Mode' : 'Project Working Mode';
        
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
                    addPromptToUI(message.prompt, message.data);
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
            }
        });
    }

    // Initialize when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', init);
})(); 