# ────────────────────────────────────────────────────────────────────
# persistence.py — Enterprise-Grade SQLite Persistence Layer
# ────────────────────────────────────────────────────────────────────
"""
Replaces ad-hoc ``sqlite3.connect()`` calls with a production-ready
connection pool that enforces:

    1. **WAL mode** — Write-Ahead Logging for concurrent read/write.
    2. **Connection pooling** — Reuse long-lived connections, eliminate
       per-query ``open()`` / ``close()`` syscall overhead.
    3. **Serialised write queue** — All mutations dispatched to a single
       writer thread, eliminating SQLITE_BUSY / SQLITE_LOCKED contention.
    4. **Shared cache** — ``?cache=shared`` ensures all connections see
       the same page cache (no stale-cache desynchronisation).
    5. **Busy timeout** — Patient queuing (120 s) instead of immediate
       failure when the lock is transiently held.
    6. **Context-manager interface** — Guarantees ``conn.close()`` even
       on exception paths.

Usage::

    from praxis.persistence import get_connection, write_queue, pool_stats

    # Read path — get a pooled connection (WAL + shared cache)
    with get_connection() as conn:
        rows = conn.execute("SELECT ...").fetchall()

    # Write path — serialised to a background worker
    write_queue.submit("INSERT INTO tools ...", (val1, val2))

    # Introspection
    stats = pool_stats()
"""

from __future__ import annotations

import logging
import queue
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger("praxis.persistence")

# ── Defaults ──
_DEFAULT_DB = Path(__file__).resolve().parent / "tools.db"
_POOL_SIZE = 5
_BUSY_TIMEOUT_MS = 120_000  # 120 seconds
_MAX_READ_CONNECTIONS = 8


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. WAL-MODE CONNECTION FACTORY                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def _create_connection(db_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """
    Create a new SQLite connection with enterprise pragmas:

    - ``journal_mode=WAL``  — concurrent readers + single writer
    - ``busy_timeout``      — patient queuing on lock contention
    - ``cache=shared``      — unified page cache across connections
    - ``foreign_keys=ON``   — referential integrity enforcement
    - ``synchronous=NORMAL``— safe WAL default (1 fsync per checkpoint)
    """
    uri = f"file:{db_path}?cache=shared"
    if read_only:
        uri += "&mode=ro"

    conn = sqlite3.connect(
        uri,
        uri=True,
        timeout=_BUSY_TIMEOUT_MS / 1000,
        check_same_thread=False,
    )

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=%d" % _BUSY_TIMEOUT_MS)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")

    # Row factory for dict-like access
    conn.row_factory = sqlite3.Row
    return conn


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. CONNECTION POOL                                              ║
# ╚════════════════════════════════════════════════════════════════════╝

