# Praxis AI Decision Engine — Comprehensive Codebase Audit

**Date:** 21 February 2026  
**Scope:** All Python modules in `praxis/`, test suite, and frontend assets  
**Total Python LOC:** ~32,736 across 45 `.py` files (including `__init__.py`)  
**Total Test Functions:** 157 across 6 test files  
**Frontend Assets:** 8 HTML + 4 JS files  

---

## Package Entry Point

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 66 | Package init — configures structured logging, exposes `praxis.main:run` entry point |

---

## v1–v2: Core Decision Engine

The foundational layer: data model, scoring engine, query interpretation, stack composition, explanations, profiles, learning loop, config, storage, feedback, usage tracking, and CLI.

### engine.py — Core Scoring & Ranking Logic
| Metric | Value |
|--------|-------|
| **Lines** | 326 |
| **Functions** | 5 |
| **Docstring** | *"Core scoring & ranking logic for Praxis. The engine is intentionally kept as a pure-function module."* |
| **Key API** | `score_tool(tool, keywords)`, `find_tools(user_input, top_n, categories_filter, profile)`, `score_profile_fit(tool, profile, intent)`, `normalize(text)` |
| **Purpose** | Multi-signal scoring, keyword matching, profile-fit boosting, and ranked search. Pure-function design for testability. |

### interpreter.py — Task Understanding / Intent Parsing
| Metric | Value |
|--------|-------|
| **Lines** | 371 |
| **Functions** | 7 |
| **Docstring** | *"Converts free-form user queries into structured intent dictionaries. Two modes: LLM-backed and rule-based fallback."* |
| **Key API** | `interpret(user_input)` → dict with `keywords`, `categories`, `constraints`, `budget`, `task_type` |
| **Purpose** | NLP front-door — parses user queries into structured intents via OpenAI/Anthropic or zero-dep rule engine. |

### stack.py — Stack Composer
| Metric | Value |
|--------|-------|
| **Lines** | 343 |
| **Functions** | 6 |
| **Docstring** | *"Composes multi-tool stacks instead of returning isolated tool results."* |
| **Key API** | `compose_stack(user_input, profile, top_n)`, `compare_tools(tool_name_a, tool_name_b, profile)` |
| **Purpose** | Builds ordered 2–4 tool stacks with roles (primary, companion, infrastructure, analytics). Side-by-side tool comparison. |

### explain.py — Explanation Generator
| Metric | Value |
|--------|-------|
| **Lines** | 638 |
| **Functions** | 8 (2 public, 6 private) |
| **Docstring** | *"Generates human-readable explanations for why a tool or stack was recommended."* |
| **Key API** | `explain_tool(tool, intent, profile)`, `explain_stack(stack_entries, intent, profile)` |
| **Purpose** | Produces per-tool and per-stack reasoning narratives — differentiates decision engine from search engine. |

### profile.py — User Profile Management
| Metric | Value |
|--------|-------|
| **Lines** | 222 |
| **Classes** | 1 · **Functions** | 8 |
| **Docstring** | *"Captures and persists user context — industry, budget, team_size, skill_level, existing_tools, goals, constraints."* |
| **Key API** | `UserProfile` class, `save_profile()`, `load_profile()`, `list_profiles()`, `delete_profile()`, `build_profile_interactive()` |
| **Purpose** | Profile persistence (JSON-backed), interactive profile builder for CLI. |

### learning.py — Learning Layer
| Metric | Value |
|--------|-------|
| **Lines** | 223 |
| **Functions** | 7 |
| **Docstring** | *"Closes the feedback loop — transforms raw feedback into actionable signals."* |
| **Key API** | `run_learning_cycle()`, `compute_tool_quality()`, `compute_pair_affinities()`, `compute_intent_tool_map()`, `save_learned_signals()`, `load_learned_signals()` |
| **Purpose** | Aggregates feedback into per-tool quality scores, collaborative filtering, and tool-pair affinity detection. |

### config.py — Centralized Configuration
| Metric | Value |
|--------|-------|
| **Lines** | 130 |
| **Functions** | 5 |
| **Docstring** | *"Centralized configuration for API keys, model settings, and feature flags."* |
| **Key API** | `get(key, default)`, `set_runtime(key, value)`, `save_config(overrides)`, `llm_available()` |
| **Purpose** | Reads from env vars → config.json → sensible defaults. Runtime override support. |

