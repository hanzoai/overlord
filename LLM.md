# Hanzo Overlord - Project Architecture

## Overview

Hanzo Overlord is a local AI project designed to drive local computer interface, optimized for Metal GPUs. The project provides tools for Mac automation and includes a Streamlit interface.

## Project Structure

```
overlord/
  tools/           # Automation tools
  __init__.py      # Package version and metadata
  app.py           # Streamlit application
  install_dependencies.py  # Dependency installer
  loop.py          # Main execution loop
tests/
  test_basic.py    # Basic tests
scripts/
  bump_version.py  # Version management script
```

## Dependencies

The project has the following key dependencies:
- Python 3.13 (required)
- Streamlit for the user interface
- Anthropic (with AWS Bedrock and Google Vertex support)
- Various input control libraries (keyboard, mouse, pynput)

All dependencies are specified in the pyproject.toml file.

## Build System

The project uses a Makefile with `uv` for package management. The Makefile includes targets for:

1. Setting up development environments
2. Installing dependencies
3. Running tests and linting
4. Building and publishing packages

A streamlined version management system has been implemented with:
- Scripts for version bumping (patch, minor, major)
- Automated synchronization between pyproject.toml and __init__.py
- Quick commands for release workflows (build, publish, tag)

## Workflow

### Development Workflow
1. Create or update virtual environment: `make venv`
2. Install dependencies: `make install`
3. Run tests: `make test`
4. Format code: `make format`
5. Run the application: `make run`

### Release Workflow
1. Bump version: `make bump-patch`, `make bump-minor`, or `make bump-major`
2. Quick release: `make patch`, `make minor`, or `make major`
   - This will bump the version, build the package, publish to PyPI, and tag the release in git

## Architecture Decisions

### Use of `uv`
The project now exclusively uses `uv` for package management. This offers:
- Faster package installation
- Better compatibility with Metal GPUs
- Simplified virtual environment management

### Version Management
- Version is maintained in pyproject.toml as the source of truth
- __init__.py version is kept in sync for runtime access
- A single script handles the versioning process

### Simplified Approach
- All dependencies are declared in pyproject.toml
- The Makefile provides a clean interface for common operations
- No complicated conditional logic or fallbacks

## Implementation Notes

### Metal GPU Optimization
The package is designed to leverage Metal GPUs on Mac systems for improved performance.

### Cross-Platform Considerations
While primarily targeting macOS, the build system detects the operating system and adjusts paths and commands accordingly.

### Quick Patching and Publishing
The system allows for quick version bumping, building, and publishing with single commands:
- `make patch` - For bug fixes and minor changes
- `make minor` - For new features that don't break compatibility
- `make major` - For breaking changes

Each of these commands will:
1. Update the version number
2. Build the package
3. Publish to PyPI
4. Create a git tag
5. Push the tag to the remote repository
