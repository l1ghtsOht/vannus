# --------------- Monetisation & Community Layer ---------------
"""
Longer-term features:
    1. Affiliate / deal integration
    2. User-generated tool benchmarks
    3. Weekly SMB AI Digest subscription

These are the revenue and community moat builders.
"""

import json
import logging
import os
from datetime import datetime, date
from typing import Optional, List, Dict
from pathlib import Path

log = logging.getLogger("praxis.monetise")

try:
    from .tools import Tool
    from .data import TOOLS
    from .profile import UserProfile, load_profile
    from .learning import compute_tool_quality, load_learned_signals
except Exception:
    from tools import Tool
    from data import TOOLS
    from profile import UserProfile, load_profile
    from learning import compute_tool_quality, load_learned_signals

_BASE = Path(__file__).resolve().parent
_BENCHMARKS_PATH = _BASE / "benchmarks.json"
_SUBSCRIBERS_PATH = _BASE / "digest_subscribers.json"
_AFFILIATES_PATH = _BASE / "affiliates.json"


# ======================================================================
# 1. Affiliate / Deal Integration
# ======================================================================

# Curated affiliate data (manual for now; later: API integrations)
_AFFILIATE_DATA = {
    "chatgpt":         {"url": "https://chat.openai.com/", "promo": None, "commission": "N/A"},
    "jasper":          {"url": "https://jasper.ai/?ref=praxis", "promo": "7-day free trial", "commission": "30%"},
    "copy.ai":         {"url": "https://copy.ai/?ref=praxis", "promo": "2,000 free words/mo", "commission": "25%"},
    "midjourney":      {"url": "https://midjourney.com/", "promo": None, "commission": "N/A"},
    "canva ai":        {"url": "https://canva.com/?ref=praxis", "promo": "30-day Pro trial", "commission": "20%"},
    "grammarly":       {"url": "https://grammarly.com/?ref=praxis", "promo": "Free tier available", "commission": "20%"},
    "notion ai":       {"url": "https://notion.so/?ref=praxis", "promo": "Free for personal use", "commission": "15%"},
    "hubspot ai":      {"url": "https://hubspot.com/?ref=praxis", "promo": "Free CRM tier", "commission": "20%"},
    "zapier":          {"url": "https://zapier.com/?ref=praxis", "promo": "14-day free trial", "commission": "25%"},
    "github copilot":  {"url": "https://github.com/features/copilot", "promo": "Free for students/OSS", "commission": "N/A"},
    "semrush":         {"url": "https://semrush.com/?ref=praxis", "promo": "7-day free trial", "commission": "40%"},
}


def get_affiliate_info(tool_name: str) -> Optional[dict]:
    """Get affiliate link + promo for a tool."""
    data = _AFFILIATE_DATA.get(tool_name.lower())
    if not data:
        # Check enriched affiliates file
        enriched = _load_json(_AFFILIATES_PATH)
        data = enriched.get(tool_name.lower())
    if not data:
        return None
    return {
        "tool": tool_name,
        "try_url": data.get("url"),
        "current_promo": data.get("promo"),
    }


def enrich_recommendation_with_affiliate(tool_name: str, rec_dict: dict) -> dict:
    """Add affiliate info to an existing recommendation dict."""
    aff = get_affiliate_info(tool_name)
    if aff:
        rec_dict["try_url"] = aff["try_url"]
        rec_dict["current_promo"] = aff["current_promo"]
    return rec_dict


# ======================================================================
# 2. User-Generated Benchmarks
# ======================================================================

def submit_benchmark(
    tool_name: str,
    user_id: str,
    task: str,
    metrics: dict,
    notes: str = "",
) -> dict:
    """Submit a mini-benchmark for a tool.

    Args:
        tool_name: Which tool was tested
        user_id: Who submitted (profile_id)
        task: What was tested (e.g., "marketing copy gen on 10 prompts")
        metrics: { "accuracy": 8, "speed": 9, "quality": 7 } (1-10 scale)
        notes: Free-form observations

    Returns: Confirmation dict
    """
    benchmarks = _load_json(_BENCHMARKS_PATH)
    if tool_name not in benchmarks:
        benchmarks[tool_name] = []

    entry = {
        "user_id": user_id,
        "task": task,
        "metrics": metrics,
        "notes": notes,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }
    benchmarks[tool_name].append(entry)

    # Cap per tool
    if len(benchmarks[tool_name]) > 100:
        benchmarks[tool_name] = benchmarks[tool_name][-100:]

    _save_json(benchmarks, _BENCHMARKS_PATH)
    log.info("benchmark: %s by %s — task=%s", tool_name, user_id, task)
    return {"status": "recorded", "tool": tool_name, "entry": entry}


