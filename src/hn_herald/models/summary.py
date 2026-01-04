"""Summary data models for LLM-generated article summaries.

This module defines the Pydantic models for AI-generated summaries, the
SummarizationStatus enum for tracking summarization outcomes, and exception
classes for LLM service errors.
"""

from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator

from hn_herald.models.article import Article


class SummarizationStatus(str, Enum):
    """Status of article summarization.

    Tracks the outcome of attempting to summarize an article using an LLM.

    Attributes:
        SUCCESS: Summary generated successfully.
        NO_CONTENT: Article has no content to summarize.
        API_ERROR: LLM API request failed.
        PARSE_ERROR: Failed to parse LLM response.
        CACHED: Summary retrieved from cache.
    """

    SUCCESS = "success"
    NO_CONTENT = "no_content"
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    CACHED = "cached"


class ArticleSummary(BaseModel):
    """LLM-generated summary of an article.

    Represents the structured output from an LLM summarization request.
    Contains the summary text, key points, and technology tags.

    Attributes:
        summary: 2-3 sentence summary of the article (20-500 chars).
        key_points: 1-5 key takeaways from the article.
        tech_tags: Up to 10 technology/topic tags.

    Example:
        >>> summary = ArticleSummary(
        ...     summary="This article discusses new Python 3.13 features.",
        ...     key_points=["JIT compiler added", "GIL removal progress"],
        ...     tech_tags=["python", "performance"],
        ... )
        >>> len(summary.key_points)
        2
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
        "str_strip_whitespace": True,
    }

    summary: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="2-3 sentence summary of the article",
    )
    key_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Key takeaways from the article",
    )
    tech_tags: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Technology/topic tags for the article",
    )

    @field_validator("key_points", mode="before")
    @classmethod
    def validate_key_points_not_empty(cls, v: list[str]) -> list[str]:
        """Validate that key_points list is not empty and items are non-empty.

        Args:
            v: List of key points to validate.

        Returns:
            Validated list with empty strings filtered out.

        Raises:
            ValueError: If no valid key points remain after filtering.
        """
        if not v:
            raise ValueError("key_points must contain at least 1 item")
        # Filter out empty strings
        filtered = [point.strip() for point in v if point and point.strip()]
        if not filtered:
            raise ValueError("key_points must contain at least 1 non-empty item")
        return filtered

    @field_validator("tech_tags", mode="before")
    @classmethod
    def validate_tech_tags(cls, v: list[str]) -> list[str]:
        """Validate and normalize tech tags.

        Args:
            v: List of tech tags to validate.

        Returns:
            Normalized list of lowercase tags with empty strings filtered out.
        """
        if not v:
            return []
        # Filter empty strings and normalize to lowercase
        return [tag.strip().lower() for tag in v if tag and tag.strip()]


class SummarizedArticle(BaseModel):
    """Article with its LLM-generated summary.

    Wrapper model combining an Article with its summarization result.
    Tracks the summarization status and any error messages.

    Attributes:
        article: The original Article model.
        summary_data: LLM-generated summary (None if summarization failed).
        summarization_status: Outcome status of summarization.
        error_message: Error details if summarization failed.

    Example:
        >>> from hn_herald.models.article import Article, ExtractionStatus
        >>> article = Article(
        ...     story_id=123,
        ...     title="Test",
        ...     hn_url="https://news.ycombinator.com/item?id=123",
        ...     hn_score=100,
        ...     author="user",
        ...     content="Article content...",
        ...     word_count=50,
        ...     status=ExtractionStatus.SUCCESS,
        ... )
        >>> summary_data = ArticleSummary(
        ...     summary="A test summary that is at least twenty characters.",
        ...     key_points=["Point one"],
        ...     tech_tags=["testing"],
        ... )
        >>> summarized = SummarizedArticle(
        ...     article=article,
        ...     summary_data=summary_data,
        ...     summarization_status=SummarizationStatus.SUCCESS,
        ... )
        >>> summarized.has_summary
        True
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
    }

    article: Article = Field(..., description="The original Article model")
    summary_data: ArticleSummary | None = Field(default=None, description="LLM-generated summary")
    summarization_status: SummarizationStatus = Field(
        ..., description="Outcome status of summarization"
    )
    error_message: str | None = Field(
        default=None, description="Error details if summarization failed"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_summary(self) -> bool:
        """Check if article has a valid summary.

        Returns:
            True if summary_data exists and status indicates success or cached.
        """
        return self.summary_data is not None and self.summarization_status in (
            SummarizationStatus.SUCCESS,
            SummarizationStatus.CACHED,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_summary(self) -> str | None:
        """Get summary text for display purposes.

        Returns:
            Summary text if available, otherwise None.
        """
        if self.summary_data is not None:
            return self.summary_data.summary
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_key_points(self) -> list[str]:
        """Get key points for display purposes.

        Returns:
            List of key points if available, otherwise empty list.
        """
        if self.summary_data is not None:
            return self.summary_data.key_points
        return []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def display_tags(self) -> list[str]:
        """Get tech tags for display purposes.

        Returns:
            List of tech tags if available, otherwise empty list.
        """
        if self.summary_data is not None:
            return self.summary_data.tech_tags
        return []


# =============================================================================
# Exception Classes
# =============================================================================


class LLMServiceError(Exception):
    """Base exception for LLM service errors.

    All LLM-related exceptions inherit from this class to enable
    catching any LLM error with a single except clause.
    """


class LLMRateLimitError(LLMServiceError):
    """LLM API rate limit exceeded.

    Raised when the LLM API returns a rate limit error (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying (None if not provided).
    """

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize LLMRateLimitError.

        Args:
            message: Error message describing the rate limit.
            retry_after: Seconds to wait before retrying.
        """
        self.retry_after = retry_after
        super().__init__(message)


class LLMAPIError(LLMServiceError):
    """LLM API request failed.

    Raised when the LLM API returns an error response.

    Attributes:
        status_code: HTTP status code from the API response.
    """

    def __init__(self, message: str, status_code: int) -> None:
        """Initialize LLMAPIError.

        Args:
            message: Error message describing the API error.
            status_code: HTTP status code from the API response.
        """
        self.status_code = status_code
        super().__init__(f"LLM API error (HTTP {status_code}): {message}")


class LLMParseError(LLMServiceError):
    """Failed to parse LLM response.

    Raised when the LLM response cannot be parsed into the expected format.

    Attributes:
        raw_output: The raw LLM output that failed to parse.
    """

    def __init__(self, message: str, raw_output: str) -> None:
        """Initialize LLMParseError.

        Args:
            message: Error message describing the parse failure.
            raw_output: The raw LLM output that failed to parse.
        """
        self.raw_output = raw_output
        super().__init__(f"Failed to parse LLM response: {message}")
