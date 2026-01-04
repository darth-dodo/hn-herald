"""Integration tests for partial failure tolerance in the LangGraph pipeline.

Tests the pipeline's ability to continue processing even when individual
components fail, accumulating errors for observability.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hn_herald.graph.graph import create_hn_graph
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.digest import Digest
from hn_herald.models.profile import UserProfile
from hn_herald.models.scoring import ScoredArticle
from hn_herald.models.story import Story, StoryType
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)


class TestPartialArticleExtractionFailures:
    """Tests for partial failures during article extraction."""

    @pytest.mark.asyncio
    async def test_50_percent_extraction_failures(self):
        """Test graph handles 50% article extraction failures.

        Given: 10 stories where 5 fail to extract
        When: Graph is invoked
        Then: 5 successful articles produce digest and 5 errors are accumulated
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=10,
        )

        stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100,
                by=f"user{i}",
                time=1704067200,
                descendants=10,
            )
            for i in range(10)
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        # Fail on even IDs
        def extract_with_failures(story):
            if story.id % 2 == 0:
                raise Exception(f"Network error for story {story.id}")
            return Article(
                story_id=story.id,
                title=story.title,
                url=story.url,
                hn_url=f"https://news.ycombinator.com/item?id={story.id}",
                hn_score=story.score,
                author=story.by,
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=extract_with_failures)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        def create_summarized(articles):
            return [
                SummarizedArticle(
                    article=article,
                    summary_data=ArticleSummary(
                        summary="This is a valid summary text",
                        key_points=["Key point"],
                        tech_tags=["python"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                )
                for article in articles
                if article.status == ExtractionStatus.SUCCESS
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_summarized)

        def create_scored(summarized, filter_below_min=False):  # noqa: FBT002
            from hn_herald.models.scoring import RelevanceScore

            return [
                ScoredArticle(
                    article=summ,
                    relevance=RelevanceScore(
                        score=0.8,
                        reason="Matches interests: python",
                        matched_interest_tags=["python"],
                        matched_disinterest_tags=[],
                    ),
                    popularity_score=0.6,
                    final_score=0.74,
                )
                for summ in summarized
            ]

        mock_scoring = MagicMock()
        mock_scoring.score_articles = MagicMock(side_effect=create_scored)

        graph = create_hn_graph()

        initial_state = {
            "profile": profile,
            "stories": [],
            "articles": [],
            "filtered_articles": [],
            "summarized_articles": [],
            "scored_articles": [],
            "ranked_articles": [],
            "digest": {},
            "errors": [],
            "start_time": 0.0,
        }

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn),
            patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm),
            patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        digest = Digest.model_validate(result["digest"])
        assert len(digest.articles) == 5  # 5 successful
        assert digest.stats.errors == 5  # 5 failures
        assert digest.stats.fetched == 10

    @pytest.mark.asyncio
    async def test_all_extractions_fail_produces_empty_digest(self):
        """Test graph produces empty digest when all extractions fail.

        Given: All article extractions fail
        When: Graph is invoked
        Then: Empty digest is produced with all errors accumulated
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=5,
        )

        stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100,
                by=f"user{i}",
                time=1704067200,
                descendants=10,
            )
            for i in range(5)
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        # All fail
        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Network error"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(return_value=[])

        mock_scoring = MagicMock()
        mock_scoring.score_articles = MagicMock(return_value=[])

        graph = create_hn_graph()

        initial_state = {
            "profile": profile,
            "stories": [],
            "articles": [],
            "filtered_articles": [],
            "summarized_articles": [],
            "scored_articles": [],
            "ranked_articles": [],
            "digest": {},
            "errors": [],
            "start_time": 0.0,
        }

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn),
            patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm),
            patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        digest = Digest.model_validate(result["digest"])
        assert len(digest.articles) == 0
        assert digest.stats.errors >= 5  # All extraction errors + filter warning


class TestPartialSummarizationFailures:
    """Tests for partial failures during summarization."""

    @pytest.mark.asyncio
    async def test_mixed_summarization_results(self):
        """Test graph handles mix of successful and failed summarizations.

        Given: Articles where some fail summarization
        When: Graph is invoked
        Then: Only successfully summarized articles are in digest
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=4,
        )

        stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100,
                by=f"user{i}",
                time=1704067200,
                descendants=10,
            )
            for i in range(4)
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        def create_article(story):
            return Article(
                story_id=story.id,
                title=story.title,
                url=story.url,
                hn_url=f"https://news.ycombinator.com/item?id={story.id}",
                hn_score=story.score,
                author=story.by,
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=create_article)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Fail summarization for story IDs 1 and 3
        def create_mixed_summarized(articles):
            return [
                SummarizedArticle(
                    article=article,
                    summary_data=ArticleSummary(
                        summary=f"This is a comprehensive summary for article {article.story_id}",
                        key_points=["Key point"],
                        tech_tags=["python"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                )
                if article.story_id % 2 == 0
                else SummarizedArticle(
                    article=article,
                    summarization_status=SummarizationStatus.API_ERROR,
                    error_message="LLM parse error",
                )
                for article in articles
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_mixed_summarized)

        def create_scored(summarized, filter_below_min=False):  # noqa: FBT002
            # Only score articles with summaries
            from hn_herald.models.scoring import RelevanceScore

            return [
                ScoredArticle(
                    article=summ,
                    relevance=RelevanceScore(
                        score=0.8,
                        reason="Matches interests: python",
                        matched_interest_tags=["python"],
                        matched_disinterest_tags=[],
                    ),
                    popularity_score=0.6,
                    final_score=0.74,
                )
                for summ in summarized
                if summ.has_summary
            ]

        mock_scoring = MagicMock()
        mock_scoring.score_articles = MagicMock(side_effect=create_scored)

        graph = create_hn_graph()

        initial_state = {
            "profile": profile,
            "stories": [],
            "articles": [],
            "filtered_articles": [],
            "summarized_articles": [],
            "scored_articles": [],
            "ranked_articles": [],
            "digest": {},
            "errors": [],
            "start_time": 0.0,
        }

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn),
            patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm),
            patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        digest = Digest.model_validate(result["digest"])
        assert len(digest.articles) == 2  # Only even IDs (0, 2)
        assert digest.stats.errors == 2  # Two summarization failures


