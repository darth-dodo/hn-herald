"""Tests for RelevanceScore and ScoredArticle models for relevance-based ranking.

This module tests the scoring Pydantic models including field validation,
property behaviors, computed fields, and the is_filtered method.
"""

import pytest
from pydantic import ValidationError

from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.scoring import RelevanceScore, ScoredArticle
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_article() -> Article:
    """Create a sample Article for testing."""
    return Article(
        story_id=12345,
        title="Python 3.13 Performance Improvements",
        url="https://example.com/python-performance",
        hn_url="https://news.ycombinator.com/item?id=12345",
        hn_score=150,
        hn_comments=42,
        author="testuser",
        content="Article about Python performance improvements...",
        word_count=500,
        status=ExtractionStatus.SUCCESS,
        domain="example.com",
    )


@pytest.fixture
def sample_article_summary() -> ArticleSummary:
    """Create a sample ArticleSummary for testing."""
    return ArticleSummary(
        summary="This article discusses Python 3.13 performance improvements including JIT.",
        key_points=["JIT compiler added", "GIL removal progress", "10% speedup"],
        tech_tags=["python", "performance", "jit"],
    )


@pytest.fixture
def sample_summarized_article(
    sample_article: Article, sample_article_summary: ArticleSummary
) -> SummarizedArticle:
    """Create a sample SummarizedArticle for testing."""
    return SummarizedArticle(
        article=sample_article,
        summary_data=sample_article_summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def sample_relevance_score() -> RelevanceScore:
    """Create a sample RelevanceScore for testing."""
    return RelevanceScore(
        score=0.8,
        reason="Matches interests: python, performance",
        matched_interest_tags=["python", "performance"],
        matched_disinterest_tags=[],
    )


# =============================================================================
# RelevanceScore Model Creation Tests
# =============================================================================


class TestRelevanceScoreCreation:
    """Tests for RelevanceScore model creation and required fields."""

    def test_relevance_score_minimal_creation(self):
        """
        Given: Only required fields (score and reason)
        When: RelevanceScore is created
        Then: Model should be created with default empty tag lists
        """
        # Arrange & Act
        relevance = RelevanceScore(
            score=0.5,
            reason="Average relevance",
        )

        # Assert
        assert relevance.score == 0.5
        assert relevance.reason == "Average relevance"
        assert relevance.matched_interest_tags == []
        assert relevance.matched_disinterest_tags == []

    def test_relevance_score_with_all_fields(self):
        """
        Given: All fields including matched tags
        When: RelevanceScore is created
        Then: All fields should be stored correctly
        """
        # Arrange & Act
        relevance = RelevanceScore(
            score=0.9,
            reason="High relevance due to multiple tag matches",
            matched_interest_tags=["python", "ai", "rust"],
            matched_disinterest_tags=["crypto"],
        )

        # Assert
        assert relevance.score == 0.9
        assert relevance.reason == "High relevance due to multiple tag matches"
        assert relevance.matched_interest_tags == ["python", "ai", "rust"]
        assert relevance.matched_disinterest_tags == ["crypto"]

    def test_relevance_score_with_only_interest_tags(self):
        """
        Given: Score, reason, and only interest tags
        When: RelevanceScore is created
        Then: Interest tags should be set and disinterest tags empty
        """
        # Arrange & Act
        relevance = RelevanceScore(
            score=0.8,
            reason="Matches interests",
            matched_interest_tags=["python", "ai"],
        )

        # Assert
        assert relevance.matched_interest_tags == ["python", "ai"]
        assert relevance.matched_disinterest_tags == []

    def test_relevance_score_with_only_disinterest_tags(self):
        """
        Given: Score, reason, and only disinterest tags
        When: RelevanceScore is created
        Then: Disinterest tags should be set and interest tags empty
        """
        # Arrange & Act
        relevance = RelevanceScore(
            score=0.2,
            reason="Contains disinterest topics",
            matched_disinterest_tags=["crypto", "nft"],
        )

        # Assert
        assert relevance.matched_interest_tags == []
        assert relevance.matched_disinterest_tags == ["crypto", "nft"]


# =============================================================================
# RelevanceScore Field Validation Tests
# =============================================================================


class TestRelevanceScoreFieldValidation:
    """Tests for RelevanceScore field validation and constraints."""

    def test_relevance_score_missing_score_raises(self):
        """
        Given: Missing required score field
        When: RelevanceScore is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RelevanceScore(reason="Test reason")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("score",) for e in errors)

    def test_relevance_score_missing_reason_raises(self):
        """
        Given: Missing required reason field
        When: RelevanceScore is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RelevanceScore(score=0.5)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("reason",) for e in errors)

    @pytest.mark.parametrize(
        "score,should_pass",
        [
            (0.0, True),  # Lower bound
            (1.0, True),  # Upper bound
            (0.5, True),  # Mid-range
            (0.001, True),  # Near lower bound
            (0.999, True),  # Near upper bound
            (-0.1, False),  # Below lower bound
            (-1.0, False),  # Negative
            (1.1, False),  # Above upper bound
            (2.0, False),  # Well above upper bound
        ],
    )
    def test_relevance_score_bounds_validation(self, score: float, *, should_pass: bool):
        """
        Given: Various score values at and around boundaries
        When: RelevanceScore is created
        Then: Should pass or fail validation as expected
        """
        if should_pass:
            # Arrange & Act
            relevance = RelevanceScore(score=score, reason="Test")

            # Assert
            assert relevance.score == score
        else:
            # Arrange & Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                RelevanceScore(score=score, reason="Test")

            errors = exc_info.value.errors()
            assert any(e["loc"] == ("score",) for e in errors)

    def test_relevance_score_zero_is_valid(self):
        """
        Given: Score of exactly 0.0
        When: RelevanceScore is created
        Then: Model should be valid
        """
        # Arrange & Act
        relevance = RelevanceScore(score=0.0, reason="No relevance")

        # Assert
        assert relevance.score == 0.0

    def test_relevance_score_one_is_valid(self):
        """
        Given: Score of exactly 1.0
        When: RelevanceScore is created
        Then: Model should be valid
        """
        # Arrange & Act
        relevance = RelevanceScore(score=1.0, reason="Perfect relevance")

        # Assert
        assert relevance.score == 1.0


