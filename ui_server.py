#!/usr/bin/env python3
"""
UI Server for Cursor AI Assistant

This server handles WebSocket communication with the UI frontend and integrates
with the context-aware agent to provide AI responses.
"""

import os
import json
import asyncio
import logging
import websockets
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import fnmatch

from agents.context_aware_agent import ContextAwareAgent
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ui_server.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class UIServer:
    """Server to handle WebSocket connections for the UI."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9999):
        """Initialize the UI server.
        
        Args:
            host: Host to listen on.
            port: Port to listen on.
        """
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided. Context functionality will be limited.")
        
        # Initialize context-aware agent
        self.agent = ContextAwareAgent(api_key=self.api_key)
        self.agent_started = False
        
        logger.info(f"UI server initialized on {host}:{port}")
    
    async def start_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket server running at ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket):
        """Handle a client connection.
        
        Args:
            websocket: The WebSocket connection.
        """
        # Register client
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Start the agent if not already started
            if not self.agent_started:
                await self.agent.start()
                self.agent_started = True
            
            # Send initial context stats
            await self.send_context_stats(websocket)
            
            # Handle messages
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosedError as e:
            logger.info(f"Connection closed with error: {e}")
        except Exception as e:
            logger.error(f"Error handling client: {str(e)}", exc_info=True)
            error_message = {
                "error": f"Internal server error: {str(e)}"
            }
            await websocket.send(json.dumps(error_message))
        finally:
            # Unregister client
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def process_message(self, websocket, message: str):
        """Process a message from a client.
        
        Args:
            websocket: The WebSocket connection.
            message: The message to process.
        """
        try:
            data = json.loads(message)
            message_type = data.get("type", "")
            
            if message_type == "query":
                await self.handle_query(websocket, data)
            elif message_type == "context_query":
                await self.handle_context_query(websocket, data)
            elif message_type == "add_context":
                await self.handle_add_context(websocket, data)
            elif message_type == "get_context_stats":
                await self.send_context_stats(websocket)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send(json.dumps({"error": f"Unknown message type: {message_type}"}))
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message")
            await websocket.send(json.dumps({"error": "Invalid JSON message"}))
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            await websocket.send(json.dumps({"error": f"Error processing message: {str(e)}"}))
    
    async def handle_query(self, websocket, data: Dict[str, Any]):
        """Handle a standard query.
        
        Args:
            websocket: The WebSocket connection.
            data: The query data.
        """
        query = data.get("query", "")
        model = data.get("model", "openai/gpt-4")
        
        if not query:
            await websocket.send(json.dumps({"error": "Empty query"}))
            return
        
        logger.info(f"Processing query: {query}")
        start_time = datetime.now()
        
        # Get response from agent
        response = await self.agent.process_query(query)
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if response["success"]:
            result = {
                "response": response["data"]["response"],
                "tokens": len(response["data"]["response"].split()) * 1.3,  # Rough estimation
                "response_time": int(response_time),
                "model": model,
                "context_count": 0
            }
            await websocket.send(json.dumps(result))
        else:
            await websocket.send(json.dumps({"error": response.get("error", "Unknown error")}))
    
    async def handle_context_query(self, websocket, data: Dict[str, Any]):
        """Handle a context-aware query.
        
        Args:
            websocket: The WebSocket connection.
            data: The query data.
        """
        query = data.get("query", "")
        model = data.get("model", "openai/gpt-4")
        
        if not query:
            await websocket.send(json.dumps({"error": "Empty query"}))
            return
        
        logger.info(f"Processing context query: {query}")
        start_time = datetime.now()
        
        # Get response from agent
        response = await self.agent.process_query(query)
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        if response["success"]:
            result = {
                "response": response["data"]["response"],
                "tokens": len(response["data"]["response"].split()) * 1.3,  # Rough estimation
                "response_time": int(response_time),
                "model": model,
                "context_count": response["data"]["context_count"] if "context_count" in response["data"] else 0
            }
            await websocket.send(json.dumps(result))
        else:
            await websocket.send(json.dumps({"error": response.get("error", "Unknown error")}))
    
    async def handle_add_context(self, websocket, data: Dict[str, Any]):
        """Handle adding context from a file or directory.
        
        Args:
            websocket: The WebSocket connection.
            data: The context data.
        """
        path_str = data.get("path", "")
        is_directory = data.get("is_directory", False)
        
        if not path_str:
            await websocket.send(json.dumps({"error": "Empty path"}))
            return
        
        try:
            # Convert to Path object
            path = Path(path_str)
            
            # Validate path
            if not path.exists():
                await websocket.send(json.dumps({"error": f"Path does not exist: {path_str}"}))
                return
            
            if is_directory:
                logger.info(f"Processing directory for context: {path_str}")
                await self.process_directory(websocket, path)
            else:
                logger.info(f"Processing file for context: {path_str}")
                
                # Check if it's a file
                if not path.is_file():
                    await websocket.send(json.dumps({"error": f"Not a file: {path_str}"}))
                    return
                
                # Process file
                try:
                    # Read file content
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Add to context
                    result = await self.agent.add_context_from_text(
                        content, 
                        metadata={
                            "file_path": str(path),
                            "file_name": path.name,
                            "file_type": path.suffix.lstrip('.'),
                        }
                    )
                    
                    if result["success"]:
                        await websocket.send(json.dumps({"status": "File processed successfully"}))
                        # Update stats for all clients
                        await self.broadcast(json.dumps({"type": "context_updated"}))
                    else:
                        await websocket.send(json.dumps({"error": result.get("error", "Unknown error")}))
                        
                except Exception as e:
                    logger.error(f"Error processing file {path_str}: {str(e)}", exc_info=True)
                    await websocket.send(json.dumps({"error": f"Error processing file: {str(e)}"}))
                
        except Exception as e:
            logger.error(f"Error adding context: {str(e)}", exc_info=True)
            await websocket.send(json.dumps({"error": f"Error adding context: {str(e)}"}))

    async def process_directory(self, websocket, dir_path: Path):
        """Process a directory recursively and add valid files to context.
        
        Args:
            websocket: The WebSocket connection.
            dir_path: Path to the directory.
        """
        # File extensions to process
        valid_extensions = [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
            ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".php", ".rb",
            ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".sh", ".bat"
        ]
        
        # Files to ignore
        ignore_patterns = [
            "node_modules", "__pycache__", ".git", ".vscode", ".idea",
            "venv", "env", "build", "dist", "*.min.*"
        ]
        
        try:
            # Count total valid files (for progress reporting)
            valid_files = []
            total_files = 0
            processed_files = 0
            
            # First pass: collect valid files
            for file_path in dir_path.rglob("*"):
                # Skip directories
                if file_path.is_dir():
                    continue
                
                # Skip files with invalid extensions or in ignored directories
                should_skip = False
                for pattern in ignore_patterns:
                    if "*" in pattern:
                        # Handle wildcard pattern
                        if fnmatch.fnmatch(file_path.name, pattern):
                            should_skip = True
                            break
                    else:
                        # Check if pattern is in path
                        if pattern in str(file_path):
                            should_skip = True
                            break
                
                if should_skip:
                    continue
                
                # Check extension
                if file_path.suffix.lower() in valid_extensions:
                    valid_files.append(file_path)
                    total_files += 1
            
            # Check if we have files to process
            if total_files == 0:
                await websocket.send(json.dumps({
                    "warning": f"No valid files found in directory: {dir_path}"
                }))
                return
            
            # Process files
            for file_path in valid_files:
                try:
                    # Update progress
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    
                    # Send progress update
                    await websocket.send(json.dumps({
                        "processing_progress": {
                            "current": processed_files,
                            "total": total_files,
                            "percentage": progress,
                            "current_file": file_path.name
                        }
                    }))
                    
                    # Read file content
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Add to context
                    result = await self.agent.add_context_from_text(
                        content, 
                        metadata={
                            "file_path": str(file_path),
                            "file_name": file_path.name,
                            "file_type": file_path.suffix.lstrip('.'),
                        }
                    )
                    
                    if not result["success"]:
                        logger.warning(f"Failed to add {file_path} to context: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)
            
            # Final update
            await websocket.send(json.dumps({
                "status": f"Directory processed successfully. Added {processed_files} files to context."
            }))
            
            # Update stats for all clients
            await self.broadcast(json.dumps({"type": "context_updated"}))
            
        except Exception as e:
            logger.error(f"Error processing directory {dir_path}: {str(e)}", exc_info=True)
            await websocket.send(json.dumps({"error": f"Error processing directory: {str(e)}"}))

    async def send_context_stats(self, websocket):
        """Send context statistics to the client.
        
        Args:
            websocket: The WebSocket connection.
        """
        try:
            # Ensure agent is started
            if not self.agent_started:
                await self.agent.start()
                self.agent_started = True
            
            # Get context stats directly from the context service
            stats = self.agent.context_service.get_stats()
            
            if stats["success"]:
                await websocket.send(json.dumps({
                    "context_stats": stats["data"]
                }))
            else:
                await websocket.send(json.dumps({
                    "error": stats.get("error", "Unknown error getting context stats")
                }))
                
        except Exception as e:
            logger.error(f"Error getting context stats: {str(e)}", exc_info=True)
            await websocket.send(json.dumps({
                "error": f"Error getting context stats: {str(e)}"
            }))
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        if not self.clients:
            return
            
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )
    
    async def stop(self):
        """Stop the server and clean up resources."""
        if self.agent_started:
            await self.agent.stop()
            self.agent_started = False
            
        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )
            self.clients.clear()
            
        logger.info("UI server stopped")

async def main():
    """Main entry point for the UI server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Cursor AI Assistant UI Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9999, help="Port to listen on")
    args = parser.parse_args()
    
    # Create and start the server
    server = UIServer(host=args.host, port=args.port)
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main()) 