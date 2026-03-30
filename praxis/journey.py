# ────────── Journey Oracle — Passive Assessment & Drift Monitor ──────────
"""
v22 · Journey Oracle — User Journey State Machine & Outcome Tracker

Tracks the full lifecycle of a user's interaction with Praxis — from
raw idea input through tool selection, stack composition, deployment,
and post-adoption outcome assessment.  Provides a **passive oracle**
that observes recommendation outcomes and feeds drift signals back
into the scoring pipeline.

Architecture
────────────
    JourneyStage       — enum of the 5 pipeline stages
    JourneyState       — mutable state container for a single user journey
    TargetScoreVector  — per-tool expected-vs-actual outcome scoring
    DriftSignal        — detected divergence from predicted outcomes
    JourneyOracle      — singleton tracker: create/advance/assess/monitor

Pipeline Stages
───────────────
    1. INTAKE      — raw idea input, context extraction (context_engine.py)
    2. DISCOVERY   — tool search, elimination pipeline (differential.py)
    3. SELECTION   — stack composition, gap resolution (residual_gap.py)
    4. DEPLOYMENT  — tool adoption, onboarding, first use
    5. OUTCOME     — post-adoption: ROI, satisfaction, drift detection

Design Principles
─────────────────
    • Passive observation — never blocks the request pipeline
    • Deterministic scoring — no LLM calls, pure arithmetic
    • Append-only state — journey history is immutable once written
    • JSON file persistence — no external infra dependencies
    • Trust-weighted outcomes — higher-trust tool signals matter more

Drift Detection
───────────────
    Compares TargetScoreVector (predicted at SELECTION) against actual
    outcome signals (logged at OUTCOME).  When drift exceeds threshold,
    emits a DriftSignal that can feed back into trust_decay.py and
    learning.py to adjust future recommendations.

    Drift formula:
        D = Σ |predicted_i − actual_i| / N
        where i ∈ {relevance, budget_fit, skill_fit, integration_ease}

Usage
─────
    from praxis.journey import get_oracle, JourneyStage

    oracle = get_oracle()

    # Start a journey
    jid = oracle.create_journey("user_123", query="need writing tools for healthcare")

    # Advance stages
    oracle.advance(jid, JourneyStage.DISCOVERY, metadata={"tools_considered": 12})
    oracle.advance(jid, JourneyStage.SELECTION, metadata={"stack": ["Jasper", "Grammarly"]})

    # Record outcome
    oracle.record_outcome(jid, "Jasper", satisfaction=0.85, roi=0.70)

    # Check for drift
    signals = oracle.detect_drift(jid)
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.journey")

# ── Resilient imports ────────────────────────────────────────────────

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg  # type: ignore[no-redef]
    except Exception:
        _cfg = None  # type: ignore[assignment]

try:
    from .context_engine import extract_context, ContextVector
except Exception:
    try:
        from praxis.context_engine import extract_context, ContextVector  # type: ignore[no-redef]
    except Exception:
        extract_context = None  # type: ignore[assignment]
        ContextVector = None  # type: ignore[assignment]

try:
    from .residual_gap import compute_gap, GapAnalysis
except Exception:
    try:
        from praxis.residual_gap import compute_gap, GapAnalysis  # type: ignore[no-redef]
    except Exception:
        compute_gap = None  # type: ignore[assignment]
        GapAnalysis = None  # type: ignore[assignment]

try:
    from .learning import get_tool_quality
except Exception:
    try:
        from praxis.learning import get_tool_quality  # type: ignore[no-redef]
    except Exception:
        get_tool_quality = None  # type: ignore[assignment]


def _conf(key: str, fallback):
    if _cfg:
        return _cfg.get(key, fallback)
    return fallback


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════

class JourneyStage(str, Enum):
    """The five stages of a user journey through Praxis."""
    INTAKE     = "intake"       # Raw idea → context extraction
    DISCOVERY  = "discovery"    # Search → elimination pipeline
    SELECTION  = "selection"    # Stack composition → gap resolution
    DEPLOYMENT = "deployment"   # Tool adoption, onboarding
    OUTCOME    = "outcome"      # Post-adoption assessment

    @property
    def index(self) -> int:
        return list(JourneyStage).index(self)


class DriftSeverity(str, Enum):
    """Severity classification for outcome drift signals."""
    NONE     = "none"
    MILD     = "mild"       # Δ < 0.20 — log only
    MODERATE = "moderate"   # 0.20 ≤ Δ < 0.40 — flag for review
    SEVERE   = "severe"     # Δ ≥ 0.40 — feed back into scoring

# ── Latent Flux reservoir-based drift (optional) ──
_LF_AVAILABLE = False
try:
    from .lf_monitor import ToolReservoir as _ToolReservoir
    _LF_AVAILABLE = True
except ImportError:
    try:
        from praxis.lf_monitor import ToolReservoir as _ToolReservoir
        _LF_AVAILABLE = True
    except ImportError:
        pass


# ═══════════════════════════════════════════════════════════════════
# Data Types
# ═══════════════════════════════════════════════════════════════════

@dataclass
class TargetScoreVector:
    """Predicted outcome scores set at SELECTION stage.

    Each dimension is 0.0–1.0.  Compared against actuals at OUTCOME.
    """
    relevance: float = 0.0
    budget_fit: float = 0.0
    skill_fit: float = 0.0
    integration_ease: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TargetScoreVector":
        return cls(
            relevance=float(d.get("relevance", 0.0)),
            budget_fit=float(d.get("budget_fit", 0.0)),
            skill_fit=float(d.get("skill_fit", 0.0)),
            integration_ease=float(d.get("integration_ease", 0.0)),
        )

    def dimensions(self) -> List[Tuple[str, float]]:
        return [
            ("relevance", self.relevance),
            ("budget_fit", self.budget_fit),
            ("skill_fit", self.skill_fit),
            ("integration_ease", self.integration_ease),
        ]


@dataclass
class DriftSignal:
    """A detected divergence between predicted and actual outcomes."""
    journey_id: str
    tool_name: str
    dimension: str
    predicted: float
    actual: float
    delta: float
    severity: str = DriftSeverity.NONE.value
    detected_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OutcomeRecord:
    """A single tool outcome observation at the OUTCOME stage."""
    tool_name: str
    satisfaction: float = 0.0       # 0.0–1.0 user satisfaction
    roi: float = 0.0                # 0.0–1.0 return on investment
    integration_success: float = 0.0  # 0.0–1.0 integration went smoothly
    still_using: bool = True        # is the user still using this tool?
    recorded_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OutcomeRecord":
        return cls(
            tool_name=str(d.get("tool_name", "")),
            satisfaction=float(d.get("satisfaction", 0.0)),
            roi=float(d.get("roi", 0.0)),
            integration_success=float(d.get("integration_success", 0.0)),
            still_using=bool(d.get("still_using", True)),
            recorded_at=str(d.get("recorded_at", "")),
        )


@dataclass
class StageEntry:
    """A recorded stage transition."""
    stage: str
    entered_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StageEntry":
        return cls(
            stage=str(d.get("stage", "")),
            entered_at=str(d.get("entered_at", "")),
            metadata=dict(d.get("metadata", {})),
        )


@dataclass
class JourneyState:
    """Complete mutable state for a single user journey."""
    journey_id: str
    user_id: str
    query: str = ""
    current_stage: str = JourneyStage.INTAKE.value
    stages: List[StageEntry] = field(default_factory=list)
    target_vectors: Dict[str, TargetScoreVector] = field(default_factory=dict)
    outcomes: List[OutcomeRecord] = field(default_factory=list)
    drift_signals: List[DriftSignal] = field(default_factory=list)
    context_snapshot: Optional[Dict[str, Any]] = None
    gap_snapshot: Optional[Dict[str, Any]] = None
    created_at: str = ""
    updated_at: str = ""
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "journey_id": self.journey_id,
            "user_id": self.user_id,
            "query": self.query,
            "current_stage": self.current_stage,
            "stages": [s.to_dict() for s in self.stages],
            "target_vectors": {k: v.to_dict() for k, v in self.target_vectors.items()},
            "outcomes": [o.to_dict() for o in self.outcomes],
            "drift_signals": [d.to_dict() for d in self.drift_signals],
            "context_snapshot": self.context_snapshot,
            "gap_snapshot": self.gap_snapshot,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JourneyState":
        state = cls(
            journey_id=str(d.get("journey_id", "")),
            user_id=str(d.get("user_id", "")),
            query=str(d.get("query", "")),
            current_stage=str(d.get("current_stage", JourneyStage.INTAKE.value)),
            created_at=str(d.get("created_at", "")),
            updated_at=str(d.get("updated_at", "")),
            completed=bool(d.get("completed", False)),
            context_snapshot=d.get("context_snapshot"),
            gap_snapshot=d.get("gap_snapshot"),
        )
        state.stages = [StageEntry.from_dict(s) for s in d.get("stages", [])]
        state.target_vectors = {
            k: TargetScoreVector.from_dict(v) for k, v in d.get("target_vectors", {}).items()
        }
        state.outcomes = [OutcomeRecord.from_dict(o) for o in d.get("outcomes", [])]
        state.drift_signals = [
            DriftSignal(**s) for s in d.get("drift_signals", [])
        ]
        return state


@dataclass
class JourneyDashboard:
    """Aggregate metrics across all journeys."""
    total_journeys: int = 0
    active_journeys: int = 0
    completed_journeys: int = 0
    avg_satisfaction: float = 0.0
    avg_roi: float = 0.0
    drift_alert_count: int = 0
    stage_distribution: Dict[str, int] = field(default_factory=dict)
    top_drift_tools: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════
# Drift Thresholds
# ═══════════════════════════════════════════════════════════════════

DRIFT_MILD_THRESHOLD = 0.15
DRIFT_MODERATE_THRESHOLD = 0.30
DRIFT_SEVERE_THRESHOLD = 0.45


def _classify_drift(delta: float) -> str:
    """Classify drift severity by absolute delta."""
    abs_d = abs(delta)
    if abs_d >= DRIFT_SEVERE_THRESHOLD:
        return DriftSeverity.SEVERE.value
    if abs_d >= DRIFT_MODERATE_THRESHOLD:
        return DriftSeverity.MODERATE.value
    if abs_d >= DRIFT_MILD_THRESHOLD:
        return DriftSeverity.MILD.value
    return DriftSeverity.NONE.value


# ═══════════════════════════════════════════════════════════════════
# Target Score Vector Builder
# ═══════════════════════════════════════════════════════════════════

def build_target_vector(
    tool_name: str,
    fit_score: float = 0.0,
    budget_match: bool = True,
    skill_match: bool = True,
    integration_count: int = 0,
) -> TargetScoreVector:
    """Build a predicted outcome vector at SELECTION time.

    Parameters are derived from the engine's scoring output:
        fit_score        — normalised to 0–1 from engine score
        budget_match     — True if tool pricing fits user budget
        skill_match      — True if tool skill level fits user
        integration_count — number of integrations with existing stack
    """
    # Relevance: normalize fit_score (engine scores typically 0-30)
    relevance = min(1.0, max(0.0, fit_score / 30.0))

    # Budget fit: binary with soft weighting
    budget_fit = 0.85 if budget_match else 0.25

    # Skill fit: binary with soft weighting
    skill_fit = 0.90 if skill_match else 0.30

    # Integration ease: sigmoid-like mapping
    if integration_count >= 5:
        integration_ease = 0.95
    elif integration_count >= 3:
        integration_ease = 0.80
    elif integration_count >= 1:
        integration_ease = 0.60
    else:
        integration_ease = 0.35

    return TargetScoreVector(
        relevance=round(relevance, 4),
        budget_fit=round(budget_fit, 4),
        skill_fit=round(skill_fit, 4),
        integration_ease=round(integration_ease, 4),
    )


# ═══════════════════════════════════════════════════════════════════
# Journey Oracle — Singleton Tracker
# ═══════════════════════════════════════════════════════════════════

class JourneyOracle:
    """Central journey tracking and drift monitoring engine.

    Thread-safe.  Persists to JSON file for restart survival.
    Designed as a passive observer — never blocks request flow.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._lock = threading.Lock()
        _env_dir = os.environ.get("PRAXIS_DATA_DIR", "")
        if data_dir:
            self._data_dir = Path(data_dir)
        elif _env_dir:
            self._data_dir = Path(_env_dir) / "journey_data"
        else:
            self._data_dir = Path(__file__).parent / "journey_data"
        self._journeys: Dict[str, JourneyState] = {}
        self._loaded = False
        # Per-tool LF reservoirs for drift detection (d=4: relevance, budget_fit, skill_fit, integration_ease)
        self._reservoirs: Dict[str, Any] = {}

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load()
            self._loaded = True

    def _state_file(self) -> Path:
        return self._data_dir / "journeys.json"

    def _load(self) -> None:
        """Load journey state from disk."""
        path = self._state_file()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for jid, jdict in data.items():
                    self._journeys[jid] = JourneyState.from_dict(jdict)
                log.info("Loaded %d journeys from %s", len(self._journeys), path)
            except Exception as exc:
                log.warning("Failed to load journeys: %s", exc)
                self._journeys = {}
        else:
            self._journeys = {}

    def _save(self) -> None:
        """Persist journey state to disk."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            data = {jid: j.to_dict() for jid, j in self._journeys.items()}
            path = self._state_file()
            tmp = path.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            tmp.replace(path)
        except Exception as exc:
            log.warning("Failed to save journeys: %s", exc)

    # ── Journey Lifecycle ────────────────────────────────────────────

    def create_journey(
        self,
        user_id: str,
        query: str = "",
        profile_id: Optional[str] = None,
    ) -> str:
        """Create a new journey and auto-run INTAKE stage.

        Returns the journey_id.
        """
        self._ensure_loaded()

        now = datetime.datetime.utcnow().isoformat()
        raw = f"{user_id}:{query}:{now}"
        jid = hashlib.sha256(raw.encode()).hexdigest()[:16]

        state = JourneyState(
            journey_id=jid,
            user_id=user_id,
            query=query,
            current_stage=JourneyStage.INTAKE.value,
            created_at=now,
            updated_at=now,
        )

        # Auto-run context extraction at INTAKE
        if extract_context and query:
            try:
                ctx = extract_context(query, profile_id=profile_id)
                state.context_snapshot = ctx.to_dict() if hasattr(ctx, "to_dict") else {}
            except Exception as exc:
                log.debug("Context extraction at INTAKE failed: %s", exc)

        # Auto-run gap analysis
        if compute_gap and query:
            try:
                gap = compute_gap(query, profile_id=profile_id)
                state.gap_snapshot = gap.to_dict() if hasattr(gap, "to_dict") else {}
            except Exception as exc:
                log.debug("Gap analysis at INTAKE failed: %s", exc)

        entry = StageEntry(
            stage=JourneyStage.INTAKE.value,
            entered_at=now,
            metadata={"query": query, "profile_id": profile_id},
        )
        state.stages.append(entry)

        with self._lock:
            self._journeys[jid] = state
            self._save()

        log.info("Journey %s created for user=%s", jid, user_id)
        return jid

    def advance(
        self,
        journey_id: str,
        stage: JourneyStage,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> JourneyState:
        """Advance a journey to a new stage.

        Stages must be advanced in order (INTAKE → DISCOVERY → SELECTION →
        DEPLOYMENT → OUTCOME).  Skipping stages is allowed for flexibility.
        """
        self._ensure_loaded()

        with self._lock:
            state = self._journeys.get(journey_id)
            if not state:
                raise ValueError(f"Journey {journey_id} not found")

            now = datetime.datetime.utcnow().isoformat()
            entry = StageEntry(
                stage=stage.value,
                entered_at=now,
                metadata=metadata or {},
            )
            state.stages.append(entry)
            state.current_stage = stage.value
            state.updated_at = now

            if stage == JourneyStage.OUTCOME:
                state.completed = True

            self._save()

        log.info("Journey %s advanced to %s", journey_id, stage.value)
        return state

    def set_target_vector(
        self,
        journey_id: str,
        tool_name: str,
        vector: TargetScoreVector,
    ) -> None:
        """Record the predicted outcome vector for a tool at SELECTION."""
        self._ensure_loaded()

        with self._lock:
            state = self._journeys.get(journey_id)
            if not state:
                raise ValueError(f"Journey {journey_id} not found")
            state.target_vectors[tool_name] = vector
            # Feed predicted vector into LF reservoir
            reservoir = self._get_reservoir(tool_name)
            if reservoir:
                try:
                    reservoir.step([vector.relevance, vector.budget_fit, vector.skill_fit, vector.integration_ease])
                except Exception:
                    pass
            state.updated_at = datetime.datetime.utcnow().isoformat()
            self._save()

    def record_outcome(
        self,
        journey_id: str,
        tool_name: str,
        satisfaction: float = 0.0,
        roi: float = 0.0,
        integration_success: float = 0.0,
        still_using: bool = True,
    ) -> OutcomeRecord:
        """Record an actual outcome observation for a tool."""
        self._ensure_loaded()

        record = OutcomeRecord(
            tool_name=tool_name,
            satisfaction=max(0.0, min(1.0, satisfaction)),
            roi=max(0.0, min(1.0, roi)),
            integration_success=max(0.0, min(1.0, integration_success)),
            still_using=still_using,
            recorded_at=datetime.datetime.utcnow().isoformat(),
        )

        with self._lock:
            state = self._journeys.get(journey_id)
            if not state:
                raise ValueError(f"Journey {journey_id} not found")
            state.outcomes.append(record)
            # Feed actual outcome into LF reservoir
            reservoir = self._get_reservoir(tool_name)
            if reservoir:
                try:
                    reservoir.step([record.satisfaction, record.roi, record.satisfaction, record.integration_success])
                except Exception:
                    pass
            state.updated_at = datetime.datetime.utcnow().isoformat()

            # Auto-advance to OUTCOME stage
            if state.current_stage != JourneyStage.OUTCOME.value:
                state.current_stage = JourneyStage.OUTCOME.value
                state.stages.append(StageEntry(
                    stage=JourneyStage.OUTCOME.value,
                    entered_at=state.updated_at,
                    metadata={"trigger": "outcome_recorded"},
                ))
                state.completed = True

            self._save()

        log.info("Outcome recorded for journey=%s tool=%s", journey_id, tool_name)
        return record

    def _get_reservoir(self, tool_name: str):
        """Get or create a ToolReservoir for drift detection."""
        if not _LF_AVAILABLE:
            return None
        if tool_name not in self._reservoirs:
            self._reservoirs[tool_name] = _ToolReservoir(d=4, leak_rate=0.15, seed=hash(tool_name) % (2**31))
        return self._reservoirs[tool_name]

    # ── Drift Detection ──────────────────────────────────────────────

    def detect_drift(self, journey_id: str) -> List[DriftSignal]:
        """Compare predicted vectors against actual outcomes.

        Returns newly detected drift signals.  Already-detected signals
        are not re-emitted.
        """
        self._ensure_loaded()

        with self._lock:
            state = self._journeys.get(journey_id)
            if not state:
                raise ValueError(f"Journey {journey_id} not found")

            new_signals: List[DriftSignal] = []
            now = datetime.datetime.utcnow().isoformat()

            # Already-detected tool+dimension combos
            existing = {
                (s.tool_name, s.dimension) for s in state.drift_signals
            }

            for outcome in state.outcomes:
                vector = state.target_vectors.get(outcome.tool_name)
                if not vector:
                    continue

                # Map outcome fields to vector dimensions
                actuals = {
                    "relevance": outcome.satisfaction,
                    "budget_fit": outcome.roi,
                    "skill_fit": outcome.satisfaction,
                    "integration_ease": outcome.integration_success,
                }

                # LF-enhanced drift detection
                reservoir = self._get_reservoir(outcome.tool_name)
                if reservoir and _LF_AVAILABLE and reservoir.step_count >= 2:
                    # Use reservoir deviation_score for severity
                    actual_vec = [
                        actuals.get("relevance", 0.0),
                        actuals.get("budget_fit", 0.0),
                        actuals.get("skill_fit", 0.0),
                        actuals.get("integration_ease", 0.0),
                    ]
                    dev_score = reservoir.deviation_score(actual_vec)
                    # Map deviation score to severity
                    if dev_score >= 3.5:
                        lf_severity = DriftSeverity.SEVERE.value
                    elif dev_score >= 2.0:
                        lf_severity = DriftSeverity.MODERATE.value
                    elif dev_score >= 1.0:
                        lf_severity = DriftSeverity.MILD.value
                    else:
                        lf_severity = DriftSeverity.NONE.value

                    if lf_severity != DriftSeverity.NONE.value:
                        # Emit a single aggregate signal per tool
                        if (outcome.tool_name, "aggregate") not in existing:
                            signal = DriftSignal(
                                journey_id=journey_id,
                                tool_name=outcome.tool_name,
                                dimension="aggregate",
                                predicted=0.0,
                                actual=dev_score,
                                delta=dev_score,
                                severity=lf_severity,
                                detected_at=now,
                            )
                            new_signals.append(signal)
                            state.drift_signals.append(signal)
                else:
                    # Fallback: threshold-based per-dimension drift
                    for dim_name, predicted in vector.dimensions():
                        actual = actuals.get(dim_name, 0.0)
                        delta = predicted - actual

                        if (outcome.tool_name, dim_name) in existing:
                            continue

                        severity = _classify_drift(delta)
                        if severity == DriftSeverity.NONE.value:
                            continue

                        signal = DriftSignal(
                            journey_id=journey_id,
                            tool_name=outcome.tool_name,
                            dimension=dim_name,
                            predicted=round(predicted, 4),
                            actual=round(actual, 4),
                            delta=round(delta, 4),
                            severity=severity,
                            detected_at=now,
                        )
                        new_signals.append(signal)
                        state.drift_signals.append(signal)

            if new_signals:
                state.updated_at = now
                self._save()
                log.info(
                    "Detected %d drift signals for journey=%s",
                    len(new_signals), journey_id,
                )

        return new_signals

    def detect_drift_all(self) -> List[DriftSignal]:
        """Run drift detection across all completed journeys."""
        self._ensure_loaded()
        all_signals: List[DriftSignal] = []

        journey_ids = []
        with self._lock:
            journey_ids = [
                jid for jid, state in self._journeys.items()
                if state.completed and state.outcomes
            ]

        for jid in journey_ids:
            try:
                signals = self.detect_drift(jid)
                all_signals.extend(signals)
            except Exception as exc:
                log.debug("Drift detection failed for %s: %s", jid, exc)

        return all_signals

    def get_reservoir_state(self, tool_name: str) -> Optional[Dict]:
        """Get LF reservoir state for a tool (variance, deviation, step count)."""
        if not _LF_AVAILABLE:
            return None
        reservoir = self._reservoirs.get(tool_name)
        if not reservoir:
            return None
        return reservoir.to_dict()

    def apply_drift_corrections(self) -> List[Dict]:
        """Feed MODERATE/SEVERE drift signals back into learning.py to adjust scoring."""
        corrections = []
        try:
            from . import learning as _learning
        except ImportError:
            try:
                import learning as _learning
            except ImportError:
                log.debug("learning module not available for drift corrections")
                return corrections

        all_signals = self.detect_drift_all()
        for signal in all_signals:
            if signal.severity in (DriftSeverity.MODERATE.value, DriftSeverity.SEVERE.value):
                drift_magnitude = min(abs(signal.delta), 1.0)
                adjusted_quality = max(0.0, 1.0 - drift_magnitude * 0.5)
                try:
                    # Record as negative quality signal
                    fb = _learning._load_feedback()
                    fb.append({
                        "query": f"drift_correction:{signal.journey_id}",
                        "tool": signal.tool_name,
                        "rating": max(1, int(adjusted_quality * 10)),
                        "accepted": False,
                        "details": {
                            "source": "drift_correction",
                            "severity": signal.severity,
                            "dimension": signal.dimension,
                            "delta": signal.delta,
                        },
                    })
                    import json, os
                    fb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback.json")
                    with open(fb_path, "w") as f:
                        json.dump(fb, f, indent=2)
                    corrections.append({
                        "tool": signal.tool_name,
                        "severity": signal.severity,
                        "adjusted_quality": adjusted_quality,
                    })
                    log.info("Drift correction applied: %s severity=%s quality=%.2f",
                             signal.tool_name, signal.severity, adjusted_quality)
                except Exception as exc:
                    log.debug("Drift correction failed for %s: %s", signal.tool_name, exc)
        return corrections

    # ── Query & Dashboard ────────────────────────────────────────────

    def get_journey(self, journey_id: str) -> Optional[JourneyState]:
        """Retrieve a single journey by ID."""
        self._ensure_loaded()
        return self._journeys.get(journey_id)

    def get_user_journeys(self, user_id: str) -> List[JourneyState]:
        """Retrieve all journeys for a specific user."""
        self._ensure_loaded()
        return [
            j for j in self._journeys.values()
            if j.user_id == user_id
        ]

    def dashboard(self) -> JourneyDashboard:
        """Compute aggregate dashboard metrics."""
        self._ensure_loaded()

        journeys = list(self._journeys.values())
        if not journeys:
            return JourneyDashboard()

        active = [j for j in journeys if not j.completed]
        completed = [j for j in journeys if j.completed]

        # Satisfaction & ROI averages across all outcomes
        all_outcomes = []
        for j in journeys:
            all_outcomes.extend(j.outcomes)

        avg_sat = 0.0
        avg_roi = 0.0
        if all_outcomes:
            avg_sat = sum(o.satisfaction for o in all_outcomes) / len(all_outcomes)
            avg_roi = sum(o.roi for o in all_outcomes) / len(all_outcomes)

        # Stage distribution
        stage_dist: Dict[str, int] = {}
        for j in journeys:
            stage = j.current_stage
            stage_dist[stage] = stage_dist.get(stage, 0) + 1

        # Drift alert aggregation
        drift_count = sum(len(j.drift_signals) for j in journeys)

        # Top drift tools
        tool_drift: Dict[str, float] = {}
        for j in journeys:
            for sig in j.drift_signals:
                tool_drift[sig.tool_name] = tool_drift.get(sig.tool_name, 0) + abs(sig.delta)

        top_drift = sorted(
            [{"tool": k, "total_drift": round(v, 4)} for k, v in tool_drift.items()],
            key=lambda x: x["total_drift"],
            reverse=True,
        )[:10]

        return JourneyDashboard(
            total_journeys=len(journeys),
            active_journeys=len(active),
            completed_journeys=len(completed),
            avg_satisfaction=round(avg_sat, 4),
            avg_roi=round(avg_roi, 4),
            drift_alert_count=drift_count,
            stage_distribution=stage_dist,
            top_drift_tools=top_drift,
        )

    def list_journeys(
        self,
        stage: Optional[str] = None,
        completed: Optional[bool] = None,
        limit: int = 50,
    ) -> List[JourneyState]:
        """List journeys with optional filters."""
        self._ensure_loaded()
        results = list(self._journeys.values())

        if stage is not None:
            results = [j for j in results if j.current_stage == stage]
        if completed is not None:
            results = [j for j in results if j.completed == completed]

        # Sort by most recently updated
        results.sort(key=lambda j: j.updated_at or "", reverse=True)
        return results[:limit]


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

_oracle: Optional[JourneyOracle] = None
_oracle_lock = threading.Lock()


def get_oracle(data_dir: Optional[str] = None) -> JourneyOracle:
    """Return the singleton JourneyOracle instance."""
    global _oracle
    if _oracle is None:
        with _oracle_lock:
            if _oracle is None:
                _oracle = JourneyOracle(data_dir=data_dir)
    return _oracle


# ═══════════════════════════════════════════════════════════════════
# Module-Level Convenience Functions
# ═══════════════════════════════════════════════════════════════════

def create_journey(user_id: str, query: str = "", profile_id: Optional[str] = None) -> str:
    """Create a new journey. Returns journey_id."""
    return get_oracle().create_journey(user_id, query, profile_id)


def advance_journey(journey_id: str, stage: JourneyStage, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Advance a journey to the next stage. Returns journey state dict."""
    state = get_oracle().advance(journey_id, stage, metadata)
    return state.to_dict()


def record_outcome(
    journey_id: str,
    tool_name: str,
    satisfaction: float = 0.0,
    roi: float = 0.0,
    integration_success: float = 0.0,
    still_using: bool = True,
) -> Dict[str, Any]:
    """Record a tool outcome. Returns the outcome dict."""
    outcome = get_oracle().record_outcome(
        journey_id, tool_name, satisfaction, roi, integration_success, still_using,
    )
    return outcome.to_dict()


def detect_drift(journey_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Detect drift for a specific journey, or all completed journeys."""
    oracle = get_oracle()
    if journey_id:
        signals = oracle.detect_drift(journey_id)
    else:
        signals = oracle.detect_drift_all()
    return [s.to_dict() for s in signals]


def journey_dashboard() -> Dict[str, Any]:
    """Get aggregate journey dashboard metrics."""
    return get_oracle().dashboard().to_dict()


# ── Module load confirmation ─────────────────────────────────────────

log.info(
    "journey.py loaded — oracle ready, stages=%d, drift_thresholds=(%.2f/%.2f/%.2f)",
    len(JourneyStage),
    DRIFT_MILD_THRESHOLD,
    DRIFT_MODERATE_THRESHOLD,
    DRIFT_SEVERE_THRESHOLD,
)
