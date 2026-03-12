# Praxis AI Tool Ingestion & Curation Pipeline — Blueprint v3.0

> **Status:** Implemented · **Last Updated:** 2026-03-01  
> **Modules:** `pipeline_constants.py` · `ingestion_engine.py` · `trust_decay.py` · `smb_scoring.py` · `relationship_extraction.py`  
> **Dashboard:** `/static/pipeline.html`  
> **API Routes:** 26 endpoints under `/pipeline/*`, `/trust-decay/*`, `/smb/*`, `/relationships/*`

---

## 1. Architecture Overview

The Ingestion & Curation Pipeline is a six-stage daily process that discovers, validates, enriches, scores, tiers, and curates AI/SaaS tools for SMB relevance.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Directory    │───▶│  Triple      │───▶│  Enrichment  │
│  Fetch        │    │  Match       │    │  (CDX/SLA)   │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
                    ┌──────────────┐    ┌──────▼───────┐
                    │  Tier        │◀───│  Survival    │
                    │  Assignment  │    │  Score       │
                    └──────┬───────┘    └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Tier 1  │ │  Tier 2  │ │  Tier 3  │
        │  Auto    │ │  HITL    │ │  Sandbox │
        └──────────┘ └──────────┘ └──────────┘
```

---

## 2. Core Modules

### 2.1 `pipeline_constants.py`

All immutable configuration values for the pipeline. No runtime mutation allowed.

| Constant | Value | Purpose |
|----------|-------|---------|
| `DIRECTORIES` | 3 sources | G2, Capterra, Product Hunt |
| `TIER_1_MIN_SURVIVAL` | 70.0 | Minimum Survival Score for Tier 1 |
| `TIER_1_MIN_SMB` | 50.0 | Minimum SMB relevance for Tier 1 |
| `TIER_1_CONFIDENCE_AUTO` | 85.0 | Auto-approve confidence threshold |
| `TIER_2_MIN_SURVIVAL` | 40.0 | Minimum for HITL review |
| `SMB_PRICING_CEILING` | $500/mo | Maximum monthly price for SMB |
| `TRUST_DECAY_INTERVAL_HOURS` | 72 | Sweep interval |
| `LLM_EXTRACTION_AUTO_COMMIT` | 0.85 | Confidence for auto-commit |
| `LLM_EXTRACTION_HITL_MIN` | 0.50 | Minimum for HITL queue |

**Survival Score Weights:**

| Component | Weight | Description |
|-----------|--------|-------------|
| `m_health` | 0.30 | Maintenance Health (commit freq, issue resolution) |
| `smb_rel` | 0.20 | SMB Relevance Score |
| `r_trend` | 0.20 | Review Trend (sentiment trajectory) |
| `s_signal` | 0.15 | Social Signal (hiring, press, funding) |
| `u_recency` | 0.10 | Usage Recency |
| `f_red` | 0.05 | Red Flag Penalty (security incidents, outages) |

### 2.2 `ingestion_engine.py` (~660 lines)

**Purpose:** Core orchestrator for the daily ingestion pipeline.

**Data Classes:**
- `DirectoryListing` — Raw listing from a directory source
- `MatchedTool` — Tool that appeared in ≥2 directories (Triple Match)
- `EnrichedTool` — Fully scored and enriched tool record

**Key Functions:**
- `fetch_all_directories()` → Fetches from 3 directory APIs (Apify + Playwright fallback)
- `normalize_and_match()` → Fuzzy matching via `difflib.SequenceMatcher`, threshold 0.85
- `enrich_tools()` → CDX changelog diffs, SLA lookups, hiring velocity
- `calculate_maintenance_health()` → Commit frequency, issue resolution time
- `calculate_smb_relevance()` → Delegates to `smb_scoring.score_smb_relevance()`
- `calculate_survival_score()` → Weighted composite using pipeline constants
- `evaluate_and_tier()` → Assigns Tier 1 / 2 / 3 based on thresholds
- `run_daily_pipeline()` → Full orchestration (fetch → match → enrich → score → tier)
- `approve_tool()` / `reject_tool()` → HITL queue management
- `run_promotion_sweep()` → Tier 2→1 promotion for tools exceeding thresholds
- `generate_why_included()` → Natural language explanation for inclusion

**Tier Assignment Logic:**
```
IF survival_score ≥ 70 AND smb_score ≥ 50 AND match_confidence ≥ 85:
    → Tier 1 (Auto-Approved)
