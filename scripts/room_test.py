#!/usr/bin/env python3
"""
Praxis Room Pipeline Test Harness

Sends a query through the full pipeline (cognitive → stream) and outputs
a structured markdown trace for AI review.

Usage:
    python scripts/room_test.py "I need HIPAA-compliant writing tools under $50/mo"
    python scripts/room_test.py --room-id abc123 "follow up question here"
    python scripts/room_test.py --host http://localhost:8001 "test query"
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

INTERNAL_MARKERS = [
    "Awakening",
    "Self-introspection",
    "structural entropy",
    "consciousness score",
    "Enlightenment advisory",
    "Authorship advisory",
    "Ecosystem context",
    "Vertical intelligence",
    "Guardrails intelligence",
    "Architecture intelligence",
    "Resilience insight",
    "Metacognition",
]

TRACE_DIR = Path(__file__).resolve().parent / "traces"


def cognitive_step(host, query):
    """Step 1: POST /cognitive"""
    url = f"{host}/cognitive"
    payload = {"query": query, "profile_id": "default", "include_trace": True}
    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json=payload, timeout=90)
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return resp, elapsed_ms
    except requests.RequestException as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return e, elapsed_ms


def ensure_room(host, room_id=None):
    """Create or reuse a room."""
    if room_id:
        return room_id

    # Try to list existing rooms
    try:
        resp = requests.get(f"{host}/room", timeout=10)
        ct = resp.headers.get("content-type", "")
        if resp.ok and "application/json" in ct:
            body = resp.json()
            rooms = body.get("data", body) if isinstance(body, dict) else body
            if isinstance(rooms, list) and rooms:
                return rooms[-1].get("id") or rooms[-1].get("room_id")
    except Exception:
        pass

    # Create a new room
    resp = requests.post(
        f"{host}/room",
        json={"name": "Test Room", "operator_context": {}},
        timeout=10,
    )
    if resp.ok:
        body = resp.json()
        room = body.get("data", body) if isinstance(body, dict) else body
        if isinstance(room, dict):
            return room.get("id") or room.get("room_id")
    return None


def stream_step(host, room_id, query):
    """Step 2: POST /room/{id}/stream — capture SSE events."""
    url = f"{host}/room/{room_id}/stream"
    payload = {"query": query, "profile_id": "default"}
    events = []
    t0 = time.perf_counter()
    try:
        resp = requests.post(url, json=payload, stream=True, timeout=120)
        if not resp.ok:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return {"status": resp.status_code, "body": resp.text[:500]}, events, elapsed_ms

        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                raw = line[6:]
                try:
                    event = json.loads(raw)
                    events.append(event)
                except json.JSONDecodeError:
                    events.append({"_raw": raw, "_parse_error": True})

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"status": resp.status_code}, events, elapsed_ms
    except requests.RequestException as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"error": str(e)}, events, elapsed_ms


def detect_flags(cognitive_data, sse_events, artifacts):
    """Auto-detect known issues."""
    flags = []

    # RASP block
    if isinstance(cognitive_data, dict) and cognitive_data.get("error"):
        err = str(cognitive_data.get("error", ""))
        if "RASP" in err or "command_injec" in err:
            flags.append("⚠ RASP block detected in cognitive response")

    for ev in sse_events:
        ev_type = ev.get("type") or ev.get("event")
        if ev_type == "error":
            msg = str(ev.get("message", "") or ev.get("data", {}).get("message", "") or ev.get("error", ""))
            if "RASP" in msg or "command_injec" in msg:
                flags.append("⚠ RASP block detected in stream")

    # Stream errors
    for ev in sse_events:
        ev_type = ev.get("type") or ev.get("event")
        if ev_type == "error":
            msg = ev.get("message") or ev.get("data", {}).get("message", "unknown")
            flags.append(f"⚠ Error event in stream: {msg}")

    # 0 eliminated tools
    if isinstance(cognitive_data, dict):
        survivors = cognitive_data.get("tools_recommended") or cognitive_data.get("survivors") or []
        considered = cognitive_data.get("tools_considered", len(survivors))
        eliminated = considered - len(survivors)
        if considered > 0 and eliminated == 0:
            flags.append("⚠ 0 tools eliminated (possible bug)")

    # Empty narrative
    if isinstance(cognitive_data, dict):
        narrative = cognitive_data.get("narrative", "")
        if not narrative or not narrative.strip():
            flags.append("⚠ Empty narrative")

    # Internal language in artifacts
    for art in artifacts:
        content = art.get("content", "")
        found = [m for m in INTERNAL_MARKERS if m.lower() in content.lower()]
        if found:
            flags.append(f"⚠ Artifact contains internal markers: {', '.join(found)}")

    if not flags:
        flags.append("✓ All steps completed cleanly")

    return flags


def format_context(ctx):
    """Format context vector fields."""
    if not ctx or not isinstance(ctx, dict):
        return "  (none)\n"
    lines = []
    for key in ["task_type", "industry", "budget", "compliance", "skill_level"]:
        field = ctx.get(key, {})
        if isinstance(field, dict):
            val = field.get("value", "null")
            conf = field.get("confidence", "?")
            lines.append(f"- {key.replace('_', ' ').title()}: {val} (confidence: {conf})")
        else:
            lines.append(f"- {key.replace('_', ' ').title()}: {field}")
    return "\n".join(lines)


def build_trace(query, timestamp, room_id, cog_resp, cog_elapsed, cog_data,
                stream_meta, sse_events, stream_elapsed, flags):
    """Build the full markdown trace."""
    lines = []
    lines.append("# Praxis Room Trace")
    lines.append(f'**Query:** "{query}"')
    lines.append(f"**Timestamp:** {timestamp}")
    lines.append(f"**Room ID:** {room_id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Step 1: Cognitive ──
    lines.append("## Step 1 — Cognitive Pipeline (/cognitive)")
    if isinstance(cog_resp, Exception):
        lines.append(f"**Status:** ERROR — {cog_resp}")
    else:
        lines.append(f"**Status:** {cog_resp.status_code} {'OK' if cog_resp.ok else cog_resp.reason}")
    lines.append(f"**Elapsed:** {cog_elapsed}ms")
    lines.append("")

    if isinstance(cog_data, dict):
        # Context
        ctx = cog_data.get("context_vector")
        lines.append("### Context Extracted")
        lines.append(format_context(ctx))
        lines.append("")

        # Survivors
        survivors = cog_data.get("tools_recommended") or cog_data.get("survivors") or []
        considered = cog_data.get("tools_considered", len(survivors))
        eliminated_count = considered - len(survivors)

        lines.append(f"### Tools Evaluated: {considered}")
        lines.append(f"### Survivors: {len(survivors)}")
        for t in survivors:
            name = t.get("name", t.get("tool", "unknown"))
            score = t.get("fit_score")
            score_str = ""
            if score is not None:
                pct = int(score * 100 if score <= 1 else score)
                score_str = f" ({pct}%)"
            desc = (t.get("description") or "")[:100]
            lines.append(f"- {name}{score_str} — {desc}")
        lines.append("")

        # Eliminated
        eliminated = cog_data.get("eliminated") or []
        lines.append(f"### Eliminated: {eliminated_count}")
        for t in eliminated[:20]:
            if isinstance(t, dict):
                name = t.get("name", t.get("tool", "unknown"))
                reason = t.get("reason", t.get("elimination_reason", ""))
                lines.append(f"- {name} — {reason}")
            else:
                lines.append(f"- {t}")
        lines.append("")

        # Narrative
        narrative = cog_data.get("narrative", "")
        lines.append("### Narrative (raw):")
        lines.append(narrative if narrative else "(empty)")
        lines.append("")

        # Error
        if cog_data.get("error"):
            lines.append(f"### Error: {cog_data['error']}")
            lines.append("")
    else:
        lines.append("### Response could not be parsed as JSON")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Step 2: Stream ──
    lines.append("## Step 2 — Execution Stream (/room/{id}/stream)")
    lines.append(f"**Elapsed:** {stream_elapsed}ms")
    if stream_meta.get("error"):
        lines.append(f"**Error:** {stream_meta['error']}")
    elif stream_meta.get("body"):
        lines.append(f"**Status:** {stream_meta.get('status')}")
        lines.append(f"**Body:** {stream_meta['body'][:300]}")
    lines.append("")

    artifacts = []
    for i, ev in enumerate(sse_events, 1):
        ev_type = ev.get("type") or ev.get("event") or ev.get("_raw", "unknown")
        lines.append(f"### SSE Event {i}: {ev_type}")

        # Annotate routing_decision
        if ev_type == "routing_decision":
            data = ev.get("data", ev)
            strategy = data.get("strategy", "?")
            models = data.get("selected_models") or data.get("models") or data.get("model_ids") or []
            lines.append(f"- Strategy: {strategy}")
            if models:
                model_names = [m.get("model_id", m) if isinstance(m, dict) else m for m in models]
                lines.append(f"- Models: {model_names}")

        # Collect artifacts
        if ev_type == "artifact_saved":
            artifacts.append(ev)

        lines.append("```json")
        lines.append(json.dumps(ev, indent=2, default=str))
        lines.append("```")
        lines.append("")

    if not sse_events:
        lines.append("(no SSE events received)")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Step 3: Artifacts ──
    lines.append("## Step 3 — Artifacts Generated")
    if not artifacts:
        lines.append("(no artifacts)")
    for i, art in enumerate(artifacts, 1):
        title = art.get("title", art.get("id", f"Artifact {i}"))
        lines.append(f'### Artifact {i}: "{title}"')
        content = art.get("content", "")
        lines.append(content if content else "(empty content)")
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── Summary ──
    total_elapsed = cog_elapsed + stream_elapsed
    lines.append("## Summary")
    lines.append(f"- Total elapsed: {total_elapsed}ms")
    lines.append(f"- Cognitive elapsed: {cog_elapsed}ms")
    lines.append(f"- Stream elapsed: {stream_elapsed}ms")
    lines.append(f"- SSE events received: {len(sse_events)}")
    lines.append(f"- Artifacts saved: {len(artifacts)}")
    errors = [e for e in sse_events if e.get("type") == "error"]
    lines.append(f"- Errors: {'none' if not errors else json.dumps(errors, default=str)}")
    lines.append("")

    # ── Flags ──
    lines.append("## Flags for Review")
    for f in flags:
        lines.append(f"- {f}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Praxis Room pipeline test harness")
    parser.add_argument("query", help="The query to send through the pipeline")
    parser.add_argument("--host", default="http://localhost:8000",
                        help="Server base URL (default: http://localhost:8000)")
    parser.add_argument("--room-id", default=None, help="Reuse an existing room ID")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"=== Praxis Room Test Harness ===")
    print(f"Query: {args.query}")
    print(f"Host:  {args.host}")
    print()

    # Step 1: Cognitive
    print("> Step 1: POST /cognitive ...", end="", flush=True)
    cog_resp, cog_elapsed = cognitive_step(args.host, args.query)
    cog_data = {}
    if isinstance(cog_resp, Exception):
        print(f" ERROR ({cog_elapsed}ms): {cog_resp}")
    else:
        print(f" {cog_resp.status_code} ({cog_elapsed}ms)")
        ct = cog_resp.headers.get("content-type", "")
        if "application/json" in ct:
            cog_data = cog_resp.json()
        else:
            cog_data = {"error": f"Non-JSON response: {cog_resp.text[:200]}"}

    # Room
    print("> Resolving room ...", end="", flush=True)
    room_id = ensure_room(args.host, args.room_id)
    if room_id:
        print(f" {room_id}")
    else:
        print(" FAILED (continuing without stream)")

    # Step 2: Stream
    sse_events = []
    stream_elapsed = 0
    stream_meta = {}
    if room_id:
        print(f"> Step 2: POST /room/{room_id}/stream ...", end="", flush=True)
        stream_meta, sse_events, stream_elapsed = stream_step(args.host, room_id, args.query)
        print(f" {len(sse_events)} events ({stream_elapsed}ms)")
    else:
        print("> Step 2: Skipped (no room)")

    # Collect artifacts from SSE
    artifacts = [e for e in sse_events if (e.get("type") or e.get("event")) == "artifact_saved"]

    # Detect flags
    flags = detect_flags(cog_data, sse_events, artifacts)

    # Collect artifact content from SSE events
    artifact_events = [e for e in sse_events if (e.get("type") or e.get("event")) == "artifact_saved"]

    # Build trace
    trace = build_trace(
        args.query, timestamp, room_id or "(none)",
        cog_resp, cog_elapsed, cog_data,
        stream_meta, sse_events, stream_elapsed,
        flags,
    )

    # Save to file
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    trace_path = TRACE_DIR / f"trace_{file_ts}.md"
    trace_path.write_text(trace, encoding="utf-8")
    print("\n> Trace saved to:", str(trace_path))

    # Print to stdout
    print("\n" + "=" * 60)
    # Use utf-8 to handle box-drawing and emoji characters
    sys.stdout.buffer.write(trace.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()

    # Exit code based on flags
    has_issues = any(f.startswith("⚠") for f in flags)
    sys.exit(1 if has_issues else 0)


if __name__ == "__main__":
    main()
