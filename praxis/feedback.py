import json
import os
import logging
from datetime import datetime, timezone
log = logging.getLogger("praxis.feedback")
try:
    from .usage import increment as increment_usage
except Exception:
    try:
        from usage import increment as increment_usage
    except Exception:
        def increment_usage(*args, **kwargs):
            # fallback no-op if usage module isn't available
            return None

FEEDBACK_FILE = "feedback.json"


def _load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_feedback(entries):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def record_feedback(query: str, tool_name: str, accepted: bool = None, rating: int = None, details: dict = None):
    """Append a feedback entry to the local feedback file.

    Backwards-compatible: `accepted` may be provided (bool). If not provided
    but `rating` is provided, `accepted` will be inferred as `rating >= 6`.
    """
    entries = _load_feedback()

    # infer accepted if not explicitly provided
    if accepted is None and rating is not None:
        accepted = bool(int(rating) >= 6)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query": query,
        "tool": tool_name,
        "accepted": bool(accepted) if accepted is not None else None,
        "rating": int(rating) if rating is not None else None,
        "details": details or None,
    }
    entries.append(entry)
    _save_feedback(entries)
    log.info("feedback: query=%r tool=%s accepted=%s rating=%s", entry["query"], tool_name, entry["accepted"], entry["rating"])
    # If accepted, increment the persisted usage/popularity for the tool
    try:
        if entry.get("accepted") and tool_name:
            increment_usage(tool_name, 1)
    except Exception:
        # non-fatal if usage increment fails
        pass

    # Auto-learn: trigger learning cycle every N feedback entries
    _maybe_auto_learn(len(entries))


def summary():
    """Return a simple summary (counts) of feedback stored.

    Returns: dict like {"total": N, "accepted": X, "rejected": Y}
    """
    entries = _load_feedback()
    total = len(entries)
    # Count accepted based on explicit flag, or infer from rating >=6
    accepted = 0
    for e in entries:
        if e.get("accepted"):
            accepted += 1
        else:
            r = e.get("rating")
            if r is not None and int(r) >= 6:
                accepted += 1
    rejected = total - accepted
    return {"total": total, "accepted": accepted, "rejected": rejected}


def get_entries(limit: int = 20):
    """Return the most recent feedback entries (newest first).

    Args:
        limit: max number of entries to return.
    """
    entries = _load_feedback()
    # entries appended over time; return reversed for newest-first
    return list(reversed(entries))[:limit]


# ======================================================================
# Auto-learn — runs learning cycle every N feedback entries
# ======================================================================

_last_learn_count = 0  # tracks feedback count at last auto-learn


def _maybe_auto_learn(current_count: int):
    """Trigger a learning cycle if enough new feedback has accumulated."""
    global _last_learn_count
    try:
        try:
            from . import config as _cfg
        except Exception:
            import config as _cfg
        threshold = _cfg.get("auto_learn_threshold", 10)
    except Exception:
        threshold = 10

    if current_count - _last_learn_count >= threshold:
        try:
            try:
                from .learning import run_learning_cycle
            except Exception:
                from learning import run_learning_cycle
            run_learning_cycle()
            _last_learn_count = current_count
            log.info("auto-learn: triggered at %d entries (threshold=%d)", current_count, threshold)
        except Exception as e:
            log.warning("auto-learn failed: %s", e)