class TestErrorAccumulation:
    """Tests for error accumulation across pipeline stages."""

    @pytest.mark.asyncio
    async def test_errors_accumulate_across_stages(self):
        """Test errors from multiple stages are accumulated.

        Given: Failures in multiple pipeline stages
        When: Graph is invoked
        Then: All errors are accumulated in final state
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=6,
        )

        stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100,
                by=f"user{i}",
                time=1704067200,
                descendants=10,
            )
            for i in range(6)
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        # Extraction failures for IDs 0, 1
        def extract_with_failures(story):
            if story.id < 2:
                raise Exception(f"Extraction failed for {story.id}")
            return Article(
                story_id=story.id,
                title=story.title,
                url=story.url,
                hn_url=f"https://news.ycombinator.com/item?id={story.id}",
                hn_score=story.score,
                author=story.by,
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=extract_with_failures)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Summarization failures for IDs 2, 3
        def create_mixed_summarized(articles):
            return [
                SummarizedArticle(
                    article=article,
                    summary_data=ArticleSummary(
                        summary="This is a valid summary text",
                        key_points=["Key point"],
                        tech_tags=["python"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                )
                if article.story_id >= 4
                else SummarizedArticle(
                    article=article,
                    summarization_status=SummarizationStatus.API_ERROR,
                    error_message="Summarization failed",
                )
                for article in articles
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_mixed_summarized)

        def create_scored(summarized, filter_below_min=False):  # noqa: FBT002
            from hn_herald.models.scoring import RelevanceScore

            return [
                ScoredArticle(
                    article=summ,
                    relevance=RelevanceScore(
                        score=0.8,
                        reason="Matches interests: python",
                        matched_interest_tags=["python"],
                        matched_disinterest_tags=[],
                    ),
                    popularity_score=0.6,
                    final_score=0.74,
                )
                for summ in summarized
                if summ.has_summary
            ]

        mock_scoring = MagicMock()
        mock_scoring.score_articles = MagicMock(side_effect=create_scored)

        graph = create_hn_graph()

        initial_state = {
            "profile": profile,
            "stories": [],
            "articles": [],
            "filtered_articles": [],
            "summarized_articles": [],
            "scored_articles": [],
            "ranked_articles": [],
            "digest": {},
            "errors": [],
            "start_time": 0.0,
        }

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn),
            patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm),
            patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        digest = Digest.model_validate(result["digest"])
        # Should have errors from both extraction (2) and summarization (2)
        assert digest.stats.errors >= 4
        # Only 2 articles should succeed (IDs 4, 5)
        assert len(digest.articles) == 2

    @pytest.mark.asyncio
    async def test_error_messages_are_descriptive(self):
        """Test error messages contain useful information.

        Given: Articles that fail extraction
        When: Graph is invoked
        Then: Error messages contain story IDs and error details
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=2,
        )

        stories = [
            Story(
                id=12345,
                title="Important Story",
                url="https://example.com/important",
                score=100,
                by="author",
                time=1704067200,
                descendants=10,
            ),
            Story(
                id=67890,
                title="Another Story",
                url="https://example.com/another",
                score=150,
                by="author2",
                time=1704067200,
                descendants=20,
            ),
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        # All fail with specific errors
        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=Exception("Network timeout after 30s"))
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(return_value=[])

        mock_scoring = MagicMock()
        mock_scoring.score_articles = MagicMock(return_value=[])

        graph = create_hn_graph()

        initial_state = {
            "profile": profile,
            "stories": [],
            "articles": [],
            "filtered_articles": [],
            "summarized_articles": [],
            "scored_articles": [],
            "ranked_articles": [],
            "digest": {},
            "errors": [],
            "start_time": 0.0,
        }

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn),
            patch("hn_herald.graph.nodes.fetch_article.ArticleLoader", return_value=mock_loader),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm),
            patch("hn_herald.graph.nodes.score.ScoringService", return_value=mock_scoring),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        errors = result["errors"]
        assert len(errors) >= 2

        # Check errors contain story IDs
        assert any("12345" in error for error in errors)
        assert any("67890" in error for error in errors)

        # Check errors contain error details
        assert any("Network timeout" in error for error in errors)