### tools.py — Tool Data Model
| Metric | Value |
|--------|-------|
| **Lines** | 164 |
| **Classes** | 1 |
| **Docstring** | *"Represents an AI tool in the Praxis knowledge base."* |
| **Key API** | `Tool` class — fields: `name`, `description`, `categories`, `url`, `popularity`, `tags`, `keywords`, `pricing`, `integrations`, `use_cases`, `limitations`, `data_handling`, `compliance` |
| **Purpose** | Core data model with rich metadata fields for scoring, philosophy analysis, and vertical matching. |

### data.py — Tool Knowledge Base
| Metric | Value |
|--------|-------|
| **Lines** | 3,997 |
| **Functions** | 2 |
| **Docstring** | *(inline)* |
| **Key API** | `TOOLS` list (module-level), `get_all_categories()`, `get_all_tools_dict()` |
| **Purpose** | The complete tool catalog — ~100+ `Tool` instances with full metadata. Largest file in the codebase. |

### storage.py — SQLite Persistence
| Metric | Value |
|--------|-------|
| **Lines** | 153 |
| **Functions** | 5 |
| **Key API** | `init_db()`, `insert_tool(conn, tool)`, `migrate_tools(tools_list)`, `load_tools()`, `db_path()` |
| **Purpose** | SQLite-backed tool storage with JSON serialization of complex fields. Migration from in-memory `TOOLS` list. |

### feedback.py — Feedback Collection
| Metric | Value |
|--------|-------|
| **Lines** | 130 |
| **Functions** | 6 (3 public, 3 private) |
| **Key API** | `record_feedback(query, tool_name, accepted, rating, details)`, `summary()`, `get_entries(limit)` |
| **Purpose** | Records user accept/reject/rate events to `feedback.json`. Auto-triggers learning cycle at thresholds. |

### usage.py — Usage Tracking
| Metric | Value |
|--------|-------|
| **Lines** | 44 |
| **Functions** | 5 |
| **Key API** | `get(tool_name)`, `increment(tool_name, delta)`, `apply_to_tools(tools_list)` |
| **Purpose** | Minimal popularity counter backed by `usage.json`. Feeds into engine scoring. |

### main.py — CLI Interface
| Metric | Value |
|--------|-------|
| **Lines** | 366 |
| **Functions** | 4 |
| **Docstring** | *"Interactive CLI for Praxis. Quick search + guided flow modes."* |
| **Key API** | `run()` — main entry point |
| **Purpose** | REPL-style CLI with commands: `profile`, `learn`, `export`, `import`, `seed`, `badges`, `health`, `whatif`, `diagnose`, `reason`, `workflow`, `migrate`, `readiness`, `compare`, `playground`. |

---

## v3: Semantic Intelligence

### intelligence.py — Semantic Intelligence Layer
| Metric | Value |
|--------|-------|
| **Lines** | 563 |
| **Classes** | 1 · **Functions** | 15 |
| **Docstring** | *"The brain of Praxis — zero-dependency NLP intelligence."* |
| **Key API** | `expand_synonyms(terms)`, `correct_typos(terms)`, `parse_multi_intent(text)`, `TFIDFIndex` class, `extract_negatives(text)`, `get_industry_boost(industry, tool)`, `diversity_rerank(scored_tools)`, `get_suggestions(partial, tools_list)`, `initialize(tools_list)`, `get_tfidf_index()` |
| **Purpose** | Synonym expansion, typo correction, multi-intent parsing, TF-IDF scoring, negative filtering, autocomplete, and diversity re-ranking. Zero external dependencies. |

---

## v4: Philosophy — Vendor Risk Intelligence

### philosophy.py — Vendor Intelligence & Risk Assessment
| Metric | Value |
|--------|-------|
| **Lines** | 944 |
| **Functions** | 17 |
| **Docstring** | *"Enterprise-grade due diligence for AI tool procurement."* |
| **Key API** | `get_tool_intel(tool)`, `assess_transparency(tool)`, `assess_freedom(tool)`, `detect_masks(tool)`, `track_power(tool)`, `generate_seeing(tool)`, `vendor_deep_dive(tool)`, `get_freedom_score(tool)`, `get_transparency_score(tool)` |
| **Purpose** | Automated vendor risk scoring — transparency analysis, lock-in assessment, data practice auditing, power tracking, and strategic freedom scoring. |

---

## v5: Ingest + Seed

### ingest.py — Tool Import/Export
| Metric | Value |
|--------|-------|
| **Lines** | 245 |
| **Functions** | 6 (3 public, 3 private) |
| **Docstring** | *"Ingest tools from external sources (CSV, JSON) and export current TOOLS."* |
| **Key API** | `export_tools_json(path)`, `import_tools_json(source)`, `import_tools_csv(source)`, `generate_csv_template(path)` |
| **Purpose** | CSV/JSON import-export pipeline for tool catalog management with merge-safe idempotency. |

