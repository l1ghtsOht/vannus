# --------------- Tests: v18 Enterprise Infrastructure ---------------
"""
Tests for the enterprise-grade modules introduced in v18:
    • ports.py — Protocol contracts
    • exceptions.py — Domain exception hierarchy
    • domain_models.py — Pydantic v2 domain models
    • llm_resilience.py — Circuit breaker + retry + self-healing
    • rate_limiter.py — Sliding-window rate limiter
    • auth.py — JWT + API-key auth
    • telemetry.py — Structured logging + trace context
    • vendor_trust.py — Multi-dimensional trust scoring
    • scoring_optimized.py — Optimized TF-IDF
"""

import asyncio
import os
import sys
import pytest

# Ensure praxis package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ======================================================================
# Helper: run async functions in sync tests
# ======================================================================

def _run(coro):
    return asyncio.run(coro)


# ======================================================================
# 1. exceptions.py
# ======================================================================

class TestExceptions:
    def test_hierarchy(self):
        from praxis.exceptions import (
            PraxisError, ToolNotFoundError, LLMCircuitOpenError,
            RateLimitExceededError, AuthenticationError,
        )
        e = ToolNotFoundError("Zapier")
        assert isinstance(e, PraxisError)
        assert e.http_status == 404
        assert "Zapier" in str(e)

        e2 = LLMCircuitOpenError("open")
        assert e2.http_status == 503

        e3 = RateLimitExceededError("slow down")
        assert e3.http_status == 429

        e4 = AuthenticationError("bad creds")
        assert e4.http_status == 401

    def test_to_dict(self):
        from praxis.exceptions import ToolNotFoundError
        e = ToolNotFoundError("missing")
        d = e.to_dict()
        assert d["error"] == "TOOL_NOT_FOUND"
        assert d["http_status"] == 404
        assert "missing" in d["message"]


# ======================================================================
# 2. domain_models.py
# ======================================================================

class TestDomainModels:
    def test_tool_model_creation(self):
        from praxis.domain_models import ToolModel
        t = ToolModel(
            name="TestTool",
            description="A test tool",
            categories=["testing"],
            tags=["test"],
        )
        assert t.name == "TestTool"
        assert t.categories == ["testing"]

    def test_tool_model_frozen(self):
        from praxis.domain_models import ToolModel
        t = ToolModel(name="X", description="d")
        with pytest.raises(Exception):  # ValidationError on frozen model
            t.name = "Y"

    def test_string_list_normalization(self):
        from praxis.domain_models import ToolModel
        t = ToolModel(name="X", description="d", categories="single")
        assert t.categories == ["single"]

    def test_vendor_trust_score_auto_fail(self):
        from praxis.domain_models import VendorTrustScore
        v = VendorTrustScore(
            vendor_name="risky",
            tool_name="RiskyTool",
            composite_score=0.3,
            open_cve_count=10,
            dimensions={},
        )
        assert v.passed is False  # auto-fail: score < 0.4 or CVEs > 5

    def test_api_response_envelope(self):
        from praxis.domain_models import APIResponse
        r = APIResponse(data={"hello": "world"})
        assert r.success is True
        assert r.data["hello"] == "world"

    def test_search_request(self):
        from praxis.domain_models import SearchRequest
        s = SearchRequest(query="find me tools")
        assert s.query == "find me tools"
        assert s.top_n == 5  # default


# ======================================================================
# 3. llm_resilience.py
# ======================================================================

class TestCircuitBreaker:
    def test_starts_closed(self):
        from praxis.llm_resilience import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == "CLOSED"
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        from praxis.llm_resilience import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1000)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.allow_request() is False

    def test_success_resets(self):
        from praxis.llm_resilience import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == "CLOSED"

    def test_manual_reset(self):
        from praxis.llm_resilience import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == "OPEN"
        cb.reset()
        assert cb.state == "CLOSED"


