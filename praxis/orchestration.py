"""
Praxis Orchestration — Event-Driven Architecture Intelligence  (v9)

Provides deep knowledge about layered tech-stack architectures,
event-driven multi-agent patterns, process isolation paradigms,
state persistence strategies, and performance constraints.

The module acts as a *meta-recommendation engine*: when a user
query involves building an AI system (not just *using* an AI tool),
Praxis can recommend the specific infrastructure, frameworks, and
architectural patterns required for production-grade deployment.

Public API
──────────
    detect_architecture_needs   → analyse query for infra requirements
    recommend_stack             → layered tech-stack recommendation
    recommend_patterns          → event-driven / isolation patterns
    get_stack_layers            → full catalogue of stack layers
    get_patterns                → full catalogue of architecture patterns
    get_performance_constraints → hardware / memory constraint analysis
    classify_engineering_query  → architect-first vs vibe-coding detection
    score_architecture          → holistic architecture maturity score
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA CLASSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class StackLayer:
    """One functional layer in a modular AI tech stack."""
    role: str                       # e.g. "Content Management & API"
    function: str                   # what it does
    recommended: List[str]          # e.g. ["Strapi + GraphQL"]
    alternatives: List[str] = field(default_factory=list)
    rationale: str = ""
    integration_notes: str = ""
    performance_tier: str = "standard"  # standard | high | extreme


@dataclass
class ArchitecturePattern:
    """A production architecture pattern for AI systems."""
    id: str
    name: str
    category: str                   # event-driven | process-isolation | state | performance
    description: str = ""
    when_to_use: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    key_technologies: List[str] = field(default_factory=list)
    python_libraries: List[str] = field(default_factory=list)
    complexity: str = "moderate"    # simple | moderate | complex | extreme
    signal_keywords: List[str] = field(default_factory=list)


@dataclass
class PerformanceConstraint:
    """A hardware/memory constraint detected from a query."""
    category: str                   # memory | compute | latency | throughput | concurrency
    description: str
    severity: str = "medium"        # low | medium | high | critical
    recommendation: str = ""
    python_gotcha: str = ""         # Python-specific performance pitfall


@dataclass
class ArchitectureAssessment:
    """Full architecture needs assessment for a user query."""
    query: str
    engineering_style: str          # architect-first | collaborative | vibe-coding | unknown
    stack_layers: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    performance_constraints: List[Dict[str, Any]] = field(default_factory=list)
    anti_patterns_detected: List[str] = field(default_factory=list)
    complexity_level: str = "moderate"
    elapsed_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "engineering_style": self.engineering_style,
            "stack_layers": self.stack_layers,
            "patterns": self.patterns,
            "performance_constraints": self.performance_constraints,
            "anti_patterns_detected": self.anti_patterns_detected,
            "complexity_level": self.complexity_level,
            "elapsed_ms": self.elapsed_ms,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LAYERED TECH STACK CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STACK_LAYERS: List[StackLayer] = [
    StackLayer(
        role="Content Management & API",
        function="Non-technical content management with webhooks for AI processing triggers",
        recommended=["Strapi + GraphQL"],
        alternatives=["Sanity.io", "Directus", "Contentful"],
        rationale="Allows non-technical teams to manage complex content architectures "
                  "while triggering automated AI processing via webhooks",
        integration_notes="Uses GraphQL subscriptions for real-time content events",
        performance_tier="standard",
    ),
    StackLayer(
        role="Backend Orchestration",
        function="High-performance async request handling for multiple agentic nodes",
        recommended=["Python + FastAPI"],
        alternatives=["Python + Django Ninja", "Node.js + tRPC", "Go + Fiber"],
        rationale="asyncio-native concurrent non-blocking requests; ASGI for max throughput",
        integration_notes="Pair with uvicorn workers behind nginx for production",
        performance_tier="high",
    ),
    StackLayer(
        role="LLM Integration Layer",
        function="Prompt chaining, RAG pipelines, and external data retrieval",
        recommended=["LangChain + OpenAI API"],
        alternatives=["LlamaIndex", "Haystack", "Semantic Kernel", "direct API calls"],
        rationale="Complex prompt chaining and RAG with built-in memory management",
        integration_notes="Use LCEL for streaming; integrates with vector stores natively",
        performance_tier="standard",
    ),
    StackLayer(
        role="Vector Storage",
        function="Semantic similarity search and metadata management for unstructured data",
        recommended=["Pinecone + PostgreSQL (pgvector)"],
        alternatives=["Weaviate", "Qdrant", "Milvus", "ChromaDB"],
        rationale="Highly efficient similarity search critical for semantic memory in agents",
        integration_notes="pgvector for co-located metadata; Pinecone for massive scale",
        performance_tier="high",
    ),
    StackLayer(
        role="Caching & Messaging",
        function="Async task queues and microservice decoupling",
        recommended=["Redis Streams + Apache Kafka"],
        alternatives=["RabbitMQ", "NATS", "AWS SQS", "Celery + Redis"],
        rationale="Completely decouples microservices; prevents agent interaction bottlenecks",
        integration_notes="Redis for hot cache + session state; Kafka for durable event log",
        performance_tier="extreme",
    ),
    StackLayer(
        role="Stream Processing",
        function="Real-time stateful computation on unbounded event streams",
        recommended=["Apache Flink"],
        alternatives=["Apache Spark Structured Streaming", "Kafka Streams", "Bytewax"],
        rationale="Handles stateful computations on unbounded data in real-time; "
                  "routes events to specialized agents based on data contracts",
        integration_notes="Flink monitors Kafka topics and invokes orchestrator LLM",
        performance_tier="extreme",
    ),
    StackLayer(
        role="State Persistence",
        function="Checkpoint and restore agentic graph state for fault-tolerance and time-travel",
        recommended=["LangGraph Checkpointers + PostgreSQL"],
        alternatives=["Redis persistence", "SQLite WAL", "custom event sourcing"],
        rationale="Persistent snapshots enable memory retention, fault-tolerance, "
                  "and the ability to rewind workflows to any historical checkpoint",
        integration_notes="Use PostgresSaver with psycopg_pool; thread_id for session routing",
        performance_tier="standard",
    ),
    StackLayer(
        role="Process Isolation & Supervision",
        function="OS-level process isolation with automatic restart and lifecycle management",
        recommended=["OmniDaemon"],
        alternatives=["supervisord", "systemd units", "Docker per-agent", "Kubernetes pods"],
        rationale="Prevents single-process trap; crash in one agent doesn't terminate system",
        integration_notes="Agent Supervisor state machine: IDLE→STARTING→RUNNING→STOPPING→CRASHED; "
                          "exponential backoff on restart; event bus (Redis) for inter-agent comms",
        performance_tier="high",
    ),
    StackLayer(
        role="Deep Learning Framework",
        function="Neural network training and inference",
        recommended=["PyTorch (research/dynamic)", "TensorFlow (enterprise/production)"],
        alternatives=["JAX", "ONNX Runtime", "Apache MXNet"],
        rationale="PyTorch for dynamic computation graphs & research; "
                  "TensorFlow for scalable production deployment",
        integration_notes="Decision depends on deployment context: research→PyTorch, enterprise→TF",
        performance_tier="extreme",
    ),
    StackLayer(
        role="Deployment & Orchestration",
        function="Containerised, scalable, resilient deployment across hybrid environments",
        recommended=["Docker + Kubernetes"],
        alternatives=["Docker Compose", "AWS ECS + Fargate", "Nomad", "Fly.io"],
        rationale="Consistent deployment across hybrid-cloud or on-premise; auto-scaling",
        integration_notes="Stateless workers behind load balancer; pull/push state from LangGraph",
        performance_tier="high",
    ),
    StackLayer(
        role="Physics Simulation Layer",
        function="Embed physical laws (PDEs) into neural network training and inference",
        recommended=["NVIDIA PhysicsNeMo + FEniCS"],
        alternatives=["DeepXDE", "Modulus (legacy)", "JAX-FEM"],
        rationale="PINNs force models to respect conservation laws; "
                  "FEniCS provides FEM solver coupling via UFL",
        integration_notes="PyTorch auto-diff computes spatial/temporal gradients; "
                          "PDE residuals added to loss function; preCICE for mesh coupling",
        performance_tier="extreme",
    ),
    StackLayer(
        role="Chemoinformatics Layer",
        function="Molecular digitisation, descriptor calculation, and QSAR modeling",
        recommended=["RDKit + DeepChem"],
        alternatives=["Open Babel", "mordred", "scikit-mol"],
        rationale="SMILES→molecular objects→physicochemical descriptors→toxicity prediction; "
                  "DeepChem provides GNN architectures optimised for chemical datasets",
        integration_notes="rdkit.Chem.MolFromSmiles for digitisation; "
                          "canonical SMILES for deduplication; DeepChem on PyTorch/JAX",
        performance_tier="high",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ARCHITECTURE PATTERN CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATTERNS: List[ArchitecturePattern] = [
    ArchitecturePattern(
        id="event_driven_eda",
        name="Event-Driven Multi-Agent Architecture",
        category="event-driven",
        description=(
            "Agents operate in a decoupled ecosystem where components "
            "interact via continuous event streams (Kafka topics / Redis Streams) "
            "rather than synchronous HTTP calls.  External actions generate "
            "event payloads → Flink routes to specialised agent topics → "
            "agents process and publish downstream events."
        ),
        when_to_use=[
            "multi-agent systems requiring loose coupling",
            "high-volume AI interaction pipelines",
            "real-time document processing workflows",
            "order-processing automation with AI agents",
        ],
        anti_patterns=[
            "synchronous HTTP chains between agents creating rigid coupling",
            "single monolithic agent handling all event types",
            "polling databases instead of consuming event streams",
        ],
        key_technologies=["Apache Kafka", "Redis Streams", "Apache Flink", "FastAPI"],
        python_libraries=["confluent-kafka", "redis", "faust-streaming", "fastapi"],
        complexity="complex",
        signal_keywords=[
            "event-driven", "kafka", "redis streams", "message queue",
            "event bus", "pub/sub", "async pipeline", "real-time", "stream processing",
            "flink", "decoupled", "microservices", "agent communication",
        ],
    ),
    ArchitecturePattern(
        id="process_isolation",
        name="OmniDaemon Process Isolation",
        category="process-isolation",
        description=(
            "Every AI agent runs in its own dedicated OS-level process.  "
            "An Agent Supervisor manages lifecycles via a state machine "
            "(IDLE → STARTING → RUNNING → STOPPING → CRASHED).  Crashes "
            "are isolated; automatic restart with exponential backoff.  "
            "Agents communicate via event bus (Redis), not shared memory."
        ),
        when_to_use=[
            "multi-agent systems where reliability is critical",
            "production AI pipelines with fault-tolerance requirements",
            "systems where individual agent crashes must not propagate",
            "environments requiring hot-swap of messaging brokers",
        ],
        anti_patterns=[
            "single-process trap — all agents in one Python process",
            "shared memory references between agents",
            "no restart protocol for crashed agents",
            "tight coupling to specific messaging broker",
        ],
        key_technologies=["OmniDaemon", "supervisord", "systemd", "Docker"],
        python_libraries=["omnidaemon", "multiprocessing", "redis"],
        complexity="complex",
        signal_keywords=[
            "process isolation", "fault tolerance", "supervisor", "crash recovery",
            "agent lifecycle", "state machine", "daemon", "omnidaemon",
            "reliability", "resilience", "hot swap",
        ],
    ),
    ArchitecturePattern(
        id="state_persistence",
        name="LangGraph State Persistence & Time-Travel",
        category="state",
        description=(
            "Persistent checkpointing of agentic graph state at every "
            "super-step.  Indexed by thread_id for session routing.  "
            "Enables memory retention, fault-tolerance, and time-travel "
            "(rewinding to historical checkpoints).  PostgresSaver with "
            "psycopg_pool for production; Redis for session discovery."
        ),
        when_to_use=[
            "conversational AI requiring perfect context retention",
            "human-in-the-loop multi-agent workflows",
            "horizontally scaled stateless backend workers",
            "workflows requiring audit trail or state replay",
        ],
        anti_patterns=[
            "in-memory-only state that is lost on restart",
            "storing full conversation history in every request payload",
            "no checkpoint mechanism for long-running workflows",
        ],
        key_technologies=["LangGraph", "PostgreSQL", "Redis", "psycopg_pool"],
        python_libraries=["langgraph", "psycopg", "redis", "fastapi"],
        complexity="moderate",
        signal_keywords=[
            "state persistence", "checkpoint", "langgraph", "time travel",
            "conversation memory", "session", "thread", "stateless workers",
            "horizontal scaling", "fault tolerance",
        ],
    ),
    ArchitecturePattern(
        id="physics_informed_nn",
        name="Physics-Informed Neural Networks (PINNs)",
        category="performance",
        description=(
            "Embed partial differential equations (Navier-Stokes, Poisson, etc.) "
            "directly into the neural network loss function.  PyTorch auto-diff "
            "computes spatial/temporal gradients; FEniCS UFL evaluates PDE residuals.  "
            "Penalises violations of conservation laws, forcing solutions that are "
            "physically possible.  preCICE handles mesh coupling for multi-physics."
        ),
        when_to_use=[
            "structural engineering with load simulation",
            "fluid dynamics (CFD) with AI acceleration",
            "thermal management in manufacturing",
            "any domain where AI must respect physical laws",
        ],
        anti_patterns=[
            "training on statistical loss only — ignoring physical constraints",
            "using standard image models for engineering geometry",
            "fiction-before-physics: visually impressive but structurally invalid designs",
        ],
        key_technologies=["FEniCS", "NVIDIA PhysicsNeMo", "preCICE", "PyTorch"],
        python_libraries=["torch", "fenics", "precice", "nvidia-physicsnemo"],
        complexity="extreme",
        signal_keywords=[
            "physics", "PDE", "finite element", "FEA", "FEM", "navier-stokes",
            "structural", "simulation", "PINN", "conservation", "mesh",
            "physicsnemo", "fenics", "stress", "strain", "load bearing",
        ],
    ),
    ArchitecturePattern(
        id="geometric_deep_learning",
        name="Geometric Deep Learning on Meshes",
        category="performance",
        description=(
            "Process simplicial meshes and unstructured point clouds natively "
            "on GPU.  TensorDict attaches scalar/vector/tensor fields to "
            "geometric vertices and cell faces.  Discrete calculus operators "
            "compute divergence, curl, and curvature directly on GPU.  "
            "GNNs + FNOs bypass slow iterative traditional solvers."
        ),
        when_to_use=[
            "aerospace CFD with complex curved surfaces",
            "thermal dynamics prediction on 3D geometries",
            "structural fatigue analysis on large meshes (50M+ nodes)",
            "real-time physics surrogate models",
        ],
        anti_patterns=[
            "flattening 3D geometry to 2D images for processing",
            "using standard CNNs on unstructured 3D data",
            "exporting GPU data to CPU-based traditional solvers",
        ],
        key_technologies=["NVIDIA PhysicsNeMo", "PyTorch Geometric", "DGL"],
        python_libraries=["torch", "torch-geometric", "nvidia-physicsnemo"],
        complexity="extreme",
        signal_keywords=[
            "mesh", "point cloud", "GNN", "graph neural network",
            "FNO", "fourier neural operator", "geometric", "voxel",
            "3D simulation", "CFD", "thermal", "aerodynamic",
        ],
    ),
    ArchitecturePattern(
        id="compound_agent_workflow",
        name="Compound Two-in-One Agent Workflows",
        category="event-driven",
        description=(
            "Multiple distinct capabilities chained within a persistent, "
            "event-driven architecture.  Examples: email parser → LLM → "
            "auto-reply + Telegram bot → DALL-E generation.  Clinical: "
            "EHR parsing → imaging modality selection → CV scan → PACS."
        ),
        when_to_use=[
            "multi-step automation crossing tool boundaries",
            "clinical diagnostic imaging pipelines",
            "compliance monitoring → remediation chains",
            "content workflows (ingest → translate → publish)",
        ],
        anti_patterns=[
            "single-tool solutions for multi-step workflows",
            "manual handoffs between pipeline stages",
            "no state persistence between chained steps",
        ],
        key_technologies=["LangGraph", "Sabrina.dev", "Apache Kafka", "Redis"],
        python_libraries=["langgraph", "langchain", "celery", "redis"],
        complexity="complex",
        signal_keywords=[
            "compound", "two-in-one", "chain", "pipeline", "multi-step",
            "workflow", "automation", "orchestrate", "sequence",
        ],
    ),
    ArchitecturePattern(
        id="memory_performance",
        name="Memory Performance Optimization",
        category="performance",
        description=(
            "Critical awareness of Python memory pitfalls: memoryview.index() "
            "is ~860× slower than bytes.index() due to CPython generic iteration "
            "fallback.  For high-performance data layers, use compiled languages "
            "(C# Span<T>/Memory<T>) while retaining Python for orchestration.  "
            "Enforce strict concurrency with isolated async pipelines and locking."
        ),
        when_to_use=[
            "massive embedding/byte-array processing",
            "high-performance parsing of large datasets",
            "real-time inference with latency constraints",
            "mixed Python + compiled language architectures",
        ],
        anti_patterns=[
            "using memoryview for byte scanning (860× slower than bytes)",
            "single-threaded Python for data-heavy processing",
            "no GIL-aware concurrency strategy",
            "copying large arrays instead of using zero-copy views",
        ],
        key_technologies=["C# Span<T>", "Cython", "Rust + PyO3", "numpy"],
        python_libraries=["numpy", "cython", "cffi", "pyo3"],
        complexity="complex",
        signal_keywords=[
            "memory", "performance", "optimization", "memoryview", "bytes",
            "zero-copy", "span", "GIL", "concurrency", "latency",
            "throughput", "embedding", "tensor", "parsing",
        ],
    ),
    ArchitecturePattern(
        id="dp_fine_tuning",
        name="Differential Privacy Fine-Tuning",
        category="privacy",
        description=(
            "DP-SGD injects calibrated noise into gradients during fine-tuning "
            "to prevent membership inference attacks.  Privacy-Flat framework: "
            "(1) perturbation-aware min-max within layers, (2) flatness-guided "
            "sparse prefix-tuning across layers, (3) weight knowledge distillation. "
            "Achieves utility parity under strict ε=3 budgets."
        ),
        when_to_use=[
            "fine-tuning on classified government documents",
            "healthcare PHI model adaptation",
            "any environment where training data must never be extractable",
        ],
        anti_patterns=[
            "standard fine-tuning on sensitive data (memorization risk)",
            "no privacy budget tracking (ε not defined)",
            "assuming open-weights means no data leakage risk",
        ],
        key_technologies=["Opacus", "DP-Transformers", "PEFT"],
        python_libraries=["opacus", "dp-transformers", "peft", "torch"],
        complexity="extreme",
        signal_keywords=[
            "differential privacy", "DP-SGD", "privacy", "classified",
            "fine-tuning", "membership inference", "epsilon", "noise",
            "opacus", "sensitive data", "PHI",
        ],
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERFORMANCE CONSTRAINT CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERFORMANCE_CONSTRAINTS: List[PerformanceConstraint] = [
    PerformanceConstraint(
        category="memory",
        description="memoryview vs bytes performance trap",
        severity="high",
        recommendation="Use bytes.index() instead of memoryview.index() for byte scanning; "
                       "memoryview.index() is ~860× slower due to CPython generic iteration fallback",
        python_gotcha="memoryview lacks stringlib optimisation; falls back to generic sequence iteration "
                      "creating iterator + next slot + integer object overhead per byte",
    ),
    PerformanceConstraint(
        category="memory",
        description="Zero-copy slicing for large tensors",
        severity="medium",
        recommendation="Use numpy views or C# Span<T>/Memory<T> for zero-copy slicing; "
                       "avoid copying data arrays during string parsing or tensor manipulation",
        python_gotcha="Python list slicing creates copies; numpy array slicing creates views",
    ),
    PerformanceConstraint(
        category="concurrency",
        description="Global Interpreter Lock (GIL) limitation",
        severity="high",
        recommendation="Use multiprocessing for CPU-bound AI tasks; asyncio for I/O-bound; "
                       "consider compiled extensions (Cython, Rust) for hot loops",
        python_gotcha="GIL prevents true parallelism in CPython threads; "
                      "threading only helps I/O-bound workloads",
    ),
    PerformanceConstraint(
        category="concurrency",
        description="Race conditions in shared memory views during parallel inference",
        severity="critical",
        recommendation="Use isolated async pipelines or highly specific locking mechanisms; "
                       "never allow concurrent loops to access shared memory views unsynchronised",
        python_gotcha="asyncio.Lock for coroutine safety; threading.Lock for thread safety; "
                      "multiprocessing.Lock for process safety — they are NOT interchangeable",
    ),
    PerformanceConstraint(
        category="compute",
        description="GPU vs CPU inference routing",
        severity="medium",
        recommendation="Route inference to GPU for batch processing; CPU for single-sample latency-sensitive; "
                       "use torch.cuda.is_available() for dynamic device selection",
        python_gotcha="Moving tensors between CPU↔GPU is expensive; batch transfers to amortise cost",
    ),
    PerformanceConstraint(
        category="latency",
        description="LLM response latency for real-time systems",
        severity="high",
        recommendation="Use streaming (SSE/WebSocket) for perceived latency reduction; "
                       "cache frequent queries in Redis; consider smaller models for sub-second paths",
        python_gotcha="Synchronous LLM calls block the event loop in async frameworks; "
                      "always use async clients (httpx.AsyncClient, openai.AsyncOpenAI)",
    ),
    PerformanceConstraint(
        category="throughput",
        description="Database bottleneck in high-volume agent systems",
        severity="high",
        recommendation="Decouple agent interactions from primary database via event bus (Kafka/Redis); "
                       "use connection pooling (psycopg_pool) and read replicas",
        python_gotcha="SQLAlchemy async requires greenlet; prefer asyncpg for raw PostgreSQL performance",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENGINEERING STYLE DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_ARCHITECT_FIRST_SIGNALS = [
    "architect", "blueprint", "specification", "solid principles",
    "design pattern", "flyweight", "scoped state", "definition of done",
    "naming convention", "xml documentation", "implementation plan",
    "modular tdd", "test-driven", "pytest", "unit test",
    "requirements engineering", "interface segregation", "dependency inversion",
    "single responsibility", "open-closed", "liskov",
]

_VIBE_CODING_SIGNALS = [
    "vibe coding", "just prompt", "generate app", "build me a",
    "create an app", "make me a website", "code this for me",
    "no tests", "quick prototype", "skip planning",
    "just write the code", "generate everything",
]

_ENTERPRISE_SIGNALS = [
    "enterprise", "production", "scalable", "fault-tolerant",
    "microservices", "kubernetes", "docker", "ci/cd",
    "load balancer", "horizontal scaling", "monitoring",
    "observability", "SLA", "99.9%", "uptime",
]

# Words that negate a following signal ("avoid vibe coding" ≠ promoting it)
_NEGATION_PREFIXES = [
    "avoid", "prevent", "stop", "don't", "do not", "never",
    "without", "eliminate", "fix", "refactor away from",
    "migrate from", "escape", "instead of",
]

def _filter_negated(signals: list, text: str) -> list:
    """Remove signals whose occurrence in *text* is preceded by a negation."""
    confirmed = []
    for sig in signals:
        idx = text.find(sig)
        if idx < 0:
            continue
        # Look at the 40-char window before the signal for negation words
        prefix_window = text[max(0, idx - 40) : idx].strip()
        if any(prefix_window.endswith(neg) or neg in prefix_window for neg in _NEGATION_PREFIXES):
            continue  # negated — skip this signal
        confirmed.append(sig)
    return confirmed


def classify_engineering_query(query: str) -> Dict[str, Any]:
    """
    Classify a software engineering query as architect-first,
    collaborative, or vibe-coding.

    Returns
    -------
    {
        "style": str,
        "confidence": float,
        "signals": list[str],
        "warnings": list[str],
        "recommendations": list[str],
    }
    """
    q_lower = query.lower()
    architect_hits = [s for s in _ARCHITECT_FIRST_SIGNALS if s in q_lower]
    vibe_hits = _filter_negated(
        [s for s in _VIBE_CODING_SIGNALS if s in q_lower], q_lower,
    )
    enterprise_hits = [s for s in _ENTERPRISE_SIGNALS if s in q_lower]

    # Score
    arch_score = len(architect_hits) * 0.15
    vibe_score = len(vibe_hits) * 0.25
    ent_score = len(enterprise_hits) * 0.12

    style = "unknown"
    confidence = 0.0
    warnings = []
    recommendations = []

    if vibe_score > arch_score and vibe_score > 0.2:
        style = "vibe-coding"
        confidence = min(vibe_score, 1.0)
        warnings = [
            "Vibe coding without specifications creates monolithic, unmaintainable code",
            "AI-generated code without tests accumulates catastrophic technical debt",
            "Without architectural blueprints, AI defaults to hallucinated design patterns",
        ]
        recommendations = [
            "Adopt Architect-First methodology: write implementation blueprint before generating code",
            "Enforce Modular TDD: author tests before application logic",
            "Define strict naming conventions and SOLID principle enforcement",
            "Use Python pytest pipelines with iterative LLM self-correction loops",
        ]
    elif arch_score > vibe_score and arch_score > 0.1:
        style = "architect-first"
        confidence = min(arch_score + ent_score, 1.0)
        recommendations = [
            "Pair with LangChain + OpenAI for specification translation",
            "Use guardrails-ai for strict schema enforcement on generated code",
            "Deploy Modular TDD loops with automated pytest → LLM retry pipelines",
        ]
    elif ent_score > 0.1:
        style = "enterprise"
        confidence = min(ent_score, 1.0)
        recommendations = [
            "Use event-driven architecture (Kafka + Redis) for agent decoupling",
            "Deploy OmniDaemon process isolation for fault tolerance",
            "Implement LangGraph checkpointers for state persistence",
            "Docker + Kubernetes for deployment orchestration",
        ]
    else:
        style = "collaborative"
        confidence = 0.5

    return {
        "style": style,
        "confidence": round(confidence, 3),
        "signals": architect_hits + vibe_hits + enterprise_hits,
        "warnings": warnings,
        "recommendations": recommendations,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STACK & PATTERN RECOMMENDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _score_pattern(pat: ArchitecturePattern, query: str) -> float:
    """Score a pattern against a query using keyword overlap."""
    q_lower = query.lower()
    q_words = set(re.findall(r"[a-z]{3,}", q_lower))
    score = 0.0

    for kw in pat.signal_keywords:
        if kw.lower() in q_lower:
            score += 0.12
        elif any(w in kw.lower().split() for w in q_words):
            score += 0.04

    for tech in pat.key_technologies:
        if tech.lower() in q_lower:
            score += 0.15

    for lib in pat.python_libraries:
        if lib.lower() in q_lower:
            score += 0.10

    return min(score, 1.0)


def _score_layer(layer: StackLayer, query: str) -> float:
    """Score a tech-stack layer against a query."""
    q_lower = query.lower()
    score = 0.0

    if any(r.lower() in q_lower for r in layer.recommended):
        score += 0.3
    if any(a.lower() in q_lower for a in layer.alternatives):
        score += 0.15

    role_words = set(re.findall(r"[a-z]{3,}", layer.role.lower()))
    func_words = set(re.findall(r"[a-z]{4,}", layer.function.lower()))
    q_words = set(re.findall(r"[a-z]{3,}", q_lower))

    overlap = len(q_words & (role_words | func_words))
    score += overlap * 0.08

    return min(score, 1.0)


def recommend_stack(
    query: str,
    *,
    max_layers: int = 8,
    threshold: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Recommend relevant tech-stack layers for the query.

    Returns layers sorted by relevance with scores.
    """
    scored = []
    for layer in STACK_LAYERS:
        s = _score_layer(layer, query)
        if s >= threshold:
            scored.append({
                "role": layer.role,
                "function": layer.function,
                "recommended": layer.recommended,
                "alternatives": layer.alternatives,
                "rationale": layer.rationale,
                "integration_notes": layer.integration_notes,
                "performance_tier": layer.performance_tier,
                "relevance": round(s, 3),
            })

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:max_layers]