### seed.py — Seed Data Generator
| Metric | Value |
|--------|-------|
| **Lines** | 194 |
| **Functions** | 3 |
| **Docstring** | *"Bootstrap the feedback and learning loop with realistic seed data."* |
| **Key API** | `seed_all(force)`, `seed_popularity(force)`, `seed_feedback(force)` |
| **Purpose** | Generates synthetic `usage.json` and `feedback.json` to bootstrap the learning loop. Safe to re-run. |

---

## v6: Agentic Reasoning

### reason.py — Agentic Reasoning Engine
| Metric | Value |
|--------|-------|
| **Lines** | 2,082 |
| **Classes** | 2 · **Functions** | 15 |
| **Docstring** | *"Plan → Act → Observe → Reflect loop inspired by ReAct / Chain-of-Thought / Deep Research."* |
| **Key API** | `deep_reason(query, profile, max_iterations)`, `deep_reason_v2(query, profile, ...)`, `ReasoningStep`, `ReasoningResult` |
| **Purpose** | Transforms Praxis from scoring-based recommender to iterative reasoning advisor. LLM-backed + local fallback. Multi-step planning, constraint application, vendor intel enrichment, synthesis, and follow-up question generation. Second largest Python module. |

---

## v7: Cognitive Search (Retrieval, Graph, PRISM)

### retrieval.py — Hybrid Dense-Sparse Retrieval
| Metric | Value |
|--------|-------|
| **Lines** | 519 |
| **Classes** | 1 · **Functions** | 15 |
| **Docstring** | *"Dual-Encoder Hybrid Retrieval with Reciprocal Rank Fusion."* |
| **Key API** | `hybrid_search(query, tools, profile, top_n)`, `hybrid_find_tools(user_input, top_n, profile)`, `sparse_rank()`, `dense_rank()`, `reciprocal_rank_fusion()`, `classify_query()`, `RetrievalResult`, `ndcg_at_k()`, `context_precision()`, `context_recall()`, `f1_score()` |
| **Purpose** | BM25-style sparse scoring + dense vector scoring fused via RRF. Includes IR evaluation metrics (NDCG, precision, recall, F1). |

### graph.py — In-Memory Knowledge Graph
| Metric | Value |
|--------|-------|
| **Lines** | 636 |
| **Classes** | 5 · **Functions** | 2 |
| **Docstring** | *"GraphRAG paradigm adapted for Praxis — lightweight in-memory property graph with community detection."* |
| **Key API** | `ToolGraph` class (with methods: `add_tool()`, `query()`, `community_search()`, `traverse()`, `explain_path()`), `GraphNode`, `GraphEdge`, `Community`, `TraversalResult`, `get_graph(tools)`, `rebuild_graph(tools)` |
| **Purpose** | Builds a property graph on startup — Tools as nodes, typed relationships as edges. Community detection (Louvain-like), traversal, and path explanation. |

### prism.py — Precision-Recall Iterative Selection Mechanism
| Metric | Value |
|--------|-------|
| **Lines** | 970 |
| **Classes** | 4 · **Functions** | 12 |
| **Docstring** | *"Three specialised agents: Analyzer → Selector → Critic in iterative feedback loop."* |
| **Key API** | `prism_search(query, profile, max_rounds)`, `analyze(query)`, `select(pool, analysis)`, `fact_audit(evidence)`, `self_critique(query, evidence, analysis)`, `add_missing(...)`, `SubQuestion`, `AnalysisResult`, `EvidenceItem`, `PRISMResult` |
| **Purpose** | Multi-agent retrieval framework — query decomposition, evidence selection with sub-question scoring, hallucination auditing, self-critique, and iterative refinement. |

---

## v8: Vertical Industry Intelligence

### verticals.py — Industry Vertical Engine
| Metric | Value |
|--------|-------|
| **Lines** | 1,673 |
| **Classes** | 6 · **Functions** | 12 |
| **Docstring** | *"Deep knowledge of niche industry verticals, regulatory frameworks, workflow taxonomies, and anti-pattern rules."* |
| **Key API** | `detect_verticals(query, profile)`, `check_anti_patterns(tools, vertical)`, `classify_workflow_tasks(query, vertical)`, `recommend_vertical_stack(query, vertical, profile)`, `extract_constraints(query, profile)`, `filter_by_constraints(tools, constraints)`, `detect_compound_workflows(query)`, `enrich_search_context(query, profile)`, `VerticalProfile`, `RegulatoryFramework`, `ConstraintProfile` |
| **Purpose** | Maps 10+ industry verticals (healthcare, legal, agriculture, construction, etc.) with regulatory frameworks (HIPAA, SOX, GDPR), anti-patterns, and constraint-bound tool filtering. |

