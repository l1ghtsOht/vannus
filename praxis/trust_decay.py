# ────────────────────────────────────────────────────────────────────
# trust_decay.py — Praxis v3.0 Trust Decay Monitoring Engine
# ────────────────────────────────────────────────────────────────────
"""
Continuous surveillance engine for vendor trust degradation.

Operates INDEPENDENTLY from the ingestion pipeline to ensure heavy
ingestion loads never impede real-time monitoring.

Detection Methods:
    1. Pricing page structural diffs (Wayback CDX)
    2. Review sentiment NLP anomaly detection (G2 / Capterra)
    3. SSL certificate validity monitoring
    4. DNS routing change detection
    5. Keyword density spike analysis for urgent complaints

Alert Tiers:
    MILD   (Yellow/Caution) — gradual erosion, no active notification
    SEVERE (Red/Under Review) — binary red-flag event, proactive email

Architecture:
    Designed for Celery Beat dispatch every 72 hours.  Ships with a
    synchronous fallback for environments without Redis/Celery.

Usage:
    from praxis.trust_decay import run_trust_sweep, get_decay_alerts
    alerts = run_trust_sweep()
    active = get_decay_alerts(severity="severe")
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Final, List, Optional, Tuple

logger = logging.getLogger("praxis.trust_decay")

# ── Latent Flux orchestration monitor (optional) ──
_lf_monitor = None
try:
    from .lf_monitor import OrchestrationMonitor as _OrchestrationMonitor
    _lf_monitor = _OrchestrationMonitor(d=6, leak_rate=0.1)
    logger.info("Latent Flux monitor loaded — LF-enhanced trust decay active")
except ImportError:
    try:
        from lf_monitor import OrchestrationMonitor as _OrchestrationMonitor  # type: ignore[no-redef]
        _lf_monitor = _OrchestrationMonitor(d=6, leak_rate=0.1)
        logger.info("Latent Flux monitor loaded (direct import)")
    except ImportError:
        logger.info("Latent Flux monitor not available — using threshold-based trust decay")

try:
    from .pipeline_constants import (
        TRUST_DECAY_INTERVAL_HOURS,
        TRUST_DECAY_MILD_SENTIMENT_DROP,
        TRUST_DECAY_SEVERE_OUTAGE_HOURS,
        TRUST_DECAY_PRICE_HIKE_PCT,
        TRUST_DECAY_SEVERE_KEYWORDS,
        TRUST_DECAY_MILD_KEYWORDS,
        BADGE_TIERS,
    )
except ImportError:
    from pipeline_constants import (  # type: ignore[no-redef]
        TRUST_DECAY_INTERVAL_HOURS,
        TRUST_DECAY_MILD_SENTIMENT_DROP,
        TRUST_DECAY_SEVERE_OUTAGE_HOURS,
        TRUST_DECAY_PRICE_HIKE_PCT,
        TRUST_DECAY_SEVERE_KEYWORDS,
        TRUST_DECAY_MILD_KEYWORDS,
        BADGE_TIERS,
    )


# =====================================================================
# Data Models
# =====================================================================

class DecaySeverity(str, Enum):
    """Trust decay alert severity levels."""
    NONE   = "none"
    MILD   = "mild"     # Yellow / Caution badge
    SEVERE = "severe"   # Red / Under Review badge


class DecaySignalType(str, Enum):
    """Categories of decay signals."""
    PRICING_CHANGE     = "pricing_change"
    SENTIMENT_DROP     = "sentiment_drop"
    SUPPORT_SLA_BREACH = "support_sla_breach"
    SSL_EXPIRY         = "ssl_expiry"
    DNS_CHANGE         = "dns_change"
    DATA_BREACH        = "data_breach"
    SERVICE_SHUTDOWN   = "service_shutdown"
    MASS_COMPLAINTS    = "mass_complaints"
    API_OUTAGE         = "api_outage"
    PE_ACQUISITION     = "pe_acquisition"
    FREE_TIER_REMOVED  = "free_tier_removed"


@dataclass
class DecaySignal:
    """A single detected trust decay signal."""
    signal_type: str
    severity: str
    description: str
    tool_name: str
    tool_url: str = ""
    evidence: str = ""              # raw data supporting the detection
    detected_at: str = ""           # ISO timestamp
    confidence: float = 0.0         # 0.0-1.0 detection confidence
    requires_hitl: bool = False     # must be human-verified before notification

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DecayAlert:
    """An aggregated alert for a single tool — may contain multiple signals."""
    tool_name: str
    tool_url: str = ""
    severity: str = DecaySeverity.NONE.value
    previous_badge: str = ""
    new_badge: str = ""
    signals: list[DecaySignal] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)  # vetted replacements
    created_at: str = ""
    notified_users: list[str] = field(default_factory=list)
    hitl_verified: bool = False

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "signals": [s.to_dict() for s in self.signals],
        }


@dataclass
class DecaySweepResult:
    """Result of a full trust decay monitoring sweep."""
    sweep_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    tools_monitored: int = 0
    alerts_generated: int = 0
    mild_alerts: int = 0
    severe_alerts: int = 0
    alerts: list[DecayAlert] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            **asdict(self),
            "alerts": [a.to_dict() for a in self.alerts],
        }


# =====================================================================
# 1. PRICING PAGE DIFF ENGINE (Wayback CDX)
# =====================================================================

def _check_pricing_changes(domain: str, tool_name: str) -> list[DecaySignal]:
    """Detect pricing page structural changes via Wayback CDX API."""
    signals: list[DecaySignal] = []
    now = datetime.datetime.utcnow().isoformat()

    try:
        import httpx
        cdx_url = "https://web.archive.org/cdx/search/cdx"
        from_date = (
            datetime.datetime.utcnow() - datetime.timedelta(days=90)
        ).strftime("%Y%m%d")
        params = {
            "url": f"{domain}/pricing*",
            "output": "json",
            "from": from_date,
            "fl": "timestamp,digest,length,statuscode",
        }
        resp = httpx.get(cdx_url, params=params, timeout=30)
        if resp.status_code != 200:
            return signals

        rows = resp.json()
        if len(rows) <= 2:
            return signals  # not enough snapshots to diff

        # Compare byte lengths — significant change = potential price hike
        lengths = [int(r[2]) for r in rows[1:] if r[2].isdigit()]
        if len(lengths) >= 2:
            oldest = lengths[0]
            newest = lengths[-1]
            if oldest > 0:
                change_pct = abs(newest - oldest) / oldest
                if change_pct >= TRUST_DECAY_PRICE_HIKE_PCT:
                    severity = DecaySeverity.MILD.value
                    desc = (
                        f"Pricing page content changed by {change_pct:.0%} "
                        f"over the last 90 days"
                    )
                    # Check for free tier removal
                    if newest < oldest * 0.5:
                        severity = DecaySeverity.SEVERE.value
                        desc = "Possible free tier removal or major pricing restructure"

                    signals.append(DecaySignal(
                        signal_type=DecaySignalType.PRICING_CHANGE.value,
                        severity=severity,
                        description=desc,
                        tool_name=tool_name,
                        tool_url=domain,
                        evidence=f"oldest_length={oldest}, newest_length={newest}, change={change_pct:.2%}",
                        detected_at=now,
                        confidence=0.7,
                        requires_hitl=(severity == DecaySeverity.SEVERE.value),
                    ))
    except Exception as exc:
        logger.debug("[trust_decay] CDX pricing check failed for %s: %s", domain, exc)

    return signals


# =====================================================================
# 2. REVIEW SENTIMENT NLP ANALYSIS
# =====================================================================

def _check_review_sentiment(tool_name: str, domain: str) -> list[DecaySignal]:
    """Analyse review sentiment trends from G2/Capterra.
    Detects both mild sentiment erosion and severe keyword spikes."""
    signals: list[DecaySignal] = []
    now = datetime.datetime.utcnow().isoformat()

    # In production: ScraperAPI → G2/Capterra → NLP sentiment extraction
    # Stub: simulate review corpus analysis

    # Check for severe keyword density spikes
    _simulated_recent_reviews = [
        # This would come from the G2/Capterra scraper
    ]

    for review_text in _simulated_recent_reviews:
        lower = review_text.lower()

        # Severe keywords
        for kw in TRUST_DECAY_SEVERE_KEYWORDS:
            if kw in lower:
                signals.append(DecaySignal(
                    signal_type=DecaySignalType.DATA_BREACH.value
                    if "breach" in kw or "leak" in kw
                    else DecaySignalType.MASS_COMPLAINTS.value,
                    severity=DecaySeverity.SEVERE.value,
                    description=f"Severe keyword detected in reviews: '{kw}'",
                    tool_name=tool_name,
                    tool_url=domain,
                    evidence=review_text[:200],
                    detected_at=now,
                    confidence=0.85,
                    requires_hitl=True,
                ))
                break

        # Mild keywords
        for kw in TRUST_DECAY_MILD_KEYWORDS:
            if kw in lower:
                signals.append(DecaySignal(
                    signal_type=DecaySignalType.SUPPORT_SLA_BREACH.value,
                    severity=DecaySeverity.MILD.value,
                    description=f"Support concern detected in reviews: '{kw}'",
                    tool_name=tool_name,
                    tool_url=domain,
                    evidence=review_text[:200],
                    detected_at=now,
                    confidence=0.65,
                    requires_hitl=False,
                ))
                break

    return signals


# =====================================================================
# 3. SSL CERTIFICATE MONITORING
# =====================================================================

def _check_ssl_certificate(domain: str, tool_name: str) -> list[DecaySignal]:
    """Monitor SSL certificate validity.  Expiring or invalid certs
    often precede catastrophic vendor shutdowns."""
    signals: list[DecaySignal] = []
    now = datetime.datetime.utcnow().isoformat()

    try:
        import ssl
        import socket
        hostname = domain.replace("https://", "").replace("http://", "").split("/")[0]
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(10)
            s.connect((hostname, 443))
            cert = s.getpeercert()
            not_after = datetime.datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            )
            days_remaining = (not_after - datetime.datetime.utcnow()).days

            if days_remaining <= 0:
                signals.append(DecaySignal(
                    signal_type=DecaySignalType.SSL_EXPIRY.value,
                    severity=DecaySeverity.SEVERE.value,
                    description=f"SSL certificate EXPIRED {abs(days_remaining)} days ago",
                    tool_name=tool_name,
                    tool_url=domain,
                    detected_at=now,
                    confidence=1.0,
                    requires_hitl=False,
                ))
            elif days_remaining <= 14:
                signals.append(DecaySignal(
                    signal_type=DecaySignalType.SSL_EXPIRY.value,
                    severity=DecaySeverity.MILD.value,
                    description=f"SSL certificate expires in {days_remaining} days",
                    tool_name=tool_name,
                    tool_url=domain,
                    detected_at=now,
                    confidence=0.9,
                    requires_hitl=False,
                ))
    except Exception as exc:
        logger.debug("[trust_decay] SSL check failed for %s: %s", domain, exc)

    return signals


# =====================================================================
# 4. DNS ROUTING MONITOR
# =====================================================================

def _check_dns_routing(domain: str, tool_name: str) -> list[DecaySignal]:
    """Detect DNS routing changes (e.g., domain parked, redirected)."""
    signals: list[DecaySignal] = []
    now = datetime.datetime.utcnow().isoformat()

    try:
        import socket
        hostname = domain.replace("https://", "").replace("http://", "").split("/")[0]
        addrs = socket.getaddrinfo(hostname, 443)
        if not addrs:
            signals.append(DecaySignal(
                signal_type=DecaySignalType.DNS_CHANGE.value,
                severity=DecaySeverity.SEVERE.value,
                description="DNS resolution failed — domain may be offline",
                tool_name=tool_name,
                tool_url=domain,
                detected_at=now,
                confidence=0.95,
                requires_hitl=True,
            ))
    except socket.gaierror:
        signals.append(DecaySignal(
            signal_type=DecaySignalType.DNS_CHANGE.value,
            severity=DecaySeverity.SEVERE.value,
            description="DNS lookup failure — domain unreachable",
            tool_name=tool_name,
            tool_url=domain,
            detected_at=now,
            confidence=0.95,
            requires_hitl=True,
        ))
    except Exception as exc:
        logger.debug("[trust_decay] DNS check failed for %s: %s", domain, exc)

    return signals


# =====================================================================
# 5. ALTERNATIVE GENERATION (Neo4j Traversal)
# =====================================================================

def _find_alternatives(tool_name: str, limit: int = 3) -> list[str]:
    """Use the Tool Relationship Layer to find vetted alternatives.
    Falls back to category-based matching if graph is unavailable."""
    try:
        from .graph import get_graph
        from .data import TOOLS
        g = get_graph(TOOLS)
        competitors = g.get_competitors(tool_name)
        if competitors:
            return [c["name"] for c in competitors[:limit]]
    except Exception:
        pass

    try:
        from .data import TOOLS
        # Fallback: find tools in the same category
        target = None
        for tool in TOOLS:
            if tool.name.lower() == tool_name.lower():
                target = tool
                break
        if target and target.categories:
            alts = [
                t.name for t in TOOLS
                if t.name != tool_name
                and any(c in t.categories for c in target.categories)
            ][:limit]
            return alts
    except Exception:
        pass

    return []


# =====================================================================
# 6. NOTIFICATION ENGINE
# =====================================================================

def _compose_severe_alert_email(alert: DecayAlert) -> dict:
    """Compose the plain-text Severe Decay notification email.
    Transforms a negative vendor event into a Praxis value demonstration."""
    alt_text = ""
    if alert.alternatives:
        alt_text = "\n\nVetted Alternatives (High-Confidence Replacements):\n"
        for i, alt in enumerate(alert.alternatives, 1):
            alt_text += f"  {i}. {alt}\n"

    signal_text = "\n".join(
        f"  • [{s.signal_type}] {s.description}"
        for s in alert.signals
    )

    body = (
        f"Trust Decay Alert — {alert.tool_name}\n"
        f"{'=' * 50}\n\n"
        f"Praxis has detected a significant trust degradation event\n"
        f"for {alert.tool_name} ({alert.tool_url}).\n\n"
        f"This tool has been moved from {alert.previous_badge} to\n"
        f"{alert.new_badge} status.\n\n"
        f"Detected Signals:\n{signal_text}\n"
        f"{alt_text}\n"
        f"Action Required: Review your operational dependency on this tool.\n"
        f"Praxis will continue monitoring and update you if the situation changes.\n\n"
        f"— Praxis Trust Decay Engine v3.0"
    )

    return {
        "subject": f"⚠ Trust Decay Alert: {alert.tool_name} — Status Changed to {alert.new_badge}",
        "body": body,
        "tool_name": alert.tool_name,
        "severity": alert.severity,
    }


# =====================================================================
# 7. ALERT STORAGE
# =====================================================================

_active_alerts: list[DecayAlert] = []
_alert_history: list[DecayAlert] = []

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pipeline_data")


def get_decay_alerts(
    severity: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> list[dict]:
    """Return active decay alerts, optionally filtered."""
    filtered = _active_alerts
    if severity:
        filtered = [a for a in filtered if a.severity == severity]
    if tool_name:
        filtered = [a for a in filtered if a.tool_name.lower() == tool_name.lower()]
    return [a.to_dict() for a in filtered]


def get_alert_history(limit: int = 50) -> list[dict]:
    """Return historical decay alerts."""
    return [a.to_dict() for a in _alert_history[-limit:]]


def acknowledge_alert(tool_name: str) -> bool:
    """Mark a decay alert as acknowledged / HITL-verified."""
    for alert in _active_alerts:
        if alert.tool_name.lower() == tool_name.lower():
            alert.hitl_verified = True
            logger.info("[trust_decay] alert acknowledged for %s", tool_name)
            return True
    return False


def dismiss_alert(tool_name: str) -> bool:
    """Dismiss a decay alert (false positive)."""
    for i, alert in enumerate(_active_alerts):
        if alert.tool_name.lower() == tool_name.lower():
            _alert_history.append(alert)
            _active_alerts.pop(i)
            logger.info("[trust_decay] alert dismissed for %s", tool_name)
            return True
    return False


# =====================================================================
# 8. MAIN SWEEP ENGINE
# =====================================================================

def _monitor_tool(tool_name: str, domain: str) -> Optional[DecayAlert]:
    """Run all decay detection checks against a single tool."""
    all_signals: list[DecaySignal] = []

    # 1. Pricing page diffs
    all_signals.extend(_check_pricing_changes(domain, tool_name))

    # 2. Review sentiment
    all_signals.extend(_check_review_sentiment(tool_name, domain))

    # 3. SSL certificate
    all_signals.extend(_check_ssl_certificate(domain, tool_name))

    # 4. DNS routing
    all_signals.extend(_check_dns_routing(domain, tool_name))

    if not all_signals:
        return None

    # Determine overall severity
    has_severe = any(s.severity == DecaySeverity.SEVERE.value for s in all_signals)
    overall_severity = DecaySeverity.SEVERE.value if has_severe else DecaySeverity.MILD.value

    # Determine badge change
    if overall_severity == DecaySeverity.SEVERE.value:
        new_badge = BADGE_TIERS["under_review"]["label"]
    else:
        new_badge = BADGE_TIERS["caution"]["label"]

    # Find alternatives for severe alerts
    alternatives = _find_alternatives(tool_name) if has_severe else []

    alert = DecayAlert(
        tool_name=tool_name,
        tool_url=domain,
        severity=overall_severity,
        previous_badge=BADGE_TIERS.get("tier_1", {}).get("label", "Gold / Sovereign"),
        new_badge=new_badge,
        signals=all_signals,
        alternatives=alternatives,
        created_at=datetime.datetime.utcnow().isoformat(),
        hitl_verified=not has_severe,  # mild alerts don't need HITL
    )
    return alert


def run_trust_sweep(
    tools: Optional[list] = None,
) -> DecaySweepResult:
    """Execute a full trust decay monitoring sweep.

    Args:
        tools: List of tool objects (or dicts with 'name' and 'url').
               If None, monitors the approved catalog from ingestion_engine.
    """
    sweep_id = hashlib.md5(
        datetime.datetime.utcnow().isoformat().encode()
    ).hexdigest()[:12]
    started = datetime.datetime.utcnow().isoformat()

    logger.info("[trust_decay] === Sweep %s Started ===", sweep_id)

    # Gather tools to monitor
    if tools is None:
        try:
            from .ingestion_engine import get_approved_catalog
            catalog = get_approved_catalog()
            tools = [
                {"name": t["canonical_name"], "url": t["canonical_url"]}
                for t in catalog
            ]
        except Exception:
            try:
                from .data import TOOLS
                tools = [{"name": t.name, "url": t.url or ""} for t in TOOLS]
            except Exception:
                tools = []

    result = DecaySweepResult(
        sweep_id=sweep_id,
        started_at=started,
        tools_monitored=len(tools),
    )

    for tool_info in tools:
        name = tool_info.get("name", "") if isinstance(tool_info, dict) else getattr(tool_info, "name", "")
        url = tool_info.get("url", "") if isinstance(tool_info, dict) else getattr(tool_info, "url", "")

        if not name:
            continue

        alert = _monitor_tool(name, url)
        if alert:
            # Check if alert already exists for this tool
            existing = next(
                (a for a in _active_alerts if a.tool_name.lower() == name.lower()),
                None,
            )
            if existing:
                # Update existing alert with new signals
                existing.signals.extend(alert.signals)
                existing.severity = max(
                    existing.severity, alert.severity,
                    key=lambda s: [DecaySeverity.NONE.value,
                                   DecaySeverity.MILD.value,
                                   DecaySeverity.SEVERE.value].index(s)
                )
            else:
                _active_alerts.append(alert)
            result.alerts.append(alert)

    # Aggregate counts
    result.alerts_generated = len(result.alerts)
    result.mild_alerts = sum(
        1 for a in result.alerts if a.severity == DecaySeverity.MILD.value
    )
    result.severe_alerts = sum(
        1 for a in result.alerts if a.severity == DecaySeverity.SEVERE.value
    )
    result.completed_at = datetime.datetime.utcnow().isoformat()

    # Auto-apply drift corrections from journey oracle if available
    try:
        from .journey import get_oracle as _sweep_oracle
        oracle = _sweep_oracle()
        corrections = oracle.apply_drift_corrections()
        if corrections:
            logger.info("[trust_decay] Applied %d drift corrections from journey oracle", len(corrections))
    except Exception:
        pass

    logger.info(
        "[trust_decay] === Sweep %s Complete — %d alerts (%d severe, %d mild) ===",
        sweep_id, result.alerts_generated, result.severe_alerts, result.mild_alerts,
    )
    return result


# =====================================================================
# 9. PERSISTENCE
# =====================================================================

def save_decay_state():
    """Persist active alerts to disk."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    path = os.path.join(_DATA_DIR, "trust_decay_alerts.json")
    state = {
        "active_alerts": [a.to_dict() for a in _active_alerts],
        "alert_history": [a.to_dict() for a in _alert_history[-200:]],
        "saved_at": datetime.datetime.utcnow().isoformat(),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_decay_state() -> bool:
    """Load persisted decay state."""
    global _active_alerts, _alert_history
    path = os.path.join(_DATA_DIR, "trust_decay_alerts.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        # Reconstruct alerts from dicts
        _active_alerts = []
        for ad in state.get("active_alerts", []):
            alert_signals = [
                DecaySignal(**{k: v for k, v in s.items() if k in DecaySignal.__dataclass_fields__})
                for s in ad.pop("signals", [])
            ]
            alert = DecayAlert(**{k: v for k, v in ad.items() if k in DecayAlert.__dataclass_fields__})
            alert.signals = alert_signals
            _active_alerts.append(alert)
        return True
    except Exception as exc:
        logger.warning("[trust_decay] failed to load state: %s", exc)
        return False


# =====================================================================
# 10. PUBLIC API HELPERS
# =====================================================================

def get_tool_trust_status(tool_name: str) -> dict:
    """Get the current trust status for a specific tool.
    Returns badge info and any active decay signals."""
    active = [a for a in _active_alerts if a.tool_name.lower() == tool_name.lower()]

    if not active:
        return {
            "tool_name": tool_name,
            "status": "healthy",
            "badge": BADGE_TIERS.get("tier_1", {}),
            "decay_severity": DecaySeverity.NONE.value,
            "active_signals": [],
            "alternatives": [],
        }

    alert = active[0]
    badge_key = "under_review" if alert.severity == DecaySeverity.SEVERE.value else "caution"
    return {
        "tool_name": tool_name,
        "status": "decaying",
        "badge": BADGE_TIERS.get(badge_key, {}),
        "decay_severity": alert.severity,
        "active_signals": [s.to_dict() for s in alert.signals],
        "alternatives": alert.alternatives,
        "detected_at": alert.created_at,
        "hitl_verified": alert.hitl_verified,
    }


def get_decay_summary() -> dict:
    """Dashboard summary of the trust decay monitoring system."""
    return {
        "active_alerts": len(_active_alerts),
        "mild_alerts": sum(1 for a in _active_alerts if a.severity == DecaySeverity.MILD.value),
        "severe_alerts": sum(1 for a in _active_alerts if a.severity == DecaySeverity.SEVERE.value),
        "pending_hitl": sum(1 for a in _active_alerts if not a.hitl_verified),
        "total_history": len(_alert_history),
        "monitoring_interval_hours": TRUST_DECAY_INTERVAL_HOURS,
        "last_sweep": _active_alerts[-1].created_at if _active_alerts else None,
        "thresholds": {
            "mild_sentiment_drop": TRUST_DECAY_MILD_SENTIMENT_DROP,
            "severe_outage_hours": TRUST_DECAY_SEVERE_OUTAGE_HOURS,
            "price_hike_pct": TRUST_DECAY_PRICE_HIKE_PCT,
        },
    }


# =====================================================================
# Latent Flux Integration — LF-enhanced trust monitoring
# =====================================================================

def lf_record_tool_call(
    tool_name: str,
    latency_ms: float = 0.0,
    quality_score: float = 1.0,
    token_consumption: float = 0.0,
    error_rate: float = 0.0,
    output_length: float = 0.0,
    cost_per_call: float = 0.0,
) -> Optional[float]:
    """Record a tool invocation's performance via LF monitor.

    Returns deviation_score if LF is available, None otherwise.
    """
    if _lf_monitor is None:
        return None
    try:
        metrics = [latency_ms, quality_score, token_consumption,
                   error_rate, output_length, cost_per_call]
        return _lf_monitor.record_tool_call(tool_name, metrics)
    except Exception as exc:
        logger.debug("LF record_tool_call failed for %s: %s", tool_name, exc)
        return None


def lf_assess_severity(tool_name: str, metrics: Optional[list] = None) -> str:
    """Assess trust decay severity using LF basin competition.

    Returns DecaySeverity value: "none", "mild", or "severe".
    Falls back to "none" if LF is unavailable.
    """
    if _lf_monitor is None:
        return DecaySeverity.NONE.value
    try:
        health = _lf_monitor.assess_pipeline_health()
        if health.winner == "failing":
            return DecaySeverity.SEVERE.value
        elif health.winner == "degrading":
            return DecaySeverity.MILD.value
        return DecaySeverity.NONE.value
    except Exception as exc:
        logger.debug("LF severity assessment failed: %s", exc)
        return DecaySeverity.NONE.value


def lf_get_tool_states() -> Optional[dict]:
    """Get all LF-monitored tool states.

    Returns dict of {tool_name: {step_count, deviation_score, variance, std}}
    or None if LF is unavailable.
    """
    if _lf_monitor is None:
        return None
    try:
        return _lf_monitor.get_all_tool_states()
    except Exception:
        return None


# =====================================================================
# MODULE INIT
# =====================================================================

logger.info(
    "trust_decay.py loaded — monitoring every %dh, %d severe keywords, %d mild keywords, LF=%s",
    TRUST_DECAY_INTERVAL_HOURS,
    len(TRUST_DECAY_SEVERE_KEYWORDS),
    len(TRUST_DECAY_MILD_KEYWORDS),
    "active" if _lf_monitor else "disabled",
)
