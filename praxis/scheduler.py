# ────────────────────────────────────────────────────────────────────
# scheduler.py — Lightweight Background Task Scheduler
# ────────────────────────────────────────────────────────────────────
"""
Pure-stdlib scheduler using threading.Timer. No Celery, no Redis.

Usage:
    scheduler = BackgroundScheduler()
    scheduler.schedule("trust_decay", run_trust_sweep, interval_seconds=259200)
    scheduler.start()
    # ...
    scheduler.stop()
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

log = logging.getLogger("praxis.scheduler")


@dataclass
class _TaskState:
    name: str
    fn: Callable
    interval: float
    run_immediately: bool = False
    _timer: Optional[threading.Timer] = field(default=None, repr=False)
    _running: bool = False
    _paused: bool = False
    run_count: int = 0
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    last_error: Optional[str] = None
    last_duration_ms: float = 0.0


class BackgroundScheduler:
    """Thread-based periodic task scheduler."""

    def __init__(self):
        self._tasks: Dict[str, _TaskState] = {}
        self._started = False
        self._lock = threading.Lock()

    def schedule(
        self,
        name: str,
        fn: Callable,
        interval_seconds: float,
        run_immediately: bool = False,
    ) -> None:
        """Register a task to run on a fixed interval."""
        with self._lock:
            self._tasks[name] = _TaskState(
                name=name,
                fn=fn,
                interval=interval_seconds,
                run_immediately=run_immediately,
            )
        log.info("Scheduled task '%s' every %.0fs", name, interval_seconds)

    def start(self) -> None:
        """Start all scheduled tasks."""
        with self._lock:
            if self._started:
                return
            self._started = True
            for task in self._tasks.values():
                self._schedule_next(task)
        log.info("Scheduler started with %d tasks", len(self._tasks))

    def stop(self) -> None:
        """Cancel all pending timers (clean shutdown)."""
        with self._lock:
            self._started = False
            for task in self._tasks.values():
                if task._timer:
                    task._timer.cancel()
                    task._timer = None
                task._running = False
        log.info("Scheduler stopped")

    def _schedule_next(self, task: _TaskState) -> None:
        """Schedule the next run of a task."""
        if not self._started or task._paused:
            return

        delay = 0.0 if (task.run_immediately and task.run_count == 0) else task.interval
        task.next_run = time.time() + delay

        def _run():
            if not self._started or task._paused:
                return
            task._running = True
            task.last_run = time.time()
            t0 = time.monotonic()
            try:
                task.fn()
                task.last_error = None
            except Exception as exc:
                task.last_error = str(exc)[:200]
                log.error("Task '%s' failed: %s", task.name, exc)
            finally:
                task.last_duration_ms = (time.monotonic() - t0) * 1000
                task.run_count += 1
                task._running = False
                if self._started and not task._paused:
                    self._schedule_next(task)

        task._timer = threading.Timer(delay, _run)
        task._timer.daemon = True
        task._timer.start()

    def trigger(self, name: str) -> bool:
        """Manually trigger a task immediately. Returns True if found."""
        with self._lock:
            task = self._tasks.get(name)
            if not task:
                return False
            if task._timer:
                task._timer.cancel()

        # Run in a thread
        def _run_now():
            task._running = True
            task.last_run = time.time()
            t0 = time.monotonic()
            try:
                task.fn()
                task.last_error = None
            except Exception as exc:
                task.last_error = str(exc)[:200]
                log.error("Task '%s' trigger failed: %s", name, exc)
            finally:
                task.last_duration_ms = (time.monotonic() - t0) * 1000
                task.run_count += 1
                task._running = False
                if self._started and not task._paused:
                    self._schedule_next(task)

        t = threading.Thread(target=_run_now, daemon=True)
        t.start()
        return True

    def pause(self, name: str) -> bool:
        with self._lock:
            task = self._tasks.get(name)
            if not task:
                return False
            task._paused = True
            if task._timer:
                task._timer.cancel()
            return True

    def resume(self, name: str) -> bool:
        with self._lock:
            task = self._tasks.get(name)
            if not task:
                return False
            task._paused = False
            if self._started:
                self._schedule_next(task)
            return True

    def status(self) -> Dict[str, Dict]:
        """Return status of all tasks."""
        now = time.time()
        result = {}
        for name, task in self._tasks.items():
            result[name] = {
                "interval_seconds": task.interval,
                "run_count": task.run_count,
                "last_run": task.last_run,
                "next_run": task.next_run,
                "last_error": task.last_error,
                "last_duration_ms": round(task.last_duration_ms, 1),
                "running": task._running,
                "paused": task._paused,
                "seconds_until_next": round(task.next_run - now, 0) if task.next_run and task.next_run > now else 0,
            }
        return result


# ── Singleton ──
_scheduler = BackgroundScheduler()


def get_scheduler() -> BackgroundScheduler:
    return _scheduler


def setup_default_tasks() -> None:
    """Register default scheduled tasks (trust decay, journey corrections)."""
    import os
    sweep_interval = int(os.environ.get("PRAXIS_TRUST_SWEEP_INTERVAL", "259200"))  # 72h default

    try:
        from .trust_decay import run_trust_sweep
        _scheduler.schedule("trust_decay", lambda: run_trust_sweep(), sweep_interval)
    except ImportError:
        try:
            from trust_decay import run_trust_sweep
            _scheduler.schedule("trust_decay", lambda: run_trust_sweep(), sweep_interval)
        except ImportError:
            log.info("trust_decay not available — skipping sweep schedule")

    try:
        from .journey import get_oracle
        _scheduler.schedule(
            "journey_corrections",
            lambda: get_oracle().apply_drift_corrections(),
            sweep_interval,
        )
    except ImportError:
        try:
            from journey import get_oracle
            _scheduler.schedule("journey_corrections", lambda: get_oracle().apply_drift_corrections(), sweep_interval)
        except ImportError:
            log.info("journey not available — skipping corrections schedule")
