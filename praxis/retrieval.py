# ────────────────────────────────────────────────────────────────────
# retrieval.py — Hybrid Dense-Sparse Retrieval with Reciprocal Rank Fusion
# ────────────────────────────────────────────────────────────────────
"""
Implements the Dual-Encoder Hybrid Retrieval architecture described in the
cognitive-search specification:

    1. **Sparse lexical scorer** — BM25-style term-frequency scoring over
       tool descriptions, categories, tags, use-cases.  Exact keyword hits
       and morphological expansion are favoured.

    2. **Dense semantic scorer** — Lightweight embedding similarity using
       TF-IDF vectors from intelligence.py (upgradeable to transformer
       embeddings when LLM keys are present, or a local sentence-transformer
       is available).

    3. **Reciprocal Rank Fusion (RRF)** — Merges the two ranked lists by
       relative position rather than raw score, eliminating the score-scale
       incompatibility between sparse and dense rankings.

    4. **Dynamic alpha weighting** — A classifier detects whether a query
       is entity-heavy (exact match) or concept-heavy (exploratory) and
       shifts fusion weight accordingly.

    5. **Evaluation metrics** — Context Precision, Context Recall, and NDCG
       helpers for agentic self-evaluation.

The module is a drop-in enhancement for engine.py.  It can be used
stand-alone or orchestrated by reason.py / prism.py.
"""
from __future__ import annotations

import math
import re
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.retrieval")

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

try:
    from .intelligence import get_tfidf_index, expand_synonyms
    _INTEL_AVAILABLE = True
except Exception:
    try:
        from intelligence import get_tfidf_index, expand_synonyms
        _INTEL_AVAILABLE = True
    except Exception:
        _INTEL_AVAILABLE = False

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None


def _w(key: str, fallback):
    if _cfg:
        try:
            return _cfg.get(key, fallback)
        except Exception:
            pass
    return fallback


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. SPARSE LEXICAL SCORER  (BM25-ish)                           ║
# ╚════════════════════════════════════════════════════════════════════╝

# Pre-computed IDF numerator (log ratio) — lazily built on first call
_idf_cache: Dict[str, float] = {}
_corpus_built = False


def _build_corpus_idf():
    """Build inverse document frequency from all tool text.  Called once."""
    global _idf_cache, _corpus_built
    if _corpus_built:
        return
    N = max(len(TOOLS), 1)
    doc_freq: Dict[str, int] = defaultdict(int)
    for tool in TOOLS:
        terms = _tool_terms(tool)
        unique_terms = set(terms)
        for t in unique_terms:
            doc_freq[t] += 1
    for term, df in doc_freq.items():
        _idf_cache[term] = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
    _corpus_built = True


def _tool_terms(tool) -> List[str]:
    """Flatten every text field of a tool into lowered terms."""
    parts: List[str] = []
    for attr in ("name", "description"):
        parts.extend((getattr(tool, attr, "") or "").lower().split())
    for attr in ("categories", "tags", "keywords", "use_cases"):
        for v in getattr(tool, attr, []):
            parts.extend(str(v).lower().split())
    return parts


def _bm25_score(tool, query_terms: List[str], *, k1: float = 1.5,
                b: float = 0.75, avg_dl: float = 40.0) -> float:
    """BM25F-style score for a single tool against query terms."""
    _build_corpus_idf()
    terms = _tool_terms(tool)
    dl = max(len(terms), 1)
    tf_map: Dict[str, int] = defaultdict(int)
    for t in terms:
        tf_map[t] += 1

    # Field boosts — category/tag hits count more
    cat_set = {c.lower() for c in getattr(tool, "categories", [])}
    tag_set = {t.lower() for t in getattr(tool, "tags", [])}
    kw_set  = {k.lower() for k in getattr(tool, "keywords", [])}
    name_low = (tool.name or "").lower()

    score = 0.0
    for qt in query_terms:
        qt = qt.lower()
        idf = _idf_cache.get(qt, 1.0)
        tf = tf_map.get(qt, 0)
        # BM25 core formula
        numerator = tf * (k1 + 1.0)
        denominator = tf + k1 * (1.0 - b + b * (dl / avg_dl))
        base = idf * (numerator / denominator) if denominator else 0.0

        # Field boosts (BM25F)
        if qt in cat_set:
            base *= 2.5
        elif qt in tag_set:
            base *= 2.0
        elif qt in kw_set:
            base *= 1.8
        elif qt in name_low:
            base *= 1.6

        score += base

    return score


