# ────────────────────────────────────────────────────────────────────
# stress.py — High-Concurrency Stress Testing Harness
# ────────────────────────────────────────────────────────────────────
"""
Provides an integrated stress-testing framework for validating the
Praxis API under production-like loads.  Implements:

    1. **Endpoint profiler** — Times every route and identifies p50/p95/p99
       latency percentiles with statistical precision.
    2. **Concurrent load driver** — Thread-pool-based load generator
       that issues parallel requests against the FastAPI test client.
    3. **Async/sync route classifier** — Automatically detects which
       endpoints are ``async def`` vs ``def`` and flags CPU-bound
       handlers that risk event-loop starvation.
    4. **Schemathesis-compatible OpenAPI extractor** — Generates the
       configuration needed to feed into Schemathesis for property-based
       fuzzing against the full API schema.
    5. **Throughput regression detector** — Compares latency baselines
       across runs to catch performance regressions.

Usage::

    from praxis.stress import (
        profile_endpoint, concurrent_load_test,
        classify_routes, StressReport,
    )

    result = concurrent_load_test("/v1/search", method="POST",
                                   payload={"query": "test"}, concurrency=50)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import math
import statistics
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.stress")


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. LATENCY STATISTICS                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class LatencyStats:
    """Statistical summary of response latencies."""
    count: int = 0
    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    median_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    stddev_ms: float = 0.0
    total_ms: float = 0.0
    errors: int = 0
    error_rate: float = 0.0
    throughput_rps: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "mean_ms": round(self.mean_ms, 2),
            "median_ms": round(self.median_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "stddev_ms": round(self.stddev_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "errors": self.errors,
            "error_rate": round(self.error_rate, 4),
            "throughput_rps": round(self.throughput_rps, 2),
        }


def _compute_latency_stats(latencies_ms: List[float], errors: int = 0,
                            elapsed_seconds: float = 0.0) -> LatencyStats:
    """Compute percentile-based latency statistics."""
    if not latencies_ms:
        return LatencyStats(errors=errors)

    sorted_lat = sorted(latencies_ms)
    n = len(sorted_lat)

    def percentile(pct: float) -> float:
        idx = int(math.ceil(pct / 100.0 * n)) - 1
        return sorted_lat[max(idx, 0)]

    stats = LatencyStats(
        count=n,
        min_ms=sorted_lat[0],
        max_ms=sorted_lat[-1],
        mean_ms=statistics.mean(sorted_lat),
        median_ms=statistics.median(sorted_lat),
        p95_ms=percentile(95),
        p99_ms=percentile(99),
        stddev_ms=statistics.stdev(sorted_lat) if n > 1 else 0.0,
        total_ms=sum(sorted_lat),
        errors=errors,
        error_rate=errors / (n + errors) if (n + errors) > 0 else 0.0,
        throughput_rps=n / elapsed_seconds if elapsed_seconds > 0 else 0.0,
    )
    return stats


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. ENDPOINT PROFILER                                            ║
# ╚════════════════════════════════════════════════════════════════════╝

def profile_endpoint(
    func: Callable,
    iterations: int = 100,
    *args,
    **kwargs,
) -> LatencyStats:
    """
    Profile a single function call, measuring latency across
    ``iterations`` invocations.

    This works with both sync functions and FastAPI route handlers.
    """
    latencies: List[float] = []
    errors = 0
    t0_total = time.monotonic()

    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        try:
            result = func(*args, **kwargs)
            # If it's a coroutine, run it
            if asyncio.iscoroutine(result):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # We're inside an async context already
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            pool.submit(asyncio.run, result).result()
                    else:
                        loop.run_until_complete(result)
                except RuntimeError:
                    asyncio.run(result)
        except Exception:
            errors += 1
        elapsed_ns = time.perf_counter_ns() - t0
        latencies.append(elapsed_ns / 1_000_000)

    total_elapsed = time.monotonic() - t0_total
    return _compute_latency_stats(latencies, errors, total_elapsed)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. CONCURRENT LOAD DRIVER                                      ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class LoadTestResult:
    """Results from a concurrent load test."""
    endpoint: str = ""
    concurrency: int = 0
    total_requests: int = 0
    stats: Optional[LatencyStats] = None
    status_codes: Dict[int, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "concurrency": self.concurrency,
            "total_requests": self.total_requests,
            "stats": self.stats.to_dict() if self.stats else None,
            "status_codes": self.status_codes,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
        }


def concurrent_load_test(
    request_func: Callable,
    concurrency: int = 10,
    total_requests: int = 100,
    *args,
    **kwargs,
) -> LoadTestResult:
    """
    Drive concurrent requests against a callable (e.g., test client method).

    Parameters
    ----------
    request_func   : A callable that makes one request. Should return
                     a response-like object with ``.status_code`` or
                     raise on failure.
    concurrency    : Number of parallel workers.
    total_requests : Total number of requests to issue.

    Usage with FastAPI TestClient::

        from fastapi.testclient import TestClient
        client = TestClient(app)
        result = concurrent_load_test(
            lambda: client.post("/v1/search", json={"query": "test"}),
            concurrency=20,
            total_requests=200,
        )
    """
    result = LoadTestResult(
        concurrency=concurrency,
        total_requests=total_requests,
    )
    latencies: List[float] = []
    errors = 0
    status_codes: Dict[int, int] = {}
    lock = threading.Lock()

    t0 = time.monotonic()

    def _worker():
        nonlocal errors
        t_start = time.perf_counter_ns()
        try:
            resp = request_func(*args, **kwargs)
            elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000
            code = getattr(resp, "status_code", 200)
            with lock:
                latencies.append(elapsed_ms)
                status_codes[code] = status_codes.get(code, 0) + 1
        except Exception:
            elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000
            with lock:
                errors += 1
                latencies.append(elapsed_ms)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_worker) for _ in range(total_requests)]
        for f in as_completed(futures):
            f.result()  # propagate exceptions

    elapsed = time.monotonic() - t0
    result.stats = _compute_latency_stats(latencies, errors, elapsed)
    result.status_codes = status_codes
    result.elapsed_seconds = elapsed
    return result


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. ASYNC/SYNC ROUTE CLASSIFIER                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class RouteClassification:
    """Classification of a single API route."""
    path: str
    method: str
    is_async: bool
    handler_name: str
    cpu_bound_risk: str = "low"   # "low" | "medium" | "high"
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "is_async": self.is_async,
            "handler_name": self.handler_name,
            "cpu_bound_risk": self.cpu_bound_risk,
            "recommendation": self.recommendation,
        }


# Known CPU-bound function names that should NOT be async def
_CPU_BOUND_CALLEES = {
    "find_tools", "score_tool", "compose_stack", "compare_tools",
    "interpret", "build_stack", "explain_tool", "hybrid_search",
    "sparse_rank", "dense_rank", "_bm25_score",
}


def classify_routes(app=None) -> List[RouteClassification]:
    """
    Classify all registered routes as async/sync and flag CPU-bound risk.

    If ``app`` is provided, inspects the actual FastAPI app.
    Otherwise, attempts to import the default app.
    """
    if app is None:
        try:
            from .api import create_app
            app = create_app()
        except ImportError:
            try:
                from api import create_app
                app = create_app()
            except ImportError:
                return []

    results = []
    for route in getattr(app, "routes", []):
        if not hasattr(route, "endpoint"):
            continue

        handler = route.endpoint
        methods = getattr(route, "methods", {"GET"})
        path = getattr(route, "path", "")
        is_async = asyncio.iscoroutinefunction(handler)
        handler_name = getattr(handler, "__name__", str(handler))

        # Determine CPU-bound risk by inspecting handler source
        cpu_risk = "low"
        recommendation = ""

        try:
            source = inspect.getsource(handler)
            for callee in _CPU_BOUND_CALLEES:
                if callee in source:
                    if is_async:
                        cpu_risk = "high"
                        recommendation = (
                            f"CRITICAL: async handler calls CPU-bound "
                            f"'{callee}()'. This will block the event loop. "
                            f"Use 'def' instead of 'async def', or wrap in "
                            f"asyncio.to_thread()."
                        )
                    else:
                        cpu_risk = "medium"
                        recommendation = (
                            f"Handler calls '{callee}()' — runs in thread pool "
                            f"(safe). Under high load, may exhaust the default "
                            f"40-thread pool."
                        )
                    break
        except (OSError, TypeError):
            pass

        for method in methods:
            results.append(RouteClassification(
                path=path,
                method=method,
                is_async=is_async,
                handler_name=handler_name,
                cpu_bound_risk=cpu_risk,
                recommendation=recommendation,
            ))

    results.sort(key=lambda r: (r.cpu_bound_risk == "low", r.path))
    return results


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. SCHEMATHESIS INTEGRATION CONFIG                              ║
# ╚════════════════════════════════════════════════════════════════════╝

def schemathesis_config(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Generate configuration for integrating Schemathesis property-based
    fuzzing into CI.

    Returns a config dict that can be written to ``schemathesis.yaml``
    or passed as CLI arguments.
    """
    return {
        "schema_url": f"{base_url}/openapi.json",
        "base_url": base_url,
        "method": "all",
        "checks": [
            "not_a_server_error",          # No 5xx responses
            "status_code_conformance",     # Response codes match schema
            "content_type_conformance",    # Content-Type matches schema
            "response_headers_conformance", # Required headers present
            "response_schema_conformance", # Response body matches schema
        ],
        "max_examples": 100,
        "hypothesis_settings": {
            "max_examples": 100,
            "deadline": 5000,
            "suppress_health_check": ["too_slow"],
        },
        "workers": 4,
        "cli_command": (
            f"schemathesis run {base_url}/openapi.json "
            f"--checks all --workers 4 --max-examples 100"
        ),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. THROUGHPUT REGRESSION DETECTOR                               ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class RegressionResult:
    """Comparison between baseline and current performance."""
    endpoint: str = ""
    baseline_p99_ms: float = 0.0
    current_p99_ms: float = 0.0
    delta_pct: float = 0.0
    regression: bool = False
    threshold_pct: float = 20.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "baseline_p99_ms": round(self.baseline_p99_ms, 2),
            "current_p99_ms": round(self.current_p99_ms, 2),
            "delta_pct": round(self.delta_pct, 1),
            "regression": self.regression,
            "threshold_pct": self.threshold_pct,
        }