def get_benchmarks(tool_name: str) -> dict:
    """Get aggregated benchmark data for a tool."""
    all_benchmarks = _load_json(_BENCHMARKS_PATH)
    entries = all_benchmarks.get(tool_name, [])

    if not entries:
        return {"tool": tool_name, "benchmarks": 0, "aggregate": {}}

    # Aggregate metrics
    metric_sums: Dict[str, List[float]] = {}
    for e in entries:
        for k, v in (e.get("metrics") or {}).items():
            if isinstance(v, (int, float)):
                metric_sums.setdefault(k, []).append(v)

    aggregate = {
        k: round(sum(vals) / len(vals), 1)
        for k, vals in metric_sums.items()
    }

    return {
        "tool": tool_name,
        "benchmarks": len(entries),
        "aggregate": aggregate,
        "recent": entries[-5:],
    }


# ======================================================================
# 3. Weekly SMB AI Digest
# ======================================================================

def subscribe_digest(email: str, profile_id: Optional[str] = None) -> dict:
    """Subscribe to the weekly AI digest."""
    subs = _load_json(_SUBSCRIBERS_PATH)
    if not isinstance(subs, list):
        subs = []

    # Check duplicate
    for s in subs:
        if s.get("email", "").lower() == email.lower():
            return {"status": "already_subscribed", "email": email}

    subs.append({
        "email": email,
        "profile_id": profile_id,
        "subscribed_at": datetime.now().isoformat(timespec="seconds"),
        "active": True,
    })
    _save_json(subs, _SUBSCRIBERS_PATH)
    log.info("digest: new subscriber %s", email)
    return {"status": "subscribed", "email": email}


def unsubscribe_digest(email: str) -> dict:
    """Unsubscribe from the digest."""
    subs = _load_json(_SUBSCRIBERS_PATH)
    if not isinstance(subs, list):
        return {"status": "not_found"}

    for s in subs:
        if s.get("email", "").lower() == email.lower():
            s["active"] = False
            _save_json(subs, _SUBSCRIBERS_PATH)
            return {"status": "unsubscribed", "email": email}
    return {"status": "not_found"}


def generate_digest(profile_id: Optional[str] = None) -> dict:
    """Generate a digest preview (what the weekly email would contain).

    Content:
        • Top emerging tools (from recent feedback trends)
        • Workflow ideas for the user's profile
        • Vendor alerts (philosophy risk changes)
    """
    profile = load_profile(profile_id) if profile_id else None
    quality = compute_tool_quality()
    signals = load_learned_signals()

    # Emerging tools (improving trend)
    emerging = []
    for name, metrics in quality.items():
        if metrics.get("recent_trend") == "improving":
            emerging.append({
                "tool": name,
                "trend": "improving",
                "accept_rate": metrics.get("accept_rate"),
            })
    emerging.sort(key=lambda x: x.get("accept_rate", 0), reverse=True)

    # Top tools by accept rate
    top_tools = sorted(
        [{"tool": n, "accept_rate": m.get("accept_rate", 0), "avg_rating": m.get("avg_rating", 0)}
         for n, m in quality.items() if m.get("total_feedback", 0) >= 2],
        key=lambda x: x["accept_rate"],
        reverse=True,
    )[:5]

    # Profile-specific suggestions
    suggestions = []
    if profile and profile.goals:
        for goal in profile.goals[:2]:
            suggestions.append(f"Explore AI tools for '{goal}' — search at /search")

    digest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profile_id": profile_id,
        "sections": {
            "emerging_tools": emerging[:5],
            "top_rated": top_tools,
            "workflow_suggestions": suggestions,
            "tip_of_the_week": "Review your /profile-readiness score to find your next high-impact AI adoption.",
        },
    }
    return digest


def subscriber_count() -> int:
    """Return count of active subscribers."""
    subs = _load_json(_SUBSCRIBERS_PATH)
    if not isinstance(subs, list):
        return 0
    return sum(1 for s in subs if s.get("active", True))


# ======================================================================
# JSON helpers
# ======================================================================

def _load_json(path: Path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {} if "benchmark" in str(path) or "affiliate" in str(path) else []


def _save_json(data, path: Path):
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        log.error("Failed to save %s: %s", path, exc)
