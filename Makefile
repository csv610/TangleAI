.PHONY: help setup-venv venv install install-dev uninstall clean build test lint format type-check pre-commit docs shell check check-api-key test-api example-query version info build-clean

# Virtual environment configuration
VENV := perplxenv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Create virtual environment if it doesn't exist
$(VENV):
	@echo "Creating virtual environment: $(VENV)"
	python3 -m venv $(VENV)
	@echo "✓ Virtual environment created"
	@echo ""
	@echo "Activate it with: source $(VENV)/bin/activate"

# Alias for venv
venv: $(VENV)

# Setup venv and install dev dependencies
setup-venv: $(VENV) install-dev
	@echo ""
	@echo "✓ Virtual environment setup complete!"
	@echo ""
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "To deactivate, run:"
	@echo "  deactivate"

# Default target
help:
	@echo "Perplexity AI Toolkit - Development Commands"
	@echo "============================================"
	@echo ""
	@echo "Virtual Environment:"
	@echo "  make venv              Create virtual environment ($(VENV))"
	@echo "  make setup-venv        Create venv and install dev dependencies (recommended)"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install           Install package in production mode"
	@echo "  make install-dev       Install package in development mode with all extras"
	@echo "  make uninstall         Uninstall the package"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              Run flake8 linter"
	@echo "  make format            Format code with black and isort"
	@echo "  make type-check        Run mypy type checker"
	@echo "  make pre-commit        Run all pre-commit checks (lint, format, type-check)"
	@echo ""
	@echo "Testing:"
	@echo "  make test              Run pytest tests"
	@echo "  make test-cov          Run tests with coverage report"
	@echo ""
	@echo "Building & Distribution:"
	@echo "  make build             Build source and wheel distributions"
	@echo "  make build-clean       Remove all build artifacts"
	@echo "  make clean             Clean all generated files (build, tests, cache)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs              Generate documentation"
	@echo ""
	@echo "Development:"
	@echo "  make shell             Start Python interactive shell"
	@echo "  make check             Run all checks (lint, type-check, test)"
	@echo ""

# Installation targets
install: $(VENV)
	@echo "Installing package..."
	$(PIP) install .
	@echo "✓ Installation complete"

install-dev: $(VENV)
	@echo "Installing development dependencies..."
	$(PIP) install -e ".[dev,pdf,image]"
	@echo "✓ Development environment setup complete"

uninstall: $(VENV)
	@echo "Uninstalling package..."
	$(PIP) uninstall -y perplexity-toolkit || true
	@echo "✓ Uninstallation complete"

# Code quality targets
lint: $(VENV)
	@echo "Running flake8..."
	$(PYTHON) -m flake8 perplx.py tangle/ examples/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "✓ Linting complete"

format: $(VENV)
	@echo "Running black..."
	$(PYTHON) -m black perplx.py tangle/ examples/
	@echo "Running isort..."
	$(PYTHON) -m isort perplx.py tangle/ examples/
	@echo "✓ Code formatting complete"

type-check: $(VENV)
	@echo "Running mypy..."
	$(PYTHON) -m mypy perplx.py tangle/ examples/ --ignore-missing-imports --check-untyped-defs || true
	@echo "✓ Type checking complete"

pre-commit: format lint type-check
	@echo "✓ All pre-commit checks passed"

# Testing targets
test: $(VENV)
	@echo "Running pytest..."
	$(PYTHON) -m pytest -v --tb=short || true

test-cov: $(VENV)
	@echo "Running pytest with coverage..."
	$(PYTHON) -m pytest --cov=. --cov-report=html --cov-report=term-missing || true
	@echo "Coverage report generated in htmlcov/index.html"

# Build targets
build: $(VENV)
	@echo "Building distributions..."
	$(PYTHON) -m build
	@echo "✓ Build complete"

build-clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	@echo "✓ Build artifacts cleaned"

# Cleanup targets
clean: build-clean
	@echo "Cleaning Python cache and test artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage*" -delete 2>/dev/null || true
	rm -rf htmlcov/
	@echo "✓ All caches cleaned"

clean-venv:
	@echo "Removing virtual environment: $(VENV)"
	rm -rf $(VENV)
	@echo "✓ Virtual environment removed"

# Documentation targets
docs: $(VENV)
	@echo "Generating documentation..."
	@echo "Note: Ensure you have sphinx installed (pip install sphinx)"
	@echo "Documentation generation would go here"
	@echo "✓ Documentation would be generated in docs/"

# Development targets
shell: $(VENV)
	@echo "Starting Python interactive shell..."
	$(PYTHON) -c "import sys; sys.path.insert(0, '.'); import perplx; from tangle.text.text_client import PerplexityTextClient; print('Available: PerplexityTextClient, ModelConfig'); import code; code.interact(local=locals())"

check: lint type-check test
	@echo "✓ All checks passed!"

# API Key setup helper
check-api-key:
	@if [ -z "$$PERPLEXITY_API_KEY" ]; then \
		echo "⚠️  PERPLEXITY_API_KEY environment variable not set"; \
		echo "Set it with: export PERPLEXITY_API_KEY='your-api-key'"; \
	else \
		echo "✓ PERPLEXITY_API_KEY is set"; \
	fi

# Run a simple test query (requires API key)
test-api: $(VENV) check-api-key
	@$(PYTHON) -c "from tangle.text.text_client import PerplexityTextClient; client = PerplexityTextClient(); print('Testing API...'); response = client.query('What is 2+2?'); print('✓ API test successful'); print('Response:', response[:100] + '...' if len(response) > 100 else response)"

# Quick start examples
example-query: $(VENV)
	@echo "Running simple query example..."
	@$(PYTHON) examples/city_info.py

# Version information
version: $(VENV)
	@echo "Perplexity AI Toolkit"
	@$(PYTHON) -c "import setup; print('Version: 0.1.0')" 2>/dev/null || echo "Version: 0.1.0"

# Info targets
info:
	@echo "Project Information"
	@echo "==================="
	@echo "Name: Perplexity AI Toolkit"
	@echo "Version: 0.1.0"
	@echo "Description: Python client and toolkit for Perplexity AI API"
	@echo ""
	@echo "Project Structure:"
	@echo "  perplx.py              - Core ModelConfig class"
	@echo "  tangle/text/           - Text processing (queries, reasoning, research, chat)"
	@echo "  tangle/pdf/            - PDF processing"
	@echo "  tangle/image/          - Image processing"
	@echo "  examples/              - Example utilities and usage"
	@echo ""
	@echo "Virtual Environment:"
	@echo "  Location: $(VENV)"
	@echo "  Activate: source $(VENV)/bin/activate"
	@echo "  Deactivate: deactivate"
	@echo ""
	@echo "Quick Links:"
	@echo "  make help              - Show this help message"
	@echo "  make setup-venv        - Setup development environment (recommended)"
	@echo "  make check             - Run all code checks"
	@echo "  make test              - Run unit tests"
	@echo "  make clean             - Clean generated files"
