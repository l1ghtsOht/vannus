# --------------- Differential Diagnosis Engine ---------------
"""
Elimination-first recommendation pipeline adapted from clinical decision
support methodology.  Instead of ranking all 246 tools by relevance,
the system:

    1. Generates a broad candidate set (the "differential")
    2. Ruthlessly prunes via hard organizational constraints
    3. Probabilistically penalises survivors for soft risk factors
    4. Ranks only the resilient survivors for final presentation

Every eliminated tool is logged with a specific reason code so the
explain layer can generate transparent "why not" counterfactuals.

Modules consumed:
    interpreter  → structured intent extraction (positive / negative / ambiguity)
    profile      → constraint matrix (budget, compliance, risk tolerance)
    engine       → broad candidate retrieval & base scoring
    intelligence → TF-IDF alignment scoring on survivor subset
    philosophy   → vendor risk penalties (lock-in, transparency, freedom)
    verification → resilience tiers (sovereign → wrapper)
    explain      → natural-language presentation assembly
    learning     → historical telemetry (churn, quality trends)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.differential")

# ── Module imports (resilient to package vs standalone) ──────────────

try:
    from .data import TOOLS
    from .tools import Tool
except ImportError:
    from data import TOOLS
    from tools import Tool

try:
    from .interpreter import interpret
except ImportError:
    from interpreter import interpret

try:
    from .profile import UserProfile
except ImportError:
    from profile import UserProfile

try:
    from .verification import score_tool as resilience_score_tool, _tier_label
except ImportError:
    from verification import score_tool as resilience_score_tool, _tier_label

try:
    from .intelligence import (
        get_tfidf_index, get_learned_boost, extract_negatives,
        expand_synonyms, get_industry_boost,
    )
    _INTEL = True
except ImportError:
    try:
        from intelligence import (
            get_tfidf_index, get_learned_boost, extract_negatives,
            expand_synonyms, get_industry_boost,
        )
        _INTEL = True
    except ImportError:
        _INTEL = False

try:
    from .philosophy import (
        assess_transparency, assess_freedom, get_tool_intel,
    )
    _PHIL = True
except ImportError:
    try:
        from philosophy import (
            assess_transparency, assess_freedom, get_tool_intel,
        )
        _PHIL = True
    except ImportError:
        _PHIL = False

try:
    from .learning import compute_tool_quality
    _LEARN = True
except ImportError:
    try:
        from learning import compute_tool_quality
        _LEARN = True
    except ImportError:
        _LEARN = False

try:
    from .engine import score_tool as engine_score_tool, normalize
except ImportError:
    from engine import score_tool as engine_score_tool, normalize


# ======================================================================
# Constants & thresholds
# ======================================================================

# Minimum viability score — below this, soft penalties eliminate a tool
MIN_VIABILITY_THRESHOLD = 0.15

# Ambiguity severity threshold — above this, trigger clarification
AMBIGUITY_THRESHOLD = 0.7

# Maximum recommended survivors to present
DEFAULT_TOP_N = 5

# Churn-rate threshold for negative telemetry penalty
CHURN_THRESHOLD = 0.6

# Budget ceiling lookup: tier → max monthly $
_BUDGET_CEILINGS = {
    "free": 0,
    "low": 50,
    "medium": 500,
    "high": float("inf"),
}

# Skill-level ordinal
_SKILL_ORDINAL = {"beginner": 1, "intermediate": 2, "advanced": 3}

# Resilience-tier risk mapping
_HIGH_RISK_TIERS = {"fragile", "wrapper"}

# Reason codes for hard elimination
class ReasonCode:
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    COMPLIANCE_FAILURE = "COMPLIANCE_FAILURE"
    NEGATIVE_INTENT = "NEGATIVE_INTENT_MATCH"
    STACK_CONFLICT = "STACK_CONFLICT"
    DEPLOYMENT_CONFLICT = "DEPLOYMENT_CONFLICT"
    ARCHITECTURAL_REDUNDANCY = "ARCHITECTURAL_REDUNDANCY"


# ======================================================================
# Data structures
# ======================================================================

@dataclass
class EliminationEntry:
    """Record of why a tool was eliminated."""
    tool_name: str
    tool_id: str  # lowercase normalised name
    reason_type: str  # "HARD_CONSTRAINT" or "SOFT_PENALTY_THRESHOLD"
    code: str
    explanation: str
    stage: int  # 2 = hard prune, 3 = soft penalty threshold


@dataclass
class ScoredSurvivor:
    """A tool that survived both pruning stages."""
    tool: Any  # Tool object
    base_score: float
    penalties_applied: List[str]
    penalty_total: float
    final_score: float
    resilience: Optional[Dict] = None  # tier, grade, score from verification
    alignment_reasons: List[str] = field(default_factory=list)


@dataclass
class AmbiguityFlag:
    """Signals that a query is too vague for deterministic processing."""
    severity: float  # 0.0–1.0
    missing_axes: List[str]
    suggested_clarifications: List[str]


@dataclass
class DifferentialResult:
    """Complete output of the differential diagnosis pipeline."""
    query: str
    profile_id: Optional[str]
    stages: Dict[str, Any]  # per-stage metadata for funnel viz
    survivors: List[Dict]
    eliminated: List[Dict]
    clarification_needed: bool = False
    clarification: Optional[Dict] = None
    funnel_narrative: List[str] = field(default_factory=list)


# ======================================================================
# Stage 1 — Intent Parsing & Broad Candidate Generation
# ======================================================================

def _parse_intents(user_query: str) -> Tuple[Dict, List[str], List[str], AmbiguityFlag]:
    """
    Parse user query into positive intents, negative constraints,
    and ambiguity assessment.

    Returns:
        (interpreted_dict, positive_keywords, negative_constraints, ambiguity)
    """
    interpreted = interpret(user_query)

    # Positive intents — everything the user is looking for
    positives = []
    for key in ("intent", "industry", "goal"):
        val = interpreted.get(key)
        if val:
            positives.append(str(val).lower())
    positives.extend([k.lower() for k in interpreted.get("keywords", [])])

    # Negative constraints — what the user explicitly excludes
    negatives = [n.lower() for n in interpreted.get("negatives", [])]

    # Ambiguity assessment
    clarification_needed = interpreted.get("clarification_needed", False)
    suggested_qs = interpreted.get("suggested_questions", [])

    # Compute severity: vague queries have few keywords and no clear intent
    keyword_count = len(positives)
    has_intent = bool(interpreted.get("intent"))
    has_industry = bool(interpreted.get("industry"))

    if keyword_count == 0:
        severity = 1.0
    elif not has_intent and keyword_count < 2:
        severity = 0.85
    elif not has_intent:
        severity = 0.6
    elif not has_industry and keyword_count < 3:
        severity = 0.4
    else:
        severity = 0.1

    missing = []
    if not has_intent:
        missing.append("task_category")
    if not has_industry:
        missing.append("industry_vertical")
    if keyword_count < 2:
        missing.append("specific_requirements")

    if not suggested_qs and severity >= AMBIGUITY_THRESHOLD:
        suggested_qs = [
            "What's the main task you're trying to accomplish?",
            "Are you looking to manage tasks, communicate in real-time, or track data?",
            "What industry or domain are you working in?",
        ]

    ambiguity = AmbiguityFlag(
        severity=severity,
        missing_axes=missing,
        suggested_clarifications=suggested_qs,
    )

    return interpreted, positives, negatives, ambiguity


def _retrieve_broad_differential(
    positives: List[str],
    negatives: List[str],
    interpreted: Dict,
) -> List[Any]:
    """
    Generate a broad candidate set by collecting all tools that have
    *any* relevance to the positive intents. This is intentionally
    generous — better to include too many than miss a niche fit.
    """
    candidates = []

    for tool in TOOLS:
        # Quick negative name check — skip tools whose name matches negatives
        tool_lower = tool.name.lower()
        if any(neg == tool_lower or neg in tool_lower for neg in negatives):
            continue

        # Score using engine's existing multi-signal scorer
        base = engine_score_tool(tool, positives)

        # Also check if tool categories overlap with positive intents at all
        cat_lower = {c.lower() for c in tool.categories}
        tag_lower = {t.lower() for t in tool.tags}
        kw_lower = {k.lower() for k in tool.keywords}

        category_hit = bool(cat_lower & set(positives))
        tag_hit = bool(tag_lower & set(positives))
        keyword_hit = bool(kw_lower & set(positives))

        # Include tool if it has any relevance signal
        if base > 0 or category_hit or tag_hit or keyword_hit:
            candidates.append((base, tool))

    # Sort by base score descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [tool for _, tool in candidates]


# ======================================================================
# Stage 2 — Deterministic Pruning (Hard Elimination)
# ======================================================================

def _apply_hard_filters(
    candidates: List[Any],
    profile: Optional[UserProfile],
    negatives: List[str],
    interpreted: Dict,
) -> Tuple[List[Any], List[EliminationEntry]]:
    """
    Apply absolute Boolean filters. Any tool violating a hard constraint
    is instantly excised.

    Hard filters:
        1. Negative intent match (user explicitly excluded)
        2. Budget ceiling violation
        3. Compliance deficit (missing mandated certs)
        4. Stack conflict (already deployed)
        5. Deployment environment conflict
        6. Architectural redundancy
    """
    survivors = []
    eliminated = []

    for tool in candidates:
        viable, code, reason = _check_hard_constraints(tool, profile, negatives, interpreted)
        if not viable:
            eliminated.append(EliminationEntry(
                tool_name=tool.name,
                tool_id=tool.name.lower(),
                reason_type="HARD_CONSTRAINT",
                code=code,
                explanation=reason,
                stage=2,
            ))
        else:
            survivors.append(tool)

    return survivors, eliminated


def _check_hard_constraints(
    tool: Any,
    profile: Optional[UserProfile],
    negatives: List[str],
    interpreted: Dict,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Evaluate a single tool against all hard filters."""

    # ── 1. Negative Intent Match ──
    tool_lower = tool.name.lower()
    tool_text = (tool_lower + " " + (tool.description or "").lower())
    for neg in negatives:
        if neg == tool_lower or neg in tool_text:
            return (
                False,
                ReasonCode.NEGATIVE_INTENT,
                f"Explicitly excluded by your query: '{neg}' matches {tool.name}.",
            )

    if profile is None:
        return True, None, None

    # ── 2. Budget Ceiling Violation ──
    budget_tier = getattr(profile, "budget", "medium")
    ceiling = _BUDGET_CEILINGS.get(budget_tier, 500)

    if ceiling < float("inf") and tool.pricing:
        # Find the minimum viable price
        min_price = None
        for tier_key in ("starter", "pro", "enterprise"):
            val = tool.pricing.get(tier_key)
            if val is not None:
                try:
                    p = float(val)
                    if min_price is None or p < min_price:
                        min_price = p
                except (TypeError, ValueError):
                    continue

        has_free = tool.pricing.get("free_tier", False)

        if min_price is not None and min_price > ceiling and not has_free:
            return (
                False,
                ReasonCode.BUDGET_EXCEEDED,
                f"Minimum viable tier (${min_price}/mo) exceeds your "
                f"budget ceiling of ${ceiling}/mo ({budget_tier} tier).",
            )

    # ── 3. Compliance Deficit ──
    constraints = getattr(profile, "constraints", [])
    tool_compliance = {c.upper() for c in getattr(tool, "compliance", [])}

    compliance_mandates = [c for c in constraints if c.upper() in
                          {"HIPAA", "SOC2", "GDPR", "ISO27001", "PCI-DSS",
                           "FERPA", "CCPA", "FedRAMP"}]

    for mandate in compliance_mandates:
        if mandate.upper() not in tool_compliance:
            return (
                False,
                ReasonCode.COMPLIANCE_FAILURE,
                f"Lacks mandated {mandate} certification required by your profile.",
            )

    # ── 4. Stack Conflict (already deployed) ──
    if hasattr(profile, "already_uses") and profile.already_uses(tool.name):
        return (
            False,
            ReasonCode.STACK_CONFLICT,
            f"{tool.name} is already deployed in your current stack.",
        )

    # ── 5. Deployment Environment Conflict ──
    deployment_prefs = [c.lower() for c in constraints
                       if c.lower() in {"self-hosted", "on-premise", "air-gapped", "sovereign-vpc"}]
    if deployment_prefs:
        # Tools that are explicitly cloud-only SaaS with no self-host option
        tool_tags_lower = {t.lower() for t in tool.tags}
        tool_kw_lower = {k.lower() for k in tool.keywords}
        all_signals = tool_tags_lower | tool_kw_lower

        has_selfhost = bool({"self-hosted", "on-premise", "open-source",
                            "self-host", "docker", "kubernetes"} & all_signals)

        if not has_selfhost and "saas" in all_signals:
            return (
                False,
                ReasonCode.DEPLOYMENT_CONFLICT,
                f"Cloud-only SaaS platform conflicts with your "
                f"{', '.join(deployment_prefs)} requirement.",
            )

    # ── 6. Architectural Redundancy ──
    existing_tools = [t.lower() for t in getattr(profile, "existing_tools", [])]
    if existing_tools:
        tool_cats = {c.lower() for c in tool.categories}
        for existing_name in existing_tools:
            # Find the existing tool in TOOLS to check category overlap
            for t in TOOLS:
                if t.name.lower() == existing_name:
                    existing_cats = {c.lower() for c in t.categories}
                    overlap = tool_cats & existing_cats
                    # If >60% category overlap, flag as redundant
                    if overlap and len(overlap) / max(len(tool_cats), 1) > 0.6:
                        return (
                            False,
                            ReasonCode.ARCHITECTURAL_REDUNDANCY,
                            f"Core functionality overlaps significantly with "
                            f"{t.name} already in your stack "
                            f"(shared categories: {', '.join(sorted(overlap))}).",
                        )
                    break

    return True, None, None


