"""Tests for Story model and StoryType enum.

This module tests the Pydantic Story model and StoryType enum
used for representing HackerNews stories.
"""

import pytest
from pydantic import ValidationError

from hn_herald.models.story import Story, StoryType


class TestStoryType:
    """Tests for StoryType enum."""

    def test_story_type_values(self):
        """Test that all StoryType enum values are correct."""
        # Arrange & Act & Assert
        assert StoryType.TOP.value == "top"
        assert StoryType.NEW.value == "new"
        assert StoryType.BEST.value == "best"
        assert StoryType.ASK.value == "ask"
        assert StoryType.SHOW.value == "show"
        assert StoryType.JOB.value == "job"

    def test_story_type_endpoint_property_top(self):
        """Test endpoint property returns correct path for TOP stories."""
        # Arrange
        story_type = StoryType.TOP

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/topstories.json"

    def test_story_type_endpoint_property_new(self):
        """Test endpoint property returns correct path for NEW stories."""
        # Arrange
        story_type = StoryType.NEW

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/newstories.json"

    def test_story_type_endpoint_property_best(self):
        """Test endpoint property returns correct path for BEST stories."""
        # Arrange
        story_type = StoryType.BEST

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/beststories.json"

    def test_story_type_endpoint_property_ask(self):
        """Test endpoint property returns correct path for ASK stories."""
        # Arrange
        story_type = StoryType.ASK

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/askstories.json"

    def test_story_type_endpoint_property_show(self):
        """Test endpoint property returns correct path for SHOW stories."""
        # Arrange
        story_type = StoryType.SHOW

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/showstories.json"

    def test_story_type_endpoint_property_job(self):
        """Test endpoint property returns correct path for JOB stories."""
        # Arrange
        story_type = StoryType.JOB

        # Act
        endpoint = story_type.endpoint

        # Assert
        assert endpoint == "/jobstories.json"

    def test_story_type_is_string_enum(self):
        """Test that StoryType is a string enum and can be used as string."""
        # Arrange
        story_type = StoryType.TOP

        # Act & Assert
        assert isinstance(story_type, str)
        assert story_type == "top"

    def test_story_type_all_values_have_endpoints(self):
        """Test that all StoryType values have valid endpoints."""
        # Arrange & Act & Assert
        for story_type in StoryType:
            endpoint = story_type.endpoint
            assert endpoint.startswith("/")
            assert endpoint.endswith("stories.json")


