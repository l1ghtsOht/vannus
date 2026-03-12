"""Room-scoped routing extension for the elimination pipeline.

Wraps ``model_router.route_query()`` with Room-specific constraints:

* **Room eliminations**: permanently excluded models (``active_eliminations``)
* **Budget enforcement**: query-level ceiling derived from remaining room budget
* **Scope config**: ``PRAXIS_ELIMINATION_SCOPE``
    - ``"room"`` (default): eliminations are isolated per Room
    - ``"global"``: eliminations propagate to the global model registry
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

log = logging.getLogger("praxis.room_router_extension")

try:
    from .model_router import (
        route_query,
        RoutingDecision,
        RoutingStrategy,
        EliminationCode,
        ModelElimination,
    )
except ImportError:
    from model_router import (  # type: ignore[no-redef]
        route_query,
        RoutingDecision,
        RoutingStrategy,
        EliminationCode,
        ModelElimination,
    )

try:
    from .model_registry import ModelCapability, PrivacyLevel
except ImportError:
    from model_registry import ModelCapability, PrivacyLevel  # type: ignore[no-redef]

try:
    from . import room_store
except ImportError:
    import room_store  # type: ignore[no-redef]

try:
    from . import config as _cfg
except ImportError:
    import config as _cfg  # type: ignore[no-redef]


# -------------------------------------------------------------------
# Data models
# -------------------------------------------------------------------

@dataclass
class RoomRoutingDecision:
    """Wraps ``RoutingDecision`` with Room-scoped metadata."""
    decision_id: str = ""
    room_id: str = ""
    inner: Optional[RoutingDecision] = None
    room_eliminations: List[ModelElimination] = field(default_factory=list)
    remaining_budget_usd: float = 0.0
    scope: str = "room"

    def to_dict(self) -> Dict[str, Any]:
        base = self.inner.to_dict() if self.inner else {}
        base["decision_id"] = self.decision_id
        base["room_id"] = self.room_id
        base["room_eliminations"] = [e.to_dict() for e in self.room_eliminations]
        base["remaining_budget_usd"] = round(self.remaining_budget_usd, 6)
        base["scope"] = self.scope
        return base


# -------------------------------------------------------------------
# Core function
# -------------------------------------------------------------------

def route_for_room(
    query: str,
    room_id: str,
    budget: str = "medium",
    privacy_required: Optional[str] = None,
    max_tier: Optional[int] = None,
    preferred_providers: Optional[List[str]] = None,
    required_capabilities: Optional[Set[ModelCapability]] = None,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 2000,
) -> RoomRoutingDecision:
    """Run the elimination pipeline with Room-scoped constraints layered on.

    1. Loads the Room from ``room_store`` to get ``active_eliminations``.
    2. Computes effective budget ceiling from remaining room balance.
    3. Calls ``route_query()`` (the existing 5-stage pipeline).
    4. Applies Room-level eliminations on top of the pipeline results.
    5. Packages the result in a ``RoomRoutingDecision``.
    """
    scope = _cfg.get("elimination_scope") or "room"
    room = room_store.get_room(room_id)

    room_elims: Dict[str, str] = {}
    remaining_budget = float("inf")
    if room:
        room_elims = room.get("active_eliminations", {})
        cap = room.get("budget_cap_usd", 50.0)
        spent = room.get("current_spend_usd", 0.0)
        remaining_budget = max(0.0, cap - spent)

    # Resolve privacy level
    priv = None
    if privacy_required:
        try:
            priv = PrivacyLevel(privacy_required)
        except (ValueError, KeyError):
            pass

    # --- Delegate to the core router ---
    decision = route_query(
        query=query,
        budget=budget,
        privacy_required=priv,
        max_tier=max_tier,
        preferred_providers=preferred_providers,
        required_capabilities=required_capabilities,
        estimated_input_tokens=estimated_input_tokens,
        estimated_output_tokens=estimated_output_tokens,
    )

    # --- Layer Room-level eliminations on top ---
    extra_elims: List[ModelElimination] = []
    if room_elims:
        surviving = []
        for scored in decision.selected_models:
            mid = scored.spec.model_id
            if mid in room_elims:
                reason = room_elims[mid]
                extra_elims.append(ModelElimination(
                    model_id=mid,
                    reason_code=EliminationCode.TIER_BLOCKED,
                    explanation=f"Room-level elimination: {reason}",
                    stage=6,  # post-pipeline stage
                ))
            else:
                surviving.append(scored)
        if surviving:
            decision.selected_models = surviving
        else:
            log.warning("Room %s: all models eliminated by room constraints", room_id)

    # --- Budget guard ---
    if decision.cost_estimate_usd > remaining_budget > 0:
        log.warning(
            "Room %s: estimated cost $%.4f exceeds remaining budget $%.4f",
            room_id, decision.cost_estimate_usd, remaining_budget,
        )

    return RoomRoutingDecision(
        decision_id=uuid4().hex,
        room_id=room_id,
        inner=decision,
        room_eliminations=extra_elims,
        remaining_budget_usd=remaining_budget,
        scope=scope,
    )


def add_room_elimination(
    room_id: str,
    model_id: str,
    reason: str,
) -> Optional[Dict[str, Any]]:
    """Permanently eliminate a model from a Room's candidate pool."""
    room = room_store.get_room(room_id)
    if room is None:
        return None
    elims = dict(room.get("active_eliminations", {}))
    elims[model_id] = reason
    return room_store.update_room(room_id, {"active_eliminations": elims})


def remove_room_elimination(
    room_id: str,
    model_id: str,
) -> Optional[Dict[str, Any]]:
    """Re-admit a previously eliminated model."""
    room = room_store.get_room(room_id)
    if room is None:
        return None
    elims = dict(room.get("active_eliminations", {}))
    elims.pop(model_id, None)
    return room_store.update_room(room_id, {"active_eliminations": elims})


def record_spend(room_id: str, amount_usd: float) -> Optional[Dict[str, Any]]:
    """Increment the Room's running cost tally."""
    room = room_store.get_room(room_id)
    if room is None:
        return None
    new_spend = room.get("current_spend_usd", 0.0) + amount_usd
    return room_store.update_room(room_id, {"current_spend_usd": new_spend})
