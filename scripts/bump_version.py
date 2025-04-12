#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Version bumping script for hanzo-overlord.

This script bumps the version in pyproject.toml and then updates
overlord/__init__.py to match.

Usage:
    python -m scripts.bump_version [major|minor|patch]
"""

import argparse
import os
import re
import sys


def read_pyproject_version(path):
    """Read version from pyproject.toml.
    
    Args:
        path: Path to pyproject.toml
        
    Returns:
        The version string from pyproject.toml
    """
    with open(path, "r") as f:
        content = f.read()
    
    # Extract version using regex
    version_pattern = r'version\s*=\s*["\']([^"\']+)["\']'
    match = re.search(version_pattern, content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def write_pyproject_version(path, new_version):
    """Write version to pyproject.toml.
    
    Args:
        path: Path to pyproject.toml
        new_version: The new version string
    """
    with open(path, "r") as f:
        content = f.read()
    
    # Update the version
    version_pattern = r'version\s*=\s*["\']([^"\']+)["\']'
    updated_content = re.sub(version_pattern, 'version = "{0}"'.format(new_version), content)
    
    with open(path, "w") as f:
        f.write(updated_content)


def bump_version(version, bump_type):
    """Bump a version string.
    
    Args:
        version: The current version string (e.g., "0.1.34")
        bump_type: The type of bump (major, minor, or patch)
        
    Returns:
        The new version string
    """
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        raise ValueError("Invalid version format: {0}".format(version))
    
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError("Invalid bump type: {0}".format(bump_type))
    
    return "{0}.{1}.{2}".format(major, minor, patch)


def update_init_version(init_path, version):
    """Update the __version__ in __init__.py.
    
    Args:
        init_path: Path to __init__.py
        version: The version string to set
        
    Returns:
        True if the file was updated, False if it already had the correct version
    """
    # Create __init__.py if it doesn't exist
    if not os.path.exists(init_path):
        print("__init__.py not found at {0}, creating it...".format(init_path))
        with open(init_path, "w") as f:
            f.write('"""Hanzo Overlord package."""\n\n__version__ = "{0}"\n'.format(version))
        print("Created __init__.py with version {0}".format(version))
        return True
    
    with open(init_path, "r") as f:
        init_content = f.read()
    
    # Look for the version pattern
    version_pattern = r'__version__\s*=\s*["\']([^"\']+)["\']'
    match = re.search(version_pattern, init_content)
    
    if match:
        current_version = match.group(1)
        if current_version == version:
            print("Version in __init__.py already matches: {0}".format(version))
            return False
        
        # Replace the version
        new_content = re.sub(
            version_pattern, 
            '__version__ = "{0}"'.format(version), 
            init_content
        )
        
        with open(init_path, "w") as f:
            f.write(new_content)
        
        print("Updated __init__.py version from {0} to {1}".format(current_version, version))
        return True
    else:
        # If __version__ isn't defined yet, add it after the module docstring
        docstring_pattern = r'""".*?"""\s*'
        match = re.search(docstring_pattern, init_content, re.DOTALL)
        if match:
            new_content = re.sub(
                docstring_pattern, 
                '{0}\n__version__ = "{1}"\n'.format(match.group(0), version), 
                init_content, 
                count=1, 
                flags=re.DOTALL
            )
        else:
            # If no docstring, add to top of file
            new_content = '"""Hanzo Overlord package."""\n\n__version__ = "{0}"\n\n{1}'.format(
                version, init_content)
            
        with open(init_path, "w") as f:
            f.write(new_content)
        
        print('Added __version__ = "{0}" to __init__.py'.format(version))
        return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Bump the project version")
    parser.add_argument(
        "bump_type", 
        choices=["major", "minor", "patch"],
        help="Type of version bump"
    )
    args = parser.parse_args()
    
    try:
        # Determine project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pyproject_path = os.path.join(project_root, "pyproject.toml")
        init_path = os.path.join(project_root, "overlord", "__init__.py")
        
        # Read current version
        current_version = read_pyproject_version(pyproject_path)
        
        # Calculate new version
        new_version = bump_version(current_version, args.bump_type)
        print("Bumping version: {0} -> {1}".format(current_version, new_version))
        
        # Update pyproject.toml
        write_pyproject_version(pyproject_path, new_version)
        print("Updated version in pyproject.toml")
        
        # Update __init__.py
        update_init_version(init_path, new_version)
        
        # Create a git commit
        print("\nTo commit this version bump, run:")
        print('git commit -am "Bump version to {0}"'.format(new_version))
        
        return 0
    except Exception as e:
        sys.stderr.write("Error: {0}\n".format(str(e)))
        return 1


if __name__ == "__main__":
    sys.exit(main())