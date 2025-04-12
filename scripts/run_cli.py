#!/usr/bin/env python
"""
A wrapper script to run the Overlord CLI without PyObjC initialization issues.
This handles the PyObjC initialization in a way that avoids the CFData assertion errors.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def run_cli():
    """Run the CLI with the right environment variables."""
    # Set environment variables to prevent ObjC errors
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    os.environ["PYOBJC_DISABLE_AUTORELEASE_POOL"] = "YES"
    os.environ["PYTHONPATH"] = str(PROJECT_ROOT)
    
    # Set an environment variable to indicate we're running in "safe mode"
    os.environ["OVERLORD_SAFE_MODE"] = "1"
    
    # Add the project root to sys.path to ensure imports work
    sys.path.insert(0, str(PROJECT_ROOT))
    
    # Import and run the CLI module directly
    cli_path = PROJECT_ROOT / "overlord" / "cli.py"
    
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
        print(f"Error running the CLI: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_cli()
