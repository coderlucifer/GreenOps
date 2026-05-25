"""
GreenOps — Database Layer

SQLite database for tracking AI API calls, carbon budgets, and analytics.
Uses pure sqlite3 for transparency — no ORM magic.
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

# Database file location
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "greenops.db")


# ============================================================
# SCHEMA
# ============================================================

SCHEMA = """
-- Users
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT DEFAULT 'admin',             -- RBAC: admin, viewer
    is_demo         INTEGER DEFAULT 0,                -- 1 for the demo account
    created_at      TEXT DEFAULT (datetime('now'))
);

-- API Keys (per user, multiple allowed)
CREATE TABLE IF NOT EXISTS api_keys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    key             TEXT UNIQUE NOT NULL,
    label           TEXT DEFAULT 'default',
    last_used_at    TEXT DEFAULT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Tracked AI API calls
CREATE TABLE IF NOT EXISTS api_calls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id         TEXT UNIQUE NOT NULL,
    user_id         INTEGER REFERENCES users(id),      -- owner
    timestamp       TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    provider        TEXT NOT NULL,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    energy_wh       REAL NOT NULL DEFAULT 0,
    co2_g           REAL NOT NULL DEFAULT 0,
    water_ml        REAL NOT NULL DEFAULT 0,
    cost_usd        REAL NOT NULL DEFAULT 0,
    latency_ms      REAL DEFAULT NULL,
    region          TEXT DEFAULT 'global_average',
    source          TEXT DEFAULT 'sdk',
    project         TEXT DEFAULT 'default',
    metadata        TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Carbon budgets
CREATE TABLE IF NOT EXISTS budgets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER REFERENCES users(id),      -- owner
    project         TEXT NOT NULL DEFAULT 'default',
    period          TEXT NOT NULL,
    co2_limit_g     REAL NOT NULL,
    energy_limit_wh REAL DEFAULT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, project, period)
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    name            TEXT NOT NULL,
    webhook_url     TEXT DEFAULT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, name)
);

