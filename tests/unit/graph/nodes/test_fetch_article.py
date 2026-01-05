"""Unit tests for fetch_article node.

Tests the fetch_article node which extracts article content from story URLs
in parallel using the Send pattern.
"""

from unittest.mock import AsyncMock, patch

import pytest

from hn_herald.graph.nodes.fetch_article import fetch_article
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.story import Story


class TestFetchArticleSuccess:
    """Tests for successful fetch_article node execution."""

    @pytest.mark.asyncio
    async def test_fetch_article_extracts_content_successfully(
        self, mock_user_profile, mock_article_loader
    ):
        """Test fetch_article extracts article successfully.

        Given: Story and mock ArticleLoader
        When: fetch_article node is executed
        Then: Article is extracted and returned in state
        """
        # Arrange
        story = Story(
            id=1,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        # Act
        with patch(
            "hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_article_loader
        ):
            result = await fetch_article(state)

        # Assert
        assert "articles" in result
        assert len(result["articles"]) == 1
        assert isinstance(result["articles"][0], Article)
        assert result["articles"][0].story_id == story.id
        assert result["articles"][0].status == ExtractionStatus.SUCCESS
        assert "errors" not in result

    @pytest.mark.asyncio
    async def test_fetch_article_calls_loader_with_story(
        self, mock_user_profile, mock_article_loader
    ):
        """Test fetch_article passes story to ArticleLoader.

        Given: Story and mock ArticleLoader
        When: fetch_article node is executed
        Then: ArticleLoader.extract_article is called with story
        """
        # Arrange
        story = Story(
            id=1,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        # Act
        with patch(
            "hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_article_loader
        ):
            await fetch_article(state)

        # Assert
        mock_article_loader.extract_article.assert_called_once_with(story)

    @pytest.mark.asyncio
    async def test_fetch_article_returns_article_with_content(self, mock_user_profile):
        """Test fetch_article returns article with content.

        Given: Story and ArticleLoader returning article with content
        When: fetch_article node is executed
        Then: Article with content is returned
        """
        # Arrange
        story = Story(
            id=1,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        article_with_content = Article(
            story_id=1,
            title="Test Story",
            url="https://example.com/article",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            hn_comments=10,
            author="testuser",
            content="This is the extracted article content with valuable information.",
            word_count=10,
            status=ExtractionStatus.SUCCESS,
        )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(return_value=article_with_content)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            result = await fetch_article(state)

        # Assert
        assert result["articles"][0].has_content is True
        assert result["articles"][0].word_count == 10
        assert len(result["articles"][0].content) > 0


class TestFetchArticleErrorHandling:
    """Tests for fetch_article error handling (partial failure tolerance)."""

    @pytest.mark.asyncio
    async def test_fetch_article_handles_extraction_failure(self, mock_user_profile):
        """Test fetch_article handles extraction failures gracefully.

        Given: Story and ArticleLoader that raises exception
        When: fetch_article node is executed
        Then: Error article is created and error is accumulated
        """
        # Arrange
        story = Story(
            id=1,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Network error"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            result = await fetch_article(state)

        # Assert
        assert "articles" in result
        assert len(result["articles"]) == 1
        assert result["articles"][0].status == ExtractionStatus.FAILED
        assert result["articles"][0].error_message == "Network error"
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "Network error" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_fetch_article_error_article_preserves_story_info(self, mock_user_profile):
        """Test error article preserves story information.

        Given: Story and ArticleLoader that fails
        When: fetch_article node is executed
        Then: Error article contains story metadata
        """
        # Arrange
        story = Story(
            id=12345,
            title="Important Story",
            url="https://example.com/important",
            score=250,
            by="author123",
            time=1704067200,
            descendants=50,
        )
        state = {"story": story, "profile": mock_user_profile}

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Extraction failed"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            result = await fetch_article(state)

        # Assert
        error_article = result["articles"][0]
        assert error_article.story_id == story.id
        assert error_article.title == story.title
        assert error_article.url == story.url
        assert error_article.hn_score == story.score
        assert error_article.author == story.by

    @pytest.mark.asyncio
    async def test_fetch_article_multiple_failures_accumulate_errors(self, mock_user_profile):
        """Test multiple fetch_article failures accumulate errors.

        Given: Multiple stories processed in parallel (simulated)
        When: Some extractions fail
        Then: Each failure creates an error article and error message
        """
        # Arrange
        stories = [
            Story(
                id=1,
                title="Story 1",
                url="https://example.com/1",
                score=100,
                by="user1",
                time=1704067200,
                descendants=10,
            ),
            Story(
                id=2,
                title="Story 2",
                url="https://example.com/2",
                score=150,
                by="user2",
                time=1704153600,
                descendants=20,
            ),
        ]

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Failed"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act - Simulate parallel execution
        results = []
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            for story in stories:
                state = {"story": story, "profile": mock_user_profile}
                result = await fetch_article(state)
                results.append(result)

        # Assert
        assert all("errors" in r for r in results)
        assert all(len(r["errors"]) == 1 for r in results)
        assert all(r["articles"][0].status == ExtractionStatus.FAILED for r in results)


class TestFetchArticleLogging:
    """Tests for fetch_article logging behavior."""

    @pytest.mark.asyncio
    async def test_fetch_article_logs_success(self, mock_user_profile, mock_article_loader, caplog):
        """Test fetch_article logs successful extraction.

        Given: Story and successful extraction
        When: fetch_article node is executed
        Then: Success is logged with story ID
        """
        # Arrange
        import logging

        caplog.set_level(logging.DEBUG)
        story = Story(
            id=12345,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        # Act
        with patch(
            "hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_article_loader
        ):
            await fetch_article(state)

        # Assert
        assert any("12345" in record.message for record in caplog.records)
        assert any(
            "Success" in record.message or "Extracting" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_fetch_article_logs_extraction_error(self, mock_user_profile, caplog):
        """Test fetch_article logs extraction errors.

        Given: Story and ArticleLoader that fails
        When: fetch_article node is executed
        Then: Error is logged with story ID and error message
        """
        # Arrange
        import logging

        caplog.set_level(logging.ERROR)
        story = Story(
            id=12345,
            title="Test Story",
            url="https://example.com/article",
            score=100,
            by="testuser",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Network timeout"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            await fetch_article(state)

        # Assert
        assert any(
            "Failed" in record.message and "12345" in record.message for record in caplog.records
        )
        assert any("Network timeout" in record.message for record in caplog.records)


class TestFetchArticleStatuses:
    """Tests for different article extraction statuses."""

    @pytest.mark.asyncio
    async def test_fetch_article_handles_no_url_status(self, mock_user_profile):
        """Test fetch_article handles NO_URL status.

        Given: Story and ArticleLoader returning NO_URL article
        When: fetch_article node is executed
        Then: Article with NO_URL status is returned
        """
        # Arrange
        story = Story(
            id=1,
            title="Ask HN: Question",
            url=None,  # No URL
            score=50,
            by="asker",
            time=1704067200,
            descendants=25,
        )
        state = {"story": story, "profile": mock_user_profile}

        no_url_article = Article(
            story_id=1,
            title="Ask HN: Question",
            url=None,
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=50,
            hn_comments=25,
            author="asker",
            status=ExtractionStatus.NO_URL,
        )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(return_value=no_url_article)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            result = await fetch_article(state)

        # Assert
        assert result["articles"][0].status == ExtractionStatus.NO_URL
        assert result["articles"][0].url is None

    @pytest.mark.asyncio
    async def test_fetch_article_handles_skipped_status(self, mock_user_profile):
        """Test fetch_article handles SKIPPED status.

        Given: Story and ArticleLoader returning SKIPPED article
        When: fetch_article node is executed
        Then: Article with SKIPPED status is returned
        """
        # Arrange
        story = Story(
            id=1,
            title="PDF Document",
            url="https://example.com/document.pdf",
            score=100,
            by="author",
            time=1704067200,
            descendants=10,
        )
        state = {"story": story, "profile": mock_user_profile}

        skipped_article = Article(
            story_id=1,
            title="PDF Document",
            url="https://example.com/document.pdf",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            hn_comments=10,
            author="author",
            status=ExtractionStatus.SKIPPED,
        )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(return_value=skipped_article)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader):
            result = await fetch_article(state)

        # Assert
        assert result["articles"][0].status == ExtractionStatus.SKIPPED
