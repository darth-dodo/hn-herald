"""Scoring data models for relevance-based article ranking.

This module defines the Pydantic models for relevance scoring, including
RelevanceScore for tag matching results and ScoredArticle for combining
articles with their computed scores.
"""

from pydantic import BaseModel, Field, computed_field

from hn_herald.models.summary import SummarizedArticle


class RelevanceScore(BaseModel):
    """Relevance score calculation result.

    Contains the computed relevance score and explanation of why the
    article matched (or did not match) user interests. Tracks which
    interest and disinterest tags were found in the article.

    Attributes:
        score: Relevance score from 0 (irrelevant) to 1 (highly relevant).
        reason: Human-readable explanation of the score.
        matched_interest_tags: Interest tags found in article.
        matched_disinterest_tags: Disinterest tags found in article.

    Example:
        >>> relevance = RelevanceScore(
        ...     score=0.8,
        ...     reason="Matches interests: python, ai",
        ...     matched_interest_tags=["python", "ai"],
        ...     matched_disinterest_tags=[],
        ... )
        >>> relevance.score
        0.8
        >>> relevance.has_interest_matches
        True
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
    }

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score from 0 to 1",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation of the score",
    )
    matched_interest_tags: list[str] = Field(
        default_factory=list,
        description="Interest tags found in article",
    )
    matched_disinterest_tags: list[str] = Field(
        default_factory=list,
        description="Disinterest tags found in article",
    )

    @property
    def has_interest_matches(self) -> bool:
        """Check if any interest tags matched.

        Returns:
            True if at least one interest tag was found in the article.
        """
        return len(self.matched_interest_tags) > 0

    @property
    def has_disinterest_matches(self) -> bool:
        """Check if any disinterest tags matched.

        Returns:
            True if at least one disinterest tag was found in the article.
        """
        return len(self.matched_disinterest_tags) > 0


class ScoredArticle(BaseModel):
    """Article with relevance and final scores.

    Wraps a SummarizedArticle with scoring information for personalized
    ranking in the digest. Combines relevance score (tag matching) with
    normalized HN popularity for a composite final score.

    Attributes:
        article: The SummarizedArticle from MVP-3.
        relevance: Relevance score details including matched tags.
        popularity_score: Normalized HN popularity (0-1).
        final_score: Composite score (70% relevance + 30% popularity).

    Example:
        >>> # Assuming summarized_article and relevance are defined
        >>> scored = ScoredArticle(
        ...     article=summarized_article,
        ...     relevance=relevance,
        ...     popularity_score=0.6,
        ...     final_score=0.74,
        ... )
        >>> scored.final_score
        0.74
        >>> scored.is_filtered(min_score=0.5)
        False
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
    }

    article: SummarizedArticle = Field(
        ...,
        description="The SummarizedArticle from MVP-3",
    )
    relevance: RelevanceScore = Field(
        ...,
        description="Relevance score details",
    )
    popularity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized HN popularity score (0-1)",
    )
    final_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite final score (70% relevance + 30% popularity)",
    )

    def is_filtered(self, min_score: float = 0.0) -> bool:
        """Check if article should be filtered based on score threshold.

        Args:
            min_score: Minimum score threshold (0-1). Articles below
                this threshold should be filtered out.

        Returns:
            True if final_score is below the minimum threshold.
        """
        return self.final_score < min_score

    @computed_field  # type: ignore[prop-decorator]
    @property
    def story_id(self) -> int:
        """Get the story ID for convenience.

        Returns:
            The HN story ID from the underlying article.
        """
        return self.article.article.story_id

    @computed_field  # type: ignore[prop-decorator]
    @property
    def title(self) -> str:
        """Get the article title for convenience.

        Returns:
            The article title from the underlying article.
        """
        return self.article.article.title

    @computed_field  # type: ignore[prop-decorator]
    @property
    def relevance_score(self) -> float:
        """Get the relevance score for convenience.

        Returns:
            The relevance score (0-1) from the RelevanceScore object.
        """
        return self.relevance.score

    @computed_field  # type: ignore[prop-decorator]
    @property
    def relevance_reason(self) -> str:
        """Get the relevance reason for convenience.

        Returns:
            Human-readable explanation of the relevance score.
        """
        return self.relevance.reason