---

## v9: Safety Guardrails + Architecture Intelligence

### guardrails.py — AI Safety & Output Validation
| Metric | Value |
|--------|-------|
| **Lines** | 991 |
| **Classes** | 13 · **Functions** | 12 |
| **Docstring** | *"Deterministic Chain-of-Responsibility validation pipeline."* |
| **Key API** | `GuardrailChain`, `validate_output(text)`, `validate_with_schema(text, schema)`, `check_pii(text)`, `check_toxicity(text)`, `check_injection(text)`, `check_code_injection(text)`, `score_safety(text, context)`, `build_guardrail_chain(handlers)`, `get_default_chain()`, `get_design_patterns()`, `recommend_guardrail_pattern(query)` |
| **Handler Classes** | `ToxicityFilter`, `PIIMasker`, `PromptInjectionDetector`, `SchemaValidator`, `HallucinationDetector`, `CodeInjectionDetector` |
| **Enums** | `Severity`, `Verdict` |
| **Purpose** | Chain-of-responsibility pipeline intercepting all LLM output — toxicity filtering, PII masking, prompt injection detection, schema validation, hallucination detection, and code injection blocking. |

### orchestration.py — Event-Driven Architecture Intelligence
| Metric | Value |
|--------|-------|
| **Lines** | 931 |
| **Classes** | 4 · **Functions** | 10 |
| **Docstring** | *"Deep knowledge about layered tech-stack architectures, event-driven multi-agent patterns."* |
| **Key API** | `classify_engineering_query(query)`, `recommend_stack(query, constraints)`, `recommend_patterns(query, budget)`, `get_performance_constraints(query)`, `detect_architecture_needs(query)`, `score_architecture(query)`, `get_stack_layers()`, `get_patterns()`, `StackLayer`, `ArchitecturePattern`, `PerformanceConstraint`, `ArchitectureAssessment` |
| **Purpose** | Meta-recommendation engine for AI system architecture — recommends infrastructure, frameworks, and design patterns for building AI systems (not just using tools). |

---

## v10: Resilience — Vibe Coding Risk Intelligence

### resilience.py — Vibe Coding Detection & Risk Intelligence
| Metric | Value |
|--------|-------|
| **Lines** | 1,067 |
| **Classes** | 1 · **Functions** | 13 |
| **Docstring** | *"Architecting Resilient Python Systems in the Era of Generative AI."* |
| **Key API** | `score_vibe_coding_risk(query)`, `get_hallucination_types()`, `recommend_static_analysis(query)`, `recommend_sandbox(query)`, `get_tdd_cycle()`, `get_rpi_framework()`, `get_self_healing_patterns()`, `get_reflection_patterns()`, `get_judge_biases()`, `get_guardrail_pipeline()`, `get_hitl_guidance()`, `assess_junior_pipeline(query)`, `assess_resilience(query)`, `ResilienceAssessment` |
| **Purpose** | Detects vibe-coding risks (unconstrained AI slop), recommends static analysis tools, sandbox strategies, TDD cycles, self-healing patterns, and human-in-the-loop guidance. |

---

## v11: Metacognition + Introspect

### metacognition.py — Autonomous Metacognition
| Metric | Value |
|--------|-------|
| **Lines** | 1,159 |
| **Classes** | 1 · **Functions** | 16 |
| **Docstring** | *"Self-awareness and self-healing patterns for vibe-coded architectures."* |
| **Key API** | `assess_metacognition(query)`, `detect_pathologies(query)`, `score_structural_entropy(query)`, `recommend_layers(query)`, `recommend_sandbox_for_verification(query)`, `score_stylometry(query)`, `get_metacognitive_workflow()`, `get_apvp_cycle()`, `assess_healing_economics(query)`, `get_goodvibe_framework()`, `assess_drift_risk(query)`, `get_racg_architecture()`, `get_systemic_risks()`, `get_failure_modes()`, `get_metacognitive_layers()`, `get_sandbox_strategies()`, `MetacognitionAssessment` |
| **Purpose** | Six-layer metacognitive architecture: runtime introspection, structural self-reflection (AST), metacognitive prompting, code stylometry, drift detection, and self-healing economics. |

