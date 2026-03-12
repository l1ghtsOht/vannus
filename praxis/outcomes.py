# --------------- Outcome-Oriented Advisory Engine ---------------
"""
Praxis Outcome Optimization & Underwhelm Prevention.

Transforms the recommendation flow from feature-comparison to
outcome-resolution pathways. Instead of showing 50 tools that
match "marketing", this module:

    1. Detects outcome intent (time_saved, cost_reduction, revenue_growth, compliance)
    2. Applies Underwhelm Prevention — intercedes on vague queries with disambiguation
    3. Ranks survivors by verified ROI against the detected outcome KPI
    4. Limits output to 3 highly-verified tools per outcome axis

Outcome Pillars:
    - Time Saved          — Workflow acceleration, automation hours reclaimed
    - Cost Reduction      — Spend optimization, license consolidation, error reduction
    - Revenue Growth      — Pipeline acceleration, conversion uplift, ARPU increase
    - Compliance Maintained — Regulatory adherence, audit readiness, risk mitigation

Integrates with:
    - interpreter.py     (outcome intent detection from raw queries)
    - engine.py          (outcome-weighted scoring in recommendation loop)
    - intelligence.py    (disambiguation flow for vague queries)
    - sovereignty.py     (only verified-domestic tools for high-compliance outcomes)
"""

from typing import Dict, List, Optional, Tuple
import logging
import re

_log = logging.getLogger("praxis.outcomes")


# ======================================================================
# 1. Outcome Taxonomy
# ======================================================================

OUTCOME_PILLARS = {
    "time_saved": {
        "label": "Time Saved",
        "icon": "⏱",
        "description": "Accelerate workflows, automate repetitive tasks, reclaim productive hours",
        "metrics": ["hours_saved_per_week", "task_completion_speed_pct", "automation_rate_pct"],
        "signal_keywords": [
            "fast", "quick", "automate", "speed", "efficiency", "streamline",
            "save time", "hours", "productivity", "workflow", "accelerate",
            "reduce manual", "batch", "bulk", "schedule", "template",
        ],
    },
    "cost_reduction": {
        "label": "Cost Reduction",
        "icon": "💰",
        "description": "Optimize spend, consolidate licenses, reduce error-driven costs",
        "metrics": ["monthly_savings_usd", "error_reduction_pct", "license_consolidation"],
        "signal_keywords": [
            "cheap", "budget", "save money", "cost", "affordable", "free",
            "reduce spend", "consolidate", "replace", "alternative", "cheaper",
            "roi", "payback", "value", "economics", "optimize cost",
        ],
    },
    "revenue_growth": {
        "label": "Revenue Growth",
        "icon": "📈",
        "description": "Accelerate pipeline, improve conversion, increase average revenue per user",
        "metrics": ["conversion_uplift_pct", "pipeline_velocity_pct", "arpu_increase_pct"],
        "signal_keywords": [
            "grow", "revenue", "sales", "leads", "conversion", "pipeline",
            "customers", "acquisition", "retention", "upsell", "marketing",
            "outbound", "inbound", "campaign", "funnel", "close rate",
        ],
    },
    "compliance": {
        "label": "Compliance Maintained",
        "icon": "🛡",
        "description": "Ensure regulatory adherence, audit readiness, risk mitigation",
        "metrics": ["audit_pass_rate_pct", "violation_reduction_pct", "time_to_compliance_days"],
        "signal_keywords": [
            "compliant", "compliance", "hipaa", "gdpr", "soc2", "audit",
            "regulated", "security", "privacy", "governance", "risk",
            "pci", "ferpa", "fedramp", "iso27001", "data protection",
        ],
    },
}

# Maximum tools per outcome recommendation
MAX_OUTCOME_RESULTS = 3

# Ambiguity threshold — if no outcome detected with confidence, trigger disambiguation
OUTCOME_CONFIDENCE_THRESHOLD = 0.3


# ======================================================================
# 2. Outcome Intent Detection
# ======================================================================

