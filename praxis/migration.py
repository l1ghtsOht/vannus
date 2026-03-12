# --------------- Migration Assistant ---------------
"""
Step-by-step migration planner for switching tools.

Input: Current tool + desired outcome (or target tool).
Output:
    • Pre-migration checklist (data export, backup)
    • Step-by-step switch guide
    • Data portability analysis (from philosophy)
    • Transition alternatives (tools to bridge gaps)
    • Risk assessment during transition
    • Estimated migration timeline

Pulls from philosophy portability scores, integration metadata, and
learned feedback trends.
"""

import logging
from typing import Optional, List

log = logging.getLogger("praxis.migration")

try:
    from .tools import Tool
    from .data import TOOLS
    from .profile import UserProfile, load_profile
    from .engine import find_tools
    from .interpreter import interpret
except Exception:
    from tools import Tool
    from data import TOOLS
    from profile import UserProfile, load_profile
    from engine import find_tools
    from interpreter import interpret

try:
    from .philosophy import assess_freedom, get_tool_intel
    _PHIL = True
except Exception:
    try:
        from philosophy import assess_freedom, get_tool_intel
        _PHIL = True
    except Exception:
        _PHIL = False


# ======================================================================
# Migration complexity scoring
# ======================================================================

_LOCK_IN_DAYS = {"low": 3, "medium": 7, "high": 21, "critical": 30}
_SKILL_EFFORT = {"beginner": "low", "intermediate": "medium", "advanced": "high"}


def migration_plan(
    from_tool: str,
    to_tool: Optional[str] = None,
    desired_outcome: Optional[str] = None,
    profile: Optional[UserProfile] = None,
    profile_id: Optional[str] = None,
) -> dict:
    """Generate a full migration plan.

    Args:
        from_tool: Name of the tool to migrate away from
        to_tool: Name of the target tool (optional)
        desired_outcome: What the user wants to achieve (if no target tool)
        profile: User profile for context
        profile_id: Alternatively load by ID

    Returns: Full migration plan dict
    """
    if not profile and profile_id:
        profile = load_profile(profile_id)

    source = _find_tool(from_tool)
    if not source:
        return {"error": f"Tool '{from_tool}' not found in database"}

    # Resolve target tool
    target = None
    if to_tool:
        target = _find_tool(to_tool)
        if not target:
            return {"error": f"Target tool '{to_tool}' not found"}
    elif desired_outcome:
        # Find best alternative via search
        struct = interpret(desired_outcome)
        results = find_tools(struct, top_n=3, profile=profile)
        candidates = [r for r in results if r.name.lower() != source.name.lower()]
        if candidates:
            target = candidates[0]
    else:
        # Suggest alternatives in same categories
        query = " ".join(source.categories[:3]) + " alternative"
        struct = interpret(query)
        results = find_tools(struct, top_n=3, profile=profile)
        candidates = [r for r in results if r.name.lower() != source.name.lower()]
        if candidates:
            target = candidates[0]

    if not target:
        return {"error": "Could not find a suitable migration target. Specify a target tool or desired outcome."}

    # ── Portability analysis ──
    source_portability = _portability_analysis(source)
    target_portability = _portability_analysis(target)

    # ── Migration steps ──
    steps = _build_migration_steps(source, target, profile)

    # ── Risk assessment ──
    risks = _migration_risks(source, target)

    # ── Timeline estimate ──
    lock_in = source_portability.get("lock_in_level", "medium")
    est_days = _LOCK_IN_DAYS.get(lock_in, 7)
    if profile and profile.team_size in ("medium", "large"):
        est_days = int(est_days * 1.5)  # larger teams take longer

    # ── Transition tools (bridges) ──
    bridges = _transition_bridges(source, target)

    # ── Integration overlap ──
    source_integ = set(i.lower() for i in (source.integrations or []))
    target_integ = set(i.lower() for i in (target.integrations or []))
    shared = sorted(source_integ & target_integ)
    lost = sorted(source_integ - target_integ)
    gained = sorted(target_integ - source_integ)

    plan = {
        "from_tool": source.name,
        "to_tool": target.name,
        "migration_complexity": lock_in,
        "estimated_days": est_days,
        "pre_migration_checklist": _pre_migration_checklist(source),
        "steps": steps,
        "risks": risks,
        "portability": {
            "source": source_portability,
            "target": target_portability,
        },
        "integrations": {
            "shared": shared[:10],
            "lost": lost[:10],
            "gained": gained[:10],
        },
        "transition_bridges": bridges,
        "post_migration": [
            f"Verify all data migrated correctly from {source.name}",
            f"Test {target.name} with your core use cases for 1-2 weeks",
            f"Gather team feedback before fully decommissioning {source.name}",
            "Update your Praxis profile with the new tool",
        ],
    }

    log.info("migration: %s → %s, complexity=%s, est_days=%d",
             source.name, target.name, lock_in, est_days)
    return plan


# ======================================================================
# Internal helpers
# ======================================================================

def _portability_analysis(tool: Tool) -> dict:
    """Analyse data portability for a tool."""
    result = {
        "tool": tool.name,
        "lock_in_level": "medium",
        "data_export": "unknown",
        "api_available": False,
    }

    if _PHIL:
        try:
            intel = get_tool_intel(tool)
            freedom = assess_freedom(tool)
            result["lock_in_level"] = intel.get("lock_in", "medium")
            result["data_export"] = intel.get("portability", "Check vendor documentation")
            result["freedom_grade"] = freedom.get("grade")
            result["freedom_score"] = freedom.get("score")
        except Exception:
            pass

    # Heuristic API detection
    integrations = getattr(tool, "integrations", []) or []
    if len(integrations) >= 5:
        result["api_available"] = True

    return result


