# ────────────────────────────────────────────────────────────────────
# prism.py — Precision-Recall Iterative Selection Mechanism
# ────────────────────────────────────────────────────────────────────
"""
Implements the PRISM multi-agent framework adapted for Praxis — three
specialised agents operating in an iterative feedback loop:

    1. **Analyzer**  — Decomposes complex queries into structured
       sub-questions with entities, constraints, and temporal bounds.
       Does NOT search.  Its output guides the downstream agents.

    2. **Selector** — Precision-focused.  Takes the raw retrieval pool
       and aggressively filters to only definitively-relevant tools,
       cross-referencing the Analyzer's sub-questions.

    3. **Adder**    — Recall-focused.  Audits what the Selector
       *rejected*, searching for bridging evidence, complementary
       tools, or associative links that the Selector missed.

The Selector ↔ Adder loop runs iteratively (configurable rounds)
until the evidence set stabilises or the time budget expires.

Also incorporates:
    • **SELF-RAG / CRAG** critique-generate loop
    • **Faithfulness scoring** — ground every claim in retrieved data
    • **Conflict-aware synthesis** — surfaces contradictions
    • **FACT-AUDIT verification** — cross-checks tool claims
"""
from __future__ import annotations

import time
import re
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("praxis.prism")

# ── Sibling imports ──
try:
    from .retrieval import hybrid_search, context_precision, context_recall, f1_score
    _RETRIEVAL_OK = True
except Exception:
    try:
        from retrieval import hybrid_search, context_precision, context_recall, f1_score
        _RETRIEVAL_OK = True
    except Exception:
        _RETRIEVAL_OK = False

try:
    from .graph import get_graph
    _GRAPH_OK = True
except Exception:
    try:
        from graph import get_graph
        _GRAPH_OK = True
    except Exception:
        _GRAPH_OK = False

try:
    from .interpreter import interpret
except Exception:
    try:
        from interpreter import interpret
    except Exception:
        interpret = None

try:
    from .engine import score_tool, find_tools
except Exception:
    try:
        from engine import score_tool, find_tools
    except Exception:
        score_tool = find_tools = None

try:
    from .philosophy import assess_transparency, assess_freedom
    _PHIL_OK = True
except Exception:
    try:
        from philosophy import assess_transparency, assess_freedom
        _PHIL_OK = True
    except Exception:
        _PHIL_OK = False

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None


def _llm_ok() -> bool:
    if _cfg:
        try:
            return _cfg.llm_available()
        except Exception:
            pass
    return False


