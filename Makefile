# =============================================================================
# HN Herald - Development Makefile
# =============================================================================
# Package Manager: uv (https://github.com/astral-sh/uv)
# =============================================================================

.PHONY: all install dev test test-cov lint format typecheck clean css build docker-build docker-run help

# Default target
all: install lint typecheck test

# =============================================================================
# Dependency Management
# =============================================================================

## Install all dependencies using uv
install:
	uv sync

# =============================================================================
# Development
# =============================================================================

## Run development server with hot reload
dev:
	uv run uvicorn hn_herald.main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# Testing
# =============================================================================

## Run all tests
test:
	uv run pytest

## Run tests with coverage report
test-cov:
	uv run pytest --cov=src/hn_herald --cov-report=term-missing

# =============================================================================
# Code Quality
# =============================================================================

## Run linter (ruff check)
lint:
	uv run ruff check src/ tests/

## Format code (ruff format)
format:
	uv run ruff format src/ tests/

## Run type checker (mypy)
typecheck:
	uv run mypy src/

# =============================================================================
# Build
# =============================================================================

## Build CSS with Tailwind (for future use)
css:
	npx tailwindcss -i ./src/hn_herald/static/input.css -o ./src/hn_herald/static/output.css --minify

## Build Python package
build:
	uv build

# =============================================================================
# Docker
# =============================================================================

## Build Docker image
docker-build:
	docker build -t hn-herald .

## Run Docker container
docker-run:
	docker run -p 8000:8000 hn-herald

# =============================================================================
# Cleanup
# =============================================================================

## Remove build artifacts and cache directories
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true

# =============================================================================
# Help
# =============================================================================

## Show this help message
help:
	@echo "HN Herald - Available targets:"
	@echo ""
	@echo "  install      Install all dependencies using uv"
	@echo "  dev          Run development server with hot reload"
	@echo "  test         Run all tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run linter (ruff check)"
	@echo "  format       Format code (ruff format)"
	@echo "  typecheck    Run type checker (mypy)"
	@echo "  clean        Remove build artifacts and cache directories"
	@echo "  css          Build CSS with Tailwind"
	@echo "  build        Build Python package"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"
	@echo "  all          Run install, lint, typecheck, and test"
	@echo "  help         Show this help message"
