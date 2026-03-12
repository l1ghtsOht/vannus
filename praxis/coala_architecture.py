# ────────────────────────────────────────────────────────────────────
# coala_architecture.py — CoALA Cognitive Architecture
# ────────────────────────────────────────────────────────────────────
"""
Implements the CoALA (Cognitive Architectures for Language Agents)
framework from the Cognitive Resilience blueprint.

Core Components:
- **Modular Memory System**: Working, Episodic, Semantic, Procedural
- **Structured Action Spaces**: Internal (reasoning, retrieval,
  learning) and External (API calls, tool use, grounding)
- **Decision Cycle**: Planning → Execution → Learning loop
- **Global Workspace Theory**: Selection-broadcast for consciousness-
  inspired information integration
- **IIT Φ Metrics**: Integrated Information Theory measure for
  system integration quality
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. MEMORY MODULES                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass
class MemoryEntry:
    """A single entry in any memory module."""
    entry_id: str
    memory_type: MemoryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    relevance_score: float = 1.0
    decay_rate: float = 0.01  # per-cycle decay

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "memory_type": self.memory_type.value,
            "content": self.content[:200],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
            "relevance_score": round(self.relevance_score, 4),
        }


class MemoryModule:
    """
    A single memory module with capacity constraints and decay.

    Working Memory: Small capacity (7±2 items), fast access, high decay
    Episodic Memory: Medium capacity, temporal ordering
    Semantic Memory: Large capacity, concept-based retrieval
    Procedural Memory: Skill/action patterns, low decay
    """

    CAPACITY_LIMITS = {
        MemoryType.WORKING: 9,        # 7±2
        MemoryType.EPISODIC: 1000,
        MemoryType.SEMANTIC: 5000,
        MemoryType.PROCEDURAL: 500,
    }

    DECAY_RATES = {
        MemoryType.WORKING: 0.15,
        MemoryType.EPISODIC: 0.02,
        MemoryType.SEMANTIC: 0.005,
        MemoryType.PROCEDURAL: 0.001,
    }

    def __init__(self, memory_type: MemoryType):
        self.memory_type = memory_type
        self.entries: Dict[str, MemoryEntry] = {}
        self.capacity = self.CAPACITY_LIMITS.get(memory_type, 100)
        self.default_decay = self.DECAY_RATES.get(memory_type, 0.01)

    def store(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        """Store a new entry; evict oldest if at capacity."""
        entry_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        entry = MemoryEntry(
            entry_id=entry_id,
            memory_type=self.memory_type,
            content=content,
            metadata=metadata or {},
            decay_rate=self.default_decay,
        )

        # Evict if at capacity (FIFO for working, lowest relevance for others)
        if len(self.entries) >= self.capacity:
            if self.memory_type == MemoryType.WORKING:
                oldest_id = min(self.entries, key=lambda k: self.entries[k].timestamp)
            else:
                oldest_id = min(self.entries, key=lambda k: self.entries[k].relevance_score)
            del self.entries[oldest_id]

        self.entries[entry_id] = entry
        return entry

    def retrieve(self, query: str, top_k: int = 5) -> List[MemoryEntry]:
        """Retrieve entries by keyword matching (simplified)."""
        scored: List[Tuple[float, MemoryEntry]] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for entry in self.entries.values():
            content_words = set(entry.content.lower().split())
            overlap = len(query_words & content_words)
            score = overlap / max(len(query_words), 1)
            entry.access_count += 1
            scored.append((score * entry.relevance_score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]

    def decay_cycle(self) -> int:
        """Apply decay to all entries; remove expired ones. Returns count removed."""
        expired: List[str] = []
        for eid, entry in self.entries.items():
            entry.relevance_score = max(0.0, entry.relevance_score - entry.decay_rate)
            if entry.relevance_score <= 0.0:
                expired.append(eid)
        for eid in expired:
            del self.entries[eid]
        return len(expired)

    def status(self) -> Dict[str, Any]:
        return {
            "memory_type": self.memory_type.value,
            "entries": len(self.entries),
            "capacity": self.capacity,
            "utilization": round(len(self.entries) / self.capacity, 4) if self.capacity > 0 else 0.0,
            "avg_relevance": round(
                sum(e.relevance_score for e in self.entries.values()) / max(len(self.entries), 1), 4
            ),
        }


class CoALAMemorySystem:
    """Complete four-module memory system."""

    def __init__(self):
        self.working = MemoryModule(MemoryType.WORKING)
        self.episodic = MemoryModule(MemoryType.EPISODIC)
        self.semantic = MemoryModule(MemoryType.SEMANTIC)
        self.procedural = MemoryModule(MemoryType.PROCEDURAL)
        self._modules = {
            MemoryType.WORKING: self.working,
            MemoryType.EPISODIC: self.episodic,
            MemoryType.SEMANTIC: self.semantic,
            MemoryType.PROCEDURAL: self.procedural,
        }

    def store(self, memory_type: MemoryType, content: str,
              metadata: Optional[Dict[str, Any]] = None) -> MemoryEntry:
        return self._modules[memory_type].store(content, metadata)

    def retrieve(self, memory_type: MemoryType, query: str, top_k: int = 5) -> List[MemoryEntry]:
        return self._modules[memory_type].retrieve(query, top_k)

    def cross_retrieve(self, query: str, top_k: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve across all memory modules simultaneously."""
        results: Dict[str, List[Dict[str, Any]]] = {}
        for mtype, module in self._modules.items():
            entries = module.retrieve(query, top_k)
            results[mtype.value] = [e.to_dict() for e in entries]
        return results

    def global_decay(self) -> Dict[str, int]:
        """Apply decay across all modules."""
        return {mtype.value: module.decay_cycle() for mtype, module in self._modules.items()}

    def status(self) -> Dict[str, Any]:
        return {
            mtype.value: module.status()
            for mtype, module in self._modules.items()
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. ACTION SPACES                                                ║
# ╚════════════════════════════════════════════════════════════════════╝

class ActionType(str, Enum):
    # Internal actions
    REASONING = "reasoning"
    RETRIEVAL = "retrieval"
    LEARNING = "learning"
    # External actions
    GROUNDING = "grounding"
    TOOL_USE = "tool_use"
    API_CALL = "api_call"


@dataclass
class Action:
    """A structured action in the CoALA decision cycle."""
    action_id: str
    action_type: ActionType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    cost: float = 1.0         # computational cost estimate
    priority: float = 0.5     # 0.0 – 1.0
    outcome: Optional[str] = None
    success: Optional[bool] = None
    execution_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "cost": round(self.cost, 4),
            "priority": round(self.priority, 4),
            "outcome": self.outcome,
            "success": self.success,
            "execution_time": round(self.execution_time, 4),
        }


