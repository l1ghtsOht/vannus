# ────────── Context-Aware Intent Transfer Engine ──────────
"""
Multi-stage context extraction and confidence scoring engine.

Extracts implicit operator context from free-form queries, enriches via
vertical intelligence and graph traversal, scores each field with a
deterministic confidence heuristic, and assigns tier levels for downstream
gap analysis.

Confidence formula:
    C(P) = α(T_match/T_total) + β(1/(1+D_graph)) + γ(S_prox) + δ(M_ex)

Tiers:
    T1 (≥ 0.90) — auto-commit to profile
    T2 (0.60–0.89) — pre-fill with default, ask for confirmation
    T3 (< 0.60) — must ask operator
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.context_engine")

# ── Imports (resilient) ──────────────────────────────────────────────
try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg  # type: ignore[no-redef]
    except Exception:
        _cfg = None  # type: ignore[assignment]

try:
    from .interpreter import interpret, _KNOWN_TOOLS
except Exception:
    try:
        from interpreter import interpret, _KNOWN_TOOLS  # type: ignore[no-redef]
    except Exception:
        interpret = None  # type: ignore[assignment]
        _KNOWN_TOOLS = set()

try:
    from .verticals import detect_verticals, extract_constraints, recommend_vertical_stack
except Exception:
    try:
        from verticals import detect_verticals, extract_constraints, recommend_vertical_stack  # type: ignore[no-redef]
    except Exception:
        detect_verticals = None  # type: ignore[assignment]
        extract_constraints = None  # type: ignore[assignment]
        recommend_vertical_stack = None  # type: ignore[assignment]

try:
    from .intelligence import expand_synonyms, TFIDFIndex
except Exception:
    try:
        from intelligence import expand_synonyms, TFIDFIndex  # type: ignore[no-redef]
    except Exception:
        expand_synonyms = None  # type: ignore[assignment]
        TFIDFIndex = None  # type: ignore[assignment]

try:
    from .profile import load_profile, UserProfile
except Exception:
    try:
        from profile import load_profile, UserProfile  # type: ignore[no-redef]
    except Exception:
        load_profile = None  # type: ignore[assignment]
        UserProfile = None  # type: ignore[assignment]


# ── Configuration helpers ────────────────────────────────────────────

def _conf(key: str, fallback):
    """Read a config value with fallback."""
    if _cfg:
        return _cfg.get(key, fallback)
    return fallback


# ── Tier thresholds ──────────────────────────────────────────────────

TIER_1 = 1  # auto-commit
TIER_2 = 2  # pre-fill
TIER_3 = 3  # ask


# ═══════════════════════════════════════════════════════════════════
# Data Types
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FieldExtraction:
    """Single field extraction result with confidence metadata."""
    value: Any
    confidence: float = 0.0
    tier: int = TIER_3
    source: str = "none"  # "explicit" | "inferred" | "graph" | "vertical" | "none"
    evidence: str = ""


@dataclass
class ContextVector:
    """Multi-dimensional extraction result from a single query.

    Each profile-relevant field has both a value and a confidence score.
    Tier assignments determine downstream behaviour:
      T1 — auto-commit (confidence ≥ 0.90)
      T2 — pre-fill with default (0.60 ≤ confidence < 0.90)
      T3 — must ask operator (confidence < 0.60)
    """
    raw_query: str = ""

    # ── Field extractions ──
    task_type: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))
    industry: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))
    budget: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))
    existing_tools: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=[]))
    team_size: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))
    skill_level: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))
    compliance: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=[]))
    constraints: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=[]))
    timeline: FieldExtraction = field(default_factory=lambda: FieldExtraction(value=None))

    # ── Enrichment data (from verticals / graph) ──
    vertical_matches: List[Dict[str, Any]] = field(default_factory=list)
    constraint_profile: Any = None  # ConstraintProfile from verticals
    stack_template: Optional[Dict[str, Any]] = None
    graph_neighbors: List[str] = field(default_factory=list)
    pruned_tools: List[str] = field(default_factory=list)  # tools eliminated by compliance

    # ── Metadata ──
    extraction_time_ms: float = 0.0
    interpreter_output: Dict[str, Any] = field(default_factory=dict)

    # ── Convenience accessors ──

    @property
    def all_fields(self) -> Dict[str, FieldExtraction]:
        """Return all profile-relevant field extractions."""
        return {
            "task_type": self.task_type,
            "industry": self.industry,
            "budget": self.budget,
            "existing_tools": self.existing_tools,
            "team_size": self.team_size,
            "skill_level": self.skill_level,
            "compliance": self.compliance,
            "constraints": self.constraints,
            "timeline": self.timeline,
        }

    @property
    def tier_assignments(self) -> Dict[str, int]:
        """Map each field name to its assigned tier."""
        return {name: fe.tier for name, fe in self.all_fields.items()}

    @property
    def t1_fields(self) -> Dict[str, Any]:
        """Fields confident enough for auto-commit."""
        return {n: fe.value for n, fe in self.all_fields.items() if fe.tier == TIER_1}

    @property
    def t2_fields(self) -> Dict[str, Any]:
        """Fields good enough for pre-fill defaults."""
        return {n: fe.value for n, fe in self.all_fields.items() if fe.tier == TIER_2}

    @property
    def t3_fields(self) -> List[str]:
        """Field names that must be asked."""
        return [n for n, fe in self.all_fields.items() if fe.tier == TIER_3]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise for API responses."""
        result = {
            "raw_query": self.raw_query,
            "fields": {},
            "tier_assignments": self.tier_assignments,
            "auto_filled": self.t1_fields,
            "pre_filled": self.t2_fields,
            "missing": self.t3_fields,
            "vertical_matches": self.vertical_matches,
            "stack_template": self.stack_template,
            "graph_neighbors": self.graph_neighbors,
            "pruned_tools": self.pruned_tools,
            "extraction_time_ms": round(self.extraction_time_ms, 2),
        }
        for name, fe in self.all_fields.items():
            result["fields"][name] = {
                "value": fe.value,
                "confidence": round(fe.confidence, 4),
                "tier": fe.tier,
                "source": fe.source,
                "evidence": fe.evidence,
            }
        return result


