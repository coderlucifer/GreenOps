"""
GreenOps SDK — Local Storage

Local SQLite database for offline tracking.
Calls are stored locally first, then synced to the backend.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


SCHEMA = """
CREATE TABLE IF NOT EXISTS tracked_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id         TEXT UNIQUE NOT NULL,
    timestamp       TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    provider        TEXT NOT NULL,
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    energy_wh       REAL DEFAULT 0,
    co2_g           REAL DEFAULT 0,
    water_ml        REAL DEFAULT 0,
    cost_usd        REAL DEFAULT 0,
    latency_ms      REAL DEFAULT NULL,
    region          TEXT DEFAULT 'global_average',
    source          TEXT DEFAULT 'sdk',
    project         TEXT DEFAULT 'default',
    metadata        TEXT DEFAULT '{}',
    synced          INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tracked_synced ON tracked_calls(synced);
CREATE INDEX IF NOT EXISTS idx_tracked_timestamp ON tracked_calls(timestamp);
"""


class LocalStore:
    """Local SQLite storage for tracked calls."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_db() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _get_db(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_call(self, call_data: Dict[str, Any]):
        """Save a tracked call to local storage."""
        with self._get_db() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO tracked_calls (
                    call_id, timestamp, model_id, provider,
                    input_tokens, output_tokens, total_tokens,
                    energy_wh, co2_g, water_ml, cost_usd,
                    latency_ms, region, source, project, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_data["call_id"],
                call_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                call_data["model_id"],
                call_data["provider"],
                call_data.get("input_tokens", 0),
                call_data.get("output_tokens", 0),
                call_data.get("total_tokens", 0),
                call_data.get("energy_wh", 0),
                call_data.get("co2_g", 0),
                call_data.get("water_ml", 0),
                call_data.get("cost_usd", 0),
                call_data.get("latency_ms"),
                call_data.get("region", "global_average"),
                call_data.get("source", "sdk"),
                call_data.get("project", "default"),
                json.dumps(call_data.get("metadata", {})),
            ))

    def get_unsynced_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get calls that haven't been synced to the backend yet."""
        with self._get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM tracked_calls WHERE synced = 0 ORDER BY timestamp ASC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_synced(self, call_ids: List[str]):
        """Mark calls as synced after successful backend upload."""
        if not call_ids:
            return
        placeholders = ",".join("?" * len(call_ids))
        with self._get_db() as conn:
            conn.execute(
                f"UPDATE tracked_calls SET synced = 1 WHERE call_id IN ({placeholders})",
                call_ids,
            )

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked calls in the current local store."""
        with self._get_db() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)                    as total_calls,
                    COALESCE(SUM(input_tokens), 0)    as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0)   as total_output_tokens,
                    COALESCE(SUM(total_tokens), 0)    as total_tokens,
                    COALESCE(SUM(energy_wh), 0)       as total_energy_wh,
                    COALESCE(SUM(co2_g), 0)           as total_co2_g,
                    COALESCE(SUM(water_ml), 0)        as total_water_ml,
                    COALESCE(SUM(cost_usd), 0)        as total_cost_usd,
                    COALESCE(AVG(latency_ms), 0)      as avg_latency_ms,
                    SUM(CASE WHEN synced = 0 THEN 1 ELSE 0 END) as unsynced_count
                FROM tracked_calls
            """).fetchone()

            models = conn.execute("""
                SELECT
                    model_id, provider,
                    COUNT(*) as call_count,
                    SUM(total_tokens) as total_tokens,
                    SUM(energy_wh) as total_energy_wh,
                    SUM(co2_g) as total_co2_g
                FROM tracked_calls
                GROUP BY model_id, provider
                ORDER BY total_energy_wh DESC
            """).fetchall()

        return {
            "totals": dict(row),
            "models": [dict(m) for m in models],
        }

    def get_recent_calls(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most recent tracked calls."""
        with self._get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM tracked_calls ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def clear(self):
        """Clear all tracked calls from local storage."""
        with self._get_db() as conn:
            conn.execute("DELETE FROM tracked_calls")