ELIF survival_score ≥ 40 AND smb_score ≥ 30:
    → Tier 2 (HITL Review Queue)
ELSE:
    → Tier 3 (Sandbox — 90-day observation)
```

### 2.3 `trust_decay.py` (~530 lines)

**Purpose:** Continuous vendor trust degradation monitoring.

**Detection Methods:**
1. **Pricing Change Detection** — Wayback CDX API diffs on pricing pages
2. **Review Sentiment Analysis** — NLP keyword density on G2/Capterra reviews
3. **SSL Certificate Monitoring** — Certificate validity and expiration checks
4. **DNS Routing Analysis** — CNAME/A record stability monitoring

**Severity Levels:** `CRITICAL` · `HIGH` · `MEDIUM` · `LOW`

**Signal Types:** `PRICING_CHANGE` · `REVIEW_DECLINE` · `SSL_ISSUE` · `DNS_ANOMALY`

**Key Functions:**
- `run_trust_sweep()` → Orchestrates all 4 detection methods
- `get_decay_alerts()` → Returns active alerts with severity filtering
- `acknowledge_alert()` / `dismiss_alert()` → Alert lifecycle management
- `get_tool_trust_status()` → Per-tool trust assessment
- `get_decay_summary()` → Aggregate dashboard metrics

**Alert Lifecycle:**
```
Detected → Active → Acknowledged → (Resolved | Dismissed)
```

### 2.4 `smb_scoring.py` (~440 lines)

**Purpose:** SMB Relevance Gate preventing enterprise tool pollution.

**22 SMB Verticals:**
Retail, F&B, Professional Services, Healthcare, Real Estate, Construction, Education, Fitness, Beauty, Automotive, Legal, Accounting, Marketing Agency, Non-Profit, Agriculture, Manufacturing (Small), Logistics, Hospitality, Pet Services, Cleaning, Photography, Event Planning

**Scoring Breakdown (0–100):**
| Component | Max Points | Method |
|-----------|-----------|--------|
| Vertical Match | 40 | Keyword presence in docs/marketing |
| Pricing Accessibility | 30 | Price point vs. $500 ceiling, transparency |
| Operational Complexity | 30 | Setup time, required expertise, integrations |

**Calibration Dataset:**
- 50 known enterprise tools (expected score < 40)
- 50 known SMB tools (expected score > 65)
- Used for supervised logistic regression validation

### 2.5 `relationship_extraction.py` (~470 lines)

**Purpose:** LLM-driven Open Information Extraction for tool ecosystems.

**Extraction Pipeline:**
1. Curated rule-based extraction from `_KNOWN_RELATIONSHIPS` (9 ecosystems)
2. LLM extraction via OpenAI → Anthropic → fallback chain
3. Confidence gating: ≥0.85 auto-commit, 0.50–0.85 HITL queue, <0.50 discard
4. Graph commit to in-memory store and optional Neo4j

**9 Curated Ecosystems:**
Stripe, Shopify, HubSpot, Slack, QuickBooks, Zapier, Google Workspace, Microsoft 365, Salesforce

**HITL Queue:** Relationships with confidence 0.50–0.85 are queued for human review before committing to the knowledge graph.

---

## 3. API Routes (26 endpoints)

### Pipeline Management
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/pipeline/ingest/trigger` | Trigger a full ingestion cycle |
| `GET` | `/pipeline/status` | Pipeline health and tier counts |
| `GET` | `/pipeline/review-queue` | Tier 2 HITL review queue |
| `GET` | `/pipeline/approved` | All Tier 1 approved tools |
| `GET` | `/pipeline/sandbox` | All Tier 3 sandbox tools |
| `POST` | `/pipeline/approve/{tool_name}` | Approve a Tier 2 tool |
| `POST` | `/pipeline/reject/{tool_name}` | Reject a Tier 2 tool |
| `POST` | `/pipeline/promotion-sweep` | Run Tier 2→1 promotion sweep |
| `GET` | `/pipeline/why-included/{tool_name}` | "Why Included?" explanation |
| `GET` | `/pipeline/constants` | All pipeline configuration constants |

