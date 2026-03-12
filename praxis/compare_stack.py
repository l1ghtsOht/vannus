# --------------- Compare Stack vs. Alternatives ---------------
"""
"Compare My Stack" — side-by-side analysis.

Input: User's current tools (from profile or explicit list).
Output: Their stack vs. an optimised alternative stack.
    • Cost comparison
    • Performance / risk comparison
    • Integration density
    • Savings estimate
    • Lock-in delta

Uses compare_tools() for pair-wise, compose_stack() for optimised alternative,
and philosophy for risk overlay.
"""

import logging
from typing import Optional, List

log = logging.getLogger("praxis.compare_stack")

try:
    from .tools import Tool
    from .profile import UserProfile, load_profile
    from .data import TOOLS
    from .engine import find_tools, score_tool
    from .interpreter import interpret
    from .stack import compose_stack
    from .explain import explain_tool
except Exception:
    from tools import Tool
    from profile import UserProfile, load_profile
    from data import TOOLS
    from engine import find_tools, score_tool
    from interpreter import interpret
    from stack import compose_stack
    from explain import explain_tool

try:
    from .philosophy import assess_freedom, assess_transparency
    _PHIL = True
except Exception:
    try:
        from philosophy import assess_freedom, assess_transparency
        _PHIL = True
    except Exception:
        _PHIL = False


def compare_my_stack(
    current_tools: List[str],
    goal: str = "",
    profile: Optional[UserProfile] = None,
    profile_id: Optional[str] = None,
) -> dict:
    """Compare user's current stack against an optimised alternative.

    Returns:
        {
            "current_stack": { tools analysis },
            "optimised_stack": { proposed alternative },
            "comparison": { deltas },
            "savings": { cost, risk, integration },
            "recommendation": str
        }
    """
    if not profile and profile_id:
        profile = load_profile(profile_id)

    # Resolve current tools to Tool objects
    current_objs = []
    for name in current_tools:
        t = _find_tool(name)
        if t:
            current_objs.append(t)

    if not current_objs:
        return {"error": "None of the specified tools were found in our database"}

    # Analyse current stack
    current_analysis = _analyse_stack(current_objs, profile)

    # Build optimised alternative via compose_stack
    # Use the goal or infer from current tool categories
    if not goal:
        all_cats = []
        for t in current_objs:
            all_cats.extend(t.categories[:2])
        goal = " ".join(list(dict.fromkeys(all_cats))[:4])  # dedupe, top 4

    struct = interpret(goal)
    optimised_result = compose_stack(struct, profile=profile, stack_size=len(current_objs))
    optimised_objs = [entry["tool"] for entry in optimised_result.get("stack", [])]

    # If optimised == current, broaden search
    if set(t.name for t in optimised_objs) == set(t.name for t in current_objs):
        # Force diversity: exclude current tools
        alt_tools = []
        for t in current_objs:
            cats = t.categories[:2]
            q = " ".join(cats) + " alternative"
            s = interpret(q)
            results = find_tools(s, top_n=2, profile=profile)
            for r in results:
                if r.name not in current_tools and r.name not in [a.name for a in alt_tools]:
                    alt_tools.append(r)
                    break
        if alt_tools:
            optimised_objs = alt_tools

    optimised_analysis = _analyse_stack(optimised_objs, profile)

    # Compute deltas
    cost_delta = (current_analysis["est_monthly_cost"] or 0) - (optimised_analysis["est_monthly_cost"] or 0)
    risk_delta = (current_analysis["avg_risk_score"] or 50) - (optimised_analysis["avg_risk_score"] or 50)
    integration_delta = optimised_analysis["integration_pairs"] - current_analysis["integration_pairs"]

    # Recommendation
    rec = _build_recommendation(current_analysis, optimised_analysis, cost_delta, risk_delta)

    result = {
        "current_stack": current_analysis,
        "optimised_stack": optimised_analysis,
        "comparison": {
            "cost_delta_monthly": round(cost_delta, 2),
            "risk_delta": round(risk_delta, 1),
            "integration_delta": integration_delta,
        },
        "savings": {
            "monthly_cost_savings": f"${max(0, cost_delta):.0f}/mo" if cost_delta > 0 else "No savings (optimised may cost more)",
            "annual_cost_savings": f"${max(0, cost_delta * 12):.0f}/yr" if cost_delta > 0 else "N/A",
            "lock_in_reduction": f"{max(0, risk_delta):.0f}% less lock-in risk" if risk_delta > 0 else "Similar risk profile",
            "integration_improvement": f"+{integration_delta} native integrations" if integration_delta > 0 else "Similar integration density",
        },
        "recommendation": rec,
    }

    log.info("compare_stack: %d current vs %d optimised, cost_delta=$%.0f, risk_delta=%.0f",
             len(current_objs), len(optimised_objs), cost_delta, risk_delta)
    return result


