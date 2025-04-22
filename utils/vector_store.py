"""
Vector Store Module

This module provides a vector database for storing and retrieving embeddings using ChromaDB.
"""

import os
import json
import logging
import chromadb
from typing import Dict, List, Any, Optional, Union
from chromadb.config import Settings
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store implementation using ChromaDB for storing and retrieving embeddings."""
    
    def __init__(
        self, 
        persistence_directory: str = "./vector_db",
        collection_name: str = "code_snippets",
        create_collection: bool = True
    ):
        """Initialize the vector store.
        
        Args:
            persistence_directory: Directory where ChromaDB will store data.
            collection_name: Name of the collection to use.
            create_collection: Whether to create the collection if it doesn't exist.
        """
        try:
            # Ensure directory exists
            os.makedirs(persistence_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=persistence_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            if create_collection:
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Code snippets for AI assistant"}
                )
                logger.info(f"Initialized vector store with collection '{collection_name}'")
            else:
                try:
                    self.collection = self.client.get_collection(name=collection_name)
                    logger.info(f"Using existing collection '{collection_name}'")
                except ValueError:
                    logger.error(f"Collection '{collection_name}' does not exist and create_collection=False")
                    raise
                    
            self.collection_name = collection_name
            self.persistence_directory = persistence_directory
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    def add_embedding(
        self,
        id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        content: str
    ) -> bool:
        """Add an embedding to the vector store.
        
        Args:
            id: Unique identifier for the embedding.
            embedding: The embedding vector.
            metadata: Metadata associated with the embedding.
            content: The original content that was embedded.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Add timestamp to metadata
            metadata["timestamp"] = datetime.now().isoformat()
            
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[id]
            )
            logger.debug(f"Added embedding with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add embedding: {str(e)}")
            return False
    
    def add_embeddings_batch(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        contents: List[str]
    ) -> bool:
        """Add multiple embeddings to the vector store in a batch operation.
        
        Args:
            ids: List of unique identifiers.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dictionaries.
            contents: List of original contents.
            
        Returns:
            True if successful, False otherwise.
        """
        if not (len(ids) == len(embeddings) == len(metadatas) == len(contents)):
            logger.error("All input lists must have the same length")
            return False
            
        try:
            # Add timestamp to all metadata
            timestamp = datetime.now().isoformat()
            for metadata in metadatas:
                metadata["timestamp"] = timestamp
                
            self.collection.add(
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas,
                ids=ids
            )
            logger.debug(f"Added {len(ids)} embeddings in batch")
            return True
        except Exception as e:
            logger.error(f"Failed to add embeddings in batch: {str(e)}")
            return False
    
    def query_similar(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for similar embeddings.
        
        Args:
            query_embedding: The embedding to find similar embeddings for.
            n_results: Maximum number of results to return.
            filter_dict: Dictionary of metadata filters.
            
        Returns:
            Dictionary with query results.
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict
            )
            
            return {
                "success": True,
                "data": results
            }
        except Exception as e:
            logger.error(f"Failed to query similar embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_by_id(self, id: str) -> Dict[str, Any]:
        """Get an embedding by its ID.
        
        Args:
            id: The ID of the embedding to retrieve.
            
        Returns:
            Dictionary with the embedding data.
        """
        try:
            result = self.collection.get(
                ids=[id],
                include=["embeddings", "metadatas", "documents"]
            )
            
            if result["ids"] and len(result["ids"]) > 0:
                return {
                    "success": True,
                    "data": {
                        "id": result["ids"][0],
                        "embedding": result["embeddings"][0] if "embeddings" in result else None,
                        "metadata": result["metadatas"][0] if "metadatas" in result else None,
                        "content": result["documents"][0] if "documents" in result else None
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"No embedding found with ID: {id}"
                }
        except Exception as e:
            logger.error(f"Failed to get embedding by ID: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_by_id(self, id: str) -> bool:
        """Delete an embedding by its ID.
        
        Args:
            id: The ID of the embedding to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.collection.delete(ids=[id])
            logger.debug(f"Deleted embedding with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete embedding: {str(e)}")
            return False
    
    def update_embedding(
        self,
        id: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> bool:
        """Update an existing embedding.
        
        Args:
            id: The ID of the embedding to update.
            embedding: New embedding vector (optional).
            metadata: New metadata (optional).
            content: New content (optional).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get current embedding data
            current = self.get_by_id(id)
            if not current["success"]:
                return False
                
            # Update only provided fields
            update_embedding = embedding if embedding is not None else current["data"].get("embedding")
            update_content = content if content is not None else current["data"].get("content")
            
            # For metadata, merge rather than replace
            update_metadata = current["data"].get("metadata", {}).copy()
            if metadata:
                update_metadata.update(metadata)
                
            # Add updated timestamp
            update_metadata["updated_at"] = datetime.now().isoformat()
            
            # Delete existing and add updated version
            if not self.delete_by_id(id):
                return False
                
            return self.add_embedding(
                id=id,
                embedding=update_embedding,
                metadata=update_metadata,
                content=update_content
            )
        except Exception as e:
            logger.error(f"Failed to update embedding: {str(e)}")
            return False
    
    def count(self) -> int:
        """Get the number of embeddings in the collection.
        
        Returns:
            Number of embeddings.
        """
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get count: {str(e)}")
            return -1
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection.
        
        Returns:
            Dictionary with collection information.
        """
        try:
            count = self.collection.count()
            return {
                "success": True,
                "data": {
                    "name": self.collection_name,
                    "count": count,
                    "metadata": self.collection.metadata
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_collection(self) -> bool:
        """Clear all embeddings from the collection.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.collection.delete(where={})
            logger.info(f"Cleared all embeddings from collection '{self.collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            return False
    
    def export_to_json(self, output_file: str) -> Dict[str, Any]:
        """Export all embeddings to a JSON file.
        
        Args:
            output_file: Path to the output JSON file.
            
        Returns:
            Dictionary with export status and information.
        """
        try:
            # Get all embeddings
            all_data = self.collection.get(
                include=["embeddings", "metadatas", "documents"]
            )
            
            # Transform to a more convenient format
            export_data = []
            for i, id in enumerate(all_data["ids"]):
                item = {
                    "id": id,
                    "content": all_data["documents"][i] if "documents" in all_data else None,
                    "metadata": all_data["metadatas"][i] if "metadatas" in all_data else None,
                    "embedding": all_data["embeddings"][i] if "embeddings" in all_data else None
                }
                export_data.append(item)
                
            # Export to JSON
            with open(output_file, 'w') as f:
                json.dump({
                    "collection": self.collection_name,
                    "count": len(export_data),
                    "timestamp": datetime.now().isoformat(),
                    "data": export_data
                }, f, indent=2)
                
            logger.info(f"Exported {len(export_data)} embeddings to {output_file}")
            return {
                "success": True,
                "data": {
                    "file": output_file,
                    "count": len(export_data)
                }
            }
        except Exception as e:
            logger.error(f"Failed to export embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def import_from_json(self, input_file: str, overwrite: bool = False) -> Dict[str, Any]:
        """Import embeddings from a JSON file.
        
        Args:
            input_file: Path to the input JSON file.
            overwrite: Whether to clear the collection before importing.
            
        Returns:
            Dictionary with import status and information.
        """
        try:
            # Read JSON file
            with open(input_file, 'r') as f:
                import_data = json.load(f)
                
            # Check if the collection matches
            if import_data.get("collection") != self.collection_name:
                logger.warning(f"Importing data from collection '{import_data.get('collection')}' to '{self.collection_name}'")
                
            # Clear collection if overwrite is True
            if overwrite:
                self.clear_collection()
                
            # Prepare data for import
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for item in import_data.get("data", []):
                # Skip items that don't have all required fields
                if not all(k in item for k in ["id", "embedding", "content"]):
                    logger.warning(f"Skipping item with ID {item.get('id')} because it's missing required fields")
                    continue
                    
                ids.append(item["id"])
                embeddings.append(item["embedding"])
                metadatas.append(item.get("metadata", {}))
                documents.append(item["content"])
                
            # Import data
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Imported {len(ids)} embeddings from {input_file}")
            return {
                "success": True,
                "data": {
                    "file": input_file,
                    "count": len(ids)
                }
            }
        except Exception as e:
            logger.error(f"Failed to import embeddings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_client(self):
        """Get the underlying ChromaDB client.
        
        Returns:
            The ChromaDB client instance.
        """
        return self.client
        
    def get_collection(self):
        """Get the underlying ChromaDB collection.
        
        Returns:
            The ChromaDB collection instance.
        """
        return self.collection 