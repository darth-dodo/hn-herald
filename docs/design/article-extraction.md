# Feature: Article Extraction (MVP-2)

## Overview

The Article Extraction service is responsible for fetching and processing article content from external URLs. This component takes Story objects from MVP-1 and extracts readable text content that can be used for AI summarization in MVP-3. It handles various webpage formats, manages problematic domains, and integrates with LangChain's document loading ecosystem.

**Business Value**: Enables users to get article content for summarization without manually visiting each link, saving time and providing a seamless reading experience.

**Target**: MVP-2 milestone - "Can read article content" with integration tests passing.

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Extract article content from story URLs | High |
| FR-2 | Handle stories without external URLs (Ask HN, jobs) | High |
| FR-3 | Skip problematic domains (Twitter, Reddit, YouTube, PDFs) | High |
| FR-4 | Truncate long articles to ~8K characters for LLM processing | Medium |
| FR-5 | Extract and preserve article metadata (title, word count) | Medium |
| FR-6 | Return typed Article objects using Pydantic models | High |
| FR-7 | Handle paywalled content gracefully (mark as unavailable) | Medium |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Async I/O using httpx | Required |
| NFR-2 | Request timeout handling | 15 seconds default |
| NFR-3 | Retry logic with exponential backoff | 3 attempts, 1-10s backoff |
| NFR-4 | Rate limiting respect | Max 10 concurrent requests |
| NFR-5 | Graceful error handling | Never crash on fetch errors |
| NFR-6 | Type safety with full type hints | Required |
| NFR-7 | Test coverage | >= 80% |

---

## Domain Handling

### Problematic Domains

These domains are skipped due to technical or content issues:

| Domain | Reason |
|--------|--------|
| `twitter.com`, `x.com` | Requires JavaScript, rate-limited |
| `reddit.com` | Heavy JavaScript, rate-limited |
| `youtube.com`, `youtu.be` | Video content, not extractable |
| `github.com` | Often code/binary, complex structure |
| `*.pdf` (file extension) | Binary format, requires special handling |
| `docs.google.com` | Authentication required |
| `medium.com` | Paywall detection issues |
| `bloomberg.com` | Heavy paywall |
| `wsj.com` | Heavy paywall |
| `nytimes.com` | Paywall |
| `linkedin.com` | Requires authentication |

### Paywall Detection

Indicators for paywalled content:
- HTTP 402 Payment Required
- Response body < 500 characters
- Contains "subscribe", "paywall", "premium" in specific contexts
- Meta tags indicating paywall (schema.org isAccessibleForFree: false)

---

## Architecture

### Component Diagram

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Story           |---->|  ArticleLoader   |---->|   Article        |
|  (from MVP-1)    |     |   (async)        |     |   (extracted)    |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                               |
                               v
                         +------------------+
                         |                  |
                         |  WebBaseLoader   |
                         |  (LangChain)     |
                         |                  |
                         +------------------+
                               |
                               v
                         +------------------+
                         |                  |
                         |  Text Splitter   |
                         |  (LangChain)     |
                         |                  |
                         +------------------+
```

### Components

#### Article Model (`src/hn_herald/models/article.py`)

Pydantic model representing extracted article content with metadata.

**Responsibilities**:
- Store extracted article content
- Track extraction status (success, skipped, failed)
- Preserve story metadata for display
- Provide content length validation

#### ArticleLoader (`src/hn_herald/services/loader.py`)

Async service for extracting article content from URLs.

**Responsibilities**:
- Fetch article content from URLs
- Detect and skip problematic domains
- Handle paywalled content
- Truncate content for LLM processing
- Batch extract with concurrency control

---

## Data Models

### ExtractionStatus Enum

```python
from enum import Enum

class ExtractionStatus(str, Enum):
    """Status of article extraction."""
    SUCCESS = "success"           # Content extracted successfully
    SKIPPED = "skipped"           # Domain or URL type not supported
    FAILED = "failed"             # Extraction failed (network, parsing)
    PAYWALLED = "paywalled"       # Content behind paywall
    NO_URL = "no_url"             # Story has no external URL (Ask HN)
    EMPTY = "empty"               # Page loaded but no content extracted
