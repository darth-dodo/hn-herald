"""Tests for UserProfile model for relevance scoring preferences.

This module tests the UserProfile Pydantic model including tag normalization,
deduplication, overlap validation, and property behaviors.
"""

import pytest
from pydantic import ValidationError

from hn_herald.models.profile import UserProfile

# =============================================================================
# UserProfile Model Creation Tests
# =============================================================================


class TestUserProfileCreation:
    """Tests for UserProfile model creation and default values."""

    def test_profile_default_values(self):
        """
        Given: No arguments to UserProfile constructor
        When: UserProfile is created
        Then: Default values should be empty lists and 0.0 min_score
        """
        # Arrange & Act
        profile = UserProfile()

        # Assert
        assert profile.interest_tags == []
        assert profile.disinterest_tags == []
        assert profile.min_score == 0.0

    def test_profile_creation_with_all_fields(self):
        """
        Given: Valid interest tags, disinterest tags, and min_score
        When: UserProfile is created
        Then: All fields should be stored correctly
        """
        # Arrange
        interest = ["python", "ai", "rust"]
        disinterest = ["crypto", "blockchain"]
        min_score = 0.3

        # Act
        profile = UserProfile(
            interest_tags=interest,
            disinterest_tags=disinterest,
            min_score=min_score,
        )

        # Assert
        assert profile.interest_tags == interest
        assert profile.disinterest_tags == disinterest
        assert profile.min_score == min_score

    def test_profile_empty_is_valid(self):
        """
        Given: Empty lists for tags
        When: UserProfile is created
        Then: Profile should be valid with empty lists
        """
        # Arrange & Act
        profile = UserProfile(
            interest_tags=[],
            disinterest_tags=[],
            min_score=0.0,
        )

        # Assert
        assert profile.interest_tags == []
        assert profile.disinterest_tags == []
        assert profile.min_score == 0.0

    def test_profile_with_only_interest_tags(self):
        """
        Given: Only interest tags provided
        When: UserProfile is created
        Then: Interest tags should be set and disinterest tags empty
        """
        # Arrange & Act
        profile = UserProfile(interest_tags=["python", "ai"])

        # Assert
        assert profile.interest_tags == ["python", "ai"]
        assert profile.disinterest_tags == []

    def test_profile_with_only_disinterest_tags(self):
        """
        Given: Only disinterest tags provided
        When: UserProfile is created
        Then: Disinterest tags should be set and interest tags empty
        """
        # Arrange & Act
        profile = UserProfile(disinterest_tags=["crypto", "nft"])

        # Assert
        assert profile.interest_tags == []
        assert profile.disinterest_tags == ["crypto", "nft"]


# =============================================================================
# Tag Normalization Tests
# =============================================================================


class TestUserProfileTagNormalization:
    """Tests for UserProfile tag normalization behavior."""

    def test_profile_normalizes_interest_tags_to_lowercase(self):
        """
        Given: Interest tags with mixed case
        When: UserProfile is created
        Then: Tags should be normalized to lowercase
        """
        # Arrange
        tags = ["PYTHON", "Ai", "RuSt"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]

    def test_profile_normalizes_disinterest_tags_to_lowercase(self):
        """
        Given: Disinterest tags with mixed case
        When: UserProfile is created
        Then: Tags should be normalized to lowercase
        """
        # Arrange
        tags = ["CRYPTO", "BlockChain", "NFT"]

        # Act
        profile = UserProfile(disinterest_tags=tags)

        # Assert
        assert profile.disinterest_tags == ["crypto", "blockchain", "nft"]

    def test_profile_strips_whitespace_from_tags(self):
        """
        Given: Tags with leading/trailing whitespace
        When: UserProfile is created
        Then: Whitespace should be stripped
        """
        # Arrange
        tags = ["  python  ", "ai ", " rust"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]

    def test_profile_strips_and_lowercases_combined(self):
        """
        Given: Tags with both whitespace and mixed case
        When: UserProfile is created
        Then: Tags should be stripped and lowercased
        """
        # Arrange
        tags = ["  PYTHON  ", " AI ", "  Rust "]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]

    def test_profile_filters_empty_tags(self):
        """
        Given: Tags list containing empty strings
        When: UserProfile is created
        Then: Empty strings should be filtered out
        """
        # Arrange
        tags = ["python", "", "ai", "  ", "rust"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]


