"""
Tests for praxis.resonance — v16 The Resonance.

Covers:
  - 5 pillar scorers
  - 7 telemetry scorers
  - TRAP framework
  - DSRP theory
  - Wisdom agent detection
  - Master assessment (fields, resonance detection, warnings, bounds)
  - Reference data getters (counts, integrity, not-found)
"""
import pytest

# Allow running from repo root (python -m pytest) or from praxis/
try:
    from praxis.resonance import (
        score_temporal_substrate,
        score_code_agency,
        score_latent_steering,
        score_conductor_dashboard,
        score_meta_awareness,
        score_resonance_index,
        score_flow_state,
        score_loop_coherence,
        score_hitl_responsiveness,
        score_steering_precision,
        score_wisdom_coverage,
        score_ontological_alignment,
        score_trap,
        score_dsrp,
        detect_wisdom_agents,
        assess_resonance,
        get_pillars,
        get_pillar,
        get_trap_pillars,
        get_trap_pillar,
        get_dsrp_rules,
        get_dsrp_rule,
        get_wisdom_agents,
        get_wisdom_agent,
        get_telemetry_metrics,
        get_telemetry_metric,
        get_reinterpretation_table,
        get_resonant_chamber,
        PILLARS,
        TRAP_PILLARS,
        DSRP_RULES,
        WISDOM_AGENTS,
        TELEMETRY_METRICS,
        REINTERPRETATION_TABLE,
        RESONANT_CHAMBER,
    )
except ImportError:
    from resonance import (
        score_temporal_substrate,
        score_code_agency,
        score_latent_steering,
        score_conductor_dashboard,
        score_meta_awareness,
        score_resonance_index,
        score_flow_state,
        score_loop_coherence,
        score_hitl_responsiveness,
        score_steering_precision,
        score_wisdom_coverage,
        score_ontological_alignment,
        score_trap,
        score_dsrp,
        detect_wisdom_agents,
        assess_resonance,
        get_pillars,
        get_pillar,
        get_trap_pillars,
        get_trap_pillar,
        get_dsrp_rules,
        get_dsrp_rule,
        get_wisdom_agents,
        get_wisdom_agent,
        get_telemetry_metrics,
        get_telemetry_metric,
        get_reinterpretation_table,
        get_resonant_chamber,
        PILLARS,
        TRAP_PILLARS,
        DSRP_RULES,
        WISDOM_AGENTS,
        TELEMETRY_METRICS,
        REINTERPRETATION_TABLE,
        RESONANT_CHAMBER,
    )


# ── Rich query for high-coverage tests ──
RICH_QUERY = (
    "Build a real-time WebSocket bidirectional streaming system with asyncio "
    "concurrency and RxPY reactive Observables for full-duplex persistent "
    "low-latency multimodal audio interruption handling. "
    "Use MCP model context protocol with FastMCP SDK for LangGraph compound AI "
    "orchestration with Planner agent and recursive reflection loops. "
    "Apply ActAdd activation addition with steering vectors in latent space "
    "using transformer_lens forward hooks for CAST conditional activation "
    "steering with alpha coefficient and CLIP aesthetic cosine similarity. "
    "Deploy a Conductor dashboard with A2UI agent-to-UI protocol and HITL "
    "human-in-the-loop non-bypassable approval gates via Temporal durable "
    "workflow with ExplainerDashboard and episodic memory for slopsquatting defense. "
    "Enable meta-awareness with TRAP transparency reasoning adaptation perception "
    "and DSRP distinctions systems relationships perspectives via Wisdom Layer "
    "cognitive oversight with complexity sentinel chaos agent karma agent "
    "systems thinking feedback loops ontological drift and reflection agent "
    "epistemic awareness logarithm telemetry."
)


