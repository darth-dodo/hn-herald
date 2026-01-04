"""Tests for HNClient async HTTP client.

This module tests the HNClient class for fetching stories from
the HackerNews Firebase API with mocked HTTP responses.
"""

import httpx
import pytest
import respx

from hn_herald.models.story import Story, StoryType
from hn_herald.services.hn_client import (
    HNAPIError,
    HNClient,
    HNClientError,
    HNTimeoutError,
)

# Test base URL used for mocking
TEST_BASE_URL = "https://hacker-news.firebaseio.com/v0"


class TestHNClientExceptions:
    """Tests for HNClient exception classes."""

    def test_hn_client_error_is_base_exception(self):
        """Test HNClientError is the base exception class."""
        # Arrange & Act
        error = HNClientError("Test error")

        # Assert
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_hn_api_error_includes_status_code(self):
        """Test HNAPIError includes status code in message."""
        # Arrange & Act
        error = HNAPIError(404, "Not found")

        # Assert
        assert error.status_code == 404
        assert "404" in str(error)
        assert "Not found" in str(error)

    def test_hn_api_error_inherits_from_client_error(self):
        """Test HNAPIError inherits from HNClientError."""
        # Arrange & Act
        error = HNAPIError(500, "Server error")

        # Assert
        assert isinstance(error, HNClientError)

    def test_hn_timeout_error_inherits_from_client_error(self):
        """Test HNTimeoutError inherits from HNClientError."""
        # Arrange & Act
        error = HNTimeoutError("Timeout")

        # Assert
        assert isinstance(error, HNClientError)


class TestHNClientContextManager:
    """Tests for HNClient context manager usage."""

    async def test_client_context_manager_entry(self):
        """Test HNClient can be used as async context manager."""
        # Arrange & Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            # Assert
            assert client._client is not None
            assert client._semaphore is not None

    async def test_client_context_manager_exit_closes_client(self):
        """Test HNClient closes HTTP client on context exit."""
        # Arrange
        client = HNClient(base_url=TEST_BASE_URL)

        # Act
        async with client:
            internal_client = client._client
            assert internal_client is not None

        # Assert - client should be closed after exit
        assert client._client is None
        assert client._semaphore is None

    async def test_client_raises_error_when_used_without_context_manager(self):
        """Test HNClient raises error when used outside context manager."""
        # Arrange
        client = HNClient(base_url=TEST_BASE_URL)

        # Act & Assert
        with pytest.raises(RuntimeError, match="context manager"):
            await client.fetch_story_ids(StoryType.TOP)

    async def test_client_custom_parameters(self):
        """Test HNClient accepts custom parameters."""
        # Arrange & Act
        async with HNClient(
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5,
            max_concurrent=20,
        ) as client:
            # Assert
            assert client.base_url == "https://custom.api.com"
            assert client.timeout == 60
            assert client.max_retries == 5
            assert client.max_concurrent == 20


