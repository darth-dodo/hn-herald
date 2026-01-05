"""Fetch article content node.

This node extracts article content from story URLs in parallel using the Send pattern.
Handles partial failures gracefully by creating error articles for failed extractions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.services.loader import ArticleLoader

if TYPE_CHECKING:
    from hn_herald.models.story import Story

logger = logging.getLogger(__name__)


async def fetch_article(state: dict[str, Any]) -> dict[str, Any]:
    """Extract article content from story URL.

    This node is a Send target, receiving individual stories to process in parallel.
    Results are appended to the articles list using the add reducer.

    Args:
        state: Send state containing:
            - story: Story to extract
            - profile: UserProfile (unused but passed for consistency)

    Returns:
        State update dict with:
            - articles: List containing the extracted Article
            - errors: List containing error message if extraction failed
    """
    story: Story = state["story"]

    logger.debug("fetch_article: Extracting article %d: %s", story.id, story.title)

    try:
        # Use ArticleLoader context manager
        async with ArticleLoader() as loader:
            article = await loader.extract_article(story)

        # Log extraction result
        if article.status == ExtractionStatus.SUCCESS:
            logger.debug(
                "fetch_article: Success for article %d (%d words)",
                story.id,
                article.word_count,
            )
        else:
            logger.debug("fetch_article: Article %d status=%s", story.id, article.status.value)

        return {
            "articles": [article],
        }

    except Exception as e:
        logger.error("fetch_article: Failed to extract article %d: %s", story.id, e)

        # Create Article with error status
        # This enables partial failure tolerance - pipeline continues
        error_article = Article(
            story_id=story.id,
            title=story.title,
            url=story.url,
            hn_url=story.hn_url,
            hn_score=story.score,
            hn_comments=story.descendants or 0,
            author=story.by,
            status=ExtractionStatus.FAILED,
            error_message=str(e),
        )

        return {
            "articles": [error_article],
            "errors": [f"Article {story.id} ({story.title}): {e}"],
        }
