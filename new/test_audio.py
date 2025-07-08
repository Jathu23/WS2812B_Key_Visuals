#!/usr/bin/env python3
"""
Test script to verify audio functionality works correctly
"""

import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import LEDController
    
    def test_audio():
        """Test audio functionality"""
        print("Testing audio functionality...")
        print("1. Audio devices should be listed in the dropdown")
        print("2. You should be able to select an audio device")
        print("3. Audio visualization should work when enabled")
        print("4. Audio level should be displayed in real-time")
        print("\nStarting GUI...")
        
        # Create the application
        app = LEDController()
        
        # Run the GUI
        app.run()
        
    if __name__ == "__main__":
        test_audio()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 