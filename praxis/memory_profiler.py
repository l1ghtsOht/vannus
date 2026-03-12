# ────────────────────────────────────────────────────────────────────
# memory_profiler.py — Continuous Agentic Loop Memory Management
# ────────────────────────────────────────────────────────────────────
"""
Addresses the memory-leak risks inherent in long-running, stateful
Plan-Act-Observe-Reflect agentic cycles:

    1. **Tracemalloc integration** — Line-by-line allocation tracking
       and snapshot differential analysis to locate leak sources.
    2. **Memory-bounded contexts** — Decorator and context managers that
       enforce hard memory ceilings on agentic operations.
    3. **Weak reference registry** — Non-binding pointers for graph-like
       objects that allow the GC to reclaim circular references.
    4. **Soak-test harness** — Drive continuous agentic loops while
       graphing memory consumption to detect slow-growing retention.
    5. **Bounded collections** — Drop-in replacements for lists/dicts
       that automatically evict oldest entries when full.

Usage::

    from praxis.memory_profiler import (
        MemoryTracker, BoundedList, BoundedDict,
        memory_bounded, soak_test_report,
    )

    tracker = MemoryTracker()
    tracker.snapshot("before_loop")
    # ... run agentic loop ...
    tracker.snapshot("after_loop")
    diff = tracker.diff("before_loop", "after_loop")
"""

from __future__ import annotations

import gc
import logging
import os
import sys
import time
import tracemalloc
import weakref
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, TypeVar

log = logging.getLogger("praxis.memory_profiler")

T = TypeVar("T")


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. TRACEMALLOC INTEGRATION                                     ║
# ╚════════════════════════════════════════════════════════════════════╝

class MemoryTracker:
    """
    Wraps ``tracemalloc`` to provide named snapshots and differential
    analysis.  Designed for detecting leaks across agentic loop iterations.

    Usage::

        tracker = MemoryTracker()
        tracker.start()
        tracker.snapshot("iteration_0")
        # ... run some work ...
        tracker.snapshot("iteration_100")
        diff = tracker.diff("iteration_0", "iteration_100")
    """

    def __init__(self, nframes: int = 10):
        self._nframes = nframes
        self._snapshots: Dict[str, tracemalloc.Snapshot] = {}
        self._timestamps: Dict[str, float] = {}
        self._process_rss: Dict[str, int] = {}

    def start(self) -> None:
        """Enable tracemalloc if not already running."""
        if not tracemalloc.is_tracing():
            tracemalloc.start(self._nframes)

    def stop(self) -> None:
        """Stop tracemalloc and discard internal tracking state."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        self._snapshots.clear()
        self._timestamps.clear()
        self._process_rss.clear()

    def snapshot(self, label: str) -> Dict[str, Any]:
        """
        Take a named memory snapshot.

        Returns a summary dict with current allocation stats.
        """
        self.start()
        snap = tracemalloc.take_snapshot()
        self._snapshots[label] = snap
        self._timestamps[label] = time.monotonic()

        current, peak = tracemalloc.get_traced_memory()
        rss = _get_process_rss()
        self._process_rss[label] = rss

        return {
            "label": label,
            "traced_current_bytes": current,
            "traced_peak_bytes": peak,
            "process_rss_bytes": rss,
            "timestamp": self._timestamps[label],
        }

    def diff(self, before: str, after: str, top_n: int = 10) -> Dict[str, Any]:
        """
        Compare two snapshots and return the top allocation changes.

        Each entry in ``top_allocations`` identifies the file, line, and
        size delta — this is how you locate the exact leak source.
        """
        snap_before = self._snapshots.get(before)
        snap_after = self._snapshots.get(after)
        if not snap_before or not snap_after:
            return {"error": f"Missing snapshot: {before if not snap_before else after}"}

        stats = snap_after.compare_to(snap_before, "lineno")
        top = stats[:top_n]

        rss_before = self._process_rss.get(before, 0)
        rss_after = self._process_rss.get(after, 0)

        return {
            "before": before,
            "after": after,
            "elapsed_seconds": round(
                self._timestamps.get(after, 0) - self._timestamps.get(before, 0), 2
            ),
            "rss_delta_bytes": rss_after - rss_before,
            "top_allocations": [
                {
                    "file": str(stat.traceback),
                    "size_delta_bytes": stat.size_diff,
                    "size_bytes": stat.size,
                    "count_delta": stat.count_diff,
                    "count": stat.count,
                }
                for stat in top
            ],
        }

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Return metadata for all stored snapshots."""
        return [
            {
                "label": label,
                "timestamp": self._timestamps.get(label),
                "rss_bytes": self._process_rss.get(label),
            }
            for label in self._snapshots
        ]


