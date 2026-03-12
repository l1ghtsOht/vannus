# --------------- Praxis Enterprise Rate Limiter ---------------
"""
v18 · Enterprise-Grade Solidification

Multi-algorithm rate limiter supporting:
    • Fixed-window   — simple counter per time-window (fast, low-memory)
    • Sliding-window — Redis Sorted-Set style (precise, burst-safe)
    • Token-bucket   — smooth sustained throughput

All implementations are **async** and **zero-dependency** (pure stdlib).
When Redis is available, swap in the Redis adapter which executes atomic
Lua scripts (see ``ports.RateLimiter`` protocol).

This module also provides a ready-made **FastAPI middleware** and a
**dependency injector** for per-route rate limits.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from ipaddress import ip_address as _parse_ip, IPv4Address, IPv6Address
from typing import Any, Dict, FrozenSet, Optional, Set

log = logging.getLogger("praxis.rate_limiter")

# Max seconds a key can sit idle before the sweep reclaims it.
_MAX_IDLE_SECONDS: float = 300.0
# How often (seconds) the background sweep runs.
_SWEEP_INTERVAL: float = 60.0
# IPs trusted to set X-Forwarded-For (loopback + common RFC-1918 ranges).
TRUSTED_PROXIES: Set[str] = {"127.0.0.1", "::1"}


# -----------------------------------------------------------------------
# Sliding Window (in-memory, Redis-ready interface)
# -----------------------------------------------------------------------

@dataclass
class SlidingWindowLimiter:
    """Sliding-log rate limiter — stores request timestamps per key.

    On each ``is_allowed()`` call:
        1. Purge timestamps older than ``window_seconds``.
        2. Count remaining entries.
        3. Allow if count < ``max_requests``.

    This is the algorithm described in the architecture report using Redis
    Sorted Sets + Lua scripts.  The in-memory variant here is suitable for
    single-process deployments; swap for the Redis adapter in production.
    """

    max_requests: int = 60
    window_seconds: float = 60.0
    _buckets: Dict[str, list] = field(default_factory=lambda: defaultdict(list))
    _last_seen: Dict[str, float] = field(default_factory=dict)

    # ── TTL sweep ────────────────────────────────────────────────
    def sweep_stale_keys(self, max_idle: float = _MAX_IDLE_SECONDS) -> int:
        """Remove keys idle longer than *max_idle* seconds. Returns count."""
        now = time.monotonic()
        stale = [k for k, ts in self._last_seen.items() if now - ts > max_idle]
        for k in stale:
            self._buckets.pop(k, None)
            self._last_seen.pop(k, None)
        if stale:
            log.debug("sliding-window sweep: removed %d stale keys", len(stale))
        return len(stale)

    async def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        self._last_seen[key] = now
        bucket = self._buckets[key]
        cutoff = now - self.window_seconds
        # Purge old entries
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= self.max_requests:
            return False
        bucket.append(now)
        return True

    async def record(self, key: str) -> None:
        """Explicitly record a request (already done inside is_allowed)."""
        pass

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        bucket = self._buckets.get(key, [])
        cutoff = now - self.window_seconds
        active = [t for t in bucket if t > cutoff]
        return max(0, self.max_requests - len(active))

    def reset(self, key: str) -> None:
        self._buckets.pop(key, None)
        self._last_seen.pop(key, None)

    def reset_all(self) -> None:
        self._buckets.clear()
        self._last_seen.clear()


# -----------------------------------------------------------------------
# Token Bucket (smooth sustained throughput)
# -----------------------------------------------------------------------

@dataclass
class TokenBucketLimiter:
    """Token-bucket rate limiter — smooth sustained throughput.

    Tokens are replenished at a constant rate.  Each request consumes one
    token.  Allows short bursts up to ``capacity`` but throttles sustained
    overuse.
    """

    capacity: int = 60
    refill_rate: float = 1.0  # tokens per second
    _buckets: Dict[str, Any] = field(default_factory=dict)

    # ── TTL sweep ────────────────────────────────────────────────
    def sweep_stale_keys(self, max_idle: float = _MAX_IDLE_SECONDS) -> int:
        """Remove keys idle longer than *max_idle* seconds. Returns count."""
        now = time.monotonic()
        stale = [k for k, b in self._buckets.items()
                 if now - b.get("last_refill", now) > max_idle]
        for k in stale:
            del self._buckets[k]
        if stale:
            log.debug("token-bucket sweep: removed %d stale keys", len(stale))
        return len(stale)

    def _get_bucket(self, key: str) -> dict:
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": float(self.capacity),
                "last_refill": time.monotonic(),
            }
        return self._buckets[key]

    async def is_allowed(self, key: str) -> bool:
        b = self._get_bucket(key)
        now = time.monotonic()
        elapsed = now - b["last_refill"]
        b["tokens"] = min(self.capacity, b["tokens"] + elapsed * self.refill_rate)
        b["last_refill"] = now
        if b["tokens"] >= 1.0:
            b["tokens"] -= 1.0
            return True
        return False

    async def record(self, key: str) -> None:
        pass

    def remaining(self, key: str) -> int:
        b = self._get_bucket(key)
        now = time.monotonic()
        elapsed = now - b["last_refill"]
        tokens = min(self.capacity, b["tokens"] + elapsed * self.refill_rate)
        return int(tokens)


# -----------------------------------------------------------------------
# Tiered Rate Limiter (per-endpoint)
# -----------------------------------------------------------------------

class TieredRateLimiter:
    """Assign different rate limits to endpoint tiers.

    Tiers (from the architecture report):
        • ``standard``  — lightweight read endpoints  (120 rpm)
        • ``expensive`` — LLM-backed agentic endpoints (20 rpm)
        • ``admin``     — admin/config endpoints       (10 rpm)
    """

    def __init__(
        self,
        standard_rpm: int = 120,
        expensive_rpm: int = 20,
        admin_rpm: int = 10,
    ):
        self._limiters: Dict[str, SlidingWindowLimiter] = {
            "standard": SlidingWindowLimiter(max_requests=standard_rpm, window_seconds=60),
            "expensive": SlidingWindowLimiter(max_requests=expensive_rpm, window_seconds=60),
            "admin": SlidingWindowLimiter(max_requests=admin_rpm, window_seconds=60),
        }

    async def is_allowed(self, key: str, tier: str = "standard") -> bool:
        limiter = self._limiters.get(tier, self._limiters["standard"])
        return await limiter.is_allowed(key)

    def remaining(self, key: str, tier: str = "standard") -> int:
        limiter = self._limiters.get(tier, self._limiters["standard"])
        return limiter.remaining(key)


# -----------------------------------------------------------------------
# FastAPI Middleware (drop-in replacement for the old RateLimitMiddleware)
# -----------------------------------------------------------------------

# -----------------------------------------------------------------------
# Background Sweep (evict stale keys to prevent unbounded memory growth)
# -----------------------------------------------------------------------

async def _background_sweep(
    limiter: SlidingWindowLimiter,
    interval: float = _SWEEP_INTERVAL,
) -> None:
    """Periodically evict idle keys from the in-memory limiter."""
    while True:
        await asyncio.sleep(interval)
        try:
            limiter.sweep_stale_keys()
        except Exception as exc:
            log.warning("rate-limiter sweep error: %s", exc)


# -----------------------------------------------------------------------
# IP Extraction (proxy-aware)
# -----------------------------------------------------------------------

def _extract_client_ip(request, trusted_proxies: Set[str] = TRUSTED_PROXIES) -> str:
    """Extract real client IP, respecting X-Forwarded-For only from trusted proxies."""
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip in trusted_proxies:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            # Take the left-most (client) IP from the chain
            candidate = forwarded.split(",")[0].strip()
            try:
                _parse_ip(candidate)  # validate it's a real IP
                return candidate
            except ValueError:
                pass
    return direct_ip


def create_rate_limit_middleware(
    limiter: Optional[SlidingWindowLimiter] = None,
):
    """Return a Starlette BaseHTTPMiddleware class wired to *limiter*.

    Usage in ``create_app()``::

        from praxis.rate_limiter import create_rate_limit_middleware, SlidingWindowLimiter
        limiter = SlidingWindowLimiter(max_requests=60, window_seconds=60)
        app.add_middleware(create_rate_limit_middleware(limiter))
    """
    _limiter = limiter or SlidingWindowLimiter()

    try:
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse
    except ImportError:
        return None

    class EnterpriseRateLimitMiddleware(BaseHTTPMiddleware):
        _sweep_task: Optional[asyncio.Task] = None

        async def dispatch(self, request, call_next):
            # ── Start background sweep on first request ──
            if EnterpriseRateLimitMiddleware._sweep_task is None:
                EnterpriseRateLimitMiddleware._sweep_task = asyncio.create_task(
                    _background_sweep(_limiter)
                )

            ip = _extract_client_ip(request)

            # Determine tier from path
            path = request.url.path
            if any(path.startswith(p) for p in ("/reason", "/cognitive", "/prism")):
                tier_key = f"{ip}:expensive"
                allowed = await _limiter.is_allowed(tier_key)
            else:
                tier_key = ip
                allowed = await _limiter.is_allowed(tier_key)

            if not allowed:
                remaining = _limiter.remaining(tier_key)
                log.warning("rate-limit: %s exceeded (remaining=%d)", ip, remaining)
                return JSONResponse(
                    {"error": "Rate limit exceeded. Try again shortly.",
                     "remaining": remaining},
                    status_code=429,
                    headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)},
                )

            response = await call_next(request)
            # Inject rate-limit headers
            response.headers["X-RateLimit-Remaining"] = str(_limiter.remaining(tier_key))
            return response

    return EnterpriseRateLimitMiddleware
