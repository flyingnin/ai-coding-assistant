/**
 * Webview panel management for the AI Coding Assistant
 */

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

// Import utilities
const websocket = require('../api/websocket');
const state = require('../utils/state');

class WebviewPanel {
    constructor() {
        this.panel = undefined;
        this.context = undefined;
    }

    /**
     * Initialize the webview panel
     * @param {vscode.ExtensionContext} context The extension context
     */
    initialize(context) {
        this.context = context;
    }

    /**
     * Create and show the webview panel
     */
    createOrShow() {
        // If the panel already exists, show it
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.One);
            return;
        }

        // Create a new panel
        this.panel = vscode.window.createWebviewPanel(
            'aiCodingAssistant',
            'AI Coding Assistant',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                localResourceRoots: [
                    vscode.Uri.file(path.join(this.context.extensionPath, 'frontend'))
                ],
                retainContextWhenHidden: true
            }
        );

        // Set the panel icon
        this.panel.iconPath = vscode.Uri.file(
            path.join(this.context.extensionPath, 'resources', 'icon.png')
        );

        // Load the HTML content
        this._setHtmlContent();

        // Set up message handlers
        this._setupMessageHandlers();

        // Update the webview with current state
        this._updateWebviewState();

        // Set up WebSocket event handlers
        this._setupWebSocketHandlers();

        // Handle panel disposal
        this.panel.onDidDispose(() => {
            this.panel = undefined;
            websocket.disconnect();
        }, null, this.context.subscriptions);
    }

    /**
     * Load and set the HTML content for the webview
     * @private
     */
    _setHtmlContent() {
        try {
            // Get paths for webview resources
            const htmlPath = vscode.Uri.file(
                path.join(this.context.extensionPath, 'frontend', 'webview.html')
            );
            const scriptPath = this.panel.webview.asWebviewUri(
                vscode.Uri.file(path.join(this.context.extensionPath, 'frontend', 'webview.js'))
            );
            const stylePath = this.panel.webview.asWebviewUri(
                vscode.Uri.file(path.join(this.context.extensionPath, 'frontend', 'styles.css'))
            );

            // Read and update the HTML content
            let htmlContent = fs.readFileSync(htmlPath.fsPath, 'utf8');
            htmlContent = htmlContent.replace('${scriptUri}', scriptPath.toString());
            htmlContent = htmlContent.replace('${styleUri}', stylePath.toString());

            // Set the webview's HTML content
            this.panel.webview.html = htmlContent;
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to load webview content: ${error.message}`);
        }
    }

    /**
     * Set up message handlers for messages from the webview
     * @private
     */
    _setupMessageHandlers() {
        this.panel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                    case 'setMode':
                        // Update the state with the new mode
                        const isGitLearningMode = message.mode === 'gitLearning';
                        state.updatePersistent('isGitLearningMode', isGitLearningMode);
                        state.save(this.context.workspaceState);

                        // Send mode change to backend
                        websocket.sendMessage({
                            command: isGitLearningMode ? 'start_learning' : 'stop_learning',
                            mode: 'github'
                        });
                        break;

                    case 'startProject':
                        // Store project info in session state
                        state.updateSession('projectInfo', {
                            goal: message.goal,
                            project: message.project,
                            codebasePath: message.codebasePath
                        });

                        // Send project info to backend
                        websocket.sendMessage({
                            command: 'start_project',
                            goal: message.goal,
                            project: message.project,
                            codebase_path: message.codebasePath,
                            git_learning_mode: state.persistent.isGitLearningMode
                        });
                        break;

                    case 'sendChatMessage':
                        // Send the chat message to the backend
                        websocket.sendMessage({
                            message: message.text,
                            git_learning_mode: state.persistent.isGitLearningMode
                        });
                        break;

                    case 'requestLearningStatus':
                        // Request learning status from backend
                        websocket.sendMessage({
                            command: 'get_learning_status'
                        });
                        break;
                }
            },
            undefined,
            this.context.subscriptions
        );
    }

    /**
     * Set up WebSocket event handlers
     * @private
     */
    _setupWebSocketHandlers() {
        // Handle WebSocket status changes
        websocket.onStatusChange((status, error) => {
            if (this.panel) {
                this.panel.webview.postMessage({ 
                    command: 'connectionStatus', 
                    status, 
                    error
                });
            }
        });

        // Handle incoming WebSocket messages
        websocket.onMessage(message => {
            if (this.panel) {
                // Forward the message to the webview
                this.panel.webview.postMessage(message);

                // Update token usage if available
                if (message.tokens) {
                    const currentTokens = state.session.totalTokens;
                    state.updateSession('totalTokens', currentTokens + message.tokens);
                }

                // Update model if available
                if (message.model) {
                    state.updateSession('currentModel', message.model);
                }
            }
        });

        // Connect to the WebSocket server
        websocket.connect();
    }

    /**
     * Update the webview with the current state
     * @private
     */
    _updateWebviewState() {
        if (this.panel) {
            // Send current mode
            this.panel.webview.postMessage({
                command: 'updateMode',
                mode: state.persistent.isGitLearningMode ? 'gitLearning' : 'projectWorking'
            });

            // Send project info if available
            if (state.session.projectInfo) {
                this.panel.webview.postMessage({
                    command: 'updateProjectInfo',
                    projectInfo: state.session.projectInfo
                });
            }

            // Send token usage
            this.panel.webview.postMessage({
                command: 'updateMetrics',
                tokens: state.session.totalTokens,
                model: state.session.currentModel
            });
        }
    }
}

module.exports = new WebviewPanel(); 