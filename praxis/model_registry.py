# --------------- Model Registry — Multi-Model Catalogue ---------------
"""
v20 · Multi-Model Ecosystem — Foundation Layer

Unified registry of LLM models with elimination-compatible metadata.
Each model is described by a ``ModelSpec`` — capabilities, cost,
trust score, privacy level, and dynamic tier assignment.

The registry feeds directly into ``model_router.py`` which applies
Praxis's elimination pipeline to select optimal models per query.

Architecture
────────────
    ModelSpec          — immutable descriptor for a single model
    ModelTier          — dynamic trust tier (1 = high-trust … 3 = sandbox)
    PrivacyLevel       — data residency classification
    ModelCapability     — capability tags for matching
    ModelRegistry      — singleton catalogue with query/filter

Design Choices
──────────────
    • Trust scores start at a default and **decay** via model_trust_decay.py
    • Tiers are dynamic — models earn/lose standing based on measured signals
    • Privacy levels enforce data residency rules (local > us_cloud > foreign)
    • Cost fields enable budget-aware elimination in model_router.py
    • Zero external dependencies — pure stdlib
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger("praxis.model_registry")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ModelTier(int, Enum):
    """Dynamic trust tier. Lower = higher trust."""
    TIER_1 = 1   # High-trust, production-grade
    TIER_2 = 2   # Research / secondary
    TIER_3 = 3   # Sandbox / probationary


class PrivacyLevel(str, Enum):
    """Data residency classification."""
    LOCAL = "local"            # Runs on-device or on-prem (Ollama, vLLM)
    US_CLOUD = "us_cloud"      # US-hosted cloud API
    FOREIGN_CLOUD = "foreign"  # Non-US or unknown jurisdiction


class ModelCapability(str, Enum):
    """Capability tags for model matching."""
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    VISION = "vision"
    LONG_CONTEXT = "long_context"
    FUNCTION_CALLING = "function_calling"
    MATH = "math"
    MULTILINGUAL = "multilingual"
    FAST = "fast"
    CHEAP = "cheap"


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    XAI = "xai"
    META = "meta"           # Llama (via Ollama, Together, etc.)
    DEEPSEEK = "deepseek"
    LOCAL = "local"         # Any local model (Ollama, vLLM)


class LatencyClass(str, Enum):
    FAST = "fast"        # < 2s TTFT
    MEDIUM = "medium"    # 2-5s TTFT
    SLOW = "slow"        # > 5s TTFT


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODEL SPEC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ModelSpec:
    """Immutable descriptor for a single LLM model."""
    model_id: str                                         # e.g. "claude-4-sonnet"
    display_name: str                                     # e.g. "Claude 4 Sonnet"
    provider: ModelProvider
    tier: ModelTier = ModelTier.TIER_2                     # dynamic, adjusted by trust decay
    capabilities: Set[ModelCapability] = field(default_factory=set)
    context_window: int = 128_000                         # tokens
    cost_per_1k_input: float = 0.003                      # USD
    cost_per_1k_output: float = 0.015                     # USD
    latency_class: LatencyClass = LatencyClass.MEDIUM
    trust_score: float = 75.0                             # 0-100, decayable
    privacy_level: PrivacyLevel = PrivacyLevel.US_CLOUD
    max_output_tokens: int = 8192
    supports_streaming: bool = True
    supports_tools: bool = False
    last_validated: float = field(default_factory=time.time)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        return hashlib.sha256(
            f"{self.model_id}:{self.provider.value}".encode()
        ).hexdigest()[:12]

    def estimated_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate USD cost for a given token count."""
        return (
            (input_tokens / 1000) * self.cost_per_1k_input
            + (output_tokens / 1000) * self.cost_per_1k_output
        )

    def has_capability(self, cap: ModelCapability) -> bool:
        return cap in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "provider": self.provider.value,
            "tier": self.tier.value,
            "capabilities": sorted(c.value for c in self.capabilities),
            "context_window": self.context_window,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "latency_class": self.latency_class.value,
            "trust_score": round(self.trust_score, 2),
            "privacy_level": self.privacy_level.value,
            "max_output_tokens": self.max_output_tokens,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
            "active": self.active,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TRUST TIER THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Models above this trust score qualify for Tier 1
TIER_1_THRESHOLD = 80.0
# Models below this get demoted to Tier 3
TIER_3_THRESHOLD = 40.0
# Minimum trust score before model is deactivated
DEACTIVATION_THRESHOLD = 15.0


