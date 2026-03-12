"""
praxis.enlightenment
~~~~~~~~~~~~~~~~~~~~
v14 — Architectural Enlightenment: Mapping Universal Metaphysical Truths
to Python System Design.

Encodes **five metaphysical truths** and the **six-stage path to
architectural awakening**, translating philosophical constructs into
concrete Pythonic design principles, scoring subsystems, and tool
recommendations.

Five Truths
-----------
I.   The Illusion of Separation  → Identity Map, Data Mesh, Unit of Work
II.  Love as Alignment           → Exception handling, self-healing, resilience
III. Mind as Projector            → MVC, Clean/Hexagonal Architecture
IV.  Ego as Enemy                → Data silos, DDD, Repository Pattern
V.   Everything is Connected     → Observer pattern, EDA, reactive systems

Six Stages
----------
1. Truth           → Domain Modeling (Value Objects, Entities)
2. Presence        → AsyncIO, Event Loop
3. Compassion      → Service Layer, Dependency Injection
4. Stillness       → Object Introspection, Reflection, gc
5. Suffering→Wisdom → Disaster Recovery, HA, self-healing
6. Remembrance     → State Design Pattern, FSM

Public API
----------
- assess_enlightenment(query)   → master assessment
- score_unity(query)            → Truth I scoring
- score_alignment(query)        → Truth II scoring
- score_projection(query)       → Truth III scoring
- score_ego_dissolution(query)  → Truth IV scoring
- score_interconnection(query)  → Truth V scoring
- score_domain_truth(query)     → Stage 1 scoring
- score_presence(query)         → Stage 2 scoring
- score_compassion(query)       → Stage 3 scoring
- score_stillness(query)        → Stage 4 scoring
- score_suffering_wisdom(query) → Stage 5 scoring
- score_remembrance(query)      → Stage 6 scoring
- get_truths()                  → all five truths
- get_truth(truth_id)           → one truth by id
- get_stages()                  → all six stages
- get_stage(stage_id)           → one stage by id
- get_identity_map()            → Identity Map pattern detail
- get_observer_pattern()        → Observer pattern detail
- get_hexagonal_arch()          → Hexagonal Architecture detail
- get_state_pattern()           → State Design Pattern detail
- get_clean_arch_layers()       → Clean Architecture layers

Dependencies: stdlib only (logging, re, dataclasses, typing).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# ======================================================================
# 1. FIVE METAPHYSICAL TRUTHS
# ======================================================================

TRUTHS: List[Dict[str, Any]] = [
    {
        "id": "separation",
        "number": "I",
        "title": "The Illusion of Separation",
        "doctrine": (
            "Separation is a fundamental illusion. Individual existence is a "
            "wave inextricably part of a larger ocean; the misunderstanding of "
            "separation is the primary catalyst for suffering."
        ),
        "python_patterns": [
            "Identity Map — one DB row ↔ one Python object per session",
            "Unit of Work — track dirty objects, flush once atomically",
            "Data Mesh — domain-owned data products with global governance",
            "Referential Integrity — enforce FK constraints at the ORM level",
            "SQLAlchemy Session — the canonical implementation of non-separation",
        ],
        "antipatterns": [
            "Multiple in-memory copies of the same DB row",
            "Centralized monolithic data lakes that fragment under scale",
            "Cache stampede from duplicated entity lookups",
            "Manual synchronisation of parallel object graphs",
        ],
        "keywords": [
            "identity map", "unit of work", "sqlalchemy", "session",
            "data mesh", "referential integrity", "single source of truth",
            "duplicate", "cache", "synchronisation", "ORM",
        ],
    },
    {
        "id": "alignment",
        "number": "II",
        "title": "Love as Alignment, Fear as the Illusion",
        "doctrine": (
            "Fear is a fundamental lie that shrinks the self and breeds the "
            "ego. Love—oneness, alignment, acceptance—is the ultimate, "
            "expansive reality. Suffering arises from believing the lie of fear."
        ),
        "python_patterns": [
            "Strategic try/except — intercept failure gracefully, not defensively",
            "Custom exception hierarchies — domain-specific error taxonomy",
            "Exponential backoff with tenacity/backoff — self-healing retries",
            "Pydantic validation — accept and transform, not gatekeep",
            "Structured logging — transform suffering into telemetry wisdom",
        ],
        "antipatterns": [
            "Excessive if/else defensive validation (fear-based)",
            "Bare except: pass — silent error suppression",
            "Crash-on-first-error scripts with no recovery",
            "Over-engineered gating that rejects valid edge cases",
        ],
        "keywords": [
            "exception", "try", "except", "retry", "backoff", "tenacity",
            "self-healing", "resilience", "validation", "pydantic",
            "structured logging", "recovery", "graceful degradation",
        ],
    },
    {
        "id": "projection",
        "number": "III",
        "title": "The Mind as a Projector, Not a Camera",
        "doctrine": (
            "The mind generates reality rather than merely recording it. "
            "Consciousness actively shapes perception. In software, the core "
            "data model (truth) must be strictly separated from the variable "
            "mechanisms that project it to users (perception)."
        ),
        "python_patterns": [
            "MVC — Model (truth), View (projection), Controller (mediator)",
            "Hexagonal Architecture — Ports (abstract) + Adapters (concrete)",
            "Clean Architecture — Dependency Rule: deps point inward to truth",
            "Dependency Inversion — core never knows about frameworks",
            "Protocols / abc — abstract ports for adapter swappability",
        ],
        "antipatterns": [
            "Business logic embedded in View templates",
            "Model aware of specific framework rendering",
            "Tight coupling between domain and HTTP/SQL layers",
            "Direct database queries in controller actions",
        ],
        "keywords": [
            "mvc", "clean architecture", "hexagonal", "ports and adapters",
            "dependency inversion", "dependency rule", "protocol",
            "abc", "adapter", "view", "model", "controller", "projection",
        ],
    },
    {
        "id": "ego",
        "number": "IV",
        "title": "The Ego as the Ultimate Enemy",
        "doctrine": (
            "The ego is a story built to survive fears—it thrives on "
            "separation, comparison, hierarchy, and conflict. Its architectural "
            "equivalent is the monolithic data silo. Letting go of the ego "
            "leads to systemic liberation."
        ),
        "python_patterns": [
            "Domain-Driven Design — bounded contexts over monolithic coupling",
            "Repository Pattern — abstraction over storage details",
            "Data Interoperability — semantic meaning consistent across envs",
            "Dependency Inversion — high-level and low-level depend on abstractions",
            "Anti-Corruption Layer — protect domains from foreign ego contamination",
        ],
        "antipatterns": [
            "Monolithic data silos hoarding information",
            "Big Ball of Mud — entangled dependencies everywhere",
            "Department-owned databases with no external access",
            "Hierarchical architectures that enforce one-way control",
        ],
        "keywords": [
            "ddd", "domain driven design", "bounded context", "repository",
            "interoperability", "data silo", "anti-corruption layer",
            "monolith", "coupling", "big ball of mud", "liberation",
        ],
    },
    {
        "id": "connection",
        "number": "V",
        "title": "Everything is Connected",
        "doctrine": (
            "Every action and emotion ripples through an interconnected whole. "
            "When state changes in one corner of an application, the entire "
            "system must organically respond—without rigid, hard-coded command "
            "structures forcing downstream actions."
        ),
        "python_patterns": [
            "Observer Pattern — subject.notify() ripples to all observers",
            "Event-Driven Architecture — emit events to message bus, not direct calls",
            "RxPY / reaktiv — reactive streams with declarative composition",
            "Temporal decoupling — async handlers listening to event bus",
            "Eventual consistency — harmonize organically over time",
        ],
        "antipatterns": [
            "Sequential microservice calls creating temporal coupling",
            "Hard-coded observer registrations",
            "Synchronous request-response chains across services",
            "Polling instead of event subscription",
        ],
        "keywords": [
            "observer", "event driven", "reactive", "rxpy", "message bus",
            "kafka", "rabbitmq", "pub sub", "eventual consistency",
            "temporal decoupling", "notify", "subscribe", "signal",
        ],
    },
]


# ======================================================================
# 2. SIX-STAGE PATH TO ARCHITECTURAL AWAKENING
# ======================================================================

STAGES: List[Dict[str, Any]] = [
    {
        "id": "truth",
        "number": 1,
        "title": "Truth: Seeing Reality as It Is via Domain Modeling",
        "practice": (
            "Awakening begins with rigorous Domain Modeling. Before writing "
            "schemas or APIs, define the truth using pure Python: distinguish "
            "Value Objects (immutable, defined by attributes) from Entities "
            "(long-lived identities whose attributes evolve)."
        ),
        "python_implementation": [
            "Value Objects via frozen dataclasses / attrs",
            "Entities with explicit id fields and lifecycle methods",
            "Ubiquitous Language in 'Business Speak' first, code second",
            "Domain events capturing state transitions",
        ],
        "keywords": [
            "domain model", "value object", "entity", "aggregate",
            "ubiquitous language", "business speak", "dataclass", "attrs",
        ],
    },
    {
        "id": "presence",
        "number": 2,
        "title": "Presence: Living in the Moment with AsyncIO",
        "practice": (
            "Living in the present moment rather than blocking the flow of "
            "existence. Python's asyncio module provides single-threaded "
            "concurrent code using coroutines, event loops, and non-blocking "
            "I/O—the Event Loop remains entirely present."
        ),
        "python_implementation": [
            "asyncio event loop as the orchestrator of presence",
            "await keyword to yield control back to the loop gracefully",
            "anyio for portable async—agnostic of asyncio vs trio",
            "uvloop for production-grade event loop performance",
        ],
        "keywords": [
            "asyncio", "async", "await", "coroutine", "event loop",
            "non-blocking", "uvloop", "anyio", "concurrent", "presence",
        ],
    },
    {
        "id": "compassion",
        "number": 3,
        "title": "Compassion and Service: Recognizing Interconnectedness",
        "practice": (
            "Recognizing interconnectedness leads to compassion. The Service "
            "Layer encapsulates use cases; Dependency Injection ensures "
            "components operate in mutual service, not subjugation."
        ),
        "python_implementation": [
            "Service Layer pattern bounding application use cases",
            "Dependency Injection via constructor injection or DI containers",
            "dependency-injector / injector for automated wiring",
            "Protocol-based contracts between producer and consumer",
        ],
        "keywords": [
            "service layer", "dependency injection", "di", "injector",
            "constructor injection", "protocol", "testability", "compassion",
        ],
    },
    {
        "id": "stillness",
        "number": 4,
        "title": "Stillness and Self-Knowledge: Object Introspection",
        "practice": (
            "Removing noise, illusions, and ego through introspection. Python "
            "embraces this natively: everything is an object with dir(), "
            "type(), hasattr(), getattr(). The gc module silently severs "
            "references to unneeded objects."
        ),
        "python_implementation": [
            "dir() / type() / hasattr() / getattr() for runtime self-knowledge",
            "inspect module for deep frame and source analysis",
            "gc module for automated memory stillness",
            "Zen of Python— 'Errors should never pass silently'",
        ],
        "keywords": [
            "introspection", "reflection", "dir", "type", "hasattr",
            "getattr", "inspect", "gc", "garbage collection", "stillness",
        ],
    },
    {
        "id": "suffering_wisdom",
        "number": 5,
        "title": "Transforming Suffering into Wisdom: Resilient Infrastructure",
        "practice": (
            "Suffering is not an endpoint but a catalyst for growth. Resilient "
            "systems minimise RTO and RPO via HA failover, geo-replication, "
            "and self-repair. Chaos engineering validates through controlled "
            "suffering."
        ),
        "python_implementation": [
            "Disaster Recovery with RTO/RPO tracking",
            "HA failover clusters and data replication",
            "Chaos Toolkit for controlled fault injection",
            "Circuit breakers (pybreaker) for graceful degradation",
        ],
        "keywords": [
            "disaster recovery", "rto", "rpo", "high availability", "ha",
            "failover", "replication", "chaos engineering", "chaos toolkit",
            "circuit breaker", "self-healing", "resilience",
        ],
    },
    {
        "id": "remembrance",
        "number": 6,
        "title": "Remembering What You Are: The State Design Pattern",
        "practice": (
            "The final stage: not becoming something new, but remembering the "
            "ancient self. The State Design Pattern and FSMs ensure an object "
            "always explicitly remembers the rules governing its current "
            "reality."
        ),
        "python_implementation": [
            "python-statemachine for declarative FSM definitions",
            "transitions library for lightweight state machines",
            "State objects delegated via Context.transition_to()",
            "Guards/Validators as Guardians of Truth preventing hallucinated transitions",
            "on_enter / on_exit callbacks as controlled ripple effects",
        ],
        "keywords": [
            "state machine", "fsm", "state pattern", "transition",
            "guard", "context", "statemachine", "finite state",
            "on_enter", "on_exit", "remembrance",
        ],
    },
]


# ======================================================================
# 3. ARCHITECTURAL PATTERN REFERENCE CATALOGUES
# ======================================================================

IDENTITY_MAP: Dict[str, Any] = {
    "pattern": "Identity Map",
    "truth": "I — The Illusion of Separation",
    "principle": (
        "Each database row corresponds to at most one Python object within a "
        "given session. Operating under unity is vastly more efficient than "
        "operating under the illusion of separation."
    ),
    "implementation": {
        "framework": "SQLAlchemy",
        "mechanism": "Session.identity_map — keyed by (mapper, primary_key)",
        "benefits": [
            "Eliminates redundant remote calls",
            "Guarantees data correctness within a transaction",
            "Single point of truth per business entity",
        ],
    },
    "proverb": "A man with two watches never knows what time it is.",
}

OBSERVER_PATTERN: Dict[str, Any] = {
    "pattern": "Observer (Pub/Sub)",
    "truth": "V — Everything is Connected",
    "principle": (
        "A one-to-many subscription mechanism where changes in a single "
        "Subject automatically notify all dependent Observers. The cosmic "
        "ripple propagates naturally without the Subject knowing observer identities."
    ),
    "implementation": {
        "python_skeleton": (
            "class Subject:\n"
            "    def __init__(self):\n"
            "        self._observers = []\n"
            "    def attach(self, observer):\n"
            "        self._observers.append(observer)\n"
            "    def notify(self, data):\n"
            "        for observer in self._observers:\n"
            "            observer.update(data)"
        ),
        "libraries": ["blinker (signals)", "RxPY (reactive streams)", "reaktiv (declarative state)"],
        "scaling": "Event-Driven Architecture (EDA) with message buses (Kafka, RabbitMQ)",
    },
}

HEXAGONAL_ARCH: Dict[str, Any] = {
    "pattern": "Hexagonal Architecture (Ports and Adapters)",
    "truth": "III — Mind as Projector",
    "principle": (
        "Application core interacts with the outside world purely through "
        "abstract Ports (Protocol / abc); outer layers provide concrete "
        "Adapters. Swapping PostgreSQL for MongoDB becomes trivial."
    ),
    "layers": [
        {
            "layer": "Entities / Domain Model",
            "philosophical_equivalent": "The Ultimate Truth",
            "role": "Immutable dataclasses/value objects encoding business rules",
        },
        {
            "layer": "Use Cases / Application Core",
            "philosophical_equivalent": "The Will / Intent",
            "role": "Service classes orchestrating data flow, isolated from UI/DB",
        },
        {
            "layer": "Interface Adapters",
            "philosophical_equivalent": "The Projector (Mind)",
            "role": "MVC components converting internal data to external formats",
        },
        {
            "layer": "Frameworks and Drivers",
            "philosophical_equivalent": "The External Illusion",
            "role": "Volatile details (Django, FastAPI, PostgreSQL) kept at arm's length",
        },
    ],
    "dependency_rule": "Source code dependencies must point strictly inward toward the core Truth.",
}

STATE_PATTERN: Dict[str, Any] = {
    "pattern": "State Design Pattern / Finite State Machine",
    "truth": "Stage 6 — Remembering What You Are",
    "principle": (
        "An object must always explicitly remember the rules governing its "
        "current reality. Instead of monstrous nested if/elif, the Context "
        "delegates to a distinct State object."
    ),
    "components": [
        {"component": "States", "philosophical_role": "The Present Reality",
         "function": "Defined points of existence — machine always knows current state"},
        {"component": "Transitions", "philosophical_role": "The Path of Evolution",
         "function": "Strictly defined paths dictating how entity evolves via events"},
        {"component": "Guards / Validators", "philosophical_role": "Guardians of Truth",
         "function": "Conditional logic preventing hallucinated transitions"},
        {"component": "Actions / Handlers", "philosophical_role": "The Ripple Effect",
         "function": "Callbacks on enter/exit enabling controlled side-effects"},
    ],
    "libraries": ["python-statemachine", "transitions"],
}

CLEAN_ARCH_LAYERS: List[Dict[str, str]] = HEXAGONAL_ARCH["layers"]


# ======================================================================
# 4. TRUTH I — UNITY SCORING
# ======================================================================

_UNITY_SIGNALS = {
    "identity_map":       {"weight": 0.20, "patterns": [
        r"\bidentity.?map\b", r"\bunit.?of.?work\b", r"\bsession\b",
        r"\bsqlalchemy\b", r"\borm\b", r"\bactive.?record\b",
    ]},
    "data_mesh":          {"weight": 0.20, "patterns": [
        r"\bdata.?mesh\b", r"\bdomain.?owned\b", r"\bdata.?product\b",
        r"\bdecentrali[sz]ed.?data\b", r"\bself.?serve\b",
    ]},
    "referential":        {"weight": 0.20, "patterns": [
        r"\breferential.?integrity\b", r"\bforeign.?key\b", r"\bfk\b",
        r"\bconstraint\b", r"\bcascade\b",
    ]},
    "single_truth":       {"weight": 0.20, "patterns": [
        r"\bsingle.?source.?of.?truth\b", r"\bssot\b",
        r"\bcanonical\b", r"\bgolden.?record\b",
    ]},
    "anti_duplication":   {"weight": 0.20, "patterns": [
        r"\bdedup\b", r"\bde.?duplicat\b", r"\bidempoten\b",
        r"\bcache.?stampede\b", r"\bcache.?aside\b",
    ]},
}


def score_unity(query: str) -> Dict[str, Any]:
    """Truth I — score how well the query addresses the Illusion of Separation."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _UNITY_SIGNALS.items():
        match = any(re.search(p, q) for p in cfg["patterns"])
        if match:
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    grade = _grade(total)
    return {"truth": "I", "score": round(total, 3), "grade": grade,
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 5. TRUTH II — ALIGNMENT SCORING
# ======================================================================

_ALIGNMENT_SIGNALS = {
    "exception_handling":  {"weight": 0.20, "patterns": [
        r"\btry\b.*\bexcept\b", r"\bexception.?hierarch\b",
        r"\bcustom.?exception\b", r"\bdomain.?error\b",
    ]},
    "self_healing":        {"weight": 0.25, "patterns": [
        r"\bself.?heal\b", r"\bexponential.?backoff\b", r"\btenacity\b",
        r"\bretry\b", r"\bcircuit.?breaker\b", r"\bbackoff\b",
    ]},
    "graceful_degrade":    {"weight": 0.20, "patterns": [
        r"\bgraceful.?degrad\b", r"\bfallback\b", r"\bfail.?safe\b",
        r"\bfault.?toleran\b",
    ]},
    "structured_logging":  {"weight": 0.15, "patterns": [
        r"\bstructured.?log\b", r"\bstructlog\b", r"\btelemetry\b",
        r"\bobservabilit\b", r"\bearly.?warning\b",
    ]},
    "validation_flow":     {"weight": 0.20, "patterns": [
        r"\bpydantic\b", r"\bvalidat\b", r"\bschema\b",
        r"\binput.?saniti[sz]\b", r"\bcontract\b",
    ]},
}


def score_alignment(query: str) -> Dict[str, Any]:
    """Truth II — score Love/Alignment-driven resilience vs fear-based fragility."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _ALIGNMENT_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"truth": "II", "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 6. TRUTH III — PROJECTION PURITY SCORING
# ======================================================================

_PROJECTION_SIGNALS = {
    "mvc":                {"weight": 0.20, "patterns": [
        r"\bmvc\b", r"\bmodel.?view.?controller\b",
        r"\btemplate\b.*\bview\b", r"\bdjango\b.*\bview\b",
    ]},
    "clean_arch":         {"weight": 0.25, "patterns": [
        r"\bclean.?architect\b", r"\bhexagonal\b",
        r"\bports?.?and.?adapters?\b", r"\bonion.?architect\b",
    ]},
    "dependency_rule":    {"weight": 0.25, "patterns": [
        r"\bdependency.?rule\b", r"\bdependency.?inversion\b",
        r"\bsolid\b", r"\bprotocol\b.*\babc\b", r"\babstract.?base\b",
    ]},
    "adapter_swap":       {"weight": 0.15, "patterns": [
        r"\badapter\b", r"\bport\b", r"\bswap\b.*\bdb\b",
        r"\bpostgresql?\b.*\bmongo\b", r"\brest\b.*\bgraphql\b",
    ]},
    "layer_isolation":    {"weight": 0.15, "patterns": [
        r"\blayer.?isolat\b", r"\bframework.?agnostic\b",
        r"\bcore.?logic\b.*\bisola\b", r"\binner.?ring\b",
    ]},
}


def score_projection(query: str) -> Dict[str, Any]:
    """Truth III — score Mind-as-Projector separation purity."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _PROJECTION_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"truth": "III", "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 7. TRUTH IV — EGO DISSOLUTION SCORING
# ======================================================================

_EGO_SIGNALS = {
    "ddd":               {"weight": 0.25, "patterns": [
        r"\bddd\b", r"\bdomain.?driven\b", r"\bbounded.?context\b",
        r"\baggregate\b", r"\bubiquitous.?language\b",
    ]},
    "repository":        {"weight": 0.20, "patterns": [
        r"\brepository.?pattern\b", r"\babstract.?storage\b",
        r"\bdata.?access.?layer\b", r"\bpersist\b.*\babstract\b",
    ]},
    "interoperability":  {"weight": 0.20, "patterns": [
        r"\binteroperab\b", r"\bapi.?contract\b", r"\bschema.?registr\b",
        r"\bsemantic.?meaning\b", r"\bshared.?vocabulary\b",
    ]},
    "silo_breaking":     {"weight": 0.20, "patterns": [
        r"\bsilo\b", r"\bdata.?liberation\b", r"\bcross.?domain\b",
        r"\bbreak.?down.?wall\b", r"\bintegrat\b",
    ]},
    "anti_corruption":   {"weight": 0.15, "patterns": [
        r"\banti.?corruption\b", r"\bacl\b",
        r"\btranslation.?layer\b", r"\badapter\b.*\bdomain\b",
    ]},
}


def score_ego_dissolution(query: str) -> Dict[str, Any]:
    """Truth IV — score Ego dissolution via DDD, interoperability, silo-breaking."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _EGO_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"truth": "IV", "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 8. TRUTH V — INTERCONNECTION SCORING
# ======================================================================

_CONNECTION_SIGNALS = {
    "observer":          {"weight": 0.20, "patterns": [
        r"\bobserver\b", r"\bpub.?sub\b", r"\bsubscri\b",
        r"\bnotif\b", r"\bsignal\b", r"\bblinker\b",
    ]},
    "eda":               {"weight": 0.25, "patterns": [
        r"\bevent.?driven\b", r"\beda\b", r"\bmessage.?bus\b",
        r"\bevent.?sourc\b", r"\bcqrs\b",
    ]},
    "reactive":          {"weight": 0.20, "patterns": [
        r"\breactiv\b", r"\brxpy\b", r"\breaktiv\b",
        r"\bstream\b", r"\boperator\b.*\bpipe\b",
    ]},
    "message_infra":     {"weight": 0.20, "patterns": [
        r"\bkafka\b", r"\brabbitmq\b", r"\bredis.?stream\b",
        r"\bcelery\b", r"\bnats\b", r"\bmqtt\b",
    ]},
    "eventual_consist":  {"weight": 0.15, "patterns": [
        r"\beventual.?consisten\b", r"\btemporal.?decoupl\b",
        r"\basync.?handler\b", r"\bsaga\b",
    ]},
}


def score_interconnection(query: str) -> Dict[str, Any]:
    """Truth V — score Everything-is-Connected via Observer/EDA/reactive patterns."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _CONNECTION_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"truth": "V", "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 9. STAGE 1 — DOMAIN TRUTH SCORING
# ======================================================================

_DOMAIN_SIGNALS = {
    "value_objects":     {"weight": 0.25, "patterns": [
        r"\bvalue.?object\b", r"\bfrozen\b.*\bdataclass\b",
        r"\bimmutable\b", r"\battrs\b.*\bfrozen\b",
    ]},
    "entities":          {"weight": 0.25, "patterns": [
        r"\bentit\b", r"\bidentit\b.*\blong.?lived\b",
        r"\baggregate.?root\b", r"\blifecycle\b",
    ]},
    "ubiquitous_lang":   {"weight": 0.25, "patterns": [
        r"\bubiquitous.?lang\b", r"\bbusiness.?speak\b",
        r"\bdomain.?model\b", r"\bdomain.?event\b",
    ]},
    "pure_python":       {"weight": 0.25, "patterns": [
        r"\bdataclass\b", r"\battrs\b", r"\bnamed.?tuple\b",
        r"\btyped.?dict\b", r"\b(pydantic.?)?base.?model\b",
    ]},
}


def score_domain_truth(query: str) -> Dict[str, Any]:
    """Stage 1 — score Domain Modeling quality."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _DOMAIN_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 1, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 10. STAGE 2 — PRESENCE SCORING
# ======================================================================

_PRESENCE_SIGNALS = {
    "asyncio":           {"weight": 0.30, "patterns": [
        r"\basyncio\b", r"\basync\b", r"\bawait\b",
        r"\bcoroutine\b", r"\bevent.?loop\b",
    ]},
    "non_blocking":      {"weight": 0.25, "patterns": [
        r"\bnon.?block\b", r"\bconcurren\b", r"\bio.?bound\b",
        r"\bparallel\b", r"\btask\b.*\bgather\b",
    ]},
    "fast_loop":         {"weight": 0.20, "patterns": [
        r"\buvloop\b", r"\banyio\b", r"\btrio\b",
        r"\bhypercorn\b", r"\buvicorn\b",
    ]},
    "anti_blocking":     {"weight": 0.25, "patterns": [
        r"\bnot?.?block\b", r"\byield.?control\b",
        r"\bcooperative\b", r"\bsingle.?thread\b.*\bconcur\b",
    ]},
}


def score_presence(query: str) -> Dict[str, Any]:
    """Stage 2 — score AsyncIO / presence-oriented design."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _PRESENCE_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 2, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 11. STAGE 3 — COMPASSION SCORING
# ======================================================================

_COMPASSION_SIGNALS = {
    "service_layer":     {"weight": 0.30, "patterns": [
        r"\bservice.?layer\b", r"\buse.?case\b", r"\bapplication.?service\b",
        r"\borchestrat\b",
    ]},
    "dependency_inj":    {"weight": 0.35, "patterns": [
        r"\bdependency.?inject\b", r"\bdi\b.*\bcontainer\b",
        r"\bconstructor.?inject\b", r"\bdependency.?injector\b",
        r"\binjector\b",
    ]},
    "testability":       {"weight": 0.20, "patterns": [
        r"\btestab\b", r"\bmock\b", r"\bfake\b.*\brepository\b",
        r"\bstub\b", r"\bparallel.?develop\b",
    ]},
    "contract_based":    {"weight": 0.15, "patterns": [
        r"\bprotocol\b", r"\binterface\b", r"\babstract\b",
        r"\bcontract\b",
    ]},
}


def score_compassion(query: str) -> Dict[str, Any]:
    """Stage 3 — score Service Layer + Dependency Injection maturity."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _COMPASSION_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 3, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 12. STAGE 4 — STILLNESS SCORING
# ======================================================================

_STILLNESS_SIGNALS = {
    "introspection":     {"weight": 0.30, "patterns": [
        r"\bdir\(\)", r"\btype\(\)", r"\bhasattr\b", r"\bgetattr\b",
        r"\bintrospect\b", r"\breflect\b",
    ]},
    "inspect_module":    {"weight": 0.25, "patterns": [
        r"\binspect\b", r"\bframe\b", r"\bsource\b.*\banalys\b",
        r"\bast\b.*\bparse\b",
    ]},
    "gc_management":     {"weight": 0.25, "patterns": [
        r"\bgc\b", r"\bgarbage.?collect\b", r"\bweak.?ref\b",
        r"\bmemory.?manag\b", r"\bcyclic.?ref\b",
    ]},
    "zen_alignment":     {"weight": 0.20, "patterns": [
        r"\bzen.?of.?python\b", r"\bexplicit\b.*\bimplicit\b",
        r"\bsimple\b.*\bcomplex\b", r"\berror\b.*\bsilent\b",
    ]},
}


def score_stillness(query: str) -> Dict[str, Any]:
    """Stage 4 — score introspection and self-knowledge maturity."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _STILLNESS_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 4, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 13. STAGE 5 — SUFFERING→WISDOM SCORING
# ======================================================================

_SUFFERING_SIGNALS = {
    "disaster_recovery": {"weight": 0.25, "patterns": [
        r"\bdisaster.?recover\b", r"\brto\b", r"\brpo\b",
        r"\bfailover\b", r"\bbackup\b",
    ]},
    "high_availability": {"weight": 0.25, "patterns": [
        r"\bhigh.?availab\b", r"\bha\b.*\bcluster\b",
        r"\breplicat\b", r"\bgeo.?redundan\b",
    ]},
    "chaos_engineering": {"weight": 0.25, "patterns": [
        r"\bchaos\b", r"\bfault.?inject\b", r"\bgameday\b",
        r"\bchaos.?toolkit\b", r"\bchaos.?monkey\b",
    ]},
    "self_repair":       {"weight": 0.25, "patterns": [
        r"\bself.?repair\b", r"\bself.?heal\b", r"\bauto.?recover\b",
        r"\bintrusion.?recover\b", r"\btemporal.?consist\b",
    ]},
}


def score_suffering_wisdom(query: str) -> Dict[str, Any]:
    """Stage 5 — score Disaster Recovery and resilient infrastructure maturity."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _SUFFERING_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 5, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 14. STAGE 6 — REMEMBRANCE SCORING
# ======================================================================

_REMEMBRANCE_SIGNALS = {
    "state_pattern":     {"weight": 0.30, "patterns": [
        r"\bstate.?pattern\b", r"\bstate.?machine\b", r"\bfsm\b",
        r"\bfinite.?state\b", r"\bstatemachine\b",
    ]},
    "transitions":       {"weight": 0.25, "patterns": [
        r"\btransition\b", r"\bon_enter\b", r"\bon_exit\b",
        r"\bguard\b", r"\bvalidat\b.*\btransition\b",
    ]},
    "declarative_fsm":   {"weight": 0.25, "patterns": [
        r"\bpython.?statemachine\b", r"\btransitions\b.*\blib\b",
        r"\bdeclarative\b.*\bstate\b",
    ]},
    "context_pattern":   {"weight": 0.20, "patterns": [
        r"\bcontext\b.*\bstate\b", r"\btransition_to\b",
        r"\bdelegate\b.*\bstate\b", r"\bbehavior\b.*\bchange\b",
    ]},
}


def score_remembrance(query: str) -> Dict[str, Any]:
    """Stage 6 — score State Design Pattern / FSM maturity."""
    q = query.lower()
    total = 0.0
    hits: Dict[str, float] = {}
    for dim, cfg in _REMEMBRANCE_SIGNALS.items():
        if any(re.search(p, q) for p in cfg["patterns"]):
            hits[dim] = cfg["weight"]
            total += cfg["weight"]
    total = min(total, 1.0)
    return {"stage": 6, "score": round(total, 3), "grade": _grade(total),
            "dimensions": hits, "max": 1.0}


# ======================================================================
# 15. MASTER ASSESSMENT
# ======================================================================

@dataclass
class EnlightenmentAssessment:
    """Unified assessment container for architectural enlightenment."""
    enlightenment_score: float = 0.0
    grade: str = "F"
    # Five truths
    unity: Dict[str, Any] = field(default_factory=dict)
    alignment: Dict[str, Any] = field(default_factory=dict)
    projection: Dict[str, Any] = field(default_factory=dict)
    ego_dissolution: Dict[str, Any] = field(default_factory=dict)
    interconnection: Dict[str, Any] = field(default_factory=dict)
    # Six stages
    domain_truth: Dict[str, Any] = field(default_factory=dict)
    presence: Dict[str, Any] = field(default_factory=dict)
    compassion: Dict[str, Any] = field(default_factory=dict)
    stillness: Dict[str, Any] = field(default_factory=dict)
    suffering_wisdom: Dict[str, Any] = field(default_factory=dict)
    remembrance: Dict[str, Any] = field(default_factory=dict)
    # Meta
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Truth weights (sum = 0.50)
_TRUTH_WEIGHTS = {
    "unity":           0.10,
    "alignment":       0.10,
    "projection":      0.10,
    "ego_dissolution": 0.10,
    "interconnection": 0.10,
}

# Stage weights (sum = 0.50)
_STAGE_WEIGHTS = {
    "domain_truth":      0.10,
    "presence":          0.08,
    "compassion":        0.08,
    "stillness":         0.08,
    "suffering_wisdom":  0.08,
    "remembrance":       0.08,
}


def assess_enlightenment(query: str) -> Dict[str, Any]:
    """
    Master enlightenment assessment combining all 5 truths + 6 stages.

    Returns a dict with composite score, per-truth and per-stage breakdowns,
    warnings, and grade.
    """
    # Evaluate all truths
    unity       = score_unity(query)
    alignment   = score_alignment(query)
    projection  = score_projection(query)
    ego         = score_ego_dissolution(query)
    connection  = score_interconnection(query)

    # Evaluate all stages
    domain      = score_domain_truth(query)
    pres        = score_presence(query)
    comp        = score_compassion(query)
    still       = score_stillness(query)
    suffer      = score_suffering_wisdom(query)
    remem       = score_remembrance(query)

    # Weighted composite
    composite = (
        unity["score"]      * _TRUTH_WEIGHTS["unity"]
        + alignment["score"]  * _TRUTH_WEIGHTS["alignment"]
        + projection["score"] * _TRUTH_WEIGHTS["projection"]
        + ego["score"]        * _TRUTH_WEIGHTS["ego_dissolution"]
        + connection["score"] * _TRUTH_WEIGHTS["interconnection"]
        + domain["score"]     * _STAGE_WEIGHTS["domain_truth"]
        + pres["score"]       * _STAGE_WEIGHTS["presence"]
        + comp["score"]       * _STAGE_WEIGHTS["compassion"]
        + still["score"]      * _STAGE_WEIGHTS["stillness"]
        + suffer["score"]     * _STAGE_WEIGHTS["suffering_wisdom"]
        + remem["score"]      * _STAGE_WEIGHTS["remembrance"]
    )

    # Normalise to [0, 1]
    weight_sum = sum(_TRUTH_WEIGHTS.values()) + sum(_STAGE_WEIGHTS.values())
    normalised = composite / weight_sum if weight_sum > 0 else 0.0
    normalised = round(min(normalised, 1.0), 3)
    grade = _grade(normalised)

    # Generate warnings
    warnings: List[str] = []
    truth_scores = {
        "Unity (I)": unity["score"],
        "Alignment (II)": alignment["score"],
        "Projection (III)": projection["score"],
        "Ego Dissolution (IV)": ego["score"],
        "Interconnection (V)": connection["score"],
    }
    stage_scores = {
        "Domain Truth (1)": domain["score"],
        "Presence (2)": pres["score"],
        "Compassion (3)": comp["score"],
        "Stillness (4)": still["score"],
        "Suffering→Wisdom (5)": suffer["score"],
        "Remembrance (6)": remem["score"],
    }
    for name, sc in {**truth_scores, **stage_scores}.items():
        if sc == 0:
            warnings.append(f"{name}: no signals detected — blindspot")

    # Synthesis warnings
    if unity["score"] > 0.5 and connection["score"] < 0.2:
        warnings.append(
            "Strong Unity but weak Interconnection — consider adding "
            "Observer/EDA patterns to propagate state changes"
        )
    if alignment["score"] < 0.3 and suffer["score"] > 0.5:
        warnings.append(
            "Resilient infrastructure detected but weak exception handling — "
            "micro-level self-healing may be missing"
        )
    if projection["score"] > 0.5 and ego["score"] < 0.2:
        warnings.append(
            "Good architectural layering but data silos may persist — "
            "apply DDD bounded contexts for full ego dissolution"
        )

    assessment = EnlightenmentAssessment(
        enlightenment_score=normalised,
        grade=grade,
        unity=unity,
        alignment=alignment,
        projection=projection,
        ego_dissolution=ego,
        interconnection=connection,
        domain_truth=domain,
        presence=pres,
        compassion=comp,
        stillness=still,
        suffering_wisdom=suffer,
        remembrance=remem,
        warnings=warnings,
    )

    result = assessment.to_dict()

    log.info(
        "enlightenment assessment: score=%.2f (%s), "
        "unity=%s, alignment=%s, projection=%s, ego=%s, connection=%s, "
        "%d warnings",
        normalised, grade,
        unity["grade"], alignment["grade"], projection["grade"],
        ego["grade"], connection["grade"],
        len(warnings),
    )

    return result


# ======================================================================
# 16. PUBLIC HELPERS
# ======================================================================

def get_truths() -> List[Dict[str, Any]]:
    """Return all five metaphysical truths."""
    return TRUTHS


def get_truth(truth_id: str) -> Optional[Dict[str, Any]]:
    """Return a single truth by id."""
    for t in TRUTHS:
        if t["id"] == truth_id:
            return t
    return None


def get_stages() -> List[Dict[str, Any]]:
    """Return all six stages of architectural awakening."""
    return STAGES


def get_stage(stage_id: str) -> Optional[Dict[str, Any]]:
    """Return a single stage by id."""
    for s in STAGES:
        if s["id"] == stage_id:
            return s
    return None


def get_identity_map() -> Dict[str, Any]:
    """Return the Identity Map pattern detail."""
    return IDENTITY_MAP


def get_observer_pattern() -> Dict[str, Any]:
    """Return the Observer pattern detail."""
    return OBSERVER_PATTERN


def get_hexagonal_arch() -> Dict[str, Any]:
    """Return the Hexagonal Architecture detail."""
    return HEXAGONAL_ARCH


def get_state_pattern() -> Dict[str, Any]:
    """Return the State Design Pattern detail."""
    return STATE_PATTERN


def get_clean_arch_layers() -> List[Dict[str, str]]:
    """Return Clean Architecture layers with philosophical equivalents."""
    return CLEAN_ARCH_LAYERS


# ======================================================================
# 17. GRADING UTILITY
# ======================================================================

def _grade(score: float) -> str:
    """Convert a 0-1 score to a letter grade."""
    if score >= 0.90:
        return "A+"
    if score >= 0.80:
        return "A"
    if score >= 0.70:
        return "B"
    if score >= 0.60:
        return "C"
    if score >= 0.45:
        return "D"
    return "F"


log.info(
    "enlightenment.py loaded — %d truths, %d stages, %d patterns",
    len(TRUTHS), len(STAGES),
    sum(1 for _ in [IDENTITY_MAP, OBSERVER_PATTERN, HEXAGONAL_ARCH, STATE_PATTERN]),
)
