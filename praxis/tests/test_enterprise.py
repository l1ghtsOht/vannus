"""
Tests for praxis.enterprise — v17 The Enterprise Engine.

Covers:
  - 6 pillar scorers + empty + unrelated                (8 tests)
  - 7 telemetry scorers                                 (7 tests)
  - Agent role scoring + composite + empty               (3 tests)
  - Medallion scoring + composite + empty                (3 tests)
  - Active agent detection                               (4 tests)
  - Master assessment fields + bounds + ready + warnings (5 tests)
  - Reference data getters — counts, lookups, not-found  (22 tests)
                                                 Total: 52 tests
"""
import pytest

try:
    from praxis.enterprise import (
        # Pillar scorers
        score_hybrid_graphrag,
        score_multi_agent,
        score_mcp_bus,
        score_data_moat,
        score_monetization,
        score_security_governance,
        # Telemetry scorers
        score_tam_coverage,
        score_graphrag_accuracy,
        score_agent_utilization,
        score_moat_strength,
        score_unit_economics,
        score_compliance,
        score_capital_efficiency,
        # Frameworks
        score_agent_roles,
        score_medallion,
        detect_active_agents,
        # Master
        assess_enterprise,
        # Getters
        get_pillars,
        get_pillar,
        get_agent_roles,
        get_agent_role,
        get_db_tiers,
        get_db_tier,
        get_medallion_tiers,
        get_medallion_tier,
        get_enrichment_apis,
        get_enrichment_api,
        get_pricing_models,
        get_pricing_model,
        get_security_frameworks,
        get_security_framework,
        get_capitalization_phases,
        get_capitalization_phase,
        get_market_metrics,
        get_market_metric,
        get_telemetry_metrics,
        get_telemetry_metric,
        # Constants
        PILLARS,
        AGENT_ROLES,
        DB_ARCHITECTURE_TIERS,
        MEDALLION_TIERS,
        DATA_ENRICHMENT_APIS,
        PRICING_MODELS,
        SECURITY_FRAMEWORKS,
        CAPITALIZATION_PHASES,
        MARKET_METRICS,
        TELEMETRY_METRICS,
    )
except ImportError:
    from enterprise import (
        score_hybrid_graphrag,
        score_multi_agent,
        score_mcp_bus,
        score_data_moat,
        score_monetization,
        score_security_governance,
        score_tam_coverage,
        score_graphrag_accuracy,
        score_agent_utilization,
        score_moat_strength,
        score_unit_economics,
        score_compliance,
        score_capital_efficiency,
        score_agent_roles,
        score_medallion,
        detect_active_agents,
        assess_enterprise,
        get_pillars,
        get_pillar,
        get_agent_roles,
        get_agent_role,
        get_db_tiers,
        get_db_tier,
        get_medallion_tiers,
        get_medallion_tier,
        get_enrichment_apis,
        get_enrichment_api,
        get_pricing_models,
        get_pricing_model,
        get_security_frameworks,
        get_security_framework,
        get_capitalization_phases,
        get_capitalization_phase,
        get_market_metrics,
        get_market_metric,
        get_telemetry_metrics,
        get_telemetry_metric,
        PILLARS,
        AGENT_ROLES,
        DB_ARCHITECTURE_TIERS,
        MEDALLION_TIERS,
        DATA_ENRICHMENT_APIS,
        PRICING_MODELS,
        SECURITY_FRAMEWORKS,
        CAPITALIZATION_PHASES,
        MARKET_METRICS,
        TELEMETRY_METRICS,
    )


RICH_QUERY = (
    "We need a Hybrid GraphRAG architecture with Neo4j knowledge graph and "
    "Weaviate vector database for multi-hop reasoning across 25,000 AI tools. "
    "The multi-agent supervisor delegates to Intent Extraction, Vendor Intelligence, "
    "Architecture Orchestration, and Budget Compliance sub-agents via LangGraph "
    "concurrent orchestration. MCP integration connects our Agentic Service Bus "
    "for JSON-RPC inter-agent communication. Our proprietary data moat uses "
    "Cognism and ZoomInfo enrichment APIs with a Medallion Architecture "
    "(Bronze/Silver/Gold tiers) and B2B gamification leaderboards for RLHF "
    "feedback. Hybrid action-based pricing protects unit economics with pre-paid "
    "inference credits and usage caps. SOC 2 Type II plus NIST AI RMF governance, "
    "Firecracker microVM sandboxing, and Presidio PII sanitization ensure "
    "enterprise security with cryptographic audit trails."
)

EMPTY_QUERY = ""
UNRELATED_QUERY = "I want to bake a chocolate cake with sprinkles."


# ======================================================================
# Pillar scoring
# ======================================================================

