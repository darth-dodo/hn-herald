"""LLM service for article summarization.

Simple service using langchain-anthropic with structured output parsing.
Supports single article and batch summarization.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from langchain.output_parsers import PydanticOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from hn_herald.config import get_settings
from hn_herald.models.summary import (
    ArticleSummary,
    BatchArticleSummary,
    LLMAPIError,
    LLMRateLimitError,
    SummarizationStatus,
    SummarizedArticle,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hn_herald.models.article import Article

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are a technical content summarizer for HackerNews articles.

Given the article title and content below, generate a structured summary.

**Instructions**:
1. Write a concise 2-3 sentence summary capturing the main points
2. Extract exactly 3 key takeaways as bullet points
3. Identify relevant technology/topic tags (e.g., Python, AI, Security, DevOps)

**Article Title**: {title}

**Article Content**:
{content}

{format_instructions}"""

BATCH_PROMPT_TEMPLATE = """You are a technical content summarizer for HackerNews articles.

Summarize each of the following articles. For each article, provide:
1. A concise 2-3 sentence summary capturing the main points
2. Exactly 3 key takeaways as bullet points
3. Relevant technology/topic tags (e.g., Python, AI, Security, DevOps)

{articles_section}

{format_instructions}"""


class LLMService:
    """Service for summarizing articles using an LLM.

    Usage:
        service = LLMService()
        result = service.summarize_article(article)
        results = service.summarize_articles_batch(articles)
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> None:
        """Initialize LLM service with optional config overrides."""
        settings = get_settings()
        self._client = ChatAnthropic(
            model=model or settings.llm_model,
            temperature=temperature if temperature is not None else settings.llm_temperature,
            max_tokens=max_tokens or settings.llm_max_tokens,
            api_key=settings.anthropic_api_key,  # type: ignore[call-arg]
        )
        self._single_parser: PydanticOutputParser[ArticleSummary] = PydanticOutputParser(
            pydantic_object=ArticleSummary
        )
        self._batch_parser: PydanticOutputParser[BatchArticleSummary] = PydanticOutputParser(
            pydantic_object=BatchArticleSummary
        )

    def summarize_article(self, article: Article) -> SummarizedArticle:
        """Summarize a single article. Returns result with status."""
        content = article.content or article.hn_text
        if not content:
            return self._result(article, status=SummarizationStatus.NO_CONTENT)

        try:
            response = self._call_llm(self._build_prompt(content, article.title))
            summary = self._single_parser.parse(response)
            return self._result(article, summary=summary)
        except LLMRateLimitError as e:
            return self._result(article, status=SummarizationStatus.API_ERROR, error=str(e))
        except LLMAPIError as e:
            return self._result(article, status=SummarizationStatus.API_ERROR, error=str(e))
        except Exception as e:
            logger.exception("Parse error for article %d", article.story_id)
            return self._result(article, status=SummarizationStatus.PARSE_ERROR, error=str(e))

    def summarize_articles(self, articles: Sequence[Article]) -> list[SummarizedArticle]:
        """Summarize multiple articles sequentially. Preserves order."""
        return [self.summarize_article(a) for a in articles]

    def summarize_articles_batch(
        self,
        articles: Sequence[Article],
        batch_size: int | None = None,
    ) -> list[SummarizedArticle]:
        """Summarize multiple articles in batched LLM calls.

        More efficient than sequential calls for multiple articles.
        Falls back to NO_CONTENT for articles without content.

        Args:
            articles: Articles to summarize.
            batch_size: Max articles per LLM call (default from settings).

        Returns:
            List of results in same order as input articles.
        """
        if not articles:
            return []

        # Get batch size from settings if not provided
        if batch_size is None:
            batch_size = get_settings().summary_batch_size

        # Separate articles with and without content
        articles_with_content, results = self._prepare_batch(articles)

        if not articles_with_content:
            return [r for r in results if r is not None]

        # Process in chunks to avoid max_tokens limit
        total_batches = (len(articles_with_content) + batch_size - 1) // batch_size
        for batch_num, i in enumerate(range(0, len(articles_with_content), batch_size), 1):
            chunk = articles_with_content[i : i + batch_size]
            logger.info(
                "LLM batch %d/%d: Processing articles %d-%d of %d",
                batch_num,
                total_batches,
                i + 1,
                min(i + batch_size, len(articles_with_content)),
                len(articles_with_content),
            )
            self._process_batch(chunk, results)

        return [r for r in results if r is not None]

    def _prepare_batch(
        self, articles: Sequence[Article]
    ) -> tuple[list[tuple[int, Article]], list[SummarizedArticle | None]]:
        """Separate articles with content from those without."""
        articles_with_content: list[tuple[int, Article]] = []
        results: list[SummarizedArticle | None] = [None] * len(articles)

        for i, article in enumerate(articles):
            if article.content or article.hn_text:
                articles_with_content.append((i, article))
            else:
                results[i] = self._result(article, status=SummarizationStatus.NO_CONTENT)

        return articles_with_content, results

    def _process_batch(
        self,
        articles_with_content: list[tuple[int, Article]],
        results: list[SummarizedArticle | None],
    ) -> None:
        """Process batch API call and populate results."""
        try:
            batch_response = self._call_llm(
                self._build_batch_prompt([a for _, a in articles_with_content])
            )
            batch_summaries = self._batch_parser.parse(batch_response)
            self._map_batch_results(articles_with_content, batch_summaries.summaries, results)
        except (LLMRateLimitError, LLMAPIError) as e:
            self._fill_error_results(
                articles_with_content, results, SummarizationStatus.API_ERROR, str(e)
            )
        except Exception as e:
            logger.exception("Batch parse error")
            self._fill_error_results(
                articles_with_content, results, SummarizationStatus.PARSE_ERROR, str(e)
            )

    def _map_batch_results(
        self,
        articles_with_content: list[tuple[int, Article]],
        summaries: list[ArticleSummary],
        results: list[SummarizedArticle | None],
    ) -> None:
        """Map batch summaries back to original article positions."""
        for (orig_idx, article), summary in zip(articles_with_content, summaries, strict=False):
            results[orig_idx] = self._result(article, summary=summary)

        # Fill any missing results (if LLM returned fewer summaries)
        self._fill_error_results(
            [(i, a) for i, a in articles_with_content if results[i] is None],
            results,
            SummarizationStatus.PARSE_ERROR,
            "Missing summary in batch response",
        )

    def _fill_error_results(
        self,
        articles: list[tuple[int, Article]],
        results: list[SummarizedArticle | None],
        status: SummarizationStatus,
        error: str,
    ) -> None:
        """Fill results with error status for given articles."""
        for orig_idx, article in articles:
            if results[orig_idx] is None:
                results[orig_idx] = self._result(article, status=status, error=error)

    def _build_prompt(self, content: str, title: str) -> str:
        """Build prompt with format instructions."""
        return PROMPT_TEMPLATE.format(
            title=title,
            content=content,
            format_instructions=self._single_parser.get_format_instructions(),
        )

    def _build_batch_prompt(self, articles: list[Article]) -> str:
        """Build batch prompt for multiple articles."""
        articles_section = "\n\n".join(
            f"---\n**Article {i + 1}**\n**Title**: {a.title}\n**Content**:\n"
            f"{a.content or a.hn_text}\n---"
            for i, a in enumerate(articles)
        )
        return BATCH_PROMPT_TEMPLATE.format(
            articles_section=articles_section,
            format_instructions=self._batch_parser.get_format_instructions(),
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(LLMRateLimitError),
        reraise=True,
    )
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with retry on rate limits."""
        try:
            response = self._client.invoke([HumanMessage(content=prompt)])
            return str(response.content)
        except Exception as e:
            if self._is_rate_limit_error(e):
                raise LLMRateLimitError(str(e)) from e
            raise LLMAPIError(str(e), status_code=500) from e

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return ("rate" in error_str and "limit" in error_str) or "429" in str(error)

    @staticmethod
    def _result(
        article: Article,
        summary: ArticleSummary | None = None,
        status: SummarizationStatus = SummarizationStatus.SUCCESS,
        error: str | None = None,
    ) -> SummarizedArticle:
        """Factory method for creating results."""
        return SummarizedArticle(
            article=article,
            summary_data=summary,
            summarization_status=status,
            error_message=error,
        )