# ═══════════════════════════════════════════════════════════════════
# Extraction Heuristics
# ═══════════════════════════════════════════════════════════════════

# ── Team size ────────────────────────────────────────────────────────

_TEAM_SIZE_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    # "team of 15", "15 employees", "staff of 8"
    (re.compile(r"\b(?:team\s+of|staff\s+of|(\d+)\s+(?:employees?|people|staff|workers?|technicians?|developers?|engineers?))\b", re.I), "numeric", ""),
    (re.compile(r"\b(\d+)\s*(?:employees?|people|staff|workers?|technicians?|developers?|engineers?)\b", re.I), "numeric", ""),
    # Qualitative
    (re.compile(r"\b(?:just\s+me|solo|one[\s-]?man|one[\s-]?person|solopreneur|freelancer?)\b", re.I), "solo", "explicit_marker"),
    (re.compile(r"\b(?:small\s+team|few\s+people|startup|co-?founder)\b", re.I), "small", "explicit_marker"),
    (re.compile(r"\b(?:growing\s+team|mid[\s-]?size|department)\b", re.I), "medium", "explicit_marker"),
    (re.compile(r"\b(?:enterprise|large\s+(?:team|org)|company[\s-]?wide|hundreds?\s+of)\b", re.I), "large", "explicit_marker"),
]

# Numeric → enum thresholds
_TEAM_THRESHOLDS = [(1, "solo"), (10, "small"), (50, "medium"), (float("inf"), "large")]


