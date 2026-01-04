"""Pytest fixtures for HN Herald test suite.

Provides reusable fixtures for testing including sample profiles,
mock API responses, and test clients.
"""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Set test environment variables BEFORE any imports from hn_herald
# This is necessary because pydantic-settings validates on import
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key-for-testing")
os.environ.setdefault("HN_HERALD_ENV", "development")
os.environ.setdefault("HN_HERALD_LOG_LEVEL", "DEBUG")
os.environ.setdefault("HN_HERALD_LLM_CACHE_TYPE", "memory")


@pytest.fixture
def sample_profile() -> dict[str, Any]:
    """Sample user profile for testing digest generation.

    Returns:
        Dictionary representing a UserProfile with common interests.
    """
    return {
        "interest_tags": ["python", "ai-ml", "web-development"],
        "disinterest_tags": ["crypto", "blockchain"],
        "custom_tags": [],
        "min_score": 20,
        "max_articles": 10,
        "fetch_type": "top",
        "fetch_count": 30,
    }


@pytest.fixture
def sample_profile_minimal() -> dict[str, Any]:
    """Minimal user profile with only required fields.

    Returns:
        Dictionary representing a minimal UserProfile.
    """
    return {
        "interest_tags": ["python"],
        "disinterest_tags": [],
        "min_score": 10,
        "max_articles": 5,
    }


@pytest.fixture
def mock_hn_story() -> dict[str, Any]:
    """Single mock HN story response.

    Returns:
        Dictionary representing a story from the HN API.
    """
    return {
        "id": 12345678,
        "title": "Show HN: I built an AI-powered code reviewer",
        "url": "https://example.com/ai-code-reviewer",
        "by": "testuser",
        "score": 150,
        "time": 1704067200,  # 2024-01-01 00:00:00 UTC
        "descendants": 42,
        "type": "story",
    }


@pytest.fixture
def mock_hn_stories() -> list[dict[str, Any]]:
    """List of mock HN stories for testing.

    Returns:
        List of story dictionaries simulating HN API response.
    """
    return [
        {
            "id": 12345678,
            "title": "Show HN: I built an AI-powered code reviewer",
            "url": "https://example.com/ai-code-reviewer",
            "by": "testuser",
            "score": 150,
            "time": 1704067200,
            "descendants": 42,
            "type": "story",
        },
        {
            "id": 12345679,
            "title": "Python 3.13 Released with New Performance Improvements",
            "url": "https://python.org/downloads/release/python-3130/",
            "by": "pythondev",
            "score": 320,
            "time": 1704153600,
            "descendants": 156,
            "type": "story",
        },
        {
            "id": 12345680,
            "title": "Understanding LangGraph: A Deep Dive",
            "url": "https://blog.langchain.dev/langgraph-deep-dive/",
            "by": "langchain",
            "score": 89,
            "time": 1704240000,
            "descendants": 23,
            "type": "story",
        },
        {
            "id": 12345681,
            "title": "Ask HN: What are you working on?",
            "url": None,  # Ask HN posts don't have URLs
            "by": "curious",
            "score": 45,
            "time": 1704326400,
            "descendants": 200,
            "type": "story",
        },
        {
            "id": 12345682,
            "title": "Bitcoin reaches new high",
            "url": "https://crypto-news.example.com/bitcoin-high",
            "by": "cryptofan",
            "score": 280,
            "time": 1704412800,
            "descendants": 450,
            "type": "story",
        },
    ]


@pytest.fixture
def mock_hn_top_stories_ids() -> list[int]:
    """Mock HN API response for top stories endpoint.

    Returns:
        List of story IDs simulating /topstories.json response.
    """
    return [12345678, 12345679, 12345680, 12345681, 12345682]


@pytest.fixture
def mock_article_content() -> str:
    """Sample extracted article content for testing.

    Returns:
        String containing sample article text.
    """
    return """
    AI-Powered Code Review: A New Approach

    Introduction
    Code review is an essential part of software development. Traditional code
    reviews can be time-consuming and often miss subtle issues. This article
    explores how artificial intelligence can assist in the code review process.

    Key Features
    - Automatic detection of common bugs and anti-patterns
    - Suggestions for code improvements
    - Integration with popular version control systems
    - Support for multiple programming languages

    Implementation Details
    The system uses a large language model fine-tuned on millions of code
    reviews. It analyzes pull requests and provides actionable feedback
    within seconds.

    Conclusion
    AI-powered code review tools can significantly improve code quality
    while reducing the burden on human reviewers.
    """.strip()


