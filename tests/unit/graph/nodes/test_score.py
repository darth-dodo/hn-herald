"""Unit tests for score node.

Tests the score_articles node which calculates relevance scores using
tag-based matching against user interests.
"""

from unittest.mock import MagicMock, patch

from hn_herald.graph.nodes.score import score_articles
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.scoring import RelevanceScore, ScoredArticle
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)


class TestScoreArticlesSuccess:
    """Tests for successful score_articles node execution."""

    def test_score_calls_scoring_service(self, mock_user_profile, mock_scoring_service):
        """Test score calls ScoringService with summarized articles.

        Given: Summarized articles and profile
        When: score_articles node is executed
        Then: ScoringService.score_articles is called
        """
        # Arrange
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Test",
                    url="https://example.com/1",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    author="user1",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring_service):
            result = score_articles(state)

        # Assert
        mock_scoring_service.score_articles.assert_called_once()
        assert "scored_articles" in result

    def test_score_filters_below_min_score(self, mock_user_profile):
        """Test score filters articles below min_score threshold.

        Given: Summarized articles and profile with min_score
        When: score_articles node is executed
        Then: ScoringService is called with filter_below_min=True
        """
        # Arrange
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Test",
                    url="https://example.com/1",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    author="user1",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=[])

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            score_articles(state)

        # Assert
        call_kwargs = mock_service.score_articles.call_args[1]
        assert call_kwargs["filter_below_min"] is True

    def test_score_returns_scored_articles(self, mock_user_profile):
        """Test score returns list of ScoredArticle objects.

        Given: Summarized articles
        When: score_articles node is executed
        Then: Scored articles are returned
        """
        # Arrange
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Test",
                    url="https://example.com/1",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    author="user1",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        scored = [
            ScoredArticle(
                article=summarized[0],
                relevance=RelevanceScore(
                    score=0.8,
                    reason="Test relevance",
                    matched_interest_tags=["python"],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.74,
            )
        ]

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=scored)

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            result = score_articles(state)

        # Assert
        assert len(result["scored_articles"]) == 1
        assert isinstance(result["scored_articles"][0], ScoredArticle)
        assert result["scored_articles"][0].final_score == 0.74


class TestScoreArticlesEmptyInput:
    """Tests for score_articles handling empty inputs."""

    def test_score_empty_summarized_articles(self, mock_user_profile):
        """Test score handles empty summarized articles list.

        Given: Empty summarized_articles list
        When: score_articles node is executed
        Then: Empty scored_articles list is returned
        """
        # Arrange
        state = {"summarized_articles": [], "profile": mock_user_profile}

        # Act
        result = score_articles(state)

        # Assert
        assert "scored_articles" in result
        assert result["scored_articles"] == []

    def test_score_all_filtered_below_threshold(self, mock_user_profile):
        """Test score when all articles filtered below min_score.

        Given: Summarized articles all below min_score
        When: score_articles node is executed
        Then: Empty scored_articles list is returned
        """
        # Arrange
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Low Relevance",
                    url="https://example.com/1",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    author="user1",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["unrelated"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=[])  # All filtered

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            result = score_articles(state)

        # Assert
        assert len(result["scored_articles"]) == 0


class TestScoreArticlesLogging:
    """Tests for score_articles logging behavior."""

    def test_score_logs_article_count(self, mock_user_profile, caplog):
        """Test score logs article count being scored.

        Given: Summarized articles
        When: score_articles node is executed
        Then: Article count is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=i,
                    title=f"Test {i}",
                    url=f"https://example.com/{i}",
                    hn_url=f"https://news.ycombinator.com/item?id={i}",
                    hn_score=100,
                    author=f"user{i}",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
            for i in range(1, 4)
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=[])

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            score_articles(state)

        # Assert
        assert any("Scoring 3 articles" in record.message for record in caplog.records)

    def test_score_logs_filtering_stats(self, mock_user_profile, caplog):
        """Test score logs filtering statistics.

        Given: Summarized articles with some filtered
        When: score_articles node is executed
        Then: Before/after counts are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=i,
                    title=f"Test {i}",
                    url=f"https://example.com/{i}",
                    hn_url=f"https://news.ycombinator.com/item?id={i}",
                    hn_score=100,
                    author=f"user{i}",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
            for i in range(1, 6)
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        # Return only 2 scored articles (3 filtered)
        scored = [
            ScoredArticle(
                article=summarized[i],
                relevance=RelevanceScore(
                    score=0.8,
                    reason="Test relevance",
                    matched_interest_tags=["python"],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.74,
            )
            for i in range(2)
        ]

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=scored)

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            score_articles(state)

        # Assert
        assert any("5" in record.message and "2" in record.message for record in caplog.records)

    def test_score_logs_average_scores(self, mock_user_profile, caplog):
        """Test score logs average scores in debug mode.

        Given: Scored articles with various scores
        When: score_articles node is executed
        Then: Average scores are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.DEBUG)
        summarized = [
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Test",
                    url="https://example.com/1",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    author="user1",
                    content="Content",
                    word_count=1,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
        state = {"summarized_articles": summarized, "profile": mock_user_profile}

        scored = [
            ScoredArticle(
                article=summarized[0],
                relevance=RelevanceScore(
                    score=0.75,
                    reason="Test relevance",
                    matched_interest_tags=["python"],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.60,
                final_score=0.72,
            )
        ]

        mock_service = MagicMock()
        mock_service.score_articles = MagicMock(return_value=scored)

        # Act
        with patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_service):
            score_articles(state)

        # Assert - check for score distribution log (changed from "Average scores")
        assert any("Score distribution" in record.message for record in caplog.records)

    def test_score_logs_warning_on_empty(self, mock_user_profile, caplog):
        """Test score logs warning when no articles to score.

        Given: Empty summarized_articles list
        When: score_articles node is executed
        Then: Warning is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.WARNING)
        state = {"summarized_articles": [], "profile": mock_user_profile}

        # Act
        score_articles(state)

        # Assert
        assert any("No articles to score" in record.message for record in caplog.records)
