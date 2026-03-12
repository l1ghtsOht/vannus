# ADR-001: Adopt Hexagonal Architecture (Ports and Adapters)

**Status:** Accepted  
**Date:** 2025-06-07  
**Deciders:** Architecture team  

## Context

Praxis grew from a single-file MVP to 45+ Python modules across 17 versions.
Business logic is tightly coupled to infrastructure: SQLite access is scattered
through `storage.py` and `data.py`, LLM calls are inlined in scoring functions,
and the rate limiter is defined inside `create_app()`.

This coupling makes unit testing slow (every test needs the real DB), adapter
swaps impossible (e.g. Redis instead of in-memory cache), and the blast radius
of any infrastructure change unbounded.

## Decision

Introduce the **Hexagonal Architecture** (Alistair Cockburn, 2005) by defining
`Protocol`-based port contracts in `praxis/ports.py`.

Key ports:
- `ToolRepository` — data access
- `LLMProvider` — any LLM backend
- `CacheProvider` — Redis / in-memory
- `GraphStore` — NetworkX / Neo4j
- `VectorStore` — FAISS / Chroma / pgvector
- `RateLimiter`, `AuthProvider`, `TelemetryProvider`

All ports use `@runtime_checkable` so adapters can be verified with `isinstance()`.

## Consequences

- **Positive:** Business logic becomes infrastructure-agnostic; adapters are
  swappable at startup; unit tests inject in-memory stubs.
- **Positive:** Clear dependency direction — domain never imports infrastructure.
- **Negative:** Initial overhead of defining and wiring port interfaces.
- **Negative:** Requires discipline to keep the boundary clean.

## Alternatives Considered

- **Direct Abstract Base Classes (ABCs):** More rigid; typing.Protocol is more
  Pythonic and supports structural subtyping (duck typing).
- **Dependency Injection framework (e.g. python-inject):** Too heavy for the
  current scale; manual wiring via `create_app()` is sufficient.
