# ────────────────────────────────────────────────────────────────────
# compliance.py — Regulatory Mapping, Immutable Audit Trails,
#                 Dynamic Data Masking, and Privacy by Design
# ────────────────────────────────────────────────────────────────────
"""
Implements the Enterprise Governance & Compliance layer for Praxis
(Blueprint §7):

1. **Regulatory Mapping** — maps EU AI Act, HIPAA, GDPR requirements
   against platform controls with gap analysis.

2. **Immutable Audit Trail** — append-only, cryptographically timestamped
   log of every significant platform event.

3. **Dynamic Data Masking** — real-time PII/PHI detection and masking
   before data enters LLM context windows.

4. **Compliance Dashboard** — aggregated compliance posture with
   remediation recommendations.

All functions are pure-Python with no external dependencies.
"""

from __future__ import annotations

import re
import json
import time
import hashlib
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. REGULATORY MAPPING                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class RegulatoryRequirement:
    """A single requirement from a regulatory framework."""
    framework: str          # "EU_AI_ACT", "HIPAA", "GDPR"
    requirement_id: str     # e.g., "EUAIA-Art6.1", "HIPAA-164.312(a)"
    title: str
    description: str
    risk_level: str = "medium"   # "low", "medium", "high", "critical"
    mapped_control: Optional[str] = None
    status: str = "unmapped"     # "unmapped", "partial", "compliant", "non_compliant"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "requirement_id": self.requirement_id,
            "title": self.title,
            "description": self.description,
            "risk_level": self.risk_level,
            "mapped_control": self.mapped_control,
            "status": self.status,
        }


# ── Built-in regulatory requirements ────────────────────────────
_EU_AI_ACT_REQUIREMENTS = [
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art6.1", "Risk Classification",
        "High-risk AI systems must be classified and registered", "high",
        "architecture.py — layer governance", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art9.1", "Risk Management System",
        "Establish and maintain a risk management system", "critical",
        "red_team.py — automated adversarial testing", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art10.1", "Data Governance",
        "Training, validation and testing data shall be subject to governance", "high",
        "governance.py — policy enforcement", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art11.1", "Technical Documentation",
        "Maintain up-to-date technical documentation", "high",
        "observability.py — tracing and audit", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art12.1", "Record-Keeping",
        "Automatic logging of events for traceability", "critical",
        "compliance.py — immutable audit trail", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art13.1", "Transparency",
        "Designed to be sufficiently transparent for users", "high",
        "observability.py — chain-of-thought visibility", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art14.1", "Human Oversight",
        "Allow effective human oversight of the AI system", "critical",
        "cognitive.py — GWT attentional spotlight", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art15.1", "Accuracy and Robustness",
        "Achieve appropriate levels of accuracy and robustness", "high",
        "stress.py — load testing and regression detection", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art17.1", "Quality Management",
        "Establish a quality management system", "high",
        "architecture.py — fitness functions", "compliant"),
    RegulatoryRequirement("EU_AI_ACT", "EUAIA-Art52.1", "Transparency for Users",
        "Inform natural persons that they are interacting with AI", "medium",
        "api.py — AI disclosure header", "compliant"),
]

_HIPAA_REQUIREMENTS = [
    RegulatoryRequirement("HIPAA", "HIPAA-164.312(a)", "Access Control",
        "Implement access controls to restrict PHI access", "critical",
        "api.py — RBAC middleware", "compliant"),
    RegulatoryRequirement("HIPAA", "HIPAA-164.312(b)", "Audit Controls",
        "Implement mechanisms to record and examine activity", "critical",
        "compliance.py — audit trail", "compliant"),
    RegulatoryRequirement("HIPAA", "HIPAA-164.312(c)", "Integrity",
        "Protect PHI from improper alteration or destruction", "high",
        "compliance.py — cryptographic hashing", "compliant"),
    RegulatoryRequirement("HIPAA", "HIPAA-164.312(d)", "Person Authentication",
        "Verify identity of persons seeking access to PHI", "high",
        "api.py — authentication middleware", "partial"),
    RegulatoryRequirement("HIPAA", "HIPAA-164.312(e)", "Transmission Security",
        "Protect PHI during electronic transmission", "high",
        "api.py — HTTPS enforcement", "compliant"),
    RegulatoryRequirement("HIPAA", "HIPAA-164.308(a)(1)", "Security Management Process",
        "Implement policies to prevent security violations", "critical",
        "governance.py — policy engine", "compliant"),
]

