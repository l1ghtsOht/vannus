# ────────────────────────────────────────────────────────────────────
# ws.py — WebSocket Broadcast Hub
# ────────────────────────────────────────────────────────────────────
"""
Lightweight pub/sub hub for real-time dashboard updates.

Channels: trust_decay, journey, pipeline, scheduler, provider_health

Usage:
    hub = BroadcastHub()
    hub.publish("trust_decay", {"event": "sweep_complete", ...})

The publish() method is sync-safe — callable from background threads.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Dict, Optional, Set

log = logging.getLogger("praxis.ws")

try:
    from fastapi import WebSocket
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False
    WebSocket = Any  # type: ignore


CHANNELS = ("trust_decay", "journey", "pipeline", "scheduler", "provider_health")


class BroadcastHub:
    """Thread-safe WebSocket broadcast hub."""

    def __init__(self):
        self._channels: Dict[str, Set] = {ch: set() for ch in CHANNELS}
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the async event loop for sync→async bridging."""
        self._loop = loop

    async def subscribe(self, channel: str, ws) -> None:
        """Add a WebSocket to a channel."""
        if channel not in self._channels:
            self._channels[channel] = set()
        with self._lock:
            self._channels[channel].add(ws)
        log.debug("WS subscribed to %s (%d total)", channel, len(self._channels[channel]))

    async def unsubscribe(self, channel: str, ws) -> None:
        """Remove a WebSocket from a channel."""
        with self._lock:
            self._channels.get(channel, set()).discard(ws)

    def publish(self, channel: str, data: dict) -> None:
        """Publish data to all subscribers (sync-safe, callable from any thread).

        If no subscribers or no event loop, this is a no-op.
        """
        subscribers = self._channels.get(channel, set())
        if not subscribers:
            return

        message = json.dumps(data)

        if self._loop and self._loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast(channel, message), self._loop
                )
            except Exception:
                pass
        else:
            # Fallback: try to broadcast directly if we're in an async context
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._broadcast(channel, message))
            except RuntimeError:
                pass  # No event loop — silently skip

    async def _broadcast(self, channel: str, message: str) -> None:
        """Internal async broadcast — handles disconnected clients."""
        dead = []
        with self._lock:
            subscribers = list(self._channels.get(channel, set()))

        for ws in subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        if dead:
            with self._lock:
                for ws in dead:
                    self._channels.get(channel, set()).discard(ws)

    def status(self) -> Dict[str, int]:
        """Return channel names → subscriber counts."""
        return {ch: len(subs) for ch, subs in self._channels.items()}


# ── Singleton ──
_hub = BroadcastHub()


def get_hub() -> BroadcastHub:
    return _hub
