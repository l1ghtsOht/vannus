# --------------- Community Badges / Battle-Tested Signals ---------------
"""
Aggregate feedback into reputation badges displayed in search results:

    "SMB Favorite"       — High accept_rate in teams <10
    "Midwest Proven"     — Strong for regulated industries
    "Budget Champion"    — Consistently chosen at free/low tiers
    "Integration King"   — Most integration connections
    "Rising Star"        — Improving trend, growing adoption
    "Power User Pick"    — High rating from advanced users

Badges are auto-computed from learned_signals + feedback data.
"""

import logging
from typing import List, Dict

log = logging.getLogger("praxis.badges")

try:
    from .tools import Tool
    from .data import TOOLS
    from .learning import compute_tool_quality, load_learned_signals
    from .feedback import _load_feedback
except Exception:
    from tools import Tool
    from data import TOOLS
    from learning import compute_tool_quality, load_learned_signals
    from feedback import _load_feedback


# ======================================================================
# Badge definitions
# ======================================================================

_BADGE_DEFS = {
    "smb_favorite": {
        "label": "SMB Favorite",
        "icon": "⭐",
        "description": "Highly rated by small teams (< 10 people)",
    },
    "budget_champion": {
        "label": "Budget Champion",
        "icon": "💰",
        "description": "Consistently chosen by free/low-budget users",
    },
    "integration_king": {
        "label": "Integration King",
        "icon": "🔗",
        "description": "Most native integrations with other tools",
    },
    "rising_star": {
        "label": "Rising Star",
        "icon": "📈",
        "description": "Rapidly improving ratings and adoption",
    },
    "power_user_pick": {
        "label": "Power User Pick",
        "icon": "🚀",
        "description": "Highly rated by advanced users",
    },
    "compliance_ready": {
        "label": "Compliance Ready",
        "icon": "🛡️",
        "description": "Meets major compliance standards (HIPAA, SOC2, GDPR)",
    },
    "enterprise_grade": {
        "label": "Enterprise Grade",
        "icon": "🏢",
        "description": "Built for large teams with enterprise features",
    },
}


# ======================================================================
# Badge computation
# ======================================================================

def compute_badges_for_tool(tool: Tool) -> List[dict]:
    """Compute all applicable badges for a single tool."""
    badges = []
    quality = compute_tool_quality()
    metrics = quality.get(tool.name, {})
    feedback = _load_feedback()

    # ── SMB Favorite ──
    # High accept_rate + involved in small-team feedback
    smb_entries = [
        e for e in feedback
        if e.get("tool") == tool.name
        and (e.get("details", {}) or {}).get("team_size") in ("solo", "small", None)
    ]
    if metrics.get("accept_rate", 0) >= 0.6 and len(smb_entries) >= 2:
        badges.append(_BADGE_DEFS["smb_favorite"])
    elif metrics.get("accept_rate", 0) >= 0.5 and tool.skill_level == "beginner":
        # Proxy: beginner-friendly tools resonate with SMBs
        badges.append(_BADGE_DEFS["smb_favorite"])

    # ── Budget Champion ──
    pricing = getattr(tool, "pricing", {}) or {}
    if pricing.get("free_tier"):
        budget_entries = [
            e for e in feedback
            if e.get("tool") == tool.name and e.get("accepted")
        ]
        if len(budget_entries) >= 2 or tool.popularity >= 5:
            badges.append(_BADGE_DEFS["budget_champion"])

    # ── Integration King ──
    integrations = getattr(tool, "integrations", []) or []
    if len(integrations) >= 8:
        badges.append(_BADGE_DEFS["integration_king"])

    # ── Rising Star ──
    if metrics.get("recent_trend") == "improving":
        badges.append(_BADGE_DEFS["rising_star"])

    # ── Power User Pick ──
    advanced_entries = [
        e for e in feedback
        if e.get("tool") == tool.name
        and (e.get("details", {}) or {}).get("skill_level") == "advanced"
        and e.get("rating", 0) >= 4
    ]
    if len(advanced_entries) >= 2:
        badges.append(_BADGE_DEFS["power_user_pick"])
    elif tool.skill_level == "advanced" and metrics.get("avg_rating", 0) >= 4.0:
        badges.append(_BADGE_DEFS["power_user_pick"])

    # ── Compliance Ready ──
    compliance = getattr(tool, "compliance", []) or []
    major = {"hipaa", "soc2", "gdpr", "fedramp"}
    if len(set(c.lower() for c in compliance) & major) >= 2:
        badges.append(_BADGE_DEFS["compliance_ready"])

    # ── Enterprise Grade ──
    if "large" in (getattr(tool, "stack_roles", []) or []):
        badges.append(_BADGE_DEFS["enterprise_grade"])
    elif pricing.get("enterprise") and len(integrations) >= 5:
        badges.append(_BADGE_DEFS["enterprise_grade"])

    return badges


def compute_all_badges() -> Dict[str, List[dict]]:
    """Compute badges for all tools in the database.

    Returns: { "ToolName": [badge1, badge2, ...], ... }
    """
    result = {}
    for tool in TOOLS:
        badges = compute_badges_for_tool(tool)
        if badges:
            result[tool.name] = badges
    log.info("badges: computed for %d tools, %d total badges",
             len(result), sum(len(b) for b in result.values()))
    return result


def get_badges(tool_name: str) -> List[dict]:
    """Get badges for a specific tool by name."""
    for t in TOOLS:
        if t.name.lower() == tool_name.lower():
            return compute_badges_for_tool(t)
    return []
