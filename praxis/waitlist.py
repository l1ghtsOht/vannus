"""
waitlist.py — Founding-100 email waitlist for Pro+ pre-launch.

Stores submitted emails in praxis/waitlist.json (gitignored). Provides
add/count APIs that the /api/waitlist routes wrap. Anti-abuse via:
  - email format validation
  - rate-limit by IP (1 add per 60 seconds)
  - dedup (one entry per email; updates timestamp on resubmit)
  - cap at 1000 entries (prevents disk-fill via spam)

When Room ships and Pro+ checkout opens, the founding-100 logic
walks this file, sends the announcement email via Resend, and
applies a Stripe coupon for the first 100 emails to subscribe.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("praxis.waitlist")

_WAITLIST_PATH = Path(__file__).parent / "waitlist.json"
_RATE_LIMIT_PATH = Path(__file__).parent / ".waitlist_ratelimit.json"

# Limits
_MAX_ENTRIES = 1000
_RATE_LIMIT_SECONDS = 60
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _load() -> Dict[str, Any]:
    """Schema: {"entries": [{"email": "...", "added_at": "...", "source": "..."}, ...]}"""
    if not _WAITLIST_PATH.exists():
        return {"entries": []}
    try:
        with open(_WAITLIST_PATH) as f:
            data = json.load(f)
        if not isinstance(data, dict) or "entries" not in data:
            return {"entries": []}
        return data
    except (IOError, OSError, json.JSONDecodeError) as e:
        log.warning("waitlist load failed: %s — starting empty", e)
        return {"entries": []}


def _save(data: Dict[str, Any]) -> None:
    tmp_path = _WAITLIST_PATH.with_suffix(".json.tmp")
    try:
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, _WAITLIST_PATH)
    except (IOError, OSError) as e:
        log.error("waitlist save failed: %s", e)
        raise


def _check_rate_limit(client_ip: Optional[str]) -> bool:
    """Returns True if the request should proceed; False if rate-limited."""
    if not client_ip:
        return True
    try:
        if _RATE_LIMIT_PATH.exists():
            with open(_RATE_LIMIT_PATH) as f:
                rl = json.load(f)
        else:
            rl = {}
        now = time.time()
        # Prune entries older than 5 minutes (memory bound)
        rl = {ip: ts for ip, ts in rl.items() if now - ts < 300}
        last = rl.get(client_ip, 0)
        if now - last < _RATE_LIMIT_SECONDS:
            return False
        rl[client_ip] = now
        with open(_RATE_LIMIT_PATH, "w") as f:
            json.dump(rl, f)
        return True
    except Exception as e:
        log.warning("rate-limit check failed (allowing): %s", e)
        return True


def add_email(email: str, source: str = "pricing", client_ip: Optional[str] = None) -> Dict[str, Any]:
    """
    Add an email to the waitlist.

    Returns: {"ok": bool, "count": int, "error": str | None}
    """
    email = (email or "").strip().lower()
    if not email:
        return {"ok": False, "error": "email required"}
    if len(email) > 254:
        return {"ok": False, "error": "email too long"}
    if not _EMAIL_RE.match(email):
        return {"ok": False, "error": "invalid email format"}

    if not _check_rate_limit(client_ip):
        return {"ok": False, "error": "rate limited — please wait 60 seconds before resubmitting"}

    data = _load()
    entries = data["entries"]

    if len(entries) >= _MAX_ENTRIES:
        return {"ok": False, "error": "waitlist temporarily closed"}

    # Dedup — update timestamp if email already present
    existing = next((e for e in entries if e.get("email") == email), None)
    if existing:
        existing["last_seen_at"] = _now_iso()
        _save(data)
        return {"ok": True, "count": len(entries), "duplicate": True}

    entries.append({
        "email": email,
        "added_at": _now_iso(),
        "source": (source or "")[:32],
    })
    _save(data)
    return {"ok": True, "count": len(entries), "duplicate": False}


def get_count() -> int:
    """Return current waitlist size."""
    return len(_load()["entries"])


def get_summary(admin: bool = False) -> Dict[str, Any]:
    """
    Return waitlist summary.

    Args:
        admin: if True, include the actual email entries (for the admin
        dashboard). If False, returns only the count + remaining spots.
    """
    data = _load()
    entries = data["entries"]
    total = len(entries)
    remaining = max(0, 100 - total)
    out: Dict[str, Any] = {
        "count": total,
        "remaining_founding_spots": remaining,
        "founding_full": total >= 100,
    }
    if admin:
        out["entries"] = entries[-200:]  # last 200, most recent first
    return out