```

### Article Model

```python
from pydantic import BaseModel, Field, computed_field

class Article(BaseModel):
    """Extracted article content with metadata.

    Represents an article extracted from a Story URL, ready for
    AI summarization. Tracks extraction status and errors.
    """
    # Story reference (from MVP-1)
    story_id: int = Field(..., description="HN story ID")
    title: str = Field(..., description="Story title from HN")
    url: str | None = Field(None, description="Original article URL")
    hn_url: str = Field(..., description="HN discussion URL")
    hn_score: int = Field(..., ge=0, description="HN upvote score")
    hn_comments: int = Field(0, ge=0, description="HN comment count")
    author: str = Field(..., description="HN story author")

    # Extracted content
    content: str | None = Field(None, description="Extracted article text")
    word_count: int = Field(0, ge=0, description="Word count of content")

    # Extraction metadata
    status: ExtractionStatus = Field(
        ExtractionStatus.SUCCESS,
        description="Extraction status"
    )
    error_message: str | None = Field(None, description="Error details if failed")
    domain: str | None = Field(None, description="Extracted domain from URL")

    # For Ask HN / Job posts
    hn_text: str | None = Field(None, description="HN post text content")

    @computed_field
    @property
    def has_content(self) -> bool:
        """Check if article has extractable content."""
        return bool(self.content) or bool(self.hn_text)

    @computed_field
    @property
    def display_content(self) -> str | None:
        """Get content for display (article content or HN text)."""
        return self.content or self.hn_text

    model_config = {
        "frozen": False,
        "extra": "ignore",
    }
```

### ArticleLoaderError

```python
class ArticleLoaderError(Exception):
    """Base exception for article loader errors."""
    pass

class ArticleFetchError(ArticleLoaderError):
    """Error fetching article content."""
    def __init__(self, url: str, message: str):
        self.url = url
        super().__init__(f"Failed to fetch {url}: {message}")

class ArticleParseError(ArticleLoaderError):
    """Error parsing article content."""
    def __init__(self, url: str, message: str):
        self.url = url
        super().__init__(f"Failed to parse {url}: {message}")
```

---

## Implementation Plan

### File Structure

```
src/hn_herald/
├── models/
│   ├── __init__.py          # Export Article, ExtractionStatus
│   ├── story.py             # Story model (MVP-1)
│   └── article.py           # Article model + ExtractionStatus enum
│
└── services/
    ├── __init__.py          # Export ArticleLoader
    ├── hn_client.py         # HN API client (MVP-1)
    └── loader.py            # Article extraction service

tests/
├── conftest.py              # Shared fixtures
├── test_models/
│   ├── test_story.py        # Story model tests (MVP-1)
│   └── test_article.py      # Article model tests
└── test_services/
    ├── test_hn_client.py    # HN client tests (MVP-1)
    └── test_loader.py       # ArticleLoader tests
```

### Implementation Tasks

| Task | Estimate | Dependencies |
|------|----------|--------------|
| 1. Create `ExtractionStatus` enum | 10 min | None |
| 2. Create `Article` Pydantic model | 30 min | Task 1 |
| 3. Create exception classes | 10 min | None |
| 4. Implement `ArticleLoader` class structure | 30 min | Tasks 1-3 |
| 5. Implement domain detection/filtering | 30 min | Task 4 |
| 6. Implement `extract_article()` single | 45 min | Tasks 4-5 |
| 7. Implement `extract_articles()` batch | 30 min | Task 6 |
| 8. Implement content truncation | 20 min | Task 6 |
| 9. Write unit tests (Article model) | 30 min | Task 2 |
| 10. Write unit tests (ArticleLoader) | 60 min | Tasks 4-8 |
| 11. Write integration test | 30 min | Tasks 4-8 |

**Total Estimate**: ~5 hours

### ArticleLoader Interface

```python
from collections.abc import Sequence

