"""FastAPI routes for HN Herald digest generation.

This module defines the REST API endpoints for generating personalized
HackerNews digests via the LangGraph pipeline.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError

from hn_herald.api.mocks import generate_mock_digest_stream
from hn_herald.graph.graph import create_hn_graph
from hn_herald.models.digest import Digest
from hn_herald.models.profile import UserProfile  # noqa: TC001
from hn_herald.models.scoring import ScoredArticle  # noqa: TC001
from hn_herald.rate_limit import rate_limit

logger = logging.getLogger(__name__)

# Create router with versioned prefix
router = APIRouter(prefix="/api/v1", tags=["digest"])

# Stage mapping: node names to user-friendly SSE stage names and messages
_STAGE_MESSAGES: dict[str, tuple[str, str]] = {
    "fetch_hn": ("fetch", "Fetching HN stories..."),
    "fetch_article": ("extract", "Extracting article content..."),
    "filter": ("filter", "Filtering articles..."),
    "summarize": ("summarize", "Summarizing with AI..."),
    "score": ("score", "Scoring relevance..."),
    "rank": ("rank", "Ranking articles..."),
    "format": ("format", "Formatting digest..."),
}


# State keys mapped to node names (ordered by pipeline execution, reversed for detection)
_STATE_KEY_TO_NODE: list[tuple[str, str]] = [
    ("digest", "format"),
    ("ranked_articles", "rank"),
    ("scored_articles", "score"),
    ("summarized_articles", "summarize"),
    ("filtered_articles", "filter"),
    ("articles", "fetch_article"),
    ("stories", "fetch_hn"),
]


def _detect_current_node(state: dict[str, Any], prev_state: dict[str, Any] | None) -> str | None:
    """Detect which pipeline node just completed based on NEW state changes.

    Compares current state to previous state to find what's newly populated.
    This correctly identifies the stage that just completed rather than
    returning an earlier stage that still has data.
    """
    prev = prev_state or {}
    for key, node in _STATE_KEY_TO_NODE:
        current_value = state.get(key)
        prev_value = prev.get(key)
        # Check if this key is newly populated or changed
        if current_value and current_value != prev_value:
            return node
    return None


class GenerateDigestRequest(BaseModel):
    """Request body for digest generation endpoint.

    Attributes:
        profile: User preferences for personalization.
        mock: Whether to use mock data instead of real API calls.
    """

    profile: UserProfile = Field(
        ...,
        description="User preferences for article relevance scoring",
    )
    mock: bool = Field(
        default=False,
        description="Use mock data for development/testing",
    )


class DigestArticleResponse(BaseModel):
    """Simplified article representation for API response.

    Attributes:
        story_id: HN story ID.
        title: Article title.
        url: Article URL.
        hn_url: HN comments URL.
        hn_score: HN upvote score.
        summary: AI-generated summary.
        key_points: List of key takeaways.
        tech_tags: Technology/topic tags.
        relevance_score: User relevance score (0-1).
        relevance_reason: Explanation of relevance.
        final_score: Composite score (0-1).
    """

    story_id: int
    title: str
    url: str
    hn_url: str
    hn_score: int
    summary: str
    key_points: list[str]
    tech_tags: list[str]
    relevance_score: float
    relevance_reason: str
    final_score: float


class DigestStatsResponse(BaseModel):
    """Statistics about digest generation.

    Attributes:
        stories_fetched: Number of HN stories retrieved.
        articles_extracted: Number of articles successfully extracted.
        articles_summarized: Number of articles successfully summarized.
        articles_scored: Number of articles scored and ranked.
        articles_returned: Number of articles in final digest.
        errors: Number of errors during processing.
        generation_time_ms: Total processing time in milliseconds.
    """

    stories_fetched: int
    articles_extracted: int
    articles_summarized: int
    articles_scored: int
    articles_returned: int
    errors: int
    generation_time_ms: int


class GenerateDigestResponse(BaseModel):
    """Response for digest generation endpoint.

    Attributes:
        articles: Ranked list of articles.
        stats: Generation statistics.
        timestamp: When digest was generated.
        profile_summary: Summary of user profile used.
    """

    articles: list[DigestArticleResponse]
    stats: DigestStatsResponse
    timestamp: datetime
    profile_summary: dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error response format.

    Attributes:
        error: High-level error message.
        detail: Detailed error information.
    """

    error: str
    detail: str | None = None


