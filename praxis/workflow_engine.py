# --------------- Praxis Workflow Engine — Executable Workflows ---------------
"""
v19 · Platform Evolution — Execution Engine

Transforms Praxis from a recommendation engine into an *execution engine*
for AI-powered business processes.  Given a natural-language request the
engine:

    1. **Decomposes** the request into typed sub-tasks.
    2. **Selects** the optimal tools/connectors for each sub-task.
    3. **Generates** a portable WorkflowPlan (JSON-serialisable DAG).
    4. **Runs** the plan through connectors with sandbox enforcement.
    5. **Collects** results and returns a unified WorkflowResult.

Design philosophy
─────────────────
    • Plans are *data* (JSON DAGs), not code — they can be stored,
      shared in the marketplace, and version-controlled.
    • Every step has a timeout, output-size cap, and retry policy.
    • Execution is async and non-blocking; each step awaits its
      connector and feeds output into the next step's params.
    • Dry-run by default — no live API calls until the user opts in.

Security
────────
    • The engine enforces a per-workflow wall-clock budget.
    • Output payloads are truncated to MAX_OUTPUT_BYTES.
    • Secrets are scoped per-step (a step only sees the secrets
      its connector requires) — principle of least privilege.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

log = logging.getLogger("praxis.workflow_engine")

try:
    from .connectors import (
        ConnectorContext, ConnectorResult, execute_connector,
        get_registry, list_connectors,
    )
except ImportError:
    from connectors import (
        ConnectorContext, ConnectorResult, execute_connector,
        get_registry, list_connectors,
    )

try:
    from .engine import find_tools
    from .interpreter import interpret
    from .data import TOOLS
except ImportError:
    from engine import find_tools
    from interpreter import interpret
    from data import TOOLS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_OUTPUT_BYTES: int = 512_000          # 512 KB per step
MAX_WORKFLOW_STEPS: int = 20
DEFAULT_STEP_TIMEOUT: float = 30.0       # seconds
DEFAULT_WORKFLOW_BUDGET: float = 300.0   # 5 min wall-clock max


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & VALUE OBJECTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TaskType(str, Enum):
    NLU = "nlu"
    INTEGRATION = "integration"
    COMPLIANCE = "compliance"
    ANALYTICS = "analytics"
    CONTENT = "content"
    AUTOMATION = "automation"
    MONITORING = "monitoring"
    BUDGETING = "budgeting"
    CUSTOM = "custom"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SubTask:
    """One decomposed sub-task from a user request."""
    id: str
    description: str
    task_type: TaskType = TaskType.CUSTOM
    keywords: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "task_type": self.task_type.value,
            "keywords": self.keywords,
            "constraints": self.constraints,
            "depends_on": self.depends_on,
        }


@dataclass
class WorkflowStep:
    """One executable step in a workflow plan."""
    id: str
    task_id: str                           # links back to SubTask.id
    connector_id: str                      # which connector to call
    action: str                            # connector action name
    params: Dict[str, Any] = field(default_factory=dict)
    timeout: float = DEFAULT_STEP_TIMEOUT
    retries: int = 1
    depends_on: List[str] = field(default_factory=list)
    tool_name: str = ""                    # human-readable tool name
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "connector_id": self.connector_id,
            "action": self.action,
            "params": self.params,
            "timeout": self.timeout,
            "retries": self.retries,
            "depends_on": self.depends_on,
            "tool_name": self.tool_name,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


@dataclass
class WorkflowPlan:
    """A complete executable workflow plan (JSON-serialisable DAG)."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    query: str = ""
    subtasks: List[SubTask] = field(default_factory=list)
    steps: List[WorkflowStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    estimated_cost_usd: float = 0.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "query": self.query,
            "subtasks": [s.to_dict() for s in self.subtasks],
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "estimated_cost_usd": self.estimated_cost_usd,
            "tags": self.tags,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowPlan":
        plan = cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            query=data.get("query", ""),
            created_at=data.get("created_at", time.time()),
            estimated_cost_usd=data.get("estimated_cost_usd", 0.0),
            tags=data.get("tags", []),
        )
        for st in data.get("subtasks", []):
            plan.subtasks.append(SubTask(
                id=st["id"], description=st["description"],
                task_type=TaskType(st.get("task_type", "custom")),
                keywords=st.get("keywords", []),
                constraints=st.get("constraints", {}),
                depends_on=st.get("depends_on", []),
            ))
        for s in data.get("steps", []):
            plan.steps.append(WorkflowStep(
                id=s["id"], task_id=s["task_id"],
                connector_id=s["connector_id"], action=s["action"],
                params=s.get("params", {}), timeout=s.get("timeout", DEFAULT_STEP_TIMEOUT),
                retries=s.get("retries", 1), depends_on=s.get("depends_on", []),
                tool_name=s.get("tool_name", ""), description=s.get("description", ""),
            ))
        return plan


