# --------------- Stack Composer ---------------
"""
Composes multi-tool *stacks* instead of returning isolated tool results.

A stack is an ordered list of 2-4 tools, each assigned a role:
    • primary        – the main tool that addresses the user's core task
    • companion      – enhances / complements the primary tool
    • infrastructure – connects the stack (automation, data routing, CI/CD)
    • analytics      – provides measurement / feedback for the workflow

The composer uses the decision engine for initial scoring, then layers on
compatibility, integration, budget, and skill-level logic to assemble the
best combination.
"""

from typing import List, Optional, Dict

try:
    from .tools import Tool
    from .profile import UserProfile
    from .engine import find_tools, score_tool
    from .data import TOOLS
    from .explain import explain_stack
except Exception:
    from tools import Tool
    from profile import UserProfile
    from engine import find_tools, score_tool
    from data import TOOLS
    from explain import explain_stack

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None


# ======================================================================
# Public API
# ======================================================================

def compose_stack(
    intent: dict,
    profile: Optional[UserProfile] = None,
    stack_size: int = 3,
    categories_filter: list = None,
) -> dict:
    """Build an optimal tool stack for the given intent + profile.

    Returns:
        {
            "stack":        list of {"tool": Tool, "role": str},
            "explanation":  dict (from explain_stack),
            "alternatives": list of Tool (runners-up not in the stack),
        }
    """
    if _cfg:
        stack_size = _cfg.get("stack_size", stack_size)

    # Step 1 — score *all* tools with profile-aware engine
    candidates = _score_candidates(intent, profile, categories_filter)

    if not candidates:
        return {"stack": [], "explanation": {}, "alternatives": []}

    # Step 2 — select the primary tool (highest score)
    stack = []
    used_names = set()

    primary = _pick_best(candidates, role="primary", used=used_names, profile=profile)
    if primary:
        stack.append({"tool": primary, "role": "primary"})
        used_names.add(primary.name)

    # Step 3 — pick companion(s) that complement the primary
    remaining_slots = stack_size - len(stack)
    if remaining_slots > 0 and primary:
        companions = _pick_companions(candidates, primary, used_names, profile, limit=min(remaining_slots, 2))
        for c in companions:
            stack.append({"tool": c, "role": "companion"})
            used_names.add(c.name)
            remaining_slots -= 1

    # Step 4 — pick infrastructure / analytics tool if slot remains
    if remaining_slots > 0:
        infra = _pick_infrastructure(candidates, stack, used_names, profile)
        if infra:
            stack.append({"tool": infra, "role": "infrastructure"})
            used_names.add(infra.name)

    # Step 5 — build explanation
    explanation = explain_stack(stack, intent, profile) if stack else {}

    # Step 6 — alternatives (next-best tools not in stack)
    alternatives = [
        tool for (_, tool) in candidates
        if tool.name not in used_names
    ][:5]

    return {
        "stack": stack,
        "explanation": explanation,
        "alternatives": alternatives,
    }


# ======================================================================
# Internal helpers
# ======================================================================

def _score_candidates(
    intent: dict,
    profile: Optional[UserProfile],
    categories_filter: list,
) -> List[tuple]:
    """Return a list of (score, Tool) tuples, sorted descending."""
    from difflib import SequenceMatcher

    # Build keywords the same way engine.find_tools does
    if isinstance(intent, dict):
        keywords = []
        for k in (intent.get("intent"), intent.get("industry"), intent.get("goal")):
            if k:
                keywords.append(str(k))
        keywords.extend(intent.get("keywords", []))
        if not keywords and intent.get("raw"):
            keywords = intent.get("raw", "").lower().split()
    else:
        keywords = str(intent).lower().split()

    if categories_filter:
        categories_filter = [c.lower().strip() for c in categories_filter if c.strip()]
    else:
        categories_filter = None

    scored = []
    for tool in TOOLS:
        # Category filter
        if categories_filter:
            tool_cats = [c.lower() for c in tool.categories]
            if not any(fc in tool_cats for fc in categories_filter):
                continue

        # Profile-based hard filters
        if profile:
            # Compliance gate
            skip = False
            for constraint in profile.constraints:
                if constraint.upper() in ("HIPAA", "SOC2", "GDPR", "FEDRAMP"):
                    if constraint.upper() not in [c.upper() for c in tool.compliance]:
                        skip = True
                        break
            if skip:
                continue

        sc = score_tool(tool, keywords)

        # Profile bonuses
        if profile:
            if tool.fits_budget(profile.budget):
                sc += 2
            if tool.fits_skill(profile.skill_level):
                sc += 2
            # Bonus for integrating with existing tools
            for et in profile.existing_tools:
                if tool.integrates_with(et):
                    sc += 3
                    break
            # Slight penalty if user already uses this tool (they want *new* recs)
            if profile.already_uses(tool.name):
                sc -= 2

        if sc > 0:
            scored.append((sc, tool))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _pick_best(
    candidates: List[tuple],
    role: str,
    used: set,
    profile: Optional[UserProfile],
) -> Optional[Tool]:
    """Pick the highest-scoring candidate that can fill *role* and isn't used."""
    for _, tool in candidates:
        if tool.name in used:
            continue
        if role in tool.stack_roles:
            return tool
    # Fallback: ignore role constraint
    for _, tool in candidates:
        if tool.name not in used:
            return tool
    return None


