"""
cost_monitor.py — LLM Spend Tracking & Admin Dashboard Data Layer
====================================================================

Pre-launch scaffold (May 2026). The Room module isn't shipping until
Week 2-3, so this records into the same SQLite store that storage.py
uses but is intentionally NOT YET WIRED into the LLM router. When Room
ships, the LLM-router middleware should call ``record_llm_call`` after
every model invocation.

What this module provides:

1. Schema migration — creates the ``llm_cost_events`` table on import.
2. Recording API — ``record_llm_call(...)`` writes a single event.
3. Aggregation API — daily / monthly / per-user / per-provider rollups.
4. Threshold alerts — ``check_alerts()`` fires Slack webhooks when
   any of these trip:
   - daily total spend > PRAXIS_COST_DAILY_ALERT_USD (default $25)
   - any single user > $5 in a day (auto-pause candidate)
   - monthly total > 80% of PRAXIS_COST_MONTHLY_BUDGET_USD
5. Dashboard payload — ``get_admin_summary()`` returns the JSON that
   ``/admin/costs.html`` renders.

Auth model: the FastAPI route registered in api.py for ``/admin/costs``
should require an admin token (``PRAXIS_ADMIN_TOKEN`` env var). This
module itself is auth-agnostic — that's a deliberate separation of
concerns.

Slack webhook: set ``PRAXIS_SLACK_COST_WEBHOOK`` to a Slack incoming
webhook URL to enable alerts. If unset, ``check_alerts()`` logs only.

Provider prices are kept in ``_PROVIDER_PRICES_USD_PER_M_TOKENS`` and
should be updated as model pricing changes (~quarterly maintenance).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.cost_monitor")


# ─── Provider pricing ─────────────────────────────────────────────────
# USD per 1M tokens. Update as providers change pricing (quarterly check).
# Format: provider -> {"input": $/M, "output": $/M}
# Sources: Gemini API pricing, OpenAI pricing, Anthropic pricing (May 2026).

_PROVIDER_PRICES_USD_PER_M_TOKENS: Dict[str, Dict[str, Dict[str, float]]] = {
    "google": {
        "gemini-2.5-flash":      {"input": 0.075, "output": 0.30},
        "gemini-2.5-pro":        {"input": 1.25,  "output": 5.00},
    },
    "openai": {
        "gpt-4o-mini":           {"input": 0.15,  "output": 0.60},
        "gpt-4o":                {"input": 2.50,  "output": 10.00},
    },
    "anthropic": {
        "claude-haiku-3.5":      {"input": 0.80,  "output": 4.00},
        "claude-sonnet-3.7":     {"input": 3.00,  "output": 15.00},
    },
}


def estimate_cost_usd(provider: str, model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a single LLM call from token counts."""
    prices = _PROVIDER_PRICES_USD_PER_M_TOKENS.get(provider, {}).get(model_id)
    if not prices:
        log.warning(
            "cost_monitor: no pricing data for %s/%s, returning 0",
            provider, model_id,
        )
        return 0.0
    return (
        (input_tokens / 1_000_000.0) * prices["input"]
        + (output_tokens / 1_000_000.0) * prices["output"]
    )


# ─── Storage ──────────────────────────────────────────────────────────

def _db_path() -> Path:
    """Same directory as tools.db for consistency with the rest of praxis."""
    return Path(__file__).parent / "tools.db"


