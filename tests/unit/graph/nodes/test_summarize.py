"""Unit tests for summarize node.

Tests the summarize node which batch summarizes articles using LLMService.
"""

from unittest.mock import MagicMock, patch

import pytest

from hn_herald.graph.nodes.summarize import summarize
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)


class TestSummarizeSuccess:
    """Tests for successful summarize node execution."""

    @pytest.mark.asyncio
    async def test_summarize_batch_processes_articles(self, mock_llm_service):
        """Test summarize calls LLMService with batch of articles.

        Given: Filtered articles
        When: summarize node is executed
        Then: LLMService.summarize_articles_batch is called
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Article 1",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Content 1",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="Article 2",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                content="Content 2",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"filtered_articles": articles}

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service):
            result = await summarize(state)

        # Assert
        mock_llm_service.summarize_articles_batch.assert_called_once_with(articles)
        assert "summarized_articles" in result

    @pytest.mark.asyncio
    async def test_summarize_returns_summarized_articles(self):
        """Test summarize returns list of SummarizedArticle objects.

        Given: Filtered articles and mock LLMService
        When: summarize node is executed
        Then: Summarized articles are returned
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Test Article",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Article content",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"filtered_articles": articles}

        summarized = [
            SummarizedArticle(
                article=articles[0],
                summary_data=ArticleSummary(
                    summary="This is a test summary with enough characters for validation",
                    key_points=["Point 1"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]

        mock_service = MagicMock()
        mock_service.summarize_articles_batch = MagicMock(return_value=summarized)

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_service):
            result = await summarize(state)

        # Assert
        assert len(result["summarized_articles"]) == 1
        assert isinstance(result["summarized_articles"][0], SummarizedArticle)
        assert result["summarized_articles"][0].has_summary is True

    @pytest.mark.asyncio
    async def test_summarize_no_errors_when_all_succeed(self):
        """Test summarize returns no errors when all succeed.

        Given: Articles that all summarize successfully
        When: summarize node is executed
        Then: No errors are returned
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Article 1",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"filtered_articles": articles}

        summarized = [
            SummarizedArticle(
                article=articles[0],
                summary_data=ArticleSummary(
                    summary="This is a valid summary text",
                    key_points=["Point"],
                    tech_tags=["tag"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]

        mock_service = MagicMock()
        mock_service.summarize_articles_batch = MagicMock(return_value=summarized)

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_service):
            result = await summarize(state)

        # Assert
        assert "errors" in result
        assert len(result["errors"]) == 0


class TestSummarizeErrorHandling:
    """Tests for summarize error handling."""

    @pytest.mark.asyncio
    async def test_summarize_accumulates_errors(self):
        """Test summarize accumulates errors from failed summarizations.

        Given: Articles with some summarization failures
        When: summarize node is executed
        Then: Errors are accumulated in state
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Success Article",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="Failed Article",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"filtered_articles": articles}

        summarized = [
            SummarizedArticle(
                article=articles[0],
                summary_data=ArticleSummary(
                    summary="Successfully summarized article",
                    key_points=["Point"],
                    tech_tags=["tag"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            ),
            SummarizedArticle(
                article=articles[1],
                summarization_status=SummarizationStatus.PARSE_ERROR,
                error_message="Parse error",
            ),
        ]

        mock_service = MagicMock()
        mock_service.summarize_articles_batch = MagicMock(return_value=summarized)

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_service):
            result = await summarize(state)

        # Assert
        assert len(result["errors"]) == 1
        assert "2" in result["errors"][0]  # Story ID
        assert "Parse error" in result["errors"][0]


class TestSummarizeEmptyInput:
    """Tests for summarize handling empty inputs."""

    @pytest.mark.asyncio
    async def test_summarize_empty_articles_list(self):
        """Test summarize handles empty filtered articles list.

        Given: Empty filtered_articles list
        When: summarize node is executed
        Then: Empty summarized_articles and error are returned
        """
        # Arrange
        state = {"filtered_articles": []}

        # Act
        result = await summarize(state)

        # Assert
        assert "summarized_articles" in result
        assert result["summarized_articles"] == []
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "No articles to summarize" in result["errors"][0]


class TestSummarizeLogging:
    """Tests for summarize logging behavior."""

    @pytest.mark.asyncio
    async def test_summarize_logs_batch_processing(self, caplog):
        """Test summarize logs batch processing information.

        Given: Filtered articles
        When: summarize node is executed
        Then: Batch processing is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        articles = [
            Article(
                story_id=1,
                title="Article",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"filtered_articles": articles}

        summarized = [
            SummarizedArticle(
                article=articles[0],
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=[],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]

        mock_service = MagicMock()
        mock_service.summarize_articles_batch = MagicMock(return_value=summarized)

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_service):
            await summarize(state)

        # Assert
        assert any("Batch summarizing" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_summarize_logs_success_and_failure_counts(self, caplog):
        """Test summarize logs success and failure counts.

        Given: Articles with mixed summarization results
        When: summarize node is executed
        Then: Success and failure counts are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        articles = [
            Article(
                story_id=i,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                hn_url=f"https://news.ycombinator.com/item?id={i}",
                hn_score=100,
                author=f"user{i}",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            )
            for i in range(1, 4)
        ]
        state = {"filtered_articles": articles}

        summarized = [
            SummarizedArticle(
                article=articles[0],
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=[],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            ),
            SummarizedArticle(
                article=articles[1],
                summarization_status=SummarizationStatus.API_ERROR,
                error_message="Error",
            ),
            SummarizedArticle(
                article=articles[2],
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=[],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            ),
        ]

        mock_service = MagicMock()
        mock_service.summarize_articles_batch = MagicMock(return_value=summarized)

        # Act
        with patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_service):
            await summarize(state)

        # Assert
        assert any("2 successful" in record.message for record in caplog.records)
        assert any("1 failed" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_summarize_logs_warning_on_empty(self, caplog):
        """Test summarize logs warning when no articles to summarize.

        Given: Empty filtered_articles list
        When: summarize node is executed
        Then: Warning is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.WARNING)
        state = {"filtered_articles": []}

        # Act
        await summarize(state)

        # Assert
        assert any("No articles to summarize" in record.message for record in caplog.records)
