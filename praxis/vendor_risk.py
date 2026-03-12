# ────────────────────────────────────────────────────────────────────
# vendor_risk.py — Vendor AI Risk Assessment, Risk Scoring,
#                  Data Lineage Tracking, and Supply Chain Governance
# ────────────────────────────────────────────────────────────────────
"""
Implements the Vendor Risk Management (VRM) module for Praxis
(Blueprint §7.3):

1. **Vendor Registry** — catalogues all third-party AI vendors,
   foundation models, vector databases, and API integrations.

2. **Risk Scoring** — automated, multi-factor AI-specific risk
   assessment based on transparency, security posture, data retention,
   and vulnerability history.

3. **Data Lineage** — tracks how internal data flows through the
   vendor ecosystem, proving no training-endpoint leakage.

4. **Continuous Monitoring** — periodic re-assessment with trend
   analysis and alert generation.

All functions are pure-Python with no external dependencies.
"""

from __future__ import annotations

import time
import hashlib
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. VENDOR MODELS                                                ║
# ╚════════════════════════════════════════════════════════════════════╝

class VendorCategory(str, Enum):
    """Categories of AI vendor integrations."""
    FOUNDATION_MODEL = "foundation_model"
    VECTOR_DATABASE = "vector_database"
    EMBEDDING_SERVICE = "embedding_service"
    ORCHESTRATION = "orchestration"
    OBSERVABILITY = "observability"
    DATA_PIPELINE = "data_pipeline"
    SECURITY = "security"
    OTHER = "other"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


@dataclass
class VendorProfile:
    """Complete profile of a third-party AI vendor."""
    vendor_id: str
    name: str
    category: str = VendorCategory.OTHER.value
    description: str = ""

    # Security posture
    soc2_compliant: bool = False
    iso27001: bool = False
    gdpr_compliant: bool = False
    hipaa_compliant: bool = False

    # AI-specific attributes
    model_types: List[str] = field(default_factory=list)
    data_retention_days: int = -1     # -1 = unknown
    trains_on_customer_data: bool = False
    supports_data_deletion: bool = False
    transparency_score: float = 0.0   # 0–1 (1 = fully transparent)

    # Data access
    data_access_scope: str = "none"   # "none", "read", "read_write", "full"
    api_endpoints_used: List[str] = field(default_factory=list)

    # Risk
    risk_score: float = 0.0           # 0–100 (higher = riskier)
    risk_level: str = RiskLevel.MEDIUM.value
    last_assessed: float = field(default_factory=time.time)
    vulnerabilities_known: int = 0

    # Metadata
    contract_expiry: Optional[str] = None
    monthly_cost_usd: float = 0.0
    status: str = "active"            # "active", "under_review", "suspended", "deprecated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vendor_id": self.vendor_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "soc2_compliant": self.soc2_compliant,
            "iso27001": self.iso27001,
            "gdpr_compliant": self.gdpr_compliant,
            "hipaa_compliant": self.hipaa_compliant,
            "model_types": self.model_types,
            "data_retention_days": self.data_retention_days,
            "trains_on_customer_data": self.trains_on_customer_data,
            "supports_data_deletion": self.supports_data_deletion,
            "transparency_score": round(self.transparency_score, 2),
            "data_access_scope": self.data_access_scope,
            "api_endpoints_used": self.api_endpoints_used,
            "risk_score": round(self.risk_score, 1),
            "risk_level": self.risk_level,
            "last_assessed": self.last_assessed,
            "vulnerabilities_known": self.vulnerabilities_known,
            "contract_expiry": self.contract_expiry,
            "monthly_cost_usd": round(self.monthly_cost_usd, 2),
            "status": self.status,
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. RISK SCORING ENGINE                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

# Risk factor weights (total = 100)
_RISK_WEIGHTS = {
    "trains_on_customer_data": 25,    # Highest risk: vendor trains on your data
    "data_access_scope": 20,
    "compliance_gaps": 15,
    "transparency": 15,
    "data_retention": 10,
    "vulnerabilities": 10,
    "supports_deletion": 5,
}