-- AI Models (Dynamic registry)
CREATE TABLE IF NOT EXISTS ai_models (
    model_id        TEXT PRIMARY KEY,
    provider        TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    family          TEXT NOT NULL,
    parameter_count TEXT,
    energy_per_1k_input_tokens_wh   REAL NOT NULL,
    energy_per_1k_output_tokens_wh  REAL NOT NULL,
    cost_per_1k_input_tokens_usd    REAL NOT NULL,
    cost_per_1k_output_tokens_usd   REAL NOT NULL,
    quality_score   INTEGER NOT NULL,
    latency_tier    TEXT NOT NULL,
    tags            TEXT NOT NULL, -- JSON array
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON api_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_calls_model ON api_calls(model_id);
CREATE INDEX IF NOT EXISTS idx_calls_user ON api_calls(user_id);
CREATE INDEX IF NOT EXISTS idx_calls_project ON api_calls(project);
CREATE INDEX IF NOT EXISTS idx_keys_key ON api_keys(key);
CREATE INDEX IF NOT EXISTS idx_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id);
"""

# Demo user credentials
DEMO_EMAIL = "demo@greenops.dev"
DEMO_PASSWORD = "demo1234"
DEMO_NAME = "Demo User"


# ============================================================
# CONNECTION MANAGEMENT
# ============================================================

def get_connection() -> sqlite3.Connection:
    """Get a database connection with WAL mode for better concurrency."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database schema and create the demo user."""
    from services.auth import hash_password, generate_api_key

    with get_db() as conn:
        conn.executescript(SCHEMA)
        
        # Migrations
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
        except Exception:
            pass
            
        try:
            conn.execute("ALTER TABLE projects ADD COLUMN webhook_url TEXT DEFAULT NULL")
        except Exception:
            pass

    # Create demo user if not exists
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (DEMO_EMAIL,)
        ).fetchone()

        if not existing:
            hashed = hash_password(DEMO_PASSWORD)
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, is_demo) VALUES (?, ?, ?, 1)",
                (DEMO_NAME, DEMO_EMAIL, hashed),
            )
            demo_user_id = cursor.lastrowid

            # Create a demo API key
            api_key = generate_api_key()
            conn.execute(
                "INSERT INTO api_keys (user_id, key, label) VALUES (?, ?, ?)",
                (demo_user_id, api_key, "demo-key"),
            )
            print(f"[GreenOps] Demo user created: {DEMO_EMAIL} / {DEMO_PASSWORD}")
            print(f"[GreenOps] Demo API key: {api_key}")
        else:
            print(f"[GreenOps] Demo user already exists")

    # Seed AI Models if empty
    with get_db() as conn:
        models_count = conn.execute("SELECT COUNT(*) as c FROM ai_models").fetchone()["c"]
        if models_count == 0:
            from services.model_profiles import MODEL_PROFILES
            for m in MODEL_PROFILES.values():
                conn.execute("""
                    INSERT INTO ai_models (
                        model_id, provider, display_name, family, parameter_count,
                        energy_per_1k_input_tokens_wh, energy_per_1k_output_tokens_wh,
                        cost_per_1k_input_tokens_usd, cost_per_1k_output_tokens_usd,
                        quality_score, latency_tier, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m.model_id, m.provider, m.display_name, m.family, m.parameter_count,
                    m.energy_per_1k_input_tokens_wh, m.energy_per_1k_output_tokens_wh,
                    m.cost_per_1k_input_tokens_usd, m.cost_per_1k_output_tokens_usd,
                    m.quality_score, m.latency_tier, json.dumps(m.tags)
                ))
            print(f"[GreenOps] Seeded {len(MODEL_PROFILES)} AI models into the database.")

    print(f"[GreenOps] Database initialized at {DB_PATH}")


# ============================================================
# USER MANAGEMENT
# ============================================================

def create_user(name: str, email: str, password_hash: str) -> Dict[str, Any]:
    """Create a new user. Returns user dict."""
    from services.auth import generate_api_key
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        user_id = cursor.lastrowid
        # Auto-create a default API key
        api_key = generate_api_key()
        conn.execute(
            "INSERT INTO api_keys (user_id, key, label) VALUES (?, ?, ?)",
            (user_id, api_key, "default"),
        )
    return {"id": user_id, "name": name, "email": email, "api_key": api_key}


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Find a user by email."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Find a user by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Find a user by their API key."""
    with get_db() as conn:
        row = conn.execute("""
            SELECT u.* FROM users u
            JOIN api_keys k ON k.user_id = u.id
            WHERE k.key = ?
        """, (api_key,)).fetchone()
        if row:
            # Update last_used_at
            conn.execute(
                "UPDATE api_keys SET last_used_at = datetime('now') WHERE key = ?",
                (api_key,),
            )
        return dict(row) if row else None


def get_user_api_keys(user_id: int) -> List[Dict[str, Any]]:
    """Get all API keys for a user."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, key, label, last_used_at, created_at FROM api_keys WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_demo_user_id() -> Optional[int]:
    """Get the demo user's ID."""
    with get_db() as conn:
        row = conn.execute("SELECT id FROM users WHERE is_demo = 1").fetchone()
        return row["id"] if row else None


# ============================================================
# PROJECTS & MODELS
# ============================================================

def get_user_projects(user_id: int) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY name ASC", (user_id,)).fetchall()
        return [dict(r) for r in rows]

def create_project(user_id: int, name: str) -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO projects (user_id, name) VALUES (?, ?)",
            (user_id, name)
        )
        row = conn.execute("SELECT * FROM projects WHERE user_id = ? AND name = ?", (user_id, name)).fetchone()
        return dict(row) if row else None

def delete_project(user_id: int, name: str) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM projects WHERE user_id = ? AND name = ?", (user_id, name))
        return cursor.rowcount > 0

def get_all_models() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM ai_models ORDER BY display_name ASC").fetchall()
        return [dict(r) for r in rows]