INTERNAL_ACTIONS = {ActionType.REASONING, ActionType.RETRIEVAL, ActionType.LEARNING}
EXTERNAL_ACTIONS = {ActionType.GROUNDING, ActionType.TOOL_USE, ActionType.API_CALL}


def classify_action(action_type: ActionType) -> str:
    """Classify an action as internal or external."""
    return "internal" if action_type in INTERNAL_ACTIONS else "external"


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. DECISION CYCLE — Planning → Execution → Learning             ║
# ╚════════════════════════════════════════════════════════════════════╝

class CyclePhase(str, Enum):
    PLANNING = "planning"
    EXECUTION = "execution"
    LEARNING = "learning"
    IDLE = "idle"


@dataclass
class DecisionCycle:
    """A single planning → execution → learning cycle."""
    cycle_id: str
    phase: CyclePhase = CyclePhase.IDLE
    planned_actions: List[Action] = field(default_factory=list)
    executed_actions: List[Action] = field(default_factory=list)
    lessons: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_cost: float = 0.0

    def plan(self, actions: List[Action]) -> None:
        """Enter planning phase and register actions."""
        self.phase = CyclePhase.PLANNING
        self.planned_actions = sorted(actions, key=lambda a: a.priority, reverse=True)

    def execute(self) -> List[Action]:
        """Execute planned actions in priority order."""
        self.phase = CyclePhase.EXECUTION
        for action in self.planned_actions:
            start = time.time()
            # Simulated execution
            action.success = True
            action.outcome = f"Executed {action.action_type.value}: {action.description[:80]}"
            action.execution_time = time.time() - start
            self.total_cost += action.cost
            self.executed_actions.append(action)
        return self.executed_actions

    def learn(self) -> List[str]:
        """Extract lessons from execution results."""
        self.phase = CyclePhase.LEARNING
        successful = sum(1 for a in self.executed_actions if a.success)
        total = len(self.executed_actions)
        rate = successful / max(total, 1)

        self.lessons = [
            f"Execution success rate: {rate:.0%}",
            f"Total cost: {self.total_cost:.2f}",
            f"Actions: {total} planned, {successful} successful",
        ]
        if rate < 0.8:
            self.lessons.append("Consider decomposing failed actions into smaller steps")

        self.end_time = time.time()
        self.phase = CyclePhase.IDLE
        return self.lessons

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "planned_count": len(self.planned_actions),
            "executed_count": len(self.executed_actions),
            "lessons": self.lessons,
            "total_cost": round(self.total_cost, 4),
            "duration": round((self.end_time or time.time()) - self.start_time, 4),
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. GLOBAL WORKSPACE THEORY — Selection-Broadcast                ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class BroadcastItem:
    """An item in the global workspace competing for broadcast."""
    item_id: str
    content: str
    source_module: str     # which specialist module produced this
    salience: float = 0.5  # 0.0 – 1.0 (urgency/importance)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": self.content[:200],
            "source_module": self.source_module,
            "salience": round(self.salience, 4),
            "timestamp": self.timestamp,
        }


