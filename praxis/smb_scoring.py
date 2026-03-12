# ────────────────────────────────────────────────────────────────────
# smb_scoring.py — SMB Relevance Gate & Vertical Fit Engine
# ────────────────────────────────────────────────────────────────────
"""
Structural mechanism that prevents Praxis from degrading into a generic
enterprise software directory.

Small and medium businesses operate under fundamentally different
constraints than enterprise corporations:
    · No dedicated IT departments
    · Constrained cash flows
    · Require immediate time-to-value

Scoring Dimensions (100-point scale):
    1. Vertical Match         (0-40)  — NLP entity extraction against marketing copy
    2. Pricing Accessibility  (0-30)  — pricing tier analysis
    3. Operational Complexity  (0-30)  — inverted complexity scale

Calibration:
    The learning.py module calibrates these weights using a supervised
    logistic regression protocol against a 100-tool ground-truth dataset
    (50 enterprise giants, 50 SMB solutions).

Usage:
    from praxis.smb_scoring import score_smb_relevance, score_vertical_fit
    smb = score_smb_relevance(tool)
    vfit = score_vertical_fit(tool, vertical="construction")
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("praxis.smb_scoring")

try:
    from .pipeline_constants import (
        SMB_VERTICAL_MATCH_MAX,
        SMB_PRICING_ACCESS_MAX,
        SMB_OPERATIONAL_COMPLEXITY_MAX,
        SMB_PRICING_CEILING,
        SMB_PER_SEAT_PENALTY_THRESHOLD,
        TIER_1_MIN_SMB,
        TIER_3_MIN_VERTICAL_FIT,
    )
except ImportError:
    from pipeline_constants import (  # type: ignore[no-redef]
        SMB_VERTICAL_MATCH_MAX,
        SMB_PRICING_ACCESS_MAX,
        SMB_OPERATIONAL_COMPLEXITY_MAX,
        SMB_PRICING_CEILING,
        SMB_PER_SEAT_PENALTY_THRESHOLD,
        TIER_1_MIN_SMB,
        TIER_3_MIN_VERTICAL_FIT,
    )


# =====================================================================
# SMB VERTICALS & KEYWORD LIBRARIES
# =====================================================================

SMB_VERTICALS: dict[str, list[str]] = {
    "construction": [
        "construction", "general contractor", "builder", "remodeling",
        "renovation", "subcontractor", "jobsite", "blueprint",
    ],
    "hvac": [
        "hvac", "heating", "cooling", "air conditioning", "furnace",
        "ductwork", "refrigeration",
    ],
    "plumbing": [
        "plumbing", "plumber", "drain", "pipe", "water heater",
        "sewer", "backflow",
    ],
    "electrical": [
        "electrical", "electrician", "wiring", "panel", "circuit",
        "lighting installation",
    ],
    "landscaping": [
        "landscaping", "lawn care", "mowing", "hardscape", "irrigation",
        "tree service",
    ],
    "healthcare": [
        "healthcare", "clinic", "medical practice", "patient intake",
        "telemedicine", "ehr", "emr", "hipaa",
    ],
    "dental": [
        "dental", "dentist", "orthodontics", "dental practice",
    ],
    "veterinary": [
        "veterinary", "vet clinic", "animal hospital", "pet care",
    ],
    "retail": [
        "retail", "pos", "point of sale", "inventory", "ecommerce",
        "shopify", "storefront",
    ],
    "restaurant": [
        "restaurant", "food service", "catering", "menu", "food truck",
        "bar", "cafe",
    ],
    "salon_spa": [
        "salon", "spa", "barbershop", "beauty", "nail", "hair",
        "esthetics", "booking",
    ],
    "cleaning": [
        "cleaning service", "janitorial", "maid service", "pressure washing",
        "carpet cleaning",
    ],
    "roofing": [
        "roofing", "roofer", "shingle", "roof repair", "gutter",
    ],
    "painting": [
        "painting", "painter", "interior painting", "exterior painting",
    ],
    "auto_repair": [
        "auto repair", "mechanic", "garage", "auto body", "oil change",
        "tire", "automotive",
    ],
    "real_estate": [
        "real estate", "realtor", "property management", "rental",
        "lease", "mls", "listing",
    ],
    "fitness": [
        "fitness", "gym", "personal training", "yoga studio",
        "crossfit", "membership",
    ],
    "daycare": [
        "daycare", "childcare", "preschool", "after school",
        "child care",
    ],
    "accounting": [
        "accounting", "bookkeeping", "tax preparation", "payroll",
        "invoicing", "cpa",
    ],
    "legal": [
        "legal", "law firm", "attorney", "case management",
        "legal document", "paralegal",
    ],
    "insurance": [
        "insurance", "insurance agency", "claims", "underwriting",
        "policy management",
    ],
    "field_service": [
        "field service", "dispatch", "work orders", "service calls",
        "field technician", "mobile workforce",
    ],
}

SMB_INDICATOR_KEYWORDS: dict[str, float] = {
    "small business": 10.0,
    "smb": 10.0,
    "solopreneur": 8.0,
    "freelance": 7.0,
    "freelancer": 7.0,
    "contractor": 8.0,
    "field service": 9.0,
    "local business": 8.0,
    "trades": 7.0,
    "owner-operator": 10.0,
    "family business": 8.0,
    "startup": 5.0,
    "side hustle": 6.0,
    "independent": 5.0,
    "micro business": 9.0,
    "1-10 employees": 10.0,
    "10-50 employees": 8.0,
}

ENTERPRISE_INDICATOR_KEYWORDS: dict[str, float] = {
    "enterprise": -8.0,
    "fortune 500": -10.0,
    "large organization": -8.0,
    "dedicated it team": -10.0,
    "it department": -8.0,
    "procurement team": -7.0,
    "sso required": -5.0,
    "custom implementation": -10.0,
    "professional services required": -9.0,
    "minimum seats": -6.0,
    "annual contract": -4.0,
    "10000+ employees": -10.0,
}

COMPLEXITY_PENALTIES: dict[str, float] = {
    "docker": 8.0,
    "kubernetes": 10.0,
    "k8s": 10.0,
    "helm chart": 8.0,
    "terraform": 7.0,
    "self-hosted": 6.0,
    "on-premise": 6.0,
    "custom implementation": 10.0,
    "dedicated it": 8.0,
    "api only": 5.0,
    "sdk required": 4.0,
    "cli only": 5.0,
    "linux server": 6.0,
    "devops": 7.0,
    "yaml configuration": 4.0,
}

COMPLEXITY_BONUSES: dict[str, float] = {
    "no-code": 10.0,
    "one-click": 8.0,
    "drag and drop": 6.0,
    "instant setup": 7.0,
    "free trial": 5.0,
    "mobile app": 4.0,
    "browser extension": 4.0,
    "zapier": 8.0,
    "zapier integration": 8.0,
    "make integration": 6.0,
    "google workspace": 5.0,
    "quickbooks": 7.0,
    "templates": 4.0,
    "setup wizard": 6.0,
    "guided onboarding": 5.0,
}


# =====================================================================
# SCORING FUNCTIONS
# =====================================================================

@dataclass
class SMBScoreBreakdown:
    """Detailed breakdown of SMB Relevance Score."""
    total_score: float = 0.0
    vertical_score: float = 0.0
    pricing_score: float = 0.0
    complexity_score: float = 0.0
    matched_verticals: list[str] = None
    smb_indicators: list[str] = None
    enterprise_indicators: list[str] = None
    complexity_penalties: list[str] = None
    complexity_bonuses: list[str] = None
    passes_gate: bool = False

    def __post_init__(self):
        self.matched_verticals = self.matched_verticals or []
        self.smb_indicators = self.smb_indicators or []
        self.enterprise_indicators = self.enterprise_indicators or []
        self.complexity_penalties = self.complexity_penalties or []
        self.complexity_bonuses = self.complexity_bonuses or []

    def to_dict(self) -> dict:
        return asdict(self)


def _extract_tool_text(tool) -> str:
    """Extract all searchable text from a tool object or dict."""
    if isinstance(tool, dict):
        parts = [
            tool.get("name", ""),
            tool.get("description", ""),
            " ".join(tool.get("categories", [])),
            " ".join(tool.get("tags", [])),
            " ".join(tool.get("keywords", [])),
            " ".join(tool.get("use_cases", [])),
        ]
    else:
        parts = [
            getattr(tool, "name", ""),
            getattr(tool, "description", ""),
            " ".join(getattr(tool, "categories", [])),
            " ".join(getattr(tool, "tags", [])),
            " ".join(getattr(tool, "keywords", [])),
            " ".join(getattr(tool, "use_cases", [])),
        ]
    return " ".join(parts).lower()


def _get_pricing(tool) -> dict:
    """Extract pricing data from a tool object or dict."""
    if isinstance(tool, dict):
        pricing = tool.get("pricing", {})
    else:
        pricing = getattr(tool, "pricing", {})
    return pricing if isinstance(pricing, dict) else {}


def score_vertical_match(tool, text: Optional[str] = None) -> tuple[float, list[str]]:
    """Score vertical match (0-40).
    Returns (score, list_of_matched_verticals)."""
    if text is None:
        text = _extract_tool_text(tool)

    matched: list[str] = []
    for vertical, keywords in SMB_VERTICALS.items():
        for kw in keywords:
            if kw in text:
                if vertical not in matched:
                    matched.append(vertical)
                break

    # Base score from vertical matches
    vertical_score = min(SMB_VERTICAL_MATCH_MAX, len(matched) * 10)

    # SMB indicator bonuses
    smb_bonus = 0.0
    for kw, pts in SMB_INDICATOR_KEYWORDS.items():
        if kw in text:
            smb_bonus += pts
    vertical_score += smb_bonus

    # Enterprise indicator penalties
    for kw, pts in ENTERPRISE_INDICATOR_KEYWORDS.items():
        if kw in text:
            vertical_score += pts  # pts are negative

    return max(0.0, min(SMB_VERTICAL_MATCH_MAX, vertical_score)), matched


def score_pricing_accessibility(tool, text: Optional[str] = None) -> float:
    """Score pricing accessibility (0-30)."""
    pricing = _get_pricing(tool)
    if text is None:
        text = _extract_tool_text(tool)

    has_free = bool(pricing.get("free_tier"))
    starter = pricing.get("starter", 0) or 0
    pro = pricing.get("pro", 0) or 0
    enterprise = pricing.get("enterprise", "")

    # Determine the lowest paid tier price
    try:
        lowest_price = min(float(p) for p in [starter, pro] if float(p) > 0) if (starter or pro) else 0
    except (TypeError, ValueError):
        lowest_price = 0

    # Scoring logic
    if has_free and lowest_price <= SMB_PRICING_CEILING:
        score = SMB_PRICING_ACCESS_MAX  # 30
    elif has_free:
        score = SMB_PRICING_ACCESS_MAX * 0.8
    elif 0 < lowest_price <= 50:
        score = SMB_PRICING_ACCESS_MAX * 0.9
    elif 0 < lowest_price <= 100:
        score = SMB_PRICING_ACCESS_MAX * 0.8
    elif 0 < lowest_price <= SMB_PRICING_CEILING:
        score = SMB_PRICING_ACCESS_MAX * 0.6
    elif lowest_price > SMB_PRICING_CEILING:
        score = SMB_PRICING_ACCESS_MAX * 0.2
    elif "contact" in str(enterprise).lower():
        score = 5.0  # "Contact Sales" heavy penalty
    else:
        score = SMB_PRICING_ACCESS_MAX * 0.7  # unknown pricing, neutral

    # Per-seat penalty
    if "per seat" in text or "per user" in text or "/user" in text:
        try:
            prices = re.findall(r"\$(\d+(?:\.\d{2})?)", text)
            if prices:
                per_seat = min(float(p) for p in prices)
                if per_seat > SMB_PER_SEAT_PENALTY_THRESHOLD:
                    score *= 0.5
        except Exception:
            pass

    return max(0.0, min(SMB_PRICING_ACCESS_MAX, score))


def score_operational_complexity(tool, text: Optional[str] = None) -> tuple[float, list[str], list[str]]:
    """Score operational complexity (0-30, inverted — lower complexity = higher score).
    Returns (score, penalties_triggered, bonuses_triggered)."""
    if text is None:
        text = _extract_tool_text(tool)

    score = SMB_OPERATIONAL_COMPLEXITY_MAX  # Start at max, subtract penalties
    penalties_hit: list[str] = []
    bonuses_hit: list[str] = []

    for term, penalty in COMPLEXITY_PENALTIES.items():
        if term in text:
            score -= penalty
            penalties_hit.append(term)

    for term, bonus in COMPLEXITY_BONUSES.items():
        if term in text:
            score += bonus
            bonuses_hit.append(term)

    return max(0.0, min(SMB_OPERATIONAL_COMPLEXITY_MAX, score)), penalties_hit, bonuses_hit


def score_smb_relevance(tool) -> SMBScoreBreakdown:
    """Calculate the full SMB Relevance Score with detailed breakdown.

    Returns an SMBScoreBreakdown with:
        - total_score (0-100)
        - dimension breakdowns
        - matched signals
        - passes_gate (True if ≥ TIER_1_MIN_SMB)
    """
    text = _extract_tool_text(tool)

    # 1. Vertical Match (0-40)
    vert_score, matched_verticals = score_vertical_match(tool, text)

    # 2. Pricing Accessibility (0-30)
    price_score = score_pricing_accessibility(tool, text)

    # 3. Operational Complexity (0-30)
    complex_score, penalties, bonuses = score_operational_complexity(tool, text)

    total = round(vert_score + price_score + complex_score, 2)
    total = min(100.0, total)

    # Identify SMB and enterprise indicators
    smb_found = [k for k in SMB_INDICATOR_KEYWORDS if k in text]
    ent_found = [k for k in ENTERPRISE_INDICATOR_KEYWORDS if k in text]

    return SMBScoreBreakdown(
        total_score=total,
        vertical_score=round(vert_score, 2),
        pricing_score=round(price_score, 2),
        complexity_score=round(complex_score, 2),
        matched_verticals=matched_verticals,
        smb_indicators=smb_found,
        enterprise_indicators=ent_found,
        complexity_penalties=penalties,
        complexity_bonuses=bonuses,
        passes_gate=total >= TIER_1_MIN_SMB,
    )


def score_vertical_fit(tool, vertical: Optional[str] = None) -> float:
    """Calculate the Vertical Fit Score for Tier 3 eligibility.
    If no vertical is specified, auto-detect the best-matching vertical.

    Returns a score 0-100."""
    text = _extract_tool_text(tool)

    if vertical:
        keywords = SMB_VERTICALS.get(vertical, [])
        if not keywords:
            return 0.0
        hits = sum(1 for kw in keywords if kw in text)
        base = (hits / max(1, len(keywords))) * 80
        # Bonus for SMB indicators
        smb_bonus = sum(
            pts for kw, pts in SMB_INDICATOR_KEYWORDS.items() if kw in text
        )
        return min(100.0, base + smb_bonus)

    # Auto-detect: find the best-matching vertical
    best_score = 0.0
    for vert, keywords in SMB_VERTICALS.items():
        hits = sum(1 for kw in keywords if kw in text)
        score = (hits / max(1, len(keywords))) * 80
        if score > best_score:
            best_score = score

    smb_bonus = sum(
        pts for kw, pts in SMB_INDICATOR_KEYWORDS.items() if kw in text
    )
    return min(100.0, best_score + smb_bonus)


# =====================================================================
# CALIBRATION DATASET (ground truth for logistic regression)
# =====================================================================

CALIBRATION_ENTERPRISE: list[str] = [
    "Salesforce", "Workday", "SAP", "Oracle Cloud", "ServiceNow",
    "Snowflake", "Databricks", "Splunk", "Palo Alto Networks", "CrowdStrike",
    "Okta", "Zscaler", "Dynatrace", "Datadog", "Confluent",
    "HashiCorp", "MongoDB Atlas Enterprise", "Elastic Enterprise",
    "Twilio Enterprise", "Segment Enterprise",
    "Adobe Experience Cloud", "HubSpot Enterprise", "Zendesk Enterprise",
    "Atlassian Enterprise", "Slack Enterprise Grid",
    "Microsoft 365 E5", "Google Workspace Enterprise", "Box Enterprise",
    "Dropbox Business Advanced", "Zoom Enterprise",
    "Asana Enterprise", "Monday.com Enterprise", "Notion Enterprise",
    "Airtable Enterprise", "Figma Organisation",
    "GitHub Enterprise", "GitLab Ultimate", "Jira Cloud Premium",
    "Confluence Cloud Premium", "Bitbucket Cloud Premium",
    "AWS", "Azure", "Google Cloud Platform", "IBM Cloud",
    "VMware", "Red Hat OpenShift", "Kubernetes Enterprise",
    "Terraform Enterprise", "Ansible Tower", "Chef Enterprise",
    "Puppet Enterprise",
]

CALIBRATION_SMB: list[str] = [
    "Jobber", "Housecall Pro", "Jane App", "ServiceTitan",
    "Calendly", "Acuity Scheduling", "Square", "Stripe",
    "QuickBooks Online", "FreshBooks", "Wave Accounting", "Xero",
    "Canva", "Mailchimp", "Constant Contact", "ConvertKit",
    "Shopify", "WooCommerce", "BigCommerce", "Squarespace",
    "Wix", "GoDaddy Website Builder", "WordPress.com",
    "Gusto", "Homebase", "Deputy", "When I Work",
    "Podium", "Birdeye", "Broadly", "NiceJob",
    "Loom", "Zoom (Pro)", "Google Meet", "Microsoft Teams Essentials",
    "Trello", "Asana (Free)", "ClickUp", "Basecamp",
    "Slack (Free)", "Discord", "Google Workspace Starter",
    "LastPass Teams", "1Password Teams", "Dashlane Business",
    "Buffer", "Hootsuite (Pro)", "Later", "Sprout Social",
    "HubSpot Free CRM", "Pipedrive",
]


# =====================================================================
# MODULE INIT
# =====================================================================

logger.info(
    "smb_scoring.py loaded — %d verticals, %d SMB indicators, "
    "gate threshold %.0f/100",
    len(SMB_VERTICALS),
    len(SMB_INDICATOR_KEYWORDS),
    TIER_1_MIN_SMB,
)