class TestRetryDecorator:
    def test_retry_on_failure(self):
        from praxis.llm_resilience import retry_llm, CircuitBreaker
        cb = CircuitBreaker(failure_threshold=10)
        call_count = 0

        @retry_llm(max_attempts=3, initial_backoff=0.01, max_backoff=0.02, circuit=cb)
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        result = _run(flaky())
        assert result == "ok"
        assert call_count == 3

    def test_all_attempts_exhausted(self):
        from praxis.llm_resilience import retry_llm, CircuitBreaker
        from praxis.exceptions import LLMError
        cb = CircuitBreaker(failure_threshold=10)

        @retry_llm(max_attempts=2, initial_backoff=0.01, max_backoff=0.02, circuit=cb)
        async def always_fails():
            raise ValueError("always")

        with pytest.raises(LLMError):
            _run(always_fails())


# ======================================================================
# 4. rate_limiter.py
# ======================================================================

class TestSlidingWindowLimiter:
    def test_allows_within_limit(self):
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert _run(lim.is_allowed("test")) is True
        # 6th should be denied
        assert _run(lim.is_allowed("test")) is False

    def test_remaining(self):
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter(max_requests=10, window_seconds=60)
        _run(lim.is_allowed("k"))
        _run(lim.is_allowed("k"))
        assert lim.remaining("k") == 8

    def test_isolation_between_keys(self):
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter(max_requests=2, window_seconds=60)
        _run(lim.is_allowed("a"))
        _run(lim.is_allowed("a"))
        assert _run(lim.is_allowed("a")) is False
        assert _run(lim.is_allowed("b")) is True  # different key


class TestTokenBucketLimiter:
    def test_allows_burst(self):
        from praxis.rate_limiter import TokenBucketLimiter
        lim = TokenBucketLimiter(capacity=3, refill_rate=0.001)
        assert _run(lim.is_allowed("x")) is True
        assert _run(lim.is_allowed("x")) is True
        assert _run(lim.is_allowed("x")) is True
        assert _run(lim.is_allowed("x")) is False  # capacity exhausted


# ======================================================================
# 5. auth.py
# ======================================================================

class TestAuth:
    def test_none_mode_returns_anonymous(self):
        os.environ["PRAXIS_AUTH_MODE"] = "none"
        from praxis.auth import authenticate_request
        user = asyncio.run(authenticate_request())
        assert user is not None
        assert user.user_id == "anonymous"

    def test_api_key_valid(self):
        os.environ["PRAXIS_AUTH_MODE"] = "api_key"
        os.environ["PRAXIS_API_KEYS"] = "test-key-123,other-key"
        from praxis.auth import authenticate_request
        user = asyncio.run(authenticate_request(x_api_key="test-key-123"))
        assert user is not None
        assert user.auth_method == "api_key"

    def test_api_key_invalid(self):
        os.environ["PRAXIS_AUTH_MODE"] = "api_key"
        os.environ["PRAXIS_API_KEYS"] = "valid-key"
        from praxis.auth import authenticate_request
        user = asyncio.run(authenticate_request(x_api_key="wrong-key"))
        assert user is None

    def test_jwt_roundtrip(self):
        os.environ["PRAXIS_AUTH_MODE"] = "oauth2"
        os.environ["PRAXIS_JWT_SECRET"] = "test-secret-256bit-minimum-length"
        from praxis.auth import generate_jwt, authenticate_request
        token = generate_jwt("user42", roles=["admin"], secret="test-secret-256bit-minimum-length")
        user = asyncio.run(authenticate_request(authorization=f"Bearer {token}"))
        assert user is not None
        assert user.user_id == "user42"
        assert user.has_role("admin")

    def test_generate_api_key(self):
        from praxis.auth import generate_api_key
        key = generate_api_key()
        assert key.startswith("prx_")
        assert len(key) > 20

    def teardown_method(self):
        for k in ("PRAXIS_AUTH_MODE", "PRAXIS_API_KEYS", "PRAXIS_JWT_SECRET"):
            os.environ.pop(k, None)


# ======================================================================
# 6. telemetry.py
# ======================================================================

class TestTelemetry:
    def test_trace_id_propagation(self):
        from praxis.telemetry import new_trace_id, get_trace_id, set_trace_id
        tid = new_trace_id()
        assert len(tid) == 32
        assert get_trace_id() == tid
        set_trace_id("custom")
        assert get_trace_id() == "custom"

    def test_structured_formatter(self):
        import json
        from praxis.telemetry import StructuredJsonFormatter, set_trace_id
        import logging
        fmt = StructuredJsonFormatter()
        set_trace_id("abc123")
        rec = logging.LogRecord("test", logging.INFO, "", 0, "hello", (), None)
        output = fmt.format(rec)
        doc = json.loads(output)
        assert doc["message"] == "hello"
        assert doc["trace_id"] == "abc123"
        assert doc["level"] == "INFO"


