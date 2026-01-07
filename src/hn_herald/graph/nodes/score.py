"""Score articles node.

This node calculates relevance scores using tag-based matching against
user interests, producing personalized article rankings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hn_herald.services.scoring import ScoringService

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


def score_articles(state: HNState) -> dict[str, Any]:
    """Score articles using tag-based relevance matching.

    Pure computation - no external calls, never fails.
    Filters articles below min_score threshold.

    Args:
        state: Current graph state containing summarized_articles and profile.

    Returns:
        State update dict with scored_articles list.
    """
    summarized = state["summarized_articles"]
    profile = state["profile"]

    if not summarized:
        logger.warning("score_articles: No articles to score")
        return {
            "scored_articles": [],
        }

    logger.info("score_articles: Scoring %d articles", len(summarized))

    # Score and filter using ScoringService
    scoring_service = ScoringService(profile)
    scored = scoring_service.score_articles(
        summarized,
        filter_below_min=True,
    )

    # Log scoring results
    removed = len(summarized) - len(scored)
    logger.info(
        "score_articles: %d → %d articles (removed %d below min_score=%.2f)",
        len(summarized),
        len(scored),
        removed,
        profile.min_score,
    )

    if scored:
        # Log score distribution
        avg_final = sum(a.final_score for a in scored) / len(scored)
        max_final = max(a.final_score for a in scored)
        min_final = min(a.final_score for a in scored)

        logger.info(
            "score_articles: Score distribution - avg=%.3f, min=%.3f, max=%.3f",
            avg_final,
            min_final,
            max_final,
        )

    return {
        "scored_articles": scored,
    }
