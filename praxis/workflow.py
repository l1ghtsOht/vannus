# --------------- Workflow Advisor ---------------
"""
Generates sequenced, multi-step workflow recommendations — not just tool
lists but actionable playbooks:

    Step 1: Use Tool A for lead gen (est. 2 hrs/week saved)
    Step 2: Pipe output to Tool B for nurture sequences
    Step 3: Analyze with Tool C for conversion tracking

Each workflow includes:
    • Ordered steps with role/purpose
    • Estimated time savings per step
    • Total cost estimate
    • Migration notes (from current tools to new ones)
    • Integration wiring instructions
    • Feedback hook: "Did this workflow save you hours?"

Hooks into compose_stack() for tool selection, explain_stack() for
narrative, and philosophy for risk overlay.
"""

import logging
from typing import Optional, List, Dict

log = logging.getLogger("praxis.workflow")

try:
    from .tools import Tool
    from .profile import UserProfile, load_profile
    from .engine import find_tools, score_tool
    from .interpreter import interpret
    from .stack import compose_stack
    from .explain import explain_tool
    from .data import TOOLS
except Exception:
    from tools import Tool
    from profile import UserProfile, load_profile
    from engine import find_tools, score_tool
    from interpreter import interpret
    from stack import compose_stack
    from explain import explain_tool
    from data import TOOLS

try:
    from .philosophy import assess_freedom, assess_transparency
    _PHIL_AVAILABLE = True
except Exception:
    try:
        from philosophy import assess_freedom, assess_transparency
        _PHIL_AVAILABLE = True
    except Exception:
        _PHIL_AVAILABLE = False


# ======================================================================
# Workflow role → action verb mapping
# ======================================================================
_ROLE_VERBS = {
    "primary":        "Execute core task with",
    "companion":      "Enhance output using",
    "infrastructure": "Connect & automate via",
    "analytics":      "Measure & optimise with",
    "lead_gen":       "Generate leads with",
    "nurture":        "Nurture prospects via",
    "analysis":       "Analyse results in",
    "creation":       "Create content with",
    "distribution":   "Distribute through",
    "monitoring":     "Monitor performance via",
}

# Category → estimated hours saved per week (conservative SMB estimates)
_TIME_SAVINGS = {
    "writing":       3.0,
    "design":        2.5,
    "marketing":     2.0,
    "automation":    4.0,
    "analytics":     1.5,
    "coding":        5.0,
    "research":      2.0,
    "support":       3.0,
    "sales":         2.5,
    "scheduling":    1.0,
    "data":          2.0,
    "seo":           1.5,
    "social media":  2.0,
    "email":         1.5,
    "video":         3.0,
    "audio":         2.0,
}


# ======================================================================
# Public API
# ======================================================================

