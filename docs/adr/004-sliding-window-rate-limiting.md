# ADR-004: Sliding Window Rate Limiting

**Status:** Accepted  
**Date:** 2025-06-07  
**Deciders:** Architecture team  

## Context

The existing rate limiter (`create_app()` in api.py) uses a basic in-memory
fixed-window approach: append timestamps to a list, prune older than 60s,
reject if count >= limit. This has several issues:

1. **No burst protection** — 60 requests in 1 second are allowed if the
   window just reset.
2. **No tiered limits** — every endpoint gets the same 60 RPM.
3. **No Redis backing** — limits reset on process restart.
4. **No rate-limit headers** — clients have no visibility into remaining quota.

## Decision

Replace with `praxis/rate_limiter.py` implementing:

1. **SlidingWindowLimiter** — sorted-list-of-timestamps algorithm (Redis
   Sorted Set equivalent). Precise, no boundary burst.
2. **TokenBucketLimiter** — smooth sustained throughput alternative.
3. **TieredRateLimiter** — per-tier limits (standard: 120rpm, expensive: 20rpm,
   admin: 10rpm).
4. **FastAPI middleware** — drop-in replacement that injects `X-RateLimit-Remaining`
   and `Retry-After` headers.

The in-memory implementation is the default adapter. A Redis adapter implementing
`ports.RateLimiter` can be swapped in via configuration.

## Consequences

- **Positive:** Eliminates burst vulnerability at window boundaries.
- **Positive:** Tiered limits protect expensive LLM endpoints.
- **Positive:** Rate-limit headers enable client-side backoff.
- **Positive:** Old middleware is preserved as fallback if v18 modules fail to import.
- **Negative:** Sliding window uses O(n) memory per key per window; acceptable
  at current scale (<1K concurrent users).

## Alternatives Considered

- **Redis Lua scripts** (architecture report recommendation): Optimal for
  multi-process deployments but requires Redis infrastructure. Deferred to
  production deployment phase.
- **leaky bucket:** Less intuitive for API consumers; token bucket preferred.
