# ────────────────────────────────────────────────────────────────────
# knowledge_graph.py — GraphRAG, Entity Extraction, Community
#                      Detection, and Knowledge Graph Construction
# ────────────────────────────────────────────────────────────────────
"""
Implements the GraphRAG knowledge visualization system described in
the Praxis enterprise blueprint (§5):

1. **Entity Extraction** — extract named entities and relationships
   from text using lightweight NLP heuristics.

2. **Knowledge Graph** — in-memory graph structure with nodes, edges,
   centrality metrics, and semantic zooming support.

3. **Community Detection** — Louvain-style modularity-based clustering
   to identify dense sub-communities that can be summarized.

4. **Graph Querying** — traversal, shortest paths, and neighborhood
   expansion for interactive exploration.

All functions are pure-Python with no external graph library dependency.
"""

from __future__ import annotations

import re
import math
import hashlib
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. DATA MODELS                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    node_id: str
    label: str
    entity_type: str = "concept"      # "concept", "tool", "person", "organization", "event", "metric"
    properties: Dict[str, Any] = field(default_factory=dict)
    community_id: Optional[int] = None
    centrality: float = 0.0
    mention_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "entity_type": self.entity_type,
            "properties": self.properties,
            "community_id": self.community_id,
            "centrality": round(self.centrality, 4),
            "mention_count": self.mention_count,
        }


@dataclass
class GraphEdge:
    """A directed edge in the knowledge graph."""
    source: str
    target: str
    relation: str = "related_to"     # "related_to", "depends_on", "part_of", "causes", "similar_to"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)

    @property
    def edge_id(self) -> str:
        return f"{self.source}--{self.relation}-->{self.target}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "weight": round(self.weight, 4),
            "properties": self.properties,
        }


@dataclass
class Community:
    """A detected community (dense cluster) in the graph."""
    community_id: int
    node_ids: List[str] = field(default_factory=list)
    label: str = ""
    summary: str = ""
    density: float = 0.0
    modularity_contribution: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "community_id": self.community_id,
            "node_count": len(self.node_ids),
            "node_ids": self.node_ids,
            "label": self.label,
            "summary": self.summary,
            "density": round(self.density, 4),
            "modularity_contribution": round(self.modularity_contribution, 4),
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. KNOWLEDGE GRAPH                                              ║
# ╚════════════════════════════════════════════════════════════════════╝

