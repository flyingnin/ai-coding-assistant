/**
 * AI Coding Assistant VS Code Extension
 */

const vscode = require('vscode');

// Import components
const webviewPanel = require('./webview/panel');
const state = require('./utils/state');
const { getSettings } = require('./config/settings');

/**
 * Activate the extension
 * @param {vscode.ExtensionContext} context The extension context
 */
function activate(context) {
    console.log('AI Coding Assistant extension is now active');
    
    // Load configuration
    const config = getSettings();
    
    // Initialize state
    state.initialize(context.workspaceState);
    
    // Initialize webview panel
    webviewPanel.initialize(context);
    
    // Register the command to start the AI Coding Assistant
    const startCommandDisposable = vscode.commands.registerCommand('aiCoding.start', () => {
        // Create and show the webview panel
        webviewPanel.createOrShow();
    });
    
    // Add to subscriptions
    context.subscriptions.push(startCommandDisposable);
}

/**
 * Deactivate the extension
 */
function deactivate() {
    console.log('AI Coding Assistant extension is now deactivated');
}

module.exports = {
    activate,
    deactivate
}; 