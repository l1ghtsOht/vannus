# ─────────────────────────────────────────────────────────────
# reason.py — Agentic Reasoning Engine (2026 Architecture)
# ─────────────────────────────────────────────────────────────
"""
Turns Praxis from a scoring-based recommender into an iterative
reasoning advisor.  Implements a **Plan → Act → Observe → Reflect**
loop inspired by ReAct / Chain-of-Thought / Deep Research patterns.

Two execution modes:
    1. **LLM-backed** — uses OpenAI / Anthropic for planning,
       self-critique, and narrative synthesis.
    2. **Local heuristic** — zero-dependency fallback that still
       decomposes, multi-searches, and self-critiques using
       deterministic rules.  Always available.

Entry point:
    deep_reason(query, profile_id=None, max_steps=5, budget_ms=15000)
        → ReasoningResult (dict-serialisable dataclass)

The module is a pure-function layer sitting *above* the
interpreter/engine/explain/philosophy stack.  It orchestrates
existing Praxis subsystems as "tools" an agent can invoke.
"""

from __future__ import annotations

import os
import time
import re
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

log = logging.getLogger("praxis.reason")

# ── Praxis subsystem imports ──────────────────────────────────────────

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None

try:
    from .interpreter import interpret
except Exception:
    from interpreter import interpret

try:
    from .engine import find_tools
except Exception:
    from engine import find_tools

try:
    from .explain import explain_tool
except Exception:
    from explain import explain_tool

try:
    from .profile import load_profile
except Exception:
    try:
        from profile import load_profile
    except Exception:
        load_profile = None

try:
    from .philosophy import assess_transparency, assess_freedom
    _PHILOSOPHY = True
except Exception:
    try:
        from philosophy import assess_transparency, assess_freedom
        _PHILOSOPHY = True
    except Exception:
        _PHILOSOPHY = False

try:
    from .data import TOOLS
except Exception:
    from data import TOOLS

# ── v7 cognitive modules ──
try:
    from .retrieval import hybrid_search as _hybrid_search, RetrievalResult
    _RETRIEVAL_OK = True
except Exception:
    try:
        from retrieval import hybrid_search as _hybrid_search, RetrievalResult
        _RETRIEVAL_OK = True
    except Exception:
        _RETRIEVAL_OK = False

try:
    from .graph import get_graph as _get_graph
    _GRAPH_OK = True
except Exception:
    try:
        from graph import get_graph as _get_graph
        _GRAPH_OK = True
    except Exception:
        _GRAPH_OK = False

try:
    from .prism import prism_search as _prism_search, PRISMResult
    _PRISM_OK = True
except Exception:
    try:
        from prism import prism_search as _prism_search, PRISMResult
        _PRISM_OK = True
    except Exception:
        _PRISM_OK = False

# ── v8 vertical intelligence ──
try:
    from .verticals import (
        detect_verticals as _detect_verticals,
        extract_constraints as _extract_constraints,
        classify_workflow_tasks as _classify_workflow,
        check_anti_patterns as _check_anti_patterns,
        enrich_search_context as _enrich_vertical_context,
        filter_by_constraints as _filter_by_constraints,
        detect_compound_workflows as _detect_compounds,
    )
    _VERTICALS_OK = True
except Exception:
    try:
        from verticals import (
            detect_verticals as _detect_verticals,
            extract_constraints as _extract_constraints,
            classify_workflow_tasks as _classify_workflow,
            check_anti_patterns as _check_anti_patterns,
            enrich_search_context as _enrich_vertical_context,
            filter_by_constraints as _filter_by_constraints,
            detect_compound_workflows as _detect_compounds,
        )
        _VERTICALS_OK = True
    except Exception:
        _VERTICALS_OK = False

# ── v9 guardrails engine ──
try:
    from .guardrails import (
        score_safety as _score_safety,
        get_design_patterns as _get_design_patterns,
        recommend_guardrail_pattern as _recommend_guardrail,
    )
    _GUARDRAILS_OK = True
except Exception:
    try:
        from guardrails import (
            score_safety as _score_safety,
            get_design_patterns as _get_design_patterns,
            recommend_guardrail_pattern as _recommend_guardrail,
        )
        _GUARDRAILS_OK = True
    except Exception:
        _GUARDRAILS_OK = False

# ── v9 orchestration engine ──
try:
    from .orchestration import (
        detect_architecture_needs as _detect_architecture,
        classify_engineering_query as _classify_engineering,
        recommend_patterns as _recommend_arch_patterns,
        score_architecture as _score_architecture,
    )
    _ORCHESTRATION_OK = True
except Exception:
    try:
        from orchestration import (
            detect_architecture_needs as _detect_architecture,
            classify_engineering_query as _classify_engineering,
            recommend_patterns as _recommend_arch_patterns,
            score_architecture as _score_architecture,
        )
        _ORCHESTRATION_OK = True
    except Exception:
        _ORCHESTRATION_OK = False

# ── v10 resilience engine ──
try:
    from .resilience import (
        assess_resilience as _assess_resilience,
        score_vibe_coding_risk as _score_vibe_risk,
        recommend_static_analysis as _recommend_sa,
        get_hallucination_types as _get_hallucinations,
    )
    _RESILIENCE_OK = True
except Exception:
    try:
        from resilience import (
            assess_resilience as _assess_resilience,
            score_vibe_coding_risk as _score_vibe_risk,
            recommend_static_analysis as _recommend_sa,
            get_hallucination_types as _get_hallucinations,
        )
        _RESILIENCE_OK = True
    except Exception:
        _RESILIENCE_OK = False

# ── v11 metacognition engine ──
try:
    from .metacognition import (
        assess_metacognition as _assess_metacognition,
        score_structural_entropy as _score_entropy,
        detect_pathologies as _detect_pathologies,
        score_stylometry as _score_stylometry,
    )
    _METACOGNITION_OK = True
except Exception:
    try:
        from metacognition import (
            assess_metacognition as _assess_metacognition,
            score_structural_entropy as _score_entropy,
            detect_pathologies as _detect_pathologies,
            score_stylometry as _score_stylometry,
        )
        _METACOGNITION_OK = True
    except Exception:
        _METACOGNITION_OK = False

# ── v11b real self-introspection ──
try:
    from .introspect import (
        self_diagnose as _self_diagnose,
        compute_structural_entropy as _real_entropy,
        compute_stylometry as _real_stylometry,
    )
    _INTROSPECT_OK = True
except Exception:
    try:
        from introspect import (
            self_diagnose as _self_diagnose,
            compute_structural_entropy as _real_entropy,
            compute_stylometry as _real_stylometry,
        )
        _INTROSPECT_OK = True
    except Exception:
        _INTROSPECT_OK = False

# ── v12 Architecture of Awakening ──
try:
    from .awakening import (
        assess_awakening as _assess_awakening,
        detect_leaky_abstractions as _detect_leaks,
        score_vsd as _score_vsd,
        assess_supply_chain as _assess_supply_chain,
    )
    _AWAKENING_OK = True
except Exception:
    try:
        from awakening import (
            assess_awakening as _assess_awakening,
            detect_leaky_abstractions as _detect_leaks,
            score_vsd as _score_vsd,
            assess_supply_chain as _assess_supply_chain,
        )
        _AWAKENING_OK = True
    except Exception:
        _AWAKENING_OK = False

# ── v13 Self-Authorship ──
try:
    from .authorship import (
        assess_authorship as _assess_authorship,
        detect_dishonesty as _detect_dishonesty,
        score_ddd_maturity as _score_ddd,
        score_resilience_posture as _score_resilience_posture,
    )
    _AUTHORSHIP_OK = True
except Exception:
    try:
        from authorship import (
            assess_authorship as _assess_authorship,
            detect_dishonesty as _detect_dishonesty,
            score_ddd_maturity as _score_ddd,
            score_resilience_posture as _score_resilience_posture,
        )
        _AUTHORSHIP_OK = True
    except Exception:
        _AUTHORSHIP_OK = False

# ── v14 Architectural Enlightenment ──
try:
    from .enlightenment import (
        assess_enlightenment as _assess_enlightenment,
        score_unity as _score_unity,
        score_alignment as _score_alignment,
        score_interconnection as _score_interconnection,
    )
    _ENLIGHTENMENT_OK = True
except Exception:
    try:
        from enlightenment import (
            assess_enlightenment as _assess_enlightenment,
            score_unity as _score_unity,
            score_alignment as _score_alignment,
            score_interconnection as _score_interconnection,
        )
        _ENLIGHTENMENT_OK = True
    except Exception:
        _ENLIGHTENMENT_OK = False

# ── v15 The Conduit: Decoupled Cognitive Systems ──
try:
    from .conduit import (
        assess_conduit as _assess_conduit,
        score_decoupling as _score_decoupling,
        score_global_workspace as _score_gwt,
        score_integrated_information as _score_phi,
    )
    _CONDUIT_OK = True
except Exception:
    try:
        from conduit import (
            assess_conduit as _assess_conduit,
            score_decoupling as _score_decoupling,
            score_global_workspace as _score_gwt,
            score_integrated_information as _score_phi,
        )
        _CONDUIT_OK = True
    except Exception:
        _CONDUIT_OK = False

