# --------------- Praxis Domain Exceptions ---------------
"""
v18 · Enterprise-Grade Solidification

Hierarchical exception taxonomy for the Praxis domain layer.
Every exception carries machine-readable ``code`` and optional ``detail``
so that API handlers can map them to appropriate HTTP status codes.
"""

from __future__ import annotations


class PraxisError(Exception):
    """Base exception for all Praxis domain errors."""

    code: str = "PRAXIS_ERROR"
    http_status: int = 500

    def __init__(self, message: str = "", *, detail: dict | None = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        return {"error": self.code, "http_status": self.http_status, "message": self.message, "detail": self.detail}


# ── Validation ────────────────────────────────────────────────────────

class ValidationError(PraxisError):
    """Input failed schema or business-rule validation."""
    code = "VALIDATION_ERROR"
    http_status = 422


class ProfileValidationError(ValidationError):
    """User-profile data is invalid or incomplete."""
    code = "PROFILE_VALIDATION_ERROR"


class ToolValidationError(ValidationError):
    """Tool metadata fails integrity checks."""
    code = "TOOL_VALIDATION_ERROR"


# ── Not Found ─────────────────────────────────────────────────────────

class NotFoundError(PraxisError):
    """Requested resource does not exist."""
    code = "NOT_FOUND"
    http_status = 404


class ToolNotFoundError(NotFoundError):
    code = "TOOL_NOT_FOUND"


class ProfileNotFoundError(NotFoundError):
    code = "PROFILE_NOT_FOUND"


# ── Authorization ─────────────────────────────────────────────────────

class AuthenticationError(PraxisError):
    """Credentials are missing or invalid."""
    code = "AUTHENTICATION_ERROR"
    http_status = 401


class AuthorizationError(PraxisError):
    """Authenticated user lacks the required permission."""
    code = "AUTHORIZATION_ERROR"
    http_status = 403


# ── Rate Limiting ─────────────────────────────────────────────────────

class RateLimitExceededError(PraxisError):
    """Client has exceeded the allowed request rate."""
    code = "RATE_LIMIT_EXCEEDED"
    http_status = 429


# ── LLM Errors ────────────────────────────────────────────────────────

class LLMError(PraxisError):
    """Base class for LLM-related failures."""
    code = "LLM_ERROR"
    http_status = 502


class LLMTimeoutError(LLMError):
    """LLM provider did not respond within the deadline."""
    code = "LLM_TIMEOUT"
    http_status = 504


class LLMRateLimitError(LLMError):
    """LLM provider returned HTTP 429."""
    code = "LLM_RATE_LIMIT"
    http_status = 429


class LLMValidationError(LLMError):
    """LLM output failed Pydantic schema validation."""
    code = "LLM_VALIDATION_ERROR"
    http_status = 502


class LLMCircuitOpenError(LLMError):
    """Circuit breaker is open — LLM calls temporarily disabled."""
    code = "LLM_CIRCUIT_OPEN"
    http_status = 503


# ── Infrastructure ────────────────────────────────────────────────────

class InfrastructureError(PraxisError):
    """Generic infrastructure failure (DB, cache, network)."""
    code = "INFRASTRUCTURE_ERROR"
    http_status = 503


class CacheError(InfrastructureError):
    code = "CACHE_ERROR"


class DatabaseError(InfrastructureError):
    code = "DATABASE_ERROR"


class GraphDatabaseError(InfrastructureError):
    code = "GRAPH_DATABASE_ERROR"


# ── Vendor Trust ──────────────────────────────────────────────────────

class VendorTrustError(PraxisError):
    """A recommended tool failed the vendor maturity audit."""
    code = "VENDOR_TRUST_FAILURE"
    http_status = 422


# ── Configuration ─────────────────────────────────────────────────────

class ConfigurationError(PraxisError):
    """System mis-configuration detected at startup."""
    code = "CONFIGURATION_ERROR"
    http_status = 500
