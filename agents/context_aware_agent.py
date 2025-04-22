"""
Context-Aware AI Agent

This agent enhances the AI assistant's capabilities by providing relevant code context
from the user's codebase when responding to queries.
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

from services.context_service import ContextService
from utils.openrouter import OpenRouterClient

# Configure logging
logger = logging.getLogger(__name__)

class ContextAwareAgent:
    """AI agent that provides context-aware assistance by utilizing code context."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        ai_model: str = "openai/gpt-4",
        context_window_size: int = 5,
        max_context_tokens: int = 4000
    ):
        """Initialize the context-aware agent.
        
        Args:
            api_key: The OpenRouter API key. If None, will load from environment.
            ai_model: The AI model to use for generating responses.
            context_window_size: Number of relevant context items to include.
            max_context_tokens: Maximum number of tokens to use for context.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.error("No API key provided for ContextAwareAgent")
            raise ValueError("API key is required for ContextAwareAgent")
            
        self.ai_model = ai_model
        self.context_window_size = context_window_size
        self.max_context_tokens = max_context_tokens
        
        # Initialize services
        self.openrouter_client = OpenRouterClient(api_key=self.api_key)
        self.context_service = ContextService(api_key=self.api_key)
        
        # Start context service
        self._context_service_started = False
        logger.info(f"ContextAwareAgent initialized with model {ai_model}")
    
    async def start(self):
        """Start the agent and its dependent services."""
        if not self._context_service_started:
            await self.context_service.start()
            self._context_service_started = True
            logger.info("ContextAwareAgent started")
    
    async def stop(self):
        """Stop the agent and its dependent services."""
        if self._context_service_started:
            await self.context_service.stop()
            self._context_service_started = False
            logger.info("ContextAwareAgent stopped")
    
    async def _get_relevant_context(self, query: str) -> str:
        """Get relevant code context for the query.
        
        Args:
            query: The user's query
            
        Returns:
            Formatted context string to include in the prompt
        """
        context_result = await self.context_service.get_relevant_context(
            query=query,
            n_results=self.context_window_size
        )
        
        if not context_result["success"]:
            logger.warning(f"Failed to get context: {context_result.get('error', 'Unknown error')}")
            return ""
            
        # Format context for inclusion in prompt
        context_str = "RELEVANT CODE CONTEXT:\n\n"
        
        for idx, (doc, metadata) in enumerate(zip(
            context_result["data"]["documents"][0],
            context_result["data"]["metadatas"][0]
        )):
            file_path = metadata.get("file_path", "unknown_file")
            language = metadata.get("language", "unknown")
            
            context_str += f"[{idx+1}] File: {file_path}\n"
            context_str += f"Language: {language}\n"
            context_str += f"```{language}\n{doc}\n```\n\n"
            
        return context_str
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create the prompt for the AI model.
        
        Args:
            query: The user's query
            context: The relevant code context
            
        Returns:
            Formatted prompt for the AI model
        """
        system_message = (
            "You are a context-aware AI assistant for developers. "
            "You have access to relevant parts of the user's codebase to provide better assistance. "
            "When answering questions, use the provided code context to inform your response. "
            "If the context doesn't contain enough information, acknowledge this and provide the best answer you can. "
            "Always prioritize code quality, readability, and best practices in your suggestions."
        )
        
        if context:
            prompt = f"{system_message}\n\n{context}\n\nUSER QUERY: {query}\n\n"
        else:
            prompt = f"{system_message}\n\nUSER QUERY: {query}\n\n"
            
        return prompt
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query with context-aware AI assistance.
        
        Args:
            query: The user's query
            
        Returns:
            Response dictionary with AI-generated answer
        """
        try:
            # Ensure services are started
            if not self._context_service_started:
                await self.start()
                
            # Get relevant context for the query
            context = await self._get_relevant_context(query)
            
            # Create prompt with context
            prompt = self._create_prompt(query, context)
            
            # Get response from AI model
            response = await self.openrouter_client.generate_chat_completion(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are a context-aware AI assistant for developers."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response["success"]:
                return {
                    "success": False,
                    "error": f"Failed to generate response: {response.get('error', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "data": {
                    "response": response["data"]["choices"][0]["message"]["content"],
                    "had_context": bool(context),
                    "context_count": context.count("File:") if context else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_current_file_to_context(self, file_path: str, content: str, language: str) -> Dict[str, Any]:
        """Add the current file being worked on to the context database.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            language: Programming language of the file
            
        Returns:
            Result dictionary
        """
        # Queue the file for background processing
        await self.context_service.queue_file_for_processing(file_path, content, language)
        
        return {
            "success": True,
            "message": f"File {file_path} queued for context processing"
        }
    
    async def add_context_from_text(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add text content to the context database.
        
        Args:
            content: The content to add
            metadata: Optional metadata for the content
            
        Returns:
            Result dictionary
        """
        try:
            if not self._context_service_started:
                await self.start()
                
            result = await self.context_service.add_text_to_context(content, metadata)
            return result
        except Exception as e:
            logger.error(f"Error adding context from text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the context database.
        
        Returns:
            Dictionary with statistics
        """
        if not self._context_service_started:
            await self.start()
            
        return self.context_service.get_stats() 