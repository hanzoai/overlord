# Default target
all: install test
	@echo "$(GREEN)All tasks completed.$(RESET)"

.PHONY: all install install-dev install-gui reinstall uninstall test lint format clean venv venv-check help check-dependencies check-system check-python check-uv run cli

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

# Variables
PYTHON_VERSION = 3.13
VENV_NAME ?= .venv
PROJECT_NAME = mac-use

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

install-gui: venv-check
	@echo "$(YELLOW)Installing GUI automation dependencies...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && python mac_use/install_dependencies.py
	@echo "$(GREEN)GUI automation dependencies installed.$(RESET)"

uninstall: venv-check
	@echo "$(YELLOW)Removing virtual environment...$(RESET)"
	$(RM_CMD) $(VENV_NAME)
	@echo "$(GREEN)Virtual environment removed.$(RESET)"

reinstall: uninstall venv install

test: venv-check
	@echo "$(YELLOW)Running tests...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && python -m pytest
	@echo "$(GREEN)Tests complete.$(RESET)"

lint: venv-check
	@echo "$(YELLOW)Running linters...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && ruff check .
	@echo "$(GREEN)Linting complete.$(RESET)"

format: venv-check
	@echo "$(YELLOW)Formatting code...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && ruff format .
	@echo "$(GREEN)Formatting complete.$(RESET)"

run: venv-check
	@echo "$(YELLOW)Running streamlit app...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && streamlit run mac_use/streamlit.py
	@echo "$(GREEN)App stopped.$(RESET)"

cli: venv-check
	@echo "$(YELLOW)Running mac-use CLI...$(RESET)"
	$(ACTIVATE_CMD) $(VENV_ACTIVATE) && mac-use
	@echo "$(GREEN)CLI command completed.$(RESET)"

clean:
	@echo "$(YELLOW)Cleaning caches...$(RESET)"
	$(RM_CMD) .pytest_cache htmlcov .coverage 2>/dev/null || true
	find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "$(GREEN)Caches cleaned.$(RESET)"

# Help target
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)all$(RESET)                 - Install dependencies, run tests"
	@echo "  $(GREEN)install$(RESET)             - Install dependencies"
	@echo "  $(GREEN)install-dev$(RESET)         - Install development dependencies
	@echo "  $(GREEN)install-gui$(RESET)         - Install GUI automation dependencies"
	@echo "  $(GREEN)uninstall$(RESET)           - Remove virtual environment"
	@echo "  $(GREEN)reinstall$(RESET)           - Recreate virtual environment and reinstall dependencies"
	@echo "  $(GREEN)test$(RESET)                - Run tests"
	@echo "  $(GREEN)lint$(RESET)                - Run linting"
	@echo "  $(GREEN)format$(RESET)              - Format code"
	@echo "  $(GREEN)run$(RESET)                 - Run streamlit app"
	@echo "  $(GREEN)clean$(RESET)               - Clean cache files"
	@echo "  $(GREEN)venv$(RESET)                - Create virtual environment"
	@echo "  $(GREEN)check-dependencies$(RESET)  - Check system dependencies"
	@echo "  $(GREEN)help$(RESET)                - Show this help message
	@echo "  $(GREEN)cli$(RESET)                 - Run the mac-use CLI command"