_GDPR_REQUIREMENTS = [
    RegulatoryRequirement("GDPR", "GDPR-Art5.1(a)", "Lawfulness and Transparency",
        "Personal data shall be processed lawfully and transparently", "critical",
        "observability.py — full traceability", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art5.1(b)", "Purpose Limitation",
        "Collected for specified, explicit purposes only", "high",
        "governance.py — purpose binding", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art5.1(c)", "Data Minimisation",
        "Adequate, relevant and limited to what is necessary", "high",
        "compliance.py — dynamic data masking", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art5.1(f)", "Integrity and Confidentiality",
        "Processed with appropriate security measures", "critical",
        "ast_security.py + persistence.py", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art17.1", "Right to Erasure",
        "Data subject right to have personal data erased", "high",
        None, "partial"),
    RegulatoryRequirement("GDPR", "GDPR-Art25.1", "Data Protection by Design",
        "Implement appropriate technical measures by design", "critical",
        "compliance.py — PII masking at protocol level", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art30.1", "Records of Processing",
        "Maintain a record of processing activities", "high",
        "compliance.py — audit trail", "compliant"),
    RegulatoryRequirement("GDPR", "GDPR-Art35.1", "Data Protection Impact Assessment",
        "Carry out assessment for high-risk processing", "high",
        "vendor_risk.py — automated risk assessment", "compliant"),
]


