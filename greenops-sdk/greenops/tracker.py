"""
GreenOps SDK — Core Tracker

The heart of the SDK. Tracks AI API calls, estimates environmental impact,
stores locally, and syncs to the GreenOps backend.
"""

import uuid
import time
import json
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from urllib import request as urllib_request
from urllib.error import URLError

from .config import get_config
from ._store import LocalStore


# ============================================================
# MODEL ENERGY PROFILES (embedded for zero-dependency usage)
# ============================================================

# Energy per 1K tokens in Wh — same values as the backend
_MODEL_ENERGY = {
    # OpenAI
    "gpt-4o":           {"input": 0.0040, "output": 0.0120, "provider": "openai"},
    "gpt-4o-mini":      {"input": 0.0008, "output": 0.0024, "provider": "openai"},
    "gpt-4-turbo":      {"input": 0.0066, "output": 0.0198, "provider": "openai"},
    "gpt-3.5-turbo":    {"input": 0.0015, "output": 0.0045, "provider": "openai"},
    "o1":               {"input": 0.0100, "output": 0.0300, "provider": "openai"},
    "o3-mini":          {"input": 0.0025, "output": 0.0075, "provider": "openai"},
    "o4-mini":          {"input": 0.0025, "output": 0.0075, "provider": "openai"},
    # Anthropic
    "claude-sonnet-4-20250514":  {"input": 0.0035, "output": 0.0105, "provider": "anthropic"},
    "claude-3-5-haiku-20241022": {"input": 0.0010, "output": 0.0030, "provider": "anthropic"},
    "claude-3-opus-20240229":    {"input": 0.0060, "output": 0.0180, "provider": "anthropic"},
    # Google
    "gemini-2.0-flash":  {"input": 0.0009, "output": 0.0027, "provider": "google"},
    "gemini-2.5-pro":    {"input": 0.0055, "output": 0.0165, "provider": "google"},
    "gemini-2.5-flash":  {"input": 0.0010, "output": 0.0030, "provider": "google"},
    # Meta
    "llama-3.1-405b":   {"input": 0.0080, "output": 0.0240, "provider": "meta"},
    "llama-3.1-70b":    {"input": 0.0040, "output": 0.0120, "provider": "meta"},
    "llama-3.1-8b":     {"input": 0.0008, "output": 0.0024, "provider": "meta"},
    # Mistral
    "mistral-large":    {"input": 0.0050, "output": 0.0150, "provider": "mistral"},
    "mistral-small":    {"input": 0.0012, "output": 0.0036, "provider": "mistral"},
    # DeepSeek
    "deepseek-r1":      {"input": 0.0045, "output": 0.0135, "provider": "deepseek"},
}

# Grid emission factor: kg CO₂ per kWh
_GRID_EF = 0.094
# Water usage effectiveness: L per kWh
_WUE = 1.15


def _lookup_model(model_id: str) -> Optional[Dict]:
    """Find model energy profile by exact or fuzzy match."""
    if model_id in _MODEL_ENERGY:
        return _MODEL_ENERGY[model_id]

    model_lower = model_id.lower()
    for key, profile in _MODEL_ENERGY.items():
        if key in model_lower or model_lower in key:
            return profile

    return None


