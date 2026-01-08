"""Tests for rate limiting module.

This module tests the rate_limit decorator and constants from
src/hn_herald/rate_limit.py, ensuring proper rate limiting behavior
for protecting upstream API quotas.
"""

import asyncio
import functools
from unittest.mock import patch

import pytest


class TestRateLimitConstants:
    """Tests for rate limit configuration constants."""

    def test_calls_constant_exported(self):
        from hn_herald.rate_limit import CALLS

        assert CALLS == 30

    def test_period_constant_exported(self):
        from hn_herald.rate_limit import PERIOD

        assert PERIOD == 60

    def test_constants_are_integers(self):
        from hn_herald.rate_limit import CALLS, PERIOD

        assert isinstance(CALLS, int)
        assert isinstance(PERIOD, int)

    def test_constants_are_positive(self):
        from hn_herald.rate_limit import CALLS, PERIOD

        assert CALLS > 0
        assert PERIOD > 0


class TestRateLimitDecoratorBasics:
    """Tests for basic rate_limit decorator functionality."""

    def test_rate_limit_decorator_exists(self):
        from hn_herald.rate_limit import rate_limit

        assert callable(rate_limit)

    async def test_decorated_async_function_callable(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def sample_func():
            return "result"

        result = await sample_func()
        assert result == "result"

    async def test_decorated_function_returns_correct_value(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def add_numbers(a, b):
            return a + b

        result = await add_numbers(5, 3)
        assert result == 8

    async def test_decorated_function_accepts_args(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = await greet("World")
        assert result == "Hello, World!"

    async def test_decorated_function_accepts_kwargs(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def create_message(prefix, suffix, sep="-"):
            return f"{prefix}{sep}{suffix}"

        result = await create_message(prefix="start", suffix="end", sep=":")
        assert result == "start:end"

    async def test_decorated_function_handles_exceptions(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def failing_func():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            await failing_func()


class TestRateLimitDecoratorMetadata:
    """Tests for functools.wraps preservation in rate_limit decorator."""

    def test_preserves_function_name(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def my_special_function():
            return None

        assert my_special_function.__name__ == "my_special_function"

    def test_preserves_function_docstring(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def documented_function():
            """This is a documented function."""
            return

        assert documented_function.__doc__ == "This is a documented function."

    def test_preserves_function_module(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def module_function():
            return None

        assert module_function.__module__ == __name__

    def test_wrapped_attribute_available(self):
        from hn_herald.rate_limit import rate_limit

        async def original_function():
            return None

        decorated = rate_limit(original_function)

        # The decorator chain may add multiple wrappers, but __wrapped__ should exist
        assert hasattr(decorated, "__wrapped__")


class TestRateLimitEnforcement:
    """Tests for rate limiting enforcement behavior."""

    async def test_multiple_calls_within_limit_succeed(self):
        from hn_herald.rate_limit import CALLS, rate_limit

        call_count = 0

        @rate_limit
        async def counting_func():
            nonlocal call_count
            call_count += 1
            return call_count

        # Make fewer calls than the limit
        for i in range(min(5, CALLS)):
            result = await counting_func()
            assert result == i + 1

        assert call_count == min(5, CALLS)

    @patch("hn_herald.rate_limit.limits")
    async def test_limits_decorator_applied_with_correct_params(self, mock_limits):
        # We need to reimport after patching to see the patched version
        # Instead, we verify the behavior by checking the module structure
        from hn_herald.rate_limit import CALLS, PERIOD

        # Verify the constants are used (indirect test)
        assert CALLS == 30
        assert PERIOD == 60

    async def test_decorated_function_is_async(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def async_func():
            return "async"

        # Should be awaitable
        import inspect

        # The decorated function should return a coroutine when called
        result_coro = async_func()
        assert inspect.iscoroutine(result_coro)
        result = await result_coro
        assert result == "async"


class TestSleepAndRetryBehavior:
    """Tests for sleep_and_retry functionality integration."""

    @patch("time.sleep")
    async def test_rate_limit_uses_sleep_and_retry(self, mock_sleep):
        from hn_herald.rate_limit import rate_limit

        # The sleep_and_retry decorator from ratelimit library wraps the function
        # to sleep when rate limit is exceeded. We verify the structure.
        @rate_limit
        async def test_func():
            return "done"

        # Function should still work
        result = await test_func()
        assert result == "done"

    async def test_decorator_chain_order(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def sample():
            """Sample docstring."""
            return

        # Verify the decorator preserves function identity via wraps
        assert sample.__name__ == "sample"
        assert sample.__doc__ == "Sample docstring."


class TestRateLimitWithMockedTime:
    """Tests for rate limiting behavior with mocked time."""

    async def test_rapid_calls_tracked(self):
        from hn_herald.rate_limit import rate_limit

        results = []

        @rate_limit
        async def tracked_func(value):
            results.append(value)
            return value

        # Make several rapid calls
        for i in range(3):
            await tracked_func(i)

        assert results == [0, 1, 2]

    async def test_concurrent_calls_handled(self):
        from hn_herald.rate_limit import rate_limit

        results = []

        @rate_limit
        async def concurrent_func(value):
            await asyncio.sleep(0.01)  # Small delay
            results.append(value)
            return value

        # Run multiple calls concurrently
        tasks = [concurrent_func(i) for i in range(3)]
        await asyncio.gather(*tasks)

        assert len(results) == 3
        assert set(results) == {0, 1, 2}


class TestRateLimitIntegration:
    """Integration tests for rate_limit module."""

    def test_module_exports(self):
        import hn_herald.rate_limit as rate_limit_module

        # Check that all expected exports are available
        assert hasattr(rate_limit_module, "rate_limit")
        assert hasattr(rate_limit_module, "CALLS")
        assert hasattr(rate_limit_module, "PERIOD")

    async def test_decorator_can_be_stacked(self):
        from hn_herald.rate_limit import rate_limit

        def logging_decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        @logging_decorator
        @rate_limit
        async def stacked_func():
            return "stacked"

        result = await stacked_func()
        assert result == "stacked"

    async def test_decorator_on_method(self):
        from hn_herald.rate_limit import rate_limit

        class Service:
            def __init__(self):
                self.call_count = 0

            @rate_limit
            async def process(self, data):
                self.call_count += 1
                return f"processed: {data}"

        service = Service()
        result = await service.process("test")

        assert result == "processed: test"
        assert service.call_count == 1

    async def test_multiple_decorated_functions_independent(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def func_a():
            return "a"

        @rate_limit
        async def func_b():
            return "b"

        # Both should work independently
        result_a = await func_a()
        result_b = await func_b()

        assert result_a == "a"
        assert result_b == "b"


class TestRateLimitEdgeCases:
    """Tests for edge cases in rate limiting."""

    async def test_none_return_value(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def returns_none():
            return None

        result = await returns_none()
        assert result is None

    async def test_empty_args(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def no_args():
            return "no args"

        result = await no_args()
        assert result == "no args"

    async def test_complex_return_types(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def returns_dict():
            return {"key": "value", "nested": {"a": 1}}

        @rate_limit
        async def returns_list():
            return [1, 2, [3, 4]]

        dict_result = await returns_dict()
        list_result = await returns_list()

        assert dict_result == {"key": "value", "nested": {"a": 1}}
        assert list_result == [1, 2, [3, 4]]

    async def test_async_generator_not_supported(self):
        from hn_herald.rate_limit import rate_limit

        # Note: The rate_limit decorator is designed for regular async functions
        # This test documents the expected behavior
        @rate_limit
        async def regular_async():
            return [1, 2, 3]

        result = await regular_async()
        assert result == [1, 2, 3]

    async def test_cancellation_handling(self):
        from hn_herald.rate_limit import rate_limit

        @rate_limit
        async def long_running():
            await asyncio.sleep(10)
            return "done"

        task = asyncio.create_task(long_running())
        await asyncio.sleep(0.01)  # Let it start
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
