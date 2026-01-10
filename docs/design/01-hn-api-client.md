# Feature: HN API Client (MVP-1)

## Overview

The HN API Client is the foundational data layer for HN Herald, responsible for fetching story data from the Hacker News Firebase API. This component enables the application to retrieve top, new, best, ask, show, and job stories along with their metadata, serving as the primary data source for the digest generation pipeline.

**Business Value**: Enables users to access HN stories through a reliable, performant async interface that handles rate limiting and network failures gracefully.

**Target**: MVP-1 milestone - "Can fetch stories" with unit tests passing.

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Fetch story IDs for all story types (top, new, best, ask, show, job) | High |
| FR-2 | Fetch individual story details by ID | High |
| FR-3 | Batch fetch multiple stories in parallel | High |
| FR-4 | Support configurable fetch count (10-50 stories) | Medium |
| FR-5 | Filter stories by minimum score before returning | Medium |
| FR-6 | Return typed Story objects using Pydantic models | High |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Async I/O using httpx | Required |
| NFR-2 | Request timeout handling | 30 seconds default |
| NFR-3 | Retry logic with exponential backoff | 3 attempts, 1-10s backoff |
| NFR-4 | Rate limiting respect | Max 10 concurrent requests |
| NFR-5 | Graceful error handling | Never crash on network errors |
| NFR-6 | Type safety with full type hints | Required |
| NFR-7 | Test coverage | >= 80% |

---

## HN API Reference

### Base Configuration

| Property | Value |
|----------|-------|
| Base URL | `https://hacker-news.firebaseio.com/v0` |
| Format | JSON |
| Authentication | None required (public API) |
| Rate Limit | Undocumented, but be respectful |

### Endpoints

#### Story List Endpoints

All endpoints return an array of story IDs (integers), sorted by the respective ranking algorithm.

| Endpoint | Description | Max Items |
|----------|-------------|-----------|
| `/topstories.json` | Top stories (default HN front page) | 500 |
| `/newstories.json` | Newest stories | 500 |
| `/beststories.json` | Best stories (all-time weighted) | 500 |
| `/askstories.json` | Ask HN stories | 200 |
| `/showstories.json` | Show HN stories | 200 |
| `/jobstories.json` | Job postings | 200 |

**Example Response**:
```json
[39856302, 39856301, 39856300, ...]
```

#### Item Endpoint

| Endpoint | Description |
|----------|-------------|
| `/item/{id}.json` | Get story/comment/poll details |

**Example Request**:
```
GET https://hacker-news.firebaseio.com/v0/item/39856302.json
```

**Example Response** (Story):
```json
{
  "id": 39856302,
  "type": "story",
  "by": "username",
  "time": 1709654321,
  "title": "Example Story Title",
  "url": "https://example.com/article",
  "score": 142,
  "descendants": 85,
  "kids": [39856400, 39856401, ...]
}
```

**Field Definitions**:

| Field | Type | Description | Optional |
|-------|------|-------------|----------|
| `id` | int | Unique item ID | No |
| `type` | string | Item type (story, comment, poll, job) | No |
| `by` | string | Username of author | Yes (deleted items) |
| `time` | int | Unix timestamp of creation | No |
| `title` | string | Story title | No (for stories) |
| `url` | string | Story URL | Yes (Ask HN, jobs) |
| `text` | string | HTML content for Ask HN/jobs | Yes |
| `score` | int | Upvote score | No |
| `descendants` | int | Total comment count | Yes |
| `kids` | int[] | Child comment IDs | Yes |
| `dead` | bool | True if story is dead | Yes |
| `deleted` | bool | True if story is deleted | Yes |

---

## Architecture

### Component Diagram

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  LangGraph Node  |---->|   HNClient       |---->|   HN API         |
|  (fetcher.py)    |     |   (async)        |     |   (Firebase)     |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                               |
                               v
                         +------------------+
                         |                  |
                         |   Story Model    |
                         |   (Pydantic)     |
                         |                  |
                         +------------------+
```

### Components

#### Story Model (`src/hn_herald/models/story.py`)

Pydantic model representing an HN story with validation and computed properties.

**Responsibilities**:
- Validate story data from API response
- Compute derived fields (hn_url)
- Handle optional fields gracefully
- Provide type safety for downstream consumers

#### StoryType Enum

Enumeration of supported story types for type-safe API calls.

#### HNClient (`src/hn_herald/services/hn_client.py`)

Async HTTP client for HN API with retry logic and error handling.

**Responsibilities**:
- Fetch story IDs by type
- Fetch individual story details
- Batch fetch with concurrency control
- Handle network errors and timeouts
- Implement retry with exponential backoff

---

## Data Models

### StoryType Enum

```python
from enum import Enum

