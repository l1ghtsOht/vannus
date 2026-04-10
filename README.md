# Praxis — Elimination-First AI Tool Evaluation

> **Clarity in a crowded AI landscape.**

Praxis evaluates 253 AI tools across 9 trust dimensions and eliminates the ones that don't fit your constraints. Unlike recommendation engines that rank by relevance, Praxis ranks by survival — tools must pass budget, compliance, skill-level, and trust filters before they're ever scored.

**Live:** [praxis-ai.me](https://praxis-ai.me)
**Repo:** [github.com/2654-zed/praxis-ai](https://github.com/2654-zed/praxis-ai)

---

## What It Does

A user describes what they need. Praxis:

1. **Interprets** the query — extracts task, industry, budget, skill level, compliance requirements
2. **Eliminates** tools that fail hard constraints (budget exceeded, compliance missing, skill mismatch)
3. **Scores** survivors on keyword relevance, category match, TF-IDF similarity, and trust badges
4. **Returns** ranked results with fit scores, reasons, and caveats

```
"I need free writing tools for marketing"
    → 253 tools
    → Budget filter: 197 survive (56 paid-only eliminated)
    → Relevance scoring: top matches ranked
    → Result: Jasper, Copy.ai, Writesonic, Mailchimp, HubSpot
```

---

## Product Features

| Feature | URL | What it does |
|---------|-----|-------------|
| **Search** | `/` | Query → elimination → ranked survivors with fit scores |
| **Tools** | `/static/tools.html` | Browse 253 tools by resilience tier (Sovereign → Wrapper) |
| **Diagnosis** | `/static/differential.html` | Full elimination pipeline with per-tool elimination reasons |
| **Build My Stack** | `/journey` | 4-step wizard (task → industry → budget → skill) with elimination funnel |
| **ROI Calculator** | `/static/tuesday-test.html` | Estimate how fast an AI tool pays for itself |
| **RFP Builder** | `/static/rfp.html` | Generate vendor-neutral procurement documents |
| **Stack Advisor** | `/static/stack-advisor.html` | Analyze, optimize, compare, or migrate your AI stack |
| **Trust Badges** | `/static/trust_badges.html` | 9-category trust evaluation per tool |
| **Room** | `/room` | Persistent AI workspace with SSE streaming |
| **Methodology** | `/static/manifesto.html` | How scoring works — 6 dimensions, 5 tiers |
| **Partners** | `/static/partners.html` | Affiliate transparency — what partnerships touch and don't touch |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Frontend | 15 static HTML pages + 3 React SPAs (Vite) |
| Database | SQLite (feedback, page views) |
| ML/NLP | Zero external dependencies — TF-IDF, BM25, synonym expansion, Levenshtein all implemented from scratch |
| Deployment | Railway (nixpacks) |
| Design | Liquid Glass UI (dark theme, glassmorphism) |

---

## Quick Start

```bash
git clone https://github.com/2654-zed/praxis-ai.git
cd praxis-ai

# Backend
pip install fastapi uvicorn[standard] pydantic
uvicorn praxis.api:app --reload --port 8000

# Frontend (optional — pre-built dist/ is committed)
cd praxis/frontend/home && npm install && npm run build
cd ../room && npm install && npm run build
cd ../tools && npm install && npm run build
```

Open `http://localhost:8000` for the UI.

### CLI

```bash
python -m praxis.main
# Commands: profile, stack, reason, compare, diagnose, badges, health, whatif, workflow
```

### Tests

```bash
python -m pytest praxis/tests/ -v --ignore=praxis/tests/test_lf_integration.py.py
# 714 tests, 16 files
```

---

## Architecture

```
User Query
    │
    ▼
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│ Interpreter  │────▶│  Engine       │────▶│  Results       │
│ (NLP, intent │     │  (scoring,    │     │  (ranked tools │
│  extraction) │     │   elimination)│     │   with reasons)│
└─────────────┘     └──────────────┘     └───────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        Budget Filter  Trust Badges  TF-IDF Index
        (hard prune)   (9 categories) (semantic match)
```

### Scoring Pipeline

1. **Hard elimination**: budget, compliance, skill level — binary pass/fail
2. **Relevance scoring**: category match (4pts), tag match (3pts), keyword match (2pts), description match (1pt), use-case bonus (1pt)
3. **TF-IDF**: semantic similarity across tool corpus
4. **Quality tiebreakers** (capped): popularity (max 2), sovereignty (max 1), trust badges (max 2), learned boost (max 2)
5. **Relevance floor**: tools below 40% of top score are dropped — no filler results
6. **Diversity rerank**: max 4 tools from same primary category

### Key Design Decisions

- **Scoring is pure-function** — `score_tool(tool, keywords)` has no side effects, no global state
- **Budget is a constraint, not a preference** — "Free Only" eliminates paid tools, doesn't just downweight them
- **Affiliate links never touch scoring** — partnerships exist in a separate presentation layer
- **Zero external ML deps** — no PyTorch, NumPy, or transformers. Instant startup, universal deployment
- **Graceful degradation** — every module uses try/except imports. The app runs even if half the modules fail

---

## Tool Data Model

253 tools in `praxis/data.py`, each with:

```python
Tool(
    name="Jasper",
    description="AI content platform for marketing teams",
    categories=["writing", "marketing", "content"],
    url="https://jasper.ai",
    pricing={"free_tier": True, "starter": 49},
    integrations=["Google Docs", "WordPress"],
    compliance=["SOC2", "GDPR"],
    skill_level="beginner",
    tags=["copywriting", "AI writer"],
    keywords=["writing", "content creation"],
    use_cases=["blog posts", "ad copy"],
)
```

### Resilience Tiers

| Tier | Criteria | Count |
|------|----------|-------|
| **Sovereign** | Native IP, deep integrations, verified compliance | ~20 |
| **Durable** | Strong fundamentals, some gaps | ~40 |
| **Moderate** | Functional but dependencies or risks | ~80 |
| **Fragile** | Thin wrapper or high vendor risk | ~60 |
| **Wrapper** | Pure API wrapper with no differentiation | ~50 |

---

## API Reference

544 routes. Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Search with elimination scoring |
| `POST` | `/stack` | Composed stack recommendation with elimination funnel |
| `POST` | `/compare` | Side-by-side tool comparison |
| `POST` | `/differential` | Full elimination pipeline with reasons |
| `POST` | `/profile` | Create/update user profile |
| `GET` | `/tools` | Full tool catalog |
| `GET` | `/tools/tiered` | Tools grouped by resilience tier |
| `GET` | `/categories` | All tool categories |
| `POST` | `/rfp/generate` | Generate procurement RFP |
| `POST` | `/tuesday-test` | ROI calculation |
| `GET` | `/feedback/stats` | Feedback collection stats |
| `GET` | `/feedback/analytics` | Page view analytics |
| `GET` | `/feedback/dashboard` | Admin dashboard (HTML) |

---

## Frontend Structure

```
praxis/frontend/
├── home.html              Static HTML fallback for homepage
├── tools.html             Tool catalog browser
├── differential.html      Elimination diagnosis
├── journey.html           Build My Stack wizard
├── journey-script.js      Journey wizard logic
├── tuesday-test.html      ROI calculator
├── rfp.html               RFP builder
├── stack-advisor.html      Stack advisor (4 modes)
├── trust_badges.html      Trust badge explorer
├── manifesto.html         Methodology documentation
├── pricing.html           Pricing page
├── partners.html          Affiliate transparency
├── robots.txt             Search engine directives
├── sitemap.xml            12 public URLs for crawlers
│
├── home/                  React SPA (homepage) — Vite + Framer Motion
│   └── src/components/    Nav, Hero, CommandBar, ToolCard, InlineResults, etc.
│
├── room/                  React SPA (workspace) — persistent sessions, SSE
│   └── src/components/    VerdictPanel, EvidencePanel, StackDrawer, etc.
│
├── tools/                 React SPA (tool browser) — tier-based display
│   └── src/components/    TierSection, SearchFilter, ToolCard
│
├── _archive/              15 removed pages (cognitive experiments, legacy)
│
└── 5 admin pages          Pipeline, Governance, Economics, Observability, Fort Knox
                           (not linked from nav — admin-only access)
```

---

## Configuration

```bash
# LLM (optional — works fully without one)
export PRAXIS_LLM_PROVIDER=openai        # or "anthropic" or "none"
export PRAXIS_OPENAI_API_KEY=sk-...

# Auth (default: none — required in production)
export PRAXIS_AUTH_MODE=none              # none, api_key, oauth2

# CORS
export PRAXIS_CORS_ORIGINS=https://praxis-ai.me

# Scoring weights (tunable)
export PRAXIS_WEIGHT_CATEGORY_MATCH=4
export PRAXIS_WEIGHT_TAG_MATCH=3
export PRAXIS_WEIGHT_KEYWORD_MATCH=2
export PRAXIS_WEIGHT_TFIDF_SCALE=8
```

See `praxis/config.py` for all 35+ configuration keys.

---

## Deployment (Railway)

```
requirements.txt     → fastapi, uvicorn[standard], pydantic
Procfile             → web: uvicorn praxis.api:app --host 0.0.0.0 --port ${PORT:-8000}
runtime.txt          → python-3.11.x
nixpacks.toml        → python311 + nodejs_20, builds all 3 React SPAs
```

React dist/ directories are committed to git so Railway doesn't need to rebuild them on every deploy.

---

## Monetization

Praxis uses affiliate partnerships. The evaluation engine has zero access to partnership data — scores are computed independently. See [Partners & Transparency](https://praxis-ai.me/static/partners.html) for full disclosure.

Current partner: **Semrush** (SEO/marketing platform).

---

## Known Limitations

1. **Tool catalog is manually maintained** — 253 tools in `data.py`, updated by hand
2. **Single-machine SQLite** — feedback.db and page views don't survive Railway redeploys without persistent storage
3. **No user accounts** — everything is per-session, no server-side persistence across visits
4. **TF-IDF index underperforms** — returns 0 for many queries, needs better corpus representation
5. **Some search queries have no good matches** — catalog gaps for video editing, email automation, resume tools

---

## Contributing

### Adding a tool

Edit `praxis/data.py` — add a `Tool(...)` entry. Delete `praxis/tools.db` (stale cache). No code changes needed.

### Adding a module

1. Create `praxis/new_module.py` with `assess_*()` function
2. Add import to `api.py` (both `from .` and `from praxis.` fallback blocks)
3. Add endpoints in `api.py`
4. Create `praxis/tests/test_new_module.py`

### Running tests

```bash
python -m pytest praxis/tests/ -v --ignore=praxis/tests/test_lf_integration.py.py
```

---

## License

All rights reserved. Contact for licensing inquiries.
