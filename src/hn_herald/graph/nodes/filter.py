"""Filter articles node.

This node removes articles without extractable content before summarization,
reducing LLM costs and improving digest quality.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hn_herald.models.article import ExtractionStatus

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


def filter_articles(state: HNState) -> dict[str, Any]:
    """Filter articles to only those with content.

    Removes articles with:
    - No content and no hn_text
    - FAILED, SKIPPED, or NO_URL status
    - Empty content after extraction

    This reduces LLM costs by only summarizing valid content.

    Args:
        state: Current graph state containing articles.

    Returns:
        State update dict with filtered_articles list.
    """
    articles = state["articles"]

    logger.info("filter_articles: Filtering %d articles", len(articles))

    # Filter to articles with content and success status
    filtered = [
        article
        for article in articles
        if article.has_content and article.status == ExtractionStatus.SUCCESS
    ]

    # Log filtering results
    removed = len(articles) - len(filtered)
    logger.info(
        "filter_articles: %d → %d articles (removed %d)", len(articles), len(filtered), removed
    )

    # Log breakdown of removed articles by status
    if removed > 0:
        status_counts: dict[str, int] = {}
        for article in articles:
            if not (article.has_content and article.status == ExtractionStatus.SUCCESS):
                status_counts[article.status.value] = status_counts.get(article.status.value, 0) + 1

        logger.debug("filter_articles: Removed by status: %s", status_counts)

    return {
        "filtered_articles": filtered,
    }