class StoryType(str, Enum):
    """Supported HN story types."""
    TOP = "top"
    NEW = "new"
    BEST = "best"
    ASK = "ask"
    SHOW = "show"
    JOB = "job"

    @property
    def endpoint(self) -> str:
        """Get the API endpoint for this story type."""
        return f"/{self.value}stories.json"
```

### Story Model

```python
from pydantic import BaseModel, Field, computed_field

class Story(BaseModel):
    """HackerNews story data model.

    Represents a story fetched from the HN API with all metadata
    needed for digest generation.
    """
    model_config = {
        "frozen": False,
        "extra": "ignore",  # Ignore unknown fields from API
        "str_strip_whitespace": True,
    }

    id: int = Field(..., description="Unique story ID from HackerNews")
    title: str = Field(..., description="Story title")
    url: str | None = Field(default=None, description="External article URL")
    score: int = Field(..., ge=0, description="HN upvote score")
    by: str = Field(..., description="Author username")
    time: int = Field(..., description="Unix timestamp of creation")
    descendants: int | None = Field(default=None, ge=0, description="Total comment count")
    type: str = Field(default="story", description="Item type from HN API")
    kids: list[int] = Field(default_factory=list, description="Child comment IDs")
    text: str | None = Field(default=None, description="HTML content for Ask HN/jobs")
    dead: bool | None = Field(default=None, description="True if story is dead/killed")
    deleted: bool | None = Field(default=None, description="True if story is deleted")

    @computed_field
    @property
    def hn_url(self) -> str:
        """Generate HN discussion URL."""
        return f"https://news.ycombinator.com/item?id={self.id}"

    @computed_field
    @property
    def has_external_url(self) -> bool:
        """Check if story has an external URL."""
        return bool(self.url)
```

### HNClientError

```python
class HNClientError(Exception):
    """Base exception for HN client errors."""
    pass

class HNAPIError(HNClientError):
    """Error from HN API (non-2xx response)."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HN API error {status_code}: {message}")

class HNTimeoutError(HNClientError):
    """Request timeout error."""
    pass
```

---

## Implementation Plan

### File Structure

```
src/hn_herald/
├── models/
│   ├── __init__.py          # Export Story, StoryType
│   └── story.py              # Story model + StoryType enum
│
└── services/
    ├── __init__.py          # Export HNClient
    └── hn_client.py         # Async HN API client

tests/
├── conftest.py              # Shared fixtures
└── test_services/
    ├── __init__.py
    └── test_hn_client.py    # Unit + integration tests
```

### Implementation Tasks

| Task | Estimate | Dependencies |
|------|----------|--------------|
| 1. Create `StoryType` enum | 15 min | None |
| 2. Create `Story` Pydantic model | 30 min | Task 1 |
| 3. Create exception classes | 15 min | None |
| 4. Implement `HNClient` class structure | 30 min | Tasks 1-3 |
| 5. Implement `fetch_story_ids()` | 30 min | Task 4 |
| 6. Implement `fetch_story()` | 30 min | Task 4 |
| 7. Implement `fetch_stories()` batch | 45 min | Tasks 5-6 |
| 8. Implement retry logic | 30 min | Task 4 |
| 9. Write unit tests | 60 min | Tasks 1-8 |
| 10. Write integration test | 30 min | Tasks 1-8 |

**Total Estimate**: ~5 hours

### HNClient Interface

```python
class HNClient:
    """Async client for HackerNews API.

    Provides methods to fetch stories from HN with automatic
    retry logic, timeout handling, and rate limiting.

    Usage:
        async with HNClient() as client:
            stories = await client.fetch_stories(StoryType.TOP, limit=30)
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
        ...

    async def __aenter__(self) -> "HNClient":
        """Async context manager entry."""
        ...

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        ...

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
        ...

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
        ...

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
        ...
```

---

## Testing Strategy

### Unit Tests

Mock all HTTP requests using `respx` or `pytest-httpx`.

**Test Cases**:

| Test | Description | Priority |
|------|-------------|----------|
| `test_story_model_validation` | Valid story data creates model | High |
| `test_story_model_optional_fields` | Optional fields default correctly | High |
| `test_story_hn_url_computed` | hn_url property computed correctly | Medium |
| `test_story_type_endpoint` | StoryType.endpoint returns correct path | High |
| `test_fetch_story_ids_success` | Returns list of IDs | High |
| `test_fetch_story_ids_limit` | Respects limit parameter | High |
| `test_fetch_story_success` | Returns Story object | High |
| `test_fetch_story_deleted` | Returns None for deleted story | Medium |
| `test_fetch_stories_parallel` | Fetches multiple stories | High |
| `test_fetch_stories_min_score` | Filters by minimum score | High |
| `test_timeout_raises_error` | HNTimeoutError on timeout | High |
| `test_api_error_raises` | HNAPIError on non-2xx | High |
| `test_retry_on_transient_error` | Retries on 5xx errors | High |
| `test_client_context_manager` | Proper resource cleanup | Medium |

### Integration Tests

Mark with `@pytest.mark.integration` and `@pytest.mark.slow`.

**Test Cases**:

| Test | Description |
|------|-------------|
| `test_fetch_real_top_stories` | Fetch actual top stories from HN API |
| `test_fetch_real_story_details` | Fetch actual story by ID |

### Test Fixtures

```python
# tests/conftest.py additions

