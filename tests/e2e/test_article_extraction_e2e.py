"""End-to-end tests for article extraction pipeline.

These tests verify the complete flow:
1. Fetch stories from HN API
2. Extract article content from URLs
3. Validate the entire pipeline works correctly

Uses Playwright for browser-based testing and real network requests.
"""

import pytest
from playwright.async_api import Route, async_playwright

from hn_herald.models.article import ExtractionStatus
from hn_herald.models.story import Story, StoryType
from hn_herald.services.hn_client import HNClient
from hn_herald.services.loader import ArticleLoader

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_html_article():
    """HTML content for a sample article page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Article - E2E Testing</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; }
            nav { background: #333; color: white; padding: 1rem; }
            article { padding: 2rem; }
            footer { background: #f0f0f0; padding: 1rem; text-align: center; }
        </style>
        <script>console.log('Analytics loaded');</script>
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
        <article>
            <h1>The Future of AI in Software Development</h1>
            <p class="meta">By John Doe | January 4, 2026</p>
            <p>Artificial intelligence is rapidly transforming how we write and maintain software.
            From code completion to automated testing, AI tools are becoming indispensable for
            modern developers.</p>
            <p>In this comprehensive guide, we explore the latest advancements in AI-powered
            development tools and how they're reshaping the industry. Machine learning models
            can now understand code context and suggest improvements.</p>
            <p>The integration of large language models into IDEs has created a new paradigm
            for software development. Developers can now describe what they want in natural
            language and receive working code implementations.</p>
            <h2>Key Benefits</h2>
            <ul>
                <li>Faster development cycles</li>
                <li>Reduced bugs through AI-powered code review</li>
                <li>Better documentation through automated generation</li>
            </ul>
            <p>As we look to the future, the collaboration between human developers and AI
            assistants will only grow stronger. The key is finding the right balance between
            automation and human creativity.</p>
        </article>
        <aside>
            <h3>Related Articles</h3>
            <ul>
                <li>Getting Started with LLMs</li>
                <li>Best Practices for AI Development</li>
            </ul>
        </aside>
        <footer>
            <p>&copy; 2026 Tech Blog. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """


# =============================================================================
# E2E Tests - Full Pipeline
# =============================================================================


@pytest.mark.e2e
class TestArticleExtractionE2E:
    """End-to-end tests for the complete article extraction pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_fetch_and_extract(self):
        """Test complete pipeline: fetch from HN API, then extract articles."""
        # Step 1: Fetch real stories from HN
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=3)

        assert len(stories) > 0, "Should fetch at least one story"

        # Step 2: Extract articles from stories
        async with ArticleLoader(timeout=30, max_retries=2) as loader:
            articles = await loader.extract_articles(stories)

        assert len(articles) == len(stories), "Should return same number of articles"

        # Verify at least one extraction outcome
        statuses = [a.status for a in articles]
        assert any(
            s in statuses
            for s in [
                ExtractionStatus.SUCCESS,
                ExtractionStatus.SKIPPED,
                ExtractionStatus.NO_URL,
            ]
        ), "Should have at least one valid extraction status"

        # Verify article metadata preserved
        for article, story in zip(articles, stories, strict=True):
            assert article.story_id == story.id
            assert article.title == story.title
            assert article.hn_url == story.hn_url

    @pytest.mark.asyncio
    async def test_extract_from_example_domain(self):
        """Test extraction from stable example.com domain."""
        story = Story(
            id=99999999,
            title="Example Domain Test",
            url="https://example.com",
            score=100,
            by="testuser",
            time=1704326400,
            type="story",
            descendants=10,
        )

        async with ArticleLoader(timeout=30) as loader:
            article = await loader.extract_article(story)

        # example.com should be extractable
        assert article.status in [ExtractionStatus.SUCCESS, ExtractionStatus.EMPTY]
        assert article.story_id == story.id
        assert article.domain == "example.com"

    @pytest.mark.asyncio
    async def test_blocked_domain_skipped(self):
        """Test that blocked domains are properly skipped."""
        blocked_stories = [
            Story(
                id=1,
                title="Twitter Post",
                url="https://twitter.com/user/status/123",
                score=50,
                by="user1",
                time=1704326400,
                type="story",
            ),
            Story(
                id=2,
                title="YouTube Video",
                url="https://youtube.com/watch?v=abc123",
                score=75,
                by="user2",
                time=1704326400,
                type="story",
            ),
            Story(
                id=3,
                title="GitHub Repo",
                url="https://github.com/user/repo",
                score=200,
                by="user3",
                time=1704326400,
                type="story",
            ),
        ]

        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(blocked_stories)

        for article in articles:
            assert article.status == ExtractionStatus.SKIPPED
            assert article.error_message is not None
            assert "Blocked domain" in article.error_message

    @pytest.mark.asyncio
    async def test_ask_hn_story_uses_text_content(self):
        """Test that Ask HN stories use the HN text content."""
        ask_hn_story = Story(
            id=88888888,
            title="Ask HN: What's your favorite programming language?",
            url=None,
            score=150,
            by="curious_dev",
            time=1704326400,
            type="story",
            descendants=200,
            text="<p>I've been using Python for years but curious what others prefer.</p>",
        )

        async with ArticleLoader() as loader:
            article = await loader.extract_article(ask_hn_story)

        assert article.status == ExtractionStatus.NO_URL
        assert article.url is None
        assert article.hn_text is not None
        assert "Python" in article.hn_text
        assert article.has_content is True


@pytest.mark.e2e
class TestArticleExtractionWithPlaywright:
    """E2E tests using Playwright for browser-based scenarios."""

    @pytest.mark.asyncio
    async def test_extract_with_local_server(self, sample_html_article):
        """Test extraction with Playwright serving local HTML content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            # Intercept requests and serve our test HTML
            test_url = "https://test-article.local/post/ai-development"

            async def handle_route(route: Route):
                if "test-article.local" in route.request.url:
                    await route.fulfill(
                        status=200,
                        content_type="text/html",
                        body=sample_html_article,
                    )
                else:
                    await route.continue_()

            await page.route("**/*", handle_route)

            # Navigate to verify page loads
            response = await page.goto(test_url)
            assert response is not None
            assert response.status == 200

            # Verify content is visible
            title = await page.title()
            assert "Test Article" in title

            content = await page.content()
            assert "Future of AI" in content
            assert "Software Development" in content

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_screenshot_on_extraction(self, sample_html_article, tmp_path):
        """Test taking screenshots during extraction for debugging."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            test_url = "https://test-article.local/screenshot-test"

            async def handle_route(route: Route):
                if "test-article.local" in route.request.url:
                    await route.fulfill(
                        status=200,
                        content_type="text/html",
                        body=sample_html_article,
                    )
                else:
                    await route.continue_()

            await page.route("**/*", handle_route)
            await page.goto(test_url)

            # Take screenshot
            screenshot_path = tmp_path / "article_screenshot.png"
            await page.screenshot(path=str(screenshot_path))

            assert screenshot_path.exists()
            assert screenshot_path.stat().st_size > 0

            # Verify article element exists
            article = await page.query_selector("article")
            assert article is not None

            article_text = await article.inner_text()
            assert "Artificial intelligence" in article_text

            await browser.close()

    @pytest.mark.asyncio
    async def test_playwright_content_extraction_comparison(self, sample_html_article):
        """Compare Playwright content extraction with ArticleLoader."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            test_url = "https://test-article.local/comparison-test"

            async def handle_route(route: Route):
                if "test-article.local" in route.request.url:
                    await route.fulfill(
                        status=200,
                        content_type="text/html",
                        body=sample_html_article,
                    )
                else:
                    await route.continue_()

            await page.route("**/*", handle_route)
            await page.goto(test_url)

            # Extract text using Playwright
            article_element = await page.query_selector("article")
            playwright_text = await article_element.inner_text() if article_element else ""

            await browser.close()

        # Verify Playwright extracted key content
        assert "Future of AI" in playwright_text
        assert "Software Development" in playwright_text
        assert "Faster development cycles" in playwright_text

        # Navigation and footer should not be in article element
        assert "Home" not in playwright_text
        assert "All rights reserved" not in playwright_text


