# ────────────────────────────────────────────────────────────────────
# cognitive.py — Global Workspace Theory, Integrated Information
#                Theory (Φ), and Structural Entropy Management
# ────────────────────────────────────────────────────────────────────
"""
Implements the cognitive interface framework described in the Praxis
enterprise blueprint:

1. **Global Workspace Theory (GWT)** — Baars 1988
   Models the multi-agent orchestration layer as a cognitive theater.
   Background agents compete for the "attentional spotlight"; winners
   broadcast their insights to the global workspace (dashboard).

2. **Integrated Information Theory (IIT)** — Tononi
   Calculates Φ (Phi) to quantify how tightly agents share context.
   High Φ = cohesive network; Low Φ = fragmented silos.

3. **Structural Entropy** — monitors UI/system complexity and triggers
   automated entropy-reduction routines when a threshold is breached.

All functions are pure-Python, deterministic where possible, and safe
for import without side-effects.
"""

from __future__ import annotations

import math
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. GLOBAL WORKSPACE THEORY — Attentional Spotlight              ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class BroadcastEvent:
    """A single event that an agent broadcasts to the global workspace."""
    agent_id: str
    event_type: str          # "anomaly" | "insight" | "completion" | "escalation"
    priority: float = 0.5    # 0.0 – 1.0 (1.0 = critical)
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "priority": round(self.priority, 4),
            "payload": self.payload,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
        }


@dataclass
class AgentModule:
    """
    Represents a background cognitive module (agent) in the GWT model.

    Each agent processes data silently.  When it detects something
    significant it submits a BroadcastEvent that competes for the
    global workspace spotlight.
    """
    agent_id: str
    role: str                        # "scanner", "planner", "executor", "evaluator"
    status: str = "idle"             # "idle", "processing", "broadcasting", "blocked"
    last_heartbeat: float = field(default_factory=time.time)
    broadcasts_sent: int = 0
    context_tokens: int = 0          # tokens currently held in context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "broadcasts_sent": self.broadcasts_sent,
            "context_tokens": self.context_tokens,
            "metadata": self.metadata,
        }


class GlobalWorkspace:
    """
    The central "theater stage" where broadcast events compete for
    the attentional spotlight and get relayed to the dashboard.

    Thread-safe.  Singleton recommended but not enforced.
    """

    MAX_BROADCAST_QUEUE = 500
    SPOTLIGHT_SIZE = 5               # max simultaneous items on "stage"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._agents: Dict[str, AgentModule] = {}
        self._broadcast_queue: List[BroadcastEvent] = []
        self._spotlight: List[BroadcastEvent] = []
        self._history: List[BroadcastEvent] = []
        self._created = time.time()

    # ── Agent lifecycle ──────────────────────────────────────────
    def register_agent(self, agent: AgentModule) -> bool:
        with self._lock:
            if agent.agent_id in self._agents:
                return False
            self._agents[agent.agent_id] = agent
            return True

    def unregister_agent(self, agent_id: str) -> bool:
        with self._lock:
            return self._agents.pop(agent_id, None) is not None

    def heartbeat(self, agent_id: str, status: str = "processing") -> bool:
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent is None:
                return False
            agent.last_heartbeat = time.time()
            agent.status = status
            return True

    def list_agents(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [a.to_dict() for a in self._agents.values()]

    # ── Selection-Broadcast cycle ────────────────────────────────
    def submit_broadcast(self, event: BroadcastEvent) -> bool:
        """Agent submits an event for competition on the stage."""
        with self._lock:
            if event.agent_id not in self._agents:
                return False
            agent = self._agents[event.agent_id]
            agent.broadcasts_sent += 1
            agent.status = "broadcasting"
            self._broadcast_queue.append(event)
            # Trim oldest if over capacity
            if len(self._broadcast_queue) > self.MAX_BROADCAST_QUEUE:
                self._broadcast_queue = self._broadcast_queue[-self.MAX_BROADCAST_QUEUE:]
            return True

    def compete_for_spotlight(self) -> List[Dict[str, Any]]:
        """
        Run the selection competition: highest-priority unacknowledged
        events win the attentional spotlight.
        """
        with self._lock:
            pending = [e for e in self._broadcast_queue if not e.acknowledged]
            pending.sort(key=lambda e: (-e.priority, e.timestamp))
            winners = pending[: self.SPOTLIGHT_SIZE]
            self._spotlight = winners
            return [e.to_dict() for e in winners]

    def acknowledge(self, agent_id: str, event_type: str) -> bool:
        """Operator acknowledges (dismisses) a broadcast from the stage."""
        with self._lock:
            for event in self._broadcast_queue:
                if event.agent_id == agent_id and event.event_type == event_type and not event.acknowledged:
                    event.acknowledged = True
                    self._history.append(event)
                    return True
            return False

    def get_spotlight(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [e.to_dict() for e in self._spotlight]

    def workspace_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "agents_registered": len(self._agents),
                "agents": [a.to_dict() for a in self._agents.values()],
                "pending_broadcasts": sum(1 for e in self._broadcast_queue if not e.acknowledged),
                "spotlight": [e.to_dict() for e in self._spotlight],
                "total_broadcasts_ever": sum(a.broadcasts_sent for a in self._agents.values()),
                "history_size": len(self._history),
                "uptime_seconds": round(time.time() - self._created, 2),
            }


# Global singleton
_workspace: Optional[GlobalWorkspace] = None
_ws_lock = threading.Lock()


def get_workspace() -> GlobalWorkspace:
    global _workspace
    with _ws_lock:
        if _workspace is None:
            _workspace = GlobalWorkspace()
        return _workspace


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. INTEGRATED INFORMATION THEORY — Φ (Phi) Metric              ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class AgentInteraction:
    """Observed interaction between two agents."""
    source: str
    target: str
    tokens_exchanged: int = 0
    messages_exchanged: int = 0
    mutual_information: float = 0.0   # bits
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "tokens_exchanged": self.tokens_exchanged,
            "messages_exchanged": self.messages_exchanged,
            "mutual_information": round(self.mutual_information, 4),
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp,
        }


