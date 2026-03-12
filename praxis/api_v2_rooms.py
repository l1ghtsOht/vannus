"""REST API routes for Praxis Room CRUD (v23).

Follows the ``register_*_routes(app, deps)`` convention used by
``api_routes_core.py`` and ``api_routes_features.py``.
"""
# pyright: reportInvalidTypeForm=false
from typing import Optional


def register_room_routes(app, deps):
    """Mount /room/* endpoints on the FastAPI ``app``."""
    _get_current_user = deps.get("get_current_user")

    # Lazy-import room_store so the module stays loadable even if
    # room_store.py hasn't been installed yet.
    try:
        from . import room_store
    except ImportError:
        import room_store  # type: ignore[no-redef]

    try:
        from pydantic import BaseModel, Field
    except ImportError:
        BaseModel = deps.get("BaseModel")  # type: ignore[assignment]
        Field = lambda *a, **kw: kw.get("default")  # noqa: E731

    # -- Request schemas (thin wrappers, not domain models) -----------

    class CreateRoomRequest(BaseModel):  # type: ignore[misc]
        name: str
        operator_context: Optional[dict] = None
        budget_cap_usd: float = 50.0

    class UpdateRoomRequest(BaseModel):  # type: ignore[misc]
        name: Optional[str] = None
        operator_context: Optional[dict] = None
        active_eliminations: Optional[dict] = None
        budget_cap_usd: Optional[float] = None
        is_archived: Optional[bool] = None

    class CreateArtifactRequest(BaseModel):  # type: ignore[misc]
        journey_id: str
        title: str
        content_type: str = "text/plain"
        content: str = ""
        created_by_model: str = "unknown"
        parent_artifact_id: Optional[str] = None
        version: int = 1

    # -- Room endpoints -----------------------------------------------

    @app.post("/room")
    def create_room(req: CreateRoomRequest):
        room = room_store.create_room(
            name=req.name,
            operator_context=req.operator_context,
            budget_cap_usd=req.budget_cap_usd,
        )
        return {"success": True, "data": room}

    @app.get("/room")
    def list_rooms(include_archived: bool = False):
        rooms = room_store.list_rooms(include_archived=include_archived)
        return {"success": True, "data": rooms}

    @app.get("/room/{room_id}")
    def get_room(room_id: str):
        room = room_store.get_room(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}
        return {"success": True, "data": room}

    @app.patch("/room/{room_id}")
    def update_room(room_id: str, req: UpdateRoomRequest):
        updates = {k: v for k, v in req.model_dump().items() if v is not None}
        room = room_store.update_room(room_id, updates)
        if room is None:
            return {"success": False, "error": "Room not found"}
        return {"success": True, "data": room}

    @app.delete("/room/{room_id}")
    def archive_room(room_id: str):
        ok = room_store.archive_room(room_id)
        if not ok:
            return {"success": False, "error": "Room not found"}
        return {"success": True, "data": {"archived": True}}

    # -- Session endpoints --------------------------------------------

    @app.post("/room/{room_id}/session")
    def create_session(room_id: str):
        room = room_store.get_room(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}
        session = room_store.create_session(room_id)
        return {"success": True, "data": session}

    @app.get("/room/{room_id}/session")
    def list_sessions(room_id: str):
        sessions = room_store.list_sessions(room_id)
        return {"success": True, "data": sessions}

    @app.post("/room/session/{session_id}/end")
    def end_session(session_id: str):
        session = room_store.end_session(session_id)
        if session is None:
            return {"success": False, "error": "Session not found"}
        return {"success": True, "data": session}

    # -- Artifact endpoints -------------------------------------------

    @app.post("/room/{room_id}/artifact")
    def create_artifact(room_id: str, req: CreateArtifactRequest):
        room = room_store.get_room(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}
        artifact = room_store.create_artifact(
            room_id=room_id,
            journey_id=req.journey_id,
            title=req.title,
            content_type=req.content_type,
            content=req.content,
            created_by_model=req.created_by_model,
            parent_artifact_id=req.parent_artifact_id,
            version=req.version,
        )
        return {"success": True, "data": artifact}

    @app.get("/room/{room_id}/artifact")
    def list_artifacts(room_id: str, journey_id: Optional[str] = None):
        artifacts = room_store.list_artifacts(room_id, journey_id=journey_id)
        return {"success": True, "data": artifacts}

    @app.get("/room/artifact/{artifact_id}")
    def get_artifact(artifact_id: str):
        artifact = room_store.get_artifact(artifact_id)
        if artifact is None:
            return {"success": False, "error": "Artifact not found"}
        return {"success": True, "data": artifact}

    # -- Room history (convenience) -----------------------------------

    @app.get("/room/{room_id}/history")
    def room_history(room_id: str):
        """Return journey timeline + session log for a Room."""
        room = room_store.get_room(room_id)
        if room is None:
            return {"success": False, "error": "Room not found"}
        sessions = room_store.list_sessions(room_id)
        artifacts = room_store.list_artifacts(room_id)
        return {
            "success": True,
            "data": {
                "room_id": room_id,
                "journey_history": room.get("journey_history", []),
                "sessions": sessions,
                "artifacts": artifacts,
            },
        }

    # -- Execute (streaming SSE) --------------------------------------

    try:
        from .room_orchestrator import execute_in_room
    except ImportError:
        try:
            from room_orchestrator import execute_in_room  # type: ignore[no-redef]
        except ImportError:
            execute_in_room = None  # type: ignore[assignment]

    class ExecuteRequest(BaseModel):  # type: ignore[misc]
        query: str
        budget: str = "medium"
        strategy: Optional[str] = None
        system_prompt: str = ""
        privacy_required: Optional[str] = None
        user_id: str = "anon"

    if execute_in_room is not None:
        try:
            from fastapi.responses import StreamingResponse
        except ImportError:
            StreamingResponse = None  # type: ignore[assignment,misc]

        @app.post("/room/{room_id}/execute")
        def execute_room_query(room_id: str, req: ExecuteRequest):
            """Run a query inside a Room (non-streaming JSON response)."""
            from .room_orchestrator import execute_in_room_sync  # noqa: F811
            events = execute_in_room_sync(
                room_id,
                req.query,
                budget=req.budget,
                strategy=req.strategy,
                system_prompt=req.system_prompt,
                privacy_required=req.privacy_required,
                user_id=req.user_id,
            )
            return {"success": True, "data": events}

        if StreamingResponse is not None:
            @app.post("/room/{room_id}/stream")
            def stream_room_query(room_id: str, req: ExecuteRequest):
                """SSE stream of Room execution events."""
                def _generate():
                    for event in execute_in_room(
                        room_id,
                        req.query,
                        budget=req.budget,
                        strategy=req.strategy,
                        system_prompt=req.system_prompt,
                        privacy_required=req.privacy_required,
                        user_id=req.user_id,
                    ):
                        yield event.to_sse()

                return StreamingResponse(
                    _generate(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no",
                    },
                )

    # -- Room-level elimination management ----------------------------

    try:
        from .room_router_extension import (
            add_room_elimination,
            remove_room_elimination,
        )
    except ImportError:
        try:
            from room_router_extension import (  # type: ignore[no-redef]
                add_room_elimination,
                remove_room_elimination,
            )
        except ImportError:
            add_room_elimination = None  # type: ignore[assignment]
            remove_room_elimination = None  # type: ignore[assignment]

    class EliminationRequest(BaseModel):  # type: ignore[misc]
        model_id: str
        reason: str = ""

    if add_room_elimination is not None:
        @app.post("/room/{room_id}/eliminate")
        def eliminate_model(room_id: str, req: EliminationRequest):
            result = add_room_elimination(room_id, req.model_id, req.reason)
            if result is None:
                return {"success": False, "error": "Room not found"}
            return {"success": True, "data": result}

        @app.post("/room/{room_id}/readmit")
        def readmit_model(room_id: str, req: EliminationRequest):
            result = remove_room_elimination(room_id, req.model_id)
            if result is None:
                return {"success": False, "error": "Room not found"}
            return {"success": True, "data": result}
