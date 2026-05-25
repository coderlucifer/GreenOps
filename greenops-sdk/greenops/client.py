"""
GreenOps SDK — OpenAI Client Wrapper

Drop-in wrapper around the OpenAI client that automatically
tracks every API call with zero code changes.

Usage:
    from greenops import OpenAIClient

    # Instead of: client = openai.OpenAI(api_key="sk-...")
    client = OpenAIClient(api_key="sk-...")

    # Use exactly like normal OpenAI client
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    # ^ This call is automatically tracked by GreenOps
"""

import time
from typing import Any, Optional

from .tracker import get_tracker


class _TrackedCompletions:
    """Wrapper around openai.chat.completions that auto-tracks calls."""

    def __init__(self, original_completions, project: Optional[str] = None):
        self._original = original_completions
        self._project = project

    def create(self, **kwargs) -> Any:
        """Wrapper around chat.completions.create() with auto-tracking."""
        tracker = get_tracker()
        start_time = time.time()

        # Call the original OpenAI method
        result = self._original.create(**kwargs)

        elapsed_ms = (time.time() - start_time) * 1000

        # Extract usage from the response
        if hasattr(result, "usage") and result.usage:
            tracker.log_call(
                model=getattr(result, "model", kwargs.get("model", "unknown")),
                input_tokens=result.usage.prompt_tokens or 0,
                output_tokens=result.usage.completion_tokens or 0,
                latency_ms=round(elapsed_ms, 2),
                provider="openai",
                project=self._project,
            )

        return result

    async def acreate(self, **kwargs) -> Any:
        """Async wrapper for chat.completions.create()."""
        tracker = get_tracker()
        start_time = time.time()

        result = await self._original.create(**kwargs)

        elapsed_ms = (time.time() - start_time) * 1000

        if hasattr(result, "usage") and result.usage:
            tracker.log_call(
                model=getattr(result, "model", kwargs.get("model", "unknown")),
                input_tokens=result.usage.prompt_tokens or 0,
                output_tokens=result.usage.completion_tokens or 0,
                latency_ms=round(elapsed_ms, 2),
                provider="openai",
                project=self._project,
            )

        return result

    def __getattr__(self, name):
        """Proxy all other attributes to the original."""
        return getattr(self._original, name)


class _TrackedChat:
    """Wrapper around openai.chat that provides tracked completions."""

    def __init__(self, original_chat, project: Optional[str] = None):
        self._original = original_chat
        self._project = project

    @property
    def completions(self):
        return _TrackedCompletions(self._original.completions, self._project)

    def __getattr__(self, name):
        return getattr(self._original, name)


class OpenAIClient:
    """
    Drop-in replacement for openai.OpenAI() that auto-tracks every call.

    Usage:
        from greenops import OpenAIClient

        client = OpenAIClient(api_key="sk-...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}]
        )
        # Automatically tracked!
    """

    def __init__(self, project: Optional[str] = None, **kwargs):
        """
        Initialize the tracked OpenAI client.

        Args:
            project: GreenOps project name for grouping
            **kwargs: All arguments passed to openai.OpenAI()
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use OpenAIClient. "
                "Install it with: pip install openai"
            )

        self._client = openai.OpenAI(**kwargs)
        self._project = project

    @property
    def chat(self):
        return _TrackedChat(self._client.chat, self._project)

    def __getattr__(self, name):
        """Proxy all other attributes to the underlying OpenAI client."""
        return getattr(self._client, name)


class AsyncOpenAIClient:
    """
    Drop-in replacement for openai.AsyncOpenAI() with auto-tracking.

    Usage:
        from greenops import AsyncOpenAIClient

        client = AsyncOpenAIClient(api_key="sk-...")
        response = await client.chat.completions.create(...)
    """

    def __init__(self, project: Optional[str] = None, **kwargs):
        try:
            import openai
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use AsyncOpenAIClient. "
                "Install it with: pip install openai"
            )

        self._client = openai.AsyncOpenAI(**kwargs)
        self._project = project

    @property
    def chat(self):
        return _TrackedChat(self._client.chat, self._project)

    def __getattr__(self, name):
        return getattr(self._client, name)