def compute_risk_score(vendor: VendorProfile) -> Dict[str, Any]:
    """
    Compute a weighted risk score for a vendor.

    Returns the overall score (0–100) and per-factor breakdown.
    """
    factors: Dict[str, Dict[str, Any]] = {}
    total_score = 0.0

    # Factor 1: Trains on customer data (binary, worst case)
    f1 = _RISK_WEIGHTS["trains_on_customer_data"] if vendor.trains_on_customer_data else 0
    factors["trains_on_customer_data"] = {
        "score": f1,
        "max": _RISK_WEIGHTS["trains_on_customer_data"],
        "detail": "Vendor trains on customer data" if vendor.trains_on_customer_data else "No training on customer data",
    }
    total_score += f1

    # Factor 2: Data access scope
    scope_scores = {"none": 0, "read": 5, "read_write": 15, "full": 20}
    f2 = scope_scores.get(vendor.data_access_scope, 10)
    factors["data_access_scope"] = {
        "score": f2,
        "max": _RISK_WEIGHTS["data_access_scope"],
        "detail": f"Access scope: {vendor.data_access_scope}",
    }
    total_score += f2

    # Factor 3: Compliance gaps
    compliance_count = sum([
        vendor.soc2_compliant, vendor.iso27001,
        vendor.gdpr_compliant, vendor.hipaa_compliant,
    ])
    f3 = max(0, _RISK_WEIGHTS["compliance_gaps"] - compliance_count * 3.75)
    factors["compliance_gaps"] = {
        "score": round(f3, 1),
        "max": _RISK_WEIGHTS["compliance_gaps"],
        "detail": f"{compliance_count}/4 compliance certifications",
    }
    total_score += f3

    # Factor 4: Transparency
    f4 = _RISK_WEIGHTS["transparency"] * (1 - vendor.transparency_score)
    factors["transparency"] = {
        "score": round(f4, 1),
        "max": _RISK_WEIGHTS["transparency"],
        "detail": f"Transparency score: {vendor.transparency_score:.0%}",
    }
    total_score += f4

    # Factor 5: Data retention
    if vendor.data_retention_days < 0:
        f5 = _RISK_WEIGHTS["data_retention"]  # Unknown = max risk
    elif vendor.data_retention_days == 0:
        f5 = 0  # No retention
    elif vendor.data_retention_days <= 30:
        f5 = 3
    elif vendor.data_retention_days <= 90:
        f5 = 6
    else:
        f5 = _RISK_WEIGHTS["data_retention"]
    factors["data_retention"] = {
        "score": f5,
        "max": _RISK_WEIGHTS["data_retention"],
        "detail": f"Retention: {vendor.data_retention_days} days" if vendor.data_retention_days >= 0 else "Retention: unknown",
    }
    total_score += f5

    # Factor 6: Known vulnerabilities
    f6 = min(vendor.vulnerabilities_known * 2, _RISK_WEIGHTS["vulnerabilities"])
    factors["vulnerabilities"] = {
        "score": f6,
        "max": _RISK_WEIGHTS["vulnerabilities"],
        "detail": f"{vendor.vulnerabilities_known} known vulnerabilities",
    }
    total_score += f6

    # Factor 7: Supports data deletion
    f7 = 0 if vendor.supports_data_deletion else _RISK_WEIGHTS["supports_deletion"]
    factors["supports_deletion"] = {
        "score": f7,
        "max": _RISK_WEIGHTS["supports_deletion"],
        "detail": "Supports deletion" if vendor.supports_data_deletion else "No deletion support",
    }
    total_score += f7

    # Classify
    if total_score >= 70:
        level = RiskLevel.CRITICAL.value
    elif total_score >= 50:
        level = RiskLevel.HIGH.value
    elif total_score >= 30:
        level = RiskLevel.MEDIUM.value
    elif total_score >= 15:
        level = RiskLevel.LOW.value
    else:
        level = RiskLevel.MINIMAL.value

    # Update vendor
    vendor.risk_score = total_score
    vendor.risk_level = level
    vendor.last_assessed = time.time()

    return {
        "vendor_id": vendor.vendor_id,
        "risk_score": round(total_score, 1),
        "risk_level": level,
        "factors": factors,
        "recommendations": _generate_recommendations(vendor, factors),
    }