def _extract_team_size(query: str) -> FieldExtraction:
    """Infer team size from query text."""
    q = query.lower()

    # Try numeric patterns first (highest confidence)
    numeric_pat = re.compile(
        r"\b(\d+)\s*(?:employees?|people|staff|workers?|technicians?|developers?|engineers?|members?)\b", re.I
    )
    m = numeric_pat.search(query)
    if m:
        count = int(m.group(1))
        enum_val = "large"
        for threshold, label in _TEAM_THRESHOLDS:
            if count <= threshold:
                enum_val = label
                break
        return FieldExtraction(
            value=enum_val, confidence=0.95, tier=TIER_1,
            source="explicit", evidence=f"numeric: {count} → {enum_val}",
        )

    # Try "team of N"
    team_of = re.compile(r"\bteam\s+of\s+(\d+)\b", re.I)
    m = team_of.search(query)
    if m:
        count = int(m.group(1))
        enum_val = "large"
        for threshold, label in _TEAM_THRESHOLDS:
            if count <= threshold:
                enum_val = label
                break
        return FieldExtraction(
            value=enum_val, confidence=0.92, tier=TIER_1,
            source="explicit", evidence=f"team of {count} → {enum_val}",
        )

    # Qualitative markers
    qualitative = [
        (r"\b(?:just\s+me|solo|one[\s-]?man|one[\s-]?person|solopreneur|freelancer?)\b", "solo"),
        (r"\b(?:small\s+team|few\s+people|startup|co-?founder)\b", "small"),
        (r"\b(?:growing\s+team|mid[\s-]?size|department)\b", "medium"),
        (r"\b(?:enterprise|large\s+(?:team|org)|company[\s-]?wide|hundreds?\s+of)\b", "large"),
    ]
    for pat, size in qualitative:
        if re.search(pat, query, re.I):
            return FieldExtraction(
                value=size, confidence=0.75, tier=TIER_2,
                source="inferred", evidence=f"qualitative marker → {size}",
            )

    # Possessive plural heuristic ("my technicians", "our developers")
    if re.search(r"\b(?:my|our)\s+\w+s\b", q):
        return FieldExtraction(
            value="small", confidence=0.45, tier=TIER_3,
            source="inferred", evidence="possessive plural suggests team",
        )

    return FieldExtraction(value=None, source="none")


# ── Budget ───────────────────────────────────────────────────────────

_BUDGET_EXPLICIT = re.compile(
    r"\$\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(?:/\s*)?(?:mo(?:nth)?|yr|year|annual(?:ly)?|per\s+month|per\s+year|p/?m)?",
    re.I,
)
_BUDGET_QUALITATIVE = [
    (r"\b(?:free\s+(?:tier|plan|version|tools?)|no[\s-]?cost|zero[\s-]?budget|\$0)\b", "free", 0.92),
    (r"\bunder\s+\$\s*\d", "low", 0.80),  # also captured by explicit
    (r"\b(?:cheap|affordable|budget[\s-]?friendly|low[\s-]?cost|inexpensive)\b", "low", 0.70),
    (r"\b(?:premium|enterprise[\s-]?grade|money\s+is\s+no\s+object|unlimited\s+budget)\b", "high", 0.75),
    (r"\b(?:mid[\s-]?range|moderate|reasonable)\b", "medium", 0.65),
]


def _extract_budget(query: str) -> FieldExtraction:
    """Infer budget level from query text."""
    # Explicit dollar amount — highest confidence
    m = _BUDGET_EXPLICIT.search(query)
    if m:
        raw_amount = m.group(1).replace(",", "")
        try:
            amount = float(raw_amount)
        except ValueError:
            amount = 0.0
        # Normalise to monthly if annual
        full_match = m.group(0).lower()
        if any(t in full_match for t in ("yr", "year", "annual")):
            amount /= 12

        if amount == 0:
            tier_val = "free"
        elif amount < 50:
            tier_val = "low"
        elif amount < 200:
            tier_val = "medium"
        else:
            tier_val = "high"

        return FieldExtraction(
            value=tier_val, confidence=0.95, tier=TIER_1,
            source="explicit", evidence=f"${raw_amount} → {tier_val}",
        )

    # Qualitative budget markers
    for pat, tier_val, conf in _BUDGET_QUALITATIVE:
        if re.search(pat, query, re.I):
            tier = TIER_1 if conf >= 0.90 else TIER_2
            return FieldExtraction(
                value=tier_val, confidence=conf, tier=tier,
                source="inferred", evidence=f"budget marker → {tier_val}",
            )

    return FieldExtraction(value=None, source="none")


# ── Skill level ──────────────────────────────────────────────────────

_SKILL_MARKERS = [
    # Beginner signals
    (r"\b(?:no[\s-]?code|low[\s-]?code|simple|easy|beginner|non[\s-]?technical|drag[\s-]?and[\s-]?drop|no\s+coding)\b",
     "beginner", 0.85),
    # Advanced signals
    (r"\b(?:api[\s-]?first|developer|sdk|custom[\s-]?integration|self[\s-]?host|open[\s-]?source|cli|terraform|kubernetes|k8s|docker)\b",
     "advanced", 0.85),
    # Intermediate (weaker signals)
    (r"\b(?:some\s+(?:technical|coding)\s+(?:experience|knowledge)|intermediate|power[\s-]?user)\b",
     "intermediate", 0.70),
]