class ArticleLoader:
    """Async service for extracting article content from URLs.

    Fetches and processes article content using LangChain's
    WebBaseLoader with retry logic and domain filtering.

    Usage:
        async with ArticleLoader() as loader:
            articles = await loader.extract_articles(stories)
    """

    # Domains that are skipped
    BLOCKED_DOMAINS: ClassVar[set[str]] = {
        "twitter.com", "x.com",
        "reddit.com", "old.reddit.com",
        "youtube.com", "youtu.be",
        "github.com",
        "docs.google.com",
        "medium.com",
        "bloomberg.com", "wsj.com", "nytimes.com",
        "linkedin.com",
    }

    # File extensions that are skipped
    BLOCKED_EXTENSIONS: ClassVar[set[str]] = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".tar", ".gz", ".rar",
        ".mp4", ".mp3", ".wav", ".avi", ".mov",
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    }

    def __init__(
        self,
        timeout: int = 15,
        max_retries: int = 3,
        max_concurrent: int = 10,
        max_content_length: int = 8000,
    ) -> None:
        """Initialize article loader.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            max_concurrent: Maximum concurrent requests
            max_content_length: Maximum content length in characters
        """
        ...

    async def __aenter__(self) -> "ArticleLoader":
        """Async context manager entry."""
        ...

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        ...

    def should_skip_url(self, url: str) -> tuple[bool, str]:
        """Check if URL should be skipped.

        Args:
            url: URL to check

        Returns:
            Tuple of (should_skip, reason)
        """
        ...

    def extract_domain(self, url: str) -> str | None:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string or None if invalid
        """
        ...

    async def extract_article(self, story: Story) -> Article:
        """Extract article content from a story.

        Handles all edge cases: no URL, blocked domain,
        paywall, extraction failure.

        Args:
            story: Story object from HN API

        Returns:
            Article with content or appropriate status
        """
        ...

    async def extract_articles(
        self,
        stories: Sequence[Story],
    ) -> list[Article]:
        """Extract articles from multiple stories in parallel.

        Args:
            stories: Sequence of Story objects

        Returns:
            List of Article objects (same order as input)
        """
        ...
```

---

## Content Extraction

### Using LangChain WebBaseLoader

```python
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

async def _fetch_content(self, url: str) -> str | None:
    """Fetch and extract content from URL."""
    # WebBaseLoader handles HTTP fetch + HTML parsing
    loader = WebBaseLoader(
        web_path=url,
        requests_per_second=1,  # Rate limiting
        header_template={
            "User-Agent": "HN-Herald/0.1 (https://github.com/darth-dodo/ai-adventures)",
        },
    )

    try:
        docs = loader.load()
    except Exception as e:
        logger.warning("Failed to load %s: %s", url, e)
        return None

    if not docs:
        return None

    # Combine all document content
    full_content = "\n\n".join(doc.page_content for doc in docs)

    # Apply text splitter for smart truncation
    if len(full_content) > self.max_content_length:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_content_length,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(full_content)
        return chunks[0] if chunks else None

    return full_content
```

### Alternative: Direct httpx + BeautifulSoup

For more control over the extraction process:

```python
from bs4 import BeautifulSoup

async def _fetch_content_direct(self, url: str) -> str | None:
    """Fetch content using httpx + BeautifulSoup."""
    try:
        response = await self._client.get(url, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("HTTP error fetching %s: %s", url, e)
        return None

    # Parse HTML
    soup = BeautifulSoup(response.text, "lxml")

    # Remove script, style, nav elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Try to find main content
    main = (
        soup.find("article") or
        soup.find("main") or
        soup.find(class_=["content", "post", "article", "entry"]) or
        soup.find("body")
    )

    if not main:
        return None

    # Extract and clean text
    text = main.get_text(separator="\n", strip=True)

    # Remove excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    content = "\n".join(lines)

    # Truncate if needed
    if len(content) > self.max_content_length:
        content = content[:self.max_content_length]
        # Find last complete sentence
        last_period = content.rfind(". ")
        if last_period > self.max_content_length // 2:
            content = content[:last_period + 1]

    return content if len(content) > 100 else None
```

### Recommended Approach

Use **direct httpx + BeautifulSoup** for MVP-2:
- More control over extraction
- Simpler async integration
- Easier to test and debug
- LangChain WebBaseLoader can be added later if needed

---

## Testing Strategy

### Unit Tests

Mock all HTTP requests using `respx`.

**Test Cases (Article Model)**:

| Test | Description | Priority |
|------|-------------|----------|
| `test_article_model_validation` | Valid article data creates model | High |
| `test_article_model_optional_fields` | Optional fields default correctly | High |
| `test_article_has_content_with_content` | has_content True when content exists | High |
| `test_article_has_content_with_hn_text` | has_content True when hn_text exists | High |
| `test_article_has_content_empty` | has_content False when no content | High |
| `test_article_display_content_prefers_content` | Prefers content over hn_text | Medium |
| `test_extraction_status_values` | All enum values defined | Medium |

**Test Cases (ArticleLoader)**:

| Test | Description | Priority |
|------|-------------|----------|
| `test_should_skip_twitter` | Skips twitter.com URLs | High |
| `test_should_skip_reddit` | Skips reddit.com URLs | High |
| `test_should_skip_youtube` | Skips youtube.com URLs | High |
| `test_should_skip_pdf` | Skips .pdf URLs | High |
| `test_should_not_skip_valid_url` | Does not skip valid article URLs | High |
| `test_extract_domain` | Correctly extracts domain from URL | High |
| `test_extract_article_success` | Extracts content successfully | High |
| `test_extract_article_no_url` | Returns NO_URL status for Ask HN | High |
| `test_extract_article_blocked_domain` | Returns SKIPPED for blocked domain | High |
| `test_extract_article_network_error` | Returns FAILED on network error | High |
| `test_extract_article_empty_content` | Returns EMPTY when no content | Medium |
| `test_extract_articles_parallel` | Extracts multiple articles in parallel | High |
| `test_extract_articles_preserves_order` | Output order matches input order | Medium |
| `test_content_truncation` | Long content is truncated properly | High |
| `test_client_context_manager` | Proper resource cleanup | Medium |

### Integration Tests

Mark with `@pytest.mark.integration` and `@pytest.mark.slow`.

**Test Cases**:

| Test | Description |
|------|-------------|
| `test_extract_real_article` | Extract content from a real public article |
| `test_blocked_domain_real` | Confirm blocked domain detection works |

### Test Fixtures

```python
# tests/conftest.py additions

@pytest.fixture
def sample_article_data() -> dict:
    """Sample Article data."""
    return {
        "story_id": 39856302,
        "title": "Test Article Title",
        "url": "https://example.com/article",
        "hn_url": "https://news.ycombinator.com/item?id=39856302",
        "hn_score": 142,
        "hn_comments": 85,
        "author": "testuser",
        "content": "This is the extracted article content...",
        "word_count": 150,
        "status": "success",
        "domain": "example.com",
    }

@pytest.fixture
def sample_story_with_url(sample_story_data) -> Story:
    """Story with external URL."""
    return Story(**sample_story_data)

@pytest.fixture
def sample_story_ask_hn() -> Story:
    """Ask HN story without external URL."""
    return Story(
        id=39856303,
        title="Ask HN: Best practices for async Python?",
        url=None,
        score=50,
        by="curious_dev",
        time=1709654321,
        descendants=25,
        type="story",
        text="<p>I'm looking for advice on...</p>",
    )

@pytest.fixture
def sample_html_content() -> str:
    """Sample HTML for content extraction."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Article</title></head>
    <body>
        <nav>Navigation here</nav>
        <article>
            <h1>Main Article Title</h1>
            <p>This is the first paragraph of the article.</p>
            <p>This is the second paragraph with more content.</p>
        </article>
        <footer>Footer content</footer>
    </body>
    </html>
    """
```

### Coverage Requirements

- Minimum 80% line coverage
- All public methods tested
- Error paths tested
- Edge cases tested (no URL, blocked domains, empty content)

---

## Error Handling

### Error Categories

| Error Type | Cause | Handling Strategy |
|------------|-------|-------------------|
| Network Timeout | Slow/unresponsive server | Retry with backoff, then mark FAILED |
| HTTP 4xx | Not found, forbidden | Log and mark FAILED |
| HTTP 5xx | Server error | Retry with backoff, then mark FAILED |
| Blocked Domain | Twitter, Reddit, etc. | Mark SKIPPED immediately |
| No URL | Ask HN, Jobs | Use HN text content, mark NO_URL |
| Parse Error | Malformed HTML | Mark FAILED with error message |
| Empty Content | No extractable text | Mark EMPTY |
| Paywall | Subscription required | Mark PAYWALLED |

### Graceful Degradation

1. **Extraction fails**: Mark article as FAILED, continue with others
2. **All extractions fail**: Return empty articles with error messages
3. **Blocked domain**: Mark as SKIPPED immediately (no retry)
4. **No URL (Ask HN)**: Use story.text as content source

---

## Dependencies

### External Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| httpx | >= 0.27.0 | Async HTTP client |
| beautifulsoup4 | >= 4.12.0 | HTML parsing |
| lxml | >= 5.0.0 | Fast HTML parser |
| pydantic | >= 2.0.0 | Data validation |
| tenacity | >= 8.2.0 | Retry logic |

### Internal Dependencies

| Module | Purpose |
|--------|---------|
| `hn_herald.config` | Access `article_fetch_timeout` and `max_content_length` settings |
| `hn_herald.models.story` | Story model from MVP-1 |

---

## Configuration

### Settings (config.py additions)

```python
# Article extraction settings
article_fetch_timeout: int = 15     # Seconds
max_content_length: int = 8000      # Characters
max_concurrent_extracts: int = 10   # Parallel extractions
```

### Environment Variables

```bash
# Article extraction
ARTICLE_FETCH_TIMEOUT=15
MAX_CONTENT_LENGTH=8000
MAX_CONCURRENT_EXTRACTS=10
```

---

## Security Considerations

1. **SSRF Prevention**: Only fetch from public URLs, no internal IPs
2. **Content Sanitization**: Extracted text is plain text, no HTML/JS execution
3. **Rate Limiting**: Respectful fetching (1 req/sec per domain)
4. **User-Agent**: Identify as HN Herald for transparency
5. **Redirect Following**: Follow redirects but limit to 5 hops

---

## Monitoring and Observability

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log levels by event
logger.info("Extracting %d articles", len(stories))
logger.debug("Fetching article from %s", url)
logger.warning("Skipped blocked domain: %s", domain)
logger.warning("Failed to extract %s: %s", url, error)
logger.info("Extracted %d articles (%d success, %d skipped, %d failed)", ...)
```

### Metrics (Future)

- Total articles extracted
- Extraction latency (p50, p95, p99)
- Success/skip/fail rates by domain
- Content length distribution

---

## Future Enhancements

1. **PDF Support**: Add PDF extraction using PyPDF2 or pdfplumber
2. **JavaScript Rendering**: Use Playwright for JS-heavy sites
3. **Caching**: Cache extracted content by URL hash
4. **Reader Mode**: Implement readability-style extraction
5. **Image Extraction**: Extract key images for article preview
6. **Paywall Detection**: More sophisticated paywall detection

---

## References

- [LangChain WebBaseLoader](https://python.langchain.com/docs/integrations/document_loaders/web_base/)
- [Beautiful Soup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [httpx Documentation](https://www.python-httpx.org/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [Tenacity Documentation](https://tenacity.readthedocs.io/)
