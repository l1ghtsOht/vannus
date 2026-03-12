# ────────────────────────────────────────────────────────────────────
# pipeline_constants.py — Immutable Constants for the Praxis v3.0
#   Ingestion & Curation Pipeline
# ────────────────────────────────────────────────────────────────────
"""
Codifies the five core principles of the Praxis AI Tool Ingestion &
Curation Pipeline v3.0 as immutable programmatic constraints.

Principles:
    1. Triple Match Imperative     — consensus across 3 directories
    2. SMB Alignment Gate          — pricing / complexity / vertical fit
    3. Trust Decay as Product      — proactive degradation monitoring
    4. Deterministic Health Proxies — proxy signals for closed-source SaaS
    5. Asynchronous Resilience     — distributed task queues, zero data loss

These constants are referenced by the ingestion engine, intelligence
scoring layer, trust decay monitor, and tiered promotion logic.  They
should NEVER be mutated at runtime.
"""

from __future__ import annotations
from typing import Final

# ======================================================================
# 1. DIRECTORY SOURCES (Triple Match)
# ======================================================================

DIRECTORIES: Final[list[str]] = ["TAAFT", "Toolify", "Futurepedia"]
"""The three external directory sources required for Triple Match."""

TRIPLE_MATCH_MIN: Final[int] = 3
"""Tools must appear in ALL directories for Tier 1 eligibility."""

DUAL_MATCH_MIN: Final[int] = 2
"""Minimum directory presence for Tier 2 eligibility."""

# ======================================================================
# 2. TIER THRESHOLDS
# ======================================================================

# --- Tier 1: Sovereign (Gold) ---
TIER_1_MIN_SURVIVAL: Final[float] = 70.0
"""Minimum Survival Score for Tier 1 candidacy."""

TIER_1_MIN_SMB: Final[float] = 50.0
"""Minimum SMB Relevance Score for Tier 1 candidacy."""

TIER_1_CONFIDENCE_AUTO: Final[float] = 85.0
"""If the system's confidence interval exceeds this, the Confidence
Dashboard highlights the tool for cursory one-click approval."""

TIER_1_REVIEW_SLA_HOURS: Final[int] = 48
"""Maximum hours for human review of a Tier 1 candidate."""

# --- Tier 2: Durable (Silver) ---
TIER_2_MIN_SURVIVAL: Final[float] = 50.0
"""Minimum Survival Score for Tier 2 sandbox entry."""

TIER_2_PROMOTION_SURVIVAL: Final[float] = 70.0
"""The Survival Score a Tier 2 tool must organically reach to be
auto-promoted to the Tier 1 human review queue."""

# --- Tier 3: Vertical Specialist (Bronze) ---
TIER_3_MIN_VERTICAL_FIT: Final[float] = 60.0
"""Minimum Vertical Fit Score for Tier 3 entry (bypasses directory match)."""

# ======================================================================
# 3. SURVIVAL SCORE WEIGHTS
# ======================================================================

WEIGHTS: Final[dict[str, float]] = {
    "m_health":   0.30,   # Maintenance Health
    "smb_rel":    0.20,   # SMB Relevance
    "r_trend":    0.20,   # Review Sentiment Trend
    "s_signal":   0.15,   # Social Signal
    "u_recency":  0.10,   # Update Recency
    "f_red":      0.05,   # No Major Red Flags (binary)
}
"""Survival Score formula: weighted convex combination on a 100-point scale."""

# Maintenance Health sub-weights
M_HEALTH_CHANGELOG_W: Final[float] = 0.40
M_HEALTH_SLA_W: Final[float] = 0.40
M_HEALTH_HIRING_W: Final[float] = 0.20

# ======================================================================
# 4. SMB RELEVANCE GATE
# ======================================================================

SMB_VERTICAL_MATCH_MAX: Final[int] = 40
"""Maximum points from vertical NLP entity extraction."""

SMB_PRICING_ACCESS_MAX: Final[int] = 30
"""Maximum points from pricing accessibility analysis."""

SMB_OPERATIONAL_COMPLEXITY_MAX: Final[int] = 30
"""Maximum points from operational complexity (inverted scale)."""

SMB_PRICING_CEILING: Final[float] = 500.0
"""Monthly pricing ceiling ($) for high SMB accessibility score."""

SMB_PER_SEAT_PENALTY_THRESHOLD: Final[float] = 50.0
"""Per-seat cost ($) above which the tool is heavily penalised."""

# ======================================================================
# 5. TRUST DECAY MONITORING
# ======================================================================