class TestFetchStoryIds:
    """Tests for HNClient.fetch_story_ids method."""

    @respx.mock
    async def test_fetch_story_ids_returns_list_of_ids(self, mock_story_ids):
        """Test fetch_story_ids returns list of story IDs."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story_ids(StoryType.TOP)

        # Assert
        assert result == mock_story_ids
        assert len(result) == 5

    @respx.mock
    async def test_fetch_story_ids_with_limit_parameter(self, mock_story_ids):
        """Test fetch_story_ids respects limit parameter."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story_ids(StoryType.TOP, limit=3)

        # Assert
        assert len(result) == 3
        assert result == [1, 2, 3]

    @respx.mock
    async def test_fetch_story_ids_different_story_types(self):
        """Test fetch_story_ids works with different story types."""
        # Arrange
        story_types = [
            (StoryType.TOP, "/topstories.json"),
            (StoryType.NEW, "/newstories.json"),
            (StoryType.BEST, "/beststories.json"),
            (StoryType.ASK, "/askstories.json"),
            (StoryType.SHOW, "/showstories.json"),
            (StoryType.JOB, "/jobstories.json"),
        ]

        for _story_type, endpoint in story_types:
            respx.get(f"{TEST_BASE_URL}{endpoint}").mock(
                return_value=httpx.Response(200, json=[100, 101, 102])
            )

        # Act & Assert
        async with HNClient(base_url=TEST_BASE_URL) as client:
            for story_type, _ in story_types:
                result = await client.fetch_story_ids(story_type, limit=3)
                assert result == [100, 101, 102]

    @respx.mock
    async def test_fetch_story_ids_returns_empty_list_when_api_returns_empty(self):
        """Test fetch_story_ids returns empty list when API returns empty."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=[])
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story_ids(StoryType.TOP)

        # Assert
        assert result == []


class TestFetchStory:
    """Tests for HNClient.fetch_story method."""

    @respx.mock
    async def test_fetch_story_returns_story_object(self, sample_story_data):
        """Test fetch_story returns Story object for valid story."""
        # Arrange
        story_id = sample_story_data["id"]
        respx.get(f"{TEST_BASE_URL}/item/{story_id}.json").mock(
            return_value=httpx.Response(200, json=sample_story_data)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(story_id)

        # Assert
        assert isinstance(result, Story)
        assert result.id == story_id
        assert result.title == "Test Story Title"
        assert result.score == 142

    @respx.mock
    async def test_fetch_story_returns_none_for_null_response(self):
        """Test fetch_story returns None when API returns null (deleted story)."""
        # Arrange
        story_id = 12345
        respx.get(f"{TEST_BASE_URL}/item/{story_id}.json").mock(
            return_value=httpx.Response(200, content=b"null")
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(story_id)

        # Assert
        assert result is None

    @respx.mock
    async def test_fetch_story_returns_none_for_deleted_story(self, sample_deleted_story_data):
        """Test fetch_story returns None for deleted story."""
        # Arrange
        story_id = sample_deleted_story_data["id"]
        respx.get(f"{TEST_BASE_URL}/item/{story_id}.json").mock(
            return_value=httpx.Response(200, json=sample_deleted_story_data)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(story_id)

        # Assert
        assert result is None

    @respx.mock
    async def test_fetch_story_returns_none_for_dead_story(self, sample_dead_story_data):
        """Test fetch_story returns None for dead (flagged) story."""
        # Arrange
        story_id = sample_dead_story_data["id"]
        respx.get(f"{TEST_BASE_URL}/item/{story_id}.json").mock(
            return_value=httpx.Response(200, json=sample_dead_story_data)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(story_id)

        # Assert
        assert result is None

    @respx.mock
    async def test_fetch_story_returns_none_for_comment(self):
        """Test fetch_story returns None for non-story items (comments)."""
        # Arrange
        comment_data = {
            "id": 12345,
            "type": "comment",
            "by": "user",
            "time": 1234567890,
            "text": "This is a comment",
        }
        respx.get(f"{TEST_BASE_URL}/item/12345.json").mock(
            return_value=httpx.Response(200, json=comment_data)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(12345)

        # Assert
        assert result is None

    @respx.mock
    async def test_fetch_story_handles_job_type(self):
        """Test fetch_story accepts job type stories."""
        # Arrange
        job_data = {
            "id": 12345,
            "type": "job",
            "by": "company",
            "time": 1234567890,
            "title": "Hiring: Software Engineer",
            "score": 5,
            "url": "https://jobs.example.com",
        }
        respx.get(f"{TEST_BASE_URL}/item/12345.json").mock(
            return_value=httpx.Response(200, json=job_data)
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_story(12345)

        # Assert
        assert isinstance(result, Story)
        assert result.type == "job"


class TestFetchStories:
    """Tests for HNClient.fetch_stories method."""

    @respx.mock
    async def test_fetch_stories_combines_fetch_and_returns_stories(
        self, mock_story_ids, multiple_stories_data
    ):
        """Test fetch_stories fetches IDs and returns Story objects."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        for story_data in multiple_stories_data:
            respx.get(f"{TEST_BASE_URL}/item/{story_data['id']}.json").mock(
                return_value=httpx.Response(200, json=story_data)
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_stories(StoryType.TOP, limit=5)

        # Assert
        assert len(result) == 5
        assert all(isinstance(s, Story) for s in result)

    @respx.mock
    async def test_fetch_stories_filters_by_min_score(self, mock_story_ids, multiple_stories_data):
        """Test fetch_stories filters stories by minimum score."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        for story_data in multiple_stories_data:
            respx.get(f"{TEST_BASE_URL}/item/{story_data['id']}.json").mock(
                return_value=httpx.Response(200, json=story_data)
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            # min_score=100 should filter out stories with score < 100
            result = await client.fetch_stories(StoryType.TOP, limit=10, min_score=100)

        # Assert - only stories with score >= 100: 500, 200, 100
        assert len(result) == 3
        assert all(s.score >= 100 for s in result)

    @respx.mock
    async def test_fetch_stories_sorts_by_score_descending(
        self, mock_story_ids, multiple_stories_data
    ):
        """Test fetch_stories sorts results by score in descending order."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        for story_data in multiple_stories_data:
            respx.get(f"{TEST_BASE_URL}/item/{story_data['id']}.json").mock(
                return_value=httpx.Response(200, json=story_data)
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_stories(StoryType.TOP, limit=5)

        # Assert - should be sorted by score descending
        scores = [s.score for s in result]
        assert scores == sorted(scores, reverse=True)
        assert scores == [500, 200, 100, 25, 5]

    @respx.mock
    async def test_fetch_stories_respects_limit(self, mock_story_ids, multiple_stories_data):
        """Test fetch_stories respects the limit parameter."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        for story_data in multiple_stories_data:
            respx.get(f"{TEST_BASE_URL}/item/{story_data['id']}.json").mock(
                return_value=httpx.Response(200, json=story_data)
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_stories(StoryType.TOP, limit=2)

        # Assert
        assert len(result) == 2
        # With limit=2 and no min_score filter, only first 2 IDs fetched (1, 2)
        # Sorted by score descending: 500 (id=1), 100 (id=2)
        assert result[0].score == 500
        assert result[1].score == 100

    @respx.mock
    async def test_fetch_stories_handles_deleted_stories(self, mock_story_ids):
        """Test fetch_stories skips deleted/dead stories gracefully."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        # Mix of valid, deleted, and null responses
        respx.get(f"{TEST_BASE_URL}/item/1.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "type": "story",
                    "title": "Valid",
                    "score": 100,
                    "by": "user",
                    "time": 123,
                },
            )
        )
        respx.get(f"{TEST_BASE_URL}/item/2.json").mock(
            return_value=httpx.Response(200, json=None)  # Deleted
        )
        respx.get(f"{TEST_BASE_URL}/item/3.json").mock(
            return_value=httpx.Response(
                200,
                json={"id": 3, "deleted": True},  # Deleted flag
            )
        )
        respx.get(f"{TEST_BASE_URL}/item/4.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 4,
                    "type": "story",
                    "title": "Valid 2",
                    "score": 50,
                    "by": "user",
                    "time": 123,
                },
            )
        )
        respx.get(f"{TEST_BASE_URL}/item/5.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 5,
                    "type": "story",
                    "title": "Dead",
                    "score": 10,
                    "by": "user",
                    "time": 123,
                    "dead": True,
                },
            )
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_stories(StoryType.TOP, limit=10)

        # Assert - only 2 valid stories
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 4

    @respx.mock
    async def test_fetch_stories_returns_empty_list_when_no_ids(self):
        """Test fetch_stories returns empty list when no story IDs."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=[])
        )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            result = await client.fetch_stories(StoryType.TOP)

        # Assert
        assert result == []


class TestErrorHandling:
    """Tests for HNClient error handling."""

    @respx.mock
    async def test_timeout_raises_hn_timeout_error(self):
        """Test timeout raises HNTimeoutError."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        # Act & Assert
        async with HNClient(base_url=TEST_BASE_URL, max_retries=1) as client:
            with pytest.raises(HNTimeoutError):
                await client.fetch_story_ids(StoryType.TOP)

    @respx.mock
    async def test_http_error_raises_hn_api_error(self):
        """Test HTTP error raises HNAPIError."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        # Act & Assert
        async with HNClient(base_url=TEST_BASE_URL, max_retries=1) as client:
            with pytest.raises(HNAPIError) as exc_info:
                await client.fetch_story_ids(StoryType.TOP)

            assert exc_info.value.status_code == 500

    @respx.mock
    async def test_404_error_raises_hn_api_error(self):
        """Test 404 error raises HNAPIError."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        # Act & Assert
        async with HNClient(base_url=TEST_BASE_URL, max_retries=1) as client:
            with pytest.raises(HNAPIError) as exc_info:
                await client.fetch_story_ids(StoryType.TOP)

            assert exc_info.value.status_code == 404

    @respx.mock
    async def test_fetch_story_handles_individual_story_errors(
        self, mock_story_ids, sample_story_data
    ):
        """Test fetch_stories handles errors for individual stories gracefully."""
        # Arrange
        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=mock_story_ids)
        )

        # First story succeeds, rest fail
        respx.get(f"{TEST_BASE_URL}/item/1.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "type": "story",
                    "title": "Valid",
                    "score": 100,
                    "by": "user",
                    "time": 123,
                },
            )
        )

        # Simulate various errors for other stories
        for story_id in [2, 3, 4, 5]:
            respx.get(f"{TEST_BASE_URL}/item/{story_id}.json").mock(
                return_value=httpx.Response(500, text="Server Error")
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL, max_retries=1) as client:
            # Should not raise - errors are logged and skipped
            result = await client.fetch_stories(StoryType.TOP, limit=10)

        # Assert - only the successful story returned
        assert len(result) == 1
        assert result[0].id == 1


