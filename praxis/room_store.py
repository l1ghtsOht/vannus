"""Persistent SQLite storage for Praxis Rooms.

Separate database (``room_data/rooms.db``) to prevent coupling with
the tool catalogue.  Follows the procedural pattern established by
``storage.py`` — no ORM, explicit ``try/finally conn.close()``.
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4


DB_DIR = Path(__file__).parent / "room_data"
DB_NAME = "rooms.db"


def db_path() -> Path:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_DIR / DB_NAME


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(val: Optional[str], default):
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        return default


# -------------------------------------------------------------------
# Schema
# -------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rooms (
    room_id          TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    operator_context TEXT NOT NULL DEFAULT '{}',
    journey_history  TEXT NOT NULL DEFAULT '[]',
    active_eliminations TEXT NOT NULL DEFAULT '{}',
    budget_cap_usd   REAL NOT NULL DEFAULT 50.0,
    current_spend_usd REAL NOT NULL DEFAULT 0.0,
    is_archived      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS room_sessions (
    session_id       TEXT PRIMARY KEY,
    room_id          TEXT NOT NULL,
    started_at       TEXT NOT NULL,
    ended_at         TEXT,
    active_journey_id TEXT,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS room_artifacts (
    artifact_id       TEXT PRIMARY KEY,
    room_id           TEXT NOT NULL,
    journey_id        TEXT NOT NULL,
    title             TEXT NOT NULL,
    content_type      TEXT NOT NULL,
    content           TEXT NOT NULL,
    version           INTEGER NOT NULL DEFAULT 1,
    parent_artifact_id TEXT,
    created_by_model  TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
"""


def init_db(path: Path = None) -> Path:
    """Create tables if they don't already exist."""
    p = path or db_path()
    conn = sqlite3.connect(p)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
    return p


# -------------------------------------------------------------------
# Room CRUD
# -------------------------------------------------------------------

