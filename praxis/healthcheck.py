# --------------- Tool Health Monitor ---------------
"""
"Early warning system" for tool degradation.

For a given tool (or stack):
  • Check feedback trends from learned_signals.json
  • Check freshness / staleness
  • Check philosophy risk updates
  • Produce a health report with alerts & alternatives

Output example:
    "ChatGPT: accept_rate dropped 15% last month — consider Claude, Gemini"
"""

import logging
from typing import Optional, List

log = logging.getLogger("praxis.healthcheck")

try:
    from .tools import Tool
    from .data import TOOLS
    from .learning import compute_tool_quality, load_learned_signals
    from .engine import find_tools
    from .interpreter import interpret
except Exception:
    from tools import Tool
    from data import TOOLS
    from learning import compute_tool_quality, load_learned_signals
    from engine import find_tools
    from interpreter import interpret

try:
    from .philosophy import assess_freedom, assess_transparency
    _PHIL = True
except Exception:
    try:
        from philosophy import assess_freedom, assess_transparency
        _PHIL = True
    except Exception:
        _PHIL = False

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None


def tool_health(tool_name: str) -> dict:
    """Full health report for a single tool."""
    tool = _find_tool(tool_name)
    if not tool:
        return {"error": f"Tool '{tool_name}' not found"}

    quality = compute_tool_quality()
    metrics = quality.get(tool.name, {})
    signals = load_learned_signals()

    alerts = []
    status = "healthy"

    # ── Feedback trend ──
    trend = metrics.get("recent_trend", "unknown")
    accept_rate = metrics.get("accept_rate", None)
    avg_rating = metrics.get("avg_rating", None)
    total_fb = metrics.get("total_feedback", 0)

    if trend == "declining":
        alerts.append(f"⚠ Declining trend — accept_rate={accept_rate}, avg_rating={avg_rating}")
        status = "warning"
    if accept_rate is not None and accept_rate < 0.4 and total_fb >= 3:
        alerts.append(f"⚠ Low accept rate ({accept_rate:.0%}) — users frequently reject this tool")
        status = "critical" if accept_rate < 0.2 else "warning"
    if avg_rating is not None and avg_rating < 3.0 and total_fb >= 3:
        alerts.append(f"⚠ Low average rating ({avg_rating:.1f}/5)")
        status = "warning"

    # ── Freshness ──
    max_days = int(_cfg.get("tool_freshness_days", 90)) if _cfg else 90
    is_stale = getattr(tool, "is_stale", lambda d: True)(max_days)
    last_updated = getattr(tool, "last_updated", None)
    if is_stale:
        alerts.append(f"⚠ Stale metadata — last updated {last_updated or 'never'} (window: {max_days}d)")
        if status == "healthy":
            status = "stale"

    # ── Philosophy risk ──
    risk = {}
    if _PHIL:
        try:
            freedom = assess_freedom(tool)
            transparency = assess_transparency(tool)
            risk = {
                "flexibility_grade": freedom.get("grade"),
                "transparency_grade": transparency.get("grade"),
                "flexibility_score": freedom.get("score"),
                "transparency_score": transparency.get("score"),
            }
            if freedom.get("grade") in ("D", "F"):
                alerts.append(f"⚠ High lock-in risk (Flexibility: {freedom['grade']})")
            if transparency.get("grade") in ("D", "F"):
                alerts.append(f"⚠ Low transparency (Transparency: {transparency['grade']})")
        except Exception:
            pass

    # ── Alternatives ──
    alternatives = []
    if alerts:
        alternatives = _find_alternatives(tool)

    report = {
        "tool": tool.name,
        "status": status,
        "alerts": alerts,
        "metrics": {
            "accept_rate": accept_rate,
            "avg_rating": avg_rating,
            "total_feedback": total_fb,
            "recent_trend": trend,
        },
        "freshness": {
            "last_updated": last_updated,
            "is_stale": is_stale,
            "window_days": max_days,
        },
        "risk": risk,
        "alternatives": alternatives,
    }

    log.info("health_check: %s → status=%s, alerts=%d", tool.name, status, len(alerts))
    return report


def stack_health(tool_names: List[str]) -> dict:
    """Health report for an entire stack of tools."""
    reports = []
    overall_status = "healthy"
    for name in tool_names:
        r = tool_health(name)
        reports.append(r)
        if r.get("status") == "critical":
            overall_status = "critical"
        elif r.get("status") in ("warning", "stale") and overall_status == "healthy":
            overall_status = "warning"

    return {
        "overall_status": overall_status,
        "tools": reports,
        "total_alerts": sum(len(r.get("alerts", [])) for r in reports),
    }


# ── helpers ──

def _find_tool(name: str) -> Optional[Tool]:
    for t in TOOLS:
        if t.name.lower() == name.lower():
            return t
    return None


def _find_alternatives(tool: Tool, limit: int = 3) -> list:
    """Find alternatives in similar categories."""
    cats = tool.categories[:3]
    if not cats:
        return []
    query = " ".join(cats)
    struct = interpret(query)
    results = find_tools(struct, top_n=limit + 1)
    return [
        {"name": t.name, "categories": t.categories, "description": t.description[:80]}
        for t in results if t.name.lower() != tool.name.lower()
    ][:limit]
