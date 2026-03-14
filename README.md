# Praxis — Elimination-First AI Tool Curation Engine

> **When AI output outpaces trust, curation is the only honest answer.**

Praxis is a backend orchestration engine that plans, evaluates, and eliminates AI tools through multi-signal scoring, agentic reasoning, and continuous trust decay monitoring. It treats tools as interchangeable execution units — not sacred recommendations — and applies clinical differential diagnosis to determine which tools survive scrutiny for a specific operator's context.

**Repository:** [github.com/2654-zed/praxis-ai](https://github.com/2654-zed/praxis-ai)

---

## Metrics

<!-- AUTO:STATS:START -->
| Metric | Value |
|--------|-------|
| **Python modules** | 116 files, ~64,100 lines |
| **Tool catalog** | 253 curated AI tools with rich metadata |
| **API endpoints** | 372 REST routes via FastAPI |
| **Test coverage** | 719 tests across 16 test files, all passing |
| **Frontend** | 29 HTML + 4 JS files (~14,500 lines), Liquid Glass UI |
| **Versions** | 17 major iterations (v1 → v17) |
| **Total LOC** | ~78,600 (Python + Frontend) |
| **Zero external ML deps** | All NLP, scoring, graph, and retrieval are zero-dependency |
| **Last auto-update** | 2026-03-14 22:38 UTC |
<!-- AUTO:STATS:END -->

---

## Table of Contents

- [Why Praxis Exists](#why-praxis-exists)
- [The Problem](#the-problem)
- [The Thesis](#the-thesis)
- [How It Works](#how-it-works)
- [How to Think About Praxis](#how-to-think-about-praxis)
- [Elimination-First Reasoning](#elimination-first-reasoning)
- [System Architecture & Data Flow](#system-architecture--data-flow)
- [Trust Decay Monitoring](#trust-decay-monitoring)
- [Context-Aware Intent Transfer](#context-aware-intent-transfer)
- [Journey Oracle & Outcome Tracking](#journey-oracle--outcome-tracking)
- [Multi-Model Ecosystem](#multi-model-ecosystem)
- [Monetization Model & Gating Logic](#monetization-model--gating-logic)
- [Strategic Positioning](#strategic-positioning)
- [Latent Flux Integration](#latent-flux-integration)
- [Engineering Principles](#engineering-principles)
- [The 22 Versions — Build History](#the-22-versions--build-history)
- [Complete Module Reference](#complete-module-reference)
- [Directory & File Map](#directory--file-map)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Test Suite](#test-suite)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Key Architectural Decisions](#key-architectural-decisions)
- [Known Technical Patterns](#known-technical-patterns)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Open Philosophical Questions](#open-philosophical-questions)
- [Contributing](#contributing)
- [How to Understand the Full Codebase from This README](#how-to-understand-the-full-codebase-from-this-readme)

---

## Why Praxis Exists

The AI tools ecosystem is growing faster than any human or organization can evaluate. There are 15,000+ AI tools available as of March 2026. Most are wrappers around the same foundation models. Many will shut down within 18 months. Some harvest data in ways their marketing pages don't disclose. A small number are genuinely transformative for the right operator.

No SMB owner has the time, expertise, or risk tolerance to evaluate this landscape themselves. And no AI assistant should recommend tools without understanding the operator's industry, budget, compliance requirements, existing stack, or skill level.

Praxis exists because **trust must be earned, measured, and continuously verified** — not assumed.

---

## The Problem

Three forces create the gap Praxis addresses:

### 1. Trust Decay
A tool that was trustworthy last quarter may not be trustworthy today. Pricing structures change. Companies get acquired by private equity firms that strip features. Free tiers vanish. Data practices evolve without notice. SSL certificates expire. API SLAs degrade.

No static recommendation engine accounts for this. Praxis does — through continuous monitoring of 11 decay signal types, producing MILD (Yellow) and SEVERE (Red) alerts that immediately affect scoring.

### 2. Output Outpacing Comprehension
AI tools produce outputs faster than operators can evaluate them. An SMB owner who adopts ChatGPT, Jasper, and Notion AI simultaneously has no framework for understanding which tool is actually generating value versus which is generating confident-sounding noise.

Praxis provides that framework — not by being another AI, but by being the **neutral bridge** that curates *which* AIs an operator should trust for their specific context.

### 3. SMB Relevance
Enterprise directories like G2 and Gartner optimize for large organizations. An 8-person healthcare clinic doesn't need Snowflake's AI features. They need HIPAA-compliant, free-tier, beginner-friendly tools that integrate with their existing workflow. Praxis scores every tool on a 100-point SMB relevance scale across three dimensions: vertical match (0–40), pricing accessibility (0–30), and operational complexity (0–30).

---

## The Thesis

> **Elimination is more honest than recommendation.**

Traditional recommendation engines rank by relevance. Praxis ranks by *survival*. The differentiation:

- **Recommendation**: "Here are the top 5 tools for your query."
- **Elimination**: "We evaluated 246 tools. 231 failed your constraints. Of the 15 survivors, here are the 3 that withstood vendor risk analysis, trust decay monitoring, compliance verification, and skill-level matching — with full explanations of *why* each eliminated tool was removed."

This is the clinical differential diagnosis model applied to software selection. Every eliminated candidate is logged with a specific reason code. Every survivor has a transparent audit trail. Nothing is a black box.

---

## How It Works

Praxis has seven core layers that form the request pipeline:

| Layer | Role |
|-------|------|
| **Interpreter** | Extracts structured intent from free-form queries — task type, industry, budget, keywords, constraints, negative signals |
| **Context Engine** | Extracts implicit operator context, scores confidence per field, assigns commitment tiers (T1/T2/T3) |
| **Decision Engine** | Multi-signal scoring across 246 tools — keyword, category, TF-IDF, profile fit, industry boost, trust badges, sovereignty |
| **Differential Engine** | Elimination pipeline — broad candidates → hard prune → soft penalize → rank survivors with reason codes |
| **Execution Layer** | Hybrid retrieval (BM25 + dense + RRF), knowledge graph traversal, PRISM multi-agent search, vertical constraint enforcement |
| **Journey Oracle** | Passive lifecycle tracking — INTAKE → DISCOVERY → SELECTION → DEPLOYMENT → OUTCOME with drift monitoring |
| **Trace Layer** | Every reasoning step recorded — sub-questions, scoring signals, agent critiques, constraint applications, explanations |

### Request Flow

```
User query: "I need HIPAA-compliant writing tools under $50/mo for my clinic"
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ INTAKE                                                              │
│                                                                     │
│ Interpreter ──── task: "writing", industry: "healthcare",           │
│                  budget: "$50/mo", constraints: ["HIPAA"]           │
│                                                                     │
│ Context Engine ─ confidence scoring per field:                      │
│                  industry: 0.95 (T1 → auto-commit)                 │
│                  budget: 0.88 (T2 → pre-fill, confirm)             │
│                  skill_level: 0.40 (T3 → must ask)                 │
│                                                                     │
│ Residual Gap ── "What is your team's technical skill level?"        │
│                 "Do you already use any AI writing tools?"          │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ DISCOVERY                                                           │
│                                                                     │
│ Decision Engine ── score all 246 tools (pure-function, no side fx)  │
│   ├── TF-IDF semantic match (weight: 8x)                           │
│   ├── Category + tag + keyword matching (4x / 3x / 2x)            │
│   ├── Popularity signal (usage.json)                               │
│   ├── Learned boost (feedback loop)                                │
│   ├── Trust badge scoring (+5 for ≥80 trust, −3 for <35)          │
│   └── Sovereignty modifier (US-owned bonus / foreign penalty)      │
│                                                                     │
│ Differential ── clinical elimination:                               │
│   Hard prune: budget > $50 → ELIMINATED (BUDGET_EXCEEDED)          │
│   Hard prune: no HIPAA BAA → ELIMINATED (COMPLIANCE_MISSING)       │
│   Hard prune: skill_level = expert, user = beginner → ELIMINATED   │
│   Soft penalty: high lock-in risk → score −3                       │
│   Soft penalty: low transparency → score −2                        │
│   Result: 246 → 11 survivors                                       │
│                                                                     │
│ Retrieval ── BM25 sparse + dense vector fusion (RRF)               │
│ Graph ─────── knowledge graph traversal + community detection      │
│ PRISM ─────── Analyzer → Selector → Critic (hallucination audit)   │
│ Verticals ─── HIPAA constraint enforcement, healthcare workflows   │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ SELECTION                                                           │
│                                                                     │
│ Stack Composer ── assigns roles:                                    │
│   🏆 Primary:       Jasper (88% fit, HIPAA-compliant, $49/mo)      │
│   🤝 Companion:     Grammarly Business (82% fit, free tier)        │
│   🔗 Infrastructure: Notion AI (76% fit, workspace integration)    │
│                                                                     │
│ Explain ──── per-tool reasoning narrative with fit scores, caveats  │
│ Journey Oracle ── records TargetScoreVector per tool                │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OUTCOME (days/weeks later)                                          │
│                                                                     │
│ Journey Oracle ── passive drift detection:                          │
│   predicted relevance: 0.88 → actual satisfaction: 0.72            │
│   Δ = 0.16 → MILD drift → logged, feeds back into scoring         │
│                                                                     │
│   predicted budget_fit: 0.85 → actual ROI: 0.45                   │
│   Δ = 0.40 → SEVERE drift → alert, trust penalty applied          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## How to Think About Praxis

Praxis behaves like several well-understood backend systems at once. These are architectural parallels, not branding metaphors.

**Query planner** — Like a database query planner, Praxis receives a high-level intent and determines the most efficient execution strategy across available tools, applying cost estimates and constraint checks before committing to a path.

**Compiler** — Like a compiler turning source code into executable instructions, the Planner converts unstructured user intent into a structured, ordered pipeline of tool calls with typed inputs and expected outputs.

**Air traffic control** — Like an ATC system coordinating independent aircraft, the Execution Layer routes concurrent tool operations safely, handles retries on failure, and prevents conflicting tool combinations from being recommended to the same user.

**Clinical differential diagnosis** — Like a physician generating a broad differential and systematically ruling out diagnoses via tests, Praxis generates a broad candidate set and systematically eliminates tools via constraint checks, producing transparent "why not" audit trails.

---

## Elimination-First Reasoning

The core philosophical innovation. Implemented in `differential.py` (1,096 lines).

### The Algorithm

```
Input: query, user_profile, tool_catalog (246 tools)

Step 1 — GENERATE DIFFERENTIAL
    Parse intent → extract positive/negative signals, constraints
    Broad retrieval → top-N candidates via engine.score_tool()
    (Typically 20-40 candidates survive initial retrieval)

Step 2 — HARD ELIMINATION (binary pass/fail)
    For each candidate, apply constraint matrix:
        Budget exceeded?           → ELIMINATED (BUDGET_EXCEEDED)
        Compliance missing?        → ELIMINATED (COMPLIANCE_MISSING)
        Skill level mismatch?      → ELIMINATED (SKILL_MISMATCH)
        Explicitly excluded?       → ELIMINATED (USER_EXCLUDED)
        Sovereignty risk?          → ELIMINATED (SOVEREIGNTY_RISK)
        Active trust decay alert?  → ELIMINATED (TRUST_DECAY_ACTIVE)

Step 3 — SOFT PENALIZATION (continuous scoring adjustment)
    For each survivor:
        Lock-in risk (philosophy.py)     → score penalty 0 to −5
        Transparency gap                 → score penalty 0 to −3
        Low community health             → score penalty 0 to −2
        Historical churn signal          → score penalty 0 to −3
        Integration gap with stack       → score penalty 0 to −2

Step 4 — RANK SURVIVORS
    Sort by adjusted score
    Apply diversity reranking (no single-vendor domination)
    Assign stack roles: primary / companion / infrastructure / analytics

Step 5 — EXPLAIN EVERY DECISION
    For each eliminated tool → generate "why not" counterfactual
    For each survivor → generate fit narrative with reasons + caveats

Output: DifferentialResult {
    survivors: List[ScoredSurvivor]
    eliminations: List[EliminationEntry]   ← each has reason_code, evidence
    ambiguities: List[AmbiguityFlag]       ← uncertain eliminations
}
```

### Elimination Reason Codes

| Code | Meaning | Hard/Soft |
|------|---------|-----------|
| `BUDGET_EXCEEDED` | Tool pricing exceeds stated budget | Hard |
| `COMPLIANCE_MISSING` | Required regulatory framework not supported | Hard |
| `SKILL_MISMATCH` | Tool requires expert skills, user is beginner | Hard |
| `USER_EXCLUDED` | User explicitly said "not X" | Hard |
| `SOVEREIGNTY_RISK` | Foreign data jurisdiction violates constraints | Hard |
| `TRUST_DECAY_ACTIVE` | SEVERE trust decay alert currently active | Hard |
| `LOCK_IN_HIGH` | Vendor lock-in risk above threshold | Soft |
| `TRANSPARENCY_LOW` | Insufficient transparency scoring | Soft |
| `CHURN_SIGNAL` | Historical user churn from this tool | Soft |
| `INTEGRATION_GAP` | Weak integration with existing stack | Soft |

### Example: "Why Not" Counterfactual

```json
{
  "tool": "Snowflake Cortex",
  "reason_code": "BUDGET_EXCEEDED",
  "evidence": "Minimum plan $150/mo, user budget=$50/mo",
  "counterfactual": "If budget were ≥$150/mo, Snowflake Cortex would rank #2
                     with 87% fit due to strong healthcare data compliance."
}
```

See `differential.py` for the full implementation.

---

## System Architecture & Data Flow

```
                            ┌─────────────────────┐
                            │   Frontend (33 files)│
                            │  Liquid Glass UI     │
                            │  journey.html        │
                            │  home.html           │
                            └────────┬────────────┘
                                     │ HTTP
                                     ▼
┌───────────────────────────────────────────────────────────────────┐
│                        FastAPI (493 routes)                       │
│  api.py · api_routes_core.py · api_routes_features.py            │
│  auth.py (OAuth2/API-key) · rate_limiter.py · telemetry.py       │
└────────────────────────────┬──────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│  Interpreter │   │Context Engine│   │ Residual Gap      │
│  interpret() │   │ extract()    │   │ compute_gap()     │
│  rule+LLM    │   │ C(P) formula │   │ dependency tree   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────────┘
       │                  │                  │
       └──────────┬───────┘──────────────────┘
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Decision Pipeline                             │
│                                                                  │
│  engine.py ─── score_tool() ─── multi-signal scoring             │
│       │                                                          │
│       ▼                                                          │
│  differential.py ─── generate_differential()                     │
│       │    Hard prune (constraints) → Soft penalize → Rank       │
│       │                                                          │
│       ├── retrieval.py (BM25 + dense + RRF)                     │
│       ├── graph.py (GraphRAG, community detection)              │
│       ├── prism.py (Analyzer → Selector → Critic)               │
│       ├── verticals.py (10+ industry verticals)                 │
│       ├── philosophy.py (vendor risk)                           │
│       ├── trust_decay.py (11 signal types)                      │
│       ├── trust_badges.py (9 badge categories)                  │
│       └── sovereignty.py (geopolitical risk)                     │
│                                                                  │
│  stack.py ─── compose_stack() ─── role assignment                │
│  explain.py ─── generate_explanation() ─── narratives            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Journey Oracle (journey.py)                         │
│  INTAKE → DISCOVERY → SELECTION → DEPLOYMENT → OUTCOME          │
│  TargetScoreVector at SELECTION → DriftSignal at OUTCOME        │
│  Feeds back into learning.py + trust_decay.py                   │
└─────────────────────────────────────────────────────────────────┘
```

### Tool Data Model

Every tool in `data.py` carries 14+ metadata fields:

```python
Tool(
    name="Jasper",
    description="AI writing assistant for marketing teams",
    categories=["writing", "marketing", "content"],
    url="https://jasper.ai",
    pricing={"free_tier": False, "starter": 49, "enterprise": "custom"},
    integrations=["Google Docs", "WordPress", "Surfer SEO"],
    compliance=["SOC2", "GDPR"],
    use_cases=["blog posts", "ad copy", "product descriptions"],
    skill_level="beginner",
    tags=["copywriting", "SEO", "templates"],
    keywords=["writing", "content creation", "marketing copy"],
    stack_roles=["primary"],
    languages=["en", "es", "de", "fr"],
    limitations=["no code generation", "limited technical writing"],
    data_handling={"stores_prompts": True, "deletion_available": True},
)
```

See `tools.py` for the `Tool` dataclass schema. See `data.py` for all 246 entries.

---

## Trust Decay Monitoring

Implemented in `trust_decay.py` (600+ lines). Operates **independently** from the main request pipeline — never blocks user queries.

### Detection Methods (11 Signal Types)

| Signal | Method | Severity |
|--------|--------|----------|
| `PRICING_CHANGE` | Wayback CDX pricing page structural diffs | MILD or SEVERE |
| `SENTIMENT_DROP` | G2/Capterra review NLP anomaly detection | MILD |
| `SUPPORT_SLA_BREACH` | Support response time degradation | MILD |
| `SSL_EXPIRY` | Certificate validity monitoring | SEVERE |
| `DNS_CHANGE` | DNS routing change detection | SEVERE |
| `DATA_BREACH` | Public breach disclosure detection | SEVERE |
| `SERVICE_SHUTDOWN` | Shutdown announcement detection | SEVERE |
| `MASS_COMPLAINTS` | Keyword density spike in complaints | MILD or SEVERE |
| `API_OUTAGE` | API uptime degradation | MILD |
| `PE_ACQUISITION` | Private equity acquisition (feature stripping risk) | MILD |
| `FREE_TIER_REMOVED` | Pricing page length drops >50% | SEVERE |

### Alert Tiers

| Tier | Badge | Effect | Notification |
|------|-------|--------|--------------|
| **MILD** (Yellow/Caution) | ⚠️ Caution | Score penalty, flagged in UI | None (passive) |
| **SEVERE** (Red/Under Review) | 🔴 Under Review | Hard elimination trigger | Proactive email alert |

### Trust Decay Formula

```python
# Each tool carries a trust_score (0-100) that feeds into engine scoring:
if trust_score >= 80:   score += 5
elif trust_score >= 65: score += 3
elif trust_score >= 50: score += 1
elif trust_score < 35:  score -= 3

# Decay signals degrade trust_score over time:
#   MILD signal:   trust_score -= 5 per signal
#   SEVERE signal: trust_score -= 15 per signal, triggers hard elimination
```

### Sweep Architecture

Designed for Celery Beat dispatch every 72 hours. Ships with synchronous fallback for environments without Redis/Celery.

```python
from praxis.trust_decay import run_trust_sweep, get_decay_alerts

alerts = run_trust_sweep()          # Full sweep across all 246 tools
active = get_decay_alerts("severe") # Only SEVERE alerts
```

### Model Trust Decay (v20)

A parallel system monitors LLM models via `model_trust_decay.py`:

| Signal | What It Measures |
|--------|-----------------|
| Hallucination Rate | PRISM `fact_audit` failure percentage |
| Quality Drift | User feedback sentiment trajectory |
| Latency Degradation | p95 latency trending upward |
| Cost Creep | Provider pricing changes |

Trust score changes feed back into `ModelRegistry` and affect `model_router.py` routing decisions.

---

## Context-Aware Intent Transfer

Implemented in `context_engine.py` and `residual_gap.py` (v21).

### The Problem

When an operator types "I need help with marketing," the system must infer 6+ context dimensions (industry, budget, skill level, team size, existing tools, compliance requirements) to produce a relevant recommendation. Traditional systems either:
1. Ask 15 questions upfront (high friction, users abandon)
2. Guess everything (low accuracy, irrelevant results)

### The Solution: Confidence-Tiered Extraction

Each context field gets a confidence score via the formula:

$$C(P) = \alpha \frac{T_{match}}{T_{total}} + \beta \frac{1}{1+D_{graph}} + \gamma S_{prox} + \delta M_{ex}$$

Where:
- $\alpha = 0.25$ — term match weight (how many query terms align with known values)
- $\beta = 0.30$ — graph distance weight (proximity in knowledge graph)
- $\gamma = 0.25$ — syntactic proximity weight (position/structure cues)
- $\delta = 0.20$ — explicit match weight (direct keyword matches)

### Tier Assignment

| Tier | Threshold | Action |
|------|-----------|--------|
| **T1** | $C \geq 0.90$ | Auto-commit to profile (no question asked) |
| **T2** | $0.60 \leq C < 0.90$ | Pre-fill with inferred default, ask for confirmation |
| **T3** | $C < 0.60$ | Must ask the operator — no reliable signal |

### Residual Gap Engine

`residual_gap.py` takes the T3 fields and produces a minimal, dependency-ordered question set:

```
Cascade Dependency Tree:
    Level 0 (BLOCKING):  industry / vertical → gates compliance pruning
    Level 1 (BRANCHING): existing_tools → gates graph traversal
    Level 2 (REFINEMENT): skill_level, budget, team_size → modulates scoring

Rules:
    • Never ask what you already know (T1/T2 fields excluded)
    • Ask industry BEFORE tools, tools BEFORE skill/budget
    • If budget="free" → skip complex integration questions
    • Maximum 4 questions per session (configurable via config.py)
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/context/extract` | Extract context from query, return ContextVector with per-field confidence |
| `POST` | `/context/resolve` | Resolve gap questions with operator answers, re-rank tools |
| `POST` | `/context/analyse` | Full cascade dependency analysis |

---

## Journey Oracle & Outcome Tracking

Implemented in `journey.py` (v22). The **passive observer** that tracks the full lifecycle.

### Pipeline Stages

```
INTAKE ──→ DISCOVERY ──→ SELECTION ──→ DEPLOYMENT ──→ OUTCOME
  │            │             │              │              │
  │            │             │              │              ▼
  │            │             │              │         Drift Detection
  │            │             │              │         Outcome Recording
  │            │             │              │         Feedback → learning.py
  │            │             ▼              │
  │            │        TargetScoreVector   │
  │            │        set per tool         │
  │            ▼                            │
  │       Elimination pipeline              │
  │       Reason codes logged               │
  ▼                                         │
  Context extraction                        │
  Gap analysis                              │
```

### TargetScoreVector

At SELECTION, each recommended tool gets a predicted outcome vector:

```python
TargetScoreVector(
    relevance=0.88,          # predicted task relevance
    budget_fit=0.85,         # predicted budget alignment
    skill_fit=0.90,          # predicted skill match
    integration_ease=0.80,   # predicted integration smoothness
)
```

### Drift Detection

At OUTCOME, actual results are compared against predictions:

$$D = \frac{\sum |predicted_i - actual_i|}{N}$$

| Severity | Threshold | Action |
|----------|-----------|--------|
| NONE | $\|Δ\| < 0.15$ | No action |
| MILD | $0.15 \leq \|Δ\| < 0.30$ | Log only |
| MODERATE | $0.30 \leq \|Δ\| < 0.45$ | Flag for review |
| SEVERE | $\|Δ\| \geq 0.45$ | Feed back into scoring pipeline |

### Usage

```python
from praxis.journey import get_oracle, JourneyStage, build_target_vector

oracle = get_oracle()

# Start journey at INTAKE
jid = oracle.create_journey("user_123", query="need writing tools for healthcare")

# Record targets at SELECTION
vector = build_target_vector("Jasper", fit_score=22, budget_match=True, skill_match=True, integration_count=3)
oracle.set_target_vector(jid, "Jasper", vector)

# Record actual outcome
oracle.record_outcome(jid, "Jasper", satisfaction=0.72, roi=0.45, integration_success=0.80)

# Detect drift
signals = oracle.detect_drift(jid)
# → DriftSignal(tool="Jasper", dimension="budget_fit", predicted=0.85, actual=0.45, delta=0.40, severity="severe")

# Dashboard
dashboard = oracle.dashboard()
# → {total_journeys: 1, avg_satisfaction: 0.72, drift_alert_count: 1, ...}
```

---

## Multi-Model Ecosystem

Implemented across 6 modules in v20. Applies Praxis's elimination reasoning to LLM model selection — not just tool selection.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│               model_registry.py                          │
│  ModelSpec: id, provider, capabilities, cost, trust,     │
│            privacy_level, latency_class, tier             │
│  8 Providers: OpenAI, Anthropic, Google, XAI, Meta,      │
│               DeepSeek, Local, LiteLLM                    │
│  Dynamic tiers: Tier 1 (prod) → Tier 2 (research)       │
│                                → Tier 3 (sandbox)        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                model_router.py                           │
│  Elimination pipeline for LLM selection:                 │
│    1. Parse intent → infer required capabilities         │
│    2. Hard-eliminate: budget, privacy, capability miss    │
│    3. Soft-penalize: trust decay, cost, latency          │
│    4. Route: single model OR multi-model collaboration   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                ecosystem.py                              │
│  Collaboration patterns:                                 │
│    Sequential Chain — pass output A → input B            │
│    Fan-Out/Fan-In — parallel + synthesis                 │
│    Specialist Routing — domain-matched model selection    │
│    Adversarial Review — models critique each other        │
│                                                          │
│  shared_state.py: CoALA (Working/Episodic/Semantic/      │
│    Procedural) + trust-weighted relay between models     │
│                                                          │
│  llm_provider.py: unified interface for all providers    │
│    Dry-run by default (mock responses). API keys from    │
│    env vars only, never hardcoded or logged.             │
│                                                          │
│  model_trust_decay.py: 4 decay signals for models        │
└─────────────────────────────────────────────────────────┘
```

### Current State

The multi-model ecosystem is **architecturally complete** but operates in **dry-run mode** by default. `llm_provider.py` returns mock responses unless real API keys are provided via environment variables. This is intentional — Praxis works zero-dependency at every layer.

---

## Monetization Model & Gating Logic

Defined in `enterprise.py` (v17) and `monetise.py`.

### Pricing Tiers

| Tier | Price | Access |
|------|-------|--------|
| **Free** | $0 | Full tool curation, elimination pipeline, trust badges, 246-tool catalog, journey wizard |
| **Pro** | Planned | Multi-model ecosystem activation, advanced analytics, priority support |
| **Enterprise** | Planned | Custom ingestion, governance dashboard, SSO, audit compliance |

### Gating Logic

```python
# From enterprise.py — three pricing models
PRICING_MODELS = [
    {"name": "traction",    "description": "free curation + earned data gravity"},
    {"name": "pilot",       "description": "paid ecosystem + agentic activation"},
    {"name": "enterprise",  "description": "custom deployment + governance SLA"},
]

# Enterprise-ready threshold:
#   ≥ 3 pillars scoring ≥ 0.45  AND  agent roles composite ≥ 0.15
```

### Revenue streams (planned)
- **Affiliate links** — tracked, disclosed, never affecting scoring (`monetise.py`)
- **User-generated benchmarks** — community-contributed performance data
- **Weekly AI digest** — curated email with scoring methodology transparency
- **Multi-model activation** — paid access to run queries through multiple LLMs simultaneously

---

## Strategic Positioning

### The Problem No One Else Is Solving

The AI tools market has 15,000+ products and is growing by hundreds per month. Every other company in this space is building another tool — another chatbot, another coding assistant, another writing helper. The market is drowning in supply.

No one is building the layer that sits above all of them.

Enterprises and SMBs face the same problem: they adopt 3-7 AI tools, manually copy outputs between them, re-explain context at every step, and have no way to measure whether any individual tool is actually delivering value. The workflow looks like this:
Human → AI Tool A → Human copies output → AI Tool B → Human explains context again → AI Tool C

This is the gap Praxis occupies. Not another tool. The orchestration layer.

### The Orchestra Model

Praxis operates on a conductor metaphor that maps directly to the architecture:

| Role | Entity | What It Does |
|------|--------|-------------|
| **Director** | The user | Defines intent, sets constraints, approves outcomes |
| **Conductor** | Praxis | Understands the workflow, selects the right tools, coordinates execution, monitors quality |
| **Musicians** | AI tools (253 in catalog) | Perform specialized tasks — writing, coding, analysis, research, automation |

The user never manually routes work between AI systems. Praxis understands the workflow and coordinates the tools automatically. The key insight: Praxis gets stronger as more tools enter the market. Every new AI tool is another musician in the orchestra, not a competitor.

### Why Praxis Is Defensible

**1. Elimination-first methodology is a philosophical moat.**
Every AI tool directory ranks by relevance. Praxis ranks by survival. The elimination pipeline — 253 tools reduced to 3-8 survivors with full audit trails — is a fundamentally different approach to recommendation. It's harder to build, harder to explain, and harder to replicate than a relevance sort. Competitors would need to rebuild the entire differential diagnosis engine, trust decay monitoring, and compliance verification stack.

**2. Trust decay monitoring creates compounding intelligence.**
Praxis monitors 11 signal types across every tool in the catalog: pricing changes, sentiment drops, SSL expiry, data breaches, PE acquisitions, free tier removals. This runs continuously. Every sweep makes the catalog more accurate. After 6 months of operation, Praxis has trust intelligence that no competitor can replicate without running the same monitoring infrastructure for the same period. Trust data is a time-locked moat.

**3. Latent Flux gives Praxis behavioral intuition, not just metrics.**
Most monitoring systems use threshold-based alerts: "if latency > 500ms, fire alert." Praxis uses geometric behavioral drift detection via Latent Flux — a per-tool Echo State Network that learns what "normal" looks like for each tool and detects when behavior deviates from the learned manifold before any single metric crosses a threshold. This catches the scenario every other system misses: gradual, multi-dimensional degradation that hasn't triggered any individual alert yet.

**4. The feedback loop closes automatically.**
Journey Oracle tracks the full lifecycle: what Praxis recommended → what the user adopted → how it actually performed → how that performance compared to predictions. Drift signals feed back into scoring automatically. This means Praxis's recommendations get measurably better with every completed journey. No competitor has this closed-loop outcome tracking for AI tool selection.

**5. Zero external ML dependencies means universal deployment.**
The entire system — NLP, scoring, graph traversal, retrieval, trust monitoring — runs on pure Python stdlib. No PyTorch, no NumPy (except in the optional Latent Flux repo), no model downloads. Praxis starts instantly, deploys anywhere Python runs, and produces fully auditable scoring decisions. This is an architectural choice that makes enterprise deployment trivially easy compared to ML-dependent competitors.

### Competitive Landscape

| Competitor | What They Do | Why Praxis Is Different |
|-----------|-------------|----------------------|
| **G2, Gartner** | Tool directories with reviews and rankings | Static rankings, no elimination reasoning, no trust monitoring, enterprise-optimized (not SMB) |
| **Product Hunt, TAAFT** | Tool discovery via popularity and recency | No personalization, no elimination, no compliance checking, no outcome tracking |
| **LangChain, CrewAI, AutoGen** | Developer frameworks for multi-agent orchestration | Developer-centric (requires code), no tool catalog, no trust monitoring, no UI for non-technical users |
| **Zapier, Make** | Workflow automation between apps | Automate actions between tools but don't select which tools to use, no elimination reasoning |
| **ChatGPT, Claude, Gemini** | General-purpose AI assistants | Can recommend tools but have no curated catalog, no trust decay data, no elimination pipeline, no outcome tracking |

Praxis's position: the only platform that combines a curated tool catalog (253 tools), elimination-first reasoning (not relevance ranking), continuous trust monitoring (11 signals), behavioral drift detection (Latent Flux), and closed-loop outcome tracking (Journey Oracle) in a single system.

### Where Praxis Is Going

**Phase 1 (current): Curation** — "Which AI tools should I use?"
Praxis evaluates 253 tools against the user's constraints and eliminates the unfit. The Room SPA is the product surface. Value: saves hours of research and avoids bad tool choices.

**Phase 2 (next): Orchestration** — "Run these tools together on my project."
Praxis doesn't just recommend tools — it executes multi-tool pipelines. The conductor coordinates Research AI → Analysis AI → Code AI → Testing AI as a single workflow. The Split Verdict layout evolves: the narrow verdict sidebar becomes the conductor status panel, the wide evidence panel becomes the live workspace.

**Phase 3 (long-term): Marketplace** — "Publish your tool to the Praxis ecosystem."
Like Steam for AI tools. Developers register tools with standardized input/output contracts. Praxis handles discovery, trust verification, orchestration, and revenue sharing. The marketplace layer monetizes once the workspace proves its value.

Each phase builds on the previous. The curation data from Phase 1 trains the orchestration engine in Phase 2. The orchestration patterns from Phase 2 define the marketplace contracts in Phase 3.

### Target Markets

**Primary: SMBs adopting AI (5-50 employees)**
These organizations are adopting AI tools faster than they can evaluate them. They don't have a CTO to vet tools, a compliance officer to check certifications, or a procurement team to negotiate pricing. Praxis is their AI procurement department.

**Secondary: AI-native agencies**
Agencies that deliver finished outcomes (marketing campaigns, analytics, content) using AI tool pipelines. These agencies need orchestration infrastructure — something to manage which tools run, in what order, with what quality checks. Praxis is their backend.

**Tertiary: Enterprise AI governance**
Large organizations that need to monitor and control which AI tools their teams use, track costs across tools, enforce compliance requirements, and maintain audit trails. The governance dashboard, trust badges, and compliance modules already serve this market.

---

## Latent Flux Integration

> **Status: Implemented (v25.4/v25.5). Core primitives integrated as orchestration reliability monitor.**

Latent Flux (LF) is a geometric computation library that provides behavioral drift detection for Praxis's tool monitoring and orchestration reliability. Three core primitives are integrated via a pure-Python adapter (`praxis/lf_monitor.py`) with zero NumPy dependency:

| LF Primitive | Praxis Component | What It Does |
|-------------|-----------------|-------------|
| **ReservoirState** (Echo State Network with σ² tracking) | `ToolReservoir` | Builds a continuous behavioral baseline per tool — learns what "normal" looks like for latency, quality, token usage, error rate, cost. Detects when current behavior deviates from the learned manifold. The σ² (running variance) addition catches tools becoming erratic before the mean shifts. |
| **AttractorCompetition** (3-basin geometric classifier) | `PipelineHealthCompetitor` | Classifies pipeline health into Healthy / Degrading / Failing basins using geometric attractor dynamics instead of hardcoded thresholds. The pipeline's combined state vector naturally falls into the correct basin. |
| **RecursiveFlow** (fixed-point cycle detection) | `RetryLoopDetector` | Detects retry loops in tool execution — when a pipeline stage repeatedly fails and retries without converging. Combined with σ from the reservoir, triggers circuit breakers before resources are wasted. |

### Integration Points

| Module | How LF Is Used |
|--------|---------------|
| `trust_decay.py` | `lf_record_tool_call()` feeds per-invocation metrics into ToolReservoir. `lf_assess_severity()` uses basin competition for MILD/SEVERE classification instead of threshold comparison. |
| `journey.py` | Per-tool reservoirs track TargetScoreVector predictions vs actual outcomes. `deviation_score()` replaces simple delta-based drift detection with manifold-aware measurement. |
| `llm_resilience.py` | Per-provider reservoirs monitor LLM call patterns. Circuit breaker trips on `deviation_score ≥ 4.0` — catches erratic-but-not-fully-failing providers that consecutive-failure counting misses. |

### Future: Conductor's Ear

As Praxis evolves from curation (recommending tools) to orchestration (executing tool pipelines), Latent Flux becomes the conductor's ear — real-time behavioral monitoring across every tool in an active pipeline. The reservoir baselines, attractor basins, and cycle detectors are already built for this use case. The primitives that currently monitor individual tool calls will monitor inter-tool relationships: does the Research AI's output quality affect the Coding AI's performance? Is the testing stage's rejection rate rising because the coding stage degraded, or because the test criteria changed? These are manifold-level questions that threshold monitoring cannot answer.

---

## Engineering Principles

These are the invariants the codebase is built around:

1. **Elimination over recommendation** — Ranking is dishonest when constraints aren't applied. Every recommendation is a survival result, not a relevance sort.

2. **Deterministic execution paths** — Scoring functions are pure. Given identical inputs, the engine produces identical rankings. LLM calls are isolated to the interpreter and reasoning layers; they do not touch scoring.

3. **Inspectable reasoning traces** — Every recommendation can be traced back to its scoring signals, constraint applications, elimination reasons, and agent sub-steps. Nothing is a black box.

4. **Tool abstraction over vendor coupling** — Tools are metadata records in a registry, not hardcoded integrations. Adding, removing, or repricing a tool requires no application code changes.

5. **Failure-aware orchestration** — Fallback strategies at every layer. Guardrails run as chain-of-responsibility, not a single gate.

6. **Pipeline composability** — Retrieval, reasoning, graph traversal, and vertical enrichment are independent modules. Any combination can be enabled or disabled per request.

7. **Zero external ML dependencies** — All NLP (synonym expansion, TF-IDF, BM25, Levenshtein, multi-intent parsing), graph operations (community detection, traversal), and dense retrieval are pure Python. No PyTorch, no transformers, no NumPy required.

8. **The LLM is optional** — Praxis works completely without any LLM API key. The interpreter falls back to rule-based parsing, reasoning to local synthesis. The LLM is an accelerator, not a dependency.

9. **Trust is ephemeral** — No tool stays trusted forever. Trust must be continuously re-earned through trust decay monitoring, outcome tracking, and drift detection.

---

## The 22 Versions — Build History

### Phase 1: Foundation — Scoring, Profiles, NLP (v1–v5)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v1** | Core Engine | Basic scoring, keyword matching, tool data model | `engine.py`, `tools.py`, `data.py`, `interpreter.py` |
| **v2** | Personalization | Profiles, stacks, explanations, feedback, config, CLI, API | `profile.py`, `stack.py`, `explain.py`, `learning.py`, `config.py`, `main.py`, `api.py`, `feedback.py`, `usage.py`, `storage.py` |
| **v3** | Intelligence | Zero-dep NLP: synonyms, typos, TF-IDF, multi-intent, diversity reranking | `intelligence.py` |
| **v4** | Philosophy | Vendor risk: transparency, freedom, lock-in, data practices, power tracking | `philosophy.py` |
| **v5** | Ingest + Seed | CSV/JSON import-export, synthetic feedback seeding | `ingest.py`, `seed.py` |

### Phase 2: Agentic Reasoning + Hybrid Retrieval (v6–v8)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v6** | Agentic Reasoning | Plan→Act→Observe→Reflect loop, LLM-backed + rule-based | `reason.py` |
| **v7** | Cognitive Search | Hybrid retrieval (BM25+dense+RRF), knowledge graph (GraphRAG), PRISM | `retrieval.py`, `graph.py`, `prism.py` |
| **v8** | Vertical Industry | 10+ verticals, regulatory frameworks (HIPAA/SOX/GDPR), anti-patterns | `verticals.py` |

### Phase 3: Safety, Guardrails + Self-Inspection (v9–v11)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v9** | Safety + Architecture | Chain-of-responsibility guardrails, event-driven architecture intelligence | `guardrails.py`, `orchestration.py` |
| **v10** | Resilience | Vibe-coding risk, static analysis, TDD/sandbox/HITL guidance | `resilience.py` |
| **v11** | Metacognition | Self-awareness, APVP cycle, drift detection, AST self-introspection | `metacognition.py`, `introspect.py` |

### Phase 4: Design Patterns + Philosophical Foundations (v12–v14)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v12** | Awakening | 6 philosophical recognitions, VSD, leaky abstractions, MESIAS risk | `awakening.py` |
| **v13** | Self-Authorship | 8 authorship responsibilities, DDD, event sourcing, Circuit Breaker, ADRs | `authorship.py` |
| **v14** | Enlightenment | 5 metaphysical truths, 6-stage path, Hexagonal/Clean Architecture, FSM | `enlightenment.py` |

### Phase 5: Enterprise Cognitive Architecture (v15–v17)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v15** | The Conduit | 7 pillars of decoupled cognition, IIT, GWT, CoALA, autopoiesis | `conduit.py` |
| **v16** | The Resonance | 5 pillars of resonant intelligence, TRAP framework, DSRP theory, 7 Wisdom agents | `resonance.py` |
| **v17** | The Enterprise Engine | 6 strategic pillars, Medallion architecture, agent roles, monetization, security | `enterprise.py` |

### Phase 6: Enterprise Infrastructure + Scale (v18)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v18** | Enterprise Infrastructure | Hexagonal Architecture contracts (Ports), exception taxonomy, Pydantic v2 domain models, LLM resilience (circuit breaker, backoff), OAuth2/API-key auth, rate limiting, structured telemetry, vendor trust scoring, optimized TF-IDF, HybridRAG v2 | `ports.py`, `exceptions.py`, `domain_models.py`, `llm_resilience.py`, `rate_limiter.py`, `auth.py`, `telemetry.py`, `vendor_trust.py`, `hybrid_retrieval_v2.py`, `scoring_optimized.py` |

### Phase 7: Ingestion, Curation & Trust Pipeline (v19)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v19** | Ingestion Pipeline v3.0 | Triple Match verification, SMB Alignment Gate, Trust Decay Monitor, Survival Scoring, HITL review queue, Agent SDK, Tool contributions, Governance, Marketplace, Connectors, Compliance, Observability, Cognitive architecture, Anti-patterns, AST security, Economics, AI Nutrition Labels, Prompt assistance, DMN-guided decomposition, Outcome-oriented advisory, Sovereignty detection, Trust badges (9 categories) | `pipeline_constants.py`, `ingestion_engine.py`, `trust_decay.py`, `smb_scoring.py`, `relationship_extraction.py`, `agent_sdk.py`, `contributions.py`, `governance.py`, `marketplace.py`, `connectors.py`, `compliance.py`, `observability.py`, `cognitive.py`, `codes_resonance.py`, `dsrp_ontology.py`, `anti_patterns.py`, `ast_security.py`, `ai_economics.py`, `nutrition.py`, `prompt_assist.py`, `outcomes.py`, `sovereignty.py`, `trust_badges.py`, `stress.py`, `differential.py`, `verification.py` |

### Phase 8: Multi-Model Ecosystem (v20)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v20** | Multi-Model Ecosystem | Elimination-first model selection, unified provider abstraction, model trust decay, collaboration orchestrator, CoALA+Relay shared state | `model_registry.py`, `llm_provider.py`, `model_trust_decay.py`, `model_router.py`, `ecosystem.py`, `shared_state.py` |

### Phase 9: Context Intelligence + Outcome Tracking (v21–v22)

| Version | Name | What It Added | Key Modules |
|---------|------|---------------|-------------|
| **v21** | Context-Aware Intent Transfer | Confidence-tiered context extraction, residual gap questions, cascade dependency tree | `context_engine.py`, `residual_gap.py` |
| **v22** | Journey Oracle | 5-stage lifecycle tracking, TargetScoreVector, passive drift detection, outcome feedback loop | `journey.py` |

### Post-v17 Audit

A full vibe-coding audit fixed 12 issues across 6 files:
- **CRITICAL**: Fixed `_score_entropy` alias collision, fixed `all_caveats` reset discarding domain intelligence
- **HIGH**: Removed 19 duplicate tools (266 → 246), removed dead code, normalized tag casing
- **MEDIUM**: Removed unused imports, fixed `int(None)` risk, fixed DB connection leak
- **LOW**: Added logging to 5 silent `except` blocks

---

## Complete Module Reference

### Core Decision Engine (v1–v2) — 13 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `engine.py` | 326 | Multi-signal scoring: keyword, tag, category, popularity, TF-IDF, profile-fit, industry boost, sovereignty, trust badges. Pure-function design |
| `interpreter.py` | 371 | LLM-backed (OpenAI/Anthropic) + rule-based intent parsing. Extracts keywords, categories, budget, constraints, task type |
| `stack.py` | 343 | Composes multi-tool stacks with roles (primary, companion, infrastructure, analytics). Side-by-side comparison |
| `explain.py` | 638 | Per-tool and per-stack reasoning narratives with fit scores, reasons, and caveats |
| `profile.py` | 222 | User profile management: industry, budget, team_size, skill_level, existing_tools, goals, constraints. JSON persistence |
| `learning.py` | 223 | Feedback-to-signal loop: tool quality computation, pair affinities, intent-tool collaborative filtering |
| `config.py` | 130 | Centralized config: env vars → `config.json` → defaults. LLM provider/model selection, feature flags, scoring weights |
| `tools.py` | 164 | `Tool` data class with 14+ fields: name, description, categories, url, pricing, integrations, compliance, use_cases, skill_level, tags, keywords, stack_roles, languages, limitations, data_handling |
| `data.py` | 3,997 | **246 curated AI tools** with full metadata. Largest data file. Exports `TOOLS`, `get_all_categories()`, `get_all_tools_dict()` |
| `storage.py` | 153 | SQLite persistence with JSON serialization. Migration from in-memory `TOOLS`. Uses `try/finally` for connection safety |
| `feedback.py` | 130 | Records accept/reject/rate events to `feedback.json`. Auto-triggers learning cycle at thresholds |
| `usage.py` | 44 | Popularity counter backed by `usage.json`. Feeds into engine scoring |
| `main.py` | 366 | REPL-style CLI: `profile`, `learn`, `compare`, `stack`, `reason`, `workflow`, `badges`, `health`, `whatif`, `diagnose` |

### Intelligence & Philosophy (v3–v5) — 4 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `intelligence.py` | 563 | Zero-dep NLP: synonym expansion (50+ maps), typo correction (Levenshtein), multi-intent parsing, TF-IDF index, negative filtering, diversity reranking, autocomplete |
| `philosophy.py` | 944 | Vendor due diligence: transparency scoring, freedom assessment, lock-in detection, data practice auditing, power concentration tracking |
| `ingest.py` | 245 | CSV/JSON import-export pipeline for tool catalog. Merge-safe idempotent operations |
| `seed.py` | 194 | Bootstraps `usage.json` and `feedback.json` with realistic synthetic data |

### Agentic Reasoning & Cognitive Search (v6–v7) — 3 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `reason.py` | 2,082 | Two reasoning modes: `deep_reason()` (v1 lite) and `deep_reason_v2()` (full consciousness stack integrating all v3–v22 modules). Plan→Act→Observe→Reflect loop. LLM-backed + local synthesis fallback |
| `retrieval.py` | 519 | Dual-encoder hybrid retrieval: BM25 sparse + dense vector scoring fused via Reciprocal Rank Fusion. IR evaluation metrics (NDCG@k, precision, recall, F1) |
| `graph.py` | 636 | In-memory property graph (GraphRAG): tools as nodes, typed relationships (integrates, competes, supplements). Community detection, traversal, path explanation, vertical stack filtering |
| `prism.py` | 970 | Three-agent iterative search: **Analyzer** (query decomposition) → **Selector** (evidence scoring) → **Critic** (hallucination audit, self-critique). Sub-question tracking |

### Vertical Industry Intelligence (v8) — 1 module

| Module | Lines | Purpose |
|--------|------:|---------|
| `verticals.py` | 1,673 | 10+ industry verticals (healthcare, legal, agriculture, construction, education, manufacturing, logistics, real estate, non-profit, government). Regulatory frameworks (HIPAA, SOX, GDPR, FERPA, FDA). Anti-pattern detection, workflow taxonomy, constraint reasoning |

### Safety, Guardrails + Resilience (v9–v10) — 3 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `guardrails.py` | 991 | **Chain-of-Responsibility pipeline**: ToxicityFilter → PIIMasker → PromptInjectionDetector → SchemaValidator → HallucinationDetector → CodeInjectionDetector. Severity/Verdict enums |
| `orchestration.py` | 931 | Event-driven architecture intelligence: stack recommendations, design pattern matching, performance constraint analysis. Meta-recommendation engine |
| `resilience.py` | 1,067 | Vibe-coding risk scoring, hallucination catalog, static analysis recommendations, sandbox strategies, TDD cycle, R.P.I. framework, HITL guidance |

### Consciousness Stack (v11–v14) — 5 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `metacognition.py` | 1,159 | Six-layer metacognitive architecture: structural entropy, APVP cycle, code stylometry, drift detection, self-healing economics, GoodVibe framework, RACG |
| `introspect.py` | 846 | **Praxis reads its own source code.** Uses `ast.parse()` to compute cyclomatic complexity, function analysis, structural entropy, import graphs, pathology detection |
| `awakening.py` | 1,095 | Six philosophical recognitions, Value Sensitive Design scoring, leaky abstraction detection, MESIAS risk, supply chain consciousness |
| `authorship.py` | 1,013 | Eight authorship responsibilities, DDD maturity, event sourcing, Strangler Fig, Circuit Breaker patterns, metacognitive agents |
| `enlightenment.py` | 1,139 | Five metaphysical truths → Python design principles, six-stage path. Maps to Identity Map, Observer, Hexagonal Architecture, State Pattern, Clean Architecture |

### Enterprise Cognitive Architecture (v15–v17) — 3 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `conduit.py` | 1,549 | Seven pillars: Decoupling, Memory Stratification (CoALA), Global Workspace Theory, IIT (Φ), Representation Engineering, Autopoiesis, CODES Resonance. Seven telemetry metrics |
| `resonance.py` | 1,266 | Five pillars: Temporal Substrate, Code Agency (MCP), Latent Steering, Conductor Dashboard, Meta-Awareness. TRAP anti-pattern framework, DSRP theory, 7 Wisdom agents |
| `enterprise.py` | 1,196 | Six strategic pillars: Hybrid GraphRAG, Multi-Agent Orchestration, MCP Bus, Data Moat, Monetization, Security Governance. Agent roles (CEO/CTO/CPO/CISO), Medallion tiers, 7 KPI metrics |

### Enterprise Infrastructure (v18) — 10 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `ports.py` | 257 | Hexagonal Architecture contracts via `typing.Protocol`. 10 port interfaces: ToolRepository, LLMProvider, CacheProvider, EventBus, GraphStore, VectorStore, TaskQueue, RateLimiter, AuthProvider, TelemetryProvider |
| `exceptions.py` | 149 | Hierarchical exception taxonomy. Every exception carries machine-readable `code` and optional `detail` → mapped to HTTP status codes |
| `domain_models.py` | 261 | Pydantic v2 domain models: ToolModel, UserProfileModel, IntentModel, ToolRecommendation, StackRecommendation, FeedbackEvent, SearchRequest, ReasonRequest, APIResponse |
| `llm_resilience.py` | 259 | Exponential backoff with jitter, circuit breaker pattern, self-healing validation loop, provider-agnostic retry. Zero-dep |
| `rate_limiter.py` | 294 | Multi-algorithm: Fixed-window, Sliding-window (Redis Sorted-Set style), Token-bucket. Async, zero-dep. FastAPI middleware |
| `auth.py` | 319 | OAuth2/API-key auth. Three modes: `none` (dev), `api_key`, `oauth2` (Bearer JWT). Stdlib hmac/json/base64; PyJWT optional |
| `telemetry.py` | 266 | Structured JSON logging, W3C trace-context propagation, FastAPI request telemetry middleware, LLM call instrumentation |
| `vendor_trust.py` | 266 | Multi-dimensional trust matrix: SOC 2 (0.25), GDPR DPA (0.15), ISO 27001 (0.15), HIPAA BAA (0.10), update frequency (0.15), CVE count (0.10), community health (0.10) |
| `hybrid_retrieval_v2.py` | 371 | HybridRAG Orchestrator v2: BM25 + Dense + GraphRAG + VectorStore → lightweight query routing → Reciprocal Rank Fusion |
| `scoring_optimized.py` | 384 | High-performance TF-IDF: scipy.sparse CSR when available, dict fallback. Thread-safe singleton, batch ingestion support |

### Ingestion, Curation & Trust Pipeline (v19) — 26 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `pipeline_constants.py` | 227 | Five immutable principles: Triple Match, SMB Gate, Trust Decay, Deterministic Health, Async Resilience. Never mutated at runtime |
| `ingestion_engine.py` | 1,035 | Core pipeline orchestrator: Apify polling (TAAFT/Toolify/Futurepedia), Triple Match verification, signal enrichment (Wayback/G2/PredictLeads), tier assignment, HITL queue, weekly promotion sweep |
| `trust_decay.py` | 600+ | 11 detection methods (pricing diffs, sentiment, SSL, DNS, breach, shutdown, complaints, outage, PE acquisition, free tier removal). MILD/SEVERE alerts. 72-hour Celery sweep |
| `smb_scoring.py` | 515 | 100-point SMB relevance: Vertical Match (0–40), Pricing Accessibility (0–30), Operational Complexity (0–30). Calibrated via logistic regression on 100-tool ground truth |
| `relationship_extraction.py` | 572 | LLM-driven tool relationship extraction for knowledge graph. Confidence gating: ≥0.85 auto, 0.50–0.85 HITL, <0.50 discard |
| `trust_badges.py` | 1,402 | 9 badge categories: sovereignty_tier, safe_harbor, training_lock, opt_out, compliance, uptime, portability, PSR, risk_flag. Trust score 0–100 |
| `sovereignty.py` | 471 | Geopolitical risk: corporate lineage, backend infrastructure, model origins. Three tiers: US-owned (Green), Allied (Blue), Foreign (Red) |
| `nutrition.py` | 295 | "AI Nutrition Facts" labels: model provenance, training data, retention, compliance, sovereignty, outcomes |
| `outcomes.py` | 376 | Outcome-oriented advisory: time_saved, cost_reduction, revenue_growth, compliance intent detection. Underwhelm Prevention on vague queries |
| `prompt_assist.py` | 526 | DMN-guided prompt decomposition + PromptBridge cross-model transfer. Template-based, zero-latency, no LLM calls |
| `differential.py` | 1,096 | Elimination-first pipeline: generate differential → hard prune → soft penalize → rank survivors. Every elimination logged with reason code |
| `agent_sdk.py` | 619 | AI Agent Integration SDK: exposes Praxis as "tool oracle" for LangChain, AutoGen, CrewAI, OpenAI/Anthropic tool-use |
| `contributions.py` | 452 | Open tool submission API: Submit → Validate → Queue → Review → Publish. Leaderboard with badges |
| `governance.py` | 517 | Enterprise control plane: usage tracking, cost aggregation, audit log, policy enforcement, team management |
| `marketplace.py` | 314 | Workflow template marketplace: save/share/rate/discover templates, featured collections |
| `connectors.py` | 437 | Pluggable tool adapter framework. Stub-first (dry-run). Built-in: Slack, OpenAI, Google Sheets, Salesforce, Zapier |
| `compliance.py` | 526 | Regulatory mapping (EU AI Act, HIPAA, GDPR), immutable audit trails (crypto-timestamped), dynamic PII/PHI masking |
| `observability.py` | 491 | OpenTelemetry-style tracing, chain-of-thought parsing, interactive reasoning trees, telemetry aggregation |
| `cognitive.py` | 568 | Global Workspace Theory (Baars 1988), IIT (Tononi Φ), structural entropy. Multi-agent orchestration as cognitive theater |
| `codes_resonance.py` | 518 | CODES framework (Chirality, Organization, Dynamics, Evolution, Synergy). Prime-structured resonance, autopoiesis, coherence gradients |
| `dsrp_ontology.py` | 350 | DSRP Theory (Distinctions, Systems, Relationships, Perspectives) + O-Theory structural ontology. Pre-execution filter |
| `anti_patterns.py` | 438 | TRAP framework (Bag of Agents, Context Stuffing, Sophistication Trap, AI Precision). Vibe-coding risk, Shadow AI prevention |
| `ast_security.py` | 745 | AST introspection security hardening: RCE prevention, algorithmic DoS, forbidden builtins, resource exhaustion. Parse-only, whitelist-based, fail-closed |
| `ai_economics.py` | 585 | Token cost attribution, ROI calculation, utilization tracking, per-user/department/workflow budget management |
| `stress.py` | 523 | High-concurrency stress testing: endpoint profiling (p50/p95/p99), load driver, async/sync classifier, regression detection |
| `verification.py` | — | Resilience verification and tiering: sovereign → durable → wrapper classification |

### Multi-Model Ecosystem (v20) — 6 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `model_registry.py` | 500+ | Unified LLM model catalog: ModelSpec, ModelTier (dynamic), PrivacyLevel, ModelCapability. 8 providers, singleton registry |
| `llm_provider.py` | 618 | Unified provider abstraction: OpenAI, Anthropic, Google, XAI, Local (Ollama/vLLM), LiteLLM. Dry-run default. API keys from env only |
| `model_trust_decay.py` | 534 | 4 decay signals for models: hallucination rate, quality drift, latency degradation, cost creep. Feeds back into ModelRegistry |
| `model_router.py` | 507 | Elimination pipeline for LLM selection: parse intent → hard-eliminate → soft-penalize → route (single or multi-model) |
| `ecosystem.py` | 748 | Multi-model collaboration: Sequential Chain, Fan-Out/Fan-In, Specialist Routing, Adversarial Review. Cost tracking via ai_economics |
| `shared_state.py` | 376 | CoALA + Relay memory: Working/Episodic/Semantic/Procedural layers. Trust-weighted reads. TF-IDF relevance gating |

### Context Intelligence + Outcome Tracking (v21–v22) — 3 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `context_engine.py` | 400+ | Multi-stage context extraction: field-level confidence scoring via C(P) formula, tier assignment (T1/T2/T3), graph enrichment, vertical intelligence integration |
| `residual_gap.py` | 350+ | Dependency-tree gap analysis: cascade levels (blocking/branching/refinement), skip rules, minimal question set, dependency ordering |
| `journey.py` | 570+ | Passive lifecycle oracle: 5-stage state machine, TargetScoreVector at SELECTION, drift detection at OUTCOME, aggregate dashboard |

### Utility Modules — 10 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `badges.py` | 166 | Community reputation badges: "Rising Star", "Budget Champion", "Integration King", "Power User Pick" |
| `compare_stack.py` | 240 | Current stack vs. Praxis-optimized alternative with cost/risk/integration density analysis |
| `diagnostics.py` | 122 | Query failure tracking — identifies coverage gaps and unserved needs |
| `healthcheck.py` | 177 | Tool health monitoring — feedback trends, freshness, risk alerts, alternatives |
| `migration.py` | 351 | Step-by-step migration planners: pre-checklist, data portability, risk assessment, bridge tools |
| `monetise.py` | 270 | Affiliate links, user-generated benchmarks, weekly AI digest email system |
| `playground.py` | 262 | Integration compatibility simulator — native/API/Zapier/webhook detection, bridge suggestions |
| `readiness.py` | 288 | AI readiness scoring 0–100: maturity assessment, next-step recommendations, learning resources |
| `whatif.py` | 182 | What-if simulator — re-runs recommendations with modified parameters, shows delta |
| `workflow.py` | 390 | Workflow advisor — generates sequenced playbooks with time savings, cost projections, integration tips |

### API Layer — 3 modules

| Module | Lines | Purpose |
|--------|------:|---------|
| `api.py` | 4,384 | Master FastAPI app: creates routes, imports all modules with graceful degradation, serves frontend |
| `api_routes_core.py` | 1,790 | Core API route registration. Dependency injection pattern. Admin guard via auth middleware |
| `api_routes_features.py` | 600+ | Feature/operations routes: health, badges, migration, whatif, benchmarks, digest, context endpoints |

---

## Directory & File Map

```
praxis/
├── __init__.py              Package init, structured logging, __all__ (58 exports)
│
├── ── Core Decision Engine (v1–v2) ──────────────────────
├── engine.py                Multi-signal scoring & ranking
├── interpreter.py           LLM + rule-based intent parsing
├── stack.py                 Multi-tool stack composer
├── explain.py               Explanation generator
├── profile.py               User profile management
├── learning.py              Feedback-to-signal loop
├── config.py                Centralized configuration
├── tools.py                 Tool data class (14+ fields)
├── data.py                  246-tool knowledge base
├── storage.py               SQLite persistence
├── feedback.py              Feedback recording
├── usage.py                 Popularity tracking
├── main.py                  CLI interface
│
├── ── Intelligence & Philosophy (v3–v5) ─────────────────
├── intelligence.py          Zero-dep NLP brain
├── philosophy.py            Vendor risk intelligence
├── ingest.py                CSV/JSON import-export
├── seed.py                  Synthetic data bootstrapping
│
├── ── Agentic Reasoning & Cognitive Search (v6–v7) ──────
├── reason.py                Plan→Act→Observe→Reflect engine
├── retrieval.py             BM25 + dense + RRF retrieval
├── graph.py                 In-memory knowledge graph (GraphRAG)
├── prism.py                 Multi-agent search (3 agents)
│
├── ── Industry & Safety (v8–v10) ────────────────────────
├── verticals.py             10+ industry verticals + regulatory
├── guardrails.py            Chain-of-responsibility safety
├── orchestration.py         Event-driven architecture intelligence
├── resilience.py            Vibe-coding risk detection
│
├── ── Consciousness Stack (v11–v14) ─────────────────────
├── metacognition.py         Self-awareness, APVP, GoodVibe
├── introspect.py            Real AST self-analysis
├── awakening.py             Conscious design, 6 recognitions
├── authorship.py            8 responsibilities, DDD, ADRs
├── enlightenment.py         5 truths, 6 stages, Clean Arch
│
├── ── Enterprise Cognitive Architecture (v15–v17) ───────
├── conduit.py               Decoupled cognitive ecology
├── resonance.py             Human-machine resonance
├── enterprise.py            Billion-dollar decision engine
│
├── ── Enterprise Infrastructure (v18) ───────────────────
├── ports.py                 Hexagonal Architecture contracts
├── exceptions.py            Exception taxonomy
├── domain_models.py         Pydantic v2 domain models
├── llm_resilience.py        Circuit breaker + backoff
├── rate_limiter.py          Multi-algorithm rate limiting
├── auth.py                  OAuth2 / API-key auth
├── telemetry.py             Structured logging + tracing
├── vendor_trust.py          Multi-dimensional trust matrix
├── hybrid_retrieval_v2.py   HybridRAG orchestrator v2
├── scoring_optimized.py     High-performance TF-IDF
│
├── ── Ingestion & Curation Pipeline (v19) ───────────────
├── pipeline_constants.py    5 immutable pipeline principles
├── ingestion_engine.py      Core pipeline orchestrator
├── trust_decay.py           11-signal trust decay monitor
├── smb_scoring.py           100-point SMB relevance gate
├── relationship_extraction.py  Knowledge graph extraction
├── trust_badges.py          9-category trust badge system
├── sovereignty.py           Geopolitical risk detection
├── nutrition.py             AI Nutrition Facts labels
├── outcomes.py              Outcome-oriented advisory
├── prompt_assist.py         DMN prompt decomposition
├── differential.py          Elimination-first pipeline
├── verification.py          Resilience tier classification
├── agent_sdk.py             AI Agent SDK (LangChain/AutoGen/CrewAI)
├── contributions.py         Open tool submission API
├── governance.py            Enterprise control plane
├── marketplace.py           Workflow template marketplace
├── connectors.py            Pluggable tool adapters
├── compliance.py            Regulatory mapping + audit trails
├── observability.py         OpenTelemetry-style tracing
├── cognitive.py             GWT + IIT cognitive architecture
├── codes_resonance.py       CODES resonance framework
├── dsrp_ontology.py         DSRP theory ontology
├── anti_patterns.py         TRAP framework + Shadow AI
├── ast_security.py          AST security hardening
├── ai_economics.py          Token cost + budget management
├── stress.py                Stress testing harness
│
├── ── Multi-Model Ecosystem (v20) ───────────────────────
├── model_registry.py        Unified LLM model catalog
├── llm_provider.py          Multi-provider abstraction
├── model_trust_decay.py     Model trust decay monitor
├── model_router.py          Elimination-first model routing
├── ecosystem.py             Multi-model collaboration
├── shared_state.py          CoALA + Relay shared memory
│
├── ── Context Intelligence (v21–v22) ────────────────────
├── context_engine.py        Confidence-tiered context extraction
├── residual_gap.py          Residual gap question engine
├── journey.py               Journey oracle + drift monitor
│
├── ── API Layer ─────────────────────────────────────────
├── api.py                   Master FastAPI app (493 routes)
├── api_routes_core.py       Core route registration
├── api_routes_features.py   Feature route registration
│
├── frontend/                33 files — Liquid Glass UI
│   ├── home.html            Primary UI with glassmorphism
│   ├── journey.html         Guided journey wizard (4 steps)
│   ├── tools.html           Tool catalog browser
│   ├── differential.html    Elimination pipeline visualizer
│   ├── conduit.html         The Listening Post
│   ├── resonance.html       The Conductor
│   ├── enterprise.html      Enterprise dashboard
│   ├── trust_badges.html    Trust badge explorer
│   ├── sovereignty.html     Sovereignty risk dashboard
│   ├── pipeline.html        Ingestion pipeline monitor
│   ├── governance-center.html  Governance control center
│   ├── economics-hub.html   AI economics dashboard
│   ├── observability-console.html  Observability console
│   ├── cognitive-dashboard.html  Cognitive architecture viewer
│   ├── knowledge-explorer.html  Knowledge graph explorer
│   ├── reasoning-router.html  Reasoning router UI
│   ├── stack-advisor.html   Stack advisor
│   ├── agent-orchestration.html  Agent orchestration UI
│   ├── manifesto.html       Assessment methodology
│   ├── fort-knox.html       Security philosophy
│   ├── rfp.html             RFP generator
│   ├── codes-resonance.html CODES resonance visualizer
│   ├── dsrp-ontology.html   DSRP ontology viewer
│   ├── coala-memory.html    CoALA memory dashboard
│   ├── mesias-governance.html  MESIAS governance
│   ├── repe-transparency.html  RepE transparency
│   ├── tuesday-test.html    Tuesday test
│   ├── category.html        Category browser
│   ├── index.html           Legacy search interface
│   ├── script.js            Search logic
│   ├── journey-script.js    Journey wizard logic
│   ├── tools-script.js      Tool catalog loader
│   └── conduit-script.js    Conduit UI handler
│
├── tests/                   15 files, 645 test functions
│   ├── test_smoke.py              20 core search tests
│   ├── test_engine.py             1 engine test
│   ├── test_interpreter.py        1 interpreter test
│   ├── test_conduit.py            33 conduit tests
│   ├── test_resonance.py          47 resonance tests
│   ├── test_enterprise.py         55 enterprise tests
│   ├── test_enterprise_infra.py   45 v18 infra tests
│   ├── test_platform_v19.py       43 v19 platform tests
│   ├── test_stress_hardening_v20.py  75 v20 stress tests
│   ├── test_v21_enterprise_cognitive.py  113 v21 tests
│   ├── test_v22_cognitive_resilience.py  124 v22 tests
│   ├── test_v23_public_surface.py  85 public surface tests
│   └── test_risk_guardrails.py    3 risk guardrail tests
│
├── journey_data/            Journey oracle persistence (auto-created)
├── pyproject.toml           Package config (praxis-cli v2.0.0)
├── praxis.bat               Windows CLI launcher
└── tools.db                 SQLite cache (auto-generated, in .gitignore)

docs/
├── FORT_KNOX_BLUEPRINT.md   Security blueprint
├── PIPELINE_BLUEPRINT_V3.md Ingestion pipeline design doc
├── SECURITY_PHILOSOPHY.md   Security philosophy
└── adr/                     Architecture Decision Records

scripts/                     Utility scripts
```

---

## API Reference

### Route Summary by Domain

| Domain | Routes | Key Paths |
|--------|-------:|-----------|
| Core (search, stack, profile, feedback) | ~25 | `/search`, `/stack`, `/compare`, `/profile`, `/feedback` |
| Intelligence & Philosophy | ~8 | `/intelligence/{tool}`, `/seeing/{tool}`, `/vendor-report/{name}` |
| Import/Export | ~4 | `/tools/import/json`, `/tools/import/csv`, `/tools/export` |
| Reasoning (agentic + cognitive) | ~3 | `/reason`, `/cognitive`, `/hybrid` |
| Graph (knowledge graph) | ~7 | `/graph/stats`, `/graph/tool/{name}`, `/graph/path/{a}/{b}` |
| Verticals (industry) | ~8 | `/verticals`, `/verticals/detect`, `/verticals/constraints` |
| Guardrails + Orchestration | ~14 | `/guardrails/validate`, `/orchestration/analyze` |
| Resilience | ~12 | `/resilience/assess`, `/resilience/vibe-coding-risk` |
| Metacognition + Introspect | ~24 | `/metacognition/assess`, `/introspect/diagnose` |
| Awakening | ~15 | `/awakening/assess`, `/awakening/vsd`, `/awakening/mesias` |
| Authorship | ~18 | `/authorship/assess`, `/authorship/ddd`, `/authorship/agent-readiness` |
| Enlightenment | ~21 | `/enlightenment/assess`, `/enlightenment/truths` |
| Conduit | ~25 | `/conduit/assess`, `/conduit/telemetry/*` |
| Resonance | ~25 | `/resonance/assess`, `/resonance/trap`, `/resonance/dsrp` |
| Enterprise | ~28 | `/enterprise/assess`, `/enterprise/kpi/*`, `/enterprise/agent-roles` |
| Sovereignty + Trust Badges | ~10 | `/sovereignty/assess`, `/trust-badges/{tool}` |
| Ingestion Pipeline | ~8 | `/pipeline/status`, `/pipeline/queue`, `/pipeline/approve` |
| Context + Journey | ~6 | `/context/extract`, `/context/resolve`, `/journey/*` |
| Utility (health, badges, migration, whatif) | ~20 | `/health`, `/badges`, `/migration-plan`, `/whatif` |
| Governance + Compliance | ~10 | `/governance/dashboard`, `/compliance/posture` |
| Economics + Marketplace | ~8 | `/economics/dashboard`, `/marketplace/templates` |
| Observability + Diagnostics | ~6 | `/observability/report`, `/diagnostics/summary` |
| **Total** | **~493** | |

### Core Endpoints (most frequently used)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serves frontend UI |
| `GET` | `/categories` | List all tool categories |
| `GET` | `/tools` | Full tool catalog with metadata |
| `POST` | `/search` | Profile-aware tool search |
| `POST` | `/stack` | Composed AI tool stack with explanations |
| `POST` | `/compare` | Side-by-side tool comparison |
| `POST` | `/profile` | Create/update user profile |
| `GET` | `/profile/{id}` | Retrieve user profile |
| `POST` | `/feedback` | Record accept/reject/rate feedback |
| `POST` | `/reason` | Full agentic reasoning |
| `POST` | `/cognitive` | Cognitive search (full consciousness stack) |
| `POST` | `/context/extract` | Context extraction with confidence tiers |
| `POST` | `/context/resolve` | Resolve gap questions |
| `GET` | `/health` | System health status |

---

## Frontend

29 static HTML pages + 1 React SPA implementing the Liquid Glass UI design system with glassmorphism, dark theme, and responsive layouts. Static pages served directly by FastAPI. Room SPA built with Vite/React and served from `/room`.

### Key Pages

| Page | Description |
|------|-------------|
| `home.html` | **Primary UI** — Command card search, category chips, tool browsing with glassmorphism effects |
| `/room` | **Room SPA** — Persistent AI workspace with director controls, pin/pass tool actions, stack builder, multi-query sessions |
| `/journey` | **Guided Journey** — 5-step wizard: task → industry → budget → skill → personalized stack |
| `tools.html` | **Tool Catalog** — Browse all 246 tools with category filtering, curated/data-table views |
| `differential.html` | **Elimination Pipeline** — Visual display of differential diagnosis results |
| `trust_badges.html` | **Trust Badges** — Explore 9-category trust assessment per tool |
| `tuesday-test.html` | **ROI Calculator** — "The Tuesday Test" — data-driven AI tool ROI estimator |
| `rfp.html` | **RFP Builder** — Generate AI tool procurement RFPs |
| `sovereignty.html` | **Sovereignty Risk** — Geopolitical risk dashboard |
| `pipeline.html` | **Ingestion Pipeline** — Monitor tool ingestion, review queue, promotion status |
| `governance-center.html` | **Governance** — Enterprise control plane: usage, costs, policies |
| `conduit.html` | **The Listening Post** — Conduit cognitive assessment dashboard |
| `resonance.html` | **The Conductor** — Resonance assessment with real-time telemetry |
| `enterprise.html` | **Enterprise Engine** — Six-pillar enterprise assessment |
| `manifesto.html` | **Methodology** — Assessment methodology and philosophical foundations |

### Room SPA (`/room`)

The Room is a React-based persistent workspace where users direct AI tool evaluation like an orchestra conductor.

- **Command Card Input** — Floating frosted-glass card with Find/Compare/Explain mode buttons, constraint chips (Budget, Team, Compliance, Industry), and circular submit button
- **Director Actions** — Pin (add to stack) and Pass (dismiss) buttons on each tool card. Pinned tools appear in the right panel "Your Stack" with copy-to-clipboard
- **Pipeline Visualization** — Real-time activity feed with auto-collapse to summary line after completion
- **Multi-Query Sessions** — Previous query results archive and collapse; new queries take center stage
- **SSE Streaming** — Real-time execution via `/room/{id}/stream` with cost tracking

### Design System

Canonical navigation across all pages: `Praxis | Search | Diagnosis | Trust Badges | All Tools | ROI Calculator | RFP Builder | Methodology`

| Token | Value |
|-------|-------|
| `--accent` | `#6366f1` (indigo) — all primary CTAs |
| `--accent-secondary` | `#50e3c2` (teal) — data/tier display only |
| `--accent-danger` | `#ef4444` — warnings only |
| `--bg-primary` | `#0a0a0f` |
| `--radius-card` | `20px` |
| `--radius-pill` | `999px` |
| Nav background | `rgba(6, 6, 14, 0.75)` with `backdrop-filter: blur(20px)` |

---

## Test Suite

```
praxis/tests/
├── test_smoke.py                    20 tests  — Core search, budget, verticals, negation, multi-intent, typos
├── test_engine.py                    1 test   — Basic find_tools() smoke
├── test_interpreter.py               1 test   — Basic interpret() smoke
├── test_conduit.py                  33 tests  — All 14 sub-scorers, telemetry, pillars
├── test_resonance.py                47 tests  — Pillar scorers, TRAP, DSRP, wisdom agents
├── test_enterprise.py               55 tests  — 6 pillars, 7 KPIs, agent roles, medallion
├── test_enterprise_infra.py         45 tests  — v18 infrastructure (auth, rate limiter, telemetry, ports)
├── test_platform_v19.py             43 tests  — v19 platform (pipeline, governance, connectors, marketplace)
├── test_stress_hardening_v20.py     75 tests  — v20 stress (model registry, ecosystem, shared state)
├── test_v21_enterprise_cognitive.py 113 tests  — v21 cognitive (context engine, residual gap, economics)
├── test_v22_cognitive_resilience.py 124 tests  — v22 cognitive resilience
├── test_v23_public_surface.py       85 tests  — Public surface (badges, sovereignty, nutrition, outcomes)
├── test_risk_guardrails.py           3 tests  — Risk guardrail integration
                                    ─────────
                                    645 total — all passing

Root-level test files:
├── test_differential.py              — Differential engine integration tests (direct execution)
├── test_safeguards.py                — Safeguard validation (direct execution)
```

Run with:
```bash
python -m pytest praxis/tests/ -v
```

**Note:** Delete `praxis/tools.db` before running tests if tool counts seem wrong — this is a stale SQLite cache issue.

---

## Quick Start

### Prerequisites
- Python 3.10+ (developed on 3.14.3)
- (Optional) OpenAI or Anthropic API key for LLM-powered interpretation

### Install

```bash
git clone https://github.com/2654-zed/praxis-ai.git
cd praxis-ai
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .

# Optional: LLM support
pip install openai anthropic
```

### CLI

```bash
praxis
# or
python -m praxis.main
```

### API Server

```bash
uvicorn praxis.api:app --reload --port 8000
# or on Windows:
run_api.bat
```

Open `http://localhost:8000` for the Liquid Glass UI.

### Key CLI Commands

| Command | Description |
|---------|-------------|
| *(any text)* | Quick search (e.g., "I need a writing tool for healthcare") |
| `profile` | Build a user profile interactively |
| `stack` | Guided stack recommendation |
| `reason <query>` | Full agentic reasoning with multi-step research |
| `compare ChatGPT vs Claude` | Side-by-side tool comparison |
| `learn` | Run learning cycle from feedback |
| `diagnose` | Self-introspection (Praxis analyzes its own code) |
| `badges` | View community reputation badges |
| `health` | System health check |
| `whatif` | Parameter tweaking simulator |
| `workflow` | Get step-by-step workflow playbook |
| `migrate` | Tool migration planner |
| `readiness` | AI readiness scoring |

---

## Configuration

Set environment variables or create `config.json` in the `praxis/` directory:

```bash
# LLM provider (optional — Praxis works fully without one)
export PRAXIS_LLM_PROVIDER=openai     # or "anthropic" or "none"
export PRAXIS_OPENAI_API_KEY=sk-...
export PRAXIS_OPENAI_MODEL=gpt-4o-mini

# Anthropic
export PRAXIS_ANTHROPIC_API_KEY=sk-ant-...
export PRAXIS_ANTHROPIC_MODEL=claude-3-haiku-20240307

# Log level
export PRAXIS_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR

# Authentication mode
export PRAXIS_AUTH_MODE=none           # none, api_key, oauth2

# Scoring weights (tunable)
export PRAXIS_WEIGHT_CATEGORY_MATCH=4
export PRAXIS_WEIGHT_TAG_MATCH=3
export PRAXIS_WEIGHT_KEYWORD_MATCH=2
export PRAXIS_WEIGHT_TFIDF_SCALE=8

# Context engine thresholds
export PRAXIS_CONTEXT_ALPHA=0.25       # term match weight
export PRAXIS_CONTEXT_BETA=0.30        # graph distance weight
export PRAXIS_CONTEXT_GAMMA=0.25       # syntactic proximity weight
export PRAXIS_CONTEXT_DELTA=0.20       # explicit match weight
export PRAXIS_CONTEXT_TIER1_THRESHOLD=0.90
export PRAXIS_CONTEXT_TIER2_THRESHOLD=0.60

# Rate limiting
export PRAXIS_RATE_LIMIT_RPM=60
```

Without an LLM key, Praxis falls back to its enhanced rule-based interpreter. All NLP intelligence (synonyms, TF-IDF, typo correction, multi-intent) works **zero-dependency**.

### Full Config Defaults

See `config.py` — all 35+ configuration keys with defaults. Priority: env var (`PRAXIS_*`) → `config.json` → hardcoded defaults.

---

## Key Architectural Decisions

### 1. Zero External ML Dependencies
All NLP, retrieval, graph, and scoring implemented from scratch. No numpy, scikit-learn, PyTorch, or transformers.
- Instant startup (no model loading)
- Universal deployment (any Python 3.10+ environment)
- Full auditability (every scoring decision is traceable)

### 2. Graceful Degradation via Import Guards
Every module beyond the core uses a try/except import pattern:
```python
try:
    from .conduit import assess_conduit as _assess_conduit
except Exception:
    _assess_conduit = None  # graceful fallback
```
Praxis runs even if modules fail to import. The API checks `if _assess_conduit:` before exposing endpoints.

### 3. Dual Import Paths (Package vs. Direct)
```python
try:
    from .module import function  # package import
except Exception:
    from module import function   # direct import (standalone)
```
Enables both `python -m praxis.main` and `python praxis/main.py`.

### 4. Pure-Function Scoring
`score_tool(tool, keywords)` has no side effects, no global state mutation. Testable, composable, concurrent-safe.

### 5. Composite Assessment Pattern
Every module from v9+ follows:
1. Multiple sub-scorers (5–14 each) return 0.0–1.0
2. Master `assess_*()` computes weighted composite
3. Warnings/recommendations from threshold analysis
4. Assessment dataclass bundles scores + composite + metadata

### 6. Hexagonal Architecture (v18+)
Abstract ports in `ports.py` define contracts via `typing.Protocol`. Adapters satisfy the shape without inheritance. Core domain knows nothing about FastAPI/SQLAlchemy/Redis/Neo4j.

### 7. Consciousness-Inspired Scoring
The v12–v16 modules use philosophical frameworks as concrete scoring dimensions:
- **Awakening**: 6 recognitions → architectural principle scores
- **Enlightenment**: 5 truths → design pattern scores (Hexagonal, Clean Arch, FSM)
- **Conduit**: Cognitive science (IIT, GWT, CoALA) → telemetry metrics
- **Resonance**: Relationship engineering → 7 numeric telemetry outputs

These are not metaphors — they are deterministic scoring functions with numeric outputs that feed into the reasoning pipeline via `deep_reason_v2()`.

---

## Known Technical Patterns

### The tools.db Stale Cache Problem
`data.py` stores the `TOOLS` list in-memory. On first import, `storage.py` may cache it to `tools.db`. If you modify `data.py`, delete `praxis/tools.db`. It's in `.gitignore`.

### Import Alias Convention in api.py
```python
from .conduit import assess_conduit as _assess_conduit
from .resonance import assess_resonance as _assess_resonance_v16  # avoids collision
```

### deep_reason vs deep_reason_v2
- `deep_reason()` — Original v6 reasoning (lighter, faster)
- `deep_reason_v2()` — Full consciousness stack: integrates all v3–v22 modules. This is what `/cognitive` calls.

### Import Flag Pattern
```python
_CONDUIT_OK = True   # set if import succeeds
_CONDUIT_OK = False  # set in except block
```
`deep_reason_v2` checks these flags before invoking enrichment.

---

## Known Limitations

1. **No real-time external API calls** — Trust decay monitoring (Wayback CDX, G2 scraping, SSL checks) requires external network access and is designed for scheduled batch runs, not inline with user requests.

2. **Multi-model ecosystem is dry-run** — `llm_provider.py` returns mock responses by default. Real model calls require API keys for each provider.

3. **No persistent user sessions** — Profiles are stored in JSON files. No database-backed user management, no session tokens for frontend.

4. **Single-machine architecture** — No distributed state, no Redis/Celery in default config. The sync fallback works but doesn't scale horizontally.

5. **Tool catalog is manually curated** — 246 tools in `data.py` are hand-maintained. The `ingestion_engine.py` pipeline for automated ingestion is architecturally complete but not running in production.

6. **Frontend is mostly server-rendered static** — 29 HTML pages served as static files by FastAPI. The Room (`/room`) is a React SPA built with Vite — requires `npm run build` in `praxis/frontend/room/` after changes.

7. **Test coverage is module-clustered** — 645 tests cover v1–v23 features well, but some v19 modules (connectors, marketplace, contributions) have lighter coverage.

---

## Roadmap

### Completed

**v24 — Room & Design System (March 13, 2026)**
- [x] Room SPA — React workspace at `/room` with SSE streaming, multi-query sessions
- [x] Director experience — Pin/Pass tool actions, "Your Stack" panel, copy-to-clipboard
- [x] Command card input — Mode buttons, constraint chips, circular submit
- [x] Click-to-expand tool card detail drawers (pricing, integrations, compliance, limitations)
- [x] Drag-and-drop stack reordering with role labels (Primary/Companion/Infrastructure)
- [x] Tool logo favicons via Google Favicon API with letter-circle fallback
- [x] Canonical nav bar audit across all 28 static HTML pages
- [x] Search dropdown layout fixes (z-index, overflow, bleed-through)
- [x] 7 new tools added (Microsoft Agent Framework, MiroFish, Grok 4.20, Perplexity Computer, Replit Agent, Lindy.ai, ASCN.AI)
- [x] 472 tool data quality fixes (skill levels, base models, keyword dedup, casing)

**v25 — Split Verdict + Latent Flux Integration (March 14, 2026)**
- [x] Complete Room SPA rebuild — Split Verdict layout (narrow verdict sidebar + wide evidence panel)
- [x] Hero search input with two-state design (centered hero → collapsed top bar)
- [x] Shared Command Bar for homepage and Room (mode toggles, parameter chips, live elimination funnel, session history, explore grid)
- [x] Latent Flux integration — pure-Python orchestration reliability monitor (ToolReservoir, PipelineHealthCompetitor, RetryLoopDetector, OrchestrationMonitor)
- [x] σ² variance tracking in ReservoirState for early behavioral drift detection
- [x] LF wired into trust_decay.py (basin-based severity replaces threshold comparison)
- [x] LF wired into journey.py (reservoir-based drift detection replaces simple delta)
- [x] LF wired into llm_resilience.py (σ-based circuit breaker trip at deviation ≥ 4.0)
- [x] Journey Oracle REST API — 6 endpoints for lifecycle tracking and drift monitoring
- [x] Auto-journey middleware — automatic stage recording from /search, /stack, /feedback requests
- [x] Drift-to-learning feedback loop — MODERATE/SEVERE drift auto-corrects scoring in learning.py
- [x] 38 LF integration tests + 51 wiring tests, all passing

### Near-term (next 2-4 weeks)
- [ ] Background scheduler for trust decay sweeps (72-hour cycle) and journey drift corrections
- [ ] Real LLM provider connections — remove dry-run gate when API keys present (OpenAI, Anthropic, Google, XAI, Ollama, DeepSeek, LiteLLM)
- [ ] Room real cost tracking — per-model token breakdown in SSE stream, "Dry run" label when mocked
- [ ] WebSocket broadcast hub for live dashboard updates (trust decay, journey, pipeline, provider health)
- [ ] Activate ingestion_engine.py — scheduled polling with dry-run default, HITL approval queue

### Medium-term (1-3 months)
- [ ] Workflow definition language — extend ecosystem.py collaboration patterns to the full 253-tool catalog
- [ ] Shared project artifacts layer — extend journey.py to hold documents, code, datasets, and decisions across pipeline stages
- [ ] Tool execution adapters — move connectors.py from stub to live for top 10 tools (Slack, OpenAI, Google Sheets, Salesforce, Zapier)
- [ ] Room tab infrastructure — Musicians (current evidence panel) | Artifacts | Pipeline views
- [ ] Persistent user sessions — database-backed profiles, auth, onboarding flow

### Long-term (3-12 months)
- [ ] Full orchestration runtime — Praxis executes multi-tool pipelines, not just recommends them
- [ ] Latent Flux as conductor's ear — real-time behavioral drift detection across live tool execution
- [ ] Developer SDK — third-party tools register with Praxis via standardized input/output contracts
- [ ] Marketplace — workflow templates, specialized agents, automation modules
- [ ] Distributed architecture — Redis state, Celery workers, horizontal scaling
- [ ] Public API with rate-limited free tier

---

## Open Philosophical Questions

These questions have no clean answers. They shape Praxis's design decisions.

1. **Can curation itself be trusted?** Praxis curates AI tools, but who curates the curator? The answer is radical transparency — every scoring signal, every elimination reason, every trust decay alert is inspectable.

2. **Is elimination more ethical than recommendation?** Showing someone what they *shouldn't* use (with evidence) may be more honest than showing them what they *should* use (with hidden biases). But elimination can also be wrong — and incorrect elimination has higher stakes than incorrect ranking.

3. **When does trust monitoring become surveillance?** Tracking pricing page changes, SSL certs, DNS routing, and review sentiment is designed to protect users. But the same infrastructure could be repurposed. The line is: we monitor *vendor behavior*, never *user behavior*.

4. **Should SMB relevance override capability?** A powerful tool that's too complex for a 5-person team might still be the "right" answer for their problem. Praxis currently penalizes complexity mismatch. Should it instead surface the tool with a "you'll need help deploying this" caveat?

5. **How should consciousness-inspired scoring be weighted?** Modules like `conduit.py` and `resonance.py` score tools on dimensions borrowed from cognitive science (IIT, GWT). These dimensions are intellectually coherent but empirically unvalidated for tool selection. How much weight should they carry vs. straightforward keyword matching?

---

## Changelog

### v25.8 — Inline Results (2026-03-14)

Homepage now shows search results inline — no page navigation. The entire product experience is on one page.
- **Submit → inline results**: POST /search, render survivor cards below the search bar. Task grid, pills, paths hide; results replace them.
- **Survivor cards**: Favicon + name + % fit score + description + compliance/pricing badges + "Visit site →" link. Top card gets indigo border + "Top pick" label.
- **Elimination summary**: "253 evaluated · N eliminated · N survived" — centered counts above cards.
- **Feedback row**: Yes/No rating (POST /feedback), Copy results (clipboard), Search again (resets to initial state).
- **Score normalization**: Raw API scores → percentage fit (top result ~95%, proportional below).
- **No navigation**: Enter, → button, and Evaluate 253 all do inline search. Room still accessible via nav bar for power users.
- 714/714 tests pass.

---

### Launch Blocker Fix (2026-03-14)

Fixed 4 bugs: submit paths broken (Enter early-return bug), autocomplete overlap (disabled), subtitle jargon, pill labels.

---

### v25.7 — Homepage Hero Rebuild (2026-03-14)

Replaced the homepage hero section with a task-builder + path-card layout:
- **Task grid** (3x2): Write content, Write code, Analyze data, Automate work, Serve customers, Build an app. Radio selection fills the search input.
- **Constraint pills** (9 toggles): Free tier, Under $50, Under $100, HIPAA, SOC2, GDPR, Beginner, Open source, API access. Simple on/off toggles — no prompt() dialogs.
- **Live summary sentence**: Updates on every task/constraint/keystroke change. Shows "Find {task} that are {constraints} — then eliminate the rest." with an "Evaluate 253 →" submit button.
- **Path cards** (4): Guided journey, Browse catalog, Compare tools, ROI calculator.
- **Footer line**: "253 tools · 11 trust signals · elimination-first methodology"
- Removed: old prompt()-based chip row, explore grid, elimination funnel bars, journey link, static subtitle.

---

### v25.6 — Medium-Term Roadmap: All 5 Items (2026-03-14)

**Item 1: Background Scheduler** — New `praxis/scheduler.py` (pure stdlib `threading.Timer`).
- `BackgroundScheduler` with schedule/start/stop/trigger/pause/resume
- Default tasks: `trust_decay` (72h) and `journey_corrections` (72h)
- API: `GET /scheduler/status`, `POST /scheduler/trigger/{name}`, `POST /scheduler/pause/{name}`, `POST /scheduler/resume/{name}`
- Startup/shutdown hooks via `@app.on_event`

**Item 2: Real Provider Connections** — `PRAXIS_DRY_RUN` env var gate (default: true).
- When false + API keys set, providers make real calls via their SDKs
- `GET /providers/status` — per-provider dict (sdk_installed, api_key_set, dry_run, circuit_state)
- 7 providers: OpenAI, Anthropic, Google, XAI, DeepSeek, Local (Ollama), LiteLLM

**Item 3: Room Cost Tracking** — TopBar shows "Dry run" in dry-run mode, actual `$0.0035` in real mode.

**Item 4: WebSocket Hub** — New `praxis/ws.py` with sync-safe `BroadcastHub`.
- 5 channels: trust_decay, journey, pipeline, scheduler, provider_health
- `ws://host/ws/{channel}` WebSocket endpoint, `GET /ws/status` subscriber counts
- Thread-safe `publish()` bridges sync→async via `asyncio.run_coroutine_threadsafe`

**Item 5: Ingestion Pipeline Activation** — Wired `ingestion_engine.py` into scheduler.
- `PRAXIS_INGESTION_ENABLED=true` to activate (default: false)
- Default interval: 168h (1 week), configurable via `PRAXIS_INGESTION_INTERVAL`
- API: `GET /pipeline/status`, `POST /pipeline/trigger`, `GET /pipeline/queue`, `POST /pipeline/approve/{name}`, `POST /pipeline/reject/{name}`
- Results published to `pipeline` WebSocket channel

**Tests:** 18 new tests (scheduler, providers, WS hub, ingestion, cost). 713/714 full suite (1 pre-existing).

---

### v25.5 — LF Wiring + Roadmap Completion (2026-03-14)

**Workstream 1: journey.py LF integration**
- Per-tool ToolReservoir (d=4) created on `set_target_vector()`, fed on `record_outcome()`
- `detect_drift()` uses reservoir `deviation_score()` when LF available (thresholds: <1.0 NONE, 1-2 MILD, 2-3.5 MODERATE, 3.5+ SEVERE), falls back to threshold-based delta when not
- New methods: `get_reservoir_state()`, `apply_drift_corrections()` (feeds MODERATE/SEVERE signals into learning.py as negative quality feedback)

**Workstream 2: llm_resilience.py LF integration**
- Per-provider ToolReservoir (d=4: latency, error_rate, quality, cost) via `record_provider_metrics()`
- `check_sigma_trip()` — trips circuit breaker when deviation_score >= 4.0 (catches erratic-but-not-fully-failing providers)
- `get_provider_health()` — combined health state (deviation, variance, failures, circuit state)

**Workstream 3a: Journey API endpoints** (added 6 new to api.py)
- `POST /journey/{id}/target` — set target vector at SELECTION
- `GET /journey/{id}/drift` — get drift signals
- `GET /journey/dashboard` — aggregate metrics
- `GET /journey/{id}/reservoir` — LF reservoir state for tools
- `POST /journey/apply-corrections` — apply drift corrections to scoring

**Workstream 3b: Auto-journey middleware**
- `_AutoJourneyMiddleware` auto-creates journeys from `/search` and `/cognitive` POST requests
- Controlled by `PRAXIS_AUTO_JOURNEY` env var (default: true)
- Non-blocking — failures never break the API response

**Workstream 3c: Drift → learning feedback loop**
- `apply_drift_corrections()` records negative feedback for tools with MODERATE/SEVERE drift
- Auto-triggered from `run_trust_sweep()` when journey module is available
- Also callable via `POST /journey/apply-corrections`

**Tests:** 51/51 LF integration tests pass. 694/696 full suite pass (2 pre-existing search ranking issues).

**Roadmap:** All 3 near-term items completed. Latent Flux integration moved to completed.

---

### v25.4 — Latent Flux Integration (2026-03-14)

Integrated Latent Flux geometric computation primitives into Praxis for orchestration reliability monitoring.

**Phase 1 (LF repo):** Added σ² (running variance) tracking to `ReservoirState`. New: `variance`, `std` properties and `deviation_score(x)` method (Mahalanobis-like z-score). Variance resets on `reset()`.

**Phase 2 (Praxis):** New `praxis/lf_monitor.py` — pure-Python (no NumPy) adapter implementing:
- `ToolReservoir` — per-tool ESN behavioral baseline with σ² tracking, power-iteration eigenvalue estimation
- `PipelineHealthCompetitor` — 3-basin attractor (Healthy/Degrading/Failing) classification
- `RetryLoopDetector` — cycle detection with σ-enhanced circuit breaker logic
- `OrchestrationMonitor` — high-level composition managing per-tool reservoirs, pipeline health, and retry detection

**Phase 3:** Wired into `trust_decay.py` with graceful fallback:
- `lf_record_tool_call()` — records per-invocation metrics to ToolReservoir
- `lf_assess_severity()` — basin-based severity (replaces threshold comparison when LF active)
- `lf_get_tool_states()` — serializable tool monitoring state
- Import guarded with try/except — falls back to threshold-based monitoring when unavailable

644/645 tests pass (1 pre-existing search ranking issue).

---

### v25.3 — Shared Command Bar (2026-03-14)

Built a shared "Command Bar" search component used by both homepage and Room SPA.

**Three-layer design:**
- **Layer 1 — Input bar**: Mode toggles (Find/Compare/Analyze) as 32px icon buttons with radio behavior, text input (15px), circular indigo submit button (36px). Glassmorphism background with focus glow.
- **Layer 2 — Parameter chips**: Active constraints show value + x (indigo border), available constraints show as "+ Label" (muted). Clicking opens inline popover. Constraints append to query on submit.
- **Layer 3 — Context area**: Idle (input <3 chars) shows explore grid (Writing 34, Coding 28, Automation 22, Analytics 19) + guided quiz link. Typing (3+ chars) shows live elimination funnel with animated bars (Catalog→Category→Budget→Compliance→Survivors).

**Homepage (home.html):** Replaced `.search-glass` with command bar HTML/CSS/JS. Removed old category chip loader, filter-strip CSS, kinetic placeholder. Explore cards fill input on click. Funnel estimates update per keystroke.

**Room SPA (React):** New `CommandBar.jsx` component with `compact` prop. Empty state renders full command bar centered. TopBar uses `<CommandBar compact />` for the collapsed input. URL params (`?q=...&mode=...`) picked up on Room load.

---

### v25.2 — Hero Search Input (2026-03-14)

Two-state search input for the Room:
- **Empty state**: Full-viewport centered hero input (640px, 52px tall, 16px font) with cycling placeholder examples on 4s intervals, quick-start category chips (Writing, Coding, Marketing, Analytics, No-code, Security), and subtitle text. Homepage glassmorphism styling.
- **Active state**: Input collapses into the top bar (36px, 13px font, 10px radius) with arrow/refresh icon toggle. TopBar shows compact always-editable input between "Praxis" and the pipeline badge.
- Follow-up input restyled: underline separator, placeholder "Ask about these results..."
- App.jsx conditionally renders HeroSearch (idle) vs TopBar+panels (has results)

---

### v25.1 — Swap Panel Widths (2026-03-14)

Swapped verdict/evidence panel proportions:
- **Verdict panel** (left): `flex-1` → `width: 340px` fixed sidebar. Narrative font reduced to 13px.
- **Evidence panel** (right): `width: 360px` → `flex-1` wide area. Non-hero cards now render in a 2-column grid (`grid-cols-2 gap-3`). Hero/top pick stays full-width above the grid.
- Removed description truncation (was `line-clamp-2` + `slice(0,160)`) and compliance badge limit (was `slice(0,4)`)
- Responsive: `<900px` stacks vertically with verdict `max-h-[200px]`; `<700px` grid collapses to 1 column

---

### v25 — Split Verdict Layout (2026-03-14)

**Complete Room SPA rebuild** — replaced 3-panel chat layout with a two-panel "Split Verdict" design.

**New layout:**
- **TopBar** (fixed): Editable query input, pipeline badge ("8 survived / 253"), context chips, cost display, "New" button
- **Left panel — Verdict**: AI narrative prose, inline pipeline progress stages, elimination badges (aggregated by reason code, expandable), follow-up input
- **Right panel — Evidence** (360px): Tool cards sorted by fit score. Top pick gets 2px indigo border, "TOP PICK" label, 24px score, expanded reasoning. All cards have "Add to stack" + "Details" buttons with favicon logos
- **Stack drawer**: Slide-up from bottom of evidence panel with drag-and-drop reorder (reuses framer-motion Reorder)

**New files (7):** `useQuerySubmit.js` hook, `TopBar.jsx`, `VerdictPanel.jsx`, `PipelineProgress.jsx`, `EvidencePanel.jsx`, `EvidenceCard.jsx`, `StackDrawer.jsx`, `FollowUpInput.jsx`

**Rewritten:** `App.jsx` (new component tree)

**Preserved:** RoomContext state management, SSE streaming, room CRUD, pin/unpin/reorder, copy-to-clipboard, ToolDetailDrawer, ReasonCodeBadge, ambient visuals

**Removed from active tree:** LeftPanel, RightPanel, Header, ActivityFeed, PhaseSteps, ContextPanel, TrustMonitor, IntentInput, RoutingPlan, ExecutionStream (files still exist, just not imported)

**Responsive:** Below 900px panels stack vertically; below 600px chips wrap

---

### v24.9 — Tool Logo Favicons (2026-03-13)

Replaced letter-in-circle tool card avatars with actual logos via Google Favicon API (`google.com/s2/favicons?domain={DOMAIN}&sz=64`). Falls back to the original letter circle on favicon load error.

**Files updated:** home.html (search results + sovereign collection), tools.html (premium/moderate/compact cards), category.html, script.js (index.html search), journey-script.js + journey.html, index.html

**Implementation:** `getLogoDomain(url)` extracts domain from tool URL, `<img>` with `onerror` fallback hides logo and shows letter circle. CSS classes: `.tool-logo`, `.sov-logo`, `.tc-logo`/`.tc-logo-sm`/`.tc-logo-xs`, `.stack-logo` — all with `object-fit: contain`, `border-radius`, dark background padding.

---

### v24.8 — 7 New Tools (2026-03-13)

Added 7 fully-profiled AI tools to the catalog (246 → 253 tools):
- **Microsoft Agent Framework** — Open-source SDK unifying Semantic Kernel + AutoGen for multi-agent orchestration (Python/.NET, MIT License)
- **MiroFish** — Open-source swarm-intelligence prediction engine from China using multi-agent simulation (AGPL-3.0, 10.2K GitHub stars)
- **Grok 4.20 Multi-Agent** — xAI's 4-agent parallel debate system (SuperGrok/API only, NOT on Poe)
- **Perplexity Computer** — Multi-model agent orchestration platform using 19+ frontier models ($200/mo Max subscription, launched Feb 25, 2026)
- **Replit Agent** — AI-powered browser IDE that builds full-stack apps from natural language (Agent 4, announced Mar 11, 2026)
- **Lindy.ai** — No-code AI agent builder with 3,000+ integrations for business workflow automation (SOC2 + HIPAA)
- **ASCN.AI** — Crypto-focused AI assistant + no-code automation builder from UAE (Web3 analytics, ArbitrageScanner team)

---

### v24.7 — Tool Data Quality Fixes (2026-03-13)

Fixed 472 issues identified in the tool catalog audit across 246 tools:
- **FIX 1 (HIGH):** `skill_level="expert"` → `"advanced"` on 10 tools (FEniCS, preCICE, NVIDIA PhysicsNeMo, MechStyle, Apache Flink, Opacus, GoodVibe Security, TransformerLens, steering-vectors, Firecracker)
- **FIX 2 (MEDIUM):** Added `base_model` to 11 generative/LLM tools (Midjourney→proprietary, DALL-E→proprietary, Google Gemini→Gemini, Stability AI→Stable Diffusion, DeepSeek-R1, Qwen3-235B, etc.)
- **FIX 3:** Skipped — HIPAA compliance on non-healthcare tools (Salesforce, Slack, etc.) is correct; these offer BAAs
- **FIX 4 (LOW):** Removed redundant `"starter": 0` from 26 tools where `free_tier: True` already communicates free access
- **FIX 5 (LOW):** Normalized 6 keyword casing inconsistencies (claude→Claude, crm→CRM, kafka→Kafka, pydantic→Pydantic, pytest→Pytest, hypothesis→Hypothesis)
- **FIX 6 (LOW):** Removed 270 duplicate keywords that matched tags on the same tool (reduces score inflation)
- Deleted stale `tools.db` SQLite cache

---

### v24.6 — Canonical Nav Audit (2026-03-13)

Unified nav bar across all 28 static HTML pages to match the canonical nav from home.html:
`Praxis | Search | Diagnosis | Trust Badges | All Tools | ROI Calculator | RFP Builder | Room | Methodology`

**22 files fixed:**
- differential.html, trust_badges.html — added missing Room link, fixed nav class/id
- sovereignty.html — replaced 5-link custom nav
- stack-advisor.html — replaced 3-link custom nav
- enterprise.html — added nav (was completely missing)
- conduit.html, index.html, resonance.html — replaced `.nav-links` pattern with canonical `.nav-bar`
- 8 dashboard pages (agent-orchestration, cognitive-dashboard, economics-hub, fort-knox, governance-center, knowledge-explorer, observability-console, pipeline) — replaced dashboard-context nav
- 6 framework pages (coala-memory, codes-resonance, dsrp-ontology, mesias-governance, reasoning-router, repe-transparency) — replaced framework-context nav
- Nav CSS unified: `position: fixed; z-index: 100; backdrop-filter: blur(30px); background: rgba(6,6,14,0.75)`
- Active class set per page (Diagnosis, Trust Badges, All Tools, ROI Calculator, RFP Builder, Methodology); no active on pages without a nav mapping

**6 files verified correct:** category.html, journey.html, manifesto.html, rfp.html, tools.html, tuesday-test.html

---

### v24.5 — Dropdown Overlap Fixes (2026-03-13)

- Footer overlap: `#ambient-footer` now hidden (`display: none`) when dropdown is open, restored on close
- Chip bleed-through: `#filter-bar` set to `visibility: hidden` when dropdown is open, restored on close
- Centralized open/close logic into `openAC()`/`closeAC()` helpers — all 2 open sites and 1 close site use them

---

### v24.4 — Search Bar & Dropdown Bug Fixes (2026-03-13)

**BUG 1: Submit button moved to input row** — `#searchBtn` relocated from `.search-bottom-row` into `.search-main-row` next to the text input, with proper flex gap

**BUG 2: Category chips wrap to two rows** — Removed `overflow-x: auto` and `flex-wrap: nowrap` from `.search-chips-inline`, chips now wrap naturally

**BUG 3: Footer z-index fix** — Lowered `.ambient-footer` from `z-index: 10` to `z-index: 1` so it no longer renders above the dropdown (which lives inside `.hero` at `z-index: 2`)

**BUG 4: Dropdown closes on outside click/scroll** — Widened click handler from `.search-input-wrap` to `.search-container`, added scroll listener that closes dropdown when `scrollY > 100`

**BUG 5: Nav bar scroll reveal** — Added `window.scroll` listener to `updateNav()` — nav now appears when `scrollY > 100` even before a search is performed

---

### v24.3 — Drag-and-Drop Stack Reordering (2026-03-13)

**Room: Drag-and-drop "Your Stack" reordering**
- Drag handle (6-dot grip icon) on each pinned tool — only the handle triggers drag (prevents accidental reorders)
- Uses framer-motion `Reorder.Group`/`Reorder.Item` with `useDragControls` for native animated reordering
- Items shift smoothly (200ms ease-out layout transition) during drag
- Dragged item gets subtle scale-up + indigo border glow + elevated shadow
- Stack role labels auto-assign by position: #1 = Primary (indigo), #2 = Companion (cyan), rest = Infrastructure (muted)
- Copy-to-clipboard output now includes role labels (e.g. "Primary: ToolName")
- Added `REORDER_PINNED_TOOLS` action to RoomContext reducer
- Remove-from-stack still works after reordering

---

### v24.2 — Dropdown Opacity & Prompt Assistance Cleanup (2026-03-13)

**Home: Search dropdown bleed-through fix**
- Replaced `rgba(16,16,28,1)` with solid `#10101c` background on `.ac-dropdown`
- Removed `backdrop-filter: blur(36px)` from dropdown — was causing compositing artifacts when nested inside `.search-glass`'s own `backdrop-filter`
- Removed `opacity` from `acReveal` animation to prevent brief transparency during open
- Changed `overflow-y: auto` to `overflow: hidden auto` for full containment

**Prompt Assistance cleanup**
- Removed dead JS (`loadModels()` IIFE and `generatePrompt()` function) that referenced elements deleted in v24
- Removed leftover HTML/CSS comments about removed section

---

### v24.1 — Tool Detail Drawers & Dropdown Fix (2026-03-13)

**Room: Click-to-expand detail drawers** — Tool cards now expand to reveal full details
- New `ToolDetailDrawer` component: survival reasons, pricing (free/starter/enterprise), integrations chips, compliance badges, trust score bar, limitations list
- Eliminated tool drawers show reason code badge + explanation evidence
- Single-drawer-open constraint: opening one card closes any previously open drawer
- 200ms height animation via framer-motion, no layout jank
- Pin/Pass buttons still work without triggering drawer (event guard via `closest('button')`)
- Chevron indicator (`▸`/rotated) on each card header

**Home: Search dropdown layout fixes**
- Fixed column overlap: switched `.bento-grid` from flex to CSS grid (`grid-template-columns: 1fr 1fr`)
- Fixed z-index bleed: dropdown background made fully opaque (`rgba(16,16,28,1)`)
- Fixed workflows positioning: moved out of right column into full-width grid row (`grid-column: 1 / -1`)
- Fixed text overflow: `.ac-label` gets `overflow: hidden; min-width: 0`
- Fixed bottom stacking: all sections now flow in normal document order via CSS grid
- Added `overflow: hidden` to `.bento-right-col` for containment

---

### v24 — Room & Design System (2026-03-13)

**Room SPA** — New React workspace at `/room`
- Built Room React app (`praxis/frontend/room/`) with Vite, served from `/room`
- Command card input with Find/Compare/Explain modes, constraint chips (Budget, Team, Compliance, Industry), inline popovers, circular submit button
- Director actions: Pin/Pass on tool cards with visual states (indigo border for pinned, 40% opacity for passed)
- Right panel: "Your Stack" — live pinned tool list with copy-to-clipboard
- Activity feed: auto-collapse to summary after DONE, human-voice text replacements
- Multi-query sessions: previous results archive and collapse
- Room rename: single-click input swap, localStorage persistence
- Fixed `room_id` → `id` normalization (eliminated `/room/undefined/stream`)
- Fixed SSE `amount_usd` → `cost_usd` field mismatch for cost tracking
- Filtered internal reasoning text and sub-query failure messages from UI

**Design System Audit** — Unified 9+ pages to canonical design tokens
- Standardized nav across all pages: `Search | Diagnosis | Trust Badges | All Tools | ROI Calculator | RFP Builder | Methodology`
- Fixed differential.html: nav class `brand` → `nav-logo`, bg opacity 0.85 → 0.75
- Fixed trust_badges.html: removed emoji from logo, nav bg, font stack
- Fixed tools.html: unified Fragile/Wrapper chip reds to `#ef4444`, collapse trigger red, placeholder unicode
- Fixed tuesday-test.html: canonical nav, range slider `accent-color`
- Fixed rfp.html: canonical nav links
- Fixed journey.html: added full canonical nav bar, progress bar height 3px → 5px
- Fixed manifesto.html: ls-chip border consistency
- Fixed home.html: removed Prompt Assistance section, footer z-index
- Added `← Praxis` back link to Room header

**Routes**
- Added `/journey` route serving `journey.html` via FastAPI

---

## Contributing

### Adding a New Module (v23+)

1. Create `praxis/new_module.py` with an `assess_*()` master function and sub-scorers
2. Add import to `api.py` (both `from .new_module` and fallback `from new_module` blocks)
3. Add endpoints in `api.py` inside `create_app()`
4. Add import flag in `reason.py` and integrate into `deep_reason_v2()`
5. Add entry to `__init__.py` `__all__`
6. Create `praxis/tests/test_new_module.py`
7. Optionally create `praxis/frontend/new_module.html`

### Adding a New Tool

Edit `data.py` — add a `Tool(...)` entry to the `TOOLS` list. Delete `tools.db` after. No application code changes needed.

### Submitting Changes

```bash
# Run tests
python -m pytest praxis/tests/ -v

# Run the full verification suite
python verify_all.py

# Run the differential test
python test_differential.py
```

### Dependencies

```
fastapi[all]
uvicorn[standard]
# Optional:
openai>=1.0
anthropic>=0.18
pytest  # dev only
```

Everything else is pure Python standard library.

---

## How to Understand the Full Codebase from This README

If you're an AI assistant or engineer encountering this codebase for the first time, here is the reading order:

### Level 1 — Core Loop (30 minutes)
1. Read **engine.py** — understand `score_tool()` (multi-signal scoring, pure function)
2. Read **interpreter.py** — understand how queries become structured intent
3. Read **data.py** (schema only, not all 246 entries) — understand the `Tool` data model
4. Read **stack.py** — understand how individual tools become composed stacks

### Level 2 — Intelligence Layer (30 minutes)
5. Read **intelligence.py** — understand the zero-dep NLP (TF-IDF, synonyms, Levenshtein)
6. Read **retrieval.py** — understand BM25 + dense + RRF fusion
7. Read **graph.py** — understand the knowledge graph (GraphRAG)
8. Read **prism.py** — understand the three-agent search pattern

### Level 3 — Elimination Pipeline (20 minutes)
9. Read **differential.py** — understand elimination-first reasoning (the core innovation)
10. Read **context_engine.py** — understand confidence-tiered context extraction
11. Read **residual_gap.py** — understand the gap question engine

### Level 4 — Trust & Safety (20 minutes)
12. Read **trust_decay.py** — understand 11-signal trust monitoring
13. Read **trust_badges.py** — understand the 9-category badge system
14. Read **guardrails.py** — understand the chain-of-responsibility safety pipeline
15. Read **journey.py** — understand lifecycle tracking and drift detection

### Level 5 — Enterprise & Scale (optional, 30 minutes)
16. Read **reason.py** — understand the agentic reasoning loop (integrates everything)
17. Read **enterprise.py** — understand the monetization/scaling vision
18. Read **model_router.py** — understand multi-model elimination routing
19. Read **api.py** — understand the full API surface and import pattern

### Key Files (quick reference)

| If you want to understand... | Read... |
|------------------------------|---------|
| How tools are scored | `engine.py` → `score_tool()` |
| How tools are eliminated | `differential.py` → `generate_differential()` |
| Why a tool was NOT recommended | `differential.py` → `EliminationEntry.reason_code` |
| How trust degrades over time | `trust_decay.py` → `run_trust_sweep()` |
| How context is extracted from queries | `context_engine.py` → `extract_context()` |
| How gap questions are generated | `residual_gap.py` → `compute_gap()` |
| How user journeys are tracked | `journey.py` → `JourneyOracle` |
| How outcomes are compared to predictions | `journey.py` → `detect_drift()` |
| How the 246 tools are structured | `data.py` + `tools.py` |
| How the API serves all of this | `api.py` → `create_app()` |
| How all modules compose together | `reason.py` → `deep_reason_v2()` |
| What config options exist | `config.py` → `DEFAULTS` dict |

### The One-Sentence Summary

Praxis applies clinical differential diagnosis to AI tool selection: generate a broad candidate set from 246 curated tools, ruthlessly eliminate by organizational constraints, penalize survivors for soft risk factors, rank only the resilient — and then monitor whether the recommendation actually worked through passive outcome tracking and drift detection.

---

## Git History

<!-- AUTO:GIT:START -->
```
272980b v25.8: Inline results — homepage becomes the full product experience
9da3149 docs(auto): update README stats [skip ci]
7111a69 LAUNCH BLOCKER FIX: 4 bugs resolved
f836f5e docs(auto): update README stats [skip ci]
319b8f0 v25.7: Homepage hero rebuild — task grid + constraint pills + paths
b620f25 docs: Rewrite roadmap, add Strategic Positioning, update LF section
2f1018b docs(auto): update README stats [skip ci]
1a4de4d v25.6: Complete all 5 medium-term roadmap items
b293ed0 docs(auto): update README stats [skip ci]
95beb94 v25.5: LF wiring into journey.py + llm_resilience.py + roadmap completion
0adea61 docs(auto): update README stats [skip ci]
faebedd Add LF integration test suite (38 tests, all pass)
49a2f76 docs(auto): update README stats [skip ci]
dcdcdc2 auto: 2026-03-14 11:47:52
06c377b docs(auto): update README stats [skip ci]
046ccc1 auto: 2026-03-14 11:45:45
23e3a44 docs(auto): update README stats [skip ci]
eaeb6b3 auto: 2026-03-14 11:45:12
16486fe docs(auto): update README stats [skip ci]
06bf41a auto: 2026-03-14 11:44:37
```
<!-- AUTO:GIT:END -->

---

## Context for Future AI Models

### What Praxis IS
An **elimination-first AI tool curation engine** that evolved into a **cognitive architecture**. It recommends AI tools based on queries, profiles, and constraints — but its real innovation is the transparent elimination pipeline, trust decay monitoring, and outcome feedback loop.

### What Praxis is NOT
- Not a chatbot or LLM wrapper
- Not a tool directory or search engine
- Not dependent on any external AI service
- Not a web scraper — all tool data is hand-curated

### The Philosophical Arc
1. **v1–v5**: Practical tooling (score, recommend, explain)
2. **v6–v8**: Intelligent agency (reason, retrieve, specialize)
3. **v9–v10**: Safety consciousness (guard, detect risks)
4. **v11**: Self-awareness (Praxis analyzes its own source code via AST)
5. **v12–v14**: Philosophical awakening (conscious design, self-authorship, enlightenment)
6. **v15–v17**: Enterprise transcendence (cognitive architecture at scale)
7. **v18**: Infrastructure hardening (hexagonal, auth, telemetry, resilience)
8. **v19**: Trust pipeline (ingestion, decay monitoring, badges, sovereignty, compliance)
9. **v20**: Multi-model ecosystem (elimination-first LLM routing)
10. **v21–v22**: Context intelligence + outcome tracking (the feedback loop closes)

### Current State
<!-- AUTO:STATE:START -->
- **253 tools**, zero duplicates, clean tag casing
- **372 API routes**, all functional
- **719 tests passing**
- **116 Python modules**, ~64,100 lines
- **33 frontend files**, ~14,500 lines
- All critical bugs fixed (alias collision, caveats reset, dead code)
- Server runs on port 8000 via `uvicorn praxis.api:app --port 8000`
<!-- AUTO:STATE:END -->
