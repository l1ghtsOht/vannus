# ────────────────────────────────────────────────────────────────────
# feedback_db.py — SQLite-backed structured feedback collection
# ────────────────────────────────────────────────────────────────────
"""
Collects three types of feedback:
  1. Search feedback — thumbs up/down on elimination results
  2. Tool feedback — flag incorrect tier, score, or badge
  3. Events — implicit behavioral signals (clicks, scroll, etc.)

Database: praxis/data/feedback.db (auto-created on first access)
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Use PRAXIS_DATA_DIR env var for persistent storage (Railway volume mount).
# Falls back to praxis/data/ for local development.
_DATA_DIR = os.environ.get("PRAXIS_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
DB_PATH = os.path.join(_DATA_DIR, "feedback.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    session_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    constraints TEXT,
    survivors TEXT,
    eliminated_count INTEGER,
    rating TEXT CHECK(rating IN ('up', 'down')),
    comment TEXT
);

CREATE TABLE IF NOT EXISTS tool_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    session_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    current_tier TEXT NOT NULL,
    suggested_tier TEXT,
    flag_type TEXT CHECK(flag_type IN ('wrong_tier', 'wrong_score', 'outdated_info', 'missing_badge', 'other')),
    reason TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    session_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT
);

CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    path TEXT NOT NULL,
    referrer TEXT,
    user_agent TEXT
);
"""


def _get_connection() -> sqlite3.Connection:
    """Open a connection. Caller must close it."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def record_search_feedback(
    session_id: str,
    query_text: str,
    constraints: Optional[str] = None,
    survivors: Optional[str] = None,
    eliminated_count: Optional[int] = None,
    rating: Optional[str] = None,
    comment: Optional[str] = None,
) -> int:
    """Insert a search feedback record. Returns the row ID."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO search_feedback (session_id, query_text, constraints, survivors, eliminated_count, rating, comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (session_id, query_text, constraints, survivors, eliminated_count, rating, comment),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def record_tool_feedback(
    session_id: str,
    tool_name: str,
    current_tier: str,
    suggested_tier: Optional[str] = None,
    flag_type: Optional[str] = None,
    reason: Optional[str] = None,
) -> int:
    """Insert a tool feedback record. Returns the row ID."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO tool_feedback (session_id, tool_name, current_tier, suggested_tier, flag_type, reason) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, tool_name, current_tier, suggested_tier, flag_type, reason),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def record_event(
    session_id: str,
    event_type: str,
    payload: Optional[str] = None,
) -> int:
    """Insert a behavioral event. Returns the row ID."""
    conn = _get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO events (session_id, event_type, payload) VALUES (?, ?, ?)",
            (session_id, event_type, payload),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_stats() -> Dict[str, Any]:
    """Return aggregate feedback stats."""
    conn = _get_connection()
    try:
        total_search = conn.execute("SELECT COUNT(*) FROM search_feedback").fetchone()[0]
        thumbs_up = conn.execute("SELECT COUNT(*) FROM search_feedback WHERE rating='up'").fetchone()[0]
        thumbs_down = conn.execute("SELECT COUNT(*) FROM search_feedback WHERE rating='down'").fetchone()[0]
        total_tool = conn.execute("SELECT COUNT(*) FROM tool_feedback").fetchone()[0]
        total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        most_flagged = conn.execute(
            "SELECT tool_name, COUNT(*) as flag_count FROM tool_feedback GROUP BY tool_name ORDER BY flag_count DESC LIMIT 10"
        ).fetchall()

        oldest = conn.execute(
            "SELECT MIN(timestamp) FROM (SELECT timestamp FROM search_feedback UNION ALL SELECT timestamp FROM tool_feedback UNION ALL SELECT timestamp FROM events)"
        ).fetchone()[0]

        return {
            "total_search_feedback": total_search,
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down,
            "thumbs_down_rate": round(thumbs_down / max(total_search, 1), 3),
            "total_tool_flags": total_tool,
            "most_flagged_tools": [{"tool_name": r[0], "flag_count": r[1]} for r in most_flagged],
            "total_events": total_events,
            "feedback_since": oldest,
        }
    finally:
        conn.close()


def record_page_view(path: str, referrer: Optional[str] = None, user_agent: Optional[str] = None) -> None:
    """Record a page view. Called from middleware — must never block or raise."""
    try:
        conn = _get_connection()
        try:
            conn.execute(
                "INSERT INTO page_views (path, referrer, user_agent) VALUES (?, ?, ?)",
                (path, referrer, user_agent),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass  # never break a request for analytics


def get_page_view_stats() -> Dict[str, Any]:
    """Return page view analytics."""
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM page_views").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM page_views WHERE timestamp >= date('now')"
        ).fetchone()[0]
        by_page = conn.execute(
            "SELECT path, COUNT(*) as views FROM page_views "
            "GROUP BY path ORDER BY views DESC LIMIT 20"
        ).fetchall()
        by_referrer = conn.execute(
            "SELECT referrer, COUNT(*) as views FROM page_views "
            "WHERE referrer IS NOT NULL AND referrer != '' "
            "GROUP BY referrer ORDER BY views DESC LIMIT 10"
        ).fetchall()
        by_day = conn.execute(
            "SELECT date(timestamp) as day, COUNT(*) as views FROM page_views "
            "GROUP BY day ORDER BY day DESC LIMIT 14"
        ).fetchall()
        return {
            "total_views": total,
            "views_today": today,
            "by_page": [{"path": r[0], "views": r[1]} for r in by_page],
            "by_referrer": [{"referrer": r[0], "views": r[1]} for r in by_referrer],
            "by_day": [{"day": r[0], "views": r[1]} for r in by_day],
        }
    finally:
        conn.close()


def get_dashboard_data() -> Dict[str, Any]:
    """Return all data needed for the admin dashboard."""
    stats = get_stats()
    conn = _get_connection()
    try:
        recent_searches = conn.execute(
            "SELECT * FROM search_feedback ORDER BY id DESC LIMIT 20"
        ).fetchall()

        recent_flags = conn.execute(
            "SELECT * FROM tool_feedback ORDER BY id DESC LIMIT 10"
        ).fetchall()

        flag_details = conn.execute(
            "SELECT tool_name, flag_type, reason, COUNT(*) as count "
            "FROM tool_feedback GROUP BY tool_name, flag_type ORDER BY count DESC"
        ).fetchall()

        event_counts = conn.execute(
            "SELECT event_type, COUNT(*) as count "
            "FROM events GROUP BY event_type ORDER BY count DESC"
        ).fetchall()

        return {
            "stats": stats,
            "recent_searches": [dict(r) for r in recent_searches],
            "recent_flags": [dict(r) for r in recent_flags],
            "flag_details": [dict(r) for r in flag_details],
            "event_counts": [dict(r) for r in event_counts],
        }
    finally:
        conn.close()