@dataclass
class WorkflowResult:
    """Outcome of executing a workflow plan."""
    plan_id: str
    success: bool
    steps_completed: int = 0
    steps_failed: int = 0
    steps_skipped: int = 0
    total_elapsed_ms: float = 0.0
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "success": self.success,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "steps_skipped": self.steps_skipped,
            "total_elapsed_ms": round(self.total_elapsed_ms, 2),
            "step_results": self.step_results,
            "summary": self.summary,
            "dry_run": self.dry_run,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TASK DECOMPOSITION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Signal → TaskType mapping for heuristic decomposition
_TASK_SIGNALS: Dict[TaskType, List[str]] = {
    TaskType.NLU: [
        "chatbot", "nlu", "nlp", "natural language", "intent",
        "conversation", "dialogue", "speech", "transcription",
    ],
    TaskType.INTEGRATION: [
        "integrate", "integration", "connect", "crm", "salesforce",
        "hubspot", "webhook", "api", "zapier", "sync",
    ],
    TaskType.COMPLIANCE: [
        "gdpr", "hipaa", "soc2", "compliance", "privacy", "audit",
        "regulation", "pci", "iso", "data protection",
    ],
    TaskType.ANALYTICS: [
        "analytics", "dashboard", "metrics", "reporting", "kpi",
        "monitor", "tracking", "insights", "visualization",
    ],
    TaskType.CONTENT: [
        "content", "writing", "blog", "email", "copy", "marketing",
        "social media", "seo", "design", "image", "video",
    ],
    TaskType.AUTOMATION: [
        "automate", "automation", "workflow", "trigger", "schedule",
        "pipeline", "orchestrate", "batch", "cron",
    ],
    TaskType.MONITORING: [
        "uptime", "alerting", "logging", "observability", "health check",
        "incident", "on-call", "status page",
    ],
    TaskType.BUDGETING: [
        "budget", "cost", "pricing", "cheap", "affordable", "free",
        "expensive", "subscription", "$", "per month", "roi",
    ],
}