def sparse_rank(query_terms: List[str], tools: Optional[List] = None,
                top_n: int = 20) -> List[Tuple[Any, float]]:
    """
    Sparse lexical ranking — returns ``[(tool, bm25_score), ...]``
    sorted descending by BM25F score.
    """
    pool = tools or TOOLS
    scored = []
    for tool in pool:
        s = _bm25_score(tool, query_terms)
        if s > 0:
            scored.append((tool, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. DENSE SEMANTIC SCORER  (TF-IDF → upgradeable to embeddings) ║
# ╚════════════════════════════════════════════════════════════════════╝

def dense_rank(query_terms: List[str], tools: Optional[List] = None,
               top_n: int = 20) -> List[Tuple[Any, float]]:
    """
    Dense semantic ranking via TF-IDF cosine similarity.

    When a real embedding model is available (local sentence-transformer
    or API key), this can be swapped to vector cosine.  The RRF layer
    above is agnostic to score magnitude.
    """
    pool = tools or TOOLS
    if not _INTEL_AVAILABLE:
        return []

    try:
        tfidf = get_tfidf_index()
    except Exception:
        return []

    # Expand synonyms for broader semantic reach
    expanded = query_terms[:]
    try:
        expanded = expand_synonyms(query_terms)
    except Exception:
        pass

    scored = []
    for tool in pool:
        try:
            s = tfidf.score(expanded, tool.name)
        except Exception:
            s = 0.0
        if s > 0:
            scored.append((tool, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. RECIPROCAL RANK FUSION  (RRF)                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def reciprocal_rank_fusion(
    *ranked_lists: List[Tuple[Any, float]],
    k: int = 60,
) -> List[Tuple[Any, float]]:
    """
    Merge multiple ranked lists using RRF.

    ``score(d) = Σ  1 / (k + rank_i(d))``

    RRF is score-magnitude-agnostic — it only uses rank position.

    **Deterministic tie-breaking** (v20 hardening):
    When two documents receive identical fused scores (highly probable
    with fractional addition), ties are broken by:
      1. Raw BM25 score from the first (sparse) list — higher is better
      2. Tool name (lexicographic) — guarantees idempotent ordering

    This ensures identical queries always return identical result
    orderings, which is critical for agentic context-window stability.
    """
    fusion: Dict[str, float] = defaultdict(float)
    tool_map: Dict[str, Any] = {}
    # Preserve raw sparse scores for deterministic tie-breaking
    sparse_scores: Dict[str, float] = {}

    for list_idx, rlist in enumerate(ranked_lists):
        for rank, (tool, raw_score) in enumerate(rlist, start=1):
            key = tool.name
            tool_map[key] = tool
            fusion[key] += 1.0 / (k + rank)
            # First list is the sparse (BM25) scorer by convention
            if list_idx == 0:
                sparse_scores[key] = raw_score

    merged = [(tool_map[name], score) for name, score in fusion.items()]
    # Deterministic sort: RRF desc → sparse score desc → name asc
    merged.sort(key=lambda x: (-x[1], -sparse_scores.get(x[0].name, 0.0), x[0].name))
    return merged


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. DYNAMIC ALPHA — query-type classifier                       ║
# ╚════════════════════════════════════════════════════════════════════╝

# Signals that the query is entity-heavy (favour sparse / exact)
_ENTITY_PATTERNS = [
    re.compile(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+\b'),  # ProperNoun ProperNoun
    re.compile(r'\b[A-Z]{2,}\b'),       # ALL-CAPS acronym
    re.compile(r'\b\d{3,}\b'),           # numeric IDs / error codes
    re.compile(r'\"[^\"]+\"'),           # quoted phrases
]

# Signals that the query is conceptual (favour dense / semantic)
_CONCEPT_SIGNALS = {
    "best", "top", "recommend", "suggest", "compare", "alternative",
    "similar", "like", "help", "need", "looking", "how", "what", "why",
    "strategy", "approach", "workflow", "stack", "ecosystem",
}


def classify_query(raw_query: str) -> Dict[str, Any]:
    """
    Classify a raw query and return an alpha-weighting recommendation.

    Returns::

        {
            "query_type":  "entity" | "concept" | "mixed",
            "alpha":       float,     # 0 = pure sparse, 1 = pure dense
            "entity_signals": [...],
            "concept_signals": [...],
        }
    """
    entity_hits: List[str] = []
    for pat in _ENTITY_PATTERNS:
        entity_hits.extend(pat.findall(raw_query))

    words = set(raw_query.lower().split())
    concept_hits = words & _CONCEPT_SIGNALS

    e = len(entity_hits)
    c = len(concept_hits)

    if e > 0 and c == 0:
        qtype, alpha = "entity", 0.2         # lean sparse
    elif c > 0 and e == 0:
        qtype, alpha = "concept", 0.8        # lean dense
    elif e > c:
        qtype, alpha = "mixed", 0.35
    elif c > e:
        qtype, alpha = "mixed", 0.65
    else:
        qtype, alpha = "mixed", 0.5

    return {
        "query_type": qtype,
        "alpha": alpha,
        "entity_signals": entity_hits,
        "concept_signals": list(concept_hits),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. HYBRID SEARCH — main entry point                            ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class RetrievalResult:
    """Structured output from hybrid_search."""
    tools: List[Tuple[Any, float]]
    sparse_count: int = 0
    dense_count: int = 0
    query_type: str = "mixed"
    alpha: float = 0.5
    fusion_method: str = "rrf"
    elapsed_ms: int = 0

    @property
    def names(self) -> List[str]:
        return [t.name for t, _ in self.tools]


def hybrid_search(
    query_terms: List[str],
    raw_query: str = "",
    tools: Optional[List] = None,
    top_n: int = 10,
    alpha_override: Optional[float] = None,
    fusion: str = "rrf",          # "rrf" | "linear"
) -> RetrievalResult:
    """
    Hybrid Dense-Sparse search with RRF or linear fusion.

    Parameters
    ----------
    query_terms : tokenised keywords for scoring
    raw_query   : original natural-language query (for alpha classifier)
    tools       : override the default TOOLS pool
    top_n       : how many results to return
    alpha_override : force a specific alpha (0 = sparse, 1 = dense)
    fusion      : ``"rrf"`` (score-agnostic) or ``"linear"`` (weighted sum)
    """
    t0 = time.perf_counter_ns()
    pool = tools or TOOLS

    # 1. Run both retrieval lanes
    fan_out = max(top_n * 4, 40)    # over-retrieve to let fusion do its job
    sparse_results = sparse_rank(query_terms, pool, fan_out)
    dense_results  = dense_rank(query_terms, pool, fan_out)

    # 2. Classify query for dynamic alpha
    qclass = classify_query(raw_query or " ".join(query_terms))
    alpha = alpha_override if alpha_override is not None else qclass["alpha"]

    # 3. Fuse
    if fusion == "rrf":
        merged = reciprocal_rank_fusion(sparse_results, dense_results)
    else:
        # Linear weighted combination
        merged = _linear_fusion(sparse_results, dense_results, alpha)

    elapsed = int((time.perf_counter_ns() - t0) / 1_000_000)

    result = RetrievalResult(
        tools=merged[:top_n],
        sparse_count=len(sparse_results),
        dense_count=len(dense_results),
        query_type=qclass["query_type"],
        alpha=alpha,
        fusion_method=fusion,
        elapsed_ms=elapsed,
    )
    log.info(
        "hybrid_search: %d sparse + %d dense → %d fused (%s, α=%.2f) in %dms",
        result.sparse_count, result.dense_count,
        len(result.tools), fusion, alpha, elapsed,
    )
    return result


def _linear_fusion(
    sparse: List[Tuple[Any, float]],
    dense: List[Tuple[Any, float]],
    alpha: float,
) -> List[Tuple[Any, float]]:
    """
    Linear weighted fusion.

    ``score(d) = (1 - α) · norm_sparse(d) + α · norm_dense(d)``
    """
    # Normalise each list to 0-1
    def _norm(lst):
        if not lst:
            return {}
        mx = max(s for _, s in lst) or 1.0
        return {t.name: (t, s / mx) for t, s in lst}

    s_map = _norm(sparse)
    d_map = _norm(dense)
    all_names = set(s_map) | set(d_map)

    combined = []
    for name in all_names:
        tool = s_map[name][0] if name in s_map else d_map[name][0]
        ss = s_map.get(name, (None, 0.0))[1]
        ds = d_map.get(name, (None, 0.0))[1]
        score = (1 - alpha) * ss + alpha * ds
        combined.append((tool, score))

    combined.sort(key=lambda x: x[1], reverse=True)
    return combined


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. EVALUATION METRICS                                          ║
# ╚════════════════════════════════════════════════════════════════════╝

def ndcg_at_k(relevance_scores: List[float], k: int = 10) -> float:
    """
    Normalised Discounted Cumulative Gain @ k.

    ``relevance_scores`` should be ordered by the system's ranking.
    Values are typically 0 / 1 / 2 (irrelevant / partial / perfect).
    """
    def _dcg(scores):
        return sum(
            (2 ** rel - 1) / math.log2(i + 2)
            for i, rel in enumerate(scores[:k])
        )
    dcg = _dcg(relevance_scores)
    ideal = _dcg(sorted(relevance_scores, reverse=True))
    return dcg / ideal if ideal else 0.0


def context_precision(retrieved_names: List[str],
                      relevant_names: List[str]) -> float:
    """Fraction of retrieved items that are relevant (signal-to-noise)."""
    if not retrieved_names:
        return 0.0
    relevant_set = {n.lower() for n in relevant_names}
    hits = sum(1 for n in retrieved_names if n.lower() in relevant_set)
    return hits / len(retrieved_names)


def context_recall(retrieved_names: List[str],
                   relevant_names: List[str]) -> float:
    """Fraction of relevant items that were actually retrieved."""
    if not relevant_names:
        return 1.0     # vacuously true
    retrieved_set = {n.lower() for n in retrieved_names}
    hits = sum(1 for n in relevant_names if n.lower() in retrieved_set)
    return hits / len(relevant_names)


def f1_score(precision: float, recall: float) -> float:
    """Harmonic mean of precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  7. CONVENIENCE — wrap the old engine interface                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def hybrid_find_tools(
    user_input,
    top_n: int = 5,
    profile=None,
    fusion: str = "rrf",
) -> List:
    """
    Drop-in replacement for ``engine.find_tools`` that uses
    hybrid retrieval + RRF under the hood.

    Accepts either a raw string or an ``interpret()`` dict.
    """
    try:
        from .interpreter import interpret
    except Exception:
        from interpreter import interpret
    try:
        from .engine import score_profile_fit
    except Exception:
        from engine import score_profile_fit

    if isinstance(user_input, dict):
        intent = user_input
    else:
        intent = interpret(str(user_input))

    keywords = intent.get("keywords", [])
    raw = intent.get("raw", "")
    negatives = {n.lower() for n in intent.get("negatives", [])}

    # Filter pool
    pool = [t for t in TOOLS
            if not any(n in (t.name or "").lower() for n in negatives)]

    # Hybrid retrieval
    hr = hybrid_search(keywords, raw_query=raw, tools=pool,
                       top_n=top_n * 3, fusion=fusion)

    # Apply profile fit + re-sort
    final = []
    for tool, rrf_score in hr.tools:
        prof_mod = score_profile_fit(tool, profile, intent) if profile else 0
        combined = rrf_score * 100 + prof_mod
        final.append((tool, combined))
    final.sort(key=lambda x: x[1], reverse=True)

    return [t for t, _ in final[:top_n]]
