"""Rank articles node.

This node sorts scored articles by final_score in descending order
to prioritize the most relevant content.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


def rank_articles(state: HNState) -> dict[str, Any]:
    """Sort articles by final_score descending.

    Simple sorting operation - never fails.

    Args:
        state: Current graph state containing scored_articles.

    Returns:
        State update dict with ranked_articles list sorted by final_score.
    """
    scored = state["scored_articles"]

    logger.info("rank_articles: Ranking %d articles", len(scored))

    # Sort by final_score descending
    ranked = sorted(scored, key=lambda x: x.final_score, reverse=True)

    # Log top articles for debugging
    if ranked:
        logger.debug(
            "rank_articles: Top article - '%s' (score=%.3f)",
            ranked[0].title,
            ranked[0].final_score,
        )

        if len(ranked) > 1:
            logger.debug(
                "rank_articles: Score range: %.3f to %.3f",
                ranked[0].final_score,
                ranked[-1].final_score,
            )

    return {
        "ranked_articles": ranked,
    }
