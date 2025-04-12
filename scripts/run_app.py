#!/usr/bin/env python
"""
A wrapper script to run the Streamlit app without PyObjC initialization issues.
This handles the PyObjC initialization in a way that avoids the CFData assertion errors.
"""

import os
import sys
import subprocess

# Define a custom which function for older Python versions
def which(program):
    """Custom implementation of which command"""
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def check_dependencies():
    """Check and install required dependencies for GUI automation"""
    # Check for cliclick (required for GUI automation)
    if not which("cliclick"):
        print("Installing cliclick for GUI automation...")
        try:
            # Check if homebrew is installed
            if not which("brew"):
                print("Homebrew is required to install cliclick. Please install homebrew first.")
                return False
                
            # Install cliclick using homebrew
            subprocess.run(["brew", "install", "cliclick"], check=True)
            print("cliclick installed successfully.")
        except subprocess.SubprocessError as e:
            print("Error installing cliclick: {0}".format(e))
            return False
    
    return True

def run_streamlit():
    """Run the Streamlit app in a subprocess with the right environment variables."""
    # First check dependencies
    if not check_dependencies():
        print("WARNING: Some dependencies are missing. The application may not function correctly.")
    
    env = os.environ.copy()
    
    # Set environment variables to prevent ObjC errors
    env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    env["PYOBJC_DISABLE_AUTORELEASE_POOL"] = "YES"
    env["PYTHONPATH"] = PROJECT_ROOT
    
    # Use a specific port to avoid conflicts
    env["STREAMLIT_SERVER_PORT"] = "8501"
    
    # Set an environment variable to indicate we're running in "safe mode"
    # This can be checked in the app to avoid loading problematic modules
    env["OVERLORD_SAFE_MODE"] = "1"
    
    # Check if streamlit is available
    if which("streamlit"):
        # Use standalone streamlit command
        cmd = ["streamlit", "run", 
              os.path.join(PROJECT_ROOT, "overlord", "app.py"),
              "--server.headless=true"]
    else:
        # Fall back to running streamlit through Python module
        try:
            result = subprocess.check_output([sys.executable, "-c", "import streamlit; print('FOUND')"])
            if "FOUND" in result:
                # Streamlit module is available
                cmd = [sys.executable, "-m", "streamlit", "run", 
                      os.path.join(PROJECT_ROOT, "overlord", "app.py"),
                      "--server.headless=true"]
            else:
                print("Streamlit is not installed. Please install it with 'pip install streamlit'.")
                return
        except:
            print("Streamlit is not installed. Please install it with 'pip install streamlit'.")
            return
    
    # Run the app in a subprocess so we can properly handle any crashes
    print("Starting Streamlit app using: {0}".format(' '.join(cmd)))
    try:
        process = subprocess.Popen(cmd, env=env)
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down the Streamlit app...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
    print("Streamlit app has been stopped.")

if __name__ == "__main__":
    run_streamlit()