def _extract_skill_level(query: str) -> FieldExtraction:
    """Infer operator skill level from query text."""
    for pat, level, conf in _SKILL_MARKERS:
        if re.search(pat, query, re.I):
            tier = TIER_1 if conf >= 0.90 else TIER_2
            return FieldExtraction(
                value=level, confidence=conf, tier=tier,
                source="inferred", evidence=f"skill marker → {level}",
            )
    return FieldExtraction(value=None, source="none")


# ── Timeline ─────────────────────────────────────────────────────────

_TIMELINE_MARKERS = [
    (r"\b(?:asap|urgent|immediately|today|right\s+now|this\s+week|deploy\s+(?:now|today|tomorrow))\b",
     "immediate", 0.88),
    (r"\b(?:next\s+(?:week|month|sprint)|soon|short[\s-]?term|within\s+\d+\s+(?:days?|weeks?))\b",
     "short_term", 0.75),
    (r"\b(?:planning|evaluating|researching|Q[1-4]|next\s+(?:quarter|year)|long[\s-]?term|roadmap)\b",
     "planning", 0.70),
]


def _extract_timeline(query: str) -> FieldExtraction:
    """Infer deployment/adoption timeline from query text."""
    for pat, phase, conf in _TIMELINE_MARKERS:
        if re.search(pat, query, re.I):
            tier = TIER_1 if conf >= 0.90 else TIER_2
            return FieldExtraction(
                value=phase, confidence=conf, tier=tier,
                source="inferred", evidence=f"timeline marker → {phase}",
            )
    return FieldExtraction(value=None, source="none")


# ── Existing tools ───────────────────────────────────────────────────

def _extract_existing_tools(query: str, entities: Optional[List[str]] = None) -> FieldExtraction:
    """Detect known tools mentioned in the query."""
    found: List[str] = []
    q_lower = query.lower()

    # Check entities from interpreter first
    if entities:
        for ent in entities:
            if ent.lower() in _KNOWN_TOOLS or ent.lower() in q_lower:
                if ent not in found:
                    found.append(ent)

    # Scan for known tools in query text
    for tool_name in _KNOWN_TOOLS:
        if tool_name in q_lower and tool_name not in [f.lower() for f in found]:
            found.append(tool_name)

    if found:
        conf = min(0.95, 0.80 + 0.05 * len(found))
        return FieldExtraction(
            value=found, confidence=conf, tier=TIER_1 if conf >= 0.90 else TIER_2,
            source="explicit", evidence=f"known tools: {', '.join(found)}",
        )
    return FieldExtraction(value=[], source="none")


# ═══════════════════════════════════════════════════════════════════
# Confidence Formula
# ═══════════════════════════════════════════════════════════════════

def compute_confidence(
    term_match_ratio: float = 0.0,
    graph_distance: float = float("inf"),
    syntactic_proximity: float = 0.0,
    explicit_match: float = 0.0,
) -> float:
    """Deterministic confidence heuristic.

    C(P) = α(T_match/T_total) + β(1/(1+D_graph)) + γ(S_prox) + δ(M_ex)

    All inputs should be normalised to [0, 1] except graph_distance (≥ 0).
    """
    alpha = _conf("context_alpha", 0.25)
    beta = _conf("context_beta", 0.30)
    gamma = _conf("context_gamma", 0.25)
    delta = _conf("context_delta", 0.20)

    score = (
        alpha * min(1.0, max(0.0, term_match_ratio))
        + beta * (1.0 / (1.0 + max(0.0, graph_distance)))
        + gamma * min(1.0, max(0.0, syntactic_proximity))
        + delta * min(1.0, max(0.0, explicit_match))
    )
    return min(1.0, max(0.0, score))


def assign_tier(confidence: float) -> int:
    """Map a confidence score to a tier level."""
    t1 = _conf("context_tier1_threshold", 0.90)
    t2 = _conf("context_tier2_threshold", 0.60)
    if confidence >= t1:
        return TIER_1
    elif confidence >= t2:
        return TIER_2
    return TIER_3


# ═══════════════════════════════════════════════════════════════════
# Main Extraction Pipeline
# ═══════════════════════════════════════════════════════════════════