TRUST_DECAY_INTERVAL_HOURS: Final[int] = 72
"""Frequency (hours) of Trust Decay surveillance sweeps."""

TRUST_DECAY_MILD_SENTIMENT_DROP: Final[float] = 0.15
"""A 15% sentiment drop over 30 days triggers Mild Decay (Yellow)."""

TRUST_DECAY_SEVERE_OUTAGE_HOURS: Final[int] = 48
"""An API outage exceeding 48 hours triggers Severe Decay (Red)."""

TRUST_DECAY_PRICE_HIKE_PCT: Final[float] = 0.20
"""A 20%+ price increase without a major release triggers an alert."""

# Keyword sets for NLP detection of support deterioration
TRUST_DECAY_SEVERE_KEYWORDS: Final[frozenset[str]] = frozenset({
    "data breach", "data leak", "hacked", "security incident",
    "service shutdown", "shutting down", "acquired by",
    "double billed", "unauthorized charge",
    "data lost", "data loss", "account locked",
})

TRUST_DECAY_MILD_KEYWORDS: Final[frozenset[str]] = frozenset({
    "support unresponsive", "no response", "ignored for weeks",
    "slow support", "downtime", "outage", "buggy",
    "pricing increased", "removed free tier",
})

# ======================================================================
# 6. BADGES & UI LABELS
# ======================================================================

BADGE_TIERS: Final[dict[str, dict]] = {
    "tier_1": {
        "label": "Gold / Sovereign",
        "tagline": "Battle-Tested & High Confidence",
        "icon": "shield-check",
        "colour": "#D4AF37",
    },
    "tier_2": {
        "label": "Silver / Durable",
        "tagline": "Emerging but Promising",
        "icon": "trending-up",
        "colour": "#C0C0C0",
    },
    "tier_3": {
        "label": "Bronze / Vertical Specialist",
        "tagline": "High Confidence in [Industry]",
        "icon": "target",
        "colour": "#CD7F32",
    },
    "caution": {
        "label": "Yellow / Caution",
        "tagline": "Recent Trust Erosion Detected",
        "icon": "alert-triangle",
        "colour": "#FFD700",
    },
    "under_review": {
        "label": "Red / Under Review",
        "tagline": "Not Recommended",
        "icon": "octagon",
        "colour": "#DC143C",
    },
}

# ======================================================================
# 7. LLM EXTRACTION CONFIDENCE
# ======================================================================

LLM_EXTRACTION_AUTO_COMMIT: Final[float] = 0.85
"""Log-probability confidence threshold above which LLM-extracted
relationships are auto-committed to the knowledge graph."""

LLM_EXTRACTION_HITL: Final[float] = 0.50
"""Below this threshold, extractions are discarded rather than queued."""

# ======================================================================
# 8. FEEDBACK LOOP
# ======================================================================

FEEDBACK_CHECKIN_DAYS: Final[list[int]] = [30, 90]
"""Structured check-in cadence (days after recommendation)."""

FEEDBACK_CALIBRATION_FAILURE_RATE: Final[float] = 0.80
"""If ≥80% of users report failure on a highly-scored tool, the
learning module auto-penalises the inflating variables."""

FEEDBACK_GROUND_TRUTH_COHORT: Final[int] = 100
"""Size of the initial high-touch consultant cohort for ML ground truth."""

# ======================================================================
# 9. OPERATIONAL
# ======================================================================

WAYBACK_CDX_WINDOW_DAYS: Final[int] = 90
"""Default window for Wayback Machine CDX diff analysis."""

SOCIAL_SIGNAL_SMB_MULTIPLIER: Final[float] = 3.0
"""Weight multiplier for mentions on Alignable / trade forums vs generic social."""

UPDATE_RECENCY_WINDOW_DAYS: Final[int] = 180
"""Feature additions or pricing changes within this window earn full points."""

SCRAPER_FALLBACK_ENABLED: Final[bool] = True
"""When a primary Apify actor fails, degrade to Playwright headless scraping."""

# ======================================================================
# 10. SUCCESS METRICS TARGETS
# ======================================================================

TARGET_TRUST_DECAY_PRECISION: Final[float] = 0.80
"""≥80% proactive detection before user reports."""

TARGET_INGESTION_LATENCY_HOURS: Final[int] = 24
"""Triple Match → Tier 1 review queue in <24 hours."""

TARGET_SAYDO_VARIANCE: Final[float] = 0.15
"""Median Say/Do ratio variance <15%."""

TARGET_HITL_THROUGHPUT_PER_HOUR: Final[int] = 30
"""Solo-founder human review throughput target."""
