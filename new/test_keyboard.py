#!/usr/bin/env python3
"""
Test script to verify keyboard functionality works correctly
"""

import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import LEDController
    
    def test_keyboard():
        """Test keyboard functionality"""
        print("Testing keyboard functionality...")
        print("1. The keyboard animation should only trigger when you type")
        print("2. Each key press should trigger a 1-second animation")
        print("3. The animation should stop automatically after the duration")
        print("4. No continuous animation should occur")
        print("\nStarting GUI...")
        
        # Create the application
        app = LEDController()
        
        # Run the GUI
        app.run()
        
    if __name__ == "__main__":
        test_keyboard()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 