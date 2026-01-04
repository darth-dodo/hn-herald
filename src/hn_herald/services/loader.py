"""Article content extraction service.

This module provides an async service for extracting article content from URLs.
It handles domain filtering, content extraction, and error handling for the
article extraction pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from hn_herald.config import get_settings
from hn_herald.models.article import Article, ExtractionStatus

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import TracebackType

    from hn_herald.models.story import Story

logger = logging.getLogger(__name__)


class ArticleLoader:
    """Async service for extracting article content from URLs.

    Fetches and processes article content using httpx and BeautifulSoup
    with retry logic, domain filtering, and content truncation.

    Usage:
        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)

    Attributes:
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.
        max_concurrent: Maximum concurrent requests.
        max_content_length: Maximum content length in characters.
    """

    # Domains that should be skipped (problematic for extraction)
    BLOCKED_DOMAINS: ClassVar[set[str]] = {
        # Social media (requires JS, rate-limited)
        "twitter.com",
        "x.com",
        "reddit.com",
        "old.reddit.com",
        "facebook.com",
        "instagram.com",
        # Video platforms (no text content)
        "youtube.com",
        "youtu.be",
        "vimeo.com",
        "tiktok.com",
        # Code hosting (complex structure, often binary)
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        # Google services (auth required)
        "docs.google.com",
        "drive.google.com",
        "sheets.google.com",
        # Paywalled sites
        "medium.com",
        "bloomberg.com",
        "wsj.com",
        "nytimes.com",
        "ft.com",
        "economist.com",
        "washingtonpost.com",
        # Professional networks (auth required)
        "linkedin.com",
    }

    # File extensions that should be skipped
    BLOCKED_EXTENSIONS: ClassVar[set[str]] = {
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        # Archives
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",
        # Media
        ".mp4",
        ".mp3",
        ".wav",
        ".avi",
        ".mov",
        ".mkv",
        ".webm",
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".webp",
        ".bmp",
        ".ico",
    }

    # Tags to remove from HTML before extraction
    REMOVE_TAGS: ClassVar[list[str]] = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "iframe",
        "noscript",
        "svg",
        "form",
        "button",
    ]

    def __init__(
        self,
        timeout: int | None = None,
        max_retries: int = 3,
        max_concurrent: int = 10,
        max_content_length: int | None = None,
    ) -> None:
        """Initialize article loader.

        Args:
            timeout: Request timeout in seconds. Defaults to settings value.
            max_retries: Maximum retry attempts for transient failures.
            max_concurrent: Maximum concurrent requests.
            max_content_length: Maximum content length in characters.
                               Defaults to settings value.
        """
        settings = get_settings()
        self.timeout = timeout or settings.article_fetch_timeout
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent
        self.max_content_length = max_content_length or settings.max_content_length
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> ArticleLoader:
        """Async context manager entry.

        Creates the HTTP client and semaphore for rate limiting.

        Returns:
            The ArticleLoader instance.
        """
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "User-Agent": "HN-Herald/0.1 (+https://github.com/darth-dodo/ai-adventures)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            follow_redirects=True,
            max_redirects=5,
        )
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit.

        Closes the HTTP client and releases resources.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception value if an exception was raised.
            exc_tb: Traceback if an exception was raised.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._semaphore = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, ensuring it's initialized.

        Returns:
            The httpx.AsyncClient instance.

        Raises:
            RuntimeError: If loader is used outside context manager.
        """
        if self._client is None:
            msg = "ArticleLoader must be used as an async context manager"
            raise RuntimeError(msg)
        return self._client

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get the semaphore for rate limiting.

        Returns:
            The asyncio.Semaphore instance.

        Raises:
            RuntimeError: If loader is used outside context manager.
        """
        if self._semaphore is None:
            msg = "ArticleLoader must be used as an async context manager"
            raise RuntimeError(msg)
        return self._semaphore

    def extract_domain(self, url: str) -> str | None:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from.

        Returns:
            Domain string (e.g., 'example.com') or None if invalid.
        """
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                # Remove www. prefix for consistency
                domain = parsed.netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                return domain
        except Exception:
            logger.debug("Failed to parse URL: %s", url)
        return None

    def should_skip_url(self, url: str) -> tuple[bool, str]:
        """Check if URL should be skipped.

        Args:
            url: URL to check.

        Returns:
            Tuple of (should_skip, reason).
        """
        if not url:
            return True, "No URL provided"

        # Check domain
        domain = self.extract_domain(url)
        if domain and domain in self.BLOCKED_DOMAINS:
            return True, f"Blocked domain: {domain}"

        # Check file extension
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        for ext in self.BLOCKED_EXTENSIONS:
            if path_lower.endswith(ext):
                return True, f"Blocked file type: {ext}"

        return False, ""

    def _clean_text(self, text: str) -> str:
        """Clean extracted text content.

        Removes excessive whitespace and normalizes line breaks.

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text content.
        """
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)
        # Split into lines and clean each
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        # Rejoin with single newlines
        return "\n".join(lines)

    def _truncate_content(self, content: str) -> str:
        """Truncate content to maximum length.

        Attempts to truncate at sentence boundaries when possible.

        Args:
            content: Content to truncate.

        Returns:
            Truncated content.
        """
        if len(content) <= self.max_content_length:
            return content

        # Truncate to max length
        truncated = content[: self.max_content_length]

        # Try to find last sentence boundary
        last_period = truncated.rfind(". ")
        last_newline = truncated.rfind("\n")

        # Use the later boundary if it's past halfway point
        boundary = max(last_period, last_newline)
        if boundary > self.max_content_length // 2:
            return truncated[: boundary + 1].strip()

        return truncated.strip()

    def _extract_content_from_html(self, html: str) -> str | None:
        """Extract text content from HTML.

        Uses BeautifulSoup to parse HTML and extract readable text.

        Args:
            html: Raw HTML content.

        Returns:
            Extracted text content or None if extraction failed.
        """
        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            logger.debug("Failed to parse HTML with lxml, trying html.parser")
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception:
                logger.warning("Failed to parse HTML")
                return None

        # Remove unwanted tags
        for tag in soup(self.REMOVE_TAGS):
            tag.decompose()

        # Try to find main content container
        main_content = (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_=re.compile(r"content|post|article|entry|story", re.I))
            or soup.find(id=re.compile(r"content|post|article|entry|story", re.I))
            or soup.find("body")
        )

        if not main_content:
            return None

        # Extract text
        text = main_content.get_text(separator="\n", strip=True)

        # Clean and validate
        cleaned = self._clean_text(text)

        # Must have minimum content
        if len(cleaned) < 100:  # noqa: PLR2004
            return None

        return cleaned

    async def _fetch_content(self, url: str) -> tuple[str | None, str | None]:
        """Fetch and extract content from URL.

        Args:
            url: URL to fetch content from.

        Returns:
            Tuple of (content, error_message). If content is None and error is None,
            content was empty. If content is None and error is set, fetch failed.
        """

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
            reraise=True,
        )
        async def _do_fetch() -> httpx.Response:
            client = self._get_client()
            semaphore = self._get_semaphore()

            async with semaphore:
                response = await client.get(url)
                response.raise_for_status()
                return response

        try:
            response = await _do_fetch()
        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s", url)
            return None, "Request timed out"
        except httpx.HTTPStatusError as e:
            logger.warning("HTTP %d fetching %s", e.response.status_code, url)
            return None, f"HTTP {e.response.status_code}"
        except httpx.TransportError as e:
            logger.warning("Transport error fetching %s: %s", url, e)
            return None, f"Transport error: {e}"

        # Check content type
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            logger.debug("Non-HTML content type for %s: %s", url, content_type)
            return None, None  # Empty content, not an error

        # Extract content from HTML
        content = self._extract_content_from_html(response.text)

        if content:
            content = self._truncate_content(content)

        return content, None

    async def extract_article(self, story: Story) -> Article:
        """Extract article content from a story.

        Handles all edge cases: no URL, blocked domain, network errors,
        empty content.

        Args:
            story: Story object from HN API.

        Returns:
            Article with extracted content or appropriate status.
        """
        # Create base article from story
        base_article: dict[str, Any] = {
            "story_id": story.id,
            "title": story.title,
            "url": story.url,
            "hn_url": story.hn_url,
            "hn_score": story.score,
            "hn_comments": story.descendants or 0,
            "author": story.by,
            "domain": self.extract_domain(story.url) if story.url else None,
            "hn_text": story.text,
        }

        # Handle stories without external URL (Ask HN, Jobs)
        if not story.url:
            logger.debug("Story %d has no external URL", story.id)
            return Article(
                **base_article,
                status=ExtractionStatus.NO_URL,
                content=None,
                word_count=len(story.text.split()) if story.text else 0,
            )

        # Check if URL should be skipped
        should_skip, reason = self.should_skip_url(story.url)
        if should_skip:
            logger.debug("Skipping story %d: %s", story.id, reason)
            return Article(
                **base_article,
                status=ExtractionStatus.SKIPPED,
                error_message=reason,
            )

        # Fetch and extract content
        logger.debug("Extracting content from %s", story.url)
        try:
            content, fetch_error = await self._fetch_content(story.url)
        except Exception as e:
            logger.warning("Failed to extract story %d: %s", story.id, e)
            return Article(
                **base_article,
                status=ExtractionStatus.FAILED,
                error_message=str(e),
            )

        # Handle fetch errors (network, HTTP errors)
        if fetch_error:
            logger.debug("Fetch error for story %d: %s", story.id, fetch_error)
            return Article(
                **base_article,
                status=ExtractionStatus.FAILED,
                error_message=fetch_error,
            )

        # Handle empty content (page loaded but no content extracted)
        if not content:
            logger.debug("No content extracted from story %d", story.id)
            return Article(
                **base_article,
                status=ExtractionStatus.EMPTY,
                error_message="No content could be extracted",
            )

        # Success
        word_count = len(content.split())
        logger.debug("Extracted %d words from story %d", word_count, story.id)
        return Article(
            **base_article,
            status=ExtractionStatus.SUCCESS,
            content=content,
            word_count=word_count,
        )

    async def extract_articles(self, stories: Sequence[Story]) -> list[Article]:
        """Extract articles from multiple stories in parallel.

        Args:
            stories: Sequence of Story objects to extract.

        Returns:
            List of Article objects in same order as input stories.
        """
        if not stories:
            return []

        logger.info("Extracting %d articles", len(stories))

        # Create extraction tasks
        tasks = [self.extract_article(story) for story in stories]

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        articles: list[Article] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                # Create failed article for exceptions
                story = stories[i]
                logger.warning("Exception extracting story %d: %s", story.id, result)
                articles.append(
                    Article(
                        story_id=story.id,
                        title=story.title,
                        url=story.url,
                        hn_url=story.hn_url,
                        hn_score=story.score,
                        hn_comments=story.descendants or 0,
                        author=story.by,
                        domain=self.extract_domain(story.url) if story.url else None,
                        hn_text=story.text,
                        status=ExtractionStatus.FAILED,
                        error_message=str(result),
                    )
                )
            else:
                articles.append(result)

        # Log summary
        success = sum(1 for a in articles if a.status == ExtractionStatus.SUCCESS)
        skipped = sum(1 for a in articles if a.status == ExtractionStatus.SKIPPED)
        failed = sum(1 for a in articles if a.status == ExtractionStatus.FAILED)
        no_url = sum(1 for a in articles if a.status == ExtractionStatus.NO_URL)
        empty = sum(1 for a in articles if a.status == ExtractionStatus.EMPTY)

        logger.info(
            "Extracted %d articles: %d success, %d skipped, %d failed, %d no_url, %d empty",
            len(articles),
            success,
            skipped,
            failed,
            no_url,
            empty,
        )

        return articles
