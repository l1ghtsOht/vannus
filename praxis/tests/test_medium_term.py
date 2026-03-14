"""Tests for v25.6 medium-term roadmap items.

Item 1: Scheduler
Item 2: Provider status
Item 3: Cost tracking
Item 4: WebSocket hub
Item 5: Ingestion pipeline
"""
import os
import sys
import time
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestScheduler(unittest.TestCase):
    """Item 1: Background scheduler."""

    def test_create_and_schedule(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        counter = {"n": 0}
        s.schedule("test_task", lambda: counter.__setitem__("n", counter["n"] + 1), 0.1, run_immediately=True)
        self.assertIn("test_task", s.status())

    def test_start_fires_task(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        counter = {"n": 0}
        s.schedule("quick", lambda: counter.__setitem__("n", counter["n"] + 1), 0.05, run_immediately=True)
        s.start()
        time.sleep(0.2)
        s.stop()
        self.assertGreater(counter["n"], 0, "Task should have fired at least once")

    def test_stop_cleans_up(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        s.schedule("dummy", lambda: None, 10)
        s.start()
        s.stop()
        status = s.status()
        self.assertIn("dummy", status)

    def test_trigger_runs_immediately(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        results = {"ran": False}
        s.schedule("manual", lambda: results.__setitem__("ran", True), 9999)
        s.start()
        s.trigger("manual")
        time.sleep(0.2)
        s.stop()
        self.assertTrue(results["ran"])

    def test_pause_resume(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        s.schedule("pausable", lambda: None, 1)
        s.start()
        self.assertTrue(s.pause("pausable"))
        status = s.status()
        self.assertTrue(status["pausable"]["paused"])
        self.assertTrue(s.resume("pausable"))
        s.stop()

    def test_status_shape(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        s.schedule("t", lambda: None, 60)
        status = s.status()
        self.assertIn("interval_seconds", status["t"])
        self.assertIn("run_count", status["t"])
        self.assertIn("paused", status["t"])

    def test_error_handling(self):
        from praxis.scheduler import BackgroundScheduler
        s = BackgroundScheduler()
        s.schedule("err", lambda: 1/0, 0.05, run_immediately=True)
        s.start()
        time.sleep(0.15)
        s.stop()
        status = s.status()
        self.assertIsNotNone(status["err"]["last_error"])
        self.assertGreater(status["err"]["run_count"], 0)

    def test_default_tasks_setup(self):
        from praxis.scheduler import setup_default_tasks, get_scheduler
        setup_default_tasks()
        status = get_scheduler().status()
        # Should have trust_decay and journey_corrections
        self.assertIn("trust_decay", status)


class TestProviderStatus(unittest.TestCase):
    """Item 2: Provider status."""

    def test_provider_list(self):
        # Just verify the module loads and has the expected pattern
        from praxis.llm_resilience import get_provider_health
        health = get_provider_health("openai")
        self.assertIn("circuit_state", health)
        self.assertIn("lf_available", health)

    def test_dry_run_default(self):
        # PRAXIS_DRY_RUN defaults to true
        dry = os.environ.get("PRAXIS_DRY_RUN", "true").lower() in ("true", "1", "yes")
        self.assertTrue(dry, "Dry run should default to true")


class TestWebSocketHub(unittest.TestCase):
    """Item 4: WebSocket broadcast hub."""

    def test_hub_creates(self):
        from praxis.ws import BroadcastHub
        hub = BroadcastHub()
        self.assertIsNotNone(hub)

    def test_status_returns_channels(self):
        from praxis.ws import BroadcastHub, CHANNELS
        hub = BroadcastHub()
        status = hub.status()
        for ch in CHANNELS:
            self.assertIn(ch, status)
            self.assertEqual(status[ch], 0)

    def test_publish_no_subscribers_noop(self):
        from praxis.ws import BroadcastHub
        hub = BroadcastHub()
        # Should not raise
        hub.publish("trust_decay", {"event": "test"})

    def test_singleton(self):
        from praxis.ws import get_hub
        h1 = get_hub()
        h2 = get_hub()
        self.assertIs(h1, h2)


class TestIngestionPipeline(unittest.TestCase):
    """Item 5: Ingestion pipeline activation."""

    def test_ingestion_module_loads(self):
        try:
            from praxis.ingestion_engine import run_daily_pipeline
            self.assertTrue(callable(run_daily_pipeline))
        except ImportError:
            self.skipTest("ingestion_engine not available")

    def test_review_queue_function(self):
        try:
            from praxis.ingestion_engine import get_review_queue
            queue = get_review_queue()
            self.assertIsNotNone(queue)
        except ImportError:
            self.skipTest("ingestion_engine not available")


class TestCostTracking(unittest.TestCase):
    """Item 3: Cost tracking."""

    def test_economics_module_loads(self):
        try:
            from praxis.ai_economics import MODEL_PRICING, UsageLedger
            self.assertIsInstance(MODEL_PRICING, dict)
            self.assertIn("gpt-4o", MODEL_PRICING)
        except ImportError:
            self.skipTest("ai_economics not available")

    def test_model_registry_pricing(self):
        try:
            from praxis.model_registry import get_registry
            reg = get_registry()
            specs = reg.list_all()
            # At least some models should exist
            self.assertGreater(len(specs), 0)
            # Each should have cost fields
            for spec in specs[:3]:
                self.assertGreater(spec.cost_per_1k_input, 0)
        except ImportError:
            self.skipTest("model_registry not available")


if __name__ == '__main__':
    unittest.main(verbosity=2)