def _compute_mutual_information(
    joint_counts: Dict[Tuple[str, str], int],
    marginal_a: Dict[str, int],
    marginal_b: Dict[str, int],
    total: int,
) -> float:
    """
    Compute MI(A;B) = Σ p(a,b) · log₂(p(a,b) / (p(a)·p(b)))

    Used to quantify how much information agent A's output provides
    about agent B's subsequent behavior.
    """
    if total == 0:
        return 0.0
    mi = 0.0
    for (a, b), count in joint_counts.items():
        p_ab = count / total
        p_a = marginal_a.get(a, 0) / total
        p_b = marginal_b.get(b, 0) / total
        if p_ab > 0 and p_a > 0 and p_b > 0:
            mi += p_ab * math.log2(p_ab / (p_a * p_b))
    return mi


def compute_phi(interactions: List[AgentInteraction]) -> Dict[str, Any]:
    """
    Compute a simplified Φ (Phi) metric for the agent network.

    Φ quantifies the *integrated information* — how much the system
    as a whole is more than the sum of its parts.  In the Praxis
    context, high Φ means agents are deeply sharing context; low Φ
    means fragmented silos.

    Method:
      1. Build an adjacency matrix of mutual-information scores.
      2. Whole-system MI = sum of all edges.
      3. For every possible bipartition, sum MI of cut edges.
      4. Φ = min over bipartitions of (cut MI) — the "minimum
         information partition" in Tononi's formalism.

    For tractability with >10 agents, we approximate using a
    spectral approach (Fiedler value of the MI-weighted graph).
    """
    if not interactions:
        return {
            "phi": 0.0,
            "interpretation": "no_data",
            "agent_count": 0,
            "edge_count": 0,
            "total_mutual_information": 0.0,
            "fragmentation_risk": "unknown",
        }

    # Build adjacency
    agents: set = set()
    edge_mi: Dict[Tuple[str, str], float] = defaultdict(float)
    for ix in interactions:
        agents.add(ix.source)
        agents.add(ix.target)
        key = tuple(sorted([ix.source, ix.target]))
        edge_mi[key] += ix.mutual_information

    agent_list = sorted(agents)
    n = len(agent_list)
    idx = {a: i for i, a in enumerate(agent_list)}

    total_mi = sum(edge_mi.values())
    if n < 2:
        return {
            "phi": 0.0,
            "interpretation": "single_agent",
            "agent_count": n,
            "edge_count": len(edge_mi),
            "total_mutual_information": round(total_mi, 4),
            "fragmentation_risk": "not_applicable",
        }

    # Build the Laplacian matrix for spectral analysis
    # L = D - W  where W is weight matrix, D is degree matrix
    laplacian = [[0.0] * n for _ in range(n)]
    for (a, b), mi_val in edge_mi.items():
        i, j = idx[a], idx[b]
        laplacian[i][j] -= mi_val
        laplacian[j][i] -= mi_val
        laplacian[i][i] += mi_val
        laplacian[j][j] += mi_val

    # Approximate Fiedler value (2nd-smallest eigenvalue) via
    # power-iteration on (λ_max·I - L) then subtract.
    # For small networks this is exact enough.
    phi_approx = _fiedler_approx(laplacian, n)

    # Interpretation thresholds
    if phi_approx < 0.1:
        interp = "fragmented"
        risk = "high"
    elif phi_approx < 0.5:
        interp = "partially_integrated"
        risk = "medium"
    elif phi_approx < 1.0:
        interp = "well_integrated"
        risk = "low"
    else:
        interp = "highly_integrated"
        risk = "minimal"

    # Per-agent connectivity
    agent_connectivity = {}
    for a in agent_list:
        degree = sum(
            mi_val for (x, y), mi_val in edge_mi.items()
            if a in (x, y)
        )
        agent_connectivity[a] = round(degree, 4)

    return {
        "phi": round(phi_approx, 4),
        "interpretation": interp,
        "agent_count": n,
        "edge_count": len(edge_mi),
        "total_mutual_information": round(total_mi, 4),
        "fragmentation_risk": risk,
        "agent_connectivity": agent_connectivity,
    }


