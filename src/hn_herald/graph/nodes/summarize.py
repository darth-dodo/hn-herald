"""Summarize articles node.

This node batch summarizes articles using the LLM service for efficiency.
Individual article failures are isolated and marked with error status.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hn_herald.services.llm import LLMService

if TYPE_CHECKING:
    from hn_herald.graph.state import HNState

logger = logging.getLogger(__name__)


async def summarize(state: HNState) -> dict[str, Any]:
    """Batch summarize articles using LLM service.

    Uses batch summarization for efficiency (single LLM call).
    Individual article failures are isolated and marked with error status.

    Args:
        state: Current graph state containing filtered_articles.

    Returns:
        State update dict with:
            - summarized_articles: List of SummarizedArticle objects
            - errors: List of error messages for failed summarizations
    """
    articles = state["filtered_articles"]

    if not articles:
        logger.warning("summarize: No articles to summarize after filtering")
        return {
            "summarized_articles": [],
            "errors": ["No articles to summarize after filtering"],
        }

    logger.info("summarize: Batch summarizing %d articles", len(articles))

    # Batch summarize using LLM service
    llm_service = LLMService()
    summarized = llm_service.summarize_articles_batch(articles)

    # Collect errors from failed summarizations
    errors = [
        f"Article {s.article.story_id} ({s.article.title}): {s.error_message}"
        for s in summarized
        if s.error_message is not None
    ]

    # Log results
    successful = sum(1 for s in summarized if s.has_summary)
    failed = len(errors)

    logger.info(
        "summarize: Completed batch summarization (%d successful, %d failed)",
        successful,
        failed,
    )

    if failed > 0:
        logger.warning("summarize: %d articles failed summarization", failed)

    return {
        "summarized_articles": summarized,
        "errors": errors,
    }
