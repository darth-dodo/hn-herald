"""Unit tests for format node.

Tests the format_digest node which creates the final Digest output by limiting
articles to max_articles and computing generation statistics.
"""

import time
from datetime import UTC

from hn_herald.graph.nodes.format import format_digest
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.digest import Digest
from hn_herald.models.profile import UserProfile
from hn_herald.models.scoring import RelevanceScore, ScoredArticle
from hn_herald.models.story import Story, StoryType
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)


class TestFormatDigestSuccess:
    """Tests for successful format_digest node execution."""

    def test_format_creates_digest_dict(self, mock_user_profile):
        """Test format creates digest dictionary.

        Given: Ranked articles and complete state
        When: format_digest node is executed
        Then: Digest dictionary is returned
        """
        # Arrange
        article = Article(
            story_id=1,
            title="Test Article",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary",
                key_points=["Key point"],
                tech_tags=["python"],
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=["python"],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        state = {
            "ranked_articles": [scored],
            "profile": mock_user_profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=1,
                    title="Test",
                    url="https://example.com/1",
                    score=100,
                    by="user1",
                    time=int(time.time()),
                    descendants=10,
                )
            ],
            "filtered_articles": [article],
            "errors": [],
        }

        # Act
        result = format_digest(state)

        # Assert
        assert "digest" in result
        assert isinstance(result["digest"], dict)
        assert "articles" in result["digest"]
        assert "timestamp" in result["digest"]
        assert "stats" in result["digest"]

    def test_format_limits_to_max_articles(self):
        """Test format limits articles to profile.max_articles.

        Given: More ranked articles than max_articles
        When: format_digest node is executed
        Then: Only max_articles are included in digest
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=3,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        base_article = Article(
            story_id=1,
            title="Base",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        base_summarized = SummarizedArticle(
            article=base_article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )

        # Create 5 ranked articles
        ranked = [
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.7,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.67,
            )
            for _ in range(5)
        ]

        state = {
            "ranked_articles": ranked,
            "profile": profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=i,
                    title=f"Story {i}",
                    url=f"https://example.com/{i}",
                    score=100,
                    by=f"user{i}",
                    time=int(time.time()),
                    descendants=10,
                )
                for i in range(5)
            ],
            "filtered_articles": [base_article] * 5,
            "errors": [],
        }

        # Act
        result = format_digest(state)
        digest_dict = result["digest"]

        # Assert
        assert len(digest_dict["articles"]) == 3  # Limited to max_articles

    def test_format_includes_all_stats(self):
        """Test format includes complete statistics.

        Given: Complete state with counts
        When: format_digest node is executed
        Then: All stats fields are populated
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=30,
        )

        article = Article(
            story_id=1,
            title="Test",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100,
                by=f"user{i}",
                time=int(time.time()),
                descendants=10,
            )
            for i in range(30)
        ]

        state = {
            "ranked_articles": [scored],
            "profile": profile,
            "start_time": time.time() - 5.0,  # 5 seconds ago
            "stories": stories,
            "filtered_articles": [article] * 20,
            "errors": ["Error 1", "Error 2"],
        }

        # Act
        result = format_digest(state)
        stats = result["digest"]["stats"]

        # Assert
        assert stats["fetched"] == 30
        assert stats["filtered"] == 20
        assert stats["final"] == 1
        assert stats["errors"] == 2
        assert stats["generation_time_ms"] >= 5000  # At least 5 seconds

    def test_format_calculates_generation_time(self):
        """Test format calculates generation time correctly.

        Given: State with start_time
        When: format_digest node is executed
        Then: generation_time_ms is calculated correctly
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        article = Article(
            story_id=1,
            title="Test",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        start_time = time.time() - 2.5  # 2.5 seconds ago

        state = {
            "ranked_articles": [scored],
            "profile": profile,
            "start_time": start_time,
            "stories": [
                Story(
                    id=1,
                    title="Test",
                    url="https://example.com/1",
                    score=100,
                    by="user1",
                    time=int(time.time()),
                    descendants=10,
                )
            ],
            "filtered_articles": [article],
            "errors": [],
        }

        # Act
        result = format_digest(state)
        generation_time = result["digest"]["stats"]["generation_time_ms"]

        # Assert
        assert generation_time >= 2500  # At least 2.5 seconds
        assert generation_time < 3000  # Less than 3 seconds (accounting for execution time)


class TestFormatDigestEmptyInput:
    """Tests for format_digest handling empty/minimal inputs."""

    def test_format_zero_ranked_articles(self):
        """Test format handles zero ranked articles.

        Given: Empty ranked_articles list
        When: format_digest node is executed
        Then: Digest with zero articles is created
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        state = {
            "ranked_articles": [],
            "profile": profile,
            "start_time": time.time(),
            "stories": [],
            "filtered_articles": [],
            "errors": [],
        }

        # Act
        result = format_digest(state)
        digest_dict = result["digest"]

        # Assert
        assert len(digest_dict["articles"]) == 0
        assert digest_dict["stats"]["final"] == 0

    def test_format_no_errors(self):
        """Test format handles state with no errors.

        Given: State with empty errors list
        When: format_digest node is executed
        Then: Stats shows 0 errors
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        article = Article(
            story_id=1,
            title="Test",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        state = {
            "ranked_articles": [scored],
            "profile": profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=1,
                    title="Test",
                    url="https://example.com/1",
                    score=100,
                    by="user1",
                    time=int(time.time()),
                    descendants=10,
                )
            ],
            "filtered_articles": [article],
            "errors": [],
        }

        # Act
        result = format_digest(state)

        # Assert
        assert result["digest"]["stats"]["errors"] == 0


class TestFormatDigestLogging:
    """Tests for format_digest logging behavior."""

    def test_format_logs_article_count(self, caplog):
        """Test format logs number of ranked articles.

        Given: Ranked articles
        When: format_digest node is executed
        Then: Article count is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        base_article = Article(
            story_id=1,
            title="Base",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        base_summarized = SummarizedArticle(
            article=base_article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )

        ranked = [
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.7,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.67,
            )
            for _ in range(5)
        ]

        state = {
            "ranked_articles": ranked,
            "profile": profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=i,
                    title=f"Story {i}",
                    url=f"https://example.com/{i}",
                    score=100,
                    by=f"user{i}",
                    time=int(time.time()),
                    descendants=10,
                )
                for i in range(5)
            ],
            "filtered_articles": [base_article] * 5,
            "errors": [],
        }

        # Act
        format_digest(state)

        # Assert
        assert any(
            "Creating final digest from 5 ranked articles" in record.message
            for record in caplog.records
        )

    def test_format_logs_digest_stats(self, caplog):
        """Test format logs complete digest statistics.

        Given: Complete state
        When: format_digest node is executed
        Then: All stats are logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=3,
            fetch_type=StoryType.TOP,
            fetch_count=30,
        )

        article = Article(
            story_id=1,
            title="Test",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        state = {
            "ranked_articles": [scored] * 5,  # 5 ranked, but limited to 3
            "profile": profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=i,
                    title=f"Story {i}",
                    url=f"https://example.com/{i}",
                    score=100,
                    by=f"user{i}",
                    time=int(time.time()),
                    descendants=10,
                )
                for i in range(30)
            ],
            "filtered_articles": [article] * 20,
            "errors": ["Error 1"],
        }

        # Act
        format_digest(state)

        # Assert
        assert any(
            "Generated digest with 3 articles" in record.message for record in caplog.records
        )
        assert any(
            "fetched=30" in record.message and "filtered=20" in record.message
            for record in caplog.records
        )


class TestFormatDigestTimestamp:
    """Tests for format_digest timestamp handling."""

    def test_format_uses_utc_timestamp(self):
        """Test format uses UTC timezone for timestamp.

        Given: State with articles
        When: format_digest node is executed
        Then: Timestamp is in UTC timezone
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.5,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        article = Article(
            story_id=1,
            title="Test",
            url="https://example.com/1",
            hn_url="https://news.ycombinator.com/item?id=1",
            hn_score=100,
            author="user1",
            content="Content",
            word_count=1,
            status=ExtractionStatus.SUCCESS,
        )
        summarized = SummarizedArticle(
            article=article,
            summary_data=ArticleSummary(
                summary="This is a complete test summary", key_points=["Key point"], tech_tags=[]
            ),
            summarization_status=SummarizationStatus.SUCCESS,
        )
        scored = ScoredArticle(
            article=summarized,
            relevance=RelevanceScore(
                score=0.8,
                reason="Test relevance",
                matched_interest_tags=[],
                matched_disinterest_tags=[],
            ),
            popularity_score=0.6,
            final_score=0.74,
        )

        state = {
            "ranked_articles": [scored],
            "profile": profile,
            "start_time": time.time(),
            "stories": [
                Story(
                    id=1,
                    title="Test",
                    url="https://example.com/1",
                    score=100,
                    by="user1",
                    time=int(time.time()),
                    descendants=10,
                )
            ],
            "filtered_articles": [article],
            "errors": [],
        }

        # Act
        result = format_digest(state)

        # Assert - Validate as Digest model to check timestamp
        digest = Digest.model_validate(result["digest"])
        assert digest.timestamp.tzinfo == UTC