def _scored_article_to_response(article: ScoredArticle) -> DigestArticleResponse | None:
    """Convert ScoredArticle to API response format.

    Args:
        article: Scored article from the pipeline.

    Returns:
        Simplified article for API response, or None if summary data is missing.
    """
    # Extract summary data - it should always be present for scored articles
    # but we handle the None case for type safety
    summary_data = article.article.summary_data
    if summary_data is None:
        logger.warning(
            f"Article {article.story_id} missing summary data, skipping",
            extra={
                "story_id": article.story_id,
                "title": article.title,
                "event_type": "missing_summary_data",
            },
        )
        return None

    return DigestArticleResponse(
        story_id=article.story_id,
        title=article.title,
        url=article.article.article.url or article.article.article.hn_url,
        hn_url=article.article.article.hn_url,
        hn_score=article.article.article.hn_score,
        summary=summary_data.summary,
        key_points=summary_data.key_points,
        tech_tags=summary_data.tech_tags,
        relevance_score=article.relevance_score,
        relevance_reason=article.relevance_reason,
        final_score=article.final_score,
    )


@router.post(
    "/digest",
    response_model=GenerateDigestResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Invalid request - validation error",
        },
        429: {
            "model": ErrorResponse,
            "description": "Too many requests - rate limit exceeded",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error - pipeline failure",
        },
        503: {
            "model": ErrorResponse,
            "description": "Service unavailable - external service error",
        },
    },
)
@rate_limit
async def generate_digest(request: GenerateDigestRequest) -> GenerateDigestResponse:
    """Generate personalized HN digest using LangGraph pipeline.

    Orchestrates the complete pipeline:
    1. Fetch HN stories based on user preferences
    2. Extract article content in parallel
    3. Filter valid articles
    4. Batch summarize with LLM
    5. Score articles by relevance
    6. Rank and format final digest

    Args:
        request: Digest generation request with user profile.

    Returns:
        Generated digest with ranked articles and statistics.

    Raises:
        HTTPException 400: Invalid user profile or request.
        HTTPException 500: Pipeline execution failed.
        HTTPException 503: External service unavailable.

    Note:
        This endpoint returns JSON by default. HTMX template rendering
        will be added when templates are implemented.
    """
    start_time = time.monotonic()
    logger.info(f"Generating digest for profile: {request.profile.model_dump()}")

    try:
        # Create and invoke LangGraph
        graph = create_hn_graph()

        # Prepare initial state
        initial_state: dict[str, Any] = {
            "profile": request.profile,
            "articles": [],
            "errors": [],
            "start_time": start_time,
        }

        logger.debug("Invoking LangGraph pipeline")
        final_state = await graph.ainvoke(initial_state)

        # Extract digest from final state
        digest_dict = final_state.get("digest")
        if not digest_dict:
            logger.error("Pipeline completed but no digest generated")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline completed but no digest was generated",
            )

        digest = Digest.model_validate(digest_dict)

        # Calculate generation time
        generation_time_ms = int((time.monotonic() - start_time) * 1000)

        # Build response - filter out articles with missing summary data
        article_responses = [
            resp
            for resp in (_scored_article_to_response(article) for article in digest.articles)
            if resp is not None
        ]
        response = GenerateDigestResponse(
            articles=article_responses,
            stats=DigestStatsResponse(
                stories_fetched=digest.stats.fetched,
                articles_extracted=len(final_state.get("articles", [])),
                articles_summarized=len(final_state.get("summarized_articles", [])),
                articles_scored=len(final_state.get("scored_articles", [])),
                articles_returned=digest.stats.final,
                errors=digest.stats.errors,
                generation_time_ms=generation_time_ms,
            ),
            timestamp=digest.timestamp,
            profile_summary={
                "interests": request.profile.interest_tags,
                "disinterests": request.profile.disinterest_tags,
                "min_score": request.profile.min_score,
                "max_articles": request.profile.max_articles,
            },
        )

        logger.info(
            "Digest generated successfully: %d articles in %dms",
            len(response.articles),
            generation_time_ms,
        )
        return response

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {e!s}",
        ) from e

    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        # Check if it's a service error
        if "HNClientError" in str(type(e).__name__) or "rate limit" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"External service error: {e!s}",
            ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Digest generation failed: {e!s}",
        ) from e


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Service is healthy",
        },
    },
)
async def health_check() -> dict[str, Any]:
    """Health check endpoint for monitoring and load balancers.

    Returns:
        Health status information.
    """
    from hn_herald import __version__
    from hn_herald.config import get_settings

    settings = get_settings()

    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.env,
    }