def _llm_call(system: str, user: str, max_tokens: int = 600,
              temperature: float = 0.3) -> str:
    """Unified LLM call — OpenAI or Anthropic."""
    if not _cfg:
        raise RuntimeError("config unavailable")
    provider = _cfg.get("llm_provider", "openai")

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=_cfg.get("openai_api_key"))
        resp = client.chat.completions.create(
            model=_cfg.get("openai_model", "gpt-4o-mini"),
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            max_tokens=max_tokens, temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    else:
        import anthropic
        client = anthropic.Anthropic(api_key=_cfg.get("anthropic_api_key"))
        resp = client.messages.create(
            model=_cfg.get("anthropic_model", "claude-sonnet-4-20250514"),
            system=system, max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()


# ╔════════════════════════════════════════════════════════════════════╗
# ║  DATA STRUCTURES                                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class SubQuestion:
    """A single sub-question decomposed by the Analyzer."""
    text: str
    entities: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    priority: int = 1        # 1 = high, 3 = low


@dataclass
class AnalysisResult:
    """Output of the Analyzer agent."""
    original_query: str
    sub_questions: List[SubQuestion]
    key_entities: List[str]
    temporal_bounds: Optional[str] = None
    query_complexity: str = "simple"    # simple | multi-hop | comparative


@dataclass
class EvidenceItem:
    """A tool + relevance metadata tracked through the PRISM loop."""
    tool: Any
    relevance_score: float = 0.0
    source: str = ""           # "hybrid" | "graph" | "adder_rescue"
    matched_sub_questions: List[int] = field(default_factory=list)
    faithfulness: float = 1.0  # 0-1 how grounded in actual data
    conflicts: List[str] = field(default_factory=list)


@dataclass
class PRISMResult:
    """Final output of the PRISM pipeline."""
    query: str
    analysis: AnalysisResult
    evidence: List[EvidenceItem]
    selected_tools: List[Any]
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    iterations: int = 0
    fact_audit: Dict[str, str] = field(default_factory=dict)   # tool → verdict
    conflicts_found: List[str] = field(default_factory=list)
    elapsed_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "query_complexity": self.analysis.query_complexity,
            "sub_questions": [
                {"text": sq.text, "entities": sq.entities,
                 "constraints": sq.constraints, "priority": sq.priority}
                for sq in self.analysis.sub_questions
            ],
            "key_entities": self.analysis.key_entities,
            "selected_tools": [
                {
                    "name": e.tool.name,
                    "relevance_score": round(e.relevance_score, 3),
                    "source": e.source,
                    "matched_sub_questions": e.matched_sub_questions,
                    "faithfulness": e.faithfulness,
                    "conflicts": e.conflicts,
                }
                for e in self.evidence
            ],
            "precision": round(self.precision, 3),
            "recall": round(self.recall, 3),
            "f1": round(self.f1, 3),
            "iterations": self.iterations,
            "fact_audit": self.fact_audit,
            "conflicts_found": self.conflicts_found,
            "elapsed_ms": self.elapsed_ms,
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  AGENT 1 — ANALYZER                                             ║
# ╚════════════════════════════════════════════════════════════════════╝

_ANALYZER_SYSTEM = """You are a search-query analyzer. Decompose the user's 
query into a JSON object with:
{
  "sub_questions": [{"text": "...", "entities": [...], "constraints": [...], "priority": 1}],
  "key_entities": [...],
  "temporal_bounds": null or "...",
  "query_complexity": "simple" | "multi-hop" | "comparative"
}
Be precise and exhaustive. Each sub-question should be independently answerable."""


def _analyze_llm(query: str) -> AnalysisResult:
    """LLM-powered query decomposition."""
    import json
    raw = _llm_call(_ANALYZER_SYSTEM, f"Query: {query}", max_tokens=500)
    # Parse JSON
    data = json.loads(raw) if raw.startswith("{") else json.loads(
        re.search(r'\{.*\}', raw, re.DOTALL).group()
    )
    sqs = [
        SubQuestion(
            text=sq["text"],
            entities=sq.get("entities", []),
            constraints=sq.get("constraints", []),
            priority=sq.get("priority", 1),
        )
        for sq in data.get("sub_questions", [])
    ]
    return AnalysisResult(
        original_query=query,
        sub_questions=sqs or [SubQuestion(text=query)],
        key_entities=data.get("key_entities", []),
        temporal_bounds=data.get("temporal_bounds"),
        query_complexity=data.get("query_complexity", "simple"),
    )


def _analyze_local(query: str) -> AnalysisResult:
    """
    Deterministic query decomposition — no LLM.

    Heuristics:
    - Split on commas / conjunctions for multi-part queries
    - Detect entities (tool names, proper nouns)
    - Detect constraints (budget, compliance, skill, negatives)
    - Classify complexity
    """
    raw = query.lower()
    intent = interpret(query) if interpret else {}
    keywords = intent.get("keywords", [])
    entities_raw = intent.get("entities", [])
    negatives = intent.get("negatives", [])
    multi = intent.get("multi_intents", [])
    industry = intent.get("industry")

    sub_questions: List[SubQuestion] = []
    all_entities: List[str] = list(entities_raw)
    all_constraints: List[str] = []
    complexity = "simple"

    # ── Entity detection (tool names mentioned in query) ──
    from .data import TOOLS as _tools
    tool_names_lower = {t.name.lower(): t.name for t in _tools}
    for tn_low, tn in tool_names_lower.items():
        if tn_low in raw and tn not in all_entities:
            all_entities.append(tn)

    # ── Constraint detection ──
    budget_match = re.search(r'\$\s*(\d+)', raw)
    if budget_match:
        all_constraints.append(f"budget_cap=${budget_match.group(1)}")

    compliance_kw = {"hipaa", "gdpr", "soc2", "soc 2", "fedramp", "iso", "compliance"}
    for ck in compliance_kw:
        if ck in raw:
            all_constraints.append(f"compliance:{ck}")

    skill_kw = {"beginner", "intermediate", "advanced", "no-code", "non-technical", "easy"}
    for sk in skill_kw:
        if sk in raw:
            all_constraints.append(f"skill:{sk}")

    lockin_kw = {"lock-in", "lockin", "vendor lock", "portability", "portable"}
    if any(lk in raw for lk in lockin_kw):
        all_constraints.append("low_vendor_lock_in")

    neg_prefix = {"avoid", "avoiding", "without", "exclude", "no "}
    negative_items = list(negatives)
    for np in neg_prefix:
        if np in raw:
            # Extract what follows
            idx = raw.find(np)
            tail = raw[idx + len(np):].strip().split(",")[0].split(" and ")[0]
            words = tail.split()[:4]
            if words:
                negative_items.append(" ".join(words))

    if negative_items:
        all_constraints.extend([f"exclude:{n}" for n in negative_items])

    # ── Sub-question generation ──
    if multi and len(multi) > 1:
        complexity = "multi-hop"
        for i, sub in enumerate(multi):
            sub_clean = sub.strip()
            sub_questions.append(SubQuestion(
                text=sub_clean,
                entities=[e for e in all_entities if e.lower() in sub_clean.lower()],
                constraints=[],
                priority=i + 1,
            ))
    else:
        # Generate angled sub-questions
        primary_intent = intent.get("intent") or ""

        # Core question
        sub_questions.append(SubQuestion(
            text=query,
            entities=all_entities,
            constraints=all_constraints,
            priority=1,
        ))

        # Angle: industry
        if industry:
            sub_questions.append(SubQuestion(
                text=f"What {primary_intent or 'tools'} work best for {industry}?",
                entities=[],
                constraints=[f"industry:{industry}"],
                priority=2,
            ))

        # Angle: comparative (if 2+ entities mentioned)
        if len(all_entities) >= 2:
            complexity = "comparative"
            sub_questions.append(SubQuestion(
                text=f"How do {all_entities[0]} and {all_entities[1]} compare?",
                entities=all_entities[:2],
                constraints=[],
                priority=2,
            ))

        # Angle: compliance
        compliance_found = [c for c in all_constraints if c.startswith("compliance:")]
        if compliance_found:
            complexity = "multi-hop"
            labels = [c.split(":")[1] for c in compliance_found]
            sub_questions.append(SubQuestion(
                text=f"Which tools satisfy {', '.join(labels)} compliance?",
                entities=[],
                constraints=compliance_found,
                priority=1,
            ))

        # Angle: budget
        if budget_match:
            sub_questions.append(SubQuestion(
                text=f"Affordable options under ${budget_match.group(1)}/month?",
                entities=[],
                constraints=[f"budget_cap=${budget_match.group(1)}"],
                priority=2,
            ))

    if len(sub_questions) > 3 or all_constraints:
        complexity = "multi-hop"

    return AnalysisResult(
        original_query=query,
        sub_questions=sub_questions[:6],
        key_entities=all_entities,
        temporal_bounds=None,
        query_complexity=complexity,
    )


def analyze(query: str) -> AnalysisResult:
    """Public analyzer entry — LLM with local fallback."""
    if _llm_ok():
        try:
            return _analyze_llm(query)
        except Exception as exc:
            log.warning("LLM analyzer failed, falling back: %s", exc)
    return _analyze_local(query)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  AGENT 2 — SELECTOR  (Precision)                                ║
# ╚════════════════════════════════════════════════════════════════════╝

def _score_relevance(tool, sub_questions: List[SubQuestion]) -> Tuple[float, List[int]]:
    """
    Score how relevant a tool is to the analyzer's sub-questions.

    Returns (relevance_score, list_of_matching_sq_indexes).
    """
    score = 0.0
    matched_idxs: List[int] = []
    tool_text = " ".join([
        (tool.name or "").lower(),
        (tool.description or "").lower(),
        " ".join(c.lower() for c in getattr(tool, "categories", [])),
        " ".join(t.lower() for t in getattr(tool, "tags", [])),
        " ".join(k.lower() for k in getattr(tool, "keywords", [])),
        " ".join(u.lower() for u in getattr(tool, "use_cases", [])),
    ])
    tool_cats = {c.lower() for c in getattr(tool, "categories", [])}
    tool_compliance = {c.lower() for c in getattr(tool, "compliance", [])}

    for idx, sq in enumerate(sub_questions):
        sq_tokens = set(sq.text.lower().split())
        sq_score = 0.0

        # Keyword overlap
        for token in sq_tokens:
            if len(token) < 3:
                continue
            if token in tool_text:
                sq_score += 1.0

        # Entity match (high value)
        for entity in sq.entities:
            if entity.lower() in tool_text:
                sq_score += 5.0

        # Constraint satisfaction
        for constraint in sq.constraints:
            if constraint.startswith("compliance:"):
                req = constraint.split(":")[1].upper()
                if req in {c.upper() for c in getattr(tool, "compliance", [])}:
                    sq_score += 4.0
                elif req == "COMPLIANCE" and tool_compliance:
                    sq_score += 2.0
            elif constraint.startswith("industry:"):
                ind = constraint.split(":")[1]
                if ind in tool_text:
                    sq_score += 3.0
            elif constraint.startswith("budget_cap="):
                try:
                    cap = int(constraint.split("=")[1].replace("$", ""))
                    pricing = getattr(tool, "pricing", {})
                    starter = pricing.get("starter", 0)
                    if pricing.get("free_tier") or (isinstance(starter, (int, float)) and 0 < starter <= cap):
                        sq_score += 3.0
                except (ValueError, TypeError):
                    pass
            elif constraint.startswith("skill:"):
                req_skill = constraint.split(":")[1]
                if getattr(tool, "skill_level", "") == req_skill:
                    sq_score += 2.0
            elif constraint.startswith("exclude:"):
                ex = constraint.split(":")[1].lower()
                if ex in tool_text:
                    sq_score -= 5.0

        # Priority weighting
        priority_mult = {1: 1.5, 2: 1.0, 3: 0.7}.get(sq.priority, 1.0)
        sq_score *= priority_mult

        if sq_score > 1.0:
            matched_idxs.append(idx)
        score += max(sq_score, 0.0)

    return score, matched_idxs


def select(pool: List[EvidenceItem], analysis: AnalysisResult,
           threshold: float = 0.3) -> Tuple[List[EvidenceItem], List[EvidenceItem]]:
    """
    Selector agent — aggressively filter to high-precision evidence.

    Returns (selected, rejected).
    """
    if not pool:
        return [], []

    # Score each item
    for item in pool:
        rel, matched = _score_relevance(item.tool, analysis.sub_questions)
        item.relevance_score = rel
        item.matched_sub_questions = matched

    # Normalise scores
    max_score = max(i.relevance_score for i in pool) or 1.0
    for item in pool:
        item.relevance_score /= max_score

    # Split by threshold
    selected = [i for i in pool if i.relevance_score >= threshold]
    rejected = [i for i in pool if i.relevance_score < threshold]

    # Ensure we keep at least top-3 even if all below threshold
    if len(selected) < 3 and pool:
        pool_sorted = sorted(pool, key=lambda x: x.relevance_score, reverse=True)
        selected = pool_sorted[:3]
        s_names = {i.tool.name for i in selected}
        rejected = [i for i in pool if i.tool.name not in s_names]

    log.info("selector: %d selected / %d rejected (threshold=%.2f)",
             len(selected), len(rejected), threshold)
    return selected, rejected


# ╔════════════════════════════════════════════════════════════════════╗
# ║  AGENT 3 — ADDER  (Recall)                                      ║
# ╚════════════════════════════════════════════════════════════════════╝

def add_missing(
    rejected: List[EvidenceItem],
    selected: List[EvidenceItem],
    analysis: AnalysisResult,
) -> List[EvidenceItem]:
    """
    Adder agent — recover bridging evidence from the rejected pool.

    Searches for:
    1. Tools that satisfy uncovered sub-questions
    2. Integration bridges (tools that connect selected tools)
    3. Category coverage gaps
    """
    recovered: List[EvidenceItem] = []
    selected_names = {e.tool.name.lower() for e in selected}

    # 1. Which sub-questions are uncovered?
    covered_sqs = set()
    for e in selected:
        covered_sqs.update(e.matched_sub_questions)

    uncovered = [
        (idx, sq)
        for idx, sq in enumerate(analysis.sub_questions)
        if idx not in covered_sqs
    ]

    if uncovered:
        for item in rejected:
            _, matched = _score_relevance(item.tool, analysis.sub_questions)
            for idx, _ in uncovered:
                if idx in matched and item.tool.name.lower() not in selected_names:
                    item.source = "adder_rescue"
                    item.matched_sub_questions = matched
                    recovered.append(item)
                    selected_names.add(item.tool.name.lower())
                    break

    # 2. Graph-based bridging
    if _GRAPH_OK and selected:
        try:
            graph = get_graph()
            # Find tools that integrate with multiple selected tools
            for item in rejected:
                if item.tool.name.lower() in selected_names:
                    continue
                integrations = set(
                    n.lower() for n in getattr(item.tool, "integrations", [])
                )
                bridge_count = len(integrations & selected_names)
                if bridge_count >= 2:
                    item.source = "adder_rescue"
                    item.relevance_score = 0.5 + bridge_count * 0.1
                    recovered.append(item)
                    selected_names.add(item.tool.name.lower())
        except Exception as exc:
            log.debug("adder graph bridging failed: %s", exc)

    # 3. Category coverage gaps
    selected_cats: Set[str] = set()
    for e in selected:
        selected_cats.update(c.lower() for c in getattr(e.tool, "categories", []))

    # Detect required categories from constraints
    required_cats: Set[str] = set()
    for sq in analysis.sub_questions:
        for c in sq.constraints:
            if c.startswith("industry:"):
                required_cats.add(c.split(":")[1].lower())
            if c.startswith("compliance:"):
                required_cats.add("security")

    missing_cats = required_cats - selected_cats
    if missing_cats:
        for item in rejected:
            if item.tool.name.lower() in selected_names:
                continue
            item_cats = {c.lower() for c in getattr(item.tool, "categories", [])}
            if item_cats & missing_cats:
                item.source = "adder_rescue"
                recovered.append(item)
                selected_names.add(item.tool.name.lower())

    log.info("adder: recovered %d items (uncovered_sqs=%d, missing_cats=%s)",
             len(recovered), len(uncovered), missing_cats or "{}")
    return recovered


# ╔════════════════════════════════════════════════════════════════════╗
# ║  FACT-AUDIT VERIFICATION                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

def _fact_audit_tool(tool) -> Tuple[str, List[str]]:
    """
    Verify claims about a tool against known data.

    Returns (verdict, conflicts) where verdict is
    SUPPORTS | REFUTES | INSUFFICIENT_EVIDENCE.
    """
    conflicts: List[str] = []
    positive_signals = 0
    negative_signals = 0

    # Check pricing consistency
    pricing = getattr(tool, "pricing", {})
    if pricing.get("free_tier") and pricing.get("starter", 0) == 0 and pricing.get("pro", 0) == 0:
        if pricing.get("enterprise") != "custom":
            conflicts.append("Claims free tier but no paid plans listed — data may be incomplete")
            negative_signals += 1
        else:
            positive_signals += 1

    # Check compliance claims
    compliance = getattr(tool, "compliance", [])
    if compliance:
        positive_signals += 1  # Has documented compliance
    else:
        # If categories suggest security but no compliance listed
        cats = {c.lower() for c in getattr(tool, "categories", [])}
        if "security" in cats and not compliance:
            conflicts.append("Categorised as security but no compliance certifications listed")
            negative_signals += 1

    # Check vendor intelligence if available
    if _PHIL_OK:
        try:
            transparency = assess_transparency(tool)
            freedom = assess_freedom(tool)

            # Cross-check claims
            t_score = transparency.get("score", 50)
            f_score = freedom.get("score", 50)

            if t_score < 40:
                conflicts.append(f"Low transparency score ({t_score}/100) — verify claims independently")
                negative_signals += 1
            else:
                positive_signals += 1

            if f_score < 30:
                conflicts.append(f"High vendor lock-in risk (freedom={f_score}/100)")
                negative_signals += 1

            # Check for contradictions between pricing and lock-in
            if pricing.get("free_tier") and f_score < 40:
                conflicts.append("Offers free tier but high lock-in — likely freemium trap")
        except Exception:
            pass

    # Check freshness
    if hasattr(tool, "is_stale") and tool.is_stale(max_days=180):
        conflicts.append("Tool data may be outdated (>6 months since last update)")
        negative_signals += 1

    # Verdict
    if negative_signals > positive_signals:
        verdict = "REFUTES" if negative_signals >= 3 else "INSUFFICIENT_EVIDENCE"
    elif positive_signals > 0:
        verdict = "SUPPORTS"
    else:
        verdict = "INSUFFICIENT_EVIDENCE"

    return verdict, conflicts


def fact_audit(evidence: List[EvidenceItem]) -> Dict[str, str]:
    """
    Run FACT-AUDIT across all evidence items.

    Returns {tool_name: verdict} map.
    """
    results: Dict[str, str] = {}
    all_conflicts: List[str] = []

    for item in evidence:
        verdict, conflicts = _fact_audit_tool(item.tool)
        results[item.tool.name] = verdict
        item.conflicts = conflicts
        item.faithfulness = {
            "SUPPORTS": 1.0,
            "INSUFFICIENT_EVIDENCE": 0.6,
            "REFUTES": 0.2,
        }.get(verdict, 0.5)
        all_conflicts.extend(
            f"[{item.tool.name}] {c}" for c in conflicts
        )

    verdicts = list(results.values())
    log.info("fact_audit: %d tools — %d SUPPORTS, %d INSUFFICIENT, %d REFUTES",
             len(results),
             verdicts.count("SUPPORTS"),
             verdicts.count("INSUFFICIENT_EVIDENCE"),
             verdicts.count("REFUTES"))
    return results


# ╔════════════════════════════════════════════════════════════════════╗
# ║  SELF-RAG / CRAG — Critique-Generate Loop                       ║
# ╚════════════════════════════════════════════════════════════════════╝

def self_critique(
    evidence: List[EvidenceItem],
    analysis: AnalysisResult,
) -> Dict[str, Any]:
    """
    Self-RAG inspired critique of the current evidence set.

    Checks:
    1. Sub-question coverage
    2. Category diversity
    3. Faithfulness scores
    4. Conflict density
    5. Whether a corrective re-search is needed
    """
    n = len(evidence)
    if n == 0:
        return {
            "coverage": 0.0, "diversity": 0.0, "faithfulness": 0.0,
            "needs_correction": True, "correction_reason": "No evidence found",
        }

    # 1. Sub-question coverage
    total_sqs = len(analysis.sub_questions)
    covered_sqs = set()
    for e in evidence:
        covered_sqs.update(e.matched_sub_questions)
    coverage = len(covered_sqs) / max(total_sqs, 1)

    # 2. Category diversity
    all_cats: Set[str] = set()
    for e in evidence:
        all_cats.update(c.lower() for c in getattr(e.tool, "categories", []))
    diversity = min(len(all_cats) / 5.0, 1.0)   # cap at 5 unique categories = 100%

    # 3. Average faithfulness
    faithfulness = sum(e.faithfulness for e in evidence) / n

    # 4. Conflict density
    total_conflicts = sum(len(e.conflicts) for e in evidence)
    conflict_rate = total_conflicts / max(n, 1)

    # 5. Correction needed?
    needs_correction = False
    reason = ""
    if coverage < 0.5:
        needs_correction = True
        uncovered_idxs = [i for i in range(total_sqs) if i not in covered_sqs]
        uncovered_texts = [analysis.sub_questions[i].text for i in uncovered_idxs
                           if i < len(analysis.sub_questions)]
        reason = f"Low coverage ({coverage:.0%}) — uncovered: {'; '.join(uncovered_texts[:2])}"
    elif faithfulness < 0.4:
        needs_correction = True
        reason = f"Low faithfulness ({faithfulness:.2f}) — too many unverified claims"
    elif conflict_rate > 2.0:
        needs_correction = True
        reason = f"High conflict rate ({conflict_rate:.1f}/tool)"

    return {
        "coverage": round(coverage, 3),
        "diversity": round(diversity, 3),
        "faithfulness": round(faithfulness, 3),
        "conflict_rate": round(conflict_rate, 2),
        "needs_correction": needs_correction,
        "correction_reason": reason,
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  ORCHESTRATOR — Full PRISM pipeline                              ║
# ╚════════════════════════════════════════════════════════════════════╝

def prism_search(
    query: str,
    top_n: int = 8,
    max_iterations: int = 2,
    budget_ms: int = 10_000,
    profile=None,
) -> PRISMResult:
    """
    Full PRISM pipeline:

    1. **Analyze** — decompose query
    2. **Retrieve** — hybrid search + graph enrichment
    3. **Select** — precision filter
    4. **Add** — recall recovery (iterative)
    5. **Fact-Audit** — verify claims
    6. **Self-Critique** — CRAG correction if needed

    Parameters
    ----------
    query       : natural language search query
    top_n       : max tools to return
    max_iterations : Selector↔Adder rounds
    budget_ms   : time budget in milliseconds
    profile     : optional user profile for fit scoring
    """
    t0 = time.perf_counter_ns()

    def _elapsed():
        return int((time.perf_counter_ns() - t0) / 1_000_000)

    # ── Phase 1: Analyze ──
    analysis = analyze(query)
    log.info("prism: analyzed '%s' → %d sub-questions, complexity=%s",
             query, len(analysis.sub_questions), analysis.query_complexity)

    # ── Phase 2: Retrieve ──
    intent = interpret(query) if interpret else {}
    keywords = intent.get("keywords", [])
    raw_query = intent.get("raw", query)

    # Hybrid retrieval
    retrieval_pool: List[EvidenceItem] = []
    if _RETRIEVAL_OK:
        hr = hybrid_search(keywords, raw_query=raw_query, top_n=top_n * 4)
        for tool, score in hr.tools:
            retrieval_pool.append(EvidenceItem(tool=tool, relevance_score=score, source="hybrid"))

    # Fallback to engine.find_tools if hybrid retrieval is unavailable or got nothing
    if not retrieval_pool and find_tools:
        results = find_tools(intent, top_n=top_n * 3)
        for tool in results:
            retrieval_pool.append(EvidenceItem(tool=tool, relevance_score=0.5, source="engine"))

    # Graph enrichment — add tools from local search of detected entities
    if _GRAPH_OK and analysis.key_entities:
        try:
            graph = get_graph()
            seen = {e.tool.name.lower() for e in retrieval_pool}
            for entity in analysis.key_entities[:3]:
                traversal = graph.local_search(entity, hops=2, max_nodes=10)
                for node_name in traversal.nodes:
                    if node_name.lower() not in seen:
                        nid = node_name.lower()
                        if nid in graph.nodes:
                            retrieval_pool.append(EvidenceItem(
                                tool=graph.nodes[nid].tool,
                                relevance_score=0.3,
                                source="graph",
                            ))
                            seen.add(nid)
        except Exception as exc:
            log.debug("graph enrichment failed: %s", exc)

    if not retrieval_pool:
        return PRISMResult(
            query=query, analysis=analysis, evidence=[], selected_tools=[],
            elapsed_ms=_elapsed(),
        )

    # ── Phase 3+4: Iterative Select ↔ Add ──
    selected = retrieval_pool
    rejected: List[EvidenceItem] = []
    iterations = 0

    for i in range(max_iterations):
        if _elapsed() > budget_ms:
            log.info("prism: budget exceeded at iteration %d", i)
            break

        selected, rejected = select(selected, analysis)
        additions = add_missing(rejected, selected, analysis)
        iterations = i + 1

        if not additions:
            break   # stable — no new evidence found
        selected.extend(additions)

    # ── Phase 5: Fact-Audit ──
    audit = fact_audit(selected)

    # ── Phase 6: Self-Critique ──
    critique = self_critique(selected, analysis)

    # Corrective re-search if needed
    if critique["needs_correction"] and _elapsed() < budget_ms * 0.8:
        log.info("prism: triggering corrective re-search: %s",
                 critique["correction_reason"])
        # Try graph-based rescue for uncovered sub-questions
        if _GRAPH_OK:
            try:
                graph = get_graph()
                seen = {e.tool.name.lower() for e in selected}
                for sq in analysis.sub_questions:
                    comms = graph.global_search(sq.text, top_n=2)
                    for comm in comms:
                        for member_name in comm.members[:3]:
                            if member_name.lower() not in seen:
                                nid = member_name.lower()
                                if nid in graph.nodes:
                                    new_item = EvidenceItem(
                                        tool=graph.nodes[nid].tool,
                                        relevance_score=0.4,
                                        source="adder_rescue",
                                    )
                                    _, matched = _score_relevance(
                                        new_item.tool, analysis.sub_questions
                                    )
                                    new_item.matched_sub_questions = matched
                                    selected.append(new_item)
                                    seen.add(nid)
            except Exception as exc:
                log.debug("corrective graph search failed: %s", exc)

            # Re-audit additions
            fact_audit(selected)

    # ── Final ranking ──
    # Sort by: faithfulness * relevance * sub-question coverage
    for item in selected:
        sq_bonus = 1.0 + len(item.matched_sub_questions) * 0.15
        item.relevance_score = item.relevance_score * item.faithfulness * sq_bonus

    selected.sort(key=lambda x: x.relevance_score, reverse=True)
    final = selected[:top_n]

    # ── Compute metrics ──
    # For internal eval, use selected names vs. the full sub-question entity set
    retrieved_names = [e.tool.name for e in final]
    relevant_proxy = analysis.key_entities or retrieved_names[:3]
    prec = context_precision(retrieved_names, relevant_proxy) if _RETRIEVAL_OK else 0.0
    rec  = context_recall(retrieved_names, relevant_proxy) if _RETRIEVAL_OK else 0.0

    # Collect all conflicts
    all_conflicts = []
    for e in final:
        for c in e.conflicts:
            all_conflicts.append(f"[{e.tool.name}] {c}")

    result = PRISMResult(
        query=query,
        analysis=analysis,
        evidence=final,
        selected_tools=[e.tool for e in final],
        precision=prec,
        recall=rec,
        f1=f1_score(prec, rec) if _RETRIEVAL_OK else 0.0,
        iterations=iterations,
        fact_audit=audit,
        conflicts_found=all_conflicts,
        elapsed_ms=_elapsed(),
    )

    log.info("prism: done in %dms — %d tools, %d iterations, P=%.2f R=%.2f F1=%.2f",
             result.elapsed_ms, len(final), iterations,
             result.precision, result.recall, result.f1)
    return result