def _estimate_impact(model_id: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
    """Estimate energy, CO₂, and water for a single call."""
    profile = _lookup_model(model_id)

    if profile:
        energy_wh = (input_tokens / 1000) * profile["input"] + \
                    (output_tokens / 1000) * profile["output"]
        provider = profile["provider"]
    else:
        # Conservative default for unknown models
        total_tokens = input_tokens + output_tokens
        energy_wh = (total_tokens / 1000) * 0.004
        provider = "unknown"

    co2_g = (energy_wh / 1000) * _GRID_EF * 1000
    water_ml = (energy_wh / 1000) * _WUE * 1000

    return {
        "energy_wh": round(energy_wh, 6),
        "co2_g": round(co2_g, 6),
        "water_ml": round(water_ml, 6),
        "provider": provider,
    }


# ============================================================
# TRACKER
# ============================================================

class Tracker:
    """
    Core GreenOps tracker.

    Tracks AI API calls, calculates environmental impact,
    stores locally, and auto-syncs to the backend.
    """

    def __init__(self):
        self._config = get_config()
        self._store: Optional[LocalStore] = None
        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._session_calls: List[Dict[str, Any]] = []

        if self._config.local_storage:
            self._store = LocalStore(self._config.db_path)

    def _ensure_config(self):
        """Refresh config reference."""
        self._config = get_config()
        if self._config.local_storage and self._store is None:
            self._store = LocalStore(self._config.db_path)

    def log_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: Optional[float] = None,
        provider: Optional[str] = None,
        project: Optional[str] = None,
        region: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Log a single AI API call.

        Args:
            model: Model identifier (e.g., "gpt-4o", "claude-sonnet-4-20250514")
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            latency_ms: Request latency in milliseconds
            provider: Provider name (auto-detected if not provided)
            project: Project name (uses config default if not provided)
            region: Region for carbon calculation (uses config default)
            metadata: Extra metadata dict

        Returns:
            Dict with the tracked call data including environmental impact.
        """
        self._ensure_config()

        # Estimate environmental impact
        impact = _estimate_impact(model, input_tokens, output_tokens)

        call_data = {
            "call_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_id": model,
            "provider": provider or impact["provider"],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "energy_wh": impact["energy_wh"],
            "co2_g": impact["co2_g"],
            "water_ml": impact["water_ml"],
            "cost_usd": 0.0,  # Calculated by backend if synced
            "latency_ms": latency_ms,
            "region": region or self._config.region,
            "source": self._config.source,
            "project": project or self._config.project,
            "metadata": metadata or {},
        }

        # Store locally
        if self._store:
            self._store.save_call(call_data)

        # Buffer for session tracking
        with self._lock:
            self._session_calls.append(call_data)
            self._buffer.append(call_data)

        # Auto-sync if buffer is full
        if self._config.auto_sync and len(self._buffer) >= self._config.sync_batch_size:
            self._sync_async()

        if self._config.verbose:
            print(
                f"[GreenOps] Tracked: {model} | "
                f"{input_tokens}+{output_tokens} tokens | "
                f"{impact['energy_wh']:.6f} Wh | "
                f"{impact['co2_g']:.6f}g CO₂"
            )

        return call_data

    def _sync_async(self):
        """Sync buffered calls to the backend in a background thread."""
        with self._lock:
            calls_to_sync = self._buffer.copy()
            self._buffer.clear()

        if not calls_to_sync:
            return

        thread = threading.Thread(
            target=self._do_sync,
            args=(calls_to_sync,),
            daemon=True,
        )
        thread.start()

    def _do_sync(self, calls: List[Dict[str, Any]]):
        """Actually send calls to the backend."""
        try:
            payload = json.dumps({
                "calls": [
                    {
                        "call_id": c["call_id"],
                        "model_id": c["model_id"],
                        "provider": c["provider"],
                        "input_tokens": c["input_tokens"],
                        "output_tokens": c["output_tokens"],
                        "latency_ms": c["latency_ms"],
                        "region": c["region"],
                        "source": c["source"],
                        "project": c["project"],
                        "metadata": c["metadata"],
                        "timestamp": c["timestamp"],
                    }
                    for c in calls
                ]
            }).encode("utf-8")

            url = f"{self._config.server_url}/api/track/batch"
            req = urllib_request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib_request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())

            # Mark as synced in local store
            if self._store:
                call_ids = [c["call_id"] for c in calls]
                self._store.mark_synced(call_ids)

            if self._config.verbose:
                print(f"[GreenOps] Synced {len(calls)} calls to backend")

        except (URLError, Exception) as e:
            if self._config.verbose:
                print(f"[GreenOps] Sync failed (will retry): {e}")
            # Calls remain in local store as unsynced

    def sync(self):
        """
        Manually sync all buffered and unsynced calls to the backend.
        Blocks until sync is complete.
        """
        self._ensure_config()

        # First flush the buffer
        with self._lock:
            buffer_calls = self._buffer.copy()
            self._buffer.clear()

        # Then get any unsynced from local store
        store_calls = []
        if self._store:
            unsynced = self._store.get_unsynced_calls(limit=500)
            # Avoid duplicates
            buffer_ids = {c["call_id"] for c in buffer_calls}
            store_calls = [c for c in unsynced if c["call_id"] not in buffer_ids]

        all_calls = buffer_calls + store_calls

        if not all_calls:
            if self._config.verbose:
                print("[GreenOps] Nothing to sync")
            return {"synced": 0}

        self._do_sync(all_calls)
        return {"synced": len(all_calls)}

    def get_session_stats(self) -> Dict[str, Any]:
        """Get stats for calls tracked in this Python session."""
        with self._lock:
            calls = self._session_calls.copy()

        if not calls:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_energy_wh": 0,
                "total_co2_g": 0,
                "total_water_ml": 0,
            }

        return {
            "total_calls": len(calls),
            "total_input_tokens": sum(c["input_tokens"] for c in calls),
            "total_output_tokens": sum(c["output_tokens"] for c in calls),
            "total_tokens": sum(c["total_tokens"] for c in calls),
            "total_energy_wh": round(sum(c["energy_wh"] for c in calls), 6),
            "total_co2_g": round(sum(c["co2_g"] for c in calls), 6),
            "total_water_ml": round(sum(c["water_ml"] for c in calls), 6),
            "models_used": list(set(c["model_id"] for c in calls)),
            "calls": calls,
        }

    def get_full_summary(self) -> Dict[str, Any]:
        """Get full summary from local storage (all-time, not just session)."""
        if self._store:
            return self._store.get_session_summary()
        return self.get_session_stats()

    def reset_session(self):
        """Clear session tracking (doesn't affect local storage)."""
        with self._lock:
            self._session_calls.clear()
            self._buffer.clear()


# Global tracker singleton
_tracker: Optional[Tracker] = None


def get_tracker() -> Tracker:
    """Get the global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = Tracker()
    return _tracker
