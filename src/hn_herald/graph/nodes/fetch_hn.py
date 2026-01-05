"""Fetch HN stories node.

This node fetches top stories from HackerNews and emits Send objects
for parallel article extraction.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from hn_herald.services.hn_client import HNClient

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


async def fetch_hn(state: HNState) -> dict[str, Any]:
    """Fetch HN stories for parallel article extraction.

    This node fetches stories from the HackerNews API based on user preferences.
    Parallel article extraction is handled by a conditional edge that creates
    Send objects for each story.

    Args:
        state: Current graph state containing user profile.

    Returns:
        State update dict with stories and start_time.

    Raises:
        HNClientError: If HN API is unavailable (critical failure).
    """
    profile = state["profile"]
    start_time = time.time()

    logger.info(
        "fetch_hn: Fetching stories (type=%s, count=%d, min_score=%d)",
        profile.fetch_type.value,
        profile.fetch_count,
        profile.min_score,
    )

    # Fetch stories from HN API
    async with HNClient() as client:
        stories = await client.fetch_stories(
            story_type=profile.fetch_type,
            limit=profile.fetch_count,
            min_score=int(profile.min_score),
        )

    if not stories:
        logger.warning("fetch_hn: No stories found from HN API")
        return {
            "stories": [],
            "errors": ["No stories found from HN API"],
            "start_time": start_time,
        }

    logger.info("fetch_hn: Fetched %d stories", len(stories))

    # Return state updates
    # Parallel article extraction is handled by conditional edge with Send pattern
    return {
        "stories": stories,
        "start_time": start_time,
    }
