"""Async client for HackerNews API.

This module provides an async HTTP client for fetching stories from the
HN Firebase API with retry logic, timeout handling, and rate limiting.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from hn_herald.config import get_settings
from hn_herald.models.story import Story, StoryType

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class HNClientError(Exception):
    """Base exception for HN client errors."""


class HNTimeoutError(HNClientError):
    """Request timeout error."""


class HNAPIError(HNClientError):
    """Error from HN API (non-2xx response).

    Attributes:
        status_code: The HTTP status code from the API response.
    """

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize HNAPIError.

        Args:
            status_code: HTTP status code from the API.
            message: Error message describing the failure.
        """
        self.status_code = status_code
        super().__init__(f"HN API error {status_code}: {message}")


class HNClient:
    """Async client for HackerNews API.

    Provides methods to fetch stories from HN with automatic
    retry logic, timeout handling, and rate limiting.

    Usage:
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=30)

    Attributes:
        base_url: The HN API base URL.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.
        max_concurrent: Maximum concurrent requests for batch operations.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
        max_retries: int = 3,
        max_concurrent: int = 10,
    ) -> None:
        """Initialize HN client.

        Args:
            base_url: HN API base URL. Defaults to settings value.
            timeout: Request timeout in seconds. Defaults to settings value.
            max_retries: Maximum retry attempts for transient failures.
            max_concurrent: Maximum concurrent requests for batch operations.
        """
        settings = get_settings()
        self.base_url = base_url or settings.hn_api_base_url
        self.timeout = timeout or settings.hn_api_timeout
        self.max_retries = max_retries
        self.max_concurrent = max_concurrent
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> HNClient:
        """Async context manager entry.

        Creates the HTTP client and semaphore for rate limiting.

        Returns:
            The HNClient instance.
        """
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={"Accept": "application/json"},
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
            RuntimeError: If client is used outside context manager.
        """
        if self._client is None:
            msg = "HNClient must be used as an async context manager"
            raise RuntimeError(msg)
        return self._client

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get the semaphore for rate limiting.

        Returns:
            The asyncio.Semaphore instance.

        Raises:
            RuntimeError: If client is used outside context manager.
        """
        if self._semaphore is None:
            msg = "HNClient must be used as an async context manager"
            raise RuntimeError(msg)
        return self._semaphore

    async def _request_with_retry(self, url: str) -> httpx.Response:
        """Make HTTP request with retry logic.

        Uses tenacity for exponential backoff on transient errors.

        Args:
            url: The URL path to request (relative to base_url).

        Returns:
            The httpx.Response object.

        Raises:
            HNTimeoutError: If the request times out after all retries.
            HNAPIError: If the API returns a non-2xx status code.
        """

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
            reraise=True,
        )
        async def _do_request() -> httpx.Response:
            client = self._get_client()
            semaphore = self._get_semaphore()

            async with semaphore:
                response = await client.get(url)
                response.raise_for_status()
                return response

        try:
            return await _do_request()
        except httpx.TimeoutException as e:
            logger.error("Request timeout for %s: %s", url, e)
            raise HNTimeoutError(f"Request timed out: {url}") from e
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error for %s: %s", url, e)
            raise HNAPIError(e.response.status_code, str(e)) from e

    async def fetch_story_ids(
        self,
        story_type: StoryType,
        limit: int = 30,
    ) -> list[int]:
        """Fetch story IDs for a given story type.

        Args:
            story_type: Type of stories to fetch (TOP, NEW, BEST, etc.).
            limit: Maximum number of IDs to return.

        Returns:
            List of story IDs sorted by HN ranking.

        Raises:
            HNTimeoutError: If the request times out.
            HNAPIError: If the API returns a non-2xx status code.
        """
        logger.info("Fetching %d story IDs for type %s", limit, story_type.value)

        response = await self._request_with_retry(story_type.endpoint)
        story_ids: list[int] = response.json()

        # Apply limit
        if limit > 0:
            story_ids = story_ids[:limit]

        logger.debug("Fetched %d story IDs", len(story_ids))
        return story_ids

    async def fetch_story(self, story_id: int) -> Story | None:
        """Fetch a single story by ID.

        Args:
            story_id: HN story ID.

        Returns:
            Story object or None if story is dead/deleted or not found.

        Raises:
            HNTimeoutError: If the request times out.
            HNAPIError: If the API returns a non-2xx status code.
        """
        logger.debug("Fetching story %d", story_id)

        url = f"/item/{story_id}.json"

        try:
            response = await self._request_with_retry(url)
        except HNAPIError as e:
            if e.status_code == 404:  # noqa: PLR2004
                logger.warning("Story %d not found", story_id)
                return None
            raise

        data = response.json()

        # Handle null response (deleted items)
        if data is None:
            logger.warning("Story %d returned null (likely deleted)", story_id)
            return None

        # Skip dead or deleted stories
        if data.get("dead", False) or data.get("deleted", False):
            logger.warning("Story %d is dead or deleted", story_id)
            return None

        # Skip non-story items (comments, polls)
        if data.get("type") not in ("story", "job"):
            logger.warning("Item %d is not a story (type: %s)", story_id, data.get("type"))
            return None

        try:
            story = Story.model_validate(data)
            logger.debug("Fetched story %d: %s", story.id, story.title)
            return story
        except Exception:
            logger.exception("Failed to parse story %d", story_id)
            return None

    async def fetch_stories(
        self,
        story_type: StoryType,
        limit: int = 30,
        min_score: int = 0,
    ) -> list[Story]:
        """Fetch multiple stories with parallel requests.

        Fetches story IDs first, then fetches each story in parallel
        with rate limiting. Filters by minimum score and sorts by score
        descending.

        Args:
            story_type: Type of stories to fetch (TOP, NEW, BEST, etc.).
            limit: Maximum stories to return after filtering.
            min_score: Minimum HN score filter.

        Returns:
            List of Story objects filtered by min_score and sorted by score descending.

        Raises:
            HNTimeoutError: If requests time out.
            HNAPIError: If the API returns a non-2xx status code.
        """
        logger.info(
            "Fetching stories: type=%s, limit=%d, min_score=%d",
            story_type.value,
            limit,
            min_score,
        )

        # Fetch more IDs than needed to account for filtering
        fetch_limit = min(limit * 2, 100) if min_score > 0 else limit

        # Fetch story IDs
        story_ids = await self.fetch_story_ids(story_type, limit=fetch_limit)

        if not story_ids:
            logger.warning("No story IDs found for type %s", story_type.value)
            return []

        # Fetch stories in parallel
        tasks = [self.fetch_story(story_id) for story_id in story_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter valid stories
        stories: list[Story] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("Failed to fetch story: %s", result)
                continue
            if result is not None and result.score >= min_score:
                stories.append(result)

        # Sort by score descending
        stories.sort(key=lambda s: s.score, reverse=True)

        # Apply final limit
        stories = stories[:limit]

        logger.info(
            "Fetched %d stories (filtered from %d IDs)",
            len(stories),
            len(story_ids),
        )

        return stories
