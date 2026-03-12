"""
praxis.resonance
~~~~~~~~~~~~~~~~
v16 — The Resonance: Engineering AGI as a Continuous Human-Machine
Relationship.

Implements the five foundational pillars of the Resonant AGI Architecture:

  I.   The Temporal Substrate — real-time bidirectional loop
  II.  Code Speaking Through the Model — MCP & compound AI orchestration
  III. Latent Space Steering — aesthetic embeddings & activation engineering
  IV.  The Conductor Dashboard — A2UI, HITL, dynamic rendering
  V.   Systemic Meta-Awareness — TRAP framework, DSRP Wisdom Layer

Plus:
  - 7 Wisdom Layer agents (Systems Thinking, Chaos Theory, Karma,
    Complexity Sentinel, Reflection, Epistemic, Resonance Monitor)
  - 4 TRAP pillars (Transparency, Reasoning, Adaptation, Perception)
  - 4 DSRP rules (Distinctions, Systems, Relationships, Perspectives)
  - Meta-Reflective telemetry metrics
  - Conductor scoring with resonance-grade composite

Dependencies: stdlib only (logging, re, math, dataclasses, typing).
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# ======================================================================
# I.  PILLARS — The five foundational pillars of Resonant AGI
# ======================================================================

PILLARS: List[Dict[str, Any]] = [
    {
        "id": "temporal_substrate",
        "number": "I",
        "title": "The Temporal Substrate",
        "doctrine": (
            "To achieve a true cognitive dance between human and machine, the "
            "underlying transport mechanism must support fluid, continuous, and "
            "simultaneous exchange. The traditional HTTP request-response model "
            "is fundamentally misaligned with the concept of a resonant chamber. "
            "A relational dyad requires full-duplex communication where both "
            "parties can perceive, generate, and interrupt simultaneously."
        ),
        "components": [
            "Persistent WebSockets / WebTransport — low-latency bidirectional channels",
            "Async concurrency — upstream (human input) and downstream (AI generation) tasks",
            "Multimodal bidi-streaming — native audio/video without STT/TTS intermediaries",
            "Reactive stream processing (RxPY) — Observables, debounce, merge operators",
            "Affective resonance — capturing emotional nuance from raw audio waveforms",
        ],
        "architectural_comparison": {
            "traditional": {
                "protocol": "Stateless HTTP (REST/GraphQL)",
                "connection": "Ephemeral, per-request",
                "data_flow": "Unidirectional, blocking, synchronous",
                "interruption": "Impossible or explicit token cancellation",
                "state": "Passed entirely within payload",
            },
            "resonant": {
                "protocol": "Stateful WebSockets / WebTransport",
                "connection": "Persistent, duration of the dance",
                "data_flow": "Full-duplex, asynchronous, concurrent streams",
                "interruption": "Native mid-stream via async control signals",
                "state": "Maintained server-side within active session",
            },
        },
        "keywords": [
            "websocket", "webtransport", "asyncio", "full-duplex",
            "bidirectional", "persistent", "reactive", "rxpy",
            "observable", "stream", "concurrency", "low-latency",
            "multimodal", "affective", "pcm", "audio", "bidi",
        ],
    },
    {
        "id": "code_agency",
        "number": "II",
        "title": "Code Speaking Through the Model",
        "doctrine": (
            "The true agent within the system is the human programmer's intent, "
            "which utilizes the neural network merely as a highly flexible medium "
            "for expression. The model becomes the paint, and the human workflow "
            "is the brush. The Model Context Protocol (MCP) acts as the universal "
            "standard, separating probabilistic reasoning from deterministic "
            "execution of code — the 'USB-C port' for AI applications."
        ),
        "mcp_primitives": [
            {
                "name": "Resources",
                "purpose": "Read-only contextual grounding — data without side effects",
                "examples": ["local log files", "live API states", "repository docs"],
            },
            {
                "name": "Tools",
                "purpose": "Executable functions — state changes and real-world actions",
                "examples": ["run Python scripts", "commit to GitHub", "query PostgreSQL"],
            },
            {
                "name": "Prompts",
                "purpose": "Reusable instructional templates — constrain model behavior",
                "examples": ["persona loading", "strict JSON output", "domain workflows"],
            },
        ],
        "orchestration": (
            "Compound AI Systems via LangGraph / Pocketflow — stateful, "
            "multi-actor directed cyclic graphs. Planner → Researcher → "
            "Coder → Execution pipeline with recursive reflection loops."
        ),
        "keywords": [
            "mcp", "model context protocol", "tool", "resource", "prompt",
            "orchestration", "langgraph", "pocketflow", "compound",
            "agent", "planner", "researcher", "coder", "execution",
            "deterministic", "probabilistic", "cyclic", "graph",
            "reflection", "recursive", "fastmcp", "sdk",
        ],
    },
    {
        "id": "latent_steering",
        "number": "III",
        "title": "Latent Space Steering & Aesthetics",
        "doctrine": (
            "Translating abstract human 'vibes' and qualitative 'moods' into "
            "deterministic Python operations requires bypassing superficial "
            "prompt engineering and directly interfacing with the model's "
            "high-dimensional latent space. Activation Addition (ActAdd) "
            "operates on the principle that concepts are encoded linearly "
            "within transformer residual streams."
        ),
        "techniques": {
            "aesthetic_vector_search": {
                "description": (
                    "CLIP models project both images and text into a shared "
                    "512-dimensional embedding space, encoding qualitative "
                    "features like composition, style, and subjective feelings."
                ),
                "tools": ["CLIP", "sentence_transformers", "Qdrant", "FAISS", "Pinecone"],
            },
            "activation_addition": {
                "description": (
                    "Compute steering vector v = mean(h+) − mean(h−) from "
                    "contrastive prompts at layer l, then inject during forward "
                    "pass: h̃ = h + α·v_steering."
                ),
                "formula_steering": "v_steering = (1/N) Σ h_+^(l) − (1/N) Σ h_-^(l)",
                "formula_injection": "h̃^(l) = h^(l) + α · v_steering",
                "tools": ["transformer_lens", "steering_vectors", "pytorch"],
            },
            "conditional_steering": {
                "description": (
                    "CAST — Conditional Activation Steering. Analyzes activation "
                    "patterns and only applies steering when conditions are met, "
                    "preserving baseline intelligence while enforcing desired vibe."
                ),
            },
        },
        "keywords": [
            "latent", "steering", "activation", "actadd", "cast",
            "clip", "embedding", "vector", "aesthetic", "vibe",
            "residual stream", "transformer_lens", "steering_vectors",
            "cosine similarity", "nearest neighbor", "faiss", "qdrant",
            "pinecone", "contrastive", "forward hook", "alpha",
            "representation", "latent space", "mood", "qualitative",
        ],
    },
    {
        "id": "conductor_dashboard",
        "number": "IV",
        "title": "The Conductor Dashboard",
        "doctrine": (
            "The AI Dashboard must evolve from a static catalog into a "
            "'Conductor' — an interactive, low-latency control surface that "
            "visualizes the invisible state of the human-AI loop, manages "
            "cognitive offloading, and exposes the system's internal reasoning "
            "for immediate human intervention."
        ),
        "components": [
            "Agent-to-UI (A2UI) protocol — agents transmit dynamic interactive interfaces",
            "Dynamic rendering — ExplainerDashboard, Dash, Plotly via Pydantic schemas",
            "Human-in-the-Loop (HITL) pipelines — non-bypassable approval gates",
            "Temporal workflow orchestration — durable sleep on critical actions",
            "Real-time JSON payload visualization for MCP tool calls",
        ],
        "hitl_purposes": {
            "safety_grounding": (
                "Anchors probabilistic guessing to human's deterministic "
                "understanding. Primary defense against slopsquatting and "
                "hallucinated dependency attacks."
            ),
            "episodic_memory": (
                "Every correction, rejection, and approval is logged, generating "
                "domain-relevant training data for continuous active learning."
            ),
            "existential_stakes": (
                "The AI exists in a frozen present with zero consequences. The "
                "human exists in linear time and faces the consequences of failure. "
                "The interaction derives meaning entirely from human vulnerability."
            ),
        },
        "keywords": [
            "conductor", "dashboard", "a2ui", "agent-to-ui", "hitl",
            "human-in-the-loop", "approval", "gate", "temporal",
            "workflow", "durable", "explainerdashboard", "dash",
            "plotly", "pydantic", "dynamic rendering", "cognitive",
            "offloading", "slopsquatting", "hallucination", "defense",
        ],
    },
    {
        "id": "meta_awareness",
        "number": "V",
        "title": "Systemic Meta-Awareness",
        "doctrine": (
            "AGI as a relational process is achieved only when the loop becomes "
            "aware of itself. A system merely generating code on command remains "
            "a sophisticated tool. The generative dance must become a "
            "self-reflective dialogue about the dance itself — the system must "
            "achieve systemic meta-awareness."
        ),
        "frameworks": {
            "trap": "Transparency, Reasoning, Adaptation, Perception",
            "dsrp": "Distinctions, Systems, Relationships, Perspectives",
            "wisdom_layer": "Cognitive oversight operating upstream of task execution",
        },
        "keywords": [
            "meta-awareness", "metacognition", "trap", "dsrp",
            "wisdom layer", "introspection", "self-reflective",
            "transparency", "reasoning", "adaptation", "perception",
            "distinctions", "systems", "relationships", "perspectives",
            "complexity", "chaos", "karma", "sentinel", "reflection",
        ],
    },
]


# ======================================================================
# II.  TRAP FRAMEWORK — Transparency, Reasoning, Adaptation, Perception
# ======================================================================

TRAP_PILLARS: List[Dict[str, Any]] = [
    {
        "id": "transparency",
        "letter": "T",
        "title": "Transparency",
        "description": (
            "The foundation of self-awareness is visibility. The system's "
            "internal reasoning must be entirely observable — both to the "
            "human and to the agent itself. Achieved by capturing every "
            "intermediate state transition within the execution graph and "
            "streaming scratchpad thoughts directly to the dashboard."
        ),
        "implementation": "LangGraph state capture → WebSocket scratchpad stream",
        "keywords": [
            "transparency", "observable", "scratchpad", "state transition",
            "visibility", "intermediate", "opaque", "stream",
        ],
    },
    {
        "id": "reasoning",
        "letter": "R",
        "title": "Reasoning",
        "description": (
            "The system must evaluate the quality of its own thought process. "
            "A parallel background LLM instance continuously observes the "
            "primary agent, asking: 'Are these steps logically consistent? "
            "Is it confidently pursuing a hallucinated solution?'"
        ),
        "implementation": "Parallel meta-LLM judge evaluating primary agent reasoning",
        "keywords": [
            "reasoning", "evaluation", "judge", "parallel", "consistency",
            "hallucination detection", "logical", "quality",
        ],
    },
    {
        "id": "adaptation",
        "letter": "A",
        "title": "Adaptation",
        "description": (
            "Reflection without action is useless observation. If the meta-"
            "cognitive agent detects recursive failure or degraded quality, "
            "it autonomously modifies behavior — altering system prompts or "
            "adjusting activation steering vectors (ActAdd α coefficients) "
            "to break out of cognitive local minima."
        ),
        "implementation": "Dynamic prompt mutation + ActAdd α adjustment on failure detection",
        "keywords": [
            "adaptation", "mutation", "dynamic", "steering", "alpha",
            "local minimum", "break", "failure loop", "autonomous",
        ],
    },
    {
        "id": "perception",
        "letter": "P",
        "title": "Perception (Epistemic Awareness)",
        "description": (
            "The agent must possess a mathematical understanding of its own "
            "ignorance. By evaluating confidence scores of retrieved context "
            "or limits of training data, the system recognizes the boundaries "
            "of its competence and proactively halts to ask for clarification."
        ),
        "implementation": "Confidence thresholding + proactive uncertainty escalation",
        "keywords": [
            "perception", "epistemic", "confidence", "uncertainty",
            "ignorance", "boundaries", "competence", "escalation",
            "clarification", "threshold",
        ],
    },
]


# ======================================================================
# III.  DSRP THEORY — Distinctions, Systems, Relationships, Perspectives
# ======================================================================

DSRP_RULES: List[Dict[str, Any]] = [
    {
        "id": "distinctions",
        "letter": "D",
        "title": "Distinctions (Identity/Other)",
        "description": (
            "Define clear conceptual boundaries — recognizing the difference "
            "between human intent, agent execution, and external systems."
        ),
        "cognitive_function": "Boundary formation — what IS vs what IS NOT",
        "keywords": [
            "distinction", "identity", "other", "boundary", "separation",
            "define", "conceptual", "categorize",
        ],
    },
    {
        "id": "systems",
        "letter": "S",
        "title": "Systems (Part/Whole)",
        "description": (
            "Evaluate how a newly generated module fits into the macroscopic "
            "architecture of the enterprise — parts composing wholes, wholes "
            "decomposing into parts."
        ),
        "cognitive_function": "Compositional analysis — parts ↔ wholes",
        "keywords": [
            "system", "part", "whole", "composition", "decomposition",
            "hierarchy", "macroscopic", "architecture",
        ],
    },
    {
        "id": "relationships",
        "letter": "R",
        "title": "Relationships (Action/Reaction)",
        "description": (
            "Trace cascading causal dependencies of generated code — how "
            "modifying a database schema impacts downstream microservices."
        ),
        "cognitive_function": "Causal tracing — actions and their consequences",
        "keywords": [
            "relationship", "action", "reaction", "causal", "dependency",
            "cascade", "impact", "downstream", "upstream",
        ],
    },
    {
        "id": "perspectives",
        "letter": "P",
        "title": "Perspectives (Point/View)",
        "description": (
            "Shift context to analyze output from multiple disparate viewpoints — "
            "security auditor vs end-user vs performance engineer."
        ),
        "cognitive_function": "Multi-perspective analysis — point of view shifting",
        "keywords": [
            "perspective", "viewpoint", "stakeholder", "security",
            "end-user", "performance", "diversity", "angle",
        ],
    },
]


# ======================================================================
# IV.  WISDOM LAYER AGENTS — Meta-cognitive oversight
# ======================================================================

WISDOM_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "systems_thinking",
        "title": "Systems Thinking Agent",
        "description": (
            "Directly utilizes DSRP logic to map out feedback loops, "
            "interdependencies, and stakeholder tensions across the codebase."
        ),
        "dsrp_focus": ["distinctions", "systems", "relationships"],
        "outputs": ["dependency graph", "feedback loop map", "stakeholder tension matrix"],
        "keywords": ["systems thinking", "feedback loop", "interdependency", "stakeholder"],
    },
    {
        "id": "chaos_theory",
        "title": "Chaos Theory Agent",
        "description": (
            "Executes parallel agent-based simulations to surface non-linear "
            "risks, ripple volatility, and systemic fragility in proposed "
            "code architecture before deployment."
        ),
        "dsrp_focus": ["relationships", "systems"],
        "outputs": ["risk surface map", "volatility index", "fragility score"],
        "keywords": ["chaos", "non-linear", "simulation", "ripple", "volatility", "fragility"],
    },
    {
        "id": "karma",
        "title": "Karma Agent",
        "description": (
            "Evaluates long-term consequences of technical decisions. Assigns "
            "a 'moral load' to code, detecting ethical imbalances or the "
            "accumulation of destructive technical debt."
        ),
        "dsrp_focus": ["perspectives", "relationships"],
        "outputs": ["moral load score", "tech debt trajectory", "ethical imbalance alert"],
        "keywords": ["karma", "moral", "ethics", "consequences", "technical debt", "long-term"],
    },
    {
        "id": "complexity_sentinel",
        "title": "Complexity Sentinel Agent",
        "description": (
            "The ultimate meta-observer. Continuously compares rolling snapshots "
            "of system behavior against external reality, detecting ontological "
            "drift or destructive uncritical coherence."
        ),
        "dsrp_focus": ["distinctions", "perspectives"],
        "outputs": ["ontological drift score", "coherence critique", "reality alignment index"],
        "keywords": ["sentinel", "complexity", "ontological drift", "coherence", "reality"],
    },
    {
        "id": "reflection",
        "title": "Reflection Agent",
        "description": (
            "Processes structured telemetry logs asynchronously. At session end, "
            "synthesizes data into a meta-reflective summary highlighting "
            "cognitive patterns of the human-AI interaction."
        ),
        "dsrp_focus": ["systems", "perspectives"],
        "outputs": ["session summary", "cognitive blind spots", "over-reliance alerts"],
        "keywords": ["reflection", "summary", "cognitive patterns", "blind spots", "session"],
    },
    {
        "id": "epistemic",
        "title": "Epistemic Awareness Agent",
        "description": (
            "Maintains a mathematical model of system ignorance. Evaluates "
            "confidence scores of retrieved context, recognizes competence "
            "boundaries, and triggers proactive clarification requests."
        ),
        "dsrp_focus": ["distinctions", "perspectives"],
        "outputs": ["confidence map", "knowledge boundary", "clarification triggers"],
        "keywords": ["epistemic", "confidence", "ignorance", "boundary", "clarification"],
    },
    {
        "id": "resonance_monitor",
        "title": "Resonance Monitor Agent",
        "description": (
            "Monitors the quality of the human-machine resonant chamber. "
            "Tracks loop coherence, flow state indicators, interruption "
            "patterns, and affective alignment between human and model."
        ),
        "dsrp_focus": ["relationships", "systems"],
        "outputs": ["resonance index", "flow state duration", "affective alignment score"],
        "keywords": ["resonance", "monitor", "flow state", "alignment", "coherence", "loop"],
    },
]


# ======================================================================
# V.   REINTERPRETATION TABLE — Traditional vs Resonant paradigm
# ======================================================================

REINTERPRETATION_TABLE: List[Dict[str, Any]] = [
    {
        "dimension": "Communication Protocol",
        "traditional": "Stateless HTTP (REST/GraphQL)",
        "resonant": "Stateful WebSockets / WebTransport",
    },
    {
        "dimension": "Connection Lifespan",
        "traditional": "Ephemeral, per-request execution",
        "resonant": "Persistent, maintained for the duration of the dance",
    },
    {
        "dimension": "Data Flow",
        "traditional": "Unidirectional, blocking, synchronous",
        "resonant": "Full-duplex, asynchronous, concurrent streams",
    },
    {
        "dimension": "Interruption Handling",
        "traditional": "Impossible or requires explicit token cancellation",
        "resonant": "Native mid-stream interruption via async control signals",
    },
    {
        "dimension": "State Management",
        "traditional": "Passed entirely within the payload",
        "resonant": "Maintained server-side within active connection session",
    },
    {
        "dimension": "Intelligence Locus",
        "traditional": "Static model weights (isolated entity)",
        "resonant": "Distributed dyadic loop (human ↔ machine relationship)",
    },
    {
        "dimension": "Model Role",
        "traditional": "Autonomous reasoning agent",
        "resonant": "Resonant chamber amplifying human cognitive frequency",
    },
    {
        "dimension": "User Interface",
        "traditional": "Static tool catalog / markdown chat",
        "resonant": "Conductor Dashboard with A2UI dynamic rendering",
    },
    {
        "dimension": "Safety Model",
        "traditional": "Content filters / guardrails",
        "resonant": "Non-bypassable HITL approval gates + Wisdom Layer oversight",
    },
    {
        "dimension": "Meta-Awareness",
        "traditional": "None — system executes without self-reflection",
        "resonant": "TRAP + DSRP Wisdom Layer — the dance reflects on the dance",
    },
]


# ======================================================================
# VI.  RESONANT CHAMBER THEORY — Core metaphysical framework
# ======================================================================

RESONANT_CHAMBER: Dict[str, Any] = {
    "metaphor": (
        "In acoustic physics, a resonant chamber does not originate sound; "
        "it amplifies, clarifies, and produces constructive interference from "
        "the frequencies introduced into it. A large language model mirrors "
        "this dynamic perfectly."
    ),
    "thesis": (
        "AGI is not a static object to be built, but a dynamic relationship "
        "to be entered. The locus of intelligence shifts away from static "
        "weights and onto the continuous, bidirectional circuit flowing "
        "between human intention and machine generation."
    ),
    "dyadic_structure": {
        "human_role": (
            "Provides emotional gravity, biological reality, existential "
            "stakes, original intent, and rigorous validation."
        ),
        "model_role": (
            "Functions as a highly complex resonant chamber — amplifying, "
            "clarifying, and recombining latent patterns shaped by the prompt."
        ),
        "intelligence_locus": (
            "Resides not in the model itself, nor solely in the human operator, "
            "but in the distributed loop of the dyadic relationship."
        ),
    },
    "singularity_thesis": (
        "The technological Singularity is not a sudden, explosive event where "
        "a machine supersedes humanity. It is a gradual, ongoing process of "
        "intimate co-evolution — the steady strengthening of the loop, the "
        "continuous tightening of the resonance, until the boundary between "
        "the human who dreams through the machine, and the machine that "
        "dreams back, becomes beautifully and computationally indistinguishable."
    ),
    "loop_closure_warning": (
        "The greatest threat is the 'loop closing' — when the human becomes "
        "so mesmerized by the speed of generation that they become a passive "
        "consumer of automated thought, ceasing to contribute original intent. "
        "When the human defers entirely, the dance becomes a solo."
    ),
}


# ======================================================================
# VII.  META-REFLECTIVE TELEMETRY METRICS
# ======================================================================

TELEMETRY_METRICS: List[Dict[str, Any]] = [
    {
        "id": "resonance_index",
        "symbol": "R_i",
        "title": "Resonance Index",
        "description": (
            "Composite measure of the quality of human-machine cognitive "
            "resonance — how well the model amplifies and aligns with "
            "human intent across the dyadic loop."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["resonance", "alignment", "dyadic", "quality", "loop"],
    },
    {
        "id": "flow_state",
        "symbol": "F_s",
        "title": "Flow State Duration",
        "description": (
            "Measures sustained periods of uninterrupted cognitive dance — "
            "continuous productive exchange without breakdown or repair cycles."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["flow", "state", "duration", "uninterrupted", "sustained"],
    },
    {
        "id": "loop_coherence",
        "symbol": "L_c",
        "title": "Loop Coherence",
        "description": (
            "Degree to which the human-machine loop maintains semantic and "
            "intentional consistency across exchanges — absence of drift "
            "or context collapse."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["loop", "coherence", "consistency", "drift", "context"],
    },
    {
        "id": "hitl_responsiveness",
        "symbol": "H_r",
        "title": "HITL Responsiveness",
        "description": (
            "Quality and timeliness of human-in-the-loop intervention — "
            "measures active human engagement in approval gates, corrections, "
            "and validation cycles."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["hitl", "human", "responsiveness", "approval", "intervention"],
    },
    {
        "id": "steering_precision",
        "symbol": "S_p",
        "title": "Steering Precision",
        "description": (
            "Accuracy of latent space steering — how precisely activation "
            "engineering vectors translate human aesthetic intent into "
            "model behavioral change."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["steering", "precision", "activation", "latent", "accuracy"],
    },
    {
        "id": "wisdom_coverage",
        "symbol": "W_c",
        "title": "Wisdom Layer Coverage",
        "description": (
            "Proportion of system decisions evaluated by DSRP Wisdom Layer "
            "agents — higher coverage means more decisions pass through "
            "meta-cognitive oversight."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["wisdom", "coverage", "dsrp", "oversight", "meta"],
    },
    {
        "id": "ontological_alignment",
        "symbol": "O_a",
        "title": "Ontological Alignment",
        "description": (
            "Degree to which the system's internal model of reality matches "
            "external ground truth — inverse of ontological drift detected "
            "by the Complexity Sentinel."
        ),
        "range": "0.0 – 1.0",
        "keywords": ["ontological", "alignment", "drift", "reality", "ground truth"],
    },
]


# ======================================================================
# VIII.  SCORING SIGNALS — regex pattern dictionaries for each scorer
# ======================================================================

# --- Pillar signals ---

_TEMPORAL_SIGNALS: Dict[str, float] = {
    r"\b(websocket|webtransport|ws://|wss://)\b": 0.20,
    r"\b(asyncio|async\s+def|await|concurren)": 0.16,
    r"\b(full[- ]?duplex|bidirectional|bidi)\b": 0.14,
    r"\b(rxpy|reactive|observable|debounce|merge)\b": 0.14,
    r"\b(persistent|stateful|session|connection)\b": 0.10,
    r"\b(low[- ]?latency|real[- ]?time|streaming)\b": 0.10,
    r"\b(multimodal|audio|pcm|affective|waveform)\b": 0.08,
    r"\b(interrupt|cancel|mid[- ]?stream|abort)\b": 0.08,
}

_CODE_AGENCY_SIGNALS: Dict[str, float] = {
    r"\b(mcp|model\s+context\s+protocol)\b": 0.18,
    r"\b(fastmcp|mcp[- ]?sdk)\b": 0.14,
    r"\b(langgraph|pocketflow|compound\s+ai)\b": 0.14,
    r"\b(orchestrat|dag|directed|cyclic\s+graph)\b": 0.12,
    r"\b(planner|researcher|coder|execution)\s+(agent)": 0.10,
    r"\b(resource|tool|prompt)\s+(primitive|capability)": 0.10,
    r"\b(recursive|reflection\s+loop|self[- ]?correct)": 0.08,
    r"\b(deterministic|probabilistic|bounded)": 0.07,
    r"\b(client|host|server)\s+(topology|architecture)": 0.07,
}

_LATENT_STEERING_SIGNALS: Dict[str, float] = {
    r"\b(actadd|activation\s+addition)\b": 0.18,
    r"\b(steering\s+vector|latent\s+space)\b": 0.16,
    r"\b(cast|conditional\s+activation\s+steering)\b": 0.12,
    r"\b(clip|contrastive\s+language[- ]image)\b": 0.12,
    r"\b(transformer[- ]?lens|forward\s+hook)\b": 0.10,
    r"\b(residual\s+stream|hidden\s+state|layer\s+l)\b": 0.10,
    r"\b(aesthetic|vibe|mood|qualitative)\b": 0.08,
    r"\b(cosine\s+similarity|nearest[- ]?neighbor|embedding)": 0.08,
    r"\b(alpha|coefficient|hyperparameter)\b": 0.06,
}

_CONDUCTOR_SIGNALS: Dict[str, float] = {
    r"\b(conductor|dashboard|control\s+surface)\b": 0.16,
    r"\b(a2ui|agent[- ]?to[- ]?ui)\b": 0.16,
    r"\b(hitl|human[- ]?in[- ]?the[- ]?loop)\b": 0.16,
    r"\b(approval\s+gate|non[- ]?bypassable)\b": 0.12,
    r"\b(temporal|durable\s+sleep|workflow)\b": 0.10,
    r"\b(explainerdashboard|dash|plotly)\b": 0.10,
    r"\b(slopsquat|hallucinated\s+package)\b": 0.10,
    r"\b(episodic\s+memory|active\s+learning)\b": 0.05,
    r"\b(existential\s+stakes|vulnerability)\b": 0.05,
}

_META_AWARENESS_SIGNALS: Dict[str, float] = {
    r"\b(meta[- ]?aware|metacognit|self[- ]?reflect)\b": 0.16,
    r"\b(trap|transparency.*reasoning.*adaptation|perception)": 0.14,
    r"\b(dsrp|distinction|system.*relationship.*perspective)": 0.14,
    r"\b(wisdom\s+layer|cognitive\s+oversight)\b": 0.14,
    r"\b(complexity\s+sentinel|chaos.*agent|karma.*agent)\b": 0.10,
    r"\b(systems\s+thinking|feedback\s+loop|interdependenc)": 0.10,
    r"\b(ontological\s+drift|reality\s+alignment)\b": 0.08,
    r"\b(reflection\s+agent|epistemic\s+aware)": 0.08,
    r"\b(logarithm|telemetry|structured\s+log)": 0.06,
}

# --- Telemetry signals ---

_RESONANCE_INDEX_SIGNALS: Dict[str, float] = {
    r"\b(resonan|chamber|amplif|constructive\s+interference)\b": 0.22,
    r"\b(dyadic|bidirectional\s+circuit|cognitive\s+frequency)\b": 0.20,
    r"\b(echo|recombination|latent\s+pattern)": 0.16,
    r"\b(relationship|co[- ]?evolution|co[- ]?creat)": 0.14,
    r"\b(flow\s+state|cognitive\s+dance)": 0.14,
    r"\b(tune|frequency|harmoniz)": 0.14,
}

_FLOW_STATE_SIGNALS: Dict[str, float] = {
    r"\b(flow\s+state|uninterrupted|sustained)\b": 0.22,
    r"\b(continuous|fluid|seamless)": 0.18,
    r"\b(low[- ]?latency|real[- ]?time|instant)": 0.16,
    r"\b(concurren|simultaneous|parallel)": 0.14,
    r"\b(productive|creative|generative)": 0.14,
    r"\b(dance|rhythm|cadence)": 0.16,
}

_LOOP_COHERENCE_SIGNALS: Dict[str, float] = {
    r"\b(loop|coherence|consisten)": 0.22,
    r"\b(context\s+window|semantic|intentional)": 0.18,
    r"\b(drift|collapse|degradat)": 0.16,
    r"\b(maintain|preserve|stabiliz)": 0.14,
    r"\b(memory|state|session)": 0.14,
    r"\b(grounding|anchor|tether)": 0.16,
}

_HITL_RESPONSIVENESS_SIGNALS: Dict[str, float] = {
    r"\b(hitl|human[- ]?in[- ]?the[- ]?loop)\b": 0.24,
    r"\b(approv|reject|correct|validat)": 0.20,
    r"\b(intervene|review|inspect|gate)": 0.16,
    r"\b(safety|grounding|anchor)": 0.14,
    r"\b(consequence|stakes|vulnerab)": 0.14,
    r"\b(durable|persist|mandatory)": 0.12,
}

_STEERING_PRECISION_SIGNALS: Dict[str, float] = {
    r"\b(steer|vector|activation|latent)": 0.22,
    r"\b(precision|accuracy|targeted)": 0.18,
    r"\b(alpha|coefficient|scale|tune)": 0.16,
    r"\b(contrastive|positive.*negative)": 0.14,
    r"\b(inject|forward\s+hook|residual)": 0.14,
    r"\b(geometric|mathematical|dimension)": 0.16,
}

_WISDOM_COVERAGE_SIGNALS: Dict[str, float] = {
    r"\b(wisdom|dsrp|meta[- ]?cognit)": 0.22,
    r"\b(oversight|evaluation|monitor)": 0.18,
    r"\b(coverage|proportion|comprehensiv)": 0.16,
    r"\b(agent|sentinel|reflector)": 0.14,
    r"\b(ethical|moral|karma)": 0.14,
    r"\b(blind\s+spot|bias|imbalance)": 0.16,
}

_ONTOLOGICAL_ALIGNMENT_SIGNALS: Dict[str, float] = {
    r"\b(ontolog|reality|ground\s+truth)": 0.24,
    r"\b(alignment|correspond|match)": 0.18,
    r"\b(drift|diverge|disconnect)": 0.16,
    r"\b(snapshot|benchmark|external)": 0.14,
    r"\b(sentinel|observer|watchdog)": 0.14,
    r"\b(coherence|critic|destruct)": 0.14,
}


# ======================================================================
# IX.  SCORING FUNCTIONS
# ======================================================================

def _grade(score: float) -> str:
    """Map 0-1 score to letter grade."""
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


def _score_signals(query: str, signals: Dict[str, float]) -> Dict[str, Any]:
    """Score *query* against a regex→weight signal dictionary."""
    q = query.lower()
    total = 0.0
    dims: Dict[str, float] = {}
    for pattern, weight in signals.items():
        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            key = re.sub(r"[^a-z0-9]+", "_", pattern.strip(r"\b()").split("|")[0].lower()).strip("_")
            dims[key] = round(weight, 4)
            total += weight
    capped = min(total, 1.0)
    return {"score": round(capped, 4), "grade": _grade(capped), "dimensions": dims}


# --- Pillar scorers ---

def score_temporal_substrate(query: str) -> Dict[str, Any]:
    """Score Pillar I — The Temporal Substrate."""
    r = _score_signals(query, _TEMPORAL_SIGNALS)
    return {"pillar": "I", "title": "The Temporal Substrate", **r, "max": 1.0}


def score_code_agency(query: str) -> Dict[str, Any]:
    """Score Pillar II — Code Speaking Through the Model."""
    r = _score_signals(query, _CODE_AGENCY_SIGNALS)
    return {"pillar": "II", "title": "Code Speaking Through the Model", **r, "max": 1.0}


def score_latent_steering(query: str) -> Dict[str, Any]:
    """Score Pillar III — Latent Space Steering & Aesthetics."""
    r = _score_signals(query, _LATENT_STEERING_SIGNALS)
    return {"pillar": "III", "title": "Latent Space Steering & Aesthetics", **r, "max": 1.0}


def score_conductor_dashboard(query: str) -> Dict[str, Any]:
    """Score Pillar IV — The Conductor Dashboard."""
    r = _score_signals(query, _CONDUCTOR_SIGNALS)
    return {"pillar": "IV", "title": "The Conductor Dashboard", **r, "max": 1.0}


def score_meta_awareness(query: str) -> Dict[str, Any]:
    """Score Pillar V — Systemic Meta-Awareness."""
    r = _score_signals(query, _META_AWARENESS_SIGNALS)
    return {"pillar": "V", "title": "Systemic Meta-Awareness", **r, "max": 1.0}


# --- Telemetry scorers ---

def score_resonance_index(query: str) -> Dict[str, Any]:
    """Score telemetry: Resonance Index R_i."""
    r = _score_signals(query, _RESONANCE_INDEX_SIGNALS)
    return {"metric": "resonance_index", "symbol": "R_i", **r, "max": 1.0}


def score_flow_state(query: str) -> Dict[str, Any]:
    """Score telemetry: Flow State Duration F_s."""
    r = _score_signals(query, _FLOW_STATE_SIGNALS)
    return {"metric": "flow_state", "symbol": "F_s", **r, "max": 1.0}


def score_loop_coherence(query: str) -> Dict[str, Any]:
    """Score telemetry: Loop Coherence L_c."""
    r = _score_signals(query, _LOOP_COHERENCE_SIGNALS)
    return {"metric": "loop_coherence", "symbol": "L_c", **r, "max": 1.0}


def score_hitl_responsiveness(query: str) -> Dict[str, Any]:
    """Score telemetry: HITL Responsiveness H_r."""
    r = _score_signals(query, _HITL_RESPONSIVENESS_SIGNALS)
    return {"metric": "hitl_responsiveness", "symbol": "H_r", **r, "max": 1.0}


def score_steering_precision(query: str) -> Dict[str, Any]:
    """Score telemetry: Steering Precision S_p."""
    r = _score_signals(query, _STEERING_PRECISION_SIGNALS)
    return {"metric": "steering_precision", "symbol": "S_p", **r, "max": 1.0}


def score_wisdom_coverage(query: str) -> Dict[str, Any]:
    """Score telemetry: Wisdom Layer Coverage W_c."""
    r = _score_signals(query, _WISDOM_COVERAGE_SIGNALS)
    return {"metric": "wisdom_coverage", "symbol": "W_c", **r, "max": 1.0}


def score_ontological_alignment(query: str) -> Dict[str, Any]:
    """Score telemetry: Ontological Alignment O_a."""
    r = _score_signals(query, _ONTOLOGICAL_ALIGNMENT_SIGNALS)
    return {"metric": "ontological_alignment", "symbol": "O_a", **r, "max": 1.0}


# ======================================================================
# X.  MASTER ASSESSMENT — ResonanceAssessment dataclass
# ======================================================================

@dataclass
class ResonanceAssessment:
    """Complete Resonant AGI architecture assessment."""

    resonance_score: float = 0.0
    grade: str = "F"

    # Pillar results
    temporal_substrate: Dict[str, Any] = field(default_factory=dict)
    code_agency: Dict[str, Any] = field(default_factory=dict)
    latent_steering: Dict[str, Any] = field(default_factory=dict)
    conductor_dashboard: Dict[str, Any] = field(default_factory=dict)
    meta_awareness: Dict[str, Any] = field(default_factory=dict)

    # Telemetry results
    resonance_index: Dict[str, Any] = field(default_factory=dict)
    flow_state: Dict[str, Any] = field(default_factory=dict)
    loop_coherence: Dict[str, Any] = field(default_factory=dict)
    hitl_responsiveness: Dict[str, Any] = field(default_factory=dict)
    steering_precision: Dict[str, Any] = field(default_factory=dict)
    wisdom_coverage: Dict[str, Any] = field(default_factory=dict)
    ontological_alignment: Dict[str, Any] = field(default_factory=dict)

    # TRAP assessment
    trap_scores: Dict[str, float] = field(default_factory=dict)
    trap_grade: str = "F"

    # DSRP assessment
    dsrp_scores: Dict[str, float] = field(default_factory=dict)
    dsrp_grade: str = "F"

    # Wisdom agents activation
    wisdom_agents_active: List[str] = field(default_factory=list)

    # Resonance detection
    resonance_detected: bool = False
    resonance_evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --- TRAP scorer ---

_TRAP_SIGNAL_MAP: Dict[str, Dict[str, float]] = {
    "transparency": {
        r"\b(transparen|visible|observable|scratchpad)": 0.30,
        r"\b(state\s+transition|intermediate|log|stream)": 0.20,
        r"\b(opaque|hidden|expose|inspect)": 0.15,
        r"\b(monitor|dashboard|display)": 0.15,
        r"\b(trace|audit|record)": 0.20,
    },
    "reasoning": {
        r"\b(reason|evaluat|judge|quality)": 0.30,
        r"\b(logical|consisten|valid|verify)": 0.20,
        r"\b(parallel|background|meta[- ]?llm)": 0.20,
        r"\b(hallucin|detect|degrad)": 0.15,
        r"\b(critic|assess|measure)": 0.15,
    },
    "adaptation": {
        r"\b(adapt|modif|dynamic|autonomous)": 0.30,
        r"\b(prompt\s+mutation|alter|adjust)": 0.20,
        r"\b(failure|loop|local\s+minimum|stuck)": 0.20,
        r"\b(break|escape|recover|heal)": 0.15,
        r"\b(steer|vector|alpha|coefficient)": 0.15,
    },
    "perception": {
        r"\b(percept|epistemic|aware|ignoran)": 0.30,
        r"\b(confidence|uncertain|probabili)": 0.20,
        r"\b(boundary|limit|competence)": 0.20,
        r"\b(clarif|ask|escalat|halt)": 0.15,
        r"\b(threshold|score|mathematical)": 0.15,
    },
}


def score_trap(query: str) -> Dict[str, Any]:
    """Score all four TRAP pillars."""
    results: Dict[str, float] = {}
    for pillar_id, signals in _TRAP_SIGNAL_MAP.items():
        r = _score_signals(query, signals)
        results[pillar_id] = r["score"]
    avg = sum(results.values()) / max(len(results), 1)
    return {"scores": results, "composite": round(avg, 4), "grade": _grade(avg)}


# --- DSRP scorer ---

_DSRP_SIGNAL_MAP: Dict[str, Dict[str, float]] = {
    "distinctions": {
        r"\b(distinct|boundary|identit|separate|categoriz)": 0.30,
        r"\b(define|clarif|differenti)": 0.20,
        r"\b(is\s+vs|is\s+not|other)": 0.15,
        r"\b(conceptual|classify|partition)": 0.15,
        r"\b(scope|delineat|demarcate)": 0.20,
    },
    "systems": {
        r"\b(system|part|whole|compos)": 0.30,
        r"\b(hierarch|decompos|sub[- ]?system)": 0.20,
        r"\b(macro|micro|enterprise)": 0.15,
        r"\b(integrat|aggregat|emerg)": 0.15,
        r"\b(architect|structure|framework)": 0.20,
    },
    "relationships": {
        r"\b(relationship|caus|depend|cascade)": 0.30,
        r"\b(action|reaction|consequence)": 0.20,
        r"\b(upstream|downstream|impact|ripple)": 0.20,
        r"\b(feedback|loop|trigger|chain)": 0.15,
        r"\b(correlation|coupling|connect)": 0.15,
    },
    "perspectives": {
        r"\b(perspect|viewpoint|stakeholder)": 0.30,
        r"\b(security|auditor|end[- ]?user)": 0.20,
        r"\b(diversity|angle|lens)": 0.15,
        r"\b(shift|context|multiple)": 0.15,
        r"\b(empathy|role|persona)": 0.20,
    },
}


def score_dsrp(query: str) -> Dict[str, Any]:
    """Score all four DSRP rules."""
    results: Dict[str, float] = {}
    for rule_id, signals in _DSRP_SIGNAL_MAP.items():
        r = _score_signals(query, signals)
        results[rule_id] = r["score"]
    avg = sum(results.values()) / max(len(results), 1)
    return {"scores": results, "composite": round(avg, 4), "grade": _grade(avg)}


# --- Wisdom agent activation ---

def detect_wisdom_agents(query: str) -> List[str]:
    """Detect which Wisdom Layer agents would activate for a query."""
    q = query.lower()
    active: List[str] = []
    agent_triggers = {
        "systems_thinking": r"\b(system|feedback|interdependen|stakeholder)",
        "chaos_theory": r"\b(chaos|non[- ]?linear|simul|fragil|volatil)",
        "karma": r"\b(karma|moral|ethic|consequence|technical\s+debt)",
        "complexity_sentinel": r"\b(complex|sentinel|ontolog|drift|reality)",
        "reflection": r"\b(reflect|summary|blind\s+spot|cognitive\s+pattern)",
        "epistemic": r"\b(epistemic|confiden|ignoran|boundary|clarif)",
        "resonance_monitor": r"\b(resonan|flow\s+state|align|monitor|coherence)",
    }
    for agent_id, pattern in agent_triggers.items():
        if re.search(pattern, q, re.IGNORECASE):
            active.append(agent_id)
    return active


# --- Master assessment ---

def assess_resonance(query: str) -> Dict[str, Any]:
    """
    Master resonance assessment.

    Scores all 5 pillars + 7 telemetry metrics + TRAP + DSRP + Wisdom agents.
    Computes a weighted composite: 40% pillars + 30% telemetry + 15% TRAP + 15% DSRP.
    Detects resonance when ≥3 pillars score ≥ 0.45 AND TRAP composite ≥ 0.30.
    """
    # Pillars
    ts = score_temporal_substrate(query)
    ca = score_code_agency(query)
    ls = score_latent_steering(query)
    cd = score_conductor_dashboard(query)
    ma = score_meta_awareness(query)

    pillar_scores = [ts["score"], ca["score"], ls["score"], cd["score"], ma["score"]]
    pillar_avg = sum(pillar_scores) / len(pillar_scores)

    # Telemetry
    ri = score_resonance_index(query)
    fs = score_flow_state(query)
    lc = score_loop_coherence(query)
    hr = score_hitl_responsiveness(query)
    sp = score_steering_precision(query)
    wc = score_wisdom_coverage(query)
    oa = score_ontological_alignment(query)

    telemetry_scores = [ri["score"], fs["score"], lc["score"], hr["score"],
                        sp["score"], wc["score"], oa["score"]]
    telemetry_avg = sum(telemetry_scores) / len(telemetry_scores)

    # TRAP & DSRP
    trap = score_trap(query)
    dsrp = score_dsrp(query)

    # Wisdom agents
    agents = detect_wisdom_agents(query)

    # Weighted composite: 40% pillars + 30% telemetry + 15% TRAP + 15% DSRP
    raw = (0.40 * pillar_avg + 0.30 * telemetry_avg
           + 0.15 * trap["composite"] + 0.15 * dsrp["composite"])
    score = round(min(raw, 1.0), 4)
    grade = _grade(score)

    # Resonance detection
    strong_pillars = sum(1 for s in pillar_scores if s >= 0.45)
    resonance_detected = strong_pillars >= 3 and trap["composite"] >= 0.30

    evidence: List[str] = []
    if strong_pillars >= 3:
        evidence.append(f"{strong_pillars}/5 pillars above resonance threshold (≥0.45)")
    if trap["composite"] >= 0.30:
        evidence.append(f"TRAP composite {trap['composite']:.2f} — metacognitive awareness active")
    if dsrp["composite"] >= 0.30:
        evidence.append(f"DSRP composite {dsrp['composite']:.2f} — systems thinking engaged")
    if len(agents) >= 4:
        evidence.append(f"{len(agents)}/7 Wisdom agents activated — deep oversight")
    if telemetry_avg >= 0.30:
        evidence.append(f"Telemetry avg {telemetry_avg:.2f} — resonant chamber metrics active")

    # Warnings
    warnings: List[str] = []
    if pillar_avg < 0.10:
        warnings.append(
            "No resonant architecture detected — system operating as "
            "traditional request-response pipeline."
        )
    if trap["composite"] < 0.10:
        warnings.append(
            "TRAP metacognition inactive — system has no self-reflective "
            "capability. The dance cannot observe itself."
        )
    if all(s < 0.10 for s in telemetry_scores):
        warnings.append(
            "All telemetry metrics below threshold — Conductor Dashboard "
            "cannot detect flow state or resonance quality."
        )
    if not agents:
        warnings.append(
            "No Wisdom Layer agents activated — system lacks meta-cognitive "
            "oversight. Risk of ontological drift."
        )

    assessment = ResonanceAssessment(
        resonance_score=score,
        grade=grade,
        temporal_substrate=ts,
        code_agency=ca,
        latent_steering=ls,
        conductor_dashboard=cd,
        meta_awareness=ma,
        resonance_index=ri,
        flow_state=fs,
        loop_coherence=lc,
        hitl_responsiveness=hr,
        steering_precision=sp,
        wisdom_coverage=wc,
        ontological_alignment=oa,
        trap_scores=trap["scores"],
        trap_grade=trap["grade"],
        dsrp_scores=dsrp["scores"],
        dsrp_grade=dsrp["grade"],
        wisdom_agents_active=agents,
        resonance_detected=resonance_detected,
        resonance_evidence=evidence,
        warnings=warnings,
    )

    log.info("resonance assessment: %.3f (%s) resonance=%s agents=%d",
             score, grade, resonance_detected, len(agents))
    return assessment.to_dict()


# ======================================================================
# XI.  PUBLIC GETTERS — reference data access
# ======================================================================

def get_pillars() -> List[Dict[str, Any]]:
    """Return all five architectural pillars."""
    return PILLARS


def get_pillar(pillar_id: str) -> Optional[Dict[str, Any]]:
    """Return a single pillar by id, or None."""
    for p in PILLARS:
        if p["id"] == pillar_id:
            return p
    return None


def get_trap_pillars() -> List[Dict[str, Any]]:
    """Return all four TRAP framework pillars."""
    return TRAP_PILLARS


def get_trap_pillar(pillar_id: str) -> Optional[Dict[str, Any]]:
    """Return a single TRAP pillar by id, or None."""
    for p in TRAP_PILLARS:
        if p["id"] == pillar_id:
            return p
    return None


def get_dsrp_rules() -> List[Dict[str, Any]]:
    """Return all four DSRP rules."""
    return DSRP_RULES


def get_dsrp_rule(rule_id: str) -> Optional[Dict[str, Any]]:
    """Return a single DSRP rule by id, or None."""
    for r in DSRP_RULES:
        if r["id"] == rule_id:
            return r
    return None


def get_wisdom_agents() -> List[Dict[str, Any]]:
    """Return all seven Wisdom Layer agents."""
    return WISDOM_AGENTS


def get_wisdom_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Return a single Wisdom agent by id, or None."""
    for a in WISDOM_AGENTS:
        if a["id"] == agent_id:
            return a
    return None


def get_telemetry_metrics() -> List[Dict[str, Any]]:
    """Return all seven telemetry metrics."""
    return TELEMETRY_METRICS


def get_telemetry_metric(metric_id: str) -> Optional[Dict[str, Any]]:
    """Return a single telemetry metric by id, or None."""
    for m in TELEMETRY_METRICS:
        if m["id"] == metric_id:
            return m
    return None


def get_reinterpretation_table() -> List[Dict[str, Any]]:
    """Return the Traditional vs Resonant reinterpretation table."""
    return REINTERPRETATION_TABLE


def get_resonant_chamber() -> Dict[str, Any]:
    """Return the Resonant Chamber theory framework."""
    return RESONANT_CHAMBER


log.info(
    "resonance.py loaded — %d pillars, %d TRAP pillars, %d DSRP rules, "
    "%d wisdom agents, %d telemetry metrics",
    len(PILLARS), len(TRAP_PILLARS), len(DSRP_RULES),
    len(WISDOM_AGENTS), len(TELEMETRY_METRICS),
)
