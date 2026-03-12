# --------------- Model Router — Elimination-First Model Selection ---------------
"""
v20 · Multi-Model Ecosystem — Routing Engine

Applies Praxis's elimination reasoning to model selection.  Instead
of always routing to the same LLM, the router:

    1. Parses intent (task type, complexity, domain, privacy sensitivity)
    2. Generates broad candidate set from ModelRegistry
    3. Hard-eliminates models violating constraints (budget, privacy, capability)
    4. Soft-penalises survivors (trust decay, cost efficiency, latency)
    5. Decides routing strategy: single model vs multi-model collaboration

This is the core innovation — clinical differential diagnosis applied
to model routing.  Each eliminated model is logged with a reason code.

Modules consumed:
    model_registry   → candidate pool
    model_trust_decay → trust scores
    interpreter      → structured intent extraction
    ai_economics     → budget enforcement
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("praxis.model_router")

try:
    from .model_registry import (
        ModelSpec, ModelTier, ModelCapability, ModelProvider,
        PrivacyLevel, LatencyClass, ModelRegistry, get_registry,
    )
except ImportError:
    from model_registry import (
        ModelSpec, ModelTier, ModelCapability, ModelProvider,
        PrivacyLevel, LatencyClass, ModelRegistry, get_registry,
    )

try:
    from .interpreter import interpret
    _INTERPRETER = True
except ImportError:
    try:
        from interpreter import interpret
        _INTERPRETER = True
    except ImportError:
        _INTERPRETER = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RoutingStrategy(str, Enum):
    SINGLE = "single"           # One best model
    FAN_OUT = "fan_out"         # N models in parallel → aggregate
    CHAIN = "chain"             # Sequential A → B → C
    CONSENSUS = "consensus"     # N models → vote on best answer
    ADVERSARIAL = "adversarial" # Model A generates, Model B critiques


class EliminationCode(str, Enum):
    """Reason codes for model elimination (mirrors differential.py)."""
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    PRIVACY_VIOLATION = "PRIVACY_VIOLATION"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    CONTEXT_WINDOW_EXCEEDED = "CONTEXT_WINDOW_EXCEEDED"
    TIER_BLOCKED = "TIER_BLOCKED"
    MODEL_INACTIVE = "MODEL_INACTIVE"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TRUST_TOO_LOW = "TRUST_TOO_LOW"
    SOFT_PENALTY_THRESHOLD = "SOFT_PENALTY_THRESHOLD"


class TaskComplexity(str, Enum):
    SIMPLE = "simple"       # Single intent, low ambiguity
    MODERATE = "moderate"   # Multiple sub-queries
    COMPLEX = "complex"     # Multi-step, cross-domain, or adversarial review needed


@dataclass
class ModelElimination:
    """Record of a model being eliminated from candidacy."""
    model_id: str
    reason_code: EliminationCode
    explanation: str
    stage: int              # 3 = hard elimination, 4 = soft penalty

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "reason_code": self.reason_code.value,
            "explanation": self.explanation,
            "stage": self.stage,
        }


@dataclass
class ScoredModel:
    """A model that survived elimination with its composite score."""
    spec: ModelSpec
    base_score: float = 0.0
    penalties: List[str] = field(default_factory=list)
    penalty_total: float = 0.0
    final_score: float = 0.0
    role: str = "primary"   # "primary", "reviewer", "specialist"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.spec.model_id,
            "display_name": self.spec.display_name,
            "provider": self.spec.provider.value,
            "tier": self.spec.tier.value,
            "trust_score": round(self.spec.trust_score, 2),
            "final_score": round(self.final_score, 2),
            "role": self.role,
            "penalties": self.penalties,
        }


@dataclass
class RoutingDecision:
    """Complete routing decision with full elimination trace."""
    query: str
    strategy: RoutingStrategy
    selected_models: List[ScoredModel]
    eliminated: List[ModelElimination]
    complexity: TaskComplexity
    cost_estimate_usd: float = 0.0
    reasoning: str = ""
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:200],
            "strategy": self.strategy.value,
            "complexity": self.complexity.value,
            "selected_models": [m.to_dict() for m in self.selected_models],
            "eliminated_count": len(self.eliminated),
            "eliminated": [e.to_dict() for e in self.eliminated],
            "cost_estimate_usd": round(self.cost_estimate_usd, 6),
            "reasoning": self.reasoning,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONSTANTS & THRESHOLDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Minimum trust score to survive soft penalties
MIN_MODEL_VIABILITY = 25.0

# Soft penalty weights
WEIGHT_TRUST = 0.35
WEIGHT_COST = 0.25
WEIGHT_LATENCY = 0.20
WEIGHT_CAPABILITY_FIT = 0.20

# Complexity thresholds
COMPLEXITY_KEYWORDS_MULTI = {
    "compare", "vs", "versus", "contrast", "evaluate",
    "pros and cons", "trade-offs", "review", "audit", "critique",
}
COMPLEXITY_KEYWORDS_CHAIN = {
    "then", "after that", "followed by", "step by step", "pipeline",
    "workflow", "first", "second", "finally",
}

# Budget ceilings (USD per query, estimated)
BUDGET_CEILINGS = {
    "free": 0.0,
    "low": 0.01,
    "medium": 0.10,
    "high": 1.00,
    "unlimited": float("inf"),
}

# Max models for multi-model strategies
MAX_FAN_OUT_MODELS = 3
MAX_CHAIN_MODELS = 4

# Privacy-sensitive keywords that trigger local-only routing
PRIVACY_TRIGGERS = {
    "hipaa", "phi", "pii", "patient", "medical record",
    "ssn", "social security", "credit card", "bank account",
    "confidential", "classified", "internal only",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CAPABILITY INFERENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Map intent keywords to required capabilities
_CAPABILITY_MAP: Dict[str, Set[ModelCapability]] = {
    "code": {ModelCapability.CODE},
    "coding": {ModelCapability.CODE},
    "programming": {ModelCapability.CODE},
    "debug": {ModelCapability.CODE, ModelCapability.REASONING},
    "refactor": {ModelCapability.CODE},
    "math": {ModelCapability.MATH, ModelCapability.REASONING},
    "calculate": {ModelCapability.MATH},
    "reason": {ModelCapability.REASONING},
    "analyze": {ModelCapability.REASONING},
    "explain": {ModelCapability.REASONING},
    "research": {ModelCapability.REASONING, ModelCapability.LONG_CONTEXT},
    "write": {ModelCapability.CREATIVE},
    "creative": {ModelCapability.CREATIVE},
    "story": {ModelCapability.CREATIVE},
    "blog": {ModelCapability.CREATIVE},
    "image": {ModelCapability.VISION},
    "photo": {ModelCapability.VISION},
    "describe image": {ModelCapability.VISION},
    "translate": {ModelCapability.MULTILINGUAL},
    "fast": {ModelCapability.FAST},
    "quick": {ModelCapability.FAST},
    "cheap": {ModelCapability.CHEAP},
    "budget": {ModelCapability.CHEAP},
}


def _infer_capabilities(query: str) -> Set[ModelCapability]:
    """Infer required capabilities from query keywords."""
    query_lower = query.lower()
    caps: Set[ModelCapability] = set()
    for keyword, required in _CAPABILITY_MAP.items():
        if keyword in query_lower:
            caps |= required
    return caps


def _detect_complexity(query: str, intent: Optional[Dict[str, Any]] = None) -> TaskComplexity:
    """Classify query complexity for routing strategy."""
    query_lower = query.lower()

    # Check for chaining signals
    chain_hits = sum(1 for kw in COMPLEXITY_KEYWORDS_CHAIN if kw in query_lower)
    if chain_hits >= 2:
        return TaskComplexity.COMPLEX

    # Check for comparison/review signals
    multi_hits = sum(1 for kw in COMPLEXITY_KEYWORDS_MULTI if kw in query_lower)
    if multi_hits >= 1:
        return TaskComplexity.MODERATE

    # Use interpreter ambiguity if available
    if intent:
        if intent.get("clarification_needed", False):
            return TaskComplexity.MODERATE
        sub_intents = intent.get("sub_intents", [])
        if len(sub_intents) > 2:
            return TaskComplexity.COMPLEX
        if len(sub_intents) > 1:
            return TaskComplexity.MODERATE

    # Length heuristic
    if len(query.split()) > 80:
        return TaskComplexity.MODERATE

    return TaskComplexity.SIMPLE


def _detect_privacy_sensitivity(query: str) -> bool:
    """Check if query contains privacy-sensitive content."""
    query_lower = query.lower()
    return any(trigger in query_lower for trigger in PRIVACY_TRIGGERS)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def route_query(
    query: str,
    budget: str = "medium",
    privacy_required: Optional[PrivacyLevel] = None,
    max_tier: Optional[int] = None,
    preferred_providers: Optional[List[str]] = None,
    required_capabilities: Optional[Set[ModelCapability]] = None,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 2000,
    registry: Optional[ModelRegistry] = None,
) -> RoutingDecision:
    """
    Elimination-first model routing.

    Mirrors the 5-stage pipeline from differential.py:
      Stage 1: Intent analysis
      Stage 2: Broad candidate generation
      Stage 3: Hard elimination
      Stage 4: Soft penalty scoring
      Stage 5: Routing strategy decision
    """
    t0 = time.time()
    reg = registry or get_registry()
    eliminated: List[ModelElimination] = []

    # ── Stage 1: Intent analysis ──────────────────────────────────
    intent: Optional[Dict[str, Any]] = None
    if _INTERPRETER:
        try:
            intent = interpret(query)
        except Exception:
            pass  # Fall back to keyword analysis

    inferred_caps = required_capabilities or _infer_capabilities(query)
    complexity = _detect_complexity(query, intent)
    privacy_sensitive = _detect_privacy_sensitivity(query)
    if privacy_sensitive and privacy_required is None:
        privacy_required = PrivacyLevel.LOCAL

    budget_ceiling = BUDGET_CEILINGS.get(budget, BUDGET_CEILINGS["medium"])

    # ── Stage 2: Broad candidate generation ──────────────────────
    candidates = reg.list_all()

    # ── Stage 3: Hard elimination ─────────────────────────────────
    survivors: List[ModelSpec] = []
    for spec in candidates:
        # Active check
        if not spec.active:
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.MODEL_INACTIVE,
                "Model deactivated due to low trust", stage=3,
            ))
            continue

        # Budget check
        est_cost = spec.estimated_cost(estimated_input_tokens, estimated_output_tokens)
        if budget_ceiling < float("inf") and est_cost > budget_ceiling:
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.BUDGET_EXCEEDED,
                f"Estimated cost ${est_cost:.4f} exceeds {budget} budget (${budget_ceiling:.2f})",
                stage=3,
            ))
            continue

        # Privacy check
        if privacy_required is not None:
            from .model_registry import _privacy_rank
            if _privacy_rank(spec.privacy_level) > _privacy_rank(privacy_required):
                eliminated.append(ModelElimination(
                    spec.model_id, EliminationCode.PRIVACY_VIOLATION,
                    f"Privacy level {spec.privacy_level.value} violates requirement {privacy_required.value}",
                    stage=3,
                ))
                continue

        # Capability check (only if capabilities were identified)
        if inferred_caps and not inferred_caps.issubset(spec.capabilities):
            missing = inferred_caps - spec.capabilities
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.CAPABILITY_MISMATCH,
                f"Missing capabilities: {', '.join(c.value for c in missing)}",
                stage=3,
            ))
            continue

        # Tier check
        if max_tier is not None and spec.tier.value > max_tier:
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.TIER_BLOCKED,
                f"Model is tier {spec.tier.value}, max allowed is {max_tier}",
                stage=3,
            ))
            continue

        # Context window check
        if estimated_input_tokens > spec.context_window * 0.9:
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.CONTEXT_WINDOW_EXCEEDED,
                f"Input tokens ({estimated_input_tokens}) near context limit ({spec.context_window})",
                stage=3,
            ))
            continue

        survivors.append(spec)

    # ── Stage 4: Soft penalty scoring ──────────────────────────────
    scored: List[ScoredModel] = []
    for spec in survivors:
        # Base score from trust
        trust_norm = spec.trust_score / 100.0   # 0-1

        # Cost efficiency: cheaper is better (inverted, normalised)
        max_cost = max(s.cost_per_1k_input for s in survivors) or 0.001
        cost_efficiency = 1.0 - (spec.cost_per_1k_input / max_cost)

        # Latency preference
        latency_scores = {LatencyClass.FAST: 1.0, LatencyClass.MEDIUM: 0.6, LatencyClass.SLOW: 0.3}
        latency_norm = latency_scores.get(spec.latency_class, 0.5)

        # Capability fit: what fraction of required caps does this model have?
        if inferred_caps:
            cap_overlap = len(inferred_caps & spec.capabilities) / len(inferred_caps)
        else:
            cap_overlap = len(spec.capabilities) / len(ModelCapability)

        # Weighted composite
        base = (
            WEIGHT_TRUST * trust_norm
            + WEIGHT_COST * cost_efficiency
            + WEIGHT_LATENCY * latency_norm
            + WEIGHT_CAPABILITY_FIT * cap_overlap
        )

        # Provider preference bonus
        penalties: List[str] = []
        if preferred_providers and spec.provider.value not in preferred_providers:
            base *= 0.85
            penalties.append("non-preferred provider (-15%)")

        # Trust penalty
        if spec.trust_score < MIN_MODEL_VIABILITY:
            eliminated.append(ModelElimination(
                spec.model_id, EliminationCode.TRUST_TOO_LOW,
                f"Trust score {spec.trust_score:.1f} below viability threshold {MIN_MODEL_VIABILITY}",
                stage=4,
            ))
            continue

        scored.append(ScoredModel(
            spec=spec,
            base_score=round(base, 4),
            penalties=penalties,
            penalty_total=round(1.0 - base, 4),
            final_score=round(base, 4),
        ))

    scored.sort(key=lambda s: s.final_score, reverse=True)

    # ── Stage 5: Routing strategy decision ────────────────────────
    if not scored:
        # No survivors — fall back to highest-trust model with minimal filters
        fallback = reg.query(min_trust=0.0, active_only=True)
        if fallback:
            scored = [ScoredModel(spec=fallback[0], final_score=0.5)]
        strategy = RoutingStrategy.SINGLE
        reasoning = "No models survived elimination — using fallback"
    elif complexity == TaskComplexity.SIMPLE:
        strategy = RoutingStrategy.SINGLE
        scored = scored[:1]
        reasoning = f"Simple query → single model: {scored[0].spec.display_name}"
    elif complexity == TaskComplexity.MODERATE:
        # Fan-out: top N models for comparison tasks
        query_lower = query.lower()
        is_comparison = any(kw in query_lower for kw in COMPLEXITY_KEYWORDS_MULTI)
        if is_comparison and len(scored) >= 2:
            strategy = RoutingStrategy.FAN_OUT
            scored = scored[:MAX_FAN_OUT_MODELS]
            for i, s in enumerate(scored):
                s.role = "primary" if i == 0 else "reviewer"
            reasoning = f"Comparison query → fan-out to {len(scored)} models"
        else:
            strategy = RoutingStrategy.SINGLE
            scored = scored[:1]
            reasoning = f"Moderate query → single best model: {scored[0].spec.display_name}"
    else:
        # Complex: chain or adversarial based on keyword signals
        query_lower = query.lower()
        has_chain_signals = any(kw in query_lower for kw in COMPLEXITY_KEYWORDS_CHAIN)
        if has_chain_signals and len(scored) >= 2:
            strategy = RoutingStrategy.CHAIN
            scored = scored[:MAX_CHAIN_MODELS]
            for i, s in enumerate(scored):
                s.role = "specialist" if i > 0 else "primary"
            reasoning = f"Pipeline query → chained {len(scored)} models"
        elif len(scored) >= 2:
            strategy = RoutingStrategy.ADVERSARIAL
            scored = scored[:2]
            scored[0].role = "primary"
            scored[1].role = "reviewer"
            # Ensure reviewer is from different provider for independence
            if scored[0].spec.provider == scored[1].spec.provider and len(survivors) > 2:
                for alt in survivors:
                    if alt.provider != scored[0].spec.provider:
                        scored[1] = ScoredModel(spec=alt, final_score=0.0, role="reviewer")
                        break
            reasoning = f"Complex query → adversarial: {scored[0].spec.display_name} generates, {scored[1].spec.display_name} reviews"
        else:
            strategy = RoutingStrategy.SINGLE
            scored = scored[:1]
            reasoning = f"Complex query but only 1 survivor → {scored[0].spec.display_name}"

    # Cost estimate
    cost_estimate = sum(
        s.spec.estimated_cost(estimated_input_tokens, estimated_output_tokens)
        for s in scored
    )

    return RoutingDecision(
        query=query,
        strategy=strategy,
        selected_models=scored,
        eliminated=eliminated,
        complexity=complexity,
        cost_estimate_usd=cost_estimate,
        reasoning=reasoning,
        elapsed_ms=(time.time() - t0) * 1000,
    )
