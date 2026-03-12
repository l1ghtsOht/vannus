# ────────────────────────────────────────────────────────────────────
# observability.py — OpenTelemetry-style Tracing, Chain-of-Thought
#                    Parsing, and Interactive Reasoning Trees
# ────────────────────────────────────────────────────────────────────
"""
Implements the AI Observability layer for the Praxis enterprise
platform (Blueprint §6):

1. **Distributed Tracing** — lightweight spans modeled on OTEL
   semantics, capturing prompt → tool → response lifecycles.

2. **Chain-of-Thought Parser** — takes raw, verbose LLM reasoning
   traces and reconstructs them as hierarchical topic trees for
   interactive drill-down.

3. **Reasoning Intervention** — supports editing model assumptions
   mid-chain, recording the edit, and resuming.

4. **Telemetry Aggregation** — latency histograms, token budgets,
   error-rate windows.

All functions are pure-Python with no external OTEL dependency.
"""

from __future__ import annotations

import re
import time
import uuid
import hashlib
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. DISTRIBUTED TRACING — Lightweight Span Model                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class Span:
    """
    A single unit of work in the agent execution lifecycle.
    Models an OTEL-compatible span without requiring the SDK.
    """
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str = ""
    parent_span_id: Optional[str] = None
    operation: str = ""               # "llm_call", "tool_invoke", "search", "guardrail"
    agent_id: str = ""
    status: str = "in_progress"       # "in_progress", "ok", "error"
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "agent_id": self.agent_id,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 2),
            "attributes": self.attributes,
            "events": self.events,
        }


