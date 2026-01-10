"""FastAPI application entry point.

Provides the main application instance with HTMX integration,
health checks, and template rendering.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from hn_herald import __version__
from hn_herald.api.routes import router as api_router
from hn_herald.config import get_settings

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Path configuration
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting HN Herald v{__version__} in {settings.env} mode")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Cache Type: {settings.llm_cache_type}")

    # Create cache directory if using SQLite cache
    # NOTE: Directory is created but LLMService does not implement caching yet
    if settings.llm_cache_type == "sqlite":
        cache_dir = Path(settings.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Cache directory: {cache_dir.absolute()}")

    yield

    # Shutdown
    logger.info("Shutting down HN Herald")


# Create FastAPI application
app = FastAPI(
    title="HN Herald",
    description="AI-powered HackerNews digest generator",
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.is_development else None,
    redoc_url="/api/redoc" if settings.is_development else None,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates if directory exists
templates: Jinja2Templates | None = None
if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Register API router
app.include_router(api_router)


@app.get("/")
async def root(request: Request) -> Response:
    """Root endpoint - serves the main web interface.

    Returns:
        HTML template with predefined tags and configuration.
    """
    if templates and (TEMPLATES_DIR / "index.html").exists():
        # Predefined tag categories for tag selector
        predefined_tags = {
            "Development": ["python", "javascript", "rust", "go", "typescript"],
            "AI/ML": ["ai", "machine-learning", "llm", "deep-learning", "nlp"],
            "Business": ["startups", "investing", "product", "engineering-management"],
        }

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "predefined_tags": predefined_tags,
            },
        )

    return JSONResponse(
        content={
            "message": "Welcome to HN Herald",
            "version": __version__,
            "docs": "/api/docs" if settings.is_development else None,
        }
    )
