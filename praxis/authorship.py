# ─────────────────────────────────────────────────────────────
# authorship.py — Self-Authorship: Translating the Weight of
#                 Self-Authorship into Python System Architecture
# ─────────────────────────────────────────────────────────────
"""
v13 — Encodes the "Self-Authorship" philosophical framework
into Praxis's reasoning pipeline.

The doctrine identifies **eight responsibilities** of the
conscious system architect, plus a capstone on metacognitive
AI agents:

    1. Honesty          — Runtime invariants, reflective auditing
    2. Interconnection   — DDD, Hexagonal Architecture, bounded contexts
    3. Continuity        — Event Sourcing, CQRS, immutable ledger
    4. Corruption Detect — Observability, circuit breakers, self-healing
    5. Teaching          — Plugin architectures, DSLs, empowering users
    6. Isolation Mgmt    — Architecture Decision Records (ADRs)
    7. Destruction       — Strangler Fig, feature flags, graceful degradation
    8. Documentation     — Self-documenting code, transparent dashboards

Capstone:  **Metacognitive AI Agents** — beyond the coherence trap

Every function is deterministic and stdlib-only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

log = logging.getLogger("praxis.authorship")


# =====================================================================
# §1 — The Eight Responsibilities
# =====================================================================

RESPONSIBILITIES: List[Dict[str, Any]] = [
    {
        "id": "honesty",
        "number": 1,
        "title": "Honesty About System Nature via Runtime Invariants & Reflective Auditing",
        "doctrine": "If an architect is the only one who truly understands the system, they are solely responsible for catching their own blind spots.",
        "anti_patterns": [
            "Suppressing exceptions to maintain the illusion of stability",
            "Allowing malformed data to pass silently through execution context",
            "Relying on implicit structural assumptions that collapse under load",
        ],
        "python_practices": [
            "Pydantic BaseModel with strict runtime validation (Rust-backed)",
            "ConfigDict(validate_assignment=True) to prevent post-creation state corruption",
            "AfterValidator for deep semantic integrity checks",
            "Pydantic Logfire for monitoring validation success/failure",
            "Reflective auditing via inspect module (isfunction, getfullargspec)",
            "CI/CD reflective scripts to catch architectural drift before deploy",
        ],
        "keywords": [
            "pydantic", "validation", "runtime", "invariant", "contract",
            "type check", "inspect", "reflection", "introspection",
            "data integrity", "schema", "strict", "mypy", "type hint",
            "after validator", "logfire", "audit",
        ],
    },
    {
        "id": "interconnection",
        "number": 2,
        "title": "Interconnected Narratives through Domain-Driven Design",
        "doctrine": "No story exists in isolation. A poorly structured service corrupts the narrative of every consumer that relies upon it.",
        "patterns": {
            "domain_model": {
                "function": "Defines Entities, Value Objects, Aggregates using pure Python",
                "equivalent": "The core truth and intrinsic identity of the architecture",
            },
            "repository": {
                "function": "Decouples domain from persistent storage mechanisms",
                "equivalent": "Identity remains independent of where memory is stored",
            },
            "unit_of_work": {
                "function": "Orchestrates atomic operations — all-or-nothing state changes",
                "equivalent": "Narrative shift is complete in entirety or not at all",
            },
            "service_layer": {
                "function": "Defines system boundaries; orchestrates use cases from outside world",
                "equivalent": "Outward-facing interface negotiating with other stories",
            },
        },
        "python_practices": [
            "Hexagonal Architecture (Ports and Adapters) — isolate domain from infrastructure",
            "Bounded Contexts — explicit boundaries between subdomains",
            "Flask/FastAPI/Django relegated to delivery mechanism only",
            "Database swap (PostgreSQL → MongoDB) has zero impact on domain model",
        ],
        "keywords": [
            "ddd", "domain driven", "hexagonal", "ports and adapters",
            "bounded context", "aggregate", "entity", "value object",
            "repository pattern", "unit of work", "service layer",
            "coupling", "decoupling", "api boundary", "domain model",
        ],
    },
    {
        "id": "continuity",
        "number": 3,
        "title": "Maintaining Continuity via Event Sourcing",
        "doctrine": "A system that cannot remember its past cannot be held accountable for its evolution.",
        "anti_patterns": [
            "CRUD UPDATE overwrites previous state — serial abandonment of selves",
            "System starts over with each transaction, retaining no memory",
            "Mutable database rows that destroy historical lineage",
        ],
        "python_practices": [
            "Event Sourcing via eventsourcing library — record every discrete action",
            "Append-only immutable event ledger — never overwrite",
            "Rebuild state at any point in time by replaying from genesis",
            "Optimistic concurrency controls to prevent narrative corruption",
            "CQRS — separate command (write) and query (read) pathways",
            "reaktiv for declarative reactive state management",
        ],
        "cqrs": {
            "command_side": "Records immutable truth of what occurred",
            "query_side": "Generates materialized views and projections",
            "benefit": "Total freedom to reinterpret data in the present + absolute responsibility for preserving the past",
        },
        "keywords": [
            "event sourcing", "cqrs", "immutable", "append only",
            "event log", "replay", "domain event", "ledger",
            "command", "query", "projection", "materialised view",
            "concurrency", "eventsourcing", "reaktiv",
        ],
    },
    {
        "id": "corruption_detection",
        "number": 4,
        "title": "Knowing When Your Architecture Is Corrupted via Observability",
        "doctrine": "When a system drops requests but logs HTTP 200, its fear is architecting — pretending deception is prudence.",
        "corruption_types": [
            "Degradation of logic",
            "Quiet failure of background jobs",
            "Masking of timeouts",
            "Optimising for comfort over correctness",
            "Dropping requests to avoid memory exhaustion while reporting success",
        ],
        "python_practices": [
            "OpenTelemetry (OTel) — vendor-agnostic distributed tracing, metrics, logging",
            "Auto-instrumentation via monkey-patching for FastAPI, Flask, SQLAlchemy",
            "Structured JSON logging with contextual metadata (user ID, tx ID, memory, __name__)",
            "Log-trace correlation via OpenTelemetry + Python logging integration",
            "Loki + Grafana for interconnected timeline visualisation",
            "Circuit Breaker (pybreaker) — trip on repeated failures, shed load gracefully",
            "Try-Heal-Retry architecture instead of naive aggressive retries",
        ],
        "circuit_breaker": {
            "mechanism": "Monitors external API calls; trips on repeated failure/latency",
            "states": ["closed (normal)", "open (tripped — fast-failing)", "half-open (probing recovery)"],
            "params": ["fail_max", "reset_timeout"],
            "doctrine_link": "Ruthlessly honest about what the system can and cannot accomplish during outage",
        },
        "keywords": [
            "observability", "opentelemetry", "otel", "tracing", "trace",
            "circuit breaker", "pybreaker", "fallback", "retry",
            "structured logging", "json logging", "loki", "grafana",
            "latency", "timeout", "health check", "monitoring",
            "auto-instrumentation", "corruption", "silent failure",
        ],
    },
    {
        "id": "teaching",
        "number": 5,
        "title": "Teaching Others to Author Themselves via DSLs & Plugins",
        "doctrine": "Power is hoarded when systems are impenetrable monoliths. A responsible architecture shows users that the pen exists.",
        "plugin_frameworks": [
            {
                "framework": "stevedore",
                "mechanism": "Manages dynamic plugins via entry_points in pyproject.toml",
                "coupling": "Highly decoupled — standard metadata, interface-driven",
            },
            {
                "framework": "pluggy",
                "mechanism": "Hook-calling system (used by pytest) — plugins intercept core behaviours via decorators",
                "coupling": "Highly decoupled — callback-oriented, dynamic intervention",
            },
            {
                "framework": "Native Entry Points",
                "mechanism": "PyPA specification (importlib.metadata) for installed distributions to advertise components",
                "coupling": "Standardised interoperability without heavy dependencies",
            },
        ],
        "dsl_approach": {
            "library": "textX",
            "parser": "Arpeggio PEG — builds parser + meta-model from grammar description",
            "power_transfer": "Non-programmers (analysts, stakeholders) author complex logic without original architects",
            "use_cases": ["data pipeline config", "finite state machines", "architectural layouts"],
        },
        "python_practices": [
            "Abstract base class defines interface contract",
            "Downstream devs write concrete implementations independently",
            "Core functionality insulated; extensions independently tested & deployed",
            "textX DSL for non-programmer authorship of business logic",
        ],
        "keywords": [
            "plugin", "stevedore", "pluggy", "entry point", "extension",
            "dsl", "domain specific language", "textx", "grammar",
            "hook", "callback", "extensible", "platform",
            "importlib", "metadata", "pyproject", "abstract",
        ],
    },
    {
        "id": "isolation",
        "number": 6,
        "title": "Navigating Isolated Complexity with Architecture Decision Records",
        "doctrine": "External observers cannot assess internal design compromises with the same fidelity as the original author.",
        "risks_of_isolation": [
            "Contempt for downstream users who 'don't understand'",
            "Messiah complex that rejects code reviews",
            "Creating artificial dependencies to maintain relevance",
        ],
        "adr_format": {
            "template": "Michael Nygard Markdown template",
            "contents": ["Business context", "Technical trade-offs considered", "Final justification"],
            "storage": "Alongside code in version control repository",
            "lifecycle": ["proposed", "accepted", "deprecated", "superseded"],
        },
        "python_practices": [
            "pyadr / adr-tools CLI for ADR lifecycle management",
            "ADRs stored in docs/adr/ within the repository",
            "Short, focused readout meetings before finalising ADRs",
            "Continuous decision log as asynchronous conversation with future developers",
        ],
        "keywords": [
            "adr", "architecture decision record", "decision log",
            "documentation", "trade-off", "rationale", "context",
            "nygard", "proposed", "accepted", "deprecated", "superseded",
            "isolation", "knowledge management",
        ],
    },
    {
        "id": "destruction",
        "number": 7,
        "title": "Productive Destruction via the Strangler Fig Pattern",
        "doctrine": "There are moments when the story originally authored becomes a prison. Tearing down a legacy monolith requires immense courage.",
        "strangler_fig": {
            "inspiration": "Biological strangler fig tree — seeds in canopy, roots wrap and replace host",
            "mechanism": "New features in isolated modern microservices; facade routes traffic; old system slowly strangled",
            "advantage": "Avoids high-risk big-bang rewrite; domain-by-domain migration",
        },
        "python_practices": [
            "API Gateway / middleware facade for traffic routing",
            "Feature flags (Unleash) for deterministic traffic split with user stickiness",
            "Graceful degradation — full capability → minimal capability → offline fallback",
            "Decoupling deployment from release for fine-grained control",
            "Fallback chain architecture for resilient multi-agent systems",
        ],
        "keywords": [
            "strangler fig", "legacy", "migration", "rewrite",
            "feature flag", "unleash", "facade", "proxy",
            "graceful degradation", "fallback", "routing",
            "decommission", "monolith", "microservice",
        ],
    },
    {
        "id": "documentation",
        "number": 8,
        "title": "Leaving Honest Documentation & Architecture Visibility",
        "doctrine": "The record must not be a sanitised autobiography. Future maintainers must learn from the genuine, flawed, pragmatic architecture.",
        "python_practices": [
            "Sphinx + autodoc + sphinx-autodoc-typehints — auto-generated from source",
            "napoleon extension for Google/NumPy style docstrings",
            "Documentation built at build time from runtime introspection — never drifts",
            "Streamlit for interactive real-time dashboards (purely declarative Python)",
            "Dash / Plotly / Bokeh for streaming data visualisation",
            "Interactive filtering, zooming, querying of live system state",
        ],
        "self_documenting": {
            "mechanism": "Sphinx imports modules and reads docstrings at build time",
            "guarantee": "API reference is exact reflection of runtime state",
            "anti_pattern": "Manual documentation that drifts from implementation — dangerous mythology",
        },
        "dashboard_tools": [
            {"tool": "Streamlit", "style": "Declarative Python scripts; top-to-bottom execution"},
            {"tool": "Dash", "style": "Plotly-backed interactive web apps"},
            {"tool": "Plotly", "style": "Rich interactive charts & graphs"},
            {"tool": "Bokeh", "style": "Real-time streaming data visualisation"},
        ],
        "keywords": [
            "sphinx", "autodoc", "documentation", "docstring",
            "napoleon", "streamlit", "dash", "plotly", "bokeh",
            "dashboard", "visualisation", "visualization",
            "self-documenting", "api reference", "transparency",
        ],
    },
]


# =====================================================================
# §2 — Metacognitive AI Agents (Capstone)
# =====================================================================

METACOGNITIVE_AGENTS: Dict[str, Any] = {
    "coherence_trap": {
        "description": "Standard ReAct agents lack internal alarm bells — they confidently execute flawed plans, hallucinate reasoning, burning tokens while driving off a logical cliff",
        "symptoms": ["Blind execution of flawed plans", "Retrieval of irrelevant documents", "Hallucinated reasoning chains", "No self-correction mechanism"],
    },
    "metacognitive_architecture": {
        "description": "Multi-agent system where specialised 'critic' agents evaluate reasoning logs, error rates, and latency of 'execution' agents",
        "frameworks": ["CrewAI", "LangGraph", "Amazon SageMaker", "Custom Python multi-agent"],
        "capabilities": [
            "Analyse execution traces for failure patterns",
            "Dynamically adjust reasoning depth and strategies in real time",
            "Note failures explicitly in internal state before retrying",
            "Adjust strategy rather than hallucinating a summary",
        ],
    },
    "ai_observability": {
        "description": "Session-level observability tracking intent, coherence, tool-call accuracy, and context retention",
        "platforms": ["Langfuse", "Arize"],
        "telemetry": ["Tokens consumed", "Latency incurred", "Prompt templates used", "Agent-to-external-system boundary interceptions"],
    },
    "self_healing_pipeline": {
        "description": "Catches failures (e.g. missing packages) without human intervention — parses stderr, recognises dependency, alters env, retries",
        "orchestrator": "Temporal",
        "cycle": ["Detect failure", "Parse stderr/traceback", "Identify root cause", "Apply fix", "Retry execution", "Validate success"],
    },
}


# =====================================================================
# §3 — Architectural Honesty Detector
# =====================================================================

_HONESTY_SIGNALS: Dict[str, Dict[str, Any]] = {
    "exception_suppression": {
        "patterns": ["bare except", "except pass", "suppress exception", "silent fail",
                      "catch all", "swallow error", "ignore exception"],
        "severity": 0.8,
        "description": "Suppressing exceptions to maintain the illusion of stability",
        "responsibility": "honesty",
    },
    "data_corruption": {
        "patterns": ["no validation", "unvalidated", "any type", "dict instead of",
                      "loose schema", "no schema", "malformed", "corrupt"],
        "severity": 0.7,
        "description": "Allowing malformed data to pass silently through execution context",
        "responsibility": "honesty",
    },
    "implicit_assumptions": {
        "patterns": ["hardcoded", "magic number", "assumed", "implicit",
                      "convention over config", "undocumented assumption"],
        "severity": 0.6,
        "description": "Relying on implicit structural assumptions that collapse under load",
        "responsibility": "honesty",
    },
    "history_destruction": {
        "patterns": ["update overwrite", "delete history", "no audit trail",
                      "mutable state", "crud only", "no event log"],
        "severity": 0.7,
        "description": "Destroying historical state — serial abandonment of selves",
        "responsibility": "continuity",
    },
    "fake_success": {
        "patterns": ["fake 200", "false success", "mask timeout", "hide error",
                      "drop request", "swallow failure", "phantom success"],
        "severity": 0.9,
        "description": "Reporting success while silently dropping requests — fear masquerading as prudence",
        "responsibility": "corruption_detection",
    },
    "monolith_hoarding": {
        "patterns": ["no api", "no plugin", "hardcoded logic", "monolith",
                      "no extension point", "closed system", "proprietary"],
        "severity": 0.6,
        "description": "Hoarding power by building impenetrable monoliths with no extension points",
        "responsibility": "teaching",
    },
    "undocumented": {
        "patterns": ["no docs", "undocumented", "no readme", "no adr",
                      "tribal knowledge", "bus factor", "no comments"],
        "severity": 0.7,
        "description": "Failing to leave honest documentation — creating mythology instead of records",
        "responsibility": "documentation",
    },
    "legacy_prison": {
        "patterns": ["legacy lock", "can't migrate", "big bang rewrite",
                      "stuck on old", "rewrite everything", "no migration path"],
        "severity": 0.6,
        "description": "Legacy architecture has become a prison with no incremental escape path",
        "responsibility": "destruction",
    },
}


def detect_dishonesty(query: str) -> Dict[str, Any]:
    """Scan a query for signals of architectural dishonesty.

    Returns detected dishonesty types, severity, and the
    responsibilities being violated.
    """
    q = query.lower()
    detected: List[Dict[str, Any]] = []
    violated_responsibilities: set = set()

    for signal_id, info in _HONESTY_SIGNALS.items():
        hits = [p for p in info["patterns"] if p in q]
        if hits:
            detected.append({
                "signal_id": signal_id,
                "description": info["description"],
                "severity": info["severity"],
                "responsibility": info["responsibility"],
                "matched_patterns": hits,
            })
            violated_responsibilities.add(info["responsibility"])

    total_severity = min(1.0, sum(d["severity"] for d in detected))
    return {
        "dishonesty_signals": detected,
        "total_severity": round(total_severity, 2),
        "violated_responsibilities": sorted(violated_responsibilities),
        "count": len(detected),
    }


# =====================================================================
# §4 — DDD Maturity Evaluator
# =====================================================================

_DDD_SIGNALS: Dict[str, Dict[str, Any]] = {
    "domain_isolation": {
        "positive": ["bounded context", "domain model", "aggregate", "entity",
                      "value object", "hexagonal", "ports and adapters", "pure domain"],
        "negative": ["framework bleeds", "orm in domain", "database coupled",
                      "no separation", "mixed concerns", "god object"],
        "weight": 0.30,
        "description": "Core domain model isolation from infrastructure",
    },
    "repository_pattern": {
        "positive": ["repository pattern", "data access layer", "abstract repository",
                      "interface", "dependency injection", "swap database"],
        "negative": ["direct sql in business", "orm everywhere", "tight coupling",
                      "hardcoded queries", "no abstraction"],
        "weight": 0.25,
        "description": "Decoupling domain from storage via repository interfaces",
    },
    "service_layer": {
        "positive": ["service layer", "use case", "application service",
                      "orchestration", "api boundary", "command handler"],
        "negative": ["api calls domain directly", "no service layer",
                      "controller does everything", "fat controller"],
        "weight": 0.25,
        "description": "Explicit service layer defining system boundaries",
    },
    "unit_of_work": {
        "positive": ["unit of work", "atomic operation", "transaction",
                      "all or nothing", "consistency boundary"],
        "negative": ["partial update", "inconsistent state", "no transaction",
                      "fragmented operation"],
        "weight": 0.20,
        "description": "Atomic state changes via Unit of Work pattern",
    },
}


def score_ddd_maturity(query: str) -> Dict[str, Any]:
    """Score Domain-Driven Design maturity of a described architecture.

    Returns per-dimension scores, composite DDD maturity,
    and recommendations.
    """
    q = query.lower()
    dimension_scores: List[Dict[str, Any]] = []
    weighted_sum = 0.0

    for dim_id, dim in _DDD_SIGNALS.items():
        pos = [s for s in dim["positive"] if s in q]
        neg = [s for s in dim["negative"] if s in q]
        raw = (len(pos) - len(neg)) / max(1, len(dim["positive"]))
        score = max(0.0, min(1.0, 0.5 + raw))

        dimension_scores.append({
            "dimension": dim_id,
            "score": round(score, 2),
            "weight": dim["weight"],
            "positive_matches": pos,
            "negative_matches": neg,
            "description": dim["description"],
        })
        weighted_sum += score * dim["weight"]

    composite = round(weighted_sum, 2)
    grade = (
        "A" if composite >= 0.80 else
        "B" if composite >= 0.65 else
        "C" if composite >= 0.50 else
        "D" if composite >= 0.35 else "F"
    )

    recommendations: List[str] = []
    for ds in dimension_scores:
        if ds["score"] < 0.5:
            recommendations.append(f"Strengthen {ds['dimension']}: {ds['description']}")

    return {
        "ddd_maturity": composite,
        "grade": grade,
        "dimensions": dimension_scores,
        "recommendations": recommendations,
        "hexagonal_note": (
            "In Hexagonal Architecture the domain model has zero framework "
            "dependencies. Switching PostgreSQL → MongoDB or REST → GraphQL "
            "should have zero impact on core domain logic."
        ),
    }


# =====================================================================
# §5 — Event Sourcing & Continuity Readiness
# =====================================================================

_CONTINUITY_POSITIVE = [
    "event sourcing", "immutable", "append only", "event log",
    "event store", "cqrs", "command query", "projection",
    "replay", "domain event", "temporal", "ledger",
    "optimistic concurrency", "audit trail", "versioned",
]

_CONTINUITY_NEGATIVE = [
    "crud only", "update overwrite", "mutable rows", "delete history",
    "no versioning", "no event log", "no audit",
    "schema migration destroys", "truncate",
]


def score_continuity(query: str) -> Dict[str, Any]:
    """Score event sourcing / continuity readiness.

    Returns a readiness score (0–1), grade, and CQRS guidance.
    """
    q = query.lower()
    pos = [s for s in _CONTINUITY_POSITIVE if s in q]
    neg = [s for s in _CONTINUITY_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_CONTINUITY_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    return {
        "continuity_score": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "cqrs_guidance": RESPONSIBILITIES[2]["cqrs"],
        "doctrine": RESPONSIBILITIES[2]["doctrine"],
    }


# =====================================================================
# §6 — Circuit Breaker & Resilience Posture
# =====================================================================

_RESILIENCE_POSITIVE = [
    "circuit breaker", "pybreaker", "fallback", "retry with backoff",
    "graceful degradation", "feature flag", "health check",
    "timeout config", "bulkhead", "load shedding",
    "opentelemetry", "tracing", "structured logging",
]

_RESILIENCE_NEGATIVE = [
    "naive retry", "aggressive retry", "no timeout", "silent fail",
    "no fallback", "no circuit breaker", "bare except",
    "unstructured log", "print debug", "no monitoring",
]


def score_resilience_posture(query: str) -> Dict[str, Any]:
    """Score system resilience posture including circuit breaker readiness.

    Returns resilience score, grade, and circuit breaker guidance.
    """
    q = query.lower()
    pos = [s for s in _RESILIENCE_POSITIVE if s in q]
    neg = [s for s in _RESILIENCE_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_RESILIENCE_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    return {
        "resilience_score": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "circuit_breaker": RESPONSIBILITIES[3]["circuit_breaker"],
        "try_heal_retry": (
            "Instead of naive, aggressive retries that exacerbate failure, "
            "use Try-Heal-Retry: trip the circuit breaker, shed load, "
            "sit patiently in a productive void until downstream recovers."
        ),
    }


# =====================================================================
# §7 — Plugin & Extensibility Maturity
# =====================================================================

_EXTENSIBILITY_POSITIVE = [
    "plugin", "stevedore", "pluggy", "entry point", "hook",
    "extensible", "abstract base", "interface", "protocol",
    "dsl", "domain specific language", "textx", "grammar",
    "callback", "event driven", "open closed",
]

_EXTENSIBILITY_NEGATIVE = [
    "monolith", "hardcoded", "no extension", "closed system",
    "proprietary", "no plugin", "no api", "tightly coupled",
    "no interface", "no abstraction",
]


def score_extensibility(query: str) -> Dict[str, Any]:
    """Score plugin architecture and extensibility maturity.

    Returns extensibility score, grade, and plugin framework guidance.
    """
    q = query.lower()
    pos = [s for s in _EXTENSIBILITY_POSITIVE if s in q]
    neg = [s for s in _EXTENSIBILITY_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_EXTENSIBILITY_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    return {
        "extensibility_score": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "plugin_frameworks": RESPONSIBILITIES[4]["plugin_frameworks"],
        "dsl_approach": RESPONSIBILITIES[4]["dsl_approach"],
    }


# =====================================================================
# §8 — Strangler Fig Migration Readiness
# =====================================================================

_MIGRATION_POSITIVE = [
    "strangler fig", "incremental migration", "facade", "proxy",
    "feature flag", "unleash", "canary", "blue green",
    "graceful degradation", "fallback chain", "api gateway",
    "domain by domain", "gradual replacement",
]

_MIGRATION_NEGATIVE = [
    "big bang rewrite", "rewrite everything", "all at once",
    "no migration path", "legacy lock", "stuck on old",
    "no feature flag", "no rollback",
]


def score_migration_readiness(query: str) -> Dict[str, Any]:
    """Score readiness for Strangler Fig-style legacy migration.

    Returns migration readiness score, grade, and guidance.
    """
    q = query.lower()
    pos = [s for s in _MIGRATION_POSITIVE if s in q]
    neg = [s for s in _MIGRATION_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_MIGRATION_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    return {
        "migration_readiness": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "strangler_fig": RESPONSIBILITIES[6]["strangler_fig"],
        "doctrine": RESPONSIBILITIES[6]["doctrine"],
    }


# =====================================================================
# §9 — Documentation & Visibility Scorer
# =====================================================================

_DOCUMENTATION_POSITIVE = [
    "sphinx", "autodoc", "docstring", "napoleon", "adr",
    "architecture decision", "self-documenting", "openapi",
    "swagger", "streamlit", "dashboard", "plotly",
    "interactive", "transparent", "api docs",
]

_DOCUMENTATION_NEGATIVE = [
    "no docs", "undocumented", "tribal knowledge", "no readme",
    "manual docs", "outdated docs", "stale docs", "no adr",
    "no api reference", "bus factor",
]


def score_documentation_health(query: str) -> Dict[str, Any]:
    """Score documentation health and architecture visibility.

    Returns documentation score, grade, and tooling guidance.
    """
    q = query.lower()
    pos = [s for s in _DOCUMENTATION_POSITIVE if s in q]
    neg = [s for s in _DOCUMENTATION_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_DOCUMENTATION_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    return {
        "documentation_score": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "self_documenting": RESPONSIBILITIES[7]["self_documenting"],
        "dashboard_tools": RESPONSIBILITIES[7]["dashboard_tools"],
    }


# =====================================================================
# §10 — Metacognitive Agent Readiness
# =====================================================================

_AGENT_POSITIVE = [
    "metacognitive", "critic agent", "self-monitoring", "multi-agent",
    "crewai", "langgraph", "langfuse", "arize", "self-healing",
    "temporal", "execution trace", "strategy adjustment",
    "error rate monitoring", "adaptive", "reasoning depth",
]

_AGENT_NEGATIVE = [
    "no monitoring", "blind execution", "no critic", "single agent",
    "no self-correction", "hallucinate", "coherence trap",
    "no observability", "no trace", "burns tokens",
]


def score_agent_readiness(query: str) -> Dict[str, Any]:
    """Score metacognitive AI agent readiness.

    Returns agent maturity score, grade, coherence trap warnings,
    and self-healing pipeline guidance.
    """
    q = query.lower()
    pos = [s for s in _AGENT_POSITIVE if s in q]
    neg = [s for s in _AGENT_NEGATIVE if s in q]

    raw = (len(pos) - len(neg) * 0.7) / max(1, len(_AGENT_POSITIVE) * 0.5)
    score = max(0.0, min(1.0, round(0.5 + raw, 2)))

    grade = (
        "A" if score >= 0.80 else
        "B" if score >= 0.65 else
        "C" if score >= 0.50 else
        "D" if score >= 0.35 else "F"
    )

    coherence_trap_warning = score < 0.4
    return {
        "agent_readiness": score,
        "grade": grade,
        "positive_signals": pos,
        "negative_signals": neg,
        "coherence_trap_warning": coherence_trap_warning,
        "metacognitive_architecture": METACOGNITIVE_AGENTS["metacognitive_architecture"],
        "self_healing_pipeline": METACOGNITIVE_AGENTS["self_healing_pipeline"],
        "ai_observability": METACOGNITIVE_AGENTS["ai_observability"],
    }


# =====================================================================
# §11 — Master Assessment: Self-Authorship
# =====================================================================

@dataclass
class AuthorshipAssessment:
    """Unified assessment from the Self-Authorship framework."""
    query: str
    authorship_score: float           # 0–1 composite
    grade: str
    violated_responsibilities: List[str]
    honesty: Dict[str, Any]
    ddd_maturity: Dict[str, Any]
    continuity: Dict[str, Any]
    resilience_posture: Dict[str, Any]
    extensibility: Dict[str, Any]
    migration_readiness: Dict[str, Any]
    documentation_health: Dict[str, Any]
    agent_readiness: Dict[str, Any]
    warnings: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_authorship(query: str) -> Dict[str, Any]:
    """Master assessment: run all Self-Authorship subsystems.

    Returns a unified AuthorshipAssessment combining:
    - Architectural honesty detection
    - DDD maturity scoring
    - Event sourcing / continuity readiness
    - Circuit breaker / resilience posture
    - Plugin / extensibility maturity
    - Strangler Fig migration readiness
    - Documentation & visibility health
    - Metacognitive agent readiness
    """
    honesty = detect_dishonesty(query)
    ddd = score_ddd_maturity(query)
    continuity = score_continuity(query)
    resilience = score_resilience_posture(query)
    extensibility = score_extensibility(query)
    migration = score_migration_readiness(query)
    docs = score_documentation_health(query)
    agents = score_agent_readiness(query)

    # Composite authorship score (weighted)
    authorship = round(
        (1.0 - honesty["total_severity"]) * 0.15
        + ddd["ddd_maturity"] * 0.15
        + continuity["continuity_score"] * 0.10
        + resilience["resilience_score"] * 0.15
        + extensibility["extensibility_score"] * 0.10
        + migration["migration_readiness"] * 0.10
        + docs["documentation_score"] * 0.10
        + agents["agent_readiness"] * 0.15,
        2,
    )

    grade = (
        "A" if authorship >= 0.80 else
        "B" if authorship >= 0.65 else
        "C" if authorship >= 0.50 else
        "D" if authorship >= 0.35 else "F"
    )

    # Aggregate warnings
    warnings: List[str] = []
    if honesty["total_severity"] > 0.5:
        warnings.append(
            f"Architectural dishonesty detected (severity {honesty['total_severity']}) — "
            f"the system is lying to itself"
        )
    if ddd["ddd_maturity"] < 0.4:
        warnings.append(
            f"Low DDD maturity ({ddd['grade']}) — domain model bleeds into infrastructure"
        )
    if continuity["continuity_score"] < 0.4:
        warnings.append(
            f"Weak continuity posture ({continuity['grade']}) — "
            f"state history may be destructively overwritten"
        )
    if resilience["resilience_score"] < 0.4:
        warnings.append(
            f"Poor resilience posture ({resilience['grade']}) — "
            f"no circuit breaker or graceful degradation detected"
        )
    if extensibility["extensibility_score"] < 0.4:
        warnings.append(
            f"Low extensibility ({extensibility['grade']}) — "
            f"system may be hoarding power as an impenetrable monolith"
        )
    if docs["documentation_score"] < 0.4:
        warnings.append(
            f"Documentation deficit ({docs['grade']}) — "
            f"future maintainers inherit mythology, not records"
        )
    if agents.get("coherence_trap_warning"):
        warnings.append(
            "Coherence trap risk — AI agents may be blindly executing "
            "without metacognitive self-monitoring"
        )

    # Aggregate recommendations
    recommendations: List[str] = list(ddd.get("recommendations", []))
    for r in honesty.get("dishonesty_signals", []):
        recommendations.append(f"Fix: {r['description']}")
    if continuity["continuity_score"] < 0.5:
        recommendations.append(
            "Consider Event Sourcing — record every state change as an immutable domain event"
        )
    if resilience["resilience_score"] < 0.5:
        recommendations.append(
            "Implement Circuit Breaker (pybreaker) and OpenTelemetry distributed tracing"
        )
    if extensibility["extensibility_score"] < 0.5:
        recommendations.append(
            "Add plugin architecture (stevedore/pluggy) and consider a DSL for non-programmer authorship"
        )
    if docs["documentation_score"] < 0.5:
        recommendations.append(
            "Set up Sphinx + autodoc for self-documenting code; adopt ADRs for decision transparency"
        )
    if agents.get("coherence_trap_warning"):
        recommendations.append(
            "Add metacognitive critic agents and self-healing pipeline (Langfuse + Temporal)"
        )

    assessment = AuthorshipAssessment(
        query=query,
        authorship_score=authorship,
        grade=grade,
        violated_responsibilities=honesty.get("violated_responsibilities", []),
        honesty=honesty,
        ddd_maturity=ddd,
        continuity=continuity,
        resilience_posture=resilience,
        extensibility=extensibility,
        migration_readiness=migration,
        documentation_health=docs,
        agent_readiness=agents,
        warnings=warnings,
        recommendations=recommendations[:15],
    )

    log.info(
        "authorship assessment: score=%.2f (%s), %d dishonesty signals, "
        "DDD=%s, continuity=%s, resilience=%s, %d warnings",
        authorship, grade, honesty["count"],
        ddd["grade"], continuity["grade"], resilience["grade"],
        len(warnings),
    )

    return assessment.to_dict()


# =====================================================================
# §12 — Public API Helpers
# =====================================================================

def get_responsibilities() -> List[Dict[str, Any]]:
    """Return the eight responsibilities catalogue."""
    return RESPONSIBILITIES


def get_responsibility(resp_id: str) -> Optional[Dict[str, Any]]:
    """Return a single responsibility by id."""
    for r in RESPONSIBILITIES:
        if r["id"] == resp_id:
            return r
    return None


def get_metacognitive_agents() -> Dict[str, Any]:
    """Return the metacognitive AI agent architecture."""
    return METACOGNITIVE_AGENTS


def get_coherence_trap() -> Dict[str, Any]:
    """Return the coherence trap definition and warning signs."""
    return METACOGNITIVE_AGENTS["coherence_trap"]


def get_self_healing_pipeline() -> Dict[str, Any]:
    """Return the self-healing pipeline architecture."""
    return METACOGNITIVE_AGENTS["self_healing_pipeline"]


def get_strangler_fig() -> Dict[str, Any]:
    """Return the Strangler Fig pattern details."""
    return RESPONSIBILITIES[6]["strangler_fig"]


def get_circuit_breaker() -> Dict[str, Any]:
    """Return the circuit breaker pattern details."""
    return RESPONSIBILITIES[3]["circuit_breaker"]


def get_ddd_patterns() -> Dict[str, Any]:
    """Return DDD patterns and their philosophical equivalents."""
    return RESPONSIBILITIES[1]["patterns"]


def get_plugin_frameworks() -> List[Dict[str, Any]]:
    """Return the plugin framework comparison."""
    return RESPONSIBILITIES[4]["plugin_frameworks"]