# ======================================================================
# Stack analysis helper
# ======================================================================

def _analyse_stack(tools: List[Tool], profile: Optional[UserProfile]) -> dict:
    """Produce a structured analysis of a tool stack."""
    total_cost = 0.0
    risk_scores = []
    entries = []
    integration_pairs = 0

    for t in tools:
        # Cost
        pricing = getattr(t, "pricing", {}) or {}
        cost = None
        if profile:
            if profile.budget == "free":
                cost = 0.0 if pricing.get("free_tier") else None
            elif profile.budget == "low":
                cost = pricing.get("starter", pricing.get("pro"))
            else:
                cost = pricing.get("pro", pricing.get("starter"))
        else:
            cost = pricing.get("pro", pricing.get("starter"))
        if isinstance(cost, (int, float)):
            total_cost += float(cost)

        # Risk
        risk_score = 50
        flex_grade = "?"
        trans_grade = "?"
        if _PHIL:
            try:
                f = assess_freedom(t)
                tr = assess_transparency(t)
                risk_score = 100 - ((f.get("score", 50) + tr.get("score", 50)) / 2)
                flex_grade = f.get("grade", "?")
                trans_grade = tr.get("grade", "?")
            except Exception:
                pass
        risk_scores.append(risk_score)

        entries.append({
            "name": t.name,
            "categories": t.categories,
            "est_monthly_cost": f"${cost:.0f}" if cost else "varies",
            "flexibility_grade": flex_grade,
            "transparency_grade": trans_grade,
            "skill_level": t.skill_level,
        })

    # Count integration pairs
    for i, a in enumerate(tools):
        for b in tools[i + 1:]:
            if a.integrates_with(b.name) or b.integrates_with(a.name):
                integration_pairs += 1

    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 50

    return {
        "tools": entries,
        "tool_count": len(tools),
        "est_monthly_cost": round(total_cost, 2) if total_cost else None,
        "avg_risk_score": round(avg_risk, 1),
        "integration_pairs": integration_pairs,
    }


def _build_recommendation(current, optimised, cost_delta, risk_delta) -> str:
    """Build a human-readable recommendation."""
    parts = []

    if cost_delta > 20:
        parts.append(f"Switching saves ~${cost_delta:.0f}/mo (${cost_delta*12:.0f}/yr)")
    elif cost_delta < -20:
        parts.append(f"Optimised stack costs ~${abs(cost_delta):.0f}/mo more but offers better capabilities")

    if risk_delta > 10:
        parts.append(f"reduces vendor lock-in by ~{risk_delta:.0f}%")
    elif risk_delta < -10:
        parts.append(f"slightly higher lock-in risk (review individual tool flexibility grades)")

    int_delta = optimised["integration_pairs"] - current["integration_pairs"]
    if int_delta > 0:
        parts.append(f"+{int_delta} more native integrations between tools")

    if not parts:
        return "Your current stack is well-optimised. Consider the alternatives only if specific pain points arise."

    return "Recommended: " + ", ".join(parts) + "."


def _find_tool(name: str) -> Optional[Tool]:
    for t in TOOLS:
        if t.name.lower() == name.lower():
            return t
    return None
