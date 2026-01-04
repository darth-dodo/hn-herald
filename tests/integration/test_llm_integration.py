"""Integration tests for LLM service with real API calls.

These tests make REAL API calls to the Anthropic API and are marked as slow
and integration tests. They will be skipped if ANTHROPIC_API_KEY is not set.

Run with: pytest -m integration tests/integration/
"""

import pytest

from hn_herald.models.article import Article, ExtractionStatus
from hn_herald.models.summary import SummarizationStatus
from hn_herald.services.llm import LLMService

# Mark all tests as slow and integration
pytestmark = [
    pytest.mark.slow,
    pytest.mark.integration,
]


@pytest.fixture
def require_api_key(monkeypatch):
    """Skip test if no valid API key is available, load from .env file."""
    from pathlib import Path

    # Try to load real API key from .env file (bypassing conftest.py defaults)
    env_file = Path(__file__).parent.parent.parent / ".env"
    api_key = None

    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip("'\"")
                break

    if not api_key or not api_key.startswith("sk-"):
        pytest.skip("No valid ANTHROPIC_API_KEY in .env file")

    # Set the real key in environment for this test
    monkeypatch.setenv("ANTHROPIC_API_KEY", api_key)


@pytest.fixture
def llm_service(require_api_key):
    """Create LLMService instance for integration tests.

    Uses settings from environment, ensuring real API key is used.
    Depends on require_api_key to skip if no valid key is available.
    """
    return LLMService()


@pytest.fixture
def article_with_tech_content():
    """Create an Article with realistic tech content for summarization.

    Returns an Article instance with content about Python performance
    improvements that should generate meaningful summaries.
    """
    return Article(
        story_id=12345678,
        title="Python 3.13 Performance Improvements: A Deep Dive",
        url="https://en.wikipedia.org/wiki/Extreme_programming",
        hn_url="https://news.ycombinator.com/item?id=12345678",
        hn_score=250,
        hn_comments=85,
        author="pythondev",
        content="""
        Python 3.13 Performance Improvements: A Deep Dive

        The Python core development team has released Python 3.13 with significant
        performance improvements that benefit both CPU-bound and I/O-bound applications.

        Key Performance Enhancements:

        1. Faster Function Calls
        The new interpreter implementation reduces function call overhead by up to 15%.
        This benefits applications with many small function calls, common in web frameworks.

        2. Improved Memory Management
        The garbage collector has been optimized to reduce pause times by 30%. Large
        applications will see more consistent performance under load.

        3. JIT Compilation Experiments
        An experimental JIT compiler is now available, showing 2-3x speedups in
        compute-intensive loops. This is opt-in and requires a special build flag.

        4. Asyncio Improvements
        The asyncio event loop has been rewritten with a more efficient task scheduler.
        High-concurrency applications see 20% better throughput.

        Migration Considerations:
        - Most existing code works without modification
        - Some C extensions may need recompilation
        - The new features are backward compatible

        Benchmarks show that web applications built with FastAPI and Django see
        10-20% improvement in request handling. Scientific computing with NumPy
        benefits from the JIT compiler experiments.

        The Python community continues to push the boundaries of what's possible
        with dynamic languages while maintaining the simplicity that makes Python
        so popular among developers.
        """.strip(),
        word_count=250,
        status=ExtractionStatus.SUCCESS,
        domain="en.wikipedia.org",
    )


@pytest.fixture
def article_with_minimal_content():
    """Create an Article with minimal content.

    Returns an Article with just a sentence or two of content.
    """
    content = (
        "The Rust 2024 edition is coming soon with new async features and "
        "improved error handling. The stabilization of async closures is the highlight."
    )
    return Article(
        story_id=87654321,
        title="Quick Update on Rust 2024 Edition",
        url="https://en.wikipedia.org/wiki/Extreme_programming",
        hn_url="https://news.ycombinator.com/item?id=87654321",
        hn_score=100,
        hn_comments=20,
        author="rustdev",
        content=content,
        word_count=25,
        status=ExtractionStatus.SUCCESS,
        domain="en.wikipedia.org",
    )


