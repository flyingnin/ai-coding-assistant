#!/usr/bin/env python3
"""
Test runner for Cursor AI Assistant.

This script discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

def run_tests():
    """Discover and run all tests."""
    # Initialize the test loader
    loader = unittest.TestLoader()
    
    # Start test discovery from the tests directory
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(test_dir)
    
    # Initialize the test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = runner.run(suite)
    
    # Return 0 for success, 1 for failure
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 