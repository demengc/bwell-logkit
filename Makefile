.PHONY: help install install-dev test test-cov lint format clean build upload docs

# Default target
help:
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install in development mode with dev dependencies"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the package"
	@echo "  upload       Upload to PyPI (requires credentials)"
	@echo "  docs         Build documentation"

# Installation
install:
	pip install .

install-dev:
	pip install -e .[dev]

# Testing
test:
	pytest

test-cov:
	pytest --cov=src/bwell_logkit --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

# Clean up
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build and upload
build: clean
	python -m build

upload: build
	python -m twine upload dist/*

# Documentation
docs:
	cd docs && make html

# Development workflow
dev-setup: install-dev
	pre-commit install

# Run all checks (useful for CI)
check: format lint test-cov
