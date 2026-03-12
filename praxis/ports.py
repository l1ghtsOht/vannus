# --------------- Praxis Ports — Hexagonal Architecture Contracts ---------------
"""
v18 · Enterprise-Grade Solidification

Abstract interfaces (Ports) that define the contracts between the Praxis
core domain and its external infrastructure.  Adapters implement these
protocols; the domain NEVER imports a concrete adapter directly.

Design principles:
    • Every port uses ``typing.Protocol`` (structural subtyping) so that
      adapters don't need to inherit from anything — they just need to satisfy
      the shape.
    • Ports live in the domain layer — they know nothing about FastAPI,
      SQLAlchemy, Redis, Neo4j, or any specific LLM SDK.
    • Adapters are injected at construction time via FastAPI's Depends() or
      via plain constructor injection in the CLI/test harness.
"""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    runtime_checkable,
)


# -----------------------------------------------------------------------
# Tool Repository Port
# -----------------------------------------------------------------------

@runtime_checkable
class ToolRepository(Protocol):
    """Read/write access to the AI-tool knowledge base."""

    def get_all(self) -> List[Dict[str, Any]]:
        """Return every tool as a dict."""
        ...

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single tool by its canonical name."""
        ...

    def search(self, keywords: Sequence[str], *, top_n: int = 10) -> List[Dict[str, Any]]:
        """Score and rank tools against *keywords*, return top-N."""
        ...

    def upsert(self, tool: Dict[str, Any]) -> None:
        """Insert or update a tool record."""
        ...

    def delete(self, name: str) -> bool:
        """Remove a tool by name; return True if it existed."""
        ...

    def count(self) -> int:
        """Total number of tools in the repository."""
        ...


# -----------------------------------------------------------------------
# LLM Provider Port
# -----------------------------------------------------------------------

@runtime_checkable
class LLMProvider(Protocol):
    """Abstraction over any LLM backend (OpenAI, Anthropic, local, mock)."""

    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a prompt and return the completion text."""
        ...

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Return embedding vectors for a list of texts."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable identifier, e.g. 'openai', 'anthropic', 'local'."""
        ...

    @property
    def model_name(self) -> str:
        """Model identifier, e.g. 'gpt-4o-mini'."""
        ...


# -----------------------------------------------------------------------
# Cache Port
# -----------------------------------------------------------------------

@runtime_checkable
class CacheProvider(Protocol):
    """Key-value cache (Redis, Memcached, or in-memory dict)."""

    async def get(self, key: str) -> Optional[str]:
        ...

    async def set(self, key: str, value: str, *, ttl_seconds: int = 300) -> None:
        ...

    async def delete(self, key: str) -> None:
        ...

    async def exists(self, key: str) -> bool:
        ...


# -----------------------------------------------------------------------
# Event Bus Port
# -----------------------------------------------------------------------

@runtime_checkable
class EventBus(Protocol):
    """Publish/subscribe for domain events (decoupled orchestration)."""

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        ...

    async def subscribe(self, event_type: str, handler: Any) -> None:
        ...


# -----------------------------------------------------------------------
# Graph Store Port
# -----------------------------------------------------------------------

@runtime_checkable
class GraphStore(Protocol):
    """Persistent graph database for tool relationships."""

    def add_node(self, name: str, properties: Dict[str, Any]) -> None:
        ...

    def add_edge(self, source: str, target: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        ...

    def neighbors(self, name: str, rel_type: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    def shortest_path(self, start: str, end: str) -> List[str]:
        ...

    def community(self, name: str) -> List[str]:
        ...

    def stats(self) -> Dict[str, Any]:
        ...


# -----------------------------------------------------------------------
# Vector Store Port
# -----------------------------------------------------------------------

@runtime_checkable
class VectorStore(Protocol):
    """Dense-vector search backend (Chroma, pgvector, FAISS, in-memory)."""

    async def upsert(self, doc_id: str, text: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        ...

    async def search(self, query_embedding: List[float], *, top_k: int = 10) -> List[Dict[str, Any]]:
        """Return ranked results with score and metadata."""
        ...

    async def delete(self, doc_id: str) -> None:
        ...


# -----------------------------------------------------------------------
# Task Queue Port
# -----------------------------------------------------------------------

@runtime_checkable
class TaskQueue(Protocol):
    """Background job dispatch (ARQ, Celery, or in-process fallback)."""

    async def enqueue(self, task_name: str, *args: Any, **kwargs: Any) -> str:
        """Submit a job; return a job_id."""
        ...

    async def status(self, job_id: str) -> Dict[str, Any]:
        """Return {'state': 'queued'|'running'|'complete'|'failed', ...}."""
        ...

    async def result(self, job_id: str) -> Any:
        """Block/wait for and return the job's result."""
        ...


# -----------------------------------------------------------------------
# Rate Limiter Port
# -----------------------------------------------------------------------

@runtime_checkable
class RateLimiter(Protocol):
    """Request-rate enforcement (sliding window, token bucket, etc.)."""

    async def is_allowed(self, key: str) -> bool:
        """Return True if the request should proceed."""
        ...

    async def record(self, key: str) -> None:
        """Record that a request was made."""
        ...

    def remaining(self, key: str) -> int:
        """Return approximate requests remaining in the current window."""
        ...


# -----------------------------------------------------------------------
# Auth Provider Port
# -----------------------------------------------------------------------

@runtime_checkable
class AuthProvider(Protocol):
    """Identity verification and authorization."""

    async def authenticate(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a bearer token; return user claims or None."""
        ...

    async def authorize(self, user: Dict[str, Any], permission: str) -> bool:
        """Check whether *user* holds *permission*."""
        ...


# -----------------------------------------------------------------------
# Telemetry Port
# -----------------------------------------------------------------------

@runtime_checkable
class TelemetryProvider(Protocol):
    """Distributed tracing, metrics, and structured-log emission."""

    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> Any:
        """Begin a trace span (returns a context-manager or span object)."""
        ...

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        ...

    def log_event(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        ...
