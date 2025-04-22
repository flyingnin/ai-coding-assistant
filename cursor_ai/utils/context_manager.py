import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CursorContext:
    """
    Manages and tracks the user's current coding context within Cursor.
    
    This class maintains information about:
    - Current and recently viewed files
    - Functions and classes being worked on
    - Current tasks and activities
    - History of user actions
    """
    
    def __init__(self):
        """Initialize the context manager."""
        # Current state
        self.current_file: Optional[str] = None
        self.recent_files: List[str] = []
        self.current_functions: List[str] = []
        self.current_tasks: List[str] = []
        
        # History tracking
        self.file_history: List[Dict[str, Any]] = []
        self.last_update: datetime = datetime.now()
        
        # Context buffer sizes
        self.max_recent_files = 10
        self.max_file_history = 50
    
    def update(self):
        """Update the context with the latest information from Cursor."""
        try:
            # This would be connected to actual Cursor API in production
            # For now, we'll use mock data or try to get info from environment
            
            # Try to get current file from environment or recent updates
            self._update_current_file()
            
            # Update the time
            self.last_update = datetime.now()
            
            logger.debug("Updated coding context")
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
    
    def _update_current_file(self):
        """Update information about the current file."""
        # In a real implementation, this would get information from Cursor's API
        # For now, we'll use a simple placeholder or environment variable
        
        # Mock implementation - in production this would get actual info from Cursor
        env_current_file = os.getenv("CURSOR_CURRENT_FILE")
        if env_current_file and env_current_file != self.current_file:
            # Add the previous current file to recent files if it exists
            if self.current_file:
                self._add_to_recent_files(self.current_file)
            
            # Update current file
            self.current_file = env_current_file
            
            # Add to file history
            self.file_history.append({
                "file": self.current_file,
                "timestamp": datetime.now(),
                "action": "opened"
            })
            
            # Trim history if too long
            if len(self.file_history) > self.max_file_history:
                self.file_history = self.file_history[-self.max_file_history:]
    
    def _add_to_recent_files(self, file_path: str):
        """Add a file to the recent files list."""
        # Remove the file if it already exists (to move it to the front)
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Add to the front of recent files
        self.recent_files.insert(0, file_path)
        
        # Trim if too long
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
    
    def get_current_file(self) -> str:
        """Get the current file."""
        return self.current_file or "Unknown"
    
    def get_recent_files(self) -> List[str]:
        """Get the list of recently viewed files."""
        return self.recent_files
    
    def get_current_functions(self) -> List[str]:
        """Get the list of functions/classes being worked on."""
        return self.current_functions
    
    def get_current_tasks(self) -> List[str]:
        """Get the list of current tasks."""
        return self.current_tasks
    
    def has_sufficient_context(self) -> bool:
        """Determine if there is enough context to generate recommendations."""
        # Basic check - require at least a current file
        if not self.current_file:
            return False
        
        # Check if we have some history
        if len(self.file_history) < 3:
            return False
        
        return True
    
    def add_task(self, task: str):
        """Add a task to the current tasks list."""
        if task not in self.current_tasks:
            self.current_tasks.append(task)
    
    def remove_task(self, task: str):
        """Remove a task from the current tasks list."""
        if task in self.current_tasks:
            self.current_tasks.remove(task)
    
    def clear(self):
        """Clear all context data."""
        self.current_file = None
        self.recent_files = []
        self.current_functions = []
        self.current_tasks = []
        self.file_history = []
        self.last_update = datetime.now() 