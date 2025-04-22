"""
VS Code Extension Interface

This module provides the interface for the VS Code extension to communicate
with the AI Coding Assistant backend.
"""

import asyncio
import json
import logging
import os
import websockets
from typing import Dict, Any, List, Callable, Optional

# Configure logging
logger = logging.getLogger(__name__)

class VSCodeExtensionInterface:
    """Interface for the VS Code extension to communicate with the AI Coding Assistant."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        """
        Initialize the VS Code extension interface.
        
        Args:
            host: The host to listen on
            port: The port to listen on
        """
        self.host = host
        self.port = port
        self.server = None
        self.connected_clients = set()
        self.message_handlers = {}
        
    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        self.server = await websockets.serve(self._handle_connection, self.host, self.port)
        logger.info("WebSocket server started")
        
        # Keep the server running
        await self.server.wait_closed()
        
    async def _handle_connection(self, websocket, path):
        """Handle a WebSocket connection."""
        try:
            # Add client to connected set
            self.connected_clients.add(websocket)
            logger.info(f"New client connected. Total clients: {len(self.connected_clients)}")
            
            # Send initial status to client
            await websocket.send(json.dumps({
                "type": "status",
                "status": "connected",
                "message": "Connected to AI Coding Assistant backend"
            }))
            
            # Handle messages from the client
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received message: {data}")
                    
                    message_type = data.get("type")
                    if message_type in self.message_handlers:
                        # Call the handler for this message type
                        await self.message_handlers[message_type](websocket, data)
                    else:
                        logger.warning(f"No handler for message type: {message_type}")
                        
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON message"
                    }))
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {e}")
        finally:
            # Remove client from connected set
            self.connected_clients.remove(websocket)
            logger.info(f"Client disconnected. Remaining clients: {len(self.connected_clients)}")
            
    def register_handler(self, message_type: str, handler: Callable):
        """
        Register a handler for a message type.
        
        Args:
            message_type: The message type to handle
            handler: The handler function
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
        
    async def broadcast_message(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        if not self.connected_clients:
            logger.warning("No connected clients to broadcast to")
            return
            
        message_json = json.dumps(message)
        await asyncio.gather(
            *[client.send(message_json) for client in self.connected_clients]
        )
        logger.info(f"Broadcasted message to {len(self.connected_clients)} clients")
        
    async def send_recommendation(self, client, recommendation: Dict[str, Any]):
        """
        Send a recommendation to a client.
        
        Args:
            client: The client to send to
            recommendation: The recommendation to send
        """
        await client.send(json.dumps({
            "type": "recommendation",
            "title": recommendation.get("title", "AI Recommendation"),
            "message": recommendation.get("description", "No description provided"),
            "priority": recommendation.get("priority", 0)
        }))
        logger.info(f"Sent recommendation: {recommendation.get('title')}")
        
    def start(self):
        """Start the server in a background task."""
        asyncio.create_task(self.start_server())
        logger.info("Started VS Code extension interface in background task")
        
    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.close()
            logger.info("Stopped VS Code extension interface")
        else:
            logger.warning("Server not running")
            
    @classmethod
    def create_and_start(cls, host: str = "127.0.0.1", port: int = 9999):
        """
        Create and start the interface.
        
        Args:
            host: The host to listen on
            port: The port to listen on
            
        Returns:
            The interface instance
        """
        interface = cls(host, port)
        interface.start()
        return interface 