def create_room(name: str, operator_context: Optional[Dict[str, Any]] = None,
                budget_cap_usd: float = 50.0, path: Path = None) -> Dict[str, Any]:
    p = path or db_path()
    init_db(p)
    now = _now()
    room = {
        "room_id": uuid4().hex,
        "name": name,
        "created_at": now,
        "updated_at": now,
        "operator_context": operator_context or {},
        "journey_history": [],
        "active_eliminations": {},
        "budget_cap_usd": budget_cap_usd,
        "current_spend_usd": 0.0,
        "is_archived": False,
    }
    conn = sqlite3.connect(p)
    try:
        conn.execute(
            "INSERT INTO rooms (room_id, name, created_at, updated_at, "
            "operator_context, journey_history, active_eliminations, "
            "budget_cap_usd, current_spend_usd, is_archived) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                room["room_id"], room["name"], room["created_at"],
                room["updated_at"],
                json.dumps(room["operator_context"]),
                json.dumps(room["journey_history"]),
                json.dumps(room["active_eliminations"]),
                room["budget_cap_usd"], room["current_spend_usd"],
                int(room["is_archived"]),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return room


def get_room(room_id: str, path: Path = None) -> Optional[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return None
    conn = sqlite3.connect(p)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM rooms WHERE room_id = ?",
                           (room_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return _row_to_room(row)


def list_rooms(include_archived: bool = False,
               path: Path = None) -> List[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return []
    conn = sqlite3.connect(p)
    try:
        conn.row_factory = sqlite3.Row
        if include_archived:
            rows = conn.execute(
                "SELECT * FROM rooms ORDER BY updated_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM rooms WHERE is_archived = 0 "
                "ORDER BY updated_at DESC").fetchall()
    finally:
        conn.close()
    return [_row_to_room(r) for r in rows]


def update_room(room_id: str, updates: Dict[str, Any],
                path: Path = None) -> Optional[Dict[str, Any]]:
    """Patch mutable fields on a Room.  Returns the updated dict or None."""
    allowed = {
        "name", "operator_context", "journey_history",
        "active_eliminations", "budget_cap_usd", "current_spend_usd",
        "is_archived",
    }
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        return get_room(room_id, path)

    p = path or db_path()
    if not p.exists():
        return None

    # Serialise complex fields
    for key in ("operator_context", "journey_history", "active_eliminations"):
        if key in filtered:
            filtered[key] = json.dumps(filtered[key])
    if "is_archived" in filtered:
        filtered["is_archived"] = int(filtered["is_archived"])

    filtered["updated_at"] = _now()
    set_clause = ", ".join(f"{k} = ?" for k in filtered)
    values = list(filtered.values()) + [room_id]

    conn = sqlite3.connect(p)
    try:
        conn.execute(f"UPDATE rooms SET {set_clause} WHERE room_id = ?",
                     values)
        conn.commit()
    finally:
        conn.close()
    return get_room(room_id, path)


def archive_room(room_id: str, path: Path = None) -> bool:
    return update_room(room_id, {"is_archived": True}, path) is not None


# -------------------------------------------------------------------
# Session CRUD
# -------------------------------------------------------------------

def create_session(room_id: str, path: Path = None) -> Dict[str, Any]:
    p = path or db_path()
    init_db(p)
    session = {
        "session_id": uuid4().hex,
        "room_id": room_id,
        "started_at": _now(),
        "ended_at": None,
        "active_journey_id": None,
    }
    conn = sqlite3.connect(p)
    try:
        conn.execute(
            "INSERT INTO room_sessions (session_id, room_id, started_at, "
            "ended_at, active_journey_id) VALUES (?, ?, ?, ?, ?)",
            (session["session_id"], session["room_id"],
             session["started_at"], session["ended_at"],
             session["active_journey_id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return session


def end_session(session_id: str, path: Path = None) -> Optional[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return None
    now = _now()
    conn = sqlite3.connect(p)
    try:
        conn.execute("UPDATE room_sessions SET ended_at = ? "
                     "WHERE session_id = ?", (now, session_id))
        conn.commit()
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM room_sessions WHERE session_id = ?",
                           (session_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def list_sessions(room_id: str, path: Path = None) -> List[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return []
    conn = sqlite3.connect(p)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM room_sessions WHERE room_id = ? "
            "ORDER BY started_at DESC", (room_id,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# -------------------------------------------------------------------
# Artifact CRUD
# -------------------------------------------------------------------

def create_artifact(room_id: str, journey_id: str, title: str,
                    content_type: str, content: str, created_by_model: str,
                    parent_artifact_id: Optional[str] = None,
                    version: int = 1,
                    path: Path = None) -> Dict[str, Any]:
    p = path or db_path()
    init_db(p)
    artifact = {
        "artifact_id": uuid4().hex,
        "room_id": room_id,
        "journey_id": journey_id,
        "title": title,
        "content_type": content_type,
        "content": content,
        "version": version,
        "parent_artifact_id": parent_artifact_id,
        "created_by_model": created_by_model,
        "created_at": _now(),
    }
    conn = sqlite3.connect(p)
    try:
        conn.execute(
            "INSERT INTO room_artifacts (artifact_id, room_id, journey_id, "
            "title, content_type, content, version, parent_artifact_id, "
            "created_by_model, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                artifact["artifact_id"], artifact["room_id"],
                artifact["journey_id"], artifact["title"],
                artifact["content_type"], artifact["content"],
                artifact["version"], artifact["parent_artifact_id"],
                artifact["created_by_model"], artifact["created_at"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return artifact


def list_artifacts(room_id: str, journey_id: Optional[str] = None,
                   path: Path = None) -> List[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return []
    conn = sqlite3.connect(p)
    try:
        conn.row_factory = sqlite3.Row
        if journey_id:
            rows = conn.execute(
                "SELECT * FROM room_artifacts WHERE room_id = ? "
                "AND journey_id = ? ORDER BY created_at DESC",
                (room_id, journey_id)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM room_artifacts WHERE room_id = ? "
                "ORDER BY created_at DESC", (room_id,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def get_artifact(artifact_id: str,
                 path: Path = None) -> Optional[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return None
    conn = sqlite3.connect(p)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM room_artifacts WHERE artifact_id = ?",
                           (artifact_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def _row_to_room(row) -> Dict[str, Any]:
    d = dict(row)
    d["operator_context"] = _parse_json(d.get("operator_context"), {})
    d["journey_history"] = _parse_json(d.get("journey_history"), [])
    d["active_eliminations"] = _parse_json(d.get("active_eliminations"), {})
    d["is_archived"] = bool(d.get("is_archived", 0))
    return d
