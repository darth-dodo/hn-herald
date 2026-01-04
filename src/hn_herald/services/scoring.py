"""Scoring service for article relevance and ranking.

This service calculates personalized scores for articles based on user
interest tags and HN popularity, producing ranked lists for digest display.

Pure computation - no external API calls required.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hn_herald.models.profile import UserProfile
    from hn_herald.models.summary import SummarizedArticle

from hn_herald.models.scoring import RelevanceScore, ScoredArticle

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for calculating article relevance and ranking.

    Scores articles based on user interest/disinterest tags and HN
    popularity, producing a ranked list for digest display.

    The scoring algorithm:
    - Matches article tech_tags against user interest/disinterest tags
    - Calculates relevance score (0-1) based on tag matches
    - Normalizes HN popularity score to 0-1 range
    - Computes composite final_score: 70% relevance + 30% popularity

    Usage:
        service = ScoringService(user_profile)
        scored_articles = service.score_articles(summarized_articles)

    Attributes:
        profile: User preferences for scoring.
        relevance_weight: Weight for relevance in final score (default 0.7).
        popularity_weight: Weight for popularity in final score (default 0.3).
    """

    # Weights for composite score
    RELEVANCE_WEIGHT: float = 0.7
    POPULARITY_WEIGHT: float = 0.3

    # Default score for articles with no tag matches
    NEUTRAL_SCORE: float = 0.5

    # Score for articles matching disinterest tags
    DISINTEREST_PENALTY_SCORE: float = 0.1

    # HN score normalization parameters
    MAX_HN_SCORE: int = 500  # Scores above this are capped at 1.0

    def __init__(
        self,
        profile: UserProfile,
        relevance_weight: float | None = None,
        popularity_weight: float | None = None,
    ) -> None:
        """Initialize scoring service.

        Args:
            profile: User preferences for scoring.
            relevance_weight: Weight for relevance (0-1). Defaults to 0.7.
            popularity_weight: Weight for popularity (0-1). Defaults to 0.3.

        Raises:
            ValueError: If weights are negative or sum > 1.
        """
        self.profile = profile
        self.relevance_weight = (
            relevance_weight if relevance_weight is not None else self.RELEVANCE_WEIGHT
        )
        self.popularity_weight = (
            popularity_weight if popularity_weight is not None else self.POPULARITY_WEIGHT
        )

        # Validate weights
        if self.relevance_weight < 0 or self.popularity_weight < 0:
            raise ValueError("Weights must be non-negative")
        if self.relevance_weight + self.popularity_weight > 1.0:
            raise ValueError("Sum of weights must not exceed 1.0")

    def score_article(
        self,
        article: SummarizedArticle,
        all_hn_scores: Sequence[int] | None = None,
    ) -> ScoredArticle:
        """Score a single article.

        Calculates relevance based on tag matching and combines with
        normalized HN popularity for a final score.

        Args:
            article: SummarizedArticle to score.
            all_hn_scores: All HN scores in batch for relative normalization.
                If None, uses absolute normalization with MAX_HN_SCORE cap.

        Returns:
            ScoredArticle with relevance and final scores.
        """
        # Get article tech tags (empty list if no summary)
        article_tags = article.display_tags

        # Calculate relevance score
        relevance = self._calculate_relevance(article_tags)

        # Normalize HN popularity
        hn_score = article.article.hn_score
        popularity_score = self._normalize_popularity(hn_score, all_hn_scores)

        # Compute composite final score
        final_score = (
            self.relevance_weight * relevance.score + self.popularity_weight * popularity_score
        )

        logger.debug(
            "Scored article %d: relevance=%.2f, popularity=%.2f, final=%.2f",
            article.article.story_id,
            relevance.score,
            popularity_score,
            final_score,
        )

        return ScoredArticle(
            article=article,
            relevance=relevance,
            popularity_score=popularity_score,
            final_score=final_score,
        )

    def score_articles(
        self,
        articles: Sequence[SummarizedArticle],
        *,
        filter_below_min: bool = True,
    ) -> list[ScoredArticle]:
        """Score and rank multiple articles.

        Scores all articles, optionally filters by min_score, and
        returns sorted by final_score descending.

        Args:
            articles: Sequence of SummarizedArticles to score.
            filter_below_min: If True, exclude articles below profile.min_score.

        Returns:
            List of ScoredArticles sorted by final_score descending.
        """
        if not articles:
            return []

        # Collect all HN scores for relative normalization
        all_hn_scores = [a.article.hn_score for a in articles]

        # Score all articles
        scored = [self.score_article(a, all_hn_scores) for a in articles]

        # Filter by minimum score if requested
        if filter_below_min and self.profile.min_score > 0:
            scored = [s for s in scored if not s.is_filtered(self.profile.min_score)]

        # Sort by final score descending
        scored.sort(key=lambda x: x.final_score, reverse=True)

        logger.info(
            "Scored %d articles, %d after filtering (min_score=%.2f)",
            len(articles),
            len(scored),
            self.profile.min_score,
        )

        return scored

    def _calculate_relevance(
        self,
        article_tags: list[str],
    ) -> RelevanceScore:
        """Calculate relevance score from tag matching.

        Algorithm:
        - If disinterest tags match: score = 0.1 (penalized)
        - If interest tags match: score = 0.5 + (match_ratio * 0.5), range 0.5-1.0
        - If no matches: score = 0.5 (neutral)
        - If no tags: score = 0.5 (neutral)

        Args:
            article_tags: Tech tags from article summary.

        Returns:
            RelevanceScore with score, reason, and matched tags.
        """
        # Handle empty tags
        if not article_tags:
            return RelevanceScore(
                score=self.NEUTRAL_SCORE,
                reason="No tags to match",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            )

        # Handle empty profile
        if not self.profile.has_preferences:
            return RelevanceScore(
                score=self.NEUTRAL_SCORE,
                reason="No preferences configured",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            )

        # Normalize article tags for matching
        normalized_tags = {tag.lower() for tag in article_tags}

        # Find matches
        matched_interest = [tag for tag in self.profile.interest_tags if tag in normalized_tags]
        matched_disinterest = [
            tag for tag in self.profile.disinterest_tags if tag in normalized_tags
        ]

        # Calculate score based on matches
        if matched_disinterest:
            # Penalize articles matching disinterest tags
            score = self.DISINTEREST_PENALTY_SCORE
        elif matched_interest:
            # Boost based on proportion of interest tags matched
            match_ratio = len(matched_interest) / len(self.profile.interest_tags)
            # Scale to 0.5-1.0 range
            score = self.NEUTRAL_SCORE + (match_ratio * 0.5)
        else:
            # Neutral score for no matches
            score = self.NEUTRAL_SCORE

        reason = self._generate_reason(matched_interest, matched_disinterest)

        return RelevanceScore(
            score=score,
            reason=reason,
            matched_interest_tags=matched_interest,
            matched_disinterest_tags=matched_disinterest,
        )

    def _normalize_popularity(
        self,
        hn_score: int,
        all_scores: Sequence[int] | None = None,
    ) -> float:
        """Normalize HN score to 0-1 range.

        Uses relative normalization when batch scores provided,
        otherwise uses absolute normalization with MAX_HN_SCORE cap.

        Args:
            hn_score: Article's HN upvote score.
            all_scores: All HN scores in batch for relative normalization.

        Returns:
            Normalized popularity score (0-1).
        """
        if all_scores and len(all_scores) > 1:
            # Relative normalization within batch
            min_score = min(all_scores)
            max_score = max(all_scores)
            if max_score > min_score:
                return (hn_score - min_score) / (max_score - min_score)
            # All same score - return neutral
            return 0.5

        # Absolute normalization using MAX_HN_SCORE cap
        return min(hn_score / self.MAX_HN_SCORE, 1.0)

    def _generate_reason(
        self,
        matched_interest: list[str],
        matched_disinterest: list[str],
    ) -> str:
        """Generate human-readable reason for relevance score.

        Args:
            matched_interest: Interest tags that matched.
            matched_disinterest: Disinterest tags that matched.

        Returns:
            Human-readable explanation string.
        """
        if matched_disinterest:
            tags_str = ", ".join(matched_disinterest)
            return f"Contains avoided topics: {tags_str}"

        if matched_interest:
            tags_str = ", ".join(matched_interest)
            return f"Matches interests: {tags_str}"

        return "No specific interest match"