class TestPillarScoring:
    """Test all 5 pillar scoring functions."""

    def test_temporal_substrate_rich(self):
        r = score_temporal_substrate(RICH_QUERY)
        assert r["pillar"] == "I"
        assert r["score"] > 0
        assert r["grade"] in ("A+", "A", "B", "C", "D", "F")

    def test_code_agency_rich(self):
        r = score_code_agency(RICH_QUERY)
        assert r["pillar"] == "II"
        assert r["score"] > 0

    def test_latent_steering_rich(self):
        r = score_latent_steering(RICH_QUERY)
        assert r["pillar"] == "III"
        assert r["score"] > 0

    def test_conductor_dashboard_rich(self):
        r = score_conductor_dashboard(RICH_QUERY)
        assert r["pillar"] == "IV"
        assert r["score"] > 0

    def test_meta_awareness_rich(self):
        r = score_meta_awareness(RICH_QUERY)
        assert r["pillar"] == "V"
        assert r["score"] > 0

    def test_empty_query_scores_zero(self):
        r = score_temporal_substrate("")
        assert r["score"] == 0.0
        assert r["grade"] == "F"

    def test_unrelated_query_scores_low(self):
        r = score_latent_steering("I need a recipe for banana bread")
        assert r["score"] < 0.3


class TestTelemetryScoring:
    """Test all 7 telemetry metric scorers."""

    def test_resonance_index(self):
        r = score_resonance_index(RICH_QUERY)
        assert r["metric"] == "resonance_index"
        assert r["symbol"] == "R_i"

    def test_flow_state(self):
        r = score_flow_state(RICH_QUERY)
        assert r["metric"] == "flow_state"

    def test_loop_coherence(self):
        r = score_loop_coherence(RICH_QUERY)
        assert r["metric"] == "loop_coherence"

    def test_hitl_responsiveness(self):
        r = score_hitl_responsiveness(RICH_QUERY)
        assert r["metric"] == "hitl_responsiveness"
        assert r["score"] > 0

    def test_steering_precision(self):
        r = score_steering_precision(RICH_QUERY)
        assert r["metric"] == "steering_precision"

    def test_wisdom_coverage(self):
        r = score_wisdom_coverage(RICH_QUERY)
        assert r["metric"] == "wisdom_coverage"

    def test_ontological_alignment(self):
        r = score_ontological_alignment(RICH_QUERY)
        assert r["metric"] == "ontological_alignment"


class TestTRAPFramework:
    """Test TRAP scoring."""

    def test_trap_returns_four_pillars(self):
        r = score_trap(RICH_QUERY)
        assert "scores" in r
        assert len(r["scores"]) == 4
        for k in ("transparency", "reasoning", "adaptation", "perception"):
            assert k in r["scores"]

    def test_trap_composite(self):
        r = score_trap(RICH_QUERY)
        assert 0 <= r["composite"] <= 1.0
        assert r["grade"] in ("A+", "A", "B", "C", "D", "F")

    def test_trap_empty(self):
        r = score_trap("")
        assert r["composite"] == 0.0


class TestDSRPTheory:
    """Test DSRP scoring."""

    def test_dsrp_returns_four_rules(self):
        r = score_dsrp(RICH_QUERY)
        assert "scores" in r
        assert len(r["scores"]) == 4
        for k in ("distinctions", "systems", "relationships", "perspectives"):
            assert k in r["scores"]

    def test_dsrp_composite(self):
        r = score_dsrp(RICH_QUERY)
        assert 0 <= r["composite"] <= 1.0

    def test_dsrp_empty(self):
        r = score_dsrp("")
        assert r["composite"] == 0.0


class TestWisdomAgents:
    """Test Wisdom Layer agent detection."""

    def test_agents_detected_rich(self):
        agents = detect_wisdom_agents(RICH_QUERY)
        assert len(agents) >= 4
        assert "systems_thinking" in agents

    def test_no_agents_for_empty(self):
        agents = detect_wisdom_agents("")
        assert agents == []

    def test_karma_detected(self):
        agents = detect_wisdom_agents("Evaluate the moral and ethical consequences of technical debt")
        assert "karma" in agents

    def test_chaos_detected(self):
        agents = detect_wisdom_agents("Run chaos simulation for non-linear fragility analysis")
        assert "chaos_theory" in agents