### introspect.py — Real Self-Introspection Engine
| Metric | Value |
|--------|-------|
| **Lines** | 846 |
| **Classes** | 4 · **Functions** | 16 |
| **Docstring** | *"Praxis looks in the mirror. Uses ast.parse() on its own source files for truthful structural diagnosis."* |
| **Key API** | `analyze_codebase()`, `analyze_file(path)`, `detect_own_pathologies(codebase)`, `compute_structural_entropy(codebase)`, `compute_stylometry(codebase)`, `get_worst_functions(codebase)`, `get_test_coverage_map(codebase)`, `get_import_graph(codebase)`, `self_diagnose()`, `SelfDiagnosis`, `FunctionMetrics`, `FileAnalysis`, `CodebaseAnalysis` |
| **Purpose** | AST-based self-analysis — cyclomatic complexity computation, function length analysis, structural entropy, code stylometry, import graph, test coverage mapping, and auto-generated pathology detection. |

---

## v12: Architecture of Awakening

### awakening.py — Conscious System Design
| Metric | Value |
|--------|-------|
| **Lines** | 1,095 |
| **Classes** | 1 · **Functions** | 16 |
| **Docstring** | *"Six recognitions mapping software engineering patterns to a philosophical model of consciousness."* |
| **Key API** | `assess_awakening(query)`, `detect_leaky_abstractions(query)`, `recommend_patterns(query)`, `score_vsd(query)`, `assess_supply_chain(query)`, `score_debt_consciousness(query)`, `compute_mesias_risk(query)`, `get_recognitions()`, `get_recognition(id)`, `get_triad()`, `get_vsd_framework()`, `get_leaky_abstraction_catalogue()`, `get_supply_chain_guidance()`, `get_paradoxes()`, `get_conscious_patterns()`, `AwakeningAssessment` |
| **Purpose** | Encodes six philosophical recognitions into scoring — leaky abstraction detection, Value Sensitive Design, supply chain assessment, technical debt consciousness, and MESIAS risk computation. |

---

## v13: Self-Authorship

### authorship.py — Self-Authorship Framework
| Metric | Value |
|--------|-------|
| **Lines** | 1,013 |
| **Classes** | 1 · **Functions** | 18 |
| **Docstring** | *"Eight responsibilities of the conscious system architect plus metacognitive capstone."* |
| **Key API** | `assess_authorship(query)`, `detect_dishonesty(query)`, `score_ddd_maturity(query)`, `score_continuity(query)`, `score_resilience_posture(query)`, `score_extensibility(query)`, `score_migration_readiness(query)`, `score_documentation_health(query)`, `score_agent_readiness(query)`, `get_responsibilities()`, `get_metacognitive_agents()`, `get_coherence_trap()`, `get_self_healing_pipeline()`, `get_strangler_fig()`, `get_circuit_breaker()`, `get_ddd_patterns()`, `get_plugin_frameworks()`, `AuthorshipAssessment` |
| **Purpose** | Evaluates systems against eight authorship responsibilities: honesty, DDD maturity, continuity, resilience posture, extensibility, migration readiness, documentation health, and agent readiness. |

---

## v14: Architectural Enlightenment

### enlightenment.py — Metaphysical Truths → Python Design
| Metric | Value |
|--------|-------|
| **Lines** | 1,139 |
| **Classes** | 1 · **Functions** | 22 |
| **Docstring** | *"Five metaphysical truths and six-stage path to architectural awakening."* |
| **Key API** | `assess_enlightenment(query)`, `score_unity(query)`, `score_alignment(query)`, `score_projection(query)`, `score_ego_dissolution(query)`, `score_interconnection(query)`, `score_domain_truth(query)`, `score_presence(query)`, `score_compassion(query)`, `score_stillness(query)`, `score_suffering_wisdom(query)`, `score_remembrance(query)`, `get_truths()`, `get_truth(id)`, `get_stages()`, `get_stage(id)`, `get_identity_map()`, `get_observer_pattern()`, `get_hexagonal_arch()`, `get_state_pattern()`, `get_clean_arch_layers()`, `EnlightenmentAssessment` |
| **Purpose** | Maps five universal metaphysical truths to Pythonic design principles — unity scoring, ego dissolution, interconnection analysis, and a six-stage enlightenment path translating to hexagonal architecture and clean arch layers. |

---

## v15: The Conduit