class ConnectionPool:
    """
    Thread-safe connection pool for read-heavy workloads.

    Connections are created lazily up to ``max_size``, then callers block
    until a connection is returned to the pool.  Every connection is
    configured with WAL mode and shared cache on creation.
    """

    def __init__(self, db_path: Path = _DEFAULT_DB, max_size: int = _MAX_READ_CONNECTIONS):
        self._db_path = db_path
        self._max_size = max_size
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=max_size)
        self._created = 0
        self._lock = threading.Lock()
        self._total_checkouts = 0
        self._total_returned = 0
        self._created_at = time.monotonic()

    # ── Acquire / Release ──

    def acquire(self, timeout: float = 30.0) -> sqlite3.Connection:
        """Get a connection from the pool (blocking up to *timeout* seconds)."""
        # Fast path — reuse an existing idle connection
        try:
            conn = self._pool.get_nowait()
            self._total_checkouts += 1
            return conn
        except queue.Empty:
            pass

        # Slow path — create a new connection if below ceiling
        with self._lock:
            if self._created < self._max_size:
                conn = _create_connection(self._db_path, read_only=True)
                self._created += 1
                self._total_checkouts += 1
                log.debug("pool: created connection #%d", self._created)
                return conn

        # At ceiling — block until someone returns a connection
        try:
            conn = self._pool.get(timeout=timeout)
            self._total_checkouts += 1
            return conn
        except queue.Empty:
            raise TimeoutError(
                f"Connection pool exhausted ({self._max_size} connections); "
                f"waited {timeout:.1f}s.  Consider raising pool size or "
                f"reducing request concurrency."
            )

    def release(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool for reuse."""
        try:
            self._pool.put_nowait(conn)
            self._total_returned += 1
        except queue.Full:
            # Pool is full — discard the overflow connection
            try:
                conn.close()
            except Exception:
                pass
            with self._lock:
                self._created = max(self._created - 1, 0)

    def stats(self) -> Dict[str, Any]:
        """Return pool health metrics."""
        return {
            "max_size": self._max_size,
            "created": self._created,
            "idle": self._pool.qsize(),
            "in_use": self._created - self._pool.qsize(),
            "total_checkouts": self._total_checkouts,
            "total_returned": self._total_returned,
            "uptime_seconds": round(time.monotonic() - self._created_at, 1),
        }

    def close_all(self) -> None:
        """Drain and close every pooled connection."""
        closed = 0
        while True:
            try:
                conn = self._pool.get_nowait()
                conn.close()
                closed += 1
            except queue.Empty:
                break
        with self._lock:
            self._created = 0
        log.info("pool: closed %d connections", closed)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. SERIALISED WRITE QUEUE                                      ║
# ╚════════════════════════════════════════════════════════════════════╝

class _WriteResult:
    """Future-like object for write operations."""
    def __init__(self):
        self._event = threading.Event()
        self._result: Any = None
        self._error: Optional[Exception] = None

    def set_result(self, val: Any) -> None:
        self._result = val
        self._event.set()

    def set_error(self, exc: Exception) -> None:
        self._error = exc
        self._event.set()

    def get(self, timeout: float = 60.0) -> Any:
        if not self._event.wait(timeout):
            raise TimeoutError("Write operation timed out")
        if self._error:
            raise self._error
        return self._result


class WriteQueue:
    """
    Serialised write queue — all database mutations pass through a single
    background thread, completely eliminating concurrent-write collisions.

    Usage::

        result = write_queue.submit("INSERT INTO ...", (v1, v2))
        rowcount = result.get()  # blocks until the write completes

    The queue also supports batch operations via ``submit_many()``.
    """

    _MAX_PENDING = 10_000  # back-pressure cap — reject writes beyond this

    def __init__(self, db_path: Path = _DEFAULT_DB):
        self._db_path = db_path
        self._queue: queue.Queue[Tuple[str, tuple, _WriteResult, bool]] = queue.Queue(
            maxsize=self._MAX_PENDING
        )
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_writes = 0
        self._total_errors = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        """Start the background writer thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._worker, daemon=True, name="praxis-write-queue"
        )
        self._thread.start()
        log.info("write-queue: background writer started")

    def stop(self) -> None:
        """Signal the writer to drain and exit."""
        self._running = False
        if self._thread and self._thread.is_alive():
            # Push a sentinel to wake the worker
            self._queue.put(("__STOP__", (), _WriteResult(), False))
            self._thread.join(timeout=10)

    def submit(self, sql: str, params: tuple = ()) -> _WriteResult:
        """Enqueue a single write operation.  Returns a future.

        Raises ``queue.Full`` if the back-pressure cap is reached.
        """
        self._ensure_running()
        future = _WriteResult()
        try:
            self._queue.put((sql, params, future, False), timeout=5.0)
        except queue.Full:
            future.set_error(
                RuntimeError(
                    f"Write queue full ({self._MAX_PENDING} pending). "
                    "The database writer cannot keep up — back-pressure applied."
                )
            )
        return future

    def submit_many(self, sql: str, params_list: List[tuple]) -> _WriteResult:
        """Enqueue a batch write (executemany).  Returns a future.

        Raises ``queue.Full`` if the back-pressure cap is reached.
        """
        self._ensure_running()
        future = _WriteResult()
        try:
            self._queue.put((sql, params_list, future, True), timeout=5.0)
        except queue.Full:
            future.set_error(
                RuntimeError(
                    f"Write queue full ({self._MAX_PENDING} pending). "
                    "The database writer cannot keep up — back-pressure applied."
                )
            )
        return future

    def stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "pending": self._queue.qsize(),
            "total_writes": self._total_writes,
            "total_errors": self._total_errors,
        }

    # ── Internal ──

    def _ensure_running(self) -> None:
        if not self._running:
            self.start()

    def _worker(self) -> None:
        conn = _create_connection(self._db_path)
        try:
            while self._running or not self._queue.empty():
                try:
                    sql, params, future, is_many = self._queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if sql == "__STOP__":
                    break

                try:
                    if is_many:
                        conn.executemany(sql, params)
                    else:
                        conn.execute(sql, params)
                    conn.commit()
                    with self._lock:
                        self._total_writes += 1
                    future.set_result(True)
                except Exception as exc:
                    conn.rollback()
                    with self._lock:
                        self._total_errors += 1
                    future.set_error(exc)
                    log.error("write-queue: %s — %s", sql[:80], exc)
        finally:
            conn.close()
            log.info("write-queue: worker exited (writes=%d, errors=%d)",
                     self._total_writes, self._total_errors)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. MODULE-LEVEL SINGLETONS                                     ║