class GlobalWorkspace:
    """
    GWT-inspired selection-broadcast mechanism.

    Items from specialist modules compete for 'consciousness' in a
    shared workspace. The most salient item wins the broadcast slot
    and becomes available to all modules.
    """

    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.candidates: List[BroadcastItem] = []
        self.broadcast_history: List[BroadcastItem] = []
        self.current_broadcast: Optional[BroadcastItem] = None

    def submit(self, content: str, source_module: str, salience: float = 0.5) -> BroadcastItem:
        """Submit an item for broadcast consideration."""
        item_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:10]
        item = BroadcastItem(
            item_id=item_id,
            content=content,
            source_module=source_module,
            salience=min(1.0, max(0.0, salience)),
        )
        self.candidates.append(item)

        # Keep only recent candidates
        if len(self.candidates) > self.capacity * 3:
            self.candidates = sorted(self.candidates, key=lambda x: x.salience, reverse=True)
            self.candidates = self.candidates[:self.capacity * 2]

        return item

    def select_and_broadcast(self) -> Optional[BroadcastItem]:
        """Select the most salient item and broadcast it."""
        if not self.candidates:
            return None

        # Selection: highest salience wins
        winner = max(self.candidates, key=lambda x: x.salience)
        self.current_broadcast = winner
        self.broadcast_history.append(winner)
        self.candidates.remove(winner)

        # Keep broadcast history bounded
        if len(self.broadcast_history) > 100:
            self.broadcast_history = self.broadcast_history[-50:]

        return winner

    def status(self) -> Dict[str, Any]:
        return {
            "candidates": len(self.candidates),
            "capacity": self.capacity,
            "current_broadcast": self.current_broadcast.to_dict() if self.current_broadcast else None,
            "total_broadcasts": len(self.broadcast_history),
            "source_distribution": self._source_distribution(),
        }

    def _source_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for item in self.broadcast_history:
            dist[item.source_module] = dist.get(item.source_module, 0) + 1
        return dist


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. IIT Φ (PHI) METRICS                                         ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class PhiMetrics:
    """Integrated Information Theory Φ measurement."""
    system_id: str
    phi_value: float          # 0.0 – ∞ (practically 0-10)
    partition_count: int      # number of subsystem partitions tested
    min_information_loss: float
    integration_level: str    # "low", "medium", "high"
    subsystem_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_id": self.system_id,
            "phi_value": round(self.phi_value, 4),
            "partition_count": self.partition_count,
            "min_information_loss": round(self.min_information_loss, 4),
            "integration_level": self.integration_level,
            "subsystem_scores": {k: round(v, 4) for k, v in self.subsystem_scores.items()},
        }


