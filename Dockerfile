# HN Herald Production Dockerfile
#
# A simple, single-stage Dockerfile for the HN Herald FastAPI application.
# Uses Python 3.12-slim base with uv for fast dependency management.
#
# Build:   docker build -t hn-herald .
# Run:     docker run -p 8000:8000 --env-file .env hn-herald
#
# Railway Deployment:
#   Railway automatically builds and deploys using this Dockerfile.
#   Set ANTHROPIC_API_KEY in the Railway dashboard.
#
# Required environment variables:
#   - ANTHROPIC_API_KEY: API key for Claude LLM access
#
# Optional environment variables (see docs/architecture.md for full list):
#   - HN_HERALD_ENV: development|production (default: development)
#   - HN_HERALD_LOG_LEVEL: INFO|DEBUG|WARNING|ERROR (default: INFO)

FROM python:3.12-slim

# Copy uv from the official image for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy all necessary files for installation
COPY pyproject.toml .
COPY uv.lock* .
COPY README.md .
COPY src/ src/

# Create venv and install the package (production dependencies only)
# Using --system to install into the container's Python environment
RUN uv pip install --system .

# Expose the application port
EXPOSE 8000

# Run the FastAPI application with uvicorn
# --host 0.0.0.0 allows connections from outside the container
# Railway sets PORT env var; default to 8000 if not set
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["exec uvicorn hn_herald.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
