#!/usr/bin/env python3
"""
Test script to demonstrate the new Center Bars audio mode
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import LEDController
    
    def test_center_bars():
        """Test the new Center Bars audio mode"""
        print("🎵 Center Bars Audio Mode Test")
        print("=" * 50)
        print("This new mode features:")
        print("• Smooth center-expanding bars")
        print("• Dynamic color gradients")
        print("• Sparkle effects on strong beats")
        print("• Smooth transitions and fading")
        print("• Asymmetric left/right effects")
        print("\nTo test:")
        print("1. Select 'Stereo Mix' for system audio")
        print("2. Choose 'Center Bars' mode")
        print("3. Enable Audio Visualization")
        print("4. Play some music!")
        print("\nStarting GUI...")
        
        # Create the application
        app = LEDController()
        
        # Run the GUI
        app.run()
        
    if __name__ == "__main__":
        test_center_bars()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 