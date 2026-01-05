"""Integration tests for the complete LangGraph digest generation pipeline.

Tests the end-to-end execution of the graph with mocked external services.
"""

import time
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


class TestGraphIntegrationSuccess:
    """Tests for successful end-to-end graph execution."""

    @pytest.mark.asyncio
    async def test_graph_full_pipeline_execution(
        self,
        mock_user_profile,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
        mock_scoring_service,
    ):
        """Test complete graph execution from profile to digest.

        Given: Profile and all mocked services
        When: Graph is invoked
        Then: Complete digest is generated with all stages
        """
        # Arrange
        graph = create_hn_graph()

        initial_state = {
            "profile": mock_user_profile,
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
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn_service),
            patch(
                "hn_herald.graph.nodes.fetch_article.ArticleLoader",
                return_value=mock_article_loader,
            ),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service),
            patch(
                "hn_herald.graph.nodes.score.ScoringService",
                return_value=mock_scoring_service,
            ),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        assert "digest" in result
        digest = Digest.model_validate(result["digest"])
        assert digest is not None
        assert digest.stats is not None
        assert digest.stats.fetched > 0
        assert digest.stats.generation_time_ms > 0

    @pytest.mark.asyncio
    async def test_graph_respects_max_articles_limit(
        self,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
    ):
        """Test graph respects profile.max_articles limit.

        Given: Profile with max_articles=5 and more stories available
        When: Graph is invoked
        Then: Final digest has at most 5 articles
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,  # Accept all
            max_articles=5,
            fetch_type=StoryType.TOP,
            fetch_count=20,
        )

        # Mock many stories
        many_stories = [
            Story(
                id=i,
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                score=100 + i,
                by=f"user{i}",
                time=1704067200,
                descendants=10,
            )
            for i in range(20)
        ]

        mock_hn = AsyncMock()
        mock_hn.fetch_stories = AsyncMock(return_value=many_stories)
        mock_hn.__aenter__ = AsyncMock(return_value=mock_hn)
        mock_hn.__aexit__ = AsyncMock(return_value=None)

        # Mock article extraction
        def create_article(story):
            return Article(
                story_id=story.id,
                title=story.title,
                url=story.url,
                hn_url=f"https://news.ycombinator.com/item?id={story.id}",
                hn_score=story.score,
                author=story.by,
                content=f"Content for story {story.id}",
                word_count=4,
                status=ExtractionStatus.SUCCESS,
            )

        mock_loader = AsyncMock()
        mock_loader.extract_article = AsyncMock(side_effect=create_article)
        mock_loader.__aenter__ = AsyncMock(return_value=mock_loader)
        mock_loader.__aexit__ = AsyncMock(return_value=None)

        # Mock summarization
        def create_summarized(articles):
            return [
                SummarizedArticle(
                    article=article,
                    summary_data=ArticleSummary(
                        summary=(
                            f"This is a comprehensive summary of the article titled {article.title}"
                        ),
                        key_points=["Point 1"],
                        tech_tags=["python"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                )
                for article in articles
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_summarized)

        # Mock scoring
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
        assert len(digest.articles) <= 5  # Respects max_articles

    @pytest.mark.asyncio
    async def test_graph_filters_low_relevance_articles(self):
        """Test graph filters articles below min_score threshold.

        Given: Profile with min_score=0.7 and articles with varying relevance
        When: Graph is invoked
        Then: Only articles above threshold are in final digest
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.7,  # High threshold
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

        def create_summarized(articles):
            return [
                SummarizedArticle(
                    article=article,
                    summary_data=ArticleSummary(
                        summary="This is a valid summary text",
                        key_points=["Key point"],
                        tech_tags=["python"] if article.story_id % 2 == 0 else ["other"],
                    ),
                    summarization_status=SummarizationStatus.SUCCESS,
                )
                for article in articles
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_summarized)

        # Mock scoring - only even IDs get high scores
        def create_scored(summarized, filter_below_min=False):  # noqa: FBT002
            from hn_herald.models.scoring import RelevanceScore

            scored = [
                ScoredArticle(
                    article=summ,
                    relevance=RelevanceScore(
                        score=0.8 if summ.article.story_id % 2 == 0 else 0.3,
                        reason="Matches interests: python"
                        if summ.article.story_id % 2 == 0
                        else "Low relevance",
                        matched_interest_tags=["python"] if summ.article.story_id % 2 == 0 else [],
                        matched_disinterest_tags=[],
                    ),
                    popularity_score=0.6,
                    final_score=0.74 if summ.article.story_id % 2 == 0 else 0.39,
                )
                for summ in summarized
            ]
            if filter_below_min:
                return [s for s in scored if s.final_score >= 0.7]
            return scored

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
        # Only articles with final_score >= 0.7 should be included
        assert all(article.final_score >= 0.7 for article in digest.articles)

    @pytest.mark.asyncio
    async def test_graph_generates_complete_stats(
        self,
        mock_user_profile,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
        mock_scoring_service,
    ):
        """Test graph generates complete statistics.

        Given: Complete graph execution
        When: Digest is generated
        Then: All stats fields are populated correctly
        """
        # Arrange
        graph = create_hn_graph()

        initial_state = {
            "profile": mock_user_profile,
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
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn_service),
            patch(
                "hn_herald.graph.nodes.fetch_article.ArticleLoader",
                return_value=mock_article_loader,
            ),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service),
            patch(
                "hn_herald.graph.nodes.score.ScoringService",
                return_value=mock_scoring_service,
            ),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        digest = Digest.model_validate(result["digest"])
        assert digest.stats.fetched >= 0
        assert digest.stats.filtered >= 0
        assert digest.stats.final >= 0
        assert digest.stats.errors >= 0
        assert digest.stats.generation_time_ms > 0
        assert digest.stats.fetched >= digest.stats.filtered >= digest.stats.final

    @pytest.mark.asyncio
    async def test_graph_execution_time_reasonable(
        self,
        mock_user_profile,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
        mock_scoring_service,
    ):
        """Test graph executes in reasonable time with mocks.

        Given: Complete graph with mocked services
        When: Graph is invoked
        Then: Execution completes quickly (< 5 seconds with mocks)
        """
        # Arrange
        graph = create_hn_graph()

        initial_state = {
            "profile": mock_user_profile,
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

        start = time.time()

        # Act
        with (
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn_service),
            patch(
                "hn_herald.graph.nodes.fetch_article.ArticleLoader",
                return_value=mock_article_loader,
            ),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service),
            patch(
                "hn_herald.graph.nodes.score.ScoringService",
                return_value=mock_scoring_service,
            ),
        ):
            result = await graph.ainvoke(initial_state)

        elapsed = time.time() - start

        # Assert
        assert elapsed < 5.0  # Should be fast with mocks
        assert "digest" in result


