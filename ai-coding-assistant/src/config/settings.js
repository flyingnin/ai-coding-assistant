/**
 * Configuration settings for the AI Coding Assistant
 */

/**
 * Default settings
 */
const DEFAULT_SETTINGS = {
    // WebSocket settings
    websocket: {
        url: 'ws://127.0.0.1:9999/ws',
        reconnectInterval: 5000,
        maxReconnectAttempts: 5
    },
    
    // API settings
    api: {
        baseUrl: 'http://127.0.0.1:9999',
        endpoints: {
            start: '/start',
            status: '/status'
        }
    },
    
    // Models
    models: [
        'Mistral-7B-Instruct',
        'OpenAI GPT-4',
        'Gemini Pro',
        'Claude 3'
    ],
    
    // Default model
    defaultModel: 'Mistral-7B-Instruct',
    
    // UI settings
    ui: {
        refreshInterval: 5000,
        maxMessages: 100,
        theme: 'light'
    }
};

/**
 * Get the configuration settings
 * @param {object} overrides Optional setting overrides
 * @returns {object} The configuration settings
 */
function getSettings(overrides = {}) {
    // Deep merge the default settings with any overrides
    return deepMerge(DEFAULT_SETTINGS, overrides);
}

/**
 * Deep merge two objects
 * @param {object} target The target object
 * @param {object} source The source object
 * @returns {object} The merged object
 * @private
 */
function deepMerge(target, source) {
    const result = { ...target };
    
    for (const key in source) {
        if (source[key] instanceof Object && key in target) {
            result[key] = deepMerge(target[key], source[key]);
        } else {
            result[key] = source[key];
        }
    }
    
    return result;
}

module.exports = {
    getSettings
}; 