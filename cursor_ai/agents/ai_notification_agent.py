import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Tuple
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to users."""
    
    def __init__(self):
        """Initialize the notification service."""
        logger.info("Notification service initialized")

    def send_notification(self, title: str, message: str, priority: int = 0) -> bool:
        """
        Send a notification to the user.

        Args:
            title: The title of the notification
            message: The content of the notification
            priority: The priority level (0-2, where 2 is highest)

        Returns:
            Whether the notification was sent successfully
        """
        try:
            logger.info(f"Sending notification: {title} (priority {priority})")
            # In a real implementation, this would send to the UI
            # For now, we just log it
            logger.info(f"NOTIFICATION - {title}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False

    def send_recommendation(self, recommendation: Dict[str, Any]) -> bool:
        """
        Send a recommendation notification to the user.

        Args:
            recommendation: Dictionary containing the recommendation information

        Returns:
            Whether the recommendation was sent successfully
        """
        try:
            title = recommendation.get("title", "AI Recommendation")
            description = recommendation.get("description", "No description provided")
            priority = recommendation.get("priority", 0)

            return self.send_notification(title, description, priority)
        except Exception as e:
            logger.error(f"Failed to send recommendation: {str(e)}")
            return False


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenRouter client."""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OpenRouter API key not provided")
        
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cursor",
            "X-Title": "Cursor AI Assistant"
        }
        
    def generate_response(self, messages: List[Dict[str, str]], model: str = "google/gemini-2.5-pro-preview-03-25", 
                          max_tokens: int = 500, temperature: float = 0.7) -> Tuple[bool, str]:
        """
        Generate a response from the OpenRouter API.
        
        Args:
            messages: List of message dictionaries with role and content
            model: Model to use for generation
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Tuple of (success, response_text)
        """
        if not self.api_key:
            logger.error("Cannot generate response: No API key provided")
            return False, "Cannot generate response: No API key provided"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            logger.info(f"Making request to OpenRouter with model: {model}")
            response = requests.post(self.url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return True, response_text
            else:
                error_message = f"OpenRouter API error: {response.status_code} - {response.text}"
                logger.error(error_message)
                return False, error_message
                
        except Exception as e:
            error_message = f"OpenRouter API request failed: {str(e)}"
            logger.error(error_message)
            return False, error_message


class AINotificationAgent:
    """Agent for generating context-aware AI notifications and recommendations."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "google/gemini-2.5-pro-preview-03-25"):
        """Initialize the AI notification agent."""
        self.notification_service = NotificationService()
        self.openrouter_client = OpenRouterClient(api_key)
        self.model = model
        
        logger.info(f"Initialized with model: {self.model}")
        
        # Context tracking
        self.context = {
            "active_file": None,
            "open_files": [],
            "errors": [],
            "last_recommendation_time": None,
            "recommendations_sent": []
        }
        
        # Thread for monitoring and sending recommendations
        self.monitor_thread = None
        self.running = False
        self.monitor_interval = 30  # seconds
        
        # Start monitoring
        self.start_monitoring()
        
    def start_monitoring(self):
        """Start the background monitoring thread."""
        if self.monitor_thread is not None and self.monitor_thread.is_alive():
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("AI notification agent monitoring started")
        
    def stop_monitoring(self):
        """Stop the background monitoring thread."""
        self.running = False
        if self.monitor_thread is not None:
            self.monitor_thread.join(timeout=1.0)
            logger.info("AI notification agent monitoring stopped")
            
    def _monitor_loop(self):
        """Background loop for monitoring and sending recommendations."""
        while self.running:
            try:
                # Check if it's time to send a recommendation
                self._check_recommendation_time()
                
                # Sleep for the monitor interval
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Shorter sleep on error
    
    def _check_recommendation_time(self):
        """Check if it's time to send a recommendation."""
        # If no recommendation time set, set it now
        if self.context["last_recommendation_time"] is None:
            self.context["last_recommendation_time"] = time.time()
            return
        
        # If it's been more than 10 minutes since last recommendation, send one
        if time.time() - self.context["last_recommendation_time"] > 600:
            self.generate_recommendation()
    
    def update_context(self, context_update: Dict[str, Any]):
        """
        Update the agent's context.
        
        Args:
            context_update: Dictionary with context updates
        """
        self.context.update(context_update)
        logger.debug(f"Context updated: {self.context}")
    
    def generate_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Generate a recommendation based on current context.
        
        Returns:
            Dictionary with the recommendation or None if no recommendation
        """
        try:
            # Prepare the context for the prompt
            context_str = json.dumps(self.context)
            
            # Create a system prompt for the recommendation
            system_message = {
                "role": "system",
                "content": """You are an intelligent assistant for the Cursor IDE. Your goal is to provide helpful, 
                concise recommendations to improve the developer's workflow based on their current context. 
                Recommendations should be brief, specific, and actionable. Focus on the most important issues 
                that would help the developer right now."""
            }
            
            # Create a user prompt with the context
            user_message = {
                "role": "user",
                "content": f"""Based on the developer's current context, provide a single, helpful recommendation:
                
                CONTEXT:
                {context_str}
                
                Your recommendation should be brief and include:
                1. A clear title (one short sentence)
                2. A concise explanation/description (1-3 sentences)
                3. A priority level (0-2, where 0=low, 1=medium, 2=high)
                
                Format your response as a JSON object with fields: title, description, priority"""
            }
            
            # Generate the recommendation
            success, response_text = self.openrouter_client.generate_response(
                messages=[system_message, user_message],
                model=self.model,
                max_tokens=250,
                temperature=0.7
            )
            
            if not success:
                logger.error(f"Failed to generate recommendation: {response_text}")
                return None
            
            # Try to parse the response as JSON
            try:
                recommendation = json.loads(response_text)
                
                # Validate the recommendation
                if "title" not in recommendation or "description" not in recommendation:
                    logger.warning(f"Invalid recommendation format: {recommendation}")
                    recommendation = {
                        "title": "AI Assistant Recommendation",
                        "description": response_text,
                        "priority": 0
                    }
                
                # Send the recommendation
                self.notification_service.send_recommendation(recommendation)
                
                # Update the last recommendation time
                self.context["last_recommendation_time"] = time.time()
                
                # Add to sent recommendations
                self.context["recommendations_sent"].append({
                    "time": time.time(),
                    "recommendation": recommendation
                })
                
                return recommendation
                
            except json.JSONDecodeError:
                # If not valid JSON, still try to use it
                logger.warning(f"Failed to parse response as JSON: {response_text}")
                recommendation = {
                    "title": "AI Assistant Recommendation",
                    "description": response_text,
                    "priority": 0
                }
                
                self.notification_service.send_recommendation(recommendation)
                self.context["last_recommendation_time"] = time.time()
                
                return recommendation
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return None 