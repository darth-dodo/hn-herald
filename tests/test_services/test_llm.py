"""Tests for LLMService client construction."""

from unittest.mock import patch

import pytest

from hn_herald.config import Settings, get_settings
from hn_herald.services.llm import LLMService

# Sampling parameters rejected by the Anthropic API (version 2026-10-21 onwards).
UNSUPPORTED_SAMPLING_PARAMS = ("temperature", "top_p", "top_k")


@pytest.fixture(autouse=True)
def _fresh_settings():
    """Clear cached settings so each test reads the current environment."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestLLMServiceClient:
    """Tests for the ChatAnthropic client configuration."""

    def test_does_not_pass_sampling_params(self):
        """Client is built without temperature, top_p or top_k."""
        with patch("hn_herald.services.llm.ChatAnthropic") as mock_chat:
            LLMService()

        kwargs = mock_chat.call_args.kwargs
        for param in UNSUPPORTED_SAMPLING_PARAMS:
            assert param not in kwargs

    def test_uses_configured_model_and_max_tokens(self):
        """Client receives model and max_tokens from settings."""
        settings = get_settings()
        with patch("hn_herald.services.llm.ChatAnthropic") as mock_chat:
            LLMService()

        kwargs = mock_chat.call_args.kwargs
        assert kwargs["model"] == settings.llm_model
        assert kwargs["max_tokens"] == settings.llm_max_tokens

    def test_overrides_model_and_max_tokens(self):
        """Explicit constructor arguments override settings."""
        with patch("hn_herald.services.llm.ChatAnthropic") as mock_chat:
            LLMService(model="claude-sonnet-4-6", max_tokens=1024)

        kwargs = mock_chat.call_args.kwargs
        assert kwargs["model"] == "claude-sonnet-4-6"
        assert kwargs["max_tokens"] == 1024


class TestLLMSettings:
    """Tests for LLM-related settings."""

    def test_no_temperature_setting(self):
        """Settings no longer expose a temperature knob."""
        assert "llm_temperature" not in Settings.model_fields