# =============================================================================
# RelevanceScore Property Tests
# =============================================================================


class TestRelevanceScoreProperties:
    """Tests for RelevanceScore property behaviors."""

    def test_has_interest_matches_true_with_tags(self):
        """
        Given: RelevanceScore with non-empty matched_interest_tags
        When: has_interest_matches is checked
        Then: Should return True
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.8,
            reason="Matches interests",
            matched_interest_tags=["python"],
        )

        # Act & Assert
        assert relevance.has_interest_matches is True

    def test_has_interest_matches_false_when_empty(self):
        """
        Given: RelevanceScore with empty matched_interest_tags
        When: has_interest_matches is checked
        Then: Should return False
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.5,
            reason="No specific matches",
            matched_interest_tags=[],
        )

        # Act & Assert
        assert relevance.has_interest_matches is False

    def test_has_interest_matches_with_multiple_tags(self):
        """
        Given: RelevanceScore with multiple matched interest tags
        When: has_interest_matches is checked
        Then: Should return True
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.9,
            reason="Multiple matches",
            matched_interest_tags=["python", "ai", "rust", "performance"],
        )

        # Act & Assert
        assert relevance.has_interest_matches is True

    def test_has_disinterest_matches_true_with_tags(self):
        """
        Given: RelevanceScore with non-empty matched_disinterest_tags
        When: has_disinterest_matches is checked
        Then: Should return True
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.3,
            reason="Contains disinterest topic",
            matched_disinterest_tags=["crypto"],
        )

        # Act & Assert
        assert relevance.has_disinterest_matches is True

    def test_has_disinterest_matches_false_when_empty(self):
        """
        Given: RelevanceScore with empty matched_disinterest_tags
        When: has_disinterest_matches is checked
        Then: Should return False
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.8,
            reason="No disinterest matches",
            matched_disinterest_tags=[],
        )

        # Act & Assert
        assert relevance.has_disinterest_matches is False

    def test_both_properties_can_be_true(self):
        """
        Given: RelevanceScore with both interest and disinterest matches
        When: Both properties are checked
        Then: Both should return True
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.5,
            reason="Mixed matches",
            matched_interest_tags=["python"],
            matched_disinterest_tags=["crypto"],
        )

        # Act & Assert
        assert relevance.has_interest_matches is True
        assert relevance.has_disinterest_matches is True

    def test_both_properties_can_be_false(self):
        """
        Given: RelevanceScore with no tag matches
        When: Both properties are checked
        Then: Both should return False
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.5,
            reason="No specific matches",
            matched_interest_tags=[],
            matched_disinterest_tags=[],
        )

        # Act & Assert
        assert relevance.has_interest_matches is False
        assert relevance.has_disinterest_matches is False


# =============================================================================
# RelevanceScore Model Configuration Tests
# =============================================================================


class TestRelevanceScoreModelConfig:
    """Tests for RelevanceScore model configuration."""

    def test_relevance_score_ignores_extra_fields(self):
        """
        Given: Extra unknown fields in input
        When: RelevanceScore is created
        Then: Unknown fields should be ignored
        """
        # Arrange & Act
        relevance = RelevanceScore(
            score=0.5,
            reason="Test",
            unknown_field="should be ignored",
            extra_data=123,
        )

        # Assert
        assert not hasattr(relevance, "unknown_field")
        assert not hasattr(relevance, "extra_data")
        assert relevance.score == 0.5

    def test_relevance_score_is_mutable(self):
        """
        Given: RelevanceScore instance
        When: Fields are modified
        Then: Modifications should succeed (frozen=False)
        """
        # Arrange
        relevance = RelevanceScore(score=0.5, reason="Test")

        # Act
        relevance.score = 0.8
        relevance.reason = "Updated reason"

        # Assert
        assert relevance.score == 0.8
        assert relevance.reason == "Updated reason"

    def test_relevance_score_serialization_to_dict(self):
        """
        Given: RelevanceScore with data
        When: Serialized to dict
        Then: All fields should be present
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.8,
            reason="Test reason",
            matched_interest_tags=["python", "ai"],
            matched_disinterest_tags=["crypto"],
        )

        # Act
        data = relevance.model_dump()

        # Assert
        assert data["score"] == 0.8
        assert data["reason"] == "Test reason"
        assert data["matched_interest_tags"] == ["python", "ai"]
        assert data["matched_disinterest_tags"] == ["crypto"]

    def test_relevance_score_json_serialization(self):
        """
        Given: RelevanceScore with data
        When: Serialized to JSON
        Then: Valid JSON string should be produced
        """
        # Arrange
        relevance = RelevanceScore(
            score=0.8,
            reason="Test reason",
            matched_interest_tags=["python"],
        )

        # Act
        json_str = relevance.model_dump_json()

        # Assert
        assert "0.8" in json_str
        assert "Test reason" in json_str
        assert "python" in json_str


