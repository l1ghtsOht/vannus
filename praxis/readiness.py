# --------------- AI Readiness Scoring ---------------
"""
Personalized "AI Readiness Score" for a user profile.

Score 0–100 measuring AI maturity based on:
    • team_size           — larger = more capacity to adopt
    • skill_level         — higher = faster adoption curve
    • existing_tools      — more = further along the journey
    • goals clarity       — explicit goals = more focused
    • constraints         — compliance awareness = maturity signal
    • budget              — willingness to invest = readiness

Plus: prioritised next-step recommendations and learning resources.

Target persona: SMBs in Kansas/Midwest who feel "behind" —
this gives actionable direction and ties into onboarding.
"""

import logging
from typing import Optional, List, Dict

log = logging.getLogger("praxis.readiness")

try:
    from .profile import UserProfile, load_profile
    from .engine import find_tools
    from .interpreter import interpret
    from .data import TOOLS
except Exception:
    from profile import UserProfile, load_profile
    from engine import find_tools
    from interpreter import interpret
    from data import TOOLS


# ======================================================================
# Scoring rubric
# ======================================================================

_TEAM_SCORES = {"solo": 10, "small": 20, "medium": 30, "large": 35}
_SKILL_SCORES = {"beginner": 5, "intermediate": 15, "advanced": 25}
_BUDGET_SCORES = {"free": 5, "low": 10, "medium": 15, "high": 20}

# How many existing tools correlate with maturity
_TOOL_BRACKETS = [
    (0, 0),
    (1, 5),
    (3, 10),
    (6, 15),
    (10, 18),
    (999, 20),  # >10 tools
]

# Goals presence = maturity signal
_MAX_GOAL_POINTS = 10
_MAX_CONSTRAINT_POINTS = 10


def score_readiness(profile: Optional[UserProfile] = None,
                    profile_id: Optional[str] = None) -> dict:
    """Compute an AI Readiness Score for a user profile.

    Returns:
        {
            "score": int (0-100),
            "grade": "A" | "B" | "C" | "D" | "F",
            "breakdown": { category: points, ... },
            "maturity_level": "Exploring" | "Adopting" | "Optimising" | "Leading",
            "strengths": [str],
            "gaps": [str],
            "next_steps": [{"action": str, "priority": str, "tools": [...]}],
            "resources": [{"title": str, "url": str}]
        }
    """
    if not profile and profile_id:
        profile = load_profile(profile_id)
    if not profile:
        return {"error": "Profile required. Create one at POST /profile first."}

    breakdown = {}
    strengths = []
    gaps = []

    # ── Team size ──
    ts = _TEAM_SCORES.get(profile.team_size, 10)
    breakdown["team_capacity"] = ts
    if profile.team_size in ("medium", "large"):
        strengths.append(f"Team of {profile.team_size} size — capacity for parallel AI adoption")
    elif profile.team_size == "solo":
        gaps.append("Solo operator — AI can multiply your output but focus on 1-2 tools first")

    # ── Skill level ──
    sk = _SKILL_SCORES.get(profile.skill_level, 5)
    breakdown["skill_level"] = sk
    if profile.skill_level == "advanced":
        strengths.append("Advanced tech skills — can leverage APIs and custom integrations")
    elif profile.skill_level == "beginner":
        gaps.append("Beginner skill level — start with no-code, guided tools")

    # ── Budget ──
    bu = _BUDGET_SCORES.get(profile.budget, 10)
    breakdown["budget_readiness"] = bu
    if profile.budget in ("medium", "high"):
        strengths.append(f"'{profile.budget}' budget tier — can access premium AI capabilities")
    elif profile.budget == "free":
        gaps.append("Free-tier only — many powerful tools have free tiers, but consider investing $20-50/mo for 10x productivity")

    # ── Existing tools ──
    num_tools = len(profile.existing_tools)
    tool_pts = 0
    for threshold, pts in _TOOL_BRACKETS:
        if num_tools <= threshold:
            tool_pts = pts
            break
    breakdown["tool_adoption"] = tool_pts
    if num_tools >= 3:
        strengths.append(f"Already using {num_tools} AI tools — building on a foundation")
    elif num_tools == 0:
        gaps.append("No existing AI tools — start with one high-impact tool in your core workflow")

    # ── Goals clarity ──
    goal_pts = min(len(profile.goals) * 3, _MAX_GOAL_POINTS)
    breakdown["goal_clarity"] = goal_pts
    if len(profile.goals) >= 2:
        strengths.append(f"Clear goals defined: {', '.join(profile.goals[:3])}")
    else:
        gaps.append("Define 2-3 specific AI goals (e.g., 'automate invoicing', 'generate marketing copy')")

    # ── Compliance awareness ──
    comp_pts = min(len(profile.constraints) * 3, _MAX_CONSTRAINT_POINTS)
    breakdown["compliance_awareness"] = comp_pts
    if profile.constraints:
        strengths.append(f"Compliance-aware: {', '.join(profile.constraints)}")

    # ── Total ──
    total = sum(breakdown.values())
    total = max(0, min(100, total))
    grade = _grade(total)
    maturity = _maturity_level(total)

    # ── Next steps ──
    next_steps = _recommend_next_steps(profile, total)

    # ── Resources ──
    resources = _learning_resources(profile)

    result = {
        "score": total,
        "grade": grade,
        "breakdown": breakdown,
        "maturity_level": maturity,
        "strengths": strengths,
        "gaps": gaps,
        "next_steps": next_steps,
        "resources": resources,
    }

    log.info("readiness: profile=%s → score=%d (%s), maturity=%s",
             profile.profile_id, total, grade, maturity)
    return result