@pytest.fixture
def article_with_no_content():
    """Create an Article with no content.

    Returns an Article where both content and hn_text are None.
    """
    return Article(
        story_id=11111111,
        title="Article Without Content",
        url="https://en.wikipedia.org/wiki/Extreme_programming",
        hn_url="https://news.ycombinator.com/item?id=11111111",
        hn_score=50,
        hn_comments=10,
        author="nocontentuser",
        content=None,
        hn_text=None,
        word_count=0,
        status=ExtractionStatus.EMPTY,
        domain="en.wikipedia.org",
    )


@pytest.fixture
def multiple_articles(article_with_tech_content, article_with_minimal_content):
    """Create a list of articles for batch summarization testing.

    Returns a list of 2 articles with content.
    """
    # Create a second tech article with different content
    second_article = Article(
        story_id=22222222,
        title="Building Production-Ready LLM Applications",
        url="https://en.wikipedia.org/wiki/Extreme_programming",
        hn_url="https://news.ycombinator.com/item?id=22222222",
        hn_score=180,
        hn_comments=65,
        author="aibuilder",
        content="""
        Building Production-Ready LLM Applications

        Deploying large language models in production requires careful consideration
        of latency, cost, and reliability. This guide covers essential patterns.

        Key Considerations:

        1. Prompt Engineering
        Structure prompts for consistent outputs. Use few-shot examples and clear
        formatting instructions to reduce hallucinations.

        2. Caching Strategies
        Implement semantic caching to reduce API costs by 40-60%. Hash similar
        queries and serve cached responses for identical requests.

        3. Error Handling
        Build robust retry logic with exponential backoff. Handle rate limits,
        timeouts, and malformed responses gracefully.

        4. Monitoring
        Track latency, token usage, and response quality. Set up alerts for
        degraded performance or unusual patterns.

        Production LLM systems require the same engineering rigor as any
        distributed system, with additional considerations for AI-specific failure modes.
        """.strip(),
        word_count=150,
        status=ExtractionStatus.SUCCESS,
        domain="en.wikipedia.org",
    )

    return [article_with_tech_content, second_article, article_with_minimal_content]


class TestSummarizeRealArticle:
    """Tests for summarizing articles with real API calls."""

    def test_summarize_real_article(self, llm_service, article_with_tech_content):
        """Summarize actual article content and verify result structure.

        This test makes a real API call to Anthropic and validates:
        - summary_data is not None
        - status is SUCCESS
        - summary has reasonable length
        - key_points has items
        - tech_tags has items
        """
        result = llm_service.summarize_article(article_with_tech_content)

        # Verify summarization was successful
        assert result.summary_data is not None, "Summary data should not be None"
        assert result.summarization_status == SummarizationStatus.SUCCESS, (
            f"Expected SUCCESS status, got {result.summarization_status}"
        )
        assert result.error_message is None, (
            f"Should have no error message, got: {result.error_message}"
        )

        # Verify summary content
        summary = result.summary_data.summary
        assert len(summary) >= 20, f"Summary should be at least 20 chars, got {len(summary)}"
        assert len(summary) <= 500, f"Summary should be at most 500 chars, got {len(summary)}"

        # Verify key points
        key_points = result.summary_data.key_points
        assert len(key_points) >= 1, "Should have at least 1 key point"
        assert len(key_points) <= 5, "Should have at most 5 key points"
        for point in key_points:
            assert isinstance(point, str), "Each key point should be a string"
            assert len(point) > 0, "Key points should not be empty"

        # Verify tech tags
        tech_tags = result.summary_data.tech_tags
        assert isinstance(tech_tags, list), "tech_tags should be a list"
        assert len(tech_tags) >= 1, "Should have at least 1 tech tag"
        for tag in tech_tags:
            assert isinstance(tag, str), "Each tag should be a string"
            assert tag == tag.lower(), "Tags should be lowercase"


