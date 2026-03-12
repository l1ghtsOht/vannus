# ────────────────────────────────────────────────────────────────────
# anti_patterns.py — TRAP Framework & Anti-Pattern Detection
# ────────────────────────────────────────────────────────────────────
"""
Implements anti-pattern detection from the Cognitive Resilience
blueprint: the TRAP Framework for multi-agent systems,
Vibe-Coding risk assessment, and Shadow AI prevention.

TRAP Anti-Patterns:
- **Bag of Agents**: Throwing agents at a problem without structured
  communication → diminishing returns, coordination overhead
- **Context Stuffing**: Overloading agent context windows with
  irrelevant information → diluted attention, hallucination
- **Sophistication Trap**: Using complex multi-agent orchestration
  for simple tasks → wasteful, slow, error-prone
- **AI Precision Anti-Pattern**: Trusting AI outputs without
  verification → compounding errors, false confidence

Vibe-Coding Risks:
- Interface flattening (loss of deep system understanding)
- Dependency on AI-generated code without comprehension
- Technical debt accumulation through unreviewed code
- Security blind spots from AI-generated configurations

Shadow AI:
- Unauthorized use of AI tools outside governance
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. TRAP ANTI-PATTERNS                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

class TrapType(str, Enum):
    BAG_OF_AGENTS = "bag_of_agents"
    CONTEXT_STUFFING = "context_stuffing"
    SOPHISTICATION_TRAP = "sophistication_trap"
    AI_PRECISION = "ai_precision"


TRAP_DESCRIPTIONS = {
    TrapType.BAG_OF_AGENTS: (
        "Multiple agents thrown at a problem without structured communication protocols. "
        "Results in coordination overhead exceeding productive work."
    ),
    TrapType.CONTEXT_STUFFING: (
        "Agent context windows overloaded with irrelevant information. "
        "Causes diluted attention, increased hallucination risk, and token waste."
    ),
    TrapType.SOPHISTICATION_TRAP: (
        "Complex multi-agent orchestration used for tasks achievable by simpler methods. "
        "Introduces unnecessary latency, cost, and failure modes."
    ),
    TrapType.AI_PRECISION: (
        "AI outputs trusted without verification or human review. "
        "Leads to compounding errors and false confidence in results."
    ),
}

TRAP_INDICATORS = {
    TrapType.BAG_OF_AGENTS: [
        "agent_count_high", "low_message_efficiency", "redundant_work",
        "no_communication_protocol", "unclear_agent_roles",
    ],
    TrapType.CONTEXT_STUFFING: [
        "context_near_limit", "irrelevant_context_ratio_high",
        "hallucination_rate_elevated", "retrieval_unused",
    ],
    TrapType.SOPHISTICATION_TRAP: [
        "simple_task_complex_pipeline", "latency_disproportionate",
        "cost_exceeds_value", "single_agent_sufficient",
    ],
    TrapType.AI_PRECISION: [
        "no_human_review", "no_test_coverage", "blind_deployment",
        "no_output_validation", "false_confidence_high",
    ],
}


@dataclass
class TrapDetection:
    """Detection result for a single TRAP anti-pattern."""
    trap_type: TrapType
    detected: bool
    severity: float          # 0.0 – 1.0
    indicators_found: List[str]
    indicators_total: int
    description: str
    remediation: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trap_type": self.trap_type.value,
            "detected": self.detected,
            "severity": round(self.severity, 4),
            "indicators_found": self.indicators_found,
            "indicators_total": self.indicators_total,
            "description": self.description,
            "remediation": self.remediation,
        }


TRAP_REMEDIATIONS = {
    TrapType.BAG_OF_AGENTS: [
        "Define explicit communication protocols between agents",
        "Assign clear roles with non-overlapping responsibilities",
        "Implement a coordinator agent with structured message passing",
        "Monitor agent utilization — remove underperforming agents",
    ],
    TrapType.CONTEXT_STUFFING: [
        "Implement retrieval filtering to inject only relevant context",
        "Monitor context window utilization vs. output quality",
        "Use summarization to compress context before injection",
        "Apply DSRP Distinctions to separate relevant from irrelevant",
    ],
    TrapType.SOPHISTICATION_TRAP: [
        "Assess task complexity BEFORE choosing architecture",
        "Use the reasoning router to match complexity to solution",
        "Start with simplest viable approach and scale up only if needed",
        "Track ROI: (quality improvement) / (added complexity cost)",
    ],
    TrapType.AI_PRECISION: [
        "Require human review for all production-impacting outputs",
        "Implement automated testing of AI-generated code/configs",
        "Add confidence calibration to all AI outputs",
        "Never deploy AI output without at least one verification step",
    ],
}


def detect_trap(
    trap_type: TrapType,
    observed_indicators: List[str],
) -> TrapDetection:
    """
    Detect a specific TRAP anti-pattern from observed indicators.

    Args:
        trap_type: Which TRAP pattern to check
        observed_indicators: List of indicator strings observed in the system
    """
    known_indicators = TRAP_INDICATORS.get(trap_type, [])
    found = [ind for ind in observed_indicators if ind in known_indicators]
    severity = len(found) / max(len(known_indicators), 1)
    detected = severity >= 0.4  # 40% of indicators present

    return TrapDetection(
        trap_type=trap_type,
        detected=detected,
        severity=severity,
        indicators_found=found,
        indicators_total=len(known_indicators),
        description=TRAP_DESCRIPTIONS.get(trap_type, ""),
        remediation=TRAP_REMEDIATIONS.get(trap_type, []) if detected else [],
    )


def scan_all_traps(
    observed_indicators: List[str],
) -> Dict[str, TrapDetection]:
    """Run TRAP detection for all four anti-patterns."""
    return {
        trap.value: detect_trap(trap, observed_indicators)
        for trap in TrapType
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. VIBE-CODING RISK ASSESSMENT                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

class VibeCodingRisk(str, Enum):
    INTERFACE_FLATTENING = "interface_flattening"
    DEPENDENCY_WITHOUT_COMPREHENSION = "dependency_without_comprehension"
    TECHNICAL_DEBT = "technical_debt"
    SECURITY_BLIND_SPOTS = "security_blind_spots"
    SKILL_ATROPHY = "skill_atrophy"


VIBE_RISK_DESCRIPTIONS = {
    VibeCodingRisk.INTERFACE_FLATTENING: (
        "Natural language interface flattens complex system interactions, "
        "hiding critical configuration details and edge cases."
    ),
    VibeCodingRisk.DEPENDENCY_WITHOUT_COMPREHENSION: (
        "Developers accept AI-generated code without understanding its "
        "logic, creating maintenance blind spots."
    ),
    VibeCodingRisk.TECHNICAL_DEBT: (
        "Rapid AI-assisted coding accumulates technical debt faster "
        "than traditional development — unreviewed patterns compound."
    ),
    VibeCodingRisk.SECURITY_BLIND_SPOTS: (
        "AI-generated configurations may include insecure defaults, "
        "missing headers, or improper input validation."
    ),
    VibeCodingRisk.SKILL_ATROPHY: (
        "Over-reliance on AI assistance causes developer skills to "
        "atrophy, reducing ability to debug or maintain systems."
    ),
}


@dataclass
class VibeCodingAssessment:
    """Assessment of vibe-coding risks in a project."""
    assessment_id: str
    project_description: str
    risks: List[Dict[str, Any]] = field(default_factory=list)
    overall_risk: float = 0.0
    risk_category: str = "low"
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "project_description": self.project_description[:200],
            "risks": self.risks,
            "overall_risk": round(self.overall_risk, 4),
            "risk_category": self.risk_category,
            "recommendations": self.recommendations,
        }


def assess_vibe_coding(
    project_description: str,
    ai_generated_ratio: float = 0.0,
    review_coverage: float = 1.0,
    test_coverage: float = 0.8,
    developer_experience_years: float = 5.0,
) -> VibeCodingAssessment:
    """
    Assess vibe-coding risks for a project.

    Args:
        project_description: Description of the project
        ai_generated_ratio: Fraction of code that is AI-generated (0.0–1.0)
        review_coverage: Fraction of AI code that has been human-reviewed (0.0–1.0)
        test_coverage: Test coverage ratio (0.0–1.0)
        developer_experience_years: Average years of experience
    """
    assess_id = hashlib.md5(f"{project_description}{time.time()}".encode()).hexdigest()[:12]

    risks: List[Dict[str, Any]] = []

    # Interface flattening risk
    flattening_risk = ai_generated_ratio * 0.6 + (1.0 - review_coverage) * 0.4
    risks.append({
        "risk": VibeCodingRisk.INTERFACE_FLATTENING.value,
        "score": round(flattening_risk, 4),
        "description": VIBE_RISK_DESCRIPTIONS[VibeCodingRisk.INTERFACE_FLATTENING],
    })

    # Dependency without comprehension
    dep_risk = ai_generated_ratio * 0.5 + (1.0 - review_coverage) * 0.5
    risks.append({
        "risk": VibeCodingRisk.DEPENDENCY_WITHOUT_COMPREHENSION.value,
        "score": round(dep_risk, 4),
        "description": VIBE_RISK_DESCRIPTIONS[VibeCodingRisk.DEPENDENCY_WITHOUT_COMPREHENSION],
    })

    # Technical debt
    debt_risk = ai_generated_ratio * 0.4 + (1.0 - test_coverage) * 0.4 + (1.0 - review_coverage) * 0.2
    risks.append({
        "risk": VibeCodingRisk.TECHNICAL_DEBT.value,
        "score": round(debt_risk, 4),
        "description": VIBE_RISK_DESCRIPTIONS[VibeCodingRisk.TECHNICAL_DEBT],
    })

    # Security blind spots
    security_risk = ai_generated_ratio * 0.5 + (1.0 - test_coverage) * 0.3 + (1.0 - review_coverage) * 0.2
    risks.append({
        "risk": VibeCodingRisk.SECURITY_BLIND_SPOTS.value,
        "score": round(security_risk, 4),
        "description": VIBE_RISK_DESCRIPTIONS[VibeCodingRisk.SECURITY_BLIND_SPOTS],
    })

    # Skill atrophy
    experience_factor = max(0.0, 1.0 - developer_experience_years / 10.0)
    atrophy_risk = ai_generated_ratio * 0.6 * experience_factor
    risks.append({
        "risk": VibeCodingRisk.SKILL_ATROPHY.value,
        "score": round(atrophy_risk, 4),
        "description": VIBE_RISK_DESCRIPTIONS[VibeCodingRisk.SKILL_ATROPHY],
    })

    overall = sum(r["score"] for r in risks) / max(len(risks), 1)

    if overall < 0.2:
        category = "low"
    elif overall < 0.4:
        category = "moderate"
    elif overall < 0.6:
        category = "high"
    else:
        category = "critical"

    recs: List[str] = []
    if review_coverage < 0.8:
        recs.append(f"Increase human review coverage from {review_coverage:.0%} to ≥80%")
    if test_coverage < 0.7:
        recs.append(f"Increase test coverage from {test_coverage:.0%} to ≥70%")
    if ai_generated_ratio > 0.5:
        recs.append("Consider reducing AI-generation ratio or adding comprehensive review gates")
    if experience_factor > 0.5:
        recs.append("Pair junior developers with seniors when using AI code generation")

    return VibeCodingAssessment(
        assessment_id=assess_id,
        project_description=project_description,
        risks=risks,
        overall_risk=overall,
        risk_category=category,
        recommendations=recs,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. SHADOW AI DETECTION                                         ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class ShadowAIIndicator:
    """An indicator of unauthorized AI tool usage."""
    indicator_type: str
    description: str
    severity: float   # 0.0 – 1.0
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_type": self.indicator_type,
            "description": self.description,
            "severity": round(self.severity, 4),
            "evidence": self.evidence,
        }


SHADOW_AI_PATTERNS = [
    {"pattern": r"(?:chatgpt|claude|gemini|copilot)\s*(?:generated|wrote|created)",
     "type": "ai_attribution_comment",
     "description": "Code comment attributing authorship to external AI",
     "severity": 0.6},
    {"pattern": r"# ?TODO:?\s*(?:ai|gpt|llm)\s",
     "type": "ai_todo_marker",
     "description": "TODO marker referencing AI assistance",
     "severity": 0.4},
    {"pattern": r"(?:openai|anthropic|google)\.(?:api|key|token)",
     "type": "unauthorized_api_reference",
     "description": "Reference to AI provider API outside approved channels",
     "severity": 0.8},
]


@dataclass
class ShadowAIReport:
    """Report of shadow AI detection scan."""
    report_id: str
    files_scanned: int
    indicators: List[ShadowAIIndicator] = field(default_factory=list)
    overall_risk: float = 0.0
    shadow_ai_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "files_scanned": self.files_scanned,
            "indicators": [i.to_dict() for i in self.indicators],
            "overall_risk": round(self.overall_risk, 4),
            "shadow_ai_detected": self.shadow_ai_detected,
        }


def scan_for_shadow_ai(
    code_snippets: List[str],
) -> ShadowAIReport:
    """
    Scan code snippets for indicators of unauthorized AI tool usage.

    Args:
        code_snippets: List of code text blocks to analyze
    """
    report_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]

    indicators: List[ShadowAIIndicator] = []

    for snippet in code_snippets:
        lower = snippet.lower()
        for pat_def in SHADOW_AI_PATTERNS:
            if re.search(pat_def["pattern"], lower):
                indicators.append(ShadowAIIndicator(
                    indicator_type=pat_def["type"],
                    description=pat_def["description"],
                    severity=pat_def["severity"],
                    evidence=snippet[:200],
                ))

    overall = max((i.severity for i in indicators), default=0.0)
    detected = len(indicators) > 0

    return ShadowAIReport(
        report_id=report_id,
        files_scanned=len(code_snippets),
        indicators=indicators,
        overall_risk=overall,
        shadow_ai_detected=detected,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def anti_patterns_summary() -> Dict[str, Any]:
    """Return a summary of the anti-pattern detection engine."""
    return {
        "trap_framework": {
            "patterns": {t.value: TRAP_DESCRIPTIONS[t][:80] for t in TrapType},
            "detection_threshold": 0.4,
        },
        "vibe_coding": {
            "risks": [r.value for r in VibeCodingRisk],
            "categories": ["low", "moderate", "high", "critical"],
        },
        "shadow_ai": {
            "pattern_count": len(SHADOW_AI_PATTERNS),
            "detection_types": [p["type"] for p in SHADOW_AI_PATTERNS],
        },
    }