def suggest_workflow(
    query: str,
    profile: Optional[UserProfile] = None,
    profile_id: Optional[str] = None,
    existing_tools: Optional[List[str]] = None,
    max_steps: int = 5,
) -> dict:
    """Build a sequenced workflow for a given goal + user context.

    Returns:
        {
            "goal": str,
            "steps": [
                {
                    "step": 1,
                    "action": "Generate leads with HubSpot AI",
                    "tool": { name, description, pricing, ... },
                    "role": "lead_gen",
                    "why": "Directly addresses your sales intent ...",
                    "est_hours_saved_per_week": 2.5,
                    "migration_notes": ["Export contacts from current CRM ...", ...],
                    "integration_tip": "Connects natively with Step 2 tool"
                },
                ...
            ],
            "total_monthly_cost": "$79/month (estimated)",
            "total_hours_saved_per_week": 8.5,
            "risk_summary": { ... },
            "alternatives": [...],
            "feedback_prompt": "Did this workflow save you hours? Rate each step."
        }
    """
    # Resolve profile
    if not profile and profile_id:
        profile = load_profile(profile_id)

    # Merge existing_tools into profile context
    if existing_tools and profile:
        combined = list(set(profile.existing_tools + existing_tools))
        profile.existing_tools = combined
    elif existing_tools and not profile:
        profile = UserProfile(existing_tools=existing_tools)

    # Interpret the query
    struct = interpret(query)
    intent = struct.get("intent", "")
    raw = struct.get("raw", query)

    # Use compose_stack to get the tool selection
    stack_result = compose_stack(
        struct,
        profile=profile,
        stack_size=min(max_steps, 5),
    )

    stack_entries = stack_result.get("stack", [])
    if not stack_entries:
        # Fallback: use find_tools directly
        tools = find_tools(struct, top_n=max_steps, profile=profile)
        stack_entries = [{"tool": t, "role": _infer_role(t, i)} for i, t in enumerate(tools)]

    # Build workflow steps
    steps = []
    total_cost = 0.0
    total_hours = 0.0

    for idx, entry in enumerate(stack_entries[:max_steps]):
        tool = entry["tool"]
        role = entry["role"]

        # Explain why this tool is in the workflow
        expl = explain_tool(tool, struct, profile)

        # Estimate time savings
        hours = _estimate_time_savings(tool, role)
        total_hours += hours

        # Estimate cost
        cost = _estimate_monthly_cost(tool, profile)
        if cost is not None:
            total_cost += cost

        # Migration notes (if user has existing tools)
        migration = _migration_notes(tool, profile)

        # Integration tip (how this connects to prev/next step)
        integration_tip = _integration_tip(
            tool, stack_entries, idx
        )

        # Risk overlay
        risk = {}
        if _PHIL_AVAILABLE:
            try:
                freedom = assess_freedom(tool)
                transparency = assess_transparency(tool)
                risk = {
                    "flexibility_grade": freedom.get("grade"),
                    "transparency_grade": transparency.get("grade"),
                }
                if freedom.get("grade") in ("D", "F"):
                    risk["warning"] = "Elevated lock-in risk — review exit strategy"
            except Exception:
                pass

        action_verb = _ROLE_VERBS.get(role, _ROLE_VERBS.get("primary", "Use"))

        step = {
            "step": idx + 1,
            "action": f"{action_verb} {tool.name}",
            "tool": {
                "name": tool.name,
                "description": tool.description,
                "pricing": tool.pricing,
                "categories": tool.categories,
                "skill_level": tool.skill_level,
                "url": tool.url,
            },
            "role": role,
            "why": expl.get("summary", ""),
            "reasons": expl.get("reasons", [])[:3],
            "est_hours_saved_per_week": round(hours, 1),
            "est_monthly_cost": f"${cost:.0f}" if cost else "Free / varies",
            "migration_notes": migration,
            "integration_tip": integration_tip,
            "risk": risk,
        }
        steps.append(step)

    # Risk summary across the whole workflow
    risk_summary = _workflow_risk_summary(stack_entries)

    # Alternatives not in the workflow
    alt_tools = stack_result.get("alternatives", [])
    alternatives = [
        {"name": t.name, "categories": t.categories, "description": t.description[:80]}
        for t in alt_tools[:5]
    ]

    cost_str = f"~${total_cost:.0f}/month" if total_cost > 0 else "Free tier / varies"

    result = {
        "goal": raw,
        "intent": intent,
        "steps": steps,
        "total_monthly_cost": cost_str,
        "total_hours_saved_per_week": round(total_hours, 1),
        "risk_summary": risk_summary,
        "alternatives": alternatives,
        "feedback_prompt": "Did this workflow save you hours? Rate each step at /feedback.",
    }

    log.info("workflow: query=%r → %d steps, est_savings=%.1f hrs/wk, cost=%s",
             raw, len(steps), total_hours, cost_str)
    return result


# ======================================================================
# Internal helpers
# ======================================================================

def _infer_role(tool: Tool, index: int) -> str:
    """Infer a workflow role when compose_stack isn't available."""
    roles = getattr(tool, "stack_roles", [])
    if roles:
        return roles[0]
    return ["primary", "companion", "infrastructure", "analytics", "companion"][min(index, 4)]


def _estimate_time_savings(tool: Tool, role: str) -> float:
    """Estimate hours saved per week based on tool categories."""
    cats = [c.lower() for c in tool.categories]
    savings = 0.0
    for cat in cats:
        if cat in _TIME_SAVINGS:
            savings = max(savings, _TIME_SAVINGS[cat])
    # Infrastructure/automation tools get a bonus
    if role in ("infrastructure", "analytics"):
        savings += 1.0
    return savings if savings > 0 else 1.0  # minimum 1 hr


