# Rate Limiting Design Document

**Date**: 2026-01-08
**Status**: Proposed

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
| `/`, `/health` | None | Static endpoints |

### Implementation

```python
# src/hn_herald/rate_limit.py
from functools import wraps
from ratelimit import sleep_and_retry, limits

CALLS = 30
PERIOD = 60  # seconds

def rate_limit(func):
    """Rate limit decorator with sleep-and-retry."""
    @sleep_and_retry
    @limits(calls=CALLS, period=PERIOD)
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper
```

```python
# src/hn_herald/api/routes.py
from hn_herald.rate_limit import rate_limit

@router.post("/digest")
@rate_limit
async def generate_digest(...):
    ...
```

### Privacy

- Global limits (not per-IP or per-user)
- No request logging or tracking
- Consistent with ADR-003

### Limitations

- In-memory storage (resets on restart)
- Single-instance only (use Redis for scale)

## References

- ADR-003: Privacy-First Architecture