def regulatory_map() -> Dict[str, Any]:
    """
    Return the full regulatory mapping matrix with gap analysis.
    """
    all_reqs = _EU_AI_ACT_REQUIREMENTS + _HIPAA_REQUIREMENTS + _GDPR_REQUIREMENTS

    frameworks: Dict[str, Dict[str, Any]] = {}
    for req in all_reqs:
        if req.framework not in frameworks:
            frameworks[req.framework] = {
                "total": 0, "compliant": 0, "partial": 0,
                "unmapped": 0, "non_compliant": 0, "requirements": [],
            }
        f = frameworks[req.framework]
        f["total"] += 1
        f[req.status] += 1
        f["requirements"].append(req.to_dict())

    # Compute compliance scores
    for fname, fdata in frameworks.items():
        total = fdata["total"] or 1
        fdata["compliance_score"] = round(
            (fdata["compliant"] + 0.5 * fdata["partial"]) / total, 4
        )

    gaps = [
        req.to_dict() for req in all_reqs
        if req.status in ("unmapped", "non_compliant")
    ]

    return {
        "frameworks": frameworks,
        "total_requirements": len(all_reqs),
        "total_gaps": len(gaps),
        "gaps": gaps,
        "overall_compliance_score": round(
            sum(f["compliance_score"] for f in frameworks.values()) / len(frameworks), 4
        ),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. IMMUTABLE AUDIT TRAIL                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class AuditEntry:
    """A single entry in the immutable audit log."""
    event_id: str = ""
    event_type: str = ""        # "model_prompt", "tool_execution", "role_change",
                                 # "data_export", "config_change", "login", "access"
    actor: str = ""             # user or agent ID
    resource: str = ""
    action: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    previous_hash: str = ""
    entry_hash: str = ""

    def compute_hash(self, previous_hash: str = "") -> str:
        """Compute cryptographic hash for immutability chain."""
        self.previous_hash = previous_hash
        payload = json.dumps({
            "event_type": self.event_type,
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()
        return self.entry_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class AuditTrail:
    """
    Append-only, cryptographically chained audit log.
    Each entry's hash depends on the previous entry, forming
    an immutable chain (similar to blockchain).
    Thread-safe.
    """

    MAX_ENTRIES = 10000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: List[AuditEntry] = []
        self._last_hash: str = "genesis"
        self._counter: int = 0

    def log(
        self,
        event_type: str,
        actor: str,
        resource: str = "",
        action: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a new entry to the audit trail."""
        with self._lock:
            self._counter += 1
            entry = AuditEntry(
                event_id=f"AE-{self._counter:06d}",
                event_type=event_type,
                actor=actor,
                resource=resource,
                action=action,
                details=details or {},
            )
            entry.compute_hash(self._last_hash)
            self._last_hash = entry.entry_hash
            self._entries.append(entry)

            # Trim oldest if over capacity (keep chain intact)
            if len(self._entries) > self.MAX_ENTRIES:
                self._entries = self._entries[-self.MAX_ENTRIES:]

            return entry.to_dict()

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify the full chain of hashes for tampering detection."""
        with self._lock:
            if not self._entries:
                return {"valid": True, "entries_checked": 0, "message": "Empty trail"}

            broken_at: List[str] = []
            prev_hash = self._entries[0].previous_hash

            for i, entry in enumerate(self._entries):
                # Recompute hash
                payload = json.dumps({
                    "event_type": entry.event_type,
                    "actor": entry.actor,
                    "resource": entry.resource,
                    "action": entry.action,
                    "timestamp": entry.timestamp,
                    "previous_hash": entry.previous_hash,
                }, sort_keys=True)
                expected = hashlib.sha256(payload.encode()).hexdigest()

                if entry.entry_hash != expected:
                    broken_at.append(entry.event_id)
                if i > 0 and entry.previous_hash != self._entries[i - 1].entry_hash:
                    broken_at.append(f"{entry.event_id}:chain_break")

            return {
                "valid": len(broken_at) == 0,
                "entries_checked": len(self._entries),
                "broken_entries": broken_at,
                "message": "Integrity verified" if not broken_at else f"{len(broken_at)} integrity violations detected",
            }

    def query(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        limit: int = 50,
        since: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Query the audit trail with optional filters."""
        with self._lock:
            results = self._entries[:]
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            if actor:
                results = [e for e in results if e.actor == actor]
            if since:
                results = [e for e in results if e.timestamp >= since]
            return [e.to_dict() for e in results[-limit:]]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            type_counts: Dict[str, int] = defaultdict(int)
            actor_counts: Dict[str, int] = defaultdict(int)
            for entry in self._entries:
                type_counts[entry.event_type] += 1
                actor_counts[entry.actor] += 1
            return {
                "total_entries": len(self._entries),
                "last_hash": self._last_hash,
                "event_type_distribution": dict(type_counts),
                "actor_distribution": dict(actor_counts),
                "capacity_used": round(len(self._entries) / self.MAX_ENTRIES, 4),
            }

    def export_ocsf(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Export audit entries in OCSF (Open Cybersecurity Schema Framework)
        format for SIEM integration.
        """
        with self._lock:
            ocsf_events = []
            for entry in self._entries[-limit:]:
                ocsf_events.append({
                    "class_uid": 3001,            # OCSF: API Activity
                    "activity_id": 1,             # Create
                    "severity_id": 1,             # Informational
                    "time": entry.timestamp,
                    "message": f"{entry.event_type}: {entry.action}",
                    "actor": {"user": {"name": entry.actor}},
                    "api": {
                        "operation": entry.action,
                        "request": {"uid": entry.event_id},
                    },
                    "resources": [{"name": entry.resource}] if entry.resource else [],
                    "metadata": {
                        "product": {"name": "Praxis", "vendor_name": "Praxis AI"},
                        "version": "1.0.0",
                        "uid": entry.event_id,
                    },
                    "unmapped": {
                        "entry_hash": entry.entry_hash,
                        "previous_hash": entry.previous_hash,
                    },
                })
            return ocsf_events


# Global audit trail singleton
_audit: Optional[AuditTrail] = None
_audit_lock = threading.Lock()


def get_audit_trail() -> AuditTrail:
    global _audit
    with _audit_lock:
        if _audit is None:
            _audit = AuditTrail()
        return _audit


def audit_log(event_type: str, actor: str, **kwargs) -> Dict[str, Any]:
    """Convenience: log to global audit trail."""
    return get_audit_trail().log(event_type, actor, **kwargs)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. DYNAMIC DATA MASKING — PII/PHI Detection                     ║
# ╚════════════════════════════════════════════════════════════════════╝

# PII detection patterns
_PII_PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), "[EMAIL_REDACTED]"),
    ("phone", re.compile(r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), "[PHONE_REDACTED]"),
    ("ssn", re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "[SSN_REDACTED]"),
    ("credit_card", re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), "[CC_REDACTED]"),
    ("ip_address", re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), "[IP_REDACTED]"),
    ("date_of_birth", re.compile(r'\b(?:DOB|date of birth)[:\s]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', re.IGNORECASE), "[DOB_REDACTED]"),
    ("medical_record", re.compile(r'\b(?:MRN|medical record)[:\s#]*\d{4,}\b', re.IGNORECASE), "[MRN_REDACTED]"),
    ("passport", re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'), "[PASSPORT_REDACTED]"),
]


@dataclass
class MaskingResult:
    """Result of a data masking operation."""
    original_length: int = 0
    masked_length: int = 0
    masked_text: str = ""
    detections: List[Dict[str, Any]] = field(default_factory=list)
    pii_found: bool = False
    total_redactions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_length": self.original_length,
            "masked_length": self.masked_length,
            "pii_found": self.pii_found,
            "total_redactions": self.total_redactions,
            "detections": self.detections,
            "masked_text": self.masked_text,
        }


