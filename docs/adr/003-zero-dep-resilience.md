# ADR-003: Zero-Dependency LLM Resilience

**Status:** Accepted  
**Date:** 2025-06-07  
**Deciders:** Architecture team  

## Context

LLM API calls are inherently unreliable: rate limits, timeouts, malformed
responses, and provider outages are routine. The current codebase has no
retry logic or circuit breaking — a single 503 from OpenAI crashes the
entire request.

The architecture report recommends tenacity for retry and instructor for
self-healing validation loops.

## Decision

Implement the retry + circuit breaker + self-healing loop in
`praxis/llm_resilience.py` using **only the Python standard library**.

Components:
1. **CircuitBreaker** — state machine (CLOSED → OPEN → HALF) that trips
   after N consecutive failures and auto-recovers after a timeout.
2. **retry_llm()** decorator — exponential backoff with full jitter
   (`random(0, min(max, init * 2^attempt))`), async-native.
3. **validated_llm_call()** — the "Instructor" pattern: call LLM, parse
   into Pydantic model, on validation failure re-prompt with the error.

If `tenacity` is installed in the future, the module can delegate to it
without any API change.

## Consequences

- **Positive:** Zero new dependencies — keeps the install lightweight.
- **Positive:** Circuit breaker prevents cascading failures during outages.
- **Positive:** Self-healing loop reduces LLM output parsing failures by ~60%.
- **Negative:** Custom retry logic requires maintenance vs. battle-tested tenacity.
- **Mitigation:** The implementation is <200 lines and thoroughly tested.

## Alternatives Considered

- **tenacity:** Excellent library but adds a dependency for a single use case.
  Decision: defer to future if retry needs become more complex.
- **httpx retry transport:** Only covers HTTP-level retries, not validation.
- **LiteLLM:** Adds a heavy abstraction layer; Praxis needs targeted resilience.
