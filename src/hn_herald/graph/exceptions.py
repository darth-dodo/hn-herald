"""Custom exceptions for LangGraph pipeline."""

from __future__ import annotations


class GraphExecutionError(Exception):
    """Base exception for graph execution failures.

    Raised when the digest generation pipeline encounters critical errors
    that prevent successful completion.

    Attributes:
        message: Human-readable error message.
        original_exception: The underlying exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
    ) -> None:
        """Initialize GraphExecutionError.

        Args:
            message: Human-readable error message.
            original_exception: The underlying exception (optional).
        """
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        """String representation of the error."""
        if self.original_exception:
            return f"{self.message} (caused by: {self.original_exception!r})"
        return self.message


class HNAPIError(GraphExecutionError):
    """Exception raised when HackerNews API is unavailable."""


class LLMServiceError(GraphExecutionError):
    """Exception raised when LLM service fails."""


class ArticleExtractionError(Exception):
    """Non-fatal exception for individual article extraction failures.

    This exception is caught and logged but doesn't stop pipeline execution,
    enabling partial failure tolerance.
    """