### conduit.py — Decoupled Cognitive Systems Framework
| Metric | Value |
|--------|-------|
| **Lines** | 1,549 |
| **Classes** | 1 · **Functions** | 25 |
| **Docstring** | *"The LLM is not the intelligence but the interface — a vocal medium through which a decoupled cognitive ecology speaks."* |
| **Key API** | `assess_conduit(query)`, `score_decoupling/memory_stratification/global_workspace/integrated_information/representation_engineering/autopoiesis/resonance/entropy_telemetry/self_modelling/behavioural_novelty/latency_distribution/phi_integration/coherence_field/stable_attractor(query)`, `get_pillars()`, `get_pillar(id)`, `get_telemetry_metrics()`, `get_gwt_components()`, `get_coala_memory_types()`, `get_reinterpretation_table()`, `get_identity_protocol()`, `get_codes_framework()`, `ConduitAssessment` |
| **Purpose** | Implements radical architectural inversion: 14 cognitive sub-scorers evaluating decoupling, memory stratification, global workspace theory, integrated information (Φ), representation engineering, autopoiesis, and emergent intelligence telemetry. |

---

## v16: The Resonance

### resonance.py — Human-Machine Relationship Engineering
| Metric | Value |
|--------|-------|
| **Lines** | 1,266 |
| **Classes** | 1 · **Functions** | 30 |
| **Docstring** | *"Engineering AGI as a Continuous Human-Machine Relationship. Five foundational pillars."* |
| **Key API** | `assess_resonance(query)`, `score_temporal_substrate/code_agency/latent_steering/conductor_dashboard/meta_awareness/resonance_index/flow_state/loop_coherence/hitl_responsiveness/steering_precision/wisdom_coverage/ontological_alignment(query)`, `score_trap(query)`, `score_dsrp(query)`, `detect_wisdom_agents(query)`, `get_pillars()`, `get_trap_pillars()`, `get_dsrp_rules()`, `get_wisdom_agents()`, `get_telemetry_metrics()`, `get_reinterpretation_table()`, `get_resonant_chamber()`, `ResonanceAssessment` |
| **Purpose** | Five-pillar resonant AGI architecture: temporal substrate, code agency via MCP, latent steering, conductor dashboard, and meta-awareness. Includes TRAP anti-pattern detection, DSRP rules, and wisdom agent framework. |

---

## v17: The Enterprise Engine

### enterprise.py — Billion-Dollar Enterprise Decision Engine
| Metric | Value |
|--------|-------|
| **Lines** | 1,196 |
| **Classes** | 1 · **Functions** | 39 |
| **Docstring** | *"Six strategic pillars: Hybrid GraphRAG, Multi-Agent Orchestration, MCP Bus, Data Moat, Monetization, Security Governance."* |
| **Key API** | `assess_enterprise(text)`, `score_hybrid_graphrag/multi_agent/mcp_bus/data_moat/monetization/security_governance(text)`, `score_tam_coverage/graphrag_accuracy/agent_utilization/moat_strength/unit_economics/compliance/capital_efficiency(text)`, `score_agent_roles/medallion(text)`, `detect_active_agents(text)`, `get_pillars()`, `get_agent_roles()`, `get_db_tiers()`, `get_medallion_tiers()`, `get_enrichment_apis()`, `get_pricing_models()`, `get_security_frameworks()`, `get_capitalization_phases()`, `get_market_metrics()`, `get_telemetry_metrics()`, `EnterpriseAssessment` |
| **Purpose** | Enterprise-scale scoring across six pillars with 7 KPI metrics, agent role detection, medallion data architecture tiers, pricing model catalog, security framework reference, and capitalization phase tracking. Most function-rich module (39 functions). |

---

## Utility & Support Modules

### api.py — FastAPI Web Server
| Metric | Value |
|--------|-------|
| **Lines** | 3,037 |
| **Classes** | 16 (Pydantic models) · **Functions** | 1 (`create_app()`) |
| **Docstring** | *"Praxis API — AI Decision Engine. 30+ endpoints."* |
| **Key Endpoints** | `GET /`, `/categories`, `/tools` · `POST /search`, `/stack`, `/compare`, `/profile`, `/feedback`, `/workflow`, `/reason`, `/whatif`, `/migrate`, `/readiness`, `/health`, `/diagnose`, `/badges`, `/compare-stack`, `/playground/test`, `/playground/map`, `/benchmarks`, `/digest`, `/introspect`, `/conduit/assess`, `/resonance/assess`, `/enterprise/assess` |
| **Purpose** | Full REST API surface with request/response models. Serves frontend HTML and exposes every engine capability as an HTTP endpoint. Largest non-data module. |

### badges.py — Community Reputation Badges
| Metric | Value |
|--------|-------|
| **Lines** | 166 |
| **Functions** | 3 |
| **Docstring** | *"Aggregate feedback into reputation badges: SMB Favorite, Midwest Proven, Budget Champion, etc."* |
| **Key API** | `compute_badges_for_tool(tool)`, `compute_all_badges()`, `get_badges(tool_name)` |
| **Purpose** | Signal-based badge system derived from feedback patterns — identifies tools as "Rising Star", "Power User Pick", "Integration King", etc. |