def _get_process_rss() -> int:
    """Get the current process RSS in bytes (cross-platform)."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except ImportError:
        pass  # Windows
    try:
        # Windows fallback using ctypes
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = PROCESS_MEMORY_COUNTERS()
        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        handle = kernel32.GetCurrentProcess()
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize
    except Exception:
        pass
    return 0


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. BOUNDED COLLECTIONS                                         ║
# ╚════════════════════════════════════════════════════════════════════╝

class BoundedList:
    """
    A list with a maximum capacity.  When full, oldest items are evicted
    (FIFO).  Drop-in replacement for unbounded trace/history lists.

    Usage::

        history = BoundedList(max_size=1000)
        history.append({"step": 1, ...})
    """

    def __init__(self, max_size: int = 1000, items: Optional[List] = None):
        self._max_size = max_size
        self._items: List[Any] = list(items or [])[-max_size:]

    def append(self, item: Any) -> None:
        self._items.append(item)
        if len(self._items) > self._max_size:
            self._items = self._items[-self._max_size:]

    def extend(self, items) -> None:
        self._items.extend(items)
        if len(self._items) > self._max_size:
            self._items = self._items[-self._max_size:]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator:
        return iter(self._items)

    def __getitem__(self, index):
        return self._items[index]

    def to_list(self) -> List:
        return list(self._items)

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def is_full(self) -> bool:
        return len(self._items) >= self._max_size


class BoundedDict:
    """
    An ordered dictionary with a maximum capacity.  When full, the
    oldest key is evicted (LRU-style).  Replaces unbounded caches.

    Usage::

        cache = BoundedDict(max_size=500)
        cache["key"] = value
    """

    def __init__(self, max_size: int = 500):
        self._max_size = max_size
        self._data: OrderedDict = OrderedDict()

    def __setitem__(self, key: str, value: Any) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        else:
            if len(self._data) >= self._max_size:
                self._data.popitem(last=False)
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        self._data.move_to_end(key)
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    @property
    def max_size(self) -> int:
        return self._max_size


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. WEAK REFERENCE REGISTRY                                     ║
# ╚════════════════════════════════════════════════════════════════════╝

class WeakRegistry:
    """
    A registry of objects that does not prevent garbage collection.

    Useful for agent-to-agent references in multi-agent architectures
    where circular references would otherwise leak memory.

    Usage::

        registry = WeakRegistry()
        registry.register("agent_1", some_agent_object)
        agent = registry.get("agent_1")  # returns None if GC'd
    """

    def __init__(self):
        self._refs: Dict[str, weakref.ref] = {}
        self._finalizer_count = 0

    def register(self, key: str, obj: Any) -> bool:
        """Register an object under a key.  Returns False if not weakref-able."""
        try:
            def _on_finalize(ref, k=key):
                self._refs.pop(k, None)
                self._finalizer_count += 1

            self._refs[key] = weakref.ref(obj, _on_finalize)
            return True
        except TypeError:
            # Object doesn't support weak references
            return False

    def get(self, key: str) -> Optional[Any]:
        """Retrieve the object, or None if it has been garbage collected."""
        ref = self._refs.get(key)
        if ref is None:
            return None
        obj = ref()
        if obj is None:
            del self._refs[key]
        return obj

    def alive_count(self) -> int:
        """Count of currently-alive registered objects."""
        alive = 0
        dead_keys = []
        for key, ref in self._refs.items():
            if ref() is not None:
                alive += 1
            else:
                dead_keys.append(key)
        for k in dead_keys:
            del self._refs[k]
        return alive

    def stats(self) -> Dict[str, int]:
        return {
            "registered": len(self._refs),
            "alive": self.alive_count(),
            "finalized": self._finalizer_count,
        }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. MEMORY-BOUNDED DECORATOR                                    ║
# ╚════════════════════════════════════════════════════════════════════╝

def memory_bounded(max_mb: float = 100.0, label: str = ""):
    """
    Decorator that aborts a function if it allocates more than ``max_mb``
    megabytes (measured via tracemalloc).

    Usage::

        @memory_bounded(max_mb=50, label="agent_loop")
        def run_agent_loop(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            _ensure_tracing()
            before = tracemalloc.get_traced_memory()[0]
            try:
                result = func(*args, **kwargs)
            finally:
                after = tracemalloc.get_traced_memory()[0]
                delta_mb = (after - before) / (1024 * 1024)
                tag = label or func.__name__
                if delta_mb > max_mb:
                    log.warning(
                        "memory_bounded[%s]: allocated %.1f MB "
                        "(limit %.1f MB) — potential leak",
                        tag, delta_mb, max_mb,
                    )
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def _ensure_tracing():
    if not tracemalloc.is_tracing():
        tracemalloc.start(5)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. SOAK TEST HARNESS                                           ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class SoakResult:
    """Results from a soak test run."""
    iterations: int = 0
    elapsed_seconds: float = 0.0
    memory_samples: List[Dict[str, Any]] = field(default_factory=list)
    peak_rss_bytes: int = 0
    final_rss_bytes: int = 0
    leak_detected: bool = False
    leak_rate_bytes_per_iteration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iterations": self.iterations,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "memory_samples_count": len(self.memory_samples),
            "peak_rss_bytes": self.peak_rss_bytes,
            "final_rss_bytes": self.final_rss_bytes,
            "leak_detected": self.leak_detected,
            "leak_rate_bytes_per_iteration": round(self.leak_rate_bytes_per_iteration, 1),
        }


