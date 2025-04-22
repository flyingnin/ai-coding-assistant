#!/usr/bin/env python3
"""
Context-Aware Agent CLI

This command-line tool allows users to interact with the context-aware AI agent,
manage code context, and receive context-enhanced responses to queries.
"""

import os
import sys
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from agents.context_aware_agent import ContextAwareAgent
from services.context_service import ContextService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("context_cli.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def process_query(agent: ContextAwareAgent, query: str):
    """Process a user query and print the response."""
    print(f"\nProcessing query: {query}\n")
    
    response = await agent.process_query(query)
    
    if response["success"]:
        print("\n" + "=" * 80)
        print("\nResponse:")
        print(response["data"]["response"])
        print("\n" + "=" * 80)
        
        if response["data"]["had_context"]:
            print(f"\nResponse was enhanced with {response['data']['context_count']} context items.\n")
        else:
            print("\nNo relevant context was found for this query.\n")
    else:
        print(f"\nError: {response.get('error', 'Unknown error')}\n")

async def add_file_to_context(agent: ContextAwareAgent, file_path: str, language: Optional[str] = None):
    """Add a file to the context database."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist.")
        return
        
    # Determine language from file extension if not provided
    if language is None:
        ext = file_path.suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".html": "html",
            ".css": "css",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php"
        }
        language = language_map.get(ext, "text")
    
    try:
        # Read file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Add to context
        result = await agent.add_current_file_to_context(
            file_path=str(file_path),
            content=content,
            language=language
        )
        
        if result["success"]:
            print(f"Added file {file_path} to context database.")
        else:
            print(f"Error adding file to context: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error reading file: {str(e)}")

async def add_directory_to_context(agent: ContextAwareAgent, dir_path: str, recursive: bool = True):
    """Add all files in a directory to the context database."""
    dir_path = Path(dir_path)
    
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"Error: Directory {dir_path} does not exist.")
        return
        
    # Define files to exclude
    exclude_patterns = [
        "__pycache__", 
        ".git", 
        "node_modules", 
        ".venv", 
        "venv", 
        ".env",
        ".jpg", 
        ".jpeg", 
        ".png", 
        ".gif", 
        ".pdf", 
        ".zip"
    ]
    
    # Walk directory
    pattern = "**/*" if recursive else "*"
    files_added = 0
    
    for file_path in dir_path.glob(pattern):
        # Skip directories and excluded patterns
        if (file_path.is_dir() or 
            any(exclude in str(file_path) for exclude in exclude_patterns) or
            any(file_path.name.endswith(ext) for ext in exclude_patterns)):
            continue
            
        try:
            # Process readable text files
            await add_file_to_context(agent, str(file_path))
            files_added += 1
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            continue
    
    print(f"Added {files_added} files from directory {dir_path} to context database.")

async def show_stats(context_service: ContextService):
    """Show statistics about the context database."""
    stats = context_service.get_stats()
    
    if stats["success"]:
        print("\nContext Database Statistics:")
        print(f"Total snippets: {stats['data']['count']}")
        print(f"Storage size: {stats['data']['size']} bytes")
        if "languages" in stats["data"]:
            print("\nLanguage distribution:")
            for lang, count in stats["data"]["languages"].items():
                print(f"  {lang}: {count} snippets")
    else:
        print(f"Error retrieving stats: {stats.get('error', 'Unknown error')}")

async def interactive_mode(agent: ContextAwareAgent):
    """Run an interactive session with the context-aware agent."""
    print("\n" + "=" * 80)
    print("Context-Aware AI Assistant Interactive Mode")
    print("=" * 80)
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'add file <path>' to add a file to the context database.")
    print("Type 'add dir <path>' to add a directory to the context database.")
    print("Type 'stats' to show context database statistics.")
    print("=" * 80 + "\n")
    
    while True:
        try:
            user_input = input("\n> ")
            
            if user_input.lower() in ["exit", "quit"]:
                break
                
            elif user_input.lower() == "stats":
                await show_stats(agent.context_service)
                
            elif user_input.lower().startswith("add file "):
                file_path = user_input[9:].strip()
                await add_file_to_context(agent, file_path)
                
            elif user_input.lower().startswith("add dir "):
                dir_path = user_input[8:].strip()
                await add_directory_to_context(agent, dir_path)
                
            elif user_input.strip():
                await process_query(agent, user_input)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(description="Context-Aware AI Assistant CLI")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a question to the context-aware AI")
    query_parser.add_argument("question", help="The question to ask")
    
    # Add file command
    add_file_parser = subparsers.add_parser("add-file", help="Add a file to the context database")
    add_file_parser.add_argument("file_path", help="Path to the file")
    add_file_parser.add_argument("--language", help="Programming language of the file")
    
    # Add directory command
    add_dir_parser = subparsers.add_parser("add-dir", help="Add files in a directory to the context database")
    add_dir_parser.add_argument("dir_path", help="Path to the directory")
    add_dir_parser.add_argument("--no-recursive", action="store_true", help="Don't recursively add files")
    
    # Stats command
    subparsers.add_parser("stats", help="Show context database statistics")
    
    # Interactive mode command
    subparsers.add_parser("interactive", help="Start an interactive session")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if OpenRouter API key is set
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize agent
    agent = ContextAwareAgent(api_key=api_key)
    
    # Start agent
    await agent.start()
    
    try:
        if args.command == "query":
            await process_query(agent, args.question)
            
        elif args.command == "add-file":
            await add_file_to_context(agent, args.file_path, args.language)
            
        elif args.command == "add-dir":
            recursive = not args.no_recursive
            await add_directory_to_context(agent, args.dir_path, recursive)
            
        elif args.command == "stats":
            await show_stats(agent.context_service)
            
        elif args.command == "interactive" or not args.command:
            await interactive_mode(agent)
            
    finally:
        # Stop agent
        await agent.stop()

def main():
    """Main entry point."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main() 