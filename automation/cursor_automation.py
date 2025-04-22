"""
Cursor Automation

This module provides automation tools for the Cursor IDE.
"""

import os
import time
import logging
import subprocess
import threading
import pyautogui
from services.notification_service import NotificationService

# Configure logging
logger = logging.getLogger(__name__)

class CursorAutomation:
    """Class to automate interactions with Cursor application."""
    
    def __init__(self, notification_service=None):
        self.notification_service = notification_service or NotificationService()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Try to find Cursor executable path - adjust based on actual installation
        if os.name == 'nt':  # Windows
            self.cursor_path = os.path.expanduser("~/AppData/Local/Programs/cursor/Cursor.exe")
        elif os.name == 'posix':  # macOS/Linux
            self.cursor_path = "/Applications/Cursor.app/Contents/MacOS/Cursor"
        else:
            self.cursor_path = None
            logger.warning(f"Unsupported OS: {os.name}")
    
    def start(self):
        """Start the cursor automation."""
        self.start_monitoring()
            
    def start_cursor(self):
        """Starts the Cursor application if it's not running."""
        if not self.cursor_path or not os.path.exists(self.cursor_path):
            logger.error(f"Cursor executable not found at: {self.cursor_path}")
            self.notification_service.notify_cursor_error("Cursor executable not found")
            return False
            
        try:
            # Check if Cursor is already running
            if self._is_cursor_running():
                logger.info("Cursor is already running")
                return True
                
            # Start Cursor
            logger.info(f"Starting Cursor from: {self.cursor_path}")
            subprocess.Popen([self.cursor_path])
            
            # Wait for Cursor to start
            for _ in range(30):  # Wait up to 30 seconds
                if self._is_cursor_running():
                    logger.info("Cursor started successfully")
                    return True
                time.sleep(1)
                
            logger.error("Cursor failed to start within timeout period")
            self.notification_service.notify_cursor_error("Failed to start Cursor")
            return False
            
        except Exception as e:
            logger.error(f"Error starting Cursor: {str(e)}")
            self.notification_service.notify_cursor_error(f"Error starting Cursor: {str(e)}")
            return False
            
    def _is_cursor_running(self):
        """Check if Cursor is currently running."""
        process_name = "Cursor.exe" if os.name == 'nt' else "Cursor"
        
        try:
            if os.name == 'nt':  # Windows
                output = subprocess.check_output(['tasklist', '/FI', f'IMAGENAME eq {process_name}']).decode()
                return process_name in output
            else:  # macOS/Linux
                output = subprocess.check_output(['pgrep', '-f', process_name]).decode()
                return len(output.strip()) > 0
        except:
            return False
            
    def bypass_continue_dialog(self):
        """
        Attempt to bypass the "continue" dialog that appears after 25 requests.
        Uses image recognition to find and click the button.
        """
        try:
            # Define the continue button's appearance
            # These are placeholder values - you'd need screenshots of the actual button
            continue_button_locations = [
                pyautogui.locateOnScreen('continue_button.png', confidence=0.8),
                pyautogui.locateOnScreen('continue_button_alt.png', confidence=0.8),
            ]
            
            for location in continue_button_locations:
                if location:
                    logger.info("Found continue button, clicking it")
                    center = pyautogui.center(location)
                    pyautogui.click(center)
                    
                    # Notify user
                    self.notification_service.send_notification(
                        title="Continue Button Bypassed",
                        message="Automatically clicked the continue button in Cursor"
                    )
                    return True
                    
            logger.info("No continue button found on screen")
            return False
            
        except Exception as e:
            logger.error(f"Error bypassing continue dialog: {str(e)}")
            return False
            
    def start_monitoring(self):
        """Start monitoring thread to detect and handle continue dialogs."""
        if self.monitoring_active:
            logger.info("Monitoring already active")
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Started monitoring for continue dialogs")
        
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Stopped monitoring")
        
    def _monitor_loop(self):
        """Monitoring loop to check for continue dialogs and inactivity."""
        last_activity_check = time.time()
        
        while self.monitoring_active:
            try:
                # Check for the continue button every 5 seconds
                self.bypass_continue_dialog()
                
                # Check for inactivity every 60 seconds
                current_time = time.time()
                if current_time - last_activity_check >= 60:
                    self.notification_service.check_inactivity(timeout_minutes=3)
                    last_activity_check = current_time
                    
                # Check if Cursor is still running
                if not self._is_cursor_running():
                    logger.warning("Cursor is no longer running")
                    self.notification_service.notify_cursor_error("Cursor has stopped running")
                    self.monitoring_active = False
                    break
                    
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(30)  # Wait longer after an error
                
    def accept_file_changes(self):
        """
        Automatically accept any pending file changes in Cursor.
        This is a placeholder - implementation will depend on Cursor's UI.
        """
        try:
            # Look for file change indicators
            # This is highly dependent on Cursor's UI
            change_indicators = pyautogui.locateAllOnScreen('file_change_indicator.png', confidence=0.7)
            
            changes_accepted = 0
            for indicator in change_indicators:
                center = pyautogui.center(indicator)
                pyautogui.click(center)
                
                # Look for accept button
                accept_button = pyautogui.locateOnScreen('accept_changes_button.png', confidence=0.8)
                if accept_button:
                    accept_center = pyautogui.center(accept_button)
                    pyautogui.click(accept_center)
                    changes_accepted += 1
                    
            if changes_accepted > 0:
                logger.info(f"Accepted {changes_accepted} file changes")
                self.notification_service.send_notification(
                    title="Changes Accepted",
                    message=f"Automatically accepted {changes_accepted} file changes in Cursor"
                )
                
            return changes_accepted
            
        except Exception as e:
            logger.error(f"Error accepting file changes: {str(e)}")
            return 0 