# ======================================================================
# Next-step recommendations
# ======================================================================

def _recommend_next_steps(profile: UserProfile, score: int) -> List[Dict]:
    """Suggest prioritised actions based on current maturity."""
    steps = []

    # Beginners: start with the basics
    if score < 30:
        # Find one easy writing/automation tool
        for goal_query in ["easy writing tool for beginners", "simple automation no-code"]:
            struct = interpret(goal_query)
            tools = find_tools(struct, top_n=2, profile=profile)
            if tools:
                steps.append({
                    "action": f"Start with {tools[0].name} — {tools[0].description[:60]}",
                    "priority": "high",
                    "tools": [t.name for t in tools[:2]],
                })
            if len(steps) >= 2:
                break

    # Mid-tier: optimize and integrate
    elif score < 60:
        # Suggest integration/automation tools
        struct = interpret("connect and automate existing tools")
        tools = find_tools(struct, top_n=3, profile=profile)
        if tools:
            steps.append({
                "action": "Connect your existing tools with an automation layer",
                "priority": "high",
                "tools": [t.name for t in tools[:2]],
            })

        # Suggest analytics
        struct = interpret("analytics and tracking for business")
        tools = find_tools(struct, top_n=2, profile=profile)
        if tools:
            steps.append({
                "action": "Add analytics to measure AI ROI",
                "priority": "medium",
                "tools": [t.name for t in tools[:2]],
            })

    # Advanced: go deeper
    else:
        # Suggest advanced/specialized tools
        if profile.goals:
            for goal in profile.goals[:2]:
                struct = interpret(f"advanced {goal} tool")
                tools = find_tools(struct, top_n=2, profile=profile)
                if tools:
                    steps.append({
                        "action": f"Level up your {goal} workflow with specialised tools",
                        "priority": "medium",
                        "tools": [t.name for t in tools[:2]],
                    })

    # Universal: compliance hardening
    if not profile.constraints and profile.industry:
        steps.append({
            "action": f"Review compliance requirements for {profile.industry} (GDPR, HIPAA, SOC2)",
            "priority": "medium",
            "tools": [],
        })

    return steps[:4]


# ======================================================================
# Learning resources
# ======================================================================

def _learning_resources(profile: UserProfile) -> List[Dict]:
    """Curated free resources based on skill level and goals."""
    resources = []

    if profile.skill_level == "beginner":
        resources.extend([
            {"title": "AI for Small Business — Getting Started Guide",
             "url": "https://www.sba.gov/ai-resources", "type": "guide"},
            {"title": "No-Code AI Tools: A Beginner's Roadmap",
             "url": "https://zapier.com/blog/no-code-ai/", "type": "article"},
        ])
    elif profile.skill_level == "intermediate":
        resources.extend([
            {"title": "Automating Business Workflows with AI",
             "url": "https://zapier.com/blog/ai-automation/", "type": "guide"},
            {"title": "Building Your First AI Stack",
             "url": "https://www.hubspot.com/ai-stack", "type": "article"},
        ])
    else:
        resources.extend([
            {"title": "Advanced AI Integration Patterns",
             "url": "https://docs.anthropic.com/", "type": "documentation"},
            {"title": "Enterprise AI Procurement Checklist",
             "url": "https://www.gartner.com/ai-procurement", "type": "whitepaper"},
        ])

    # Industry-specific
    if profile.industry:
        resources.append({
            "title": f"AI Tools for {profile.industry.title()} — Industry Guide",
            "url": f"https://praxis.ai/guides/{profile.industry.lower().replace(' ', '-')}",
            "type": "guide",
        })

    return resources


# ── helpers ──

def _grade(score: int) -> str:
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

def _maturity_level(score: int) -> str:
    if score >= 75: return "Leading"
    if score >= 50: return "Optimising"
    if score >= 25: return "Adopting"
    return "Exploring"