class TestStoryModel:
    """Tests for Story Pydantic model."""

    def test_story_model_creation_with_all_fields(self, sample_story_data):
        """Test Story model creation with all fields provided."""
        # Arrange - sample_story_data from fixture

        # Act
        story = Story.model_validate(sample_story_data)

        # Assert
        assert story.id == 39856302
        assert story.title == "Test Story Title"
        assert story.url == "https://example.com/article"
        assert story.score == 142
        assert story.by == "testuser"
        assert story.time == 1709654321
        assert story.descendants == 85
        assert story.type == "story"
        assert story.kids == [39856400, 39856401]

    def test_story_model_creation_with_optional_fields_missing(self, sample_story_data_minimal):
        """Test Story model creation with optional fields using defaults."""
        # Arrange - sample_story_data_minimal from fixture

        # Act
        story = Story.model_validate(sample_story_data_minimal)

        # Assert - required fields
        assert story.id == 39856303
        assert story.title == "Minimal Story"
        assert story.score == 50
        assert story.by == "minimaluser"
        assert story.time == 1709654322

        # Assert - optional fields have defaults
        assert story.url is None
        assert story.descendants is None  # Not provided in minimal data
        assert story.type == "story"
        assert story.kids == []
        assert story.text is None
        assert story.dead is None  # Not provided, defaults to None
        assert story.deleted is None  # Not provided, defaults to None

    def test_story_model_with_ask_hn_story(self, sample_story_data_ask_hn):
        """Test Story model with Ask HN story that has text but no URL."""
        # Arrange - sample_story_data_ask_hn from fixture

        # Act
        story = Story.model_validate(sample_story_data_ask_hn)

        # Assert
        assert story.id == 39856304
        assert story.title == "Ask HN: What are your favorite testing practices?"
        assert story.url is None
        assert story.text == "I'm curious about what testing approaches people use..."
        assert story.score == 75

    def test_story_hn_url_computed_property(self, sample_story_data):
        """Test hn_url computed property generates correct HN discussion URL."""
        # Arrange
        story = Story.model_validate(sample_story_data)

        # Act
        hn_url = story.hn_url

        # Assert
        assert hn_url == "https://news.ycombinator.com/item?id=39856302"

    def test_story_hn_url_computed_property_different_ids(self):
        """Test hn_url computed property works with different IDs."""
        # Arrange
        story1 = Story(id=12345, title="Test", score=10, by="user", time=1234567890)
        story2 = Story(id=99999999, title="Test 2", score=20, by="user2", time=1234567891)

        # Act & Assert
        assert story1.hn_url == "https://news.ycombinator.com/item?id=12345"
        assert story2.hn_url == "https://news.ycombinator.com/item?id=99999999"

    def test_story_has_external_url_true_when_url_exists(self, sample_story_data):
        """Test has_external_url returns True when URL is present."""
        # Arrange
        story = Story.model_validate(sample_story_data)

        # Act
        has_url = story.has_external_url

        # Assert
        assert has_url is True

    def test_story_has_external_url_false_when_url_is_none(self, sample_story_data_ask_hn):
        """Test has_external_url returns False when URL is None."""
        # Arrange
        story = Story.model_validate(sample_story_data_ask_hn)

        # Act
        has_url = story.has_external_url

        # Assert
        assert has_url is False

    def test_story_has_external_url_false_when_url_is_empty_string(self):
        """Test has_external_url returns False when URL is empty string."""
        # Arrange
        story = Story(
            id=12345,
            title="Empty URL Story",
            url="",
            score=10,
            by="user",
            time=1234567890,
        )

        # Act
        has_url = story.has_external_url

        # Assert
        assert has_url is False

    def test_story_model_validation_error_missing_required_id(self):
        """Test Story model raises error when id is missing."""
        # Arrange
        invalid_data = {
            "title": "Test",
            "score": 10,
            "by": "user",
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)

    def test_story_model_validation_error_missing_required_title(self):
        """Test Story model raises error when title is missing."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "score": 10,
            "by": "user",
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_story_model_validation_error_missing_required_score(self):
        """Test Story model raises error when score is missing."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "title": "Test",
            "by": "user",
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("score",) for e in errors)

    def test_story_model_validation_error_missing_required_by(self):
        """Test Story model raises error when by (author) is missing."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "title": "Test",
            "score": 10,
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("by",) for e in errors)

    def test_story_model_validation_error_missing_required_time(self):
        """Test Story model raises error when time is missing."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "title": "Test",
            "score": 10,
            "by": "user",
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("time",) for e in errors)

    def test_story_model_validation_error_negative_score(self):
        """Test Story model raises error for negative score."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "title": "Test",
            "score": -5,
            "by": "user",
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("score",) for e in errors)

    def test_story_model_validation_error_negative_descendants(self):
        """Test Story model raises error for negative descendants."""
        # Arrange
        invalid_data = {
            "id": 12345,
            "title": "Test",
            "score": 10,
            "by": "user",
            "time": 1234567890,
            "descendants": -1,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("descendants",) for e in errors)

    def test_story_model_validation_error_invalid_id_type(self):
        """Test Story model raises error for invalid id type."""
        # Arrange
        invalid_data = {
            "id": "not-an-integer",
            "title": "Test",
            "score": 10,
            "by": "user",
            "time": 1234567890,
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Story.model_validate(invalid_data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)

    def test_story_model_ignores_unknown_fields(self, sample_story_data):
        """Test Story model ignores unknown fields from API."""
        # Arrange
        data_with_extra = sample_story_data.copy()
        data_with_extra["unknown_field"] = "should be ignored"
        data_with_extra["another_unknown"] = 12345

        # Act
        story = Story.model_validate(data_with_extra)

        # Assert
        assert story.id == 39856302
        assert not hasattr(story, "unknown_field")
        assert not hasattr(story, "another_unknown")

    def test_story_model_dead_story(self, sample_dead_story_data):
        """Test Story model correctly handles dead flag."""
        # Arrange - sample_dead_story_data from fixture

        # Act
        story = Story.model_validate(sample_dead_story_data)

        # Assert
        assert story.dead is True
        assert story.deleted is None  # Not provided in fixture

    def test_story_model_serialization(self, sample_story_data):
        """Test Story model can be serialized to dict."""
        # Arrange
        story = Story.model_validate(sample_story_data)

        # Act
        data = story.model_dump()

        # Assert
        assert data["id"] == 39856302
        assert data["title"] == "Test Story Title"
        assert "hn_url" in data  # Computed field included
        assert "has_external_url" in data  # Computed field included

    def test_story_model_json_serialization(self, sample_story_data):
        """Test Story model can be serialized to JSON."""
        # Arrange
        story = Story.model_validate(sample_story_data)

        # Act
        json_str = story.model_dump_json()

        # Assert
        assert '"id":39856302' in json_str or '"id": 39856302' in json_str
        assert "Test Story Title" in json_str

    def test_story_model_with_empty_kids_list(self):
        """Test Story model handles empty kids list correctly."""
        # Arrange
        data = {
            "id": 12345,
            "title": "Test",
            "score": 10,
            "by": "user",
            "time": 1234567890,
            "kids": [],
        }

        # Act
        story = Story.model_validate(data)

        # Assert
        assert story.kids == []

    def test_story_model_with_large_kids_list(self):
        """Test Story model handles large kids list correctly."""
        # Arrange
        data = {
            "id": 12345,
            "title": "Test",
            "score": 10,
            "by": "user",
            "time": 1234567890,
            "kids": list(range(1000, 2000)),  # 1000 comment IDs
        }

        # Act
        story = Story.model_validate(data)

        # Assert
        assert len(story.kids) == 1000
        assert story.kids[0] == 1000
        assert story.kids[-1] == 1999

    def test_story_model_zero_score(self):
        """Test Story model accepts zero score."""
        # Arrange
        data = {
            "id": 12345,
            "title": "Zero Score Story",
            "score": 0,
            "by": "user",
            "time": 1234567890,
        }

        # Act
        story = Story.model_validate(data)

        # Assert
        assert story.score == 0

    def test_story_model_high_score(self):
        """Test Story model accepts very high score."""
        # Arrange
        data = {
            "id": 12345,
            "title": "Viral Story",
            "score": 10000,
            "by": "user",
            "time": 1234567890,
        }

        # Act
        story = Story.model_validate(data)

        # Assert
        assert story.score == 10000
