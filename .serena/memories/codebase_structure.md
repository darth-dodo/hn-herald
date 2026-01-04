# HN Herald - Codebase Structure

## Project Root
```
hn-herald/
├── src/hn_herald/        # Main package
├── tests/                # Test files
├── docs/                 # Documentation
│   ├── product.md        # PRD
│   └── architecture.md   # Technical design
├── pyproject.toml        # Dependencies & config
├── Makefile              # Dev commands
├── Dockerfile            # Container build
├── .env.example          # Environment template
├── .pre-commit-config.yaml
├── tasks.md              # Task tracking (source of truth)
└── README.md
```

## Source Package (src/hn_herald/)
```
src/hn_herald/
├── __init__.py           # Package with version
├── main.py               # FastAPI app entry, health endpoint
├── config.py             # Pydantic Settings class
│
├── api/                  # HTTP endpoints (to be implemented)
│   └── __init__.py
│
├── models/               # Pydantic models (to be implemented)
│   └── __init__.py       # UserProfile, Story, Article, Digest
│
├── services/             # External service clients (to be implemented)
│   └── __init__.py       # hn_client.py, llm.py, loader.py
│
├── graph/                # LangGraph pipeline (to be implemented)
│   ├── __init__.py
│   └── nodes/            # Pipeline nodes
│       └── __init__.py   # fetcher, extractor, summarizer, etc.
│
├── callbacks/            # LangChain callbacks (to be implemented)
│   └── __init__.py       # HTMX progress callbacks
│
├── templates/            # Jinja2 templates (to be created)
│
└── static/               # Static assets (to be created)
```

## Tests
```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures
├── test_api.py           # Health endpoint tests (8 tests)
├── test_graph/           # (to be created)
├── test_services/        # (to be created)
└── test_models/          # (to be created)
```

## Key Files

### Entry Points
- `src/hn_herald/main.py` - FastAPI app with `/api/health` endpoint
- `src/hn_herald/config.py` - Settings from environment variables

### Configuration
- `pyproject.toml` - All Python config (deps, ruff, pytest, mypy, coverage)
- `.env.example` - Environment variable template
- `.pre-commit-config.yaml` - Pre-commit hooks

### Documentation
- `docs/product.md` - User stories, features, roadmap
- `docs/architecture.md` - Technical design, data models, LangGraph pipeline
- `tasks.md` - Current project state and task tracking
