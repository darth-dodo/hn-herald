# HN Herald - Code Style & Conventions

## Python Version
- Python 3.12+

## Formatting & Linting
- **Formatter**: Ruff (configured in pyproject.toml)
- **Linter**: Ruff with extensive rule set
- **Type Checker**: MyPy (strict mode)
- **Line Length**: 100 characters

## Naming Conventions
- **Files**: snake_case (e.g., `hn_client.py`, `user_profile.py`)
- **Classes**: PascalCase (e.g., `UserProfile`, `HNClient`)
- **Functions**: snake_case (e.g., `fetch_stories`, `generate_digest`)
- **Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE

## Type Hints
- **Required**: All function signatures must have type hints
- **Pydantic Models**: Use for data validation
- **MyPy**: Strict mode enabled, no implicit Any

## Docstrings
- **Style**: Google docstring convention
- **Required for**: Public functions, classes, modules
- **Not required for**: `__init__`, test files, private methods

## Import Style
```python
# Standard library
from typing import Literal

# Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# Local
from hn_herald.config import settings
```

## Code Organization
```
src/hn_herald/
├── api/           # HTTP endpoints
├── callbacks/     # LangChain callbacks
├── graph/         # LangGraph pipeline
│   └── nodes/     # Pipeline nodes
├── models/        # Pydantic models
├── services/      # External service clients
├── templates/     # Jinja2 templates
├── static/        # Static assets (CSS, JS)
├── config.py      # Pydantic Settings
└── main.py        # FastAPI app entry
```

## Pydantic Models
```python
class UserProfile(BaseModel):
    """User profile with interests and settings."""

    interest_tags: list[str] = []
    min_score: int = 20
    max_articles: int = 10
```

## FastAPI Patterns
- Use dependency injection for shared resources
- Use Response models for API endpoints
- Use background tasks for long operations

## Async Patterns
- Prefer `async def` for I/O operations
- Use `httpx.AsyncClient` for HTTP requests
- Use `asyncio.gather` for parallel operations

## Testing Patterns
- Test files: `tests/test_*.py`
- Use pytest fixtures in `conftest.py`
- Mock external services with `respx` or `pytest-httpx`
- Async tests: Use `pytest-asyncio`