def _ensure_schema() -> None:
    """Idempotent — create llm_cost_events table if it doesn't exist."""
    p = _db_path()
    conn = sqlite3.connect(p)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_cost_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,                  -- ISO8601 UTC
                event_date_utc TEXT NOT NULL,          -- YYYY-MM-DD for fast filter
                event_month_utc TEXT NOT NULL,         -- YYYY-MM for fast filter
                user_id TEXT,                          -- nullable (e.g., admin/system calls)
                user_tier TEXT,                        -- "free" | "pro" | "pro_plus" | "internal"
                provider TEXT NOT NULL,
                model_id TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                request_id TEXT,                       -- correlation w/ logs
                metadata TEXT                          -- JSON for arbitrary tags
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_date ON llm_cost_events (event_date_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_month ON llm_cost_events (event_month_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_user_date ON llm_cost_events (user_id, event_date_utc)")
        conn.commit()
    finally:
        conn.close()


# Auto-migrate on import (cheap idempotent)
try:
    _ensure_schema()
except Exception as e:
    log.warning("cost_monitor: schema init failed (%s) — module will function but writes may fail", e)


# ─── Recording API ─────────────────────────────────────────────────────

def record_llm_call(
    *,
    user_id: Optional[str],
    user_tier: Optional[str],
    provider: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: Optional[float] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Record one LLM call to the cost ledger.

    Call from the LLM router AFTER each model invocation. Failures here
    must not break the user-facing call — wrap in try/except in the caller.

    Args:
        user_id: Vannus user ID, or None for system calls
        user_tier: "free" | "pro" | "pro_plus" | "internal"
        provider: "google" | "openai" | "anthropic"
        model_id: e.g. "gemini-2.5-flash"
        input_tokens: prompt tokens consumed
        output_tokens: completion tokens generated
        cost_usd: optional pre-computed cost; if None, estimated from prices
        request_id: correlation ID for log tracing
        metadata: arbitrary tags (will be JSON-encoded)
    """
    if cost_usd is None:
        cost_usd = estimate_cost_usd(provider, model_id, input_tokens, output_tokens)

    now = datetime.now(timezone.utc)
    ts_utc = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    event_date = now.strftime("%Y-%m-%d")
    event_month = now.strftime("%Y-%m")

    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            INSERT INTO llm_cost_events
                (ts_utc, event_date_utc, event_month_utc, user_id, user_tier,
                 provider, model_id, input_tokens, output_tokens, cost_usd,
                 request_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts_utc, event_date, event_month, user_id, user_tier,
                provider, model_id, int(input_tokens), int(output_tokens),
                float(cost_usd), request_id,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ─── Aggregation API ───────────────────────────────────────────────────

def get_user_daily_spend(user_id: str, day: Optional[date] = None) -> float:
    """USD spent by a single user on a given date (default: today UTC)."""
    day = day or datetime.now(timezone.utc).date()
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_cost_events "
            "WHERE user_id = ? AND event_date_utc = ?",
            (user_id, day.isoformat()),
        )
        return float(cur.fetchone()[0] or 0)
    finally:
        conn.close()


def get_user_monthly_spend(user_id: str, year_month: Optional[str] = None) -> float:
    """USD spent by a single user in a given YYYY-MM (default: current month UTC)."""
    year_month = year_month or datetime.now(timezone.utc).strftime("%Y-%m")
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_cost_events "
            "WHERE user_id = ? AND event_month_utc = ?",
            (user_id, year_month),
        )
        return float(cur.fetchone()[0] or 0)
    finally:
        conn.close()


def get_daily_total(day: Optional[date] = None) -> float:
    """USD spent across all users on a given date (default: today UTC)."""
    day = day or datetime.now(timezone.utc).date()
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_cost_events "
            "WHERE event_date_utc = ?",
            (day.isoformat(),),
        )
        return float(cur.fetchone()[0] or 0)
    finally:
        conn.close()


def get_monthly_total(year_month: Optional[str] = None) -> float:
    """USD spent across all users in a given YYYY-MM (default: current month UTC)."""
    year_month = year_month or datetime.now(timezone.utc).strftime("%Y-%m")
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM llm_cost_events "
            "WHERE event_month_utc = ?",
            (year_month,),
        )
        return float(cur.fetchone()[0] or 0)
    finally:
        conn.close()


def get_top_users_today(limit: int = 10) -> List[Dict[str, Any]]:
    """Top-N users by today's USD spend (for the dashboard table)."""
    today = datetime.now(timezone.utc).date().isoformat()
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            """
            SELECT user_id, user_tier, SUM(cost_usd) as total_usd, COUNT(*) as call_count
            FROM llm_cost_events
            WHERE event_date_utc = ? AND user_id IS NOT NULL
            GROUP BY user_id
            ORDER BY total_usd DESC
            LIMIT ?
            """,
            (today, limit),
        )
        cols = ["user_id", "user_tier", "total_usd", "call_count"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def get_daily_series(days_back: int = 30) -> List[Dict[str, Any]]:
    """Daily total spend for the last N days (chart-friendly format)."""
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            """
            SELECT event_date_utc, SUM(cost_usd) as total_usd, COUNT(*) as call_count
            FROM llm_cost_events
            WHERE event_date_utc >= ?
            GROUP BY event_date_utc
            ORDER BY event_date_utc ASC
            """,
            ((datetime.now(timezone.utc).date() - timedelta(days=days_back)).isoformat(),),
        )
        cols = ["date", "total_usd", "call_count"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def get_provider_breakdown_today() -> List[Dict[str, Any]]:
    """USD by provider/model for today (cost diagnostic by upstream)."""
    today = datetime.now(timezone.utc).date().isoformat()
    conn = sqlite3.connect(_db_path())
    try:
        cur = conn.execute(
            """
            SELECT provider, model_id, SUM(cost_usd) as total_usd, COUNT(*) as call_count
            FROM llm_cost_events
            WHERE event_date_utc = ?
            GROUP BY provider, model_id
            ORDER BY total_usd DESC
            """,
            (today,),
        )
        cols = ["provider", "model_id", "total_usd", "call_count"]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# ─── Dashboard payload ──────────────────────────────────────────────────

def get_admin_summary() -> Dict[str, Any]:
    """Single JSON payload for /admin/costs.html to render."""
    daily_alert_threshold_usd = float(os.environ.get("PRAXIS_COST_DAILY_ALERT_USD", "25"))
    monthly_budget_usd = float(os.environ.get("PRAXIS_COST_MONTHLY_BUDGET_USD", "200"))

    today_total = get_daily_total()
    month_total = get_monthly_total()
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "thresholds": {
            "daily_alert_usd": daily_alert_threshold_usd,
            "monthly_budget_usd": monthly_budget_usd,
            "per_user_daily_max_usd": 5.0,
        },
        "summary": {
            "today_total_usd": round(today_total, 4),
            "today_alert_breached": today_total >= daily_alert_threshold_usd,
            "month_total_usd": round(month_total, 4),
            "month_pct_of_budget": (
                round((month_total / monthly_budget_usd) * 100.0, 1) if monthly_budget_usd > 0 else None
            ),
        },
        "top_users_today": get_top_users_today(10),
        "provider_breakdown_today": get_provider_breakdown_today(),
        "daily_series_30d": get_daily_series(30),
        "notes": [
            "Wired status: not yet — Room module not shipping until Week 2-3 of build.",
            "Internal-tier accounts (drake@vannus.co, jason@vannus.co) appear here for transparency but are not billed.",
            "Set PRAXIS_COST_DAILY_ALERT_USD and PRAXIS_COST_MONTHLY_BUDGET_USD env vars to tune thresholds.",
            "Set PRAXIS_SLACK_COST_WEBHOOK to enable Slack alerts.",
        ],
    }


# ─── Threshold alerts ───────────────────────────────────────────────────

def check_alerts(*, dry_run: bool = False) -> List[Dict[str, Any]]:
    """
    Run all threshold checks and (optionally) fire Slack webhooks.

    Call from a scheduled job (cron, Railway cron, or wherever) every
    5-15 minutes during launch period; can be relaxed to hourly later.

    Returns: list of fired alerts (dicts with severity, kind, payload).
    """
    fired: List[Dict[str, Any]] = []

    daily_threshold = float(os.environ.get("PRAXIS_COST_DAILY_ALERT_USD", "25"))
    monthly_budget = float(os.environ.get("PRAXIS_COST_MONTHLY_BUDGET_USD", "200"))
    per_user_daily_max = 5.0

    today_total = get_daily_total()
    if today_total >= daily_threshold:
        fired.append({
            "severity": "warning",
            "kind": "daily_total_exceeded",
            "today_total_usd": round(today_total, 4),
            "threshold_usd": daily_threshold,
        })

    month_total = get_monthly_total()
    if monthly_budget > 0 and month_total >= 0.80 * monthly_budget:
        fired.append({
            "severity": "warning",
            "kind": "monthly_budget_80_pct",
            "month_total_usd": round(month_total, 4),
            "budget_usd": monthly_budget,
            "pct": round((month_total / monthly_budget) * 100.0, 1),
        })

    # Per-user daily ceiling — auto-pause candidate
    for u in get_top_users_today(50):
        if u["total_usd"] >= per_user_daily_max:
            fired.append({
                "severity": "critical",
                "kind": "user_daily_max_exceeded",
                "user_id": u["user_id"],
                "user_tier": u.get("user_tier"),
                "total_usd": round(u["total_usd"], 4),
                "threshold_usd": per_user_daily_max,
                "recommendation": "auto_pause_account_pending_review",
            })

    if not fired:
        return []

    webhook_url = os.environ.get("PRAXIS_SLACK_COST_WEBHOOK", "").strip()
    if dry_run or not webhook_url:
        for f in fired:
            log.warning("cost_monitor alert (NOT sent — no webhook): %s", f)
        return fired

    # Send to Slack
    try:
        import urllib.request
        for f in fired:
            severity_icon = "🚨" if f["severity"] == "critical" else "⚠️"
            text = f"{severity_icon} Vannus cost alert: {f['kind']} — {json.dumps(f, sort_keys=True)}"
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps({"text": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).read()
    except Exception as e:
        log.error("cost_monitor: failed to fire Slack webhook — %s", e)

    return fired
