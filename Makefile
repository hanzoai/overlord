# Default target
all: install-all test run
	@echo "$(GREEN)All tasks completed.$(RESET)"

.PHONY: all install install-all install-dev install-test reinstall uninstall test lint format clean venv venv-check pytest-check help check-dependencies check-system check-python check-uv run cli install-autogui install-tweening build-package publish

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
	VENV_PYTHON = $(VENV_NAME)\Scripts\python.exe
	RM_CMD = rmdir /s /q
	CP = copy
	SEP = \\
	ACTIVATE_CMD = call
else
	VENV_ACTIVATE = $(VENV_NAME)/bin/activate
	VENV_PYTHON = $(VENV_NAME)/bin/python
	RM_CMD = rm -rf
	CP = cp
	SEP = /
	ACTIVATE_CMD = .
endif

# Python interpreter and package manager
PYTHON = python

# Check if uv is available, otherwise use plain pip
UV := $(shell command -v uv 2> /dev/null)
ifeq ($(UV),)
	PACKAGE_CMD = pip install
	VENV_CMD = $(PYTHON) -m venv
else
	PACKAGE_CMD = uv pip install
	VENV_CMD = uv venv --python=python$(PYTHON_VERSION)
endif

# System & dependency checks
check-uv:
	@echo "$(YELLOW)Checking uv installation...$(RESET)"
	@if ! command -v uv > /dev/null; then \
		echo "$(YELLOW)uv not found. Installing uv...$(RESET)"; \
		pip install uv || { echo "$(RED)Failed to install uv. Please install it manually.$(RESET)"; exit 1; }; \
		echo "$(BLUE)uv installed successfully.$(RESET)"; \
	else \
		echo "$(BLUE)uv is installed.$(RESET)"; \
	fi

check-python:
	@echo "$(YELLOW)Checking Python $(PYTHON_VERSION) installation...$(RESET)"
	@if ! command -v python$(PYTHON_VERSION) > /dev/null; then \
		echo "$(YELLOW)Python $(PYTHON_VERSION) not found. Installing it using uv...$(RESET)"; \
		uv python install $(PYTHON_VERSION) || { echo "$(RED)Failed to install Python $(PYTHON_VERSION).$(RESET)"; exit 1; }; \
		echo "$(BLUE)Python $(PYTHON_VERSION) installed.$(RESET)"; \
	else \
		echo "$(BLUE)$$(python$(PYTHON_VERSION) --version) is installed.$(RESET)"; \
	fi

check-system:
	@echo "$(YELLOW)Checking system...$(RESET)"
	@if [ "$$(uname)" = "Darwin" ]; then \
		echo "$(BLUE)macOS detected.$(RESET)"; \
	elif [ "$$(uname)" = "Linux" ]; then \
		echo "$(BLUE)Linux detected.$(RESET)"; \
	else \
		echo "$(RED)Unsupported system detected. Please use macOS or Linux.$(RESET)"; \
		exit 1; \
	fi

check-dependencies: check-system check-uv check-python
	@echo "$(GREEN)Dependencies checked successfully.$(RESET)"

# Create virtual environment
venv: check-python
	@echo "$(YELLOW)Creating virtual environment...$(RESET)"
	@$(VENV_CMD) $(VENV_NAME)
	@echo "Virtual environment created. Run 'source $(VENV_ACTIVATE)' to activate it."

# Helper to check for virtual environment
venv-check:
	@if [ ! -f $(VENV_ACTIVATE) ]; then \
		echo "$(YELLOW)Virtual environment not found. Creating one...$(RESET)" ; \
		$(MAKE) venv ; \
	fi

# Helper to check if pytest is installed
pytest-check: venv-check
	@if ! $(ACTIVATE_CMD) $(VENV_ACTIVATE) && python -c "import pytest" 2>/dev/null; then \
		echo "$(YELLOW)pytest not found. Installing development dependencies...$(RESET)"; \
		$(MAKE) install-dev; \
	else \
		echo "$(BLUE)pytest already installed.$(RESET)"; \
	fi

# Install tweening package from local repository
install-tweening: venv-check
	@echo "$(YELLOW)Installing hanzo-pytweening from local repository...$(RESET)"
	cd ../tweening && $(ACTIVATE_CMD) /Users/z/work/hanzo/overlord/$(VENV_ACTIVATE) && $(PACKAGE_CMD) -e .
	@echo "$(GREEN)hanzo-pytweening installed.$(RESET)"

# Install autogui package from local repository
install-autogui: venv-check install-tweening
	@echo "$(YELLOW)Installing hanzo-autogui from local repository...$(RESET)"
	cd ../autogui && $(ACTIVATE_CMD) /Users/z/work/hanzo/overlord/$(VENV_ACTIVATE) && $(PACKAGE_CMD) -e .
	@echo "$(GREEN)hanzo-autogui installed.$(RESET)"

install-all: venv-check install-autogui install

install: venv-check
	@echo "$(YELLOW)Installing dependencies...$(RESET)"
	@$(ACTIVATE_CMD) $(VENV_ACTIVATE) && $(PACKAGE_CMD) -e . || { \
		echo "$(YELLOW)Installation with $(PACKAGE_CMD) failed. Trying with pip...$(RESET)"; \
		$(ACTIVATE_CMD) $(VENV_ACTIVATE) && pip install -e .; \
	}
	@echo "$(GREEN)Installation complete.$(RESET)"