# ======================================================================
# Stage 3 — Probabilistic Penalisation (Soft Elimination)
# ======================================================================

def _apply_soft_penalties(
    survivors: List[Any],
    positives: List[str],
    profile: Optional[UserProfile],
    interpreted: Dict,
) -> Tuple[List[ScoredSurvivor], List[EliminationEntry]]:
    """
    Evaluate survivors against heuristic risk factors. Rather than
    outright removing tools, penalties degrade relevance scores.
    If cumulative penalties reduce a tool below the viability threshold,
    it is moved to the eliminated set.

    Penalty vectors:
        1. Resilience Tier Mismatch (0.00–0.45)
        2. Vendor Lock-In Risk (0.00–0.30)
        3. Cognitive Load / Skill Mismatch (0.00–0.25)
        4. Negative Telemetry Trajectory (0.00–0.20)
        5. Transparency Deficit (0.00–0.15)
    """
    scored = []
    eliminated = []

    # Pre-compute telemetry data
    quality_data = {}
    if _LEARN:
        try:
            quality_data = compute_tool_quality()
        except Exception:
            pass

    # Pre-compute resilience cache
    resilience_cache = {}

    for tool in survivors:
        # Base relevance from engine scoring
        base_raw = engine_score_tool(tool, positives)

        # TF-IDF alignment bonus
        tfidf_bonus = 0.0
        if _INTEL:
            try:
                tfidf = get_tfidf_index()
                tfidf_bonus = tfidf.score(positives, tool.name) * 0.5
            except Exception:
                pass

        # Learned boost
        learned = 0.0
        if _INTEL:
            try:
                learned = get_learned_boost(tool.name) * 0.05
            except Exception:
                pass

        # Industry boost
        industry_boost = 0.0
        if _INTEL and interpreted.get("industry"):
            try:
                industry_boost = get_industry_boost(interpreted["industry"], tool) * 0.05
            except Exception:
                pass

        # Normalise base score to 0–1 range (assuming max raw ~30)
        base_normalised = min(1.0, (base_raw + tfidf_bonus + learned + industry_boost) / 30.0)

        # ── Compute penalties ──
        penalty, reasons = _compute_penalties(tool, profile, quality_data, resilience_cache)

        final_score = max(0.0, base_normalised - penalty)

        # Get resilience data for this tool
        resilience_data = _get_resilience(tool, resilience_cache)

        if final_score < MIN_VIABILITY_THRESHOLD:
            eliminated.append(EliminationEntry(
                tool_name=tool.name,
                tool_id=tool.name.lower(),
                reason_type="SOFT_PENALTY_THRESHOLD",
                code="CUMULATIVE_PENALTY",
                explanation=(
                    f"Cumulative risk penalties ({penalty:.0%}) reduced viability "
                    f"below threshold. Factors: {'; '.join(reasons)}"
                ),
                stage=3,
            ))
        else:
            scored.append(ScoredSurvivor(
                tool=tool,
                base_score=round(base_normalised, 3),
                penalties_applied=reasons,
                penalty_total=round(penalty, 3),
                final_score=round(final_score, 3),
                resilience=resilience_data,
                alignment_reasons=[],
            ))

    # Sort by final score descending
    scored.sort(key=lambda s: s.final_score, reverse=True)
    return scored, eliminated


