#!/usr/bin/env python3
"""
Simple launcher for the Netscapy GUI
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import main
    print("Starting Netscapy GUI...")
    main()
except ImportError as e:
    print(f"Error importing GUI: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)
