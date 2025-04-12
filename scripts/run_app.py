#!/usr/bin/env python
"""
A wrapper script to run the Streamlit app without PyObjC initialization issues.
This handles the PyObjC initialization in a way that avoids the CFData assertion errors.
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_streamlit():
    """Run the Streamlit app in a subprocess with the right environment variables."""
    env = os.environ.copy()
    
    # Set environment variables to prevent ObjC errors
    env["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    env["PYOBJC_DISABLE_AUTORELEASE_POOL"] = "YES"
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    
    # Use a specific port to avoid conflicts
    env["STREAMLIT_SERVER_PORT"] = "8501"
    
    # Set an environment variable to indicate we're running in "safe mode"
    # This can be checked in the app to avoid loading problematic modules
    env["OVERLORD_SAFE_MODE"] = "1"
    
    # Find the streamlit executable in the same environment as this script
    streamlit_cmd = sys.executable.replace("python", "streamlit")
    if not os.path.exists(streamlit_cmd):
        # Fall back to running streamlit through the module system
        cmd = [sys.executable, "-m", "streamlit", "run", 
               str(PROJECT_ROOT / "overlord" / "app.py"),
               "--server.headless=true"]
    else:
        cmd = [streamlit_cmd, "run", 
               str(PROJECT_ROOT / "overlord" / "app.py"),
               "--server.headless=true"]
    
    # Run the app in a subprocess so we can properly handle any crashes
    print(f"Starting Streamlit app using: {' '.join(cmd)}")
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
