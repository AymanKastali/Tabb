.DEFAULT_GOAL := help

.PHONY: help setup sync lint format type-check test test-cov security check clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: sync ## Set up the full dev environment
	uv run pre-commit install

sync: ## Sync all dependencies
	uv sync --all-groups

lint: ## Run ruff linter
	uv run ruff check src/ tests/

format: ## Auto-format code with ruff
	uv run ruff format src/ tests/

type-check: ## Run mypy type checker
	uv run mypy src/

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=term-missing

security: ## Run bandit security scan
	uv run bandit -c pyproject.toml -r src/

check: lint type-check security test ## Run all checks (lint + types + security + tests)

clean: ## Remove build artifacts and caches
	rm -rf dist/ build/ .ruff_cache/ .pytest_cache/ .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
