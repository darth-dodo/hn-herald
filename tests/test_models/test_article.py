"""Tests for Article model and ExtractionStatus enum."""

import pytest

from hn_herald.models.article import (
    Article,
    ArticleFetchError,
    ArticleLoaderError,
    ArticleParseError,
    ExtractionStatus,
)

# =============================================================================
# ExtractionStatus Enum Tests
# =============================================================================


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_extraction_status_values_exist(self):
        """All expected enum values should exist."""
        assert ExtractionStatus.SUCCESS == "success"
        assert ExtractionStatus.SKIPPED == "skipped"
        assert ExtractionStatus.FAILED == "failed"
        assert ExtractionStatus.PAYWALLED == "paywalled"
        assert ExtractionStatus.NO_URL == "no_url"
        assert ExtractionStatus.EMPTY == "empty"

    def test_extraction_status_is_str_enum(self):
        """ExtractionStatus should be a string enum."""
        assert isinstance(ExtractionStatus.SUCCESS, str)
        assert isinstance(ExtractionStatus.SUCCESS.value, str)

    def test_extraction_status_count(self):
        """Should have exactly 6 status values."""
        assert len(ExtractionStatus) == 6


# =============================================================================
# Article Model Validation Tests
# =============================================================================


class TestArticleModelValidation:
    """Tests for Article model validation."""

    def test_article_model_required_fields(self):
        """Article should require story_id, title, hn_url, hn_score, author."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
        )
        assert article.story_id == 12345
        assert article.title == "Test Article"
        assert article.hn_url == "https://news.ycombinator.com/item?id=12345"
        assert article.hn_score == 100
        assert article.author == "testuser"

    def test_article_model_default_values(self):
        """Article should have correct default values."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
        )
        assert article.url is None
        assert article.hn_comments == 0
        assert article.content is None
        assert article.word_count == 0
        assert article.status == ExtractionStatus.SUCCESS
        assert article.error_message is None
        assert article.domain is None
        assert article.hn_text is None

    def test_article_model_optional_fields(self):
        """Article should accept all optional fields."""
        article = Article(
            story_id=12345,
            title="Test Article",
            url="https://example.com/article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            hn_comments=50,
            author="testuser",
            content="Article content here",
            word_count=150,
            status=ExtractionStatus.SUCCESS,
            error_message=None,
            domain="example.com",
            hn_text="HN text content",
        )
        assert article.url == "https://example.com/article"
        assert article.hn_comments == 50
        assert article.content == "Article content here"
        assert article.word_count == 150
        assert article.domain == "example.com"
        assert article.hn_text == "HN text content"

    def test_article_model_score_ge_zero(self):
        """hn_score should be >= 0."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=0,
            author="testuser",
        )
        assert article.hn_score == 0

    def test_article_model_invalid_score_raises(self):
        """hn_score < 0 should raise validation error."""
        with pytest.raises(ValueError):
            Article(
                story_id=12345,
                title="Test Article",
                hn_url="https://news.ycombinator.com/item?id=12345",
                hn_score=-1,
                author="testuser",
            )

    def test_article_model_ignores_extra_fields(self):
        """Article should ignore unknown fields."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            unknown_field="should be ignored",
        )
        assert not hasattr(article, "unknown_field")


# =============================================================================
# Article Computed Properties Tests
# =============================================================================