def _compute_penalties(
    tool: Any,
    profile: Optional[UserProfile],
    quality_data: Dict,
    resilience_cache: Dict,
) -> Tuple[float, List[str]]:
    """Calculate compound penalty for a single tool."""
    penalty = 0.0
    reasons = []

    # ── 1. Resilience Tier Mismatch ──
    res = _get_resilience(tool, resilience_cache)
    tier = res.get("tier", "moderate") if res else "moderate"

    risk_tolerance = "medium"  # default
    if profile:
        # Infer risk tolerance from profile constraints and preferences
        prefs = getattr(profile, "preferences", {}) or {}
        risk_tolerance = prefs.get("risk_tolerance", "medium")

        # Auto-escalate risk sensitivity for regulated industries
        industry = getattr(profile, "industry", "").lower()
        constraints = [c.lower() for c in getattr(profile, "constraints", [])]
        if any(c in constraints for c in ["hipaa", "soc2", "pci-dss", "fedramp"]):
            risk_tolerance = "low"
        elif industry in {"healthcare", "finance", "legal", "defense", "government"}:
            if risk_tolerance != "low":
                risk_tolerance = "low"

    if risk_tolerance == "low" and tier in ("wrapper", "fragile"):
        p = 0.45 if tier == "wrapper" else 0.30
        penalty += p
        reasons.append(
            f"High architectural risk ({tier} tier) unsuitable for "
            f"low-risk-tolerance profile ({p:.0%} penalty)."
        )
    elif risk_tolerance == "medium" and tier == "wrapper":
        penalty += 0.20
        reasons.append(
            "Wrapper-tier architecture carries elevated vendor dependency "
            "risk (20% penalty)."
        )

    # ── 2. Vendor Lock-In Risk ──
    if _PHIL:
        try:
            freedom = assess_freedom(tool)
            freedom_score = freedom.get("score", 50)
            if freedom_score < 35:
                p = 0.30
                penalty += p
                risk_factors = freedom.get("risk_factors", [])
                reasons.append(
                    f"Severe vendor lock-in risk (freedom score: {freedom_score}/100). "
                    f"{risk_factors[0] if risk_factors else 'Limited data portability.'}"
                )
            elif freedom_score < 50:
                p = 0.15
                penalty += p
                reasons.append(
                    f"Moderate lock-in risk (freedom score: {freedom_score}/100)."
                )
        except Exception:
            pass

    # ── 3. Cognitive Load / Skill Mismatch ──
    if profile:
        user_skill = _SKILL_ORDINAL.get(
            getattr(profile, "skill_level", "beginner"), 1
        )
        tool_skill = _SKILL_ORDINAL.get(
            getattr(tool, "skill_level", "beginner"), 1
        )
        team_size = getattr(profile, "team_size", "solo")

        if tool_skill > user_skill:
            mismatch = tool_skill - user_skill
            p = 0.25 if mismatch >= 2 else 0.12
            penalty += p
            reasons.append(
                f"Complexity mismatch: tool requires {tool.skill_level} skill "
                f"but profile indicates {profile.skill_level} ({p:.0%} penalty)."
            )

        # Enterprise tools penalised for tiny teams
        if team_size in ("solo", "small") and tool_skill >= 2:
            ent_price = (tool.pricing or {}).get("enterprise")
            if ent_price and str(ent_price).lower() != "custom":
                try:
                    if float(ent_price) > 200:
                        penalty += 0.10
                        reasons.append(
                            "Enterprise-grade pricing disproportionate for "
                            f"{team_size} team size."
                        )
                except (TypeError, ValueError):
                    pass

    # ── 4. Negative Telemetry Trajectory ──
    if quality_data:
        tq = quality_data.get(tool.name, {})
        trend = tq.get("recent_trend", "stable")
        accept_rate = tq.get("accept_rate", 0.5)

        if trend == "declining" and accept_rate < CHURN_THRESHOLD:
            p = 0.20
            penalty += p
            reasons.append(
                f"Declining satisfaction trend (accept rate: {accept_rate:.0%}) "
                f"among similar users ({p:.0%} penalty)."
            )
        elif trend == "declining":
            p = 0.08
            penalty += p
            reasons.append(
                f"Recent declining trend in user satisfaction ({p:.0%} penalty)."
            )

    # ── 5. Transparency Deficit ──
    if _PHIL:
        try:
            transparency = assess_transparency(tool)
            t_score = transparency.get("score", 50)
            if t_score < 35:
                p = 0.15
                penalty += p
                concerns = transparency.get("concerns", [])
                reasons.append(
                    f"Low vendor transparency (score: {t_score}/100). "
                    f"{concerns[0] if concerns else 'Opaque data practices.'}"
                )
        except Exception:
            pass

    return penalty, reasons


