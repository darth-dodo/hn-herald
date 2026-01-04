"""Tests for ScoringService for article relevance and ranking.

This module tests the ScoringService including initialization validation,
tag matching algorithms, popularity normalization, composite scoring,
batch scoring operations, and edge cases.
"""

import pytest

from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.profile import UserProfile
from hn_herald.models.summary import ArticleSummary, SummarizationStatus, SummarizedArticle
from hn_herald.services.scoring import ScoringService

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_profile() -> UserProfile:
    """Sample user profile with interest and disinterest tags."""
    return UserProfile(
        interest_tags=["python", "ai", "rust"],
        disinterest_tags=["crypto", "blockchain"],
        min_score=0.0,
    )


@pytest.fixture
def sample_profile_interests_only() -> UserProfile:
    """Sample profile with only interest tags."""
    return UserProfile(
        interest_tags=["python", "ai", "rust"],
        disinterest_tags=[],
        min_score=0.0,
    )


@pytest.fixture
def sample_profile_disinterests_only() -> UserProfile:
    """Sample profile with only disinterest tags."""
    return UserProfile(
        interest_tags=[],
        disinterest_tags=["crypto", "blockchain"],
        min_score=0.0,
    )


@pytest.fixture
def empty_profile() -> UserProfile:
    """Empty profile with no preferences."""
    return UserProfile(
        interest_tags=[],
        disinterest_tags=[],
        min_score=0.0,
    )


@pytest.fixture
def profile_with_min_score() -> UserProfile:
    """Profile with min_score threshold."""
    return UserProfile(
        interest_tags=["python", "ai"],
        disinterest_tags=["crypto"],
        min_score=0.5,
    )


def create_article(
    story_id: int = 1,
    title: str = "Test Article",
    hn_score: int = 100,
    author: str = "testuser",
) -> Article:
    """Helper to create Article instances."""
    return Article(
        story_id=story_id,
        title=title,
        url=f"https://example.com/article-{story_id}",
        hn_url=f"https://news.ycombinator.com/item?id={story_id}",
        hn_score=hn_score,
        hn_comments=50,
        author=author,
        content="Sample article content for testing.",
        word_count=100,
        status=ExtractionStatus.SUCCESS,
    )


def create_summary(
    summary_text: str = "This is a test summary for the article.",
    key_points: list[str] | None = None,
    tech_tags: list[str] | None = None,
) -> ArticleSummary:
    """Helper to create ArticleSummary instances."""
    if key_points is None:
        key_points = ["Key point one"]
    if tech_tags is None:
        tech_tags = []
    return ArticleSummary(
        summary=summary_text,
        key_points=key_points,
        tech_tags=tech_tags,
    )


def create_summarized_article(
    story_id: int = 1,
    title: str = "Test Article",
    hn_score: int = 100,
    tech_tags: list[str] | None = None,
    *,
    has_summary: bool = True,
) -> SummarizedArticle:
    """Helper to create SummarizedArticle instances."""
    article = create_article(
        story_id=story_id,
        title=title,
        hn_score=hn_score,
    )
    if has_summary:
        summary_data = create_summary(tech_tags=tech_tags or [])
        return SummarizedArticle(
            article=article,
            summary=summary_data,
            summarization_status=SummarizationStatus.SUCCESS,
        )
    return SummarizedArticle(
        article=article,
        summary=None,
        summarization_status=SummarizationStatus.NO_CONTENT,
    )


# =============================================================================
# ScoringService Initialization Tests
# =============================================================================