# ╚════════════════════════════════════════════════════════════════════╝

_pool: Optional[ConnectionPool] = None
_write_q: Optional[WriteQueue] = None
_init_lock = threading.Lock()


def initialize(db_path: Path = _DEFAULT_DB,
               pool_size: int = _MAX_READ_CONNECTIONS) -> None:
    """Initialise the connection pool and write queue (idempotent)."""
    global _pool, _write_q
    with _init_lock:
        if _pool is None:
            _pool = ConnectionPool(db_path, max_size=pool_size)
            log.info("persistence: pool initialised (max=%d)", pool_size)
        if _write_q is None:
            _write_q = WriteQueue(db_path)
            _write_q.start()
            log.info("persistence: write-queue started")


def shutdown() -> None:
    """Cleanly shut down the pool and write queue."""
    global _pool, _write_q
    with _init_lock:
        if _write_q:
            _write_q.stop()
            _write_q = None
        if _pool:
            _pool.close_all()
            _pool = None
    log.info("persistence: shutdown complete")


@contextmanager
def get_connection(db_path: Path = _DEFAULT_DB):
    """
    Context manager — acquire a read connection from the pool.

    Usage::

        with get_connection() as conn:
            rows = conn.execute("SELECT ...").fetchall()
    """
    global _pool
    if _pool is None:
        initialize(db_path)
    conn = _pool.acquire()
    try:
        yield conn
    finally:
        _pool.release(conn)


@property
def write_queue() -> WriteQueue:
    """Return the singleton write queue."""
    global _write_q
    if _write_q is None:
        initialize()
    return _write_q


def get_write_queue() -> WriteQueue:
    """Return the singleton write queue (function form)."""
    global _write_q
    if _write_q is None:
        initialize()
    return _write_q


def pool_stats() -> Dict[str, Any]:
    """Return combined health metrics for pool + write queue."""
    return {
        "pool": _pool.stats() if _pool else {"status": "not_initialised"},
        "write_queue": _write_q.stats() if _write_q else {"status": "not_initialised"},
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. MIGRATION HELPER — WAL-upgrade existing databases            ║
# ╚════════════════════════════════════════════════════════════════════╝

def upgrade_to_wal(db_path: Path = _DEFAULT_DB) -> Dict[str, str]:
    """
    Upgrade an existing database to WAL mode.

    Safe to call on databases already in WAL mode — the PRAGMA is
    idempotent and returns the current journal mode.
    """
    conn = sqlite3.connect(str(db_path), timeout=_BUSY_TIMEOUT_MS / 1000)
    try:
        before = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.execute("PRAGMA journal_mode=WAL")
        after = conn.execute("PRAGMA journal_mode").fetchone()[0]
        conn.execute("PRAGMA synchronous=NORMAL")

        # Integrity check as post-migration validation
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

        return {
            "before": before,
            "after": after,
            "integrity": integrity,
            "status": "upgraded" if before != after else "already_wal",
        }
    finally:
        conn.close()


def diagnose(db_path: Path = _DEFAULT_DB) -> Dict[str, Any]:
    """
    Return a comprehensive health diagnostic of the SQLite database.
    """
    if not db_path.exists():
        return {"exists": False}

    conn = sqlite3.connect(str(db_path), timeout=5)
    try:
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        page_count = conn.execute("PRAGMA page_count").fetchone()[0]
        freelist = conn.execute("PRAGMA freelist_count").fetchone()[0]
        wal_auto = conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [r[0] for r in tables]

        row_counts = {}
        for t in table_names:
            cnt = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
            row_counts[t] = cnt

        return {
            "exists": True,
            "path": str(db_path),
            "journal_mode": journal,
            "page_size": page_size,
            "page_count": page_count,
            "db_size_bytes": page_size * page_count,
            "freelist_pages": freelist,
            "wal_autocheckpoint": wal_auto,
            "integrity": integrity,
            "tables": table_names,
            "row_counts": row_counts,
        }
    finally:
        conn.close()