def _fiedler_approx(laplacian: List[List[float]], n: int) -> float:
    """
    Approximate the Fiedler value (algebraic connectivity) of a
    weighted graph Laplacian using inverse power iteration.

    The Fiedler value is the second-smallest eigenvalue of L.
    A larger value means the graph is harder to partition → more
    integrated → higher Φ.
    """
    if n <= 1:
        return 0.0

    # Estimate λ_max via Gershgorin bound
    lambda_max = max(
        laplacian[i][i] + sum(abs(laplacian[i][j]) for j in range(n) if j != i)
        for i in range(n)
    )
    if lambda_max < 1e-12:
        return 0.0

    # Shifted matrix M = λ_max·I - L  (largest eigenvalue of M = λ_max - λ_2)
    M = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            M[i][j] = -laplacian[i][j]
            if i == j:
                M[i][j] += lambda_max

    # Power iteration to find dominant eigenvector of M
    # Must deflate by the constant vector (eigenvector of λ_max of L)
    import random
    rng = random.Random(42)   # deterministic
    v = [rng.gauss(0, 1) for _ in range(n)]
    # Orthogonalise against constant vector
    mean_v = sum(v) / n
    v = [vi - mean_v for vi in v]
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    v = [x / norm for x in v]

    for _ in range(200):
        # Matrix-vector product
        w = [sum(M[i][j] * v[j] for j in range(n)) for i in range(n)]
        # Orthogonalise
        mean_w = sum(w) / n
        w = [wi - mean_w for wi in w]
        norm = math.sqrt(sum(x * x for x in w)) or 1.0
        v = [x / norm for x in w]

    # Rayleigh quotient for the eigenvalue of M
    Mv = [sum(M[i][j] * v[j] for j in range(n)) for i in range(n)]
    numerator = sum(v[i] * Mv[i] for i in range(n))
    denominator = sum(v[i] * v[i] for i in range(n)) or 1.0
    lambda_M = numerator / denominator

    # λ_2(L) = λ_max - λ_M
    fiedler = max(0.0, lambda_max - lambda_M)
    return fiedler


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. STRUCTURAL ENTROPY — UI/System Complexity Monitor            ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class EntropySnapshot:
    """A single measurement of system structural entropy."""
    timestamp: float = field(default_factory=time.time)
    panel_count: int = 0
    widget_count: int = 0
    data_partitions: int = 0
    active_agents: int = 0
    pending_events: int = 0
    entropy_bits: float = 0.0
    above_threshold: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "panel_count": self.panel_count,
            "widget_count": self.widget_count,
            "data_partitions": self.data_partitions,
            "active_agents": self.active_agents,
            "pending_events": self.pending_events,
            "entropy_bits": round(self.entropy_bits, 4),
            "above_threshold": self.above_threshold,
        }


