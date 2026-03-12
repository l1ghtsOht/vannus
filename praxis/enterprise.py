"""
praxis.enterprise
~~~~~~~~~~~~~~~~~
v17 — The Enterprise Engine: Architecting the Billion-Dollar Enterprise
Decision Engine — Scaling the Praxis AI Platform.

Implements the six strategic pillars of the Enterprise AI Architecture:

  I.    Hybrid GraphRAG Architecture — Vector DB + Knowledge Graph + Document DB
  II.   Multi-Agent Orchestration — Supervisor + 4 specialized sub-agents
  III.  MCP & Agentic Service Bus — universal integration protocol layer
  IV.   Proprietary Data Moat — vendor intelligence, medallion tiers, gamification
  V.    Monetization & AI Unit Economics — hybrid action-based pricing
  VI.   Enterprise Security & Governance — SOC 2, NIST AI RMF, microVM isolation

Plus:
  - 4 Agent Roles (Intent Extraction, Vendor Intelligence, Architecture
    Orchestration, Budget & Compliance)
  - 4 Database Architecture Tiers (SQLite/JSON, Vector DB, Knowledge Graph,
    Hybrid GraphRAG)
  - 3 Medallion Tiers (Bronze, Silver, Gold)
  - 3 Data Enrichment APIs (Cognism, Clearbit, ZoomInfo)
  - 3 Pricing Models (Flat-Rate, Pure Consumption, Hybrid/Action-Based)
  - 4 Security Frameworks (SOC 2 Type II, NIST AI RMF, MicroVM Sandbox,
    PII Sanitization)
  - 4 Capitalization Phases (Digital Sandbox KC, Arch Grants, MTC IDEA
    Fund, KCRise Fund)
  - 3 Market Metrics (Enterprise AI Market, AI Platforms, AI Software &
    Services)
  - 7 Enterprise Telemetry Metrics

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
# I.  PILLARS — The six strategic pillars of the Enterprise Engine
# ======================================================================

PILLARS: List[Dict[str, Any]] = [
    {
        "id": "hybrid_graphrag",
        "number": "I",
        "title": "Hybrid GraphRAG Architecture",
        "doctrine": (
            "The enterprise decision engine must transcend brittle TF-IDF and "
            "heuristic matching by fusing Vector Databases for high-dimensional "
            "semantic search, Knowledge Graphs for multi-hop reasoning and "
            "explainable dependency tracing, and Document Databases for raw "
            "vendor corpus storage — yielding a Hybrid GraphRAG architecture "
            "that drastically reduces LLM hallucination while ensuring "
            "technically accurate, structurally sound stack recommendations."
        ),
        "components": [
            "Vector Database (VDB) — dense embedding indexing",
            "Knowledge Graph (GDB) — entity-relationship traversal",
            "Document Database (DDB) — raw text and API specs",
            "Hybrid retrieval pipeline — VDB → GDB sub-graph → LLM",
        ],
        "keywords": [
            "graphrag", "vector database", "knowledge graph", "rag",
            "retrieval augmented generation", "embedding", "semantic search",
            "multi-hop reasoning", "sub-graph", "document database",
        ],
    },
    {
        "id": "multi_agent_orchestration",
        "number": "II",
        "title": "Multi-Agent Orchestration",
        "doctrine": (
            "A single monolithic LLM call is an execution bottleneck that "
            "exhausts context limits and precludes deep reasoning.  The engine "
            "must adopt a Supervisor architecture that dynamically delegates "
            "to specialized sub-agents — Intent Extraction, Vendor Intelligence, "
            "Architecture Orchestration, and Budget & Compliance — operating "
            "concurrently via LangGraph / CrewAI / Agno, mirroring human "
            "teamwork with parallel processing streams and optimized windows."
        ),
        "components": [
            "Supervisor / Orchestrator Agent",
            "Intent Extraction Agent — structured parameter extraction",
            "Vendor Intelligence Agent — GraphRAG + live API enrichment",
            "Architecture Orchestration Agent — stack composition via graph",
            "Budget & Compliance Agent — financial and regulatory safety net",
        ],
        "keywords": [
            "multi-agent", "supervisor", "orchestrator", "langgraph",
            "crewai", "agno", "sub-agent", "concurrent", "delegation",
            "parallel", "intent extraction", "architecture orchestration",
        ],
    },
    {
        "id": "mcp_agentic_bus",
        "number": "III",
        "title": "MCP & Agentic Service Bus",
        "doctrine": (
            "Praxis must natively adopt the Model Context Protocol (MCP) as a "
            "universal plug-and-play integration layer, enabling agents to "
            "securely query live vendor endpoints — pricing APIs, status pages, "
            "documentation servers — in real time.  Beyond advisory, Praxis "
            "pioneers the Agentic Service Bus: an infrastructure layer for "
            "high-volume structured inter-agent communication via JSON-RPC, "
            "bypassing expensive natural-language translation at every node."
        ),
        "components": [
            "MCP client / server implementation",
            "Live vendor endpoint pinging — pricing, status, docs",
            "JSON-RPC inter-agent communication protocol",
            "Agentic Service Bus middleware layer",
            "MCP-compliant scaffolding template generation",
        ],
        "keywords": [
            "mcp", "model context protocol", "agentic service bus",
            "json-rpc", "live endpoint", "vendor api", "integration",
            "anthropic", "linux foundation", "scaffolding", "middleware",
        ],
    },
    {
        "id": "proprietary_data_moat",
        "number": "IV",
        "title": "Proprietary Data Moat",
        "doctrine": (
            "Foundation models commoditize rapidly; the true defensibility is "
            "proprietary, high-signal data that competitors cannot replicate.  "
            "Praxis must scale from 25 curated tools to 25,000+ via automated "
            "ingestion, B2B enrichment APIs (Cognism, Clearbit, ZoomInfo), a "
            "vendor self-service portal with Medallion Architecture (Bronze / "
            "Silver / Gold data tiers), and B2B gamification loops that "
            "crowdsource RLHF through leaderboards, certifications, and "
            "behavioral data exhaust capture."
        ),
        "components": [
            "Real-time vendor intelligence via enrichment APIs",
            "Vendor self-service API portal (OpenAPI / MCP format)",
            "Medallion Architecture — Bronze → Silver → Gold tiers",
            "B2B gamification — leaderboards, certifications, rewards",
            "Behavioral data exhaust capture and RLHF feedback loops",
        ],
        "keywords": [
            "data moat", "cognism", "clearbit", "zoominfo", "enrichment",
            "medallion", "bronze", "silver", "gold", "gamification",
            "leaderboard", "rlhf", "data exhaust", "network effect",
            "vendor portal", "self-service",
        ],
    },
    {
        "id": "monetization_economics",
        "number": "V",
        "title": "Monetization & AI Unit Economics",
        "doctrine": (
            "Traditional flat-rate SaaS pricing is fundamentally misaligned "
            "with AI economics where every query incurs material compute costs "
            "(50-60% gross margins vs 80-90% for classic SaaS).  Praxis must "
            "implement a Hybrid Pricing Model — base platform subscription + "
            "action-based usage tiers charging for concrete business outcomes "
            "(Enterprise Architecture Mapped, Compliance Audit Generated, MCP "
            "Scaffold Deployed) — with usage caps and pre-paid inference credits "
            "to protect margins structurally."
        ),
        "components": [
            "Base platform subscription — predictable recurring revenue",
            "Action-based (usage) tiers — outcome-aligned pricing",
            "Usage caps and pre-paid inference credits",
            "Internal metering, tracking, and billing infrastructure",
            "COGS management and margin protection systems",
        ],
        "keywords": [
            "monetization", "pricing", "unit economics", "cogs",
            "hybrid pricing", "subscription", "action-based", "consumption",
            "inference credits", "margin", "saas", "gross margin",
            "metering", "billing",
        ],
    },
    {
        "id": "security_governance",
        "number": "VI",
        "title": "Enterprise Security & Governance",
        "doctrine": (
            "Mission-critical Fortune 500 integration demands exceeding the "
            "most stringent security and regulatory thresholds.  Praxis must "
            "be engineered for SOC 2 Type II + NIST AI RMF layered compliance, "
            "microVM-based code execution sandboxing (hardware-level isolation "
            "beyond Docker containers), automated PII sanitization before "
            "external LLM interaction, and perpetual cryptographically secure "
            "audit trails ensuring total explainability for enterprise audits."
        ),
        "components": [
            "SOC 2 Type II — 5 Trust Services Criteria",
            "NIST AI RMF — model drift, data poisoning, explainability",
            "MicroVM sandboxing — hardware-level blast radius containment",
            "Automated PII sanitization and data scrubbing",
            "Cryptographic audit trails — full recommendation provenance",
        ],
        "keywords": [
            "soc2", "nist", "ai rmf", "microvm", "sandbox", "isolation",
            "pii", "sanitization", "audit trail", "compliance", "gdpr",
            "ccpa", "hipaa", "governance", "security", "zero trust",
        ],
    },
]

# ======================================================================
# II. AGENT ROLES — The four specialized sub-agents
# ======================================================================

AGENT_ROLES: List[Dict[str, Any]] = [
    {
        "id": "intent_extraction",
        "title": "Intent Extraction Agent",
        "responsibility": (
            "Analyzes free-form user input to extract structured parameters: "
            "budget constraints, technical skill levels (low-code vs pro-code), "
            "existing software stacks (AWS, Azure, GCP ecosystems), and overall "
            "business goals."
        ),
        "inputs": ["free-form query", "user profile", "session history"],
        "outputs": ["budget_range", "skill_level", "ecosystem_affinity",
                     "business_goals", "compliance_requirements"],
    },
    {
        "id": "vendor_intelligence",
        "title": "Vendor Intelligence Agent",
        "responsibility": (
            "Traverses the Hybrid GraphRAG database and simultaneously queries "
            "external data enrichment APIs to gather real-time data on "
            "prospective tools that match the extracted parameters."
        ),
        "inputs": ["structured_intent", "graphrag_context", "enrichment_apis"],
        "outputs": ["tool_shortlist", "vendor_metadata", "pricing_data",
                     "compliance_status", "integration_capabilities"],
    },
    {
        "id": "architecture_orchestration",
        "title": "Architecture Orchestration Agent",
        "responsibility": (
            "Formulates the actual enterprise AI stack by leveraging the "
            "knowledge graph to group tools logically — ensuring primary "
            "agents pair with compatible companions and infrastructure tools "
            "via graph traversal of integrates_with / requires_infrastructure "
            "/ is_compliant_with edges."
        ),
        "inputs": ["tool_shortlist", "graph_db_context", "ecosystem_affinity"],
        "outputs": ["composed_stack", "primary_tools", "companion_tools",
                     "infrastructure_tools", "integration_map"],
    },
    {
        "id": "budget_compliance",
        "title": "Budget & Compliance Agent",
        "responsibility": (
            "Final safety check: cross-references the proposed AI tool stack "
            "against financial constraints and regulatory requirements.  "
            "Rejects non-compliant tools (e.g., no SOC 2 for healthcare) "
            "and forces the Architecture Agent to find alternatives."
        ),
        "inputs": ["composed_stack", "budget_range", "compliance_requirements"],
        "outputs": ["validated_stack", "budget_utilization", "compliance_report",
                     "rejected_tools", "alternative_suggestions"],
    },
]

# ======================================================================
# III. DATABASE ARCHITECTURE TIERS — Evolution of data persistence
# ======================================================================

DB_ARCHITECTURE_TIERS: List[Dict[str, Any]] = [
    {
        "id": "sqlite_json",
        "title": "SQLite / JSON (Current MVP)",
        "strengths": "Rapid prototyping, simple local persistence, zero cloud costs.",
        "limitations": "Does not scale, lacks semantic understanding, rigid, concurrent lock issues.",
        "optimal_use": "Immediate deprecation. Local caching for offline CLI only.",
        "status": "deprecated",
    },
    {
        "id": "vector_db",
        "title": "Vector Database (Standalone)",
        "strengths": "Low-latency retrieval, massive scale, deep semantic search.",
        "limitations": "Lacks reasoning paths, cannot understand strict technical dependencies.",
        "optimal_use": "Unstructured semantic search of tool capabilities and documentation.",
        "status": "component",
    },
    {
        "id": "knowledge_graph",
        "title": "Knowledge Graph (Standalone)",
        "strengths": "Deep reasoning, precise entity relationships, high explainability.",
        "limitations": "High maintenance overhead, strict ontology required, slower retrieval.",
        "optimal_use": "Mapping tool compatibility, API dependencies, pricing logic, compliance.",
        "status": "component",
    },
    {
        "id": "hybrid_graphrag",
        "title": "Hybrid GraphRAG (Proposed)",
        "strengths": "Contextually rich retrieval, multi-hop logic, minimal hallucination.",
        "limitations": "High system complexity, sophisticated engineering, increased compute costs.",
        "optimal_use": "Enterprise-grade core reasoning engine powering entire backend orchestration.",
        "status": "target",
    },
]

# ======================================================================
# IV. MEDALLION ARCHITECTURE — Data quality tiers
# ======================================================================

MEDALLION_TIERS: List[Dict[str, Any]] = [
    {
        "id": "bronze",
        "title": "Bronze Tier",
        "description": "Raw data ingested via web scraping or initial third-party API enrichment.",
        "quality": "unverified",
        "source": "automated",
    },
    {
        "id": "silver",
        "title": "Silver Tier",
        "description": "Cleaned, formatted, verified against the Praxis ontology by automated agents.",
        "quality": "verified",
        "source": "system",
    },
    {
        "id": "gold",
        "title": "Gold Tier",
        "description": (
            "High-fidelity data submitted, cryptographically verified, and "
            "continuously updated directly by the vendor via self-service portal, "
            "augmented with real-time performance analytics."
        ),
        "quality": "certified",
        "source": "vendor",
    },
]

# ======================================================================
# V. DATA ENRICHMENT APIs — Third-party vendor intelligence sources
# ======================================================================

DATA_ENRICHMENT_APIS: List[Dict[str, Any]] = [
    {
        "id": "cognism",
        "title": "Cognism",
        "strengths": "Proprietary domains, financial insights, GDPR/SOC2 compliance trails, batch/real-time enrichment.",
        "strategy": (
            "Primary source for verifying vendor compliance, financial "
            "stability, and corporate metadata before tool recommendation."
        ),
    },
    {
        "id": "clearbit",
        "title": "Clearbit (HubSpot)",
        "strengths": "100+ B2B data attributes, deep firmographic/technographic data, CRM integration.",
        "strategy": (
            "Deep technographic profiling of legacy tools an AI vendor "
            "naturally integrates with, mapping back to the Graph DB."
        ),
    },
    {
        "id": "zoominfo",
        "title": "ZoomInfo API",
        "strengths": "Comprehensive profile data, enterprise scale, extensive corporate hierarchies.",
        "strategy": (
            "Mapping parent/child vendor relationships (e.g., OpenAI vs "
            "Microsoft Azure OpenAI) for accurate organizational lineage."
        ),
    },
]

# ======================================================================
# VI. PRICING MODELS — B2B monetization strategies
# ======================================================================

PRICING_MODELS: List[Dict[str, Any]] = [
    {
        "id": "flat_rate",
        "title": "Flat-Rate Subscription",
        "mechanics": "Single monthly or annual fee for all features regardless of usage.",
        "pros": "Ultimate billing simplicity, highly predictable revenue stream.",
        "cons": "Extreme risk of negative margins from power users; ignores variable COGS.",
        "recommended": False,
    },
    {
        "id": "pure_consumption",
        "title": "Pure Consumption (Tokens)",
        "mechanics": "Pay strictly for compute/inference used per session.",
        "pros": "Mathematically guarantees margin protection on every query.",
        "cons": "Confusing for non-technical buyers; extreme budget unpredictability.",
        "recommended": False,
    },
    {
        "id": "hybrid_action",
        "title": "Hybrid / Action-Based",
        "mechanics": "Base subscription + variable fees per completed architectural outcome.",
        "pros": "Balances predictability with scalability; aligns price with value delivered.",
        "cons": "Requires sophisticated internal metering, tracking, billing infrastructure.",
        "recommended": True,
    },
]

# ======================================================================
# VII. SECURITY FRAMEWORKS — Layered compliance and isolation
# ======================================================================

SECURITY_FRAMEWORKS: List[Dict[str, Any]] = [
    {
        "id": "soc2_type_ii",
        "title": "SOC 2 Type II",
        "scope": "Infrastructure-level controls over 3-12 months.",
        "criteria": ["Security", "Availability", "Processing Integrity",
                      "Confidentiality", "Privacy"],
        "limitation": "Designed for deterministic software; does not cover AI-specific risks.",
    },
    {
        "id": "nist_ai_rmf",
        "title": "NIST AI Risk Management Framework",
        "scope": "AI-specific risk governance and lifecycle management.",
        "criteria": ["Model drift detection", "Training data poisoning defense",
                      "Recommendation explainability", "Adversarial robustness testing"],
        "limitation": "Does not replace traditional IT audit frameworks.",
    },
    {
        "id": "microvm_sandbox",
        "title": "MicroVM Sandboxing",
        "scope": "Runtime code isolation via hardware-level virtualization.",
        "criteria": ["Ephemeral execution environments", "Container breakout prevention",
                      "Blast radius containment", "Immediate sandbox destruction after task"],
        "limitation": "Higher resource overhead than standard Docker containers.",
    },
    {
        "id": "pii_sanitization",
        "title": "PII Sanitization Protocol",
        "scope": "Automated data scrubbing before external LLM interaction.",
        "criteria": ["PII detection and removal", "IP address scrubbing",
                      "GDPR / CCPA / Colorado AI Act compliance",
                      "Cryptographic audit trail generation"],
        "limitation": "May reduce query specificity if over-aggressive.",
    },
]

# ======================================================================
# VIII. CAPITALIZATION PHASES — Phased regional funding strategy
# ======================================================================

CAPITALIZATION_PHASES: List[Dict[str, Any]] = [
    {
        "id": "digital_sandbox_kc",
        "title": "Digital Sandbox KC",
        "funding_type": "Proof-of-concept / Pre-seed",
        "amount": "$20,000",
        "utilization": (
            "Initial engineering transition from SQLite MVP to baseline "
            "Graph/Vector database prototype."
        ),
    },
    {
        "id": "arch_grants",
        "title": "Arch Grants",
        "funding_type": "Non-dilutive civic grant / Early stage",
        "amount": "$75,000",
        "utilization": (
            "Subsidizing API integration costs (Cognism, ZoomInfo) for "
            "continuous data enrichment and vendor tracking."
        ),
    },
    {
        "id": "mtc_idea_fund",
        "title": "MTC IDEA Fund (Seed)",
        "funding_type": "State-sponsored equity / convertible debt",
        "amount": "$500,000",
        "utilization": (
            "Building proprietary API vendor portal, multi-agent "
            "orchestration layer, and UI/UX gamification."
        ),
    },
    {
        "id": "kcrise_fund",
        "title": "KCRise Fund",
        "funding_type": "Institutional Venture Capital / Seed to Series A",
        "amount": "> $1,000,000",
        "utilization": (
            "SOC 2/NIST compliance, scaling enterprise sales team, "
            "deploying the Agentic Service Bus."
        ),
    },
]

# ======================================================================
# IX. MARKET METRICS — Enterprise AI TAM projections
# ======================================================================

MARKET_METRICS: List[Dict[str, Any]] = [
    {
        "id": "total_enterprise_ai",
        "title": "Total Enterprise AI Market",
        "current_value": "$114.87B (2026)",
        "projection": "$273.08B (2031)",
        "cagr": "18.91%",
        "drivers": (
            "Automation mandates, scaling enterprise inference workloads, "
            "localized foundation models."
        ),
    },
    {
        "id": "enterprise_ai_platforms",
        "title": "Enterprise AI Platforms",
        "current_value": "$1,480.0M (2025)",
        "projection": "$10,466.2M (2033)",
        "cagr": "27.7%",
        "drivers": (
            "Cloud-native deployments, operational efficiency improvements, "
            "multi-agent frameworks."
        ),
    },
    {
        "id": "global_ai_software",
        "title": "Global AI Software & Services",
        "current_value": "$371.71B (2025)",
        "projection": "$2,407.02B (2032)",
        "cagr": "30.6%",
        "drivers": (
            "Widespread foundation model availability, scalable APIs, "
            "democratization of AI capabilities."
        ),
    },
]

# ======================================================================
# X. TELEMETRY METRICS — 7 enterprise health signals
# ======================================================================

TELEMETRY_METRICS: List[Dict[str, Any]] = [
    {
        "id": "tam_coverage",
        "symbol": "T_c",
        "title": "TAM Coverage Index",
        "description": "Fraction of the total addressable market covered by current tool catalog.",
    },
    {
        "id": "graphrag_accuracy",
        "symbol": "G_a",
        "title": "GraphRAG Accuracy",
        "description": "Precision of hybrid retrieval: correct recommendations / total recommendations.",
    },
    {
        "id": "agent_utilization",
        "symbol": "A_u",
        "title": "Agent Utilization",
        "description": "Multi-agent orchestration efficiency — concurrent agent saturation rate.",
    },
    {
        "id": "moat_strength",
        "symbol": "M_s",
        "title": "Moat Strength",
        "description": "Data moat defensibility index — proprietary data volume / total data ratio.",
    },
    {
        "id": "unit_economics",
        "symbol": "U_e",
        "title": "Unit Economics Health",
        "description": "COGS-to-revenue ratio health — margin protection across all query types.",
    },
    {
        "id": "compliance_score",
        "symbol": "C_s",
        "title": "Compliance Score",
        "description": "Governance adherence — SOC 2 + NIST AI RMF coverage percentage.",
    },
    {
        "id": "capital_efficiency",
        "symbol": "K_e",
        "title": "Capital Efficiency",
        "description": "Funding runway and burn-rate optimization — months of runway remaining.",
    },
]

# ======================================================================
# XI. SIGNAL MAPS — Regex patterns for scoring
# ======================================================================

_GRAPHRAG_SIGNALS: Dict[str, float] = {
    r"(?i)\b(graphrag|graph[\s-]?rag)\b": 1.0,
    r"(?i)\b(vector[\s-]?database|vdb|embedding[\s-]?index)\b": 0.8,
    r"(?i)\b(knowledge[\s-]?graph|gdb|neo4j|entity[\s-]?relationship)\b": 0.8,
    r"(?i)\b(retrieval[\s-]?augmented|rag|hybrid[\s-]?retrieval)\b": 0.7,
    r"(?i)\b(semantic[\s-]?search|dense[\s-]?embedding)\b": 0.6,
    r"(?i)\b(multi[\s-]?hop|sub[\s-]?graph|graph[\s-]?traversal)\b": 0.7,
    r"(?i)\b(document[\s-]?database|ddb|corpus)\b": 0.5,
    r"(?i)\b(hallucination[\s-]?reduction|explainab)\b": 0.6,
}

_MULTI_AGENT_SIGNALS: Dict[str, float] = {
    r"(?i)\b(multi[\s-]?agent|supervisor[\s-]?agent)\b": 1.0,
    r"(?i)\b(langgraph|crewai|agno|autogen)\b": 0.9,
    r"(?i)\b(orchestrat|sub[\s-]?agent|delegation)\b": 0.7,
    r"(?i)\b(concurrent|parallel[\s-]?processing)\b": 0.6,
    r"(?i)\b(intent[\s-]?extraction|vendor[\s-]?intelligence)\b": 0.7,
    r"(?i)\b(architecture[\s-]?orchestration|budget[\s-]?compliance)\b": 0.7,
    r"(?i)\b(group[\s-]?chat|debate|refine)\b": 0.5,
    r"(?i)\b(fault[\s-]?toleran|resilien|retry)\b": 0.5,
}

_MCP_BUS_SIGNALS: Dict[str, float] = {
    r"(?i)\b(model[\s-]?context[\s-]?protocol|mcp)\b": 1.0,
    r"(?i)\b(agentic[\s-]?service[\s-]?bus)\b": 0.9,
    r"(?i)\b(json[\s-]?rpc|inter[\s-]?agent)\b": 0.7,
    r"(?i)\b(live[\s-]?endpoint|vendor[\s-]?api[\s-]?ping)\b": 0.6,
    r"(?i)\b(scaffolding|template[\s-]?generat)\b": 0.5,
    r"(?i)\b(middleware|integration[\s-]?layer)\b": 0.5,
    r"(?i)\b(linux[\s-]?foundation|anthropic[\s-]?mcp)\b": 0.6,
    r"(?i)\b(provision|automat.*deploy)\b": 0.5,
}

_DATA_MOAT_SIGNALS: Dict[str, float] = {
    r"(?i)\b(data[\s-]?moat|proprietary[\s-]?data)\b": 1.0,
    r"(?i)\b(cognism|clearbit|zoominfo)\b": 0.8,
    r"(?i)\b(medallion|bronze|silver|gold[\s-]?tier)\b": 0.7,
    r"(?i)\b(vendor[\s-]?portal|self[\s-]?service)\b": 0.6,
    r"(?i)\b(gamification|leaderboard|certification)\b": 0.6,
    r"(?i)\b(data[\s-]?exhaust|behavioral[\s-]?data)\b": 0.7,
    r"(?i)\b(rlhf|feedback[\s-]?loop|crowdsourc)\b": 0.7,
    r"(?i)\b(network[\s-]?effect|enrichment[\s-]?api)\b": 0.6,
}

_MONETIZATION_SIGNALS: Dict[str, float] = {
    r"(?i)\b(hybrid[\s-]?pricing|action[\s-]?based[\s-]?pricing)\b": 1.0,
    r"(?i)\b(unit[\s-]?economics|cogs|gross[\s-]?margin)\b": 0.8,
    r"(?i)\b(inference[\s-]?credit|usage[\s-]?cap)\b": 0.7,
    r"(?i)\b(subscription|recurring[\s-]?revenue)\b": 0.6,
    r"(?i)\b(metering|billing[\s-]?infrastructure)\b": 0.6,
    r"(?i)\b(consumption[\s-]?based|pay[\s-]?per[\s-]?use)\b": 0.5,
    r"(?i)\b(margin[\s-]?protection|margin[\s-]?erosion)\b": 0.7,
    r"(?i)\b(saas[\s-]?economics|b2b[\s-]?pricing)\b": 0.5,
}

_SECURITY_SIGNALS: Dict[str, float] = {
    r"(?i)\b(soc[\s-]?2|soc2[\s-]?type[\s-]?ii)\b": 1.0,
    r"(?i)\b(nist[\s-]?ai[\s-]?rmf|ai[\s-]?risk[\s-]?management)\b": 0.9,
    r"(?i)\b(microvm|micro[\s-]?vm|sandbox|blast[\s-]?radius)\b": 0.8,
    r"(?i)\b(pii[\s-]?sanitiz|data[\s-]?scrub)\b": 0.7,
    r"(?i)\b(audit[\s-]?trail|cryptographic[\s-]?audit)\b": 0.7,
    r"(?i)\b(gdpr|ccpa|hipaa|colorado[\s-]?ai[\s-]?act)\b": 0.6,
    r"(?i)\b(zero[\s-]?trust|container[\s-]?breakout)\b": 0.5,
    r"(?i)\b(governance|compliance[\s-]?framework)\b": 0.5,
}

# Telemetry signal maps
_TAM_SIGNALS: Dict[str, float] = {
    r"(?i)\b(tam|total[\s-]?addressable[\s-]?market)\b": 1.0,
    r"(?i)\b(market[\s-]?coverage|market[\s-]?size|market[\s-]?share)\b": 0.7,
    r"(?i)\b(enterprise[\s-]?ai[\s-]?market|billion[\s-]?dollar)\b": 0.6,
    r"(?i)\b(cagr|compound[\s-]?annual[\s-]?growth)\b": 0.5,
}

_GRAPHRAG_ACC_SIGNALS: Dict[str, float] = {
    r"(?i)\b(graphrag[\s-]?accuracy|retrieval[\s-]?precision)\b": 1.0,
    r"(?i)\b(hybrid[\s-]?retrieval|correct[\s-]?recommend)\b": 0.7,
    r"(?i)\b(hallucination[\s-]?rate|technical[\s-]?accuracy)\b": 0.6,
    r"(?i)\b(precision|recall|f1[\s-]?score)\b": 0.5,
}

_AGENT_UTIL_SIGNALS: Dict[str, float] = {
    r"(?i)\b(agent[\s-]?utilization|orchestration[\s-]?efficiency)\b": 1.0,
    r"(?i)\b(concurrent[\s-]?agents?|parallel[\s-]?stream)\b": 0.7,
    r"(?i)\b(saturation[\s-]?rate|throughput)\b": 0.6,
    r"(?i)\b(latency|context[\s-]?window[\s-]?optim)\b": 0.5,
}

_MOAT_STRENGTH_SIGNALS: Dict[str, float] = {
    r"(?i)\b(moat[\s-]?strength|data[\s-]?defensib)\b": 1.0,
    r"(?i)\b(proprietary[\s-]?volume|unique[\s-]?data)\b": 0.7,
    r"(?i)\b(switching[\s-]?cost|lock[\s-]?in)\b": 0.6,
    r"(?i)\b(network[\s-]?effect|flywheel)\b": 0.5,
}

_UNIT_ECON_SIGNALS: Dict[str, float] = {
    r"(?i)\b(unit[\s-]?economics|cogs[\s-]?ratio)\b": 1.0,
    r"(?i)\b(gross[\s-]?margin|margin[\s-]?health)\b": 0.7,
    r"(?i)\b(compute[\s-]?cost|inference[\s-]?cost)\b": 0.6,
    r"(?i)\b(revenue[\s-]?per[\s-]?query|ltv[\s-]?cac)\b": 0.5,
}

_COMPLIANCE_SIGNALS: Dict[str, float] = {
    r"(?i)\b(compliance[\s-]?score|governance[\s-]?adherence)\b": 1.0,
    r"(?i)\b(soc[\s-]?2[\s-]?coverage|nist[\s-]?coverage)\b": 0.7,
    r"(?i)\b(audit[\s-]?pass[\s-]?rate|control[\s-]?effectiveness)\b": 0.6,
    r"(?i)\b(regulatory[\s-]?readiness|framework[\s-]?coverage)\b": 0.5,
}

_CAPITAL_EFF_SIGNALS: Dict[str, float] = {
    r"(?i)\b(capital[\s-]?efficien|burn[\s-]?rate)\b": 1.0,
    r"(?i)\b(runway|months[\s-]?remaining)\b": 0.7,
    r"(?i)\b(funding[\s-]?utiliz|grant[\s-]?efficien)\b": 0.6,
    r"(?i)\b(dilution|equity[\s-]?preserv)\b": 0.5,
}

# ======================================================================
# XII. SCORING ENGINE
# ======================================================================


def _score_signals(text: str, signal_map: Dict[str, float]) -> float:
    """Score *text* against a regex→weight signal map.  Returns 0.0–1.0."""
    if not text:
        return 0.0
    total = 0.0
    max_possible = sum(signal_map.values()) or 1.0
    for pattern, weight in signal_map.items():
        if re.search(pattern, text):
            total += weight
    return min(total / max_possible, 1.0)


def _grade(score: float) -> str:
    """Map 0.0–1.0 to letter grade."""
    if score >= 0.90:
        return "A+"
    if score >= 0.80:
        return "A"
    if score >= 0.65:
        return "B"
    if score >= 0.45:
        return "C"
    if score >= 0.25:
        return "D"
    return "F"


# — Pillar scorers —

def score_hybrid_graphrag(text: str) -> Dict[str, Any]:
    """Score query for Hybrid GraphRAG architecture alignment."""
    s = _score_signals(text, _GRAPHRAG_SIGNALS)
    return {"pillar": "hybrid_graphrag", "score": round(s, 4), "grade": _grade(s)}


def score_multi_agent(text: str) -> Dict[str, Any]:
    """Score query for Multi-Agent Orchestration alignment."""
    s = _score_signals(text, _MULTI_AGENT_SIGNALS)
    return {"pillar": "multi_agent_orchestration", "score": round(s, 4), "grade": _grade(s)}


def score_mcp_bus(text: str) -> Dict[str, Any]:
    """Score query for MCP & Agentic Service Bus alignment."""
    s = _score_signals(text, _MCP_BUS_SIGNALS)
    return {"pillar": "mcp_agentic_bus", "score": round(s, 4), "grade": _grade(s)}


def score_data_moat(text: str) -> Dict[str, Any]:
    """Score query for Proprietary Data Moat alignment."""
    s = _score_signals(text, _DATA_MOAT_SIGNALS)
    return {"pillar": "proprietary_data_moat", "score": round(s, 4), "grade": _grade(s)}


def score_monetization(text: str) -> Dict[str, Any]:
    """Score query for Monetization & AI Unit Economics alignment."""
    s = _score_signals(text, _MONETIZATION_SIGNALS)
    return {"pillar": "monetization_economics", "score": round(s, 4), "grade": _grade(s)}


def score_security_governance(text: str) -> Dict[str, Any]:
    """Score query for Enterprise Security & Governance alignment."""
    s = _score_signals(text, _SECURITY_SIGNALS)
    return {"pillar": "security_governance", "score": round(s, 4), "grade": _grade(s)}


# — Telemetry scorers —

def score_tam_coverage(text: str) -> Dict[str, Any]:
    """TAM Coverage Index telemetry scorer."""
    s = _score_signals(text, _TAM_SIGNALS)
    return {"metric": "tam_coverage", "score": round(s, 4), "grade": _grade(s)}


def score_graphrag_accuracy(text: str) -> Dict[str, Any]:
    """GraphRAG Accuracy telemetry scorer."""
    s = _score_signals(text, _GRAPHRAG_ACC_SIGNALS)
    return {"metric": "graphrag_accuracy", "score": round(s, 4), "grade": _grade(s)}


def score_agent_utilization(text: str) -> Dict[str, Any]:
    """Agent Utilization telemetry scorer."""
    s = _score_signals(text, _AGENT_UTIL_SIGNALS)
    return {"metric": "agent_utilization", "score": round(s, 4), "grade": _grade(s)}


def score_moat_strength(text: str) -> Dict[str, Any]:
    """Moat Strength telemetry scorer."""
    s = _score_signals(text, _MOAT_STRENGTH_SIGNALS)
    return {"metric": "moat_strength", "score": round(s, 4), "grade": _grade(s)}


def score_unit_economics(text: str) -> Dict[str, Any]:
    """Unit Economics Health telemetry scorer."""
    s = _score_signals(text, _UNIT_ECON_SIGNALS)
    return {"metric": "unit_economics", "score": round(s, 4), "grade": _grade(s)}


def score_compliance(text: str) -> Dict[str, Any]:
    """Compliance Score telemetry scorer."""
    s = _score_signals(text, _COMPLIANCE_SIGNALS)
    return {"metric": "compliance_score", "score": round(s, 4), "grade": _grade(s)}


def score_capital_efficiency(text: str) -> Dict[str, Any]:
    """Capital Efficiency telemetry scorer."""
    s = _score_signals(text, _CAPITAL_EFF_SIGNALS)
    return {"metric": "capital_efficiency", "score": round(s, 4), "grade": _grade(s)}


# ======================================================================
# XIII. COMPOSITE FRAMEWORKS
# ======================================================================

_AGENT_SIGNAL_MAP: Dict[str, Dict[str, float]] = {
    "intent_extraction": {
        r"(?i)\b(intent[\s-]?extract\w*|parameter[\s-]?pars\w*|structured[\s-]?input)": 1.0,
        r"(?i)\b(budget[\s-]?constraint\w*|skill[\s-]?level\w*|ecosystem[\s-]?affinity)": 0.7,
        r"(?i)\b(business[\s-]?goal\w*|free[\s-]?form|nlp[\s-]?pars\w*)": 0.5,
    },
    "vendor_intelligence": {
        r"(?i)\b(vendor[\s-]?intel\w*|real[\s-]?time[\s-]?data|enrichment)": 1.0,
        r"(?i)\b(tool[\s-]?shortlist|api[\s-]?quer\w*|market[\s-]?data)": 0.7,
        r"(?i)\b(pricing[\s-]?data|compliance[\s-]?status)": 0.5,
    },
    "architecture_orchestration": {
        r"(?i)\b(architecture[\s-]?orchestrat\w*|stack[\s-]?compos\w*)": 1.0,
        r"(?i)\b(primary[\s-]?tool\w*|companion[\s-]?tool\w*|infrastructure[\s-]?tool\w*)": 0.7,
        r"(?i)\b(graph[\s-]?traversal|integrates[\s-]?with)": 0.5,
    },
    "budget_compliance": {
        r"(?i)\b(budget[\s-]?compliance|budget[\s-]?compliance[\s-]?agent|regulatory[\s-]?check)": 1.0,
        r"(?i)\b(financial[\s-]?constraint\w*|reject[\s-]?tool\w*|alternative\w*)": 0.7,
        r"(?i)\b(soc[\s-]?2[\s-]?check|hipaa[\s-]?require\w*)": 0.5,
    },
}

_MEDALLION_SIGNAL_MAP: Dict[str, Dict[str, float]] = {
    "bronze": {
        r"(?i)\b(raw[\s-]?data|web[\s-]?scrap\w*|initial[\s-]?ingest\w*|bronze)": 1.0,
        r"(?i)\b(unverified|automated[\s-]?collection)": 0.7,
        r"(?i)\b(third[\s-]?party[\s-]?api|bulk[\s-]?import)": 0.5,
    },
    "silver": {
        r"(?i)\b(cleaned|formatted|ontology[\s-]?verified|silver)": 1.0,
        r"(?i)\b(automated[\s-]?agent[\s-]?verified|quality[\s-]?check)": 0.7,
        r"(?i)\b(schema[\s-]?valid\w*|normali[zs]\w*)": 0.5,
    },
    "gold": {
        r"(?i)\b(vendor[\s-]?verified|cryptographic|self[\s-]?service|gold)": 1.0,
        r"(?i)\b(real[\s-]?time[\s-]?analytics|certified[\s-]?data)": 0.7,
        r"(?i)\b(continuous[\s-]?update|high[\s-]?fidelity)": 0.5,
    },
}


def score_agent_roles(text: str) -> Dict[str, Any]:
    """Score text against each of the 4 agent roles, return per-role + composite."""
    per_role: Dict[str, float] = {}
    for role_id, sigs in _AGENT_SIGNAL_MAP.items():
        per_role[role_id] = round(_score_signals(text, sigs), 4)
    composite = sum(per_role.values()) / max(len(per_role), 1)
    return {
        "roles": per_role,
        "composite": round(composite, 4),
        "grade": _grade(composite),
    }


def score_medallion(text: str) -> Dict[str, Any]:
    """Score text against the 3 Medallion Architecture tiers."""
    per_tier: Dict[str, float] = {}
    for tier_id, sigs in _MEDALLION_SIGNAL_MAP.items():
        per_tier[tier_id] = round(_score_signals(text, sigs), 4)
    composite = sum(per_tier.values()) / max(len(per_tier), 1)
    return {
        "tiers": per_tier,
        "composite": round(composite, 4),
        "grade": _grade(composite),
    }


def detect_active_agents(text: str) -> List[str]:
    """Detect which of the 4 sub-agents would be activated by the query."""
    active: List[str] = []
    for role in AGENT_ROLES:
        role_id = role["id"]
        sigs = _AGENT_SIGNAL_MAP.get(role_id, {})
        if _score_signals(text, sigs) >= 0.25:
            active.append(role_id)
    return active


# ======================================================================
# XIV. MASTER ASSESSMENT
# ======================================================================

@dataclass
class EnterpriseAssessment:
    """Complete enterprise engine assessment for a query."""
    enterprise_score: float
    grade: str
    hybrid_graphrag: Dict[str, Any]
    multi_agent: Dict[str, Any]
    mcp_bus: Dict[str, Any]
    data_moat: Dict[str, Any]
    monetization: Dict[str, Any]
    security: Dict[str, Any]
    # Telemetry
    tam_coverage: Dict[str, Any]
    graphrag_accuracy: Dict[str, Any]
    agent_utilization: Dict[str, Any]
    moat_strength: Dict[str, Any]
    unit_economics: Dict[str, Any]
    compliance_telem: Dict[str, Any]
    capital_efficiency: Dict[str, Any]
    # Frameworks
    agent_roles_grade: str
    medallion_grade: str
    active_agents: List[str]
    # Composites
    pillar_composite: float
    telemetry_composite: float
    enterprise_ready: bool
    evidence: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assess_enterprise(text: str) -> Dict[str, Any]:
    """Master enterprise assessment — pillar + telemetry + framework scoring.

    Composite formula:
        40% pillar composite + 30% telemetry composite + 15% agent roles + 15% medallion

    Enterprise-ready detection:
        >= 3 pillars with score >= 0.45 AND agent roles composite >= 0.30
    """
    # Pillar scores
    p_graphrag = score_hybrid_graphrag(text)
    p_agent = score_multi_agent(text)
    p_mcp = score_mcp_bus(text)
    p_moat = score_data_moat(text)
    p_money = score_monetization(text)
    p_sec = score_security_governance(text)

    pillar_scores = [
        p_graphrag["score"], p_agent["score"], p_mcp["score"],
        p_moat["score"], p_money["score"], p_sec["score"],
    ]
    pillar_composite = sum(pillar_scores) / len(pillar_scores)

    # Telemetry scores
    t_tam = score_tam_coverage(text)
    t_gra = score_graphrag_accuracy(text)
    t_aut = score_agent_utilization(text)
    t_moat = score_moat_strength(text)
    t_unit = score_unit_economics(text)
    t_comp = score_compliance(text)
    t_cap = score_capital_efficiency(text)

    telemetry_scores = [
        t_tam["score"], t_gra["score"], t_aut["score"],
        t_moat["score"], t_unit["score"], t_comp["score"],
        t_cap["score"],
    ]
    telemetry_composite = sum(telemetry_scores) / len(telemetry_scores)

    # Framework scores
    agent_result = score_agent_roles(text)
    medallion_result = score_medallion(text)
    active = detect_active_agents(text)

    # Composite
    enterprise_score = (
        0.40 * pillar_composite
        + 0.30 * telemetry_composite
        + 0.15 * agent_result["composite"]
        + 0.15 * medallion_result["composite"]
    )

    # Enterprise-ready detection
    high_pillars = sum(1 for s in pillar_scores if s >= 0.45)
    enterprise_ready = high_pillars >= 3 and agent_result["composite"] >= 0.15

    # Evidence
    evidence: List[str] = []
    for p in PILLARS:
        pid = p["id"]
        for name, sig_map in [
            ("hybrid_graphrag", _GRAPHRAG_SIGNALS),
            ("multi_agent_orchestration", _MULTI_AGENT_SIGNALS),
            ("mcp_agentic_bus", _MCP_BUS_SIGNALS),
            ("proprietary_data_moat", _DATA_MOAT_SIGNALS),
            ("monetization_economics", _MONETIZATION_SIGNALS),
            ("security_governance", _SECURITY_SIGNALS),
        ]:
            if pid == name:
                for pat in sig_map:
                    m = re.search(pat, text)
                    if m:
                        evidence.append(f"[{pid}] matched: '{m.group()}'")

    # Warnings
    warnings: List[str] = []
    if pillar_composite < 0.20:
        warnings.append("Very low pillar coverage — query may not relate to enterprise architecture.")
    if p_sec["score"] < 0.25:
        warnings.append("Security & governance signals weak — enterprise readiness at risk.")
    if agent_result["composite"] < 0.15:
        warnings.append("No multi-agent orchestration signals detected.")
    if t_unit["score"] < 0.20:
        warnings.append("Unit economics not addressed — margin sustainability unclear.")

    grade = _grade(enterprise_score)

    assessment = EnterpriseAssessment(
        enterprise_score=round(enterprise_score, 4),
        grade=grade,
        hybrid_graphrag=p_graphrag,
        multi_agent=p_agent,
        mcp_bus=p_mcp,
        data_moat=p_moat,
        monetization=p_money,
        security=p_sec,
        tam_coverage=t_tam,
        graphrag_accuracy=t_gra,
        agent_utilization=t_aut,
        moat_strength=t_moat,
        unit_economics=t_unit,
        compliance_telem=t_comp,
        capital_efficiency=t_cap,
        agent_roles_grade=agent_result["grade"],
        medallion_grade=medallion_result["grade"],
        active_agents=active,
        pillar_composite=round(pillar_composite, 4),
        telemetry_composite=round(telemetry_composite, 4),
        enterprise_ready=enterprise_ready,
        evidence=evidence,
        warnings=warnings,
    )

    log.info(
        "Enterprise assessment: %.2f (%s) — %d pillars, %d agents active, "
        "ready=%s | pillars=%d agents=%d enrichment=%d security=%d "
        "monetization=%d market=%d capitalization=%d telemetry=%d",
        enterprise_score, grade,
        len(PILLARS), len(active), enterprise_ready,
        len(PILLARS), len(AGENT_ROLES), len(DATA_ENRICHMENT_APIS),
        len(SECURITY_FRAMEWORKS), len(PRICING_MODELS),
        len(MARKET_METRICS), len(CAPITALIZATION_PHASES),
        len(TELEMETRY_METRICS),
    )

    return assessment.to_dict()


# ======================================================================
# XV. PUBLIC GETTERS — reference data retrieval
# ======================================================================

def get_pillars() -> List[Dict[str, Any]]:
    """Return all six enterprise pillars."""
    return PILLARS


def get_pillar(pillar_id: str) -> Optional[Dict[str, Any]]:
    """Return a single pillar by id, or None."""
    for p in PILLARS:
        if p["id"] == pillar_id:
            return p
    return None


def get_agent_roles() -> List[Dict[str, Any]]:
    """Return all four agent roles."""
    return AGENT_ROLES


def get_agent_role(role_id: str) -> Optional[Dict[str, Any]]:
    """Return a single agent role by id, or None."""
    for r in AGENT_ROLES:
        if r["id"] == role_id:
            return r
    return None


def get_db_tiers() -> List[Dict[str, Any]]:
    """Return all four database architecture tiers."""
    return DB_ARCHITECTURE_TIERS


def get_db_tier(tier_id: str) -> Optional[Dict[str, Any]]:
    """Return a single DB architecture tier by id, or None."""
    for t in DB_ARCHITECTURE_TIERS:
        if t["id"] == tier_id:
            return t
    return None


def get_medallion_tiers() -> List[Dict[str, Any]]:
    """Return all three Medallion Architecture tiers."""
    return MEDALLION_TIERS


def get_medallion_tier(tier_id: str) -> Optional[Dict[str, Any]]:
    """Return a single medallion tier by id, or None."""
    for t in MEDALLION_TIERS:
        if t["id"] == tier_id:
            return t
    return None


def get_enrichment_apis() -> List[Dict[str, Any]]:
    """Return all three data enrichment API profiles."""
    return DATA_ENRICHMENT_APIS


def get_enrichment_api(api_id: str) -> Optional[Dict[str, Any]]:
    """Return a single enrichment API by id, or None."""
    for a in DATA_ENRICHMENT_APIS:
        if a["id"] == api_id:
            return a
    return None


def get_pricing_models() -> List[Dict[str, Any]]:
    """Return all three pricing model strategies."""
    return PRICING_MODELS


def get_pricing_model(model_id: str) -> Optional[Dict[str, Any]]:
    """Return a single pricing model by id, or None."""
    for m in PRICING_MODELS:
        if m["id"] == model_id:
            return m
    return None


def get_security_frameworks() -> List[Dict[str, Any]]:
    """Return all four security frameworks."""
    return SECURITY_FRAMEWORKS


def get_security_framework(framework_id: str) -> Optional[Dict[str, Any]]:
    """Return a single security framework by id, or None."""
    for f in SECURITY_FRAMEWORKS:
        if f["id"] == framework_id:
            return f
    return None


def get_capitalization_phases() -> List[Dict[str, Any]]:
    """Return all four capitalization phases."""
    return CAPITALIZATION_PHASES


def get_capitalization_phase(phase_id: str) -> Optional[Dict[str, Any]]:
    """Return a single capitalization phase by id, or None."""
    for p in CAPITALIZATION_PHASES:
        if p["id"] == phase_id:
            return p
    return None


def get_market_metrics() -> List[Dict[str, Any]]:
    """Return all three market metrics."""
    return MARKET_METRICS


def get_market_metric(metric_id: str) -> Optional[Dict[str, Any]]:
    """Return a single market metric by id, or None."""
    for m in MARKET_METRICS:
        if m["id"] == metric_id:
            return m
    return None


def get_telemetry_metrics() -> List[Dict[str, Any]]:
    """Return all seven enterprise telemetry metrics."""
    return TELEMETRY_METRICS


def get_telemetry_metric(metric_id: str) -> Optional[Dict[str, Any]]:
    """Return a single enterprise telemetry metric by id, or None."""
    for m in TELEMETRY_METRICS:
        if m["id"] == metric_id:
            return m
    return None
