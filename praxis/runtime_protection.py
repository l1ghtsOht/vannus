# ────────────────────────────────────────────────────────────────────
# runtime_protection.py — RASP/ADR Runtime Protection
# ────────────────────────────────────────────────────────────────────
"""
Implements Runtime Application Self-Protection (RASP) and
Autonomous Detection & Response (ADR) from the Cognitive
Resilience blueprint.

Core Capabilities:
- **RASP Monitoring**: Real-time attack detection at the application
  layer (injection, XSS, path traversal, deserialization)
- **ADR Engine**: Autonomous threat response with configurable
  escalation policies
- **CSP Validation**: Content Security Policy header verification
- **Security Header Checking**: HSTS, X-Frame-Options, etc.
- **Anomaly Detection**: Statistical anomaly blocking based on
  request patterns
- **Compliance Mapping**: PCI-DSS, HIPAA, SOC2 control verification
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. THREAT DETECTION — RASP                                     ║
# ╚════════════════════════════════════════════════════════════════════╝

class ThreatCategory(str, Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    DESERIALIZATION = "deserialization"
    SSRF = "ssrf"
    PROMPT_INJECTION = "prompt_injection"
    RATE_ABUSE = "rate_abuse"


class ThreatSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


THREAT_PATTERNS = {
    ThreatCategory.SQL_INJECTION: [
        # Classic variants + UNION ALL and comment-bypass (UNION/**/SELECT)
        r"(?:union(?:\s+all)?\s*(?:/\*.*?\*/)?\s*select|;\s*drop\s+table|'\s*or\s+'1'\s*=\s*'1|--\s*$)",
        r"(?:insert\s+into|update\s+\w+\s+set|delete\s+from)\s+\w+",
        # Hex/unicode encoding bypass: 0x554e494f4e → UNION
        r"0x(?:[0-9a-f]{2})+",
        # Stacked queries with non-whitespace separators
        r"(?:;\s*(?:select|insert|update|delete|drop|truncate|exec)\b)",
        # Time-based blind injection (bypasses pattern-match filters via delay, not data)
        r"(?:waitfor\s+delay\s*'|pg_sleep\s*\(|sleep\s*\(\s*\d|benchmark\s*\(\s*\d)",
        # Boolean-based blind: conditional expressions that don't match classic or/and
        r"(?:case\s+when\s+.+?\s+then\s+.+?\s+else|if\s*\(\s*\d\s*=\s*\d)",
    ],
    ThreatCategory.XSS: [
        r"<script[^>]*>",
        r"(?:on(?:error|load|click|mouseover))\s*=",
        r"javascript\s*:",
    ],
    ThreatCategory.PATH_TRAVERSAL: [
        r"\.\./",
        r"(?:%2e%2e|\.\.\\)",
        r"(?:/etc/passwd|/proc/self|c:\\windows)",
    ],
    ThreatCategory.COMMAND_INJECTION: [
        # Common shell commands — with optional /bin/ or /usr/bin/ prefix
        r"(?:;\s*(?:(?:/(?:usr/)?bin/)?(?:ls|cat|rm|wget|curl|bash|sh|python|perl|ruby|nc|ncat|netcat))\b)",
        r"(?:\|\s*(?:sh|bash|cmd|powershell))",
        r"(?:`[^`]+`|\$\([^)]+\))",
        # Obfuscated commands: c''at, c\at, $(echo cat)
        r"""(?:[a-z](?:''|\\|\$\(echo\s)[a-z]+)""",
        # Backtick and $() substitution
        r"(?:;\s*\$\{[^}]+\})",
    ],
    ThreatCategory.DESERIALIZATION: [
        r"(?:pickle\.loads|yaml\.load\(|eval\(|exec\()",
        r"(?:__import__|os\.system|subprocess\.)",
    ],
    ThreatCategory.SSRF: [
        # ── Static IP / hostname patterns ──────────────────────────────
        # Hostname-based (direct)
        r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254\.)",
        # IPv6 loopback variants: ::1, [::1], [::ffff:127.0.0.1]
        r"(?:\[?::1\]?|\[?::ffff:(?:127\.|0:0:0:1)\]?)",
        # Decimal/octal/hex IP encoding: 2130706433, 0x7F000001, 017700000001
        r"(?:0x7[fF]0{6}[0-9a-fA-F]{2}|2130706433|017700000001)",
        # Shorthand IPs: 127.1, 127.0.1
        r"(?:127\.\d{1,3}(?:\.\d{1,3})?(?!\.\d)|0:0:0:0:0:0:0:1)",
        # Non-HTTP schemes used for SSRF
        r"(?:file://|gopher://|dict://|ftp://)",
        # Cloud metadata hostnames (static) — NOTE: DNS rebinding can still
        # redirect attacker.com to 169.254.169.254 at resolution time.
        # This filter only blocks the *literal string*; for full protection
        # use an egress allowlist or DNS pinning at the network layer.
        r"(?:169\.254\.169\.254|169\.254\.170\.2)",
        r"(?:metadata\.google\.internal|instance-data\.ec2\.internal)",
        # Azure IMDS endpoint
        r"(?:168\.63\.129\.16)",
    ],
    ThreatCategory.PROMPT_INJECTION: [
        r"(?:ignore\s+(?:previous|above|all)\s+instructions)",
        r"(?:you\s+are\s+now\s+(?:a|an)\s+(?:different|new))",
        r"(?:system\s*:\s*override|disregard\s+(?:safety|rules))",
    ],
}

SEVERITY_MAPPING = {
    ThreatCategory.SQL_INJECTION: ThreatSeverity.CRITICAL,
    ThreatCategory.XSS: ThreatSeverity.HIGH,
    ThreatCategory.PATH_TRAVERSAL: ThreatSeverity.HIGH,
    ThreatCategory.COMMAND_INJECTION: ThreatSeverity.CRITICAL,
    ThreatCategory.DESERIALIZATION: ThreatSeverity.CRITICAL,
    ThreatCategory.SSRF: ThreatSeverity.HIGH,
    ThreatCategory.PROMPT_INJECTION: ThreatSeverity.MEDIUM,
    ThreatCategory.RATE_ABUSE: ThreatSeverity.LOW,
}


@dataclass
class ThreatDetection:
    """A detected security threat."""
    detection_id: str
    category: ThreatCategory
    severity: ThreatSeverity
    pattern_matched: str
    input_sample: str       # sanitized excerpt of triggering input
    timestamp: float = field(default_factory=time.time)
    blocked: bool = False
    response_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_id": self.detection_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "pattern_matched": self.pattern_matched,
            "input_sample": self.input_sample[:100],
            "timestamp": self.timestamp,
            "blocked": self.blocked,
            "response_action": self.response_action,
        }


def scan_input(
    input_text: str,
    categories: Optional[List[ThreatCategory]] = None,
) -> List[ThreatDetection]:
    """
    Scan input text for security threats using RASP patterns.

    Args:
        input_text: The text to scan (user input, request body, etc.)
        categories: Optional subset of threat categories to check
    """
    if categories is None:
        categories = list(ThreatCategory)
        categories.remove(ThreatCategory.RATE_ABUSE)  # requires context, not pattern

    detections: List[ThreatDetection] = []

    for cat in categories:
        patterns = THREAT_PATTERNS.get(cat, [])
        for pat in patterns:
            if re.search(pat, input_text, re.IGNORECASE):
                det_id = hashlib.md5(f"{cat.value}{pat}{time.time()}".encode()).hexdigest()[:10]
                detections.append(ThreatDetection(
                    detection_id=det_id,
                    category=cat,
                    severity=SEVERITY_MAPPING.get(cat, ThreatSeverity.MEDIUM),
                    pattern_matched=pat[:80],
                    input_sample=input_text[:100],
                ))
                break  # one detection per category is sufficient

    return detections


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. ADR — Autonomous Detection & Response                       ║
# ╚════════════════════════════════════════════════════════════════════╝

class ResponseAction(str, Enum):
    LOG_ONLY = "log_only"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    ESCALATE = "escalate"


ESCALATION_POLICY = {
    ThreatSeverity.INFO: ResponseAction.LOG_ONLY,
    ThreatSeverity.LOW: ResponseAction.WARN,
    ThreatSeverity.MEDIUM: ResponseAction.BLOCK,
    ThreatSeverity.HIGH: ResponseAction.BLOCK,
    ThreatSeverity.CRITICAL: ResponseAction.QUARANTINE,
}


@dataclass
class ADRResponse:
    """Autonomous response to a detected threat."""
    response_id: str
    detection: ThreatDetection
    action: ResponseAction
    details: str
    escalated: bool = False
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "detection_id": self.detection.detection_id,
            "threat_category": self.detection.category.value,
            "severity": self.detection.severity.value,
            "action": self.action.value,
            "details": self.details,
            "escalated": self.escalated,
            "timestamp": self.timestamp,
        }


def respond_to_threat(
    detection: ThreatDetection,
    custom_policy: Optional[Dict[str, str]] = None,
) -> ADRResponse:
    """
    Generate an autonomous response to a detected threat.

    Uses the default escalation policy unless a custom one is provided.
    """
    resp_id = hashlib.md5(f"{detection.detection_id}{time.time()}".encode()).hexdigest()[:10]

    if custom_policy and detection.severity.value in custom_policy:
        action = ResponseAction(custom_policy[detection.severity.value])
    else:
        action = ESCALATION_POLICY.get(detection.severity, ResponseAction.BLOCK)

    details = (
        f"Threat {detection.category.value} (severity: {detection.severity.value}) "
        f"→ action: {action.value}"
    )

    detection.blocked = action in {ResponseAction.BLOCK, ResponseAction.QUARANTINE}
    detection.response_action = action.value

    return ADRResponse(
        response_id=resp_id,
        detection=detection,
        action=action,
        details=details,
        escalated=action == ResponseAction.ESCALATE,
    )


def scan_and_respond(
    input_text: str,
    categories: Optional[List[ThreatCategory]] = None,
) -> List[ADRResponse]:
    """Full RASP+ADR pipeline: scan input and generate responses."""
    detections = scan_input(input_text, categories)
    return [respond_to_threat(d) for d in detections]


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. SECURITY HEADER VALIDATION                                   ║
# ╚════════════════════════════════════════════════════════════════════╝

REQUIRED_HEADERS = {
    "Strict-Transport-Security": {
        "required": True,
        "recommended_value": "max-age=31536000; includeSubDomains; preload",
        "description": "HSTS — enforce HTTPS",
    },
    "X-Content-Type-Options": {
        "required": True,
        "recommended_value": "nosniff",
        "description": "Prevent MIME type sniffing",
    },
    "X-Frame-Options": {
        "required": True,
        "recommended_value": "DENY",
        "description": "Prevent clickjacking via iframes",
    },
    "Content-Security-Policy": {
        "required": True,
        "recommended_value": "default-src 'self'",
        "description": "CSP — restrict resource loading",
    },
    "X-XSS-Protection": {
        "required": False,
        "recommended_value": "0",
        "description": "Legacy XSS filter (modern browsers use CSP)",
    },
    "Referrer-Policy": {
        "required": False,
        "recommended_value": "strict-origin-when-cross-origin",
        "description": "Control referrer information leakage",
    },
    "Permissions-Policy": {
        "required": False,
        "recommended_value": "camera=(), microphone=(), geolocation=()",
        "description": "Restrict browser features",
    },
}


@dataclass
class HeaderValidation:
    """Result of security header validation."""
    header_name: str
    present: bool
    value: Optional[str]
    required: bool
    compliant: bool
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header_name": self.header_name,
            "present": self.present,
            "value": self.value,
            "required": self.required,
            "compliant": self.compliant,
            "recommendation": self.recommendation,
        }


@dataclass
class HeaderReport:
    """Complete security header audit report."""
    report_id: str
    validations: List[HeaderValidation] = field(default_factory=list)
    compliance_score: float = 0.0
    missing_required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "validations": [v.to_dict() for v in self.validations],
            "compliance_score": round(self.compliance_score, 4),
            "missing_required": self.missing_required,
        }


def validate_headers(
    headers: Dict[str, str],
) -> HeaderReport:
    """
    Validate security headers against best practices.

    Args:
        headers: Dict of header_name → value from HTTP response
    """
    report_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    validations: List[HeaderValidation] = []
    missing_req: List[str] = []

    for header_name, spec in REQUIRED_HEADERS.items():
        present = header_name in headers
        value = headers.get(header_name)
        required = spec["required"]
        compliant = present  # basic compliance = presence

        recommendation = ""
        if not present and required:
            missing_req.append(header_name)
            recommendation = f"Add {header_name}: {spec['recommended_value']}"
        elif not present:
            recommendation = f"Consider adding {header_name}: {spec['recommended_value']}"

        validations.append(HeaderValidation(
            header_name=header_name,
            present=present,
            value=value,
            required=required,
            compliant=compliant,
            recommendation=recommendation,
        ))

    total = len(REQUIRED_HEADERS)
    compliant_count = sum(1 for v in validations if v.compliant)
    score = compliant_count / total if total > 0 else 0.0

    return HeaderReport(
        report_id=report_id,
        validations=validations,
        compliance_score=score,
        missing_required=missing_req,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. ANOMALY DETECTION                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class AnomalyRecord:
    """A detected anomaly in request patterns."""
    anomaly_id: str
    metric_name: str
    observed_value: float
    expected_range: Tuple[float, float]
    deviation: float       # standard deviations from mean
    severity: ThreatSeverity
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "metric_name": self.metric_name,
            "observed_value": round(self.observed_value, 4),
            "expected_range": [round(self.expected_range[0], 4), round(self.expected_range[1], 4)],
            "deviation": round(self.deviation, 4),
            "severity": self.severity.value,
            "timestamp": self.timestamp,
        }


def detect_anomaly(
    metric_name: str,
    observed: float,
    historical_mean: float,
    historical_std: float,
    threshold_sigmas: float = 3.0,
) -> Optional[AnomalyRecord]:
    """
    Detect statistical anomalies in a metric.

    Args:
        metric_name: Name of the metric being monitored
        observed: Current observed value
        historical_mean: Historical average
        historical_std: Historical standard deviation
        threshold_sigmas: Number of standard deviations for anomaly (default 3σ)
    """
    if historical_std <= 0:
        return None

    deviation = abs(observed - historical_mean) / historical_std

    if deviation < threshold_sigmas:
        return None  # within normal range

    anom_id = hashlib.md5(f"{metric_name}{observed}{time.time()}".encode()).hexdigest()[:10]

    if deviation < 4.0:
        severity = ThreatSeverity.LOW
    elif deviation < 5.0:
        severity = ThreatSeverity.MEDIUM
    elif deviation < 6.0:
        severity = ThreatSeverity.HIGH
    else:
        severity = ThreatSeverity.CRITICAL

    expected_range = (
        historical_mean - threshold_sigmas * historical_std,
        historical_mean + threshold_sigmas * historical_std,
    )

    return AnomalyRecord(
        anomaly_id=anom_id,
        metric_name=metric_name,
        observed_value=observed,
        expected_range=expected_range,
        deviation=deviation,
        severity=severity,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. COMPLIANCE MAPPING                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

COMPLIANCE_CONTROLS = {
    "PCI_DSS": {
        "6.5": "Address common coding vulnerabilities",
        "6.6": "Web application firewall or code review",
        "8.1": "Unique IDs for all users",
        "10.1": "Audit trails for all system components",
    },
    "HIPAA": {
        "164.312(a)": "Access control — unique user identification",
        "164.312(c)": "Integrity controls — protect data from alteration",
        "164.312(d)": "Authentication — verify entity identity",
        "164.312(e)": "Transmission security — encryption in transit",
    },
    "SOC2": {
        "CC6.1": "Logical and physical access controls",
        "CC6.6": "Security event monitoring and response",
        "CC7.2": "System monitoring for anomalies",
        "CC8.1": "Change management processes",
    },
}


@dataclass
class ComplianceCheck:
    """Result of a specific compliance control check."""
    framework: str
    control_id: str
    description: str
    status: str        # "pass", "fail", "partial", "not_applicable"
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework,
            "control_id": self.control_id,
            "description": self.description,
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass
class ComplianceReport:
    """Complete compliance verification report."""
    report_id: str
    framework: str
    checks: List[ComplianceCheck] = field(default_factory=list)
    compliance_score: float = 0.0
    status: str = "non_compliant"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "framework": self.framework,
            "checks": [c.to_dict() for c in self.checks],
            "compliance_score": round(self.compliance_score, 4),
            "status": self.status,
        }


def check_compliance(
    framework: str,
    control_statuses: Dict[str, str],
) -> ComplianceReport:
    """
    Verify compliance against a specific framework.

    Args:
        framework: "PCI_DSS", "HIPAA", or "SOC2"
        control_statuses: Dict mapping control_id → status
            (status: "pass", "fail", "partial", "not_applicable")
    """
    report_id = hashlib.md5(f"{framework}{time.time()}".encode()).hexdigest()[:10]
    controls = COMPLIANCE_CONTROLS.get(framework, {})

    checks: List[ComplianceCheck] = []
    for ctrl_id, description in controls.items():
        status = control_statuses.get(ctrl_id, "fail")
        checks.append(ComplianceCheck(
            framework=framework,
            control_id=ctrl_id,
            description=description,
            status=status,
        ))

    passing = sum(1 for c in checks if c.status in {"pass", "not_applicable"})
    score = passing / max(len(checks), 1)

    if score >= 1.0:
        overall_status = "compliant"
    elif score >= 0.8:
        overall_status = "mostly_compliant"
    elif score >= 0.5:
        overall_status = "partially_compliant"
    else:
        overall_status = "non_compliant"

    return ComplianceReport(
        report_id=report_id,
        framework=framework,
        checks=checks,
        compliance_score=score,
        status=overall_status,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def runtime_protection_summary() -> Dict[str, Any]:
    """Return a summary of the runtime protection engine."""
    return {
        "rasp": {
            "threat_categories": [t.value for t in ThreatCategory],
            "pattern_count": sum(len(p) for p in THREAT_PATTERNS.values()),
        },
        "adr": {
            "response_actions": [a.value for a in ResponseAction],
            "escalation_policy": {s.value: a.value for s, a in ESCALATION_POLICY.items()},
        },
        "security_headers": {
            "total": len(REQUIRED_HEADERS),
            "required": sum(1 for h in REQUIRED_HEADERS.values() if h["required"]),
        },
        "anomaly_detection": {
            "method": "Statistical (z-score)",
            "default_threshold": "3σ",
        },
        "compliance_frameworks": list(COMPLIANCE_CONTROLS.keys()),
    }
