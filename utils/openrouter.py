"""
OpenRouter Client

This module provides a client for the OpenRouter API, focusing on generating embeddings
for code snippets and text using various AI models.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class OpenRouterClient:
    """Client for interacting with OpenRouter API with a focus on embeddings."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://openrouter.ai/api/v1"):
        """Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from environment.
            base_url: Base URL for the OpenRouter API.
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("No OpenRouter API key provided. Set OPENROUTER_API_KEY env variable or pass it directly.")
            
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-assistant", # Replace with your actual site
            "X-Title": "AI Assistant"
        })
        
        logger.info("OpenRouter client initialized")
        
    def generate_embeddings(self, 
                          text: str, 
                          model: str = "openai/text-embedding-3-small") -> Dict[str, Any]:
        """Generate embeddings for the given text.
        
        Args:
            text: The text to generate embeddings for.
            model: The model to use for generating embeddings.
            
        Returns:
            Dictionary with the embedding results, including success status.
        """
        if not self.api_key:
            logger.error("Cannot generate embeddings: No API key available")
            return {
                "success": False,
                "error": "No API key available"
            }
            
        try:
            url = f"{self.base_url}/embeddings"
            payload = {
                "model": model,
                "input": text
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract embedding from response
            if "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]:
                embedding = data["data"][0]["embedding"]
                logger.debug(f"Generated embedding with dimension {len(embedding)}")
                return {
                    "success": True,
                    "data": {
                        "embedding": embedding,
                        "model": model,
                        "usage": data.get("usage", {}),
                    }
                }
            else:
                logger.error(f"Invalid response format: {data}")
                return {
                    "success": False,
                    "error": "Invalid response format from OpenRouter",
                    "raw_response": data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def generate_batch_embeddings(self, 
                               texts: List[str], 
                               model: str = "openai/text-embedding-3-small") -> Dict[str, Any]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for.
            model: The model to use for generating embeddings.
            
        Returns:
            Dictionary with the embeddings results, including success status.
        """
        if not self.api_key:
            logger.error("Cannot generate embeddings: No API key available")
            return {
                "success": False,
                "error": "No API key available"
            }
            
        try:
            url = f"{self.base_url}/embeddings"
            payload = {
                "model": model,
                "input": texts
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract embeddings from response
            if "data" in data and len(data["data"]) > 0:
                embeddings = [item.get("embedding") for item in data.get("data", [])]
                logger.debug(f"Generated {len(embeddings)} embeddings")
                return {
                    "success": True,
                    "data": {
                        "embeddings": embeddings,
                        "model": model,
                        "usage": data.get("usage", {})
                    }
                }
            else:
                logger.error(f"Invalid response format: {data}")
                return {
                    "success": False,
                    "error": "Invalid response format from OpenRouter",
                    "raw_response": data
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def get_available_embedding_models(self) -> Dict[str, Any]:
        """Get a list of available embedding models from OpenRouter.
        
        Returns:
            Dictionary with the available models, including success status.
        """
        if not self.api_key:
            logger.error("Cannot get models: No API key available")
            return {
                "success": False,
                "error": "No API key available"
            }
            
        try:
            url = f"{self.base_url}/models"
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Filter for embedding models only
            embedding_models = [
                model for model in data.get("data", [])
                if model.get("capabilities", {}).get("embeddings", False)
            ]
            
            return {
                "success": True,
                "data": {
                    "models": embedding_models
                }
            }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            } 