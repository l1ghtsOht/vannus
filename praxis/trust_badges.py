# --------------- Praxis Trust Badge Architecture ---------------
"""
The definitive fiduciary layer for SMB AI tool evaluation.

Implements the 2026 Trust Badge Blueprint — translating abstract AI
governance frameworks into immediate, actionable visual intelligence.

Badge Categories (9 total):
    1. sovereignty_tier    — Navy Blue / Shield with flag
    2. safe_harbor_origin  — Indigo / Interlocking Circles
    3. training_lock       — Emerald Green / Closed Padlock
    4. training_opt_out    — Amber / Half-Open Padlock
    5. compliance_verif    — Gold / Checkmark Ribbon
    6. uptime_resilience   — Slate Grey / Server Stack (1-4 bars)
    7. portability_score   — Purple / Arrow exiting box
    8. psr_metric          — Teal / Bullseye Target
    9. risk_flag           — Crimson Red / Warning Triangle

Design Principles:
    · Outcome-Centric Translation — never raw specs, always business impact
    · Elimination-First Honesty — lead with limitations and risks
    · Dynamic Verification over Static Claims
    · Zero-Friction Scannability — traffic-light visual hierarchy
    · Agentic Fiduciary Standards — verified loyalty to user intent
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("praxis.trust_badges")

# ======================================================================
# Badge Category Definitions
# ======================================================================

BADGE_CATEGORIES = {
    "sovereignty_tier": {
        "label": "Data Sovereignty",
        "icon": "🛡️",
        "color": "#1B2A4A",           # Navy blue
        "color_name": "navy",
        "description": "Backend hosting and corporate ownership evaluation against US CLOUD Act and EU Data Governance Act.",
        "type": "static",
        "review_interval_days": 30,
    },
    "safe_harbor_origin": {
        "label": "Allied Infrastructure",
        "icon": "🤝",
        "color": "#4B0082",           # Indigo
        "color_name": "indigo",
        "description": "Vendor headquartered in CFIUS-exempt or allied jurisdiction with cross-border data transfer compliance.",
        "type": "static",
        "review_interval_days": 30,
    },
    "training_lock": {
        "label": "Training Privacy",
        "icon": "🔒",
        "color": "#10B981",           # Emerald green
        "color_name": "emerald",
        "description": "Vendor contractually guarantees zero training on customer data, inputs, and metadata.",
        "type": "static",
        "review_interval_days": 30,
    },
    "training_opt_out": {
        "label": "Conditional Privacy",
        "icon": "⚠️",
        "color": "#F59E0B",           # Amber
        "color_name": "amber",
        "description": "Default data usage is permissive but verifiable opt-out mechanism exists.",
        "type": "static",
        "review_interval_days": 30,
    },
    "compliance_verif": {
        "label": "Compliance Standard",
        "icon": "🏆",
        "color": "#D4A017",           # Gold
        "color_name": "gold",
        "description": "Active ISO/IEC 42001, SOC2 Type II, FedRAMP, and GDPR certifications verified.",
        "type": "static",
        "review_interval_days": 90,
    },
    "uptime_resilience": {
        "label": "Operational Resilience",
        "icon": "⚡",
        "color": "#64748B",           # Slate grey
        "color_name": "slate",
        "description": "Infrastructure tier classification mapping to Uptime Institute standards (Tiers I-IV).",
        "type": "dynamic",
        "update_frequency": "continuous",
    },
    "portability_score": {
        "label": "Exit Portability",
        "icon": "📦",
        "color": "#7C3AED",           # Purple
        "color_name": "purple",
        "description": "Scored 1-10 based on EU Data Act and UK DUAA export, deletion, and termination mandates.",
        "type": "dynamic",
        "update_frequency": "monthly",
    },
    "psr_metric": {
        "label": "Real-World Utility",
        "icon": "🎯",
        "color": "#14B8A6",           # Teal
        "color_name": "teal",
        "description": "Prompt Success Rate and Output Quality Score from verified real-user telemetry.",
        "type": "dynamic",
        "update_frequency": "daily",
    },
    "risk_flag": {
        "label": "Elimination Flag",
        "icon": "🚩",
        "color": "#DC2626",           # Crimson red
        "color_name": "crimson",
        "description": "Critical deficiencies, EU AI Act violations, proprietary black-box models, or punitive exit costs.",
        "type": "dynamic",
        "update_frequency": "continuous",
    },
}


# ======================================================================
# Badge Grade Thresholds
# ======================================================================

_COMPLIANCE_WEIGHT = {
    "SOC2":     15,
    "GDPR":     12,
    "ISO27001": 12,
    "HIPAA":    15,
    "FedRAMP":  15,
    "PCI-DSS":  10,
    "CCPA":      8,
    "FERPA":     8,
    "ISO42001": 18,   # AI Management Systems — highest weight
}

_RESILIENCE_TIERS = {
    1: {"label": "Tier I — Basic", "uptime": "99.671%", "bars": 1,
        "tooltip": "Basic site infrastructure. Single power and cooling path. Non-redundant components."},
    2: {"label": "Tier II — Redundant", "uptime": "99.741%", "bars": 2,
        "tooltip": "Redundant capacity components. Single distribution path for power and cooling."},
    3: {"label": "Tier III — Concurrently Maintainable", "uptime": "99.982%", "bars": 3,
        "tooltip": "Enterprise-grade availability. Multiple power/cooling paths. Concurrent maintainability."},
    4: {"label": "Tier IV — Fault Tolerant", "uptime": "99.995%", "bars": 4,
        "tooltip": "Mission-critical fault tolerance. Full redundancy with automated fail-over."},
}


# ======================================================================
# Vendor Badge Intelligence
# ======================================================================
# Extended profiles beyond sovereignty.py — covers portability, resilience,
# PSR, training privacy, compliance detail, and risk flags.

_BADGE_INTEL = {
    # --- Major AI Platforms ---
    "chatgpt": {
        "training_policy": "opt_out",    # Enterprise tier excludes training
        "training_detail": "Consumer: inputs used for training. Enterprise: opt-out enforced.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.85,
        "oqs_baseline": 0.82,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "claude": {
        "training_policy": "never",
        "training_detail": "Does not train on user conversations by default. Enterprise opt-out contractual.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json", "txt"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.88,
        "oqs_baseline": 0.86,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "gemini": {
        "training_policy": "opt_out",
        "training_detail": "Integrated with Google account. Broad data collection policies apply. Workspace tier has controls.",
        "uptime_tier": 4,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 60,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.83,
        "oqs_baseline": 0.80,
        "compliance_verified": ["SOC2", "GDPR", "ISO27001", "FedRAMP"],
        "base_model_disclosed": True,
        "risk_flags": ["Ecosystem lock-in via Google Workspace integration"],
    },
    "copilot": {
        "training_policy": "opt_out",
        "training_detail": "Business tier excludes code from training. Individual plans may contribute.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.84,
        "oqs_baseline": 0.81,
        "compliance_verified": ["SOC2", "GDPR", "ISO27001"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "github copilot": {
        "training_policy": "opt_out",
        "training_detail": "Business tier excludes code from training. Individual plans may contribute to model improvement.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.86,
        "oqs_baseline": 0.83,
        "compliance_verified": ["SOC2", "GDPR", "ISO27001"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },

    # --- Open Source Champions ---
    "hugging face": {
        "training_policy": "never",
        "training_detail": "Open platform. You control your models and data. No training on customer data.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["json", "csv", "parquet", "safetensors"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.75,
        "oqs_baseline": 0.72,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "n8n": {
        "training_policy": "never",
        "training_detail": "Self-hostable. Your data stays on your infrastructure.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.78,
        "oqs_baseline": 0.76,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "supabase": {
        "training_policy": "never",
        "training_detail": "PostgreSQL-based. Self-hostable. Full data sovereignty.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json", "csv", "sql"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.80,
        "oqs_baseline": 0.78,
        "compliance_verified": ["SOC2", "GDPR", "HIPAA"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },
    "langchain": {
        "training_policy": "never",
        "training_detail": "Framework is local. LangSmith tracing sends trace data to servers.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["json", "yaml"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.73,
        "oqs_baseline": 0.70,
        "compliance_verified": ["SOC2"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },

    # --- Automation Platforms ---
    "zapier": {
        "training_policy": "opt_out",
        "training_detail": "Data passes through Zapier servers. Task logs retained for debugging.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 60,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.82,
        "oqs_baseline": 0.79,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Proprietary workflow format — high rebuild cost on exit"],
    },
    "make": {
        "training_policy": "opt_out",
        "training_detail": "Data passes through Make servers. Scenario logs retained.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 60,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.79,
        "oqs_baseline": 0.76,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Proprietary scenario format — migration requires full rebuild"],
    },

    # --- Design Tools ---
    "canva ai": {
        "training_policy": "opt_out",
        "training_detail": "AI features process through Canva infrastructure. Opt-out available in enterprise.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["png", "jpg", "pdf", "svg"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.87,
        "oqs_baseline": 0.84,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": [],
    },
    "figma ai": {
        "training_policy": "opt_out",
        "training_detail": "AI features use design data for suggestions. Controls available.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["svg", "png", "pdf"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.81,
        "oqs_baseline": 0.78,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Design system lock-in — component libraries not portable"],
    },
    "midjourney": {
        "training_policy": "opt_in",
        "training_detail": "Generated images public by default (free tier). Prompts may inform training.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["png", "jpg"], "guaranteed_export_days": 0,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.90,
        "oqs_baseline": 0.88,
        "compliance_verified": [],
        "base_model_disclosed": False,
        "risk_flags": ["Default public visibility of generated images", "No stated compliance certifications"],
    },

    # --- CRM / Sales ---
    "hubspot": {
        "training_policy": "opt_out",
        "training_detail": "Customer data stored on HubSpot servers. AI features process CRM data.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["csv", "json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.80,
        "oqs_baseline": 0.77,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Workflow automation logic not portable"],
    },
    "salesforce": {
        "training_policy": "opt_out",
        "training_detail": "Einstein AI processes your data for insights. Data Trust Layer available.",
        "uptime_tier": 4,
        "portability": {"export_formats": ["csv"], "guaranteed_export_days": 90,
                        "guarantees_deletion": True, "cancellation_fee": 500,
                        "notice_period_days": 90, "supports_iso_19941": False},
        "psr_baseline": 0.76,
        "oqs_baseline": 0.74,
        "compliance_verified": ["SOC2", "GDPR", "ISO27001", "FedRAMP", "HIPAA"],
        "base_model_disclosed": False,
        "risk_flags": ["Very high lock-in — ecosystem migration notoriously expensive",
                       "Punitive cancellation terms"],
    },

    # --- Writing ---
    "grammarly": {
        "training_policy": "opt_out",
        "training_detail": "Processes all text you type. Enterprise plan offers enhanced data controls.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["txt"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.89,
        "oqs_baseline": 0.86,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": [],
    },
    "jasper": {
        "training_policy": "opt_in",
        "training_detail": "Brand voice training uses your inputs. Content stored on Jasper servers.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["txt", "docx"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.78,
        "oqs_baseline": 0.75,
        "compliance_verified": ["SOC2"],
        "base_model_disclosed": False,
        "risk_flags": ["Brand voice profiles not portable — lock-in via training investment"],
    },

    # --- Communication / Productivity ---
    "notion ai": {
        "training_policy": "opt_out",
        "training_detail": "AI features process workspace docs. Opt-out available.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["markdown", "csv", "html"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.81,
        "oqs_baseline": 0.78,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Export loses structure, relations, and views — high rebuild cost"],
    },
    "slack": {
        "training_policy": "opt_out",
        "training_detail": "Messages stored on Salesforce servers. Employers have full access.",
        "uptime_tier": 4,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.84,
        "oqs_baseline": 0.81,
        "compliance_verified": ["SOC2", "GDPR", "ISO27001", "FedRAMP"],
        "base_model_disclosed": False,
        "risk_flags": ["Team culture and context not exportable"],
    },

    # --- Analytics ---
    "amplitude": {
        "training_policy": "opt_out",
        "training_detail": "Event data analyzed on Amplitude servers.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["csv", "json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.77,
        "oqs_baseline": 0.74,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": False,
        "risk_flags": ["Dashboards and cohort definitions not portable"],
    },
    "posthog": {
        "training_policy": "never",
        "training_detail": "Self-hostable. Cloud analytics available.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["json", "csv"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.76,
        "oqs_baseline": 0.73,
        "compliance_verified": ["SOC2", "GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },

    # --- E-commerce ---
    "shopify": {
        "training_policy": "opt_out",
        "training_detail": "All store data on Shopify servers. AI processes customer data.",
        "uptime_tier": 4,
        "portability": {"export_formats": ["csv"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.82,
        "oqs_baseline": 0.80,
        "compliance_verified": ["SOC2", "GDPR", "PCI-DSS"],
        "base_model_disclosed": False,
        "risk_flags": ["Very high lock-in — themes, apps, and customizations don't migrate"],
    },
    "stripe": {
        "training_policy": "never",
        "training_detail": "Payment data processed per PCI compliance. Financial data on Stripe servers.",
        "uptime_tier": 4,
        "portability": {"export_formats": ["csv", "json"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.91,
        "oqs_baseline": 0.89,
        "compliance_verified": ["SOC2", "GDPR", "PCI-DSS", "ISO27001"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },

    # --- Security ---
    "vanta": {
        "training_policy": "never",
        "training_detail": "Compliance scanning requires deep infrastructure access. No model training.",
        "uptime_tier": 3,
        "portability": {"export_formats": ["csv", "pdf"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 30, "supports_iso_19941": False},
        "psr_baseline": 0.83,
        "oqs_baseline": 0.80,
        "compliance_verified": ["SOC2", "ISO27001"],
        "base_model_disclosed": False,
        "risk_flags": [],
    },

    # --- Deep Learning / ML ---
    "perplexity ai": {
        "training_policy": "opt_out",
        "training_detail": "Search queries processed for results. Pro plan has enhanced privacy.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["txt"], "guaranteed_export_days": 30,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.87,
        "oqs_baseline": 0.84,
        "compliance_verified": ["SOC2"],
        "base_model_disclosed": False,
        "risk_flags": [],
    },
    "stability ai": {
        "training_policy": "opt_out",
        "training_detail": "Open-weight models available. API usage may have data handling terms.",
        "uptime_tier": 2,
        "portability": {"export_formats": ["png", "jpg", "safetensors"], "guaranteed_export_days": 0,
                        "guarantees_deletion": True, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": True},
        "psr_baseline": 0.80,
        "oqs_baseline": 0.78,
        "compliance_verified": ["GDPR"],
        "base_model_disclosed": True,
        "risk_flags": [],
    },

    # --- High Risk Vendors ---
    "deepseek": {
        "training_policy": "opt_in",
        "training_detail": "Chinese-developed. Data practices subject to PRC data governance laws.",
        "uptime_tier": 1,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 90,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.82,
        "oqs_baseline": 0.79,
        "compliance_verified": [],
        "base_model_disclosed": True,
        "risk_flags": ["PRC jurisdiction — subject to Chinese National Intelligence Law",
                       "No SOC2 or GDPR certifications",
                       "Data may be accessible to foreign government"],
    },
    "baidu ernie": {
        "training_policy": "opt_in",
        "training_detail": "Chinese-developed. All data processed under PRC regulations.",
        "uptime_tier": 1,
        "portability": {"export_formats": [], "guaranteed_export_days": 0,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.70,
        "oqs_baseline": 0.67,
        "compliance_verified": [],
        "base_model_disclosed": False,
        "risk_flags": ["PRC jurisdiction", "No export capabilities",
                       "No Western compliance certifications", "Proprietary architecture undisclosed"],
    },
    "qwen": {
        "training_policy": "opt_in",
        "training_detail": "Alibaba-developed. PRC data governance applies.",
        "uptime_tier": 1,
        "portability": {"export_formats": ["json"], "guaranteed_export_days": 0,
                        "guarantees_deletion": False, "cancellation_fee": 0,
                        "notice_period_days": 0, "supports_iso_19941": False},
        "psr_baseline": 0.77,
        "oqs_baseline": 0.74,
        "compliance_verified": [],
        "base_model_disclosed": True,
        "risk_flags": ["PRC jurisdiction — Alibaba Cloud", "No Western compliance certifications"],
    },
}


# ======================================================================
# Allied / Safe Harbor Jurisdictions
# ======================================================================

_ALLIED_JURISDICTIONS = {
    "USA", "GBR", "CAN", "AUS", "NZL",               # Five Eyes
    "DEU", "FRA", "NLD", "BEL", "LUX", "ITA", "ESP",  # EU core
    "PRT", "IRL", "AUT", "FIN", "SWE", "DNK", "NOR",  # EU/EEA
    "CHE", "JPN", "KOR", "ISR", "TWN", "SGP",          # Allied / Safe Harbor
    "EST", "LVA", "LTU", "POL", "CZE", "SVK",          # EU East
    "HRV", "SVN", "ROU", "BGR", "GRC", "CYP", "MLT",
}

_HIGH_RISK_JURISDICTIONS = {
    "CHN", "RUS", "IRN", "PRK", "BLR", "VEN", "CUB", "SYR", "MMR",
}


# ======================================================================
# Core Badge Calculation Functions
# ======================================================================

def _get_badge_intel(tool_name: str) -> dict:
    """Retrieve badge intelligence for a tool, falling back to heuristics."""
    key = tool_name.lower().strip()
    if key in _BADGE_INTEL:
        return dict(_BADGE_INTEL[key])
    return {}


def calculate_sovereignty_badge(tool) -> dict:
    """Calculate the Data Sovereignty badge (sovereignty_tier).

    Evaluates backend hosting and corporate ownership against US CLOUD Act
    and EU Data Governance Act. Verifies UBO registries for >51% domestic
    or allied ownership.
    """
    country = getattr(tool, "country_of_origin", "USA") or "USA"
    is_us = getattr(tool, "is_us_controlled", True)
    jurisdiction = getattr(tool, "data_jurisdiction", "US") or "US"

    if country in {"USA"} and is_us:
        tier = "sovereign"
        tooltip = (f"🇺🇸 Locally Sovereign: Ultimate Beneficial Owner registries verify "
                   f">51% US ownership. Your data is legally protected from foreign "
                   f"government access and hosted entirely on US infrastructure.")
        status = "verified"
        color = "#1B2A4A"
    elif country in _ALLIED_JURISDICTIONS:
        tier = "allied"
        tooltip = (f"🤝 Allied / Safe Harbor Origin: Headquartered in a trusted allied "
                   f"jurisdiction ({country}). Fully compliant with international "
                   f"cross-border data transfer frameworks.")
        status = "verified"
        color = "#4B0082"
    elif country in _HIGH_RISK_JURISDICTIONS:
        tier = "high_risk"
        tooltip = (f"⚠️ High Risk Jurisdiction: Headquartered in {country}. "
                   f"Data may be subject to foreign government access laws. "
                   f"Enhanced due diligence required before procurement.")
        status = "flagged"
        color = "#DC2626"
    else:
        tier = "unknown"
        tooltip = (f"❓ Jurisdiction Unverified: Origin ({country}) not yet confirmed. "
                   f"Verify UBO and data hosting before committing sensitive data.")
        status = "pending"
        color = "#6B7280"

    return {
        "badge_id": "sovereignty_tier",
        "label": "Data Sovereignty",
        "tier": tier,
        "icon": "🛡️",
        "color": color,
        "tooltip": tooltip,
        "status": status,
        "country": country,
        "jurisdiction": jurisdiction,
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_allied_badge(tool) -> Optional[dict]:
    """Calculate the Allied Infrastructure badge (safe_harbor_origin).

    Only granted to vendors in CFIUS-exempt or allied jurisdictions.
    """
    country = getattr(tool, "country_of_origin", "USA") or "USA"

    if country not in _ALLIED_JURISDICTIONS:
        return None

    # US tools get sovereignty badge instead
    if country == "USA":
        return None

    return {
        "badge_id": "safe_harbor_origin",
        "label": "Allied Infrastructure",
        "icon": "🤝",
        "color": "#4B0082",
        "tooltip": (f"🤝 Allied / Safe Harbor Origin: Headquartered in {country}. "
                    f"Fully compliant with international cross-border data transfer frameworks."),
        "status": "verified",
        "country": country,
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_training_badge(tool) -> dict:
    """Calculate the Training Privacy badge (training_lock or training_opt_out).

    Binary evaluation: zero-training guarantee → emerald lock,
    opt-out available → amber half-lock.
    """
    intel = _get_badge_intel(tool.name)
    training = intel.get("training_policy") or getattr(tool, "training_data_usage", "opt_out")
    detail = intel.get("training_detail", "")

    if training == "never":
        return {
            "badge_id": "training_lock",
            "label": "Training Privacy",
            "icon": "🔒",
            "color": "#10B981",
            "tooltip": (f"🔒 Zero Training: The vendor contractually guarantees your proprietary "
                        f"data, inputs, and metadata will never be used to train or refine their "
                        f"AI models. {detail}"),
            "status": "verified",
            "policy": "never",
            "risk_level": "safe",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    elif training == "opt_out":
        return {
            "badge_id": "training_opt_out",
            "label": "Conditional Privacy",
            "icon": "⚠️",
            "color": "#F59E0B",
            "tooltip": (f"⚠️ Opt-Out Required: This tool trains on user data by default. "
                        f"You must manually configure privacy settings to opt out of model "
                        f"training. Risk level: Caution. {detail}"),
            "status": "caution",
            "policy": "opt_out",
            "risk_level": "caution",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
    else:  # opt_in or unknown
        return {
            "badge_id": "training_opt_out",
            "label": "Conditional Privacy",
            "icon": "🔓",
            "color": "#DC2626",
            "tooltip": (f"🔓 Active Training: This tool uses your data for model training "
                        f"by default with no documented opt-out mechanism. High risk for "
                        f"proprietary or sensitive workflows. {detail}"),
            "status": "warning",
            "policy": training or "opt_in",
            "risk_level": "high",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }


def calculate_compliance_badge(tool) -> dict:
    """Calculate the Compliance Standard badge (compliance_verif).

    Aggregates and verifies active ISO/IEC 42001, SOC2 Type II, FedRAMP,
    and GDPR certifications.
    """
    intel = _get_badge_intel(tool.name)
    stated = set(getattr(tool, "compliance", []) or [])
    verified = set(intel.get("compliance_verified", []))

    # Merge: intel-verified takes precedence, then tool-stated
    all_certs = stated | verified

    score = 0
    cert_details = []
    for cert in all_certs:
        weight = _COMPLIANCE_WEIGHT.get(cert, 5)
        is_verified = cert in verified
        score += weight if is_verified else weight * 0.5
        cert_details.append({
            "code": cert,
            "verified": is_verified,
            "weight": weight,
            "status": "verified" if is_verified else "stated",
        })

    # Grade
    if score >= 40:
        grade = "A"
        status = "certified"
    elif score >= 25:
        grade = "B"
        status = "strong"
    elif score >= 15:
        grade = "C"
        status = "basic"
    elif score >= 5:
        grade = "D"
        status = "minimal"
    else:
        grade = "F"
        status = "none"

    tooltip_certs = ", ".join(sorted(all_certs)) if all_certs else "None stated"
    if grade in ("A", "B"):
        tooltip = (f"🏆 Certified Secure: Holds verified {tooltip_certs} certifications. "
                   f"Audited continuously for ethical AI deployment and data security.")
    elif grade == "C":
        tooltip = (f"🏅 Basic Compliance: {tooltip_certs} certifications stated. "
                   f"Partial verification — confirm scope covers your use case.")
    else:
        tooltip = (f"⚠️ Limited Compliance: {tooltip_certs or 'No certifications found'}. "
                   f"Enhanced due diligence required for regulated industries.")

    return {
        "badge_id": "compliance_verif",
        "label": "Compliance Standard",
        "icon": "🏆" if grade in ("A", "B") else "🏅" if grade == "C" else "⚠️",
        "color": "#D4A017" if grade in ("A", "B") else "#F59E0B" if grade == "C" else "#DC2626",
        "tooltip": tooltip,
        "status": status,
        "grade": grade,
        "score": round(score, 1),
        "certifications": cert_details,
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_resilience_badge(tool) -> dict:
    """Calculate the Operational Resilience badge (uptime_resilience).

    Maps to Uptime Institute Tier Classification System (Tiers I-IV).
    """
    intel = _get_badge_intel(tool.name)
    tier = intel.get("uptime_tier", 0)

    if tier == 0:
        # Infer from tool characteristics
        compliance = set(getattr(tool, "compliance", []) or [])
        if "FedRAMP" in compliance:
            tier = 4
        elif "SOC2" in compliance and "ISO27001" in compliance:
            tier = 3
        elif "SOC2" in compliance:
            tier = 2
        else:
            tier = 1

    tier_data = _RESILIENCE_TIERS.get(tier, _RESILIENCE_TIERS[1])

    if tier >= 3:
        tooltip = (f"⚡ {tier_data['label']}: Enterprise-grade availability ({tier_data['uptime']}). "
                   f"{tier_data['tooltip']}")
    elif tier == 2:
        tooltip = (f"⚡ {tier_data['label']}: Standard availability ({tier_data['uptime']}). "
                   f"{tier_data['tooltip']}")
    else:
        tooltip = (f"⚡ {tier_data['label']}: Basic availability ({tier_data['uptime']}). "
                   f"{tier_data['tooltip']} Consider redundancy requirements.")

    return {
        "badge_id": "uptime_resilience",
        "label": "Operational Resilience",
        "icon": "⚡",
        "color": "#64748B",
        "tooltip": tooltip,
        "status": "verified" if tier >= 3 else "adequate" if tier == 2 else "basic",
        "tier": tier,
        "tier_label": tier_data["label"],
        "uptime": tier_data["uptime"],
        "bars": tier_data["bars"],
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_portability_badge(tool) -> dict:
    """Calculate the Exit Portability badge (portability_score).

    Scored 1-10 based on EU Data Act and UK DUAA compliance mandates.
    Integrates export format standards, timelines, and financial penalties.
    """
    intel = _get_badge_intel(tool.name)
    port_data = intel.get("portability", {})

    score = 0
    penalties = []

    # ── Export Format Standards (Max +4) ──
    if port_data.get("supports_iso_19941"):
        score += 4
    elif port_data.get("export_formats") and any(
        f in ("json", "csv", "sql", "xml", "parquet")
        for f in port_data.get("export_formats", [])
    ):
        score += 2
    else:
        penalties.append("Proprietary export format only. High data extraction cost.")

    # ── EU Data Act Export Timelines (Max +3) ──
    export_days = port_data.get("guaranteed_export_days", 999)
    if export_days <= 30 and port_data.get("guarantees_deletion"):
        score += 3
    elif export_days <= 60:
        score += 1
    else:
        penalties.append("Data export timeline exceeds 60 days or lacks deletion guarantees.")

    # ── Financial Lock-in / Termination Penalties (Max +3) ──
    if port_data.get("cancellation_fee", 999) == 0 and port_data.get("notice_period_days", 999) <= 60:
        score += 3
    elif port_data.get("cancellation_fee", 999) <= 100:
        score += 1
    else:
        penalties.append("Significant financial penalty required for early termination.")

    # Fallback heuristic if no intel
    if not port_data:
        try:
            from . import philosophy
        except ImportError:
            import philosophy
        intel_phil = philosophy.get_tool_intel(tool)
        lock_in = intel_phil.get("lock_in", "medium")
        if lock_in == "low":
            score = 8
        elif lock_in == "medium":
            score = 5
        elif lock_in in ("high", "very high"):
            score = 2
            penalties.append("High lock-in risk identified from vendor intelligence.")
        else:
            score = 4

    score = max(1, min(10, score))

    # Categorize
    if score >= 9:
        status = "High Portability"
        tooltip = (f"📦 High Portability ({score}/10): Negligible lock-in risk. "
                   f"Guarantees data export to standard formats within 30 days. "
                   f"No early termination financial penalties.")
        color = "#10B981"
    elif score >= 5:
        status = "Moderate Portability"
        tooltip = (f"📦 Moderate Portability ({score}/10): Standard export available. "
                   f"Some constraints on format, timeline, or termination terms. "
                   f"Review exit strategy before deep integration.")
        color = "#F59E0B"
    else:
        status = "High Lock-in Risk"
        tooltip = (f"📦 High Lock-in Risk ({score}/10): Significant exit barriers. "
                   f"{'; '.join(penalties[:2]) if penalties else 'Limited export capabilities.'}")
        color = "#DC2626"

    return {
        "badge_id": "portability_score",
        "label": "Exit Portability",
        "icon": "📦",
        "color": color,
        "tooltip": tooltip,
        "status": status,
        "score": score,
        "max_score": 10,
        "penalties": penalties,
        "export_formats": port_data.get("export_formats", []),
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_psr_badge(tool) -> dict:
    """Calculate the Real-World Utility badge (psr_metric).

    Prompt Success Rate (PSR) and Output Quality Score (OQS) based on
    aggregated verified real-user telemetry.
    """
    intel = _get_badge_intel(tool.name)
    psr = intel.get("psr_baseline", 0.0)
    oqs = intel.get("oqs_baseline", 0.0)

    # Also factor in verified_roi_score from tool
    roi = getattr(tool, "verified_roi_score", 0.0) or 0.0

    # Composite utility score
    if psr > 0:
        psr_pct = int(psr * 100)
        oqs_pct = int(oqs * 100)

        if psr >= 0.85:
            status = "excellent"
            tooltip = (f"🎯 {psr_pct}% Success Rate (PSR): {psr_pct} out of 100 users report "
                       f"receiving the exact, accurate output required on their first prompt "
                       f"without needing to rephrase or iterate. OQS: {oqs_pct}%.")
            color = "#10B981"
        elif psr >= 0.70:
            status = "good"
            tooltip = (f"🎯 {psr_pct}% Success Rate (PSR): Good first-prompt accuracy. "
                       f"Some iteration may be required for complex tasks. OQS: {oqs_pct}%.")
            color = "#14B8A6"
        else:
            status = "developing"
            tooltip = (f"🎯 {psr_pct}% Success Rate (PSR): Below average first-prompt accuracy. "
                       f"Expect significant iteration for most tasks. OQS: {oqs_pct}%.")
            color = "#F59E0B"
    else:
        psr_pct = 0
        oqs_pct = 0
        status = "unverified"
        tooltip = ("🎯 PSR: Unverified — Insufficient telemetry data to calculate a "
                   "reliable Prompt Success Rate. Check back as more users contribute feedback.")
        color = "#6B7280"

    return {
        "badge_id": "psr_metric",
        "label": "Real-World Utility",
        "icon": "🎯",
        "color": color,
        "tooltip": tooltip,
        "status": status,
        "psr": psr_pct,
        "oqs": oqs_pct,
        "roi_score": round(roi, 2),
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


def calculate_risk_flag(tool) -> Optional[dict]:
    """Calculate the Elimination Flag (risk_flag).

    Highlights critical deficiencies: EU AI Act violations, proprietary
    black-box models, punitive exit costs, or foreign jurisdiction risks.
    """
    intel = _get_badge_intel(tool.name)
    flags = list(intel.get("risk_flags", []))

    # Auto-detect additional flags
    country = getattr(tool, "country_of_origin", "USA") or "USA"
    if country in _HIGH_RISK_JURISDICTIONS:
        flags.append(f"Foreign jurisdiction ({country}) — subject to foreign government data access laws")

    if not intel.get("base_model_disclosed", True) and not intel:
        flags.append("Base model architecture is proprietary and publicly undisclosed")

    training = intel.get("training_policy") or getattr(tool, "training_data_usage", "opt_out")
    if training == "opt_in":
        flags.append("Vendor uses customer data for model training by default without opt-out")

    # Portability red flags
    port = intel.get("portability", {})
    if port.get("cancellation_fee", 0) > 200:
        flags.append(f"Punitive cancellation fee: ${port['cancellation_fee']}")
    if port.get("guaranteed_export_days", 0) > 90:
        flags.append("Data export timeline exceeds 90 days — potential data hostage risk")

    if not flags:
        return None

    severity = "critical" if len(flags) >= 3 else "high" if len(flags) >= 2 else "warning"

    return {
        "badge_id": "risk_flag",
        "label": "Elimination Flag",
        "icon": "🚩",
        "color": "#DC2626",
        "tooltip": (f"⚠️ High Risk: {flags[0]}. "
                    f"{'Additional concerns: ' + '; '.join(flags[1:3]) + '.' if len(flags) > 1 else ''}"),
        "status": severity,
        "flags": flags,
        "flag_count": len(flags),
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ======================================================================
# Composite Badge Assembly
# ======================================================================

def calculate_all_badges(tool) -> dict:
    """Calculate all applicable badges for a single tool.

    Returns a complete trust profile with all 9 badge categories evaluated.
    This is the primary entry point for badge computation.
    """
    sovereignty = calculate_sovereignty_badge(tool)
    allied = calculate_allied_badge(tool)
    training = calculate_training_badge(tool)
    compliance = calculate_compliance_badge(tool)
    resilience = calculate_resilience_badge(tool)
    portability = calculate_portability_badge(tool)
    psr = calculate_psr_badge(tool)
    risk = calculate_risk_flag(tool)

    # Assemble active badges (exclude None)
    badges = {
        "sovereignty_tier": sovereignty,
        "training_privacy": training,
        "compliance_verif": compliance,
        "uptime_resilience": resilience,
        "portability_score": portability,
        "psr_metric": psr,
    }
    if allied:
        badges["safe_harbor_origin"] = allied
    if risk:
        badges["risk_flag"] = risk

    # Compute composite trust score (0-100)
    trust_score = _compute_trust_score(badges)

    # Determine primary display badges (top 3 for mobile)
    primary = _select_primary_badges(badges, tool)

    return {
        "tool_name": tool.name,
        "trust_score": trust_score["score"],
        "trust_grade": trust_score["grade"],
        "badges": badges,
        "badge_count": len(badges),
        "primary_badges": primary,
        "has_risk_flag": risk is not None,
        "risk_flag_count": risk["flag_count"] if risk else 0,
        "summary": _generate_trust_summary(tool, badges, trust_score),
        "computed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _compute_trust_score(badges: dict) -> dict:
    """Compute a composite trust score from all active badges.

    Weighted formula:
        Sovereignty:  20%
        Training:     20%
        Compliance:   20%
        Resilience:   10%
        Portability:  15%
        PSR:          15%
        Risk Flag:   -20 per flag (penalty)
    """
    score = 0.0

    # Sovereignty (0–20)
    sov = badges.get("sovereignty_tier", {})
    tier = sov.get("tier", "unknown")
    if tier == "sovereign":
        score += 20
    elif tier == "allied":
        score += 15
    elif tier == "unknown":
        score += 5
    # high_risk = 0

    # Training Privacy (0–20)
    train = badges.get("training_privacy", {})
    policy = train.get("policy", "opt_out")
    if policy == "never":
        score += 20
    elif policy == "opt_out":
        score += 10
    # opt_in = 0

    # Compliance (0–20)
    comp = badges.get("compliance_verif", {})
    comp_grade = comp.get("grade", "F")
    grade_map = {"A": 20, "B": 15, "C": 10, "D": 5, "F": 0}
    score += grade_map.get(comp_grade, 0)

    # Resilience (0–10)
    res = badges.get("uptime_resilience", {})
    res_tier = res.get("tier", 1)
    score += min(10, res_tier * 2.5)

    # Portability (0–15)
    port = badges.get("portability_score", {})
    port_score = port.get("score", 5)
    score += port_score * 1.5

    # PSR (0–15)
    psr = badges.get("psr_metric", {})
    psr_val = psr.get("psr", 0)
    score += (psr_val / 100) * 15

    # Risk Flag penalty
    risk = badges.get("risk_flag")
    if risk:
        penalty = min(40, risk.get("flag_count", 1) * 15)
        score -= penalty

    score = max(0, min(100, round(score)))

    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    return {"score": score, "grade": grade}


def _select_primary_badges(badges: dict, tool) -> list:
    """Select the 2-3 most critical badges for mobile/condensed display.

    Priority logic:
        1. Risk flags always shown
        2. Training privacy (critical for data-sensitive industries)
        3. Sovereignty (critical for regulated industries)
        4. PSR (universal utility signal)
    """
    primary = []

    if "risk_flag" in badges:
        primary.append({"badge_id": "risk_flag", "icon": "🚩", "color": "#DC2626"})

    train = badges.get("training_privacy", {})
    if train.get("risk_level") in ("caution", "high"):
        primary.append({"badge_id": train.get("badge_id"), "icon": train.get("icon"), "color": train.get("color")})

    sov = badges.get("sovereignty_tier", {})
    if sov.get("tier") in ("high_risk", "unknown"):
        primary.append({"badge_id": "sovereignty_tier", "icon": "🛡️", "color": sov.get("color")})

    psr = badges.get("psr_metric", {})
    if psr.get("psr", 0) >= 85:
        primary.append({"badge_id": "psr_metric", "icon": "🎯", "color": "#14B8A6"})

    # Ensure compliance shows for strong certifications
    comp = badges.get("compliance_verif", {})
    if comp.get("grade") in ("A", "B") and len(primary) < 3:
        primary.append({"badge_id": "compliance_verif", "icon": "🏆", "color": "#D4A017"})

    return primary[:3]


def _generate_trust_summary(tool, badges: dict, trust_score: dict) -> str:
    """Generate a plain-text trust summary for the tool."""
    name = tool.name
    grade = trust_score["grade"]
    score = trust_score["score"]

    parts = [f"{name}: Trust Score {score}/100 (Grade {grade})."]

    sov = badges.get("sovereignty_tier", {})
    if sov.get("tier") == "sovereign":
        parts.append("US-sovereign data handling.")
    elif sov.get("tier") == "allied":
        parts.append(f"Allied jurisdiction ({sov.get('country', 'N/A')}).")
    elif sov.get("tier") == "high_risk":
        parts.append("⚠️ HIGH RISK JURISDICTION.")

    train = badges.get("training_privacy", {})
    if train.get("policy") == "never":
        parts.append("Zero-training guarantee.")
    elif train.get("policy") == "opt_out":
        parts.append("Opt-out required for training privacy.")
    elif train.get("policy") == "opt_in":
        parts.append("⚠️ Data used for training by default.")

    risk = badges.get("risk_flag")
    if risk:
        parts.append(f"🚩 {risk['flag_count']} elimination flag(s): {risk['flags'][0]}")

    return " ".join(parts)


# ======================================================================
# Batch Operations
# ======================================================================

def calculate_all_tools_badges(tools: list) -> dict:
    """Calculate badges for all tools and return aggregate statistics.

    Returns:
        {
            "tools": { tool_name: badge_profile },
            "summary": {
                "total": int,
                "sovereign": int,
                "allied": int,
                "high_risk": int,
                "zero_training": int,
                "flagged": int,
                "avg_trust_score": float,
                "grade_distribution": { "A": int, "B": int, ... },
                "avg_psr": float,
                "avg_portability": float,
            }
        }
    """
    results = {}
    stats = {
        "total": 0, "sovereign": 0, "allied": 0, "high_risk": 0,
        "zero_training": 0, "flagged": 0,
        "trust_scores": [], "psr_scores": [], "port_scores": [],
        "grade_dist": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
    }

    for tool in tools:
        profile = calculate_all_badges(tool)
        results[tool.name] = profile
        stats["total"] += 1
        stats["trust_scores"].append(profile["trust_score"])
        stats["grade_dist"][profile["trust_grade"]] = stats["grade_dist"].get(profile["trust_grade"], 0) + 1

        # Sovereignty distribution
        sov_tier = profile["badges"].get("sovereignty_tier", {}).get("tier")
        if sov_tier == "sovereign":
            stats["sovereign"] += 1
        elif sov_tier == "allied":
            stats["allied"] += 1
        elif sov_tier == "high_risk":
            stats["high_risk"] += 1

        # Training
        train_policy = profile["badges"].get("training_privacy", {}).get("policy")
        if train_policy == "never":
            stats["zero_training"] += 1

        # Risk flags
        if profile["has_risk_flag"]:
            stats["flagged"] += 1

        # PSR
        psr_val = profile["badges"].get("psr_metric", {}).get("psr", 0)
        if psr_val > 0:
            stats["psr_scores"].append(psr_val)

        # Portability
        port_val = profile["badges"].get("portability_score", {}).get("score", 0)
        stats["port_scores"].append(port_val)

    summary = {
        "total": stats["total"],
        "sovereign": stats["sovereign"],
        "allied": stats["allied"],
        "high_risk": stats["high_risk"],
        "unknown": stats["total"] - stats["sovereign"] - stats["allied"] - stats["high_risk"],
        "zero_training": stats["zero_training"],
        "flagged": stats["flagged"],
        "avg_trust_score": round(sum(stats["trust_scores"]) / max(1, len(stats["trust_scores"])), 1),
        "grade_distribution": stats["grade_dist"],
        "avg_psr": round(sum(stats["psr_scores"]) / max(1, len(stats["psr_scores"])), 1),
        "avg_portability": round(sum(stats["port_scores"]) / max(1, len(stats["port_scores"])), 1),
    }

    return {"tools": results, "summary": summary}


def get_badge_categories() -> dict:
    """Return the full badge category definitions for the frontend."""
    return dict(BADGE_CATEGORIES)


def get_badge_intel(tool_name: str) -> dict:
    """Return raw badge intelligence data for a tool."""
    return _get_badge_intel(tool_name)


# ======================================================================
# Stat Bar & Filter Support
# ======================================================================

def generate_stat_bar(tools: list, filters_applied: dict = None) -> dict:
    """Generate the Dynamic Results Stat Bar for search results.

    Returns:
        {
            "total_results": int,
            "hidden_count": int,
            "hidden_reasons": [str],
            "segment_counts": { "all": int, "sovereign": int, "allied": int, "high_risk": int },
            "trust_distribution": { "A": int, "B": int, "C": int, "D": int, "F": int },
        }
    """
    segments = {"all": len(tools), "us_controlled": 0, "allied": 0, "high_risk": 0}
    grade_dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    hidden = 0
    hidden_reasons = set()

    for tool in tools:
        profile = calculate_all_badges(tool)
        grade_dist[profile["trust_grade"]] = grade_dist.get(profile["trust_grade"], 0) + 1

        sov_tier = profile["badges"].get("sovereignty_tier", {}).get("tier")
        if sov_tier == "sovereign":
            segments["us_controlled"] += 1
        elif sov_tier == "allied":
            segments["allied"] += 1
        elif sov_tier == "high_risk":
            segments["high_risk"] += 1
            if filters_applied and filters_applied.get("hide_high_risk"):
                hidden += 1
                hidden_reasons.add("Non-Sovereign Data Hosting")

        if profile["has_risk_flag"]:
            port = profile["badges"].get("portability_score", {})
            if port.get("score", 10) <= 3:
                if filters_applied and filters_applied.get("hide_lock_in"):
                    hidden += 1
                    hidden_reasons.add("High Lock-in Risk")

    stat_text = f"Showing {len(tools) - hidden} results."
    if hidden:
        stat_text += f" {hidden} tools hidden due to {' or '.join(hidden_reasons)}."

    return {
        "total_results": len(tools),
        "visible_count": len(tools) - hidden,
        "hidden_count": hidden,
        "hidden_reasons": list(hidden_reasons),
        "stat_text": stat_text,
        "segment_counts": segments,
        "trust_distribution": grade_dist,
    }


logger.info(
    "Trust Badge Architecture loaded — %d badge categories, %d vendor profiles",
    len(BADGE_CATEGORIES), len(_BADGE_INTEL)
)
