# --------------- What-If Simulator ---------------
"""
Interactive parameter tweaking: "What if my budget doubles? Team grows to 20?"

Re-runs recommendations with modified profile params and shows the delta
between current and hypothetical results.

Great for SMBs planning growth via CLI or /whatif API endpoint.
"""

import copy
import logging
from typing import Optional, Dict, List

log = logging.getLogger("praxis.whatif")

try:
    from .profile import UserProfile, load_profile
    from .engine import find_tools
    from .interpreter import interpret
    from .stack import compose_stack
    from .explain import explain_tool
except Exception:
    from profile import UserProfile, load_profile
    from engine import find_tools
    from interpreter import interpret
    from stack import compose_stack
    from explain import explain_tool


def simulate(
    query: str,
    changes: Dict[str, str],
    profile: Optional[UserProfile] = None,
    profile_id: Optional[str] = None,
    top_n: int = 5,
) -> dict:
    """Run a what-if simulation.

    Args:
        query: The recommendation query (e.g., "best marketing tools")
        changes: Dict of profile field → new value (e.g., {"budget": "high", "team_size": "medium"})
        profile: Base profile to modify
        profile_id: Alternatively load by ID
        top_n: Number of results to return

    Returns:
        {
            "baseline": { recommendations with current profile },
            "hypothetical": { recommendations with tweaked profile },
            "delta": { what changed },
            "changes_applied": { ... }
        }
    """
    if not profile and profile_id:
        profile = load_profile(profile_id)
    if not profile:
        profile = UserProfile()

    struct = interpret(query)

    # ── Baseline: current profile ──
    baseline_tools = find_tools(struct, top_n=top_n, profile=profile)
    baseline_stack = compose_stack(struct, profile=profile, stack_size=min(top_n, 4))
    baseline = _summarise_results(baseline_tools, baseline_stack, struct, profile)

    # ── Hypothetical: modified profile ──
    hypo_profile = _apply_changes(profile, changes)
    hypo_tools = find_tools(struct, top_n=top_n, profile=hypo_profile)
    hypo_stack = compose_stack(struct, profile=hypo_profile, stack_size=min(top_n, 4))
    hypothetical = _summarise_results(hypo_tools, hypo_stack, struct, hypo_profile)

    # ── Delta ──
    delta = _compute_delta(baseline, hypothetical, baseline_tools, hypo_tools)

    result = {
        "query": query,
        "changes_applied": changes,
        "baseline": baseline,
        "hypothetical": hypothetical,
        "delta": delta,
    }

    log.info("whatif: query=%r, changes=%s → %d new tools, score_delta=%+d",
             query, changes,
             delta.get("new_tools_count", 0),
             delta.get("avg_fit_delta", 0))
    return result


# ======================================================================
# Helpers
# ======================================================================

def _apply_changes(profile: UserProfile, changes: Dict) -> UserProfile:
    """Create a modified copy of the profile."""
    d = profile.to_dict()
    for key, val in changes.items():
        if key in d:
            # Handle list fields
            if isinstance(d[key], list) and isinstance(val, str):
                d[key] = [v.strip() for v in val.split(",")]
            else:
                d[key] = val
    return UserProfile.from_dict(d)


def _summarise_results(tools, stack_result, struct, profile) -> dict:
    """Summarise recommendation results."""
    tool_summaries = []
    fit_scores = []

    for t in tools:
        expl = explain_tool(t, struct, profile)
        fit_scores.append(expl.get("fit_score", 50))
        tool_summaries.append({
            "name": t.name,
            "fit_score": expl.get("fit_score"),
            "categories": t.categories[:3],
            "reasons": expl.get("reasons", [])[:2],
        })

    stack_tools = [
        {
            "name": entry["tool"].name,
            "role": entry["role"],
        }
        for entry in stack_result.get("stack", [])
    ]

    avg_fit = round(sum(fit_scores) / len(fit_scores)) if fit_scores else 50
    cost = stack_result.get("explanation", {}).get("total_monthly_cost", "varies")

    return {
        "tools": tool_summaries,
        "avg_fit_score": avg_fit,
        "stack": stack_tools,
        "est_monthly_cost": cost,
        "profile_summary": {
            "budget": profile.budget,
            "team_size": profile.team_size,
            "skill_level": profile.skill_level,
        },
    }


def _compute_delta(baseline, hypothetical, base_tools, hypo_tools) -> dict:
    """Compute what changed between baseline and hypothetical."""
    base_names = set(t.name for t in base_tools)
    hypo_names = set(t.name for t in hypo_tools)

    new_tools = sorted(hypo_names - base_names)
    dropped_tools = sorted(base_names - hypo_names)
    kept_tools = sorted(base_names & hypo_names)

    fit_delta = hypothetical["avg_fit_score"] - baseline["avg_fit_score"]

    return {
        "new_tools": new_tools,
        "new_tools_count": len(new_tools),
        "dropped_tools": dropped_tools,
        "kept_tools": kept_tools,
        "avg_fit_delta": fit_delta,
        "summary": _delta_summary(new_tools, dropped_tools, fit_delta),
    }


def _delta_summary(new_tools, dropped_tools, fit_delta) -> str:
    """Human-readable delta summary."""
    parts = []
    if new_tools:
        parts.append(f"{len(new_tools)} new tool(s) unlocked: {', '.join(new_tools[:3])}")
    if dropped_tools:
        parts.append(f"{len(dropped_tools)} tool(s) no longer top-ranked: {', '.join(dropped_tools[:3])}")
    if fit_delta > 0:
        parts.append(f"average fit score improved by +{fit_delta}")
    elif fit_delta < 0:
        parts.append(f"average fit score decreased by {fit_delta}")
    if not parts:
        return "No significant changes in recommendations."
    return " | ".join(parts)
