"""
Context Manager Module

This module provides a context manager for handling code context,
generating embeddings, and storing/retrieving relevant context using vector search.
"""

import os
import uuid
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from utils.openrouter import OpenRouterClient
from utils.vector_store import VectorStore

# Configure logging
logger = logging.getLogger(__name__)

class ContextManager:
    """Context manager for handling code snippets and their embeddings."""
    
    def __init__(
        self,
        openrouter_api_key: str,
        embedding_model: str = "openai/text-embedding-ada-002",
        vector_db_path: str = "./vector_db",
        collection_name: str = "code_context",
        context_window_size: int = 1000
    ):
        """Initialize the context manager.
        
        Args:
            openrouter_api_key: API key for OpenRouter.
            embedding_model: Model to use for generating embeddings.
            vector_db_path: Path to store vector database.
            collection_name: Name of the collection in the vector store.
            context_window_size: Size of context window in tokens.
        """
        try:
            # Initialize OpenRouter client for embeddings
            self.embeddings_client = OpenRouterClient(api_key=openrouter_api_key)
            self.embedding_model = embedding_model
            
            # Initialize vector store
            self.vector_store = VectorStore(
                persistence_directory=vector_db_path,
                collection_name=collection_name
            )
            
            self.context_window_size = context_window_size
            logger.info(f"Context manager initialized with embedding model {embedding_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize context manager: {str(e)}")
            raise
    
    async def add_code_snippet(
        self,
        code: str,
        file_path: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None,
        snippet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a code snippet to the context manager.
        
        Args:
            code: The code snippet text.
            file_path: Path to the file containing the code.
            language: Programming language of the code.
            metadata: Additional metadata for the snippet.
            snippet_id: Optional ID for the snippet. If None, a UUID will be generated.
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Generate a unique ID if not provided
            if snippet_id is None:
                snippet_id = str(uuid.uuid4())
                
            # Prepare metadata
            snippet_metadata = {
                "file_path": file_path,
                "language": language,
                "added_at": datetime.now().isoformat(),
                "token_count": len(code.split())  # Simple tokenization
            }
            
            # Add custom metadata if provided
            if metadata:
                snippet_metadata.update(metadata)
                
            # Generate embedding for the code snippet
            embedding_result = await self.embeddings_client.generate_embeddings(
                text=code,
                model=self.embedding_model
            )
            
            if not embedding_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to generate embedding: {embedding_result.get('error', 'Unknown error')}"
                }
                
            # Add the snippet to the vector store
            embedding = embedding_result["data"]["embedding"]
            add_result = self.vector_store.add_embedding(
                id=snippet_id,
                embedding=embedding,
                metadata=snippet_metadata,
                content=code
            )
            
            if not add_result:
                return {
                    "success": False,
                    "error": "Failed to add snippet to vector store"
                }
                
            return {
                "success": True,
                "data": {
                    "id": snippet_id,
                    "metadata": snippet_metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding code snippet: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_code_snippets_batch(
        self,
        snippets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Add multiple code snippets in a batch.
        
        Args:
            snippets: List of dictionaries with code snippets and metadata.
                Each dictionary should have: code, file_path, language, and optional metadata.
                
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            codes = []
            file_paths = []
            languages = []
            metadatas = []
            snippet_ids = []
            
            # Process each snippet
            for snippet in snippets:
                if not all(k in snippet for k in ["code", "file_path", "language"]):
                    return {
                        "success": False,
                        "error": "Each snippet must have code, file_path, and language"
                    }
                
                codes.append(snippet["code"])
                file_paths.append(snippet["file_path"])
                languages.append(snippet["language"])
                
                # Generate ID if not provided
                snippet_id = snippet.get("id", str(uuid.uuid4()))
                snippet_ids.append(snippet_id)
                
                # Prepare metadata
                snippet_metadata = {
                    "file_path": snippet["file_path"],
                    "language": snippet["language"],
                    "added_at": datetime.now().isoformat(),
                    "token_count": len(snippet["code"].split())
                }
                
                # Add custom metadata if provided
                if "metadata" in snippet and snippet["metadata"]:
                    snippet_metadata.update(snippet["metadata"])
                    
                metadatas.append(snippet_metadata)
            
            # Generate embeddings in batch
            embedding_results = await self.embeddings_client.generate_batch_embeddings(
                texts=codes,
                model=self.embedding_model
            )
            
            if not embedding_results["success"]:
                return {
                    "success": False,
                    "error": f"Failed to generate batch embeddings: {embedding_results.get('error', 'Unknown error')}"
                }
                
            # Add to vector store
            embeddings = embedding_results["data"]
            add_result = self.vector_store.add_embeddings_batch(
                ids=snippet_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                contents=codes
            )
            
            if not add_result:
                return {
                    "success": False,
                    "error": "Failed to add snippets to vector store"
                }
                
            return {
                "success": True,
                "data": {
                    "count": len(snippet_ids),
                    "ids": snippet_ids
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding code snippets batch: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_relevant_context(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve relevant code context based on a query.
        
        Args:
            query: Query text to find relevant context.
            n_results: Maximum number of results to return.
            filter_dict: Optional filters for the search (language, file_path, etc.)
            
        Returns:
            Dictionary with search results.
        """
        try:
            # Generate embedding for the query
            embedding_result = await self.embeddings_client.generate_embeddings(
                text=query,
                model=self.embedding_model
            )
            
            if not embedding_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to generate query embedding: {embedding_result.get('error', 'Unknown error')}"
                }
                
            # Search for relevant context
            query_embedding = embedding_result["data"]["embedding"]
            search_results = self.vector_store.query_similar(
                query_embedding=query_embedding,
                n_results=n_results,
                filter_dict=filter_dict
            )
            
            if not search_results["success"]:
                return {
                    "success": False,
                    "error": f"Failed to search for context: {search_results.get('error', 'Unknown error')}"
                }
                
            # Format results
            results = search_results["data"]
            formatted_results = []
            
            for i, snippet_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "id": snippet_id,
                    "code": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1.0 - results["distances"][0][i]  # Convert distance to similarity
                })
                
            return {
                "success": True,
                "data": {
                    "results": formatted_results,
                    "count": len(formatted_results)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_code_snippet(
        self,
        snippet_id: str,
        code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing code snippet.
        
        Args:
            snippet_id: ID of the snippet to update.
            code: New code snippet (if None, only metadata is updated).
            metadata: New metadata (if None, only code is updated).
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Get current snippet
            snippet = self.vector_store.get_by_id(snippet_id)
            
            if not snippet["success"]:
                return {
                    "success": False,
                    "error": f"Snippet not found: {snippet_id}"
                }
                
            # Update the metadata
            updated_metadata = None
            if metadata:
                updated_metadata = snippet["data"]["metadata"].copy()
                updated_metadata.update(metadata)
                updated_metadata["updated_at"] = datetime.now().isoformat()
                
            # Generate new embedding if code is updated
            updated_embedding = None
            if code:
                embedding_result = await self.embeddings_client.generate_embeddings(
                    text=code,
                    model=self.embedding_model
                )
                
                if not embedding_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to generate embedding: {embedding_result.get('error', 'Unknown error')}"
                    }
                    
                updated_embedding = embedding_result["data"]["embedding"]
                
                # Update token count in metadata
                if updated_metadata is None:
                    updated_metadata = snippet["data"]["metadata"].copy()
                updated_metadata["token_count"] = len(code.split())
                updated_metadata["updated_at"] = datetime.now().isoformat()
                
            # Update in vector store
            update_result = self.vector_store.update_embedding(
                id=snippet_id,
                embedding=updated_embedding,
                metadata=updated_metadata,
                content=code
            )
            
            if not update_result:
                return {
                    "success": False,
                    "error": "Failed to update snippet"
                }
                
            return {
                "success": True,
                "data": {
                    "id": snippet_id,
                    "metadata": updated_metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Error updating code snippet: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_code_snippet(self, snippet_id: str) -> Dict[str, Any]:
        """Delete a code snippet.
        
        Args:
            snippet_id: ID of the snippet to delete.
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Check if snippet exists
            snippet = self.vector_store.get_by_id(snippet_id)
            
            if not snippet["success"]:
                return {
                    "success": False,
                    "error": f"Snippet not found: {snippet_id}"
                }
                
            # Delete from vector store
            delete_result = self.vector_store.delete_by_id(snippet_id)
            
            if not delete_result:
                return {
                    "success": False,
                    "error": "Failed to delete snippet"
                }
                
            return {
                "success": True,
                "data": {
                    "id": snippet_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error deleting code snippet: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_snippet_by_id(self, snippet_id: str) -> Dict[str, Any]:
        """Get a specific code snippet by ID.
        
        Args:
            snippet_id: ID of the snippet to retrieve.
            
        Returns:
            Dictionary with the snippet data.
        """
        try:
            return self.vector_store.get_by_id(snippet_id)
        except Exception as e:
            logger.error(f"Error getting snippet by ID: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the context manager.
        
        Returns:
            Dictionary with statistics.
        """
        try:
            collection_info = self.vector_store.get_collection_info()
            
            if not collection_info["success"]:
                return {
                    "success": False,
                    "error": f"Failed to get collection info: {collection_info.get('error', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "data": {
                    "total_snippets": collection_info["data"]["count"],
                    "collection_name": collection_info["data"]["name"],
                    "embedding_model": self.embedding_model,
                    "context_window_size": self.context_window_size
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting context manager stats: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_context(self, output_file: str) -> Dict[str, Any]:
        """Export all context data to a file.
        
        Args:
            output_file: Path to output file.
            
        Returns:
            Dictionary with export result.
        """
        try:
            return self.vector_store.export_to_json(output_file)
        except Exception as e:
            logger.error(f"Error exporting context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_context(self, input_file: str, overwrite: bool = False) -> Dict[str, Any]:
        """Import context data from a file.
        
        Args:
            input_file: Path to input file.
            overwrite: Whether to clear existing data.
            
        Returns:
            Dictionary with import result.
        """
        try:
            return self.vector_store.import_from_json(input_file, overwrite)
        except Exception as e:
            logger.error(f"Error importing context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_context(self) -> Dict[str, Any]:
        """Clear all context data.
        
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            clear_result = self.vector_store.clear_collection()
            
            if not clear_result:
                return {
                    "success": False,
                    "error": "Failed to clear context"
                }
                
            return {
                "success": True,
                "data": {
                    "message": "Context cleared successfully"
                }
            }
            
        except Exception as e:
            logger.error(f"Error clearing context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def refresh_embeddings(
        self,
        new_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Refresh all embeddings, optionally with a new model.
        
        Args:
            new_model: New embedding model to use. If None, use the current model.
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Get all snippets
            collection_info = self.vector_store.get_collection_info()
            if not collection_info["success"]:
                return {
                    "success": False,
                    "error": f"Failed to get collection info: {collection_info.get('error', 'Unknown error')}"
                }
                
            total_snippets = collection_info["data"]["count"]
            if total_snippets == 0:
                return {
                    "success": True,
                    "data": {
                        "message": "No snippets to refresh",
                        "count": 0
                    }
                }
                
            # Export to temporary file
            temp_file = f"temp_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            export_result = self.export_context(temp_file)
            
            if not export_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to export context: {export_result.get('error', 'Unknown error')}"
                }
                
            # Read exported data
            with open(temp_file, 'r') as f:
                data = json.load(f)
                
            snippets = data.get("data", [])
            
            # Update model if specified
            if new_model:
                self.embedding_model = new_model
                
            # Regenerate embeddings for each snippet
            updated_count = 0
            for snippet in snippets:
                embedding_result = await self.embeddings_client.generate_embeddings(
                    text=snippet["content"],
                    model=self.embedding_model
                )
                
                if not embedding_result["success"]:
                    continue
                    
                # Update the snippet with new embedding
                snippet["embedding"] = embedding_result["data"]["embedding"]
                
                # Update metadata
                if "metadata" not in snippet:
                    snippet["metadata"] = {}
                snippet["metadata"]["embedding_model"] = self.embedding_model
                snippet["metadata"]["refreshed_at"] = datetime.now().isoformat()
                
                updated_count += 1
                
            # Write updated data back to file
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            # Clear and reimport
            self.clear_context()
            import_result = self.import_context(temp_file, overwrite=True)
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
                
            if not import_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to reimport context: {import_result.get('error', 'Unknown error')}"
                }
                
            return {
                "success": True,
                "data": {
                    "message": "Embeddings refreshed successfully",
                    "count": updated_count,
                    "model": self.embedding_model
                }
            }
            
        except Exception as e:
            logger.error(f"Error refreshing embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_file_to_context(
        self,
        file_path: str,
        content: str,
        language: str,
        chunk_size: int = 1000,
        overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add an entire file to the context by chunking it.
        
        Args:
            file_path: Path to the file.
            content: Content of the file.
            language: Programming language of the file.
            chunk_size: Size of each chunk in characters.
            overlap: Overlap between chunks in characters.
            metadata: Additional metadata for the file.
            
        Returns:
            Dictionary with the result of the operation.
        """
        try:
            # Basic chunking by characters
            chunks = []
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if len(chunk) < 50:  # Skip very small chunks
                    continue
                chunks.append(chunk)
                
            if not chunks:
                return {
                    "success": False,
                    "error": "File too small to chunk"
                }
                
            # Prepare metadata
            base_metadata = {
                "file_path": file_path,
                "language": language,
                "source": "file_import",
                "total_chunks": len(chunks)
            }
            
            if metadata:
                base_metadata.update(metadata)
                
            # Add chunks as snippets
            snippet_ids = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["chunk_total"] = len(chunks)
                
                result = await self.add_code_snippet(
                    code=chunk,
                    file_path=file_path,
                    language=language,
                    metadata=chunk_metadata
                )
                
                if result["success"]:
                    snippet_ids.append(result["data"]["id"])
                    
            return {
                "success": True,
                "data": {
                    "file_path": file_path,
                    "chunks": len(chunks),
                    "snippet_ids": snippet_ids
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding file to context: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 