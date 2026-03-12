# --------------- Model Trust Decay — Dynamic Trust Monitoring ---------------
"""
v20 · Multi-Model Ecosystem — Trust Decay Layer

Adapts the tool-level trust decay system (trust_decay.py) to monitor
LLM models.  Instead of pricing-page diffs and SSL checks, this module
tracks four model-specific decay signals:

    1. Hallucination Rate   — PRISM fact_audit failure %
    2. Quality Drift        — User feedback sentiment trajectory
    3. Latency Degradation  — p95 response time trending up
    4. Cost Creep           — Provider pricing changes

Trust score changes feed back into ModelRegistry to dynamically adjust
tiers via ``registry.update_trust()``.

Architecture
────────────
    ModelDecaySignalType  — signal categories
    ModelDecaySignal      — single detected decay event
    ModelDecayAlert       — aggregated per-model alert
    ModelTrustMonitor     — stateful monitor with signal ingestion + sweep
"""

from __future__ import annotations

import logging
import statistics
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.model_trust_decay")

try:
    from .model_registry import (
        ModelSpec, ModelTier, ModelRegistry, get_registry, compute_tier,
        TIER_1_THRESHOLD, TIER_3_THRESHOLD, DEACTIVATION_THRESHOLD,
    )
except ImportError:
    from model_registry import (
        ModelSpec, ModelTier, ModelRegistry, get_registry, compute_tier,
        TIER_1_THRESHOLD, TIER_3_THRESHOLD, DEACTIVATION_THRESHOLD,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ModelDecaySignalType(str, Enum):
    HALLUCINATION_RATE = "hallucination_rate"
    QUALITY_DRIFT = "quality_drift"
    LATENCY_DEGRADATION = "latency_degradation"
    COST_CREEP = "cost_creep"


class ModelDecaySeverity(str, Enum):
    NONE = "none"
    MILD = "mild"        # -1 to -5 trust points
    SEVERE = "severe"    # -5 to -15 trust points
    CRITICAL = "critical"  # -15+ trust points


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class ModelDecaySignal:
    """A single detected trust decay signal for a model."""
    signal_type: ModelDecaySignalType
    severity: ModelDecaySeverity
    model_id: str
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    detected_at: float = field(default_factory=time.time)
    trust_impact: float = 0.0   # negative number = trust loss
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "severity": self.severity.value,
            "model_id": self.model_id,
            "description": self.description,
            "trust_impact": round(self.trust_impact, 2),
            "confidence": round(self.confidence, 2),
            "detected_at": self.detected_at,
        }


@dataclass
class ModelDecayAlert:
    """Aggregated alert for a single model."""
    model_id: str
    status: AlertStatus = AlertStatus.ACTIVE
    severity: ModelDecaySeverity = ModelDecaySeverity.NONE
    signals: List[ModelDecaySignal] = field(default_factory=list)
    previous_trust: float = 0.0
    new_trust: float = 0.0
    previous_tier: int = 2
    new_tier: int = 2
    created_at: float = field(default_factory=time.time)

    @property
    def total_impact(self) -> float:
        return sum(s.trust_impact for s in self.signals)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "signal_count": len(self.signals),
            "total_impact": round(self.total_impact, 2),
            "previous_trust": round(self.previous_trust, 2),
            "new_trust": round(self.new_trust, 2),
            "previous_tier": self.previous_tier,
            "new_tier": self.new_tier,
            "signals": [s.to_dict() for s in self.signals],
            "created_at": self.created_at,
        }


@dataclass
class ModelSweepResult:
    """Result of a full model trust decay sweep."""
    sweep_id: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0
    models_monitored: int = 0
    alerts_generated: int = 0
    alerts: List[ModelDecayAlert] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sweep_id": self.sweep_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "models_monitored": self.models_monitored,
            "alerts_generated": self.alerts_generated,
            "alerts": [a.to_dict() for a in self.alerts],
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SIGNAL THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Hallucination rate (0-1) above which decay triggers
HALLUCINATION_MILD_THRESHOLD = 0.15
HALLUCINATION_SEVERE_THRESHOLD = 0.30

# Quality: minimum satisfaction rating (out of 5) before decay
QUALITY_MILD_THRESHOLD = 3.5
QUALITY_SEVERE_THRESHOLD = 2.5

# Latency degradation: % increase over baseline p95 to trigger
LATENCY_MILD_PCT = 0.30     # 30% slower
LATENCY_SEVERE_PCT = 0.75   # 75% slower