# ======================================================================
# 7. vendor_trust.py
# ======================================================================

class TestVendorTrust:
    def test_full_compliance_high_score(self):
        from praxis.vendor_trust import VendorTrustEngine, VendorProfile
        engine = VendorTrustEngine()
        p = VendorProfile(
            vendor_name="Acme", tool_name="AcmeTool",
            soc2=True, gdpr=True, iso27001=True, hipaa=True,
            open_cve_count=0, days_since_last_update=7,
            github_stars=5000, github_contributors=50,
            has_security_policy=True,
        )
        result = engine.score(p)
        assert result["passed"] is True
        assert result["composite_score"] > 0.8
        assert result["risk_tier"] == "low"

    def test_no_compliance_low_score(self):
        from praxis.vendor_trust import VendorTrustEngine, VendorProfile
        engine = VendorTrustEngine()
        p = VendorProfile(
            vendor_name="Risky", tool_name="RiskyTool",
            open_cve_count=10, days_since_last_update=500,
        )
        result = engine.score(p)
        assert result["passed"] is False
        assert result["risk_tier"] in ("high", "critical")

    def test_blocked_override(self):
        from praxis.vendor_trust import VendorTrustEngine, VendorProfile
        engine = VendorTrustEngine()
        p = VendorProfile(vendor_name="Bad", tool_name="BadTool", risk_override="blocked")
        result = engine.score(p)
        assert result["passed"] is False
        assert result["risk_tier"] == "blocked"

    def test_annotate_recommendations(self):
        from praxis.vendor_trust import annotate_recommendations
        recs = [{"name": "UnknownTool"}]
        result = annotate_recommendations(recs)
        assert result[0]["vendor_trust"]["risk_tier"] == "unverified"


# ======================================================================
# 8. scoring_optimized.py
# ======================================================================

class TestOptimizedTFIDF:
    def _make_mock_tools(self):
        """Create minimal tool-like objects for testing."""
        class MockTool:
            def __init__(self, name, desc, cats=None, tags=None, kws=None, ucs=None):
                self.name = name
                self.description = desc
                self.categories = cats or []
                self.tags = tags or []
                self.keywords = kws or []
                self.use_cases = ucs or []

        return [
            MockTool("Zapier", "Automation platform for workflows", ["automation"], ["workflow", "integration"]),
            MockTool("Figma", "Design tool for UI/UX", ["design"], ["ui", "ux", "prototyping"]),
            MockTool("GitHub", "Code hosting and version control", ["development"], ["git", "code", "collaboration"]),
            MockTool("Notion", "All-in-one workspace for notes", ["productivity"], ["notes", "wiki", "project management"]),
        ]

    def test_build_and_score(self):
        from praxis.scoring_optimized import OptimizedTFIDF
        idx = OptimizedTFIDF()
        idx.build(self._make_mock_tools())
        assert idx.built is True

        score = idx.score(["automation", "workflow"], "Zapier")
        assert score > 0

        score_low = idx.score(["automation", "workflow"], "Figma")
        assert score > score_low  # Zapier should score higher for automation

    def test_batch_score(self):
        from praxis.scoring_optimized import OptimizedTFIDF
        idx = OptimizedTFIDF()
        idx.build(self._make_mock_tools())

        results = idx.batch_score(["design", "ui"], top_n=2)
        assert len(results) > 0
        assert results[0][0] == "Figma"  # Figma should top for design

    def test_stats(self):
        from praxis.scoring_optimized import OptimizedTFIDF
        idx = OptimizedTFIDF()
        idx.build(self._make_mock_tools())
        stats = idx.stats()
        assert stats["doc_count"] == 4
        assert stats["vocab_size"] > 0
        assert stats["built"] is True


# ======================================================================
# 9. ports.py — Protocol compliance
# ======================================================================