# ── v16 The Resonance: AGI as Continuous Human-Machine Relationship ──
try:
    from .resonance import (
        assess_resonance as _assess_resonance,
        score_temporal_substrate as _score_temporal,
        score_code_agency as _score_code_agency,
        score_latent_steering as _score_latent,
        score_conductor_dashboard as _score_conductor,
        score_meta_awareness as _score_meta_aware,
    )
    _RESONANCE_OK = True
except Exception:
    try:
        from resonance import (
            assess_resonance as _assess_resonance,
            score_temporal_substrate as _score_temporal,
            score_code_agency as _score_code_agency,
            score_latent_steering as _score_latent,
            score_conductor_dashboard as _score_conductor,
            score_meta_awareness as _score_meta_aware,
        )
        _RESONANCE_OK = True
    except Exception:
        _RESONANCE_OK = False

# ── v17 The Enterprise Engine: Billion-Dollar Decision Engine ─────────
try:
    from .enterprise import (
        assess_enterprise as _assess_enterprise,
        score_hybrid_graphrag as _score_graphrag,
        score_multi_agent as _score_multi_agent,
        score_mcp_bus as _score_mcp_bus,
        score_data_moat as _score_data_moat,
        score_monetization as _score_monetization,
        score_security_governance as _score_sec_gov,
    )
    _ENTERPRISE_OK = True
except Exception:
    try:
        from enterprise import (
            assess_enterprise as _assess_enterprise,
            score_hybrid_graphrag as _score_graphrag,
            score_multi_agent as _score_multi_agent,
            score_mcp_bus as _score_mcp_bus,
            score_data_moat as _score_data_moat,
            score_monetization as _score_monetization,
            score_security_governance as _score_sec_gov,
        )
        _ENTERPRISE_OK = True
    except Exception:
        _ENTERPRISE_OK = False


# ======================================================================
# Data structures
# ======================================================================

@dataclass
class ReasoningStep:
    """One atomic step in the reasoning trace."""
    phase: str          # "plan" | "act" | "observe" | "reflect" | "synthesize"
    action: str         # human-readable description of what happened
    detail: Any = None  # structured payload (search results, scores, etc.)
    elapsed_ms: int = 0


@dataclass
class ReasoningResult:
    """Complete output of a deep reasoning session."""
    query: str
    plan: List[str]                        # the research plan
    steps: List[ReasoningStep] = field(default_factory=list)
    tools_considered: int = 0
    tools_recommended: List[Dict] = field(default_factory=list)
    narrative: str = ""                     # final human-readable answer
    confidence: float = 0.0                 # 0-1 self-assessed confidence
    caveats: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    total_elapsed_ms: int = 0
    mode: str = "local"                     # "llm" | "local"
    reasoning_depth: int = 0                # how many act-observe cycles ran

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


# ======================================================================
# Configuration helpers
# ======================================================================

def _llm_ok() -> bool:
    """Check if an LLM provider is configured and available."""
    if _cfg and _cfg.llm_available():
        return True
    return False


