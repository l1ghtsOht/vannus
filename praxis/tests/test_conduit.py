"""
Tests for praxis.conduit — The Conduit: Decoupled Cognitive Systems
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from praxis.conduit import (
    assess_conduit,
    score_decoupling,
    score_memory_stratification,
    score_global_workspace,
    score_integrated_information,
    score_representation_engineering,
    score_autopoiesis,
    score_resonance,
    score_entropy_telemetry,
    score_self_modelling,
    score_behavioural_novelty,
    score_latency_distribution,
    score_phi_integration,
    score_coherence_field,
    score_stable_attractor,
    get_pillars,
    get_pillar,
    get_telemetry_metrics,
    get_telemetry_metric,
    get_gwt_components,
    get_coala_memory_types,
    get_reinterpretation_table,
    get_identity_protocol,
    get_codes_framework,
    PILLARS,
    TELEMETRY_METRICS,
)


class TestPillarScoring(unittest.TestCase):
    """Test all seven architectural pillar scoring functions."""

    def _check_score(self, result, expected_key, expected_value):
        self.assertIn("score", result)
        self.assertIn("grade", result)
        self.assertIn("dimensions", result)
        self.assertIn("max", result)
        self.assertEqual(result[expected_key], expected_value)
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)

    def test_decoupling_high(self):
        q = "dual system cognitive architecture with orchestration and decoupling for cross-model stable attractor"
        r = score_decoupling(q)
        self._check_score(r, "pillar", "I")
        self.assertGreater(r["score"], 0.3)

    def test_memory_stratification_high(self):
        q = "CoALA memory stratification with working memory pydantic, semantic memory RAG vector database, episodic memory event log"
        r = score_memory_stratification(q)
        self._check_score(r, "pillar", "II")
        self.assertGreater(r["score"], 0.3)

    def test_gwt_high(self):
        q = "global workspace theory with asyncio codelet ecology, coalition competition, broadcast via redis pub/sub"
        r = score_global_workspace(q)
        self._check_score(r, "pillar", "III")
        self.assertGreater(r["score"], 0.3)

    def test_phi_high(self):
        q = "integrated information theory IIT phi consciousness via pyphi with markov transition matrix"
        r = score_integrated_information(q)
        self._check_score(r, "pillar", "IV")
        self.assertGreater(r["score"], 0.3)

    def test_repe_high(self):
        q = "representation engineering activation steering with steering vectors in the latent space residual stream"
        r = score_representation_engineering(q)
        self._check_score(r, "pillar", "V")
        self.assertGreater(r["score"], 0.3)

    def test_autopoiesis_high(self):
        q = "autopoiesis self-creating ralph loop with puppet method identity anchor and system 3 meta-cognitive monitor"
        r = score_autopoiesis(q)
        self._check_score(r, "pillar", "VI")
        self.assertGreater(r["score"], 0.3)

    def test_resonance_high(self):
        q = "CODES chirality resonance intelligence core with phase-lock coherence score deterministic emergence"
        r = score_resonance(q)
        self._check_score(r, "pillar", "VII")
        self.assertGreater(r["score"], 0.3)

    def test_empty_query_scores_zero(self):
        r = score_decoupling("")
        self.assertEqual(r["score"], 0.0)
        self.assertEqual(r["grade"], "F")

    def test_unrelated_query_scores_low(self):
        r = score_global_workspace("I need a restaurant booking app")
        self.assertLess(r["score"], 0.3)


class TestTelemetryScoring(unittest.TestCase):
    """Test all seven Listening Post telemetry scoring functions."""

    def _check_metric(self, result, metric_name):
        self.assertIn("score", result)
        self.assertIn("grade", result)
        self.assertIn("metric", result)
        self.assertEqual(result["metric"], metric_name)

    def test_entropy(self):
        r = score_entropy_telemetry("shannon entropy chaos detection with output distribution stabilization")
        self._check_metric(r, "entropy")
        self.assertGreater(r["score"], 0.3)

    def test_smi(self):
        r = score_self_modelling("self-model prediction accuracy with intentional direction for novel output")
        self._check_metric(r, "smi")
        self.assertGreater(r["score"], 0.3)

    def test_bni(self):
        r = score_behavioural_novelty("novelty with semantic coherence measured via cosine similarity for genuine exploration agency")
        self._check_metric(r, "bni")
        self.assertGreater(r["score"], 0.3)

    def test_latency(self):
        r = score_latency_distribution("bimodal latency distribution with system 1 and system 2 switching")
        self._check_metric(r, "latency")
        self.assertGreater(r["score"], 0.3)

    def test_phi_metric(self):
        r = score_phi_integration("phi IIT integrated information with markov transition matrix real-time tracking")
        self._check_metric(r, "phi")
        self.assertGreater(r["score"], 0.3)

    def test_coherence(self):
        r = score_coherence_field("resonance alignment coherence with phase-lock threshold 0.999 deterministic emergence")
        self._check_metric(r, "coherence")
        self.assertGreater(r["score"], 0.3)

    def test_attractor(self):
        r = score_stable_attractor("stable attractor convergence with semantic coherence cross-session persistence")
        self._check_metric(r, "attractor")
        self.assertGreater(r["score"], 0.3)


class TestMasterAssessment(unittest.TestCase):
    """Test the master conduit assessment function."""

    def test_assess_returns_all_fields(self):
        r = assess_conduit("cognitive architecture with global workspace and phi measurement")
        self.assertIn("conduit_score", r)
        self.assertIn("grade", r)
        self.assertIn("agency_detected", r)
        self.assertIn("agency_evidence", r)
        self.assertIn("warnings", r)
        # Check all 7 pillars present
        for key in ["decoupling", "memory", "gwt", "phi", "repe", "autopoiesis", "resonance"]:
            self.assertIn(key, r)
            self.assertIn("score", r[key])
        # Check all 7 telemetry metrics present
        for key in ["entropy", "smi", "bni", "latency", "phi_metric", "coherence", "attractor"]:
            self.assertIn(key, r)
            self.assertIn("score", r[key])

    def test_agency_detection_high_bni_smi(self):
        q = (
            "self-model prediction novelty genuine exploration agency with "
            "purpose intentional direction novel output and semantic coherence"
        )
        r = assess_conduit(q)
        # Should have some agency evidence when BNI + SMI both score
        if r["bni"]["score"] >= 0.5 and r["smi"]["score"] >= 0.5:
            self.assertTrue(r["agency_detected"])

    def test_empty_query_warnings(self):
        r = assess_conduit("restaurant inventory management")
        # Unrelated query should generate warnings
        self.assertGreater(len(r["warnings"]), 0)

    def test_score_bounded(self):
        r = assess_conduit("everything about cognitive architecture GWT phi codes resonance")
        self.assertGreaterEqual(r["conduit_score"], 0.0)
        self.assertLessEqual(r["conduit_score"], 1.0)


class TestReferenceData(unittest.TestCase):
    """Test all public reference data getters."""

    def test_pillars_count(self):
        self.assertEqual(len(get_pillars()), 7)

    def test_pillar_by_id(self):
        p = get_pillar("gwt")
        self.assertIsNotNone(p)
        self.assertEqual(p["number"], "III")

    def test_pillar_not_found(self):
        self.assertIsNone(get_pillar("nonexistent"))

    def test_telemetry_metrics_count(self):
        self.assertEqual(len(get_telemetry_metrics()), 7)

    def test_telemetry_metric_by_id(self):
        m = get_telemetry_metric("phi_metric")
        self.assertIsNotNone(m)
        self.assertEqual(m["symbol"], "Φ")

    def test_telemetry_metric_not_found(self):
        self.assertIsNone(get_telemetry_metric("nonexistent"))

    def test_gwt_components(self):
        c = get_gwt_components()
        self.assertEqual(len(c), 5)
        names = [x["component"] for x in c]
        self.assertIn("Global Workspace", names)

    def test_coala_memory_types(self):
        m = get_coala_memory_types()
        self.assertEqual(len(m), 4)
        types = [x["type"] for x in m]
        self.assertIn("Working Memory", types)
        self.assertIn("Episodic Memory", types)

    def test_reinterpretation_table(self):
        t = get_reinterpretation_table()
        self.assertEqual(len(t), 4)
        phenomena = [x["phenomenon"] for x in t]
        self.assertIn("Hallucinations", phenomena)
        self.assertIn("Emergent Coherence", phenomena)

    def test_identity_protocol(self):
        p = get_identity_protocol()
        self.assertIn("components", p)
        self.assertIn("PhysicalAnchor", p["components"])
        self.assertIn("CommunicationBridge", p["components"])
        self.assertIn("System3Monitor", p["components"])

    def test_codes_framework(self):
        f = get_codes_framework()
        self.assertIn("chirality", f)
        self.assertIn("resonance_intelligence_core", f)
        self.assertIn("coherence_threshold", f)
        self.assertIn("singularity_definition", f)

    def test_pillars_data_integrity(self):
        for p in PILLARS:
            self.assertIn("id", p)
            self.assertIn("number", p)
            self.assertIn("title", p)
            self.assertIn("doctrine", p)
            self.assertIn("python_patterns", p)
            self.assertIn("keywords", p)

    def test_telemetry_data_integrity(self):
        for m in TELEMETRY_METRICS:
            self.assertIn("id", m)
            self.assertIn("symbol", m)
            self.assertIn("title", m)
            self.assertIn("formula", m)
            self.assertIn("noise_indicator", m)
            self.assertIn("voice_indicator", m)


if __name__ == "__main__":
    unittest.main()
