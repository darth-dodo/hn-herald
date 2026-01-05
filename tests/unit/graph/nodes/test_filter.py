"""Unit tests for filter node.

Tests the filter_articles node which removes articles without content
before summarization to reduce LLM costs.
"""

from hn_herald.graph.nodes.filter import filter_articles
from hn_herald.models.article import Article, ExtractionStatus


class TestFilterArticlesSuccess:
    """Tests for successful filter_articles node execution."""

    def test_filter_keeps_articles_with_content(self):
        """Test filter keeps articles with SUCCESS status and content.

        Given: Articles with SUCCESS status and content
        When: filter_articles node is executed
        Then: Articles are kept in filtered list
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
                content="This is article content.",
                word_count=4,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="Article 2",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                content="More article content here.",
                word_count=4,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert "filtered_articles" in result
        assert len(result["filtered_articles"]) == 2
        assert all(a.has_content for a in result["filtered_articles"])
        assert all(a.status == ExtractionStatus.SUCCESS for a in result["filtered_articles"])

    def test_filter_removes_failed_articles(self):
        """Test filter removes articles with FAILED status.

        Given: Mix of SUCCESS and FAILED articles
        When: filter_articles node is executed
        Then: Only SUCCESS articles are kept
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
                content="Article content",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="Failed Article",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                status=ExtractionStatus.FAILED,
                error_message="Network error",
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 1
        assert result["filtered_articles"][0].story_id == 1
        assert result["filtered_articles"][0].status == ExtractionStatus.SUCCESS

    def test_filter_removes_no_url_articles(self):
        """Test filter removes articles with NO_URL status.

        Given: Mix of SUCCESS and NO_URL articles
        When: filter_articles node is executed
        Then: Only SUCCESS articles are kept
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Regular Article",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Content here",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="Ask HN Article",
                url=None,
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=50,
                author="user2",
                status=ExtractionStatus.NO_URL,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 1
        assert result["filtered_articles"][0].story_id == 1

    def test_filter_removes_skipped_articles(self):
        """Test filter removes articles with SKIPPED status.

        Given: Mix of SUCCESS and SKIPPED articles
        When: filter_articles node is executed
        Then: Only SUCCESS articles are kept
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="HTML Article",
                url="https://example.com/article",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="Article content",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=2,
                title="PDF Document",
                url="https://example.com/doc.pdf",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=80,
                author="user2",
                status=ExtractionStatus.SKIPPED,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 1
        assert result["filtered_articles"][0].story_id == 1


class TestFilterArticlesEmptyInput:
    """Tests for filter_articles handling empty inputs."""

    def test_filter_empty_articles_list(self):
        """Test filter handles empty articles list.

        Given: Empty articles list
        When: filter_articles node is executed
        Then: Empty filtered_articles list is returned
        """
        # Arrange
        state = {"articles": []}

        # Act
        result = filter_articles(state)

        # Assert
        assert "filtered_articles" in result
        assert result["filtered_articles"] == []

    def test_filter_all_articles_removed(self):
        """Test filter when all articles are filtered out.

        Given: Articles all with FAILED status
        When: filter_articles node is executed
        Then: Empty filtered_articles list is returned
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Failed 1",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                status=ExtractionStatus.FAILED,
            ),
            Article(
                story_id=2,
                title="Failed 2",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                status=ExtractionStatus.FAILED,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 0


class TestFilterArticlesLogging:
    """Tests for filter_articles logging behavior."""

    def test_filter_logs_filtering_stats(self, caplog):
        """Test filter logs filtering statistics.

        Given: Articles with mix of statuses
        When: filter_articles node is executed
        Then: Filtering statistics are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        articles = [
            Article(
                story_id=1,
                title="Success 1",
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
                title="Failed 1",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                status=ExtractionStatus.FAILED,
            ),
            Article(
                story_id=3,
                title="Success 2",
                url="https://example.com/3",
                hn_url="https://news.ycombinator.com/item?id=3",
                hn_score=200,
                author="user3",
                content="More content",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert any("3" in record.message and "2" in record.message for record in caplog.records)
        assert len(result["filtered_articles"]) == 2

    def test_filter_logs_status_breakdown(self, caplog):
        """Test filter logs breakdown of removed articles by status.

        Given: Articles with different statuses
        When: filter_articles node is executed
        Then: Status breakdown is logged in debug mode
        """
        # Arrange
        import logging

        caplog.set_level(logging.DEBUG)
        articles = [
            Article(
                story_id=1,
                title="Success",
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
                title="Failed",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                status=ExtractionStatus.FAILED,
            ),
            Article(
                story_id=3,
                title="No URL",
                url=None,
                hn_url="https://news.ycombinator.com/item?id=3",
                hn_score=50,
                author="user3",
                status=ExtractionStatus.NO_URL,
            ),
        ]
        state = {"articles": articles}

        # Act
        filter_articles(state)

        # Assert
        assert any("Removed by status" in record.message for record in caplog.records)


class TestFilterArticlesEdgeCases:
    """Tests for filter_articles edge cases."""

    def test_filter_preserves_article_order(self):
        """Test filter preserves article order.

        Given: Articles in specific order
        When: filter_articles node is executed
        Then: Order is preserved in filtered list
        """
        # Arrange
        articles = [
            Article(
                story_id=3,
                title="Third",
                url="https://example.com/3",
                hn_url="https://news.ycombinator.com/item?id=3",
                hn_score=200,
                author="user3",
                content="Content 3",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
            Article(
                story_id=1,
                title="First",
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
                title="Second",
                url="https://example.com/2",
                hn_url="https://news.ycombinator.com/item?id=2",
                hn_score=150,
                author="user2",
                content="Content 2",
                word_count=2,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 3
        assert result["filtered_articles"][0].story_id == 3
        assert result["filtered_articles"][1].story_id == 1
        assert result["filtered_articles"][2].story_id == 2

    def test_filter_articles_without_content_but_success_status(self):
        """Test filter removes SUCCESS articles without content.

        Given: Article with SUCCESS status but no content
        When: filter_articles node is executed
        Then: Article is removed (has_content check)
        """
        # Arrange
        articles = [
            Article(
                story_id=1,
                title="Empty Content",
                url="https://example.com/1",
                hn_url="https://news.ycombinator.com/item?id=1",
                hn_score=100,
                author="user1",
                content="",  # Empty content
                word_count=0,
                status=ExtractionStatus.SUCCESS,
            ),
        ]
        state = {"articles": articles}

        # Act
        result = filter_articles(state)

        # Assert
        assert len(result["filtered_articles"]) == 0