class TestPillarScoring:
    def test_graphrag_rich(self):
        r = score_hybrid_graphrag(RICH_QUERY)
        assert r["pillar"] == "hybrid_graphrag"
        assert r["score"] > 0.3

    def test_multi_agent_rich(self):
        r = score_multi_agent(RICH_QUERY)
        assert r["pillar"] == "multi_agent_orchestration"
        assert r["score"] > 0.3

    def test_mcp_bus_rich(self):
        r = score_mcp_bus(RICH_QUERY)
        assert r["pillar"] == "mcp_agentic_bus"
        assert r["score"] > 0.3

    def test_data_moat_rich(self):
        r = score_data_moat(RICH_QUERY)
        assert r["pillar"] == "proprietary_data_moat"
        assert r["score"] > 0.3

    def test_monetization_rich(self):
        r = score_monetization(RICH_QUERY)
        assert r["pillar"] == "monetization_economics"
        assert r["score"] > 0.3

    def test_security_rich(self):
        r = score_security_governance(RICH_QUERY)
        assert r["pillar"] == "security_governance"
        assert r["score"] > 0.3

    def test_empty_returns_zero(self):
        for fn in [score_hybrid_graphrag, score_multi_agent, score_mcp_bus,
                    score_data_moat, score_monetization, score_security_governance]:
            assert fn(EMPTY_QUERY)["score"] == 0.0

    def test_unrelated_low(self):
        for fn in [score_hybrid_graphrag, score_multi_agent, score_mcp_bus,
                    score_data_moat, score_monetization, score_security_governance]:
            assert fn(UNRELATED_QUERY)["score"] < 0.2


# ======================================================================
# Telemetry scoring
# ======================================================================

class TestTelemetryScoring:
    def test_tam(self):
        r = score_tam_coverage("Total addressable market with enterprise AI market TAM")
        assert r["metric"] == "tam_coverage"
        assert r["score"] > 0.3

    def test_graphrag_acc(self):
        r = score_graphrag_accuracy("GraphRAG accuracy and retrieval precision with hallucination rate")
        assert r["score"] > 0.3

    def test_agent_util(self):
        r = score_agent_utilization("Agent utilization with concurrent agents and throughput")
        assert r["score"] > 0.3

    def test_moat_str(self):
        r = score_moat_strength("Moat strength and data defensibility with network effects")
        assert r["score"] > 0.3

    def test_unit_econ(self):
        r = score_unit_economics("Unit economics and COGS ratio with gross margin health")
        assert r["score"] > 0.3

    def test_compliance_score(self):
        r = score_compliance("Compliance score and governance adherence with SOC 2 coverage")
        assert r["score"] > 0.3

    def test_capital_eff(self):
        r = score_capital_efficiency("Capital efficiency and burn rate with runway months remaining")
        assert r["score"] > 0.3


# ======================================================================
# Agent role scoring
# ======================================================================

class TestAgentRoles:
    def test_rich_roles(self):
        r = score_agent_roles(RICH_QUERY)
        assert "roles" in r
        assert len(r["roles"]) == 4
        assert r["composite"] > 0.0

    def test_composite_bounded(self):
        r = score_agent_roles(RICH_QUERY)
        assert 0.0 <= r["composite"] <= 1.0

    def test_empty_zero(self):
        r = score_agent_roles(EMPTY_QUERY)
        assert r["composite"] == 0.0


# ======================================================================
# Medallion scoring
# ======================================================================

class TestMedallion:
    def test_rich_tiers(self):
        r = score_medallion(RICH_QUERY)
        assert "tiers" in r
        assert len(r["tiers"]) == 3

    def test_composite_bounded(self):
        r = score_medallion(RICH_QUERY)
        assert 0.0 <= r["composite"] <= 1.0

    def test_empty_zero(self):
        r = score_medallion(EMPTY_QUERY)
        assert r["composite"] == 0.0


# ======================================================================
# Active agent detection
# ======================================================================

class TestActiveAgents:
    def test_rich_detects_agents(self):
        active = detect_active_agents(RICH_QUERY)
        assert len(active) >= 2

    def test_empty_none(self):
        active = detect_active_agents(EMPTY_QUERY)
        assert active == []

    def test_intent_only(self):
        active = detect_active_agents("We need intent extraction of budget constraints and skill levels")
        assert "intent_extraction" in active

    def test_budget_compliance(self):
        active = detect_active_agents("Budget compliance and regulatory check for SOC 2 required tools")
        assert "budget_compliance" in active


# ======================================================================
# Master assessment
# ======================================================================

