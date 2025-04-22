/**
 * AI Coding Assistant - Setup Links
 * 
 * This script sets up the proper symlinks between the VS Code extension and the backend.
 * It should be run after cloning both repositories.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration - adjust these paths as needed
const config = {
    // Default paths
    extensionPath: path.resolve(__dirname), // Current directory
    backendPath: path.resolve('..'), // Parent directory
    
    // Files to link (format: [source, target])
    links: [
        // Copy README info to backend
        ['README.md', '../ai-assistant/vscode-extension-README.md'],
        
        // Link frontend resources
        ['frontend/webview.js', '../ai-assistant/webview.js'],
        ['frontend/webview.html', '../ai-assistant/webview.html'],
        ['frontend/styles.css', '../ai-assistant/styles.css']
    ]
};

// Check if we're on Windows
const isWindows = process.platform === 'win32';

/**
 * Create a symbolic link or copy a file
 * @param {string} source Source file path
 * @param {string} target Target file path
 */
function createLink(source, target) {
    const sourcePath = path.resolve(config.extensionPath, source);
    const targetPath = path.resolve(config.extensionPath, target);
    
    console.log(`Linking: ${sourcePath} -> ${targetPath}`);
    
    // Ensure target directory exists
    const targetDir = path.dirname(targetPath);
    if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
        console.log(`Created directory: ${targetDir}`);
    }
    
    try {
        // If target exists, remove it first
        if (fs.existsSync(targetPath)) {
            fs.unlinkSync(targetPath);
            console.log(`Removed existing file: ${targetPath}`);
        }
        
        if (isWindows) {
            // Windows: Use mklink or copy
            try {
                execSync(`mklink "${targetPath}" "${sourcePath}"`);
                console.log(`Created symlink: ${targetPath}`);
            } catch (error) {
                // Fall back to copying on Windows if mklink fails (requires admin)
                fs.copyFileSync(sourcePath, targetPath);
                console.log(`Copied file (mklink failed): ${targetPath}`);
            }
        } else {
            // Unix: Use symlink
            fs.symlinkSync(sourcePath, targetPath);
            console.log(`Created symlink: ${targetPath}`);
        }
    } catch (error) {
        console.error(`Error creating link for ${source} -> ${target}:`, error.message);
    }
}

/**
 * Main function
 */
function main() {
    console.log('Setting up links for AI Coding Assistant...');
    console.log(`Extension path: ${config.extensionPath}`);
    console.log(`Backend path: ${config.backendPath}`);
    
    // Create links
    config.links.forEach(([source, target]) => {
        createLink(source, target);
    });
    
    console.log('Links created successfully!');
    console.log('');
    console.log('Next steps:');
    console.log('1. Install the extension in VS Code (npm run package, then install .vsix)');
    console.log('2. Start the backend server (cd ../ai-assistant && python run_vscode_extension.py)');
    console.log('3. Press Ctrl+Shift+P in VS Code and run "AI Coding: Start"');
}

// Run the main function
main(); 