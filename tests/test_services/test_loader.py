"""Tests for ArticleLoader service."""

import httpx
import pytest
import respx

from hn_herald.models.article import ExtractionStatus
from hn_herald.models.story import Story
from hn_herald.services.loader import ArticleLoader

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_html_page():
    """Sample HTML page for content extraction testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Article</title>
        <script>var tracking = true;</script>
        <style>body { font-family: sans-serif; }</style>
    </head>
    <body>
        <nav>Navigation menu</nav>
        <header>Site header</header>
        <article>
            <h1>Main Article Title</h1>
            <p>This is the first paragraph of the article with important content.</p>
            <p>This is the second paragraph with more information about the topic.</p>
            <p>The third paragraph contains additional context.</p>
        </article>
        <aside>Sidebar content</aside>
        <footer>Footer content</footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_story():
    """Sample Story object for testing."""
    return Story(
        id=12345,
        title="Test Story Title",
        url="https://example.com/article",
        score=100,
        by="testuser",
        time=1709654321,
        descendants=50,
    )


@pytest.fixture
def sample_story_no_url():
    """Sample Ask HN story without external URL."""
    return Story(
        id=12346,
        title="Ask HN: What are your favorite tools?",
        url=None,
        score=75,
        by="curious",
        time=1709654322,
        descendants=30,
        text="I'm looking for recommendations on developer tools...",
    )


@pytest.fixture
def sample_story_twitter():
    """Sample story with Twitter URL."""
    return Story(
        id=12347,
        title="Interesting Twitter Thread",
        url="https://twitter.com/user/status/12345",
        score=50,
        by="shareuser",
        time=1709654323,
        descendants=10,
    )


@pytest.fixture
def sample_story_pdf():
    """Sample story with PDF URL."""
    return Story(
        id=12348,
        title="Research Paper PDF",
        url="https://example.com/paper.pdf",
        score=80,
        by="researcher",
        time=1709654324,
        descendants=25,
    )


# =============================================================================
# Domain and URL Filtering Tests
# =============================================================================


class TestURLFiltering:
    """Tests for URL filtering logic."""

    @pytest.mark.parametrize(
        "url,expected_skip",
        [
            ("https://twitter.com/user/status/123", True),
            ("https://x.com/user/status/123", True),
            ("https://reddit.com/r/programming", True),
            ("https://old.reddit.com/r/programming", True),
            ("https://youtube.com/watch?v=123", True),
            ("https://youtu.be/123", True),
            ("https://github.com/user/repo", True),
            ("https://medium.com/@user/article", True),
            ("https://nytimes.com/article", True),
            ("https://linkedin.com/posts/123", True),
        ],
    )
    def test_should_skip_blocked_domains(self, url, expected_skip):
        """Blocked domains should be skipped."""
        loader = ArticleLoader()
        should_skip, reason = loader.should_skip_url(url)
        assert should_skip == expected_skip
        if expected_skip:
            assert "Blocked domain" in reason

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/article",
            "https://blog.example.org/post",
            "https://techcrunch.com/article",
            "https://arstechnica.com/story",
            "https://news.example.com/breaking",
        ],
    )
    def test_should_not_skip_valid_urls(self, url):
        """Valid URLs should not be skipped."""
        loader = ArticleLoader()
        should_skip, reason = loader.should_skip_url(url)
        assert should_skip is False
        assert reason == ""

    @pytest.mark.parametrize(
        "url,expected_skip",
        [
            ("https://example.com/paper.pdf", True),
            ("https://example.com/doc.docx", True),
            ("https://example.com/video.mp4", True),
            ("https://example.com/image.png", True),
            ("https://example.com/archive.zip", True),
        ],
    )
    def test_should_skip_blocked_extensions(self, url, expected_skip):
        """Blocked file extensions should be skipped."""
        loader = ArticleLoader()
        should_skip, reason = loader.should_skip_url(url)
        assert should_skip == expected_skip
        if expected_skip:
            assert "Blocked file type" in reason

    def test_should_skip_empty_url(self):
        """Empty URL should be skipped."""
        loader = ArticleLoader()
        should_skip, reason = loader.should_skip_url("")
        assert should_skip is True
        assert "No URL" in reason

    def test_should_skip_none_url(self):
        """None URL should be skipped (with type guard)."""
        loader = ArticleLoader()
        should_skip, _reason = loader.should_skip_url(None)
        assert should_skip is True


class TestDomainExtraction:
    """Tests for domain extraction."""

    @pytest.mark.parametrize(
        "url,expected_domain",
        [
            ("https://example.com/article", "example.com"),
            ("https://www.example.com/article", "example.com"),
            ("https://blog.example.com/post", "blog.example.com"),
            ("http://example.org/page", "example.org"),
            ("https://sub.domain.example.com/path", "sub.domain.example.com"),
        ],
    )
    def test_extract_domain(self, url, expected_domain):
        """Should correctly extract domain from URL."""
        loader = ArticleLoader()
        domain = loader.extract_domain(url)
        assert domain == expected_domain

    def test_extract_domain_removes_www(self):
        """Should remove www. prefix from domain."""
        loader = ArticleLoader()
        domain = loader.extract_domain("https://www.example.com/article")
        assert domain == "example.com"

    def test_extract_domain_invalid_url(self):
        """Should return None for invalid URL."""
        loader = ArticleLoader()
        domain = loader.extract_domain("not-a-valid-url")
        assert domain is None

    def test_extract_domain_empty_url(self):
        """Should return None for empty URL."""
        loader = ArticleLoader()
        domain = loader.extract_domain("")
        assert domain is None


# =============================================================================
# Article Extraction Tests
# =============================================================================


class TestArticleExtraction:
    """Tests for article content extraction."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_article_success(self, sample_story, sample_html_page):
        """Should successfully extract article content."""
        respx.get("https://example.com/article").mock(
            return_value=httpx.Response(
                200,
                text=sample_html_page,
                headers={"content-type": "text/html"},
            )
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story)

        assert article.status == ExtractionStatus.SUCCESS
        assert article.story_id == sample_story.id
        assert article.title == sample_story.title
        assert article.content is not None
        assert len(article.content) > 0
        assert article.word_count > 0
        assert article.domain == "example.com"

    @pytest.mark.asyncio
    async def test_extract_article_no_url(self, sample_story_no_url):
        """Should handle stories without external URL."""
        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story_no_url)

        assert article.status == ExtractionStatus.NO_URL
        assert article.story_id == sample_story_no_url.id
        assert article.content is None
        assert article.hn_text == sample_story_no_url.text
        assert article.has_content is True

    @pytest.mark.asyncio
    async def test_extract_article_blocked_domain(self, sample_story_twitter):
        """Should skip blocked domains."""
        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story_twitter)

        assert article.status == ExtractionStatus.SKIPPED
        assert "Blocked domain" in article.error_message
        assert article.content is None

    @pytest.mark.asyncio
    async def test_extract_article_blocked_extension(self, sample_story_pdf):
        """Should skip blocked file extensions."""
        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story_pdf)

        assert article.status == ExtractionStatus.SKIPPED
        assert "Blocked file type" in article.error_message
        assert article.content is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_article_network_error(self, sample_story):
        """Should handle network errors gracefully."""
        respx.get("https://example.com/article").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        async with ArticleLoader(max_retries=1) as loader:
            article = await loader.extract_article(sample_story)

        assert article.status == ExtractionStatus.FAILED
        assert article.content is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_article_http_error(self, sample_story):
        """Should handle HTTP errors gracefully."""
        respx.get("https://example.com/article").mock(return_value=httpx.Response(404))

        async with ArticleLoader(max_retries=1) as loader:
            article = await loader.extract_article(sample_story)

        assert article.status == ExtractionStatus.FAILED
        assert article.content is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_article_empty_content(self, sample_story):
        """Should handle pages with no extractable content."""
        empty_html = "<html><body></body></html>"
        respx.get("https://example.com/article").mock(
            return_value=httpx.Response(
                200,
                text=empty_html,
                headers={"content-type": "text/html"},
            )
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story)

        assert article.status == ExtractionStatus.EMPTY
        assert article.content is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_article_non_html_content(self, sample_story):
        """Should handle non-HTML content types."""
        respx.get("https://example.com/article").mock(
            return_value=httpx.Response(
                200,
                text='{"data": "json content"}',
                headers={"content-type": "application/json"},
            )
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(sample_story)

        assert article.status == ExtractionStatus.EMPTY
        assert article.content is None


# =============================================================================
# Batch Extraction Tests
# =============================================================================


class TestBatchExtraction:
    """Tests for batch article extraction."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_articles_parallel(self, sample_html_page):
        """Should extract multiple articles in parallel."""
        stories = [
            Story(
                id=1,
                title="Article 1",
                url="https://example1.com/article",
                score=100,
                by="user1",
                time=1709654321,
            ),
            Story(
                id=2,
                title="Article 2",
                url="https://example2.com/article",
                score=200,
                by="user2",
                time=1709654322,
            ),
            Story(
                id=3,
                title="Article 3",
                url="https://example3.com/article",
                score=300,
                by="user3",
                time=1709654323,
            ),
        ]

        for story in stories:
            respx.get(story.url).mock(
                return_value=httpx.Response(
                    200,
                    text=sample_html_page,
                    headers={"content-type": "text/html"},
                )
            )

        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)

        assert len(articles) == 3
        for i, article in enumerate(articles):
            assert article.story_id == stories[i].id
            assert article.status == ExtractionStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_extract_articles_preserves_order(self):
        """Should preserve order of input stories in output."""
        stories = [
            Story(id=1, title="First", url=None, score=100, by="user", time=1709654321),
            Story(id=2, title="Second", url=None, score=200, by="user", time=1709654322),
            Story(id=3, title="Third", url=None, score=300, by="user", time=1709654323),
        ]

        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)

        assert len(articles) == 3
        assert articles[0].story_id == 1
        assert articles[1].story_id == 2
        assert articles[2].story_id == 3

    @pytest.mark.asyncio
    async def test_extract_articles_empty_list(self):
        """Should handle empty story list."""
        async with ArticleLoader() as loader:
            articles = await loader.extract_articles([])

        assert articles == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_extract_articles_mixed_results(self, sample_html_page):
        """Should handle mixed success/failure results."""
        stories = [
            Story(
                id=1,
                title="Success Article",
                url="https://example.com/success",
                score=100,
                by="user",
                time=1709654321,
            ),
            Story(
                id=2,
                title="Ask HN",
                url=None,
                score=50,
                by="user",
                time=1709654322,
                text="Question text",
            ),
            Story(
                id=3,
                title="Twitter Link",
                url="https://twitter.com/user/status/123",
                score=75,
                by="user",
                time=1709654323,
            ),
        ]

        respx.get("https://example.com/success").mock(
            return_value=httpx.Response(
                200,
                text=sample_html_page,
                headers={"content-type": "text/html"},
            )
        )

        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)

        assert len(articles) == 3
        assert articles[0].status == ExtractionStatus.SUCCESS
        assert articles[1].status == ExtractionStatus.NO_URL
        assert articles[2].status == ExtractionStatus.SKIPPED


# =============================================================================
# Content Processing Tests
# =============================================================================


class TestContentProcessing:
    """Tests for content processing and truncation."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_content_truncation(self):
        """Should truncate long content to max length."""
        # Create HTML with very long content
        long_paragraph = "This is a long paragraph. " * 1000
        long_html = f"""
        <html><body>
        <article>
            <p>{long_paragraph}</p>
        </article>
        </body></html>
        """

        story = Story(
            id=1,
            title="Long Article",
            url="https://example.com/long",
            score=100,
            by="user",
            time=1709654321,
        )

        respx.get("https://example.com/long").mock(
            return_value=httpx.Response(
                200,
                text=long_html,
                headers={"content-type": "text/html"},
            )
        )

        async with ArticleLoader(max_content_length=1000) as loader:
            article = await loader.extract_article(story)

        assert article.status == ExtractionStatus.SUCCESS
        assert len(article.content) <= 1000

    @respx.mock
    @pytest.mark.asyncio
    async def test_removes_script_and_style_tags(self):
        """Should remove script and style tags from content."""
        html_with_scripts = """
        <html><body>
        <script>var x = 1;</script>
        <style>.class { color: red; }</style>
        <article>
            <p>This is the actual content that should be extracted from the article. It contains
            meaningful text that readers would want to consume. This paragraph is long enough
            to pass the minimum content length validation that ensures we have real content.</p>
        </article>
        </body></html>
        """

        story = Story(
            id=1,
            title="Test",
            url="https://example.com/test",
            score=100,
            by="user",
            time=1709654321,
        )

        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(
                200,
                text=html_with_scripts,
                headers={"content-type": "text/html"},
            )
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(story)

        assert article.status == ExtractionStatus.SUCCESS
        assert "var x = 1" not in article.content
        assert "color: red" not in article.content
        assert "actual content" in article.content


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Tests for context manager behavior."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Should properly manage async client lifecycle."""
        loader = ArticleLoader()

        # Client should be None before entering context
        assert loader._client is None

        async with loader:
            # Client should exist inside context
            assert loader._client is not None

        # Client should be None after exiting context
        assert loader._client is None

    @pytest.mark.asyncio
    async def test_handles_missing_client_gracefully(self):
        """Should handle missing client with FAILED status."""
        loader = ArticleLoader()

        story = Story(
            id=1,
            title="Test",
            url="https://example.com/test",
            score=100,
            by="user",
            time=1709654321,
        )

        # When used outside context manager, should return FAILED article
        article = await loader.extract_article(story)
        assert article.status == ExtractionStatus.FAILED
        assert "context manager" in article.error_message


# =============================================================================
# Integration Tests (marked for optional running)
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestIntegration:
    """Integration tests that make real HTTP requests."""

    @pytest.mark.asyncio
    async def test_extract_real_article(self):
        """Extract content from a real public webpage."""
        # Using example.com which is a stable test domain
        story = Story(
            id=1,
            title="Example Domain",
            url="https://example.com",
            score=100,
            by="test",
            time=1709654321,
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(story)

        # example.com should return successfully
        assert article.status in (ExtractionStatus.SUCCESS, ExtractionStatus.EMPTY)
        assert article.domain == "example.com"
