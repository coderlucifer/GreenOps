"""
GreenOps SDK — Decorators

@track decorator for wrapping AI-related functions.
Automatically detects OpenAI/Anthropic/Google responses and logs them.
"""

import time
import functools
from typing import Optional, Callable, Any

from .tracker import get_tracker


def track(
    func: Optional[Callable] = None,
    *,
    model: Optional[str] = None,
    project: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Decorator to automatically track AI API calls.

    Supports two usage patterns:

    1. Simple (auto-detect):
        @track
        def my_function():
            return openai_client.chat.completions.create(...)

    2. With options:
        @track(project="my-chatbot", region="us_oregon")
        def my_function():
            return openai_client.chat.completions.create(...)

    The decorator inspects the return value to auto-detect:
    - OpenAI ChatCompletion responses
    - Anthropic Message responses
    - Google GenerativeAI responses
    - Raw dicts with token/usage fields
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            tracker = get_tracker()
            start_time = time.time()

            # Call the original function
            result = fn(*args, **kwargs)

            elapsed_ms = (time.time() - start_time) * 1000

            # Try to extract tracking data from the result
            tracking_data = _extract_tracking_data(result, model_override=model)

            if tracking_data:
                tracker.log_call(
                    model=tracking_data["model"],
                    input_tokens=tracking_data["input_tokens"],
                    output_tokens=tracking_data["output_tokens"],
                    latency_ms=round(elapsed_ms, 2),
                    provider=tracking_data.get("provider"),
                    project=project,
                    region=region,
                )

            return result

        # Mark as tracked for introspection
        wrapper._greenops_tracked = True
        return wrapper

    # Handle both @track and @track(...) usage
    if func is not None:
        return decorator(func)
    return decorator


def track_async(
    func: Optional[Callable] = None,
    *,
    model: Optional[str] = None,
    project: Optional[str] = None,
    region: Optional[str] = None,
):
    """
    Async version of @track for async AI API calls.

    Usage:
        @track_async
        async def my_function():
            return await openai_client.chat.completions.create(...)
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            tracker = get_tracker()
            start_time = time.time()

            result = await fn(*args, **kwargs)

            elapsed_ms = (time.time() - start_time) * 1000

            tracking_data = _extract_tracking_data(result, model_override=model)

            if tracking_data:
                tracker.log_call(
                    model=tracking_data["model"],
                    input_tokens=tracking_data["input_tokens"],
                    output_tokens=tracking_data["output_tokens"],
                    latency_ms=round(elapsed_ms, 2),
                    provider=tracking_data.get("provider"),
                    project=project,
                    region=region,
                )

            return result

        wrapper._greenops_tracked = True
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


# ============================================================
# RESPONSE PARSERS
# ============================================================

def _extract_tracking_data(result: Any, model_override: Optional[str] = None) -> Optional[dict]:
    """
    Inspect a response object and extract model + token usage.
    Supports OpenAI, Anthropic, Google, and raw dicts.
    """
    if result is None:
        return None

    # --- OpenAI ChatCompletion ---
    # Has: model, usage.prompt_tokens, usage.completion_tokens
    if hasattr(result, "usage") and hasattr(result, "model"):
        usage = result.usage
        if usage and hasattr(usage, "prompt_tokens"):
            return {
                "model": model_override or result.model,
                "input_tokens": usage.prompt_tokens or 0,
                "output_tokens": usage.completion_tokens or 0,
                "provider": "openai",
            }

    # --- Anthropic Message ---
    # Has: model, usage.input_tokens, usage.output_tokens
    if hasattr(result, "usage") and hasattr(result, "content"):
        usage = result.usage
        if hasattr(usage, "input_tokens") and hasattr(usage, "output_tokens"):
            model_name = model_override or getattr(result, "model", "unknown")
            return {
                "model": model_name,
                "input_tokens": usage.input_tokens or 0,
                "output_tokens": usage.output_tokens or 0,
                "provider": "anthropic",
            }

    # --- Google GenerativeAI ---
    # Has: usage_metadata with prompt_token_count, candidates_token_count
    if hasattr(result, "usage_metadata"):
        meta = result.usage_metadata
        if hasattr(meta, "prompt_token_count"):
            return {
                "model": model_override or getattr(result, "model", "gemini"),
                "input_tokens": meta.prompt_token_count or 0,
                "output_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                "provider": "google",
            }

    # --- Raw dict (e.g., from REST API calls) ---
    if isinstance(result, dict):
        # OpenAI-style dict
        if "usage" in result and isinstance(result["usage"], dict):
            usage = result["usage"]
            return {
                "model": model_override or result.get("model", "unknown"),
                "input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", 0)),
                "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", 0)),
                "provider": _detect_provider(result.get("model", "")),
            }

    return None


def _detect_provider(model_id: str) -> str:
    """Detect provider from model name."""
    model_lower = model_id.lower()
    if "gpt" in model_lower or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return "openai"
    if "claude" in model_lower:
        return "anthropic"
    if "gemini" in model_lower:
        return "google"
    if "llama" in model_lower:
        return "meta"
    if "mistral" in model_lower:
        return "mistral"
    if "deepseek" in model_lower:
        return "deepseek"
    return "unknown"