def get_model(model_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM ai_models WHERE model_id = ?", (model_id,)).fetchone()
        return dict(row) if row else None


# ============================================================
# API CALL TRACKING
# ============================================================

def insert_api_call(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a tracked API call into the database.
    Returns the inserted record.
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO api_calls (
                call_id, user_id, timestamp, model_id, provider,
                input_tokens, output_tokens, total_tokens,
                energy_wh, co2_g, water_ml, cost_usd,
                latency_ms, region, source, project, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            call_data["call_id"],
            call_data.get("user_id"),
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

    return call_data


def insert_api_calls_batch(calls: List[Dict[str, Any]], user_id: Optional[int] = None) -> int:
    """
    Batch insert multiple API calls. Returns count inserted.
    """
    with get_db() as conn:
        conn.executemany("""
            INSERT OR IGNORE INTO api_calls (
                call_id, user_id, timestamp, model_id, provider,
                input_tokens, output_tokens, total_tokens,
                energy_wh, co2_g, water_ml, cost_usd,
                latency_ms, region, source, project, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (
                c["call_id"], c.get("user_id", user_id),
                c.get("timestamp", datetime.now(timezone.utc).isoformat()),
                c["model_id"], c["provider"],
                c.get("input_tokens", 0), c.get("output_tokens", 0), c.get("total_tokens", 0),
                c.get("energy_wh", 0), c.get("co2_g", 0), c.get("water_ml", 0),
                c.get("cost_usd", 0), c.get("latency_ms"),
                c.get("region", "global_average"), c.get("source", "sdk"),
                c.get("project", "default"), json.dumps(c.get("metadata", {})),
            )
            for c in calls
        ])
    return len(calls)

def stream_csv_calls(user_id: int):
    """Generator to stream all calls as CSV rows efficiently."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Timestamp", "Model", "Provider", "Input Tokens", "Output Tokens", 
        "Total Tokens", "Energy (Wh)", "CO2 (g)", "Water (mL)", 
        "Cost (USD)", "Latency (ms)", "Region", "Project", "Source"
    ])
    yield output.getvalue()
    output.truncate(0)
    output.seek(0)

    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM api_calls WHERE user_id = ? ORDER BY timestamp DESC", 
            (user_id,)
        )
        for row in cursor:
            writer.writerow([
                row["timestamp"], row["model_id"], row["provider"],
                row["input_tokens"], row["output_tokens"], row["total_tokens"],
                round(row["energy_wh"], 6), round(row["co2_g"], 6), 
                round(row["water_ml"], 6), round(row["cost_usd"], 6),
                row["latency_ms"], row["region"], row["project"], row["source"],
            ])
            yield output.getvalue()
            output.truncate(0)
            output.seek(0)


def get_recent_calls(
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[int] = None,
    project: Optional[str] = None,
    model_id: Optional[str] = None,
    provider: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get recent API calls with optional filters."""
    query = "SELECT * FROM api_calls WHERE 1=1"
    params = []

    if user_id is not None:
        query += " AND user_id = ?"
        params.append(user_id)
    if project:
        query += " AND project = ?"
        params.append(project)
    if model_id:
        query += " AND model_id = ?"
        params.append(model_id)
    if provider:
        query += " AND provider = ?"
        params.append(provider)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_call_count(user_id: Optional[int] = None) -> int:
    """Get total number of tracked calls."""
    with get_db() as conn:
        if user_id is not None:
            row = conn.execute("SELECT COUNT(*) as cnt FROM api_calls WHERE user_id = ?", (user_id,)).fetchone()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM api_calls").fetchone()
        return row["cnt"]


# ============================================================
# DASHBOARD AGGREGATION
# ============================================================

def get_dashboard_summary(
    user_id: Optional[int] = None,
    project: Optional[str] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Get aggregated dashboard metrics for the last N days.
    """
    where_clause = "WHERE timestamp >= datetime('now', ?)"
    params: list = [f"-{days} days"]

    if user_id is not None:
        where_clause += " AND user_id = ?"
        params.append(user_id)
    if project:
        where_clause += " AND project = ?"
        params.append(project)

    with get_db() as conn:
        totals = conn.execute(f"""
            SELECT
                COUNT(*)               as total_calls,
                COALESCE(SUM(input_tokens), 0)   as total_input_tokens,
                COALESCE(SUM(output_tokens), 0)  as total_output_tokens,
                COALESCE(SUM(total_tokens), 0)   as total_tokens,
                COALESCE(SUM(energy_wh), 0)      as total_energy_wh,
                COALESCE(SUM(co2_g), 0)          as total_co2_g,
                COALESCE(SUM(water_ml), 0)       as total_water_ml,
                COALESCE(SUM(cost_usd), 0)       as total_cost_usd,
                COALESCE(AVG(latency_ms), 0)     as avg_latency_ms
            FROM api_calls
            {where_clause}
        """, params).fetchone()

        models = conn.execute(f"""
            SELECT
                model_id, provider,
                COUNT(*)                as call_count,
                SUM(total_tokens)       as total_tokens,
                SUM(energy_wh)          as total_energy_wh,
                SUM(co2_g)             as total_co2_g,
                SUM(water_ml)          as total_water_ml,
                SUM(cost_usd)          as total_cost_usd
            FROM api_calls
            {where_clause}
            GROUP BY model_id, provider
            ORDER BY total_energy_wh DESC
        """, params).fetchall()

        trends = conn.execute(f"""
            SELECT
                DATE(timestamp)        as date,
                COUNT(*)               as calls,
                SUM(energy_wh)         as energy_wh,
                SUM(co2_g)            as co2_g,
                SUM(water_ml)         as water_ml,
                SUM(total_tokens)     as tokens,
                SUM(cost_usd)         as cost_usd
            FROM api_calls
            {where_clause}
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """, params).fetchall()

        sources = conn.execute(f"""
            SELECT
                source,
                COUNT(*) as call_count,
                SUM(energy_wh) as total_energy_wh
            FROM api_calls
            {where_clause}
            GROUP BY source
        """, params).fetchall()

    return {
        "period_days": days,
        "totals": dict(totals),
        "models": [dict(m) for m in models],
        "daily_trends": [dict(t) for t in trends],
        "sources": [dict(s) for s in sources],
    }


def get_model_comparison() -> List[Dict[str, Any]]:
    """Get usage comparison across all models ever tracked."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                model_id,
                provider,
                COUNT(*)                   as total_calls,
                SUM(total_tokens)          as total_tokens,
                SUM(energy_wh)             as total_energy_wh,
                SUM(co2_g)                as total_co2_g,
                SUM(water_ml)             as total_water_ml,
                SUM(cost_usd)             as total_cost_usd,
                AVG(energy_wh)            as avg_energy_per_call,
                AVG(latency_ms)           as avg_latency_ms,
                MIN(timestamp)            as first_used,
                MAX(timestamp)            as last_used
            FROM api_calls
            GROUP BY model_id, provider
            ORDER BY total_energy_wh DESC
        """).fetchall()

    return [dict(r) for r in rows]


def get_hourly_distribution() -> List[Dict[str, Any]]:
    """Get call distribution by hour of day (useful for peak analysis)."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*)        as calls,
                SUM(energy_wh)  as energy_wh,
                SUM(co2_g)     as co2_g
            FROM api_calls
            GROUP BY hour
            ORDER BY hour
        """).fetchall()

    return [dict(r) for r in rows]


