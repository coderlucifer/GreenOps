"""
GreenOps SDK — Configuration

Centralized configuration for the SDK.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GreenOpsConfig:
    """SDK Configuration."""

    # Backend server URL
    server_url: str = "http://localhost:8000"

    # Default project name for grouping tracked calls
    project: str = "default"

    # Default region for carbon calculations
    region: str = "global_average"

    # Source identifier
    source: str = "sdk"

    # Auto-sync: send tracked calls to the backend automatically
    auto_sync: bool = True

    # Sync batch size — how many calls to buffer before sending
    sync_batch_size: int = 10

    # Enable local storage (SQLite) for offline tracking
    local_storage: bool = True

    # Local database path
    db_path: Optional[str] = None

    # Verbose logging
    verbose: bool = False

    def __post_init__(self):
        # Override from environment variables if set
        self.server_url = os.environ.get("GREENOPS_SERVER_URL", self.server_url)
        self.project = os.environ.get("GREENOPS_PROJECT", self.project)
        self.region = os.environ.get("GREENOPS_REGION", self.region)
        self.verbose = os.environ.get("GREENOPS_VERBOSE", "").lower() in ("1", "true", "yes")

        if self.db_path is None:
            # Default to user's home directory
            home = os.path.expanduser("~")
            greenops_dir = os.path.join(home, ".greenops")
            os.makedirs(greenops_dir, exist_ok=True)
            self.db_path = os.path.join(greenops_dir, "tracking.db")


# Global config singleton
_config: Optional[GreenOpsConfig] = None


def get_config() -> GreenOpsConfig:
    """Get the global SDK configuration."""
    global _config
    if _config is None:
        _config = GreenOpsConfig()
    return _config


def configure(**kwargs) -> GreenOpsConfig:
    """
    Configure the GreenOps SDK.

    Example:
        greenops.configure(
            server_url="https://greenops.example.com",
            project="my-chatbot",
            region="us_oregon",
        )
    """
    global _config
    _config = GreenOpsConfig(**kwargs)
    return _config
