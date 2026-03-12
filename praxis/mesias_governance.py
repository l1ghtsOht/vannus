# ────────────────────────────────────────────────────────────────────
# mesias_governance.py — MESIAS Governance Framework
# ────────────────────────────────────────────────────────────────────
"""
Implements the MESIAS (Monitoring, Evaluation, Supervision,
Intervention, Auditing, and Security) governance framework from
the Cognitive Resilience blueprint.

Core Capabilities:
- **Ethical Evaluation**: Score AI actions across ethical dimensions
- **Risk-Based Scoring**: Weighted risk assessment for AI operations
- **Value-Sensitive Design (VSD)**: Embed stakeholder values into
  evaluation criteria
- **Governance Workspace**: Structured decision logging and audit trail
- **Compliance Dashboards**: Real-time governance health metrics
- **Efficiency Benchmarks**: 41.8% non-functional overhead reduction target
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. ETHICAL EVALUATION                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

class EthicalDimension(str, Enum):
    AUTONOMY = "autonomy"             # respect for human decision-making
    BENEFICENCE = "beneficence"       # do good / maximize benefit
    NON_MALEFICENCE = "non_maleficence"  # do no harm
    JUSTICE = "justice"               # fairness and equity
    TRANSPARENCY = "transparency"     # explainability and openness
    ACCOUNTABILITY = "accountability" # clear responsibility chains
    PRIVACY = "privacy"              # data protection and consent


DIMENSION_WEIGHTS = {
    EthicalDimension.AUTONOMY: 0.15,
    EthicalDimension.BENEFICENCE: 0.15,
    EthicalDimension.NON_MALEFICENCE: 0.20,  # highest — primum non nocere
    EthicalDimension.JUSTICE: 0.15,
    EthicalDimension.TRANSPARENCY: 0.10,
    EthicalDimension.ACCOUNTABILITY: 0.10,
    EthicalDimension.PRIVACY: 0.15,
}


@dataclass
class EthicalScore:
    """Score for a single ethical dimension."""
    dimension: EthicalDimension
    score: float          # 0.0 – 1.0
    weight: float         # dimension weight
    evidence: str = ""    # supporting evidence for the score
    flags: List[str] = field(default_factory=list)

    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 4),
            "weight": round(self.weight, 4),
            "weighted_score": round(self.weighted_score(), 4),
            "evidence": self.evidence,
            "flags": self.flags,
        }


@dataclass
class EthicalEvaluation:
    """Complete ethical evaluation of an AI action or system."""
    evaluation_id: str
    subject: str              # what is being evaluated
    scores: List[EthicalScore] = field(default_factory=list)
    overall_score: float = 0.0
    pass_threshold: float = 0.6
    passed: bool = False
    critical_failures: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "subject": self.subject,
            "scores": [s.to_dict() for s in self.scores],
            "overall_score": round(self.overall_score, 4),
            "pass_threshold": self.pass_threshold,
            "passed": self.passed,
            "critical_failures": self.critical_failures,
            "timestamp": self.timestamp,
        }


def evaluate_ethics(
    subject: str,
    dimension_scores: Dict[str, float],
    pass_threshold: float = 0.6,
) -> EthicalEvaluation:
    """
    Perform ethical evaluation across all dimensions.

    Args:
        subject: Description of what is being evaluated
        dimension_scores: Dict mapping dimension names to 0.0–1.0 scores
        pass_threshold: Minimum overall score to pass (default 0.6)
    """
    eval_id = hashlib.md5(f"{subject}{time.time()}".encode()).hexdigest()[:12]

    scores: List[EthicalScore] = []
    critical: List[str] = []

    for dim in EthicalDimension:
        raw = dimension_scores.get(dim.value, 0.5)
        raw = max(0.0, min(1.0, raw))
        weight = DIMENSION_WEIGHTS.get(dim, 1.0 / len(EthicalDimension))

        flags: List[str] = []
        if raw < 0.3:
            flags.append(f"CRITICAL: {dim.value} score dangerously low ({raw:.2f})")
            critical.append(f"{dim.value}: {raw:.2f}")
        elif raw < 0.5:
            flags.append(f"WARNING: {dim.value} score below acceptable ({raw:.2f})")

        scores.append(EthicalScore(
            dimension=dim,
            score=raw,
            weight=weight,
            evidence=f"Evaluated for subject: {subject[:100]}",
            flags=flags,
        ))

    overall = sum(s.weighted_score() for s in scores)
    passed = overall >= pass_threshold and len(critical) == 0

    return EthicalEvaluation(
        evaluation_id=eval_id,
        subject=subject,
        scores=scores,
        overall_score=overall,
        pass_threshold=pass_threshold,
        passed=passed,
        critical_failures=critical,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. RISK-BASED SCORING                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

class RiskLevel(str, Enum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment for an AI operation."""
    assessment_id: str
    operation: str
    risk_level: RiskLevel
    risk_score: float         # 0.0 – 1.0
    impact_score: float       # severity if risk materializes
    likelihood_score: float   # probability of risk materializing
    mitigations: List[str] = field(default_factory=list)
    residual_risk: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "operation": self.operation,
            "risk_level": self.risk_level.value,
            "risk_score": round(self.risk_score, 4),
            "impact_score": round(self.impact_score, 4),
            "likelihood_score": round(self.likelihood_score, 4),
            "mitigations": self.mitigations,
            "residual_risk": round(self.residual_risk, 4),
        }