def _pick_companions(
    candidates: List[tuple],
    primary: Tool,
    used: set,
    profile: Optional[UserProfile],
    limit: int = 2,
) -> List[Tool]:
    """Pick tools that complement the primary — different categories, ideally integrating."""
    primary_cats = set(c.lower() for c in primary.categories)
    companions = []

    # Prefer tools that integrate with the primary and cover different categories
    integrating = []
    non_integrating = []

    for _, tool in candidates:
        if tool.name in used:
            continue
        if "companion" not in tool.stack_roles and "primary" not in tool.stack_roles:
            continue  # skip pure infra for companion slot
        # Avoid heavy overlap with primary
        tool_cats = set(c.lower() for c in tool.categories)
        overlap = len(primary_cats & tool_cats) / max(len(primary_cats | tool_cats), 1)
        if overlap > 0.7:
            continue  # too similar

        if tool.integrates_with(primary.name) or primary.integrates_with(tool.name):
            integrating.append(tool)
        else:
            non_integrating.append(tool)

    for t in integrating + non_integrating:
        if len(companions) >= limit:
            break
        companions.append(t)

    return companions


def _pick_infrastructure(
    candidates: List[tuple],
    current_stack: list,
    used: set,
    profile: Optional[UserProfile],
) -> Optional[Tool]:
    """Pick an infrastructure or analytics tool that connects the stack."""
    stack_names = {e["tool"].name for e in current_stack}

    best = None
    best_integration_count = -1

    for _, tool in candidates:
        if tool.name in used:
            continue
        if "infrastructure" not in tool.stack_roles and "analytics" not in tool.stack_roles:
            continue

        # Count how many stack members this tool integrates with
        integration_count = sum(
            1 for sn in stack_names
            if tool.integrates_with(sn) or any(
                e["tool"].integrates_with(tool.name) for e in current_stack
            )
        )

        if integration_count > best_integration_count:
            best_integration_count = integration_count
            best = tool

    return best


# ======================================================================
# Comparison helper
# ======================================================================

def compare_tools(tool_name_a: str, tool_name_b: str, profile: Optional[UserProfile] = None) -> dict:
    """Side-by-side comparison of two tools in the knowledge base."""
    tool_a = next((t for t in TOOLS if t.name.lower() == tool_name_a.lower()), None)
    tool_b = next((t for t in TOOLS if t.name.lower() == tool_name_b.lower()), None)

    if not tool_a or not tool_b:
        return {"error": f"Tool not found: {tool_name_a if not tool_a else tool_name_b}"}

    def _summarize(tool: Tool) -> dict:
        return {
            "name": tool.name,
            "description": tool.description,
            "categories": tool.categories,
            "pricing": tool.pricing,
            "skill_level": tool.skill_level,
            "compliance": tool.compliance,
            "integrations": tool.integrations[:8],
            "use_cases": tool.use_cases,
            "stack_roles": tool.stack_roles,
            "fits_budget": tool.fits_budget(profile.budget) if profile else None,
            "fits_skill": tool.fits_skill(profile.skill_level) if profile else None,
        }

    result = {
        "tool_a": _summarize(tool_a),
        "tool_b": _summarize(tool_b),
        "shared_integrations": sorted(
            set(i.lower() for i in tool_a.integrations) &
            set(i.lower() for i in tool_b.integrations)
        ),
        "shared_categories": sorted(
            set(c.lower() for c in tool_a.categories) &
            set(c.lower() for c in tool_b.categories)
        ),
        "direct_integration": tool_a.integrates_with(tool_b.name) or tool_b.integrates_with(tool_a.name),
    }

    # Recommend the better fit
    try:
        from .explain import explain_tool
    except Exception:
        from explain import explain_tool

    expl_a = explain_tool(tool_a, {"keywords": [], "raw": ""}, profile)
    expl_b = explain_tool(tool_b, {"keywords": [], "raw": ""}, profile)
    score_a, score_b = expl_a["fit_score"], expl_b["fit_score"]

    if profile:
        if score_a > score_b:
            result["recommendation"] = f"{tool_a.name} is a better fit for your profile (score: {score_a} vs {score_b})"
        elif score_b > score_a:
            result["recommendation"] = f"{tool_b.name} is a better fit for your profile (score: {score_b} vs {score_a})"
        else:
            result["recommendation"] = "Both tools are equally suitable for your profile"
    else:
        # General comparison without profile context
        pop_a = getattr(tool_a, "popularity", 0) or 0
        pop_b = getattr(tool_b, "popularity", 0) or 0
        if pop_a > pop_b:
            result["recommendation"] = f"{tool_a.name} is more widely adopted (popularity: {pop_a} vs {pop_b}). {tool_b.name} may be stronger for niche use cases."
        elif pop_b > pop_a:
            result["recommendation"] = f"{tool_b.name} is more widely adopted (popularity: {pop_b} vs {pop_a}). {tool_a.name} may be stronger for niche use cases."
        else:
            result["recommendation"] = f"Both tools are similarly rated. Create a profile for a personalized recommendation."

    return result
