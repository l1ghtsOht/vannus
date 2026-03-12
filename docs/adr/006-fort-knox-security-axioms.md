# ADR-006: Fort Knox Security Architecture — 5-Axiom Defence-in-Depth

## Status
**Accepted** — February 2026

## Context

Praxis operates as an autonomous AI orchestration engine processing stochastic,
natural language inputs that act simultaneously as data and executable instructions.
Traditional perimeter defense (WAFs, static input validation) is insufficient
against advanced adversarial vectors: indirect prompt injection, payload inflation,
AST alias-chaining, and hallucination cascades.

The existing Hexagonal Architecture (ADR-001) provides structural isolation but
lacks a formalized, multi-layer security posture that maps defensive components
to specific threat classes with fail-closed guarantees.

## Decision

Adopt a **5-Axiom "Fort Knox" defence-in-depth** model that enforces sequential
security checkpoints across the full request lifecycle:

| Axiom | Name | Component | Threat Class |
|-------|------|-----------|-------------|
| 1 | The Moat | CORS allowlist + Rate Limiting | Session flooding, DDoS |
| 2 | The Sally Port | RASP Middleware | Prompt injection, payload inflation |
| 3 | Identity Gates | JWT AuthN/AuthZ (Zero-Trust) | Privilege escalation, lateral movement |
| 4 | Internal Scanners | AST Taint Propagation | Alias-chaining, logic mutation, RCE |
| 5 | The Vault | Bounded Write Queues + File Locking | Race conditions, memory corruption |

Additionally, 4 **Cognitive Offloading Safeguards** are deployed within the Vault:

1. **Architectural Boundaries** — Validates imports against hexagonal layer rules
2. **Complexity Ceilings** — Enforces CC ≤ 10 and nesting ≤ 5
3. **LLM-to-LLM Verification** — AST mutation + dual-agent consistency check
4. **Boring Code Optimisation** — KERNEL prompt framework for maintainable output

## Consequences

### Positive
- Every request traverses 5 independent security checkpoints
- Architectural topology physically blocks Presentation→Persistence bypass
- RASP operates at runtime with contextual visibility (not static signatures)
- Bounded queues prevent memory exhaustion from write amplification
- Cognitive safeguards prevent AI-generated code from degrading codebase quality

### Negative
- Additional middleware layers add ~2-5ms per-request latency
- RASP requires exemption list for endpoints that legitimately receive code payloads
- File locking can create contention under extreme concurrent write loads

### Risk Mitigation
- RASP mode is configurable (`enforce` / `log` / `off`) via environment variable
- `/safeguards/` prefix exempted from RASP to allow code analysis endpoints
- Write queue maxsize (10,000) is tunable per deployment

## References

- [FORT_KNOX_BLUEPRINT.md](../FORT_KNOX_BLUEPRINT.md) — Full architectural blueprint
- [ADR-001: Hexagonal Architecture](001-hexagonal-architecture.md)
- [ADR-003: Zero-Dep Resilience](003-zero-dep-resilience.md)
- [ADR-004: Sliding Window Rate Limiting](004-sliding-window-rate-limiting.md)
