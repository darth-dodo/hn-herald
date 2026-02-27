"""HackerNews story data models.

This module defines the Pydantic models for HN story data and the StoryType enum
for type-safe API calls. These models validate data from the HN Firebase API
and provide computed properties for common operations.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class StoryType(StrEnum):
    """Supported HN story types.

    Each type corresponds to a specific HN API endpoint that returns
    story IDs sorted by the respective ranking algorithm.

    Attributes:
        TOP: Front page stories ranked by HN algorithm.
        NEW: Newest stories in chronological order.
        BEST: Best stories weighted by all-time performance.
        ASK: "Ask HN" discussion threads.
        SHOW: "Show HN" project showcases.
        JOB: Job postings from YC companies.
    """

    TOP = "top"
    NEW = "new"
    BEST = "best"
    ASK = "ask"
    SHOW = "show"
    JOB = "job"

    @property
    def endpoint(self) -> str:
        """Get the API endpoint path for this story type.

        Returns:
            The endpoint path with leading slash (e.g., '/topstories.json').
        """
        return f"/{self.value}stories.json"


class Story(BaseModel):
    """HackerNews story data model.

    Represents a story fetched from the HN API with all metadata
    needed for digest generation. Validates API response data and
    provides computed properties for common operations.

    Attributes:
        id: Unique story identifier from HackerNews.
        title: Story title as displayed on HN.
        url: External article URL (None for Ask HN, jobs, etc.).
        score: Current upvote score on HN.
        by: Username of the story author.
        time: Unix timestamp of story creation.
        descendants: Total comment count (None if not available).
        type: Item type from HN API (usually "story").
        kids: List of child comment IDs.
        text: HTML content for Ask HN posts or job listings.
        dead: True if the story has been killed by moderators.
        deleted: True if the story has been deleted by author.

    Example:
        >>> story = Story(
        ...     id=39856302,
        ...     title="Example Story",
        ...     url="https://example.com",
        ...     score=142,
        ...     by="testuser",
        ...     time=1709654321,
        ...     descendants=85,
        ...     type="story",
        ... )
        >>> story.hn_url
        'https://news.ycombinator.com/item?id=39856302'
        >>> story.has_external_url
        True
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",  # Ignore unknown fields from API
        "str_strip_whitespace": True,
    }

    id: int = Field(..., description="Unique story ID from HackerNews")
    title: str = Field(..., description="Story title")
    url: str | None = Field(default=None, description="External article URL")
    score: int = Field(..., ge=0, description="HN upvote score")
    by: str = Field(..., description="Author username")
    time: int = Field(..., description="Unix timestamp of creation")
    descendants: int | None = Field(default=None, ge=0, description="Total comment count")
    type: str = Field(default="story", description="Item type from HN API")
    kids: list[int] = Field(default_factory=list, description="Child comment IDs")
    text: str | None = Field(default=None, description="HTML content for Ask HN/jobs")
    dead: bool | None = Field(default=None, description="True if story is dead/killed")
    deleted: bool | None = Field(default=None, description="True if story is deleted")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def hn_url(self) -> str:
        """Generate the HackerNews discussion URL for this story.

        Returns:
            Full URL to the story's discussion page on HN.
        """
        return f"https://news.ycombinator.com/item?id={self.id}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_external_url(self) -> bool:
        """Check if the story has an external URL.

        Ask HN posts, job postings, and some other story types
        do not have external URLs.

        Returns:
            True if the story has a non-empty external URL.
        """
        return bool(self.url)
