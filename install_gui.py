#!/usr/bin/env python3
"""
Installation script for Netscapy GUI

This script helps set up the environment for the GUI.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        print("✅ Tkinter is available")
        return True
    except ImportError:
        print("❌ Tkinter is not available")
        print("Please install tkinter for your Python distribution")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def check_external_tools():
    """Check if external tools are available"""
    print("\n🔧 Checking external tools...")

    tools = {
        'nmap': 'Network mapper for port scanning',
        'nikto': 'Web server scanner',
        'whatweb': 'Web technology fingerprinting'
    }

    missing_tools = []

    for tool, description in tools.items():
        try:
            result = subprocess.run([tool, '--version'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {tool}: {description}")
            else:
                print(f"⚠️  {tool}: Installed but may not work properly")
                missing_tools.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ {tool}: Not found - {description}")
            missing_tools.append(tool)

    if missing_tools:
        print(f"\n⚠️  Missing tools: {', '.join(missing_tools)}")
        print("These tools are required for full functionality:")
        print("- On Ubuntu/Debian: sudo apt install nmap nikto")
        print("- On Kali Linux: sudo apt-get install nmap nikto")
        print("- WhatWeb: Install from https://github.com/urbanadventurer/WhatWeb")
        print("\nThe GUI will still work for viewing results and configuration.")

    return len(missing_tools) == 0


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ['output', 'output/reports', 'logs']

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def test_gui_import():
    """Test if GUI can be imported"""
    print("\n🧪 Testing GUI import...")
    try:
        import gui
        print("✅ GUI module imports successfully")
        return True
    except ImportError as e:
        print(f"❌ GUI import failed: {e}")
        return False


def main():
    """Main installation function"""
    print("🚀 Netscapy GUI Installation")
    print("=" * 40)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Check tkinter
    if not check_tkinter():
        print("\n💡 To install tkinter:")
        print("- Ubuntu/Debian: sudo apt-get install python3-tk")
        print("- CentOS/RHEL: sudo yum install tkinter")
        print("- Windows: Usually included with Python")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create directories
    create_directories()

    # Check external tools
    check_external_tools()

    # Test GUI import
    if not test_gui_import():
        sys.exit(1)

    print("\n🎉 Installation completed successfully!")
    print("\nTo run the GUI:")
    print("  python run_gui.py")
    print("  or")
    print("  python gui.py")
    print("\nTo see a demo:")
    print("  python demo_gui.py")


if __name__ == "__main__":
    main()
