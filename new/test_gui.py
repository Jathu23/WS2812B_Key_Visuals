#!/usr/bin/env python3
"""
Simple test script to verify the GUI works without Arduino connection
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import LEDController
    
    def test_gui():
        """Test the GUI without connecting to Arduino"""
        print("Starting GUI test...")
        
        # Create the application
        app = LEDController()
        
        # Show a test message
        messagebox.showinfo("Test", "GUI is working! This is a test without Arduino connection.")
        
        # Run the GUI
        app.run()
        
    if __name__ == "__main__":
        test_gui()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 