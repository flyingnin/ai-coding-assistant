/**
 * WebSocket API client for communicating with the backend server
 */

const WebSocket = require('ws');

class WebSocketClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.messageHandlers = [];
        this.statusChangeHandlers = [];
    }

    /**
     * Connect to the WebSocket server
     * @param {string} url The WebSocket server URL
     * @returns {Promise} A promise that resolves when connected
     */
    connect(url = 'ws://127.0.0.1:9999/ws') {
        return new Promise((resolve, reject) => {
            try {
                // Close existing connection if any
                if (this.ws) {
                    try {
                        this.ws.close();
                    } catch (e) {
                        console.error('Error closing WebSocket:', e);
                    }
                }

                // Create new connection
                this.ws = new WebSocket(url);
                
                // Set up event handlers
                this.ws.on('open', () => {
                    this.isConnected = true;
                    this._notifyStatusChange('online');
                    resolve();
                });
                
                this.ws.on('message', (data) => {
                    try {
                        const message = JSON.parse(data);
                        this._notifyMessageHandlers(message);
                    } catch (err) {
                        console.error('Error parsing WebSocket message:', err);
                    }
                });
                
                this.ws.on('close', () => {
                    this.isConnected = false;
                    this._notifyStatusChange('offline');
                });
                
                this.ws.on('error', (error) => {
                    this.isConnected = false;
                    this._notifyStatusChange('offline', error.message);
                    reject(error);
                });
                
            } catch (error) {
                this.isConnected = false;
                this._notifyStatusChange('offline', error.message);
                reject(error);
            }
        });
    }

    /**
     * Send a message to the WebSocket server
     * @param {object} message The message to send
     * @returns {boolean} Success status
     */
    sendMessage(message) {
        if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify(message));
            return true;
        } catch (err) {
            console.error('Error sending message to WebSocket:', err);
            return false;
        }
    }

    /**
     * Add a handler for incoming messages
     * @param {function} handler The handler function
     */
    onMessage(handler) {
        if (typeof handler === 'function') {
            this.messageHandlers.push(handler);
        }
    }

    /**
     * Add a handler for connection status changes
     * @param {function} handler The handler function
     */
    onStatusChange(handler) {
        if (typeof handler === 'function') {
            this.statusChangeHandlers.push(handler);
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.ws) {
            try {
                this.ws.close();
            } catch (e) {
                console.error('Error closing WebSocket:', e);
            }
            this.ws = null;
            this.isConnected = false;
            this._notifyStatusChange('offline');
        }
    }

    /**
     * Notify all message handlers of a new message
     * @param {object} message The received message
     * @private
     */
    _notifyMessageHandlers(message) {
        this.messageHandlers.forEach(handler => {
            try {
                handler(message);
            } catch (err) {
                console.error('Error in message handler:', err);
            }
        });
    }

    /**
     * Notify all status change handlers of a status change
     * @param {string} status The new status
     * @param {string} error Optional error message
     * @private
     */
    _notifyStatusChange(status, error = null) {
        this.statusChangeHandlers.forEach(handler => {
            try {
                handler(status, error);
            } catch (err) {
                console.error('Error in status change handler:', err);
            }
        });
    }
}

module.exports = new WebSocketClient(); 