class TestGraphIntegrationPartialFailures:
    """Tests for graph handling partial failures gracefully."""

    @pytest.mark.asyncio
    async def test_graph_continues_with_some_article_extraction_failures(self):
        """Test graph continues when some article extractions fail.

        Given: Some articles fail to extract
        When: Graph is invoked
        Then: Pipeline continues with successful articles and accumulates errors
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

        # Mock loader - fail on odd story IDs
        def extract_with_failures(story):
            if story.id % 2 == 1:
                raise Exception(f"Failed to extract story {story.id}")
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
        # Should have successful articles
        assert len(digest.articles) > 0
        # Should have accumulated errors
        assert len(result["errors"]) > 0
        # Stats should reflect partial failures
        assert digest.stats.errors > 0

    @pytest.mark.asyncio
    async def test_graph_handles_summarization_failures(self):
        """Test graph handles some summarization failures.

        Given: Some articles fail to summarize
        When: Graph is invoked
        Then: Pipeline continues with successfully summarized articles
        """
        # Arrange
        profile = UserProfile(
            interest_tags=["python"],
            disinterest_tags=[],
            min_score=0.0,
            max_articles=10,
            fetch_type=StoryType.TOP,
            fetch_count=3,
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
            for i in range(3)
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

        # Mock summarization - fail on story ID 1
        def create_summarized_with_failures(articles):
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
                if article.story_id != 1
                else SummarizedArticle(
                    article=article,
                    summarization_status=SummarizationStatus.API_ERROR,
                    error_message="LLM parse error",
                )
                for article in articles
            ]

        mock_llm = MagicMock()
        mock_llm.summarize_articles_batch = MagicMock(side_effect=create_summarized_with_failures)

        def create_scored(summarized, filter_below_min=False):  # noqa: FBT002
            # Only score successfully summarized articles
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
        # Should have some successful articles
        assert len(digest.articles) > 0
        # Should have errors from failed summarization
        assert digest.stats.errors > 0


class TestGraphIntegrationStateTransitions:
    """Tests for correct state transitions through the pipeline."""

    @pytest.mark.asyncio
    async def test_graph_state_transitions_correctly(
        self,
        mock_user_profile,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
        mock_scoring_service,
    ):
        """Test state transitions through all pipeline stages.

        Given: Complete graph execution
        When: Graph is invoked
        Then: Each stage populates its expected state fields
        """
        # Arrange
        graph = create_hn_graph()

        initial_state = {
            "profile": mock_user_profile,
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
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn_service),
            patch(
                "hn_herald.graph.nodes.fetch_article.ArticleLoader",
                return_value=mock_article_loader,
            ),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service),
            patch(
                "hn_herald.graph.nodes.score.ScoringService",
                return_value=mock_scoring_service,
            ),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert - all state fields should be populated
        assert len(result["stories"]) > 0
        assert len(result["articles"]) > 0
        assert result["start_time"] > 0
        assert "digest" in result
        assert isinstance(result["digest"], dict)

    @pytest.mark.asyncio
    async def test_graph_preserves_profile_through_pipeline(
        self,
        mock_user_profile,
        mock_hn_service,
        mock_article_loader,
        mock_llm_service,
        mock_scoring_service,
    ):
        """Test profile is preserved throughout pipeline.

        Given: Initial profile
        When: Graph is invoked
        Then: Profile is accessible in final state
        """
        # Arrange
        graph = create_hn_graph()

        initial_state = {
            "profile": mock_user_profile,
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
            patch("hn_herald.graph.nodes.fetch_hn.HNClient", return_value=mock_hn_service),
            patch(
                "hn_herald.graph.nodes.fetch_article.ArticleLoader",
                return_value=mock_article_loader,
            ),
            patch("hn_herald.graph.nodes.summarize.LLMService", return_value=mock_llm_service),
            patch(
                "hn_herald.graph.nodes.score.ScoringService",
                return_value=mock_scoring_service,
            ),
        ):
            result = await graph.ainvoke(initial_state)

        # Assert
        assert result["profile"] == mock_user_profile