class TestMasterAssessment:
    """Test the master assess_resonance function."""

    def test_assessment_has_all_fields(self):
        r = assess_resonance(RICH_QUERY)
        assert "resonance_score" in r
        assert "grade" in r
        assert "temporal_substrate" in r
        assert "code_agency" in r
        assert "latent_steering" in r
        assert "conductor_dashboard" in r
        assert "meta_awareness" in r
        assert "trap_scores" in r
        assert "trap_grade" in r
        assert "dsrp_scores" in r
        assert "dsrp_grade" in r
        assert "wisdom_agents_active" in r
        assert "resonance_detected" in r
        assert "resonance_evidence" in r
        assert "warnings" in r

    def test_score_in_bounds(self):
        r = assess_resonance(RICH_QUERY)
        assert 0.0 <= r["resonance_score"] <= 1.0

    def test_resonance_detected_on_rich_query(self):
        r = assess_resonance(RICH_QUERY)
        assert r["resonance_detected"] is True
        assert len(r["resonance_evidence"]) > 0

    def test_warnings_on_empty(self):
        r = assess_resonance("")
        assert len(r["warnings"]) > 0
        assert r["grade"] == "F"

    def test_telemetry_fields_present(self):
        r = assess_resonance(RICH_QUERY)
        for k in ("resonance_index", "flow_state", "loop_coherence",
                   "hitl_responsiveness", "steering_precision",
                   "wisdom_coverage", "ontological_alignment"):
            assert k in r
            assert "score" in r[k]


class TestReferenceData:
    """Test all getter functions and constant integrity."""

    def test_pillars_count(self):
        assert len(get_pillars()) == 5

    def test_pillar_lookup(self):
        p = get_pillar("temporal_substrate")
        assert p is not None
        assert p["number"] == "I"

    def test_pillar_not_found(self):
        assert get_pillar("nonexistent") is None

    def test_trap_count(self):
        assert len(get_trap_pillars()) == 4

    def test_trap_lookup(self):
        p = get_trap_pillar("transparency")
        assert p is not None
        assert p["letter"] == "T"

    def test_trap_not_found(self):
        assert get_trap_pillar("nonexistent") is None

    def test_dsrp_count(self):
        assert len(get_dsrp_rules()) == 4

    def test_dsrp_lookup(self):
        r = get_dsrp_rule("distinctions")
        assert r is not None
        assert r["letter"] == "D"

    def test_dsrp_not_found(self):
        assert get_dsrp_rule("nonexistent") is None

    def test_wisdom_agents_count(self):
        assert len(get_wisdom_agents()) == 7

    def test_wisdom_agent_lookup(self):
        a = get_wisdom_agent("karma")
        assert a is not None
        assert "Karma" in a["title"]

    def test_wisdom_agent_not_found(self):
        assert get_wisdom_agent("nonexistent") is None

    def test_telemetry_count(self):
        assert len(get_telemetry_metrics()) == 7

    def test_telemetry_lookup(self):
        m = get_telemetry_metric("resonance_index")
        assert m is not None
        assert m["symbol"] == "R_i"

    def test_telemetry_not_found(self):
        assert get_telemetry_metric("nonexistent") is None

    def test_reinterpretation_count(self):
        assert len(get_reinterpretation_table()) == 10

    def test_resonant_chamber(self):
        c = get_resonant_chamber()
        assert "thesis" in c
        assert "dyadic_structure" in c
        assert "singularity_thesis" in c
        assert "loop_closure_warning" in c

    def test_constant_integrity(self):
        assert len(PILLARS) == 5
        assert len(TRAP_PILLARS) == 4
        assert len(DSRP_RULES) == 4
        assert len(WISDOM_AGENTS) == 7
        assert len(TELEMETRY_METRICS) == 7
        assert len(REINTERPRETATION_TABLE) == 10
        assert "thesis" in RESONANT_CHAMBER
