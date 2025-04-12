.PHONY: all install install-dev install-test install-publish reinstall uninstall test lint format clean venv run cli build publish patch minor major bump-patch bump-minor bump-major tag-version

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

# Variables
PYTHON_VERSION = 3.13
VENV_NAME ?= .venv
PROJECT_NAME = overlord

# Detect OS for proper path handling
ifeq ($(OS),Windows_NT)
	VENV_ACTIVATE = $(VENV_NAME)\Scripts\activate
	RM_CMD = rmdir /s /q
	SEP = \\
else
	VENV_ACTIVATE = $(VENV_NAME)/bin/activate
	RM_CMD = rm -rf
	SEP = /
endif

# UV package manager
UV = uv

# Project paths
SRC_DIR = overlord
TEST_DIR = tests
DIST_DIR = dist

# Default target
all: install test run
	@echo "$(GREEN)All tasks completed.$(RESET)"

# Run commands in virtual environment
define run_in_venv
	. $(VENV_ACTIVATE) && $(1)
endef

# Create virtual environment
venv:
	@echo "$(YELLOW)Creating virtual environment...$(RESET)"
	@$(UV) venv $(VENV_NAME) --python=$(PYTHON_VERSION)
	@echo "$(GREEN)Virtual environment created. Run 'source $(VENV_ACTIVATE)' to activate it.$(RESET)"

# Install package and dependencies
install: venv
	@echo "$(YELLOW)Installing package...$(RESET)"
	@$(call run_in_venv, $(UV) pip install -e .)
	@echo "$(GREEN)Installation complete.$(RESET)"

# Install development dependencies
install-dev: venv
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	@$(call run_in_venv, $(UV) pip install -e ".[dev]")
	@echo "$(GREEN)Development dependencies installed.$(RESET)"

# Install test dependencies
install-test: venv
	@echo "$(YELLOW)Installing test dependencies...$(RESET)"
	@$(call run_in_venv, $(UV) pip install -e ".[dev]")
	@echo "$(GREEN)Test dependencies installed.$(RESET)"

# Install dependencies for publishing
install-publish: venv
	@echo "$(YELLOW)Installing publish dependencies...$(RESET)"
	@$(call run_in_venv, $(UV) pip install build twine)
	@echo "$(GREEN)Publish dependencies installed.$(RESET)"

# Reinstall and uninstall
uninstall:
	@echo "$(YELLOW)Removing virtual environment...$(RESET)"
	$(RM_CMD) $(VENV_NAME)
	@echo "$(GREEN)Virtual environment removed.$(RESET)"

reinstall: uninstall venv install

# Testing and code quality
test: install-test
	@echo "$(YELLOW)Running tests...$(RESET)"
	@$(call run_in_venv, python -m pytest)
	@echo "$(GREEN)Tests complete.$(RESET)"

lint: install-dev
	@echo "$(YELLOW)Running linters...$(RESET)"
	@$(call run_in_venv, ruff check .)
	@echo "$(GREEN)Linting complete.$(RESET)"

format: install-dev
	@echo "$(YELLOW)Formatting code...$(RESET)"
	@$(call run_in_venv, ruff format .)
	@echo "$(GREEN)Formatting complete.$(RESET)"

# Run commands
run: install
	@echo "$(YELLOW)Running streamlit app...$(RESET)"
	@$(call run_in_venv, python scripts/run_app.py)
	@echo "$(GREEN)App stopped.$(RESET)"

cli: install
	@echo "$(YELLOW)Running overlord CLI...$(RESET)"
	@$(call run_in_venv, python scripts/run_cli.py)
	@echo "$(GREEN)CLI command completed.$(RESET)"

# Clean up
clean:
	@echo "$(YELLOW)Cleaning caches...$(RESET)"
	$(RM_CMD) .pytest_cache htmlcov .coverage $(DIST_DIR) 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "$(GREEN)Caches cleaned.$(RESET)"

