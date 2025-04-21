const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const WebSocket = require('ws');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // Track webview panel
    let currentPanel = undefined;
    
    // Track AI mode (git learning or project working)
    let isGitLearningMode = false;
    
    // Track token usage
    let totalTokens = 0;
    let currentModel = 'Mistral-7B-Instruct';
    
    // WebSocket connection
    let ws = null;
    
    // Command to start the AI Coding Assistant
    const startCommandDisposable = vscode.commands.registerCommand('aiCoding.start', () => {
        // If panel already exists, show it
        if (currentPanel) {
            currentPanel.reveal(vscode.ViewColumn.One);
            return;
        }
        
        // Create new webview panel
        currentPanel = vscode.window.createWebviewPanel(
            'aiCodingAssistant',
            'AI Coding Assistant',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.file(path.join(context.extensionPath, 'frontend'))
                ],
                retainContextWhenHidden: true
            }
        );
        
        // Set webview icon
        currentPanel.iconPath = vscode.Uri.file(
            path.join(context.extensionPath, 'resources', 'icon.png')
        );
        
        // Get paths for webview resources
        const htmlPath = vscode.Uri.file(path.join(context.extensionPath, 'frontend', 'webview.html'));
        const scriptPath = currentPanel.webview.asWebviewUri(
            vscode.Uri.file(path.join(context.extensionPath, 'frontend', 'webview.js'))
        );
        const stylePath = currentPanel.webview.asWebviewUri(
            vscode.Uri.file(path.join(context.extensionPath, 'frontend', 'styles.css'))
        );
        
        // Read and update the HTML content
        let htmlContent = fs.readFileSync(htmlPath.fsPath, 'utf8');
        htmlContent = htmlContent.replace('${scriptUri}', scriptPath.toString());
        htmlContent = htmlContent.replace('${styleUri}', stylePath.toString());
        
        // Set the webview's HTML content
        currentPanel.webview.html = htmlContent;
        
        // Handle messages from the webview
        currentPanel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'setMode':
                        isGitLearningMode = message.mode === 'gitLearning';
                        // Store this preference in workspace state
                        context.workspaceState.update('aiCoding.isGitLearningMode', isGitLearningMode);
                        break;
                        
                    case 'startProject':
                        // Handle starting a project - will be initiated from the webview
                        break;
                        
                    case 'sendChatMessage':
                        // Handle user chat message - forward to the WebSocket
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            try {
                                ws.send(JSON.stringify({
                                    message: message.text,
                                    git_learning_mode: isGitLearningMode
                                }));
                            } catch (err) {
                                console.error('Error sending message to WebSocket:', err);
                                
                                if (currentPanel) {
                                    currentPanel.webview.postMessage({
                                        command: 'connectionStatus',
                                        status: 'offline',
                                        error: 'Failed to send message to backend.'
                                    });
                                }
                            }
                        } else {
                            if (currentPanel) {
                                currentPanel.webview.postMessage({
                                    command: 'connectionStatus',
                                    status: 'offline',
                                    error: 'WebSocket connection not available.'
                                });
                            }
                            // Try to reconnect
                            initWebSocket();
                        }
                        break;
                }
            },
            undefined,
            context.subscriptions
        );
        
        // Initialize WebSocket connection
        initWebSocket();
        
        // When the panel is closed, clean up resources
        currentPanel.onDidDispose(
            () => {
                currentPanel = undefined;
                if (ws) {
                    ws.close();
                    ws = null;
                }
            },
            null,
            context.subscriptions
        );
    });
    
    context.subscriptions.push(startCommandDisposable);
    
    /**
     * Initialize WebSocket connection to the backend
     */
    function initWebSocket() {
        if (ws) {
            ws.close();
        }
        
        try {
            ws = new WebSocket('ws://localhost:8000/ws');
            
            ws.on('open', () => {
                // Notify the webview that connection is established
                if (currentPanel) {
                    currentPanel.webview.postMessage({ 
                        command: 'connectionStatus', 
                        status: 'online' 
                    });
                }
            });
            
            ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    
                    // Update metrics if available
                    if (message.tokens) {
                        totalTokens += message.tokens;
                    }
                    
                    if (message.model) {
                        currentModel = message.model;
                    }
                    
                    // Send the message to the webview
                    if (currentPanel) {
                        currentPanel.webview.postMessage({
                            command: 'addPrompt',
                            prompt: message.prompt || message.message,
                            data: message
                        });
                        
                        // Update metrics
                        currentPanel.webview.postMessage({
                            command: 'updateMetrics',
                            tokens: totalTokens,
                            model: currentModel
                        });
                    }
                    
                    // Also show as notification for visibility when webview is not focused
                    vscode.window.setStatusBarMessage(`AI: ${message.prompt || message.message}`, 5000);
                } catch (err) {
                    console.error('Error processing WebSocket message:', err);
                    
                    if (currentPanel) {
                        currentPanel.webview.postMessage({
                            command: 'addPrompt',
                            prompt: 'Error processing response from AI. Please try again.',
                            error: true
                        });
                    }
                }
            });
            
            ws.on('error', (error) => {
                console.error('WebSocket connection error:', error);
                
                if (currentPanel) {
                    currentPanel.webview.postMessage({ 
                        command: 'connectionStatus', 
                        status: 'offline',
                        error: 'Connection error. Backend might be offline.'
                    });
                }
            });
            
            ws.on('close', () => {
                if (currentPanel) {
                    currentPanel.webview.postMessage({ 
                        command: 'connectionStatus', 
                        status: 'offline' 
                    });
                }
                
                // Try to reconnect after a delay
                setTimeout(() => {
                    if (currentPanel) {
                        initWebSocket();
                    }
                }, 5000);
            });
        } catch (err) {
            console.error('Failed to create WebSocket connection:', err);
            
            if (currentPanel) {
                currentPanel.webview.postMessage({ 
                    command: 'connectionStatus', 
                    status: 'offline',
                    error: 'Failed to connect to backend. Is the server running?'
                });
            }
        }
    }
}

// This method is called when your extension is deactivated
function deactivate() {
    // Clean up any resources here
}

module.exports = {
    activate,
    deactivate
};