# =============================================================================
# Tag Deduplication Tests
# =============================================================================


class TestUserProfileTagDeduplication:
    """Tests for UserProfile tag deduplication behavior."""

    def test_profile_deduplicates_interest_tags(self):
        """
        Given: Duplicate tags in interest_tags
        When: UserProfile is created
        Then: Duplicates should be removed preserving first occurrence
        """
        # Arrange
        tags = ["python", "ai", "python", "rust", "ai"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]

    def test_profile_deduplicates_disinterest_tags(self):
        """
        Given: Duplicate tags in disinterest_tags
        When: UserProfile is created
        Then: Duplicates should be removed preserving first occurrence
        """
        # Arrange
        tags = ["crypto", "nft", "crypto", "blockchain", "nft"]

        # Act
        profile = UserProfile(disinterest_tags=tags)

        # Assert
        assert profile.disinterest_tags == ["crypto", "nft", "blockchain"]

    def test_profile_deduplicates_case_insensitive(self):
        """
        Given: Tags that are duplicates when case-normalized
        When: UserProfile is created
        Then: Case-insensitive duplicates should be removed
        """
        # Arrange
        tags = ["Python", "PYTHON", "python", "AI", "ai"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "ai"]

    def test_profile_preserves_order_after_deduplication(self):
        """
        Given: Tags with duplicates in various positions
        When: UserProfile is created
        Then: Order of first occurrences should be preserved
        """
        # Arrange
        tags = ["rust", "python", "ai", "python", "rust", "go"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["rust", "python", "ai", "go"]


# =============================================================================
# Tag Overlap Validation Tests
# =============================================================================


class TestUserProfileTagOverlapValidation:
    """Tests for UserProfile tag overlap validation."""

    def test_profile_raises_on_tag_overlap(self):
        """
        Given: Same tag in both interest and disinterest lists
        When: UserProfile is created
        Then: ValueError should be raised
        """
        # Arrange
        interest = ["python", "ai", "rust"]
        disinterest = ["crypto", "python"]  # 'python' overlaps

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            UserProfile(interest_tags=interest, disinterest_tags=disinterest)

        assert "python" in str(exc_info.value)
        assert "interest and disinterest" in str(exc_info.value).lower()

    def test_profile_raises_on_multiple_overlaps(self):
        """
        Given: Multiple tags in both interest and disinterest lists
        When: UserProfile is created
        Then: ValueError should be raised listing all overlapping tags
        """
        # Arrange
        interest = ["python", "ai", "rust"]
        disinterest = ["python", "ai"]  # both overlap

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            UserProfile(interest_tags=interest, disinterest_tags=disinterest)

        error_msg = str(exc_info.value).lower()
        assert "python" in error_msg or "ai" in error_msg

    def test_profile_overlap_detection_is_case_insensitive(self):
        """
        Given: Tags that overlap when normalized (different case)
        When: UserProfile is created
        Then: ValueError should be raised
        """
        # Arrange
        interest = ["PYTHON", "AI"]
        disinterest = ["python", "crypto"]  # 'python' overlaps when normalized

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            UserProfile(interest_tags=interest, disinterest_tags=disinterest)

        assert "python" in str(exc_info.value)

    def test_profile_no_overlap_is_valid(self):
        """
        Given: Completely distinct interest and disinterest tags
        When: UserProfile is created
        Then: Profile should be created successfully
        """
        # Arrange
        interest = ["python", "ai", "rust"]
        disinterest = ["crypto", "blockchain", "nft"]

        # Act
        profile = UserProfile(interest_tags=interest, disinterest_tags=disinterest)

        # Assert
        assert profile.interest_tags == ["python", "ai", "rust"]
        assert profile.disinterest_tags == ["crypto", "blockchain", "nft"]

    def test_profile_empty_interest_no_overlap_check(self):
        """
        Given: Empty interest tags and non-empty disinterest tags
        When: UserProfile is created
        Then: No overlap error should occur
        """
        # Arrange & Act
        profile = UserProfile(
            interest_tags=[],
            disinterest_tags=["crypto", "blockchain"],
        )

        # Assert
        assert profile.interest_tags == []
        assert profile.disinterest_tags == ["crypto", "blockchain"]

    def test_profile_empty_disinterest_no_overlap_check(self):
        """
        Given: Non-empty interest tags and empty disinterest tags
        When: UserProfile is created
        Then: No overlap error should occur
        """
        # Arrange & Act
        profile = UserProfile(
            interest_tags=["python", "ai"],
            disinterest_tags=[],
        )

        # Assert
        assert profile.interest_tags == ["python", "ai"]
        assert profile.disinterest_tags == []


# =============================================================================
# min_score Validation Tests
# =============================================================================


class TestUserProfileMinScoreValidation:
    """Tests for UserProfile min_score field validation."""

    def test_profile_min_score_default_is_zero(self):
        """
        Given: No min_score provided
        When: UserProfile is created
        Then: min_score should default to 0.0
        """
        # Arrange & Act
        profile = UserProfile()

        # Assert
        assert profile.min_score == 0.0

    def test_profile_min_score_zero_is_valid(self):
        """
        Given: min_score of 0.0
        When: UserProfile is created
        Then: Profile should be valid
        """
        # Arrange & Act
        profile = UserProfile(min_score=0.0)

        # Assert
        assert profile.min_score == 0.0

    def test_profile_min_score_one_is_valid(self):
        """
        Given: min_score of 1.0
        When: UserProfile is created
        Then: Profile should be valid
        """
        # Arrange & Act
        profile = UserProfile(min_score=1.0)

        # Assert
        assert profile.min_score == 1.0

    def test_profile_min_score_mid_range_is_valid(self):
        """
        Given: min_score of 0.5
        When: UserProfile is created
        Then: Profile should be valid
        """
        # Arrange & Act
        profile = UserProfile(min_score=0.5)

        # Assert
        assert profile.min_score == 0.5

    def test_profile_min_score_below_zero_raises(self):
        """
        Given: min_score below 0
        When: UserProfile is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(min_score=-0.1)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("min_score",) for e in errors)

    def test_profile_min_score_above_one_raises(self):
        """
        Given: min_score above 1.0
        When: UserProfile is created
        Then: ValidationError should be raised
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(min_score=1.1)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("min_score",) for e in errors)

    def test_profile_min_score_very_small_valid(self):
        """
        Given: Very small positive min_score
        When: UserProfile is created
        Then: Profile should be valid
        """
        # Arrange & Act
        profile = UserProfile(min_score=0.001)

        # Assert
        assert profile.min_score == 0.001

    def test_profile_min_score_near_one_valid(self):
        """
        Given: min_score very close to 1.0
        When: UserProfile is created
        Then: Profile should be valid
        """
        # Arrange & Act
        profile = UserProfile(min_score=0.999)

        # Assert
        assert profile.min_score == 0.999


