"""Shared pytest fixtures for HN Herald tests.

This module provides common test fixtures used across multiple test files.
Organized by category for easy discovery and maintenance.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

# =============================================================================
# Story Fixtures
# =============================================================================


@pytest.fixture
def mock_story():
    """Create a mock Story object for testing.

    Returns:
        Mock Story with typical test data.
    """
    from hn_herald.models.story import Story

    return Story(
        id=1,
        title="Test Story",
        url="https://example.com",
        score=100,
        by="testuser",
        time=1234567890,
        descendants=10,
        type="story",
    )


@pytest.fixture
def mock_stories():
    """Create multiple mock Story objects for batch testing.

    Returns:
        List of 3 mock Stories with varying data.
    """
    from hn_herald.models.story import Story

    return [
        Story(
            id=1,
            title="Test Story 1",
            url="https://example.com/1",
            score=100,
            by="user1",
            time=1234567890,
            descendants=10,
        ),
        Story(
            id=2,
            title="Test Story 2",
            url="https://example.com/2",
            score=200,
            by="user2",
            time=1234567891,
            descendants=20,
        ),
        Story(
            id=3,
            title="Test Story 3",
            url="https://example.com/3",
            score=300,
            by="user3",
            time=1234567892,
            descendants=30,
        ),
    ]


# =============================================================================
# Article Fixtures
# =============================================================================


@pytest.fixture
def mock_article():
    """Create a mock Article object for testing.

    Returns:
        Mock Article with SUCCESS status and typical test data.
    """
    from hn_herald.models.article import Article, ExtractionStatus

    return Article(
        story_id=1,
        title="Test Article",
        url="https://example.com",
        hn_url="https://news.ycombinator.com/item?id=1",
        hn_score=100,
        hn_comments=10,
        author="testuser",
        content="Test content",
        word_count=2,
        status=ExtractionStatus.SUCCESS,
    )


@pytest.fixture
def mock_articles():
    """Create multiple mock Article objects for batch testing.

    Returns:
        List of 3 mock Articles with SUCCESS status.
    """
    from hn_herald.models.article import Article, ExtractionStatus

    return [
        Article(
            story_id=1,
            title="Test Article 1",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            hn_comments=10,
            author="user1",
            content="Content 1",
            word_count=2,
            status=ExtractionStatus.SUCCESS,
        ),
        Article(
            story_id=2,
            title="Test Article 2",
            url="https://example.com/2",
            hn_url="https://news.ycombinator.com/item?id=2",
            hn_score=200,
            hn_comments=20,
            author="user2",
            content="Content 2",
            word_count=2,
            status=ExtractionStatus.SUCCESS,
        ),
        Article(
            story_id=3,
            title="Test Article 3",
            url="https://example.com/3",
            hn_url="https://news.ycombinator.com/item?id=3",
            hn_score=300,
            hn_comments=30,
            author="user3",
            content="Content 3",
            word_count=2,
            status=ExtractionStatus.SUCCESS,
        ),
    ]


# =============================================================================
# Summary Fixtures
# =============================================================================


@pytest.fixture
def mock_article_summary():
    """Create a mock ArticleSummary for testing.

    Returns:
        Mock ArticleSummary with valid test data.
    """
    from hn_herald.models.summary import ArticleSummary

    return ArticleSummary(
        summary="This is a test summary with enough characters for validation",
        key_points=["Point 1", "Point 2"],
        tech_tags=["python", "testing"],
    )


@pytest.fixture
def mock_summarized_article():
    """Create a mock SummarizedArticle for testing.

    Returns:
        Mock SummarizedArticle with SUCCESS status.
    """
    from hn_herald.models.article import Article, ExtractionStatus
    from hn_herald.models.summary import (
        ArticleSummary,
        SummarizationStatus,
        SummarizedArticle,
    )

    article = Article(
        story_id=1,
        title="Test Article",
        url="https://example.com",
        hn_url="https://news.ycombinator.com/item?id=1",
        hn_score=100,
        hn_comments=10,
        author="testuser",
        content="Test content",
        word_count=2,
        status=ExtractionStatus.SUCCESS,
    )

    summary = ArticleSummary(
        summary="This is a test summary with enough characters for validation",
        key_points=["Point 1", "Point 2"],
        tech_tags=["python", "testing"],
    )

    return SummarizedArticle(
        article=article,
        summary_data=summary,
        summarization_status=SummarizationStatus.SUCCESS,
    )


@pytest.fixture
def mock_summarized_articles():
    """Create multiple mock SummarizedArticle objects for batch testing.

    Returns:
        List of 3 mock SummarizedArticles with SUCCESS status.
    """
    from hn_herald.models.article import Article, ExtractionStatus
    from hn_herald.models.summary import (
        ArticleSummary,
        SummarizationStatus,
        SummarizedArticle,
    )

    articles = [
        Article(
            story_id=i,
            title=f"Test Article {i}",
            url=f"https://example.com/{i}",
            hn_url=f"https://news.ycombinator.com/item?id={i}",
            hn_score=100 * i,
            hn_comments=10 * i,
            author=f"user{i}",
            content=f"Content {i}",
            word_count=2,
            status=ExtractionStatus.SUCCESS,
        )
        for i in range(1, 4)
    ]

    summaries = [
        ArticleSummary(
            summary=f"Summary {i} with enough characters for validation purposes",
            key_points=[f"Point {i}.1", f"Point {i}.2"],
            tech_tags=["python", "testing"],
        )
        for i in range(1, 4)
    ]

    return [
        SummarizedArticle(
            article=article,
            summary_data=summary,
            summarization_status=SummarizationStatus.SUCCESS,
        )
        for article, summary in zip(articles, summaries, strict=True)
    ]


# =============================================================================
# UserProfile Fixtures
# =============================================================================


@pytest.fixture
def mock_user_profile():
    """Create a mock UserProfile for testing.

    Returns:
        Mock UserProfile with typical test preferences.
    """
    from hn_herald.models.profile import UserProfile

    return UserProfile(
        interest_tags=["python", "ai-ml"],
        disinterest_tags=["crypto"],
        min_score=0.5,
        max_articles=10,
    )


# =============================================================================
# Service Fixtures
# =============================================================================


@pytest.fixture
def mock_hn_service():
    """Mock HNClient for graph node testing with async context manager support.

    Returns:
        AsyncMock configured as HNClient with context manager support.
    """
    from hn_herald.models.story import Story

    # Create AsyncMock for the client
    mock_service = AsyncMock()
    mock_service.fetch_stories = AsyncMock(
        return_value=[
            Story(
                id=1,
                title="Test Story",
                url="https://example.com",
                score=100,
                by="testuser",
                time=1234567890,
                descendants=10,
            )
        ]
    )

    # Setup context manager support
    mock_service.__aenter__ = AsyncMock(return_value=mock_service)
    mock_service.__aexit__ = AsyncMock(return_value=None)

    return mock_service


@pytest.fixture
def mock_article_loader():
    """Mock ArticleLoader for graph node testing.

    Returns:
        AsyncMock configured as ArticleLoader with context manager support.
    """
    from hn_herald.models.article import Article, ExtractionStatus

    # Create the article to return
    test_article = Article(
        story_id=1,
        title="Test Article",
        url="https://example.com",
        hn_url="https://news.ycombinator.com/item?id=1",
        hn_score=100,
        hn_comments=10,
        author="testuser",
        content="Test content",
        word_count=2,
        status=ExtractionStatus.SUCCESS,
    )

    # Create AsyncMock for the loader
    mock_loader = AsyncMock()
    mock_loader.extract_article = AsyncMock(return_value=test_article)

    # Setup context manager support
    mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
    mock_loader.__aexit__ = AsyncMock(return_value=None)

    return mock_loader


@pytest.fixture
def mock_llm_service():
    """Mock LLMService for graph node testing.

    Returns:
        MagicMock configured as LLMService.
    """
    from hn_herald.models.article import Article, ExtractionStatus
    from hn_herald.models.summary import (
        ArticleSummary,
        SummarizationStatus,
        SummarizedArticle,
    )

    mock_service = MagicMock()
    mock_service.summarize_articles_batch = MagicMock(
        return_value=[
            SummarizedArticle(
                article=Article(
                    story_id=1,
                    title="Test Article",
                    url="https://example.com/article",
                    hn_url="https://news.ycombinator.com/item?id=1",
                    hn_score=100,
                    hn_comments=10,
                    author="testuser",
                    content="Test content",
                    word_count=2,
                    status=ExtractionStatus.SUCCESS,
                ),
                summary_data=ArticleSummary(
                    summary="This is a test summary with enough characters for validation",
                    key_points=["Point 1"],
                    tech_tags=["python"],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
        ]
    )
    return mock_service


@pytest.fixture
def mock_scoring_service():
    """Mock ScoringService for graph node testing.

    Returns:
        MagicMock configured as ScoringService.
    """
    from hn_herald.models.article import Article, ExtractionStatus
    from hn_herald.models.scoring import RelevanceScore, ScoredArticle
    from hn_herald.models.summary import (
        ArticleSummary,
        SummarizationStatus,
        SummarizedArticle,
    )

    mock_service = MagicMock()
    mock_service.score_articles = MagicMock(
        return_value=[
            ScoredArticle(
                article=SummarizedArticle(
                    article=Article(
                        story_id=1,
                        title="Test Article",
                        url="https://example.com/article",
                        hn_url="https://news.ycombinator.com/item?id=1",
                        hn_score=100,
                        hn_comments=10,
                        author="testuser",
                        content="Test content",
                        word_count=2,
                        status=ExtractionStatus.SUCCESS,
                    ),
                    summary_data=ArticleSummary(
                        summary="This is a test summary with enough characters for validation",
                        key_points=["Point 1"],
                        tech_tags=["python"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                ),
                relevance=RelevanceScore(
                    score=0.75,
                    reason="Matches interests: python",
                    matched_interest_tags=["python"],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.72,
            )
        ]
    )
    return mock_service


# =============================================================================
# API Testing Fixtures
# =============================================================================


@pytest.fixture
def test_client():
    """Create FastAPI test client.

    Returns:
        TestClient for API testing.
    """
    from fastapi.testclient import TestClient

    from hn_herald.main import app

    return TestClient(app)


# =============================================================================
# Story Data Fixtures
# =============================================================================


@pytest.fixture
def sample_story_data():
    """Sample story data dict for testing Story model.

    Returns:
        Dict with all story fields.
    """
    return {
        "id": 39856302,
        "title": "Test Story Title",
        "url": "https://example.com/article",
        "score": 142,
        "by": "testuser",
        "time": 1709654321,
        "descendants": 85,
        "type": "story",
        "kids": [39856400, 39856401],
    }


@pytest.fixture
def sample_story_data_minimal():
    """Minimal story data dict for testing Story model.

    Returns:
        Dict with only required story fields.
    """
    return {
        "id": 39856303,
        "title": "Minimal Story",
        "score": 50,
        "by": "minimaluser",
        "time": 1709654322,
    }


@pytest.fixture
def multiple_stories_data():
    """Multiple story data dicts for batch testing.

    Returns:
        List of story data dicts.
    """
    return [
        {
            "id": 1,
            "title": "Story 1",
            "url": "https://example.com/1",
            "score": 100,
            "by": "user1",
            "time": 1234567890,
            "descendants": 10,
            "type": "story",
        },
        {
            "id": 2,
            "title": "Story 2",
            "url": "https://example.com/2",
            "score": 200,
            "by": "user2",
            "time": 1234567891,
            "descendants": 20,
            "type": "story",
        },
        {
            "id": 3,
            "title": "Story 3",
            "url": "https://example.com/3",
            "score": 300,
            "by": "user3",
            "time": 1234567892,
            "descendants": 30,
            "type": "story",
        },
        {
            "id": 4,
            "title": "Story 4",
            "url": "https://example.com/4",
            "score": 400,
            "by": "user4",
            "time": 1234567893,
            "descendants": 40,
            "type": "story",
        },
        {
            "id": 5,
            "title": "Story 5",
            "url": "https://example.com/5",
            "score": 500,
            "by": "user5",
            "time": 1234567894,
            "descendants": 50,
            "type": "story",
        },
    ]


@pytest.fixture
def sample_story_data_ask_hn():
    """Sample Ask HN story data (no external URL).

    Returns:
        Dict with Ask HN story fields (no url field).
    """
    return {
        "id": 39856304,
        "title": "Ask HN: What are your favorite testing practices?",
        "score": 75,
        "by": "askuser",
        "time": 1709654323,
        "type": "story",
        "text": "I'm curious about what testing approaches people use...",
    }


@pytest.fixture
def sample_dead_story_data():
    """Sample dead story data.

    Returns:
        Dict with dead story fields.
    """
    return {
        "id": 999,
        "title": "Dead Story",
        "score": 10,
        "by": "deaduser",
        "time": 1234567800,
        "dead": True,
        "type": "story",
    }


@pytest.fixture
def sample_story_ids_data():
    """Sample story IDs list.

    Returns:
        List of story IDs.
    """
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


@pytest.fixture
def mock_story_ids():
    """Mock story IDs for HN client testing.

    Returns:
        List of 5 story IDs.
    """
    return [1, 2, 3, 4, 5]


@pytest.fixture
def sample_deleted_story_data():
    """Sample deleted story data.

    Returns:
        Dict with deleted story fields.
    """
    return {
        "id": 888,
        "deleted": True,
        "type": "story",
    }