def extract_context(
    query: str,
    *,
    profile_id: Optional[str] = None,
) -> ContextVector:
    """Primary entry point — extract implicit context from a free-form query.

    Pipeline:
        1. interpret() for baseline extraction
        2. detect_verticals() for vertical intelligence
        3. extract_constraints() for compliance/deployment
        4. Field-specific extractors (team, budget, skill, timeline, tools)
        5. Confidence scoring and tier assignment
        6. Optional profile enrichment

    Returns a fully-populated ContextVector.
    """
    t0 = time.perf_counter()
    cv = ContextVector(raw_query=query)

    # ── Step 1: Interpreter baseline ──
    interp = {}
    if interpret is not None:
        try:
            interp = interpret(query)
        except Exception as exc:
            log.warning("interpret() failed: %s", exc)
    cv.interpreter_output = interp

    raw_intent = interp.get("intent")
    raw_industry = interp.get("industry")
    keywords = interp.get("keywords", [])
    entities = interp.get("entities", [])

    # ── Step 2: Vertical detection ──
    if detect_verticals is not None:
        try:
            verticals = detect_verticals(
                query, keywords=keywords, industry=raw_industry,
            )
            cv.vertical_matches = verticals
        except Exception as exc:
            log.warning("detect_verticals() failed: %s", exc)

    # ── Step 3: Constraint extraction ──
    if extract_constraints is not None:
        try:
            cp = extract_constraints(
                query, keywords=keywords, industry=raw_industry,
                verticals=cv.vertical_matches or None,
            )
            cv.constraint_profile = cp
        except Exception as exc:
            log.warning("extract_constraints() failed: %s", exc)

    # ── Step 4: Field-specific extractors ──

    # Task type — from interpreter intent
    if raw_intent:
        cv.task_type = FieldExtraction(
            value=raw_intent,
            confidence=compute_confidence(
                term_match_ratio=0.8, syntactic_proximity=0.9,
                explicit_match=1.0 if raw_intent else 0.0,
            ),
            source="explicit" if raw_intent else "none",
            evidence=f"interpreter intent: {raw_intent}",
        )
        cv.task_type.tier = assign_tier(cv.task_type.confidence)

    # Industry — from interpreter + verticals
    if raw_industry:
        vert_boost = 0.0
        if cv.vertical_matches:
            top_vert = cv.vertical_matches[0]
            vert_conf = top_vert.get("confidence", 0.0)
            if top_vert.get("vertical_id", "").replace("_", " ") in raw_industry or raw_industry in str(top_vert.get("signals", [])):
                vert_boost = vert_conf * 0.3
        cv.industry = FieldExtraction(
            value=raw_industry,
            confidence=min(1.0, compute_confidence(
                term_match_ratio=0.7, syntactic_proximity=0.8,
                explicit_match=1.0,
            ) + vert_boost),
            source="explicit",
            evidence=f"interpreter industry: {raw_industry}",
        )
        cv.industry.tier = assign_tier(cv.industry.confidence)
    elif cv.vertical_matches:
        top = cv.vertical_matches[0]
        cv.industry = FieldExtraction(
            value=top.get("vertical_id", ""),
            confidence=top.get("confidence", 0.0) * 0.85,
            source="vertical",
            evidence=f"top vertical: {top.get('vertical_id')} (conf={top.get('confidence', 0):.2f})",
        )
        cv.industry.tier = assign_tier(cv.industry.confidence)

    # Budget
    cv.budget = _extract_budget(query)

    # Team size
    cv.team_size = _extract_team_size(query)

    # Skill level
    cv.skill_level = _extract_skill_level(query)

    # Timeline
    cv.timeline = _extract_timeline(query)

    # Existing tools
    cv.existing_tools = _extract_existing_tools(query, entities)

    # Compliance — from constraint profile
    if cv.constraint_profile is not None:
        comp_list = getattr(cv.constraint_profile, "compliance_required", [])
        reg_list = getattr(cv.constraint_profile, "regulatory", [])
        all_comp = list(set(comp_list + reg_list))
        if all_comp:
            cv.compliance = FieldExtraction(
                value=all_comp,
                confidence=0.85,
                tier=TIER_2,
                source="vertical",
                evidence=f"constraint extraction: {', '.join(all_comp)}",
            )

    # Constraints — from constraint profile
    if cv.constraint_profile is not None:
        anti = getattr(cv.constraint_profile, "anti_patterns_triggered", [])
        deploy = getattr(cv.constraint_profile, "deployment", "any")
        sov = getattr(cv.constraint_profile, "data_sovereignty", "standard")
        constraint_list = []
        if deploy != "any":
            constraint_list.append(f"deployment:{deploy}")
        if sov != "standard":
            constraint_list.append(f"sovereignty:{sov}")
        constraint_list.extend(anti)
        if constraint_list:
            cv.constraints = FieldExtraction(
                value=constraint_list,
                confidence=0.80,
                tier=TIER_2,
                source="vertical",
                evidence=f"constraint profile: {', '.join(constraint_list)}",
            )

    # ── Step 5: Stack template enrichment ──
    if recommend_vertical_stack is not None and cv.vertical_matches:
        top_vert = cv.vertical_matches[0]
        if top_vert.get("confidence", 0) >= 0.5:
            try:
                budget_val = cv.budget.value if cv.budget.value else None
                stack = recommend_vertical_stack(
                    top_vert["vertical_id"],
                    budget=budget_val,
                )
                cv.stack_template = stack
            except Exception as exc:
                log.warning("recommend_vertical_stack() failed: %s", exc)

    # ── Step 6: Profile enrichment (if profile exists) ──
    if profile_id and load_profile is not None:
        try:
            profile = load_profile(profile_id)
            if profile:
                _enrich_from_profile(cv, profile)
        except Exception as exc:
            log.warning("Profile enrichment failed: %s", exc)

    cv.extraction_time_ms = (time.perf_counter() - t0) * 1000
    log.info(
        "Context extracted in %.1fms | T1=%d T2=%d T3=%d",
        cv.extraction_time_ms,
        len(cv.t1_fields),
        len(cv.t2_fields),
        len(cv.t3_fields),
    )
    return cv


