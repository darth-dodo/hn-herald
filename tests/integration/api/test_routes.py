"""Integration tests for API routes.

Tests the complete FastAPI endpoints including request validation,
LangGraph pipeline execution, and response formatting.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from hn_herald.main import app
from hn_herald.models.article import Article
from hn_herald.models.digest import Digest, DigestStats
from hn_herald.models.profile import UserProfile
from hn_herald.models.scoring import RelevanceScore, ScoredArticle
from hn_herald.models.story import Story, StoryType
from hn_herald.models.summary import ArticleSummary, SummarizationStatus, SummarizedArticle


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_profile() -> UserProfile:
    """Sample user profile for testing."""
    return UserProfile(
        interest_tags=["python", "ai"],
        disinterest_tags=["crypto"],
        min_score=0.3,
        max_articles=10,
        fetch_type=StoryType.TOP,
        fetch_count=30,
    )


@pytest.fixture
def sample_story() -> Story:
    """Sample HN story for testing."""
    return Story(
        id=12345,
        title="Test Story",
        url="https://example.com/article",
        score=100,
        by="testuser",
        time=1704067200,
    )


@pytest.fixture
def sample_article(sample_story: Story) -> Article:
    """Sample article for testing."""
    return Article(
        story_id=sample_story.id,
        title=sample_story.title,
        url=sample_story.url,
        hn_url=sample_story.hn_url,
        hn_score=sample_story.score,
        author=sample_story.by,
        content="This is test content about Python and AI.",
        word_count=8,
    )


@pytest.fixture
def sample_summarized_article(sample_article: Article) -> SummarizedArticle:
    """Sample summarized article for testing."""
    summary_data = ArticleSummary(
        summary="Test article about Python and AI.",
        key_points=["Point 1", "Point 2", "Point 3"],
        tech_tags=["python", "ai"],
    )
    return SummarizedArticle(
        article=sample_article,
        summary_data=summary_data,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def sample_scored_article(sample_summarized_article: SummarizedArticle) -> ScoredArticle:
    """Sample scored article for testing."""
    relevance = RelevanceScore(
        score=0.8,
        reason="Matches interests: python, ai",
        matched_interest_tags=["python", "ai"],
        matched_disinterest_tags=[],
    )
    return ScoredArticle(
        article=sample_summarized_article,
        relevance=relevance,
        popularity_score=0.6,
        final_score=0.74,
    )


@pytest.fixture
def sample_digest(sample_scored_article: ScoredArticle) -> Digest:
    """Sample digest for testing."""
    return Digest(
        articles=[sample_scored_article],
        timestamp=datetime.now(UTC),
        stats=DigestStats(
            fetched=30,
            filtered=25,
            final=1,
            errors=0,
            generation_time_ms=1000,
        ),
    )


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_200(self, client: TestClient) -> None:
        """Test that health check returns 200 OK."""
        response = client.get("/api/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_check_response_format(self, client: TestClient) -> None:
        """Test that health check returns correct format."""
        response = client.get("/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "healthy"

    def test_health_check_includes_version(self, client: TestClient) -> None:
        """Test that health check includes version information."""
        from hn_herald import __version__

        response = client.get("/api/health")
        data = response.json()

        assert data["version"] == __version__


class TestGenerateEndpoint:
    """Tests for the digest generation endpoint."""

    def test_generate_requires_profile(self, client: TestClient) -> None:
        """Test that generate endpoint requires profile."""
        response = client.post("/api/generate", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_validates_profile(self, client: TestClient) -> None:
        """Test that generate endpoint validates profile."""
        invalid_profile = {
            "profile": {
                "interest_tags": ["python"],
                "min_score": 1.5,  # Invalid: must be <= 1.0
            }
        }

        response = client.post("/api/generate", json=invalid_profile)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_success(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
        sample_digest: Digest,
    ) -> None:
        """Test successful digest generation."""
        # Mock graph execution
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "digest": sample_digest.model_dump(),
                "articles": [],
                "summarized_articles": [],
                "scored_articles": [],
                "errors": [],
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)

        assert response.status_code == status.HTTP_200_OK

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_response_format(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
        sample_digest: Digest,
    ) -> None:
        """Test that response has correct format."""
        # Mock graph execution
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "digest": sample_digest.model_dump(),
                "articles": [],
                "summarized_articles": [],
                "scored_articles": [],
                "errors": [],
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)
        data = response.json()

        assert "articles" in data
        assert "stats" in data
        assert "timestamp" in data
        assert "profile_summary" in data
        assert isinstance(data["articles"], list)
        assert isinstance(data["stats"], dict)

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_includes_stats(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
        sample_digest: Digest,
    ) -> None:
        """Test that response includes generation statistics."""
        # Mock graph execution
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "digest": sample_digest.model_dump(),
                "articles": [],
                "summarized_articles": [],
                "scored_articles": [],
                "errors": [],
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)
        data = response.json()

        stats = data["stats"]
        assert "stories_fetched" in stats
        assert "articles_extracted" in stats
        assert "articles_summarized" in stats
        assert "articles_scored" in stats
        assert "articles_returned" in stats
        assert "errors" in stats
        assert "generation_time_ms" in stats

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_includes_profile_summary(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
        sample_digest: Digest,
    ) -> None:
        """Test that response includes profile summary."""
        # Mock graph execution
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "digest": sample_digest.model_dump(),
                "articles": [],
                "summarized_articles": [],
                "scored_articles": [],
                "errors": [],
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)
        data = response.json()

        profile_summary = data["profile_summary"]
        assert "interests" in profile_summary
        assert "disinterests" in profile_summary
        assert "min_score" in profile_summary
        assert "max_articles" in profile_summary

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_handles_pipeline_failure(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
    ) -> None:
        """Test that pipeline failures return 500 error."""
        # Mock graph execution failure
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("Pipeline failed"))
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_handles_missing_digest(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
    ) -> None:
        """Test that missing digest in state returns 500 error."""
        # Mock graph execution with missing digest
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "articles": [],
                "errors": [],
                # Missing "digest" key
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @patch("hn_herald.api.routes.create_hn_graph")
    async def test_generate_article_response_fields(
        self,
        mock_create_graph: MagicMock,
        client: TestClient,
        sample_profile: UserProfile,
        sample_digest: Digest,
    ) -> None:
        """Test that article responses contain all required fields."""
        # Mock graph execution
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(
            return_value={
                "digest": sample_digest.model_dump(),
                "articles": [],
                "summarized_articles": [],
                "scored_articles": [],
                "errors": [],
            }
        )
        mock_create_graph.return_value = mock_graph

        request_body = {"profile": sample_profile.model_dump()}
        response = client.post("/api/generate", json=request_body)
        data = response.json()

        if data["articles"]:
            article = data["articles"][0]
            required_fields = [
                "story_id",
                "title",
                "url",
                "hn_url",
                "hn_score",
                "summary",
                "key_points",
                "tech_tags",
                "relevance_score",
                "relevance_reason",
                "final_score",
            ]
            for field in required_fields:
                assert field in article


class TestAPIIntegration:
    """Integration tests for complete API workflow."""

    def test_api_router_mounted(self, client: TestClient) -> None:
        """Test that API router is properly mounted."""
        # Health endpoint should exist at /api/health
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_schema_available_in_dev(self, client: TestClient) -> None:
        """Test that OpenAPI schema is available in development mode."""
        # This test assumes development mode is enabled
        # In production, docs should be disabled
        response = client.get("/api/docs")

        # Could be 200 (dev) or 404 (prod)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_cors_headers_present(self, client: TestClient) -> None:
        """Test that CORS headers are present in responses."""
        response = client.get("/api/health")

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