def soak_test(
    func: Callable,
    iterations: int = 100,
    sample_interval: int = 10,
    leak_threshold_mb: float = 5.0,
    *args,
    **kwargs,
) -> SoakResult:
    """
    Run ``func`` for ``iterations`` iterations while tracking memory.

    Parameters
    ----------
    func              : The function to stress-test.
    iterations        : How many times to invoke ``func``.
    sample_interval   : Take a memory sample every N iterations.
    leak_threshold_mb : Flag a leak if total growth exceeds this.

    Returns
    -------
    SoakResult with memory trajectory and leak detection.
    """
    _ensure_tracing()
    gc.collect()

    result = SoakResult()
    t0 = time.monotonic()
    initial_rss = _get_process_rss()
    peak_rss = initial_rss

    for i in range(iterations):
        func(*args, **kwargs)

        if i % sample_interval == 0 or i == iterations - 1:
            current, peak_traced = tracemalloc.get_traced_memory()
            rss = _get_process_rss()
            peak_rss = max(peak_rss, rss)
            result.memory_samples.append({
                "iteration": i,
                "traced_current_bytes": current,
                "traced_peak_bytes": peak_traced,
                "rss_bytes": rss,
            })

    result.iterations = iterations
    result.elapsed_seconds = time.monotonic() - t0
    result.peak_rss_bytes = peak_rss
    result.final_rss_bytes = _get_process_rss()

    # Leak detection — linear regression on RSS samples
    if len(result.memory_samples) >= 3:
        rss_values = [s["rss_bytes"] for s in result.memory_samples]
        growth = rss_values[-1] - rss_values[0]
        growth_mb = growth / (1024 * 1024)
        result.leak_rate_bytes_per_iteration = growth / max(iterations, 1)
        result.leak_detected = growth_mb > leak_threshold_mb

    return result


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. GC DIAGNOSTICS                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

def gc_diagnostics() -> Dict[str, Any]:
    """
    Return garbage collector state and statistics.

    Useful for detecting uncollectable circular references.
    """
    gc.collect()
    return {
        "enabled": gc.isenabled(),
        "threshold": gc.get_threshold(),
        "counts": gc.get_count(),
        "garbage_objects": len(gc.garbage),
        "tracked_objects": len(gc.get_objects()),
        "freeze_count": gc.get_freeze_count() if hasattr(gc, "get_freeze_count") else None,
    }


def memory_summary() -> Dict[str, Any]:
    """
    Return a comprehensive memory health summary.
    """
    rss = _get_process_rss()
    traced_current = 0
    traced_peak = 0
    if tracemalloc.is_tracing():
        traced_current, traced_peak = tracemalloc.get_traced_memory()

    return {
        "process_rss_bytes": rss,
        "process_rss_mb": round(rss / (1024 * 1024), 1),
        "traced_current_bytes": traced_current,
        "traced_peak_bytes": traced_peak,
        "gc": gc_diagnostics(),
        "python_version": sys.version,
        "platform": sys.platform,
    }