def compute_phi(
    subsystem_connections: Dict[str, List[str]],
    subsystem_information: Dict[str, float],
) -> PhiMetrics:
    """
    Compute simplified IIT Φ metric for a system.

    Φ measures the degree of integrated information — how much
    information is generated by the system above and beyond its parts.

    Args:
        subsystem_connections: adjacency list of subsystem dependencies
        subsystem_information: information content per subsystem (bits)
    """
    n = len(subsystem_connections)
    if n == 0:
        return PhiMetrics(
            system_id="empty",
            phi_value=0.0,
            partition_count=0,
            min_information_loss=0.0,
            integration_level="low",
        )

    system_id = hashlib.md5(str(sorted(subsystem_connections.keys())).encode()).hexdigest()[:10]

    # Total system information
    total_info = sum(subsystem_information.values())

    # Compute integration across partitions
    # For each possible bipartition, compute information loss
    nodes = list(subsystem_connections.keys())
    min_loss = float("inf")
    partition_count = 0

    # Simplified: test partitions by splitting each node out
    for i, node in enumerate(nodes):
        partition_a = {node}
        partition_b = set(nodes) - partition_a

        if not partition_b:
            continue

        partition_count += 1

        # Information in partition A
        info_a = subsystem_information.get(node, 0.0)

        # Information in partition B
        info_b = sum(subsystem_information.get(n, 0.0) for n in partition_b)

        # Cross-partition connections (integration)
        cross_connections = 0
        for neighbor in subsystem_connections.get(node, []):
            if neighbor in partition_b:
                cross_connections += 1

        # Information loss when partition is cut
        loss = cross_connections * (info_a + info_b) / max(n, 1)
        min_loss = min(min_loss, loss) if loss > 0 else min_loss

    if min_loss == float("inf"):
        min_loss = 0.0

    # Φ is the minimum information loss across best partition
    phi = min_loss

    # Classification
    if phi < 1.0:
        level = "low"
    elif phi < 3.0:
        level = "medium"
    else:
        level = "high"

    return PhiMetrics(
        system_id=system_id,
        phi_value=phi,
        partition_count=partition_count,
        min_information_loss=min_loss,
        integration_level=level,
        subsystem_scores=subsystem_information,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. MODULE SUMMARY                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def coala_summary() -> Dict[str, Any]:
    """Return a summary of the CoALA cognitive architecture."""
    return {
        "memory_modules": {
            "working": {"capacity": 9, "decay_rate": 0.15, "function": "Active processing buffer (7±2 items)"},
            "episodic": {"capacity": 1000, "decay_rate": 0.02, "function": "Event/experience storage"},
            "semantic": {"capacity": 5000, "decay_rate": 0.005, "function": "Concept/knowledge graph"},
            "procedural": {"capacity": 500, "decay_rate": 0.001, "function": "Skill/action patterns"},
        },
        "action_spaces": {
            "internal": ["reasoning", "retrieval", "learning"],
            "external": ["grounding", "tool_use", "api_call"],
        },
        "decision_cycle": ["planning", "execution", "learning"],
        "global_workspace": {
            "mechanism": "Selection-broadcast (GWT)",
            "description": "Most salient item wins broadcast to all modules",
        },
        "iit_phi": {
            "metric": "Φ (integrated information)",
            "levels": {"low": "<1.0", "medium": "1.0-3.0", "high": ">3.0"},
        },
    }
