# ────────────────────────────────────────────────────────────────────
# graph.py — In-Memory Knowledge Graph with Community Detection
# ────────────────────────────────────────────────────────────────────
"""
Implements the GraphRAG paradigm adapted for Praxis's tool-recommendation
domain.  Instead of Neo4j (external dependency), we build a lightweight,
in-memory **property graph** from the tool knowledge base on startup:

    Nodes  = Tools  (with full metadata)
    Edges  = Typed relationships:
        • shares_category  — same category membership
        • integrates_with  — declared in tool.integrations
        • similar_audience — same skill-level + overlapping use-cases
        • competes_with    — high overlap but not integrated

Graph capabilities:
    1. **Entity resolution** — canonical tool names, fuzzy matching
    2. **Community detection** — Leiden-inspired modularity clustering
    3. **Local search**  — k-hop traversal from anchor node(s)
    4. **Global search** — community-level summaries
    5. **Multi-hop paths** — find bridging tools between two concepts
    6. **Relationship scoring** — weighted edge traversal

The graph auto-rebuilds whenever the TOOLS list changes (via hash check).
"""
from __future__ import annotations

import math
import time
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

log = logging.getLogger("praxis.graph")

# ── Imports from sibling modules ──
try:
    from .data import TOOLS
    from .tools import Tool
except Exception:
    try:
        from data import TOOLS
        from tools import Tool
    except Exception:
        TOOLS = []
        Tool = None


# ╔════════════════════════════════════════════════════════════════════╗
# ║  DATA STRUCTURES                                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class GraphNode:
    """A node in the knowledge graph representing a tool."""
    name: str
    tool: Any                       # Tool object
    categories: FrozenSet[str] = field(default_factory=frozenset)
    community_id: int = -1

    @property
    def id(self) -> str:
        return self.name.lower()


@dataclass
class GraphEdge:
    """Weighted, typed edge between two tool-nodes."""
    source: str            # tool name (lowered)
    target: str
    rel_type: str          # shares_category | integrates_with | similar_audience | competes_with
    weight: float = 1.0
    detail: str = ""       # human-readable explanation


@dataclass
class Community:
    """A cluster of tightly-connected tool-nodes."""
    id: int
    members: List[str]               # tool names
    categories: List[str]            # dominant categories
    summary: str = ""                # generated thematic summary
    density: float = 0.0             # internal edge density


@dataclass
class TraversalResult:
    """Output of a graph search."""
    anchor: str
    hops: int
    nodes: List[str]
    edges: List[GraphEdge]
    communities_touched: List[int]
    elapsed_ms: int = 0


# ╔════════════════════════════════════════════════════════════════════╗
# ║  KNOWLEDGE GRAPH                                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