# Minimum observation window (number of data points) before acting
MIN_OBSERVATION_WINDOW = 10

# Trust recovery rate per positive sweep (capped)
TRUST_RECOVERY_RATE = 1.5
MAX_TRUST = 100.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TRUST MONITOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ModelTrustMonitor:
    """
    Stateful trust decay monitor.  Ingests telemetry signals from:
      - PRISM fact_audit   (hallucination tracking)
      - User feedback      (quality tracking)
      - LLMResponse        (latency tracking)
      - Registry diffs     (cost tracking)

    Runs periodic sweeps to compute decay and update ModelRegistry.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self._lock = threading.RLock()
        self._registry = registry or get_registry()
        self._sweep_counter = 0

        # Telemetry accumulators (model_id → list of values)
        self._hallucination_log: Dict[str, List[float]] = defaultdict(list)
        self._quality_log: Dict[str, List[float]] = defaultdict(list)
        self._latency_log: Dict[str, List[float]] = defaultdict(list)
        self._cost_baseline: Dict[str, float] = {}  # model_id → original cost

        # Alert history
        self._alerts: List[ModelDecayAlert] = []

        # Initialize cost baselines
        for spec in self._registry.list_all():
            self._cost_baseline[spec.model_id] = spec.cost_per_1k_input

    # ── Telemetry ingestion ──

    def record_hallucination(self, model_id: str, hallucinated: bool) -> None:
        """Record a single fact-audit result. 1.0 = hallucination, 0.0 = faithful."""
        with self._lock:
            self._hallucination_log[model_id].append(1.0 if hallucinated else 0.0)
            # Keep rolling window
            if len(self._hallucination_log[model_id]) > 500:
                self._hallucination_log[model_id] = self._hallucination_log[model_id][-500:]

    def record_quality(self, model_id: str, rating: float) -> None:
        """Record user satisfaction rating (1-5 scale)."""
        clamped = max(1.0, min(5.0, rating))
        with self._lock:
            self._quality_log[model_id].append(clamped)
            if len(self._quality_log[model_id]) > 500:
                self._quality_log[model_id] = self._quality_log[model_id][-500:]

    def record_latency(self, model_id: str, latency_ms: float) -> None:
        """Record response latency."""
        with self._lock:
            self._latency_log[model_id].append(latency_ms)
            if len(self._latency_log[model_id]) > 500:
                self._latency_log[model_id] = self._latency_log[model_id][-500:]

    # ── Signal analysis ──

    def _analyze_hallucination(self, model_id: str) -> Optional[ModelDecaySignal]:
        """Compute hallucination rate and generate signal if above threshold."""
        data = self._hallucination_log.get(model_id, [])
        if len(data) < MIN_OBSERVATION_WINDOW:
            return None
        rate = sum(data) / len(data)
        if rate >= HALLUCINATION_SEVERE_THRESHOLD:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.HALLUCINATION_RATE,
                severity=ModelDecaySeverity.SEVERE,
                model_id=model_id,
                description=f"Hallucination rate {rate:.1%} exceeds severe threshold ({HALLUCINATION_SEVERE_THRESHOLD:.0%})",
                evidence={"rate": round(rate, 4), "sample_size": len(data)},
                trust_impact=-10.0,
                confidence=min(1.0, len(data) / 100),
            )
        if rate >= HALLUCINATION_MILD_THRESHOLD:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.HALLUCINATION_RATE,
                severity=ModelDecaySeverity.MILD,
                model_id=model_id,
                description=f"Hallucination rate {rate:.1%} above mild threshold ({HALLUCINATION_MILD_THRESHOLD:.0%})",
                evidence={"rate": round(rate, 4), "sample_size": len(data)},
                trust_impact=-3.0,
                confidence=min(1.0, len(data) / 100),
            )
        return None

    def _analyze_quality(self, model_id: str) -> Optional[ModelDecaySignal]:
        """Detect quality drift via user feedback trend."""
        data = self._quality_log.get(model_id, [])
        if len(data) < MIN_OBSERVATION_WINDOW:
            return None
        avg = statistics.mean(data)
        if avg <= QUALITY_SEVERE_THRESHOLD:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.QUALITY_DRIFT,
                severity=ModelDecaySeverity.SEVERE,
                model_id=model_id,
                description=f"Avg quality rating {avg:.2f}/5 is critically low",
                evidence={"avg_rating": round(avg, 2), "sample_size": len(data)},
                trust_impact=-8.0,
                confidence=min(1.0, len(data) / 50),
            )
        if avg <= QUALITY_MILD_THRESHOLD:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.QUALITY_DRIFT,
                severity=ModelDecaySeverity.MILD,
                model_id=model_id,
                description=f"Avg quality rating {avg:.2f}/5 below expectations",
                evidence={"avg_rating": round(avg, 2), "sample_size": len(data)},
                trust_impact=-3.0,
                confidence=min(1.0, len(data) / 50),
            )
        return None

    def _analyze_latency(self, model_id: str) -> Optional[ModelDecaySignal]:
        """Detect latency degradation via p95 trending."""
        data = self._latency_log.get(model_id, [])
        if len(data) < MIN_OBSERVATION_WINDOW:
            return None

        # Compare first-half p95 vs second-half p95
        mid = len(data) // 2
        if mid < 5:
            return None
        first_half = sorted(data[:mid])
        second_half = sorted(data[mid:])
        p95_first = first_half[int(len(first_half) * 0.95)]
        p95_second = second_half[int(len(second_half) * 0.95)]

        if p95_first <= 0:
            return None
        degradation = (p95_second - p95_first) / p95_first

        if degradation >= LATENCY_SEVERE_PCT:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.LATENCY_DEGRADATION,
                severity=ModelDecaySeverity.SEVERE,
                model_id=model_id,
                description=f"p95 latency increased {degradation:.0%} ({p95_first:.0f}ms → {p95_second:.0f}ms)",
                evidence={"p95_before": round(p95_first), "p95_after": round(p95_second), "degradation_pct": round(degradation, 3)},
                trust_impact=-5.0,
                confidence=0.7,
            )
        if degradation >= LATENCY_MILD_PCT:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.LATENCY_DEGRADATION,
                severity=ModelDecaySeverity.MILD,
                model_id=model_id,
                description=f"p95 latency increased {degradation:.0%}",
                evidence={"p95_before": round(p95_first), "p95_after": round(p95_second), "degradation_pct": round(degradation, 3)},
                trust_impact=-2.0,
                confidence=0.6,
            )
        return None

    def _analyze_cost_creep(self, model_id: str) -> Optional[ModelDecaySignal]:
        """Detect provider pricing changes."""
        spec = self._registry.get(model_id)
        if spec is None:
            return None
        baseline = self._cost_baseline.get(model_id, spec.cost_per_1k_input)
        if baseline <= 0:
            return None
        increase = (spec.cost_per_1k_input - baseline) / baseline
        if increase >= 0.50:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.COST_CREEP,
                severity=ModelDecaySeverity.SEVERE,
                model_id=model_id,
                description=f"Input cost increased {increase:.0%} from baseline",
                evidence={"baseline": baseline, "current": spec.cost_per_1k_input},
                trust_impact=-4.0,
                confidence=0.95,
            )
        if increase >= 0.20:
            return ModelDecaySignal(
                signal_type=ModelDecaySignalType.COST_CREEP,
                severity=ModelDecaySeverity.MILD,
                model_id=model_id,
                description=f"Input cost increased {increase:.0%} from baseline",
                evidence={"baseline": baseline, "current": spec.cost_per_1k_input},
                trust_impact=-2.0,
                confidence=0.95,
            )
        return None

    # ── Sweep ──

    def run_sweep(self) -> ModelSweepResult:
        """
        Run a trust decay sweep across all models.
        Generates signals, computes trust impact, updates registry.
        """
        with self._lock:
            self._sweep_counter += 1
            sweep_id = f"MS-{self._sweep_counter:04d}"
            t0 = time.time()
            models = self._registry.list_all()
            alerts: List[ModelDecayAlert] = []

            for spec in models:
                mid = spec.model_id
                signals: List[ModelDecaySignal] = []

                # Run all four analyzers
                for analyzer in (
                    self._analyze_hallucination,
                    self._analyze_quality,
                    self._analyze_latency,
                    self._analyze_cost_creep,
                ):
                    sig = analyzer(mid)
                    if sig is not None:
                        signals.append(sig)

                if signals:
                    # Apply trust impact
                    total_impact = sum(s.trust_impact * s.confidence for s in signals)
                    new_trust = max(0.0, min(MAX_TRUST, spec.trust_score + total_impact))

                    # Determine alert severity
                    worst = max(signals, key=lambda s: abs(s.trust_impact))
                    alert = ModelDecayAlert(
                        model_id=mid,
                        severity=worst.severity,
                        signals=signals,
                        previous_trust=spec.trust_score,
                        new_trust=new_trust,
                        previous_tier=spec.tier.value,
                        new_tier=compute_tier(new_trust).value,
                    )
                    alerts.append(alert)

                    # Update registry
                    self._registry.update_trust(mid, new_trust)
                    log.info("Model %s trust: %.1f → %.1f (%d signals)",
                             mid, spec.trust_score, new_trust, len(signals))
                else:
                    # No decay signals — slight trust recovery
                    if spec.trust_score < MAX_TRUST:
                        recovery = min(TRUST_RECOVERY_RATE, MAX_TRUST - spec.trust_score)
                        self._registry.update_trust(mid, spec.trust_score + recovery)

            # Store alerts
            self._alerts.extend(alerts)
            # Cap alert history
            if len(self._alerts) > 1000:
                self._alerts = self._alerts[-1000:]

            return ModelSweepResult(
                sweep_id=sweep_id,
                started_at=t0,
                completed_at=time.time(),
                models_monitored=len(models),
                alerts_generated=len(alerts),
                alerts=alerts,
            )

    # ── Alert management ──

    def get_alerts(
        self,
        model_id: Optional[str] = None,
        status: Optional[AlertStatus] = None,
        limit: int = 50,
    ) -> List[ModelDecayAlert]:
        """Retrieve alerts with optional filters."""
        with self._lock:
            filtered = self._alerts
            if model_id:
                filtered = [a for a in filtered if a.model_id == model_id]
            if status:
                filtered = [a for a in filtered if a.status == status]
            return filtered[-limit:]

    def acknowledge_alert(self, model_id: str, index: int = -1) -> bool:
        """Acknowledge (but not resolve) an alert for a model."""
        with self._lock:
            model_alerts = [a for a in self._alerts if a.model_id == model_id and a.status == AlertStatus.ACTIVE]
            if not model_alerts:
                return False
            model_alerts[index].status = AlertStatus.ACKNOWLEDGED
            return True

    def dismiss_alert(self, model_id: str, index: int = -1) -> bool:
        with self._lock:
            model_alerts = [a for a in self._alerts if a.model_id == model_id and a.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)]
            if not model_alerts:
                return False
            model_alerts[index].status = AlertStatus.DISMISSED
            return True

    def get_model_trust_status(self, model_id: str) -> Dict[str, Any]:
        """Comprehensive trust status for a single model."""
        spec = self._registry.get(model_id)
        if spec is None:
            return {"error": f"Model {model_id} not found"}

        with self._lock:
            halluc_data = self._hallucination_log.get(model_id, [])
            quality_data = self._quality_log.get(model_id, [])
            latency_data = self._latency_log.get(model_id, [])
            alerts = [a for a in self._alerts if a.model_id == model_id]

        return {
            "model_id": model_id,
            "trust_score": round(spec.trust_score, 2),
            "tier": spec.tier.value,
            "active": spec.active,
            "signals": {
                "hallucination": {
                    "sample_size": len(halluc_data),
                    "rate": round(sum(halluc_data) / max(len(halluc_data), 1), 4),
                } if halluc_data else None,
                "quality": {
                    "sample_size": len(quality_data),
                    "avg_rating": round(statistics.mean(quality_data), 2) if quality_data else 0,
                } if quality_data else None,
                "latency": {
                    "sample_size": len(latency_data),
                    "p95_ms": round(sorted(latency_data)[int(len(latency_data) * 0.95)]) if latency_data else 0,
                } if latency_data else None,
            },
            "active_alerts": len([a for a in alerts if a.status == AlertStatus.ACTIVE]),
            "total_alerts": len(alerts),
        }

    def summary(self) -> Dict[str, Any]:
        """Trust monitoring summary across all models."""
        with self._lock:
            active_alerts = [a for a in self._alerts if a.status == AlertStatus.ACTIVE]
        return {
            "sweep_count": self._sweep_counter,
            "total_alerts": len(self._alerts),
            "active_alerts": len(active_alerts),
            "models_with_alerts": len(set(a.model_id for a in active_alerts)),
            "models_monitored": len(self._registry.list_all()),
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODULE-LEVEL SINGLETON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_monitor: Optional[ModelTrustMonitor] = None
_monitor_lock = threading.Lock()


def get_trust_monitor() -> ModelTrustMonitor:
    """Return the module-level singleton trust monitor."""
    global _monitor
    if _monitor is None:
        with _monitor_lock:
            if _monitor is None:
                _monitor = ModelTrustMonitor()
    return _monitor
