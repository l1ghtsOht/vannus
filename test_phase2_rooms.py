"""Phase 2 integration test — room routing, orchestration, SSE events."""
import tempfile, os, json
from pathlib import Path
from praxis.room_store import create_room, get_room
from praxis.room_router_extension import (
    route_for_room, add_room_elimination, remove_room_elimination, record_spend,
)
from praxis.room_orchestrator import (
    execute_in_room, execute_in_room_sync, EventType, RoomEvent,
)

# Use a temp DB
_TMPDIR = tempfile.mkdtemp()
os.environ["PRAXIS_ROOM_DB"] = str(Path(_TMPDIR) / "test.db")  # not used directly but set

# --- Test 1: Room-scoped routing ---
from praxis import room_store
_orig = room_store.db_path
_tmp_db = Path(_TMPDIR) / "test_rooms.db"
room_store.db_path = lambda: (room_store.DB_DIR.mkdir(parents=True, exist_ok=True) or _tmp_db) or _tmp_db

r = create_room("Router Test Room", budget_cap_usd=10.0)
rid = r["room_id"]
print(f"Room created: {rid[:8]}")

# Route a query for the room
decision = route_for_room("Compare Python web frameworks", room_id=rid, budget="medium")
print(f"Routing strategy: {decision.inner.strategy.value}")
print(f"Selected models: {len(decision.inner.selected_models)}")
print(f"Eliminated: {len(decision.inner.eliminated)}")
print(f"Scope: {decision.scope}")
assert decision.room_id == rid
assert decision.remaining_budget_usd == 10.0
print("Routing: OK")

# --- Test 2: Add room elimination ---
result = add_room_elimination(rid, "fake-model-1", "Not trusted")
assert result is not None
room = get_room(rid)
assert "fake-model-1" in room["active_eliminations"]
print("Elimination added: OK")

# --- Test 3: Remove room elimination ---
result = remove_room_elimination(rid, "fake-model-1")
room = get_room(rid)
assert "fake-model-1" not in room["active_eliminations"]
print("Elimination removed: OK")

# --- Test 4: Record spend ---
record_spend(rid, 2.50)
room = get_room(rid)
assert room["current_spend_usd"] == 2.50
record_spend(rid, 1.25)
room = get_room(rid)
assert room["current_spend_usd"] == 3.75
print("Spend tracking: OK")

# --- Test 5: Orchestrator event stream ---
events = execute_in_room_sync(rid, "What is FastAPI?")
event_types = [e["event"] for e in events]
print(f"Events generated: {len(events)}")
print(f"Event types: {event_types}")

assert "session_start" in event_types
assert "context_extracted" in event_types
assert "routing_decision" in event_types
assert "session_end" in event_types
print("Orchestrator stream: OK")

# --- Test 6: SSE serialisation ---
for ev in execute_in_room(rid, "Test SSE"):
    sse_line = ev.to_sse()
    assert sse_line.startswith("event: ")
    assert "data: " in sse_line
    # Verify JSON payload is parseable
    data_line = sse_line.split("data: ", 1)[1].strip()
    parsed = json.loads(data_line)
    assert "event" in parsed
    assert "room_id" in parsed
    break  # just test the first event
print("SSE format: OK")

# Cleanup
import shutil
shutil.rmtree(_TMPDIR, ignore_errors=True)
# Reset db_path
room_store.db_path = _orig

print("\nALL PHASE 2 TESTS PASSED")