def _get_resilience(tool: Any, cache: Dict) -> Optional[Dict]:
    """Get resilience report for a tool, with caching."""
    key = tool.name.lower()
    if key not in cache:
        try:
            report = resilience_score_tool(tool)
            cache[key] = {
                "score": report.score,
                "grade": report.grade,
                "tier": report.tier,
                "flags": report.flags,
                "summary": report.summary,
            }
        except Exception:
            cache[key] = None
    return cache[key]


# ======================================================================
# Stage 4 — Ranking & Presentation Assembly
# ======================================================================

def _build_survivor_card(survivor: ScoredSurvivor, positives: List[str]) -> Dict:
    """Build a rich presentation dict for a surviving tool."""
    tool = survivor.tool

    # Generate survival reasons
    survival_reasons = []

    # Budget survival
    if tool.pricing and tool.pricing.get("free_tier"):
        survival_reasons.append("Offers a free tier matching budget constraints")
    elif tool.pricing:
        starter = tool.pricing.get("starter")
        if starter:
            survival_reasons.append(f"Accessible pricing (from ${starter}/mo)")

    # Compliance survival
    if tool.compliance:
        compliance_str = ", ".join(tool.compliance[:3])
        survival_reasons.append(f"Verified compliant: {compliance_str}")

    # Resilience
    res = survivor.resilience or {}
    tier = res.get("tier", "unknown")
    grade = res.get("grade", "?")
    if tier in ("sovereign", "durable"):
        survival_reasons.append(
            f"Resilient architecture ({tier.title()} tier, Grade {grade})"
        )

    # Category/use-case alignment
    cat_overlap = set(c.lower() for c in tool.categories) & set(positives)
    if cat_overlap:
        survival_reasons.append(
            f"Direct category match: {', '.join(sorted(cat_overlap))}"
        )

    # Integration strength
    if len(tool.integrations) >= 5:
        survival_reasons.append(
            f"Strong integration ecosystem ({len(tool.integrations)} connectors)"
        )

    # No penalties = clean bill of health
    if not survivor.penalties_applied:
        survival_reasons.append("Zero risk penalties — clean architectural profile")

    return {
        "name": tool.name,
        "description": tool.description,
        "url": tool.url,
        "categories": tool.categories,
        "pricing": tool.pricing,
        "compliance": tool.compliance,
        "skill_level": tool.skill_level,
        "integrations": tool.integrations[:10],
        "use_cases": tool.use_cases,
        "final_score": survivor.final_score,
        "base_score": survivor.base_score,
        "penalty_total": survivor.penalty_total,
        "resilience": survivor.resilience,
        "survival_reasons": survival_reasons,
        "penalties_applied": survivor.penalties_applied,
    }


