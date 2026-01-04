"""Format digest node.

This node creates the final Digest output by limiting articles to max_articles
and computing generation statistics.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from hn_herald.models.digest import Digest, DigestStats

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


def format_digest(state: HNState) -> dict[str, Any]:
    """Create final digest with limited articles and stats.

    Limits output to profile.max_articles and computes generation statistics.

    Args:
        state: Current graph state containing:
            - ranked_articles: Sorted articles
            - profile: User preferences
            - start_time: Pipeline start timestamp
            - stories: Fetched stories
            - filtered_articles: Articles with content
            - errors: Accumulated errors

    Returns:
        State update dict with digest (serialized to dict).
    """
    ranked = state["ranked_articles"]
    profile = state["profile"]
    start_time = state["start_time"]

    logger.info("format_digest: Creating final digest from %d ranked articles", len(ranked))

    # Limit to max_articles
    limited = ranked[: profile.max_articles]

    # Calculate generation time
    generation_time_ms = int((time.time() - start_time) * 1000)

    # Create digest with stats
    digest = Digest(
        articles=limited,
        timestamp=datetime.now(UTC),
        stats=DigestStats(
            fetched=len(state["stories"]),
            filtered=len(state["filtered_articles"]),
            final=len(limited),
            errors=len(state.get("errors", [])),
            generation_time_ms=generation_time_ms,
        ),
    )

    logger.info(
        "format_digest: Generated digest with %d articles "
        "(fetched=%d, filtered=%d, errors=%d, time=%dms)",
        len(limited),
        digest.stats.fetched,
        digest.stats.filtered,
        digest.stats.errors,
        generation_time_ms,
    )

    # Return serialized digest
    return {
        "digest": digest.model_dump(),
    }
