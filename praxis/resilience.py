"""
Praxis Resilience — Vibe Coding Detection & Architectural Risk Intelligence  (v10)

Encodes the full body of knowledge from "Architecting Resilient Python Systems
in the Era of Generative AI" as a programmatic recommendation engine.

The module provides:

 * Vibe-coding risk scoring — detect when a query or workflow smells like
   unconstrained AI slop generation rather than architect-first engineering.
 * Static analysis strategy — recommend the right mix of Bandit / Semgrep /
   Sloppylint / Ruff / Mypy given the project context.
 * Sandbox strategy — gVisor / Firecracker / WebAssembly / Capsule selection
   based on isolation requirements.
 * TDD prompt-engineering cycle — Red-Green-Refactor guidance for bounding
   the probabilistic latent space.
 * R.P.I. (Research-Plan-Implement) framework — context pollution mitigation
   and intentional compaction recommendations.
 * Self-healing CI/CD patterns — Try-Heal-Retry, Pipeline Doctor, Pydantic
   Logic Funnel recommendations.
 * Agentic reflection patterns — ReAct, Reflexion, Two-Agent architecture.
 * LLM-as-a-Judge bias catalogue — execution blindness, verbosity bias,
   unnatural code bias, security vulnerability.
 * Middleware guardrail pipeline — 3-layer defense-in-depth architecture.
 * Human-in-the-Loop workflow guidance — Temporal, checkpoint/hibernate,
   durable execution recommendations.
 * Junior developer pipeline — AI-as-mentor vs AI-as-vending-machine.

Public API
──────────
    assess_resilience          → master assessment for a query
    score_vibe_coding_risk     → 0-1 vibe-coding risk score
    recommend_static_analysis  → ranked static analysis toolchain
    recommend_sandbox          → ranked isolation strategies
    get_tdd_cycle              → TDD prompt-engineering guidance
    get_rpi_framework          → R.P.I. context management framework
    get_self_healing_patterns  → CI/CD self-healing patterns
    get_reflection_patterns    → agentic reflection architectures
    get_judge_biases           → LLM-as-a-Judge bias catalogue
    get_guardrail_pipeline     → 3-layer middleware guardrail spec
    get_hitl_guidance          → human-in-the-loop recommendations
    assess_junior_pipeline     → junior developer pipeline health
    get_hallucination_types    → AI hallucination taxonomy
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA CLASSES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ResilienceAssessment:
    """Full resilience assessment for a user query."""
    query: str
    vibe_coding_risk: float             # 0.0 = architect, 1.0 = pure vibe
    risk_grade: str                     # A-F
    risk_signals: List[str]
    warnings: List[str]
    static_analysis: List[Dict[str, Any]]
    sandbox_strategy: List[Dict[str, Any]]
    recommended_patterns: List[Dict[str, Any]]
    hallucination_risks: List[str]
    hitl_required: bool
    elapsed_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "vibe_coding_risk": self.vibe_coding_risk,
            "risk_grade": self.risk_grade,
            "risk_signals": self.risk_signals,
            "warnings": self.warnings,
            "static_analysis": self.static_analysis,
            "sandbox_strategy": self.sandbox_strategy,
            "recommended_patterns": self.recommended_patterns,
            "hallucination_risks": self.hallucination_risks,
            "hitl_required": self.hitl_required,
            "elapsed_ms": self.elapsed_ms,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  VIBE CODING RISK DETECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_VIBE_SIGNALS = [
    ("just generate", 0.20, "No specification — pure vibe coding"),
    ("generate everything", 0.25, "Requesting bulk autonomous generation"),
    ("build me a", 0.15, "Vague generative request without architecture"),
    ("make me a", 0.15, "Vague generative request without architecture"),
    ("create an app", 0.18, "App-level generation from single prompt"),
    ("vibe coding", 0.30, "Explicit vibe coding intent"),
    ("no tests", 0.20, "Bypassing TDD — no safety net"),
    ("skip testing", 0.20, "Bypassing TDD — no safety net"),
    ("skip planning", 0.18, "No architectural planning phase"),
    ("just prompt", 0.15, "Treating AI as code vending machine"),
    ("just copy", 0.18, "Blindly copying AI output without review"),
    ("quick prototype", 0.08, "Prototype mentality without safeguards"),
    ("code this for me", 0.15, "Delegation without understanding"),
    ("write the whole", 0.18, "Requesting monolithic generation"),
    ("generate app", 0.18, "Full application generation request"),
    ("don't need tests", 0.22, "Explicitly rejecting test guardrails"),
    ("don't worry about", 0.12, "Dismissing quality constraints"),
    ("just make it work", 0.15, "Functionality-only without quality"),
    ("automate everything", 0.10, "Unbounded automation request"),
    ("let ai handle", 0.20, "Abdicating architectural authority"),
    ("ai will figure", 0.22, "Over-reliance on AI autonomy"),
]

_ARCHITECT_SIGNALS = [
    ("architect", -0.08),
    ("specification", -0.10),
    ("blueprint", -0.10),
    ("test-driven", -0.12),
    ("tdd", -0.12),
    ("pytest", -0.08),
    ("unit test", -0.08),
    ("code review", -0.10),
    ("design pattern", -0.08),
    ("solid principles", -0.10),
    ("human review", -0.10),
    ("security audit", -0.12),
    ("static analysis", -0.10),
    ("bandit", -0.06),
    ("semgrep", -0.08),
    ("sandbox", -0.06),
    ("rpi framework", -0.12),
    ("research plan implement", -0.12),
    ("hitl", -0.10),
    ("human-in-the-loop", -0.12),
]


def score_vibe_coding_risk(query: str) -> Dict[str, Any]:
    """
    Score how likely a query represents dangerous vibe coding (0.0—1.0).

    Returns
    -------
    {
        "risk_score": float,
        "grade": str,       # A (safe) through F (pure vibe slop)
        "signals": [...],
        "mitigations": [...],
        "warnings": [...],
    }
    """
    q_lower = query.lower()
    signals: List[str] = []
    warnings: List[str] = []
    raw = 0.0

    # Positive risk signals
    for pattern, weight, desc in _VIBE_SIGNALS:
        if pattern in q_lower:
            raw += weight
            signals.append(desc)

    # Negative (mitigating) signals
    mitigations: List[str] = []
    for pattern, weight in _ARCHITECT_SIGNALS:
        if pattern in q_lower:
            raw += weight   # weight is negative
            mitigations.append(f"Detected: '{pattern}' — mitigating risk")

    # Length heuristic — very short queries with no detail = risky
    word_count = len(query.split())
    if word_count < 8 and raw > 0:
        raw += 0.10
        signals.append("Extremely short query — insufficient specification depth")
    elif word_count > 50:
        raw -= 0.05
        mitigations.append("Detailed query — suggests thoughtful specification")

    risk = max(0.0, min(1.0, raw))

    # Grade
    if risk >= 0.8:
        grade = "F"
        warnings = [
            "CRITICAL: This query exhibits extreme vibe coding signals",
            "AI-generated code without tests accumulates catastrophic security debt",
            "Vibe coding creates a 'lost generation' of engineers who cannot debug",
            "Unconstrained AI agents risk runaway loops and destructive operations",
        ]
    elif risk >= 0.6:
        grade = "D"
        warnings = [
            "HIGH RISK: Query lacks architectural safeguards",
            "Enforce Test-Driven Development before any code generation",
            "Apply R.P.I. framework to prevent context pollution",
        ]
    elif risk >= 0.4:
        grade = "C"
        warnings = [
            "MODERATE RISK: Some vibe coding tendencies detected",
            "Consider adding explicit test requirements and code review steps",
        ]
    elif risk >= 0.2:
        grade = "B"
        warnings = ["LOW RISK: Minor vibe coding signals — maintain architectural discipline"]
    else:
        grade = "A"
        warnings = []

    return {
        "risk_score": round(risk, 3),
        "grade": grade,
        "signals": signals,
        "mitigations": mitigations,
        "warnings": warnings,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HALLUCINATION TAXONOMY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HALLUCINATION_TYPES: List[Dict[str, Any]] = [
    {
        "id": "polyglot_bleeding",
        "name": "Polyglot Syntax Bleeding",
        "description": "LLM applies syntax from Java, JavaScript, or Ruby to Python objects — "
                       "e.g., .forEach(), .length, .equals(), .isEmpty(), .nil?, array_push()",
        "severity": "high",
        "detection": "Sloppylint scans for non-Python idioms in generated code",
        "example": "Using myList.forEach() instead of for x in my_list",
    },
    {
        "id": "package_hallucination",
        "name": "Package Hallucination & Supply Chain Attacks",
        "description": "Model invents non-existent PyPI packages; attackers pre-register "
                       "hallucinated names to execute supply chain attacks on pip install",
        "severity": "critical",
        "detection": "Verify all import statements against known-good package allowlist; "
                     "use pip audit and safety check before installation",
        "example": "import flask_ml_utils  # hallucinated package, malicious on PyPI",
    },
    {
        "id": "api_fabrication",
        "name": "API & Method Fabrication",
        "description": "Model confidently invokes API endpoints, class methods, or function "
                       "signatures that do not exist in the target library version",
        "severity": "high",
        "detection": "Type checking (Mypy), automated import verification, integration tests",
        "example": "pandas.DataFrame.to_graphql()  # method does not exist",
    },
    {
        "id": "confident_falsity",
        "name": "Confident Factual Falsity",
        "description": "Model states incorrect facts with high confidence — fabricated "
                       "study citations, wrong library version numbers, incorrect defaults",
        "severity": "medium",
        "detection": "RAG with verified-only sources; mandatory human fact-checking",
        "example": "Claiming numpy 2.0 deprecated np.array (false)",
    },
    {
        "id": "logic_hallucination",
        "name": "Logical Hallucination",
        "description": "Code appears syntactically valid but contains subtle logical errors — "
                       "off-by-one, inverted conditions, incorrect recursion base cases",
        "severity": "high",
        "detection": "Property-based testing (Hypothesis), mutation testing, code execution",
        "example": "if len(items) >= 0: return items[0]  # works for empty list by accident",
    },
    {
        "id": "security_hallucination",
        "name": "Security Hallucination",
        "description": "Model generates code with hardcoded API keys, weak cryptography, "
                       "authorization bypasses, or insecure deserialization",
        "severity": "critical",
        "detection": "Bandit + Semgrep security scanning in CI pipeline",
        "example": "API_KEY = 'sk-live-abc123...'  # hardcoded secret in source",
    },
]


def get_hallucination_types() -> List[Dict[str, Any]]:
    """Return the full hallucination taxonomy."""
    return HALLUCINATION_TYPES


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATIC ANALYSIS STRATEGY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATIC_ANALYSIS_TOOLS: List[Dict[str, Any]] = [
    {
        "id": "semgrep",
        "name": "Semgrep",
        "mechanism": "Extensible pattern matching and deep taint analysis",
        "targets": [
            "Advanced injection risks", "complex API misconfigurations",
            "custom architectural violations", "insecure data flows",
        ],
        "vibe_coding_efficacy": "high",
        "rationale": "Customizable registries allow adaptation to evolving AI threat "
                     "landscapes; replaces Bandit+ESLint in major platforms like GitLab",
        "signal_keywords": ["security", "injection", "taint", "vulnerability", "api", "production"],
        "priority": 1,
    },
    {
        "id": "bandit",
        "name": "Bandit",
        "mechanism": "Heuristic AST parsing for Python security flaws",
        "targets": [
            "Hardcoded secrets", "weak cryptography",
            "dangerous built-in functions (eval, exec)", "insecure imports",
        ],
        "vibe_coding_efficacy": "moderate",
        "rationale": "Foundational security scanner; susceptible to missing complex "
                     "data flows generated by advanced models; high false-positive rate",
        "signal_keywords": ["security", "secrets", "eval", "crypto", "basic"],
        "priority": 2,
    },
    {
        "id": "sloppylint",
        "name": "Sloppylint",
        "mechanism": "AI-specific anti-pattern matching",
        "targets": [
            "Polyglot hallucinations (.forEach, .length on Python objects)",
            "Non-idiomatic AI structures", "JavaScript/Java/Ruby syntax bleeding",
        ],
        "vibe_coding_efficacy": "essential",
        "rationale": "Only linter purpose-built to catch generative AI slop; acts as "
                     "complementary layer that rejects hallucinated syntax before CI",
        "signal_keywords": ["ai", "hallucination", "slop", "polyglot", "generated"],
        "priority": 1,
    },
    {
        "id": "ruff",
        "name": "Ruff",
        "mechanism": "Ultra-fast lexical and AST analysis (Rust-based)",
        "targets": [
            "Code style deviations", "unused imports", "undefined names",
            "basic formatting violations",
        ],
        "vibe_coding_efficacy": "low",
        "rationale": "Blind to logical hallucinations and cross-language syntax "
                     "bleeding; excellent for speed but insufficient standalone",
        "signal_keywords": ["style", "format", "lint", "fast", "import"],
        "priority": 3,
    },
    {
        "id": "mypy",
        "name": "Mypy",
        "mechanism": "Static type checking against type annotations",
        "targets": [
            "Type mismatches", "missing return types", "incorrect generics",
            "API fabrication detection via stub files",
        ],
        "vibe_coding_efficacy": "moderate",
        "rationale": "Catches AI-fabricated method calls and wrong argument types; "
                     "requires type annotations to be maximally effective",
        "signal_keywords": ["type", "typing", "annotation", "strict", "mypy"],
        "priority": 2,
    },
]


def recommend_static_analysis(
    query: str,
    *,
    max_tools: int = 5,
) -> List[Dict[str, Any]]:
    """
    Recommend a ranked static analysis toolchain for the query.
    """
    q_lower = query.lower()
    scored = []

    for tool in STATIC_ANALYSIS_TOOLS:
        score = 0.0
        for kw in tool["signal_keywords"]:
            if kw in q_lower:
                score += 0.15
        # Prioritise by vibe coding relevance
        if tool["vibe_coding_efficacy"] == "essential":
            score += 0.25
        elif tool["vibe_coding_efficacy"] == "high":
            score += 0.18
        elif tool["vibe_coding_efficacy"] == "moderate":
            score += 0.10

        scored.append({**tool, "relevance": round(score, 3)})

    scored.sort(key=lambda x: (-x["relevance"], x["priority"]))
    return scored[:max_tools]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SANDBOX STRATEGY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SANDBOX_STRATEGIES: List[Dict[str, Any]] = [
    {
        "id": "gvisor_agent_sandbox",
        "name": "gVisor + Agent Sandbox",
        "isolation_level": "user-space kernel",
        "description": "gVisor intercepts system calls between container and host OS; "
                       "Agent Sandbox provides K8s-native ephemeral pods with SandboxWarmPool "
                       "for <1s startup latency",
        "when_to_use": [
            "Kubernetes-native AI agent execution",
            "Production environments requiring strong process/storage/network isolation",
            "High-volume ephemeral execution with warm pool scheduling",
        ],
        "limitations": ["Requires Kubernetes cluster", "Some syscall compatibility gaps"],
        "technologies": ["gVisor", "Agent Sandbox", "Kubernetes"],
        "signal_keywords": ["kubernetes", "container", "production", "agent", "execution", "sandbox"],
    },
    {
        "id": "firecracker_microvm",
        "name": "AWS Firecracker MicroVM",
        "isolation_level": "hardware-level hypervisor",
        "description": "Wraps containers within lightweight VMs for hardware-level isolation; "
                       "each AI task gets its own VM boundary",
        "when_to_use": [
            "Maximum isolation for untrusted code",
            "AWS-native environments",
            "Compliance requirements demanding hardware isolation",
        ],
        "limitations": ["Substantial per-task overhead", "AWS ecosystem affinity"],
        "technologies": ["Firecracker", "Kata Containers"],
        "signal_keywords": ["hardware", "vm", "microvm", "firecracker", "aws", "maximum security"],
    },
    {
        "id": "wasm_capsule",
        "name": "WebAssembly (Capsule)",
        "isolation_level": "deny-by-default WASM sandbox",
        "description": "Compiles Python tasks to WebAssembly modules with zero privileges; "
                       "strict fuel metering prevents infinite loops; returns structured JSON envelopes",
        "when_to_use": [
            "Granular per-task isolation",
            "Preventing runaway infinite loops from hallucinating agents",
            "Lightweight isolation without full container overhead",
        ],
        "limitations": [
            "Incompatible with NumPy/Pandas (C-extension limitation)",
            "No direct filesystem/network access",
            "Python networking not supported",
        ],
        "technologies": ["WebAssembly", "Capsule"],
        "signal_keywords": ["wasm", "webassembly", "capsule", "task", "function", "lightweight", "loop"],
    },
    {
        "id": "docker_standard",
        "name": "Standard Docker Containers",
        "isolation_level": "namespace isolation (shared kernel)",
        "description": "Standard Linux containers — INSUFFICIENT for untrusted AI code. "
                       "Shared host kernel means kernel exploits = full system breakout",
        "when_to_use": [
            "Development/testing environments only",
            "Trusted code with known dependencies",
        ],
        "limitations": [
            "Shared kernel — vulnerable to kernel exploits",
            "No protection against container breakout",
            "NOT recommended for untrusted AI-generated code",
        ],
        "technologies": ["Docker"],
        "signal_keywords": ["docker", "container", "dev", "testing"],
        "warning": "INSUFFICIENT for executing untrusted AI-generated code",
    },
    {
        "id": "language_level",
        "name": "Python Language-Level Sandboxing",
        "isolation_level": "NONE — dangerous fallacy",
        "description": "Attempting to sandbox Python by deleting builtins (del __builtins__.eval) "
                       "is trivially bypassed via object graph traversal "
                       "(().__class__.__bases__[0].__subclasses__()) or traceback frame access "
                       "(e.__traceback__.tb_frame.f_globals)",
        "when_to_use": [],
        "limitations": [
            "NEVER use for security isolation",
            "Python's mutable runtime makes language sandboxing impossible",
            "Any restriction can be bypassed via introspection",
        ],
        "technologies": [],
        "signal_keywords": [],
        "warning": "DANGEROUS FALLACY — never rely on Python language-level sandboxing for security",
    },
]


def recommend_sandbox(
    query: str,
    *,
    max_results: int = 4,
) -> List[Dict[str, Any]]:
    """Recommend isolation strategies ranked by relevance."""
    q_lower = query.lower()
    scored = []

    for strat in SANDBOX_STRATEGIES:
        if strat["id"] == "language_level":
            continue  # never recommend
        score = 0.0
        for kw in strat.get("signal_keywords", []):
            if kw in q_lower:
                score += 0.12
        if strat["isolation_level"] in ("user-space kernel", "hardware-level hypervisor"):
            score += 0.10
        scored.append({**strat, "relevance": round(score, 3)})

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:max_results]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TDD PROMPT ENGINEERING CYCLE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TDD_CYCLE: Dict[str, Any] = {
    "name": "Test-Driven Prompt Engineering",
    "purpose": "Bound the probabilistic latent space of LLMs using deterministic test constraints",
    "phases": [
        {
            "phase": "Red — Generate Failing Tests",
            "description": (
                "Feed a high-level feature description to the AI and instruct it to "
                "generate a comprehensive PyTest suite defining expected behavior. "
                "Explicitly challenge the AI to brainstorm edge cases: extremely long "
                "strings, null inputs, empty data structures, unexpected Unicode. "
                "These failing tests establish an airtight API contract that acts as "
                "context-specific guardrails."
            ),
            "prompt_template": (
                "Given this feature specification: {spec}\n"
                "Generate a comprehensive pytest test suite that:\n"
                "1. Tests all happy-path behaviors\n"
                "2. Tests edge cases: empty inputs, null values, extremely long strings\n"
                "3. Tests Unicode edge cases and special characters\n"
                "4. Tests error handling and exception paths\n"
                "5. Tests boundary conditions\n"
                "DO NOT write any implementation code."
            ),
            "anti_pattern": "Writing implementation before tests — lets AI hallucinate unchecked",
        },
        {
            "phase": "Green — Minimal Implementation",
            "description": (
                "Prompt the AI to review failing tests and write the absolute minimal "
                "implementation to make those specific tests pass. Prevents over-engineering, "
                "bloated slop, and unrequested features."
            ),
            "prompt_template": (
                "Here are the failing test results:\n{test_output}\n"
                "Write the MINIMAL implementation code to make these tests pass. "
                "Do NOT add any functionality not required by the tests."
            ),
            "anti_pattern": "Asking AI to 'build everything' — generates bloated, untested slop",
        },
        {
            "phase": "Green — Error Feedback Loop",
            "description": (
                "If tests fail, feed the exact Python traceback, error name, and "
                "localized code logic back into the AI context. Never vaguely ask "
                "'fix the bug' — provide empirical evidence for precise diagnosis."
            ),
            "prompt_template": (
                "The test suite produced this failure:\n"
                "Error: {error_name}\n"
                "Traceback:\n{traceback}\n"
                "Failing test:\n{test_code}\n"
                "Implementation:\n{impl_code}\n"
                "Diagnose the root cause and generate a minimal patch."
            ),
            "anti_pattern": "Vaguely asking AI to 'fix' without empirical traceback data",
        },
        {
            "phase": "Refactor — Confident Restructuring",
            "description": (
                "With all tests passing, instruct the AI to optimize, modernize, "
                "and make the code more Pythonic. The pre-existing test suite "
                "immediately flags any regression, enabling confident massive changes."
            ),
            "prompt_template": (
                "All tests pass. Refactor this implementation to:\n"
                "1. Improve algorithmic complexity\n"
                "2. Follow Pythonic conventions\n"
                "3. Add type annotations\n"
                "4. Improve readability\n"
                "The existing test suite MUST continue to pass."
            ),
            "anti_pattern": "Refactoring without test coverage — no regression detection",
        },
    ],
}


def get_tdd_cycle() -> Dict[str, Any]:
    """Return the TDD prompt-engineering cycle specification."""
    return TDD_CYCLE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  R.P.I. FRAMEWORK — Context Pollution Mitigation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RPI_FRAMEWORK: Dict[str, Any] = {
    "name": "Research-Plan-Implement (R.P.I.) Framework",
    "purpose": "Eradicate context pollution and prevent the 'Dumb Zone' — "
               "the state where a model's attention is diluted by irrelevant data, "
               "causing reasoning collapse and unmitigated slop generation",
    "phases": [
        {
            "phase": "Research — Establish Empirical Ground Truth",
            "constraints": [
                "AI is STRICTLY FORBIDDEN from writing implementation code",
                "Execute read-only queries against the filesystem only",
                "Assume documentation is obsolete or deceitful — verify empirically",
                "Output: compact deterministic markdown summary of repo state",
            ],
            "purpose": "Establish absolute ground truth without polluting context",
        },
        {
            "phase": "Plan — Compression of Intent",
            "constraints": [
                "SEPARATE reasoning model or human architect reviews research summary",
                "Author a detailed, step-by-step technical implementation plan",
                "Human MUST review and approve the PLAN, not just the final code",
                "This is the critical bottleneck for human-in-the-loop intervention",
            ],
            "purpose": "Translate vague requirements into clean, explicit technical directives",
            "warning": "Reviewing only the final code — not the plan — outsources "
                       "core architectural thinking to probabilistic models",
        },
        {
            "phase": "Implement — Intentional Compaction",
            "constraints": [
                "ENTIRELY SEPARATE AI agent with FRESH EMPTY context window",
                "Feed ONLY the approved plan + localized files to modify",
                "Zero context pollution from research phase",
                "Model dedicates 100% attention to high-fidelity code generation",
            ],
            "purpose": "Achieve 'Intentional Compaction' — immune to context pollution",
        },
    ],
    "anti_patterns": [
        "Single-threaded linear conversation for complex codebases",
        "Allowing research context to pollute implementation context",
        "Skipping the planning phase — junior devs flood repos with slop",
        "No human review of the plan — outsourcing architecture to AI",
    ],
    "warning": "Without R.P.I. discipline, junior developers use AI to fill skill gaps, "
               "flooding repositories with slop that causes severe senior engineer burnout",
}


def get_rpi_framework() -> Dict[str, Any]:
    """Return the R.P.I. framework specification."""
    return RPI_FRAMEWORK


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SELF-HEALING CI/CD PATTERNS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SELF_HEALING_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "pipeline_doctor",
        "name": "Pipeline Doctor / Interceptor",
        "description": (
            "Pipeline failure is treated as a trigger event, not a terminal stop. "
            "A specialised 'Repair Agent' ingests the error trace, analyses surrounding "
            "logs, and independently formulates a fix with scoped read-only permissions."
        ),
        "pattern": "Try-Heal-Retry",
        "technologies": ["Pydantic (Logic Funnel)", "LangChain", "GitHub Actions"],
        "pydantic_role": "Pydantic schema acts as a 'Logic Funnel' — forces LLM to return "
                          "executable payloads with specific data types, array lengths, and "
                          "exact JSON structures rather than conversational text",
    },
    {
        "id": "react_reflexion",
        "name": "ReAct + Reflexion Self-Debugging Loop",
        "description": (
            "Cyclic self-correcting agent loop: Think → Act → Observe → Reflect. "
            "LLM generates implementation (Think), sandbox executes (Act), captures "
            "stdout/stderr/traces (Observe), agent evaluates mistake and corrects (Reflect)."
        ),
        "pattern": "Think-Act-Observe-Reflect",
        "technologies": ["LangGraph", "PyCapsule", "Sandbox"],
    },
    {
        "id": "two_agent",
        "name": "Two-Agent Architecture (Programmer + Executor)",
        "description": (
            "Programmer Agent handles code generation/refactoring; isolated Executor Agent "
            "handles validation, unit testing, and error analysis. Segregation prevents "
            "the LLM from conflating intended logic with actual runtime output."
        ),
        "pattern": "Segregation of Duties",
        "technologies": ["PyCapsule", "LangGraph", "Docker"],
    },
]


def get_self_healing_patterns() -> List[Dict[str, Any]]:
    """Return the self-healing CI/CD pattern catalogue."""
    return SELF_HEALING_PATTERNS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AGENTIC REFLECTION PATTERNS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFLECTION_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "react",
        "name": "ReAct (Reason + Act)",
        "description": "Agent alternates between reasoning about the task and taking actions; "
                       "each observation informs the next reasoning step",
        "cycle": ["Reason", "Act", "Observe"],
        "strength": "Grounded reasoning via real-world feedback",
        "weakness": "No explicit self-critique mechanism",
    },
    {
        "id": "reflexion",
        "name": "Reflexion",
        "description": "Agent explicitly evaluates its previous mistakes after observing results "
                       "and generates verbal self-critique to improve next attempt",
        "cycle": ["Think", "Act", "Observe", "Reflect"],
        "strength": "Self-improving through explicit error analysis",
        "weakness": "Higher token consumption per iteration",
    },
    {
        "id": "two_agent_segregation",
        "name": "Two-Agent Segregation",
        "description": "Programmer Agent (generation) + Executor Agent (validation/testing) — "
                       "functional independence prevents logic-output conflation",
        "cycle": ["Generate", "Execute", "Analyse", "Correct"],
        "strength": "Minimises computational consumption; clean separation of concerns",
        "weakness": "Requires orchestration framework (LangGraph) for control flow",
    },
]


def get_reflection_patterns() -> List[Dict[str, Any]]:
    """Return the agentic reflection pattern catalogue."""
    return REFLECTION_PATTERNS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  LLM-AS-A-JUDGE BIAS CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JUDGE_BIASES: List[Dict[str, Any]] = [
    {
        "id": "execution_blindness",
        "name": "Execution Blindness",
        "description": "LLMs struggle to evaluate functional correctness through static text "
                       "analysis alone — hallucinate non-existent bugs (FP) or miss severe "
                       "logical flaws (FN) without actual execution traces",
        "severity": "critical",
        "mitigation": "Supply LLM judges with actual execution traces and stdout logs, "
                      "not just source code",
    },
    {
        "id": "verbosity_bias",
        "name": "Verbosity Bias",
        "description": "LLMs exhibit systemic preference for lengthy, detailed outputs — "
                       "consistently underrate concise, efficient code in favour of verbose explanations",
        "severity": "high",
        "mitigation": "Explicitly weight conciseness in evaluation rubric; "
                      "penalise excessive verbosity in scoring criteria",
    },
    {
        "id": "unnatural_code_bias",
        "name": "Unnatural Code Bias",
        "description": "AI judges consistently underrate highly optimised human-written code "
                       "because it lacks the predictable structural patterns common in AI generation",
        "severity": "medium",
        "mitigation": "Calibrate with human-expert ground truth scores; "
                      "use diverse evaluation panels (multiple judge models)",
    },
    {
        "id": "security_vulnerability",
        "name": "Security Vulnerability in Judging",
        "description": "LLM judges miss nuanced threats like hallucinated packages and are "
                       "susceptible to adversarial prompt injection attacks embedded in code",
        "severity": "critical",
        "mitigation": "Layer deterministic security scanners (Semgrep, Bandit) alongside "
                      "LLM-based evaluation; never rely on LLM judge alone for security",
    },
]


def get_judge_biases() -> List[Dict[str, Any]]:
    """Return the LLM-as-a-Judge bias catalogue."""
    return JUDGE_BIASES


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MIDDLEWARE GUARDRAIL PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GUARDRAIL_PIPELINE: List[Dict[str, Any]] = [
    {
        "layer": 1,
        "name": "Input Security — Perimeter Defence",
        "function": "Fast deterministic checks to filter malicious prompt injections "
                    "and irrelevant prompts before they reach agent reasoning",
        "mechanisms": [
            "Deterministic regex pattern matching",
            "Keyword-based injection detection",
            "PII detection, masking, and redaction (credit cards, IPs, SSNs)",
        ],
        "latency": "sub-millisecond",
        "defense_type": "deterministic",
    },
    {
        "layer": 2,
        "name": "Plan Scrutiny — Intent Validation",
        "function": "Evaluate agent's proposed action plan against compliance policies "
                    "before execution — blocks risky or non-compliant intentions",
        "mechanisms": [
            "Action plan validation against corporate compliance policies",
            "Unauthorised shell command detection",
            "Resource access control enforcement",
            "Data exfiltration pattern detection",
        ],
        "latency": "low",
        "defense_type": "policy-based",
    },
    {
        "layer": 3,
        "name": "Output Verification — Adaptive Sanitisation",
        "function": "Rigorous output verification using adaptive guardrails derived "
                    "from historical red-team testing and vulnerability discoveries",
        "mechanisms": [
            "Model-based output evaluation against evaluation rubric",
            "Adaptive guardrails from red-team vulnerability history",
            "Schema enforcement (Pydantic Logic Funnel)",
            "Hallucination detection via execution trace comparison",
        ],
        "latency": "moderate",
        "defense_type": "adaptive + model-based",
    },
]


def get_guardrail_pipeline() -> List[Dict[str, Any]]:
    """Return the 3-layer middleware guardrail pipeline specification."""
    return GUARDRAIL_PIPELINE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HUMAN-IN-THE-LOOP GUIDANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HITL_GUIDANCE: Dict[str, Any] = {
    "principle": "Human-in-the-Loop is a CORE ARCHITECTURAL REQUIREMENT, "
                 "not an optional fallback mechanism",
    "rationale": "AI agents inevitably encounter undocumented edge cases, hallucinate "
                 "complex logic, or reach junctures requiring authoritative human decisions",
    "implementation": {
        "state_management": {
            "requirement": "Systems must pause gracefully, wait for human review "
                           "(minutes/hours/weeks), and resume without context loss",
            "technology": "Temporal — durable execution framework for long-running workflows",
            "pattern": "Agent reaches checkpoint → notifies human → hibernates state → "
                       "resumes on approval/correction",
        },
        "high_stakes_scenarios": [
            "AI modifications to cloud infrastructure",
            "Financial transaction approvals",
            "Security protocol modifications",
            "Production database operations",
            "Compliance-sensitive data processing",
        ],
        "feedback_capture": "Every human correction MUST be captured in structured feedback "
                            "database to continuously retrain and improve future accuracy",
        "code_review_scaling": {
            "problem": "Pull request review becomes bottleneck as AI code volume grows — "
                       "review latency rises, engagement declines, cognitive fatigue sets in",
            "solution": "Shift code review LEFT — embed AI-assisted review directly in IDE "
                        "for immediate in-flow feedback before code is committed",
        },
    },
}


def get_hitl_guidance() -> Dict[str, Any]:
    """Return human-in-the-loop workflow guidance."""
    return HITL_GUIDANCE


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  JUNIOR DEVELOPER PIPELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def assess_junior_pipeline(query: str) -> Dict[str, Any]:
    """
    Assess whether a query/workflow supports junior developer growth
    or contributes to the 'lost generation' problem.
    """
    q_lower = query.lower()

    mentorship_signals = [
        ("pair program", "AI as pair programmer — supports learning"),
        ("explain", "Requesting explanation — promotes understanding"),
        ("teach me", "Mentorship mode — builds competency"),
        ("help me understand", "Deep understanding — builds debugging skills"),
        ("debug", "Debugging practice — essential career skill"),
        ("step by step", "Structured learning — builds architectural intuition"),
        ("code review", "Review culture — teaches secure patterns"),
        ("why does", "Curiosity-driven — builds pattern recognition"),
        ("how does", "Mechanistic understanding — builds system thinking"),
    ]

    vending_signals = [
        ("just generate", "AI as vending machine — blocks learning"),
        ("build it for me", "Zero developer engagement — atrophies skills"),
        ("copy paste", "Mindless adoption — no understanding"),
        ("don't explain", "Rejecting mentorship — skill stagnation"),
        ("just the code", "Output-only mentality — no comprehension"),
    ]

    mentorship_hits = [(sig, desc) for sig, desc in mentorship_signals if sig in q_lower]
    vending_hits = [(sig, desc) for sig, desc in vending_signals if sig in q_lower]

    if vending_hits and not mentorship_hits:
        mode = "vending-machine"
        health = "critical"
        warning = (
            "AI-as-vending-machine creates a 'lost generation' of engineers lacking "
            "debugging skills, pattern recognition, and architectural intuition"
        )
    elif mentorship_hits:
        mode = "mentor"
        health = "healthy"
        warning = None
    else:
        mode = "neutral"
        health = "unknown"
        warning = (
            "Consider framing AI interactions as pair programming sessions — "
            "narrate thought process, ask about design patterns, query edge cases"
        )

    return {
        "mode": mode,
        "pipeline_health": health,
        "mentorship_signals": [d for _, d in mentorship_hits],
        "vending_signals": [d for _, d in vending_hits],
        "warning": warning,
        "recommendation": (
            "Treat AI as a junior peer: narrate your thought process, ask about "
            "design patterns, query missing edge cases. Observe the Think-Act-Observe-"
            "Reflect cycle to learn professional-grade error-aware reasoning."
        ),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MASTER ASSESSMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def assess_resilience(query: str) -> Dict[str, Any]:
    """
    Master function — comprehensive resilience assessment for a query.

    Combines vibe-coding risk, static analysis recommendations, sandbox
    strategy, hallucination risks, and HITL requirements into a single
    assessment.
    """
    t0 = time.perf_counter()

    # Vibe coding risk
    vibe = score_vibe_coding_risk(query)

    # Static analysis
    sa = recommend_static_analysis(query)

    # Sandbox
    sb = recommend_sandbox(query)

    # Hallucination detection
    q_lower = query.lower()
    hallucination_risks: List[str] = []
    for ht in HALLUCINATION_TYPES:
        # Check if any hallucination-related keywords appear
        kw_match = any(k in q_lower for k in [
            ht["id"].replace("_", " "),
            ht["name"].lower().split()[0],
        ])
        if kw_match or (ht["severity"] == "critical" and vibe["risk_score"] > 0.3):
            hallucination_risks.append(f"{ht['name']}: {ht['description']}")

    # HITL required?
    hitl_keywords = ["production", "infrastructure", "financial", "security",
                     "database", "deploy", "compliance", "cloud"]
    hitl_required = any(k in q_lower for k in hitl_keywords) or vibe["risk_score"] > 0.5

    # Patterns — select most relevant
    patterns: List[Dict[str, Any]] = []
    if vibe["risk_score"] > 0.3:
        patterns.append({
            "pattern": "R.P.I. Framework",
            "reason": "High vibe-coding risk — enforce Research-Plan-Implement discipline",
        })
    if vibe["risk_score"] > 0.2:
        patterns.append({
            "pattern": "TDD Prompt Engineering",
            "reason": "Bound latent space with test-driven constraints",
        })
    if "ci" in q_lower or "pipeline" in q_lower or "deploy" in q_lower:
        patterns.append({
            "pattern": "Self-Healing CI/CD (Try-Heal-Retry)",
            "reason": "Pipeline resilience for probabilistic AI outputs",
        })
    if "agent" in q_lower or "autonomous" in q_lower:
        patterns.append({
            "pattern": "Two-Agent Architecture",
            "reason": "Segregate generation from validation for agent reliability",
        })
    if hitl_required:
        patterns.append({
            "pattern": "Human-in-the-Loop (Temporal)",
            "reason": "High-stakes scenario requires human approval checkpoints",
        })

    elapsed = int((time.perf_counter() - t0) * 1000)

    assessment = ResilienceAssessment(
        query=query,
        vibe_coding_risk=vibe["risk_score"],
        risk_grade=vibe["grade"],
        risk_signals=vibe["signals"],
        warnings=vibe["warnings"],
        static_analysis=sa,
        sandbox_strategy=sb,
        recommended_patterns=patterns,
        hallucination_risks=hallucination_risks,
        hitl_required=hitl_required,
        elapsed_ms=elapsed,
    )

    log.info(
        "assess_resilience: vibe_risk=%.2f grade=%s, %d SA tools, "
        "%d sandbox, hitl=%s in %dms",
        vibe["risk_score"], vibe["grade"], len(sa),
        len(sb), hitl_required, elapsed,
    )

    return assessment.to_dict()


log.info(
    "resilience.py loaded — %d hallucination types, %d SA tools, "
    "%d sandbox strategies, %d self-healing patterns, %d judge biases",
    len(HALLUCINATION_TYPES), len(STATIC_ANALYSIS_TOOLS),
    len(SANDBOX_STRATEGIES), len(SELF_HEALING_PATTERNS), len(JUDGE_BIASES),
)
