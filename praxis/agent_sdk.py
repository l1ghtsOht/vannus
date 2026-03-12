# --------------- Praxis Agent SDK — Tool Oracle for AI Agents ---------------
"""
v19 · Platform Evolution — AI Agent Integration

Exposes Praxis as a "tool oracle" that any LLM or AI agent framework
can query.  Instead of hard-coding tool knowledge into every agent,
agents call the Praxis SDK to:

    • Discover tools matching a capability requirement
    • Get structured plans for multi-tool workflows
    • Retrieve compliance and trust metadata
    • Execute workflows through the connector layer

The SDK provides both a **local Python API** (for in-process agents)
and a **request schema** for the REST API (consumed by any language).

Integration targets
───────────────────
    • LangChain / LangGraph tool-calling
    • AutoGen agent-to-agent coordination
    • CrewAI crew definitions
    • OpenAI function-calling / tool-use
    • Anthropic tool-use protocol
    • Custom agent loops

Design
──────
    AgentSession      — stateful session for multi-turn agent interactions
    ToolOracleQuery   — structured query format for tool discovery
    PlanRequest       — request a full workflow plan
    sdk_discover()    — one-shot tool discovery
    sdk_plan()        — one-shot plan generation
    sdk_execute()     — execute a plan and return results
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.agent_sdk")

try:
    from .engine import find_tools
    from .interpreter import interpret
    from .data import TOOLS
except ImportError:
    from engine import find_tools
    from interpreter import interpret
    from data import TOOLS

try:
    from .workflow_engine import generate_plan, execute_plan, WorkflowPlan
    _WF_ENGINE = True
except ImportError:
    _WF_ENGINE = False

try:
    from .vendor_trust import VendorTrustEngine
    _TRUST_AVAILABLE = True
except ImportError:
    _TRUST_AVAILABLE = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class AgentSession:
    """Stateful session for multi-turn agent interactions."""
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    agent_name: str = "unknown"
    framework: str = "custom"              # langchain | autogen | crewai | openai | anthropic | custom
    created_at: float = field(default_factory=time.time)
    last_touched: float = field(default_factory=time.time)
    queries: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def record_query(self, query: str, result: Dict[str, Any]) -> None:
        now = time.time()
        self.queries.append({
            "query": query,
            "result_summary": result.get("summary", ""),
            "tools_found": len(result.get("tools", result.get("results", []))),
            "timestamp": now,
        })
        self.last_touched = now

    def get_history(self) -> List[Dict[str, Any]]:
        return self.queries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "framework": self.framework,
            "created_at": self.created_at,
            "last_touched": self.last_touched,
            "query_count": len(self.queries),
            "context": self.context,
        }


# Active sessions (process-local)
_sessions: Dict[str, AgentSession] = {}
_session_lock = threading.Lock()
_SESSION_TTL_SECONDS = 60 * 60          # 1 hour inactivity TTL
_MAX_ACTIVE_SESSIONS = 1000


def _prune_sessions(now: Optional[float] = None) -> None:
    ts = now if now is not None else time.time()

    # Remove stale sessions first.
    expired = [
        sid
        for sid, session in _sessions.items()
        if (ts - session.last_touched) > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _sessions.pop(sid, None)

    # Enforce hard cap by evicting least-recently-touched sessions.
    overflow = len(_sessions) - _MAX_ACTIVE_SESSIONS
    if overflow > 0:
        victim_ids = sorted(_sessions, key=lambda sid: _sessions[sid].last_touched)[:overflow]
        for sid in victim_ids:
            _sessions.pop(sid, None)


def create_session(
    agent_name: str = "unknown",
    framework: str = "custom",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a new agent session."""
    now = time.time()
    session = AgentSession(
        agent_name=agent_name,
        framework=framework,
        context=context or {},
        last_touched=now,
    )
    with _session_lock:
        _prune_sessions(now)
        _sessions[session.session_id] = session
    log.info("Agent session created: %s (%s / %s)", session.session_id, agent_name, framework)
    return session.to_dict()


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session info."""
    with _session_lock:
        _prune_sessions()
        session = _sessions.get(session_id)
        if session:
            session.last_touched = time.time()
    return session.to_dict() if session else None


def end_session(session_id: str) -> bool:
    """End and clean up a session."""
    with _session_lock:
        return _sessions.pop(session_id, None) is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOOL DISCOVERY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ToolOracleQuery:
    """Structured query for tool discovery."""
    capability: str                        # natural-language description
    constraints: Dict[str, Any] = field(default_factory=dict)
    top_n: int = 5
    include_trust: bool = False
    include_pricing: bool = True
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def sdk_discover(
    capability: str,
    *,
    top_n: int = 5,
    constraints: Optional[Dict[str, Any]] = None,
    include_trust: bool = False,
    include_pricing: bool = True,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Discover tools matching a capability requirement.

    This is the primary entry point for AI agents.  Returns a structured
    dict with tool recommendations enriched with metadata an agent needs
    to make tool-calling decisions.
    """
    t0 = time.time()
    constraints = constraints or {}

    # Interpret the capability request
    intent = interpret(capability)
    keywords = intent.get("keywords", capability.split())

    # Find matching tools
    raw_results = find_tools(" ".join(keywords), top_n=top_n * 2)  # over-fetch for filtering
    results = []

    for tool in raw_results[:top_n * 2]:
        if not hasattr(tool, "name"):
            continue

        entry: Dict[str, Any] = {
            "name": tool.name,
            "description": getattr(tool, "description", ""),
            "categories": getattr(tool, "categories", []),
            "tags": getattr(tool, "tags", []),
            "url": getattr(tool, "url", ""),
            "skill_level": getattr(tool, "skill_level", "beginner"),
            "use_cases": getattr(tool, "use_cases", []),
            "integrations": getattr(tool, "integrations", []),
        }

        if include_pricing:
            entry["pricing"] = getattr(tool, "pricing", {})

        # Budget filter
        max_budget = constraints.get("max_monthly_usd")
        if max_budget is not None:
            pricing = getattr(tool, "pricing", {}) or {}
            starter = pricing.get("starter", 0)
            if starter and float(starter) > max_budget:
                entry["budget_warning"] = f"Starter plan ${starter}/mo exceeds ${max_budget} limit"

        # Compliance filter
        required_compliance = constraints.get("compliance", [])
        if required_compliance:
            tool_compliance = {c.lower() for c in getattr(tool, "compliance", [])}
            missing = [c for c in required_compliance if c.lower() not in tool_compliance]
            if missing:
                entry["compliance_gaps"] = missing

        # Trust enrichment
        if include_trust and _TRUST_AVAILABLE:
            try:
                engine = VendorTrustEngine()
                profile = engine.build_profile(tool.name, tool)
                score = engine.score(profile)
                entry["trust_score"] = {
                    "composite": score.composite_score,
                    "passed": score.passed,
                    "maturity": score.maturity.value if hasattr(score.maturity, 'value') else str(score.maturity),
                }
            except Exception:
                pass

        results.append(entry)

    # Trim to requested count
    results = results[:top_n]

    response = {
        "query": capability,
        "intent": intent,
        "results": results,
        "total_found": len(results),
        "constraints_applied": constraints,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }

    # Record in session if available
    if session_id:
        with _session_lock:
            _prune_sessions()
            session = _sessions.get(session_id)
            if session:
                session.record_query(capability, response)

    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PLAN GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sdk_plan(
    query: str,
    *,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a workflow plan for a complex request."""
    if not _WF_ENGINE:
        return {"error": "Workflow engine not available", "query": query}

    t0 = time.time()
    plan = generate_plan(query)
    response = {
        "plan": plan.to_dict(),
        "step_count": len(plan.steps),
        "subtask_count": len(plan.subtasks),
        "estimated_cost_usd": plan.estimated_cost_usd,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }

    if session_id:
        with _session_lock:
            _prune_sessions()
            session = _sessions.get(session_id)
            if session:
                session.record_query(f"plan: {query}", response)

    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PLAN EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def sdk_execute(
    plan_dict: Dict[str, Any],
    *,
    secrets: Optional[Dict[str, str]] = None,
    dry_run: bool = True,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a workflow plan (async)."""
    if not _WF_ENGINE:
        return {"error": "Workflow engine not available"}

    plan = WorkflowPlan.from_dict(plan_dict)
    result = await execute_plan(plan, secrets=secrets, dry_run=dry_run)
    response = result.to_dict()

    if session_id:
        with _session_lock:
            _prune_sessions()
            session = _sessions.get(session_id)
            if session:
                session.record_query(f"execute: {plan.name}", response)

    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MULTI-MODEL ECOSYSTEM — SDK Extensions (v20)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    from .model_router import route_query
    from .ecosystem import run_collaboration
    from .shared_state import get_shared_state_manager
    _ECOSYSTEM_AVAILABLE = True
except ImportError:
    try:
        from model_router import route_query
        from ecosystem import run_collaboration
        from shared_state import get_shared_state_manager
        _ECOSYSTEM_AVAILABLE = True
    except ImportError:
        _ECOSYSTEM_AVAILABLE = False


def sdk_route(
    query: str,
    *,
    budget_usd: float = 5.0,
    privacy_required: bool = False,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Route a query to the optimal model(s) using elimination-first selection.

    Returns the routing decision including selected models, strategy,
    eliminated candidates with reasons, and estimated cost.
    """
    if not _ECOSYSTEM_AVAILABLE:
        return {"error": "Multi-model ecosystem not available"}

    t0 = time.time()
    decision = route_query(query)
    response = {
        "action": "route",
        "query": query,
        "strategy": decision.strategy.value,
        "selected_models": decision.selected_models,
        "eliminated": decision.eliminated,
        "complexity": decision.complexity,
        "cost_estimate_usd": decision.cost_estimate_usd,
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }

    if session_id:
        with _session_lock:
            _prune_sessions()
            session = _sessions.get(session_id)
            if session:
                session.record_query(f"route: {query}", response)

    return response


def sdk_collaborate(
    task: str,
    *,
    strategy: Optional[str] = None,
    budget_usd: float = 5.0,
    system_prompt: Optional[str] = None,
    privacy_required: bool = False,
    user_id: str = "sdk",
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a full multi-model collaboration on a task.

    Automatically routes the task, selects the best strategy
    (single / fan-out / chain / adversarial), executes, and
    returns a unified result with full trace and cost breakdown.
    """
    if not _ECOSYSTEM_AVAILABLE:
        return {"error": "Multi-model ecosystem not available"}

    t0 = time.time()
    result = run_collaboration(
        task=task,
        strategy=strategy,
        budget_usd=budget_usd,
        system_prompt=system_prompt,
        privacy_required=privacy_required,
        user_id=user_id,
    )
    response = {
        "action": "collaborate",
        "task": task,
        **result.to_dict(),
        "sdk_latency_ms": round((time.time() - t0) * 1000, 2),
    }

    if session_id:
        with _session_lock:
            _prune_sessions()
            session = _sessions.get(session_id)
            if session:
                session.record_query(f"collaborate: {task}", response)

    return response


def sdk_shared_state(
    action: str = "status",
    *,
    key: Optional[str] = None,
    value: Optional[Any] = None,
    model_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Interact with the multi-model shared state manager.

    Actions
    -------
    status      Return summary of shared state (output count, artifact count).
    get         Retrieve artifact by key.
    set         Store artifact with key and value.
    context     Retrieve curated context for a model (requires model_id).
    """
    if not _ECOSYSTEM_AVAILABLE:
        return {"error": "Multi-model ecosystem not available"}

    mgr = get_shared_state_manager()

    if action == "status":
        return {
            "action": "status",
            "output_count": len(mgr._outputs),
            "artifact_count": len(mgr._artifacts),
        }
    elif action == "get":
        if not key:
            return {"error": "Provide a 'key' for get action"}
        val = mgr.get_artifact(key)
        return {"action": "get", "key": key, "value": val, "found": val is not None}
    elif action == "set":
        if not key:
            return {"error": "Provide a 'key' for set action"}
        mgr.set_artifact(key, value)
        return {"action": "set", "key": key, "stored": True}
    elif action == "context":
        if not model_id:
            return {"error": "Provide 'model_id' for context action"}
        ctx = mgr.get_context_for_model(model_id)
        return {"action": "context", "model_id": model_id, "context": ctx.to_text()}
    else:
        return {"error": f"Unknown action: {action}"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  OPENAI / ANTHROPIC FUNCTION SCHEMA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_tool_schema() -> Dict[str, Any]:
    """
    Return an OpenAI-compatible function/tool schema that LLMs can use
    to call Praxis as a tool.

    Usage (in your agent's tool list):
        tools = [praxis_sdk.get_tool_schema()]
    """
    return {
        "type": "function",
        "function": {
            "name": "praxis_tool_oracle",
            "description": (
                "Query the Praxis AI tool knowledge base. "
                "Discovers tools, generates workflow plans, and provides "
                "trust/compliance metadata for AI tool selection."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["discover", "plan", "execute"],
                        "description": "The action to perform",
                    },
                    "query": {
                        "type": "string",
                        "description": "Natural-language query or capability requirement",
                    },
                    "top_n": {
                        "type": "integer",
                        "default": 5,
                        "description": "Number of results to return for discover",
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Optional constraints: max_monthly_usd, compliance, etc.",
                    },
                    "include_trust": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include vendor trust scores",
                    },
                },
                "required": ["action", "query"],
            },
        },
    }


def handle_tool_call(
    action: str,
    query: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Universal handler for tool calls from any LLM framework.
    Dispatch to discover / plan / route / collaborate based on action.
    """
    if action == "discover":
        return sdk_discover(
            query,
            top_n=kwargs.get("top_n", 5),
            constraints=kwargs.get("constraints"),
            include_trust=kwargs.get("include_trust", False),
            include_pricing=kwargs.get("include_pricing", True),
            session_id=kwargs.get("session_id"),
        )
    elif action == "plan":
        return sdk_plan(query, session_id=kwargs.get("session_id"))
    elif action == "execute":
        return {"error": "Use sdk_execute() (async) for plan execution"}
    elif action == "route":
        return sdk_route(
            query,
            budget_usd=kwargs.get("budget_usd", 5.0),
            privacy_required=kwargs.get("privacy_required", False),
            session_id=kwargs.get("session_id"),
        )
    elif action == "collaborate":
        return sdk_collaborate(
            query,
            strategy=kwargs.get("strategy"),
            budget_usd=kwargs.get("budget_usd", 5.0),
            system_prompt=kwargs.get("system_prompt"),
            privacy_required=kwargs.get("privacy_required", False),
            user_id=kwargs.get("user_id", "sdk"),
            session_id=kwargs.get("session_id"),
        )
    else:
        return {"error": f"Unknown action: {action}"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SDK METADATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sdk_info() -> Dict[str, Any]:
    """Return SDK version and capabilities for agent handshake."""
    return {
        "sdk_name": "praxis-agent-sdk",
        "sdk_version": "0.2.0",
        "capabilities": ["discover", "plan", "execute", "trust", "route", "collaborate", "shared_state"],
        "tool_count": len(TOOLS),
        "ecosystem_available": _ECOSYSTEM_AVAILABLE,
        "supported_frameworks": [
            "langchain", "autogen", "crewai",
            "openai", "anthropic", "custom",
        ],
        "openai_tool_schema": get_tool_schema(),
    }