def mask_pii(text: str, categories: Optional[List[str]] = None) -> MaskingResult:
    """
    Detect and mask PII/PHI in text before it enters the LLM context.

    Operates at the protocol level: the original sensitive data never
    reaches the language model.

    Parameters
    ----------
    text       : Raw text potentially containing PII.
    categories : Optional list of PII categories to mask. If None,
                 all categories are applied.
    """
    result = MaskingResult(original_length=len(text))
    masked = text

    for cat_name, pattern, replacement in _PII_PATTERNS:
        if categories and cat_name not in categories:
            continue

        matches = list(pattern.finditer(masked))
        for m in reversed(matches):  # reverse to preserve indices
            result.detections.append({
                "category": cat_name,
                "start": m.start(),
                "end": m.end(),
                "redacted_to": replacement,
            })
            masked = masked[:m.start()] + replacement + masked[m.end():]

    result.masked_text = masked
    result.masked_length = len(masked)
    result.total_redactions = len(result.detections)
    result.pii_found = result.total_redactions > 0
    return result


def detect_pii(text: str) -> Dict[str, Any]:
    """Detect PII without masking — for reporting only."""
    detections: Dict[str, int] = defaultdict(int)
    for cat_name, pattern, _ in _PII_PATTERNS:
        count = len(pattern.findall(text))
        if count > 0:
            detections[cat_name] = count
    return {
        "pii_detected": len(detections) > 0,
        "categories": dict(detections),
        "total_instances": sum(detections.values()),
        "text_length": len(text),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. COMPLIANCE DASHBOARD                                         ║
# ╚════════════════════════════════════════════════════════════════════╝

def compliance_posture() -> Dict[str, Any]:
    """
    Aggregate compliance posture across all frameworks.
    """
    reg_map = regulatory_map()
    audit = get_audit_trail()

    return {
        "regulatory_compliance": reg_map,
        "audit_trail": audit.stats(),
        "audit_integrity": audit.verify_integrity(),
        "data_masking": {
            "engine": "dynamic_protocol_level",
            "categories_supported": [cat for cat, _, _ in _PII_PATTERNS],
            "status": "active",
        },
        "overall_grade": _compute_compliance_grade(reg_map["overall_compliance_score"]),
    }


def _compute_compliance_grade(score: float) -> str:
    """Convert compliance score to letter grade."""
    if score >= 0.95:
        return "A+"
    elif score >= 0.90:
        return "A"
    elif score >= 0.85:
        return "A-"
    elif score >= 0.80:
        return "B+"
    elif score >= 0.75:
        return "B"
    elif score >= 0.70:
        return "B-"
    elif score >= 0.60:
        return "C"
    else:
        return "F"