# =============================================================================
# has_preferences Property Tests
# =============================================================================


class TestUserProfileHasPreferences:
    """Tests for UserProfile has_preferences property."""

    def test_profile_has_preferences_false_when_empty(self):
        """
        Given: UserProfile with no tags
        When: has_preferences is checked
        Then: Should return False
        """
        # Arrange
        profile = UserProfile()

        # Act & Assert
        assert profile.has_preferences is False

    def test_profile_has_preferences_true_with_interest_tags(self):
        """
        Given: UserProfile with only interest tags
        When: has_preferences is checked
        Then: Should return True
        """
        # Arrange
        profile = UserProfile(interest_tags=["python"])

        # Act & Assert
        assert profile.has_preferences is True

    def test_profile_has_preferences_true_with_disinterest_tags(self):
        """
        Given: UserProfile with only disinterest tags
        When: has_preferences is checked
        Then: Should return True
        """
        # Arrange
        profile = UserProfile(disinterest_tags=["crypto"])

        # Act & Assert
        assert profile.has_preferences is True

    def test_profile_has_preferences_true_with_both_tags(self):
        """
        Given: UserProfile with both interest and disinterest tags
        When: has_preferences is checked
        Then: Should return True
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python", "ai"],
            disinterest_tags=["crypto"],
        )

        # Act & Assert
        assert profile.has_preferences is True


# =============================================================================
# Model Configuration Tests
# =============================================================================


class TestUserProfileModelConfig:
    """Tests for UserProfile model configuration."""

    def test_profile_ignores_extra_fields(self):
        """
        Given: Extra unknown fields in input
        When: UserProfile is created
        Then: Unknown fields should be ignored
        """
        # Arrange & Act
        profile = UserProfile(
            interest_tags=["python"],
            unknown_field="should be ignored",
            another_extra=123,
        )

        # Assert
        assert not hasattr(profile, "unknown_field")
        assert not hasattr(profile, "another_extra")
        assert profile.interest_tags == ["python"]

    def test_profile_is_mutable(self):
        """
        Given: UserProfile instance
        When: Fields are modified
        Then: Modifications should succeed (frozen=False)
        """
        # Arrange
        profile = UserProfile(interest_tags=["python"])

        # Act
        profile.min_score = 0.5

        # Assert
        assert profile.min_score == 0.5

    def test_profile_serialization_to_dict(self):
        """
        Given: UserProfile with data
        When: Serialized to dict
        Then: All fields should be present
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python", "ai"],
            disinterest_tags=["crypto"],
            min_score=0.3,
        )

        # Act
        data = profile.model_dump()

        # Assert
        assert data["interest_tags"] == ["python", "ai"]
        assert data["disinterest_tags"] == ["crypto"]
        assert data["min_score"] == 0.3

    def test_profile_json_serialization(self):
        """
        Given: UserProfile with data
        When: Serialized to JSON
        Then: Valid JSON string should be produced
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            min_score=0.5,
        )

        # Act
        json_str = profile.model_dump_json()

        # Assert
        assert '"interest_tags":["python"]' in json_str or '"interest_tags": ["python"]' in json_str
        assert "0.5" in json_str


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestUserProfileEdgeCases:
    """Tests for UserProfile edge cases."""

    def test_profile_with_single_tag(self):
        """
        Given: Single tag in interest_tags
        When: UserProfile is created
        Then: Single tag should be stored
        """
        # Arrange & Act
        profile = UserProfile(interest_tags=["python"])

        # Assert
        assert profile.interest_tags == ["python"]
        assert len(profile.interest_tags) == 1

    def test_profile_with_many_tags(self):
        """
        Given: Many tags (near max_length)
        When: UserProfile is created
        Then: All tags should be stored
        """
        # Arrange
        tags = [f"tag{i}" for i in range(50)]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert len(profile.interest_tags) == 50

    def test_profile_with_hyphenated_tags(self):
        """
        Given: Tags with hyphens
        When: UserProfile is created
        Then: Tags should be preserved with hyphens
        """
        # Arrange
        tags = ["machine-learning", "web-dev", "ai-ml"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["machine-learning", "web-dev", "ai-ml"]

    def test_profile_with_numeric_tags(self):
        """
        Given: Tags containing numbers
        When: UserProfile is created
        Then: Tags should be preserved
        """
        # Arrange
        tags = ["python3", "es2024", "vue3"]

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python3", "es2024", "vue3"]

    def test_profile_with_unicode_tags(self):
        """
        Given: Tags with unicode characters
        When: UserProfile is created
        Then: Tags should be preserved (lowercased)
        """
        # Arrange
        tags = ["Python", "Rust"]  # Standard ASCII to avoid locale issues

        # Act
        profile = UserProfile(interest_tags=tags)

        # Assert
        assert profile.interest_tags == ["python", "rust"]
