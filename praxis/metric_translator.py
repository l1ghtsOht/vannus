# ────────────────────────────────────────────────────────────────────
# metric_translator.py — Enterprise Metric Language Layer
#
# Translates internal Praxis philosophical / research terminology
# into enterprise-ready metric names that buyers immediately
# understand.  Every public API response passes through this
# translator so external consumers never see internal jargon.
# ────────────────────────────────────────────────────────────────────
"""
Maps internal Praxis scoring labels → enterprise metric labels.

Design rules:
  • Internal depth stays intact (values are unchanged).
  • Only *keys* and *labels* are translated.
  • The translator is pure-function, zero side-effects.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. TERMINOLOGY MAP                                              ║
# ╚════════════════════════════════════════════════════════════════════╝

# Internal label → public enterprise label
_KEY_MAP: Dict[str, str] = {
    # Philosophy → Enterprise
    "resonance_index":          "integration_compatibility_score",
    "resonance":                "integration_compatibility",
    "awakening_score":          "architecture_maturity_score",
    "awakening":                "architecture_maturity",
    "enlightenment_score":      "system_coherence_score",
    "enlightenment":            "system_coherence",
    "conduit_score":            "cognitive_architecture_score",
    "metacognition_score":      "self_diagnostic_score",
    "metacognition":            "self_diagnostics",
    "consciousness_level":      "architecture_depth_level",

    # Scoring → Enterprise metrics
    "phi":                      "integration_information_index",
    "phi_value":                "integration_information_index",
    "entropy":                  "architectural_complexity_score",
    "structural_entropy":       "architectural_complexity_score",
    "flow_state":               "workflow_efficiency_score",
    "loop_coherence":           "feedback_loop_quality",
    "steering_precision":       "control_accuracy_score",
    "wisdom_coverage":          "decision_coverage_score",
    "ontological_alignment":    "schema_alignment_score",
    "hitl_responsiveness":      "human_oversight_responsiveness",

    # Risk → Enterprise risk
    "vibe_coding_risk":         "ai_generation_risk_score",
    "shadow_ai":                "unauthorized_ai_usage",
    "lock_in_index":            "vendor_lock_in_probability",
    "lock_in":                  "vendor_lock_in",
    "trap_score":               "anti_pattern_risk_score",
    "ego_dissolution":          "vendor_dependency_reduction",

    # Architecture → Enterprise architecture
    "autopoiesis":              "self_maintaining_capability",
    "global_workspace":         "shared_context_architecture",
    "representation_engineering": "model_transparency_analysis",
    "memory_stratification":    "tiered_memory_architecture",
    "decoupling":               "component_independence_score",

    # Conduit → Enterprise cognitive
    "smi":                      "system_maturity_index",
    "bni":                      "bottleneck_index",
    "attractor":                "stability_attractor_score",

    # Cost → Enterprise cost
    "total_monthly_cost":       "estimated_monthly_cost_usd",
    "cost_delta_monthly":       "monthly_cost_difference_usd",
    "annual_cost_savings":      "projected_annual_savings_usd",
    "roi_percentage":           "return_on_investment_pct",

    # Migration → Enterprise migration
    "migration_complexity":     "migration_difficulty",
    "estimated_days":           "estimated_migration_days",
    "transition_bridges":       "bridging_tools",

    # Compliance → Enterprise compliance
    "compliance_score":         "regulatory_compliance_score",
    "overall_grade":            "compliance_grade",
    "pii_exposure":             "personal_data_exposure_risk",
    "data_lineage":             "data_flow_map",
}

# Section / category labels for grouping
_SECTION_MAP: Dict[str, str] = {
    "resonance":        "Integration Analysis",
    "awakening":        "Architecture Assessment",
    "enlightenment":    "System Coherence",
    "conduit":          "Cognitive Architecture",
    "metacognition":    "Self-Diagnostics",
    "prism":            "Multi-Lens Analysis",
}


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. TRANSLATION FUNCTIONS                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

def translate_key(key: str) -> str:
    """Translate a single internal key to its enterprise equivalent."""
    return _KEY_MAP.get(key, key)


def translate_section(section: str) -> str:
    """Translate an internal section name to enterprise label."""
    return _SECTION_MAP.get(section.lower(), section)


def translate_dict(data: Dict[str, Any], *, deep: bool = True) -> Dict[str, Any]:
    """
    Recursively translate all keys in a dictionary.
    Values are preserved — only labels change.
    """
    result: Dict[str, Any] = {}
    for k, v in data.items():
        new_key = translate_key(k)
        if deep and isinstance(v, dict):
            result[new_key] = translate_dict(v, deep=True)
        elif deep and isinstance(v, list):
            result[new_key] = [
                translate_dict(item, deep=True) if isinstance(item, dict) else item
                for item in v
            ]
        else:
            result[new_key] = v
    return result


def translate_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top-level response translator for public API.
    Adds a `_meta` block and translates all keys.
    """
    translated = translate_dict(data)
    translated["_meta"] = {
        "api_version":  "public-v1",
        "metric_format": "enterprise",
        "documentation": "/api/v1/docs",
    }
    return translated


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3.  RISK SUMMARY BUILDER                                       ║
# ╚════════════════════════════════════════════════════════════════════╝

def build_risk_summary(
    vendor_risk: Optional[Dict] = None,
    compliance: Optional[Dict] = None,
    lock_in: Optional[float] = None,
    migration_complexity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Combine multiple internal risk signals into a single
    enterprise-readable risk summary.
    """
    risk_factors: List[Dict[str, Any]] = []

    if vendor_risk:
        risk_factors.append({
            "factor": "vendor_risk_score",
            "value":  vendor_risk.get("risk_score", 0),
            "level":  vendor_risk.get("risk_level", "unknown"),
            "detail": vendor_risk.get("recommendations", [])[:3],
        })

    if compliance:
        score = compliance.get("overall_compliance_score",
                 compliance.get("compliance_score", 0))
        risk_factors.append({
            "factor": "regulatory_compliance_score",
            "value":  score,
            "level":  _compliance_level(score),
            "detail": compliance.get("gaps", [])[:3],
        })

    if lock_in is not None:
        risk_factors.append({
            "factor": "vendor_lock_in_probability",
            "value":  lock_in,
            "level":  "high" if lock_in > 0.7 else "medium" if lock_in > 0.4 else "low",
        })

    if migration_complexity:
        risk_factors.append({
            "factor": "migration_difficulty",
            "value":  migration_complexity,
            "level":  migration_complexity,
        })

    # Composite risk score (0-100)
    scores = [f["value"] for f in risk_factors if isinstance(f["value"], (int, float))]
    composite = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "composite_risk_score": composite,
        "risk_level": _risk_level(composite),
        "factors": risk_factors,
        "recommendations_count": sum(
            len(f.get("detail", [])) for f in risk_factors
        ),
    }


def _compliance_level(score: float) -> str:
    if score >= 0.9:
        return "excellent"
    if score >= 0.7:
        return "good"
    if score >= 0.5:
        return "moderate"
    return "poor"


def _risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"