class TestArticleComputedProperties:
    """Tests for Article computed properties."""

    def test_article_has_content_with_content(self):
        """has_content should return True when content exists."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            content="Some article content",
        )
        assert article.has_content is True

    def test_article_has_content_with_hn_text(self):
        """has_content should return True when hn_text exists."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            hn_text="Ask HN text content",
        )
        assert article.has_content is True

    def test_article_has_content_empty(self):
        """has_content should return False when both content and hn_text are None."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
        )
        assert article.has_content is False

    def test_article_has_content_empty_string(self):
        """has_content should return False when content is empty string."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            content="",
        )
        assert article.has_content is False

    def test_article_display_content_prefers_content(self):
        """display_content should return content over hn_text."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            content="Article content",
            hn_text="HN text",
        )
        assert article.display_content == "Article content"

    def test_article_display_content_fallback_hn_text(self):
        """display_content should return hn_text when no content."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            hn_text="HN text content",
        )
        assert article.display_content == "HN text content"

    def test_article_display_content_none(self):
        """display_content should return None when both missing."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
        )
        assert article.display_content is None


# =============================================================================
# Article Status Tests
# =============================================================================


class TestArticleStatus:
    """Tests for Article status handling."""

    def test_article_success_status_default(self):
        """SUCCESS should be the default status."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
        )
        assert article.status == ExtractionStatus.SUCCESS

    def test_article_failed_status_with_error(self):
        """FAILED status should include error_message."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            status=ExtractionStatus.FAILED,
            error_message="Connection timeout",
        )
        assert article.status == ExtractionStatus.FAILED
        assert article.error_message == "Connection timeout"

    def test_article_skipped_status(self):
        """SKIPPED status should work correctly."""
        article = Article(
            story_id=12345,
            title="Test Article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            status=ExtractionStatus.SKIPPED,
            error_message="Blocked domain: twitter.com",
        )
        assert article.status == ExtractionStatus.SKIPPED

    def test_article_no_url_status(self):
        """NO_URL status should be used for Ask HN posts."""
        article = Article(
            story_id=12345,
            title="Ask HN: Testing question",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            status=ExtractionStatus.NO_URL,
            hn_text="The question content...",
        )
        assert article.status == ExtractionStatus.NO_URL
        assert article.url is None
        assert article.hn_text == "The question content..."

    def test_article_paywalled_status(self):
        """PAYWALLED status should work correctly."""
        article = Article(
            story_id=12345,
            title="Test Article",
            url="https://nytimes.com/article",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            status=ExtractionStatus.PAYWALLED,
        )
        assert article.status == ExtractionStatus.PAYWALLED

    def test_article_empty_status(self):
        """EMPTY status should be used when no content extracted."""
        article = Article(
            story_id=12345,
            title="Test Article",
            url="https://example.com/empty-page",
            hn_url="https://news.ycombinator.com/item?id=12345",
            hn_score=100,
            author="testuser",
            status=ExtractionStatus.EMPTY,
            error_message="No content could be extracted",
        )
        assert article.status == ExtractionStatus.EMPTY


# =============================================================================
# Exception Tests
# =============================================================================


class TestArticleExceptions:
    """Tests for Article exception classes."""

    def test_article_loader_error_base(self):
        """ArticleLoaderError should be the base exception."""
        error = ArticleLoaderError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)

    def test_article_fetch_error(self):
        """ArticleFetchError should include URL."""
        error = ArticleFetchError("https://example.com", "Connection refused")
        assert error.url == "https://example.com"
        assert "https://example.com" in str(error)
        assert "Connection refused" in str(error)
        assert isinstance(error, ArticleLoaderError)

    def test_article_parse_error(self):
        """ArticleParseError should include URL."""
        error = ArticleParseError("https://example.com", "Invalid HTML")
        assert error.url == "https://example.com"
        assert "https://example.com" in str(error)
        assert "Invalid HTML" in str(error)
        assert isinstance(error, ArticleLoaderError)

    def test_fetch_error_inherits_from_loader_error(self):
        """ArticleFetchError should inherit from ArticleLoaderError."""
        error = ArticleFetchError("https://example.com", "error")
        assert isinstance(error, ArticleLoaderError)
        assert isinstance(error, Exception)

    def test_parse_error_inherits_from_loader_error(self):
        """ArticleParseError should inherit from ArticleLoaderError."""
        error = ArticleParseError("https://example.com", "error")
        assert isinstance(error, ArticleLoaderError)
        assert isinstance(error, Exception)