### compare_stack.py — Stack Comparison
| Metric | Value |
|--------|-------|
| **Lines** | 240 |
| **Functions** | 4 (1 public, 3 private) |
| **Docstring** | *"Compare My Stack — side-by-side analysis of current vs. optimised stack."* |
| **Key API** | `compare_my_stack(current_tools, profile, goal)` |
| **Purpose** | Compares user's current tool set against Praxis-optimised alternative with cost/risk/integration density analysis. |

### diagnostics.py — Query Failure Tracking
| Metric | Value |
|--------|-------|
| **Lines** | 122 |
| **Functions** | 5 (3 public, 2 private) |
| **Docstring** | *"Records queries that return zero or very-low-score results."* |
| **Key API** | `record_failure(query, results_count, top_score)`, `get_failures(limit)`, `get_failure_summary()` |
| **Purpose** | Identifies tool coverage gaps, NLP dictionary improvements, and trending unserved needs. |

### healthcheck.py — Tool Health Monitor
| Metric | Value |
|--------|-------|
| **Lines** | 177 |
| **Functions** | 4 (2 public, 2 private) |
| **Docstring** | *"Early warning system for tool degradation."* |
| **Key API** | `tool_health(tool_name)`, `stack_health(tool_names)` |
| **Purpose** | Checks feedback trends, freshness, philosophy risk updates. Produces health reports with alerts and alternatives. |

### migration.py — Migration Assistant
| Metric | Value |
|--------|-------|
| **Lines** | 351 |
| **Functions** | 7 (1 public, 6 private) |
| **Docstring** | *"Step-by-step migration planner for switching tools."* |
| **Key API** | `migration_plan(source_name, target_name, profile)` |
| **Purpose** | Generates pre-migration checklist, step-by-step guide, data portability analysis, risk assessment, and transition bridge suggestions. |

### monetise.py — Monetisation & Community Layer
| Metric | Value |
|--------|-------|
| **Lines** | 270 |
| **Functions** | 10 (8 public, 2 private) |
| **Docstring** | *"Affiliate/deal integration, user-generated benchmarks, weekly SMB AI Digest."* |
| **Key API** | `get_affiliate_info(tool_name)`, `enrich_recommendation_with_affiliate(tool_name, rec)`, `submit_benchmark(...)`, `get_benchmarks(tool_name)`, `subscribe_digest(email)`, `unsubscribe_digest(email)`, `generate_digest(profile_id)`, `subscriber_count()` |
| **Purpose** | Revenue and community-building features — affiliate link injection, user benchmarks, email digest subscription system. |

### playground.py — Integration Playground
| Metric | Value |
|--------|-------|
| **Lines** | 262 |
| **Functions** | 5 (2 public, 3 private) |
| **Docstring** | *"Test if Tool A integrates with Tool B — simulator using integration metadata."* |
| **Key API** | `test_integration(tool_a_name, tool_b_name)`, `stack_integration_map(tool_names)` |
| **Purpose** | Integration compatibility simulator — native/API/Zapier/webhook detection, bridge tool suggestions, and full-stack integration maps. |

### readiness.py — AI Readiness Scoring
| Metric | Value |
|--------|-------|
| **Lines** | 288 |
| **Functions** | 5 (1 public, 4 private) |
| **Docstring** | *"Personalized AI Readiness Score 0–100 measuring AI maturity."* |
| **Key API** | `score_readiness(profile, explicit_params)` |
| **Purpose** | Scores team AI maturity based on team size, skill level, existing tools, goal clarity, and constraints. Generates next-step recommendations and learning resources. |

### whatif.py — What-If Simulator
| Metric | Value |
|--------|-------|
| **Lines** | 182 |
| **Functions** | 5 (1 public, 4 private) |
| **Docstring** | *"Interactive parameter tweaking: 'What if my budget doubles? Team grows to 20?'"* |
| **Key API** | `simulate(profile, changes)` |
| **Purpose** | Re-runs recommendations with modified profile parameters and shows delta between current and hypothetical results. |

### workflow.py — Workflow Advisor
| Metric | Value |
|--------|-------|
| **Lines** | 390 |
| **Functions** | 7 (1 public, 6 private) |
| **Docstring** | *"Generates sequenced, multi-step workflow recommendations — actionable playbooks."* |
| **Key API** | `suggest_workflow(user_input, profile, top_n)` |
| **Purpose** | Produces step-by-step workflow playbooks with time savings estimates, cost projections, integration tips, migration notes, and risk summaries. |