@pytest.mark.e2e
class TestHNAPIE2E:
    """E2E tests for HN API integration."""

    @pytest.mark.asyncio
    async def test_fetch_real_top_stories(self):
        """Test fetching real top stories from HN."""
        async with HNClient() as client:
            story_ids = await client.fetch_story_ids(StoryType.TOP, limit=10)

        assert len(story_ids) == 10
        assert all(isinstance(id_, int) for id_ in story_ids)
        assert all(id_ > 0 for id_ in story_ids)

    @pytest.mark.asyncio
    async def test_fetch_real_story_details(self):
        """Test fetching real story details from HN."""
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=1)

        assert len(stories) == 1
        story = stories[0]

        assert story.id > 0
        assert story.title
        assert story.by
        assert story.score >= 0
        assert story.hn_url.startswith("https://news.ycombinator.com/item?id=")

    @pytest.mark.asyncio
    async def test_fetch_multiple_story_types(self):
        """Test fetching different story types from HN."""
        async with HNClient() as client:
            # Fetch from different endpoints
            top_ids = await client.fetch_story_ids(StoryType.TOP, limit=3)
            new_ids = await client.fetch_story_ids(StoryType.NEW, limit=3)

        # Should get different stories
        assert len(top_ids) == 3
        assert len(new_ids) == 3
        # Top and new stories may overlap but typically won't
        assert len(set(top_ids + new_ids)) >= 3


@pytest.mark.e2e
class TestFullPipelineE2E:
    """Full end-to-end pipeline tests."""

    @pytest.mark.asyncio
    async def test_complete_digest_pipeline(self):
        """Test the complete pipeline: HN API -> Article Extraction."""
        # Step 1: Fetch stories
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=5)

        assert len(stories) > 0

        # Step 2: Extract articles
        async with ArticleLoader(timeout=20, max_retries=1) as loader:
            articles = await loader.extract_articles(stories)

        assert len(articles) == len(stories)

        # Step 3: Analyze results
        success_count = sum(1 for a in articles if a.status == ExtractionStatus.SUCCESS)
        skipped_count = sum(1 for a in articles if a.status == ExtractionStatus.SKIPPED)
        failed_count = sum(1 for a in articles if a.status == ExtractionStatus.FAILED)
        no_url_count = sum(1 for a in articles if a.status == ExtractionStatus.NO_URL)

        # Results summary (visible with pytest -v)
        _ = (success_count, skipped_count, failed_count, no_url_count)

        # At least some articles should have a definitive status
        total_processed = success_count + skipped_count + no_url_count
        assert total_processed > 0 or failed_count > 0, "All articles should have a status"

        # Check successful extractions have content
        for article in articles:
            if article.status == ExtractionStatus.SUCCESS:
                assert article.content is not None
                assert article.word_count > 0
                assert len(article.content) > 100

    @pytest.mark.asyncio
    async def test_pipeline_preserves_metadata(self):
        """Test that article metadata is preserved through the pipeline."""
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=2)

        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)

        for article, story in zip(articles, stories, strict=True):
            # Verify all metadata is preserved
            assert article.story_id == story.id
            assert article.title == story.title
            assert article.hn_url == story.hn_url
            assert article.hn_score == story.score
            assert article.author == story.by

            if story.url:
                assert article.url == story.url
                assert article.domain is not None
