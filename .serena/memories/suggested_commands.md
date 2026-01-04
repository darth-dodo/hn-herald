# HN Herald - Suggested Commands

## Development Commands (Makefile)

### Setup & Installation
```bash
make install          # Install all dependencies using uv
```

### Development
```bash
make dev              # Run development server with hot reload (port 8000)
```

### Testing
```bash
make test             # Run all tests
make test-cov         # Run tests with coverage report
uv run pytest         # Run pytest directly
uv run pytest -v      # Run pytest with verbose output
uv run pytest -k "test_name"  # Run specific test
```

### Code Quality
```bash
make lint             # Run ruff linter
make format           # Format code with ruff
make typecheck        # Run mypy type checker
make all              # Run install, lint, typecheck, and test
```

### Build & Docker
```bash
make build            # Build Python package
make docker-build     # Build Docker image
make docker-run       # Run Docker container
make css              # Build Tailwind CSS (when frontend is added)
```

### Cleanup
```bash
make clean            # Remove build artifacts and cache directories
```

## Git Workflow
```bash
git status && git branch           # Check current state
git checkout -b feature/<name>     # Create feature branch
git add . && git commit -m "..."   # Commit changes
git push origin feature/<name>     # Push to remote
```

## Pre-commit Hooks
```bash
pre-commit install           # Install hooks (run once after clone)
pre-commit run --all-files   # Run all hooks manually
```

## UV Package Manager
```bash
uv sync                # Sync dependencies from pyproject.toml
uv add <package>       # Add a new dependency
uv run <command>       # Run command in virtual environment
```

## System Utilities (Darwin/macOS)
```bash
ls -la                 # List files with details
find . -name "*.py"    # Find Python files
grep -r "pattern" .    # Search for pattern in files
```