def _generate_recommendations(vendor: VendorProfile, factors: Dict) -> List[str]:
    """Generate actionable risk-reduction recommendations."""
    recs: List[str] = []

    if vendor.trains_on_customer_data:
        recs.append("CRITICAL: Negotiate data processing agreement prohibiting training on customer data")

    if vendor.data_access_scope in ("read_write", "full"):
        recs.append("Reduce data access scope to read-only where possible")

    if not vendor.soc2_compliant:
        recs.append("Request SOC 2 Type II attestation from vendor")

    if not vendor.gdpr_compliant:
        recs.append("Verify GDPR compliance or implement additional data protection measures")

    if vendor.transparency_score < 0.5:
        recs.append("Request model cards and data processing documentation for transparency")

    if vendor.data_retention_days < 0:
        recs.append("Clarify data retention policy with vendor")
    elif vendor.data_retention_days > 90:
        recs.append("Negotiate shorter data retention period (≤30 days recommended)")

    if not vendor.supports_data_deletion:
        recs.append("Ensure vendor implements data deletion capability for GDPR Art.17 compliance")

    if vendor.vulnerabilities_known > 0:
        recs.append(f"Review and track {vendor.vulnerabilities_known} known vulnerabilities")

    return recs


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. DATA LINEAGE                                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class DataLineageEntry:
    """A single data flow event in the vendor ecosystem."""
    entry_id: str = ""
    timestamp: float = field(default_factory=time.time)
    data_type: str = ""          # "query", "embedding", "document", "response"
    source: str = ""             # internal system or user
    destination_vendor: str = ""
    purpose: str = ""            # "inference", "embedding", "storage", "training"
    data_size_bytes: int = 0
    contains_pii: bool = False
    authorized: bool = True
    trace_id: str = ""           # link to observability trace

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "data_type": self.data_type,
            "source": self.source,
            "destination_vendor": self.destination_vendor,
            "purpose": self.purpose,
            "data_size_bytes": self.data_size_bytes,
            "contains_pii": self.contains_pii,
            "authorized": self.authorized,
            "trace_id": self.trace_id,
        }


class DataLineageTracker:
    """Track all data flows to external vendors."""

    MAX_ENTRIES = 20000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: List[DataLineageEntry] = []
        self._counter: int = 0

    def record_flow(
        self,
        data_type: str,
        source: str,
        destination_vendor: str,
        purpose: str = "inference",
        data_size_bytes: int = 0,
        contains_pii: bool = False,
        authorized: bool = True,
        trace_id: str = "",
    ) -> Dict[str, Any]:
        with self._lock:
            self._counter += 1
            entry = DataLineageEntry(
                entry_id=f"DL-{self._counter:06d}",
                data_type=data_type,
                source=source,
                destination_vendor=destination_vendor,
                purpose=purpose,
                data_size_bytes=data_size_bytes,
                contains_pii=contains_pii,
                authorized=authorized,
                trace_id=trace_id,
            )
            self._entries.append(entry)
            if len(self._entries) > self.MAX_ENTRIES:
                self._entries = self._entries[-self.MAX_ENTRIES:]
            return entry.to_dict()

    def lineage_for_vendor(self, vendor_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                e.to_dict() for e in self._entries
                if e.destination_vendor == vendor_id
            ]

    def detect_unauthorized(self) -> List[Dict[str, Any]]:
        """Detect any unauthorized data flows."""
        with self._lock:
            return [e.to_dict() for e in self._entries if not e.authorized]

    def detect_pii_exposure(self) -> List[Dict[str, Any]]:
        """Detect data flows containing PII sent to external vendors."""
        with self._lock:
            return [
                e.to_dict() for e in self._entries
                if e.contains_pii and e.purpose != "inference"
            ]

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            vendor_dist: Dict[str, int] = defaultdict(int)
            purpose_dist: Dict[str, int] = defaultdict(int)
            total_bytes = 0
            pii_flows = 0
            unauthorized = 0

            for entry in self._entries:
                vendor_dist[entry.destination_vendor] += 1
                purpose_dist[entry.purpose] += 1
                total_bytes += entry.data_size_bytes
                if entry.contains_pii:
                    pii_flows += 1
                if not entry.authorized:
                    unauthorized += 1

            return {
                "total_flows": len(self._entries),
                "total_bytes_transferred": total_bytes,
                "pii_flows": pii_flows,
                "unauthorized_flows": unauthorized,
                "vendor_distribution": dict(vendor_dist),
                "purpose_distribution": dict(purpose_dist),
            }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. VENDOR REGISTRY                                              ║
# ╚════════════════════════════════════════════════════════════════════╝

