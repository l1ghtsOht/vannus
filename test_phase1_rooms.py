"""Quick Phase 1 CRUD round-trip test."""
import tempfile, os
from pathlib import Path
from praxis.room_store import (
    create_room, get_room, list_rooms, update_room, archive_room,
    create_session, end_session, list_sessions,
    create_artifact, list_artifacts, get_artifact,
)

p = Path(tempfile.mkdtemp()) / "test_rooms.db"

# Create room
r = create_room("Test Room", operator_context={"tier1": ["python"]}, budget_cap_usd=100.0, path=p)
print("Created:", r["room_id"][:8], "name=", r["name"])

# Get room
r2 = get_room(r["room_id"], path=p)
assert r2["name"] == "Test Room"
assert r2["operator_context"] == {"tier1": ["python"]}
print("Get: OK")

# List rooms
rooms = list_rooms(path=p)
assert len(rooms) == 1
print("List:", len(rooms), "room(s)")

# Update room
r3 = update_room(r["room_id"], {"name": "Updated Room", "budget_cap_usd": 200.0}, path=p)
assert r3["name"] == "Updated Room"
assert r3["budget_cap_usd"] == 200.0
print("Update: OK")

# Session
s = create_session(r["room_id"], path=p)
print("Session:", s["session_id"][:8])
sessions = list_sessions(r["room_id"], path=p)
assert len(sessions) == 1
s2 = end_session(s["session_id"], path=p)
assert s2["ended_at"] is not None
print("End session: OK")

# Artifact
a = create_artifact(r["room_id"], "j1", "Test Artifact", "text/plain", "body", "gpt-4o", path=p)
print("Artifact:", a["artifact_id"][:8])
arts = list_artifacts(r["room_id"], path=p)
assert len(arts) == 1
a2 = get_artifact(a["artifact_id"], path=p)
assert a2["title"] == "Test Artifact"
print("Artifact get: OK")

# Archive
ok = archive_room(r["room_id"], path=p)
assert ok
r4 = get_room(r["room_id"], path=p)
assert r4["is_archived"] is True
rooms_active = list_rooms(path=p)
assert len(rooms_active) == 0
rooms_all = list_rooms(include_archived=True, path=p)
assert len(rooms_all) == 1
print("Archive: OK")

# Cleanup
os.unlink(p)
print("ALL PHASE 1 TESTS PASSED")