def _build_migration_steps(source: Tool, target: Tool, profile: Optional[UserProfile]) -> List[dict]:
    """Build ordered migration steps."""
    steps = [
        {
            "step": 1,
            "title": "Audit current usage",
            "detail": f"Document all workflows, automations, and integrations using {source.name}. "
                      f"Export your data (conversations, files, settings).",
        },
        {
            "step": 2,
            "title": "Set up target tool",
            "detail": f"Create your {target.name} account. Start with free tier if available. "
                      f"Import basic data/settings.",
        },
        {
            "step": 3,
            "title": "Parallel testing",
            "detail": f"Run {source.name} and {target.name} side-by-side for 1 week. "
                      f"Test your top 3 use cases.",
        },
    ]

    # Integration rewiring
    source_integ = set(i.lower() for i in (source.integrations or []))
    target_integ = set(i.lower() for i in (target.integrations or []))
    lost = source_integ - target_integ

    if lost:
        steps.append({
            "step": 4,
            "title": "Rewire integrations",
            "detail": f"Reconnect these integrations that {target.name} doesn't natively support: "
                      f"{', '.join(sorted(lost)[:5])}. Use Zapier/Make as bridge if needed.",
        })

    steps.append({
        "step": len(steps) + 1,
        "title": "Full migration",
        "detail": f"Move remaining workflows to {target.name}. Update team access/permissions. "
                  f"Cancel {source.name} subscription after grace period.",
    })

    steps.append({
        "step": len(steps) + 1,
        "title": "Post-migration review",
        "detail": f"After 2 weeks on {target.name}, evaluate: Is productivity maintained? "
                  f"Are there gaps? Rate both tools at /feedback.",
    })

    return steps


def _migration_risks(source: Tool, target: Tool) -> List[dict]:
    """Identify migration risks."""
    risks = []

    # Data loss risk
    if _PHIL:
        try:
            intel = get_tool_intel(source)
            if intel.get("lock_in") in ("high", "critical"):
                risks.append({
                    "risk": "Data lock-in",
                    "severity": "high",
                    "detail": f"{source.name} has {intel.get('lock_in')} lock-in. "
                              f"Data export may be limited: {intel.get('portability', 'check docs')}",
                    "mitigation": "Export all data before cancelling. Keep backup for 90 days.",
                })
        except Exception:
            pass

    # Skill gap risk
    if source.skill_level != target.skill_level:
        risks.append({
            "risk": "Skill gap",
            "severity": "medium",
            "detail": f"{source.name} is {source.skill_level}-level; "
                      f"{target.name} requires {target.skill_level} skills",
            "mitigation": "Budget time for training. Check vendor tutorials.",
        })

    # Integration disruption
    source_integ = set(i.lower() for i in (source.integrations or []))
    target_integ = set(i.lower() for i in (target.integrations or []))
    lost = source_integ - target_integ
    if len(lost) > 3:
        risks.append({
            "risk": "Integration disruption",
            "severity": "medium",
            "detail": f"Losing {len(lost)} integrations: {', '.join(sorted(lost)[:5])}",
            "mitigation": "Map each lost integration to a Zapier/Make alternative before switching.",
        })

    if not risks:
        risks.append({
            "risk": "Low risk migration",
            "severity": "low",
            "detail": "No major risk factors detected",
            "mitigation": "Standard parallel-run approach recommended.",
        })

    return risks


def _transition_bridges(source: Tool, target: Tool) -> List[dict]:
    """Suggest tools that bridge the gap during migration."""
    bridges = []

    # Zapier/Make for integration gaps
    source_integ = set(i.lower() for i in (source.integrations or []))
    target_integ = set(i.lower() for i in (target.integrations or []))
    if source_integ - target_integ:
        zapier = _find_tool("Zapier")
        if zapier:
            bridges.append({
                "tool": "Zapier",
                "purpose": "Bridge integration gaps during transition",
                "est_cost": "$19/mo (starter)",
            })

    return bridges


def _find_tool(name: str) -> Optional[Tool]:
    for t in TOOLS:
        if t.name.lower() == name.lower():
            return t
    return None


def _pre_migration_checklist(source: Tool) -> List[str]:
    """Generate a pre-migration checklist based on the source tool."""
    items = [
        f"Export all data from {source.name} (conversations, files, settings)",
        f"Document current {source.name} workflows and automations",
        f"List all integrations connected to {source.name}",
        "Back up exported data to a separate location",
        "Notify team members of the planned migration timeline",
    ]

    if _PHIL:
        try:
            intel = get_tool_intel(source)
            if intel.get("lock_in") in ("high", "critical"):
                items.insert(0, f"⚠ HIGH LOCK-IN: Review {source.name}'s data export limitations before proceeding")
            portability = intel.get("portability", "")
            if portability and portability != "Check vendor documentation":
                items.append(f"Portability note: {portability}")
        except Exception:
            pass

    compliance = getattr(source, "compliance", []) or []
    if compliance:
        items.append(f"Ensure target tool meets these compliance requirements: {', '.join(compliance)}")

    return items