class TestSummarizeMinimalContent:
    """Tests for summarizing articles with minimal content."""

    def test_summarize_minimal_content(self, llm_service, article_with_minimal_content):
        """Handle short content and still generate a summary.

        Verifies that even with just a sentence or two, the LLM can
        generate a valid summary structure.
        """
        result = llm_service.summarize_article(article_with_minimal_content)

        # Should still succeed with minimal content
        assert result.summary_data is not None, "Should generate summary even for minimal content"
        assert result.summarization_status == SummarizationStatus.SUCCESS, (
            f"Expected SUCCESS status, got {result.summarization_status}"
        )

        # Verify summary structure is valid
        summary = result.summary_data.summary
        assert len(summary) >= 20, "Summary should meet minimum length requirement"

        key_points = result.summary_data.key_points
        assert len(key_points) >= 1, "Should have at least 1 key point"


class TestSummarizeArticleNoContent:
    """Tests for handling articles without content."""

    def test_summarize_article_no_content(self, llm_service, article_with_no_content):
        """Handle missing content gracefully.

        When an article has no content (content=None and hn_text=None),
        the service should return NO_CONTENT status.
        """
        result = llm_service.summarize_article(article_with_no_content)

        # Should return NO_CONTENT status
        assert result.summarization_status == SummarizationStatus.NO_CONTENT, (
            f"Expected NO_CONTENT status, got {result.summarization_status}"
        )
        assert result.summary_data is None, "Should have no summary data when there is no content"
        # error_message is optional for NO_CONTENT status


class TestSummarizeMultipleArticles:
    """Tests for batch summarization."""

    def test_summarize_multiple_articles(self, llm_service, multiple_articles):
        """Batch summarization preserves order and generates summaries.

        Verifies that:
        - Results are returned in the same order as input
        - Each article with content has a summary
        """
        results = llm_service.summarize_articles(multiple_articles)

        # Verify result count matches input
        assert len(results) == len(multiple_articles), (
            f"Expected {len(multiple_articles)} results, got {len(results)}"
        )

        # Verify order is preserved by checking story_ids
        for i, (result, original) in enumerate(zip(results, multiple_articles, strict=True)):
            assert result.article.story_id == original.story_id, (
                f"Result order mismatch at index {i}: "
                f"expected story_id {original.story_id}, got {result.article.story_id}"
            )

        # Verify each article with content has a summary
        for result in results:
            if result.article.has_content:
                assert result.summary_data is not None, (
                    f"Article {result.article.story_id} has content but no summary"
                )
                assert result.summarization_status == SummarizationStatus.SUCCESS, (
                    f"Article {result.article.story_id} should have SUCCESS status"
                )


