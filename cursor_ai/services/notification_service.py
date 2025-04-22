import requests
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class NotificationService:
    """Notification service to send alerts to user's devices."""
    
    def __init__(self):
        # Initialize notification services
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.last_active_time = datetime.now()
        self.active = True
        
        # Check if pushover credentials are set
        if not self.pushover_token or not self.pushover_user:
            logger.warning("Pushover credentials not set. Notifications will be logged only.")
            self.notification_enabled = False
        else:
            self.notification_enabled = True
            
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_active_time = datetime.now()
        self.active = True
        
    def check_inactivity(self, timeout_minutes=3):
        """Check if the system has been inactive beyond the threshold."""
        if not self.active:
            return False
            
        current_time = datetime.now()
        elapsed = (current_time - self.last_active_time).total_seconds() / 60
        
        if elapsed > timeout_minutes:
            self.send_notification(
                title="Cursor Inactivity Alert", 
                message=f"Your Cursor assistant has been inactive for {timeout_minutes} minutes."
            )
            self.active = False
            return True
        return False
    
    def send_notification(self, title, message, priority=0):
        """Send a notification via Pushover and log it."""
        logger.info(f"NOTIFICATION: {title} - {message}")
        
        if not self.notification_enabled:
            return True
            
        try:
            # Send via Pushover
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": self.pushover_token,
                    "user": self.pushover_user,
                    "title": title,
                    "message": message,
                    "priority": priority
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Notification sent successfully: {title}")
                return True
            else:
                logger.error(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    def notify_changes_accepted(self, file_path):
        """Notify that changes to a file were automatically accepted."""
        self.send_notification(
            title="Changes Accepted", 
            message=f"Automatically accepted changes to: {os.path.basename(file_path)}"
        )
    
    def notify_cursor_error(self, error_message):
        """Notify about errors in Cursor."""
        self.send_notification(
            title="Cursor Error Alert", 
            message=f"Cursor encountered an error: {error_message}",
            priority=1
        )
        self.active = False

    def send_recommendation(self, recommendation):
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
