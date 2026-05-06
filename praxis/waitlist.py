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


def _notify_new_signup(email: str, source: str, count: int) -> None:
    """
    Optional outbound notification when someone joins the waitlist.

    Two notification channels, both configured via env vars (set either,
    both, or neither — silent if neither is set):

    1. Slack incoming webhook: VANNUS_WAITLIST_SLACK_WEBHOOK
       Posts "New Vannus waitlist signup: <email> (source=<src>, total=<n>)"

    2. Email-via-Resend: VANNUS_WAITLIST_NOTIFY_EMAIL +
       RESEND_API_KEY env vars. Sends a plain-text email to the
       configured address (typically drake@vannus.co) per signup.

    Both fail silently — the signup itself must succeed even if
    notification fails.
    """
    import urllib.request

    # Slack notification
    slack_url = os.environ.get("VANNUS_WAITLIST_SLACK_WEBHOOK", "").strip()
    if slack_url:
        try:
            text = f"🌱 New Vannus Founding-100 signup: `{email}` (source={source}, total={count}/100)"
            req = urllib.request.Request(
                slack_url,
                data=json.dumps({"text": text}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as e:
            log.warning("waitlist Slack notify failed: %s", e)

    # Email-via-Resend notification.
    # The reply_to is set to the signup's email so when Drake hits "Reply"
    # in his inbox, the reply goes directly to the person who signed up —
    # no copy-paste required. Drake can individualize the welcome reply
    # however he wants.
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    notify_email = os.environ.get("VANNUS_WAITLIST_NOTIFY_EMAIL", "").strip()
    if resend_key and notify_email:
        try:
            payload = {
                # Per Resend's guidance: avoid "noreply@" — it lowers
                # inbox trust because recipients can't provide feedback.
                # Use a real address (hello@vannus.co) backed by a
                # Namecheap forwarder. The reply_to below means hitting
                # Reply still routes to the signup person.
                "from": "Vannus <hello@vannus.co>",
                "to": [notify_email],
                "reply_to": email,  # ← reply goes straight to the signup
                "subject": f"🌱 Founding-100 signup #{count}: {email}",
                "text": (
                    f"A new email joined the Vannus Founding-100 waitlist.\n\n"
                    f"==================================================\n"
                    f"Email:                {email}\n"
                    f"Source:               {source}\n"
                    f"Signup number:        #{count} of 100\n"
                    f"Remaining spots:      {max(0, 100 - count)}\n"
                    f"==================================================\n\n"
                    f"To reply directly to this person, just hit Reply.\n"
                    f"This email's Reply-To is set to {email}.\n\n"
                    f"To see all waitlist entries (admin):\n"
                    f"  curl -H 'X-Admin-Token: $PRAXIS_ADMIN_TOKEN' \\\n"
                    f"       https://vannus.co/admin/api/waitlist\n"
                ),
            }
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as e:
            log.warning("waitlist Resend email notify failed: %s", e)


def add_email(email: str, source: str = "pricing", client_ip: Optional[str] = None) -> Dict[str, Any]:
    """
    Add an email to the waitlist.

    Returns: {"ok": bool, "count": int, "error": str | None, "duplicate": bool}

    Side effects (best-effort, never block the success response):
      - Persists to praxis/waitlist.json
      - Optional: Slack webhook ping (VANNUS_WAITLIST_SLACK_WEBHOOK)
      - Optional: Resend email to drake@vannus.co or wherever
        VANNUS_WAITLIST_NOTIFY_EMAIL points (also requires RESEND_API_KEY)
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
        # No notify for duplicates — Drake doesn't need to know about resubmits
        return {"ok": True, "count": len(entries), "duplicate": True}

    entries.append({
        "email": email,
        "added_at": _now_iso(),
        "source": (source or "")[:32],
    })
    _save(data)

    # Best-effort outbound notification (Slack and/or Resend email)
    try:
        _notify_new_signup(email, (source or "")[:32], len(entries))
    except Exception as e:
        log.warning("waitlist notify pipeline failed (non-fatal): %s", e)

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
