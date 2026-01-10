# Rate Limiting Design Document

**Date**: 2026-01-08
**Status**: Implemented

---

## Overview

Rate limiting for HN Herald to protect upstream Anthropic API quotas while maintaining privacy-first design.

## Problem

- No rate limiting on `/api/v1/digest` endpoint
- Each digest makes multiple LLM calls (~6 batches)
- Risk of cost explosion and API quota exhaustion

## Solution

### Library

`ratelimit>=2.2.1` - Simple decorator-based rate limiting

### Configuration

| Endpoint | Limit | Rationale |
|----------|-------|-----------|
| `/api/v1/digest` | 30/min | Protects LLM API quota |
| `/api/v1/digest/stream` | 30/min | SSE endpoint, same protection |
| `/`, `/health` | None | Static endpoints |

### Implementation

```python
# src/hn_herald/rate_limit.py
from ratelimit import RateLimitException, limits, sleep_and_retry

CALLS: int = 30
PERIOD: int = 60  # seconds

class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int = PERIOD) -> None:
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

def rate_limit(func):
    """Rate limit decorator with sleep-and-retry.

    Supports both sync and async functions. When rate limit is exceeded,
    raises RateLimitExceededError with retry_after information.
    """
    # Implementation handles sync/async detection and wrapping
    ...
```

```python
# src/hn_herald/api/routes.py
from hn_herald.rate_limit import rate_limit

@router.post("/digest")
@rate_limit
async def generate_digest(...):
    ...

@router.post("/digest/stream")
@rate_limit
async def generate_digest_stream(...):
    ...
```

### Error Response

When rate limit is exceeded, the API returns HTTP 429 with:

```json
{
  "error": "Rate limit exceeded",
  "detail": "Rate limit exceeded: 30 calls per 60 seconds"
}
```

The `RateLimitExceededError` includes a `retry_after` field (defaults to 60 seconds) for client retry logic.

### Privacy

- Global limits (not per-IP or per-user)
- No request logging or tracking
- Consistent with ADR-003

### Limitations

- In-memory storage (resets on restart)
- Single-instance only (use Redis for scale)

## References

- ADR-003: Privacy-First Architecture