def _enrich_from_profile(cv: ContextVector, profile) -> None:
    """Boost confidence of fields that align with an existing profile."""
    if not profile:
        return

    # If industry matches profile, boost confidence
    if cv.industry.value and hasattr(profile, "industry") and profile.industry:
        if cv.industry.value.lower() == profile.industry.lower():
            cv.industry.confidence = min(1.0, cv.industry.confidence + 0.15)
            cv.industry.tier = assign_tier(cv.industry.confidence)
            cv.industry.evidence += " | profile match boost"

    # If tools overlap with profile existing_tools, boost
    if cv.existing_tools.value and hasattr(profile, "existing_tools") and profile.existing_tools:
        profile_tools = {t.lower() for t in profile.existing_tools}
        extracted_tools = {t.lower() for t in cv.existing_tools.value}
        overlap = profile_tools & extracted_tools
        if overlap:
            cv.existing_tools.confidence = min(1.0, cv.existing_tools.confidence + 0.10)
            cv.existing_tools.tier = assign_tier(cv.existing_tools.confidence)
            cv.existing_tools.evidence += f" | profile overlap: {', '.join(overlap)}"

    # If no budget extracted but profile has one, use as weak default
    if cv.budget.value is None and hasattr(profile, "budget") and profile.budget:
        cv.budget = FieldExtraction(
            value=profile.budget, confidence=0.55, tier=TIER_3,
            source="inferred", evidence=f"profile default: {profile.budget}",
        )

    # Same for team_size
    if cv.team_size.value is None and hasattr(profile, "team_size") and profile.team_size:
        cv.team_size = FieldExtraction(
            value=profile.team_size, confidence=0.50, tier=TIER_3,
            source="inferred", evidence=f"profile default: {profile.team_size}",
        )

    # Same for skill_level
    if cv.skill_level.value is None and hasattr(profile, "skill_level") and profile.skill_level:
        cv.skill_level = FieldExtraction(
            value=profile.skill_level, confidence=0.50, tier=TIER_3,
            source="inferred", evidence=f"profile default: {profile.skill_level}",
        )


# ═══════════════════════════════════════════════════════════════════
# Graph Enrichment (Phase 2.3 — called after graph methods are ready)
# ═══════════════════════════════════════════════════════════════════

