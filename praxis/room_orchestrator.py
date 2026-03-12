"""Room Orchestrator — session lifecycle, collaboration dispatch, and SSE events.

Ties together:
  * ``room_store``            — persistent Room + Session state
  * ``room_router_extension`` — Room-scoped elimination routing
  * ``ecosystem``             — multi-model collaboration execution
  * ``shared_state``          — CoALA memory relay
  * ``context_engine``        — ContextVector extraction
  * ``journey``               — journey lifecycle management

Produces a stream of ``RoomEvent`` dicts that the SSE endpoint
serialises as ``text/event-stream`` lines.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional

log = logging.getLogger("praxis.room_orchestrator")

# ── Lazy imports (keep module safe if dependencies aren't installed) ──

try:
    from . import room_store
except ImportError:
    import room_store  # type: ignore[no-redef]

try:
    from .room_router_extension import (
        route_for_room,
        RoomRoutingDecision,
        record_spend,
    )
except ImportError:
    from room_router_extension import (  # type: ignore[no-redef]
        route_for_room,
        RoomRoutingDecision,
        record_spend,
    )

_ecosystem_available = False
try:
    from .ecosystem import run_collaboration, CollaborationResult
    _ecosystem_available = True
except ImportError:
    try:
        from ecosystem import run_collaboration, CollaborationResult  # type: ignore[no-redef]
        _ecosystem_available = True
    except ImportError:
        pass

_context_engine_available = False
try:
    from .context_engine import extract_context
    _context_engine_available = True
except ImportError:
    try:
        from context_engine import extract_context  # type: ignore[no-redef]
        _context_engine_available = True
    except ImportError:
        pass

_shared_state_available = False
try:
    from .shared_state import SharedStateManager
    _shared_state_available = True
except ImportError:
    try:
        from shared_state import SharedStateManager  # type: ignore[no-redef]
        _shared_state_available = True
    except ImportError:
        pass

_journey_available = False
try:
    from .journey import JourneyOracle
    _journey_available = True
except ImportError:
    try:
        from journey import JourneyOracle  # type: ignore[no-redef]
        _journey_available = True
    except ImportError:
        pass


# -------------------------------------------------------------------
# Event types
# -------------------------------------------------------------------

class EventType(str, Enum):
    SESSION_START = "session_start"
    CONTEXT_EXTRACTED = "context_extracted"
    ROUTING_DECISION = "routing_decision"
    MODEL_START = "model_start"
    TOKEN_CHUNK = "token_chunk"
    MODEL_COMPLETE = "model_complete"
    COLLABORATION_RESULT = "collaboration_result"
    ARTIFACT_SAVED = "artifact_saved"
    SPEND_RECORDED = "spend_recorded"
    JOURNEY_UPDATE = "journey_update"
    SESSION_END = "session_end"
    ERROR = "error"


@dataclass
class RoomEvent:
    """Single SSE-serialisable event."""
    event: EventType
    room_id: str
    session_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Format as a Server-Sent Events text message."""
        payload = {
            "event": self.event.value,
            "room_id": self.room_id,
            "session_id": self.session_id,
            "data": self.data,
            "ts": round(self.timestamp, 3),
        }
        return f"event: {self.event.value}\ndata: {json.dumps(payload)}\n\n"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.value,
            "room_id": self.room_id,
            "session_id": self.session_id,
            "data": self.data,
            "ts": round(self.timestamp, 3),
        }


# -------------------------------------------------------------------
# Orchestrator
# -------------------------------------------------------------------

def _emit(event_type: EventType, room_id: str, session_id: str,
          data: Optional[Dict[str, Any]] = None) -> RoomEvent:
    return RoomEvent(event=event_type, room_id=room_id,
                     session_id=session_id, data=data or {})


