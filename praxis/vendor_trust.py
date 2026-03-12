# --------------- Praxis Vendor Trust Scoring Engine ---------------
"""
v18 · Enterprise-Grade Solidification

Governance & compliance layer that evaluates third-party tool vendors on
a multi-dimensional trust matrix:

    Dimension             Weight    Source
    ───────────────────── ─────── ──────────────────
    SOC 2 Type II         0.25    Vendor attestation
    GDPR DPA              0.15    Legal review
    ISO 27001             0.15    Certificate
    HIPAA BAA             0.10    Legal review
    Update frequency      0.15    Package registry
    Open CVE count        0.10    NVD / OSV
    Community health      0.10    GitHub API

The resulting ``VendorTrustScore`` model (``domain_models.py``) is
attached to every ``ToolRecommendation`` when governance mode is active.

Zero external dependencies.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.vendor_trust")


# -----------------------------------------------------------------------
# Weight Configuration
# -----------------------------------------------------------------------

DEFAULT_WEIGHTS: Dict[str, float] = {
    "soc2":             0.25,
    "gdpr":             0.15,
    "iso27001":         0.15,
    "hipaa":            0.10,
    "update_frequency": 0.15,
    "cve_score":        0.10,
    "community_health": 0.10,
}


# -----------------------------------------------------------------------
# VendorProfile (enrichment data)
# -----------------------------------------------------------------------

@dataclass
class VendorProfile:
    """Raw compliance and health data for a tool vendor."""

    vendor_name: str
    tool_name: str

    # Compliance attestations (True = verified)
    soc2: bool = False
    gdpr: bool = False
    iso27001: bool = False
    hipaa: bool = False

    # Health metrics
    open_cve_count: int = 0
    days_since_last_update: int = 0
    github_stars: int = 0
    github_contributors: int = 0
    has_security_policy: bool = False

    # Override / manual risk flag
    risk_override: Optional[str] = None  # "approved", "blocked", "review_required"


# -----------------------------------------------------------------------
# Scoring Functions
# -----------------------------------------------------------------------

def _compliance_score(attested: bool) -> float:
    """Binary compliance dimension: 1.0 if attested, 0.0 otherwise."""
    return 1.0 if attested else 0.0


def _update_frequency_score(days_since: int) -> float:
    """Map days-since-last-update to [0, 1].

    ≤ 30 days → 1.0
    31–90 days → linear decay
    91–365 → slow decay
    > 365 → 0.1
    """
    if days_since <= 30:
        return 1.0
    if days_since <= 90:
        return 1.0 - (days_since - 30) / 120  # ~0.5 at 90 days
    if days_since <= 365:
        return max(0.1, 0.5 - (days_since - 90) / 550)
    return 0.1


def _cve_score(count: int) -> float:
    """Map open CVE count to [0, 1].

    0 → 1.0, 1 → 0.8, 3 → 0.5, 5+ → exponential decay
    """
    if count == 0:
        return 1.0
    return max(0.0, 1.0 - 0.2 * count)


def _community_health_score(stars: int, contributors: int, has_policy: bool) -> float:
    """Composite community health signal."""
    score = 0.0

    # Stars (log scale, capped at 10,000)
    if stars > 0:
        score += min(0.4, math.log10(stars) / 10)

    # Contributors
    if contributors >= 50:
        score += 0.3
    elif contributors >= 10:
        score += 0.2
    elif contributors >= 3:
        score += 0.1

    # Security policy
    if has_policy:
        score += 0.3

    return min(1.0, score)


# -----------------------------------------------------------------------
# Trust Score Engine
# -----------------------------------------------------------------------

class VendorTrustEngine:
    """Compute and cache vendor trust scores."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = weights or DEFAULT_WEIGHTS
        self._cache: Dict[str, Dict] = {}  # vendor → {score_dict, timestamp}
        self._cache_ttl = 3600  # 1 hour

    def score(self, profile: VendorProfile) -> Dict[str, Any]:
        """Compute the full trust breakdown for a vendor."""

        # -- Check override --
        if profile.risk_override == "blocked":
            return self._blocked_result(profile)

        # -- Dimension scores --
        dims = {
            "soc2":             _compliance_score(profile.soc2),
            "gdpr":             _compliance_score(profile.gdpr),
            "iso27001":         _compliance_score(profile.iso27001),
            "hipaa":            _compliance_score(profile.hipaa),
            "update_frequency": _update_frequency_score(profile.days_since_last_update),
            "cve_score":        _cve_score(profile.open_cve_count),
            "community_health": _community_health_score(
                profile.github_stars, profile.github_contributors,
                profile.has_security_policy,
            ),
        }

        # -- Weighted composite --
        composite = sum(dims[k] * self._weights.get(k, 0) for k in dims)
        composite = round(min(1.0, max(0.0, composite)), 3)

        # -- Pass/fail gate --
        passed = composite >= 0.4 and profile.open_cve_count <= 5
        if profile.risk_override == "approved":
            passed = True

        # -- Risk tier --
        tier = self._risk_tier(composite)

        result = {
            "vendor_name":     profile.vendor_name,
            "tool_name":       profile.tool_name,
            "composite_score": composite,
            "passed":          passed,
            "risk_tier":       tier,
            "dimensions":      dims,
            "open_cve_count":  profile.open_cve_count,
            "risk_override":   profile.risk_override,
        }

        # Cache
        self._cache[profile.tool_name] = {"result": result, "ts": time.monotonic()}
        return result

    def score_batch(self, profiles: List[VendorProfile]) -> List[Dict[str, Any]]:
        """Score multiple vendors."""
        return [self.score(p) for p in profiles]

    def get_cached(self, tool_name: str) -> Optional[Dict[str, Any]]:
        entry = self._cache.get(tool_name)
        if entry and (time.monotonic() - entry["ts"]) < self._cache_ttl:
            return entry["result"]
        return None

    # -- Helpers --

    @staticmethod
    def _risk_tier(score: float) -> str:
        if score >= 0.8:
            return "low"
        if score >= 0.5:
            return "medium"
        if score >= 0.3:
            return "high"
        return "critical"

    @staticmethod
    def _blocked_result(profile: VendorProfile) -> Dict[str, Any]:
        return {
            "vendor_name":     profile.vendor_name,
            "tool_name":       profile.tool_name,
            "composite_score": 0.0,
            "passed":          False,
            "risk_tier":       "blocked",
            "dimensions":      {},
            "open_cve_count":  profile.open_cve_count,
            "risk_override":   "blocked",
        }


# -----------------------------------------------------------------------
# Convenience: annotate tool recommendations with trust scores
# -----------------------------------------------------------------------

def annotate_recommendations(
    recommendations: List[Dict[str, Any]],
    *,
    engine: Optional[VendorTrustEngine] = None,
    profiles: Optional[Dict[str, VendorProfile]] = None,
) -> List[Dict[str, Any]]:
    """Attach ``vendor_trust`` sub-dict to each recommendation.

    ``profiles`` maps tool_name → VendorProfile.  Tools without a profile
    receive a default "unverified" trust entry.
    """
    eng = engine or VendorTrustEngine()
    profs = profiles or {}

    for rec in recommendations:
        name = rec.get("name") or rec.get("tool_name") or ""
        if name in profs:
            rec["vendor_trust"] = eng.score(profs[name])
        else:
            rec["vendor_trust"] = {
                "vendor_name":     "unknown",
                "tool_name":       name,
                "composite_score": 0.0,
                "passed":          False,
                "risk_tier":       "unverified",
                "dimensions":      {},
                "open_cve_count":  0,
                "risk_override":   None,
            }
    return recommendations