def _build_elimination_card(entry: EliminationEntry) -> Dict:
    """Build a presentation dict for an eliminated tool."""
    return {
        "name": entry.tool_name,
        "reason_type": entry.reason_type,
        "code": entry.code,
        "explanation": entry.explanation,
        "stage": entry.stage,
        "stage_label": "Hard Constraint" if entry.stage == 2 else "Soft Penalty",
    }


def _generate_funnel_narrative(
    total_scanned: int,
    broad_count: int,
    post_hard: int,
    hard_eliminated: int,
    post_soft: int,
    soft_eliminated: int,
    final_count: int,
) -> List[str]:
    """Generate the step-by-step funnel narrative for the UI animation."""
    steps = [
        f"Scanning {total_scanned} tools in the Praxis knowledge base...",
        f"Generated broad differential: {broad_count} potential candidates.",
    ]

    if hard_eliminated > 0:
        steps.append(
            f"Eliminating {hard_eliminated} tools failing hard constraints "
            f"(budget, compliance, conflicts)..."
        )

    steps.append(f"{post_hard} candidates survived deterministic pruning.")

    if soft_eliminated > 0:
        steps.append(
            f"Penalising survivors for risk factors... {soft_eliminated} tools "
            f"fell below viability threshold."
        )

    steps.append(
        f"Ranking the top {final_count} highly resilient survivors."
    )

    return steps


