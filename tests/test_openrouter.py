import unittest
from unittest.mock import patch, MagicMock
from cursor_ai.utils.openrouter import OpenRouter

class TestOpenRouter(unittest.TestCase):
    """Tests for the OpenRouter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.router = OpenRouter(api_key=self.api_key)
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.router.api_key, self.api_key)
        self.assertEqual(self.router.model, "mistralai/mistral-7b-instruct:free")
        self.assertEqual(self.router.base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(self.router.max_tokens, 1000)
        self.assertEqual(self.router.temperature, 0.7)
    
    def test_build_headers(self):
        """Test header building."""
        headers = self.router._build_headers()
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(headers["HTTP-Referer"], "https://cursor.ai")
        self.assertEqual(headers["X-Title"], "Cursor AI Assistant")
    
    def test_build_payload_default(self):
        """Test payload building with default settings."""
        messages = [{"role": "user", "content": "Hello"}]
        payload = self.router._build_payload(messages)
        
        self.assertEqual(payload["model"], "mistralai/mistral-7b-instruct:free")
        self.assertEqual(payload["messages"], messages)
        self.assertEqual(payload["max_tokens"], 1000)
        self.assertEqual(payload["temperature"], 0.7)
    
    def test_format_messages_string(self):
        """Test formatting a string prompt."""
        messages = self.router._format_messages("Hello, world!")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello, world!")
    
    @patch('requests.post')
    def test_invoke(self, mock_post):
        """Test invoking the API."""
        # Configure mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello, I'm an AI assistant."
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Test invoke
        result = self.router.invoke("Hello")
        
        # Check result
        self.assertEqual(result.content, "Hello, I'm an AI assistant.")
        
        # Verify mock was called
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main() 