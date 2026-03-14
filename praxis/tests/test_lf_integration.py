#!/usr/bin/env python3
"""Integration tests for v25.4 Latent Flux integration.

Validates all three phases:
  Phase 1: σ² in ReservoirState (LF repo — skip if not importable)
  Phase 2: Pure-Python adapter (praxis/lf_monitor.py)
  Phase 3: trust_decay.py wiring

Runs standalone or via pytest:
  python praxis/tests/test_lf_integration.py
  python -m pytest praxis/tests/test_lf_integration.py -v
"""

import math
import os
import random
import sys
import unittest

# Ensure praxis is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# =====================================================================
# Phase 1: σ² in ReservoirState (LF repo)
# =====================================================================

_HAS_LF = False
try:
    sys.path.insert(0, os.path.expanduser('~/Desktop/latent-flux-master'))
    from flux_manifold.reservoir_state import ReservoirState
    import numpy as np
    _HAS_LF = True
except ImportError:
    pass


@unittest.skipUnless(_HAS_LF, "Latent Flux repo not on sys.path")
class TestPhase1_ReservoirStateSigma(unittest.TestCase):
    """Phase 1: σ² tracking in ReservoirState (LF repo)."""

    def setUp(self):
        self.rs = ReservoirState(d=4, leak_rate=0.3, seed=42)

    def test_variance_starts_zero(self):
        v = self.rs.variance
        self.assertEqual(len(v), 4)
        for val in v:
            self.assertAlmostEqual(float(val), 0.0, places=6)

    def test_std_equals_sqrt_variance(self):
        # Feed some data first
        for _ in range(5):
            self.rs.step(np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        v = self.rs.variance
        s = self.rs.std
        for i in range(4):
            self.assertAlmostEqual(float(s[i]), math.sqrt(max(float(v[i]), 1e-12)), places=5)

    def test_deviation_score_returns_scalar(self):
        for _ in range(5):
            self.rs.step(np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        score = self.rs.deviation_score(np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)

    def test_variance_accumulates(self):
        rng = random.Random(99)
        for _ in range(20):
            x = np.array([rng.gauss(0, 1) for _ in range(4)], dtype=np.float32)
            self.rs.step(x)
        v = self.rs.variance
        self.assertTrue(any(float(val) > 0 for val in v), f"Variance still zero after 20 steps: {v}")

    def test_outlier_higher_deviation(self):
        for _ in range(20):
            self.rs.step(np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))
        near = self.rs.deviation_score(np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))
        far = self.rs.deviation_score(np.array([100.0, 100.0, 100.0, 100.0], dtype=np.float32))
        self.assertGreater(far, near, f"Outlier score {far} should exceed near-baseline {near}")

    def test_reset_clears_variance(self):
        for _ in range(10):
            self.rs.step(np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        self.rs.reset()
        v = self.rs.variance
        for val in v:
            self.assertAlmostEqual(float(val), 0.0, places=6)


# =====================================================================
# Phase 2: Pure-Python adapter (praxis/lf_monitor.py)
# =====================================================================

from praxis.lf_monitor import (
    ToolReservoir,
    PipelineHealthCompetitor,
    CompetitionResult,
    RetryLoopDetector,
    LoopResult,
    OrchestrationMonitor,
)


class TestPhase2_ToolReservoir(unittest.TestCase):
    """Phase 2: ToolReservoir (pure Python ESN + σ²)."""

    def test_construct(self):
        r = ToolReservoir(d=6, leak_rate=0.1, seed=42)
        self.assertEqual(r.d, 6)
        self.assertEqual(r.step_count, 0)

    def test_step_returns_list(self):
        r = ToolReservoir(d=6)
        y = r.step([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        self.assertIsInstance(y, list)
        self.assertEqual(len(y), 6)

    def test_variance_accumulates(self):
        r = ToolReservoir(d=6, leak_rate=0.1)
        rng = random.Random(42)
        for _ in range(30):
            x = [rng.gauss(0, 1) for _ in range(6)]
            r.step(x)
        v = r.variance
        self.assertTrue(any(val > 0 for val in v), f"Variance still zero: {v}")

    def test_deviation_score_nonnegative(self):
        r = ToolReservoir(d=6, leak_rate=0.1)
        for _ in range(10):
            r.step([0.1] * 6)
        score = r.deviation_score([0.1] * 6)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)

    def test_deviation_score_zero_when_cold(self):
        r = ToolReservoir(d=6)
        # Only 1 step — should return 0
        r.step([1.0] * 6)
        self.assertEqual(r.deviation_score([1.0] * 6), 0.0)

    def test_to_dict(self):
        r = ToolReservoir(d=6)
        r.step([1.0] * 6)
        d = r.to_dict()
        self.assertIn("d", d)
        self.assertIn("variance", d)
        self.assertIn("step_count", d)
        self.assertEqual(d["step_count"], 1)


class TestPhase2_PipelineHealthCompetitor(unittest.TestCase):
    """Phase 2: PipelineHealthCompetitor (3-basin attractor)."""

    def test_construct(self):
        c = PipelineHealthCompetitor(d=6)
        self.assertEqual(c.d, 6)

    def test_compete_returns_result(self):
        c = PipelineHealthCompetitor(d=6)
        result = c.compete([0.0] * 6)
        self.assertIsInstance(result, CompetitionResult)
        self.assertIn(result.winner, ("healthy", "degrading", "failing"))

    def test_near_zero_is_healthy(self):
        c = PipelineHealthCompetitor(d=3)
        result = c.compete([0.1, 0.2, 0.1])
        self.assertEqual(result.winner.lower(), "healthy")

    def test_extreme_is_failing(self):
        c = PipelineHealthCompetitor(d=3)
        result = c.compete([10.0, 10.0, 10.0])
        self.assertEqual(result.winner.lower(), "failing")

    def test_mid_is_degrading(self):
        c = PipelineHealthCompetitor(d=3)
        result = c.compete([1.0, 1.0, 1.0])
        self.assertEqual(result.winner.lower(), "degrading")


class TestPhase2_RetryLoopDetector(unittest.TestCase):
    """Phase 2: RetryLoopDetector (cycle detection)."""

    def test_construct(self):
        d = RetryLoopDetector(max_depth=5)
        self.assertEqual(d.max_depth, 5)

    def test_no_loop_on_short_sequence(self):
        d = RetryLoopDetector()
        result = d.detect([0.8])
        self.assertIsInstance(result, LoopResult)
        self.assertFalse(result.is_looping)

    def test_loop_detected_on_oscillation(self):
        d = RetryLoopDetector(convergence_threshold=0.05)
        # Oscillating: pass, fail, pass, fail, pass, fail
        result = d.detect([0.9, 0.1, 0.9, 0.1, 0.9, 0.1])
        self.assertTrue(result.is_looping)
        self.assertGreater(result.cycle_depth, 3)

    def test_breaker_trips_on_deep_loop(self):
        d = RetryLoopDetector(max_depth=3)
        result = d.detect([0.9, 0.1, 0.9, 0.1, 0.9, 0.1, 0.9, 0.1])
        self.assertTrue(d.should_trip_breaker(result, deviation_score=0.0))

    def test_breaker_trips_with_sigma(self):
        d = RetryLoopDetector(max_depth=10, sigma_threshold=1.5)
        result = d.detect([0.8, 0.2, 0.7, 0.3, 0.8, 0.2])  # 6 oscillating outcomes
        # cycle_depth = 5 (all drifts > threshold), deviation_score high
        self.assertTrue(d.should_trip_breaker(result, deviation_score=3.0))


class TestPhase2_OrchestrationMonitor(unittest.TestCase):
    """Phase 2: OrchestrationMonitor (composition)."""

    def test_construct(self):
        m = OrchestrationMonitor()
        self.assertEqual(m.d, 6)

    def test_record_tool_call(self):
        m = OrchestrationMonitor()
        score = m.record_tool_call("Claude", [100, 0.9, 500, 0.01, 200, 0.05])
        self.assertIsInstance(score, float)

    def test_get_tool_states(self):
        m = OrchestrationMonitor()
        for i in range(25):
            m.record_tool_call("stable_tool", [100, 0.9, 500, 0.01, 200, 0.05])
        states = m.get_all_tool_states()
        self.assertIn("stable_tool", states)
        self.assertEqual(states["stable_tool"]["step_count"], 25)

    def test_assess_pipeline_health(self):
        m = OrchestrationMonitor()
        for _ in range(10):
            m.record_tool_call("tool_a", [100, 0.9, 500, 0.01, 200, 0.05])
        health = m.assess_pipeline_health()
        self.assertIsInstance(health, CompetitionResult)
        self.assertIn(health.winner, ("healthy", "degrading", "failing"))

    def test_independent_baselines(self):
        m = OrchestrationMonitor()
        for _ in range(15):
            m.record_tool_call("fast_tool", [0.05, 0.95, 100, 0.0, 50, 0.001])
            m.record_tool_call("slow_tool", [2.0, 0.7, 800, 0.05, 300, 0.1])
        states = m.get_all_tool_states()
        self.assertIn("fast_tool", states)
        self.assertIn("slow_tool", states)
        self.assertEqual(states["fast_tool"]["step_count"], 15)
        self.assertEqual(states["slow_tool"]["step_count"], 15)

    def test_retry_loop_detection(self):
        m = OrchestrationMonitor()
        for outcome in [0.9, 0.1, 0.8, 0.2, 0.7, 0.1, 0.8, 0.2]:
            m.record_retry_outcome("code_stage", outcome)
        result, should_trip = m.check_retry_loops("code_stage")
        self.assertIsInstance(result, LoopResult)
        self.assertTrue(result.is_looping)


# =====================================================================
# Phase 3: trust_decay.py wiring
# =====================================================================

class TestPhase3_TrustDecayWiring(unittest.TestCase):
    """Phase 3: LF integration in trust_decay.py."""

    def test_import_succeeds(self):
        import praxis.trust_decay as td
        self.assertTrue(hasattr(td, 'lf_record_tool_call'))
        self.assertTrue(hasattr(td, 'lf_assess_severity'))
        self.assertTrue(hasattr(td, 'lf_get_tool_states'))

    def test_lf_record_tool_call(self):
        from praxis.trust_decay import lf_record_tool_call
        # Positional args
        score = lf_record_tool_call("test_tool", 0.12, 0.93, 450, 0.0, 180, 0.001)
        # Should return a float or None
        self.assertTrue(score is None or isinstance(score, float))

    def test_lf_record_tool_call_kwargs(self):
        from praxis.trust_decay import lf_record_tool_call
        score = lf_record_tool_call(
            tool_name="test_tool_kw",
            latency_ms=0.12,
            quality_score=0.93,
            token_consumption=450,
            error_rate=0.0,
            output_length=180,
            cost_per_call=0.001,
        )
        self.assertTrue(score is None or isinstance(score, float))

    def test_lf_assess_severity(self):
        from praxis.trust_decay import lf_assess_severity
        severity = lf_assess_severity("test_tool")
        self.assertIsInstance(severity, str)
        self.assertIn(severity, ("none", "mild", "severe"))

    def test_lf_get_tool_states(self):
        from praxis.trust_decay import lf_record_tool_call, lf_get_tool_states
        # Record some data first
        for _ in range(5):
            lf_record_tool_call("reliable_tool", 100, 0.9, 500, 0.01, 200, 0.05)
        states = lf_get_tool_states()
        if states is not None:
            self.assertIsInstance(states, dict)
            # Should contain at least one tool
            self.assertGreater(len(states), 0)

    def test_garbage_input_no_crash(self):
        from praxis.trust_decay import lf_record_tool_call
        # These should either succeed or raise a clean error — NOT crash
        try:
            lf_record_tool_call("garbage_tool", -999, -1, 0, 0, 0, 0)
        except (ValueError, TypeError, OverflowError):
            pass  # Clean error is acceptable

        try:
            lf_record_tool_call("inf_tool", float('inf'), 0, 0, 0, 0, 0)
        except (ValueError, TypeError, OverflowError):
            pass  # Clean error is acceptable


# =====================================================================
# Behavioral scenarios
# =====================================================================

class TestBehavioralScenarios(unittest.TestCase):
    """Cross-cutting behavioral validation."""

    def test_stable_tool_low_deviation(self):
        r = ToolReservoir(d=6, leak_rate=0.1, seed=7)
        rng = random.Random(7)
        for _ in range(50):
            x = [0.1 + rng.gauss(0, 0.01) for _ in range(6)]
            r.step(x)
        score = r.deviation_score([0.1] * 6)
        self.assertLess(score, 5.0, f"Stable tool deviation too high: {score}")

    def test_degrading_tool_rising_variance(self):
        r = ToolReservoir(d=6, leak_rate=0.1, seed=8)
        # 30 stable
        for _ in range(30):
            r.step([1.0] * 6)
        var_before = sum(r.variance)
        # 30 drifting
        for i in range(30):
            drift = [1.0 + i * 0.02 * (j + 1) for j in range(6)]
            r.step(drift)
        var_after = sum(r.variance)
        self.assertGreater(var_after, var_before,
                           f"Variance should increase with drift: before={var_before}, after={var_after}")

    def test_independent_tool_baselines(self):
        m = OrchestrationMonitor()
        for _ in range(15):
            m.record_tool_call("fast", [0.05, 0.95, 100, 0.0, 50, 0.001])
            m.record_tool_call("slow", [2.0, 0.7, 800, 0.05, 300, 0.1])
        states = m.get_all_tool_states()
        self.assertIn("fast", states)
        self.assertIn("slow", states)
        # Both should have tracked independently
        self.assertEqual(states["fast"]["step_count"], 15)
        self.assertEqual(states["slow"]["step_count"], 15)


# =====================================================================
# Pure Python constraint
# =====================================================================

class TestPurePythonConstraint(unittest.TestCase):
    """Verify lf_monitor.py has no hard NumPy/ML imports."""

    def test_no_banned_imports(self):
        src_path = os.path.join(os.path.dirname(__file__), '..', 'lf_monitor.py')
        with open(src_path, 'r') as f:
            lines = f.readlines()

        banned = {'numpy', 'torch', 'sklearn', 'scipy', 'pandas', 'tensorflow'}
        try_depth = 0
        violations = []

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('try:'):
                try_depth += 1
            elif stripped.startswith(('except', 'except:')):
                try_depth = max(0, try_depth - 1)
            elif stripped.startswith(('import ', 'from ')):
                if try_depth == 0:
                    for pkg in banned:
                        if pkg in stripped.split():
                            violations.append(f"Line {lineno}: {stripped}")

        self.assertEqual(violations, [],
                         f"Found banned imports outside try/except: {violations}")


# =====================================================================
# Phase 4: Journey reservoir drift detection
# =====================================================================

class TestPhase4_JourneyReservoirDrift(unittest.TestCase):
    """Journey.py LF-enhanced drift detection."""

    def test_journey_import(self):
        from praxis.journey import get_oracle, JourneyStage, TargetScoreVector
        oracle = get_oracle()
        self.assertIsNotNone(oracle)

    def test_reservoir_created_on_target(self):
        from praxis.journey import get_oracle, JourneyStage, TargetScoreVector
        oracle = get_oracle()
        jid = oracle.create_journey("test_p4a", "reservoir test")
        oracle.advance(jid, JourneyStage.SELECTION)
        oracle.set_target_vector(jid, "ReservoirTool", TargetScoreVector(0.9, 0.8, 0.7, 0.6))
        rstate = oracle.get_reservoir_state("ReservoirTool")
        # Should exist if LF is available
        if rstate is not None:
            self.assertIn("step_count", rstate)
            self.assertGreater(rstate["step_count"], 0)

    def test_stable_data_low_drift(self):
        from praxis.journey import get_oracle, JourneyStage, TargetScoreVector
        oracle = get_oracle()
        jid = oracle.create_journey("test_p4b", "stable test")
        oracle.advance(jid, JourneyStage.SELECTION)
        oracle.set_target_vector(jid, "StableTool", TargetScoreVector(0.8, 0.8, 0.8, 0.8))
        oracle.record_outcome(jid, "StableTool", satisfaction=0.75, roi=0.7, integration_success=0.8)
        signals = oracle.detect_drift(jid)
        # With stable data, drift should be minimal or empty
        severe = [s for s in signals if s.severity == "severe"]
        self.assertEqual(len(severe), 0, f"Unexpected severe drift from stable data: {severe}")

    def test_get_reservoir_state(self):
        from praxis.journey import get_oracle
        oracle = get_oracle()
        rstate = oracle.get_reservoir_state("NonexistentTool999")
        # Should return None for a tool that hasn't been tracked
        self.assertIsNone(rstate)

    def test_apply_drift_corrections(self):
        from praxis.journey import get_oracle
        oracle = get_oracle()
        corrections = oracle.apply_drift_corrections()
        self.assertIsInstance(corrections, list)


# =====================================================================
# Phase 5: Circuit breaker sigma-based trip
# =====================================================================

class TestPhase5_CircuitBreakerSigma(unittest.TestCase):
    """llm_resilience.py LF-enhanced circuit breaker."""

    def test_imports(self):
        from praxis.llm_resilience import record_provider_metrics, get_provider_health, check_sigma_trip
        self.assertTrue(callable(record_provider_metrics))
        self.assertTrue(callable(get_provider_health))
        self.assertTrue(callable(check_sigma_trip))

    def test_record_provider_metrics(self):
        from praxis.llm_resilience import record_provider_metrics
        dev = record_provider_metrics("test_p5", latency_ms=100, error_rate=0.01, quality_score=0.9, cost_usd=0.05)
        self.assertIsInstance(dev, float)
        self.assertGreaterEqual(dev, 0.0)

    def test_get_provider_health(self):
        from praxis.llm_resilience import record_provider_metrics, get_provider_health
        for _ in range(5):
            record_provider_metrics("health_test_p5", latency_ms=100, error_rate=0.0, quality_score=0.95, cost_usd=0.01)
        health = get_provider_health("health_test_p5")
        self.assertIn("deviation_score", health)
        self.assertIn("circuit_state", health)
        self.assertIn("lf_available", health)
        self.assertEqual(health["circuit_state"], "CLOSED")

    def test_sigma_no_trip_on_stable(self):
        from praxis.llm_resilience import record_provider_metrics, check_sigma_trip
        for _ in range(10):
            record_provider_metrics("stable_p5", latency_ms=100, error_rate=0.01, quality_score=0.9, cost_usd=0.05)
        self.assertFalse(check_sigma_trip("stable_p5", deviation_threshold=4.0))

    def test_sigma_trip_needs_history(self):
        from praxis.llm_resilience import check_sigma_trip
        # No history → should not trip
        self.assertFalse(check_sigma_trip("nonexistent_p5"))


# =====================================================================
# Phase 6: Journey API endpoints
# =====================================================================

class TestPhase6_JourneyAPI(unittest.TestCase):
    """Journey REST API endpoint availability."""

    def test_journey_create_function_exists(self):
        from praxis.journey import get_oracle
        oracle = get_oracle()
        self.assertTrue(hasattr(oracle, 'create_journey'))

    def test_journey_target_vector_function(self):
        from praxis.journey import get_oracle
        oracle = get_oracle()
        self.assertTrue(hasattr(oracle, 'set_target_vector'))

    def test_journey_dashboard(self):
        from praxis.journey import get_oracle
        oracle = get_oracle()
        dash = oracle.dashboard()
        self.assertIsNotNone(dash)
        d = dash.to_dict()
        self.assertIn("total_journeys", d)


# =====================================================================
# Runner
# =====================================================================

if __name__ == '__main__':
    # Colorized standalone runner
    import io

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    # Parse and colorize
    output = stream.getvalue()
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    skipped = len(result.skipped)
    passed = total - failures - skipped

    print("\n" + "=" * 60)
    print("LATENT FLUX INTEGRATION TEST RESULTS")
    print("=" * 60)

    for line in output.split('\n'):
        if '... ok' in line:
            name = line.split(' ... ')[0].strip()
            print(f"  [PASS] {name}")
        elif '... FAIL' in line or '... ERROR' in line:
            name = line.split(' ... ')[0].strip()
            print(f"  [FAIL] {name}")
        elif '... skipped' in line:
            name = line.split(' ... ')[0].strip()
            reason = line.split("'")[1] if "'" in line else "skipped"
            print(f"  [SKIP] {name} ({reason})")

    # Print failure details
    for test, traceback in result.failures + result.errors:
        print(f"\n--- FAIL: {test} ---")
        print(traceback)

    print(f"\n  Total: {total}  Pass: {passed}  Fail: {failures}  Skip: {skipped}")
    print("=" * 60)

    sys.exit(1 if failures else 0)