# =============================================================================
# ScoredArticle Model Creation Tests
# =============================================================================


class TestScoredArticleCreation:
    """Tests for ScoredArticle model creation and required fields."""

    def test_scored_article_creation_with_all_fields(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: All required fields for ScoredArticle
        When: ScoredArticle is created
        Then: All fields should be stored correctly
        """
        # Arrange & Act
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.6,
            final_score=0.74,
        )

        # Assert
        assert scored.article == sample_summarized_article
        assert scored.relevance == sample_relevance_score
        assert scored.popularity_score == 0.6
        assert scored.final_score == 0.74

    def test_scored_article_missing_article_raises(self, sample_relevance_score: RelevanceScore):
        """
        Given: Missing required article field
        When: ScoredArticle is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ScoredArticle(
                relevance=sample_relevance_score,
                popularity_score=0.5,
                final_score=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("article",) for e in errors)

    def test_scored_article_missing_relevance_raises(
        self, sample_summarized_article: SummarizedArticle
    ):
        """
        Given: Missing required relevance field
        When: ScoredArticle is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ScoredArticle(
                article=sample_summarized_article,
                popularity_score=0.5,
                final_score=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("relevance",) for e in errors)

    def test_scored_article_missing_popularity_score_raises(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: Missing required popularity_score field
        When: ScoredArticle is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ScoredArticle(
                article=sample_summarized_article,
                relevance=sample_relevance_score,
                final_score=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("popularity_score",) for e in errors)

    def test_scored_article_missing_final_score_raises(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: Missing required final_score field
        When: ScoredArticle is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ScoredArticle(
                article=sample_summarized_article,
                relevance=sample_relevance_score,
                popularity_score=0.5,
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("final_score",) for e in errors)


# =============================================================================
# ScoredArticle Score Bounds Validation Tests
# =============================================================================


class TestScoredArticleScoreBoundsValidation:
    """Tests for ScoredArticle score field bounds validation."""

    @pytest.mark.parametrize(
        "score,should_pass",
        [
            (0.0, True),  # Lower bound
            (1.0, True),  # Upper bound
            (0.5, True),  # Mid-range
            (0.001, True),  # Near lower bound
            (0.999, True),  # Near upper bound
            (-0.1, False),  # Below lower bound
            (1.1, False),  # Above upper bound
        ],
    )
    def test_popularity_score_bounds_validation(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
        score: float,
        *,
        should_pass: bool,
    ):
        """
        Given: Various popularity_score values at and around boundaries
        When: ScoredArticle is created
        Then: Should pass or fail validation as expected
        """
        if should_pass:
            # Arrange & Act
            scored = ScoredArticle(
                article=sample_summarized_article,
                relevance=sample_relevance_score,
                popularity_score=score,
                final_score=0.5,
            )

            # Assert
            assert scored.popularity_score == score
        else:
            # Arrange & Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                ScoredArticle(
                    article=sample_summarized_article,
                    relevance=sample_relevance_score,
                    popularity_score=score,
                    final_score=0.5,
                )

            errors = exc_info.value.errors()
            assert any(e["loc"] == ("popularity_score",) for e in errors)

    @pytest.mark.parametrize(
        "score,should_pass",
        [
            (0.0, True),  # Lower bound
            (1.0, True),  # Upper bound
            (0.5, True),  # Mid-range
            (0.001, True),  # Near lower bound
            (0.999, True),  # Near upper bound
            (-0.1, False),  # Below lower bound
            (1.1, False),  # Above upper bound
        ],
    )
    def test_final_score_bounds_validation(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
        score: float,
        *,
        should_pass: bool,
    ):
        """
        Given: Various final_score values at and around boundaries
        When: ScoredArticle is created
        Then: Should pass or fail validation as expected
        """
        if should_pass:
            # Arrange & Act
            scored = ScoredArticle(
                article=sample_summarized_article,
                relevance=sample_relevance_score,
                popularity_score=0.5,
                final_score=score,
            )

            # Assert
            assert scored.final_score == score
        else:
            # Arrange & Act & Assert
            with pytest.raises(ValidationError) as exc_info:
                ScoredArticle(
                    article=sample_summarized_article,
                    relevance=sample_relevance_score,
                    popularity_score=0.5,
                    final_score=score,
                )

            errors = exc_info.value.errors()
            assert any(e["loc"] == ("final_score",) for e in errors)


# =============================================================================
# ScoredArticle is_filtered Method Tests
# =============================================================================


class TestScoredArticleIsFiltered:
    """Tests for ScoredArticle is_filtered method."""

    def test_is_filtered_returns_true_below_threshold(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with final_score below min_score threshold
        When: is_filtered is called
        Then: Should return True (article should be filtered out)
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.3,
        )

        # Act & Assert
        assert scored.is_filtered(min_score=0.5) is True

    def test_is_filtered_returns_false_above_threshold(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with final_score above min_score threshold
        When: is_filtered is called
        Then: Should return False (article should not be filtered out)
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act & Assert
        assert scored.is_filtered(min_score=0.5) is False

    def test_is_filtered_returns_false_at_threshold(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with final_score equal to min_score threshold
        When: is_filtered is called
        Then: Should return False (article at threshold should not be filtered)
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.5,
        )

        # Act & Assert
        assert scored.is_filtered(min_score=0.5) is False

    def test_is_filtered_default_threshold_zero(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with any positive final_score
        When: is_filtered is called with default threshold (0.0)
        Then: Should return False
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.001,
        )

        # Act & Assert
        assert scored.is_filtered() is False

    def test_is_filtered_with_zero_final_score(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with final_score of 0.0
        When: is_filtered is called with default threshold
        Then: Should return False (0.0 is not less than 0.0)
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.0,
            final_score=0.0,
        )

        # Act & Assert
        assert scored.is_filtered() is False
        assert scored.is_filtered(min_score=0.0) is False

    @pytest.mark.parametrize(
        "final_score,min_score,expected_filtered",
        [
            (0.0, 0.0, False),  # Zero equals threshold
            (0.0, 0.1, True),  # Zero below threshold
            (0.5, 0.5, False),  # Equals threshold
            (0.49, 0.5, True),  # Just below threshold
            (0.51, 0.5, False),  # Just above threshold
            (1.0, 1.0, False),  # Max equals max threshold
            (0.99, 1.0, True),  # Just below max threshold
            (1.0, 0.0, False),  # Max score, min threshold
            (0.001, 0.001, False),  # Near-zero equals threshold
        ],
    )
    def test_is_filtered_various_thresholds(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
        final_score: float,
        min_score: float,
        *,
        expected_filtered: bool,
    ):
        """
        Given: Various combinations of final_score and min_score threshold
        When: is_filtered is called
        Then: Should return expected result based on score comparison
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=final_score,
        )

        # Act & Assert
        assert scored.is_filtered(min_score=min_score) is expected_filtered


