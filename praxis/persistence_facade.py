"""Workflow-layer facade over persistence module for presentation safety boundaries."""

try:
    from .persistence import (
        get_connection,
        get_write_queue,
        pool_stats,
        upgrade_to_wal,
        diagnose,
    )
except Exception:
    from persistence import (  # type: ignore
        get_connection,
        get_write_queue,
        pool_stats,
        upgrade_to_wal,
        diagnose,
    )