# ============================================================
# CARBON BUDGET
# ============================================================

def set_budget(user_id: int, project: str, period: str, co2_limit_g: float, energy_limit_wh: Optional[float] = None):
    """Set or update a carbon budget for a project."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO budgets (user_id, project, period, co2_limit_g, energy_limit_wh)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, project, period)
            DO UPDATE SET co2_limit_g = ?, energy_limit_wh = ?
        """, (user_id, project, period, co2_limit_g, energy_limit_wh, co2_limit_g, energy_limit_wh))


def get_budget_status(user_id: int, project: str = "default") -> List[Dict[str, Any]]:
    """Get current budget status with usage for all periods."""
    period_intervals = {
        "daily": "-1 day",
        "weekly": "-7 days",
        "monthly": "-30 days",
    }

    results = []
    with get_db() as conn:
        budgets = conn.execute(
            "SELECT * FROM budgets WHERE user_id = ? AND project = ?", (user_id, project,)
        ).fetchall()

        for budget in budgets:
            interval = period_intervals.get(budget["period"], "-30 days")

            usage = conn.execute("""
                SELECT
                    COALESCE(SUM(co2_g), 0)    as used_co2_g,
                    COALESCE(SUM(energy_wh), 0) as used_energy_wh,
                    COUNT(*)                    as call_count
                FROM api_calls
                WHERE user_id = ? AND project = ? AND timestamp >= datetime('now', ?)
            """, (user_id, project, interval)).fetchone()

            limit = budget["co2_limit_g"]
            used = usage["used_co2_g"]
            pct = round((used / limit) * 100, 2) if limit > 0 else 0

            results.append({
                "project": project,
                "period": budget["period"],
                "co2_limit_g": limit,
                "co2_used_g": round(used, 4),
                "co2_remaining_g": round(max(0, limit - used), 4),
                "usage_percent": pct,
                "energy_limit_wh": budget["energy_limit_wh"],
                "energy_used_wh": round(usage["used_energy_wh"], 4),
                "call_count": usage["call_count"],
                "status": "exceeded" if pct >= 100 else "warning" if pct >= 80 else "ok",
            })

    return results

def prune_demo_data(user_id: int, max_records: int = 1000) -> None:
    """Keeps only the most recent `max_records` for the given user, deleting older ones."""
    with get_db() as conn:
        conn.execute("""
            DELETE FROM api_calls 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM api_calls 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            )
        """, (user_id, user_id, max_records))

def vacuum_db() -> None:
    """Reclaim disk space and optimize the database."""
    conn = get_connection()
    conn.isolation_level = None  # VACUUM must run outside of a transaction
    try:
        conn.execute("VACUUM")
    finally:
        conn.close()
