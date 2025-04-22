import unittest
from unittest.mock import patch, MagicMock
from cursor_ai.services.notification_service import NotificationService

class TestNotificationService(unittest.TestCase):
    """Tests for the NotificationService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = NotificationService()
        # Ensure notification_enabled is False for testing
        self.service.notification_enabled = False
    
    def test_send_notification(self):
        """Test sending a notification."""
        result = self.service.send_notification("Test Title", "Test Message")
        self.assertTrue(result, "Notification should succeed when disabled")
    
    @patch('requests.post')
    def test_send_notification_with_pushover(self, mock_post):
        """Test sending a notification with Pushover enabled."""
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Enable notifications for this test
        self.service.notification_enabled = True
        self.service.pushover_token = "test_token"
        self.service.pushover_user = "test_user"
        
        # Send notification
        result = self.service.send_notification("Test Title", "Test Message")
        
        # Check result
        self.assertTrue(result, "Notification should succeed")
        
        # Verify mock was called correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.pushover.net/1/messages.json")
        self.assertEqual(kwargs['data']['token'], "test_token")
        self.assertEqual(kwargs['data']['user'], "test_user")
        self.assertEqual(kwargs['data']['title'], "Test Title")
        self.assertEqual(kwargs['data']['message'], "Test Message")
    
    @patch('requests.post')
    def test_send_recommendation(self, mock_post):
        """Test sending a recommendation notification."""
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Create test recommendation
        recommendation = {
            "title": "Test Recommendation",
            "description": "This is a test recommendation",
            "priority": 1
        }
        
        # Send recommendation
        result = self.service.send_recommendation(recommendation)
        
        # Verify result
        self.assertTrue(result, "Recommendation should succeed")

if __name__ == '__main__':
    unittest.main() 