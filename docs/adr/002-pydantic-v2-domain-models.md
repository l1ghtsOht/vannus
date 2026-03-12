# ADR-002: Pydantic v2 for Domain Models

**Status:** Accepted  
**Date:** 2025-06-07  
**Deciders:** Architecture team  

## Context

The existing `Tool` class (`tools.py`) is a plain Python class with manual
`to_dict()` / `from_dict()` methods. Validation is ad-hoc: numeric ranges
are unchecked, string lists silently accept non-list inputs, and URL fields
have no format validation.

LLM outputs are parsed via `json.loads()` with no schema enforcement,
leading to silent data corruption when the model returns malformed JSON.

## Decision

Define all domain objects as **Pydantic v2 BaseModel** classes in
`praxis/domain_models.py` with:

- `model_config = ConfigDict(frozen=True)` for immutable value objects
- `field_validator` for string list normalization and URL validation
- `model_validator` for cross-field constraints (e.g. VendorTrustScore auto-fail)
- Constrained types via `Field(ge=0, le=100)` for scores
- `extra = "allow"` only on `IntentModel` (LLM output is unpredictable)

## Consequences

- **Positive:** Runtime validation at the boundary catches bad data immediately.
- **Positive:** `model_json_schema()` auto-generates OpenAPI docs.
- **Positive:** Frozen models prevent accidental mutation in scoring pipelines.
- **Negative:** Pydantic v2 is already a FastAPI dependency, so no new dep.
- **Negative:** Migration of existing Tool class is incremental (both coexist).

## Alternatives Considered

- **dataclasses + manual validation:** Lighter but error-prone, no JSON schema.
- **attrs:** Excellent but adds a new dependency; Pydantic already ships with FastAPI.
- **msgspec:** Faster serialization but less ecosystem integration.
