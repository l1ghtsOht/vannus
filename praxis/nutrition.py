# --------------- AI Nutrition Labels ---------------
"""
Praxis AI Nutrition Label Engine.

Generates standardized, highly readable "AI Nutrition Facts" labels for
every tool in the directory. Inspired by food nutrition labels — provides
immediate, non-technical transparency into:

    1. Base Model Provenance     — What architecture powers the tool
    2. Training Data Usage       — Does the vendor train on your data?
    3. Data Retention Posture    — ZDR compliance, TTL metrics
    4. Compliance Frameworks     — GDPR, HIPAA, SOC2, etc.
    5. Sovereignty Status        — Country of origin, trust tier
    6. Outcome Metrics           — Verified ROI, primary KPI

Integrates with:
    - sovereignty.py  (trust tier, country, ZDR status)
    - philosophy.py   (vendor intelligence: data practices, lock-in)
    - explain.py      (renders labels in tool profile UI)
"""

from typing import Dict, List, Optional
import logging

_log = logging.getLogger("praxis.nutrition")


# ======================================================================
# 1. Label Component Definitions
# ======================================================================

# Data practice risk levels
_DATA_PRACTICE_RISK = {
    "never":   {"level": "safe",     "icon": "🟢", "label": "Never trains on your data"},
    "opt_out": {"level": "caution",  "icon": "🟡", "label": "Trains unless you opt out"},
    "opt_in":  {"level": "warning",  "icon": "🔴", "label": "Trains on your data by default"},
}

# Retention policy templates
_RETENTION_POLICIES = {
    "ephemeral":    {"ttl": "0 seconds",   "risk": "minimal",  "label": "Processed in memory only. No persistent storage."},
    "short":        {"ttl": "< 30 days",   "risk": "low",      "label": "Prompts deleted within 30 days."},
    "standard":     {"ttl": "30–90 days",  "risk": "moderate",  "label": "Standard retention period. May be used for service improvement."},
    "long":         {"ttl": "> 90 days",   "risk": "elevated",  "label": "Extended retention. Review vendor DPA carefully."},
    "indefinite":   {"ttl": "Indefinite",  "risk": "high",      "label": "No published deletion timeline. Assume permanent retention."},
    "unknown":      {"ttl": "Not disclosed","risk": "uncertain", "label": "Vendor does not disclose data retention timeline."},
}

# Compliance badge definitions
_COMPLIANCE_BADGES = {
    "SOC2":     {"icon": "🛡", "full_name": "SOC 2 Type II",        "category": "security"},
    "GDPR":     {"icon": "🇪🇺", "full_name": "EU GDPR Compliant",   "category": "privacy"},
    "HIPAA":    {"icon": "🏥", "full_name": "HIPAA Compliant",      "category": "healthcare"},
    "ISO27001": {"icon": "📋", "full_name": "ISO 27001 Certified",  "category": "security"},
    "FedRAMP":  {"icon": "🏛", "full_name": "FedRAMP Authorized",   "category": "government"},
    "PCI-DSS":  {"icon": "💳", "full_name": "PCI DSS Compliant",    "category": "financial"},
    "CCPA":     {"icon": "🌴", "full_name": "CCPA Compliant",       "category": "privacy"},
    "FERPA":    {"icon": "🎓", "full_name": "FERPA Compliant",      "category": "education"},
}


# ======================================================================
# 2. Retention Inference Engine
# ======================================================================

def _infer_retention_policy(tool) -> Dict:
    """
    Infer a tool's data retention policy from available metadata.

    Uses ZDR compliance, training data usage, and vendor intelligence
    to determine the most likely retention posture.
    """
    zdr = getattr(tool, "zdr_compliant", False)
    train_use = getattr(tool, "training_data_usage", "opt_out")

    if zdr:
        return _RETENTION_POLICIES["ephemeral"]
    if train_use == "never":
        return _RETENTION_POLICIES["short"]
    if train_use == "opt_out":
        return _RETENTION_POLICIES["standard"]
    if train_use == "opt_in":
        return _RETENTION_POLICIES["long"]
    return _RETENTION_POLICIES["unknown"]


# ======================================================================
# 3. Core Nutrition Label Generator
# ======================================================================

