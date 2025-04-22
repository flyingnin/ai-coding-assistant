"""
Context Service

This service provides an interface to access and manage code context functionality
for the Cursor AI Assistant.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable

from context.manager import ContextManager

# Configure logging
logger = logging.getLogger(__name__)

class ContextService:
    """Service for managing code context and providing relevant information to the AI assistant."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the context service.
        
        Args:
            api_key: The OpenRouter API key. If None, will attempt to load from environment.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No API key provided for ContextService. Context functionality will be limited.")
            self.context_manager = None
        else:
            self.context_manager = ContextManager(
                openrouter_api_key=self.api_key,
                vector_db_path=os.path.join(os.path.dirname(__file__), "..", "data", "vector_db"),
                collection_name="cursor_code_context"
            )
            logger.info("ContextService initialized with ContextManager")
        
        self.active = False
        self._background_task = None
        self._file_queue = asyncio.Queue()
        self._on_context_updated_callbacks = []
    
    async def start(self):
        """Start the context service."""
        if not self.context_manager:
            logger.warning("Cannot start ContextService without valid API key")
            return False
            
        if self.active:
            logger.warning("ContextService is already running")
            return True
            
        self.active = True
        self._background_task = asyncio.create_task(self._process_file_queue())
        logger.info("ContextService started")
        return True
    
    async def stop(self):
        """Stop the context service."""
        if not self.active:
            return
            
        self.active = False
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            self._background_task = None
        
        logger.info("ContextService stopped")
    
    def on_context_updated(self, callback: Callable):
        """Register a callback to be invoked when context is updated.
        
        Args:
            callback: Function to call when context is updated
        """
        self._on_context_updated_callbacks.append(callback)
    
    async def add_file_to_context(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """Add a file to the context database.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language of the file
            
        Returns:
            Result dictionary
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        result = await self.context_manager.add_file_to_context(
            file_path=file_path,
            content=content,
            language=language
        )
        
        if result["success"]:
            # Notify callbacks
            for callback in self._on_context_updated_callbacks:
                try:
                    callback(file_path, "add")
                except Exception as e:
                    logger.error(f"Error in context update callback: {str(e)}")
        
        return result
    
    async def queue_file_for_processing(self, file_path: str, content: str, language: str):
        """Queue a file to be added to the context in the background.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language of the file
        """
        await self._file_queue.put((file_path, content, language))
        logger.debug(f"Queued file for context processing: {file_path}")
    
    async def _process_file_queue(self):
        """Background task to process the file queue."""
        while self.active:
            try:
                if self._file_queue.empty():
                    await asyncio.sleep(1)
                    continue
                    
                file_path, content, language = await self._file_queue.get()
                logger.debug(f"Processing file from queue: {file_path}")
                
                await self.add_file_to_context(file_path, content, language)
                self._file_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing file queue: {str(e)}")
                await asyncio.sleep(5)  # Pause before retrying
    
    async def get_relevant_context(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Get code snippets relevant to the query.
        
        Args:
            query: The query text
            n_results: Maximum number of results to return
            
        Returns:
            Dictionary with relevant code snippets
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        return await self.context_manager.get_relevant_context(query, n_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the context database.
        
        Returns:
            Dictionary with statistics
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        return self.context_manager.get_stats()
    
    async def export_context(self, output_file: str) -> Dict[str, Any]:
        """Export the context database to a file.
        
        Args:
            output_file: Path to the output file
            
        Returns:
            Result dictionary
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        return self.context_manager.export_context(output_file)
    
    async def import_context(self, input_file: str, overwrite: bool = False) -> Dict[str, Any]:
        """Import context from a file.
        
        Args:
            input_file: Path to the input file
            overwrite: Whether to overwrite existing data
            
        Returns:
            Result dictionary
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        return self.context_manager.import_context(input_file, overwrite)
    
    async def clear_context(self) -> Dict[str, Any]:
        """Clear all context data.
        
        Returns:
            Result dictionary
        """
        if not self.context_manager:
            return {"success": False, "error": "ContextManager not initialized"}
            
        return self.context_manager.clear_context() 