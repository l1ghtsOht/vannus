# ────────── Residual Gap Interface ──────────
"""
Dependency-tree gap analysis and question ordering engine.

After the context engine extracts what it can from a query, this module
determines what *cannot* be inferred (the "residual gap") and produces
a minimal, dependency-ordered set of questions for the operator.

Cascade dependency tree:
    Level 0 (BLOCKING):     industry / vertical → gates compliance pruning
    Level 1 (BRANCHING):    existing_tools (core anchors) → gates graph traversal
    Level 2 (REFINEMENT):   skill_level, budget, team_size, timeline → modulates scoring

Design principles:
    • Never ask what you already know (T1 and T2 fields are excluded)
    • Dependency ordering: industry before tools, tools before skill/budget
    • Skip rules: if budget="free" → skip complex integration questions
    • Maximum question count capped by config.context_max_gap_questions
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.residual_gap")

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg  # type: ignore[no-redef]
    except Exception:
        _cfg = None  # type: ignore[assignment]

try:
    from .context_engine import (
        ContextVector, FieldExtraction, TIER_1, TIER_2, TIER_3,
        assign_tier, extract_context,
    )
except Exception:
    try:
        from context_engine import (  # type: ignore[no-redef]
            ContextVector, FieldExtraction, TIER_1, TIER_2, TIER_3,
            assign_tier, extract_context,
        )
    except Exception:
        ContextVector = None  # type: ignore[assignment]
        TIER_1, TIER_2, TIER_3 = 1, 2, 3


def _conf(key: str, fallback):
    if _cfg:
        return _cfg.get(key, fallback)
    return fallback


# ═══════════════════════════════════════════════════════════════════
# Data Types
# ═══════════════════════════════════════════════════════════════════

@dataclass
class GapQuestion:
    """A single question to present to the operator."""
    field: str                          # target profile field
    question_text: str
    presentation_type: str = "dropdown"  # dropdown | slider | multi_choice | text
    options: List[Dict[str, Any]] = field(default_factory=list)
    default_value: Optional[Any] = None
    default_confidence: float = 0.0
    cascade_level: int = 2              # 0=blocking, 1=branching, 2=refinement
    depends_on: Optional[str] = None    # field that must be answered first
    skip_if: Optional[Dict[str, Any]] = None  # conditions to auto-skip

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "question_text": self.question_text,
            "presentation_type": self.presentation_type,
            "options": self.options,
            "default_value": self.default_value,
            "default_confidence": round(self.default_confidence, 4),
            "cascade_level": self.cascade_level,
            "depends_on": self.depends_on,
            "skip_if": self.skip_if,
        }


@dataclass
class GapAnalysis:
    """Complete gap analysis result."""
    questions: List[GapQuestion] = field(default_factory=list)
    auto_filled: Dict[str, Any] = field(default_factory=dict)
    pre_filled: Dict[str, Any] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    total_friction_clicks: int = 0
    context_vector: Optional[Any] = None  # ContextVector, typed as Any to avoid circular import issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "questions": [q.to_dict() for q in self.questions],
            "auto_filled": self.auto_filled,
            "pre_filled": self.pre_filled,
            "missing": self.missing,
            "total_friction_clicks": self.total_friction_clicks,
            "question_count": len(self.questions),
        }


# ═══════════════════════════════════════════════════════════════════
# Question Templates
# ═══════════════════════════════════════════════════════════════════

_QUESTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "industry": {
        "question_text": "What industry or domain is this for?",
        "presentation_type": "dropdown",
        "cascade_level": 0,
        "depends_on": None,
        "base_options": [
            {"value": "healthcare", "label": "Healthcare"},
            {"value": "finance", "label": "Finance / Fintech"},
            {"value": "ecommerce", "label": "E-commerce / Retail"},
            {"value": "saas", "label": "SaaS / Software"},
            {"value": "education", "label": "Education"},
            {"value": "real_estate", "label": "Real Estate"},
            {"value": "legal", "label": "Legal"},
            {"value": "agency", "label": "Agency / Consulting"},
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "government", "label": "Government"},
            {"value": "other", "label": "Other"},
        ],
    },
    "existing_tools": {
        "question_text": "What tools do you currently use?",
        "presentation_type": "multi_choice",
        "cascade_level": 1,
        "depends_on": "industry",
        "base_options": [],  # populated dynamically from context
    },
    "skill_level": {
        "question_text": "What's your technical comfort level?",
        "presentation_type": "dropdown",
        "cascade_level": 2,
        "depends_on": "existing_tools",
        "base_options": [
            {"value": "beginner", "label": "Non-technical (drag & drop, no code)"},
            {"value": "intermediate", "label": "Some technical experience"},
            {"value": "advanced", "label": "Developer / technical"},
        ],
    },
    "budget": {
        "question_text": "What's your monthly budget for tools?",
        "presentation_type": "dropdown",
        "cascade_level": 2,
        "depends_on": None,
        "base_options": [
            {"value": "free", "label": "Free only"},
            {"value": "low", "label": "Under $50/month"},
            {"value": "medium", "label": "$50 – $200/month"},
            {"value": "high", "label": "Over $200/month"},
        ],
    },
    "team_size": {
        "question_text": "How large is your team?",
        "presentation_type": "dropdown",
        "cascade_level": 2,
        "depends_on": None,
        "base_options": [
            {"value": "solo", "label": "Just me"},
            {"value": "small", "label": "2–10 people"},
            {"value": "medium", "label": "11–50 people"},
            {"value": "large", "label": "50+ people"},
        ],
    },
    "timeline": {
        "question_text": "When do you need this in place?",
        "presentation_type": "dropdown",
        "cascade_level": 2,
        "depends_on": None,
        "base_options": [
            {"value": "immediate", "label": "This week / ASAP"},
            {"value": "short_term", "label": "Within a month"},
            {"value": "planning", "label": "Still evaluating / researching"},
        ],
    },
    "compliance": {
        "question_text": "Do you have specific compliance requirements?",
        "presentation_type": "multi_choice",
        "cascade_level": 1,
        "depends_on": "industry",
        "base_options": [
            {"value": "HIPAA", "label": "HIPAA (Healthcare)"},
            {"value": "SOC2", "label": "SOC 2"},
            {"value": "GDPR", "label": "GDPR (EU Privacy)"},
            {"value": "PCI-DSS", "label": "PCI-DSS (Payments)"},
            {"value": "FedRAMP", "label": "FedRAMP (Government)"},
            {"value": "none", "label": "None / Not sure"},
        ],
        "skip_if": {"industry": ["other"]},
    },
}

# Fields that are profile-relevant but rarely asked (constraints, task_type)
_SKIP_FIELDS = {"task_type", "constraints"}


# ═══════════════════════════════════════════════════════════════════
# Core Gap Computation
# ═══════════════════════════════════════════════════════════════════

def compute_gap(context_vector) -> GapAnalysis:
    """Analyse a ContextVector and produce a dependency-ordered question set.

    Pipeline:
        1. Separate T1 (auto-commit), T2 (pre-fill), T3 (must-ask) fields
        2. Build questions only for T2 fields needing confirmation + T3 fields
        3. Order by cascade_level (blocking → branching → refinement)
        4. Apply skip rules
        5. Cap at max question count
    """
    cv = context_vector
    ga = GapAnalysis(context_vector=cv)

    # ── Categorise fields by tier ──
    for name, fe in cv.all_fields.items():
        if fe.tier == TIER_1:
            ga.auto_filled[name] = fe.value
        elif fe.tier == TIER_2:
            ga.pre_filled[name] = fe.value
        else:
            if name not in _SKIP_FIELDS:
                ga.missing.append(name)

    # ── Build questions for T3 fields + T2 fields that need confirmation ──
    raw_questions: List[GapQuestion] = []

    for field_name in ga.missing:
        template = _QUESTION_TEMPLATES.get(field_name)
        if not template:
            continue

        q = GapQuestion(
            field=field_name,
            question_text=template["question_text"],
            presentation_type=template["presentation_type"],
            cascade_level=template["cascade_level"],
            depends_on=template.get("depends_on"),
            skip_if=template.get("skip_if"),
            options=_build_options(field_name, template, cv),
        )
        raw_questions.append(q)

    # Add T2 fields that might benefit from confirmation (low confidence T2)
    for field_name, value in ga.pre_filled.items():
        fe = cv.all_fields[field_name]
        # Only add confirmation question if confidence is below 0.75
        if fe.confidence < 0.75 and field_name not in _SKIP_FIELDS:
            template = _QUESTION_TEMPLATES.get(field_name)
            if not template:
                continue
            q = GapQuestion(
                field=field_name,
                question_text=template["question_text"],
                presentation_type=template["presentation_type"],
                cascade_level=template["cascade_level"],
                depends_on=template.get("depends_on"),
                skip_if=template.get("skip_if"),
                options=_build_options(field_name, template, cv),
                default_value=value,
                default_confidence=fe.confidence,
            )
            raw_questions.append(q)

    # ── Apply skip rules ──
    questions = _apply_skip_rules(raw_questions, ga.auto_filled, ga.pre_filled)

    # ── Sort by cascade level (blocking first) ──
    questions.sort(key=lambda q: (q.cascade_level, q.field))

    # ── Cap at max questions ──
    max_q = _conf("context_max_gap_questions", 4)
    if len(questions) > max_q:
        questions = questions[:max_q]

    ga.questions = questions
    ga.total_friction_clicks = _estimate_friction(questions)

    log.info(
        "Gap analysis: auto=%d prefill=%d ask=%d questions=%d friction=%d",
        len(ga.auto_filled), len(ga.pre_filled), len(ga.missing),
        len(ga.questions), ga.total_friction_clicks,
    )
    return ga


def _build_options(
    field_name: str,
    template: Dict[str, Any],
    cv,
) -> List[Dict[str, Any]]:
    """Build contextually-enriched options for a gap question."""
    options = list(template.get("base_options", []))

    # Enrich industry options with vertical matches
    if field_name == "industry" and cv.vertical_matches:
        # Put top vertical matches at the front
        vert_options = []
        existing_values = {o["value"] for o in options}
        for vert in cv.vertical_matches[:3]:
            vid = vert.get("vertical_id", "")
            if vid and vid not in existing_values:
                vert_options.append({
                    "value": vid,
                    "label": vid.replace("_", " ").title(),
                    "confidence": round(vert.get("confidence", 0), 2),
                })
        options = vert_options + options

    # Enrich existing_tools options with graph neighbors
    if field_name == "existing_tools" and cv.graph_neighbors:
        for tool_name in cv.graph_neighbors[:10]:
            options.append({
                "value": tool_name,
                "label": tool_name.title(),
            })

    # Enrich compliance with vertical-specific frameworks
    if field_name == "compliance" and cv.constraint_profile is not None:
        existing_values = {o["value"] for o in options}
        for reg in getattr(cv.constraint_profile, "regulatory", []):
            if reg not in existing_values:
                options.insert(-1, {"value": reg, "label": reg})

    return options


def _apply_skip_rules(
    questions: List[GapQuestion],
    auto_filled: Dict[str, Any],
    pre_filled: Dict[str, Any],
) -> List[GapQuestion]:
    """Remove questions that should be skipped based on already-known context."""
    known = {**auto_filled, **pre_filled}
    kept: List[GapQuestion] = []

    for q in questions:
        # Skip if the dependency hasn't been resolved and is at a higher cascade
        if q.depends_on and q.depends_on not in known:
            # Don't skip — we need the dependency question first, which will be present
            pass

        # Apply skip_if rules
        if q.skip_if:
            should_skip = False
            for dep_field, skip_values in q.skip_if.items():
                known_val = known.get(dep_field)
                if known_val and known_val in skip_values:
                    should_skip = True
                    break
            if should_skip:
                continue

        # Skip compliance questions if no regulated industry detected
        if q.field == "compliance":
            industry_val = known.get("industry", "")
            regulated = {"healthcare", "finance", "fintech", "government",
                         "clinical", "legal", "insurance"}
            if industry_val and industry_val.lower() not in regulated:
                continue

        kept.append(q)
    return kept


def _estimate_friction(questions: List[GapQuestion]) -> int:
    """Estimate total user interaction clicks for a question set."""
    clicks = 0
    for q in questions:
        if q.presentation_type == "dropdown":
            clicks += 2  # click to open + click to select
        elif q.presentation_type == "multi_choice":
            clicks += 1 + min(3, len(q.options))  # open + selections
        elif q.presentation_type == "slider":
            clicks += 1
        elif q.presentation_type == "text":
            clicks += 3  # click + type + confirm
        if q.default_value is not None:
            clicks -= 1  # pre-filled saves a click
    return max(0, clicks)


# ═══════════════════════════════════════════════════════════════════
# Gap Resolution
# ═══════════════════════════════════════════════════════════════════

def resolve_gap(
    gap_analysis: GapAnalysis,
    user_answers: Dict[str, Any],
) -> Any:
    """Merge user answers into the ContextVector and re-tier.

    Args:
        gap_analysis: The GapAnalysis from compute_gap()
        user_answers: Dict mapping field names to user-provided values

    Returns:
        Updated ContextVector with answered fields promoted to T1.
    """
    cv = gap_analysis.context_vector
    if cv is None:
        return None

    for field_name, answer in user_answers.items():
        fe = cv.all_fields.get(field_name)
        if fe is None:
            continue

        fe.value = answer
        fe.confidence = 1.0  # user-confirmed = maximum confidence
        fe.tier = TIER_1
        fe.source = "user_confirmed"
        fe.evidence = f"operator answered: {answer}"

        # Apply to the ContextVector's field
        setattr(cv, field_name, fe)

    # Record corrections for learning
    try:
        from .context_engine import record_context_correction
    except Exception:
        try:
            from context_engine import record_context_correction  # type: ignore[no-redef]
        except Exception:
            record_context_correction = None  # type: ignore[assignment]

    if record_context_correction is not None:
        for field_name, answer in user_answers.items():
            # Check if this was originally inferred differently
            original = gap_analysis.pre_filled.get(field_name)
            if original is not None and original != answer:
                record_context_correction(
                    field=field_name,
                    inferred_value=original,
                    corrected_value=answer,
                    query=cv.raw_query,
                )

    log.info("Gap resolved: %d answers applied", len(user_answers))
    return cv


# ═══════════════════════════════════════════════════════════════════
# Convenience: Full pipeline entry point
# ═══════════════════════════════════════════════════════════════════

def analyse_query(
    query: str,
    *,
    profile_id: Optional[str] = None,
) -> GapAnalysis:
    """One-call convenience: extract context → compute gap → return analysis.

    This is the recommended entry point for the API layer.
    """
    if extract_context is None:
        raise RuntimeError("context_engine module not available")

    cv = extract_context(query, profile_id=profile_id)
    return compute_gap(cv)
