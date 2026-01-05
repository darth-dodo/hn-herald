"""LangGraph state definition for HN Herald digest generation pipeline."""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

# These imports are needed at runtime for TypedDict, not just type-checking
from hn_herald.models.article import Article  # noqa: TC001
from hn_herald.models.profile import UserProfile  # noqa: TC001
from hn_herald.models.scoring import ScoredArticle  # noqa: TC001
from hn_herald.models.story import Story  # noqa: TC001
from hn_herald.models.summary import SummarizedArticle  # noqa: TC001


class HNState(TypedDict):
    """State for HN Herald digest generation pipeline.

    State flows through progressive refinement stages:
    1. UserProfile input
    2. Stories fetched from HN API
    3. Articles extracted in parallel (with Send pattern)
    4. Filtered articles (content required)
    5. Summarized articles (LLM batch processing)
    6. Scored articles (relevance + popularity)
    7. Ranked articles (sorted by final_score)
    8. Digest output (limited to max_articles)

    Errors are accumulated throughout execution for observability.

    Attributes:
        profile: User preferences for personalization.
        stories: HN stories fetched from API.
        articles: Articles extracted in parallel (Send pattern with add reducer).
        filtered_articles: Articles with valid content.
        summarized_articles: Articles with LLM-generated summaries.
        scored_articles: Articles with relevance and popularity scores.
        ranked_articles: Articles sorted by final_score descending.
        digest: Final digest output (serialized dict).
        errors: Accumulated errors from all nodes.
        start_time: Pipeline start timestamp (Unix time).
    """

    # Input
    profile: UserProfile

    # Pipeline stages (progressive refinement)
    stories: list[Story]
    articles: Annotated[list[Article], add]  # Parallel append via Send
    filtered_articles: list[Article]
    summarized_articles: list[SummarizedArticle]
    scored_articles: list[ScoredArticle]
    ranked_articles: list[ScoredArticle]

    # Output
    digest: dict[str, Any]  # Digest model serialized to dict

    # Metadata
    errors: Annotated[list[str], add]  # Accumulated errors
    start_time: float  # Unix timestamp