def recommend_patterns(
    query: str,
    *,
    max_patterns: int = 5,
    threshold: float = 0.05,
) -> List[Dict[str, Any]]:
    """
    Recommend architecture patterns matching the query.

    Returns patterns sorted by relevance with scores.
    """
    scored = []
    for pat in PATTERNS:
        s = _score_pattern(pat, query)
        if s >= threshold:
            scored.append({
                "id": pat.id,
                "name": pat.name,
                "category": pat.category,
                "description": pat.description,
                "when_to_use": pat.when_to_use,
                "anti_patterns": pat.anti_patterns,
                "key_technologies": pat.key_technologies,
                "python_libraries": pat.python_libraries,
                "complexity": pat.complexity,
                "relevance": round(s, 3),
            })

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:max_patterns]


def get_performance_constraints(
    query: str,
) -> List[Dict[str, Any]]:
    """
    Detect performance constraints relevant to the query.
    """
    q_lower = query.lower()
    results = []

    for pc in PERFORMANCE_CONSTRAINTS:
        kw = set(re.findall(r"[a-z]{4,}", pc.description.lower()))
        kw.update(re.findall(r"[a-z]{4,}", pc.recommendation.lower()))
        q_words = set(re.findall(r"[a-z]{4,}", q_lower))
        overlap = len(kw & q_words)

        # Also check category
        if pc.category in q_lower:
            overlap += 2

        if overlap >= 1:
            results.append({
                "category": pc.category,
                "description": pc.description,
                "severity": pc.severity,
                "recommendation": pc.recommendation,
                "python_gotcha": pc.python_gotcha,
                "relevance": overlap,
            })

    results.sort(key=lambda x: x["relevance"], reverse=True)
    return results[:5]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MASTER ASSESSMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def detect_architecture_needs(
    query: str,
    *,
    industry: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Master function — analyses a query for architecture requirements
    and returns a comprehensive assessment.

    Returns
    -------
    {
        "engineering_style": {...},
        "stack_layers": [...],
        "patterns": [...],
        "performance_constraints": [...],
        "complexity_level": str,
        "elapsed_ms": int,
    }
    """
    t0 = time.perf_counter()

    eng_style = classify_engineering_query(query)
    stack = recommend_stack(query)
    patterns = recommend_patterns(query)
    perf = get_performance_constraints(query)

    # Determine complexity
    complexity = "simple"
    if len(patterns) >= 3 or any(p.get("complexity") == "extreme" for p in patterns):
        complexity = "extreme"
    elif len(patterns) >= 2 or len(stack) >= 4:
        complexity = "complex"
    elif len(patterns) >= 1 or len(stack) >= 2:
        complexity = "moderate"

    # Detect anti-patterns
    anti_patterns = []
    q_lower = query.lower()
    if "vibe coding" in q_lower or "just prompt" in q_lower:
        anti_patterns.append("vibe-coding detected — recommend Architect-First methodology")
    if "monolithic" in q_lower or "single process" in q_lower:
        anti_patterns.append("monolithic/single-process risk — recommend process isolation")
    if "synchronous" in q_lower and ("agent" in q_lower or "multi" in q_lower):
        anti_patterns.append("synchronous multi-agent coupling — recommend event-driven architecture")
    if "memoryview" in q_lower and "index" in q_lower:
        anti_patterns.append("memoryview.index() is ~860× slower than bytes.index()")

    elapsed = int((time.perf_counter() - t0) * 1000)

    result = {
        "engineering_style": eng_style,
        "stack_layers": stack,
        "patterns": patterns,
        "performance_constraints": perf,
        "anti_patterns_detected": anti_patterns,
        "complexity_level": complexity,
        "elapsed_ms": elapsed,
    }

    log.info(
        "detect_architecture_needs: style=%s, %d layers, %d patterns, "
        "complexity=%s in %dms",
        eng_style["style"], len(stack), len(patterns), complexity, elapsed,
    )

    return result


def get_stack_layers() -> List[Dict[str, Any]]:
    """Return the full stack layer catalogue."""
    return [
        {
            "role": sl.role,
            "function": sl.function,
            "recommended": sl.recommended,
            "alternatives": sl.alternatives,
            "rationale": sl.rationale,
            "performance_tier": sl.performance_tier,
        }
        for sl in STACK_LAYERS
    ]


def get_patterns() -> List[Dict[str, Any]]:
    """Return the full architecture pattern catalogue."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "description": p.description,
            "complexity": p.complexity,
            "key_technologies": p.key_technologies,
            "python_libraries": p.python_libraries,
        }
        for p in PATTERNS
    ]


def score_architecture(query: str) -> Dict[str, Any]:
    """
    Holistic architecture maturity score for a query.

    Returns a 0-100 score with breakdown by dimensions.
    """
    needs = detect_architecture_needs(query)

    # Scoring dimensions
    has_patterns = min(len(needs["patterns"]) * 15, 30)
    has_stack = min(len(needs["stack_layers"]) * 8, 25)
    has_perf = min(len(needs["performance_constraints"]) * 10, 20)
    style_bonus = 15 if needs["engineering_style"]["style"] in ("architect-first", "enterprise") else 0
    anti_penalty = len(needs["anti_patterns_detected"]) * 5

    score = max(0, min(100, has_patterns + has_stack + has_perf + style_bonus - anti_penalty + 10))

    return {
        "score": score,
        "grade": "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D",
        "dimensions": {
            "patterns": has_patterns,
            "stack_coverage": has_stack,
            "performance_awareness": has_perf,
            "engineering_maturity": style_bonus,
            "anti_pattern_penalty": -anti_penalty,
        },
        "assessment": needs,
    }


log.info("orchestration.py loaded — %d stack layers, %d patterns, %d perf constraints",
         len(STACK_LAYERS), len(PATTERNS), len(PERFORMANCE_CONSTRAINTS))