@router.post(
    "/digest/stream",
    responses={
        429: {
            "model": ErrorResponse,
            "description": "Too many requests - rate limit exceeded",
        },
    },
)
@rate_limit
async def generate_digest_stream(request: GenerateDigestRequest) -> StreamingResponse:
    """Generate digest with Server-Sent Events for real-time progress.

    Args:
        request: Digest generation request with user profile.

    Returns:
        SSE stream with pipeline progress updates.
    """
    # Use mock mode if requested
    if request.mock:
        logger.info("Using mock data for digest generation")
        return await generate_mock_digest_stream(request.profile)

    request_id = f"req_{int(time.time() * 1000)}"
    logger.info(
        f"[{request_id}] SSE digest request started",
        extra={
            "request_id": request_id,
            "profile": request.profile.model_dump(),
            "event_type": "sse_request_start",
        },
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for pipeline progress."""
        events_sent = 0
        stages_completed = []
        last_stage_sent: str | None = None

        try:
            start_time = time.monotonic()

            # Send initial event
            event = {"stage": "starting", "message": "Initializing pipeline..."}
            yield f"data: {json.dumps(event)}\n\n"
            events_sent += 1
            await asyncio.sleep(0.1)

            # Create LangGraph
            graph = create_hn_graph()

            initial_state: dict[str, Any] = {
                "profile": request.profile,
                "articles": [],
                "errors": [],
                "start_time": start_time,
            }

            # Use astream() with stream_mode="values" to get full accumulated state
            # This avoids the double-execution bug of astream_events() + ainvoke()
            final_state: dict[str, Any] | None = None
            prev_state: dict[str, Any] | None = None
            last_node: str | None = None

            async for chunk in graph.astream(initial_state, stream_mode="values"):
                # Detect which node just ran by comparing to previous state
                current_node = _detect_current_node(chunk, prev_state)
                if current_node and current_node != last_node:
                    if current_node in _STAGE_MESSAGES:
                        stage, message = _STAGE_MESSAGES[current_node]
                        if stage != last_stage_sent:
                            yield f"data: {json.dumps({'stage': stage, 'message': message})}\n\n"
                            events_sent += 1
                            stages_completed.append(stage)
                            last_stage_sent = stage
                    last_node = current_node

                prev_state = chunk
                final_state = chunk
                await asyncio.sleep(0.01)  # Prevent overwhelming the client

            # Extract digest from final state
            digest_dict = final_state.get("digest") if final_state else None

            if not digest_dict:
                err = {"stage": "error", "message": "Pipeline completed but no digest generated"}
                yield f"data: {json.dumps(err)}\n\n"
                return

            digest = Digest.model_validate(digest_dict)
            generation_time_ms = int((time.monotonic() - start_time) * 1000)

            # Build response - filter out articles with missing summary data
            article_responses = [
                resp
                for resp in (_scored_article_to_response(article) for article in digest.articles)
                if resp is not None
            ]

            logger.info(
                f"[{request_id}] SSE digest completed",
                extra={
                    "request_id": request_id,
                    "event_type": "sse_complete",
                    "articles_count": len(article_responses),
                    "generation_time_ms": generation_time_ms,
                    "stages_completed": stages_completed,
                    "events_sent": events_sent,
                },
            )

            # Get stats from final_state (which is the full accumulated state)
            fs = final_state or {}
            response = GenerateDigestResponse(
                articles=article_responses,
                stats=DigestStatsResponse(
                    stories_fetched=digest.stats.fetched,
                    articles_extracted=len(fs.get("articles", [])),
                    articles_summarized=len(fs.get("summarized_articles", [])),
                    articles_scored=len(fs.get("scored_articles", [])),
                    articles_returned=digest.stats.final,
                    errors=digest.stats.errors,
                    generation_time_ms=generation_time_ms,
                ),
                timestamp=digest.timestamp,
                profile_summary={
                    "interests": request.profile.interest_tags,
                    "disinterests": request.profile.disinterest_tags,
                    "min_score": request.profile.min_score,
                    "max_articles": request.profile.max_articles,
                },
            )

            # Send completion event with digest data
            complete_event = {
                "stage": "complete",
                "digest": response.model_dump(mode="json"),
            }
            yield f"data: {json.dumps(complete_event)}\n\n"

        except Exception as e:
            logger.exception(
                f"[{request_id}] SSE stream error",
                extra={
                    "request_id": request_id,
                    "event_type": "sse_error",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stages_completed": stages_completed,
                    "events_sent": events_sent,
                },
            )
            err_event = {"stage": "error", "message": f"{type(e).__name__}: {e!s}"}
            yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