def decompose_request(query: str) -> List[SubTask]:
    """Heuristic decomposition of a natural-language request into sub-tasks."""
    q_lower = query.lower()
    subtasks: List[SubTask] = []
    task_idx = 0

    for task_type, signals in _TASK_SIGNALS.items():
        hits = [s for s in signals if s in q_lower]
        if hits:
            task_idx += 1
            subtasks.append(SubTask(
                id=f"task-{task_idx}",
                description=f"{task_type.value.title()} sub-task detected from: {', '.join(hits)}",
                task_type=task_type,
                keywords=hits,
            ))

    # If nothing matched, create a single catch-all task
    if not subtasks:
        intent = interpret(query)
        kws = intent.get("keywords", query.split())
        subtasks.append(SubTask(
            id="task-1",
            description=f"General task: {query[:120]}",
            task_type=TaskType.CUSTOM,
            keywords=kws if isinstance(kws, list) else [kws],
        ))

    # Wire sequential dependencies
    for i, st in enumerate(subtasks):
        if i > 0:
            st.depends_on = [subtasks[i - 1].id]

    # Extract budget constraint
    budget_match = re.search(r'\$\s*([\d,]+)', query)
    if budget_match:
        budget = float(budget_match.group(1).replace(",", ""))
        for st in subtasks:
            st.constraints["max_monthly_usd"] = budget

    return subtasks


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOOL SELECTION & PLAN GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _select_tool_for_task(subtask: SubTask) -> Optional[Dict[str, Any]]:
    """Use Praxis engine to find the best tool for a sub-task."""
    query = " ".join(subtask.keywords) if subtask.keywords else subtask.description
    results = find_tools(query, top_n=3)
    if not results:
        return None

    # If budget constraint, filter by pricing
    max_budget = subtask.constraints.get("max_monthly_usd")
    if max_budget is not None:
        for r in results:
            tool = r if hasattr(r, "name") else None
            if tool:
                pricing = getattr(tool, "pricing", {}) or {}
                starter = pricing.get("starter", 0)
                if starter and float(starter) <= max_budget:
                    return {"name": tool.name, "tool": tool, "reason": "Within budget and best match"}
        # If no budget match, return first anyway with warning
        first = results[0]
        tool = first if hasattr(first, "name") else None
        if tool:
            return {"name": tool.name, "tool": tool, "reason": "Best match (budget may exceed limit)"}

    first = results[0]
    tool = first if hasattr(first, "name") else None
    if tool:
        return {"name": tool.name, "tool": tool, "reason": "Top-ranked match"}
    return None