class TestClientConfiguration:
    """Tests for HNClient configuration options."""

    async def test_default_configuration(self):
        """Test HNClient uses default configuration from settings."""
        # Arrange & Act
        async with HNClient() as client:
            # Assert
            assert client.base_url == "https://hacker-news.firebaseio.com/v0"
            assert client.timeout == 30
            assert client.max_retries == 3
            assert client.max_concurrent == 10

    async def test_custom_base_url(self):
        """Test HNClient accepts custom base URL."""
        # Arrange & Act
        async with HNClient(base_url="https://custom.api.com/v1") as client:
            # Assert
            assert client.base_url == "https://custom.api.com/v1"

    async def test_custom_timeout(self):
        """Test HNClient accepts custom timeout."""
        # Arrange & Act
        async with HNClient(timeout=60) as client:
            # Assert
            assert client.timeout == 60

    async def test_custom_max_retries(self):
        """Test HNClient accepts custom max retries."""
        # Arrange & Act
        async with HNClient(max_retries=5) as client:
            # Assert
            assert client.max_retries == 5

    async def test_custom_max_concurrent(self):
        """Test HNClient accepts custom max concurrent requests."""
        # Arrange & Act
        async with HNClient(max_concurrent=20) as client:
            # Assert
            assert client.max_concurrent == 20


