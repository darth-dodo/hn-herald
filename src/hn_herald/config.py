"""Configuration management using Pydantic Settings.

Follows 12-factor app principles with environment-based configuration.
All settings can be overridden via environment variables with HN_HERALD_ prefix.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables are prefixed with HN_HERALD_ except for
    API keys which use their standard names.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required API Keys (no prefix for standard naming)
    anthropic_api_key: str

    # Application Settings
    env: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM Settings
    llm_model: str = "claude-3-5-haiku-20241022"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 8192  # Increased for batch summarization (5 articles ~1500 tokens each)

    # LangSmith Settings (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "hn-herald"

    # Caching Settings
    llm_cache_type: Literal["sqlite", "memory", "none"] = "sqlite"
    llm_cache_ttl: int = 86400  # 24 hours in seconds
    cache_dir: str = ".cache"

    # HN API Fetching Settings
    hn_api_base_url: str = "https://hacker-news.firebaseio.com/v0"
    hn_api_timeout: int = 30

    # Article Fetching Settings
    article_fetch_timeout: int = 15
    max_content_length: int = 8000
    loader_timeout: int = 15
    loader_max_content: int = 50000

    # Performance Settings
    max_concurrent_fetches: int = 10
    summary_batch_size: int = 5

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"

    @property
    def cache_database_path(self) -> str:
        """Path to SQLite cache database."""
        return f"{self.cache_dir}/llm_cache.db"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Uses lru_cache to ensure settings are only loaded once.

    Returns:
        Settings instance with values from environment.

    Raises:
        ValidationError: If required settings (like anthropic_api_key) are missing.
    """
    return Settings()
