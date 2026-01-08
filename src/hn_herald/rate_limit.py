"""Rate limiting module for HN Herald API endpoints.

This module provides rate limiting decorators to protect upstream API quotas
(particularly the Anthropic API) from excessive usage. The implementation
follows a privacy-first design consistent with ADR-003:

Privacy-First Rate Limiting:
    - Global limits applied across all requests (not per-IP or per-user)
    - No request logging, tracking, or storage of client identifiers
    - In-memory state that resets on application restart
    - No analytics or usage metrics collected

The rate limiter uses a simple token bucket algorithm via the `ratelimit`
library, with automatic sleep-and-retry behavior to handle rate limit
exceeded scenarios gracefully.

Limitations:
    - In-memory storage: Limits reset on application restart
    - Single-instance: For horizontal scaling, use Redis-backed rate limiting

Typical usage:
    from hn_herald.rate_limit import rate_limit

    @router.post("/digest")
    @rate_limit
    async def generate_digest(...):
        ...

References:
    - Design Doc: docs/design/07-rate-limiting.md
    - Privacy Architecture: docs/adr/003-privacy-first-architecture.md
"""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import TYPE_CHECKING, Any, cast, overload

from ratelimit import RateLimitException, limits, sleep_and_retry

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# Rate limit configuration constants
# Exported for testing and configuration validation
CALLS: int = 30
"""Maximum number of calls allowed within the rate limit period."""

PERIOD: int = 60
"""Rate limit period in seconds."""


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded and cannot be retried.

    This exception wraps the underlying ratelimit library exception to provide
    a clean interface for error handling in FastAPI exception handlers.

    Attributes:
        message: Human-readable error message.
        retry_after: Suggested wait time in seconds before retrying.
    """

    def __init__(self, message: str, retry_after: int = PERIOD) -> None:
        """Initialize rate limit exceeded error.

        Args:
            message: Error message describing the rate limit violation.
            retry_after: Suggested seconds to wait before retrying.
        """
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)


def _create_sync_wrapper[**P, R](
    func: Callable[P, R],
) -> Callable[P, R]:
    """Create a rate-limited wrapper for synchronous functions.

    Args:
        func: The synchronous function to wrap.

    Returns:
        Rate-limited wrapper function.
    """

    @sleep_and_retry
    @limits(calls=CALLS, period=PERIOD)
    @wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return cast("Callable[P, R]", sync_wrapper)


def _create_async_wrapper[**P, R](
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    """Create a rate-limited wrapper for asynchronous functions.

    The ratelimit library's decorators are synchronous, so we apply them
    to a sync wrapper function and then await the actual async call.
    This ensures proper rate limiting while maintaining async behavior.

    Args:
        func: The asynchronous function to wrap.

    Returns:
        Rate-limited async wrapper function.
    """

    @wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Create a synchronous rate-limited function that we can call
        # The rate limiting happens in the sync layer, then we await the result

        @sleep_and_retry
        @limits(calls=CALLS, period=PERIOD)
        def rate_limited_call() -> Awaitable[R]:
            return func(*args, **kwargs)

        try:
            # Get the coroutine from the rate-limited sync wrapper
            coro = rate_limited_call()
            # Await the actual async function
            result: R = await coro
            return result
        except RateLimitException as e:
            logger.warning(
                "Rate limit exceeded for %s: %s",
                func.__name__,
                str(e),
                extra={
                    "event_type": "rate_limit_exceeded",
                    "function": func.__name__,
                    "calls_limit": CALLS,
                    "period_seconds": PERIOD,
                },
            )
            raise RateLimitExceededError(
                f"Rate limit exceeded: {CALLS} calls per {PERIOD} seconds",
                retry_after=PERIOD,
            ) from e

    return async_wrapper


@overload
def rate_limit[**P, R](func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]: ...


@overload
def rate_limit[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...


def rate_limit[**P, R](
    func: Callable[P, R] | Callable[P, Awaitable[Any]],
) -> Callable[P, R] | Callable[P, Awaitable[Any]]:
    """Rate limit decorator with sleep-and-retry behavior.

    Applies global rate limiting to protect upstream API quotas.
    Supports both synchronous and asynchronous functions.

    Privacy Note:
        This decorator implements global rate limiting without any
        per-client tracking. All requests share the same rate limit
        bucket, consistent with the privacy-first architecture.

    Configuration:
        - CALLS: Maximum requests allowed (default: 30)
        - PERIOD: Time window in seconds (default: 60)

    Behavior:
        When the rate limit is reached, the decorator will automatically
        sleep and retry (via sleep_and_retry) rather than immediately
        raising an exception. This provides graceful degradation under
        load.

    Args:
        func: The function to rate limit. Can be sync or async.

    Returns:
        Rate-limited wrapper that preserves the original function signature.

    Example:
        >>> @rate_limit
        ... async def generate_digest(profile: UserProfile) -> Digest:
        ...     # This endpoint is protected by rate limiting
        ...     return await pipeline.execute(profile)

        >>> @rate_limit
        ... def sync_operation() -> str:
        ...     return "result"
    """
    # Check if the function is a coroutine function
    if asyncio.iscoroutinefunction(func):
        return _create_async_wrapper(func)
    return _create_sync_wrapper(func)  # type: ignore[return-value]


__all__ = [
    "CALLS",
    "PERIOD",
    "RateLimitExceededError",
    "rate_limit",
]