class TestIntegration:
    """Integration-style tests with comprehensive mocking."""

    @respx.mock
    async def test_full_workflow_fetch_top_stories(self, multiple_stories_data):
        """Test complete workflow of fetching top stories."""
        # Arrange
        story_ids = [s["id"] for s in multiple_stories_data]

        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=story_ids)
        )

        for story_data in multiple_stories_data:
            respx.get(f"{TEST_BASE_URL}/item/{story_data['id']}.json").mock(
                return_value=httpx.Response(200, json=story_data)
            )

        # Act
        async with HNClient(base_url=TEST_BASE_URL) as client:
            # Step 1: Fetch story IDs
            ids = await client.fetch_story_ids(StoryType.TOP, limit=5)
            assert len(ids) == 5

            # Step 2: Fetch individual story
            story = await client.fetch_story(ids[0])
            assert isinstance(story, Story)

            # Step 3: Fetch all stories with filtering
            stories = await client.fetch_stories(StoryType.TOP, limit=3, min_score=50)
            assert len(stories) <= 3
            assert all(s.score >= 50 for s in stories)

            # Verify sorting
            scores = [s.score for s in stories]
            assert scores == sorted(scores, reverse=True)

    @respx.mock
    async def test_multiple_story_types_in_same_session(self):
        """Test fetching different story types in the same session."""
        # Arrange
        top_ids = [1, 2, 3]
        new_ids = [4, 5, 6]
        ask_ids = [7, 8, 9]

        respx.get(f"{TEST_BASE_URL}/topstories.json").mock(
            return_value=httpx.Response(200, json=top_ids)
        )
        respx.get(f"{TEST_BASE_URL}/newstories.json").mock(
            return_value=httpx.Response(200, json=new_ids)
        )
        respx.get(f"{TEST_BASE_URL}/askstories.json").mock(
            return_value=httpx.Response(200, json=ask_ids)
        )

        # Act & Assert
        async with HNClient(base_url=TEST_BASE_URL) as client:
            top_result = await client.fetch_story_ids(StoryType.TOP)
            assert top_result == top_ids

            new_result = await client.fetch_story_ids(StoryType.NEW)
            assert new_result == new_ids

            ask_result = await client.fetch_story_ids(StoryType.ASK)
            assert ask_result == ask_ids
