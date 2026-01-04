"""Unit tests for fetch_hn node.

Tests the fetch_hn node which fetches stories from HN API and emits
Send objects for parallel article extraction.
"""

from unittest.mock import AsyncMock, patch

import pytest

from hn_herald.graph.nodes.fetch_hn import fetch_hn
from hn_herald.models.story import Story
from hn_herald.services.hn_client import HNClientError


class TestFetchHNSuccess:
    """Tests for successful fetch_hn node execution."""

    @pytest.mark.asyncio
    async def test_fetch_hn_returns_stories_and_start_time(self, mock_user_profile, mock_stories):
        """Test fetch_hn returns stories and start_time in state update.

        Given: Profile and mock HNClient with stories
        When: fetch_hn node is executed
        Then: Dict with stories and start_time is returned
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=mock_stories)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            result = await fetch_hn(state)

        # Assert
        assert isinstance(result, dict)
        assert "stories" in result
        assert "start_time" in result
        assert result["stories"] == mock_stories
        assert isinstance(result["start_time"], float)

    @pytest.mark.asyncio
    async def test_fetch_hn_calls_hn_client_with_profile_params(
        self, mock_user_profile, mock_stories
    ):
        """Test fetch_hn passes profile parameters to HNClient.

        Given: Profile with specific fetch parameters
        When: fetch_hn node is executed
        Then: HNClient is called with correct parameters
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=mock_stories)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            await fetch_hn(state)

        # Assert
        mock_client.fetch_stories.assert_called_once_with(
            story_type=mock_user_profile.fetch_type,
            limit=mock_user_profile.fetch_count,
            min_score=mock_user_profile.min_score,
        )

    @pytest.mark.asyncio
    async def test_fetch_hn_sets_start_time(self, mock_user_profile, mock_stories):
        """Test fetch_hn sets start_time in state.

        Given: Profile and stories
        When: fetch_hn node is executed
        Then: start_time is set to current Unix timestamp
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=mock_stories)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            result = await fetch_hn(state)

        # Assert
        assert "start_time" in result
        assert isinstance(result["start_time"], float)
        assert result["start_time"] > 0

    @pytest.mark.asyncio
    async def test_fetch_hn_with_single_story(self, mock_user_profile):
        """Test fetch_hn handles single story correctly.

        Given: Profile and HNClient returning single story
        When: fetch_hn node is executed
        Then: One Send object and state update are returned
        """
        # Arrange
        state = {"profile": mock_user_profile}
        single_story = [
            Story(
                id=1,
                title="Single Story",
                url="https://example.com/single",
                score=100,
                by="user1",
                time=1704067200,
                descendants=10,
            )
        ]

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=single_story)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            result = await fetch_hn(state)

        # Assert
        assert isinstance(result, dict)
        assert "stories" in result
        assert len(result["stories"]) == 1
        assert result["stories"][0] == single_story[0]


class TestFetchHNEmptyResults:
    """Tests for fetch_hn handling empty results."""

    @pytest.mark.asyncio
    async def test_fetch_hn_no_stories_returns_error(self, mock_user_profile):
        """Test fetch_hn handles empty story list.

        Given: Profile and HNClient returning no stories
        When: fetch_hn node is executed
        Then: Error is returned in state with empty stories list
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=[])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            result = await fetch_hn(state)

        # Assert
        assert isinstance(result, dict)
        assert result["stories"] == []
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "No stories found" in result["errors"][0]
        assert "start_time" in result
        assert isinstance(result["start_time"], float)


class TestFetchHNErrorHandling:
    """Tests for fetch_hn error handling."""

    @pytest.mark.asyncio
    async def test_fetch_hn_hn_client_error_propagates(self, mock_user_profile):
        """Test fetch_hn propagates HNClient errors.

        Given: Profile and HNClient that raises error
        When: fetch_hn node is executed
        Then: HNClientError is propagated
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(side_effect=HNClientError("API unavailable"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client),
            pytest.raises(HNClientError, match="API unavailable"),
        ):
            await fetch_hn(state)

    @pytest.mark.asyncio
    async def test_fetch_hn_network_error_propagates(self, mock_user_profile):
        """Test fetch_hn propagates network errors.

        Given: Profile and HNClient that raises network error
        When: fetch_hn node is executed
        Then: Exception is propagated
        """
        # Arrange
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(side_effect=Exception("Network timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client),
            pytest.raises(Exception, match="Network timeout"),
        ):
            await fetch_hn(state)


class TestFetchHNLogging:
    """Tests for fetch_hn logging behavior."""

    @pytest.mark.asyncio
    async def test_fetch_hn_logs_fetch_parameters(self, mock_user_profile, mock_stories, caplog):
        """Test fetch_hn logs fetch parameters.

        Given: Profile with fetch parameters
        When: fetch_hn node is executed
        Then: Fetch parameters are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=mock_stories)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            await fetch_hn(state)

        # Assert
        assert any("Fetching stories" in record.message for record in caplog.records)
        assert any(
            str(mock_user_profile.fetch_count) in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_fetch_hn_logs_story_count(self, mock_user_profile, mock_stories, caplog):
        """Test fetch_hn logs fetched story count.

        Given: Profile and stories
        When: fetch_hn node is executed
        Then: Story count is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=mock_stories)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            await fetch_hn(state)

        # Assert
        assert any(
            "Fetched" in record.message and str(len(mock_stories)) in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_fetch_hn_logs_warning_on_empty(self, mock_user_profile, caplog):
        """Test fetch_hn logs warning when no stories found.

        Given: Profile and HNClient returning empty list
        When: fetch_hn node is executed
        Then: Warning is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.WARNING)
        state = {"profile": mock_user_profile}

        mock_client = AsyncMock()
        mock_client.fetch_stories = AsyncMock(return_value=[])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_client):
            await fetch_hn(state)

        # Assert
        assert any("No stories found" in record.message for record in caplog.records)
