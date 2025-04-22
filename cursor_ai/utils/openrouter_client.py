import os
import requests
from typing import Dict, Any, Optional, List

class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1"
    
    def __init__(self, api_key=None, model="google/gemini-2.5-pro-exp-03-25:free", max_tokens=1024):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("No OpenRouter API key provided or found in environment variables")
        
        self.model = model
        self.max_tokens = max_tokens
    
    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cursor.sh",
            "X-Title": "Cursor AI Assistant"
        }
    
    def chat_completion(self, messages, temperature=0.7, max_tokens=None):
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens
        }
        
        try:
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error in OpenRouter API request: {str(e)}")
            raise
    
    def generate_completion(self, prompt, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)
        
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Error parsing OpenRouter API response: {str(e)}")
            return ""