def detect_outcome_intent(query: str, profile: object = None) -> Dict:
    """
    Analyze a user query to determine the primary outcome axis.

    Returns:
        {
            "primary_outcome": str | None,     # time_saved, cost_reduction, etc.
            "confidence": float,                # 0.0 - 1.0
            "all_scores": {pillar: score},      # Score per outcome axis
            "is_ambiguous": bool,               # True if disambiguation needed
            "disambiguation_options": [str],    # Suggested clarification prompts
            "profile_boost": str | None,        # Outcome boosted by profile context
        }
    """
    query_lower = query.lower().strip()
    words = set(re.findall(r'\b[a-z]+\b', query_lower))

    scores = {}
    for pillar_id, pillar in OUTCOME_PILLARS.items():
        score = 0.0
        for kw in pillar["signal_keywords"]:
            if kw in query_lower:
                score += 0.15
            elif any(w in kw.split() for w in words):
                score += 0.05
        scores[pillar_id] = min(score, 1.0)

    # Profile context boost
    profile_boost = None
    if profile:
        goals = getattr(profile, "goals", []) or []
        constraints = getattr(profile, "constraints", []) or []
        industry = getattr(profile, "industry", "") or ""

        for goal in goals:
            goal_lower = goal.lower()
            for pid, p in OUTCOME_PILLARS.items():
                if any(kw in goal_lower for kw in p["signal_keywords"][:5]):
                    scores[pid] = min(scores[pid] + 0.2, 1.0)
                    profile_boost = pid

        # Regulated industries get compliance boost
        regulated = {"healthcare", "finance", "legal", "defense", "government", "insurance", "banking"}
        if industry.lower() in regulated:
            scores["compliance"] = min(scores["compliance"] + 0.3, 1.0)
            if not profile_boost:
                profile_boost = "compliance"

    # Determine primary
    if scores:
        primary = max(scores, key=scores.get)
        confidence = scores[primary]
    else:
        primary = None
        confidence = 0.0

    is_ambiguous = confidence < OUTCOME_CONFIDENCE_THRESHOLD
    disambiguation = []
    if is_ambiguous:
        disambiguation = _generate_disambiguation(query)

    return {
        "primary_outcome": primary if not is_ambiguous else None,
        "confidence": round(confidence, 3),
        "all_scores": {k: round(v, 3) for k, v in scores.items()},
        "is_ambiguous": is_ambiguous,
        "disambiguation_options": disambiguation,
        "profile_boost": profile_boost,
    }


def _generate_disambiguation(query: str) -> List[str]:
    """Generate outcome-centric clarification prompts for vague queries."""
    return [
        f"Are you looking to save time on '{query}' workflows?",
        f"Are you trying to reduce costs related to '{query}'?",
        f"Is your goal to grow revenue through better '{query}' tooling?",
        f"Do you need '{query}' tools that meet specific compliance requirements?",
    ]


# ======================================================================
# 3. Outcome-Weighted Ranking
# ======================================================================

def rank_by_outcome(tools: list, outcome: str, top_n: int = MAX_OUTCOME_RESULTS) -> List[Dict]:
    """
    Re-rank tools by their verified ROI score for a specific outcome pillar.

    Args:
        tools: List of Tool objects (pre-filtered by search relevance)
        outcome: Target outcome pillar ID
        top_n: Maximum results to return

    Returns:
        List of outcome-scored tool dicts, sorted by verified ROI
    """
    scored = []
    for tool in tools:
        kpi = getattr(tool, "target_outcome_kpi", None) or ""
        roi = getattr(tool, "verified_roi_score", 0.0) or 0.0
        metrics = getattr(tool, "outcome_metrics", {}) or {}

        # Exact KPI match gets full ROI score
        if kpi == outcome:
            outcome_score = roi
        # Partial match (tool has ROI but different primary KPI)
        elif roi > 0:
            outcome_score = roi * 0.5
        else:
            outcome_score = 0.0

        # Bonus for tools with verified outcome metrics
        if metrics:
            outcome_score = min(outcome_score + 0.1, 1.0)

        scored.append({
            "tool": tool,
            "tool_name": tool.name,
            "outcome_score": round(outcome_score, 3),
            "primary_kpi": kpi,
            "verified_roi": roi,
            "metrics": metrics,
            "kpi_match": kpi == outcome,
        })

    scored.sort(key=lambda x: x["outcome_score"], reverse=True)
    return scored[:top_n]


# ======================================================================
# 4. Underwhelm Prevention Engine
# ======================================================================

