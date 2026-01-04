"""Digest data models.

This module defines the final digest output model that packages ranked articles
with generation statistics for API responses.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, Field

from hn_herald.models.scoring import ScoredArticle  # noqa: TC001


class DigestStats(BaseModel):
    """Statistics about digest generation.

    Tracks the funnel from fetched stories to final articles,
    including error counts and generation time.

    Attributes:
        fetched: Number of stories fetched from HN API.
        filtered: Number of articles with extractable content.
        final: Number of articles in final digest.
        errors: Number of errors encountered during generation.
        generation_time_ms: Total pipeline execution time in milliseconds.
    """

    fetched: int = Field(..., description="Number of stories fetched from HN", ge=0)
    filtered: int = Field(..., description="Number of articles with content", ge=0)
    final: int = Field(..., description="Number of articles in final digest", ge=0)
    errors: int = Field(..., description="Number of errors during generation", ge=0)
    generation_time_ms: int = Field(..., description="Generation time in milliseconds", ge=0)


class Digest(BaseModel):
    """Final personalized digest output.

    Contains ranked articles limited to user's max_articles preference,
    along with generation statistics and timestamp.

    Attributes:
        articles: Ranked and scored articles (limited to max_articles).
        timestamp: UTC timestamp of digest generation.
        stats: Generation statistics and metrics.
    """

    articles: list[ScoredArticle] = Field(..., description="Ranked articles in the digest")
    timestamp: datetime = Field(..., description="Digest generation timestamp (UTC)")
    stats: DigestStats = Field(..., description="Generation statistics")
