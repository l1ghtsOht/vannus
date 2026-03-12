# ---------- Query Failure Tracking & Diagnostics ----------
"""
Records queries that return zero or very-low-score results so we can:
  1. Identify gaps in tool coverage
  2. Improve NLP / synonym dictionaries
  3. Spot trending needs that aren't served yet

Data format (query_failures.json):
[
  {
    "query": "best AI for underwater basket weaving",
    "timestamp": "2026-02-20T14:35:22",
    "results_count": 0,
    "top_score": 0,
    "interpreted": { ... }   // optional parsed intent
  },
  ...
]
"""

import json
import logging
from datetime import datetime
from pathlib import Path

log = logging.getLogger("praxis.diagnostics")

# --- Persistence paths ---
try:
    _BASE = Path(__file__).resolve().parent
except Exception:
    _BASE = Path(".")
_FAILURES_PATH = _BASE / "query_failures.json"

# Configurable thresholds
MIN_RESULTS_THRESHOLD = 1        # fewer than this → logged as failure
LOW_SCORE_THRESHOLD = 3.0         # top-score below this → logged as low-confidence


# ------------------------------------------------------------------
# Record a failure / low-confidence query
# ------------------------------------------------------------------
def record_failure(query, results_count: int, top_score: float = 0.0,
                   interpreted: dict = None, *, path: Path = None):
    """Persist a query failure entry to JSON."""
    path = path or _FAILURES_PATH
    entry = {
        "query": query if isinstance(query, str) else str(query),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "results_count": results_count,
        "top_score": round(top_score, 2),
    }
    if interpreted:
        entry["interpreted"] = interpreted

    entries = _load(path)
    entries.append(entry)

    # Cap at 500 to prevent unbounded growth
    if len(entries) > 500:
        entries = entries[-500:]

    _save(entries, path)
    log.info("query_failure recorded: %r → %d results (top_score=%.1f)",
             entry["query"], results_count, top_score)


# ------------------------------------------------------------------
# Retrieve failure log
# ------------------------------------------------------------------
def get_failures(limit: int = 50, *, path: Path = None):
    """Return the most recent `limit` failure entries, newest first."""
    path = path or _FAILURES_PATH
    entries = _load(path)
    entries.reverse()
    return entries[:limit]


def get_failure_summary(*, path: Path = None):
    """Aggregate stats for the diagnostics dashboard."""
    path = path or _FAILURES_PATH
    entries = _load(path)
    if not entries:
        return {"total_failures": 0, "zero_result_count": 0,
                "low_score_count": 0, "top_missed_queries": []}

    zero = [e for e in entries if e.get("results_count", 0) == 0]
    low = [e for e in entries if 0 < e.get("results_count", 0) and
           e.get("top_score", 0) < LOW_SCORE_THRESHOLD]

    # Find most-frequently-failing query strings
    from collections import Counter
    freq = Counter(e.get("query", "").lower().strip() for e in entries)
    top_missed = [{"query": q, "count": c} for q, c in freq.most_common(10)]

    return {
        "total_failures": len(entries),
        "zero_result_count": len(zero),
        "low_score_count": len(low),
        "top_missed_queries": top_missed,
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _load(path: Path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Failed to load %s: %s", path, exc)
    return []


def _save(entries: list, path: Path):
    try:
        path.write_text(json.dumps(entries, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    except Exception as exc:
        log.error("Failed to save %s: %s", path, exc)