def assess_risk(
    operation: str,
    impact: float,
    likelihood: float,
    existing_mitigations: Optional[List[str]] = None,
) -> RiskAssessment:
    """
    Perform risk-based scoring for an AI operation.

    Risk = Impact × Likelihood, reduced by mitigations.
    """
    assess_id = hashlib.md5(f"{operation}{time.time()}".encode()).hexdigest()[:12]

    impact = max(0.0, min(1.0, impact))
    likelihood = max(0.0, min(1.0, likelihood))
    raw_risk = impact * likelihood

    # Each mitigation reduces risk by ~15%
    mitigations = existing_mitigations or []
    mitigation_factor = max(0.1, 1.0 - len(mitigations) * 0.15)
    residual = raw_risk * mitigation_factor

    if residual < 0.1:
        level = RiskLevel.MINIMAL
    elif residual < 0.25:
        level = RiskLevel.LOW
    elif residual < 0.5:
        level = RiskLevel.MEDIUM
    elif residual < 0.75:
        level = RiskLevel.HIGH
    else:
        level = RiskLevel.CRITICAL

    return RiskAssessment(
        assessment_id=assess_id,
        operation=operation,
        risk_level=level,
        risk_score=raw_risk,
        impact_score=impact,
        likelihood_score=likelihood,
        mitigations=mitigations,
        residual_risk=residual,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. VALUE-SENSITIVE DESIGN (VSD)                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class StakeholderValue:
    """A value held by a stakeholder group."""
    stakeholder: str
    value_name: str
    importance: float       # 0.0 – 1.0
    current_satisfaction: float  # 0.0 – 1.0
    description: str = ""

    def gap(self) -> float:
        """How much the current state falls short of the value's importance."""
        return max(0.0, self.importance - self.current_satisfaction)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stakeholder": self.stakeholder,
            "value_name": self.value_name,
            "importance": round(self.importance, 4),
            "current_satisfaction": round(self.current_satisfaction, 4),
            "gap": round(self.gap(), 4),
            "description": self.description,
        }


@dataclass
class VSDAnalysis:
    """Value-Sensitive Design analysis aggregating stakeholder values."""
    analysis_id: str
    values: List[StakeholderValue] = field(default_factory=list)
    overall_satisfaction: float = 0.0
    largest_gap: str = ""
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "values": [v.to_dict() for v in self.values],
            "overall_satisfaction": round(self.overall_satisfaction, 4),
            "largest_gap": self.largest_gap,
            "recommendations": self.recommendations,
        }


def analyze_vsd(
    stakeholder_values: List[Dict[str, Any]],
) -> VSDAnalysis:
    """
    Perform Value-Sensitive Design analysis.

    Args:
        stakeholder_values: List of dicts with keys:
            stakeholder, value_name, importance, current_satisfaction
    """
    analysis_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]

    values: List[StakeholderValue] = []
    for sv in stakeholder_values:
        values.append(StakeholderValue(
            stakeholder=sv.get("stakeholder", "unknown"),
            value_name=sv.get("value_name", "unnamed"),
            importance=sv.get("importance", 0.5),
            current_satisfaction=sv.get("current_satisfaction", 0.5),
            description=sv.get("description", ""),
        ))

    if not values:
        return VSDAnalysis(analysis_id=analysis_id)

    overall = sum(v.current_satisfaction * v.importance for v in values) / sum(v.importance for v in values)

    largest_gap_val = max(values, key=lambda v: v.gap())
    largest_gap = f"{largest_gap_val.stakeholder}: {largest_gap_val.value_name} (gap: {largest_gap_val.gap():.2f})"

    recs: List[str] = []
    for v in sorted(values, key=lambda x: x.gap(), reverse=True)[:3]:
        if v.gap() > 0.2:
            recs.append(
                f"Address {v.value_name} for {v.stakeholder} — "
                f"importance {v.importance:.0%} but satisfaction only {v.current_satisfaction:.0%}"
            )

    return VSDAnalysis(
        analysis_id=analysis_id,
        values=values,
        overall_satisfaction=overall,
        largest_gap=largest_gap,
        recommendations=recs,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. GOVERNANCE WORKSPACE — Decision Logging                     ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class GovernanceDecision:
    """A logged governance decision."""
    decision_id: str
    title: str
    description: str
    decision_maker: str
    ethical_score: Optional[float] = None
    risk_level: Optional[str] = None
    outcome: str = "pending"
    rationale: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "description": self.description[:200],
            "decision_maker": self.decision_maker,
            "ethical_score": round(self.ethical_score, 4) if self.ethical_score else None,
            "risk_level": self.risk_level,
            "outcome": self.outcome,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
        }


