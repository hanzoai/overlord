#!/usr/bin/env python3
"""
Helper script to install GUI automation dependencies in a way compatible with Python 3.13
"""

import os
import platform
import subprocess
import sys


def run_command(cmd):
    """Run a shell command and print output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"Success: {result.stdout}")
    return result.returncode == 0


def install_mac_dependencies():
    """Install Mac-specific dependencies"""
    print("Installing PyAutoGUI dependencies on macOS")
    
    # Install pyobjc components separately (more reliable than depending on PyAutoGUI)
    commands = [
        "pip install pyobjc-core",
        "pip install pyobjc-framework-Cocoa",
        "pip install pyobjc-framework-Quartz",
        # Now install mouse control libraries
        "pip install mouseinfo",
        "pip install mouse",
        # Install pillow for screenshot capabilities
        "pip install pillow",
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            print(f"Warning: Failed to run {cmd}")
    
    print("Mac dependencies installation completed")


def install_linux_dependencies():
    """Install Linux-specific dependencies"""
    print("Installing PyAutoGUI dependencies on Linux")
    
    # Install X11 dependencies
    commands = [
        "pip install python3-xlib",
        "pip install pyscreeze",
        "pip install mouseinfo",
        "pip install mouse",
        "pip install pillow",
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            print(f"Warning: Failed to run {cmd}")
    
    print("Linux dependencies installation completed")


def main():
    """Main function to install the appropriate dependencies"""
    system = platform.system()
    
    if system == "Darwin":
        install_mac_dependencies()
    elif system == "Linux":
        install_linux_dependencies()
    else:
        print(f"Unsupported platform: {system}")
        return 1
    
    print("GUI automation dependencies installed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