class TestOutputStructureValid:
    """Tests for verifying PydanticOutputParser works correctly."""

    def test_output_structure_valid(self, llm_service, article_with_tech_content):
        """Verify PydanticOutputParser produces valid structured output.

        This test validates the complete output structure:
        - summary is a string with minimum length
        - key_points is a list of strings
        - tech_tags is a list of strings
        """
        result = llm_service.summarize_article(article_with_tech_content)

        # Ensure we have a summary
        assert result.summary_data is not None, "Summary data required for this test"
        summary_data = result.summary_data

        # Validate summary field
        assert isinstance(summary_data.summary, str), (
            f"summary should be str, got {type(summary_data.summary)}"
        )
        assert len(summary_data.summary) >= 20, (
            f"summary should be at least 20 chars, got {len(summary_data.summary)}"
        )

        # Validate key_points field
        assert isinstance(summary_data.key_points, list), (
            f"key_points should be list, got {type(summary_data.key_points)}"
        )
        assert len(summary_data.key_points) >= 1, "key_points should have at least 1 item"
        for i, point in enumerate(summary_data.key_points):
            assert isinstance(point, str), f"key_points[{i}] should be str, got {type(point)}"
            assert len(point) > 0, f"key_points[{i}] should not be empty"

        # Validate tech_tags field
        assert isinstance(summary_data.tech_tags, list), (
            f"tech_tags should be list, got {type(summary_data.tech_tags)}"
        )
        for i, tag in enumerate(summary_data.tech_tags):
            assert isinstance(tag, str), f"tech_tags[{i}] should be str, got {type(tag)}"
            # Tags should be normalized to lowercase by the validator
            assert tag == tag.lower(), f"tech_tags[{i}] should be lowercase, got '{tag}'"

    def test_summary_content_is_relevant(self, llm_service, article_with_tech_content):
        """Verify summary content is relevant to the article.

        The summary should contain keywords relevant to Python performance.
        """
        result = llm_service.summarize_article(article_with_tech_content)

        assert result.summary_data is not None, "Summary data required for this test"
        summary_text = result.summary_data.summary.lower()

        # Summary should mention Python or performance-related terms
        relevant_keywords = ["python", "performance", "improve", "faster", "speed"]
        has_relevant_keyword = any(kw in summary_text for kw in relevant_keywords)
        assert has_relevant_keyword, (
            f"Summary should contain relevant keywords, got: {summary_text}"
        )

    def test_tech_tags_are_relevant(self, llm_service, article_with_tech_content):
        """Verify tech tags are relevant to the article content.

        For a Python performance article, tags should include Python-related terms.
        """
        result = llm_service.summarize_article(article_with_tech_content)

        assert result.summary_data is not None, "Summary data required for this test"
        tech_tags = [tag.lower() for tag in result.summary_data.tech_tags]

        # Should have at least one Python-related tag
        python_related = ["python", "python3", "cpython", "jit", "performance", "asyncio"]
        has_python_tag = any(any(related in tag for related in python_related) for tag in tech_tags)
        assert has_python_tag, f"Should have Python-related tags, got: {tech_tags}"


class TestBatchSummarization:
    """Tests for batch summarization (single LLM call for multiple articles)."""

    def test_summarize_articles_batch(self, llm_service, multiple_articles):
        """Batch summarization in single LLM call preserves order and generates summaries.

        Verifies that:
        - Results are returned in the same order as input
        - Each article with content has a summary
        - Single API call is more efficient than sequential
        """
        results = llm_service.summarize_articles_batch(multiple_articles)

        # Verify result count matches input
        assert len(results) == len(multiple_articles), (
            f"Expected {len(multiple_articles)} results, got {len(results)}"
        )

        # Verify order is preserved by checking story_ids
        for i, (result, original) in enumerate(zip(results, multiple_articles, strict=True)):
            assert result.article.story_id == original.story_id, (
                f"Result order mismatch at index {i}"
            )

        # Verify each article with content has a summary
        for result in results:
            if result.article.has_content:
                assert result.summary_data is not None, (
                    f"Article {result.article.story_id} has content but no summary"
                )
                assert result.summarization_status == SummarizationStatus.SUCCESS, (
                    f"Article {result.article.story_id} should have SUCCESS status"
                )

    def test_summarize_articles_batch_empty_list(self, llm_service):
        """Batch summarization handles empty list gracefully."""
        results = llm_service.summarize_articles_batch([])
        assert results == []

    def test_summarize_articles_batch_with_no_content_article(
        self, llm_service, article_with_tech_content, article_with_no_content
    ):
        """Batch summarization handles mixed content articles correctly.

        Articles without content should get NO_CONTENT status,
        articles with content should be summarized.
        """
        articles = [article_with_tech_content, article_with_no_content]
        results = llm_service.summarize_articles_batch(articles)

        assert len(results) == 2

        # First article has content - should be summarized
        assert results[0].summarization_status == SummarizationStatus.SUCCESS
        assert results[0].summary_data is not None

        # Second article has no content - should get NO_CONTENT status
        assert results[1].summarization_status == SummarizationStatus.NO_CONTENT
        assert results[1].summary_data is None