@pytest.fixture
def sample_story_data() -> dict:
    """Sample HN story API response."""
    return {
        "id": 39856302,
        "type": "story",
        "by": "testuser",
        "time": 1709654321,
        "title": "Test Story Title",
        "url": "https://example.com/article",
        "score": 142,
        "descendants": 85,
        "kids": [39856400, 39856401],
    }

@pytest.fixture
def sample_story_ids() -> list[int]:
    """Sample story ID list."""
    return [39856302, 39856301, 39856300, 39856299, 39856298]

@pytest.fixture
def mock_hn_client(respx_mock, sample_story_data, sample_story_ids):
    """HN client with mocked responses."""
    base_url = "https://hacker-news.firebaseio.com/v0"

    # Mock story list endpoints
    for story_type in ["top", "new", "best", "ask", "show", "job"]:
        respx_mock.get(f"{base_url}/{story_type}stories.json").respond(
            json=sample_story_ids
        )

    # Mock individual story endpoint
    respx_mock.get(f"{base_url}/item/39856302.json").respond(
        json=sample_story_data
    )

    return HNClient(base_url=base_url)
```

### Coverage Requirements

- Minimum 80% line coverage
- All public methods tested
- Error paths tested
- Edge cases tested (empty lists, missing fields)

---

## Error Handling

### Error Categories

| Error Type | Cause | Handling Strategy |
|------------|-------|-------------------|
| Network Timeout | Slow/unresponsive API | Retry with backoff, then raise `HNTimeoutError` |
| HTTP 4xx | Bad request/not found | Log and skip item, continue processing |
| HTTP 5xx | Server error | Retry with backoff, then raise `HNAPIError` |
| Invalid JSON | Malformed response | Skip item, log warning |
| Missing Fields | Incomplete data | Use Pydantic defaults, skip if required field missing |
| Rate Limiting | Too many requests | Exponential backoff, respect Retry-After header |

### Retry Strategy

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.TransientError, httpx.TimeoutException)),
)
async def _request_with_retry(self, url: str) -> httpx.Response:
    """Make HTTP request with retry logic."""
    ...
```

### Graceful Degradation

1. **Individual story fails**: Skip story, log warning, continue with others
2. **Story list fails**: Raise error to caller (cannot proceed without IDs)
3. **All stories fail**: Return empty list with logged errors

---

## Dependencies

### External Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| httpx | >= 0.26.0 | Async HTTP client |
| pydantic | >= 2.0.0 | Data validation |
| tenacity | >= 8.0.0 | Retry logic |

### Internal Dependencies

| Module | Purpose |
|--------|---------|
| `hn_herald.config` | Access `hn_api_base_url` and `hn_api_timeout` settings |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| HN API changes/deprecation | Low | High | Abstract API details, monitor for changes |
| Rate limiting | Medium | Medium | Implement respectful rate limiting, backoff |
| Slow API responses | Medium | Low | Async with timeouts, parallel fetching |
| Story data inconsistency | Low | Low | Pydantic validation, ignore unknown fields |
| Network instability | Medium | Medium | Retry logic with exponential backoff |

---

## Security Considerations

1. **No authentication required**: HN API is public, no credentials stored
2. **Input validation**: All API responses validated through Pydantic
3. **URL handling**: Story URLs are not fetched by this component (handled by loader service)
4. **Rate limiting**: Respectful API usage to avoid IP blocking

---

## Monitoring and Observability

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels by event
logger.info("Fetching %d story IDs for type %s", limit, story_type)
logger.warning("Story %d not found or deleted", story_id)
logger.error("HN API error: %s", error)
logger.debug("Fetched story %d: %s", story.id, story.title)
```

### Metrics (Future)

- Total stories fetched
- Fetch latency (p50, p95, p99)
- Error rate by type
- Retry count

---

## Future Enhancements

1. **Caching**: Cache story IDs and details to reduce API calls
2. **Comment fetching**: Add methods to fetch story comments
3. **User profiles**: Fetch user information for stories
4. **Algolia integration**: Use Algolia HN Search API for advanced queries
5. **WebSocket updates**: Real-time story updates via Firebase

---

## References

- [HN API Documentation](https://github.com/HackerNews/API)
- [Firebase REST API](https://firebase.google.com/docs/database/rest/start)
- [httpx Documentation](https://www.python-httpx.org/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [Tenacity Documentation](https://tenacity.readthedocs.io/)