def _map_task_to_connector(subtask: SubTask, tool_selection: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Map a selected tool to an available connector + action."""
    registry = get_registry()
    tool_name = tool_selection.get("name", "")

    # Try direct match by tool name
    for c in registry.list_connectors():
        if c["tool_name"].lower() == tool_name.lower():
            # Pick the most relevant action
            actions = c["actions"]
            action = actions[0] if actions else "default"
            # Try to pick a smarter action based on task type
            task_action_map = {
                TaskType.NLU: ["chat_completion", "send_message"],
                TaskType.INTEGRATION: ["trigger_webhook", "query_records", "create_record"],
                TaskType.COMPLIANCE: ["query_records", "read_range"],
                TaskType.ANALYTICS: ["read_range", "query_records"],
                TaskType.CONTENT: ["chat_completion", "send_message"],
                TaskType.AUTOMATION: ["trigger_webhook", "list_zaps"],
            }
            preferred = task_action_map.get(subtask.task_type, [])
            for pref in preferred:
                if pref in actions:
                    action = pref
                    break
            return {"connector_id": c["id"], "action": action}

    # If no matching connector, map common task types to default connectors
    fallback_map = {
        TaskType.NLU: ("openai", "chat_completion"),
        TaskType.CONTENT: ("openai", "chat_completion"),
        TaskType.INTEGRATION: ("zapier", "trigger_webhook"),
        TaskType.AUTOMATION: ("zapier", "trigger_webhook"),
        TaskType.ANALYTICS: ("google_sheets", "read_range"),
    }
    fb = fallback_map.get(subtask.task_type)
    if fb and registry.get_connector(fb[0]):
        return {"connector_id": fb[0], "action": fb[1]}

    return None


def generate_plan(query: str) -> WorkflowPlan:
    """Decompose a request and generate a full executable workflow plan."""
    subtasks = decompose_request(query)
    plan = WorkflowPlan(
        name=f"Workflow for: {query[:80]}",
        description=f"Auto-generated plan with {len(subtasks)} sub-tasks",
        query=query,
        subtasks=subtasks,
    )

    step_idx = 0
    for subtask in subtasks:
        tool_sel = _select_tool_for_task(subtask)
        if tool_sel is None:
            continue
        connector_info = _map_task_to_connector(subtask, tool_sel)
        if connector_info is None:
            continue

        step_idx += 1
        step = WorkflowStep(
            id=f"step-{step_idx}",
            task_id=subtask.id,
            connector_id=connector_info["connector_id"],
            action=connector_info["action"],
            tool_name=tool_sel.get("name", ""),
            description=f"{subtask.task_type.value.title()}: {subtask.description[:80]}",
            depends_on=[f"step-{step_idx - 1}"] if step_idx > 1 else [],
        )
        plan.steps.append(step)

    # Estimate cost (rough heuristic)
    plan.estimated_cost_usd = len(plan.steps) * 0.02  # dry-run estimate

    return plan


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKFLOW EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def execute_plan(
    plan: WorkflowPlan,
    secrets: Optional[Dict[str, str]] = None,
    dry_run: bool = True,
    budget_seconds: float = DEFAULT_WORKFLOW_BUDGET,
) -> WorkflowResult:
    """Execute all steps in a workflow plan, respecting dependencies."""
    t0 = time.monotonic()
    secrets = secrets or {}
    completed: Dict[str, Dict[str, Any]] = {}
    result = WorkflowResult(plan_id=plan.id, success=True, dry_run=dry_run)

    # Build dependency graph
    step_map = {s.id: s for s in plan.steps}

    for step in plan.steps:
        # Check wall-clock budget
        elapsed = (time.monotonic() - t0) * 1000
        if elapsed / 1000 > budget_seconds:
            step.status = StepStatus.SKIPPED
            step.error = "Workflow budget exceeded"
            result.steps_skipped += 1
            result.step_results.append(step.to_dict())
            continue

        # Check dependencies
        deps_met = all(d in completed for d in step.depends_on)
        if not deps_met:
            step.status = StepStatus.SKIPPED
            step.error = "Unmet dependency"
            result.steps_skipped += 1
            result.step_results.append(step.to_dict())
            continue

        # Inject upstream outputs into params
        for dep_id in step.depends_on:
            dep_result = completed.get(dep_id, {})
            step.params[f"_upstream_{dep_id}"] = dep_result

        # Scope secrets to this connector's requirements
        connector = get_registry().get_connector(step.connector_id)
        step_secrets = {}
        if connector:
            for key in connector.spec.required_secrets:
                if key in secrets:
                    step_secrets[key] = secrets[key]

        # Execute with retries
        step.status = StepStatus.RUNNING
        last_error = None
        for attempt in range(max(1, step.retries)):
            try:
                cr = await execute_connector(
                    step.connector_id, step.action, step.params,
                    secrets=step_secrets, dry_run=dry_run,
                    timeout=step.timeout,
                )
                if cr.success:
                    step.status = StepStatus.COMPLETED
                    # Truncate output
                    data_json = json.dumps(cr.data, default=str)
                    if len(data_json) > MAX_OUTPUT_BYTES:
                        cr.data = {"_truncated": True, "preview": data_json[:1000]}
                    step.result = cr.to_dict()
                    step.elapsed_ms = cr.elapsed_ms
                    completed[step.id] = cr.data
                    result.steps_completed += 1
                    break
                else:
                    last_error = cr.error
            except Exception as exc:
                last_error = str(exc)

            if attempt < step.retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # backoff

        if step.status != StepStatus.COMPLETED:
            step.status = StepStatus.FAILED
            step.error = last_error or "Unknown error"
            result.steps_failed += 1
            result.success = False

        result.step_results.append(step.to_dict())

    result.total_elapsed_ms = (time.monotonic() - t0) * 1000

    # Generate summary
    result.summary = (
        f"Workflow '{plan.name}' {'succeeded' if result.success else 'had failures'}: "
        f"{result.steps_completed} completed, {result.steps_failed} failed, "
        f"{result.steps_skipped} skipped in {result.total_elapsed_ms:.0f}ms"
    )

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONVENIENCE: ONE-SHOT ASSEMBLE & RUN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def assemble_and_run(
    query: str,
    secrets: Optional[Dict[str, str]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """End-to-end: decompose → plan → execute → return result dict."""
    plan = generate_plan(query)
    result = await execute_plan(plan, secrets=secrets, dry_run=dry_run)
    return {
        "plan": plan.to_dict(),
        "result": result.to_dict(),
    }