class TestMasterAssessment:
    def test_all_fields_present(self):
        r = assess_enterprise(RICH_QUERY)
        required = [
            "enterprise_score", "grade", "hybrid_graphrag", "multi_agent",
            "mcp_bus", "data_moat", "monetization", "security",
            "tam_coverage", "graphrag_accuracy", "agent_utilization",
            "moat_strength", "unit_economics", "compliance_telem",
            "capital_efficiency", "agent_roles_grade", "medallion_grade",
            "active_agents", "pillar_composite", "telemetry_composite",
            "enterprise_ready", "evidence", "warnings",
        ]
        for f in required:
            assert f in r, f"Missing field: {f}"

    def test_score_bounds(self):
        r = assess_enterprise(RICH_QUERY)
        assert 0.0 <= r["enterprise_score"] <= 1.0
        assert 0.0 <= r["pillar_composite"] <= 1.0
        assert 0.0 <= r["telemetry_composite"] <= 1.0

    def test_enterprise_ready_on_rich(self):
        r = assess_enterprise(RICH_QUERY)
        assert r["enterprise_ready"] is True

    def test_warnings_on_weak(self):
        r = assess_enterprise(UNRELATED_QUERY)
        assert len(r["warnings"]) > 0

    def test_telemetry_present(self):
        r = assess_enterprise(RICH_QUERY)
        for key in TELEM_KEYS:
            assert key in r
            assert "score" in r[key]
            assert "grade" in r[key]


TELEM_KEYS = [
    "tam_coverage", "graphrag_accuracy", "agent_utilization",
    "moat_strength", "unit_economics", "compliance_telem", "capital_efficiency"
]


# ======================================================================
# Reference data getters
# ======================================================================

class TestReferenceData:
    def test_pillars_count(self):
        assert len(get_pillars()) == 6

    def test_pillar_lookup(self):
        p = get_pillar("hybrid_graphrag")
        assert p is not None
        assert p["number"] == "I"

    def test_pillar_not_found(self):
        assert get_pillar("nonexistent") is None

    def test_agent_roles_count(self):
        assert len(get_agent_roles()) == 4

    def test_agent_role_lookup(self):
        r = get_agent_role("vendor_intelligence")
        assert r is not None

    def test_agent_role_not_found(self):
        assert get_agent_role("nonexistent") is None

    def test_db_tiers_count(self):
        assert len(get_db_tiers()) == 4

    def test_db_tier_lookup(self):
        t = get_db_tier("hybrid_graphrag")
        assert t is not None
        assert t["status"] == "target"

    def test_db_tier_not_found(self):
        assert get_db_tier("nonexistent") is None

    def test_medallion_tiers_count(self):
        assert len(get_medallion_tiers()) == 3

    def test_medallion_lookup(self):
        t = get_medallion_tier("gold")
        assert t is not None
        assert t["quality"] == "certified"

    def test_enrichment_apis_count(self):
        assert len(get_enrichment_apis()) == 3

    def test_enrichment_lookup(self):
        a = get_enrichment_api("cognism")
        assert a is not None

    def test_pricing_models_count(self):
        assert len(get_pricing_models()) == 3

    def test_pricing_lookup(self):
        m = get_pricing_model("hybrid_action")
        assert m is not None
        assert m["recommended"] is True

    def test_security_frameworks_count(self):
        assert len(get_security_frameworks()) == 4

    def test_security_lookup(self):
        f = get_security_framework("soc2_type_ii")
        assert f is not None

    def test_capitalization_count(self):
        assert len(get_capitalization_phases()) == 4

    def test_capitalization_lookup(self):
        p = get_capitalization_phase("arch_grants")
        assert p is not None
        assert "$75,000" in p["amount"]

    def test_market_metrics_count(self):
        assert len(get_market_metrics()) == 3

    def test_market_lookup(self):
        m = get_market_metric("total_enterprise_ai")
        assert m is not None

    def test_telemetry_metrics_count(self):
        assert len(get_telemetry_metrics()) == 7

    def test_telemetry_lookup(self):
        m = get_telemetry_metric("tam_coverage")
        assert m is not None
        assert m["symbol"] == "T_c"


# ======================================================================
# Structural integrity
# ======================================================================

class TestIntegrity:
    def test_constants_all_ids_unique(self):
        for collection in [PILLARS, AGENT_ROLES, DB_ARCHITECTURE_TIERS,
                           MEDALLION_TIERS, DATA_ENRICHMENT_APIS,
                           PRICING_MODELS, SECURITY_FRAMEWORKS,
                           CAPITALIZATION_PHASES, MARKET_METRICS,
                           TELEMETRY_METRICS]:
            ids = [item["id"] for item in collection]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {collection[0].get('title','?')}"

    def test_pillar_has_keywords(self):
        for p in PILLARS:
            assert "keywords" in p
            assert len(p["keywords"]) >= 5