def execute_in_room(
    room_id: str,
    query: str,
    *,
    budget: str = "medium",
    strategy: Optional[str] = None,
    system_prompt: str = "",
    privacy_required: Optional[str] = None,
    user_id: str = "anon",
) -> Generator[RoomEvent, None, None]:
    """Run a full query lifecycle inside a Room, yielding SSE events.

    Pipeline:
        1. Open (or reuse) a Room Session
        2. Extract ContextVector and serialise into Room
        3. Route through Room-scoped elimination pipeline
        4. Dispatch to ecosystem.run_collaboration()
        5. Record spend + persist artifact
        6. Yield events at each stage for SSE streaming
    """
    # ── 1. Session ────────────────────────────────────────────────
    room = room_store.get_room(room_id)
    if room is None:
        yield _emit(EventType.ERROR, room_id, "",
                    {"message": "Room not found"})
        return

    session = room_store.create_session(room_id)
    sid = session["session_id"]
    yield _emit(EventType.SESSION_START, room_id, sid, {
        "room_name": room.get("name", ""),
    })

    # Shared state manager for this session
    ssm = None
    if _shared_state_available:
        ssm = SharedStateManager(session_id=sid)

    # ── 2. Context extraction ─────────────────────────────────────
    ctx_dict: Dict[str, Any] = {}
    if _context_engine_available:
        try:
            cv = extract_context(query)
            ctx_dict = cv.to_dict()
            # Persist to Room's operator_context (merge, don't overwrite)
            existing_ctx = dict(room.get("operator_context", {}))
            existing_ctx["latest_extraction"] = ctx_dict
            room_store.update_room(room_id, {"operator_context": existing_ctx})
        except Exception as exc:
            log.warning("Context extraction failed: %s", exc)

    yield _emit(EventType.CONTEXT_EXTRACTED, room_id, sid, {
        "tier_count": len(ctx_dict.get("tier_assignments", {})),
        "context_keys": list(ctx_dict.keys())[:10],
    })

    # ── 3. Room-scoped routing ────────────────────────────────────
    try:
        routing: RoomRoutingDecision = route_for_room(
            query=query,
            room_id=room_id,
            budget=budget,
            privacy_required=privacy_required,
        )
        routing_dict = routing.to_dict()
    except Exception as exc:
        log.error("Routing failed: %s", exc)
        yield _emit(EventType.ERROR, room_id, sid,
                    {"message": f"Routing error: {exc}"})
        room_store.end_session(sid)
        yield _emit(EventType.SESSION_END, room_id, sid)
        return

    yield _emit(EventType.ROUTING_DECISION, room_id, sid, {
        "strategy": routing_dict.get("strategy", "single"),
        "selected_models": routing_dict.get("selected_models", []),
        "eliminated_count": routing_dict.get("eliminated_count", 0),
        "room_eliminations": routing_dict.get("room_eliminations", []),
        "remaining_budget_usd": routing_dict.get("remaining_budget_usd", 0),
        "cost_estimate_usd": routing_dict.get("cost_estimate_usd", 0),
    })

    # ── 4. Collaboration execution ────────────────────────────────
    collab_result = None
    if _ecosystem_available:
        resolved_strategy = strategy or routing_dict.get("strategy", "single")

        # Notify that models are starting
        selected = routing_dict.get("selected_models", [])
        for m in selected:
            mid = m.get("model_id", "unknown")
            yield _emit(EventType.MODEL_START, room_id, sid, {
                "model_id": mid,
                "role": m.get("role", "primary"),
            })

        try:
            collab_result = run_collaboration(
                task=query,
                strategy=resolved_strategy,
                budget=budget,
                system_prompt=system_prompt,
                privacy_required=privacy_required,
                user_id=user_id,
            )
        except Exception as exc:
            log.error("Collaboration failed: %s", exc)
            yield _emit(EventType.ERROR, room_id, sid,
                        {"message": f"Collaboration error: {exc}"})

    if collab_result is not None:
        result_dict = collab_result.to_dict()

        # Record outputs in shared state
        if ssm:
            ssm.record_output(
                model_id=", ".join(result_dict.get("models_used", [])),
                content=result_dict.get("final_output", "")[:2000],
                confidence=result_dict.get("consensus_score", 0.8),
            )

        yield _emit(EventType.COLLABORATION_RESULT, room_id, sid, {
            "strategy": result_dict.get("strategy", ""),
            "models_used": result_dict.get("models_used", []),
            "final_output": result_dict.get("final_output", ""),
            "total_cost_usd": result_dict.get("total_cost_usd", 0),
            "total_tokens": result_dict.get("total_tokens", 0),
            "consensus_score": result_dict.get("consensus_score", 0),
        })

        # ── 5a. Record spend ──────────────────────────────────────
        cost = result_dict.get("total_cost_usd", 0.0)
        if cost > 0:
            record_spend(room_id, cost)
            yield _emit(EventType.SPEND_RECORDED, room_id, sid, {
                "amount_usd": cost,
            })

        # ── 5b. Persist artifact ──────────────────────────────────
        output_text = result_dict.get("final_output", "")
        if output_text:
            # Determine journey_id (from Room's latest journey or "none")
            journey_id = "none"
            jh = room.get("journey_history", [])
            if jh:
                journey_id = jh[-1]

            artifact = room_store.create_artifact(
                room_id=room_id,
                journey_id=journey_id,
                title=query[:200],
                content_type="text/plain",
                content=output_text,
                created_by_model=", ".join(
                    result_dict.get("models_used", ["unknown"])),
            )
            yield _emit(EventType.ARTIFACT_SAVED, room_id, sid, {
                "artifact_id": artifact["artifact_id"],
            })
    else:
        # No ecosystem — return a stub result
        yield _emit(EventType.COLLABORATION_RESULT, room_id, sid, {
            "strategy": "none",
            "models_used": [],
            "final_output": "(ecosystem module unavailable)",
            "total_cost_usd": 0,
            "total_tokens": 0,
        })

    # ── 6. Journey bookkeeping ────────────────────────────────────
    if _journey_available:
        try:
            oracle = JourneyOracle()
            # Record query as a journey advancement event
            yield _emit(EventType.JOURNEY_UPDATE, room_id, sid, {
                "stage": "active",
            })
        except Exception:
            pass

    # ── 7. Close session ──────────────────────────────────────────
    room_store.end_session(sid)
    yield _emit(EventType.SESSION_END, room_id, sid)


# -------------------------------------------------------------------
# Convenience: non-streaming wrapper
# -------------------------------------------------------------------

def execute_in_room_sync(
    room_id: str,
    query: str,
    **kwargs,
) -> List[Dict[str, Any]]:
    """Consume all events and return them as a list of dicts."""
    return [ev.to_dict() for ev in execute_in_room(room_id, query, **kwargs)]