# Version management
bump-patch: install
	@echo "$(YELLOW)Bumping patch version...$(RESET)"
	@$(call run_in_venv, python scripts/bump_version.py patch)
	@echo "$(GREEN)Version bumped.$(RESET)"

bump-minor: install
	@echo "$(YELLOW)Bumping minor version...$(RESET)"
	@$(call run_in_venv, python scripts/bump_version.py minor)
	@echo "$(GREEN)Version bumped.$(RESET)"

bump-major: install
	@echo "$(YELLOW)Bumping major version...$(RESET)"
	@$(call run_in_venv, python scripts/bump_version.py major)
	@echo "$(GREEN)Version bumped.$(RESET)"

# Git tagging
tag-version:
	@VERSION=$$(grep 'version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "$(YELLOW)Creating git tag v$$VERSION...$(RESET)"; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "$(YELLOW)Pushing changes and tags to remote...$(RESET)"; \
	git push origin main; \
	git push origin "v$$VERSION"; \
	echo "$(GREEN)Version tagged and pushed.$(RESET)"

# Build and publish
build: clean install-publish
	@echo "$(YELLOW)Building package...$(RESET)"
	@$(call run_in_venv, python -m build)
	@echo "$(GREEN)Package built. Distribution files are in '$(DIST_DIR)/'$(RESET)"

# Publish to PyPI
_publish:
ifdef PYPI_TOKEN
	@echo "$(YELLOW)Publishing to PyPI with token...$(RESET)"
	@$(call run_in_venv, TWINE_USERNAME=__token__ TWINE_PASSWORD=$(PYPI_TOKEN) python -m twine upload $(DIST_DIR)/*)
else
	@echo "$(YELLOW)Publishing to PyPI...$(RESET)"
	@$(call run_in_venv, python -m twine upload $(DIST_DIR)/*)
endif
	@echo "$(GREEN)Package published to PyPI.$(RESET)"

# Combined version bump, build, publish and tag targets
publish: build _publish tag-version

patch: bump-patch build _publish tag-version

minor: bump-minor build _publish tag-version

major: bump-major build _publish tag-version

# Help target
help:
	@echo "$(BLUE)Hanzo Overlord Makefile$(RESET)"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Development Targets:"
	@echo "  $(GREEN)all$(RESET)              - Install dependencies, run tests, and start the app"
	@echo "  $(GREEN)install$(RESET)          - Install package in development mode"
	@echo "  $(GREEN)install-dev$(RESET)      - Install development dependencies"
	@echo "  $(GREEN)install-test$(RESET)     - Install test dependencies"
	@echo "  $(GREEN)reinstall$(RESET)        - Recreate virtual environment and reinstall dependencies"
	@echo "  $(GREEN)uninstall$(RESET)        - Remove virtual environment"
	@echo "  $(GREEN)test$(RESET)             - Run tests"
	@echo "  $(GREEN)lint$(RESET)             - Run linting"
	@echo "  $(GREEN)format$(RESET)           - Format code"
	@echo ""
	@echo "Run Targets:"
	@echo "  $(GREEN)run$(RESET)              - Run streamlit app"
	@echo "  $(GREEN)cli$(RESET)              - Run the overlord CLI"
	@echo ""
	@echo "Build & Publish Targets:"
	@echo "  $(GREEN)build$(RESET)            - Build Python package distribution"
	@echo "  $(GREEN)publish$(RESET)          - Build, publish to PyPI, and tag version"
	@echo "  $(GREEN)patch$(RESET)            - Bump patch version, build, publish, and tag"
	@echo "  $(GREEN)minor$(RESET)            - Bump minor version, build, publish, and tag"
	@echo "  $(GREEN)major$(RESET)            - Bump major version, build, publish, and tag"
	@echo ""
	@echo "Utility Targets:"
	@echo "  $(GREEN)venv$(RESET)             - Create virtual environment"
	@echo "  $(GREEN)clean$(RESET)            - Clean cache files"
	@echo "  $(GREEN)help$(RESET)             - Show this help message"