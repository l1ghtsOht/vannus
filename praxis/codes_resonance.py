# ────────────────────────────────────────────────────────────────────
# codes_resonance.py — CODES Resonance Framework
# ────────────────────────────────────────────────────────────────────
"""
Implements the CODES (Chirality, Organization, Dynamics, Evolution,
Synergy) Resonance Framework from the Cognitive Resilience blueprint.

Key Concepts:
- **Chirality**: Structural handedness — detecting whether system
  components have non-superimposable mirror symmetry
- **Prime-Structured Resonance**: Using prime-based patterns to
  identify fundamental frequencies in system behavior
- **SCNT² (Super-Connected Network Theory Squared)**: Network
  topology metrics for agent communication graphs
- **7P-MCST Model**: People, Process, Product, Platform, Performance,
  Protection, Perspective — multi-criteria scoring
- **Autopoiesis**: Self-maintaining system boundary detection
- **Coherence Gradients**: Measuring alignment across subsystems
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. CHIRALITY ANALYSIS                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

class ChiralityType(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    ACHIRAL = "achiral"  # symmetric / superimposable


@dataclass
class ChiralityAssessment:
    """Assess structural handedness of a system component."""
    component_id: str
    chirality: ChiralityType
    asymmetry_score: float           # 0.0 (achiral) – 1.0 (maximally chiral)
    mirror_component: Optional[str]  # ID of the mirror counterpart, if any
    implications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "chirality": self.chirality.value,
            "asymmetry_score": round(self.asymmetry_score, 4),
            "mirror_component": self.mirror_component,
            "implications": self.implications,
        }


def assess_chirality(
    component_a: Dict[str, Any],
    component_b: Dict[str, Any],
) -> ChiralityAssessment:
    """
    Compare two system components for structural chirality.

    Chirality is detected when two components share the same interface
    but implement fundamentally non-interchangeable behaviors (like
    left and right hands).
    """
    a_keys = set(component_a.keys())
    b_keys = set(component_b.keys())

    shared = a_keys & b_keys
    total = a_keys | b_keys
    structural_similarity = len(shared) / max(len(total), 1)

    # Check value differences for shared keys
    value_diffs = 0
    for k in shared:
        if component_a[k] != component_b[k]:
            value_diffs += 1
    value_asymmetry = value_diffs / max(len(shared), 1)

    # Chirality: high structural similarity but high value asymmetry
    asymmetry = value_asymmetry * structural_similarity
    if asymmetry < 0.2:
        chirality = ChiralityType.ACHIRAL
    elif value_asymmetry > 0.5:
        chirality = ChiralityType.LEFT  # arbitrary assignment
    else:
        chirality = ChiralityType.RIGHT

    implications = []
    if chirality != ChiralityType.ACHIRAL:
        implications.append("Components are structurally similar but functionally non-interchangeable")
        implications.append("Ensure both orientations are tested independently")

    return ChiralityAssessment(
        component_id=component_a.get("id", "component_a"),
        chirality=chirality,
        asymmetry_score=round(asymmetry, 4),
        mirror_component=component_b.get("id", "component_b"),
        implications=implications,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. PRIME-STRUCTURED RESONANCE                                   ║
# ╚════════════════════════════════════════════════════════════════════╝

def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _primes_up_to(limit: int) -> List[int]:
    return [n for n in range(2, limit + 1) if _is_prime(n)]


@dataclass
class ResonanceProfile:
    """Prime-structured resonance analysis of system behaviour."""
    system_id: str
    signal_length: int
    prime_harmonics: List[int]        # primes that divide signal cycles
    resonance_strength: float         # 0.0 – 1.0
    fundamental_frequency: int        # dominant prime factor
    harmonic_series: List[float]      # normalized harmonic amplitudes
    coherent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "signal_length": self.signal_length,
            "prime_harmonics": self.prime_harmonics,
            "resonance_strength": round(self.resonance_strength, 4),
            "fundamental_frequency": self.fundamental_frequency,
            "harmonic_series": [round(h, 4) for h in self.harmonic_series],
            "coherent": self.coherent,
        }


def compute_resonance(
    signal: List[float],
    system_id: str = "default",
) -> ResonanceProfile:
    """
    Analyze a numeric signal for prime-structured resonance patterns.

    Identifies prime harmonics in the signal length and computes
    resonance strength based on how many prime factors divide evenly
    into behavioral cycles.
    """
    n = len(signal)
    if n == 0:
        return ResonanceProfile(
            system_id=system_id,
            signal_length=0,
            prime_harmonics=[],
            resonance_strength=0.0,
            fundamental_frequency=0,
            harmonic_series=[],
            coherent=False,
        )

    # Find prime factors of signal length
    primes = _primes_up_to(n)
    harmonics = [p for p in primes if n % p == 0]

    # Compute harmonic amplitudes (simplified DFT at prime frequencies)
    harmonic_amplitudes: List[float] = []
    for p in harmonics[:8]:  # limit to first 8 for performance
        # Compute amplitude at frequency 1/p
        real_sum = sum(signal[i] * math.cos(2 * math.pi * i / p) for i in range(n))
        imag_sum = sum(signal[i] * math.sin(2 * math.pi * i / p) for i in range(n))
        amplitude = math.sqrt(real_sum ** 2 + imag_sum ** 2) / n
        harmonic_amplitudes.append(amplitude)

    # Normalize
    max_amp = max(harmonic_amplitudes) if harmonic_amplitudes else 1.0
    normalized = [a / max_amp if max_amp > 0 else 0.0 for a in harmonic_amplitudes]

    # Resonance strength: average of top harmonics
    resonance = sum(normalized) / max(len(normalized), 1)

    fundamental = harmonics[0] if harmonics else 1

    return ResonanceProfile(
        system_id=system_id,
        signal_length=n,
        prime_harmonics=harmonics,
        resonance_strength=resonance,
        fundamental_frequency=fundamental,
        harmonic_series=normalized,
        coherent=resonance >= 0.6,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. SCNT² — Super-Connected Network Theory Squared               ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class NetworkTopology:
    """SCNT² metrics for an agent communication graph."""
    nodes: int
    edges: int
    density: float               # edges / max_possible_edges
    clustering_coefficient: float  # average local clustering
    avg_path_length: float
    hub_nodes: List[str]         # nodes with degree > 2× average
    bottleneck_risk: float       # 0.0 – 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "density": round(self.density, 4),
            "clustering_coefficient": round(self.clustering_coefficient, 4),
            "avg_path_length": round(self.avg_path_length, 4),
            "hub_nodes": self.hub_nodes,
            "bottleneck_risk": round(self.bottleneck_risk, 4),
        }


def analyze_network(
    adjacency: Dict[str, List[str]],
) -> NetworkTopology:
    """
    Compute SCNT² network topology metrics for an agent graph.

    Args:
        adjacency: node_id → [connected_node_ids]
    """
    nodes = list(adjacency.keys())
    n = len(nodes)
    if n == 0:
        return NetworkTopology(
            nodes=0, edges=0, density=0.0,
            clustering_coefficient=0.0, avg_path_length=0.0,
            hub_nodes=[], bottleneck_risk=0.0,
        )

    # Count edges (undirected)
    edge_set: set = set()
    for src, targets in adjacency.items():
        for tgt in targets:
            pair = tuple(sorted([src, tgt]))
            edge_set.add(pair)
    edges = len(edge_set)

    max_edges = n * (n - 1) / 2 if n > 1 else 1
    density = edges / max_edges

    # Degree analysis
    degrees = {node: len(adjacency.get(node, [])) for node in nodes}
    avg_degree = sum(degrees.values()) / n if n > 0 else 0

    # Hub detection (degree > 2× average)
    hub_threshold = 2 * avg_degree
    hubs = [node for node, deg in degrees.items() if deg > hub_threshold]

    # Simplified clustering coefficient
    clustering_values: List[float] = []
    for node in nodes:
        neighbors = set(adjacency.get(node, []))
        k = len(neighbors)
        if k < 2:
            clustering_values.append(0.0)
            continue
        # Count edges among neighbors
        neighbor_edges = 0
        for nb in neighbors:
            for nb2 in adjacency.get(nb, []):
                if nb2 in neighbors and nb2 != nb:
                    neighbor_edges += 1
        neighbor_edges //= 2  # undirected
        max_nb_edges = k * (k - 1) / 2
        clustering_values.append(neighbor_edges / max_nb_edges if max_nb_edges > 0 else 0.0)

    avg_clustering = sum(clustering_values) / n if n > 0 else 0.0

    # Bottleneck risk: high if few hubs with high density
    bottleneck = min(1.0, len(hubs) * 0.3 + (1.0 - density) * 0.4) if n > 2 else 0.0

    return NetworkTopology(
        nodes=n,
        edges=edges,
        density=density,
        clustering_coefficient=avg_clustering,
        avg_path_length=1.0 + (1.0 - density) * 3.0,  # approximation
        hub_nodes=hubs,
        bottleneck_risk=bottleneck,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. 7P-MCST MODEL — Multi-Criteria Scoring                      ║
# ╚════════════════════════════════════════════════════════════════════╝

SEVEN_P_DOMAINS = [
    "people", "process", "product", "platform",
    "performance", "protection", "perspective",
]


@dataclass
class SevenPScore:
    """7P Multi-Criteria Scoring for system evaluation."""
    scores: Dict[str, float]   # domain → score (0.0-1.0)
    weights: Dict[str, float]  # domain → weight
    overall: float = 0.0
    weakest: str = ""
    strongest: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "overall": round(self.overall, 4),
            "weakest": self.weakest,
            "strongest": self.strongest,
        }


def evaluate_seven_p(
    scores: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
) -> SevenPScore:
    """
    Evaluate a system using the 7P multi-criteria scoring model.

    Args:
        scores: Dict mapping domain names to 0.0–1.0 scores
        weights: Optional custom weights (defaults to equal)

    Returns 7P assessment with overall score and weak/strong analysis.
    """
    if weights is None:
        weights = {d: 1.0 / len(SEVEN_P_DOMAINS) for d in SEVEN_P_DOMAINS}

    # Normalize weights
    total_weight = sum(weights.values())
    norm_weights = {k: v / total_weight for k, v in weights.items()} if total_weight > 0 else weights

    # Compute weighted overall
    overall = sum(scores.get(d, 0.0) * norm_weights.get(d, 0.0) for d in SEVEN_P_DOMAINS)

    # Find weakest and strongest
    scored_domains = {d: scores.get(d, 0.0) for d in SEVEN_P_DOMAINS if d in scores}
    weakest = min(scored_domains, key=scored_domains.get, default="")
    strongest = max(scored_domains, key=scored_domains.get, default="")

    return SevenPScore(
        scores=scores,
        weights=norm_weights,
        overall=overall,
        weakest=weakest,
        strongest=strongest,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. AUTOPOIESIS — Self-Maintaining Boundary Detection            ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class AutopoiesisStatus:
    """Status of self-maintaining system boundaries."""
    system_id: str
    boundary_integrity: float     # 0.0 – 1.0
    self_production_rate: float   # rate of internal regeneration
    external_perturbation: float  # rate of external disruption
    viable: bool                  # boundary intact and self-sustaining
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "boundary_integrity": round(self.boundary_integrity, 4),
            "self_production_rate": round(self.self_production_rate, 4),
            "external_perturbation": round(self.external_perturbation, 4),
            "viable": self.viable,
            "recommendations": self.recommendations,
        }


def assess_autopoiesis(
    system_id: str,
    internal_regeneration: float,
    external_disruption: float,
    boundary_strength: float = 0.8,
) -> AutopoiesisStatus:
    """
    Assess whether a system is autopoietic (self-maintaining).

    An autopoietic system is viable when its internal regeneration
    rate exceeds external disruption, maintaining boundary integrity.
    """
    net_production = internal_regeneration - external_disruption
    integrity = min(1.0, max(0.0, boundary_strength + net_production * 0.5))
    viable = integrity >= 0.5 and internal_regeneration > external_disruption

    recs: List[str] = []
    if not viable:
        if integrity < 0.5:
            recs.append("Boundary integrity critically low — reinforce system boundaries")
        if internal_regeneration <= external_disruption:
            recs.append("External perturbation exceeds self-production — reduce coupling or increase internal capacity")
    else:
        if integrity < 0.7:
            recs.append("Boundary integrity marginal — monitor closely")

    return AutopoiesisStatus(
        system_id=system_id,
        boundary_integrity=integrity,
        self_production_rate=internal_regeneration,
        external_perturbation=external_disruption,
        viable=viable,
        recommendations=recs,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. COHERENCE GRADIENTS                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class CoherenceGradient:
    """Measures alignment coherence across subsystems."""
    subsystem_scores: Dict[str, float]  # subsystem_id → alignment (0-1)
    overall_coherence: float
    gradient_steepness: float           # max variance between subsystems
    weakest_link: str
    fully_coherent: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subsystem_scores": {k: round(v, 4) for k, v in self.subsystem_scores.items()},
            "overall_coherence": round(self.overall_coherence, 4),
            "gradient_steepness": round(self.gradient_steepness, 4),
            "weakest_link": self.weakest_link,
            "fully_coherent": self.fully_coherent,
        }


def compute_coherence_gradient(
    subsystem_alignments: Dict[str, float],
) -> CoherenceGradient:
    """
    Compute coherence gradient across multiple subsystems.

    A steep gradient indicates misalignment — some subsystems
    are well-aligned while others lag behind.
    """
    if not subsystem_alignments:
        return CoherenceGradient(
            subsystem_scores={},
            overall_coherence=0.0,
            gradient_steepness=0.0,
            weakest_link="none",
            fully_coherent=False,
        )

    values = list(subsystem_alignments.values())
    overall = sum(values) / len(values)
    steepness = max(values) - min(values) if len(values) > 1 else 0.0
    weakest = min(subsystem_alignments, key=subsystem_alignments.get)
    fully = all(v >= 0.8 for v in values)

    return CoherenceGradient(
        subsystem_scores=subsystem_alignments,
        overall_coherence=overall,
        gradient_steepness=steepness,
        weakest_link=weakest,
        fully_coherent=fully,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  7. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def codes_summary() -> Dict[str, Any]:
    """Return a summary of the CODES resonance framework."""
    return {
        "chirality": {
            "types": ["left", "right", "achiral"],
            "description": "Structural handedness detection for non-interchangeable components",
        },
        "resonance": {
            "method": "Prime-structured harmonic analysis",
            "coherence_threshold": 0.6,
        },
        "scnt_squared": {
            "metrics": ["density", "clustering_coefficient", "avg_path_length", "bottleneck_risk"],
            "description": "Super-Connected Network Theory Squared for agent communication graphs",
        },
        "seven_p": {
            "domains": SEVEN_P_DOMAINS,
            "description": "Multi-criteria scoring: People, Process, Product, Platform, Performance, Protection, Perspective",
        },
        "autopoiesis": {
            "viability_condition": "internal_regeneration > external_disruption AND boundary_integrity >= 0.5",
        },
        "coherence_gradient": {
            "full_coherence_threshold": 0.8,
        },
    }