def detect_regression(
    baseline: Dict[str, LatencyStats],
    current: Dict[str, LatencyStats],
    threshold_pct: float = 20.0,
) -> List[RegressionResult]:
    """
    Compare current latency stats against a baseline.

    Flags a ``regression`` if the p99 latency increased by more than
    ``threshold_pct`` percent.
    """
    results = []
    for endpoint in current:
        base = baseline.get(endpoint)
        curr = current[endpoint]
        if not base:
            continue

        if base.p99_ms > 0:
            delta = ((curr.p99_ms - base.p99_ms) / base.p99_ms) * 100
        else:
            delta = 0.0

        results.append(RegressionResult(
            endpoint=endpoint,
            baseline_p99_ms=base.p99_ms,
            current_p99_ms=curr.p99_ms,
            delta_pct=delta,
            regression=delta > threshold_pct,
            threshold_pct=threshold_pct,
        ))

    return results


# ╔════════════════════════════════════════════════════════════════════╗
# ║  7. COMPREHENSIVE STRESS REPORT                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class StressReport:
    """Full stress-test report aggregating all dimensions."""
    route_classifications: List[Dict[str, Any]] = field(default_factory=list)
    high_risk_routes: int = 0
    schemathesis_config: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_classifications_count": len(self.route_classifications),
            "high_risk_routes": self.high_risk_routes,
            "schemathesis_config": self.schemathesis_config,
            "recommendations": self.recommendations,
        }


