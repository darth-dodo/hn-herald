"""Article extraction data models.

This module defines the Pydantic models for extracted article content and the
ExtractionStatus enum for tracking extraction outcomes. These models bridge
the gap between HN stories and AI summarization.
"""

from enum import Enum

from pydantic import BaseModel, Field, computed_field


class ExtractionStatus(str, Enum):
    """Status of article content extraction.

    Tracks the outcome of attempting to extract content from a story URL.

    Attributes:
        SUCCESS: Content extracted successfully.
        SKIPPED: Domain or URL type not supported (e.g., Twitter, PDF).
        FAILED: Extraction failed due to network or parsing error.
        PAYWALLED: Content is behind a paywall.
        NO_URL: Story has no external URL (e.g., Ask HN).
        EMPTY: Page loaded but no meaningful content extracted.
    """

    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    PAYWALLED = "paywalled"
    NO_URL = "no_url"
    EMPTY = "empty"


class Article(BaseModel):
    """Extracted article content with metadata.

    Represents an article extracted from a Story URL, ready for
    AI summarization. Tracks extraction status and errors.

    Attributes:
        story_id: HN story ID reference.
        title: Story title from HN.
        url: Original article URL (None for Ask HN).
        hn_url: HN discussion URL.
        hn_score: HN upvote score.
        hn_comments: HN comment count.
        author: HN story author username.
        content: Extracted article text content.
        word_count: Word count of extracted content.
        status: Extraction outcome status.
        error_message: Error details if extraction failed.
        domain: Extracted domain from URL.
        hn_text: HN post text content (for Ask HN/jobs).

    Example:
        >>> article = Article(
        ...     story_id=39856302,
        ...     title="Example Article",
        ...     url="https://example.com/article",
        ...     hn_url="https://news.ycombinator.com/item?id=39856302",
        ...     hn_score=142,
        ...     author="testuser",
        ...     content="Article content here...",
        ...     word_count=250,
        ... )
        >>> article.has_content
        True
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
        "str_strip_whitespace": True,
    }

    # Story reference fields (from MVP-1 Story model)
    story_id: int = Field(..., description="HN story ID reference")
    title: str = Field(..., description="Story title from HN")
    url: str | None = Field(default=None, description="Original article URL")
    hn_url: str = Field(..., description="HN discussion URL")
    hn_score: int = Field(..., ge=0, description="HN upvote score")
    hn_comments: int = Field(default=0, ge=0, description="HN comment count")
    author: str = Field(..., description="HN story author username")

    # Extracted content fields
    content: str | None = Field(default=None, description="Extracted article text content")
    word_count: int = Field(default=0, ge=0, description="Word count of extracted content")

    # Extraction metadata
    status: ExtractionStatus = Field(
        default=ExtractionStatus.SUCCESS,
        description="Extraction outcome status",
    )
    error_message: str | None = Field(
        default=None, description="Error details if extraction failed"
    )
    domain: str | None = Field(default=None, description="Extracted domain from URL")

    # HN text content (for Ask HN, Jobs, etc.)
    hn_text: str | None = Field(default=None, description="HN post text content")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_content(self) -> bool:
        """Check if article has extractable content.

        Returns:
            True if content or hn_text exists and is non-empty.
        """
        return bool(self.content) or bool(self.hn_text)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_content(self) -> str | None:
        """Get content for display purposes.

        Prefers extracted article content over HN text.

        Returns:
            Article content if available, otherwise HN text, or None.
        """
        return self.content or self.hn_text


class ArticleLoaderError(Exception):
    """Base exception for article loader errors."""


class ArticleFetchError(ArticleLoaderError):
    """Error fetching article content from URL.

    Attributes:
        url: The URL that failed to fetch.
    """

    def __init__(self, url: str, message: str) -> None:
        """Initialize ArticleFetchError.

        Args:
            url: The URL that failed to fetch.
            message: Error message describing the failure.
        """
        self.url = url
        super().__init__(f"Failed to fetch {url}: {message}")


class ArticleParseError(ArticleLoaderError):
    """Error parsing article content from HTML.

    Attributes:
        url: The URL whose content failed to parse.
    """

    def __init__(self, url: str, message: str) -> None:
        """Initialize ArticleParseError.

        Args:
            url: The URL whose content failed to parse.
            message: Error message describing the parsing failure.
        """
        self.url = url
        super().__init__(f"Failed to parse {url}: {message}")