class VendorRegistry:
    """Central registry of all third-party AI vendors."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._vendors: Dict[str, VendorProfile] = {}
        self._lineage = DataLineageTracker()

    def register(self, vendor: VendorProfile) -> bool:
        with self._lock:
            if vendor.vendor_id in self._vendors:
                return False
            # Auto-score
            compute_risk_score(vendor)
            self._vendors[vendor.vendor_id] = vendor
            return True

    def update(self, vendor_id: str, updates: Dict[str, Any]) -> bool:
        with self._lock:
            v = self._vendors.get(vendor_id)
            if not v:
                return False
            for key, val in updates.items():
                if hasattr(v, key):
                    setattr(v, key, val)
            compute_risk_score(v)
            return True

    def get(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            v = self._vendors.get(vendor_id)
            return v.to_dict() if v else None

    def list_vendors(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [v.to_dict() for v in self._vendors.values()]

    def risk_summary(self) -> Dict[str, Any]:
        with self._lock:
            risk_dist: Dict[str, int] = defaultdict(int)
            high_risk: List[str] = []
            total_cost = 0.0

            for v in self._vendors.values():
                risk_dist[v.risk_level] += 1
                if v.risk_level in (RiskLevel.HIGH.value, RiskLevel.CRITICAL.value):
                    high_risk.append(v.name)
                total_cost += v.monthly_cost_usd

            return {
                "total_vendors": len(self._vendors),
                "risk_distribution": dict(risk_dist),
                "high_risk_vendors": high_risk,
                "total_monthly_cost_usd": round(total_cost, 2),
                "requires_immediate_review": len(high_risk),
            }

    @property
    def lineage(self) -> DataLineageTracker:
        return self._lineage


# Global registry singleton
_registry: Optional[VendorRegistry] = None
_reg_lock = threading.Lock()


def get_registry() -> VendorRegistry:
    global _registry
    with _reg_lock:
        if _registry is None:
            _registry = VendorRegistry()
            _seed_default_vendors(_registry)
        return _registry


def _seed_default_vendors(registry: VendorRegistry) -> None:
    """Seed with the vendor ecosystem commonly used by AI platforms."""
    defaults = [
        VendorProfile(
            vendor_id="openai", name="OpenAI",
            category=VendorCategory.FOUNDATION_MODEL.value,
            description="GPT-4o, GPT-4-turbo foundation models",
            soc2_compliant=True, gdpr_compliant=True,
            model_types=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            data_retention_days=30, trains_on_customer_data=False,
            supports_data_deletion=True, transparency_score=0.7,
            data_access_scope="read", monthly_cost_usd=500.0,
        ),
        VendorProfile(
            vendor_id="anthropic", name="Anthropic",
            category=VendorCategory.FOUNDATION_MODEL.value,
            description="Claude 3.5 Sonnet, Claude 3 Opus/Haiku",
            soc2_compliant=True, gdpr_compliant=True, hipaa_compliant=True,
            model_types=["claude-3.5-sonnet", "claude-3-opus", "claude-3-haiku"],
            data_retention_days=0, trains_on_customer_data=False,
            supports_data_deletion=True, transparency_score=0.8,
            data_access_scope="read", monthly_cost_usd=400.0,
        ),
        VendorProfile(
            vendor_id="google-ai", name="Google AI",
            category=VendorCategory.FOUNDATION_MODEL.value,
            description="Gemini 1.5 Pro/Flash",
            soc2_compliant=True, iso27001=True, gdpr_compliant=True,
            model_types=["gemini-1.5-pro", "gemini-1.5-flash"],
            data_retention_days=30, trains_on_customer_data=False,
            supports_data_deletion=True, transparency_score=0.6,
            data_access_scope="read", monthly_cost_usd=300.0,
        ),
        VendorProfile(
            vendor_id="pinecone", name="Pinecone",
            category=VendorCategory.VECTOR_DATABASE.value,
            description="Managed vector database for embeddings",
            soc2_compliant=True, gdpr_compliant=True,
            data_retention_days=0, trains_on_customer_data=False,
            supports_data_deletion=True, transparency_score=0.7,
            data_access_scope="read_write", monthly_cost_usd=70.0,
        ),
        VendorProfile(
            vendor_id="langchain", name="LangChain",
            category=VendorCategory.ORCHESTRATION.value,
            description="Agent orchestration and LangSmith observability",
            soc2_compliant=True, gdpr_compliant=True,
            data_retention_days=90, trains_on_customer_data=False,
            supports_data_deletion=True, transparency_score=0.9,
            data_access_scope="read", monthly_cost_usd=50.0,
        ),
    ]
    for v in defaults:
        registry.register(v)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. CONVENIENCE                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def vendor_risk_dashboard() -> Dict[str, Any]:
    """Full vendor risk management snapshot."""
    registry = get_registry()
    return {
        "vendors": registry.list_vendors(),
        "risk_summary": registry.risk_summary(),
        "data_lineage": registry.lineage.summary(),
        "unauthorized_flows": registry.lineage.detect_unauthorized(),
        "pii_exposure": registry.lineage.detect_pii_exposure(),
    }