def underwhelm_check(query: str, result_count: int, outcome_data: Dict) -> Dict:
    """
    Evaluate whether search results will overwhelm or underwhelm the user.

    If the query is vague and would return too many results, this triggers
    the active disambiguation flow ("Underwhelm Prevention").

    Returns:
        {
            "action": "proceed" | "disambiguate" | "constrain",
            "reason": str,
            "suggested_filters": list,
            "max_display": int,
        }
    """
    is_ambiguous = outcome_data.get("is_ambiguous", False)
    confidence = outcome_data.get("confidence", 0.0)

    # Vague query + many results → force disambiguation
    if is_ambiguous and result_count > 10:
        return {
            "action": "disambiguate",
            "reason": f"Query '{query}' matches {result_count} tools across multiple categories. "
                      "Select a primary business outcome to narrow results.",
            "suggested_filters": outcome_data.get("disambiguation_options", []),
            "max_display": 0,
        }

    # Moderate ambiguity → constrain to outcome-ranked top 3
    if confidence < 0.5 and result_count > 5:
        return {
            "action": "constrain",
            "reason": "Applying outcome optimization to surface the highest-ROI options.",
            "suggested_filters": [
                f"Filter by: {OUTCOME_PILLARS[p]['label']}"
                for p in sorted(outcome_data.get("all_scores", {}),
                               key=outcome_data["all_scores"].get, reverse=True)[:3]
            ],
            "max_display": MAX_OUTCOME_RESULTS,
        }

    # Clear intent → proceed normally
    return {
        "action": "proceed",
        "reason": "Clear outcome intent detected. Showing best matches.",
        "suggested_filters": [],
        "max_display": result_count,
    }


# ======================================================================
# 5. Outcome Navigation Pills
# ======================================================================

def get_outcome_pills() -> List[Dict]:
    """
    Return the outcome-centric navigation pills for the UI.

    Replaces generic technical filters with business outcome axes.
    """
    return [
        {
            "id": pid,
            "label": p["label"],
            "icon": p["icon"],
            "description": p["description"],
        }
        for pid, p in OUTCOME_PILLARS.items()
    ]


def get_outcome_detail(outcome_id: str) -> Optional[Dict]:
    """Get detailed info for a specific outcome pillar."""
    pillar = OUTCOME_PILLARS.get(outcome_id)
    if not pillar:
        return None
    return {
        "id": outcome_id,
        **pillar,
    }


# ======================================================================
# 6. Outcome-Enriched Search Result Assembly
# ======================================================================

def assemble_outcome_results(
    tools: list,
    query: str,
    profile: object = None,
    force_outcome: str = None,
) -> Dict:
    """
    Full outcome-oriented search result assembly.

    1. Detect outcome intent
    2. Check for underwhelm conditions
    3. Rank by outcome ROI
    4. Return structured results with outcome context

    Returns:
        {
            "outcome_detected": {outcome_data},
            "underwhelm_check": {check_data},
            "outcome_pills": [pill],
            "ranked_results": [tool_scores],
            "display_mode": "outcome" | "standard" | "disambiguate",
        }
    """
    outcome_data = detect_outcome_intent(query, profile)

    # Force override
    if force_outcome and force_outcome in OUTCOME_PILLARS:
        outcome_data["primary_outcome"] = force_outcome
        outcome_data["is_ambiguous"] = False
        outcome_data["confidence"] = 1.0

    uw_check = underwhelm_check(query, len(tools), outcome_data)

    ranked = []
    display_mode = "standard"

    if uw_check["action"] == "disambiguate":
        display_mode = "disambiguate"
    elif outcome_data["primary_outcome"]:
        ranked = rank_by_outcome(tools, outcome_data["primary_outcome"])
        display_mode = "outcome"
    else:
        # No clear outcome → rank by general ROI
        ranked = rank_by_outcome(tools, "time_saved", top_n=5)
        display_mode = "standard"

    return {
        "outcome_detected": outcome_data,
        "underwhelm_check": uw_check,
        "outcome_pills": get_outcome_pills(),
        "ranked_results": ranked,
        "display_mode": display_mode,
        "total_candidates": len(tools),
    }


_log.info(
    "outcomes.py loaded — %d outcome pillars, max %d results per axis, "
    "confidence threshold %.1f",
    len(OUTCOME_PILLARS), MAX_OUTCOME_RESULTS, OUTCOME_CONFIDENCE_THRESHOLD,
)