class GovernanceWorkspace:
    """Structured decision logging and audit trail."""

    def __init__(self):
        self.decisions: List[GovernanceDecision] = []
        self.audit_log: List[Dict[str, Any]] = []

    def log_decision(
        self,
        title: str,
        description: str,
        decision_maker: str,
        ethical_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        rationale: str = "",
    ) -> GovernanceDecision:
        dec_id = hashlib.md5(f"{title}{time.time()}".encode()).hexdigest()[:12]
        decision = GovernanceDecision(
            decision_id=dec_id,
            title=title,
            description=description,
            decision_maker=decision_maker,
            ethical_score=ethical_score,
            risk_level=risk_level,
            rationale=rationale,
        )
        self.decisions.append(decision)
        self.audit_log.append({
            "event": "decision_logged",
            "decision_id": dec_id,
            "timestamp": time.time(),
        })
        return decision

    def resolve_decision(self, decision_id: str, outcome: str) -> Optional[GovernanceDecision]:
        for dec in self.decisions:
            if dec.decision_id == decision_id:
                dec.outcome = outcome
                self.audit_log.append({
                    "event": "decision_resolved",
                    "decision_id": decision_id,
                    "outcome": outcome,
                    "timestamp": time.time(),
                })
                return dec
        return None

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return list(self.audit_log)

    def status(self) -> Dict[str, Any]:
        pending = sum(1 for d in self.decisions if d.outcome == "pending")
        resolved = sum(1 for d in self.decisions if d.outcome != "pending")
        return {
            "total_decisions": len(self.decisions),
            "pending": pending,
            "resolved": resolved,
            "audit_events": len(self.audit_log),
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. EFFICIENCY BENCHMARKS                                       ║
# ╚════════════════════════════════════════════════════════════════════╝

# Target: 41.8% reduction in non-functional overhead (from blueprint)
EFFICIENCY_TARGET = 0.418


@dataclass
class EfficiencyMetrics:
    """Measure governance overhead and efficiency."""
    total_operations: int
    governance_overhead_ms: float    # total time in governance checks
    operation_time_ms: float         # total time in actual operations
    overhead_ratio: float            # governance / total
    target_ratio: float = 1.0 - EFFICIENCY_TARGET
    within_target: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_operations": self.total_operations,
            "governance_overhead_ms": round(self.governance_overhead_ms, 2),
            "operation_time_ms": round(self.operation_time_ms, 2),
            "overhead_ratio": round(self.overhead_ratio, 4),
            "target_ratio": round(self.target_ratio, 4),
            "within_target": self.within_target,
            "efficiency_improvement_needed": round(
                max(0, self.overhead_ratio - self.target_ratio), 4
            ),
        }


def measure_efficiency(
    total_operations: int,
    governance_overhead_ms: float,
    operation_time_ms: float,
) -> EfficiencyMetrics:
    """Compute governance efficiency metrics against the 41.8% target."""
    total_time = governance_overhead_ms + operation_time_ms
    ratio = governance_overhead_ms / total_time if total_time > 0 else 0.0
    target = 1.0 - EFFICIENCY_TARGET

    return EfficiencyMetrics(
        total_operations=total_operations,
        governance_overhead_ms=governance_overhead_ms,
        operation_time_ms=operation_time_ms,
        overhead_ratio=ratio,
        target_ratio=target,
        within_target=ratio <= target,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def mesias_summary() -> Dict[str, Any]:
    """Return a summary of the MESIAS governance framework."""
    return {
        "ethical_dimensions": [d.value for d in EthicalDimension],
        "dimension_weights": {d.value: w for d, w in DIMENSION_WEIGHTS.items()},
        "risk_levels": [r.value for r in RiskLevel],
        "vsd": {
            "description": "Value-Sensitive Design — embed stakeholder values into evaluation",
            "analysis_type": "gap analysis between importance and satisfaction",
        },
        "governance_workspace": {
            "capabilities": ["decision logging", "audit trail", "outcome tracking"],
        },
        "efficiency_target": f"{EFFICIENCY_TARGET:.1%} non-functional overhead reduction",
        "pass_threshold": 0.6,
    }