def enrich_via_graph(cv: ContextVector, tool_graph=None) -> ContextVector:
    """Enrich a ContextVector using graph traversal.

    - Anchor tools → subgraph neighbors (integrates_with edges)
    - Vertical stacks → tool candidate pool
    - Compliance requirements → prune non-compliant tools

    Mutates and returns the same ContextVector.
    """
    if tool_graph is None:
        return cv

    # ── Anchor subgraph ──
    if cv.existing_tools.value:
        for tool_name in cv.existing_tools.value:
            try:
                if hasattr(tool_graph, "get_anchor_subgraph"):
                    subgraph = tool_graph.get_anchor_subgraph(tool_name, max_hops=2)
                    if subgraph:
                        for node_name in subgraph:
                            if node_name not in cv.graph_neighbors:
                                cv.graph_neighbors.append(node_name)
                elif hasattr(tool_graph, "local_search"):
                    result = tool_graph.local_search(
                        tool_name, hops=2,
                        rel_filter={"integrates_with"},
                    )
                    if result and hasattr(result, "nodes"):
                        for node in result.nodes:
                            name = node.name if hasattr(node, "name") else str(node)
                            if name not in cv.graph_neighbors:
                                cv.graph_neighbors.append(name)
            except Exception as exc:
                log.debug("Graph anchor search failed for %s: %s", tool_name, exc)

    # ── Vertical stack tools ──
    if cv.vertical_matches and hasattr(tool_graph, "get_vertical_stack_tools"):
        top = cv.vertical_matches[0]
        if top.get("confidence", 0) >= 0.5:
            try:
                stack_tools = tool_graph.get_vertical_stack_tools(top["vertical_id"])
                for t in stack_tools:
                    if t not in cv.graph_neighbors:
                        cv.graph_neighbors.append(t)
            except Exception as exc:
                log.debug("Vertical stack tools failed: %s", exc)

    # ── Compliance pruning ──
    if cv.compliance.value and hasattr(tool_graph, "prune_non_compliant"):
        try:
            pruned = tool_graph.prune_non_compliant(
                cv.graph_neighbors, cv.compliance.value,
            )
            cv.pruned_tools = [t for t in cv.graph_neighbors if t not in pruned]
            cv.graph_neighbors = pruned
        except Exception as exc:
            log.debug("Compliance pruning failed: %s", exc)

    # ── Boost existing_tools confidence if graph confirms ecosystem ──
    if cv.graph_neighbors and cv.existing_tools.value:
        neighbor_set = {n.lower() for n in cv.graph_neighbors}
        tool_set = {t.lower() for t in cv.existing_tools.value}
        confirmed = neighbor_set & tool_set
        if confirmed:
            cv.existing_tools.confidence = min(1.0, cv.existing_tools.confidence + 0.05 * len(confirmed))
            cv.existing_tools.tier = assign_tier(cv.existing_tools.confidence)

    return cv


# ═══════════════════════════════════════════════════════════════════
# Context Correction Recording (Phase 4.3)
# ═══════════════════════════════════════════════════════════════════

_CORRECTIONS_FILE = Path(__file__).parent / "context_corrections.json"


def record_context_correction(
    field: str,
    inferred_value: Any,
    corrected_value: Any,
    query: str,
) -> None:
    """Record when a user corrects an auto-inferred context field.

    Stored for future learning-cycle weight tuning.
    """
    corrections = []
    if _CORRECTIONS_FILE.exists():
        try:
            with open(_CORRECTIONS_FILE, "r", encoding="utf-8") as f:
                corrections = json.load(f)
        except Exception:
            corrections = []

    corrections.append({
        "field": field,
        "inferred": inferred_value,
        "corrected": corrected_value,
        "query": query,
        "timestamp": time.time(),
    })

    with open(_CORRECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(corrections, f, indent=2)

    log.info("Context correction recorded: %s %s → %s", field, inferred_value, corrected_value)


def compute_correction_rate() -> Dict[str, float]:
    """Aggregate correction frequency per field.

    Returns dict mapping field names to their correction rates (0.0–1.0).
    """
    if not _CORRECTIONS_FILE.exists():
        return {}

    try:
        with open(_CORRECTIONS_FILE, "r", encoding="utf-8") as f:
            corrections = json.load(f)
    except Exception:
        return {}

    if not corrections:
        return {}

    field_counts: Dict[str, int] = {}
    for entry in corrections:
        f = entry.get("field", "unknown")
        field_counts[f] = field_counts.get(f, 0) + 1

    total = len(corrections)
    return {f: count / total for f, count in field_counts.items()}
