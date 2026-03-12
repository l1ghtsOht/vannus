"""
praxis.metacognition  –  Autonomous Metacognition for Vibe-Coded Architectures
===============================================================================
v11 intelligence layer implementing self-awareness and self-healing patterns
for Python systems built under AI-native / vibe-coding paradigms.

Covers six architectural layers:
  1. Runtime Introspection & Dynamic Telemetry
  2. Structural Self-Reflection via AST / LibCST
  3. Metacognitive Prompting & Code Stylometry
  4. Repository-Level Semantic Consistency (RACG)
  5. Safe Execution Sandboxing & Verification
  6. GoodVibe Autonomous Security Remediation

Plus:  vibe-pathology detection, technical-bankruptcy scoring,
       self-healing economics & risk analysis, architectural-drift
       monitoring, and the Analyze→Patch→Verify→Propose cycle.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# =====================================================================
# Data-class: master metacognition assessment
# =====================================================================

@dataclass
class MetacognitionAssessment:
    """Full metacognition assessment for a query / project description."""
    query: str = ""
    self_awareness_score: float = 0.0          # 0-1
    grade: str = "C"                           # A-F
    pathology_flags: List[str] = field(default_factory=list)
    bankruptcy_risk: float = 0.0               # 0-1
    recommended_layers: List[str] = field(default_factory=list)
    sandbox_recommendation: str = ""
    security_posture: str = ""
    drift_risk: str = "low"
    healing_loop_bounded: bool = False
    stylometry_probability: float = 0.0        # 0-1 AI-generation prob.
    metacognitive_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "self_awareness_score": round(self.self_awareness_score, 3),
            "grade": self.grade,
            "pathology_flags": self.pathology_flags,
            "bankruptcy_risk": round(self.bankruptcy_risk, 3),
            "recommended_layers": self.recommended_layers,
            "sandbox_recommendation": self.sandbox_recommendation,
            "security_posture": self.security_posture,
            "drift_risk": self.drift_risk,
            "healing_loop_bounded": self.healing_loop_bounded,
            "stylometry_probability": round(self.stylometry_probability, 3),
            "metacognitive_steps": self.metacognitive_steps,
            "warnings": self.warnings,
        }


# =====================================================================
# 1  FOUR HORSEMEN — Vibe-Coded Pathology Detection
# =====================================================================

FAILURE_MODES: List[Dict[str, Any]] = [
    {
        "id": "zero_db_indexing",
        "name": "Zero Database Indexing",
        "prevalence": 0.89,
        "impact": "critical",
        "description": (
            "Applications generated to manually scan hundreds of thousands of "
            "records per request.  Functions flawlessly in early prototyping "
            "but catastrophically fails under load — unhandled timeouts and "
            "database crashes as the LLM failed to anticipate scalar data growth."
        ),
        "signals": [
            "full table scan", "no index", "sequential scan",
            "query timeout", "database crash", "ORM N+1",
        ],
        "remediation": (
            "Add composite indexes on foreign-key and frequently-filtered "
            "columns; enable query-plan analysis (EXPLAIN ANALYZE); implement "
            "read replicas and caching layers."
        ),
    },
    {
        "id": "server_overspending",
        "name": "Massive Server Overspending",
        "prevalence": 0.76,
        "impact": "high",
        "description": (
            "Organizations provision up to 8× more server capacity than "
            "empirically required, compensating for fundamentally inefficient "
            "AI-generated algorithmic complexities with raw compute power "
            "rather than refactoring root logic."
        ),
        "signals": [
            "autoscale", "over-provisioned", "high CPU idle",
            "brute force", "O(n²)", "no profiling",
        ],
        "remediation": (
            "Profile hot paths (cProfile / py-spy); replace brute-force "
            "algorithms with indexed / cached equivalents; set declarative "
            "resource quotas and Policy-as-Code cost ceilings."
        ),
    },
    {
        "id": "absent_tests",
        "name": "Absence of Automated Tests",
        "prevalence": 0.91,
        "impact": "critical",
        "description": (
            "Feature deployment velocity drops asymptotically to zero as "
            "developers fear breaking undocumented, fragile components.  "
            "The AI did not generate deterministic verification mechanisms "
            "alongside the feature code."
        ),
        "signals": [
            "no tests", "no pytest", "no coverage", "manual QA only",
            "fear of refactor", "undocumented",
        ],
        "remediation": (
            "Mandate minimum 80% branch coverage; auto-generate pytest "
            "stubs via AST node enumeration; integrate coverage gating "
            "into CI/CD pipelines."
        ),
    },
    {
        "id": "security_vulnerabilities",
        "name": "Critical Security Vulnerabilities",
        "prevalence": 0.68,
        "impact": "critical",
        "description": (
            "LLM-generated code routinely bypasses human security reviews "
            "— severe authentication and authorization flaws.  AI models "
            "generate functional but deeply insecure placeholder logic "
            "silently pushed to production."
        ),
        "signals": [
            "no auth", "hardcoded secret", "SQL injection",
            "XSS", "insecure placeholder", "no input validation",
        ],
        "remediation": (
            "Deploy GoodVibe security-neuron judge model; run Bandit + "
            "Semgrep in pre-commit hooks; enforce parameterized queries "
            "and input sanitization."
        ),
    },
]


def get_failure_modes() -> List[Dict[str, Any]]:
    """Return the Four Horsemen failure-mode catalogue."""
    return FAILURE_MODES


def detect_pathologies(query: str) -> Dict[str, Any]:
    """Scan a query / project description for Four Horsemen signals.

    Returns dict with ``flags`` (list of matched failure‐mode IDs),
    ``bankruptcy_risk`` (0‐1 float), and ``remediations``.
    """
    q = query.lower()
    flags: List[str] = []
    remediations: List[str] = []

    for fm in FAILURE_MODES:
        hits = sum(1 for s in fm["signals"] if s in q)
        if hits:
            flags.append(fm["id"])
            remediations.append(fm["remediation"])

    # bankruptcy risk = weighted average of matched prevalences
    if flags:
        matched = [fm for fm in FAILURE_MODES if fm["id"] in flags]
        bankruptcy = sum(fm["prevalence"] for fm in matched) / len(matched)
    else:
        bankruptcy = 0.0

    return {
        "flags": flags,
        "bankruptcy_risk": round(bankruptcy, 3),
        "remediations": remediations,
    }


# =====================================================================
# 2  STRUCTURAL ENTROPY & TECHNICAL BANKRUPTCY SCORING
# =====================================================================

_ENTROPY_SIGNALS: List[Dict[str, float]] = [
    {"pattern": "vibe cod",     "weight": 0.15},
    {"pattern": "no review",    "weight": 0.12},
    {"pattern": "ai generat",   "weight": 0.12},
    {"pattern": "copy paste",   "weight": 0.10},
    {"pattern": "prototype",    "weight": 0.08},
    {"pattern": "quick hack",   "weight": 0.14},
    {"pattern": "no doc",       "weight": 0.09},
    {"pattern": "spaghetti",    "weight": 0.13},
    {"pattern": "tight coupl",  "weight": 0.11},
    {"pattern": "god class",    "weight": 0.12},
    {"pattern": "mega function","weight": 0.11},
    {"pattern": "no abstract",  "weight": 0.10},
    {"pattern": "dead code",    "weight": 0.08},
    {"pattern": "redundant",    "weight": 0.07},
    {"pattern": "duplicate",    "weight": 0.07},
    {"pattern": "no type hint", "weight": 0.06},
    {"pattern": "global state", "weight": 0.10},
    {"pattern": "monolith",     "weight": 0.08},
    {"pattern": "brittle",      "weight": 0.09},
    {"pattern": "fragile",      "weight": 0.09},
]

_MITIGATING: List[Dict[str, float]] = [
    {"pattern": "test suite",   "weight": 0.10},
    {"pattern": "ci/cd",        "weight": 0.08},
    {"pattern": "code review",  "weight": 0.09},
    {"pattern": "refactor",     "weight": 0.07},
    {"pattern": "type check",   "weight": 0.06},
    {"pattern": "architect",    "weight": 0.08},
    {"pattern": "design pattern","weight": 0.07},
    {"pattern": "abstraction",  "weight": 0.06},
    {"pattern": "solid principle","weight": 0.07},
    {"pattern": "modular",      "weight": 0.06},
    {"pattern": "coverage",     "weight": 0.07},
    {"pattern": "lint",         "weight": 0.05},
    {"pattern": "doc string",   "weight": 0.04},
    {"pattern": "sandbox",      "weight": 0.06},
    {"pattern": "policy",       "weight": 0.05},
]


def score_structural_entropy(query: str) -> Dict[str, Any]:
    """Compute structural-entropy score (0-1) for a project description.

    Higher = greater entropy / closer to technical bankruptcy.
    """
    q = query.lower()
    raw = sum(s["weight"] for s in _ENTROPY_SIGNALS if s["pattern"] in q)
    mitigation = sum(s["weight"] for s in _MITIGATING if s["pattern"] in q)
    score = max(0.0, min(1.0, raw - mitigation))

    if score >= 0.7:
        grade = "F"
        status = "technical_bankruptcy"
    elif score >= 0.5:
        grade = "D"
        status = "high_entropy"
    elif score >= 0.3:
        grade = "C"
        status = "moderate_entropy"
    elif score >= 0.15:
        grade = "B"
        status = "manageable"
    else:
        grade = "A"
        status = "healthy"

    return {
        "entropy_score": round(score, 3),
        "grade": grade,
        "status": status,
        "signals_matched": [
            s["pattern"] for s in _ENTROPY_SIGNALS if s["pattern"] in q
        ],
        "mitigations_matched": [
            s["pattern"] for s in _MITIGATING if s["pattern"] in q
        ],
    }


# =====================================================================
# 3  SIX-LAYER METACOGNITIVE ARCHITECTURE
# =====================================================================

METACOGNITIVE_LAYERS: List[Dict[str, Any]] = [
    {
        "layer": 1,
        "name": "Runtime Introspection & Dynamic Telemetry",
        "description": (
            "Foundation of software self-awareness — monitors dynamic state "
            "in real-time using inspect module, dir(), getattr(), vars(), "
            "__dict__.  Intercepts exceptions, captures local/global variable "
            "state at failure, maps function signatures via inspect.signature(), "
            "and pipes stderr (2>&1) into the metacognitive AI layer."
        ),
        "python_tools": [
            "inspect", "dir()", "getattr()", "vars()", "__dict__",
            "traceback", "sys.exc_info()", "logging",
        ],
        "capabilities": [
            "exception interception",
            "call-stack capture",
            "parameter introspection",
            "context-aware retry with exponential backoff",
            "granular telemetry for LLM diagnostic",
        ],
        "use_when": [
            "runtime failures",
            "debugging AI-generated code",
            "building self-healing error recovery",
        ],
    },
    {
        "layer": 2,
        "name": "Structural Self-Reflection via AST / LibCST",
        "description": (
            "Parses source code into Abstract Syntax Trees to understand "
            "anatomy at rest.  Standard ast module identifies branches, loops, "
            "and exception paths.  LibCST (Concrete Syntax Tree) enables "
            "round-trip parsing fidelity — preserves formatting, comments, "
            "and whitespace while allowing targeted node patching."
        ),
        "python_tools": [
            "ast", "LibCST", "astroid", "radon (cyclomatic complexity)",
        ],
        "capabilities": [
            "cyclomatic complexity measurement",
            "dead-code detection",
            "AST-node-targeted test generation",
            "round-trip code rewriting",
            "intelligent fuzz testing via boundary-value AST traversal",
        ],
        "use_when": [
            "high cyclomatic complexity detected",
            "auto-generating test suites",
            "safe code rewriting / refactoring",
        ],
    },
    {
        "layer": 3,
        "name": "Metacognitive Prompting & Code Stylometry",
        "description": (
            "Detects the stylometric fingerprint of the codebase — calculates "
            "'vibe score' probability that modules were AI-generated without "
            "human oversight.  Metrics: cyclomatic complexity, code-clone "
            "detection (tree edit distance), coupling metrics.  Triggers "
            "multi-stage metacognitive prompt workflow."
        ),
        "python_tools": [
            "radon", "vulture", "jscpd", "code-clone detectors",
        ],
        "capabilities": [
            "AI-generation probability scoring",
            "stylometric fingerprinting",
            "multi-stage introspective workflow (Analyze → Judge → "
            "Critique → Propose → Confidence)",
            "hallucination mitigation via forced self-critique",
            "confidence calibration",
        ],
        "metacognitive_workflow": [
            "1. Analyze input: review AST paths, stylometric metrics, runtime logs",
            "2. Initial judgment: formulate hypothesis on root architectural flaw",
            "3. Critical evaluation: challenge assumptions — 'Could this be wrong?'",
            "4. Propose final answer: synthesize patch from self-critique",
            "5. State confidence: calibrated score with reasoning + LibCST mods",
        ],
        "use_when": [
            "flagged high AI-generation probability",
            "high structural entropy + dense redundancy",
            "before deploying autonomous refactoring",
        ],
    },
    {
        "layer": 4,
        "name": "Repository-Level Semantic Consistency (RACG)",
        "description": (
            "Overcomes contextual myopia of standard vibe coding.  Uses "
            "Retrieval-Augmented Code Generation with CodeBERT embeddings "
            "indexed in FAISS for cosine-similarity retrieval.  Constructs "
            "global Data Flow Graph / AST-graph mapping all cross-file "
            "dependencies to enforce semantic consistency."
        ),
        "python_tools": [
            "CodeBERT", "FAISS", "sentence-transformers",
            "NetworkX (AST-graph)", "InfoNCE loss",
        ],
        "capabilities": [
            "cross-file dependency retrieval",
            "global interface definition tracking",
            "data-flow graph construction",
            "dynamic model routing with cost-aware selection",
            "global invariant enforcement",
        ],
        "use_when": [
            "multi-file refactoring",
            "schema changes with downstream impact",
            "eliminating redundant data models and conflicting API contracts",
        ],
    },
    {
        "layer": 5,
        "name": "Safe Execution Sandboxing & Verification",
        "description": (
            "Isolates self-generated patches in ephemeral sandboxes before "
            "any production deployment.  The Analyze→Patch→Verify→Propose "
            "cycle: provision sandbox → load patches + auto-generated tests → "
            "run tests → on pass, create PR to staging; on fail, feed stderr "
            "back into metacognitive loop."
        ),
        "python_tools": [
            "E2B (cloud Linux VMs)", "Docker-Py", "Pyodide (WebAssembly)",
            "Firecracker (microVMs)",
        ],
        "capabilities": [
            "ephemeral sandbox provisioning",
            "automated patch verification",
            "AST complexity regression checks",
            "security vulnerability scanning pre-merge",
            "continuous iteration on failed patches",
        ],
        "use_when": [
            "deploying autonomous code modifications",
            "verifying LLM-generated patches",
            "multi-tenant agent execution requiring isolation",
        ],
    },
    {
        "layer": 6,
        "name": "GoodVibe Autonomous Security Remediation",
        "description": (
            "Dual-model closed-loop DevSecOps: primary LLM generates "
            "functional code/patches; secondary judge model (fine-tuned on "
            "security-critical neurons via GoodVibe methodology) continuously "
            "audits the repository AST for insecure patterns.  Achieves "
            "matching performance with 4,700× fewer trainable parameters than "
            "full fine-tuning."
        ),
        "python_tools": [
            "codedog-ai", "Bandit", "Semgrep", "GoodVibe-tuned judge model",
        ],
        "capabilities": [
            "security-neuron localization and optimization",
            "unparameterized SQL detection",
            "API key exposure scanning",
            "XSS and auth-flaw detection",
            "closed-loop autonomous remediation routing",
        ],
        "use_when": [
            "vibe-coded projects without security review",
            "continuous background security auditing",
            "autonomous DevSecOps pipeline",
        ],
    },
]


def get_metacognitive_layers() -> List[Dict[str, Any]]:
    """Return the six-layer metacognitive architecture catalogue."""
    return METACOGNITIVE_LAYERS


def recommend_layers(query: str) -> List[Dict[str, Any]]:
    """Recommend which metacognitive layers apply to a project query."""
    q = query.lower()
    recommended: List[Dict[str, Any]] = []
    for layer in METACOGNITIVE_LAYERS:
        relevance = 0.0
        for uw in layer.get("use_when", []):
            if any(tok in q for tok in uw.lower().split()):
                relevance += 0.25
        # Boost layers by keyword overlap
        for tool in layer.get("python_tools", []):
            if tool.lower().replace("()", "") in q:
                relevance += 0.15
        for cap in layer.get("capabilities", []):
            keywords = [w for w in cap.lower().split() if len(w) > 4]
            if any(kw in q for kw in keywords):
                relevance += 0.10
        relevance = min(1.0, relevance)
        if relevance > 0.0:
            recommended.append({
                "layer": layer["layer"],
                "name": layer["name"],
                "relevance": round(relevance, 2),
            })
    # Always include layers 1 & 5 as baseline for vibe-coded projects
    layer_ids = {r["layer"] for r in recommended}
    for must_have in [1, 5]:
        if must_have not in layer_ids:
            lyr = METACOGNITIVE_LAYERS[must_have - 1]
            recommended.append({
                "layer": lyr["layer"],
                "name": lyr["name"],
                "relevance": 0.10,
            })
    recommended.sort(key=lambda x: (-x["relevance"], x["layer"]))
    return recommended


# =====================================================================
# 4  SANDBOX VERIFICATION STRATEGIES
# =====================================================================

SANDBOX_STRATEGIES: List[Dict[str, Any]] = [
    {
        "id": "e2b",
        "name": "E2B Cloud Linux VMs",
        "isolation_level": "OS-level",
        "startup": "seconds",
        "internet_access": True,
        "best_for": (
            "Cloud-native, scalable AI coding assistants that require "
            "internet access, complex system dependencies, and multi-tool "
            "integration."
        ),
        "characteristics": (
            "Long-running cloud-hosted environments.  Full OS access built on "
            "fully isolated open-source infrastructure without risking the host."
        ),
    },
    {
        "id": "docker",
        "name": "Docker / Docker-Py",
        "isolation_level": "container-level",
        "startup": "seconds",
        "internet_access": True,
        "best_for": (
            "Local development workflows and standard CI/CD pipeline testing "
            "for syntax, linting, and unit-test verification."
        ),
        "characteristics": (
            "Standard containerized environments.  Less secure against "
            "advanced kernel-level breakouts than microVMs, but ubiquitous "
            "and easy to orchestrate."
        ),
    },
    {
        "id": "pyodide_wasm",
        "name": "WebAssembly (Pyodide)",
        "isolation_level": "wasm-sandbox",
        "startup": "milliseconds",
        "internet_access": False,
        "best_for": (
            "High-speed lightweight logic verification and autonomous control "
            "loops requiring strict host isolation and instant feedback."
        ),
        "characteristics": (
            "Executes Python entirely within a WASM sandbox — browser or "
            "Node.js/CLI.  No remote execution, limits system-level API access."
        ),
    },
    {
        "id": "firecracker",
        "name": "Firecracker MicroVMs",
        "isolation_level": "VM-level (KVM)",
        "startup": "<125ms",
        "internet_access": True,
        "best_for": (
            "Granular multi-tenant agent execution where absolute, "
            "cryptographic isolation from untrusted AI-generated code "
            "is mandated."
        ),
        "characteristics": (
            "True VM-level security requiring KVM virtualization.  "
            "'Secure by default' with minimal overhead compared to "
            "traditional heavyweight VMs."
        ),
    },
]


def get_sandbox_strategies() -> List[Dict[str, Any]]:
    """Return sandbox verification strategies for the APVP cycle."""
    return SANDBOX_STRATEGIES


def recommend_sandbox_for_verification(query: str) -> Dict[str, Any]:
    """Recommend the best sandbox strategy for a given verification need."""
    q = query.lower()
    if any(k in q for k in ["multi-tenant", "untrusted", "cryptographic", "kvm"]):
        pick = "firecracker"
    elif any(k in q for k in ["cloud", "internet", "scalable", "multi-tool"]):
        pick = "e2b"
    elif any(k in q for k in ["instant", "fast", "wasm", "lightweight", "browser"]):
        pick = "pyodide_wasm"
    else:
        pick = "docker"
    strat = next(s for s in SANDBOX_STRATEGIES if s["id"] == pick)
    return {"recommended": strat, "all_strategies": SANDBOX_STRATEGIES}


# =====================================================================
# 5  CODE STYLOMETRY & AI-GENERATION PROBABILITY
# =====================================================================

_STYLOMETRY_CUES: List[Dict[str, float]] = [
    {"pattern": "ai generat",     "weight": 0.18},
    {"pattern": "vibe cod",       "weight": 0.16},
    {"pattern": "copilot",        "weight": 0.12},
    {"pattern": "chatgpt",        "weight": 0.14},
    {"pattern": "no human review","weight": 0.15},
    {"pattern": "auto generat",   "weight": 0.13},
    {"pattern": "prompt generat", "weight": 0.14},
    {"pattern": "llm generat",    "weight": 0.13},
    {"pattern": "boilerplate",    "weight": 0.08},
    {"pattern": "scaffold",       "weight": 0.07},
    {"pattern": "long function",  "weight": 0.09},
    {"pattern": "short class",    "weight": 0.07},
    {"pattern": "no comment",     "weight": 0.08},
    {"pattern": "repetitive",     "weight": 0.09},
    {"pattern": "homogeneous",    "weight": 0.08},
]


def score_stylometry(query: str) -> Dict[str, Any]:
    """Estimate AI-generation probability from a project description.

    Returns ``probability`` (0-1), matched ``cues``, and ``verdict``.
    """
    q = query.lower()
    prob = sum(c["weight"] for c in _STYLOMETRY_CUES if c["pattern"] in q)
    prob = min(1.0, prob)
    if prob >= 0.6:
        verdict = "high_ai_probability"
    elif prob >= 0.3:
        verdict = "moderate_ai_probability"
    elif prob >= 0.1:
        verdict = "low_ai_probability"
    else:
        verdict = "likely_human_authored"
    return {
        "probability": round(prob, 3),
        "verdict": verdict,
        "cues_matched": [c["pattern"] for c in _STYLOMETRY_CUES if c["pattern"] in q],
    }


# =====================================================================
# 6  METACOGNITIVE PROMPTING WORKFLOW
# =====================================================================

METACOGNITIVE_WORKFLOW: List[Dict[str, str]] = [
    {
        "step": "1_analyze",
        "name": "Analyze the Input",
        "instruction": (
            "Review AST paths, stylometric metrics, and historical runtime "
            "logs. Map the structural entropy and identify which of the "
            "Four Horsemen are present."
        ),
        "anti_pattern": (
            "Skipping analysis and jumping straight to code generation — "
            "the defining error of unchecked vibe coding."
        ),
    },
    {
        "step": "2_initial_judgment",
        "name": "Make an Initial Judgment",
        "instruction": (
            "Formulate a preliminary hypothesis regarding the root "
            "architectural flaw.  Reference specific AST nodes, file "
            "paths, and dependency chains."
        ),
        "anti_pattern": (
            "Generating a generic 'fix everything' patch without localizing "
            "the root cause."
        ),
    },
    {
        "step": "3_critical_evaluation",
        "name": "Critically Self-Evaluate",
        "instruction": (
            "Challenge your own assumptions: 'Could this hypothesis be "
            "wrong? What alternative architectural flaws could cause this "
            "symptom, and how does this patch impact global state?'"
        ),
        "anti_pattern": (
            "Overconfident single-hypothesis reasoning — the hallucination "
            "trap that produces plausible but logically flawed patches."
        ),
    },
    {
        "step": "4_propose",
        "name": "Propose Final Answer",
        "instruction": (
            "Synthesize a final architectural patch based on self-critique. "
            "Express as targeted LibCST node modifications. Validate against "
            "repository-level semantic graph."
        ),
        "anti_pattern": (
            "Proposing cosmetic fixes that mask symptoms rather than "
            "addressing structural root causes."
        ),
    },
    {
        "step": "5_confidence",
        "name": "State Confidence Calibration",
        "instruction": (
            "Output a calibrated confidence score (0-1) and explain "
            "reasoning alongside the proposed modifications. Flag "
            "uncertainty explicitly."
        ),
        "anti_pattern": (
            "Presenting AI-generated patches as certainties — the "
            "'confident falsity' hallucination class."
        ),
    },
]


def get_metacognitive_workflow() -> List[Dict[str, str]]:
    """Return the five-step metacognitive prompting workflow."""
    return METACOGNITIVE_WORKFLOW


# =====================================================================
# 7  ANALYZE → PATCH → VERIFY → PROPOSE (APVP) CYCLE
# =====================================================================

APVP_CYCLE: Dict[str, Any] = {
    "name": "Analyze → Patch → Verify → Propose",
    "description": (
        "The autonomous self-healing loop for vibe-coded architectures.  "
        "Continuously runs: structural analysis → LLM patch generation → "
        "isolated sandbox verification → PR/commit proposal.  Failed "
        "verifications re-enter the metacognitive prompting loop."
    ),
    "phases": [
        {
            "phase": "analyze",
            "actions": [
                "Parse source into AST / LibCST",
                "Calculate cyclomatic complexity and coupling metrics",
                "Run stylometry to detect AI-generation probability",
                "Query FAISS embeddings for cross-file impacts",
                "Detect Four Horsemen pathology signals",
            ],
        },
        {
            "phase": "patch",
            "actions": [
                "Initiate metacognitive prompting workflow",
                "Generate targeted LibCST node modifications",
                "Auto-generate pytest stubs from AST node enumeration",
                "Validate against repository Data Flow Graph",
            ],
        },
        {
            "phase": "verify",
            "actions": [
                "Provision ephemeral sandbox (E2B / Docker / Pyodide / Firecracker)",
                "Load proposed code modifications into sandbox",
                "Execute auto-generated test suite",
                "Check AST complexity regression vs. pre-patch baseline",
                "Run GoodVibe security judge model",
            ],
        },
        {
            "phase": "propose",
            "actions": [
                "On pass: package into automated PR to staging branch",
                "Attach confidence score, AST diff, and test report",
                "On fail: pipe stderr + failure context into metacognitive loop",
                "Iterate until tests unequivocally pass",
                "Log healing event for drift monitoring",
            ],
        },
    ],
}


def get_apvp_cycle() -> Dict[str, Any]:
    """Return the Analyze→Patch→Verify→Propose self-healing cycle."""
    return APVP_CYCLE


# =====================================================================
# 8  SELF-HEALING ECONOMICS & SYSTEMIC RISKS
# =====================================================================

SYSTEMIC_RISKS: List[Dict[str, Any]] = [
    {
        "id": "infinite_regression",
        "name": "Infinite Automated Regression Loops",
        "severity": "critical",
        "description": (
            "LLM identifies a symptom (e.g., /tmp filling up) but lacks "
            "deep context to solve the root cause.  Implements a cron to "
            "delete files every 5 minutes rather than fixing the memory leak. "
            "System 'heals' the immediate error but masks a fatal flaw."
        ),
        "mitigation": (
            "Bound healing loop iterations (max_retries).  Require root-cause "
            "hypothesis in metacognitive step 2 before any patch is generated. "
            "Escalate to human-in-the-loop after 3 failed iterations."
        ),
    },
    {
        "id": "cost_explosion",
        "name": "Unbounded Cost Escalation",
        "severity": "critical",
        "description": (
            "Self-healing system solves performance issues by autonomously "
            "spinning up cloud resources or scaling clusters.  Without "
            "financial guardrails, can literally bankrupt the organization "
            "within days."
        ),
        "mitigation": (
            "Implement declarative Policy-as-Code resource quotas.  Set "
            "hard cost ceilings per healing iteration.  Require human "
            "approval for any resource provisioning above threshold."
        ),
    },
    {
        "id": "architectural_drift",
        "name": "Context Degradation / Architectural Drift",
        "severity": "high",
        "description": (
            "As AI continuously patches and refactors, the architecture "
            "drifts from human readability.  AI favors giant cohesive "
            "domain modules over traditional deep abstractions.  Human "
            "team finds repository incomprehensible."
        ),
        "mitigation": (
            "Enforce readability metrics (max function length, max "
            "cyclomatic complexity).  Require human review for patches "
            "exceeding drift threshold.  Maintain architectural decision "
            "records (ADRs) for all autonomous changes."
        ),
    },
    {
        "id": "catastrophic_loop_failure",
        "name": "Catastrophic Self-Healing Failure",
        "severity": "critical",
        "description": (
            "If the self-healing loop itself experiences a failure, or a "
            "novel business requirement exceeds the AI's comprehension, "
            "human developers cannot intervene — the codebase has "
            "irreversibly evolved into an alien, silicon-based artifact."
        ),
        "mitigation": (
            "Maintain immutable snapshots before each autonomous healing "
            "event.  Implement kill-switch to disable autonomous patching. "
            "Keep human-readable documentation synchronized via LLM "
            "summarization after each change."
        ),
    },
]


def get_systemic_risks() -> List[Dict[str, Any]]:
    """Return the systemic risks of autonomous self-healing."""
    return SYSTEMIC_RISKS


def assess_healing_economics(query: str) -> Dict[str, Any]:
    """Assess whether a project has adequate guardrails for self-healing.

    Returns risk profile, detected safeguards, and warnings.
    """
    q = query.lower()

    safeguards: List[str] = []
    _sg = [
        ("cost ceiling", "cost_ceiling"),
        ("resource quota", "resource_quota"),
        ("policy-as-code", "policy_as_code"),
        ("kill switch", "kill_switch"),
        ("max retries", "max_retries"),
        ("human review", "human_review"),
        ("human-in-the-loop", "hitl"),
        ("adr", "decision_records"),
        ("snapshot", "immutable_snapshots"),
        ("rollback", "rollback_capability"),
    ]
    for pattern, name in _sg:
        if pattern in q:
            safeguards.append(name)

    risk_factors: List[str] = []
    _rf = [
        ("autonomous", "autonomous_patching"),
        ("self-heal", "self_healing_enabled"),
        ("auto scale", "auto_scaling"),
        ("no limit", "unbounded"),
        ("unrestricted", "unrestricted_access"),
        ("no oversight", "no_oversight"),
    ]
    for pattern, name in _rf:
        if pattern in q:
            risk_factors.append(name)

    # Overall risk
    if risk_factors and not safeguards:
        overall = "dangerous"
    elif len(risk_factors) > len(safeguards):
        overall = "risky"
    elif safeguards:
        overall = "guarded"
    else:
        overall = "neutral"

    warnings: List[str] = []
    if "autonomous" in q and "human" not in q:
        warnings.append(
            "Autonomous patching detected without human-in-the-loop — "
            "risk of infinite regression and cost explosion."
        )
    if "self-heal" in q and "snapshot" not in q and "rollback" not in q:
        warnings.append(
            "Self-healing enabled without immutable snapshots — "
            "catastrophic loop failure cannot be reversed."
        )

    return {
        "overall_risk": overall,
        "safeguards_detected": safeguards,
        "risk_factors": risk_factors,
        "warnings": warnings,
        "systemic_risks": [r["name"] for r in SYSTEMIC_RISKS],
    }


# =====================================================================
# 9  GOODVIBE SECURITY POSTURE
# =====================================================================

GOODVIBE_FRAMEWORK: Dict[str, Any] = {
    "name": "GoodVibe Security-by-Vibe Framework",
    "approach": (
        "Recasts security analysis as a supervised evaluation task.  "
        "Identifies security-critical neurons within the LLM and optimizes "
        "them through cluster-based fine-tuning.  Achieves matching "
        "performance with 4,700× fewer trainable parameters than full "
        "fine-tuning."
    ),
    "dual_model_architecture": {
        "primary_model": (
            "Large-parameter LLM generating functional code and "
            "refactoring patches."
        ),
        "judge_model": (
            "Efficient model fine-tuned on security-critical neuron subset "
            "via GoodVibe methodology — acts as uncompromising security auditor."
        ),
    },
    "vulnerability_patterns_scanned": [
        "Unparameterized SQL queries",
        "Exposed API keys / hardcoded secrets",
        "Cross-site scripting (XSS)",
        "Flawed authentication logic",
        "Missing input sanitization",
        "Insecure deserialization",
        "Path traversal",
        "Command injection",
    ],
    "remediation_loop": (
        "Judge model detects vulnerability → calculates risk impact → "
        "routes specific AST node back to primary metacognitive generator "
        "with deterministic remediation instructions → creates closed-loop "
        "DevSecOps pipeline."
    ),
}


def get_goodvibe_framework() -> Dict[str, Any]:
    """Return the GoodVibe security-by-vibe framework details."""
    return GOODVIBE_FRAMEWORK


# =====================================================================
# 10  ARCHITECTURAL DRIFT MONITORING
# =====================================================================

def assess_drift_risk(query: str) -> Dict[str, Any]:
    """Assess architectural-drift risk based on project description.

    Returns drift_level, indicators, and recommended countermeasures.
    """
    q = query.lower()
    drift_indicators: List[str] = []
    countermeasures: List[str] = []

    _drift = [
        ("no documentation", "missing_docs"),
        ("no adr", "no_decision_records"),
        ("autonomous refactor", "unreviewed_auto_refactor"),
        ("giant module", "module_bloat"),
        ("incomprehensible", "readability_collapse"),
        ("alien code", "alien_artifact"),
        ("no human review", "no_review_gate"),
        ("frequent auto-patch", "high_patch_frequency"),
        ("context window", "context_degradation"),
        ("silicon-based", "ai_native_drift"),
    ]
    for pattern, indicator in _drift:
        if pattern in q:
            drift_indicators.append(indicator)

    if drift_indicators:
        countermeasures = [
            "Enforce max function length (50 lines) and max cyclomatic complexity (10)",
            "Maintain Architecture Decision Records (ADRs) for all autonomous changes",
            "Run readability metrics (Halstead, maintainability index) as CI gate",
            "Require human approval for patches modifying >3 files",
            "Keep immutable snapshots before each healing event",
            "Synchronize human-readable documentation via LLM summarization",
        ]

    n = len(drift_indicators)
    if n >= 4:
        level = "critical"
    elif n >= 2:
        level = "high"
    elif n >= 1:
        level = "moderate"
    else:
        level = "low"

    return {
        "drift_level": level,
        "indicators": drift_indicators,
        "countermeasures": countermeasures[:n + 2] if countermeasures else [],
    }


# =====================================================================
# 11  RACG — Retrieval-Augmented Code Generation guidance
# =====================================================================

RACG_ARCHITECTURE: Dict[str, Any] = {
    "name": "Retrieval-Augmented Code Generation (RACG)",
    "purpose": (
        "Overcomes contextual myopia of standard vibe coding by giving "
        "the AI persistent, holistic memory of the entire repository."
    ),
    "components": [
        {
            "name": "CodeBERT Embedding Layer",
            "role": (
                "Generates dense vector representations of every file, "
                "function, class, and docstring in the repository."
            ),
        },
        {
            "name": "FAISS Vector Index",
            "role": (
                "Indexes multi-dimensional embeddings for high-performance "
                "cosine-similarity retrieval using InfoNCE loss."
            ),
        },
        {
            "name": "Global Data Flow Graph / AST-Graph",
            "role": (
                "Mathematically maps relationships between all modules so "
                "changes in one file are structurally aware of downstream "
                "impacts in other files."
            ),
        },
        {
            "name": "Dynamic Model Router",
            "role": (
                "Normalizes proposed changes against the global repository "
                "graph via learned cost-aware selection."
            ),
        },
    ],
    "anti_pattern": (
        "Providing the LLM with the entire repository in a massive context "
        "window — yields limited gains and worsens performance through "
        "severe noise and attention diffusion."
    ),
}


def get_racg_architecture() -> Dict[str, Any]:
    """Return RACG architecture guidance."""
    return RACG_ARCHITECTURE


# =====================================================================
# 12  MASTER METACOGNITION ASSESSMENT
# =====================================================================

def assess_metacognition(query: str) -> Dict[str, Any]:
    """Run all metacognition subsystems for a query and return a unified
    assessment combining pathology, entropy, stylometry, layers, sandbox,
    security, drift, and economics."""

    pathology = detect_pathologies(query)
    entropy = score_structural_entropy(query)
    stylometry = score_stylometry(query)
    layers = recommend_layers(query)
    sandbox = recommend_sandbox_for_verification(query)
    drift = assess_drift_risk(query)
    economics = assess_healing_economics(query)

    # Composite self-awareness score
    # Penalize: entropy + bankruptcy + drift + stylometry
    # Reward: detected safeguards
    penalty = (
        entropy["entropy_score"] * 0.3
        + pathology["bankruptcy_risk"] * 0.3
        + stylometry["probability"] * 0.2
        + (0.15 if drift["drift_level"] in ("high", "critical") else 0.0)
    )
    reward = len(economics.get("safeguards_detected", [])) * 0.05
    awareness = max(0.0, min(1.0, 1.0 - penalty + reward))

    if awareness >= 0.85:
        grade = "A"
    elif awareness >= 0.70:
        grade = "B"
    elif awareness >= 0.50:
        grade = "C"
    elif awareness >= 0.30:
        grade = "D"
    else:
        grade = "F"

    warnings: List[str] = []
    if pathology["flags"]:
        warnings.append(
            f"Four Horsemen detected: {', '.join(pathology['flags'])}"
        )
    if entropy["status"] in ("high_entropy", "technical_bankruptcy"):
        warnings.append(
            f"Structural entropy: {entropy['status']} "
            f"(score {entropy['entropy_score']})"
        )
    if stylometry["verdict"] == "high_ai_probability":
        warnings.append(
            f"High AI-generation probability ({stylometry['probability']}) — "
            "mandatory metacognitive review before deployment"
        )
    if drift["drift_level"] in ("high", "critical"):
        warnings.append(
            f"Architectural drift: {drift['drift_level']} — "
            f"{len(drift['indicators'])} indicators detected"
        )
    warnings.extend(economics.get("warnings", []))

    assessment = MetacognitionAssessment(
        query=query,
        self_awareness_score=awareness,
        grade=grade,
        pathology_flags=pathology["flags"],
        bankruptcy_risk=pathology["bankruptcy_risk"],
        recommended_layers=[l["name"] for l in layers[:4]],
        sandbox_recommendation=sandbox["recommended"]["name"],
        security_posture=economics.get("overall_risk", "neutral"),
        drift_risk=drift["drift_level"],
        healing_loop_bounded=bool(economics.get("safeguards_detected")),
        stylometry_probability=stylometry["probability"],
        metacognitive_steps=[s["name"] for s in METACOGNITIVE_WORKFLOW],
        warnings=warnings,
    )

    return assessment.to_dict()
