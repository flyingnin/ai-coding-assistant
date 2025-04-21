const vscode = require('vscode');
const WebSocket = require('ws');

function activate(context) {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.on('message', (prompt) => {
        vscode.window.showInformationMessage(`Next Step: ${prompt}`);
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.edit(editBuilder => {
                editBuilder.insert(editor.selection.active, `\n${prompt}\n`);
            });
        }
    });
    context.subscriptions.push(vscode.commands.registerCommand('aiCoding.start', async () => {
        const goal = await vscode.window.showInputBox({ prompt: 'Enter your coding goal' });
        const project = await vscode.window.showInputBox({ prompt: 'Enter project name' });
        const codebase_path = await vscode.window.showInputBox({ prompt: 'Enter codebase path (e.g., D:\\new_project)' });
        if (goal && project && codebase_path) {
            fetch('http://localhost:8000/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal, project, codebase_path })
            });
        }
    }));
}

module.exports = { activate };