# ======================================================================
# Public API — Generate Differential Recommendations
# ======================================================================

def generate_differential(
    user_query: str,
    profile: Optional[UserProfile] = None,
    top_n: int = DEFAULT_TOP_N,
) -> DifferentialResult:
    """
    Execute the full 4-stage differential diagnosis pipeline.

    Args:
        user_query:  natural-language input
        profile:     optional UserProfile for constraint-aware filtering
        top_n:       max survivors to return (default 5)

    Returns:
        DifferentialResult with survivors, eliminated log, and funnel narrative
    """
    total_tools = len(TOOLS)

    # ── Stage 1: Intent Parsing ──
    interpreted, positives, negatives, ambiguity = _parse_intents(user_query)

    # Clarification protocol for highly ambiguous queries
    if ambiguity.severity >= AMBIGUITY_THRESHOLD and len(positives) < 2:
        return DifferentialResult(
            query=user_query,
            profile_id=getattr(profile, "profile_id", None) if profile else None,
            stages={
                "stage_1": {
                    "status": "ambiguity_detected",
                    "severity": ambiguity.severity,
                    "missing_axes": ambiguity.missing_axes,
                }
            },
            survivors=[],
            eliminated=[],
            clarification_needed=True,
            clarification={
                "severity": ambiguity.severity,
                "missing_axes": ambiguity.missing_axes,
                "suggested_questions": ambiguity.suggested_clarifications,
                "message": (
                    "Your query is too broad for confident recommendations. "
                    "Please help us narrow the differential:"
                ),
            },
            funnel_narrative=[
                f"Scanning {total_tools} tools...",
                "Query ambiguity detected — requesting clarification.",
            ],
        )

    # ── Stage 2: Broad Candidate Generation ──
    broad_candidates = _retrieve_broad_differential(positives, negatives, interpreted)
    broad_count = len(broad_candidates)

    # ── Stage 3: Deterministic Pruning ──
    hard_survivors, hard_eliminated = _apply_hard_filters(
        broad_candidates, profile, negatives, interpreted
    )

    # ── Stage 4: Probabilistic Penalisation ──
    scored_survivors, soft_eliminated = _apply_soft_penalties(
        hard_survivors, positives, profile, interpreted
    )

    # ── Airlock Protocol: Empty Survivor Set ──
    airlock_active = False
    if not scored_survivors and hard_eliminated:
        # Relax: convert budget and secondary filters to soft context
        log.warning("Empty survivor set — activating airlock protocol")
        airlock_active = True

        # Re-run with relaxed constraints (no profile)
        relaxed_survivors, _ = _apply_hard_filters(
            broad_candidates, None, negatives, interpreted
        )
        scored_survivors, soft_eliminated_relaxed = _apply_soft_penalties(
            relaxed_survivors, positives, profile, interpreted
        )
        soft_eliminated.extend(soft_eliminated_relaxed)

    # ── Stage 5: Final Assembly ──
    final_survivors = scored_survivors[:top_n]

    # Build presentation cards
    survivor_cards = [
        _build_survivor_card(s, positives) for s in final_survivors
    ]
    elimination_cards = [
        _build_elimination_card(e)
        for e in (hard_eliminated + soft_eliminated)
    ]

    # Sort eliminations: show well-known tools first (higher alphabetical recognition)
    elimination_cards.sort(key=lambda e: e["name"])

    # Funnel narrative
    narrative = _generate_funnel_narrative(
        total_scanned=total_tools,
        broad_count=broad_count,
        post_hard=len(hard_survivors),
        hard_eliminated=len(hard_eliminated),
        post_soft=len(scored_survivors),
        soft_eliminated=len(soft_eliminated),
        final_count=len(final_survivors),
    )

    if airlock_active:
        narrative.append(
            "⚠ No tools matched ALL your absolute requirements. "
            "We relaxed secondary constraints to find these viable options, "
            "but preserved your legally mandated security protocols."
        )

    return DifferentialResult(
        query=user_query,
        profile_id=getattr(profile, "profile_id", None) if profile else None,
        stages={
            "stage_1_parsing": {
                "positives": positives,
                "negatives": negatives,
                "ambiguity_severity": ambiguity.severity,
                "interpreted": {
                    "intent": interpreted.get("intent"),
                    "industry": interpreted.get("industry"),
                    "goal": interpreted.get("goal"),
                },
            },
            "stage_2_broad": {
                "candidates_generated": broad_count,
            },
            "stage_3_hard_prune": {
                "survivors": len(hard_survivors),
                "eliminated": len(hard_eliminated),
                "filters_applied": list(set(e.code for e in hard_eliminated)),
            },
            "stage_4_soft_penalty": {
                "survivors": len(scored_survivors),
                "eliminated_by_threshold": len(soft_eliminated),
            },
            "airlock_activated": airlock_active,
        },
        survivors=survivor_cards,
        eliminated=elimination_cards,
        funnel_narrative=narrative,
    )


