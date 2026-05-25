"""
GreenOps SDK — Track the carbon footprint of your AI usage.

Quick Start:
    import greenops

    # Configure (optional — defaults to localhost:8000)
    greenops.configure(project="my-app", server_url="http://localhost:8000")

    # Option 1: Manual tracking
    greenops.log("gpt-4o", input_tokens=500, output_tokens=200)

    # Option 2: Decorator
    @greenops.track
    def ask_ai(prompt):
        return client.chat.completions.create(model="gpt-4o", messages=[...])

    # Option 3: Drop-in OpenAI client
    from greenops import OpenAIClient
    client = OpenAIClient(api_key="sk-...")

    # View report
    greenops.report()
"""

__version__ = "1.0.0"
__author__ = "GreenOps"

# ---- Configuration ----
from .config import configure, get_config

# ---- Core Tracking ----
from .tracker import get_tracker

# ---- Decorators ----
from .decorators import track, track_async

# ---- Client Wrappers ----
from .client import OpenAIClient, AsyncOpenAIClient

# ---- Reporting ----
from .report import summary as report
from .report import quick_stats, print_call


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def log(
    model: str,
    input_tokens: int,
    output_tokens: int,
    **kwargs,
):
    """
    Log an AI API call manually.

    Args:
        model: Model ID (e.g., "gpt-4o")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        **kwargs: Optional: latency_ms, provider, project, region, metadata

    Example:
        greenops.log("gpt-4o", input_tokens=500, output_tokens=200)
    """
    return get_tracker().log_call(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        **kwargs,
    )


def sync():
    """
    Sync all tracked calls to the GreenOps backend.
    Call this before your script exits to ensure all data is sent.

    Example:
        greenops.sync()
    """
    return get_tracker().sync()


def stats():
    """
    Get current session stats as a dict.

    Example:
        data = greenops.stats()
        print(f"Total CO₂: {data['total_co2_g']}g")
    """
    return get_tracker().get_session_stats()


def reset():
    """Reset the session tracker (doesn't affect local storage)."""
    get_tracker().reset_session()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # Configuration
    "configure",
    "get_config",
    # Tracking
    "log",
    "track",
    "track_async",
    "sync",
    "stats",
    "reset",
    # Clients
    "OpenAIClient",
    "AsyncOpenAIClient",
    # Reporting
    "report",
    "quick_stats",
    "print_call",
    # Version
    "__version__",
]