@dataclass
class Trace:
    """A collection of spans forming a complete execution trace."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32])
    root_span: Optional[Span] = None
    spans: List[Span] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created: float = field(default_factory=time.time)

    def add_span(self, span: Span) -> Span:
        span.trace_id = self.trace_id
        self.spans.append(span)
        if span.parent_span_id is None:
            self.root_span = span
        return span

    def total_duration_ms(self) -> float:
        if not self.spans:
            return 0.0
        start = min(s.start_time for s in self.spans)
        end = max(s.end_time or s.start_time for s in self.spans)
        return (end - start) * 1000

    def total_tokens(self) -> int:
        return sum(s.attributes.get("tokens", 0) for s in self.spans)

    def error_spans(self) -> List[Span]:
        return [s for s in self.spans if s.status == "error"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_count": len(self.spans),
            "total_duration_ms": round(self.total_duration_ms(), 2),
            "total_tokens": self.total_tokens(),
            "error_count": len(self.error_spans()),
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class TraceCollector:
    """Thread-safe trace collection and retrieval."""

    MAX_TRACES = 1000

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._traces: Dict[str, Trace] = {}
        self._order: List[str] = []

    def create_trace(self, metadata: Optional[Dict[str, Any]] = None) -> Trace:
        trace = Trace(metadata=metadata or {})
        with self._lock:
            self._traces[trace.trace_id] = trace
            self._order.append(trace.trace_id)
            # Evict oldest
            while len(self._order) > self.MAX_TRACES:
                old_id = self._order.pop(0)
                self._traces.pop(old_id, None)
        return trace

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            trace = self._traces.get(trace_id)
            return trace.to_dict() if trace else None

    def list_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            recent = list(self._traces.values())[-limit:]
            return [t.to_dict() for t in reversed(recent)]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total_spans = sum(len(t.spans) for t in self._traces.values())
            total_errors = sum(len(t.error_spans()) for t in self._traces.values())
            total_tokens = sum(t.total_tokens() for t in self._traces.values())
            durations = [t.total_duration_ms() for t in self._traces.values() if t.spans]
            return {
                "total_traces": len(self._traces),
                "total_spans": total_spans,
                "total_errors": total_errors,
                "total_tokens": total_tokens,
                "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0.0,
                "max_capacity": self.MAX_TRACES,
            }


# Global singleton
_collector: Optional[TraceCollector] = None
_coll_lock = threading.Lock()


def get_collector() -> TraceCollector:
    global _collector
    with _coll_lock:
        if _collector is None:
            _collector = TraceCollector()
        return _collector


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. CHAIN-OF-THOUGHT PARSER                                      ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class ReasoningNode:
    """A node in the hierarchical reasoning tree."""
    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    label: str = ""
    content: str = ""
    node_type: str = "step"        # "root", "step", "assumption", "conclusion", "tool_call", "observation"
    confidence: float = 1.0
    children: List["ReasoningNode"] = field(default_factory=list)
    editable: bool = True
    edited: bool = False
    original_content: Optional[str] = None

    def add_child(self, child: "ReasoningNode") -> "ReasoningNode":
        self.children.append(child)
        return child

    def edit(self, new_content: str) -> None:
        if not self.edited:
            self.original_content = self.content
        self.content = new_content
        self.edited = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "content": self.content,
            "node_type": self.node_type,
            "confidence": round(self.confidence, 4),
            "children": [c.to_dict() for c in self.children],
            "editable": self.editable,
            "edited": self.edited,
            "original_content": self.original_content,
        }

    def flatten(self) -> List[Dict[str, Any]]:
        """Return flat list of all nodes in pre-order traversal."""
        result = [{
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "depth": 0,
        }]
        for child in self.children:
            for item in child.flatten():
                item["depth"] = item.get("depth", 0) + 1
                result.append(item)
        return result


# ── Parsing heuristics ───────────────────────────────────────────

_STEP_PATTERNS = [
    re.compile(r"^(?:step|phase)\s*(\d+)[:\.]?\s*(.*)", re.IGNORECASE),
    re.compile(r"^(\d+)[.)]\s+(.*)", re.IGNORECASE),
    re.compile(r"^(?:first|second|third|then|next|finally)[,:]?\s*(.*)", re.IGNORECASE),
]

_ASSUMPTION_PATTERNS = [
    re.compile(r"(?:assum(?:e|ing|ption)|hypothes(?:is|ize)|given that)\s*(.*)", re.IGNORECASE),
]

_TOOL_CALL_PATTERNS = [
    re.compile(r"(?:call(?:ing)?|invok(?:e|ing)|using|running)\s+(?:tool|function|api)\s*[:\s]*(.*)", re.IGNORECASE),
    re.compile(r"```(?:tool_call|function_call)(.*?)```", re.DOTALL),
]

_CONCLUSION_PATTERNS = [
    re.compile(r"(?:therefore|thus|conclusion|result|answer|final(?:ly)?)[:\s]+\s*(.*)", re.IGNORECASE),
]

_OBSERVATION_PATTERNS = [
    re.compile(r"(?:observ(?:e|ing|ation)|notic(?:e|ing)|result shows?)\s*(.*)", re.IGNORECASE),
]


def parse_chain_of_thought(raw_text: str, query: str = "") -> ReasoningNode:
    """
    Parse a raw LLM reasoning trace into a hierarchical topic tree.

    The parser identifies:
    - Numbered steps → step nodes
    - Assumptions → assumption sub-nodes
    - Tool calls → tool_call nodes
    - Observations → observation nodes
    - Conclusions → conclusion nodes

    Returns the root of the tree.
    """
    root = ReasoningNode(
        label="Reasoning Trace",
        content=query or "User Query",
        node_type="root",
        editable=False,
    )

    if not raw_text or not raw_text.strip():
        return root

    lines = raw_text.strip().split("\n")
    current_step: Optional[ReasoningNode] = None
    buffer: List[str] = []

    def flush_buffer():
        nonlocal buffer
        if buffer and current_step:
            current_step.content += "\n".join(buffer)
            buffer = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for step patterns
        matched_step = False
        for pat in _STEP_PATTERNS:
            m = pat.match(stripped)
            if m:
                flush_buffer()
                groups = m.groups()
                label = groups[-1] if groups else stripped
                current_step = ReasoningNode(
                    label=label[:80] or f"Step",
                    content=stripped,
                    node_type="step",
                )
                root.add_child(current_step)
                matched_step = True
                break

        if matched_step:
            continue

        # Check for assumptions (as children of current step)
        for pat in _ASSUMPTION_PATTERNS:
            m = pat.search(stripped)
            if m:
                flush_buffer()
                node = ReasoningNode(
                    label=m.group(1)[:60] or "Assumption",
                    content=stripped,
                    node_type="assumption",
                    confidence=0.7,
                )
                if current_step:
                    current_step.add_child(node)
                else:
                    root.add_child(node)
                matched_step = True
                break

        if matched_step:
            continue

        # Check for tool calls
        for pat in _TOOL_CALL_PATTERNS:
            m = pat.search(stripped)
            if m:
                flush_buffer()
                node = ReasoningNode(
                    label=m.group(1)[:60] or "Tool Call",
                    content=stripped,
                    node_type="tool_call",
                    editable=False,
                )
                if current_step:
                    current_step.add_child(node)
                else:
                    root.add_child(node)
                matched_step = True
                break

        if matched_step:
            continue

        # Check for observations
        for pat in _OBSERVATION_PATTERNS:
            m = pat.search(stripped)
            if m:
                flush_buffer()
                node = ReasoningNode(
                    label=m.group(1)[:60] or "Observation",
                    content=stripped,
                    node_type="observation",
                    editable=False,
                )
                if current_step:
                    current_step.add_child(node)
                else:
                    root.add_child(node)
                matched_step = True
                break

        if matched_step:
            continue

        # Check for conclusions
        for pat in _CONCLUSION_PATTERNS:
            m = pat.search(stripped)
            if m:
                flush_buffer()
                node = ReasoningNode(
                    label=m.group(1)[:60] or "Conclusion",
                    content=stripped,
                    node_type="conclusion",
                    editable=False,
                )
                root.add_child(node)
                current_step = None
                matched_step = True
                break

        if not matched_step:
            buffer.append(stripped)

    flush_buffer()

    # If no structure was detected, create a single "raw" node
    if not root.children:
        root.add_child(ReasoningNode(
            label="Raw Reasoning",
            content=raw_text[:2000],
            node_type="step",
        ))

    return root


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. TELEMETRY AGGREGATION                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class TelemetryWindow:
    """Sliding-window telemetry statistics."""
    window_seconds: int = 300    # 5 minutes
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    latencies: List[float] = field(default_factory=list)

    def record(self, latency_ms: float, tokens: int = 0, error: bool = False) -> None:
        self.request_count += 1
        self.total_latency_ms += latency_ms
        self.total_tokens += tokens
        self.latencies.append(latency_ms)
        if error:
            self.error_count += 1
        # Keep latencies bounded
        if len(self.latencies) > 10000:
            self.latencies = self.latencies[-5000:]

    def percentile(self, pct: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * pct / 100)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_seconds": self.window_seconds,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / max(self.request_count, 1), 4),
            "avg_latency_ms": round(self.total_latency_ms / max(self.request_count, 1), 2),
            "p50_ms": round(self.percentile(50), 2),
            "p95_ms": round(self.percentile(95), 2),
            "p99_ms": round(self.percentile(99), 2),
            "total_tokens": self.total_tokens,
        }


# Global telemetry
_telemetry = TelemetryWindow()


def record_telemetry(latency_ms: float, tokens: int = 0, error: bool = False) -> None:
    _telemetry.record(latency_ms, tokens, error)


def telemetry_summary() -> Dict[str, Any]:
    return _telemetry.to_dict()


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. CONVENIENCE                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def observability_report() -> Dict[str, Any]:
    """Full observability snapshot."""
    collector = get_collector()
    return {
        "tracing": collector.stats(),
        "telemetry": telemetry_summary(),
        "recent_traces": collector.list_traces(limit=10),
    }
