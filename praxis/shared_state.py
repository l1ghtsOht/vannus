# --------------- Shared State — Hybrid CoALA + Relay Memory ---------------
"""
v20 · Multi-Model Ecosystem — Shared Latent State

Provides a unified shared state layer for multi-model collaboration.
Two layers:

    Layer 1: Persistent Memory (CoALA)
        All models read/write to shared Working/Episodic/Semantic/Procedural
        memory.  Writes are tagged with source_model and trust_at_write.

    Layer 2: Message Relay
        Model A's output becomes Model B's context.  Relevance gating
        prunes irrelevant prior outputs before injecting into context.

Design Choices
──────────────
    • Trust-weighted reads — higher-trust model outputs get priority
      when context window space is limited.
    • Structured intermediate representation — all model outputs
      normalised to JSON with content, reasoning_trace, confidence.
    • Relevance gate — TF-IDF similarity filters what goes into
      the next model's context window.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.shared_state")

try:
    from .coala_architecture import (
        MemoryType, MemoryEntry, MemoryModule, CoALAMemorySystem,
    )
    _COALA = True
except ImportError:
    try:
        from coala_architecture import (
            MemoryType, MemoryEntry, MemoryModule, CoALAMemorySystem,
        )
        _COALA = True
    except ImportError:
        _COALA = False

try:
    from .model_registry import ModelSpec, get_registry
except ImportError:
    from model_registry import ModelSpec, get_registry


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ModelOutput:
    """Structured intermediate representation of a model's output."""
    model_id: str
    content: str
    reasoning_trace: str = ""
    confidence: float = 0.8
    trust_at_write: float = 75.0
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "content": self.content[:300],
            "confidence": round(self.confidence, 3),
            "trust_at_write": round(self.trust_at_write, 2),
            "timestamp": self.timestamp,
            "token_count": self.token_count,
        }


@dataclass
class ContextWindow:
    """A curated context window for injection into a model."""
    target_model: str
    entries: List[ModelOutput]
    total_tokens: int = 0
    relevance_scores: List[float] = field(default_factory=list)

    def to_text(self, max_tokens: int = 4000) -> str:
        """Serialize context entries as text for injection."""
        parts: List[str] = []
        remaining = max_tokens
        for entry in self.entries:
            # Rough estimate: 1 token ≈ 4 chars
            est_tokens = len(entry.content) // 4
            if est_tokens > remaining:
                break
            parts.append(
                f"[{entry.model_id} | trust={entry.trust_at_write:.0f} | "
                f"conf={entry.confidence:.2f}]\n{entry.content}"
            )
            remaining -= est_tokens
        return "\n\n---\n\n".join(parts)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RELEVANCE GATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _compute_relevance(query: str, content: str) -> float:
    """Simple TF-IDF-like relevance score between query and content."""
    if not query or not content:
        return 0.0
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    if not query_words:
        return 0.0
    overlap = query_words & content_words
    # Jaccard-ish with length normalisation
    return len(overlap) / max(len(query_words), 1)


