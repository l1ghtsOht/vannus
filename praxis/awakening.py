# ─────────────────────────────────────────────────────────────
# awakening.py — Architecture of Awakening: Conscious System Design
# ─────────────────────────────────────────────────────────────
"""
v12 — Encodes the "Architecture of Awakening" philosophical
framework into Praxis's reasoning pipeline.

The doctrine identifies **six recognitions** that map software
engineering patterns to a philosophical model of consciousness:

    1. Metaprogramming & Leaky Abstractions  (The Forgetting)
    2. State Management & Responsibility      (The End of Innocence)
    3. Observability & Witnessing              (The Social Record)
    4. Decorators & Trojan Horses              (The Dual Payload)
    5. Value Sensitive Design                  (The Commandment)
    6. Paradox & Technical Debt                (The Contradiction)

Master triad:  **Remember · Build · Witness**

Every function in this module is deterministic and stdlib-only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

log = logging.getLogger("praxis.awakening")


# =====================================================================
# §1 — The Six Recognitions
# =====================================================================

RECOGNITIONS: List[Dict[str, Any]] = [
    {
        "id": "first",
        "number": 1,
        "title": "Metaprogramming, Reflection & Leaky Abstractions",
        "doctrine": "The cage has no lock because you are both prisoner and architect.",
        "metaphor": "The Architecture of Forgetting",
        "python_concepts": [
            "Metaclasses (type.__new__, __init_subclass__)",
            "Reflection (type, isinstance, dir, getattr, setattr, inspect)",
            "Quines / Ouroboros programs — code producing its own source",
            "Custom __new__ / __init__ interception",
        ],
        "leaky_abstractions": [
            {
                "illusion": "Object-Relational Mappers (ORMs)",
                "crumb": "N+1 query performance degradation; complex joins failing silently",
                "awakening": "Dropping to raw SQL; understanding relational mechanics",
            },
            {
                "illusion": "Generational Garbage Collection",
                "crumb": "MemoryError exceptions; quadratic-time collection on large heaps",
                "awakening": "Profiling allocation; understanding CPython reference counting",
            },
            {
                "illusion": "Remote Procedure Calls (RPCs)",
                "crumb": "Network latency; silent timeouts; IPv6 scope ID resolution failures",
                "awakening": "Async execution; explicit network-layer fallbacks",
            },
            {
                "illusion": "Dynamic Duck Typing",
                "crumb": "Runtime TypeErrors; fragile refactoring",
                "awakening": "Static type hinting; metaclass validation at class creation",
            },
        ],
        "keywords": [
            "metaclass", "reflection", "introspection", "metaprogramming",
            "leaky abstraction", "orm", "n+1", "memory", "quine",
            "type.__new__", "inspect", "getattr", "duck typing", "abstraction",
            "runtime error", "garbage collection", "reference counting",
        ],
    },
    {
        "id": "second",
        "number": 2,
        "title": "State Management, Responsibility & the End of Innocence",
        "doctrine": "Once you see the spell in the structure, you cannot unknow the magic.",
        "metaphor": "The End of Innocence",
        "python_concepts": [
            "State Design Pattern — object delegates behaviour to active state",
            "Chain of Responsibility — decoupled handler pipeline",
            "Explicit context managers (__enter__ / __exit__)",
            "Middleware chains (Django, FastAPI, ASGI)",
        ],
        "design_patterns": [
            {
                "pattern": "State",
                "type": "behavioural",
                "purpose": "Object alters behaviour when internal state changes — appears to change class",
                "python_impl": "Abstract State base + concrete state classes (Draft → Moderation → Published)",
                "doctrine_link": "Every restriction, permission, or capability is self-authored",
            },
            {
                "pattern": "Chain of Responsibility",
                "type": "behavioural",
                "purpose": "Decouples sender from receiver; multiple handlers get opportunity to process",
                "python_impl": "Sequential handler chain (auth → validation → rate-limit → business logic)",
                "doctrine_link": "Shared structural responsibility — each node owns its domain",
            },
        ],
        "keywords": [
            "state pattern", "chain of responsibility", "middleware",
            "context manager", "state machine", "explicit state",
            "responsibility", "handler", "pipeline", "decoupled",
            "innocence", "magic", "implicit", "monolith", "coupling",
        ],
    },
    {
        "id": "third",
        "number": 3,
        "title": "Observability, Telemetry & the Social Architecture of Witnessing",
        "doctrine": "Bear witness anyway. Document the architecture anyway. Leave crumbs anyway.",
        "metaphor": "The Act of Witnessing",
        "python_concepts": [
            "Observer Design Pattern — one-to-many notification",
            "Distributed Tracing (OpenTelemetry, Jaeger)",
            "Structured Logging (structlog, python-json-logger)",
            "Self-documenting APIs (OpenAPI / Swagger / GraphQL introspection)",
            "Immutable audit trails",
        ],
        "civic_hacking": {
            "principle": "Others are also architects who forgot",
            "examples": [
                "Code for Kansas City — civic tech for municipal reform",
                "KC Tech Council — professional advocacy & ethical review",
                "Papers We Love — re-examining theoretical CS foundations",
                "GenCyber camps — workforce development & security education",
                "AI ethics meetups — witnessing algorithmic impact on lives",
            ],
        },
        "keywords": [
            "observer", "telemetry", "tracing", "logging", "observability",
            "opentelemetry", "jaeger", "prometheus", "audit", "witness",
            "documentation", "openapi", "swagger", "structured logging",
            "civic", "community", "open source", "crumbs", "record",
        ],
    },
    {
        "id": "fourth",
        "number": 4,
        "title": "The Trojan Horse: Decorators & the Smuggling of Intent",
        "doctrine": "Whatever you build is both genuine offering and hidden payload. Will you know what you're smuggling?",
        "metaphor": "The Dual Payload",
        "python_concepts": [
            "Decorators (@) — wrap functions to inject cross-cutting concerns",
            "functools.wraps — preserving identity after wrapping",
            "Supply chain security (PyPI typo-squatting, LLM hallucinated packages)",
            "SBOM — Software Bill of Materials tracking",
            "Reflections on Trusting Trust — compiler-level trojans",
        ],
        "decorator_anatomy": {
            "visible_offering": "Route an HTTP request (@app.route), validate input (@validate)",
            "hidden_payload": "Silent auth enforcement, execution timing, cache mutation, state injection",
            "unconscious_use": "Haphazard decorators creating untraceable bottlenecks & hidden dependencies",
            "conscious_use": "Deliberate separation of concerns; cross-cutting payloads consistently applied",
        },
        "supply_chain_risks": [
            {
                "attack": "Trojan module in import path",
                "description": "Malicious os.py placed where host application imports with elevated privileges",
                "mitigation": "Strict virtual environments; isolated Docker execution; path sanitisation",
            },
            {
                "attack": "LLM-hallucinated packages",
                "description": "AI tools recommend spoofed or non-existent packages delivering malware",
                "mitigation": "Automated dependency auditing; SBOM tracking; hash verification",
            },
            {
                "attack": "Typo-squatting on PyPI",
                "description": "Packages with near-identical names smuggle data exfiltration scripts",
                "mitigation": "pip-audit, Safety scanner, CycloneDX SBOM generation, private registry mirrors",
            },
        ],
        "keywords": [
            "decorator", "trojan", "supply chain", "sbom", "pypi",
            "dependency", "wraps", "functools", "hidden", "payload",
            "smuggling", "security", "audit", "malware", "typosquat",
            "ken thompson", "trusting trust", "separation of concerns",
        ],
    },
    {
        "id": "fifth",
        "number": 5,
        "title": "Value Sensitive Design (VSD): The Commandment",
        "doctrine": "There is no neutral architecture. Every choice is a spell. Every structure trains its users in how to be.",
        "metaphor": "The Commandment",
        "python_concepts": [
            "SHAP / LIME for ML explainability",
            "Fairness-aware ML (AIF360, Fairlearn)",
            "IEEE 7000 Ethically Aligned Design",
            "MESIAS ethical risk assessment platform",
            "UrbanSim — VSD-driven urban simulation",
        ],
        "vsd_tripartite": {
            "conceptual": "Identify direct & indirect stakeholders; define values at stake (privacy, autonomy, welfare, fairness)",
            "empirical": "Observe how users actually interact with the system; identify automation–expectation tension",
            "technical": "Analyse how architecture, data structures & algorithms support or hinder identified values",
        },
        "vsd_values": [
            {
                "value": "Transparency & Explainability",
                "python_impl": "ML explainability (SHAP, LIME); structured logging; OpenAPI specs",
                "teaching": "Trains users to comprehend algorithmic logic; agency to inspect & challenge",
            },
            {
                "value": "Privacy & Security",
                "python_impl": "Data anonymisation pipelines; SHA-256 + salting; decentralised storage",
                "teaching": "Trains users to expect data sovereignty; prevents surveillance architecture",
            },
            {
                "value": "Human Autonomy",
                "python_impl": "Explicit opt-in telemetry; State patterns requiring manual confirmation; override interfaces",
                "teaching": "Cultivates independence; prevents unappealable algorithmic decisions",
            },
            {
                "value": "Flexibility & Agility",
                "python_impl": "Modular components; microservices; Dependency Injection; standard SQL outputs",
                "teaching": "Allows evolution with changing values; prevents vendor/architectural lock-in",
            },
        ],
        "keywords": [
            "vsd", "value sensitive design", "ethics", "fairness", "bias",
            "explainability", "shap", "lime", "transparency", "privacy",
            "autonomy", "ieee 7000", "mesias", "urbansim", "stakeholder",
            "neutral", "algorithmic", "accountability", "responsible ai",
        ],
    },
    {
        "id": "sixth",
        "number": 6,
        "title": "Paradox, Technical Debt & the Architecture of Contradiction",
        "doctrine": "You will create cages while believing you're building doors. This is not failure. This is the condition.",
        "metaphor": "The Acceptance of Contradiction",
        "python_concepts": [
            "Flexibility ↔ Complexity paradox",
            "Technical debt as human condition, not moral failure",
            "Hype-Driven Development — ego-driven over-engineering",
            "Glyph recursive symbolic interface — modelling consciousness breakdown",
            "Resilience over perfection — modular design for graceful obsolescence",
        ],
        "paradoxes": [
            {
                "name": "Flexibility breeds Complexity",
                "description": "Modular, abstract, extensible design drastically increases cognitive overhead",
                "python_example": "Dynamic typing + metaclasses = immense flexibility → fragile runtime, complex debugging",
            },
            {
                "name": "Abstraction creates Dependency",
                "description": "Systems meant to free developers eventually bind them to the abstraction itself",
                "python_example": "Heavy ORM usage trades upfront ease for long-term architectural complexity",
            },
            {
                "name": "Ego Smuggling",
                "description": "Developers introduce unnecessary complexity for resume-building, not problem-solving",
                "python_example": "Microservices for 10-user apps; custom ORMs because of SQL insecurity",
            },
        ],
        "resolution": "The conscious architect does not strive for utopia. They strive for resilience — modular design, explicit state, documented interfaces — so the current cage can be dismantled and rebuilt with minimal systemic suffering.",
        "keywords": [
            "paradox", "technical debt", "complexity", "flexibility",
            "over-engineering", "hype", "ego", "contradiction", "resilience",
            "glyph", "recursive", "consciousness", "obsolescence",
            "debt acceptance", "modular", "graceful degradation",
        ],
    },
]


# =====================================================================
# §2 — The Remember · Build · Witness Triad
# =====================================================================

TRIAD: Dict[str, Dict[str, Any]] = {
    "remember": {
        "title": "Remember",
        "doctrine": "Use the introspective capabilities of the runtime to ensure code remains aware of its own structure and origins.",
        "practices": [
            "Apply Python reflection (inspect, type, dir, getattr, ast.parse) to maintain structural self-awareness",
            "Acknowledge every abstraction is inherently leaky — leaks are diagnostic markers, not bugs",
            "Implement metaclass validation to enforce conventions at class creation time",
            "Write quine-like self-documenting components that expose their own configuration",
        ],
        "anti_patterns": [
            "Treating MemoryError / TypeError as 'random bugs' rather than abstraction signals",
            "Building thicker walls of abstraction instead of acknowledging boundaries",
            "Ignoring runtime reflection capabilities in favour of static-only analysis",
        ],
    },
    "build": {
        "title": "Build",
        "doctrine": "Wield the spells of software architecture with deep ethical awareness. Abandon the myth of technological neutrality.",
        "practices": [
            "Apply Value Sensitive Design from project inception — conceptual + empirical + technical investigations",
            "Use decorators with transparency — know exactly what cross-cutting concerns you're smuggling",
            "Deploy State and Chain of Responsibility patterns to make context & flow explicit",
            "Integrate ML explainability (SHAP/LIME) for every model touching human decisions",
            "Audit dependencies with SBOM tracking, pip-audit, Safety scanner",
        ],
        "anti_patterns": [
            "Deploying black-box ML models without explainability",
            "Applying decorators haphazardly without understanding hidden side-effects",
            "Building dependency trees of hundreds of unvetted packages",
            "Treating architecture as 'neutral' when every choice trains user behaviour",
        ],
    },
    "witness": {
        "title": "Witness",
        "doctrine": "Maintain the historical and operational record. Technically through telemetry; socially through community engagement.",
        "practices": [
            "Implement Observer pattern for non-intrusive, persistent state monitoring",
            "Deploy OpenTelemetry / Jaeger for distributed tracing across services",
            "Generate OpenAPI / Swagger self-documenting API specifications",
            "Maintain immutable audit trails of state transformations",
            "Engage with civic tech, ethical review boards, and open-source communities",
        ],
        "anti_patterns": [
            "Silent failures with no logging or alerting",
            "Opaque APIs with no schema documentation",
            "Isolated development with no community code review",
            "Destroying historical operational records (log rotation without archiving)",
        ],
    },
}


# =====================================================================
# §3 — Leaky Abstraction Detector
# =====================================================================

_LEAK_SIGNALS: Dict[str, Dict[str, Any]] = {
    "orm_leak": {
        "patterns": ["n+1", "orm", "sqlalchemy", "django orm", "query performance",
                      "raw sql", "database slow", "lazy load", "eager load"],
        "recognition": "first",
        "illusion": "Object-Relational Mapper",
        "description": "ORM abstraction leaking — N+1 queries, silent join failures, or performance degradation forcing raw SQL drop-down",
        "severity": 0.7,
    },
    "memory_leak": {
        "patterns": ["memoryerror", "memory leak", "garbage collection", "gc.collect",
                      "reference cycle", "heap", "out of memory", "oom"],
        "recognition": "first",
        "illusion": "Automatic Memory Management",
        "description": "GC abstraction leaking — heap exhaustion, reference cycles, or quadratic collection forcing manual memory profiling",
        "severity": 0.8,
    },
    "network_leak": {
        "patterns": ["timeout", "latency", "rpc", "grpc", "network", "packet loss",
                      "connection refused", "dns", "ipv6", "socket"],
        "recognition": "first",
        "illusion": "Remote Procedure Calls as Local Functions",
        "description": "Network abstraction leaking — latency, timeouts, or DNS failures breaking the illusion of local execution",
        "severity": 0.6,
    },
    "type_leak": {
        "patterns": ["typeerror", "duck typing", "type hint", "mypy", "type check",
                      "runtime type", "attribute error", "isinstance"],
        "recognition": "first",
        "illusion": "Dynamic Duck Typing",
        "description": "Type abstraction leaking — runtime TypeErrors or fragile refactoring revealing the absence of static safety",
        "severity": 0.5,
    },
    "state_leak": {
        "patterns": ["global state", "singleton", "race condition", "thread safe",
                      "mutex", "deadlock", "concurrent", "shared state"],
        "recognition": "second",
        "illusion": "Implicit Global State",
        "description": "State management leaking — concurrency bugs, race conditions, or deadlocks exposing hidden shared mutable state",
        "severity": 0.8,
    },
    "framework_leak": {
        "patterns": ["magic", "autoconfig", "convention over", "implicit",
                      "auto-discovery", "hidden import", "monkey patch"],
        "recognition": "second",
        "illusion": "Framework Magic / Convention over Configuration",
        "description": "Framework abstraction leaking — auto-discovery, monkey-patching, or implicit imports creating untraceable behaviour",
        "severity": 0.6,
    },
    "decorator_leak": {
        "patterns": ["decorator", "wrapper", "functools.wraps", "side effect",
                      "cross-cutting", "aop", "aspect"],
        "recognition": "fourth",
        "illusion": "Transparent Function Wrapping",
        "description": "Decorator abstraction leaking — hidden side-effects, performance bottlenecks, or lost function identity from stacked wrappers",
        "severity": 0.5,
    },
    "supply_chain_leak": {
        "patterns": ["dependency", "supply chain", "sbom", "pip audit", "pypi",
                      "malware", "typosquat", "hallucinated package", "cve"],
        "recognition": "fourth",
        "illusion": "Trusted Package Ecosystem",
        "description": "Supply chain abstraction leaking — unvetted dependencies, hallucinated packages, or typosquatted malware in the dependency tree",
        "severity": 0.9,
    },
}


def detect_leaky_abstractions(query: str) -> Dict[str, Any]:
    """Scan a query for signals of leaky abstractions.

    Returns dict with detected leaks, total severity, and
    which Recognitions are active.
    """
    q = query.lower()
    detected: List[Dict[str, Any]] = []
    active_recognitions: set = set()

    for leak_id, info in _LEAK_SIGNALS.items():
        hits = [p for p in info["patterns"] if p in q]
        if hits:
            detected.append({
                "leak_id": leak_id,
                "illusion": info["illusion"],
                "description": info["description"],
                "severity": info["severity"],
                "recognition": info["recognition"],
                "matched_signals": hits,
            })
            active_recognitions.add(info["recognition"])

    total_severity = min(1.0, sum(d["severity"] for d in detected))
    return {
        "leaks_detected": detected,
        "total_severity": round(total_severity, 2),
        "active_recognitions": sorted(active_recognitions),
        "count": len(detected),
    }


# =====================================================================
# §4 — Conscious Pattern Advisor
# =====================================================================

CONSCIOUS_PATTERNS: List[Dict[str, Any]] = [
    {
        "pattern": "State",
        "type": "behavioural",
        "recognition": "second",
        "conscious_intent": "Transform implicit boolean-flag state management into explicit, auditable state transitions",
        "components": ["Abstract State base class", "Concrete state classes", "Context class delegating to active state"],
        "when_to_use": [
            "Object behaviour changes dramatically by mode/phase/status",
            "Business rules differ per lifecycle stage (Draft → Review → Published)",
            "Current code uses sprawling if/elif/else chains to check mode flags",
        ],
        "keywords": ["state", "lifecycle", "phase", "mode", "transition", "status", "draft", "published"],
    },
    {
        "pattern": "Chain of Responsibility",
        "type": "behavioural",
        "recognition": "second",
        "conscious_intent": "Distribute processing responsibility across a decoupled handler pipeline",
        "components": ["Abstract Handler interface", "Concrete handlers with next-reference", "Client feeding payload into chain"],
        "when_to_use": [
            "Request must pass through auth → validation → rate-limit → business logic",
            "Multiple handlers may independently modify or reject a payload",
            "Middleware architecture for web frameworks (Django, FastAPI)",
        ],
        "keywords": ["chain", "handler", "middleware", "pipeline", "auth", "validation", "rate limit"],
    },
    {
        "pattern": "Observer",
        "type": "behavioural",
        "recognition": "third",
        "conscious_intent": "Non-intrusive, persistent witnessing of state changes across the system",
        "components": ["Subject (Observable)", "Observer interface", "Concrete observers (Logger, Alerter, MetricsCollector)"],
        "when_to_use": [
            "Multiple subsystems need to react to state changes in a core object",
            "Audit trail / telemetry must record state transformations without coupling",
            "Event-driven architecture with pub/sub semantics",
        ],
        "keywords": ["observer", "event", "pub/sub", "notify", "subscribe", "telemetry", "audit"],
    },
    {
        "pattern": "Decorator (Structural)",
        "type": "structural",
        "recognition": "fourth",
        "conscious_intent": "Deliberately smuggle cross-cutting concerns while preserving function identity",
        "components": ["Wrapper function / class", "functools.wraps for identity preservation", "Clear docstring of what is being injected"],
        "when_to_use": [
            "Cross-cutting concerns (auth, logging, caching, timing) applied uniformly",
            "Separation of concerns without polluting business logic",
            "Building composable function pipelines with @ syntax",
        ],
        "keywords": ["decorator", "@", "wrapper", "cross-cutting", "auth", "cache", "logging", "timing"],
    },
    {
        "pattern": "Strategy",
        "type": "behavioural",
        "recognition": "sixth",
        "conscious_intent": "Replace rigid conditional logic with interchangeable algorithmic families",
        "components": ["Strategy interface", "Concrete strategy classes", "Context selecting strategy at runtime"],
        "when_to_use": [
            "Multiple algorithms solve the same problem differently (sorting, pricing, routing)",
            "Client should select algorithm at runtime without conditional branching",
            "Need to add new algorithms without modifying existing code (Open/Closed Principle)",
        ],
        "keywords": ["strategy", "algorithm", "interchangeable", "policy", "runtime selection"],
    },
    {
        "pattern": "Dependency Injection",
        "type": "structural",
        "recognition": "fifth",
        "conscious_intent": "Eliminate hidden coupling; make all dependencies explicit and auditable",
        "components": ["Interface/Protocol definitions", "Constructor injection", "DI container (optional)"],
        "when_to_use": [
            "Classes instantiate their own dependencies internally (tight coupling)",
            "Need testability — must mock external services",
            "VSD flexibility value — system must evolve without lock-in",
        ],
        "keywords": ["injection", "dependency", "coupling", "testability", "mock", "interface", "protocol"],
    },
]


def recommend_patterns(query: str) -> Dict[str, Any]:
    """Recommend conscious design patterns for a query.

    Returns matched patterns with their doctrine links and when-to-use.
    """
    q = query.lower()
    matched: List[Dict[str, Any]] = []

    for pat in CONSCIOUS_PATTERNS:
        hits = [k for k in pat["keywords"] if k in q]
        if hits:
            matched.append({
                "pattern": pat["pattern"],
                "type": pat["type"],
                "recognition": pat["recognition"],
                "conscious_intent": pat["conscious_intent"],
                "components": pat["components"],
                "when_to_use": pat["when_to_use"],
                "signal_count": len(hits),
                "matched_keywords": hits,
            })

    matched.sort(key=lambda m: m["signal_count"], reverse=True)
    return {"patterns": matched, "count": len(matched)}


# =====================================================================
# §5 — Value Sensitive Design (VSD) Evaluator
# =====================================================================

_VSD_DIMENSIONS: List[Dict[str, Any]] = [
    {
        "value": "transparency",
        "weight": 0.25,
        "positive_signals": [
            "explainability", "shap", "lime", "openapi", "swagger",
            "documentation", "logging", "audit trail", "open source",
            "interpretable", "feature importance",
        ],
        "negative_signals": [
            "black box", "proprietary", "opaque", "no docs",
            "undocumented", "closed source", "hidden",
        ],
        "description": "System comprehensibility — can stakeholders inspect and challenge algorithmic decisions?",
    },
    {
        "value": "privacy",
        "weight": 0.25,
        "positive_signals": [
            "anonymisation", "anonymization", "encryption", "hashing",
            "gdpr", "data sovereignty", "opt-in", "consent",
            "differential privacy", "federated", "decentralised",
        ],
        "negative_signals": [
            "tracking", "surveillance", "no consent", "data broker",
            "third party sharing", "telemetry default on", "cookies",
        ],
        "description": "Data sovereignty — does the architecture protect user data and respect consent boundaries?",
    },
    {
        "value": "autonomy",
        "weight": 0.25,
        "positive_signals": [
            "human in the loop", "hitl", "override", "opt-in",
            "manual confirmation", "user control", "configurable",
            "adjustable", "freedom", "exit",
        ],
        "negative_signals": [
            "automatic", "forced", "mandatory", "no override",
            "locked in", "vendor lock", "captive", "dependency",
        ],
        "description": "Human agency — can users override, exit, or modify algorithmic recommendations?",
    },
    {
        "value": "flexibility",
        "weight": 0.25,
        "positive_signals": [
            "modular", "microservice", "dependency injection", "plugin",
            "extensible", "decoupled", "sql output", "standard format",
            "open standard", "interoperable", "api first",
        ],
        "negative_signals": [
            "monolith", "tight coupling", "proprietary format",
            "vendor lock", "hardcoded", "rigid", "legacy",
        ],
        "description": "Evolutionary capacity — can the system adapt to changing human values without structural lock-in?",
    },
]


def score_vsd(query: str) -> Dict[str, Any]:
    """Score a query/description against VSD value dimensions.

    Returns per-dimension scores, composite VSD alignment,
    grade, and actionable recommendations.
    """
    q = query.lower()
    dimension_scores: List[Dict[str, Any]] = []
    weighted_sum = 0.0

    for dim in _VSD_DIMENSIONS:
        pos_hits = [s for s in dim["positive_signals"] if s in q]
        neg_hits = [s for s in dim["negative_signals"] if s in q]

        raw = (len(pos_hits) - len(neg_hits)) / max(1, len(dim["positive_signals"]))
        score = max(0.0, min(1.0, 0.5 + raw))

        dimension_scores.append({
            "value": dim["value"],
            "score": round(score, 2),
            "weight": dim["weight"],
            "positive_matches": pos_hits,
            "negative_matches": neg_hits,
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
            recommendations.append(
                f"Improve {ds['value']}: {ds['description']}"
            )
        if ds["negative_matches"]:
            recommendations.append(
                f"Address {ds['value']} concerns: detected signals [{', '.join(ds['negative_matches'])}]"
            )

    return {
        "vsd_score": composite,
        "grade": grade,
        "dimensions": dimension_scores,
        "recommendations": recommendations,
        "tripartite_method": _VSD_DIMENSIONS[0] is not None,  # always True; structure marker
    }


# =====================================================================
# §6 — Supply Chain Risk Evaluator
# =====================================================================

_SUPPLY_CHAIN_SIGNALS: Dict[str, float] = {
    # Positive (risk reducers, negative weight = less risk)
    "pip audit": -0.15, "safety": -0.10, "sbom": -0.15,
    "cyclonedx": -0.10, "hash verification": -0.10,
    "private registry": -0.10, "docker": -0.08,
    "virtual environment": -0.08, "pinned dependencies": -0.10,
    "lockfile": -0.08, "reproducible": -0.05,
    # Negative (risk amplifiers, positive weight)
    "unvetted": 0.15, "hundreds of dependencies": 0.20,
    "no audit": 0.15, "pypi": 0.05, "hallucinated": 0.20,
    "ai generated": 0.10, "typosquat": 0.20,
    "trust": 0.05, "malware": 0.25,
    "supply chain attack": 0.25, "no lockfile": 0.15,
}


def assess_supply_chain(query: str) -> Dict[str, Any]:
    """Assess supply chain risk from query signals.

    Returns risk score (0–1), grade, and Ken Thompson warning.
    """
    q = query.lower()
    risk = 0.5  # baseline — unknown is moderate risk
    matched: List[Dict[str, Any]] = []

    for signal, weight in _SUPPLY_CHAIN_SIGNALS.items():
        if signal in q:
            risk += weight
            matched.append({"signal": signal, "weight": round(weight, 2)})

    risk = max(0.0, min(1.0, round(risk, 2)))
    grade = (
        "A" if risk <= 0.20 else
        "B" if risk <= 0.35 else
        "C" if risk <= 0.50 else
        "D" if risk <= 0.70 else "F"
    )

    return {
        "risk_score": risk,
        "grade": grade,
        "matched_signals": matched,
        "ken_thompson_warning": (
            "Reflections on Trusting Trust (1984): vulnerabilities can hide "
            "deep within the very tools used to build the system. "
            "Verify your compiler, your package manager, and your AI assistant."
        ),
        "mitigations": [
            "Run pip-audit and Safety scanner on every CI build",
            "Generate CycloneDX SBOM for all production deployments",
            "Pin all dependency versions with hash verification",
            "Mirror critical packages in a private registry",
            "Isolate untrusted code in Docker / gVisor / Firecracker",
            "Verify AI-recommended packages exist on PyPI before installing",
        ],
    }


# =====================================================================
# §7 — Technical Debt Acceptance Scorer
# =====================================================================

_DEBT_ACCEPTANCE_SIGNALS = {
    # signals of conscious debt acceptance (positive)
    "accepted": [
        "documented debt", "tech debt ticket", "adr", "architecture decision",
        "known limitation", "trade-off", "pragmatic", "good enough",
        "iterative", "mvp", "timeboxed", "spike", "prototype", "refactor plan",
    ],
    # signals of unconscious debt accumulation (negative)
    "unconscious": [
        "quick fix", "hack", "todo", "fixme", "workaround", "temporary",
        "magic number", "copy paste", "no tests", "untested", "legacy",
        "spaghetti", "god class", "mega function", "over-engineer",
        "resume driven", "hype driven", "bleeding edge",
    ],
}


def score_debt_consciousness(query: str) -> Dict[str, Any]:
    """Score whether technical debt signals are conscious (accepted,
    documented) or unconscious (ignored, ego-driven).

    Returns consciousness ratio + doctrine wisdom.
    """
    q = query.lower()
    accepted = [s for s in _DEBT_ACCEPTANCE_SIGNALS["accepted"] if s in q]
    unconscious = [s for s in _DEBT_ACCEPTANCE_SIGNALS["unconscious"] if s in q]

    total = len(accepted) + len(unconscious)
    consciousness = len(accepted) / max(1, total)

    grade = (
        "A" if consciousness >= 0.80 else
        "B" if consciousness >= 0.60 else
        "C" if consciousness >= 0.40 else
        "D" if consciousness >= 0.20 else "F"
    )

    return {
        "consciousness_ratio": round(consciousness, 2),
        "grade": grade,
        "accepted_debt_signals": accepted,
        "unconscious_debt_signals": unconscious,
        "total_signals": total,
        "doctrine": RECOGNITIONS[5]["doctrine"],  # sixth recognition
        "resolution": RECOGNITIONS[5]["resolution"],
        "wisdom": (
            "Technical debt is the digital imprint of a flawed human "
            "operating within constraints of time, budget, and evolving "
            "understanding. The conscious architect does not strive for "
            "utopia — they strive for resilience."
        ),
    }


# =====================================================================
# §8 — MESIAS Ethical Risk Index (Simplified)
# =====================================================================

_MESIAS_DIMENSIONS: List[Dict[str, Any]] = [
    {
        "dimension": "Fairness & Non-Discrimination",
        "weight": 0.20,
        "signals": ["fairness", "bias", "discrimination", "aif360", "fairlearn",
                     "demographic parity", "equal opportunity", "disparate impact"],
        "mitigations": ["calibrated equalized odds", "reweighing", "adversarial debiasing"],
    },
    {
        "dimension": "Transparency & Explainability",
        "weight": 0.20,
        "signals": ["shap", "lime", "explainability", "interpretable", "feature importance",
                     "waterfall plot", "surrogate model", "glass box"],
        "mitigations": ["SHAP feature attribution", "LIME local surrogate", "global model-agnostic explanations"],
    },
    {
        "dimension": "Privacy & Data Governance",
        "weight": 0.20,
        "signals": ["gdpr", "ccpa", "anonymisation", "differential privacy", "consent",
                     "data minimisation", "right to erasure", "purpose limitation"],
        "mitigations": ["k-anonymity", "l-diversity", "differential privacy noise injection"],
    },
    {
        "dimension": "Robustness & Safety",
        "weight": 0.15,
        "signals": ["adversarial", "robustness", "fault tolerance", "graceful degradation",
                     "fuzzing", "boundary testing", "safety critical"],
        "mitigations": ["adversarial training", "input validation", "output guardrails", "fallback mechanisms"],
    },
    {
        "dimension": "Accountability & Auditability",
        "weight": 0.15,
        "signals": ["audit", "accountability", "traceability", "logging", "immutable record",
                     "chain of custody", "model registry", "experiment tracking"],
        "mitigations": ["MLflow experiment tracking", "model versioning", "decision audit logs"],
    },
    {
        "dimension": "Human Oversight & Control",
        "weight": 0.10,
        "signals": ["human in the loop", "hitl", "override", "manual review",
                     "escalation", "kill switch", "graceful shutdown"],
        "mitigations": ["mandatory human review for high-stakes decisions", "confidence thresholds with escalation"],
    },
]


def compute_mesias_risk(query: str) -> Dict[str, Any]:
    """Compute a simplified MESIAS-style ethical risk index.

    Maps query signals to 6 ethical dimensions (aligned with
    OECD / EU ALTAI framework) and returns composite risk score.
    """
    q = query.lower()
    dimension_results: List[Dict[str, Any]] = []
    weighted_coverage = 0.0

    for dim in _MESIAS_DIMENSIONS:
        hits = [s for s in dim["signals"] if s in q]
        coverage = min(1.0, len(hits) / max(1, len(dim["signals"]) * 0.4))

        dimension_results.append({
            "dimension": dim["dimension"],
            "coverage": round(coverage, 2),
            "weight": dim["weight"],
            "matched_signals": hits,
            "gap": round(1.0 - coverage, 2),
            "mitigations": dim["mitigations"] if coverage < 0.5 else [],
        })
        weighted_coverage += coverage * dim["weight"]

    # Risk is the inverse of coverage
    risk_score = round(1.0 - weighted_coverage, 2)
    grade = (
        "A" if risk_score <= 0.20 else
        "B" if risk_score <= 0.35 else
        "C" if risk_score <= 0.50 else
        "D" if risk_score <= 0.70 else "F"
    )

    return {
        "ethical_risk_score": risk_score,
        "grade": grade,
        "dimensions": dimension_results,
        "framework": "MESIAS (aligned with OECD AI Principles & EU ALTAI)",
        "doctrine": "Every algorithm is a spell. The MESIAS mirror forces you to see the ethical reflection of what you build.",
    }


# =====================================================================
# §9 — Master Assessment: Architecture of Awakening
# =====================================================================

@dataclass
class AwakeningAssessment:
    """Unified assessment from the Architecture of Awakening."""
    query: str
    consciousness_score: float  # 0–1 composite
    grade: str
    active_recognitions: List[str]
    leaky_abstractions: Dict[str, Any]
    conscious_patterns: Dict[str, Any]
    vsd_alignment: Dict[str, Any]
    supply_chain_risk: Dict[str, Any]
    debt_consciousness: Dict[str, Any]
    mesias_risk: Dict[str, Any]
    triad_assessment: Dict[str, Any]
    warnings: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _score_triad(query: str) -> Dict[str, Any]:
    """Score the Remember · Build · Witness triad engagement."""
    q = query.lower()
    scores = {}
    for key, pillar in TRIAD.items():
        practice_hits = sum(
            1 for p in pillar["practices"]
            if any(w in q for w in p.lower().split() if len(w) > 4)
        )
        anti_hits = sum(
            1 for a in pillar["anti_patterns"]
            if any(w in q for w in a.lower().split() if len(w) > 4)
        )
        raw = (practice_hits - anti_hits * 0.5) / max(1, len(pillar["practices"]))
        scores[key] = {
            "score": round(max(0.0, min(1.0, 0.5 + raw)), 2),
            "practice_signals": practice_hits,
            "anti_pattern_signals": anti_hits,
            "doctrine": pillar["doctrine"],
        }
    composite = sum(s["score"] for s in scores.values()) / 3
    return {"pillars": scores, "composite": round(composite, 2)}


def assess_awakening(query: str) -> Dict[str, Any]:
    """Master assessment: run all Architecture of Awakening subsystems.

    Returns a unified AwakeningAssessment combining:
    - Leaky abstraction detection
    - Conscious pattern recommendations
    - VSD alignment scoring
    - Supply chain risk
    - Technical debt consciousness
    - MESIAS ethical risk index
    - Remember · Build · Witness triad
    """
    leaks = detect_leaky_abstractions(query)
    patterns = recommend_patterns(query)
    vsd = score_vsd(query)
    supply = assess_supply_chain(query)
    debt = score_debt_consciousness(query)
    mesias = compute_mesias_risk(query)
    triad = _score_triad(query)

    # Active recognitions from leaks + patterns
    active_recs = set(leaks.get("active_recognitions", []))
    for p in patterns.get("patterns", []):
        active_recs.add(p.get("recognition", ""))
    active_recs.discard("")

    # Composite consciousness score (weighted)
    consciousness = round(
        vsd["vsd_score"] * 0.25
        + (1.0 - supply["risk_score"]) * 0.15
        + debt["consciousness_ratio"] * 0.20
        + (1.0 - mesias["ethical_risk_score"]) * 0.20
        + triad["composite"] * 0.20,
        2,
    )

    grade = (
        "A" if consciousness >= 0.80 else
        "B" if consciousness >= 0.65 else
        "C" if consciousness >= 0.50 else
        "D" if consciousness >= 0.35 else "F"
    )

    # Aggregate warnings
    warnings: List[str] = []
    if leaks["total_severity"] > 0.5:
        warnings.append(
            f"High abstraction leakage detected (severity {leaks['total_severity']}) — "
            f"the architecture is showing its seams"
        )
    if supply["risk_score"] > 0.5:
        warnings.append(
            f"Elevated supply chain risk ({supply['grade']}) — "
            f"unvetted dependencies detected"
        )
    if debt["consciousness_ratio"] < 0.3:
        warnings.append(
            f"Technical debt appears unconscious (ratio {debt['consciousness_ratio']}) — "
            f"ego may be smuggling alongside wisdom"
        )
    if mesias["ethical_risk_score"] > 0.5:
        warnings.append(
            f"MESIAS ethical risk elevated ({mesias['grade']}) — "
            f"VSD investigations recommended before deployment"
        )
    if vsd["vsd_score"] < 0.4:
        warnings.append(
            f"Low VSD alignment ({vsd['grade']}) — "
            f"architecture may be training users toward dependency"
        )

    # Aggregate recommendations
    recommendations = list(vsd.get("recommendations", []))
    for dim in mesias.get("dimensions", []):
        for m in dim.get("mitigations", []):
            if m not in recommendations:
                recommendations.append(m)
    if supply["risk_score"] > 0.3:
        recommendations.extend(supply.get("mitigations", [])[:3])

    assessment = AwakeningAssessment(
        query=query,
        consciousness_score=consciousness,
        grade=grade,
        active_recognitions=sorted(active_recs),
        leaky_abstractions=leaks,
        conscious_patterns=patterns,
        vsd_alignment=vsd,
        supply_chain_risk=supply,
        debt_consciousness=debt,
        mesias_risk=mesias,
        triad_assessment=triad,
        warnings=warnings,
        recommendations=recommendations[:15],
    )

    log.info(
        "awakening assessment: consciousness=%.2f (%s), %d leaks, %d patterns, %d warnings",
        consciousness, grade, leaks["count"], patterns["count"], len(warnings),
    )

    return assessment.to_dict()


# =====================================================================
# §10 — Public API Helpers
# =====================================================================

def get_recognitions() -> List[Dict[str, Any]]:
    """Return the six recognitions catalogue."""
    return RECOGNITIONS


def get_recognition(recognition_id: str) -> Optional[Dict[str, Any]]:
    """Return a single recognition by id (first, second, ... sixth)."""
    for r in RECOGNITIONS:
        if r["id"] == recognition_id:
            return r
    return None


def get_triad() -> Dict[str, Any]:
    """Return the Remember · Build · Witness triad."""
    return TRIAD


def get_vsd_framework() -> Dict[str, Any]:
    """Return VSD dimensions and their architectural implementations."""
    return {
        "framework": "Value Sensitive Design (Batya Friedman, 1990s)",
        "methodology": "Tripartite: Conceptual + Empirical + Technical investigations",
        "standard": "IEEE 7000 Ethically Aligned Design",
        "dimensions": _VSD_DIMENSIONS,
    }


def get_leaky_abstraction_catalogue() -> Dict[str, Any]:
    """Return the complete leaky abstraction signal catalogue."""
    return {
        "law": "Joel Spolsky's Law of Leaky Abstractions (2002)",
        "doctrine": RECOGNITIONS[0]["doctrine"],
        "signals": _LEAK_SIGNALS,
    }


def get_supply_chain_guidance() -> Dict[str, Any]:
    """Return supply chain security guidance."""
    return {
        "doctrine": RECOGNITIONS[3]["doctrine"],
        "risks": RECOGNITIONS[3]["supply_chain_risks"],
        "decorator_anatomy": RECOGNITIONS[3]["decorator_anatomy"],
        "signals": _SUPPLY_CHAIN_SIGNALS,
    }


def get_paradoxes() -> Dict[str, Any]:
    """Return the architectural paradoxes and their resolutions."""
    return {
        "doctrine": RECOGNITIONS[5]["doctrine"],
        "paradoxes": RECOGNITIONS[5]["paradoxes"],
        "resolution": RECOGNITIONS[5]["resolution"],
    }


def get_conscious_patterns() -> List[Dict[str, Any]]:
    """Return the conscious design pattern catalogue."""
    return CONSCIOUS_PATTERNS
