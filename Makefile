.PHONY: help app data-update test test-unit test-integration test-cov lint format format-check type-check check-all pre-commit-install pre-commit-run clean

help:  ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Application targets
app:  ## Run the Streamlit dashboard
	poetry run streamlit run app/streamlit_app.py

data-update:  ## Update latest gameweeks data
	poetry run python scripts/update_latest_gameweeks.py --gameweeks 1

# Testing targets
test:  ## Run all tests
	poetry run pytest

test-unit:  ## Run unit tests only
	poetry run pytest tests/unit

test-integration:  ## Run integration tests only
	poetry run pytest tests/integration

test-cov:  ## Run tests with coverage report
	poetry run pytest --cov=src --cov-report=html --cov-report=term

# Code quality targets
lint:  ## Run ruff linter
	poetry run ruff check src tests

format:  ## Format code with black
	poetry run black src tests

format-check:  ## Check code formatting without making changes
	poetry run black --check src tests

type-check:  ## Run mypy type checking
	poetry run mypy src

check-all:  ## Run all quality checks (format, lint, type-check, test)
	@echo "Running all quality checks..."
	@echo "1/4 Checking code formatting..."
	@poetry run black --check src tests
	@echo "2/4 Running linter..."
	@poetry run ruff check src tests
	@echo "3/4 Running type checker..."
	@poetry run mypy src || true
	@echo "4/4 Running tests..."
	@poetry run pytest
	@echo "All checks complete!"

# Pre-commit targets
pre-commit-install:  ## Install pre-commit hooks
	poetry run pre-commit install

pre-commit-run:  ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# Utility targets
clean:  ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "Cleaned temporary files and caches"