def compute_tier(trust_score: float) -> ModelTier:
    """Derive tier from current trust score."""
    if trust_score >= TIER_1_THRESHOLD:
        return ModelTier.TIER_1
    if trust_score >= TIER_3_THRESHOLD:
        return ModelTier.TIER_2
    return ModelTier.TIER_3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEFAULT MODEL CATALOGUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_DEFAULT_MODELS: List[ModelSpec] = [
    # ── Tier 1: High-trust, production-grade ──
    ModelSpec(
        model_id="claude-4-sonnet",
        display_name="Claude 4 Sonnet",
        provider=ModelProvider.ANTHROPIC,
        tier=ModelTier.TIER_1,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CREATIVE, ModelCapability.FUNCTION_CALLING,
            ModelCapability.LONG_CONTEXT,
        },
        context_window=200_000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        latency_class=LatencyClass.FAST,
        trust_score=92.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=16384,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="claude-4-opus",
        display_name="Claude 4 Opus",
        provider=ModelProvider.ANTHROPIC,
        tier=ModelTier.TIER_1,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CREATIVE, ModelCapability.FUNCTION_CALLING,
            ModelCapability.LONG_CONTEXT, ModelCapability.MATH,
        },
        context_window=200_000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        latency_class=LatencyClass.MEDIUM,
        trust_score=95.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=16384,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="grok-3",
        display_name="Grok 3",
        provider=ModelProvider.XAI,
        tier=ModelTier.TIER_1,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CREATIVE, ModelCapability.FUNCTION_CALLING,
            ModelCapability.MATH,
        },
        context_window=131_072,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        latency_class=LatencyClass.FAST,
        trust_score=85.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=8192,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="o3",
        display_name="OpenAI o3",
        provider=ModelProvider.OPENAI,
        tier=ModelTier.TIER_1,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.MATH, ModelCapability.FUNCTION_CALLING,
        },
        context_window=200_000,
        cost_per_1k_input=0.010,
        cost_per_1k_output=0.040,
        latency_class=LatencyClass.SLOW,
        trust_score=90.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=16384,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="o4-mini",
        display_name="OpenAI o4-mini",
        provider=ModelProvider.OPENAI,
        tier=ModelTier.TIER_1,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.MATH, ModelCapability.FUNCTION_CALLING,
            ModelCapability.FAST, ModelCapability.CHEAP,
        },
        context_window=200_000,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.004,
        latency_class=LatencyClass.FAST,
        trust_score=82.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=16384,
        supports_tools=True,
    ),

    # ── Tier 2: Research / secondary ──
    ModelSpec(
        model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        provider=ModelProvider.GOOGLE,
        tier=ModelTier.TIER_2,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CREATIVE, ModelCapability.VISION,
            ModelCapability.LONG_CONTEXT, ModelCapability.MULTILINGUAL,
        },
        context_window=1_000_000,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        latency_class=LatencyClass.MEDIUM,
        trust_score=72.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=8192,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        provider=ModelProvider.GOOGLE,
        tier=ModelTier.TIER_2,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.FAST, ModelCapability.CHEAP,
            ModelCapability.LONG_CONTEXT, ModelCapability.MULTILINGUAL,
        },
        context_window=1_000_000,
        cost_per_1k_input=0.000075,
        cost_per_1k_output=0.0003,
        latency_class=LatencyClass.FAST,
        trust_score=68.0,
        privacy_level=PrivacyLevel.US_CLOUD,
        max_output_tokens=8192,
        supports_tools=True,
    ),
    ModelSpec(
        model_id="llama-4-maverick",
        display_name="Llama 4 Maverick",
        provider=ModelProvider.META,
        tier=ModelTier.TIER_2,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CREATIVE, ModelCapability.MULTILINGUAL,
        },
        context_window=1_000_000,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0008,
        latency_class=LatencyClass.MEDIUM,
        trust_score=65.0,
        privacy_level=PrivacyLevel.LOCAL,
        max_output_tokens=8192,
        supports_tools=False,
    ),
    ModelSpec(
        model_id="deepseek-v3",
        display_name="DeepSeek V3",
        provider=ModelProvider.DEEPSEEK,
        tier=ModelTier.TIER_2,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.MATH, ModelCapability.CHEAP,
        },
        context_window=128_000,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        latency_class=LatencyClass.MEDIUM,
        trust_score=60.0,
        privacy_level=PrivacyLevel.FOREIGN_CLOUD,
        max_output_tokens=8192,
        supports_tools=True,
    ),

    # ── Local models (self-hosted) ──
    ModelSpec(
        model_id="ollama-llama3",
        display_name="Llama 3 (Ollama local)",
        provider=ModelProvider.LOCAL,
        tier=ModelTier.TIER_2,
        capabilities={
            ModelCapability.CODE, ModelCapability.REASONING,
            ModelCapability.CHEAP,
        },
        context_window=128_000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        latency_class=LatencyClass.MEDIUM,
        trust_score=70.0,
        privacy_level=PrivacyLevel.LOCAL,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_tools=False,
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ModelRegistry:
    """
    Thread-safe singleton catalogue of available LLM models.
    Feeds into model_router.py for elimination-based selection.
    """

    def __init__(self, seed_defaults: bool = True):
        self._lock = threading.RLock()
        self._models: Dict[str, ModelSpec] = {}
        if seed_defaults:
            for m in _DEFAULT_MODELS:
                self._models[m.model_id] = m
            log.info("Model registry seeded with %d default models", len(self._models))

    # ── CRUD ──

    def register(self, spec: ModelSpec) -> None:
        """Register or update a model."""
        with self._lock:
            self._models[spec.model_id] = spec
            log.info("Registered model %s (tier=%d, trust=%.1f)",
                     spec.model_id, spec.tier.value, spec.trust_score)

    def deregister(self, model_id: str) -> bool:
        with self._lock:
            if model_id in self._models:
                del self._models[model_id]
                log.info("Deregistered model %s", model_id)
                return True
            return False

    def get(self, model_id: str) -> Optional[ModelSpec]:
        with self._lock:
            return self._models.get(model_id)

    def list_all(self) -> List[ModelSpec]:
        with self._lock:
            return list(self._models.values())

    # ── Query / Filter ──

    def query(
        self,
        capabilities: Optional[Set[ModelCapability]] = None,
        max_tier: Optional[int] = None,
        max_cost_per_1k_input: Optional[float] = None,
        privacy_level: Optional[PrivacyLevel] = None,
        provider: Optional[ModelProvider] = None,
        min_trust: Optional[float] = None,
        min_context_window: Optional[int] = None,
        active_only: bool = True,
    ) -> List[ModelSpec]:
        """
        Query models matching all supplied filters.
        Returns models sorted by trust_score descending.
        """
        with self._lock:
            candidates = list(self._models.values())

        results = []
        for m in candidates:
            if active_only and not m.active:
                continue
            if capabilities and not capabilities.issubset(m.capabilities):
                continue
            if max_tier is not None and m.tier.value > max_tier:
                continue
            if max_cost_per_1k_input is not None and m.cost_per_1k_input > max_cost_per_1k_input:
                continue
            if privacy_level is not None and _privacy_rank(m.privacy_level) > _privacy_rank(privacy_level):
                continue
            if provider is not None and m.provider != provider:
                continue
            if min_trust is not None and m.trust_score < min_trust:
                continue
            if min_context_window is not None and m.context_window < min_context_window:
                continue
            results.append(m)

        results.sort(key=lambda m: m.trust_score, reverse=True)
        return results

    def by_capability(self, cap: ModelCapability) -> List[ModelSpec]:
        """Shortcut: all active models with a specific capability."""
        return self.query(capabilities={cap})

    # ── Trust mutations ──

    def update_trust(self, model_id: str, new_score: float) -> Optional[ModelSpec]:
        """Update trust score and recalculate tier. Returns updated spec or None."""
        with self._lock:
            spec = self._models.get(model_id)
            if spec is None:
                return None
            new_tier = compute_tier(new_score)
            deactivate = new_score < DEACTIVATION_THRESHOLD
            updated = ModelSpec(
                model_id=spec.model_id,
                display_name=spec.display_name,
                provider=spec.provider,
                tier=new_tier,
                capabilities=spec.capabilities,
                context_window=spec.context_window,
                cost_per_1k_input=spec.cost_per_1k_input,
                cost_per_1k_output=spec.cost_per_1k_output,
                latency_class=spec.latency_class,
                trust_score=max(0.0, min(100.0, new_score)),
                privacy_level=spec.privacy_level,
                max_output_tokens=spec.max_output_tokens,
                supports_streaming=spec.supports_streaming,
                supports_tools=spec.supports_tools,
                last_validated=time.time(),
                active=not deactivate,
                metadata=spec.metadata,
            )
            self._models[model_id] = updated
            if spec.tier != new_tier:
                log.warning("Model %s tier changed: %d → %d (trust=%.1f)",
                            model_id, spec.tier.value, new_tier.value, new_score)
            if deactivate:
                log.warning("Model %s deactivated (trust=%.1f < %.1f)",
                            model_id, new_score, DEACTIVATION_THRESHOLD)
            return updated

    # ── Summaries ──

    def summary(self) -> Dict[str, Any]:
        """Registry-level statistics."""
        with self._lock:
            models = list(self._models.values())
        active = [m for m in models if m.active]
        by_tier = {}
        for m in active:
            tier = f"tier_{m.tier.value}"
            by_tier.setdefault(tier, []).append(m.model_id)
        by_provider = {}
        for m in active:
            by_provider.setdefault(m.provider.value, []).append(m.model_id)
        return {
            "total_models": len(models),
            "active_models": len(active),
            "by_tier": {k: len(v) for k, v in by_tier.items()},
            "by_provider": {k: len(v) for k, v in by_provider.items()},
            "avg_trust_score": round(
                sum(m.trust_score for m in active) / max(len(active), 1), 2
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                mid: spec.to_dict()
                for mid, spec in self._models.items()
            }


def _privacy_rank(level: PrivacyLevel) -> int:
    """Lower = more private. Used for filtering."""
    return {
        PrivacyLevel.LOCAL: 0,
        PrivacyLevel.US_CLOUD: 1,
        PrivacyLevel.FOREIGN_CLOUD: 2,
    }.get(level, 2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODULE-LEVEL SINGLETON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_registry: Optional[ModelRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> ModelRegistry:
    """Return the module-level singleton registry."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ModelRegistry(seed_defaults=True)
    return _registry