class ToolGraph:
    """
    In-memory knowledge graph built from the Praxis tool database.

    Usage::

        g = get_graph()
        result = g.local_search("Slack", hops=2)
        comms  = g.global_search("compliance security")
        path   = g.find_path("ChatGPT", "Datadog")
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.adj: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.communities: List[Community] = []
        self._hash: int = 0
        self._built = False

    # ── Build ──

    def build(self, tools: Optional[List] = None):
        """Construct the full graph from the tool knowledge base."""
        t0 = time.perf_counter_ns()
        pool = tools or TOOLS
        new_hash = hash(tuple(t.name for t in pool))
        if self._built and new_hash == self._hash:
            return  # no changes
        self._hash = new_hash

        self.nodes.clear()
        self.edges.clear()
        self.adj.clear()
        self.communities.clear()

        # Phase 1: Create nodes
        for tool in pool:
            cats = frozenset(c.lower() for c in getattr(tool, "categories", []))
            node = GraphNode(name=tool.name, tool=tool, categories=cats)
            self.nodes[node.id] = node

        # Phase 2: Extract edges
        self._extract_integration_edges(pool)
        self._extract_category_edges(pool)
        self._extract_audience_edges(pool)
        self._extract_competition_edges(pool)

        # Phase 3: Community detection
        self._detect_communities()

        # Phase 4: Generate community summaries
        self._summarise_communities()

        self._built = True
        elapsed = int((time.perf_counter_ns() - t0) / 1_000_000)
        log.info(
            "graph built: %d nodes, %d edges, %d communities in %dms",
            len(self.nodes), len(self.edges),
            len(self.communities), elapsed,
        )

    def _add_edge(self, src: str, tgt: str, rel: str,
                  weight: float = 1.0, detail: str = ""):
        src_l, tgt_l = src.lower(), tgt.lower()
        if src_l == tgt_l:
            return
        if src_l not in self.nodes or tgt_l not in self.nodes:
            return
        # Avoid duplicate typed edges
        for e in self.adj[src_l]:
            if e.target == tgt_l and e.rel_type == rel:
                return
        edge = GraphEdge(src_l, tgt_l, rel, weight, detail)
        self.edges.append(edge)
        self.adj[src_l].append(edge)
        # Add reverse for undirected relationships
        if rel in ("shares_category", "similar_audience", "competes_with"):
            rev = GraphEdge(tgt_l, src_l, rel, weight, detail)
            self.edges.append(rev)
            self.adj[tgt_l].append(rev)

    # ── Edge extraction ──

    def _extract_integration_edges(self, tools):
        """integrates_with — declared integrations between tools."""
        name_set = {t.name.lower() for t in tools}
        for tool in tools:
            for integ in getattr(tool, "integrations", []):
                if integ.lower() in name_set:
                    self._add_edge(
                        tool.name, integ, "integrates_with",
                        weight=2.0,
                        detail=f"{tool.name} integrates with {integ}",
                    )

    def _extract_category_edges(self, tools):
        """shares_category — tools in the same category cluster."""
        cat_members: Dict[str, List[str]] = defaultdict(list)
        for tool in tools:
            for cat in getattr(tool, "categories", []):
                cat_members[cat.lower()].append(tool.name)

        for cat, members in cat_members.items():
            if len(members) < 2:
                continue
            # Limit combinatorial explosion for large categories
            group = members[:15]
            for a, b in combinations(group, 2):
                self._add_edge(
                    a, b, "shares_category",
                    weight=1.0,
                    detail=f"Both in '{cat}' category",
                )

    def _extract_audience_edges(self, tools):
        """similar_audience — same skill-level + overlapping use-cases."""
        for i, ta in enumerate(tools):
            for tb in tools[i + 1:]:
                if getattr(ta, "skill_level", "") != getattr(tb, "skill_level", ""):
                    continue
                uc_a = set(u.lower() for u in getattr(ta, "use_cases", []))
                uc_b = set(u.lower() for u in getattr(tb, "use_cases", []))
                overlap = uc_a & uc_b
                if len(overlap) >= 2:
                    self._add_edge(
                        ta.name, tb.name, "similar_audience",
                        weight=0.5 + len(overlap) * 0.3,
                        detail=f"Shared use-cases: {', '.join(list(overlap)[:3])}",
                    )

    def _extract_competition_edges(self, tools):
        """competes_with — high category overlap but NOT integrated."""
        for i, ta in enumerate(tools):
            cats_a = set(c.lower() for c in getattr(ta, "categories", []))
            integs_a = set(n.lower() for n in getattr(ta, "integrations", []))
            for tb in tools[i + 1:]:
                cats_b = set(c.lower() for c in getattr(tb, "categories", []))
                overlap = cats_a & cats_b
                if len(overlap) < 2:
                    continue
                # Not integrated = likely competitors
                if tb.name.lower() not in integs_a:
                    jaccard = len(overlap) / max(len(cats_a | cats_b), 1)
                    if jaccard >= 0.4:
                        self._add_edge(
                            ta.name, tb.name, "competes_with",
                            weight=jaccard,
                            detail=f"Competing in: {', '.join(list(overlap)[:3])}",
                        )

    # ── Community detection (Leiden-inspired greedy modularity) ──

    def _detect_communities(self):
        """
        Lightweight community detection via greedy modularity optimisation.

        This approximates the Leiden algorithm without the full complexity:
        1. Start each node in its own community
        2. Iteratively merge nodes into the community that maximizes
           modularity gain
        3. Stop when no further improvement is possible
        """
        node_ids = list(self.nodes.keys())
        if not node_ids:
            return

        # Initialise: each node in its own community
        community_of: Dict[str, int] = {n: i for i, n in enumerate(node_ids)}
        total_weight = sum(e.weight for e in self.edges) or 1.0

        # Node strength (sum of edge weights)
        strength: Dict[str, float] = defaultdict(float)
        for e in self.edges:
            strength[e.source] += e.weight

        improved = True
        iterations = 0
        max_iter = 20

        while improved and iterations < max_iter:
            improved = False
            iterations += 1
            for node in node_ids:
                current_comm = community_of[node]
                # Compute modularity gain of moving to each neighbor's community
                neighbor_comms: Dict[int, float] = defaultdict(float)
                for edge in self.adj.get(node, []):
                    nc = community_of[edge.target]
                    neighbor_comms[nc] += edge.weight

                best_gain = 0.0
                best_comm = current_comm

                ki = strength[node]
                for comm, w_in in neighbor_comms.items():
                    if comm == current_comm:
                        continue
                    # Simplified modularity gain
                    sigma_tot = sum(
                        strength[n] for n, c in community_of.items() if c == comm
                    )
                    delta_q = (w_in / total_weight) - (sigma_tot * ki) / (2 * total_weight ** 2)
                    if delta_q > best_gain:
                        best_gain = delta_q
                        best_comm = comm

                if best_comm != current_comm:
                    community_of[node] = best_comm
                    improved = True

        # Collect communities
        comm_members: Dict[int, List[str]] = defaultdict(list)
        for node, comm in community_of.items():
            comm_members[comm].append(node)

        # Filter singletons and re-index
        self.communities = []
        for idx, (_, members) in enumerate(
            sorted(comm_members.items(), key=lambda x: -len(x[1]))
        ):
            if len(members) < 2:
                continue

            # Dominant categories
            cat_counts: Dict[str, int] = defaultdict(int)
            for m in members:
                n = self.nodes.get(m)
                if n:
                    for c in n.categories:
                        cat_counts[c] += 1
            top_cats = sorted(cat_counts, key=cat_counts.get, reverse=True)[:4]

            # Density
            internal_edges = sum(
                1 for e in self.edges
                if e.source in set(members) and e.target in set(members)
            )
            max_edges = len(members) * (len(members) - 1) or 1
            density = internal_edges / max_edges

            comm = Community(
                id=idx,
                members=[self.nodes[m].name for m in members],
                categories=top_cats,
                density=round(density, 3),
            )
            self.communities.append(comm)

            # Tag nodes
            for m in members:
                if m in self.nodes:
                    self.nodes[m].community_id = idx

    def _summarise_communities(self):
        """Generate human-readable summaries for each community."""
        for comm in self.communities:
            cats = ", ".join(comm.categories[:3]) if comm.categories else "general"
            count = len(comm.members)
            top_names = ", ".join(comm.members[:4])
            if count > 4:
                top_names += f" (+{count - 4} more)"
            comm.summary = (
                f"Cluster of {count} tools focused on {cats}. "
                f"Key members: {top_names}. "
                f"Internal density: {comm.density:.0%}."
            )

    # ══════════════════════════════════════════════════════════════════
    # QUERY INTERFACE
    # ══════════════════════════════════════════════════════════════════

    def resolve_entity(self, name: str) -> Optional[str]:
        """Fuzzy entity resolution — canonical node ID or None."""
        low = name.lower().strip()
        if low in self.nodes:
            return low
        # Partial / fuzzy match
        from difflib import get_close_matches
        matches = get_close_matches(low, list(self.nodes.keys()), n=1, cutoff=0.6)
        return matches[0] if matches else None

    def local_search(self, anchor_name: str, hops: int = 2,
                     rel_filter: Optional[Set[str]] = None,
                     max_nodes: int = 30) -> TraversalResult:
        """
        Fan-out BFS from an anchor node, collecting k-hop neighbors.

        Parameters
        ----------
        anchor_name : tool name to start from
        hops        : maximum BFS depth
        rel_filter  : if set, only traverse edges of these types
        max_nodes   : hard cap on returned nodes
        """
        t0 = time.perf_counter_ns()
        anchor = self.resolve_entity(anchor_name)
        if not anchor:
            return TraversalResult(anchor_name, hops, [], [], [], 0)

        visited: Set[str] = {anchor}
        collected_edges: List[GraphEdge] = []
        queue: deque = deque([(anchor, 0)])

        while queue and len(visited) < max_nodes:
            current, depth = queue.popleft()
            if depth >= hops:
                continue
            for edge in self.adj.get(current, []):
                if rel_filter and edge.rel_type not in rel_filter:
                    continue
                if edge.target not in visited:
                    visited.add(edge.target)
                    collected_edges.append(edge)
                    queue.append((edge.target, depth + 1))

        comms = list({
            self.nodes[n].community_id
            for n in visited if n in self.nodes and self.nodes[n].community_id >= 0
        })

        elapsed = int((time.perf_counter_ns() - t0) / 1_000_000)
        return TraversalResult(
            anchor=anchor,
            hops=hops,
            nodes=[self.nodes[n].name for n in visited if n in self.nodes],
            edges=collected_edges,
            communities_touched=comms,
            elapsed_ms=elapsed,
        )

    def global_search(self, query: str, top_n: int = 3) -> List[Community]:
        """
        Search across community summaries for thematic matches.

        Returns the top-N communities whose categories or summaries
        best match the query.
        """
        tokens = set(query.lower().split())
        scored: List[Tuple[Community, float]] = []

        for comm in self.communities:
            score = 0.0
            # Category match
            for cat in comm.categories:
                if cat in tokens:
                    score += 3.0
                elif any(t in cat for t in tokens):
                    score += 1.0
            # Summary keyword match
            summary_low = comm.summary.lower()
            for t in tokens:
                if t in summary_low:
                    score += 0.5
            # Member name match
            for member in comm.members:
                if member.lower() in tokens:
                    score += 5.0

            if score > 0:
                scored.append((comm, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_n]]

    def find_path(self, start: str, end: str,
                  max_depth: int = 4) -> Optional[List[GraphEdge]]:
        """
        BFS shortest path between two tools.

        Returns the list of edges forming the path, or None if
        no path exists within max_depth hops.
        """
        src = self.resolve_entity(start)
        tgt = self.resolve_entity(end)
        if not src or not tgt:
            return None
        if src == tgt:
            return []

        visited: Set[str] = {src}
        queue: deque = deque([(src, [])])

        while queue:
            current, path_so_far = queue.popleft()
            if len(path_so_far) >= max_depth:
                continue
            for edge in self.adj.get(current, []):
                if edge.target == tgt:
                    return path_so_far + [edge]
                if edge.target not in visited:
                    visited.add(edge.target)
                    queue.append((edge.target, path_so_far + [edge]))

        return None

    def get_competitors(self, tool_name: str) -> List[str]:
        """Direct competitors based on competes_with edges."""
        nid = self.resolve_entity(tool_name)
        if not nid:
            return []
        return [
            self.nodes[e.target].name
            for e in self.adj.get(nid, [])
            if e.rel_type == "competes_with" and e.target in self.nodes
        ]

    def get_integrations(self, tool_name: str) -> List[str]:
        """Direct integration partners."""
        nid = self.resolve_entity(tool_name)
        if not nid:
            return []
        return [
            self.nodes[e.target].name
            for e in self.adj.get(nid, [])
            if e.rel_type == "integrates_with" and e.target in self.nodes
        ]

    def get_community_members(self, tool_name: str) -> List[str]:
        """All tools in the same community."""
        nid = self.resolve_entity(tool_name)
        if not nid or nid not in self.nodes:
            return []
        cid = self.nodes[nid].community_id
        if cid < 0:
            return []
        for comm in self.communities:
            if comm.id == cid:
                return comm.members
        return []

    def enrich_tool_context(self, tool_name: str) -> Dict[str, Any]:
        """
        Assemble a rich context payload for a tool using graph data:
        integrations, competitors, community, and multi-hop neighbors.
        """
        nid = self.resolve_entity(tool_name)
        if not nid or nid not in self.nodes:
            return {"tool": tool_name, "found": False}

        node = self.nodes[nid]
        traversal = self.local_search(tool_name, hops=2, max_nodes=20)

        # Categorise edges by type
        edge_summary: Dict[str, List[str]] = defaultdict(list)
        for e in traversal.edges:
            target_name = self.nodes[e.target].name if e.target in self.nodes else e.target
            edge_summary[e.rel_type].append(target_name)

        # Community info
        comm_info = None
        if node.community_id >= 0:
            for c in self.communities:
                if c.id == node.community_id:
                    comm_info = {
                        "id": c.id,
                        "members": c.members,
                        "categories": c.categories,
                        "summary": c.summary,
                        "density": c.density,
                    }
                    break

        return {
            "tool": node.name,
            "found": True,
            "categories": list(node.categories),
            "integrates_with": edge_summary.get("integrates_with", []),
            "competes_with": edge_summary.get("competes_with", []),
            "shares_category": edge_summary.get("shares_category", [])[:8],
            "similar_audience": edge_summary.get("similar_audience", [])[:5],
            "community": comm_info,
            "graph_neighbors": len(traversal.nodes) - 1,
            "communities_touched": traversal.communities_touched,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the full graph for API / debug output."""
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "community_count": len(self.communities),
            "communities": [
                {
                    "id": c.id,
                    "members": c.members,
                    "categories": c.categories,
                    "summary": c.summary,
                    "density": c.density,
                }
                for c in self.communities
            ],
            "edge_types": dict(
                sorted(
                    defaultdict(
                        int,
                        ((e.rel_type, 1) for _ in [None]
                         for e in self.edges),
                    ).items()
                )
            ) if False else self._edge_type_counts(),
        }

    def _edge_type_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for e in self.edges:
            counts[e.rel_type] += 1
        return dict(counts)

    # ── Context-Aware Intent Transfer extensions ─────────────────

    def get_vertical_stack_tools(self, vertical_id: str) -> List[str]:
        """Return catalog-matched tools from a vertical's stack template.

        Looks up the vertical's recommended stack layers and maps them to
        actual tools in the graph via entity resolution and substring match.
        """
        try:
            from .verticals import recommend_vertical_stack
        except Exception:
            try:
                from verticals import recommend_vertical_stack  # type: ignore[no-redef]
            except Exception:
                return []

        stack = recommend_vertical_stack(vertical_id)
        if not stack:
            return []

        matched: List[str] = []
        layers = stack.get("stack_layers", [])
        for layer in layers:
            recommended = []
            if hasattr(layer, "recommended"):
                recommended = layer.recommended
            elif isinstance(layer, dict):
                recommended = layer.get("recommended", [])
            for rec in recommended:
                rec_lower = rec.lower()
                # Try entity resolution first
                resolved = self.resolve_entity(rec_lower)
                if resolved and resolved not in matched:
                    matched.append(resolved)
                    continue
                # Fallback: substring match against graph nodes
                for node_name in self.nodes:
                    if node_name in rec_lower or rec_lower in node_name:
                        if node_name not in matched:
                            matched.append(node_name)
        return matched

    def get_anchor_subgraph(
        self,
        anchor_tool: str,
        max_hops: int = 2,
    ) -> List[str]:
        """Bounded BFS along integrates_with edges from an anchor tool.

        Returns list of tool names reachable within max_hops via
        integration edges only.
        """
        result = self.local_search(
            anchor_tool, hops=max_hops,
            rel_filter={"integrates_with"},
        )
        if result is None:
            return []
        # result.nodes is List[str] of tool names
        return [n for n in result.nodes if n.lower() != anchor_tool.lower()]

    def prune_non_compliant(
        self,
        tool_pool: List[str],
        compliance_requirements: List[str],
    ) -> List[str]:
        """Remove tools that lack required compliance certifications.

        Checks each tool's metadata for compliance/certification fields.
        Tools not in the graph are preserved (benefit of the doubt).
        """
        if not compliance_requirements:
            return list(tool_pool)

        req_lower = {r.lower() for r in compliance_requirements}
        kept: List[str] = []

        for tool_name in tool_pool:
            node = self.nodes.get(tool_name.lower())
            if node is None or node.tool is None:
                # Not in graph — keep by default
                kept.append(tool_name)
                continue

            tool_obj = node.tool
            # Check compliance fields on the tool object
            tool_compliance: List[str] = []
            for attr in ("compliance", "certifications", "security"):
                val = getattr(tool_obj, attr, None)
                if isinstance(val, list):
                    tool_compliance.extend(v.lower() for v in val)
                elif isinstance(val, str) and val:
                    tool_compliance.append(val.lower())

            # Also check tags/categories for compliance signals
            for attr in ("tags", "categories"):
                val = getattr(tool_obj, attr, None)
                if isinstance(val, (list, set, frozenset)):
                    tool_compliance.extend(v.lower() for v in val)

            # If we have no metadata, keep (don't over-prune)
            if not tool_compliance:
                kept.append(tool_name)
                continue

            # Check if any required certification is mentioned
            has_required = any(
                req in comp or comp in req
                for req in req_lower
                for comp in tool_compliance
            )
            if has_required:
                kept.append(tool_name)
            # else: pruned — tool lacks required compliance

        return kept


# ╔════════════════════════════════════════════════════════════════════╗
# ║  SINGLETON                                                      ║
# ╚════════════════════════════════════════════════════════════════════╝

_graph_instance: Optional[ToolGraph] = None


def get_graph(tools: Optional[List] = None) -> ToolGraph:
    """Return the singleton ToolGraph, building it on first call."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = ToolGraph()
    if not _graph_instance._built:
        _graph_instance.build(tools)
    return _graph_instance


def rebuild_graph(tools: Optional[List] = None):
    """Force a full rebuild (call after tool-list mutation)."""
    global _graph_instance
    _graph_instance = ToolGraph()
    _graph_instance.build(tools)
    return _graph_instance