class KnowledgeGraph:
    """
    In-memory knowledge graph with CRUD, centrality, community
    detection, and traversal.

    Thread-safe.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse_adj: Dict[str, List[str]] = defaultdict(list)
        self._communities: List[Community] = []

    # ── Node CRUD ────────────────────────────────────────────────
    def add_node(self, node: GraphNode) -> bool:
        with self._lock:
            if node.node_id in self._nodes:
                self._nodes[node.node_id].mention_count += 1
                return False
            self._nodes[node.node_id] = node
            return True

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            n = self._nodes.get(node_id)
            return n.to_dict() if n else None

    def remove_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self._nodes:
                return False
            del self._nodes[node_id]
            self._edges = [e for e in self._edges if e.source != node_id and e.target != node_id]
            self._adjacency.pop(node_id, None)
            self._reverse_adj.pop(node_id, None)
            for adj in self._adjacency.values():
                while node_id in adj:
                    adj.remove(node_id)
            for adj in self._reverse_adj.values():
                while node_id in adj:
                    adj.remove(node_id)
            return True

    # ── Edge CRUD ────────────────────────────────────────────────
    def add_edge(self, edge: GraphEdge) -> bool:
        with self._lock:
            if edge.source not in self._nodes or edge.target not in self._nodes:
                return False
            self._edges.append(edge)
            self._adjacency[edge.source].append(edge.target)
            self._reverse_adj[edge.target].append(edge.source)
            return True

    def get_edges(self, node_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                e.to_dict() for e in self._edges
                if e.source == node_id or e.target == node_id
            ]

    # ── Stats ────────────────────────────────────────────────────
    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def graph_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self._graph_stats_unlocked()

    def _graph_stats_unlocked(self) -> Dict[str, Any]:
        type_dist: Dict[str, int] = defaultdict(int)
        for n in self._nodes.values():
            type_dist[n.entity_type] += 1
        return {
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
            "community_count": len(self._communities),
            "entity_type_distribution": dict(type_dist),
            "avg_degree": round(
                2 * len(self._edges) / max(len(self._nodes), 1), 2
            ),
        }

    # ── Centrality ───────────────────────────────────────────────
    def compute_centrality(self) -> Dict[str, float]:
        """
        Compute degree centrality for all nodes.
        Normalized by (n-1) where n = total nodes.
        """
        with self._lock:
            n = len(self._nodes)
            if n <= 1:
                for node in self._nodes.values():
                    node.centrality = 0.0
                return {nid: 0.0 for nid in self._nodes}

            degree: Dict[str, int] = defaultdict(int)
            for edge in self._edges:
                degree[edge.source] += 1
                degree[edge.target] += 1

            result = {}
            for nid, node in self._nodes.items():
                c = degree.get(nid, 0) / (n - 1)
                node.centrality = c
                result[nid] = round(c, 4)
            return result

    # ── Community Detection (Louvain-inspired) ───────────────────
    def detect_communities(self) -> List[Dict[str, Any]]:
        """
        Simplified Louvain community detection.

        Phase 1: Each node starts in its own community.
        Phase 2: Greedily move nodes to neighbor's community if
                 modularity gain is positive.
        Phase 3: Repeat until stable.

        Returns list of Community dicts.
        """
        with self._lock:
            if not self._nodes:
                self._communities = []
                return []

            node_ids = list(self._nodes.keys())
            community_of: Dict[str, int] = {nid: i for i, nid in enumerate(node_ids)}
            m = len(self._edges) or 1  # total edges

            # Build degree and adjacency
            degree: Dict[str, float] = defaultdict(float)
            neighbors: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
            for e in self._edges:
                degree[e.source] += e.weight
                degree[e.target] += e.weight
                neighbors[e.source].append((e.target, e.weight))
                neighbors[e.target].append((e.source, e.weight))

            total_weight = sum(e.weight for e in self._edges) or 1.0

            changed = True
            iterations = 0
            max_iterations = 50

            while changed and iterations < max_iterations:
                changed = False
                iterations += 1
                for nid in node_ids:
                    current_comm = community_of[nid]
                    best_comm = current_comm
                    best_gain = 0.0

                    # Evaluate moving nid to each neighbor's community
                    neighbor_comms: Set[int] = set()
                    for neighbor, w in neighbors.get(nid, []):
                        neighbor_comms.add(community_of[neighbor])

                    for comm in neighbor_comms:
                        if comm == current_comm:
                            continue
                        gain = self._modularity_gain(
                            nid, comm, community_of, neighbors, degree, total_weight
                        )
                        if gain > best_gain:
                            best_gain = gain
                            best_comm = comm

                    if best_comm != current_comm:
                        community_of[nid] = best_comm
                        changed = True

            # Build community objects
            comm_members: Dict[int, List[str]] = defaultdict(list)
            for nid, c_id in community_of.items():
                comm_members[c_id].append(nid)

            self._communities = []
            for c_id, members in comm_members.items():
                # Compute internal density
                internal_edges = sum(
                    1 for e in self._edges
                    if community_of.get(e.source) == c_id and community_of.get(e.target) == c_id
                )
                max_edges = len(members) * (len(members) - 1) / 2 or 1
                density = internal_edges / max_edges

                comm = Community(
                    community_id=c_id,
                    node_ids=sorted(members),
                    label=self._generate_community_label(members),
                    density=density,
                )
                self._communities.append(comm)

                # Tag nodes
                for nid in members:
                    if nid in self._nodes:
                        self._nodes[nid].community_id = c_id

            return [c.to_dict() for c in self._communities]

    def _modularity_gain(
        self,
        node_id: str,
        target_comm: int,
        community_of: Dict[str, int],
        neighbors: Dict[str, List[Tuple[str, float]]],
        degree: Dict[str, float],
        total_weight: float,
    ) -> float:
        """Compute modularity gain from moving node to target community."""
        ki = degree.get(node_id, 0.0)
        # Sum of weights connecting node_id to target community
        ki_in = sum(
            w for n, w in neighbors.get(node_id, [])
            if community_of.get(n) == target_comm
        )
        # Total degree of target community
        sigma_tot = sum(
            degree.get(n, 0.0) for n, c in community_of.items()
            if c == target_comm
        )
        # Modularity gain formula
        gain = (ki_in / total_weight) - (sigma_tot * ki) / (2 * total_weight * total_weight)
        return gain

    def _generate_community_label(self, member_ids: List[str]) -> str:
        """Generate a human-readable label for a community."""
        labels = []
        for nid in member_ids[:3]:
            node = self._nodes.get(nid)
            if node:
                labels.append(node.label)
        suffix = f" (+{len(member_ids) - 3})" if len(member_ids) > 3 else ""
        return ", ".join(labels) + suffix

    # ── Traversal ────────────────────────────────────────────────
    def neighbors(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """Get neighborhood of a node up to `depth` hops."""
        with self._lock:
            if node_id not in self._nodes:
                return {"error": "node_not_found"}

            visited: Set[str] = {node_id}
            frontier: Set[str] = {node_id}
            layers: List[List[str]] = []

            for d in range(depth):
                next_frontier: Set[str] = set()
                for nid in frontier:
                    for neighbor in self._adjacency.get(nid, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.add(neighbor)
                    for neighbor in self._reverse_adj.get(nid, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_frontier.add(neighbor)
                layers.append(sorted(next_frontier))
                frontier = next_frontier

            nodes = [self._nodes[nid].to_dict() for nid in visited if nid in self._nodes]
            edges = [
                e.to_dict() for e in self._edges
                if e.source in visited and e.target in visited
            ]
            return {
                "center": node_id,
                "depth": depth,
                "nodes": nodes,
                "edges": edges,
                "layers": layers,
            }

    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """BFS shortest path between two nodes."""
        with self._lock:
            if source not in self._nodes or target not in self._nodes:
                return None
            if source == target:
                return [source]

            visited: Set[str] = {source}
            queue: deque[Tuple[str, List[str]]] = deque([(source, [source])])

            while queue:
                current, path = queue.popleft()
                for neighbor in self._adjacency.get(current, []) + self._reverse_adj.get(current, []):
                    if neighbor == target:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            return None

    # ── Serialization ────────────────────────────────────────────
    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": [n.to_dict() for n in self._nodes.values()],
                "edges": [e.to_dict() for e in self._edges],
                "communities": [c.to_dict() for c in self._communities],
                "stats": self._graph_stats_unlocked(),
            }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. ENTITY EXTRACTION (Lightweight NLP)                          ║
# ╚════════════════════════════════════════════════════════════════════╝

# Patterns for entity recognition
_PROPER_NOUN = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')
_ACRONYM = re.compile(r'\b([A-Z]{2,6})\b')
_TOOL_PATTERN = re.compile(r'\b([A-Z][a-z]+(?:\.[a-z]+)+)\b')  # e.g., "Apache.Kafka"
_RELATION_PATTERNS = [
    (re.compile(r'(\w+)\s+depends?\s+on\s+(\w+)', re.IGNORECASE), "depends_on"),
    (re.compile(r'(\w+)\s+(?:is\s+)?part\s+of\s+(\w+)', re.IGNORECASE), "part_of"),
    (re.compile(r'(\w+)\s+causes?\s+(\w+)', re.IGNORECASE), "causes"),
    (re.compile(r'(\w+)\s+(?:is\s+)?similar\s+to\s+(\w+)', re.IGNORECASE), "similar_to"),
    (re.compile(r'(\w+)\s+(?:integrates?|connects?)\s+(?:with\s+)?(\w+)', re.IGNORECASE), "related_to"),
    (re.compile(r'(\w+)\s+(?:uses?|utilizes?)\s+(\w+)', re.IGNORECASE), "depends_on"),
]

# Common English stop-words to filter from entity extraction
_STOP_ENTITIES = {
    "The", "This", "That", "These", "Those", "It", "Its", "They",
    "We", "Our", "You", "Your", "He", "She", "But", "And", "For",
    "From", "With", "Into", "About", "After", "Before", "During",
    "When", "Where", "What", "Which", "Who", "How", "Why", "Not",
    "Also", "Each", "Every", "Most", "Some", "Any", "All", "Both",
    "Many", "Much", "Such", "Very", "More", "Other",
}


def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract named entities from text using pattern matching.

    Returns a list of {label, entity_type, mentions} dicts.
    """
    entities: Dict[str, Dict[str, Any]] = {}

    # Proper nouns
    for m in _PROPER_NOUN.finditer(text):
        label = m.group(1)
        if label in _STOP_ENTITIES or len(label) < 3:
            continue
        key = label.lower()
        if key not in entities:
            entities[key] = {"label": label, "entity_type": "concept", "mentions": 0}
        entities[key]["mentions"] += 1

    # Acronyms
    for m in _ACRONYM.finditer(text):
        label = m.group(1)
        if len(label) < 2:
            continue
        key = label.lower()
        if key not in entities:
            entities[key] = {"label": label, "entity_type": "concept", "mentions": 0}
        entities[key]["mentions"] += 1

    return list(entities.values())


