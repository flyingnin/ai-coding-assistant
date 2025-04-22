"""
AI Notification Agent

This module contains the AI notification agent implementation for providing
context-aware AI notifications and recommendations.
"""

import os
import logging
import threading
import time
import json
from typing import Dict, List, Optional, Any, Tuple

from services.notification_service import NotificationService
from utils.openrouter import OpenRouterClient

# Configure logging
logger = logging.getLogger(__name__)

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
        
    def start(self):
        """Start the AI notification agent."""
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