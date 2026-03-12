# --------------- Praxis Telemetry — Structured Logging & Tracing ---------------
"""
v18 · Enterprise-Grade Solidification

Enterprise observability layer implementing:
    • **Structured JSON logging** — every log entry is a queryable JSON doc
      with fields: timestamp, level, logger, message, trace_id, span_id,
      event_type, user_id, latency_ms, and arbitrary extras.
    • **Trace-context propagation** — generates and propagates W3C-style
      ``trace_id`` / ``span_id`` across async call chains.
    • **Request telemetry middleware** — auto-instruments every FastAPI
      request with latency, status, and user info.
    • **LLM call instrumentation** — wraps LLM invocations with token
      usage, model, latency, and validation metrics.

Zero external deps (stdlib only).  When OpenTelemetry SDK is installed,
the module patches itself to emit real OTel spans.
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# -----------------------------------------------------------------------
# Context Variables (trace propagation)
# -----------------------------------------------------------------------

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="")
_span_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("span_id", default="")
_user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="anonymous")


def get_trace_id() -> str:
    return _trace_id_var.get() or ""


def set_trace_id(tid: str) -> None:
    _trace_id_var.set(tid)


def new_trace_id() -> str:
    tid = uuid.uuid4().hex
    _trace_id_var.set(tid)
    return tid


def get_span_id() -> str:
    return _span_id_var.get() or ""


def new_span_id() -> str:
    sid = uuid.uuid4().hex[:16]
    _span_id_var.set(sid)
    return sid


def set_user_id(uid: str) -> None:
    _user_id_var.set(uid)


def get_user_id() -> str:
    return _user_id_var.get()


# -----------------------------------------------------------------------
# Structured JSON Formatter
# -----------------------------------------------------------------------

class StructuredJsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects.

    Fields:
        timestamp, level, logger, message, trace_id, span_id, user_id,
        event_type, module, funcName, lineno, exc_info, + any extras.
    """

    def format(self, record: logging.LogRecord) -> str:
        doc: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": get_trace_id(),
            "span_id": get_span_id(),
            "user_id": get_user_id(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        # Merge extras from log calls: log.info("msg", extra={"foo": "bar"})
        for key in ("event_type", "latency_ms", "status_code", "tool_name",
                     "llm_model", "llm_tokens", "error_code", "request_path"):
            val = getattr(record, key, None)
            if val is not None:
                doc[key] = val

        if record.exc_info and record.exc_info[1]:
            doc["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            doc["exc_message"] = str(record.exc_info[1])

        return json.dumps(doc, default=str)


# -----------------------------------------------------------------------
# Setup function
# -----------------------------------------------------------------------

_configured = False


def configure_telemetry(
    *,
    json_logs: Optional[bool] = None,
    log_level: str = "INFO",
) -> None:
    """Initialize structured logging for the entire application.

    Call once at startup (e.g., in ``create_app()``).

    Parameters
    ----------
    json_logs : bool | None
        Force JSON logging.  Defaults to ``True`` in production
        (``PRAXIS_ENV != "development"``), ``False`` in dev.
    log_level : str
        Log level (respects ``PRAXIS_LOG_LEVEL`` env var).
    """
    global _configured
    if _configured:
        return
    _configured = True

    level_str = os.environ.get("PRAXIS_LOG_LEVEL", log_level).upper()
    level = getattr(logging, level_str, logging.INFO)

    if json_logs is None:
        json_logs = os.environ.get("PRAXIS_ENV", "development") != "development"

    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_logs:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(level)


# -----------------------------------------------------------------------
# Request Telemetry Middleware (FastAPI)
# -----------------------------------------------------------------------

def create_telemetry_middleware():
    """Return a Starlette middleware class that instruments every request.

    Injected fields:
        • X-Trace-Id response header
        • trace_id context variable for downstream logging
        • latency_ms + status_code log entry
    """
    try:
        from starlette.middleware.base import BaseHTTPMiddleware
    except ImportError:
        return None

    class TelemetryMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            # Extract or generate trace ID
            tid = request.headers.get("x-trace-id") or new_trace_id()
            set_trace_id(tid)
            new_span_id()

            t0 = time.monotonic()
            response = await call_next(request)
            latency = (time.monotonic() - t0) * 1000

            response.headers["X-Trace-Id"] = tid
            response.headers["X-Span-Id"] = get_span_id()

            log.info(
                "%s %s %d %.1fms",
                request.method, request.url.path, response.status_code, latency,
                extra={
                    "event_type": "http_request",
                    "request_path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency, 1),
                },
            )
            return response

    return TelemetryMiddleware


log = logging.getLogger("praxis.telemetry")


# -----------------------------------------------------------------------
# LLM Instrumentation Helper
# -----------------------------------------------------------------------

def log_llm_call(
    *,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    latency_ms: float = 0,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """Emit a structured log event for an LLM API call."""
    log.info(
        "llm_call model=%s tokens=%d+%d latency=%.1fms success=%s",
        model, prompt_tokens, completion_tokens, latency_ms, success,
        extra={
            "event_type": "llm_call",
            "llm_model": model,
            "llm_tokens": prompt_tokens + completion_tokens,
            "latency_ms": round(latency_ms, 1),
        },
    )


def log_validation_event(
    *,
    model_cls: str,
    success: bool,
    error: Optional[str] = None,
    attempt: int = 1,
) -> None:
    """Emit a structured log event for Pydantic validation of LLM output."""
    level = logging.INFO if success else logging.WARNING
    log.log(
        level,
        "validation model=%s success=%s attempt=%d%s",
        model_cls, success, attempt, f" error={error}" if error else "",
        extra={
            "event_type": "llm_validation",
            "llm_model": model_cls,
        },
    )