def _llm_call(system: str, user: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
    """Unified thin wrapper around whichever LLM provider is configured."""
    provider = _cfg.get("llm_provider", "none")

    if provider == "openai":
        import openai
        client = openai.OpenAI(api_key=_cfg.get("openai_api_key"))
        model = _cfg.get("openai_model", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=_cfg.get("anthropic_api_key"))
        model = _cfg.get("anthropic_model", "claude-3-haiku-20240307")
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()

    raise RuntimeError(f"Unknown LLM provider: {provider}")


# ======================================================================
# PHASE 1 — Query Decomposition / Planning
# ======================================================================

_PLAN_SYSTEM = """\
You are the planning module of Praxis, an AI decision engine that recommends \
software tools for small & mid-size businesses.

Given a user's query, produce a JSON research plan.  Return ONLY valid JSON \
(no markdown fences):
{
  "sub_queries": ["...", "..."],
  "constraints": ["...", "..."],
  "evaluation_criteria": ["...", "..."],
  "research_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."]
}

Rules:
- Break compounds queries into 2-5 focused sub-queries.
- Extract hard constraints (budget caps, compliance, skill level, exclusions).
- Name 2-4 evaluation criteria the final answer should address.
- Outline 3-5 concrete research steps.
"""


def _llm_plan(query: str, intent: dict) -> dict:
    """Use LLM to decompose a complex query into a research plan."""
    context = f"Parsed intent: {json.dumps({k: v for k, v in intent.items() if k != 'raw'}, default=str)}"
    raw = _llm_call(_PLAN_SYSTEM, f"Query: {query}\n{context}", max_tokens=600)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON from markdown fences
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        raise


def _local_plan(query: str, intent: dict) -> dict:
    """Deterministic query decomposition — no LLM required."""
    sub_queries: List[str] = []
    constraints: List[str] = []
    criteria: List[str] = []
    steps: List[str] = []

    raw = query.lower()
    keywords = intent.get("keywords", [])
    negatives = intent.get("negatives", [])
    industry = intent.get("industry")
    goal = intent.get("goal")
    multi_intents = intent.get("multi_intents", [])

    # ── Sub-query generation ──
    primary = intent.get("intent") or ""

    # Negative-intent words that convert a sub-query into a constraint
    _NEG_PREFIXES = {"avoid", "avoiding", "without", "exclude", "excluding",
                     "no ", "not ", "skip", "skipping", "ban", "banning"}

    # Multi-intent splitting
    if multi_intents and len(multi_intents) > 1:
        for sub in multi_intents:
            sub_clean = sub.strip()
            # Detect negative sub-intents → convert to constraints instead
            if any(sub_clean.lower().startswith(neg) for neg in _NEG_PREFIXES):
                constraints.append(f"negative:{sub_clean}")
            else:
                sub_queries.append(sub_clean)
    else:
        # Single intent: generate sub-queries from different angles
        if primary:
            sub_queries.append(f"best {primary} tools")
        if industry:
            sub_queries.append(f"{primary or 'tools'} for {industry}")
        if goal:
            sub_queries.append(f"tools for {goal}")
        if not sub_queries:
            sub_queries.append(query)

    # Budget sub-query
    _budget_words = {"budget", "price", "cost", "cheap", "free", "affordable", "$", "under"}
    if any(w in raw for w in _budget_words):
        # Extract dollar amount if present
        dollar_match = re.search(r'\$\s*(\d+)', raw)
        if dollar_match:
            constraints.append(f"budget_cap_monthly=${dollar_match.group(1)}")
            sub_queries.append(f"affordable {primary} tools under ${dollar_match.group(1)}/mo")
        else:
            sub_queries.append(f"affordable {primary} tools")

    # Compliance sub-query
    _compliance_words = {"hipaa", "gdpr", "soc2", "soc 2", "compliance", "certified", "fedramp", "iso"}
    found_compliance = [w for w in _compliance_words if w in raw]
    if found_compliance:
        constraints.extend(found_compliance)
        # Avoid redundant phrasing like 'compliance compliance'
        specific = [w for w in found_compliance if w != "compliance"]
        if specific:
            sub_queries.append(f"tools with {', '.join(specific)} compliance")
        elif found_compliance:
            sub_queries.append("compliance-ready tools")

    # Negatives — filter out noise words that come from splitting compound terms
    _noise_negatives = {"in", "the", "a", "an", "of", "to", "for", "is", "and", "or", "not"}
    meaningful_negatives = [n for n in negatives if n not in _noise_negatives]
    if meaningful_negatives:
        constraints.extend([f"exclude:{n}" for n in meaningful_negatives])

    # Skill-level constraint
    _skill_words = {"beginner", "intermediate", "advanced", "no-code", "technical", "non-technical", "easy"}
    found_skill = [w for w in _skill_words if w in raw]
    if found_skill:
        constraints.extend(found_skill)

    # Lock-in / portability concern
    _lockin_words = {"lock-in", "lockin", "vendor lock", "portable", "portability", "switching", "migrate"}
    if any(w in raw for w in _lockin_words):
        criteria.append("low_vendor_lock_in")
        sub_queries.append("tools with good data portability and low lock-in")

    # ── Evaluation criteria ──
    criteria.insert(0, "relevance_to_task")
    criteria.append("pricing_and_value")
    if industry:
        criteria.append(f"industry_fit_{industry}")
    criteria.append("ease_of_adoption")
    # De-dup while preserving order
    seen = set()
    criteria = [c for c in criteria if not (c in seen or seen.add(c))]

    # ── Research steps ──
    steps.append(f"Step 1: Search for tools matching each sub-query ({len(sub_queries)} queries)")
    steps.append("Step 2: Merge results and de-duplicate — score against evaluation criteria")
    if constraints:
        steps.append(f"Step 3: Apply hard constraints ({', '.join(constraints[:3])})")
    else:
        steps.append("Step 3: Apply profile-based fit scoring")
    steps.append("Step 4: Run vendor intelligence checks (transparency & lock-in)")
    steps.append("Step 5: Self-critique — check coverage, diversity, and faithfulness")

    return {
        "sub_queries": sub_queries[:5],
        "constraints": constraints,
        "evaluation_criteria": criteria[:5],
        "research_steps": steps,
    }


# ======================================================================
# PHASE 2 — Act: Execute sub-searches and gather evidence
# ======================================================================

def _execute_sub_search(sub_query: str, profile=None, top_n: int = 5) -> List[Dict]:
    """Run one sub-query through the interpreter → engine pipeline."""
    intent = interpret(sub_query)
    results = find_tools(intent, top_n=top_n, profile=profile)
    out = []
    for t in results:
        expl = explain_tool(t, intent, profile)
        out.append({
            "name": t.name,
            "description": t.description,
            "url": getattr(t, "url", None),
            "categories": getattr(t, "categories", []),
            "pricing": getattr(t, "pricing", None),
            "skill_level": getattr(t, "skill_level", None),
            "compliance": getattr(t, "compliance", []),
            "integrations": getattr(t, "integrations", []),
            "fit_score": expl.get("fit_score", 0),
            "reasons": expl.get("reasons", []),
            "caveats": expl.get("caveats", []),
        })
    return out


def _merge_results(all_results: List[List[Dict]]) -> List[Dict]:
    """Merge results from multiple sub-searches, boost tools that appear
    in multiple result sets (cross-query consistency signal)."""
    by_name: Dict[str, Dict] = {}
    occurrence: Dict[str, int] = {}

    for result_set in all_results:
        for tool in result_set:
            name = tool["name"]
            occurrence[name] = occurrence.get(name, 0) + 1
            if name not in by_name:
                by_name[name] = dict(tool)
                by_name[name]["_cross_query_hits"] = 1
            else:
                # Keep the higher fit score
                if tool.get("fit_score", 0) > by_name[name].get("fit_score", 0):
                    old_hits = by_name[name]["_cross_query_hits"]
                    by_name[name] = dict(tool)
                    by_name[name]["_cross_query_hits"] = old_hits + 1
                else:
                    by_name[name]["_cross_query_hits"] += 1
                # Merge reasons (de-dup)
                existing_reasons = set(by_name[name].get("reasons", []))
                for r in tool.get("reasons", []):
                    if r not in existing_reasons:
                        by_name[name].setdefault("reasons", []).append(r)

    # Score boost for cross-query consistency
    merged = list(by_name.values())
    for t in merged:
        hits = t.pop("_cross_query_hits", 1)
        if hits > 1:
            t["fit_score"] = min(100, t.get("fit_score", 0) + (hits - 1) * 8)
            t.setdefault("reasons", []).insert(
                0, f"Matched across {hits} of your requirements"
            )

    merged.sort(key=lambda t: t.get("fit_score", 0), reverse=True)
    return merged


# ======================================================================
# PHASE 3 — Observe: Apply constraints & vendor intelligence
# ======================================================================

def _apply_constraints(tools: List[Dict], constraints: List[str]) -> List[Dict]:
    """Filter / penalise tools that violate hard constraints."""
    if not constraints:
        return tools

    exclusions = {c.replace("exclude:", "").lower() for c in constraints if c.startswith("exclude:")}
    budget_cap = None
    required_compliance = set()
    skill_ceiling = None

    for c in constraints:
        if c.startswith("budget_cap_monthly="):
            try:
                budget_cap = int(c.split("=")[1].replace("$", ""))
            except ValueError:
                pass
        elif c in {"hipaa", "gdpr", "soc2", "soc 2", "fedramp", "iso", "compliance"}:
            required_compliance.add(c.upper().replace(" ", ""))
        elif c in {"beginner", "intermediate", "advanced", "no-code", "easy"}:
            skill_ceiling = c

    filtered = []
    for t in tools:
        name_low = t["name"].lower()

        # Hard exclusion
        if any(ex in name_low for ex in exclusions):
            continue

        # Budget check
        if budget_cap and t.get("pricing"):
            starter = t["pricing"].get("starter")
            if starter and isinstance(starter, (int, float)) and starter > budget_cap:
                t["caveats"] = t.get("caveats", []) + [
                    f"Starter plan (${starter}/mo) exceeds your ${budget_cap}/mo budget"
                ]
                t["fit_score"] = max(0, t.get("fit_score", 0) - 15)

        # Compliance check
        if required_compliance:
            tool_compliance = {c.upper().replace(" ", "") for c in t.get("compliance", [])}
            missing = required_compliance - tool_compliance
            if missing:
                t["caveats"] = t.get("caveats", []) + [
                    f"Missing compliance: {', '.join(missing)}"
                ]
                t["fit_score"] = max(0, t.get("fit_score", 0) - 10)

        # Skill-level check
        if skill_ceiling:
            tool_skill = (t.get("skill_level") or "").lower()
            if skill_ceiling in ("beginner", "no-code", "easy") and tool_skill == "advanced":
                t["caveats"] = t.get("caveats", []) + [
                    f"Requires {tool_skill} skills — may be steep for {skill_ceiling} users"
                ]
                t["fit_score"] = max(0, t.get("fit_score", 0) - 12)

        filtered.append(t)

    filtered.sort(key=lambda t: t.get("fit_score", 0), reverse=True)
    return filtered


def _enrich_with_vendor_intel(tools: List[Dict]) -> List[Dict]:
    """Run vendor intelligence checks and attach transparency/freedom data."""
    if not _PHILOSOPHY:
        return tools

    tool_lookup = {t.name.lower(): t for t in TOOLS}

    for t in tools:
        tool_obj = tool_lookup.get(t["name"].lower())
        if not tool_obj:
            continue
        try:
            trans = assess_transparency(tool_obj)
            freedom = assess_freedom(tool_obj)
            t["transparency_score"] = trans.get("score", 0)
            t["transparency_grade"] = trans.get("grade", "?")
            t["freedom_score"] = freedom.get("score", 0)
            t["freedom_grade"] = freedom.get("grade", "?")
            # Surface serious vendor risks as caveats
            if trans.get("score", 100) < 40:
                t.setdefault("caveats", []).append(
                    f"Low transparency ({trans.get('grade', '?')}) — limited visibility into data practices"
                )
            if freedom.get("score", 100) < 40:
                t.setdefault("caveats", []).append(
                    f"High vendor lock-in ({freedom.get('grade', '?')}) — migration may be difficult"
                )
        except Exception as e:
            log.debug("vendor intel failed for %s: %s", t["name"], e)

    return tools


# ======================================================================
# PHASE 4 — Reflect: Self-critique the draft answer
# ======================================================================

_REFLECT_SYSTEM = """\
You are the self-critique module of Praxis, an AI decision engine.
You are reviewing a draft recommendation before it's shown to the user.

Given the original query, research plan, and draft tool recommendations, \
produce a JSON critique.  Return ONLY valid JSON (no markdown fences):
{
  "faithfulness": 0-10,
  "coverage": 0-10,
  "diversity": 0-10,
  "issues": ["...", "..."],
  "suggestions": ["...", "..."],
  "missing_angles": ["...", "..."],
  "confidence": 0.0-1.0
}

Score meanings:
- faithfulness: How well do recommendations match the query constraints?
- coverage: Are all aspects of the query addressed?
- diversity: Is there variety (categories, price points, skill levels)?
"""


def _llm_reflect(query: str, plan: dict, tools: List[Dict]) -> dict:
    """Use LLM to self-critique the draft answer."""
    tool_summary = json.dumps(
        [{"name": t["name"], "fit": t.get("fit_score"), "caveats": t.get("caveats", [])} for t in tools[:8]],
        default=str
    )
    prompt = f"Query: {query}\nPlan: {json.dumps(plan, default=str)}\nDraft tools:\n{tool_summary}"
    raw = _llm_call(_REFLECT_SYSTEM, prompt, max_tokens=500)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
        return {"faithfulness": 5, "coverage": 5, "diversity": 5, "issues": [],
                "suggestions": [], "missing_angles": [], "confidence": 0.5}


def _local_reflect(query: str, plan: dict, tools: List[Dict]) -> dict:
    """Deterministic self-critique — checks structural quality signals."""
    issues = []
    suggestions = []
    missing = []

    # Faithfulness: do results address the sub-queries?
    sub_queries = plan.get("sub_queries", [])
    faith_score = 10
    if not tools:
        faith_score = 0
        issues.append("No tools found for any sub-query")
    elif len(tools) < 3:
        faith_score = max(3, faith_score - 3)
        issues.append("Very few results — query may be too specific")

    # Coverage: are all sub-queries represented?
    cov_score = 10
    if sub_queries:
        # Rough check: see if tool reasons mention aspects of each sub-query
        all_reasons = " ".join(
            " ".join(t.get("reasons", []) + [t.get("description", "")])
            for t in tools
        ).lower()
        unaddressed = []
        for sq in sub_queries:
            sq_words = [w for w in sq.lower().split() if len(w) > 3]
            if sq_words and not any(w in all_reasons for w in sq_words):
                unaddressed.append(sq)
        if unaddressed:
            cov_score = max(2, 10 - len(unaddressed) * 2)
            missing.extend([f"Sub-query not well covered: '{sq}'" for sq in unaddressed])

    # Diversity: check category spread
    div_score = 10
    all_cats = set()
    price_points = set()
    skill_levels = set()
    for t in tools:
        all_cats.update(t.get("categories", []))
        pricing = t.get("pricing") or {}
        if pricing.get("free_tier"):
            price_points.add("free")
        if pricing.get("starter"):
            price_points.add("paid")
        if t.get("skill_level"):
            skill_levels.add(t["skill_level"])

    if len(all_cats) < 2 and len(tools) > 2:
        div_score -= 3
        suggestions.append("All tools are in the same category — consider broadening")
    if len(price_points) < 2 and len(tools) > 2:
        div_score -= 2
        suggestions.append("Limited pricing diversity — include both free-tier and paid options")
    if len(skill_levels) < 2 and len(tools) > 3:
        div_score -= 1
        suggestions.append("All tools target the same skill level")

    # Constraint enforcement check
    constraints = plan.get("constraints", [])
    caveat_count = sum(len(t.get("caveats", [])) for t in tools)
    if caveat_count > len(tools) * 2:
        faith_score -= 2
        issues.append("Many tools have constraint violations — consider stricter filtering")

    avg = (faith_score + cov_score + div_score) / 30.0
    confidence = round(min(1.0, max(0.1, avg)), 2)

    return {
        "faithfulness": max(0, faith_score),
        "coverage": max(0, cov_score),
        "diversity": max(0, min(10, div_score)),
        "issues": issues,
        "suggestions": suggestions,
        "missing_angles": missing,
        "confidence": confidence,
    }


# ======================================================================
# PHASE 5 — Synthesize: narrative generation
# ======================================================================

_SYNTH_SYSTEM = """\
You are the synthesis module of Praxis, an AI tool recommendation engine.

Given a user query, research plan, ranked tool recommendations, and a \
self-critique, write a concise (3–6 sentence) executive recommendation \
that a busy SMB owner can act on immediately.

Guidelines:
- Lead with the top recommendation and WHY it wins.
- Mention 1-2 alternatives and when they'd be better.
- Surface the most important caveats.
- If the critique found issues, acknowledge gaps honestly.
- Use plain language — no jargon.
"""


def _llm_synthesize(query: str, plan: dict, tools: List[Dict], critique: dict) -> str:
    """Generate a narrative summary via LLM."""
    payload = {
        "query": query,
        "plan_summary": plan.get("research_steps", []),
        "top_tools": [
            {"name": t["name"], "fit": t.get("fit_score"), "reasons": t.get("reasons", [])[:2],
             "caveats": t.get("caveats", [])[:2]}
            for t in tools[:5]
        ],
        "critique": critique,
    }
    return _llm_call(_SYNTH_SYSTEM, json.dumps(payload, default=str), max_tokens=500, temperature=0.4)


def _local_synthesize(query: str, tools: List[Dict], critique: dict) -> str:
    """Build narrative without LLM — template-driven but informative."""
    if not tools:
        return (
            "I wasn't able to find tools that closely match this query. "
            "Try broadening your search or adjusting constraints."
        )

    lines = []
    top = tools[0]
    top_name = top["name"]
    top_reasons = top.get("reasons", [])
    top_fit = top.get("fit_score", 0)

    # Lead recommendation
    if top_reasons:
        lines.append(f"**{top_name}** is your strongest match ({top_fit}% fit) — {top_reasons[0].lower()}.")
    else:
        lines.append(f"**{top_name}** leads the pack with a {top_fit}% fit score for your query.")

    # Runner up
    if len(tools) > 1:
        runner = tools[1]
        runner_name = runner["name"]
        runner_fit = runner.get("fit_score", 0)
        diff = top_fit - runner_fit
        if diff < 5:
            lines.append(f"**{runner_name}** ({runner_fit}% fit) is a very close alternative worth evaluating side-by-side.")
        else:
            runner_reasons = runner.get("reasons", [])
            why = f" — {runner_reasons[0].lower()}" if runner_reasons else ""
            lines.append(f"**{runner_name}** ({runner_fit}% fit) is a solid backup{why}.")

    # Third option if diverse
    if len(tools) > 2:
        third = tools[2]
        cats_overlap = set(top.get("categories", [])) & set(third.get("categories", []))
        if not cats_overlap:
            lines.append(f"For a different approach, consider **{third['name']}** ({third.get('fit_score', 0)}% fit).")

    # Key caveats
    top_caveats = top.get("caveats", [])
    if top_caveats:
        lines.append(f"**Heads up:** {top_caveats[0]}")

    # Confidence disclaimer
    conf = critique.get("confidence", 0.5)
    if conf < 0.5:
        lines.append("*Note: My confidence in this recommendation is moderate — the query may benefit from more specific constraints.*")

    # Coverage gaps
    missing = critique.get("missing_angles", [])
    if missing:
        lines.append(f"*I wasn't able to fully address: {missing[0]}.*")

    return " ".join(lines)


# ======================================================================
# Follow-up question generation
# ======================================================================

def _generate_follow_ups(query: str, plan: dict, tools: List[Dict], critique: dict) -> List[str]:
    """Suggest smart follow-up questions based on gaps and context."""
    questions = []

    missing = critique.get("missing_angles", [])
    suggestions = critique.get("suggestions", [])

    # From critique gaps
    if missing:
        for gap in missing[:2]:
            if "compliance" in gap.lower():
                questions.append("Do you have specific compliance requirements (HIPAA, SOC2, GDPR)?")
            elif "budget" in gap.lower() or "pricing" in gap.lower():
                questions.append("What's your monthly budget for this tooling?")
            else:
                cleaned = gap.split(":")[-1].strip().strip("'\"")
                questions.append(f"Could you elaborate on: {cleaned}?")

    # From suggestion signals
    if suggestions and not questions:
        if any("pricing" in s for s in suggestions):
            questions.append("Would you prefer free-tier options, or is a paid tool acceptable?")
        if any("skill" in s for s in suggestions):
            questions.append("What's the team's technical comfort level — beginner or experienced?")

    # Industry detection
    if not any("industry" in q.lower() for q in questions):
        constraints = plan.get("constraints", [])
        if not any("industry" in str(c) for c in constraints):
            all_keywords = query.lower().split()
            _generic = {"tool", "tools", "best", "need", "help", "want", "ai"}
            if not set(all_keywords) - _generic:
                questions.append("What industry are you in? This helps narrow recommendations significantly.")

    # Comparison offer
    if len(tools) >= 2:
        questions.append(
            f"Would you like a detailed comparison between {tools[0]['name']} and {tools[1]['name']}?"
        )

    return questions[:4]


# ======================================================================
# MAIN ENTRY POINT — deep_reason()
# ======================================================================

def deep_reason(
    query: str,
    profile_id: Optional[str] = None,
    max_steps: int = 5,
    budget_ms: int = 15_000,
) -> ReasoningResult:
    """
    Execute the full Plan → Act → Observe → Reflect → Synthesize
    reasoning loop.

    Args:
        query:      raw user question (can be complex multi-part)
        profile_id: optional user profile for personalised scoring
        max_steps:  max sub-search iterations (default 5)
        budget_ms:  time budget in milliseconds (default 15s)

    Returns:
        ReasoningResult with full trace, recommendations, and narrative
    """
    t0 = time.time()
    use_llm = _llm_ok()
    mode = "llm" if use_llm else "local"
    steps: List[ReasoningStep] = []

    log.info("deep_reason: mode=%s query=%r max_steps=%d", mode, query, max_steps)

    # Load profile
    profile = None
    if profile_id and load_profile:
        try:
            profile = load_profile(profile_id)
        except Exception:
            pass

    # ── PHASE 1: Plan ─────────────────────────────────────────────
    t1 = time.time()
    intent = interpret(query)

    try:
        if use_llm:
            plan = _llm_plan(query, intent)
        else:
            plan = _local_plan(query, intent)
    except Exception as e:
        log.warning("LLM planning failed, falling back to local: %s", e)
        plan = _local_plan(query, intent)
        mode = "local"  # downgrade

    sub_queries = plan.get("sub_queries", [query])
    constraints = plan.get("constraints", [])
    research_steps = plan.get("research_steps", [])

    steps.append(ReasoningStep(
        phase="plan",
        action=f"Decomposed query into {len(sub_queries)} sub-queries with {len(constraints)} constraints",
        detail={"sub_queries": sub_queries, "constraints": constraints,
                "evaluation_criteria": plan.get("evaluation_criteria", []),
                "research_steps": research_steps},
        elapsed_ms=int((time.time() - t1) * 1000),
    ))

    log.info("plan: %d sub-queries, %d constraints", len(sub_queries), len(constraints))

    # ── PHASE 2: Act — execute sub-searches ───────────────────────
    all_sub_results: List[List[Dict]] = []
    depth = 0

    for i, sq in enumerate(sub_queries[:max_steps]):
        if (time.time() - t0) * 1000 > budget_ms:
            steps.append(ReasoningStep(
                phase="act",
                action=f"Stopped at sub-query {i+1}/{len(sub_queries)} — budget exhausted",
            ))
            break

        t_act = time.time()
        results = _execute_sub_search(sq, profile=profile, top_n=5)
        all_sub_results.append(results)
        depth += 1

        steps.append(ReasoningStep(
            phase="act",
            action=f"Sub-query {i+1}: \"{sq}\" → {len(results)} tools",
            detail=[{"name": r["name"], "fit": r.get("fit_score", 0)} for r in results],
            elapsed_ms=int((time.time() - t_act) * 1000),
        ))

    # Merge
    t_merge = time.time()
    merged = _merge_results(all_sub_results)
    tools_considered = len(merged)

    steps.append(ReasoningStep(
        phase="observe",
        action=f"Merged {tools_considered} unique tools from {depth} sub-searches",
        elapsed_ms=int((time.time() - t_merge) * 1000),
    ))

    # ── PHASE 3: Observe — constraints + vendor intel ─────────────
    t_obs = time.time()
    merged = _apply_constraints(merged, constraints)
    merged = _enrich_with_vendor_intel(merged)

    steps.append(ReasoningStep(
        phase="observe",
        action=f"Applied {len(constraints)} constraints and vendor intelligence enrichment",
        detail={"post_filter_count": len(merged),
                "top_3": [t["name"] for t in merged[:3]]},
        elapsed_ms=int((time.time() - t_obs) * 1000),
    ))

    # ── PHASE 4: Reflect — self-critique ──────────────────────────
    t_ref = time.time()
    try:
        if use_llm:
            critique = _llm_reflect(query, plan, merged[:8])
        else:
            critique = _local_reflect(query, plan, merged[:8])
    except Exception as e:
        log.warning("LLM reflection failed, falling back to local: %s", e)
        critique = _local_reflect(query, plan, merged[:8])

    confidence = critique.get("confidence", 0.5)

    steps.append(ReasoningStep(
        phase="reflect",
        action=f"Self-critique: faith={critique.get('faithfulness')}/10, "
               f"coverage={critique.get('coverage')}/10, "
               f"diversity={critique.get('diversity')}/10, "
               f"confidence={confidence}",
        detail=critique,
        elapsed_ms=int((time.time() - t_ref) * 1000),
    ))

    # ── Optional: re-search if critique found serious gaps ────────
    if confidence < 0.4 and depth < max_steps and (time.time() - t0) * 1000 < budget_ms * 0.8:
        missing = critique.get("missing_angles", [])
        if missing:
            # Attempt one more targeted search
            rescue_query = missing[0].split(":")[-1].strip().strip("'")
            t_rescue = time.time()
            rescue_results = _execute_sub_search(rescue_query, profile=profile, top_n=3)
            if rescue_results:
                all_sub_results.append(rescue_results)
                merged = _merge_results(all_sub_results)
                merged = _apply_constraints(merged, constraints)
                merged = _enrich_with_vendor_intel(merged)
                depth += 1

                steps.append(ReasoningStep(
                    phase="act",
                    action=f"Rescue search for gap: \"{rescue_query}\" → {len(rescue_results)} tools",
                    detail=[{"name": r["name"], "fit": r.get("fit_score", 0)} for r in rescue_results],
                    elapsed_ms=int((time.time() - t_rescue) * 1000),
                ))

                # Re-critique
                critique = _local_reflect(query, plan, merged[:8])
                confidence = critique.get("confidence", 0.5)

    # ── PHASE 5: Synthesize ───────────────────────────────────────
    t_synth = time.time()
    top_tools = merged[:8]

    try:
        if use_llm:
            narrative = _llm_synthesize(query, plan, top_tools, critique)
        else:
            narrative = _local_synthesize(query, top_tools, critique)
    except Exception as e:
        log.warning("LLM synthesis failed, falling back to local: %s", e)
        narrative = _local_synthesize(query, top_tools, critique)

    steps.append(ReasoningStep(
        phase="synthesize",
        action="Generated executive narrative",
        elapsed_ms=int((time.time() - t_synth) * 1000),
    ))

    # ── Follow-up questions ───────────────────────────────────────
    follow_ups = _generate_follow_ups(query, plan, top_tools, critique)

    # ── Assemble final caveats ────────────────────────────────────
    all_caveats = []
    for t in top_tools[:3]:
        for c in t.get("caveats", []):
            if c not in all_caveats:
                all_caveats.append(c)
    # Add critique issues
    for issue in critique.get("issues", []):
        if issue not in all_caveats:
            all_caveats.append(issue)

    total_ms = int((time.time() - t0) * 1000)

    result = ReasoningResult(
        query=query,
        plan=research_steps,
        steps=steps,
        tools_considered=tools_considered,
        tools_recommended=[
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "url": t.get("url"),
                "categories": t.get("categories", []),
                "fit_score": t.get("fit_score", 0),
                "reasons": t.get("reasons", [])[:4],
                "caveats": t.get("caveats", [])[:3],
                "pricing": t.get("pricing"),
                "integrations": t.get("integrations", []),
                "compliance": t.get("compliance", []),
                "skill_level": t.get("skill_level"),
                "transparency_score": t.get("transparency_score"),
                "transparency_grade": t.get("transparency_grade"),
                "freedom_score": t.get("freedom_score"),
                "freedom_grade": t.get("freedom_grade"),
            }
            for t in top_tools[:8]
        ],
        narrative=narrative,
        confidence=confidence,
        caveats=all_caveats[:8],
        follow_up_questions=follow_ups,
        total_elapsed_ms=total_ms,
        mode=mode,
        reasoning_depth=depth,
    )

    log.info(
        "deep_reason: done in %dms, mode=%s, depth=%d, tools_found=%d, confidence=%.2f",
        total_ms, mode, depth, len(top_tools), confidence,
    )

    return result


