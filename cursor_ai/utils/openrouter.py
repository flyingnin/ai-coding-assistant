import requests
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class OpenRouter:
    """
    A class to interact with OpenRouter API, designed to be a drop-in replacement
    for LangChain's ChatOpenAI class.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "mistralai/mistral-7b-instruct:free", 
        base_url: str = "https://openrouter.ai/api/v1",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (defaults to mistralai/mistral-7b-instruct:free which is free)
            base_url: Base URL for the OpenRouter API
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Log initial setup
        logger.info(f"Initializing OpenRouter with model: {model}")
        if not api_key or len(api_key) < 10 or api_key.startswith("your_"):
            logger.warning("Invalid API key format detected")
        
    def _build_headers(self) -> Dict[str, str]:
        """Build the headers for the API request."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://cursor.ai",  # Identify your application
            "X-Title": "Cursor AI Assistant"  # Identify your application
        }
        
    def _build_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Build the payload for the API request."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        # Handle special cases for different model providers
        if "phind" in self.model.lower() and "codellama" in self.model.lower():
            logger.info(f"Using specialized settings for Phind CodeLlama model")
            # Phind models may benefit from different parameters
            payload["top_p"] = 0.95  # Add top_p parameter
        
        # Optimize for Gemini models
        elif "gemini" in self.model.lower():
            logger.info(f"Using specialized settings for Gemini model")
            # Gemini models work well with these parameters
            payload["top_k"] = 40
            payload["top_p"] = 0.9
            
            # For coding tasks, use a more deterministic configuration
            if "pro" in self.model.lower() and self.temperature <= 0.3:
                payload["top_p"] = 0.5  # More focused output for coding
                
        return payload
        
    def invoke(self, prompt: Any) -> Any:
        """
        Invoke the OpenRouter API with a ChatPromptTemplate.
        Compatible with LangChain's ChatOpenAI API.
        
        Args:
            prompt: A LangChain ChatPromptTemplate formatted message
            
        Returns:
            A response object with a content attribute
        """
        # Convert LangChain prompt to OpenRouter messages format
        messages = self._format_messages(prompt)
        
        # Make the API request
        try:
            url = f"{self.base_url}/chat/completions"
            headers = self._build_headers()
            payload = self._build_payload(messages)
            
            logger.debug(f"Sending request to OpenRouter API with model {self.model}")
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            
            # Check for specific error cases
            if response.status_code == 401:
                logger.error("Authentication error: Invalid API key")
                raise Exception("Authentication error: Invalid API key")
            elif response.status_code == 404:
                logger.error(f"Model not found: {self.model}")
                raise Exception(f"Model not found: {self.model}")
                
            response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            logger.debug("Successfully received response from OpenRouter API")
            
            # Create a response object similar to LangChain's
            class OpenRouterResponse:
                def __init__(self, content: str):
                    self.content = content
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                # Extract the generated content
                content = response_data["choices"][0]["message"]["content"]
                return OpenRouterResponse(content)
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return OpenRouterResponse("Error: Unexpected response format")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            raise Exception(f"Error calling OpenRouter API: {e}")
            
    def _format_messages(self, prompt: Any) -> List[Dict[str, str]]:
        """Convert various prompt formats to OpenRouter messages format."""
        if hasattr(prompt, "messages") and callable(prompt.messages):
            # Handle LangChain prompt templates
            formatted_messages = prompt.messages()
            messages = []
            
            for msg in formatted_messages:
                if hasattr(msg, "content") and hasattr(msg, "type"):
                    role = "system" if msg.type == "system" else ("assistant" if msg.type == "ai" else "user")
                    messages.append({"role": role, "content": msg.content})
                elif isinstance(msg, dict) and "content" in msg:
                    role = msg.get("role", "user")
                    messages.append({"role": role, "content": msg["content"]})
            
        elif isinstance(prompt, str):
            # Handle simple string prompts
            messages = [{"role": "user", "content": prompt}]
        else:
            # Try best effort to extract content
            content = str(prompt)
            messages = [{"role": "user", "content": content}]
            
        return messages
            
    def __call__(self, *args, **kwargs):
        """Make the class callable for compatibility with LangChain."""
        return self.invoke(*args, **kwargs)
        
    def get_available_models(self):
        """Get list of available models from OpenRouter API."""
        try:
            url = f"{self.base_url}/models"
            headers = self._build_headers()
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            model_data = response.json()
            if "data" in model_data:
                return [model["id"] for model in model_data["data"]]
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return [] 