class TestScoringServiceInitialization:
    """Tests for ScoringService initialization and weight validation."""

    def test_initialization_with_default_weights(self, sample_profile):
        """
        Given: A valid UserProfile
        When: ScoringService is created without custom weights
        Then: Default weights (0.7 relevance, 0.3 popularity) should be set
        """
        # Arrange & Act
        service = ScoringService(sample_profile)

        # Assert
        assert service.profile == sample_profile
        assert service.relevance_weight == 0.7
        assert service.popularity_weight == 0.3

    def test_initialization_with_custom_weights(self, sample_profile):
        """
        Given: A valid UserProfile with custom weights
        When: ScoringService is created
        Then: Custom weights should be stored correctly
        """
        # Arrange & Act
        service = ScoringService(
            sample_profile,
            relevance_weight=0.6,
            popularity_weight=0.4,
        )

        # Assert
        assert service.relevance_weight == 0.6
        assert service.popularity_weight == 0.4

    def test_initialization_with_zero_popularity_weight(self, sample_profile):
        """
        Given: A UserProfile with zero popularity weight
        When: ScoringService is created
        Then: Only relevance should contribute to final score
        """
        # Arrange & Act
        service = ScoringService(
            sample_profile,
            relevance_weight=1.0,
            popularity_weight=0.0,
        )

        # Assert
        assert service.relevance_weight == 1.0
        assert service.popularity_weight == 0.0

    def test_initialization_with_zero_relevance_weight(self, sample_profile):
        """
        Given: A UserProfile with zero relevance weight
        When: ScoringService is created
        Then: Only popularity should contribute to final score
        """
        # Arrange & Act
        service = ScoringService(
            sample_profile,
            relevance_weight=0.0,
            popularity_weight=1.0,
        )

        # Assert
        assert service.relevance_weight == 0.0
        assert service.popularity_weight == 1.0

    def test_initialization_raises_on_negative_relevance_weight(self, sample_profile):
        """
        Given: A negative relevance_weight
        When: ScoringService is created
        Then: ValueError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ScoringService(sample_profile, relevance_weight=-0.1)

        assert "non-negative" in str(exc_info.value)

    def test_initialization_raises_on_negative_popularity_weight(self, sample_profile):
        """
        Given: A negative popularity_weight
        When: ScoringService is created
        Then: ValueError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ScoringService(sample_profile, popularity_weight=-0.1)

        assert "non-negative" in str(exc_info.value)

    def test_initialization_raises_on_weights_sum_exceeding_one(self, sample_profile):
        """
        Given: Weights that sum to more than 1.0
        When: ScoringService is created
        Then: ValueError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValueError) as exc_info:
            ScoringService(
                sample_profile,
                relevance_weight=0.7,
                popularity_weight=0.5,
            )

        assert "exceed 1.0" in str(exc_info.value)

    def test_initialization_allows_weights_sum_exactly_one(self, sample_profile):
        """
        Given: Weights that sum to exactly 1.0
        When: ScoringService is created
        Then: Service should be created successfully
        """
        # Arrange & Act
        service = ScoringService(
            sample_profile,
            relevance_weight=0.5,
            popularity_weight=0.5,
        )

        # Assert
        assert service.relevance_weight + service.popularity_weight == 1.0

    def test_initialization_allows_weights_sum_less_than_one(self, sample_profile):
        """
        Given: Weights that sum to less than 1.0
        When: ScoringService is created
        Then: Service should be created successfully
        """
        # Arrange & Act
        service = ScoringService(
            sample_profile,
            relevance_weight=0.3,
            popularity_weight=0.3,
        )

        # Assert
        assert service.relevance_weight + service.popularity_weight == 0.6


# =============================================================================
# Tag Matching Algorithm Tests
# =============================================================================


class TestTagMatchingAlgorithm:
    """Tests for the _calculate_relevance tag matching algorithm."""

    def test_interest_tag_match_single_tag(self, sample_profile):
        """
        Given: Article with one matching interest tag
        When: Relevance is calculated
        Then: Score should be between 0.5 and 1.0 based on match ratio
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["python", "javascript"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        # 1 out of 3 interest tags matched = 0.5 + (1/3 * 0.5) = 0.667
        assert relevance.score == pytest.approx(0.667, abs=0.01)
        assert relevance.matched_interest_tags == ["python"]
        assert relevance.matched_disinterest_tags == []
        assert "python" in relevance.reason

    def test_interest_tag_match_all_tags(self, sample_profile):
        """
        Given: Article with all interest tags matching
        When: Relevance is calculated
        Then: Score should be 1.0
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["python", "ai", "rust", "javascript"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        # All 3 interest tags matched = 0.5 + (3/3 * 0.5) = 1.0
        assert relevance.score == 1.0
        assert set(relevance.matched_interest_tags) == {"python", "ai", "rust"}
        assert relevance.has_interest_matches is True

    def test_interest_tag_match_partial(self, sample_profile):
        """
        Given: Article with partial interest tag matches
        When: Relevance is calculated
        Then: Score should be proportional to match ratio
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["python", "ai"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        # 2 out of 3 interest tags = 0.5 + (2/3 * 0.5) = 0.833
        assert relevance.score == pytest.approx(0.833, abs=0.01)
        assert set(relevance.matched_interest_tags) == {"python", "ai"}

    def test_disinterest_tag_match_penalizes_score(self, sample_profile):
        """
        Given: Article with matching disinterest tag
        When: Relevance is calculated
        Then: Score should be penalized to 0.1
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["python", "crypto"]  # python is interest, crypto is disinterest

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert relevance.score == 0.1
        assert "python" in relevance.matched_interest_tags
        assert "crypto" in relevance.matched_disinterest_tags
        assert relevance.has_disinterest_matches is True
        assert "avoided" in relevance.reason.lower()

    def test_disinterest_tag_overrides_interest_tag(self, sample_profile):
        """
        Given: Article with both interest and disinterest tag matches
        When: Relevance is calculated
        Then: Disinterest should take precedence (penalized score)
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["python", "ai", "rust", "crypto", "blockchain"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert relevance.score == 0.1  # Penalized due to disinterest match
        assert set(relevance.matched_interest_tags) == {"python", "ai", "rust"}
        assert set(relevance.matched_disinterest_tags) == {"crypto", "blockchain"}

    def test_no_tag_matches_returns_neutral_score(self, sample_profile):
        """
        Given: Article with no matching interest or disinterest tags
        When: Relevance is calculated
        Then: Score should be neutral (0.5)
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["javascript", "golang", "kotlin"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert relevance.score == 0.5
        assert relevance.matched_interest_tags == []
        assert relevance.matched_disinterest_tags == []
        assert "no specific interest" in relevance.reason.lower()

    def test_empty_article_tags_returns_neutral_score(self, sample_profile):
        """
        Given: Article with no tags
        When: Relevance is calculated
        Then: Score should be neutral (0.5)
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags: list[str] = []

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert relevance.score == 0.5
        assert "no tags" in relevance.reason.lower()

    def test_no_user_preferences_returns_neutral_score(self, empty_profile):
        """
        Given: Empty user profile with no preferences
        When: Relevance is calculated
        Then: Score should be neutral (0.5)
        """
        # Arrange
        service = ScoringService(empty_profile)
        article_tags = ["python", "ai", "rust"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert relevance.score == 0.5
        assert "no preferences" in relevance.reason.lower()

    def test_case_insensitive_tag_matching(self, sample_profile):
        """
        Given: Article tags with different case than profile tags
        When: Relevance is calculated
        Then: Matching should be case-insensitive
        """
        # Arrange
        service = ScoringService(sample_profile)
        article_tags = ["PYTHON", "AI", "Rust"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        # All 3 tags should match (case-insensitive)
        assert relevance.score == 1.0
        assert len(relevance.matched_interest_tags) == 3


# =============================================================================
# Popularity Normalization Tests
# =============================================================================


class TestPopularityNormalization:
    """Tests for the _normalize_popularity method."""

    def test_relative_normalization_with_batch_scores(self, sample_profile):
        """
        Given: A batch of HN scores
        When: Popularity is normalized
        Then: Score should be relative within the batch (0-1)
        """
        # Arrange
        service = ScoringService(sample_profile)
        all_scores = [50, 100, 200]

        # Act
        low_norm = service._normalize_popularity(50, all_scores)
        mid_norm = service._normalize_popularity(100, all_scores)
        high_norm = service._normalize_popularity(200, all_scores)

        # Assert
        # (50 - 50) / (200 - 50) = 0.0
        assert low_norm == 0.0
        # (100 - 50) / (200 - 50) = 0.333
        assert mid_norm == pytest.approx(0.333, abs=0.01)
        # (200 - 50) / (200 - 50) = 1.0
        assert high_norm == 1.0

    def test_absolute_normalization_without_batch_scores(self, sample_profile):
        """
        Given: No batch scores provided
        When: Popularity is normalized
        Then: Absolute normalization with MAX_HN_SCORE=500 cap should be used
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        norm_100 = service._normalize_popularity(100, None)
        norm_250 = service._normalize_popularity(250, None)
        norm_500 = service._normalize_popularity(500, None)
        norm_1000 = service._normalize_popularity(1000, None)

        # Assert
        # 100 / 500 = 0.2
        assert norm_100 == 0.2
        # 250 / 500 = 0.5
        assert norm_250 == 0.5
        # 500 / 500 = 1.0
        assert norm_500 == 1.0
        # 1000 / 500 = capped at 1.0
        assert norm_1000 == 1.0

    def test_absolute_normalization_caps_at_max_hn_score(self, sample_profile):
        """
        Given: HN score above MAX_HN_SCORE (500)
        When: Popularity is normalized
        Then: Score should be capped at 1.0
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        result = service._normalize_popularity(750, None)

        # Assert
        assert result == 1.0

    def test_relative_normalization_all_same_scores(self, sample_profile):
        """
        Given: All HN scores in batch are the same
        When: Popularity is normalized
        Then: Score should be 0.5 (neutral)
        """
        # Arrange
        service = ScoringService(sample_profile)
        all_scores = [100, 100, 100]

        # Act
        result = service._normalize_popularity(100, all_scores)

        # Assert
        assert result == 0.5

    def test_relative_normalization_single_score_batch(self, sample_profile):
        """
        Given: Batch with only one score
        When: Popularity is normalized
        Then: Should fall back to absolute normalization
        """
        # Arrange
        service = ScoringService(sample_profile)
        all_scores = [100]

        # Act
        result = service._normalize_popularity(100, all_scores)

        # Assert
        # Single score batch should use absolute: 100/500 = 0.2
        assert result == 0.2

    def test_relative_normalization_empty_batch(self, sample_profile):
        """
        Given: Empty batch scores
        When: Popularity is normalized
        Then: Should fall back to absolute normalization
        """
        # Arrange
        service = ScoringService(sample_profile)
        all_scores: list[int] = []

        # Act
        result = service._normalize_popularity(100, all_scores)

        # Assert
        assert result == 0.2  # 100/500

    def test_normalization_with_zero_score(self, sample_profile):
        """
        Given: HN score of 0
        When: Popularity is normalized
        Then: Score should be 0.0
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        result_abs = service._normalize_popularity(0, None)
        result_rel = service._normalize_popularity(0, [0, 100, 200])

        # Assert
        assert result_abs == 0.0
        assert result_rel == 0.0


# =============================================================================
# Composite Scoring Tests
# =============================================================================


class TestCompositeScoring:
    """Tests for composite final score calculation."""

    def test_composite_score_default_weights(self, sample_profile):
        """
        Given: Default weights (70% relevance, 30% popularity)
        When: Article is scored
        Then: Final score should be 0.7*relevance + 0.3*popularity
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(
            hn_score=250,
            tech_tags=["python", "ai", "rust"],  # All match = relevance 1.0
        )

        # Act
        scored = service.score_article(article, all_hn_scores=None)

        # Assert
        # relevance = 1.0 (all tags match)
        # popularity = 250/500 = 0.5
        # final = 0.7 * 1.0 + 0.3 * 0.5 = 0.85
        assert scored.relevance.score == 1.0
        assert scored.popularity_score == 0.5
        assert scored.final_score == pytest.approx(0.85, abs=0.01)

    def test_composite_score_custom_weights(self, sample_profile):
        """
        Given: Custom weights (50% relevance, 50% popularity)
        When: Article is scored
        Then: Final score should reflect custom weights
        """
        # Arrange
        service = ScoringService(
            sample_profile,
            relevance_weight=0.5,
            popularity_weight=0.5,
        )
        article = create_summarized_article(
            hn_score=500,
            tech_tags=["python"],  # 1/3 match = relevance 0.667
        )

        # Act
        scored = service.score_article(article, all_hn_scores=None)

        # Assert
        # relevance = 0.5 + (1/3 * 0.5) = 0.667
        # popularity = 500/500 = 1.0
        # final = 0.5 * 0.667 + 0.5 * 1.0 = 0.833
        assert scored.relevance.score == pytest.approx(0.667, abs=0.01)
        assert scored.popularity_score == 1.0
        assert scored.final_score == pytest.approx(0.833, abs=0.01)

    def test_composite_score_only_relevance(self, sample_profile):
        """
        Given: 100% relevance weight, 0% popularity weight
        When: Article is scored
        Then: Final score should equal relevance score
        """
        # Arrange
        service = ScoringService(
            sample_profile,
            relevance_weight=1.0,
            popularity_weight=0.0,
        )
        article = create_summarized_article(
            hn_score=500,
            tech_tags=["python", "ai"],  # 2/3 match
        )

        # Act
        scored = service.score_article(article, all_hn_scores=None)

        # Assert
        assert scored.final_score == scored.relevance.score

    def test_composite_score_only_popularity(self, sample_profile):
        """
        Given: 0% relevance weight, 100% popularity weight
        When: Article is scored
        Then: Final score should equal popularity score
        """
        # Arrange
        service = ScoringService(
            sample_profile,
            relevance_weight=0.0,
            popularity_weight=1.0,
        )
        article = create_summarized_article(
            hn_score=250,
            tech_tags=["python", "ai", "rust"],
        )

        # Act
        scored = service.score_article(article, all_hn_scores=None)

        # Assert
        assert scored.final_score == scored.popularity_score
        assert scored.final_score == 0.5  # 250/500

    def test_scoring_article_without_summary(self, sample_profile):
        """
        Given: Article without summary (no tags)
        When: Article is scored
        Then: Relevance should be neutral (0.5)
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(
            hn_score=100,
            has_summary=False,
        )

        # Act
        scored = service.score_article(article, all_hn_scores=None)

        # Assert
        assert scored.relevance.score == 0.5
        assert "no tags" in scored.relevance.reason.lower()


# =============================================================================
# Batch Scoring Tests
# =============================================================================


class TestBatchScoring:
    """Tests for score_articles batch scoring method."""

    def test_batch_scoring_multiple_articles(self, sample_profile):
        """
        Given: Multiple articles to score
        When: Batch scoring is performed
        Then: All articles should be scored and returned sorted by final_score
        """
        # Arrange
        service = ScoringService(sample_profile)
        articles = [
            create_summarized_article(
                story_id=1, hn_score=100, tech_tags=["javascript"]
            ),  # no match
            create_summarized_article(
                story_id=2, hn_score=200, tech_tags=["python", "ai", "rust"]
            ),  # full match
            create_summarized_article(
                story_id=3, hn_score=300, tech_tags=["python"]
            ),  # partial match
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=False)

        # Assert
        assert len(scored) == 3
        # Should be sorted by final_score descending
        assert scored[0].article.article.story_id == 2  # Full match, high relevance
        assert scored[-1].article.article.story_id == 1  # No match, low relevance
        # Verify descending order
        assert scored[0].final_score >= scored[1].final_score >= scored[2].final_score

    def test_batch_scoring_with_min_score_filter(self, profile_with_min_score):
        """
        Given: Profile with min_score threshold
        When: Batch scoring with filtering enabled
        Then: Articles below min_score should be filtered out
        """
        # Arrange
        service = ScoringService(profile_with_min_score)
        articles = [
            create_summarized_article(
                story_id=1, hn_score=50, tech_tags=["crypto"]
            ),  # disinterest, low score
            create_summarized_article(
                story_id=2, hn_score=400, tech_tags=["python", "ai"]
            ),  # high match
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=True)

        # Assert
        # Article 1 should be filtered (disinterest penalty = 0.1 relevance)
        # min_score is 0.5
        assert len(scored) == 1
        assert scored[0].article.article.story_id == 2

    def test_batch_scoring_without_filtering(self, profile_with_min_score):
        """
        Given: Profile with min_score but filtering disabled
        When: Batch scoring without filtering
        Then: All articles should be returned
        """
        # Arrange
        service = ScoringService(profile_with_min_score)
        articles = [
            create_summarized_article(story_id=1, hn_score=50, tech_tags=["crypto"]),
            create_summarized_article(story_id=2, hn_score=400, tech_tags=["python", "ai"]),
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=False)

        # Assert
        assert len(scored) == 2

    def test_batch_scoring_uses_relative_popularity(self, sample_profile):
        """
        Given: Multiple articles with varying HN scores
        When: Batch scoring is performed
        Then: Popularity should be normalized relative to the batch
        """
        # Arrange
        service = ScoringService(sample_profile)
        articles = [
            create_summarized_article(story_id=1, hn_score=100, tech_tags=[]),  # min score
            create_summarized_article(story_id=2, hn_score=200, tech_tags=[]),  # mid score
            create_summarized_article(story_id=3, hn_score=300, tech_tags=[]),  # max score
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=False)

        # Assert
        # With neutral relevance (0.5), popularity becomes the differentiator
        # Article 3 should have highest popularity (1.0), article 1 lowest (0.0)
        scored_by_id = {s.article.article.story_id: s for s in scored}
        assert scored_by_id[1].popularity_score == 0.0
        assert scored_by_id[2].popularity_score == 0.5
        assert scored_by_id[3].popularity_score == 1.0

    def test_batch_scoring_empty_list(self, sample_profile):
        """
        Given: Empty list of articles
        When: Batch scoring is performed
        Then: Empty list should be returned
        """
        # Arrange
        service = ScoringService(sample_profile)
        articles: list[SummarizedArticle] = []

        # Act
        scored = service.score_articles(articles)

        # Assert
        assert scored == []

    def test_batch_scoring_single_article(self, sample_profile):
        """
        Given: Single article
        When: Batch scoring is performed
        Then: Article should be scored with absolute popularity normalization
        """
        # Arrange
        service = ScoringService(sample_profile)
        articles = [
            create_summarized_article(story_id=1, hn_score=250, tech_tags=["python"]),
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=False)

        # Assert
        assert len(scored) == 1
        # Single article, relative normalization falls back to absolute
        assert scored[0].popularity_score == 0.5  # 250/500


# =============================================================================
# Reason Generation Tests
# =============================================================================


class TestReasonGeneration:
    """Tests for _generate_reason method."""

    def test_reason_for_interest_matches(self, sample_profile):
        """
        Given: Matched interest tags
        When: Reason is generated
        Then: Reason should mention interests
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        reason = service._generate_reason(["python", "ai"], [])

        # Assert
        assert "interests" in reason.lower()
        assert "python" in reason
        assert "ai" in reason

    def test_reason_for_disinterest_matches(self, sample_profile):
        """
        Given: Matched disinterest tags
        When: Reason is generated
        Then: Reason should mention avoided topics
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        reason = service._generate_reason(["python"], ["crypto", "blockchain"])

        # Assert
        assert "avoided" in reason.lower()
        assert "crypto" in reason
        assert "blockchain" in reason

    def test_reason_for_no_matches(self, sample_profile):
        """
        Given: No matched tags
        When: Reason is generated
        Then: Reason should indicate no specific match
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        reason = service._generate_reason([], [])

        # Assert
        assert "no specific interest" in reason.lower()


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestScoringEdgeCases:
    """Tests for edge cases in scoring."""

    def test_all_articles_same_hn_score(self, sample_profile):
        """
        Given: All articles have the same HN score
        When: Batch scoring is performed
        Then: Popularity should be 0.5 for all
        """
        # Arrange
        service = ScoringService(sample_profile)
        articles = [
            create_summarized_article(story_id=1, hn_score=100, tech_tags=["python"]),
            create_summarized_article(story_id=2, hn_score=100, tech_tags=["ai"]),
            create_summarized_article(story_id=3, hn_score=100, tech_tags=["rust"]),
        ]

        # Act
        scored = service.score_articles(articles, filter_below_min=False)

        # Assert
        for s in scored:
            assert s.popularity_score == 0.5

    def test_profile_with_only_disinterest_tags(self, sample_profile_disinterests_only):
        """
        Given: Profile with only disinterest tags
        When: Article is scored
        Then: Non-matching articles should get neutral, matching should be penalized
        """
        # Arrange
        service = ScoringService(sample_profile_disinterests_only)
        neutral_article = create_summarized_article(
            story_id=1, hn_score=100, tech_tags=["python", "ai"]
        )
        penalized_article = create_summarized_article(
            story_id=2, hn_score=100, tech_tags=["crypto"]
        )

        # Act
        neutral_scored = service.score_article(neutral_article, None)
        penalized_scored = service.score_article(penalized_article, None)

        # Assert
        assert neutral_scored.relevance.score == 0.5
        assert penalized_scored.relevance.score == 0.1

    def test_profile_with_only_interest_tags(self, sample_profile_interests_only):
        """
        Given: Profile with only interest tags
        When: Article is scored
        Then: Matching articles should get boosted scores
        """
        # Arrange
        service = ScoringService(sample_profile_interests_only)
        matching_article = create_summarized_article(
            story_id=1, hn_score=100, tech_tags=["python", "ai"]
        )
        non_matching_article = create_summarized_article(
            story_id=2, hn_score=100, tech_tags=["javascript"]
        )

        # Act
        matching_scored = service.score_article(matching_article, None)
        non_matching_scored = service.score_article(non_matching_article, None)

        # Assert
        assert matching_scored.relevance.score > 0.5
        assert non_matching_scored.relevance.score == 0.5

    def test_very_high_hn_score(self, sample_profile):
        """
        Given: Article with very high HN score (above MAX_HN_SCORE)
        When: Article is scored
        Then: Popularity should be capped at 1.0
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(story_id=1, hn_score=2000, tech_tags=[])

        # Act
        scored = service.score_article(article, None)

        # Assert
        assert scored.popularity_score == 1.0

    def test_zero_hn_score(self, sample_profile):
        """
        Given: Article with zero HN score
        When: Article is scored
        Then: Popularity should be 0.0
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(story_id=1, hn_score=0, tech_tags=["python"])

        # Act
        scored = service.score_article(article, None)

        # Assert
        assert scored.popularity_score == 0.0

    def test_scored_article_convenience_properties(self, sample_profile):
        """
        Given: A scored article
        When: Convenience properties are accessed
        Then: They should return expected values from nested objects
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(
            story_id=42,
            title="Test Title",
            hn_score=100,
            tech_tags=["python"],
        )

        # Act
        scored = service.score_article(article, None)

        # Assert
        assert scored.story_id == 42
        assert scored.title == "Test Title"
        assert scored.relevance_score == scored.relevance.score
        assert scored.relevance_reason == scored.relevance.reason

    def test_is_filtered_method(self, sample_profile):
        """
        Given: A scored article
        When: is_filtered is checked with various thresholds
        Then: Correct filtering behavior should be returned
        """
        # Arrange
        service = ScoringService(sample_profile)
        article = create_summarized_article(story_id=1, hn_score=100, tech_tags=[])
        scored = service.score_article(article, None)
        # neutral relevance (0.5), low popularity (0.2) => final ~0.41

        # Act & Assert
        assert scored.is_filtered(min_score=0.0) is False
        assert scored.is_filtered(min_score=0.3) is False
        assert scored.is_filtered(min_score=0.5) is True
        assert scored.is_filtered(min_score=0.8) is True


# =============================================================================
# Parametrized Tests
# =============================================================================


class TestScoringParametrized:
    """Parametrized tests for comprehensive coverage."""

    @pytest.mark.parametrize(
        "interest_count,expected_min_score,expected_max_score",
        [
            (0, 0.5, 0.5),  # No matches
            (1, 0.5, 0.7),  # 1 of 3 matches
            (2, 0.7, 0.9),  # 2 of 3 matches
            (3, 0.9, 1.0),  # All 3 match
        ],
    )
    def test_relevance_score_ranges(
        self,
        sample_profile,
        interest_count,
        expected_min_score,
        expected_max_score,
    ):
        """
        Given: Various numbers of matching interest tags
        When: Relevance is calculated
        Then: Score should fall within expected range
        """
        # Arrange
        service = ScoringService(sample_profile)
        # sample_profile has ["python", "ai", "rust"] as interests
        matching_tags = ["python", "ai", "rust"][:interest_count]
        article_tags = [*matching_tags, "unrelated"]

        # Act
        relevance = service._calculate_relevance(article_tags)

        # Assert
        assert expected_min_score <= relevance.score <= expected_max_score

    @pytest.mark.parametrize(
        "hn_score,expected_popularity",
        [
            (0, 0.0),
            (100, 0.2),
            (250, 0.5),
            (500, 1.0),
            (750, 1.0),  # Capped
            (1000, 1.0),  # Capped
        ],
    )
    def test_absolute_popularity_normalization(
        self,
        sample_profile,
        hn_score,
        expected_popularity,
    ):
        """
        Given: Various HN scores without batch context
        When: Popularity is normalized
        Then: Score should match expected value
        """
        # Arrange
        service = ScoringService(sample_profile)

        # Act
        popularity = service._normalize_popularity(hn_score, None)

        # Assert
        assert popularity == pytest.approx(expected_popularity, abs=0.01)

    @pytest.mark.parametrize(
        "relevance_w,popularity_w,expected_valid",
        [
            (0.7, 0.3, True),
            (0.5, 0.5, True),
            (1.0, 0.0, True),
            (0.0, 1.0, True),
            (0.3, 0.3, True),
            (-0.1, 0.3, False),
            (0.7, -0.1, False),
            (0.6, 0.5, False),  # Sum > 1.0
            (0.8, 0.8, False),  # Sum > 1.0
        ],
    )
    def test_weight_validation(
        self,
        sample_profile,
        relevance_w,
        popularity_w,
        expected_valid,
    ):
        """
        Given: Various weight combinations
        When: ScoringService is initialized
        Then: Validation should pass or fail as expected
        """
        # Arrange & Act & Assert
        if expected_valid:
            service = ScoringService(
                sample_profile,
                relevance_weight=relevance_w,
                popularity_weight=popularity_w,
            )
            assert service.relevance_weight == relevance_w
            assert service.popularity_weight == popularity_w
        else:
            with pytest.raises(ValueError):
                ScoringService(
                    sample_profile,
                    relevance_weight=relevance_w,
                    popularity_weight=popularity_w,
                )