# =============================================================================
# ScoredArticle Computed Field Tests
# =============================================================================


class TestScoredArticleComputedFields:
    """Tests for ScoredArticle computed field properties."""

    def test_story_id_returns_article_story_id(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with underlying article
        When: story_id is accessed
        Then: Should return the story_id from the underlying article
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act & Assert
        assert scored.story_id == 12345
        assert scored.story_id == sample_summarized_article.article.story_id

    def test_title_returns_article_title(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with underlying article
        When: title is accessed
        Then: Should return the title from the underlying article
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act & Assert
        assert scored.title == "Python 3.13 Performance Improvements"
        assert scored.title == sample_summarized_article.article.title

    def test_relevance_score_returns_relevance_score_value(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with relevance object
        When: relevance_score is accessed
        Then: Should return the score from the relevance object
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act & Assert
        assert scored.relevance_score == 0.8
        assert scored.relevance_score == sample_relevance_score.score

    def test_relevance_reason_returns_relevance_reason(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with relevance object
        When: relevance_reason is accessed
        Then: Should return the reason from the relevance object
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act & Assert
        assert scored.relevance_reason == "Matches interests: python, performance"
        assert scored.relevance_reason == sample_relevance_score.reason


# =============================================================================
# ScoredArticle Model Configuration Tests
# =============================================================================


class TestScoredArticleModelConfig:
    """Tests for ScoredArticle model configuration."""

    def test_scored_article_ignores_extra_fields(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: Extra unknown fields in input
        When: ScoredArticle is created
        Then: Unknown fields should be ignored
        """
        # Arrange & Act
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
            unknown_field="should be ignored",
            extra_data=123,
        )

        # Assert
        assert not hasattr(scored, "unknown_field")
        assert not hasattr(scored, "extra_data")
        assert scored.final_score == 0.7

    def test_scored_article_is_mutable(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle instance
        When: Fields are modified
        Then: Modifications should succeed (frozen=False)
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act
        scored.final_score = 0.9
        scored.popularity_score = 0.8

        # Assert
        assert scored.final_score == 0.9
        assert scored.popularity_score == 0.8

    def test_scored_article_serialization_to_dict(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with data
        When: Serialized to dict
        Then: All fields including computed fields should be present
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.6,
            final_score=0.74,
        )

        # Act
        data = scored.model_dump()

        # Assert
        assert data["popularity_score"] == 0.6
        assert data["final_score"] == 0.74
        assert "article" in data
        assert "relevance" in data
        # Computed fields should also be present
        assert data["story_id"] == 12345
        assert data["title"] == "Python 3.13 Performance Improvements"
        assert data["relevance_score"] == 0.8
        assert data["relevance_reason"] == "Matches interests: python, performance"

    def test_scored_article_json_serialization(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with data
        When: Serialized to JSON
        Then: Valid JSON string should be produced with computed fields
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.6,
            final_score=0.74,
        )

        # Act
        json_str = scored.model_dump_json()

        # Assert
        assert "0.74" in json_str  # final_score
        assert "0.6" in json_str  # popularity_score
        assert "12345" in json_str  # story_id
        assert "Python 3.13" in json_str  # title


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestScoringEdgeCases:
    """Tests for edge cases in scoring models."""

    def test_relevance_score_with_empty_reason(self):
        """
        Given: Empty string reason
        When: RelevanceScore is created
        Then: Model should be valid with empty reason
        """
        # Arrange & Act
        relevance = RelevanceScore(score=0.5, reason="")

        # Assert
        assert relevance.reason == ""

    def test_relevance_score_with_very_long_reason(self):
        """
        Given: Very long reason string
        When: RelevanceScore is created
        Then: Model should store the long reason
        """
        # Arrange
        long_reason = "A" * 10000

        # Act
        relevance = RelevanceScore(score=0.5, reason=long_reason)

        # Assert
        assert len(relevance.reason) == 10000

    def test_relevance_score_with_many_tags(self):
        """
        Given: Many matched interest and disinterest tags
        When: RelevanceScore is created
        Then: All tags should be stored
        """
        # Arrange
        interest_tags = [f"interest_{i}" for i in range(100)]
        disinterest_tags = [f"disinterest_{i}" for i in range(100)]

        # Act
        relevance = RelevanceScore(
            score=0.5,
            reason="Many tags",
            matched_interest_tags=interest_tags,
            matched_disinterest_tags=disinterest_tags,
        )

        # Assert
        assert len(relevance.matched_interest_tags) == 100
        assert len(relevance.matched_disinterest_tags) == 100

    def test_relevance_score_with_special_characters_in_tags(self):
        """
        Given: Tags with special characters
        When: RelevanceScore is created
        Then: Tags should be preserved as-is
        """
        # Arrange
        tags = ["c++", "c#", ".net", "node.js", "machine-learning"]

        # Act
        relevance = RelevanceScore(
            score=0.5,
            reason="Special chars",
            matched_interest_tags=tags,
        )

        # Assert
        assert relevance.matched_interest_tags == tags

    def test_scored_article_with_zero_scores(
        self,
        sample_summarized_article: SummarizedArticle,
    ):
        """
        Given: All scores at zero
        When: ScoredArticle is created
        Then: Model should be valid with zero scores
        """
        # Arrange
        zero_relevance = RelevanceScore(
            score=0.0,
            reason="No relevance",
        )

        # Act
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=zero_relevance,
            popularity_score=0.0,
            final_score=0.0,
        )

        # Assert
        assert scored.final_score == 0.0
        assert scored.popularity_score == 0.0
        assert scored.relevance_score == 0.0

    def test_scored_article_with_max_scores(
        self,
        sample_summarized_article: SummarizedArticle,
    ):
        """
        Given: All scores at maximum (1.0)
        When: ScoredArticle is created
        Then: Model should be valid with max scores
        """
        # Arrange
        max_relevance = RelevanceScore(
            score=1.0,
            reason="Perfect relevance",
        )

        # Act
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=max_relevance,
            popularity_score=1.0,
            final_score=1.0,
        )

        # Assert
        assert scored.final_score == 1.0
        assert scored.popularity_score == 1.0
        assert scored.relevance_score == 1.0

    def test_relevance_score_with_unicode_tags(self):
        """
        Given: Tags with unicode characters
        When: RelevanceScore is created
        Then: Tags should be preserved
        """
        # Arrange
        tags = ["python", "rust"]

        # Act
        relevance = RelevanceScore(
            score=0.5,
            reason="Unicode test",
            matched_interest_tags=tags,
        )

        # Assert
        assert relevance.matched_interest_tags == tags

    def test_relevance_score_with_unicode_reason(self):
        """
        Given: Reason with unicode characters
        When: RelevanceScore is created
        Then: Reason should be preserved
        """
        # Arrange
        reason = "Matches: Python, Rust"

        # Act
        relevance = RelevanceScore(score=0.5, reason=reason)

        # Assert
        assert relevance.reason == reason


# =============================================================================
# Integration-like Tests
# =============================================================================


class TestScoringModelIntegration:
    """Tests for interactions between RelevanceScore and ScoredArticle."""

    def test_scored_article_reflects_relevance_changes(
        self,
        sample_summarized_article: SummarizedArticle,
        sample_relevance_score: RelevanceScore,
    ):
        """
        Given: ScoredArticle with mutable relevance
        When: Relevance score is modified
        Then: ScoredArticle computed fields should reflect the change
        """
        # Arrange
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=sample_relevance_score,
            popularity_score=0.5,
            final_score=0.7,
        )

        # Act
        sample_relevance_score.score = 0.3
        sample_relevance_score.reason = "Updated reason"

        # Assert
        assert scored.relevance_score == 0.3
        assert scored.relevance_reason == "Updated reason"

    def test_create_scored_article_with_inline_relevance(
        self,
        sample_summarized_article: SummarizedArticle,
    ):
        """
        Given: Creating ScoredArticle with inline RelevanceScore
        When: ScoredArticle is created
        Then: All nested objects should be accessible
        """
        # Arrange & Act
        scored = ScoredArticle(
            article=sample_summarized_article,
            relevance=RelevanceScore(
                score=0.75,
                reason="Good match",
                matched_interest_tags=["python"],
            ),
            popularity_score=0.6,
            final_score=0.7,
        )

        # Assert
        assert scored.relevance_score == 0.75
        assert scored.relevance_reason == "Good match"
        assert scored.relevance.has_interest_matches is True

    def test_multiple_scored_articles_with_same_article(
        self,
        sample_summarized_article: SummarizedArticle,
    ):
        """
        Given: Same summarized article with different relevance scores
        When: Multiple ScoredArticles are created
        Then: Each should maintain independent scores
        """
        # Arrange
        relevance1 = RelevanceScore(score=0.3, reason="Low match")
        relevance2 = RelevanceScore(score=0.9, reason="High match")

        # Act
        scored1 = ScoredArticle(
            article=sample_summarized_article,
            relevance=relevance1,
            popularity_score=0.5,
            final_score=0.35,
        )
        scored2 = ScoredArticle(
            article=sample_summarized_article,
            relevance=relevance2,
            popularity_score=0.5,
            final_score=0.85,
        )

        # Assert
        assert scored1.relevance_score == 0.3
        assert scored2.relevance_score == 0.9
        assert scored1.final_score == 0.35
        assert scored2.final_score == 0.85
        # But they share the same story_id and title
        assert scored1.story_id == scored2.story_id
        assert scored1.title == scored2.title
