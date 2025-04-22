/**
 * State management for the AI Coding Assistant extension
 */

class ExtensionState {
    constructor() {
        // Persistent state (saved across sessions)
        this.persistent = {
            isGitLearningMode: false
        };
        
        // Session state (not persisted)
        this.session = {
            totalTokens: 0,
            currentModel: 'Mistral-7B-Instruct',
            projectInfo: null
        };
        
        // Listeners for state changes
        this.listeners = [];
    }

    /**
     * Initialize the state with values from VS Code workspace state
     * @param {vscode.WorkspaceState} workspaceState The VS Code workspace state
     */
    initialize(workspaceState) {
        if (workspaceState) {
            // Load saved mode preference
            this.persistent.isGitLearningMode = 
                workspaceState.get('aiCoding.isGitLearningMode', false);
        }
    }

    /**
     * Save the persistent state to VS Code workspace state
     * @param {vscode.WorkspaceState} workspaceState The VS Code workspace state
     */
    save(workspaceState) {
        if (workspaceState) {
            workspaceState.update(
                'aiCoding.isGitLearningMode', 
                this.persistent.isGitLearningMode
            );
        }
    }

    /**
     * Update a persistent state value
     * @param {string} key The state key to update
     * @param {any} value The new value
     */
    updatePersistent(key, value) {
        if (key in this.persistent) {
            this.persistent[key] = value;
            this._notifyListeners();
        }
    }

    /**
     * Update a session state value
     * @param {string} key The state key to update
     * @param {any} value The new value
     */
    updateSession(key, value) {
        if (key in this.session) {
            this.session[key] = value;
            this._notifyListeners();
        }
    }

    /**
     * Get the complete state
     * @returns {object} The current state
     */
    getState() {
        return {
            ...this.persistent,
            ...this.session
        };
    }

    /**
     * Register a listener for state changes
     * @param {function} listener The listener function
     */
    addListener(listener) {
        if (typeof listener === 'function') {
            this.listeners.push(listener);
        }
    }

    /**
     * Notify all listeners of a state change
     * @private
     */
    _notifyListeners() {
        const state = this.getState();
        this.listeners.forEach(listener => {
            try {
                listener(state);
            } catch (err) {
                console.error('Error in state change listener:', err);
            }
        });
    }
}

module.exports = new ExtensionState(); 