def extract_relationships(text: str) -> List[Dict[str, str]]:
    """Extract relationships from text using pattern matching."""
    rels: List[Dict[str, str]] = []
    for pattern, relation in _RELATION_PATTERNS:
        for m in pattern.finditer(text):
            source = m.group(1)
            target = m.group(2)
            if source.lower() not in _STOP_ENTITIES and target.lower() not in _STOP_ENTITIES:
                rels.append({
                    "source": source,
                    "target": target,
                    "relation": relation,
                })
    return rels


def build_graph_from_text(text: str) -> KnowledgeGraph:
    """
    Full pipeline: extract entities + relationships → build graph
    → compute centrality → detect communities.
    """
    graph = KnowledgeGraph()

    # Extract and add entities as nodes
    entities = extract_entities(text)
    for ent in entities:
        node_id = hashlib.md5(ent["label"].lower().encode()).hexdigest()[:12]
        graph.add_node(GraphNode(
            node_id=node_id,
            label=ent["label"],
            entity_type=ent["entity_type"],
            mention_count=ent["mentions"],
        ))

    # Extract and add relationships as edges
    rels = extract_relationships(text)
    # Build label→node_id lookup
    label_to_id: Dict[str, str] = {}
    for ent in entities:
        nid = hashlib.md5(ent["label"].lower().encode()).hexdigest()[:12]
        label_to_id[ent["label"].lower()] = nid

    for rel in rels:
        src_id = label_to_id.get(rel["source"].lower())
        tgt_id = label_to_id.get(rel["target"].lower())
        if src_id and tgt_id:
            graph.add_edge(GraphEdge(
                source=src_id,
                target=tgt_id,
                relation=rel["relation"],
            ))

    # Compute metrics
    graph.compute_centrality()
    graph.detect_communities()

    return graph


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. CONVENIENCE                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

# Global graph instance
_graph: Optional[KnowledgeGraph] = None
_graph_lock = threading.Lock()


def get_graph() -> KnowledgeGraph:
    global _graph
    with _graph_lock:
        if _graph is None:
            _graph = KnowledgeGraph()
        return _graph


def knowledge_graph_summary() -> Dict[str, Any]:
    """Return summary of the global knowledge graph."""
    g = get_graph()
    return g.graph_stats()