def _estimate_monthly_cost(tool: Tool, profile: Optional[UserProfile]) -> Optional[float]:
    """Estimate monthly cost based on pricing dict and profile budget."""
    pricing = getattr(tool, "pricing", {}) or {}
    if not pricing:
        return None

    if profile and profile.budget == "free":
        return 0.0 if pricing.get("free_tier") else None

    # Pick price tier based on profile budget
    if profile and profile.budget == "low":
        cost = pricing.get("starter", pricing.get("pro"))
    elif profile and profile.budget == "high":
        cost = pricing.get("enterprise", pricing.get("pro"))
    else:
        cost = pricing.get("pro", pricing.get("starter"))

    return float(cost) if isinstance(cost, (int, float)) else None


def _migration_notes(tool: Tool, profile: Optional[UserProfile]) -> List[str]:
    """Generate migration tips for switching from existing tools to this one."""
    notes = []
    if not profile:
        return notes

    for existing in profile.existing_tools:
        existing_lower = existing.lower()
        tool_cats = [c.lower() for c in tool.categories]

        # Check if the existing tool overlaps in categories
        overlap = False
        for t in TOOLS:
            if t.name.lower() == existing_lower:
                existing_cats = [c.lower() for c in t.categories]
                shared = set(tool_cats) & set(existing_cats)
                if shared:
                    overlap = True
                    if tool.integrates_with(existing):
                        notes.append(
                            f"✓ {tool.name} integrates with {existing} — "
                            f"run both in parallel during transition"
                        )
                    else:
                        notes.append(
                            f"→ {tool.name} replaces {existing} for "
                            f"{', '.join(sorted(shared))} — export data from {existing} first"
                        )
                break
    if not notes:
        notes.append(f"No conflicts with your current stack — add {tool.name} directly")
    return notes


def _integration_tip(tool: Tool, stack_entries: list, current_idx: int) -> str:
    """Describe how this step connects to adjacent steps in the workflow."""
    tips = []

    # Check connection to previous step
    if current_idx > 0:
        prev_tool = stack_entries[current_idx - 1]["tool"]
        if tool.integrates_with(prev_tool.name) or prev_tool.integrates_with(tool.name):
            tips.append(f"Receives output from Step {current_idx} ({prev_tool.name}) via native integration")
        else:
            tips.append(f"Connect to Step {current_idx} ({prev_tool.name}) via Zapier/Make or manual export")

    # Check connection to next step
    if current_idx < len(stack_entries) - 1:
        next_tool = stack_entries[current_idx + 1]["tool"]
        if tool.integrates_with(next_tool.name) or next_tool.integrates_with(tool.name):
            tips.append(f"Feeds into Step {current_idx + 2} ({next_tool.name}) natively")
        else:
            tips.append(f"Pass results to Step {current_idx + 2} ({next_tool.name}) via export/webhook")

    return " | ".join(tips) if tips else "Standalone step — no direct tool-to-tool wiring needed"


def _workflow_risk_summary(stack_entries: list) -> dict:
    """Aggregate risk across all tools in the workflow."""
    if not _PHIL_AVAILABLE or not stack_entries:
        return {"overall": "unavailable"}

    flex_scores = []
    trans_scores = []
    warnings = []

    for entry in stack_entries:
        tool = entry["tool"]
        try:
            f = assess_freedom(tool)
            t = assess_transparency(tool)
            fs = f.get("score", 50)
            ts = t.get("score", 50)
            flex_scores.append(fs)
            trans_scores.append(ts)
            if f.get("grade") in ("D", "F"):
                warnings.append(f"{tool.name}: high lock-in risk (Flexibility {f['grade']})")
            if t.get("grade") in ("D", "F"):
                warnings.append(f"{tool.name}: low transparency (Transparency {t['grade']})")
        except Exception:
            pass

    avg_flex = sum(flex_scores) / len(flex_scores) if flex_scores else 50
    avg_trans = sum(trans_scores) / len(trans_scores) if trans_scores else 50

    return {
        "avg_flexibility_score": round(avg_flex),
        "avg_transparency_score": round(avg_trans),
        "warnings": warnings[:5],
        "overall": "low_risk" if avg_flex >= 60 and avg_trans >= 60 else
                   "medium_risk" if avg_flex >= 40 and avg_trans >= 40 else "high_risk",
    }