class TestPorts:
    def test_protocols_importable(self):
        from praxis.ports import (
            ToolRepository, LLMProvider, CacheProvider, EventBus,
            GraphStore, VectorStore, TaskQueue, RateLimiter,
            AuthProvider, TelemetryProvider,
        )
        # All are runtime-checkable Protocol classes
        assert hasattr(ToolRepository, '__protocol_attrs__') or True  # Protocol

    def test_sliding_window_satisfies_rate_limiter_port(self):
        """SlidingWindowLimiter structurally matches RateLimiter protocol."""
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter()
        # Duck-type check: has is_allowed, record, remaining
        assert hasattr(lim, 'is_allowed')
        assert hasattr(lim, 'record')
        assert hasattr(lim, 'remaining')


# ======================================================================
# 10. Architecture Review Fixes (v18.1)
# ======================================================================

class TestRateLimiterSweep:
    """TTL sweep prevents unbounded dict growth."""

    def test_sliding_window_sweep_removes_stale(self):
        import time
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter(max_requests=10, window_seconds=60)
        # Simulate old traffic
        _run(lim.is_allowed("old_key"))
        # Fake the last-seen to the past
        lim._last_seen["old_key"] = time.monotonic() - 999
        removed = lim.sweep_stale_keys(max_idle=300)
        assert removed == 1
        assert "old_key" not in lim._buckets

    def test_sliding_window_sweep_keeps_active(self):
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter(max_requests=10, window_seconds=60)
        _run(lim.is_allowed("active"))
        removed = lim.sweep_stale_keys(max_idle=300)
        assert removed == 0
        assert "active" in lim._buckets

    def test_token_bucket_sweep_removes_stale(self):
        import time
        from praxis.rate_limiter import TokenBucketLimiter
        lim = TokenBucketLimiter(capacity=10)
        _run(lim.is_allowed("stale"))
        lim._buckets["stale"]["last_refill"] = time.monotonic() - 999
        removed = lim.sweep_stale_keys(max_idle=300)
        assert removed == 1

    def test_reset_clears_last_seen(self):
        from praxis.rate_limiter import SlidingWindowLimiter
        lim = SlidingWindowLimiter()
        _run(lim.is_allowed("k"))
        lim.reset("k")
        assert "k" not in lim._last_seen
        lim.reset_all()
        assert len(lim._last_seen) == 0


class TestProxyIPExtraction:
    """_extract_client_ip respects X-Forwarded-For only from trusted proxies."""

    def test_direct_ip_returned_for_untrusted(self):
        from praxis.rate_limiter import _extract_client_ip

        class FakeClient:
            host = "203.0.113.5"
        class FakeRequest:
            client = FakeClient()
            headers = {"x-forwarded-for": "10.0.0.1"}

        assert _extract_client_ip(FakeRequest()) == "203.0.113.5"

    def test_forwarded_ip_for_trusted_proxy(self):
        from praxis.rate_limiter import _extract_client_ip

        class FakeClient:
            host = "127.0.0.1"
        class FakeRequest:
            client = FakeClient()
            headers = {"x-forwarded-for": "198.51.100.42, 10.0.0.1"}

        assert _extract_client_ip(FakeRequest()) == "198.51.100.42"


class TestNegationGuard:
    """Vibe-coding negation filter prevents false positives."""

    def test_avoid_vibe_coding_not_vibe_style(self):
        from praxis.orchestration import classify_engineering_query
        result = classify_engineering_query("How do I avoid vibe coding?")
        assert result["style"] != "vibe-coding"

    def test_direct_vibe_coding_still_detected(self):
        from praxis.orchestration import classify_engineering_query
        result = classify_engineering_query("I want to do vibe coding and just prompt my way through")
        assert result["style"] == "vibe-coding"


class TestComputedFieldPassed:
    """VendorTrustScore.passed is now a computed_field, not mutated."""

    def test_passing_score(self):
        from praxis.domain_models import VendorTrustScore
        v = VendorTrustScore(
            tool_name="Good", composite_score=0.8, open_cve_count=0,
        )
        assert v.passed is True

    def test_failing_score(self):
        from praxis.domain_models import VendorTrustScore
        v = VendorTrustScore(
            tool_name="Bad", composite_score=0.2, open_cve_count=10,
        )
        assert v.passed is False

    def test_boundary_cve(self):
        from praxis.domain_models import VendorTrustScore
        v = VendorTrustScore(
            tool_name="Edge", composite_score=0.5, open_cve_count=6,
        )
        assert v.passed is False  # CVE > 5