def compute_structural_entropy(
    panel_count: int = 0,
    widget_count: int = 0,
    data_partitions: int = 0,
    active_agents: int = 0,
    pending_events: int = 0,
    threshold: float = 5.0,
) -> EntropySnapshot:
    """
    Measure the structural entropy (disorder) of the current UI state.

    Uses Shannon entropy over the distribution of UI elements:
      H = -Σ pᵢ · log₂(pᵢ)

    When H exceeds the threshold, metacognitive routines should
    engage to collapse panels, group anomalies, and simplify the view.
    """
    counts = [
        ("panels", max(panel_count, 0)),
        ("widgets", max(widget_count, 0)),
        ("partitions", max(data_partitions, 0)),
        ("agents", max(active_agents, 0)),
        ("events", max(pending_events, 0)),
    ]
    total = sum(c for _, c in counts)

    if total == 0:
        return EntropySnapshot(entropy_bits=0.0, above_threshold=False)

    entropy = 0.0
    for _, count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    snap = EntropySnapshot(
        panel_count=panel_count,
        widget_count=widget_count,
        data_partitions=data_partitions,
        active_agents=active_agents,
        pending_events=pending_events,
        entropy_bits=entropy,
        above_threshold=entropy > threshold,
    )
    return snap


def entropy_reduction_plan(snapshot: EntropySnapshot) -> Dict[str, Any]:
    """
    Generate an automated entropy-reduction action plan.

    If entropy is above threshold, returns concrete UI actions:
    - Collapse secondary panels
    - Group related anomalies by root cause
    - Hide empty containers
    - Summarise low-priority broadcasts
    """
    if not snapshot.above_threshold:
        return {
            "action_required": False,
            "entropy_bits": round(snapshot.entropy_bits, 4),
            "message": "System entropy within acceptable range",
        }

    actions: List[Dict[str, str]] = []

    if snapshot.panel_count > 8:
        actions.append({
            "action": "collapse_panels",
            "detail": f"Collapse {snapshot.panel_count - 6} secondary panels to reduce visual density",
            "priority": "high",
        })

    if snapshot.pending_events > 10:
        actions.append({
            "action": "group_anomalies",
            "detail": f"Group {snapshot.pending_events} pending events by root cause",
            "priority": "high",
        })

    if snapshot.widget_count > 12:
        actions.append({
            "action": "hide_empty_widgets",
            "detail": "Auto-hide widgets with no active data streams",
            "priority": "medium",
        })

    if snapshot.data_partitions > 6:
        actions.append({
            "action": "merge_partitions",
            "detail": f"Merge {snapshot.data_partitions - 4} low-activity data partitions",
            "priority": "medium",
        })

    actions.append({
        "action": "summarize_broadcasts",
        "detail": "Coalesce low-priority broadcasts into digest view",
        "priority": "low",
    })

    return {
        "action_required": True,
        "entropy_bits": round(snapshot.entropy_bits, 4),
        "actions": actions,
        "estimated_reduction": round(snapshot.entropy_bits * 0.4, 4),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. CONVENIENCE FUNCTIONS                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

def cognitive_summary() -> Dict[str, Any]:
    """Return a comprehensive cognitive-layer health snapshot."""
    ws = get_workspace()
    state = ws.workspace_state()

    # Compute entropy for current state
    snap = compute_structural_entropy(
        active_agents=state["agents_registered"],
        pending_events=state["pending_broadcasts"],
    )

    return {
        "global_workspace": state,
        "structural_entropy": snap.to_dict(),
        "entropy_reduction": entropy_reduction_plan(snap),
    }