# ======================================================================
# deep_reason_v2 — Cognitive Search Pipeline
# ======================================================================

def deep_reason_v2(
    query: str,
    profile_id: Optional[str] = None,
    max_steps: int = 5,
    budget_ms: int = 15_000,
) -> ReasoningResult:
    """
    v2 cognitive reasoning pipeline that layers:

        1. **Hybrid Retrieval** (RRF dense-sparse fusion)
        2. **GraphRAG** (knowledge-graph traversal & community context)
        3. **PRISM Agents** (Analyzer → Selector → Adder loop)
        4. **FACT-AUDIT** verification
        5. **Self-Critique** (CRAG correction)

    Falls back gracefully to deep_reason() if the new modules
    aren't available.
    """
    if not (_RETRIEVAL_OK and _GRAPH_OK and _PRISM_OK):
        log.info("deep_reason_v2: missing modules (retrieval=%s graph=%s prism=%s), "
                 "falling back to v1", _RETRIEVAL_OK, _GRAPH_OK, _PRISM_OK)
        return deep_reason(query, profile_id, max_steps, budget_ms)

    t0 = time.time()
    use_llm = _llm_ok()
    mode = "llm" if use_llm else "local"
    steps: List[ReasoningStep] = []
    all_caveats: List[str] = []

    log.info("deep_reason_v2: mode=%s query=%r", mode, query)

    # Load profile
    profile = None
    if profile_id and load_profile:
        try:
            profile = load_profile(profile_id)
        except Exception:
            pass

    # ── PHASE 1: Plan (via PRISM Analyzer) ────────────────────────
    t1 = time.time()
    intent = interpret(query)

    try:
        if use_llm:
            plan = _llm_plan(query, intent)
        else:
            plan = _local_plan(query, intent)
    except Exception as e:
        log.warning("v2 planning failed: %s", e)
        plan = _local_plan(query, intent)
        mode = "local"

    sub_queries = plan.get("sub_queries", [query])
    constraints = plan.get("constraints", [])
    research_steps = plan.get("research_steps", [])

    steps.append(ReasoningStep(
        phase="plan",
        action=f"Decomposed into {len(sub_queries)} sub-queries, {len(constraints)} constraints",
        detail={"sub_queries": sub_queries, "constraints": constraints},
        elapsed_ms=int((time.time() - t1) * 1000),
    ))

    # ── PHASE 1b: Vertical Intelligence ───────────────────────────
    vertical_ctx = None
    if _VERTICALS_OK:
        try:
            t_vert = time.time()
            vertical_ctx = _enrich_vertical_context(
                query,
                keywords=intent.get("keywords", []),
                industry=intent.get("industry"),
            )
            if vertical_ctx and vertical_ctx.get("verticals") and len(vertical_ctx["verticals"]) > 0:
                top_v = vertical_ctx["verticals"][0]
                steps.append(ReasoningStep(
                    phase="vertical",
                    action=f"Detected vertical: {top_v.get('vertical_name', top_v.get('vertical_id'))} "
                           f"(confidence {top_v.get('confidence', 0):.2f})",
                    detail={
                        "vertical_id": top_v["vertical_id"],
                        "constraints": vertical_ctx.get("constraints", {}),
                        "compound_workflows": len(vertical_ctx.get("compound_workflows", [])),
                    },
                    elapsed_ms=int((time.time() - t_vert) * 1000),
                ))
        except Exception as exc:
            log.debug("v2 vertical enrichment: %s", exc)

    # ── PHASE 1c: Guardrails + Architecture Intelligence ──────────
    safety_ctx = None
    arch_ctx = None

    if _GUARDRAILS_OK:
        try:
            t_guard = time.time()
            safety_result = _score_safety(query)
            safety_score = safety_result.get("safety_score", 1.0)
            guard_pattern = _recommend_guardrail(query)
            safety_ctx = {
                "safety_score": safety_score,
                "verdict": safety_result.get("verdict", "pass"),
                "recommended_pattern": guard_pattern,
            }
            steps.append(ReasoningStep(
                phase="guardrails",
                action=f"Safety score: {safety_score:.2f}, "
                       f"pattern: {guard_pattern.get('pattern_id', 'none')}",
                detail=safety_ctx,
                elapsed_ms=int((time.time() - t_guard) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 guardrails enrichment: %s", exc)

    if _ORCHESTRATION_OK:
        try:
            t_arch = time.time()
            arch_ctx = _detect_architecture(query, industry=intent.get("industry"))
            eng_style = arch_ctx.get("engineering_style", {})
            n_patterns = len(arch_ctx.get("patterns", []))
            steps.append(ReasoningStep(
                phase="architecture",
                action=f"Architecture: style={eng_style.get('style', 'unknown')}, "
                       f"{n_patterns} patterns, "
                       f"complexity={arch_ctx.get('complexity_level', 'unknown')}",
                detail={
                    "engineering_style": eng_style.get("style"),
                    "complexity": arch_ctx.get("complexity_level"),
                    "pattern_count": n_patterns,
                    "anti_patterns": arch_ctx.get("anti_patterns_detected", []),
                },
                elapsed_ms=int((time.time() - t_arch) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 architecture enrichment: %s", exc)

    # ── PHASE 1d: Resilience & Vibe Coding Assessment ──────────────
    resilience_ctx = None
    if _RESILIENCE_OK:
        try:
            t_res = time.time()
            vibe_result = _score_vibe_risk(query)
            resilience_ctx = {
                "vibe_risk": vibe_result["risk_score"],
                "grade": vibe_result["grade"],
                "signals": vibe_result["signals"],
                "warnings": vibe_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="resilience",
                action=f"Vibe-coding risk: {vibe_result['risk_score']:.2f} "
                       f"(grade {vibe_result['grade']}), "
                       f"{len(vibe_result['signals'])} signals",
                detail=resilience_ctx,
                elapsed_ms=int((time.time() - t_res) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 resilience enrichment: %s", exc)

    # ── PHASE 1e: Metacognition & Self-Awareness ───────────────────
    metacog_ctx = None
    if _METACOGNITION_OK:
        try:
            t_mc = time.time()
            mc_result = _assess_metacognition(query)
            metacog_ctx = {
                "self_awareness": mc_result["self_awareness_score"],
                "grade": mc_result["grade"],
                "pathology_flags": mc_result["pathology_flags"],
                "bankruptcy_risk": mc_result["bankruptcy_risk"],
                "drift_risk": mc_result["drift_risk"],
                "stylometry": mc_result["stylometry_probability"],
                "warnings": mc_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="metacognition",
                action=f"Self-awareness: {mc_result['self_awareness_score']:.2f} "
                       f"(grade {mc_result['grade']}), "
                       f"bankruptcy risk {mc_result['bankruptcy_risk']:.2f}, "
                       f"{len(mc_result['pathology_flags'])} pathology flags",
                detail=metacog_ctx,
                elapsed_ms=int((time.time() - t_mc) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 metacognition enrichment: %s", exc)

    # ── PHASE 1f: Real Self-Introspection ──────────────────────────
    introspect_ctx = None
    if _INTROSPECT_OK:
        try:
            t_si = time.time()
            si_result = _real_entropy()  # actual AST analysis of praxis/
            introspect_ctx = {
                "entropy_score": si_result["entropy_score"],
                "grade": si_result["grade"],
                "status": si_result["status"],
                "dimensions": si_result["dimensions"],
            }
            steps.append(ReasoningStep(
                phase="introspection",
                action=f"Self-introspection: structural entropy "
                       f"{si_result['entropy_score']:.2f} "
                       f"(grade {si_result['grade']}/{si_result['status']})",
                detail=introspect_ctx,
                elapsed_ms=int((time.time() - t_si) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 self-introspection: %s", exc)

    # ── PHASE 1g: Architecture of Awakening ────────────────────────
    awakening_ctx = None
    if _AWAKENING_OK:
        try:
            t_aw = time.time()
            aw_result = _assess_awakening(query)
            awakening_ctx = {
                "consciousness": aw_result["consciousness_score"],
                "grade": aw_result["grade"],
                "leaks": aw_result["leaky_abstractions"]["count"],
                "patterns": aw_result["conscious_patterns"]["count"],
                "vsd_score": aw_result["vsd_alignment"]["vsd_score"],
                "supply_risk": aw_result["supply_chain_risk"]["risk_score"],
                "debt_consciousness": aw_result["debt_consciousness"]["consciousness_ratio"],
                "mesias_risk": aw_result["mesias_risk"]["ethical_risk_score"],
                "warnings": aw_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="awakening",
                action=f"Awakening: consciousness {aw_result['consciousness_score']:.2f} "
                       f"(grade {aw_result['grade']}), "
                       f"{aw_result['leaky_abstractions']['count']} leaks, "
                       f"{aw_result['conscious_patterns']['count']} patterns, "
                       f"VSD {aw_result['vsd_alignment']['vsd_score']:.2f}",
                detail=awakening_ctx,
                elapsed_ms=int((time.time() - t_aw) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 awakening enrichment: %s", exc)

    # ── PHASE 1h: Self-Authorship Assessment ──────────────────────
    authorship_ctx = None
    if _AUTHORSHIP_OK:
        try:
            t_au = time.time()
            au_result = _assess_authorship(query)
            authorship_ctx = {
                "authorship": au_result["authorship_score"],
                "grade": au_result["grade"],
                "dishonesty_count": au_result["honesty"]["count"],
                "ddd_grade": au_result["ddd_maturity"]["grade"],
                "continuity_grade": au_result["continuity"]["grade"],
                "resilience_grade": au_result["resilience_posture"]["grade"],
                "extensibility_grade": au_result["extensibility"]["grade"],
                "agent_readiness": au_result["agent_readiness"]["grade"],
                "warnings": au_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="authorship",
                action=f"Authorship: {au_result['authorship_score']:.2f} "
                       f"(grade {au_result['grade']}), "
                       f"DDD={au_result['ddd_maturity']['grade']}, "
                       f"continuity={au_result['continuity']['grade']}, "
                       f"resilience={au_result['resilience_posture']['grade']}",
                detail=authorship_ctx,
                elapsed_ms=int((time.time() - t_au) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 authorship enrichment: %s", exc)

    # ── PHASE 1i: Architectural Enlightenment Assessment ──────────
    enlightenment_ctx = None
    if _ENLIGHTENMENT_OK:
        try:
            t_en = time.time()
            en_result = _assess_enlightenment(query)
            enlightenment_ctx = {
                "enlightenment": en_result["enlightenment_score"],
                "grade": en_result["grade"],
                "unity_grade": en_result["unity"]["grade"],
                "alignment_grade": en_result["alignment"]["grade"],
                "projection_grade": en_result["projection"]["grade"],
                "ego_grade": en_result["ego_dissolution"]["grade"],
                "connection_grade": en_result["interconnection"]["grade"],
                "presence_grade": en_result["presence"]["grade"],
                "remembrance_grade": en_result["remembrance"]["grade"],
                "warnings": en_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="enlightenment",
                action=f"Enlightenment: {en_result['enlightenment_score']:.2f} "
                       f"(grade {en_result['grade']}), "
                       f"unity={en_result['unity']['grade']}, "
                       f"alignment={en_result['alignment']['grade']}, "
                       f"connection={en_result['interconnection']['grade']}",
                detail=enlightenment_ctx,
                elapsed_ms=int((time.time() - t_en) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 enlightenment enrichment: %s", exc)

    # ── PHASE 1j: Conduit — Decoupled Cognitive Assessment ─────────
    conduit_ctx = None
    if _CONDUIT_OK:
        try:
            t_co = time.time()
            co_result = _assess_conduit(query)
            conduit_ctx = {
                "conduit": co_result["conduit_score"],
                "grade": co_result["grade"],
                "decoupling_grade": co_result["decoupling"]["grade"],
                "memory_grade": co_result["memory"]["grade"],
                "gwt_grade": co_result["gwt"]["grade"],
                "phi_grade": co_result["phi"]["grade"],
                "repe_grade": co_result["repe"]["grade"],
                "autopoiesis_grade": co_result["autopoiesis"]["grade"],
                "resonance_grade": co_result["resonance"]["grade"],
                "agency_detected": co_result["agency_detected"],
                "warnings": co_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="conduit",
                action=f"Conduit: {co_result['conduit_score']:.2f} "
                       f"(grade {co_result['grade']}), "
                       f"decoupling={co_result['decoupling']['grade']}, "
                       f"gwt={co_result['gwt']['grade']}, "
                       f"phi={co_result['phi']['grade']}, "
                       f"agency={'YES' if co_result['agency_detected'] else 'no'}",
                detail=conduit_ctx,
                elapsed_ms=int((time.time() - t_co) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 conduit enrichment: %s", exc)

    # ── PHASE 1k: Resonance — AGI Relational Architecture Assessment ──
    resonance_ctx = None
    if _RESONANCE_OK:
        try:
            t_res = time.time()
            res_result = _assess_resonance(query)
            resonance_ctx = {
                "resonance": res_result["resonance_score"],
                "grade": res_result["grade"],
                "temporal_grade": res_result["temporal_substrate"]["grade"],
                "code_agency_grade": res_result["code_agency"]["grade"],
                "latent_steering_grade": res_result["latent_steering"]["grade"],
                "conductor_grade": res_result["conductor_dashboard"]["grade"],
                "meta_awareness_grade": res_result["meta_awareness"]["grade"],
                "trap_grade": res_result["trap_grade"],
                "dsrp_grade": res_result["dsrp_grade"],
                "wisdom_agents": res_result["wisdom_agents_active"],
                "resonance_detected": res_result["resonance_detected"],
                "warnings": res_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="resonance",
                action=f"Resonance: {res_result['resonance_score']:.2f} "
                       f"(grade {res_result['grade']}), "
                       f"temporal={res_result['temporal_substrate']['grade']}, "
                       f"conductor={res_result['conductor_dashboard']['grade']}, "
                       f"TRAP={res_result['trap_grade']}, "
                       f"resonance={'YES' if res_result['resonance_detected'] else 'no'}",
                detail=resonance_ctx,
                elapsed_ms=int((time.time() - t_res) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 resonance enrichment: %s", exc)

    # ── PHASE 1l: Enterprise Engine — Billion-Dollar Architecture Assessment ──
    enterprise_ctx = None
    if _ENTERPRISE_OK:
        try:
            t_ent = time.time()
            ent_result = _assess_enterprise(query)
            enterprise_ctx = {
                "enterprise": ent_result["enterprise_score"],
                "grade": ent_result["grade"],
                "graphrag_grade": ent_result["hybrid_graphrag"]["grade"],
                "multi_agent_grade": ent_result["multi_agent"]["grade"],
                "mcp_bus_grade": ent_result["mcp_bus"]["grade"],
                "data_moat_grade": ent_result["data_moat"]["grade"],
                "monetization_grade": ent_result["monetization"]["grade"],
                "security_grade": ent_result["security"]["grade"],
                "agent_roles_grade": ent_result["agent_roles_grade"],
                "medallion_grade": ent_result["medallion_grade"],
                "active_agents": ent_result["active_agents"],
                "enterprise_ready": ent_result["enterprise_ready"],
                "warnings": ent_result["warnings"],
            }
            steps.append(ReasoningStep(
                phase="enterprise",
                action=f"Enterprise: {ent_result['enterprise_score']:.2f} "
                       f"(grade {ent_result['grade']}), "
                       f"graphrag={ent_result['hybrid_graphrag']['grade']}, "
                       f"agents={ent_result['multi_agent']['grade']}, "
                       f"security={ent_result['security']['grade']}, "
                       f"ready={'YES' if ent_result['enterprise_ready'] else 'no'}",
                detail=enterprise_ctx,
                elapsed_ms=int((time.time() - t_ent) * 1000),
            ))
        except Exception as exc:
            log.debug("v2 enterprise enrichment: %s", exc)

    # ── PHASE 2: PRISM Pipeline ───────────────────────────────────
    t_prism = time.time()
    prism_result = _prism_search(
        query,
        top_n=max_steps * 3,
        max_iterations=2,
        budget_ms=int(budget_ms * 0.6),
        profile=profile,
    )

    steps.append(ReasoningStep(
        phase="act",
        action=f"PRISM: {len(prism_result.selected_tools)} tools via "
               f"{prism_result.iterations} Selector↔Adder iterations "
               f"(P={prism_result.precision:.2f} R={prism_result.recall:.2f})",
        detail={
            "complexity": prism_result.analysis.query_complexity,
            "sub_questions": len(prism_result.analysis.sub_questions),
            "precision": prism_result.precision,
            "recall": prism_result.recall,
            "f1": prism_result.f1,
        },
        elapsed_ms=int((time.time() - t_prism) * 1000),
    ))

    # ── PHASE 3: Graph Context Enrichment ─────────────────────────
    t_graph = time.time()
    graph_context = {}
    try:
        graph = _get_graph()
        for tool in prism_result.selected_tools[:5]:
            ctx = graph.enrich_tool_context(tool.name)
            if ctx.get("found"):
                graph_context[tool.name] = ctx

        # Community-level insights for the query
        comms = graph.global_search(query, top_n=2)
        comm_summaries = [c.summary for c in comms]
    except Exception as exc:
        log.debug("v2 graph enrichment: %s", exc)
        comm_summaries = []

    steps.append(ReasoningStep(
        phase="observe",
        action=f"Graph enrichment: {len(graph_context)} tools contextualised, "
               f"{len(comm_summaries)} community insights",
        detail={"community_summaries": comm_summaries},
        elapsed_ms=int((time.time() - t_graph) * 1000),
    ))

    # ── PHASE 4: Build tool dicts with enrichment ─────────────────
    t_enrich = time.time()
    merged: List[Dict] = []
    for ev in prism_result.evidence:
        tool = ev.tool
        expl = explain_tool(tool, intent, profile)
        td = {
            "name": tool.name,
            "description": tool.description,
            "url": getattr(tool, "url", None),
            "categories": getattr(tool, "categories", []),
            "pricing": getattr(tool, "pricing", None),
            "skill_level": getattr(tool, "skill_level", None),
            "compliance": getattr(tool, "compliance", []),
            "integrations": getattr(tool, "integrations", []),
            "fit_score": expl.get("fit_score", 0),
            "reasons": expl.get("reasons", []),
            "caveats": expl.get("caveats", []),
            "faithfulness": round(ev.faithfulness, 2),
            "fact_verdict": prism_result.fact_audit.get(tool.name, "UNKNOWN"),
            "source": ev.source,
        }

        # Graft graph context
        gctx = graph_context.get(tool.name, {})
        if gctx:
            td["graph_competitors"] = gctx.get("competes_with", [])[:5]
            td["graph_integrations"] = gctx.get("integrates_with", [])[:5]
            td["graph_community"] = gctx.get("community", {}).get("summary", "")

        merged.append(td)

    # Apply constraints from plan
    merged = _apply_constraints(merged, constraints)
    merged = _enrich_with_vendor_intel(merged)

    steps.append(ReasoningStep(
        phase="observe",
        action=f"Enriched {len(merged)} tools with explanations, graph, and vendor intel",
        elapsed_ms=int((time.time() - t_enrich) * 1000),
    ))

    # ── PHASE 5: Reflect ──────────────────────────────────────────
    t_ref = time.time()
    try:
        if use_llm:
            critique = _llm_reflect(query, plan, merged[:8])
        else:
            critique = _local_reflect(query, plan, merged[:8])
    except Exception:
        critique = _local_reflect(query, plan, merged[:8])

    confidence = critique.get("confidence", 0.5)

    # Layer in PRISM metrics
    if prism_result.f1 > 0:
        confidence = confidence * 0.7 + prism_result.f1 * 0.3

    # Penalise if many FACT-AUDIT conflicts
    if prism_result.conflicts_found:
        penalty = min(len(prism_result.conflicts_found) * 0.03, 0.15)
        confidence = max(0.1, confidence - penalty)

    steps.append(ReasoningStep(
        phase="reflect",
        action=f"Self-critique: confidence={confidence:.2f}, "
               f"PRISM F1={prism_result.f1:.2f}, "
               f"conflicts={len(prism_result.conflicts_found)}",
        detail={**critique, "prism_f1": prism_result.f1,
                "conflicts": prism_result.conflicts_found[:5]},
        elapsed_ms=int((time.time() - t_ref) * 1000),
    ))

    # ── PHASE 6: Synthesize ───────────────────────────────────────
    t_synth = time.time()
    top_tools = merged[:8]

    try:
        if use_llm:
            narrative = _llm_synthesize(query, plan, top_tools, critique)
        else:
            narrative = _local_synthesize(query, top_tools, critique)
    except Exception:
        narrative = _local_synthesize(query, top_tools, critique)

    # Append community insights
    if comm_summaries and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        narrative += " *Ecosystem context: " + comm_summaries[0] + "*"

    # Append vertical intelligence
    if vertical_ctx and vertical_ctx.get("verticals") and len(vertical_ctx["verticals"]) > 0 and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        top_v = vertical_ctx["verticals"][0]
        vname = top_v.get("vertical_name", "unknown")
        narrative += f" *Industry vertical: {vname}.*"

        # Warn about action vs decision task boundaries
        wf = vertical_ctx.get("workflow_classification")
        if wf:
            decision_names = [
                d["name"] for d in wf.get("decision_tasks", [])
                if d.get("relevance") == "high"
            ]
            if decision_names:
                narrative += (
                    f" Note: your query touches on decision-level tasks "
                    f"({', '.join(decision_names[:3])}) that require human "
                    f"judgment — AI tools can support but not replace these."
                )

        # Surface anti-pattern warnings
        if _VERTICALS_OK:
            try:
                tool_names = [t["name"] for t in top_tools]
                ap_warnings = _check_anti_patterns(
                    query, tool_names,
                    verticals=vertical_ctx.get("verticals"),
                )
                for w in ap_warnings[:2]:
                    all_caveats.insert(0, f"⚠ {w['anti_pattern']}: {w['description']}")
            except Exception:
                pass

        # Surface compound workflows
        for cw in vertical_ctx.get("compound_workflows", [])[:1]:
            narrative += (
                f" *Compound workflow available: {cw['name']} — "
                f"{cw['description']}*"
            )

    # Append guardrails intelligence
    if safety_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        s_score = safety_ctx.get("safety_score", 1.0)
        if s_score < 0.5:
            narrative += (
                f" *Safety advisory: query safety score is {s_score:.2f} — "
                f"consider applying guardrail patterns before deployment.*"
            )
        pat = safety_ctx.get("recommended_pattern") or {}
        if isinstance(pat, dict) and pat.get("pattern_id"):
            narrative += (
                f" *Recommended guardrail: {pat['pattern_id']} — "
                f"{pat.get('description', '')}*"
            )

    # Append architecture intelligence
    if arch_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        eng = arch_ctx.get("engineering_style", {})
        if eng.get("warnings"):
            for w in eng["warnings"][:1]:
                all_caveats.insert(0, f"⚠ Architecture: {w}")
        arch_pats = arch_ctx.get("patterns", [])
        if arch_pats:
            top_pat = arch_pats[0]
            narrative += (
                f" *Architecture pattern: {top_pat['name']} "
                f"(complexity: {top_pat.get('complexity', 'unknown')}).*"
            )
        for ap in arch_ctx.get("anti_patterns_detected", [])[:2]:
            all_caveats.insert(0, f"⚠ {ap}")

    # Append resilience intelligence
    if resilience_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        vr = resilience_ctx.get("vibe_risk", 0)
        if vr > 0.3:
            narrative += (
                f" *Resilience advisory: vibe-coding risk score {vr:.2f} "
                f"(grade {resilience_ctx.get('grade', '?')}) — "
                f"consider applying TDD prompt engineering and R.P.I. framework.*"
            )
        for w in resilience_ctx.get("warnings", [])[:2]:
            all_caveats.insert(0, f"⚠ Resilience: {w}")

    # Append metacognition intelligence
    if metacog_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        sa = metacog_ctx.get("self_awareness", 1.0)
        if sa < 0.7:
            narrative += (
                f" *Metacognition advisory: self-awareness score {sa:.2f} "
                f"(grade {metacog_ctx.get('grade', '?')}) — "
                f"structural entropy and AI-generation signals detected; "
                f"apply Analyze→Patch→Verify→Propose cycle.*"
            )
        if metacog_ctx.get("bankruptcy_risk", 0) > 0.5:
            narrative += (
                f" *Technical bankruptcy risk {metacog_ctx['bankruptcy_risk']:.2f} — "
                f"Four Horsemen pathologies present.*"
            )
        for w in metacog_ctx.get("warnings", [])[:2]:
            all_caveats.insert(0, f"⚠ Metacognition: {w}")

    # Append real self-introspection intelligence
    if introspect_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        ent = introspect_ctx.get("entropy_score", 0)
        if ent > 0.3:
            dims = introspect_ctx.get("dimensions", {})
            worst_dim = max(dims, key=dims.get) if dims else "unknown"
            narrative += (
                f" *Self-introspection: Praxis structural entropy {ent:.2f} "
                f"(grade {introspect_ctx.get('grade', '?')}) — "
                f"largest deficit: {worst_dim.replace('_', ' ')}.*"
            )
            all_caveats.insert(0, f"⚠ Self-aware: entropy {ent:.2f} — {introspect_ctx.get('status', '?')}")

    # Append Architecture of Awakening intelligence
    if awakening_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        cs = awakening_ctx.get("consciousness", 0)
        vsd_s = awakening_ctx.get("vsd_score", 0)
        if cs < 0.6:
            narrative += (
                f" *Awakening advisory: consciousness score {cs:.2f} "
                f"(grade {awakening_ctx.get('grade', '?')}) — "
                f"VSD alignment {vsd_s:.2f}; apply Remember·Build·Witness triad.*"
            )
        if awakening_ctx.get("leaks", 0) > 0:
            narrative += (
                f" *Leaky abstractions detected ({awakening_ctx['leaks']}) — "
                f"the architecture is showing its seams.*"
            )
        if awakening_ctx.get("supply_risk", 0) > 0.5:
            narrative += (
                f" *Supply chain risk elevated ({awakening_ctx['supply_risk']:.2f}) — "
                f"audit dependencies before deployment.*"
            )
        for w in awakening_ctx.get("warnings", [])[:2]:
            all_caveats.insert(0, f"⚠ Awakening: {w}")

    # Append Self-Authorship intelligence
    if authorship_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        aus = authorship_ctx.get("authorship", 0)
        if aus < 0.6:
            narrative += (
                f" *Authorship advisory: self-authorship score {aus:.2f} "
                f"(grade {authorship_ctx.get('grade', '?')}) — "
                f"DDD={authorship_ctx.get('ddd_grade', '?')}, "
                f"continuity={authorship_ctx.get('continuity_grade', '?')}, "
                f"resilience={authorship_ctx.get('resilience_grade', '?')}.*"
            )
        if authorship_ctx.get("dishonesty_count", 0) > 0:
            narrative += (
                f" *Architectural dishonesty signals detected "
                f"({authorship_ctx['dishonesty_count']}) — "
                f"the system may be lying to itself.*"
            )
        if authorship_ctx.get("agent_readiness", "C") in ("D", "F"):
            narrative += (
                f" *Coherence trap risk — AI agents may need metacognitive "
                f"critic layers (CrewAI/LangGraph + Langfuse).*"
            )
        for w in authorship_ctx.get("warnings", [])[:2]:
            all_caveats.insert(0, f"⚠ Authorship: {w}")

    # Append Architectural Enlightenment intelligence
    if enlightenment_ctx and os.getenv("PRAXIS_DEBUG_OUTPUT", "0") == "1":
        ens = enlightenment_ctx.get("enlightenment", 0)
        if ens < 0.6:
            narrative += (
                f" *Enlightenment advisory: score {ens:.2f} "
                f"(grade {enlightenment_ctx.get('grade', '?')}) — "
                f"unity={enlightenment_ctx.get('unity_grade', '?')}, "
                f"alignment={enlightenment_ctx.get('alignment_grade', '?')}, "
                f"connection={enlightenment_ctx.get('connection_grade', '?')}.*"
            )
        if enlightenment_ctx.get("ego_grade", "C") in ("D", "F"):
            narrative += (
                " *Data silo ego detected — apply DDD bounded contexts "
                "and Repository Pattern for ego dissolution.*"
            )
        if enlightenment_ctx.get("remembrance_grade", "C") in ("D", "F"):
            narrative += (
                " *State amnesia risk — consider python-statemachine or "
                "transitions library for explicit FSM governance.*"
            )
        for w in enlightenment_ctx.get("warnings", [])[:2]:
            all_caveats.insert(0, f"⚠ Enlightenment: {w}")

    steps.append(ReasoningStep(
        phase="synthesize",
        action="Generated cognitive narrative with graph + PRISM + vertical + guardrails + architecture + resilience + metacognition + introspection + awakening + authorship + enlightenment context",
        elapsed_ms=int((time.time() - t_synth) * 1000),
    ))

    # ── Follow-ups & caveats ──────────────────────────────────────
    follow_ups = _generate_follow_ups(query, plan, top_tools, critique)
    # Append tool / PRISM / critique caveats to the domain-intelligence
    # caveats already gathered (verticals, architecture, resilience, etc.)
    for t in top_tools[:3]:
        for c in t.get("caveats", []):
            if c not in all_caveats:
                all_caveats.append(c)
    for c in prism_result.conflicts_found[:4]:
        if c not in all_caveats:
            all_caveats.append(c)
    for issue in critique.get("issues", []):
        if issue not in all_caveats:
            all_caveats.append(issue)

    total_ms = int((time.time() - t0) * 1000)
    depth = prism_result.iterations + 1  # +1 for the plan phase

    result = ReasoningResult(
        query=query,
        plan=research_steps,
        steps=steps,
        tools_considered=len(prism_result.evidence),
        tools_recommended=[
            {
                "name": t["name"],
                "description": t.get("description", ""),
                "url": t.get("url"),
                "categories": t.get("categories", []),
                "fit_score": t.get("fit_score", 0),
                "reasons": t.get("reasons", [])[:4],
                "caveats": t.get("caveats", [])[:3],
                "pricing": t.get("pricing"),
                "integrations": t.get("integrations", []),
                "compliance": t.get("compliance", []),
                "skill_level": t.get("skill_level"),
                "transparency_score": t.get("transparency_score"),
                "transparency_grade": t.get("transparency_grade"),
                "freedom_score": t.get("freedom_score"),
                "freedom_grade": t.get("freedom_grade"),
                "faithfulness": t.get("faithfulness"),
                "fact_verdict": t.get("fact_verdict"),
                "source": t.get("source"),
                "graph_competitors": t.get("graph_competitors", []),
                "graph_integrations": t.get("graph_integrations", []),
                "graph_community": t.get("graph_community", ""),
                "vertical_id": vertical_ctx["verticals"][0].get("vertical_id") if vertical_ctx and vertical_ctx.get("verticals") and len(vertical_ctx["verticals"]) > 0 else None,
            }
            for t in top_tools[:8]
        ],
        narrative=narrative,
        confidence=round(confidence, 2),
        caveats=all_caveats[:10],
        follow_up_questions=follow_ups,
        total_elapsed_ms=total_ms,
        mode=f"{mode}+cognitive",
        reasoning_depth=depth,
    )

    log.info(
        "deep_reason_v2: done in %dms, mode=%s, depth=%d, tools=%d, confidence=%.2f",
        total_ms, mode, depth, len(top_tools), confidence,
    )
    return result
