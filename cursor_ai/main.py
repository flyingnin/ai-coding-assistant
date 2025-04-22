#!/usr/bin/env python3
"""
Main entry point for running the Cursor AI Assistant.

This module provides functions to run the AI notification agent, automation tools,
and code context services.
"""

import os
import sys
import time
import logging
import argparse
import asyncio
from dotenv import load_dotenv

from cursor_ai.agents.ai_notification_agent import AINotificationAgent
from cursor_ai.automation.cursor_automation import CursorAutomation
from cursor_ai.services.notification_service import NotificationService
from services.context_service import ContextService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cursor_ai.log")
    ]
)
logger = logging.getLogger(__name__)

def run_notification_agent():
    """Run the AI notification agent."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Check if OpenRouter API key is set
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("OPENROUTER_API_KEY environment variable not set")
            sys.exit(1)
            
        # Initialize the agent
        logger.info("Initializing AI Notification Agent")
        agent = AINotificationAgent(api_key=api_key)
        
        # Main loop to keep the program running
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Shutting down notification agent")
            agent.stop_monitoring()
            
    except Exception as e:
        logger.error(f"Error running notification agent: {str(e)}", exc_info=True)
        sys.exit(1)

def run_cursor_automation():
    """Run the Cursor automation tools."""
    try:
        # Initialize services
        notification_service = NotificationService()
        automation = CursorAutomation(notification_service)
        
        # Start Cursor if not running
        if automation.start_cursor():
            # Start monitoring for continue dialogs and inactivity
            automation.start_monitoring()
            
            # Main loop
            try:
                while True:
                    # Check for file changes to accept automatically
                    automation.accept_file_changes()
                    time.sleep(30)
            except KeyboardInterrupt:
                logger.info("Shutting down cursor automation")
                automation.stop_monitoring()
                
    except Exception as e:
        logger.error(f"Error running cursor automation: {str(e)}", exc_info=True)
        sys.exit(1)

async def run_context_service():
    """Run the code context service."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Check if OpenRouter API key is set
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.error("OPENROUTER_API_KEY environment variable not set")
            sys.exit(1)
            
        # Initialize the context service
        logger.info("Initializing Context Service")
        context_service = ContextService(api_key=api_key)
        
        # Start the service
        await context_service.start()
        
        # Main loop to keep the program running
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            logger.info("Shutting down context service")
            await context_service.stop()
            
    except Exception as e:
        logger.error(f"Error running context service: {str(e)}", exc_info=True)
        sys.exit(1)

def context_service_wrapper():
    """Wrapper to run the async context service in a synchronous environment."""
    asyncio.run(run_context_service())

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cursor AI Assistant")
    parser.add_argument("--mode", choices=["notification", "automation", "context", "all"], 
                      default="all", help="Mode to run (default: all)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Cursor AI Assistant in {args.mode} mode")
    
    # Load environment variables at startup
    load_dotenv()
    
    if args.mode in ["notification", "all"]:
        if args.mode == "all":
            # Fork a process for the notification agent
            if os.name != 'nt':  # Not Windows
                pid = os.fork()
                if pid == 0:  # Child process
                    run_notification_agent()
                    sys.exit(0)
            else:
                # On Windows, we just run in the same process for simplicity
                run_notification_agent()
        else:
            run_notification_agent()
            
    if args.mode in ["context", "all"]:
        if args.mode == "all":
            # Fork a process for the context service
            if os.name != 'nt':  # Not Windows
                pid = os.fork()
                if pid == 0:  # Child process
                    context_service_wrapper()
                    sys.exit(0)
            else:
                # On Windows, we just run in a thread
                import threading
                context_thread = threading.Thread(target=context_service_wrapper)
                context_thread.daemon = True
                context_thread.start()
        else:
            context_service_wrapper()
            
    if args.mode in ["automation", "all"]:
        run_cursor_automation()

if __name__ == "__main__":
    main() 