def gate_context(
    target_query: str,
    available_outputs: List[ModelOutput],
    max_entries: int = 5,
    min_relevance: float = 0.1,
) -> ContextWindow:
    """
    Relevance gate: select the most relevant prior model outputs
    for injection into the target model's context.

    Uses trust-weighted relevance: score = relevance × trust_factor.
    """
    scored: List[Tuple[float, ModelOutput]] = []
    for output in available_outputs:
        relevance = _compute_relevance(target_query, output.content)
        if relevance < min_relevance:
            continue
        # Trust weighting: normalise trust to 0.5-1.5 multiplier
        trust_factor = 0.5 + (output.trust_at_write / 100.0)
        weighted_score = relevance * trust_factor
        scored.append((weighted_score, output))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = scored[:max_entries]

    entries = [output for _, output in selected]
    relevance_scores = [score for score, _ in selected]
    total_tokens = sum(e.token_count for e in entries)

    return ContextWindow(
        target_model="",
        entries=entries,
        total_tokens=total_tokens,
        relevance_scores=relevance_scores,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SHARED STATE MANAGER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SharedStateManager:
    """
    Manages shared latent state for a collaboration session.

    Layer 1: CoALA memory (persistent, decayable)
    Layer 2: Output log (sequential relay)

    All writes are tagged with source model and trust score at time of write.
    """

    def __init__(self, session_id: str = ""):
        self._lock = threading.RLock()
        self.session_id = session_id

        # Layer 1: CoALA memory (if available)
        self._memory: Optional[Any] = None
        if _COALA:
            self._memory = CoALAMemorySystem()

        # Layer 2: Sequential output log
        self._outputs: List[ModelOutput] = []

        # Key-value store for structured artifacts
        self._artifacts: Dict[str, Dict[str, Any]] = {}

    # ── Layer 1: CoALA Memory ──

    def store_memory(
        self,
        content: str,
        model_id: str,
        memory_type: str = "working",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Store content in CoALA memory, tagged with source model."""
        if not self._memory:
            return None

        # Look up model trust
        registry = get_registry()
        spec = registry.get(model_id)
        trust = spec.trust_score if spec else 50.0

        enriched_metadata = {
            **(metadata or {}),
            "source_model": model_id,
            "trust_at_write": trust,
            "session_id": self.session_id,
        }

        with self._lock:
            try:
                mem_type = MemoryType(memory_type)
            except ValueError:
                mem_type = MemoryType.WORKING
            entry = self._memory.store(mem_type, content, enriched_metadata)
            return entry.entry_id if entry else None

    def retrieve_memory(
        self,
        query: str,
        memory_type: str = "working",
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve from CoALA memory."""
        if not self._memory:
            return []
        with self._lock:
            try:
                mem_type = MemoryType(memory_type)
            except ValueError:
                mem_type = MemoryType.WORKING
            entries = self._memory.retrieve(mem_type, query, top_k)
            return [e.to_dict() for e in entries]

    def cross_retrieve(self, query: str, top_k: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve across all memory types."""
        if not self._memory:
            return {}
        with self._lock:
            results = self._memory.cross_retrieve(query, top_k)
            return {
                mem_type: [e.to_dict() for e in entries]
                for mem_type, entries in results.items()
            }

    def decay_cycle(self) -> Dict[str, int]:
        """Run decay across all memory modules."""
        if not self._memory:
            return {}
        with self._lock:
            return self._memory.global_decay()

    # ── Layer 2: Output Log (Relay) ──

    def record_output(
        self,
        model_id: str,
        content: str,
        reasoning_trace: str = "",
        confidence: float = 0.8,
        token_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelOutput:
        """Record a model's output for relay to subsequent models."""
        registry = get_registry()
        spec = registry.get(model_id)
        trust = spec.trust_score if spec else 50.0

        output = ModelOutput(
            model_id=model_id,
            content=content,
            reasoning_trace=reasoning_trace,
            confidence=confidence,
            trust_at_write=trust,
            token_count=token_count or (len(content) // 4),
            metadata=metadata or {},
        )
        with self._lock:
            self._outputs.append(output)
            # Also store in CoALA episodic memory
            self.store_memory(
                content=content[:500],
                model_id=model_id,
                memory_type="episodic",
                metadata={"type": "model_output", "confidence": confidence},
            )
        return output

    def get_context_for_model(
        self,
        target_query: str,
        target_model: str = "",
        max_entries: int = 5,
        max_tokens: int = 4000,
    ) -> ContextWindow:
        """
        Build a relevance-gated context window for the target model.
        Filters and ranks prior outputs by relevance × trust.
        """
        with self._lock:
            outputs = list(self._outputs)

        # Exclude target model's own outputs to avoid echo
        available = [o for o in outputs if o.model_id != target_model]

        context = gate_context(
            target_query=target_query,
            available_outputs=available,
            max_entries=max_entries,
        )
        context.target_model = target_model
        return context

    def get_all_outputs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [o.to_dict() for o in self._outputs[-limit:]]

    # ── Key-Value Artifacts ──

    def set_artifact(self, key: str, value: Any, source_model: str = "") -> None:
        """Store a named artifact (code file, plan, etc.)."""
        with self._lock:
            self._artifacts[key] = {
                "value": value,
                "source_model": source_model,
                "timestamp": time.time(),
            }

    def get_artifact(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._artifacts.get(key)
            return entry["value"] if entry else None

    def list_artifacts(self) -> List[str]:
        with self._lock:
            return list(self._artifacts.keys())

    # ── Status ──

    def status(self) -> Dict[str, Any]:
        with self._lock:
            memory_status = {}
            if self._memory:
                for mem_type in MemoryType:
                    module = self._memory._modules.get(mem_type)
                    if module:
                        memory_status[mem_type.value] = module.status()
            return {
                "session_id": self.session_id,
                "output_count": len(self._outputs),
                "artifact_count": len(self._artifacts),
                "memory_available": self._memory is not None,
                "memory_modules": memory_status,
                "models_contributed": list(set(o.model_id for o in self._outputs)),
            }


# ── Singleton ──────────────────────────────────────────────────────
_shared_state: Optional[SharedStateManager] = None
_shared_state_lock = threading.Lock()


def get_shared_state_manager(session_id: str = "default") -> SharedStateManager:
    """Return the global SharedStateManager singleton."""
    global _shared_state
    with _shared_state_lock:
        if _shared_state is None:
            _shared_state = SharedStateManager(session_id=session_id)
        return _shared_state