### Trust Decay
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/trust-decay/sweep` | Run trust decay sweep |
| `GET` | `/trust-decay/alerts` | Active trust decay alerts |
| `GET` | `/trust-decay/summary` | Decay statistics summary |
| `GET` | `/trust-decay/tool/{tool_name}` | Per-tool trust status |
| `POST` | `/trust-decay/acknowledge/{tool_name}` | Acknowledge alert |
| `POST` | `/trust-decay/dismiss/{tool_name}` | Dismiss alert |
| `GET` | `/trust-decay/history` | Historical alert log |

### SMB Scoring
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/smb/score/{tool_name}` | SMB score for specific tool |
| `GET` | `/smb/score-all` | SMB scores for all tools |
| `GET` | `/smb/vertical-fit/{tool_name}` | Vertical fit breakdown |
| `GET` | `/smb/verticals` | Available SMB verticals |

### Relationship Extraction
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/relationships/extract/{tool_name}` | Extract relationships for a tool |
| `GET` | `/relationships/hitl-queue` | Relationships pending review |
| `POST` | `/relationships/approve` | Approve a queued relationship |
| `POST` | `/relationships/reject` | Reject a queued relationship |
| `GET` | `/relationships/summary` | Relationship graph summary |

---

## 4. Frontend Dashboard

**Location:** `/static/pipeline.html`

**Features:**
- **Stats Row** — 6 live metrics (Total, Tier 1/2/3, Decay Alerts, Relationships)
- **Pipeline Flow Visualization** — 6-stage animated progress indicator
- **Tier Distribution Bar** — Color-coded proportional bar chart
- **SMB Gauge** — Animated ring gauge showing average SMB score
- **HITL Review Queue** — Approve/reject cards with "Why Included?" tooltips
- **Trust Decay Alerts** — Severity-coded alert feed with sweep trigger
- **Tool Relationship Graph** — Source → relation → target visualization
- **Approved Tools** — Tier 1 tool chip display
- **Sandbox** — Tier 3 emerging tool display
- **Pipeline Configuration** — Live display of weights, thresholds, decay params

**Auto-refresh:** Every 30 seconds via `setInterval`

**Design:** Liquid Glass CSS with aurora background, matching Fort Knox aesthetic

---

## 5. Success Metrics (KPIs)

| Metric | Target |
|--------|--------|
| False positive rate | < 5% |
| Stale tool retention | < 2% (30-day window) |
| HITL review turnaround | < 48 hours |
| User trust score | > 85 (via feedback) |
| Pipeline cycle time | < 15 minutes |

---

## 6. Integration Points

- **Existing Modules:** Leverages `philosophy.py` (security axioms), `graph.py` (knowledge graph), `tools.py` (tool registry), `data.py` (seed data)
- **External APIs:** Apify (directory scraping), Wayback CDX (changelog diffs), ScraperAPI (G2/Capterra), PredictLeads (hiring velocity)
- **Optional:** Neo4j for persistent relationship graph storage
- **Auth:** All endpoints inherit Praxis authentication middleware
- **Telemetry:** Pipeline metrics emitted via existing telemetry infrastructure