@pytest.fixture
def mock_llm_summary_response() -> dict[str, Any]:
    """Mock LLM response for article summarization.

    Returns:
        Dictionary representing parsed summary output.
    """
    return {
        "summary": (
            "An AI-powered code review tool that uses large language models "
            "to automatically detect bugs, suggest improvements, and provide "
            "actionable feedback on pull requests within seconds."
        ),
        "key_points": [
            "Automatic detection of bugs and anti-patterns",
            "Integration with version control systems",
            "Fine-tuned on millions of code reviews",
        ],
        "tech_tags": ["ai", "code-review", "llm", "devtools"],
    }


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Mock httpx.AsyncClient for testing HTTP requests.

    Returns:
        MagicMock configured as an async HTTP client.
    """
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI test client for API testing.

    Returns:
        TestClient instance configured for the HN Herald app.
    """
    from hn_herald.main import app

    return TestClient(app)


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configure test environment settings.

    Sets up environment variables for testing without requiring
    actual API keys.

    Args:
        monkeypatch: Pytest fixture for modifying environment.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-not-real")
    monkeypatch.setenv("HN_HERALD_ENV", "development")
    monkeypatch.setenv("HN_HERALD_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("HN_HERALD_LLM_CACHE_TYPE", "memory")


# =============================================================================
# HN API Client Fixtures
# =============================================================================


@pytest.fixture
def sample_story_data() -> dict[str, Any]:
    """Sample HN story API response data.

    Returns a complete story response as returned by the HN API
    /item/{id}.json endpoint.

    Returns:
        Dictionary matching HN API story response format.
    """
    return {
        "id": 39856302,
        "type": "story",
        "by": "testuser",
        "time": 1709654321,
        "title": "Test Story Title",
        "url": "https://example.com/article",
        "score": 142,
        "descendants": 85,
        "kids": [39856400, 39856401],
    }


@pytest.fixture
def sample_story():
    """Sample Story model instance.

    Returns a Story model instance for use in tests that need
    a pre-constructed Story object.

    Returns:
        Story model instance with test data.
    """
    from hn_herald.models.story import Story

    return Story(
        id=39856302,
        title="Test Story Title",
        url="https://example.com/article",
        score=142,
        by="testuser",
        time=1709654321,
        descendants=85,
        kids=[39856400, 39856401],
    )


@pytest.fixture
def mock_story_ids() -> list[int]:
    """List of mock story IDs for testing.

    Returns:
        List of 5 story IDs for testing fetch operations.
    """
    return [1, 2, 3, 4, 5]


@pytest.fixture
def sample_story_data_minimal() -> dict[str, Any]:
    """Minimal story data with only required fields.

    Tests that optional fields are handled correctly with defaults.

    Returns:
        Dictionary with minimal required HN API story fields.
    """
    return {
        "id": 39856303,
        "type": "story",
        "by": "minimaluser",
        "time": 1709654322,
        "title": "Minimal Story",
        "score": 50,
    }


@pytest.fixture
def sample_story_data_ask_hn() -> dict[str, Any]:
    """Sample Ask HN story without external URL.

    Returns:
        Dictionary representing an Ask HN post with text but no URL.
    """
    return {
        "id": 39856304,
        "type": "story",
        "by": "asker",
        "time": 1709654323,
        "title": "Ask HN: What are your favorite testing practices?",
        "text": "I'm curious about what testing approaches people use...",
        "score": 75,
        "descendants": 50,
        "kids": [39856500, 39856501, 39856502],
    }


@pytest.fixture
def sample_deleted_story_data() -> dict[str, Any]:
    """Sample deleted story data.

    Returns:
        Dictionary representing a deleted HN story.
    """
    return {
        "id": 39856305,
        "deleted": True,
    }


@pytest.fixture
def sample_dead_story_data() -> dict[str, Any]:
    """Sample dead story data.

    Returns:
        Dictionary representing a dead (flagged) HN story.
    """
    return {
        "id": 39856306,
        "type": "story",
        "by": "deaduser",
        "time": 1709654324,
        "title": "Dead Story",
        "score": 10,
        "dead": True,
    }


@pytest.fixture
def multiple_stories_data() -> list[dict[str, Any]]:
    """Multiple stories with varying scores for filtering tests.

    Returns:
        List of story dictionaries with different scores.
    """
    return [
        {
            "id": 1,
            "type": "story",
            "by": "user1",
            "time": 1709654321,
            "title": "High Score Story",
            "url": "https://example.com/high",
            "score": 500,
            "descendants": 100,
        },
        {
            "id": 2,
            "type": "story",
            "by": "user2",
            "time": 1709654322,
            "title": "Medium Score Story",
            "url": "https://example.com/medium",
            "score": 100,
            "descendants": 50,
        },
        {
            "id": 3,
            "type": "story",
            "by": "user3",
            "time": 1709654323,
            "title": "Low Score Story",
            "url": "https://example.com/low",
            "score": 25,
            "descendants": 10,
        },
        {
            "id": 4,
            "type": "story",
            "by": "user4",
            "time": 1709654324,
            "title": "Very Low Score Story",
            "url": "https://example.com/very-low",
            "score": 5,
            "descendants": 2,
        },
        {
            "id": 5,
            "type": "story",
            "by": "user5",
            "time": 1709654325,
            "title": "Medium-High Score Story",
            "url": "https://example.com/medium-high",
            "score": 200,
            "descendants": 75,
        },
    ]
