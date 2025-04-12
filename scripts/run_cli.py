#!/usr/bin/env python
"""
A wrapper script to run the Overlord CLI without PyObjC initialization issues.
This handles the PyObjC initialization in a way that avoids the CFData assertion errors.
"""

import os
import sys
import importlib.util
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

def run_cli():
    """Run the CLI with the right environment variables."""
    # First check dependencies
    if not check_dependencies():
        print("WARNING: Some dependencies are missing. The application may not function correctly.")
    
    # Set environment variables to prevent ObjC errors
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    os.environ["PYOBJC_DISABLE_AUTORELEASE_POOL"] = "YES"
    os.environ["PYTHONPATH"] = PROJECT_ROOT
    
    # Set an environment variable to indicate we're running in "safe mode"
    os.environ["OVERLORD_SAFE_MODE"] = "1"
    
    # Add the project root to sys.path to ensure imports work
    sys.path.insert(0, PROJECT_ROOT)
    
    # Import and run the CLI module directly
    cli_path = os.path.join(PROJECT_ROOT, "overlord", "cli.py")
    
    try:
        # Import the CLI module
        spec = importlib.util.spec_from_file_location("cli", cli_path)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        
        # Look for a main function or similar entry point
        if hasattr(cli_module, "main"):
            cli_module.main()
        elif hasattr(cli_module, "cli"):
            cli_module.cli()
        else:
            # If no specific entry point is found, the module's top-level code will have run
            print("CLI execution complete.")
    except Exception as e:
        print("Error running the CLI: {0}".format(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_cli()
