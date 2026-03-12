# --------------- Praxis HybridRAG Orchestrator v2 ---------------
"""
v18 · Enterprise-Grade Solidification

Unified retrieval orchestrator that combines:
    • **Sparse BM25** from retrieval.py
    • **Dense TF-IDF / embedding** from intelligence.py
    • **GraphRAG community** from graph.py
    • **Vector store** via ports.VectorStore

The orchestrator uses a lightweight **routing agent** to decide which
retrieval lanes to activate based on query classification.

Architecture (from the report):
    ┌─────────────┐
    │ Query Router │ ─── classify → entity / concept / hybrid
    └─────┬───────┘
          ├──→ Sparse (BM25)
          ├──→ Dense  (TF-IDF / embeddings)
          ├──→ Graph  (community traversal)
          └──→ Reciprocal Rank Fusion → top-N results

This module augments (not replaces) the existing ``retrieval.py`` and
``graph.py`` with a higher-level orchestration layer.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger("praxis.hybrid_retrieval_v2")

# ── Sibling imports ──
try:
    from .retrieval import (
        hybrid_search as _legacy_hybrid,
        sparse_rank as _sparse_rank,
        dense_rank as _dense_rank,
        reciprocal_rank_fusion as _rrf,
        classify_query as _classify_query,
    )
    _RETRIEVAL_OK = True
except Exception:
    try:
        from retrieval import (
            hybrid_search as _legacy_hybrid,
            sparse_rank as _sparse_rank,
            dense_rank as _dense_rank,
            reciprocal_rank_fusion as _rrf,
            classify_query as _classify_query,
        )
        _RETRIEVAL_OK = True
    except Exception:
        _RETRIEVAL_OK = False
        _legacy_hybrid = _sparse_rank = _dense_rank = _rrf = _classify_query = None

try:
    from .graph import ToolGraph
    _GRAPH_OK = True
except Exception:
    try:
        from graph import ToolGraph
        _GRAPH_OK = True
    except Exception:
        _GRAPH_OK = False
        ToolGraph = None

try:
    from .data import TOOLS
except Exception:
    try:
        from data import TOOLS
    except Exception:
        TOOLS = []


# -----------------------------------------------------------------------
# Retrieval Lane Results
# -----------------------------------------------------------------------

@dataclass
class LaneResult:
    """Output from a single retrieval lane."""
    lane_name: str
    results: List[Tuple[Any, float]]  # (tool, score)
    elapsed_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratedResult:
    """Final fused result from the orchestrator."""
    tools: List[Tuple[Any, float]]
    lanes_used: List[str]
    query_classification: str
    alpha: float
    elapsed_ms: float
    lane_details: Dict[str, LaneResult] = field(default_factory=dict)

    @property
    def names(self) -> List[str]:
        return [t.name for t, _ in self.tools]


# -----------------------------------------------------------------------
# Query Router
# -----------------------------------------------------------------------

class QueryRouter:
    """Classifies queries and selects which retrieval lanes to activate.

    Classification tiers:
        • ``entity``  — exact tool/vendor name → favour sparse + graph
        • ``concept`` — abstract need → favour dense + graph
        • ``hybrid``  — mix → all lanes
    """

    def route(
        self,
        raw_query: str,
        query_terms: List[str],
    ) -> Dict[str, Any]:
        """Return routing decision: lanes to activate + weights."""
        if _RETRIEVAL_OK and _classify_query:
            qclass = _classify_query(raw_query or " ".join(query_terms))
            qtype = qclass.get("query_type", "mixed")
            alpha = qclass.get("alpha", 0.5)
        else:
            qtype = "mixed"
            alpha = 0.5

        # Map query type to lane activation
        if qtype == "entity":
            lanes = ["sparse", "graph"]
            weights = {"sparse": 0.7, "graph": 0.3, "dense": 0.0}
        elif qtype == "concept":
            lanes = ["dense", "graph"]
            weights = {"sparse": 0.2, "dense": 0.5, "graph": 0.3}
        else:
            lanes = ["sparse", "dense", "graph"]
            weights = {"sparse": 0.35, "dense": 0.35, "graph": 0.30}

        # Degrade gracefully if graph is unavailable
        if not _GRAPH_OK and "graph" in lanes:
            lanes.remove("graph")
            remaining = sum(weights[l] for l in lanes)
            if remaining > 0:
                for l in lanes:
                    weights[l] = weights[l] / remaining

        return {
            "query_type": qtype,
            "alpha": alpha,
            "lanes": lanes,
            "weights": weights,
        }


# -----------------------------------------------------------------------
# Orchestrator
# -----------------------------------------------------------------------

class HybridRAGOrchestrator:
    """Three-lane retrieval orchestrator with dynamic routing."""

    def __init__(
        self,
        graph: Optional[Any] = None,
        vector_store: Optional[Any] = None,
        router: Optional[QueryRouter] = None,
    ):
        self.graph = graph
        self.vector_store = vector_store
        self.router = router or QueryRouter()
        self._graph_instance: Optional[Any] = None

    def _get_graph(self):
        """Lazily load or build the graph."""
        if self.graph is not None:
            return self.graph
        if self._graph_instance is not None:
            return self._graph_instance
        if _GRAPH_OK and ToolGraph is not None:
            try:
                g = ToolGraph()
                g.build_from_tools(TOOLS)
                self._graph_instance = g
                return g
            except Exception as e:
                log.debug("graph build failed: %s", e)
        return None

    def search(
        self,
        query_terms: List[str],
        raw_query: str = "",
        *,
        top_n: int = 10,
        alpha_override: Optional[float] = None,
        tools: Optional[List] = None,
    ) -> OrchestratedResult:
        """Execute multi-lane retrieval and fuse results."""
        t0 = time.perf_counter_ns()
        pool = tools or TOOLS

        # 1. Route
        routing = self.router.route(raw_query, query_terms)
        lanes = routing["lanes"]
        weights = routing["weights"]
        alpha = alpha_override if alpha_override is not None else routing["alpha"]

        lane_details: Dict[str, LaneResult] = {}
        all_results: List[Tuple[List[Tuple[Any, float]], float]] = []  # (results, weight)
        fan_out = max(top_n * 4, 40)

        # 2. Execute lanes
        if "sparse" in lanes and _RETRIEVAL_OK and _sparse_rank:
            lt0 = time.perf_counter_ns()
            try:
                sparse = _sparse_rank(query_terms, pool, fan_out)
                elapsed = (time.perf_counter_ns() - lt0) / 1_000_000
                lr = LaneResult("sparse", sparse, elapsed)
                lane_details["sparse"] = lr
                all_results.append((sparse, weights.get("sparse", 0.35)))
            except Exception as e:
                log.warning("sparse retrieval failed: %s", e)

        if "dense" in lanes and _RETRIEVAL_OK and _dense_rank:
            lt0 = time.perf_counter_ns()
            try:
                dense = _dense_rank(query_terms, pool, fan_out)
                elapsed = (time.perf_counter_ns() - lt0) / 1_000_000
                lr = LaneResult("dense", dense, elapsed)
                lane_details["dense"] = lr
                all_results.append((dense, weights.get("dense", 0.35)))
            except Exception as e:
                log.warning("dense retrieval failed: %s", e)

        if "graph" in lanes:
            lt0 = time.perf_counter_ns()
            try:
                graph_results = self._graph_search(query_terms, pool, top_n=fan_out)
                elapsed = (time.perf_counter_ns() - lt0) / 1_000_000
                lr = LaneResult("graph", graph_results, elapsed)
                lane_details["graph"] = lr
                all_results.append((graph_results, weights.get("graph", 0.30)))
            except Exception as e:
                log.warning("graph retrieval failed: %s", e)

        # 3. Fuse — weighted RRF
        merged = self._weighted_rrf(all_results, k=60)

        total_ms = (time.perf_counter_ns() - t0) / 1_000_000

        result = OrchestratedResult(
            tools=merged[:top_n],
            lanes_used=list(lane_details.keys()),
            query_classification=routing["query_type"],
            alpha=alpha,
            elapsed_ms=round(total_ms, 1),
            lane_details=lane_details,
        )

        log.info(
            "hybrid_rag_v2: lanes=%s type=%s alpha=%.2f → %d results in %.1fms",
            result.lanes_used, result.query_classification, alpha,
            len(result.tools), total_ms,
        )
        return result

    # ── Graph lane ──

    def _graph_search(
        self,
        query_terms: List[str],
        pool: List,
        top_n: int = 40,
    ) -> List[Tuple[Any, float]]:
        """Graph community search: find tools related via knowledge graph."""
        g = self._get_graph()
        if g is None:
            return []

        hits: Dict[str, float] = {}
        query_lower = " ".join(query_terms).lower()

        # Community-based search
        try:
            communities = g.global_search(query_lower, top_n=5)
            for comm in communities:
                for member_name in comm.members if hasattr(comm, 'members') else []:
                    hits[member_name] = hits.get(member_name, 0) + 0.5
        except Exception:
            pass

        # Neighbor expansion: if any query term matches a tool name, get neighbors
        tool_names = {t.name.lower(): t for t in pool}
        for term in query_terms:
            tl = term.lower()
            if tl in tool_names:
                try:
                    neighbors = g.neighbors(tl) if hasattr(g, 'neighbors') else []
                    for n in neighbors:
                        hits[n] = hits.get(n, 0) + 0.7
                except Exception:
                    pass

        # Map hits back to tool objects
        results: List[Tuple[Any, float]] = []
        for name, score in sorted(hits.items(), key=lambda x: -x[1]):
            tool = tool_names.get(name.lower())
            if tool:
                results.append((tool, score))

        return results[:top_n]

    # ── Weighted RRF ──

    @staticmethod
    def _weighted_rrf(
        lane_results: List[Tuple[List[Tuple[Any, float]], float]],
        k: int = 60,
    ) -> List[Tuple[Any, float]]:
        """Weighted Reciprocal Rank Fusion across multiple lanes.

        ``score(d) = Σ_lane weight_lane * (1 / (k + rank_lane(d)))``
        """
        fused: Dict[str, Tuple[Any, float]] = {}  # tool_name → (tool, score)

        for lane_results_list, weight in lane_results:
            for rank, (tool, _score) in enumerate(lane_results_list, start=1):
                name = getattr(tool, 'name', str(tool))
                rrf_score = weight * (1.0 / (k + rank))
                if name in fused:
                    old_tool, old_score = fused[name]
                    fused[name] = (old_tool, old_score + rrf_score)
                else:
                    fused[name] = (tool, rrf_score)

        # Sort by fused score descending
        return sorted(fused.values(), key=lambda x: -x[1])


# -----------------------------------------------------------------------
# Module-level singleton
# -----------------------------------------------------------------------

_orchestrator: Optional[HybridRAGOrchestrator] = None


def get_orchestrator(**kwargs) -> HybridRAGOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HybridRAGOrchestrator(**kwargs)
    return _orchestrator


def hybrid_search_v2(
    query_terms: List[str],
    raw_query: str = "",
    *,
    top_n: int = 10,
    **kwargs,
) -> OrchestratedResult:
    """Convenience wrapper around the singleton orchestrator."""
    return get_orchestrator().search(
        query_terms, raw_query, top_n=top_n, **kwargs,
    )