def generate_stress_report(app=None) -> StressReport:
    """
    Generate a comprehensive stress-testing recommendation report.

    Classifies all routes, identifies risks, and provides actionable
    remediation guidance.
    """
    report = StressReport()

    # Route classification
    classifications = classify_routes(app)
    report.route_classifications = [c.to_dict() for c in classifications]
    report.high_risk_routes = sum(1 for c in classifications if c.cpu_bound_risk == "high")

    # Schemathesis config
    report.schemathesis_config = schemathesis_config()

    # Generate recommendations
    async_cpu = [c for c in classifications if c.cpu_bound_risk == "high"]
    sync_cpu = [c for c in classifications if c.cpu_bound_risk == "medium"]

    if async_cpu:
        report.recommendations.append(
            f"CRITICAL: {len(async_cpu)} async routes call CPU-bound functions. "
            f"These will block the ASGI event loop under concurrent load. "
            f"Convert to sync 'def' routes or wrap with asyncio.to_thread()."
        )

    if sync_cpu:
        report.recommendations.append(
            f"WARNING: {len(sync_cpu)} sync routes call CPU-bound functions. "
            f"Under high concurrency (>40 simultaneous requests), these may "
            f"exhaust the Starlette thread pool. Consider increasing "
            f"ANYIO_BACKEND_OPTIONS max_threads or using ProcessPoolExecutor "
            f"for compute-heavy operations."
        )

    if not async_cpu and not sync_cpu:
        report.recommendations.append(
            "All routes have acceptable CPU-bound risk profiles."
        )

    report.recommendations.append(
        "Deploy k6 for brute-force latency baselines (p99 targets), "
        "Locust for multi-step agentic journey simulation, and "
        "Schemathesis for automated OpenAPI schema fuzzing."
    )

    return report