install-dev: venv-check
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	@$(ACTIVATE_CMD) $(VENV_ACTIVATE) && $(PACKAGE_CMD) pytest ruff black mypy || { \
		echo "$(YELLOW)Installation with $(PACKAGE_CMD) failed. Trying with pip...$(RESET)"; \
		$(ACTIVATE_CMD) $(VENV_ACTIVATE) && pip install pytest ruff black mypy; \
	}
	@echo "$(GREEN)Development dependencies installed.$(RESET)"

install-test: venv-check install-autogui
	@echo "$(YELLOW)Installing test dependencies...$(RESET)"
	@$(ACTIVATE_CMD) $(VENV_ACTIVATE) && $(PACKAGE_CMD) -e ".[dev]" || { \
		echo "$(YELLOW)Installation with $(PACKAGE_CMD) failed. Trying with pip...$(RESET)"; \
		$(ACTIVATE_CMD) $(VENV_ACTIVATE) && pip install -e ".[dev]"; \
	}
	@echo "$(GREEN)Test dependencies installed.$(RESET)"

uninstall: venv-check
	@echo "$(YELLOW)Removing virtual environment...$(RESET)"
	$(RM_CMD) $(VENV_NAME)
	@echo "$(GREEN)Virtual environment removed.$(RESET)"

reinstall: uninstall venv install

test: pytest-check
	@echo "$(YELLOW)Running tests...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && python -m pytest
	@echo "$(GREEN)Tests complete.$(RESET)"

lint: pytest-check
	@echo "$(YELLOW)Running linters...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && ruff check .
	@echo "$(GREEN)Linting complete.$(RESET)"

format: pytest-check
	@echo "$(YELLOW)Formatting code...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && ruff format .
	@echo "$(GREEN)Formatting complete.$(RESET)"

run: venv-check
	@echo "$(YELLOW)Running streamlit app...$(RESET)"
	uv run overlord/app.py
	@echo "$(GREEN)App stopped.$(RESET)"

cli: venv-check
	@echo "$(YELLOW)Running overlord CLI...$(RESET)"
	uv run overlord/cli.py
	@echo "$(GREEN)CLI command completed.$(RESET)"

clean:
	@echo "$(YELLOW)Cleaning caches...$(RESET)"
	$(RM_CMD) .pytest_cache htmlcov .coverage 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "$(GREEN)Caches cleaned.$(RESET)"

# Build Python package distribution
build-package: install-all test
	@echo "$(YELLOW)Building package...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && $(PACKAGE_CMD) build || $(ACTIVATE_CMD) $(VENV_ACTIVATE) && pip install build
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && python -m build
	@echo "$(GREEN)Package built. Distribution files are in 'dist/'$(RESET)"

# Publish package to PyPI
publish: build-package
	@echo "$(YELLOW)Publishing package to PyPI...$(RESET)"
	@read -p "Are you sure you want to publish to PyPI? [y/N] " answer && [[ $$answer == [yY] ]]
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && $(PACKAGE_CMD) twine || $(ACTIVATE_CMD) $(VENV_ACTIVATE) && pip install twine
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && twine upload dist/*
	@echo "$(GREEN)Package published to PyPI.$(RESET)"

# Help target
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)all$(RESET)                 - Install dependencies, run tests, and start the app"
	@echo "  $(GREEN)install$(RESET)             - Install dependencies (including local hanzo-autogui and hanzo-pytweening)"
	@echo "  $(GREEN)install-autogui$(RESET)     - Install hanzo-autogui from local repository"
	@echo "  $(GREEN)install-tweening$(RESET)    - Install hanzo-pytweening from local repository"
	@echo "  $(GREEN)install-dev$(RESET)         - Install development dependencies"
	@echo "  $(GREEN)install-test$(RESET)        - Install test dependencies"
	@echo "  $(GREEN)uninstall$(RESET)           - Remove virtual environment"
	@echo "  $(GREEN)reinstall$(RESET)           - Recreate virtual environment and reinstall dependencies"
	@echo "  $(GREEN)test$(RESET)                - Run tests (installs dev dependencies if needed)"
	@echo "  $(GREEN)lint$(RESET)                - Run linting (installs dev dependencies if needed)"
	@echo "  $(GREEN)format$(RESET)              - Format code (installs dev dependencies if needed)"
	@echo "  $(GREEN)run$(RESET)                 - Run streamlit app"
	@echo "  $(GREEN)cli$(RESET)                 - Run the overlord CLI command"
	@echo "  $(GREEN)clean$(RESET)               - Clean cache files"
	@echo "  $(GREEN)build-package$(RESET)       - Build Python package distribution"
	@echo "  $(GREEN)publish$(RESET)             - Publish package to PyPI"
	@echo "  $(GREEN)venv$(RESET)                - Create virtual environment"
	@echo "  $(GREEN)check-dependencies$(RESET)  - Check system dependencies"
	@echo "  $(GREEN)check-python$(RESET)        - Check Python installation"
	@echo "  $(GREEN)check-uv$(RESET)            - Check uv installation"
	@echo "  $(GREEN)help$(RESET)                - Show this help message"
