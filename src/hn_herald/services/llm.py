"""LLM service for article summarization.

Simple service using langchain-anthropic with structured output parsing.
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


class LLMService:
    """Service for summarizing articles using an LLM.

    Usage:
        service = LLMService()
        result = service.summarize_article(article)
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
        self._parser: PydanticOutputParser[ArticleSummary] = PydanticOutputParser(
            pydantic_object=ArticleSummary
        )

    def summarize_article(self, article: Article) -> SummarizedArticle:
        """Summarize a single article. Returns result with status."""
        content = article.content or article.hn_text
        if not content:
            return self._result(article, status=SummarizationStatus.NO_CONTENT)

        try:
            response = self._call_llm(self._build_prompt(content, article.title))
            summary = self._parser.parse(response)
            return self._result(article, summary=summary)
        except LLMRateLimitError as e:
            return self._result(article, status=SummarizationStatus.API_ERROR, error=str(e))
        except LLMAPIError as e:
            return self._result(article, status=SummarizationStatus.API_ERROR, error=str(e))
        except Exception as e:
            logger.exception("Parse error for article %d", article.story_id)
            return self._result(article, status=SummarizationStatus.PARSE_ERROR, error=str(e))

    def summarize_articles(self, articles: Sequence[Article]) -> list[SummarizedArticle]:
        """Summarize multiple articles. Preserves order, handles failures gracefully."""
        return [self.summarize_article(a) for a in articles]

    def _build_prompt(self, content: str, title: str) -> str:
        """Build prompt with format instructions."""
        return PROMPT_TEMPLATE.format(
            title=title,
            content=content,
            format_instructions=self._parser.get_format_instructions(),
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