def generate_nutrition_label(tool, sovereignty_data: Dict = None) -> Dict:
    """
    Generate a complete AI Nutrition Facts label for a tool.

    Args:
        tool: Tool object with sovereignty/privacy attributes
        sovereignty_data: Pre-computed sovereignty assessment (optional)

    Returns:
        {
            "title": "AI Nutrition Facts: ToolName",
            "sections": {
                "provenance": { ... },
                "data_usage": { ... },
                "retention": { ... },
                "compliance": { ... },
                "sovereignty": { ... },
                "outcome": { ... },
            },
            "risk_summary": { ... },
            "generated_at": str,
        }
    """
    from datetime import datetime, timezone

    name = getattr(tool, "name", str(tool))

    # --- Provenance Section ---
    base_model = getattr(tool, "base_model", None)
    provenance = {
        "base_model": base_model or "Proprietary / Undisclosed",
        "model_disclosed": base_model is not None,
        "open_weights": base_model and any(k in (base_model or "").lower()
                                            for k in ("open", "llama", "mistral", "sdxl")),
    }

    # --- Data Usage Section ---
    train_use = getattr(tool, "training_data_usage", "opt_out")
    data_practice = _DATA_PRACTICE_RISK.get(train_use, _DATA_PRACTICE_RISK["opt_out"])
    data_usage = {
        "training_data_policy": train_use,
        "risk_level": data_practice["level"],
        "icon": data_practice["icon"],
        "label": data_practice["label"],
        "trains_on_user_data": train_use != "never",
    }

    # --- Retention Section ---
    retention = _infer_retention_policy(tool)

    # --- Compliance Section ---
    compliance_list = getattr(tool, "compliance", []) or []
    compliance_badges = []
    for cert in compliance_list:
        badge = _COMPLIANCE_BADGES.get(cert)
        if badge:
            compliance_badges.append({**badge, "code": cert})
        else:
            compliance_badges.append({"icon": "📄", "full_name": cert, "category": "other", "code": cert})

    compliance = {
        "frameworks": compliance_list,
        "badges": compliance_badges,
        "count": len(compliance_list),
        "has_security": any(b["category"] == "security" for b in compliance_badges),
        "has_privacy": any(b["category"] == "privacy" for b in compliance_badges),
        "has_healthcare": any(b["category"] == "healthcare" for b in compliance_badges),
    }

    # --- Sovereignty Section ---
    sov = sovereignty_data or {}
    sovereignty = {
        "country_of_origin": sov.get("country_of_origin") or getattr(tool, "country_of_origin", "USA"),
        "trust_tier": sov.get("trust_tier", "unknown"),
        "badge": sov.get("badge", {}),
        "is_us_controlled": sov.get("is_us_controlled", getattr(tool, "is_us_controlled", None)),
        "data_jurisdiction": sov.get("data_jurisdiction") or getattr(tool, "data_jurisdiction", "US"),
        "zdr_compliant": sov.get("zdr_compliant", getattr(tool, "zdr_compliant", False)),
    }

    # --- Outcome Section ---
    kpi = getattr(tool, "target_outcome_kpi", None)
    roi = getattr(tool, "verified_roi_score", 0.0)
    metrics = getattr(tool, "outcome_metrics", {}) or {}
    outcome = {
        "primary_kpi": kpi or "Unverified",
        "verified_roi_score": roi,
        "roi_grade": _roi_grade(roi),
        "metrics": metrics,
        "has_verified_outcomes": roi > 0.0,
    }

    # --- Risk Summary ---
    risk_flags = []
    if data_usage["trains_on_user_data"]:
        risk_flags.append("Vendor may use your inputs for model training")
    if retention.get("risk") in ("elevated", "high", "uncertain"):
        risk_flags.append(f"Data retention: {retention['ttl']}")
    if sovereignty["trust_tier"] == "high_risk":
        risk_flags.append("High-risk foreign supply chain detected")
    if not provenance["model_disclosed"]:
        risk_flags.append("Base model architecture not publicly disclosed")

    overall_risk = "low"
    if len(risk_flags) >= 3:
        overall_risk = "high"
    elif len(risk_flags) >= 1:
        overall_risk = "moderate"

    return {
        "title": f"AI Nutrition Facts: {name}",
        "tool_name": name,
        "sections": {
            "provenance": provenance,
            "data_usage": data_usage,
            "retention": retention,
            "compliance": compliance,
            "sovereignty": sovereignty,
            "outcome": outcome,
        },
        "risk_summary": {
            "overall_risk": overall_risk,
            "flags": risk_flags,
            "flag_count": len(risk_flags),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _roi_grade(score: float) -> str:
    """Convert ROI score to letter grade."""
    if score >= 0.85:
        return "A"
    if score >= 0.75:
        return "B"
    if score >= 0.60:
        return "C"
    if score >= 0.40:
        return "D"
    return "F"


# ======================================================================
# 4. Batch Label Generation
# ======================================================================

def generate_all_labels(tools: list, sovereignty_assessments: Dict = None) -> List[Dict]:
    """
    Generate nutrition labels for all tools in the catalog.

    Args:
        tools: Full tool list
        sovereignty_assessments: Optional pre-computed {tool_name: assessment}

    Returns:
        List of nutrition label dicts
    """
    sov_map = {}
    if sovereignty_assessments:
        for a in sovereignty_assessments.get("assessments", []):
            sov_map[a["tool_name"]] = a

    labels = []
    for tool in tools:
        name = getattr(tool, "name", str(tool))
        sov = sov_map.get(name)
        labels.append(generate_nutrition_label(tool, sov))

    return labels


# ======================================================================
# 5. Platform Self-Label
# ======================================================================

def praxis_self_label() -> Dict:
    """
    Generate the AI Nutrition Label for the Praxis platform itself.

    Displayed as a persistent cryptographic banner in the UI:
    "Session Data is Ephemeral. No Search Recording. No External LLM Training."
    """
    return {
        "title": "AI Nutrition Facts: Praxis Platform",
        "tool_name": "Praxis",
        "platform_commitments": [
            "Session data is ephemeral — processed in transient memory only",
            "No search query recording — zero persistent logs",
            "No external LLM training — your queries never refine third-party models",
            "Local-first scoring — all NLP runs zero-dependency on-server",
            "Full audit trail — every recommendation traceable to scoring signals",
        ],
        "banner_text": "Session Data is Ephemeral. No Search Recording. No External LLM Training.",
        "zdr_compliant": True,
        "training_data_usage": "never",
        "data_retention_ttl": "0 seconds (in-memory only)",
        "compliance_posture": "NIST AI RMF aligned, Zero Data Retention by architecture",
    }


_log.info(
    "nutrition.py loaded — %d data practice tiers, %d retention policies, "
    "%d compliance badges defined",
    len(_DATA_PRACTICE_RISK), len(_RETENTION_POLICIES), len(_COMPLIANCE_BADGES),
)
