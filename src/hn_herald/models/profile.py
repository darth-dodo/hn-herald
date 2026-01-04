"""User profile model for relevance scoring preferences.

This module defines the UserProfile Pydantic model for storing user
interest and disinterest tags used in article relevance scoring.
"""

from pydantic import BaseModel, Field, field_validator, model_validator

from hn_herald.models.story import StoryType


class UserProfile(BaseModel):
    """User preferences for article relevance scoring and digest generation.

    Stores interest and disinterest tags used to calculate
    personalized relevance scores, along with fetch preferences.

    Attributes:
        interest_tags: Tags for topics user wants to see more of.
        disinterest_tags: Tags for topics user wants to filter out.
        min_score: Minimum final score threshold (0-1).
        max_articles: Maximum number of articles in digest.
        fetch_type: Type of stories to fetch (TOP, NEW, BEST, etc.).
        fetch_count: Number of stories to fetch from HN API.

    Example:
        >>> profile = UserProfile(
        ...     interest_tags=["python", "ai", "rust"],
        ...     disinterest_tags=["crypto", "blockchain"],
        ...     min_score=0.3,
        ...     max_articles=10,
        ...     fetch_type=StoryType.TOP,
        ...     fetch_count=30,
        ... )
        >>> "python" in profile.interest_tags
        True
    """

    model_config = {
        "frozen": False,
        "extra": "ignore",
        "str_strip_whitespace": True,
    }

    # Relevance scoring preferences
    interest_tags: list[str] = Field(
        default_factory=list,
        description="Tags for topics to see more of",
        max_length=50,
    )
    disinterest_tags: list[str] = Field(
        default_factory=list,
        description="Tags for topics to filter out",
        max_length=50,
    )
    min_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum final score threshold (0-1)",
    )

    # Digest generation preferences
    max_articles: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of articles in digest",
    )
    fetch_type: StoryType = Field(
        default=StoryType.TOP,
        description="Type of HN stories to fetch",
    )
    fetch_count: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of stories to fetch from HN API",
    )

    @field_validator("interest_tags", "disinterest_tags", mode="before")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase and remove duplicates.

        Args:
            v: List of tags to normalize.

        Returns:
            Deduplicated list of lowercase tags.
        """
        if not v:
            return []
        # Normalize to lowercase and deduplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for tag in v:
            normalized = tag.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

    @model_validator(mode="after")
    def validate_no_tag_overlap(self) -> "UserProfile":
        """Ensure interest and disinterest tags do not overlap.

        Returns:
            The validated UserProfile instance.

        Raises:
            ValueError: If any tags appear in both interest and disinterest lists.
        """
        if not self.interest_tags or not self.disinterest_tags:
            return self

        overlap = set(self.interest_tags) & set(self.disinterest_tags)
        if overlap:
            raise ValueError(
                f"Tags cannot be in both interest and disinterest lists: {sorted(overlap)}"
            )
        return self

    @property
    def has_preferences(self) -> bool:
        """Check if user has defined any preferences.

        Returns:
            True if user has interest or disinterest tags.
        """
        return bool(self.interest_tags or self.disinterest_tags)