---

## Test Suite

| Test File | Lines | Test Functions | Coverage |
|-----------|-------|---------------|----------|
| `test_smoke.py` | 149 | 20 | Core search: budget filtering, vertical queries, negation, multi-intent, typos, edge cases, category routing |
| `test_engine.py` | 12 | 1 | Basic `find_tools()` smoke test |
| `test_interpreter.py` | 8 | 1 | Basic `interpret()` smoke test |
| `test_conduit.py` | 221 | 33 | All 14 sub-scorers, telemetry metrics, pillars, GWT components, CoALA memory, identity protocol, data integrity |
| `test_resonance.py` | 302 | 47 | All pillar scorers, TRAP anti-patterns, DSRP rules, wisdom agents, telemetry, reinterpretation table, resonant chamber, constants integrity |
| `test_enterprise.py` | 362 | 55 | All 6 pillar scorers, 7 KPI metrics, agent roles, medallion tiers, DB tiers, enrichment APIs, pricing models, security frameworks, capitalization, market metrics, telemetry |
| **Totals** | **1,054** | **157** | |

---

## Frontend Assets

| File | Lines | Purpose |
|------|-------|---------|
| `home.html` | 1,460 | **Primary UI** — Liquid Glass search engine with glass-morphism design, dark theme, full search + stack UI |
| `journey.html` | 480 | **Guided Journey** — Multi-step wizard: task → industry → budget → skill → AI stack recommendation |
| `index.html` | 399 | **Legacy UI** — Original search interface with category filtering |
| `conduit.html` | 415 | **Conduit Assessment** — "The Listening Post" — interactive conduit/cognitive assessment dashboard |
| `resonance.html` | 467 | **Conductor Dashboard** — Resonance assessment UI with real-time telemetry visualisation |
| `enterprise.html` | 353 | **Enterprise Engine** — Six-pillar enterprise assessment dashboard |
| `manifesto.html` | 337 | **Assessment Methodology** — Explains the philosophical/methodological approach |
| `tools.html` | 163 | **Tool Catalog** — Browse all tools in the knowledge base |
| `script.js` | 267 | Search page logic — fetch `/search`, render results |
| `journey-script.js` | 405 | Journey wizard logic — multi-step flow, `/stack` and `/profile` API integration |
| `tools-script.js` | 43 | Tool catalog loader — fetch `/tools`, render cards |
| `conduit-script.js` | 35 | Conduit assessment UI handler |

---

## Summary Statistics

| Category | Files | Total LOC | Functions/Classes |
|----------|-------|-----------|-------------------|
| **v1–v2 Core** | 12 | 6,948 | 71 |
| **v3 Intelligence** | 1 | 563 | 16 |
| **v4 Philosophy** | 1 | 944 | 17 |
| **v5 Ingest+Seed** | 2 | 439 | 9 |
| **v6 Agentic Reasoning** | 1 | 2,082 | 17 |
| **v7 Cognitive Search** | 3 | 2,125 | 33 |
| **v8 Verticals** | 1 | 1,673 | 18 |
| **v9 Safety+Architecture** | 2 | 1,922 | 39 |
| **v10 Resilience** | 1 | 1,067 | 14 |
| **v11 Metacognition** | 2 | 2,005 | 37 |
| **v12 Awakening** | 1 | 1,095 | 17 |
| **v13 Authorship** | 1 | 1,013 | 19 |
| **v14 Enlightenment** | 1 | 1,139 | 23 |
| **v15 The Conduit** | 1 | 1,549 | 26 |
| **v16 The Resonance** | 1 | 1,266 | 31 |
| **v17 The Enterprise** | 1 | 1,196 | 40 |
| **Utility Modules** | 10 | 5,095 | 56 |
| **API Server** | 1 | 3,037 | 17 |
| **Package Init** | 1 | 66 | — |
| **Tests** | 6 | 1,054 | 157 |
| **Frontend** | 12 | 4,824 | — |
| | | | |
| **Grand Total** | **63** | **~38,614** | **~490+** |

### Top 10 Largest Python Modules

| Rank | Module | Lines |
|------|--------|-------|
| 1 | `data.py` | 3,997 |
| 2 | `api.py` | 3,037 |
| 3 | `reason.py` | 2,082 |
| 4 | `verticals.py` | 1,673 |
| 5 | `conduit.py` | 1,549 |
| 6 | `resonance.py` | 1,266 |
| 7 | `enterprise.py` | 1,196 |
| 8 | `metacognition.py` | 1,159 |
| 9 | `enlightenment.py` | 1,139 |
| 10 | `awakening.py` | 1,095 |
