# ────────────────────────────────────────────────────────────────────
# dsrp_ontology.py — DSRP Theory & O-Theory Structural Ontology
# ────────────────────────────────────────────────────────────────────
"""
Implements the four universal DSRP patterns (Distinctions, Systems,
Relationships, Perspectives) and O-Theory integration from the
Cognitive Resilience blueprint.

DSRP Theory:
- **Distinctions (D)**: Identity (i) and Other (o) — defining boundaries
- **Systems (S)**: Part (p) and Whole (w) — part-whole configurations
- **Relationships (R)**: Action (a) and Reaction (r) — causal links
- **Perspectives (P)**: Point (ρ) and View (v) — observational frames

O-Theory:
- Law of Structural Cognition: M = I · O
- Love Reality Loop: lim(t→∞) Mₜ/ℝ = 1

The DSRP matrix is enforced as a pre-execution filter: all AI agent
tasks must pass through structural validation before execution.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. DSRP PATTERNS                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

class DSRPPattern(str, Enum):
    DISTINCTION = "distinction"
    SYSTEM = "system"
    RELATIONSHIP = "relationship"
    PERSPECTIVE = "perspective"


@dataclass
class Distinction:
    """D-pattern: defines what something IS and what it is NOT."""
    identity: str          # what the entity is
    other: str             # what it explicitly is NOT
    boundary: str = ""     # description of the boundary
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": "distinction",
            "identity": self.identity,
            "other": self.other,
            "boundary": self.boundary,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class System:
    """S-pattern: part-whole configuration."""
    whole: str
    parts: List[str] = field(default_factory=list)
    organization: str = ""   # how parts relate to form the whole

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": "system",
            "whole": self.whole,
            "parts": self.parts,
            "organization": self.organization,
            "part_count": len(self.parts),
        }


@dataclass
class Relationship:
    """R-pattern: directional causal or dependency link."""
    source: str
    target: str
    action: str        # what the source does to the target
    reaction: str = "" # how the target responds
    strength: float = 1.0  # 0.0 – 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": "relationship",
            "source": self.source,
            "target": self.target,
            "action": self.action,
            "reaction": self.reaction,
            "strength": round(self.strength, 4),
        }


@dataclass
class Perspective:
    """P-pattern: observational frame."""
    point: str         # the observer or reference point (ρ)
    view: str          # what is seen from that point (v)
    bias_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": "perspective",
            "point": self.point,
            "view": self.view,
            "bias_notes": self.bias_notes,
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. DSRP MATRIX — Pre-Execution Structural Validation            ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class DSRPMatrix:
    """
    A complete DSRP structural analysis of a task or request.

    Before any AI agent is permitted to execute a task, generate code,
    or modify a database, the platform MUST force the agent to
    explicitly process the request through this matrix.
    """
    task_id: str
    task_description: str
    distinctions: List[Distinction] = field(default_factory=list)
    systems: List[System] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    perspectives: List[Perspective] = field(default_factory=list)
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def validate(self) -> bool:
        """
        Validate structural completeness. A valid matrix requires
        at least one of each DSRP pattern filled in.
        """
        errors: List[str] = []
        if not self.distinctions:
            errors.append("Missing Distinction: task scope/boundary not defined")
        if not self.systems:
            errors.append("Missing System: part-whole decomposition not provided")
        if not self.relationships:
            errors.append("Missing Relationship: no causal/dependency links identified")
        if not self.perspectives:
            errors.append("Missing Perspective: no observational frame specified")
        self.validation_errors = errors
        self.validation_passed = len(errors) == 0
        return self.validation_passed

    def completeness_score(self) -> float:
        """0.0 – 1.0 measure of structural completeness."""
        filled = sum([
            1 if self.distinctions else 0,
            1 if self.systems else 0,
            1 if self.relationships else 0,
            1 if self.perspectives else 0,
        ])
        return filled / 4.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "distinctions": [d.to_dict() for d in self.distinctions],
            "systems": [s.to_dict() for s in self.systems],
            "relationships": [r.to_dict() for r in self.relationships],
            "perspectives": [p.to_dict() for p in self.perspectives],
            "validation_passed": self.validation_passed,
            "validation_errors": self.validation_errors,
            "completeness_score": round(self.completeness_score(), 4),
            "created_at": self.created_at,
        }


def build_dsrp_matrix(
    task_description: str,
    *,
    distinctions: Optional[List[Dict[str, str]]] = None,
    systems: Optional[List[Dict[str, Any]]] = None,
    relationships: Optional[List[Dict[str, str]]] = None,
    perspectives: Optional[List[Dict[str, str]]] = None,
) -> DSRPMatrix:
    """
    Build and validate a DSRP matrix from raw inputs.

    Parameters accept dicts that will be converted to the appropriate
    DSRP dataclass instances.
    """
    task_id = hashlib.md5(task_description.encode()).hexdigest()[:12]

    d_list = [Distinction(
        identity=d.get("identity", ""),
        other=d.get("other", ""),
        boundary=d.get("boundary", ""),
        confidence=d.get("confidence", 1.0),
    ) for d in (distinctions or [])]

    s_list = [System(
        whole=s.get("whole", ""),
        parts=s.get("parts", []),
        organization=s.get("organization", ""),
    ) for s in (systems or [])]

    r_list = [Relationship(
        source=r.get("source", ""),
        target=r.get("target", ""),
        action=r.get("action", ""),
        reaction=r.get("reaction", ""),
        strength=r.get("strength", 1.0),
    ) for r in (relationships or [])]

    p_list = [Perspective(
        point=p.get("point", ""),
        view=p.get("view", ""),
        bias_notes=p.get("bias_notes", ""),
    ) for p in (perspectives or [])]

    matrix = DSRPMatrix(
        task_id=task_id,
        task_description=task_description,
        distinctions=d_list,
        systems=s_list,
        relationships=r_list,
        perspectives=p_list,
    )
    matrix.validate()
    return matrix


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. O-THEORY — Organization Theory                              ║
# ╚════════════════════════════════════════════════════════════════════╝

def structural_cognition(information: float, organization: float) -> float:
    """
    Compute cognitive complexity via O-Theory:
        M = I · O
    Cognitive Complexity = Information × Organization
    """
    return information * organization


def love_reality_loop(
    mental_model_fidelity: float,
    reality_fidelity: float,
) -> Dict[str, Any]:
    """
    Evaluate the Love Reality Loop convergence.

    The LRL describes recursive alignment between mental models (M)
    and real-world structures (ℝ): lim(t→∞) Mₜ/ℝ = 1.

    Args:
        mental_model_fidelity: 0.0 – 1.0 quality of the AI's internal model
        reality_fidelity: 0.0 – 1.0 quality of ground truth representation

    Returns alignment metrics.
    """
    if reality_fidelity <= 0:
        ratio = 0.0
    else:
        ratio = min(2.0, mental_model_fidelity / reality_fidelity)

    convergence = 1.0 - abs(1.0 - ratio)
    aligned = convergence >= 0.85

    return {
        "mental_model_fidelity": round(mental_model_fidelity, 4),
        "reality_fidelity": round(reality_fidelity, 4),
        "m_over_r_ratio": round(ratio, 4),
        "convergence": round(convergence, 4),
        "aligned": aligned,
        "recommendation": (
            "Models are well-aligned with reality" if aligned
            else "Structural refinement needed to close M/ℝ gap"
        ),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. SEMANTIC HEURISTIC EXTRACTION                                ║
# ╚════════════════════════════════════════════════════════════════════╝

# Common perspective viewpoints for code generation
STANDARD_PERSPECTIVES = [
    {"point": "end_user", "view": "usability, accessibility, performance"},
    {"point": "security_auditor", "view": "attack surface, input validation, secrets management"},
    {"point": "database_admin", "view": "schema design, query efficiency, data integrity"},
    {"point": "devops_engineer", "view": "deployment, monitoring, scalability"},
    {"point": "compliance_officer", "view": "regulatory adherence, audit trail, data privacy"},
]


def auto_perspectives(task_description: str) -> List[Perspective]:
    """
    Automatically generate relevant perspectives for a task.
    Uses keyword matching to select from standard viewpoints.
    """
    lower = task_description.lower()
    selected: List[Perspective] = []

    keyword_map = {
        "end_user": ["user", "ui", "frontend", "interface", "ux", "button", "form"],
        "security_auditor": ["security", "auth", "password", "token", "encrypt", "secret", "api key"],
        "database_admin": ["database", "sql", "query", "schema", "migration", "table", "index"],
        "devops_engineer": ["deploy", "docker", "ci/cd", "pipeline", "kubernetes", "monitor", "scale"],
        "compliance_officer": ["compliance", "gdpr", "hipaa", "audit", "regulation", "privacy", "pci"],
    }

    for sp in STANDARD_PERSPECTIVES:
        point = sp["point"]
        keywords = keyword_map.get(point, [])
        if any(kw in lower for kw in keywords):
            selected.append(Perspective(point=point, view=sp["view"]))

    # Always include at least one perspective
    if not selected:
        selected.append(Perspective(
            point="system_architect",
            view="structural integrity, modularity, extensibility",
        ))

    return selected


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def dsrp_summary() -> Dict[str, Any]:
    """Return a summary of the DSRP ontology engine."""
    return {
        "patterns": {
            "distinction": {"elements": ["identity", "other"], "function": "define boundaries"},
            "system": {"elements": ["part", "whole"], "function": "part-whole decomposition"},
            "relationship": {"elements": ["action", "reaction"], "function": "causal links"},
            "perspective": {"elements": ["point", "view"], "function": "observational frames"},
        },
        "o_theory": {
            "law": "M = I × O",
            "description": "Cognitive Complexity = Information × Organization",
            "love_reality_loop": "lim(t→∞) Mₜ/ℝ = 1",
        },
        "standard_perspectives": [p["point"] for p in STANDARD_PERSPECTIVES],
    }