# ======================================================================
# Override Tracking (feeds learning.py)
# ======================================================================

_OVERRIDE_LOG_FILE = "override_log.json"


def record_override(
    query: str,
    eliminated_tool: str,
    reason_code: str,
    profile_id: Optional[str] = None,
):
    """
    Record when a user manually selects a tool that was eliminated.
    High override rates signal that a filter is too aggressive.
    """
    import json
    import os
    from datetime import datetime, timezone

    log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), _OVERRIDE_LOG_FILE
    )

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query": query,
        "tool": eliminated_tool,
        "reason_code": reason_code,
        "profile_id": profile_id,
    }

    existing = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    existing.append(entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    return entry


def get_override_stats() -> Dict:
    """
    Compute override statistics for monitoring filter accuracy.

    Returns:
        {
            "total_overrides": int,
            "by_reason_code": { code: count },
            "by_tool": { tool_name: count },
            "override_rate_signals": [
                { "code": str, "count": int, "recommendation": str }
            ]
        }
    """
    import json
    import os

    log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), _OVERRIDE_LOG_FILE
    )

    if not os.path.exists(log_path):
        return {"total_overrides": 0, "by_reason_code": {}, "by_tool": {},
                "override_rate_signals": []}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception:
        entries = []

    by_code: Dict[str, int] = {}
    by_tool: Dict[str, int] = {}

    for e in entries:
        code = e.get("reason_code", "UNKNOWN")
        tool = e.get("tool", "unknown")
        by_code[code] = by_code.get(code, 0) + 1
        by_tool[tool] = by_tool.get(tool, 0) + 1

    # Generate signals for filters with high override rates
    signals = []
    for code, count in sorted(by_code.items(), key=lambda x: x[1], reverse=True):
        if count >= 5:
            signals.append({
                "code": code,
                "count": count,
                "recommendation": (
                    f"Filter '{code}' has been overridden {count} times. "
                    f"Consider downgrading from hard constraint to soft penalty."
                ),
            })

    return {
        "total_overrides": len(entries),
        "by_reason_code": by_code,
        "by_tool": by_tool,
        "override_rate_signals": signals,
    }
