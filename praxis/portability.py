# --------------- Exit Portability Calculator ---------------
"""
Programmatic determination of SMB vendor lock-in exposure.

Implements the calculate_exit_portability algorithm from the 2026 Trust Badge
Blueprint, integrating EU Data Act and UK DUAA requirements for export
formats, deletion timelines, and termination penalties.

The portability score is a critical component of the Trust Badge system,
directly feeding into the portability_score badge and the philosophy.py
elimination flag triggers.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("praxis.portability")


# ======================================================================
# Contract Data Model
# ======================================================================

class ContractData:
    """Represents vendor contractual terms relevant to exit portability."""

    def __init__(
        self,
        supports_iso_19941: bool = False,
        export_formats: list = None,
        guaranteed_export_days: int = 999,
        guarantees_deletion: bool = False,
        cancellation_fee: float = 0,
        notice_period_days: int = 0,
        has_api_export: bool = False,
        max_export_size_gb: float = 0,
        supports_bulk_export: bool = False,
        data_retention_after_cancel_days: int = 90,
    ):
        self.supports_iso_19941 = supports_iso_19941
        self.export_formats = export_formats or []
        self.guaranteed_export_days = guaranteed_export_days
        self.guarantees_deletion = guarantees_deletion
        self.cancellation_fee = cancellation_fee
        self.notice_period_days = notice_period_days
        self.has_api_export = has_api_export
        self.max_export_size_gb = max_export_size_gb
        self.supports_bulk_export = supports_bulk_export
        self.data_retention_after_cancel_days = data_retention_after_cancel_days


# ======================================================================
# Standard Export Formats (ISO/IEC 19941:2017 compliant)
# ======================================================================

_STANDARD_FORMATS = {"json", "csv", "xml", "sql", "parquet", "yaml", "txt", "markdown"}
_PROPRIETARY_FORMATS = {"proprietary", "custom", "binary", "encrypted"}


# ======================================================================
# Vendor Contract Intelligence
# ======================================================================

_VENDOR_CONTRACTS = {
    "chatgpt": ContractData(
        export_formats=["json"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
    "claude": ContractData(
        export_formats=["json", "txt"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
    "gemini": ContractData(
        export_formats=["json"], guaranteed_export_days=60,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
    "hugging face": ContractData(
        supports_iso_19941=True,
        export_formats=["json", "csv", "parquet", "safetensors"],
        guaranteed_export_days=0, guarantees_deletion=True,
        cancellation_fee=0, notice_period_days=0,
        has_api_export=True, supports_bulk_export=True,
    ),
    "n8n": ContractData(
        supports_iso_19941=True,
        export_formats=["json"], guaranteed_export_days=0,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
    "supabase": ContractData(
        supports_iso_19941=True,
        export_formats=["json", "csv", "sql"], guaranteed_export_days=0,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True, supports_bulk_export=True,
    ),
    "zapier": ContractData(
        export_formats=["json"], guaranteed_export_days=60,
        guarantees_deletion=False, cancellation_fee=0,
        notice_period_days=30,
    ),
    "make": ContractData(
        export_formats=["json"], guaranteed_export_days=60,
        guarantees_deletion=False, cancellation_fee=0,
        notice_period_days=30,
    ),
    "salesforce": ContractData(
        export_formats=["csv"], guaranteed_export_days=90,
        guarantees_deletion=True, cancellation_fee=500,
        notice_period_days=90,
    ),
    "shopify": ContractData(
        export_formats=["csv"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30,
    ),
    "notion ai": ContractData(
        export_formats=["markdown", "csv", "html"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0,
    ),
    "slack": ContractData(
        export_formats=["json"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30,
    ),
    "hubspot": ContractData(
        export_formats=["csv", "json"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30,
    ),
    "stripe": ContractData(
        export_formats=["csv", "json"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30, has_api_export=True,
    ),
    "figma ai": ContractData(
        export_formats=["svg", "png", "pdf"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0,
    ),
    "canva ai": ContractData(
        export_formats=["png", "jpg", "pdf", "svg"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0,
    ),
    "amplitude": ContractData(
        export_formats=["csv", "json"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30,
    ),
    "posthog": ContractData(
        supports_iso_19941=True,
        export_formats=["json", "csv"], guaranteed_export_days=0,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
    "midjourney": ContractData(
        export_formats=["png", "jpg"], guaranteed_export_days=0,
        guarantees_deletion=False, cancellation_fee=0,
        notice_period_days=0,
    ),
    "grammarly": ContractData(
        export_formats=["txt"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0,
    ),
    "vanta": ContractData(
        export_formats=["csv", "pdf"], guaranteed_export_days=30,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=30,
    ),
    "langchain": ContractData(
        supports_iso_19941=True,
        export_formats=["json", "yaml"], guaranteed_export_days=0,
        guarantees_deletion=True, cancellation_fee=0,
        notice_period_days=0, has_api_export=True,
    ),
}


# ======================================================================
# Core Portability Calculator
# ======================================================================

def calculate_exit_portability(tool, contract_override: dict = None) -> dict:
    """Calculate vendor exit portability score per EU Data Act mandates.

    This is the central algorithm described in the Trust Badge Blueprint.
    Integrates engine.py contract data with philosophy.py risk evaluation.

    Args:
        tool: Tool object
        contract_override: Optional dict to override stored contract data

    Returns:
        {
            "score": int (1-10),
            "status": "High Portability" | "Moderate Portability" | "High Lock-in Risk",
            "reasons": [str],           # Penalty descriptions
            "breakdown": {              # Detailed score breakdown
                "export_format": { "score": int, "max": 4, "detail": str },
                "export_timeline": { "score": int, "max": 3, "detail": str },
                "financial_lock_in": { "score": int, "max": 3, "detail": str },
            },
            "contract_data": dict,      # Raw contract data used
            "recommendation": str,
            "eu_data_act_compliant": bool,
        }
    """
    name_key = tool.name.lower().strip()

    # Fetch contract data
    if contract_override:
        contract = ContractData(**contract_override)
    elif name_key in _VENDOR_CONTRACTS:
        contract = _VENDOR_CONTRACTS[name_key]
    else:
        contract = _infer_contract(tool)

    score = 0
    penalties = []
    breakdown = {}

    # ── 1. Export Format Standards & Interoperability (Max +4) ──
    if contract.supports_iso_19941:
        fmt_score = 4
        fmt_detail = "ISO/IEC 19941:2017 compliant. Full cloud data interoperability."
    elif contract.export_formats and any(
        f.lower() in _STANDARD_FORMATS for f in contract.export_formats
    ):
        standard_fmts = [f for f in contract.export_formats if f.lower() in _STANDARD_FORMATS]
        fmt_score = min(3, len(standard_fmts))
        if contract.has_api_export:
            fmt_score = min(4, fmt_score + 1)
        fmt_detail = f"Standard formats: {', '.join(standard_fmts)}."
        if contract.has_api_export:
            fmt_detail += " API export available."
    else:
        fmt_score = 0
        penalties.append("Proprietary export format only. High data extraction cost.")
        fmt_detail = "No standard export formats available."

    score += fmt_score
    breakdown["export_format"] = {"score": fmt_score, "max": 4, "detail": fmt_detail}

    # ── 2. EU Data Act Export Timelines & Deletion Protocols (Max +3) ──
    if contract.guaranteed_export_days <= 30 and contract.guarantees_deletion:
        time_score = 3
        time_detail = f"Export within {contract.guaranteed_export_days} days with guaranteed deletion."
    elif contract.guaranteed_export_days <= 60:
        time_score = 1
        time_detail = f"Export within {contract.guaranteed_export_days} days."
        if not contract.guarantees_deletion:
            time_detail += " ⚠️ No deletion guarantee."
    else:
        time_score = 0
        penalties.append("Data export timeline exceeds 60 days or lacks deletion guarantees.")
        time_detail = f"Export timeline: {contract.guaranteed_export_days} days."

    score += time_score
    breakdown["export_timeline"] = {"score": time_score, "max": 3, "detail": time_detail}

    # ── 3. Financial Lock-in / Termination Penalties (Max +3) ──
    # Enforces the 2027 mandate for free switching services
    if contract.cancellation_fee == 0 and contract.notice_period_days <= 60:
        fin_score = 3
        fin_detail = "No cancellation fee. Notice period ≤60 days."
    elif contract.cancellation_fee <= 100 and contract.notice_period_days <= 90:
        fin_score = 1
        fin_detail = f"Cancellation fee: ${contract.cancellation_fee}. Notice: {contract.notice_period_days} days."
    else:
        fin_score = 0
        penalties.append(f"Significant financial penalty for early termination (${contract.cancellation_fee}).")
        fin_detail = f"Cancellation fee: ${contract.cancellation_fee}. Notice: {contract.notice_period_days} days."

    score += fin_score
    breakdown["financial_lock_in"] = {"score": fin_score, "max": 3, "detail": fin_detail}

    # Clamp
    score = max(1, min(10, score))

    # EU Data Act compliance check
    eu_compliant = (
        fmt_score >= 2 and
        contract.guaranteed_export_days <= 30 and
        contract.guarantees_deletion and
        contract.cancellation_fee == 0
    )

    # Categorize & recommend
    if score >= 9:
        status = "High Portability"
        recommendation = (
            f"{tool.name} offers excellent exit portability. Low lock-in risk. "
            f"Safe for deep integration and long-term commitment."
        )
    elif score >= 5:
        status = "Moderate Portability"
        recommendation = (
            f"{tool.name} has standard portability. Review export capabilities "
            f"and negotiate termination terms before deep integration."
        )
    else:
        status = "High Lock-in Risk"
        recommendation = (
            f"⚠️ {tool.name} presents significant exit barriers. "
            f"{'; '.join(penalties[:2])} "
            f"Consider negotiating better exit terms or use a competitor."
        )
        # Trigger philosophy.py elimination flag
        _trigger_elimination_if_severe(tool, score, penalties)

    return {
        "tool_name": tool.name,
        "score": score,
        "status": status,
        "reasons": penalties,
        "breakdown": breakdown,
        "contract_data": {
            "export_formats": contract.export_formats,
            "guaranteed_export_days": contract.guaranteed_export_days,
            "guarantees_deletion": contract.guarantees_deletion,
            "cancellation_fee": contract.cancellation_fee,
            "notice_period_days": contract.notice_period_days,
            "supports_iso_19941": contract.supports_iso_19941,
            "has_api_export": contract.has_api_export,
        },
        "recommendation": recommendation,
        "eu_data_act_compliant": eu_compliant,
    }


def _infer_contract(tool) -> ContractData:
    """Infer contract data from tool attributes when no curated data exists."""
    compliance = set(getattr(tool, "compliance", []) or [])
    integrations = getattr(tool, "integrations", []) or []
    categories = [c.lower() for c in getattr(tool, "categories", []) or []]

    # Heuristic: open-source tools generally have excellent portability
    tags = {t.lower() for t in getattr(tool, "tags", []) or []}
    keywords = {k.lower() for k in getattr(tool, "keywords", []) or []}
    is_open = "open-source" in tags | keywords or "self-hosted" in tags | keywords

    if is_open:
        return ContractData(
            supports_iso_19941=True,
            export_formats=["json", "csv"],
            guaranteed_export_days=0,
            guarantees_deletion=True,
            cancellation_fee=0,
            notice_period_days=0,
            has_api_export=True,
        )

    # Heuristic: high lock-in categories
    high_lock_in_cats = {"crm", "e-commerce", "analytics", "data"}
    if any(c in high_lock_in_cats for c in categories):
        return ContractData(
            export_formats=["csv"],
            guaranteed_export_days=60,
            guarantees_deletion=True,
            cancellation_fee=0,
            notice_period_days=30,
        )

    # Default: moderate
    return ContractData(
        export_formats=["json"] if "SOC2" in compliance else [],
        guaranteed_export_days=30,
        guarantees_deletion="GDPR" in compliance,
        cancellation_fee=0,
        notice_period_days=0,
    )


def _trigger_elimination_if_severe(tool, score: int, penalties: list):
    """Log severe lock-in for philosophy.py elimination flag integration."""
    if score <= 3:
        logger.warning(
            "ELIMINATION FLAG — %s: portability_score=%d, penalties=%s",
            tool.name, score, penalties
        )


# ======================================================================
# Batch & Comparison
# ======================================================================

def calculate_all_portability(tools: list) -> dict:
    """Calculate portability for all tools.

    Returns:
        {
            "tools": { tool_name: portability_result },
            "summary": {
                "avg_score": float,
                "high_portability": int,
                "moderate": int,
                "high_lock_in": int,
                "eu_compliant_pct": float,
            }
        }
    """
    results = {}
    scores = []
    high = moderate = lock_in = eu_count = 0

    for tool in tools:
        result = calculate_exit_portability(tool)
        results[tool.name] = result
        scores.append(result["score"])

        if result["status"] == "High Portability":
            high += 1
        elif result["status"] == "Moderate Portability":
            moderate += 1
        else:
            lock_in += 1

        if result["eu_data_act_compliant"]:
            eu_count += 1

    total = len(tools) or 1
    return {
        "tools": results,
        "summary": {
            "avg_score": round(sum(scores) / max(1, len(scores)), 1),
            "high_portability": high,
            "moderate": moderate,
            "high_lock_in": lock_in,
            "eu_compliant_pct": round(eu_count / total * 100, 1),
        },
    }


def compare_portability(tool_names: list, tools_db: list) -> list:
    """Side-by-side portability comparison for multiple tools."""
    tool_map = {t.name.lower(): t for t in tools_db}
    comparisons = []

    for name in tool_names:
        tool = tool_map.get(name.lower())
        if tool:
            result = calculate_exit_portability(tool)
            comparisons.append(result)

    comparisons.sort(key=lambda x: x["score"], reverse=True)
    return comparisons


logger.info(
    "Portability module loaded — %d vendor contracts profiled",
    len(_VENDOR_CONTRACTS)
)
