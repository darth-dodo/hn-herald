"""Unit tests for rank node.

Tests the rank_articles node which sorts scored articles by final_score
in descending order.
"""

from hn_herald.graph.nodes.rank import rank_articles
from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.scoring import RelevanceScore, ScoredArticle
from hn_herald.models.summary import (
    ArticleSummary,
    SummarizationStatus,
    SummarizedArticle,
)


class TestRankArticlesSuccess:
    """Tests for successful rank_articles node execution."""

    def test_rank_sorts_by_final_score_descending(self):
        """Test rank sorts articles by final_score in descending order.

        Given: Scored articles with different final_scores
        When: rank_articles node is executed
        Then: Articles are sorted by final_score descending
        """
        # Arrange
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

        scored = [
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.5,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.5,
                final_score=0.5,
            ),
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.8,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.7,
                final_score=0.77,
            ),
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.6,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.6,
                final_score=0.6,
            ),
        ]
        state = {"scored_articles": scored}

        # Act
        result = rank_articles(state)

        # Assert
        assert "ranked_articles" in result
        ranked = result["ranked_articles"]
        assert len(ranked) == 3
        assert ranked[0].final_score == 0.77
        assert ranked[1].final_score == 0.6
        assert ranked[2].final_score == 0.5

    def test_rank_preserves_all_articles(self):
        """Test rank preserves all scored articles.

        Given: List of scored articles
        When: rank_articles node is executed
        Then: All articles are present in ranked list
        """
        # Arrange
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

        scored = [
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
            for _ in range(10)
        ]
        state = {"scored_articles": scored}

        # Act
        result = rank_articles(state)

        # Assert
        assert len(result["ranked_articles"]) == len(scored)

    def test_rank_stable_sort_equal_scores(self):
        """Test rank uses stable sort for equal scores.

        Given: Scored articles with identical final_scores
        When: rank_articles node is executed
        Then: Original order is preserved for equal scores
        """
        # Arrange
        articles = [
            Article(
                story_id=i,
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                hn_url=f"https://news.ycombinator.com/item?id={i}",
                hn_score=100,
                author=f"user{i}",
                content="Content",
                word_count=1,
                status=ExtractionStatus.SUCCESS,
            )
            for i in range(1, 4)
        ]

        summarized = [
            SummarizedArticle(
                article=article,
                summary_data=ArticleSummary(
                    summary="This is a complete test summary",
                    key_points=["Key point"],
                    tech_tags=[],
                ),
                summarization_status=SummarizationStatus.SUCCESS,
            )
            for article in articles
        ]

        # All have same score
        scored = [
            ScoredArticle(
                article=summ,
                relevance=RelevanceScore(
                    score=0.7,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.7,
                final_score=0.7,
            )
            for summ in summarized
        ]
        state = {"scored_articles": scored}

        # Act
        result = rank_articles(state)

        # Assert - order should be preserved
        ranked = result["ranked_articles"]
        assert ranked[0].article.article.story_id == 1
        assert ranked[1].article.article.story_id == 2
        assert ranked[2].article.article.story_id == 3


class TestRankArticlesEmptyInput:
    """Tests for rank_articles handling empty inputs."""

    def test_rank_empty_scored_articles(self):
        """Test rank handles empty scored articles list.

        Given: Empty scored_articles list
        When: rank_articles node is executed
        Then: Empty ranked_articles list is returned
        """
        # Arrange
        state = {"scored_articles": []}

        # Act
        result = rank_articles(state)

        # Assert
        assert "ranked_articles" in result
        assert result["ranked_articles"] == []


class TestRankArticlesSingleArticle:
    """Tests for rank_articles with single article."""

    def test_rank_single_article(self):
        """Test rank handles single article correctly.

        Given: Single scored article
        When: rank_articles node is executed
        Then: Single article is returned in ranked list
        """
        # Arrange
        article = Article(
            story_id=1,
            title="Single",
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

        scored = [
            ScoredArticle(
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
        ]
        state = {"scored_articles": scored}

        # Act
        result = rank_articles(state)

        # Assert
        assert len(result["ranked_articles"]) == 1
        assert result["ranked_articles"][0].final_score == 0.74


class TestRankArticlesLogging:
    """Tests for rank_articles logging behavior."""

    def test_rank_logs_article_count(self, caplog):
        """Test rank logs number of articles being ranked.

        Given: Scored articles
        When: rank_articles node is executed
        Then: Article count is logged
        """
        # Arrange
        import logging

        caplog.set_level(logging.INFO)
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

        scored = [
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
        state = {"scored_articles": scored}

        # Act
        rank_articles(state)

        # Assert
        assert any("Ranking 5 articles" in record.message for record in caplog.records)

    def test_rank_logs_top_article_debug(self, caplog):
        """Test rank logs top article information in debug mode.

        Given: Scored articles
        When: rank_articles node is executed
        Then: Top article info is logged in debug
        """
        # Arrange
        import logging

        caplog.set_level(logging.DEBUG)
        article = Article(
            story_id=1,
            title="Top Article",
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

        scored = [
            ScoredArticle(
                article=summarized,
                relevance=RelevanceScore(
                    score=0.9,
                    reason="Test relevance",
                    matched_interest_tags=["python"],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.8,
                final_score=0.87,
            )
        ]
        state = {"scored_articles": scored}

        # Act
        rank_articles(state)

        # Assert
        assert any(
            "Top article" in record.message and "Top Article" in record.message
            for record in caplog.records
        )

    def test_rank_logs_score_range_debug(self, caplog):
        """Test rank logs score range in debug mode.

        Given: Multiple scored articles with different scores
        When: rank_articles node is executed
        Then: Score range is logged in debug
        """
        # Arrange
        import logging

        caplog.set_level(logging.DEBUG)
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

        scored = [
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.9,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.8,
                final_score=0.87,
            ),
            ScoredArticle(
                article=base_summarized,
                relevance=RelevanceScore(
                    score=0.5,
                    reason="Test relevance",
                    matched_interest_tags=[],
                    matched_disinterest_tags=[],
                ),
                popularity_score=0.4,
                final_score=0.47,
            ),
        ]
        state = {"scored_articles": scored}

        # Act
        rank_articles(state)

        # Assert
        assert any("Score range" in record.message for record in caplog.records)
