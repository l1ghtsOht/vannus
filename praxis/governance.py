# --------------- Praxis Governance — Enterprise Control Plane ---------------
"""
v19 · Platform Evolution — Enterprise Governance

Provides a "single pane of glass" for enterprise teams to monitor
AI tool usage, costs, compliance posture, and team activity across
the entire Praxis platform.

Capabilities
────────────
    • Usage tracking — per-team, per-tool, per-endpoint counters
    • Cost aggregation — estimated spend across provisioned tools
    • Compliance dashboard — GDPR / HIPAA / SOC2 posture per tool
    • Audit log — immutable record of all governance-relevant events
    • Policy enforcement — block tools that violate org policies
    • Team management stubs — role-based access scaffolding

All data is held in-process for MVP; swap to a database adapter
for multi-instance deployments.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger("praxis.governance")

_BASE = Path(__file__).resolve().parent
_AUDIT_LOG_PATH = _BASE / "governance_audit.json"
_POLICIES_PATH = _BASE / "governance_policies.json"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuditAction(str, Enum):
    TOOL_SEARCH = "tool_search"
    TOOL_SELECTED = "tool_selected"
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_EXECUTED = "workflow_executed"
    CONNECTOR_CALLED = "connector_called"
    POLICY_VIOLATION = "policy_violation"
    SUBMISSION_APPROVED = "submission_approved"
    SUBMISSION_REJECTED = "submission_rejected"
    CONFIG_CHANGED = "config_changed"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class TeamRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action: AuditAction = AuditAction.TOOL_SEARCH
    actor: str = "system"
    team: str = "default"
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "action": self.action.value,
            "actor": self.actor,
            "team": self.team,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class OrgPolicy:
    """An organisational policy rule."""
    policy_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    description: str = ""
    rule_type: str = "block_tool"          # block_tool | require_compliance | budget_cap | require_approval
    conditions: Dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_by: str = "admin"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "conditions": self.conditions,
            "active": self.active,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class UsageRecord:
    """Aggregated usage counter for a tool within a team."""
    tool_name: str = ""
    team: str = "default"
    search_count: int = 0
    selection_count: int = 0
    workflow_count: int = 0
    estimated_cost_usd: float = 0.0
    last_used: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "team": self.team,
            "search_count": self.search_count,
            "selection_count": self.selection_count,
            "workflow_count": self.workflow_count,
            "estimated_cost_usd": self.estimated_cost_usd,
            "last_used": self.last_used,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  IN-PROCESS STATE  (swap for DB adapter in production)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_usage: Dict[str, UsageRecord] = {}       # key = "team:tool"
_audit_buffer: List[Dict[str, Any]] = []


def _usage_key(team: str, tool: str) -> str:
    return f"{team}:{tool}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERSISTENCE HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Cross-platform file-locking primitive ──────────────────────────
import tempfile
import sys as _sys

def _lock_file(fp):
    """Advisory exclusive lock — Windows (msvcrt) or POSIX (fcntl)."""
    if _sys.platform == "win32":
        import msvcrt
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)

def _unlock_file(fp):
    if _sys.platform == "win32":
        import msvcrt
        try:
            msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl
        fcntl.flock(fp, fcntl.LOCK_UN)


def _load_json(path: Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_json(path: Path, data: Any) -> None:
    """Atomic-ish write with advisory file lock.

    1. Acquire an exclusive lock via a sidecar ``.lock`` file.
    2. Write to a temp file in the same directory.
    3. Rename (atomic on POSIX, near-atomic on Windows NTFS) over the target.
    4. Release the lock.
    """
    lock_path = path.with_suffix(path.suffix + ".lock")
    try:
        lock_path.touch(exist_ok=True)
        with open(lock_path, "r+b") as lock_fp:
            try:
                _lock_file(lock_fp)
            except (OSError, IOError):
                # If we can't get the lock, fall through to best-effort write
                log.warning("Could not acquire lock for %s — writing without lock", path)
            fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
            try:
                import os as _os_mod
                _os_mod.write(fd, json.dumps(data, indent=2, default=str).encode("utf-8"))
                _os_mod.close(fd)
                # Atomic rename
                import shutil
                shutil.move(tmp, str(path))
            except Exception:
                # Clean up temp file on failure
                try:
                    import os as _os_mod2
                    _os_mod2.unlink(tmp)
                except OSError:
                    pass
                raise
            finally:
                _unlock_file(lock_fp)
    except OSError as exc:
        log.warning("Failed to save %s: %s", path, exc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUDIT LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def record_audit(
    action: AuditAction,
    *,
    actor: str = "system",
    team: str = "default",
    details: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Append an entry to the audit log."""
    entry = AuditEntry(action=action, actor=actor, team=team, details=details or {})
    _audit_buffer.append(entry.to_dict())

    # Flush to disk periodically (every 50 entries)
    if len(_audit_buffer) >= 50:
        _flush_audit()

    return entry


def _flush_audit() -> None:
    """Write buffered audit entries to disk."""
    if not _audit_buffer:
        return
    existing = _load_json(_AUDIT_LOG_PATH)
    if not isinstance(existing, list):
        existing = []
    existing.extend(_audit_buffer)
    # Keep last 10,000 entries
    if len(existing) > 10_000:
        existing = existing[-10_000:]
    _save_json(_AUDIT_LOG_PATH, existing)
    _audit_buffer.clear()


def get_audit_log(
    *,
    team: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Retrieve audit log entries with optional filters."""
    _flush_audit()
    entries = _load_json(_AUDIT_LOG_PATH)
    if not isinstance(entries, list):
        entries = []

    if team:
        entries = [e for e in entries if e.get("team") == team]
    if action:
        entries = [e for e in entries if e.get("action") == action]

    entries.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
    return entries[:limit]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USAGE TRACKING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def record_usage(
    tool_name: str,
    event: str = "search",         # search | selection | workflow
    *,
    team: str = "default",
    cost_usd: float = 0.0,
) -> None:
    """Record a usage event for a tool within a team."""
    key = _usage_key(team, tool_name)
    if key not in _usage:
        _usage[key] = UsageRecord(tool_name=tool_name, team=team)
    rec = _usage[key]
    rec.last_used = time.time()
    if event == "search":
        rec.search_count += 1
    elif event == "selection":
        rec.selection_count += 1
    elif event == "workflow":
        rec.workflow_count += 1
    rec.estimated_cost_usd += cost_usd


def get_usage(
    *,
    team: Optional[str] = None,
    tool_name: Optional[str] = None,
    sort_by: str = "selection_count",
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query usage records with optional filters."""
    items = list(_usage.values())
    if team:
        items = [u for u in items if u.team == team]
    if tool_name:
        items = [u for u in items if u.tool_name == tool_name]

    key_fn = lambda u: getattr(u, sort_by, 0)
    items.sort(key=key_fn, reverse=True)
    return [u.to_dict() for u in items[:limit]]


def get_cost_summary(team: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate cost summary across tools."""
    items = list(_usage.values())
    if team:
        items = [u for u in items if u.team == team]

    total_cost = sum(u.estimated_cost_usd for u in items)
    by_tool = {}
    for u in items:
        by_tool.setdefault(u.tool_name, 0.0)
        by_tool[u.tool_name] += u.estimated_cost_usd

    return {
        "total_cost_usd": round(total_cost, 2),
        "tool_count": len(by_tool),
        "by_tool": {k: round(v, 2) for k, v in sorted(by_tool.items(), key=lambda x: -x[1])},
        "team": team or "all",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COMPLIANCE DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def assess_compliance(
    required_standards: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Assess compliance posture across all tools in use."""
    required = set(s.upper() for s in (required_standards or ["GDPR", "SOC2"]))

    try:
        from .data import TOOLS
    except ImportError:
        try:
            from data import TOOLS
        except ImportError:
            TOOLS = []

    results = []
    compliant_count = 0
    for tool in TOOLS:
        tool_compliance = set(c.upper() for c in getattr(tool, "compliance", []))
        met = required & tool_compliance
        gaps = required - tool_compliance

        if not gaps:
            status = ComplianceStatus.COMPLIANT
            compliant_count += 1
        elif met:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT

        results.append({
            "tool": tool.name,
            "status": status.value,
            "met": sorted(met),
            "gaps": sorted(gaps),
        })

    return {
        "required_standards": sorted(required),
        "total_tools": len(TOOLS),
        "compliant": compliant_count,
        "partial": sum(1 for r in results if r["status"] == "partial"),
        "non_compliant": sum(1 for r in results if r["status"] == "non_compliant"),
        "tools": results,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  POLICY ENGINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_policy(
    name: str,
    rule_type: str,
    conditions: Dict[str, Any],
    *,
    description: str = "",
    created_by: str = "admin",
) -> Dict[str, Any]:
    """Create a new organisational policy."""
    policy = OrgPolicy(
        name=name,
        description=description,
        rule_type=rule_type,
        conditions=conditions,
        created_by=created_by,
    )
    policies = _load_json(_POLICIES_PATH)
    if not isinstance(policies, dict):
        policies = {}
    policies[policy.policy_id] = policy.to_dict()
    _save_json(_POLICIES_PATH, policies)
    record_audit(AuditAction.CONFIG_CHANGED, actor=created_by,
                 details={"policy_created": policy.policy_id, "name": name})
    return policy.to_dict()


def list_policies(active_only: bool = True) -> List[Dict[str, Any]]:
    """List all policies."""
    policies = _load_json(_POLICIES_PATH)
    if not isinstance(policies, dict):
        return []
    items = list(policies.values())
    if active_only:
        items = [p for p in items if p.get("active", True)]
    return items


def check_tool_allowed(tool_name: str, team: str = "default") -> Dict[str, Any]:
    """Check if a tool is allowed under current policies."""
    policies = _load_json(_POLICIES_PATH)
    if not isinstance(policies, dict):
        return {"allowed": True, "violations": []}

    violations = []
    for policy in policies.values():
        if not policy.get("active", True):
            continue
        rule_type = policy.get("rule_type", "")
        conditions = policy.get("conditions", {})

        if rule_type == "block_tool":
            blocked_tools = conditions.get("tools", [])
            if tool_name.lower() in [t.lower() for t in blocked_tools]:
                violations.append({
                    "policy": policy["name"],
                    "reason": f"Tool '{tool_name}' is blocked by policy",
                })

        elif rule_type == "require_compliance":
            required = conditions.get("standards", [])
            try:
                from .data import TOOLS
            except ImportError:
                try:
                    from data import TOOLS
                except ImportError:
                    TOOLS = []
            for t in TOOLS:
                if t.name.lower() == tool_name.lower():
                    tool_compliance = {c.upper() for c in getattr(t, "compliance", [])}
                    missing = [s for s in required if s.upper() not in tool_compliance]
                    if missing:
                        violations.append({
                            "policy": policy["name"],
                            "reason": f"Missing compliance: {', '.join(missing)}",
                        })
                    break

        elif rule_type == "budget_cap":
            cap = conditions.get("max_monthly_usd", float("inf"))
            key = _usage_key(team, tool_name)
            if key in _usage and _usage[key].estimated_cost_usd > cap:
                violations.append({
                    "policy": policy["name"],
                    "reason": f"Budget cap exceeded: ${_usage[key].estimated_cost_usd:.2f} > ${cap}",
                })

    allowed = len(violations) == 0
    if not allowed:
        record_audit(AuditAction.POLICY_VIOLATION, team=team,
                     details={"tool": tool_name, "violations": violations})

    return {"allowed": allowed, "tool": tool_name, "team": team, "violations": violations}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GOVERNANCE DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def governance_dashboard(team: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate governance dashboard data."""
    return {
        "usage": get_usage(team=team, limit=20),
        "cost_summary": get_cost_summary(team=team),
        "compliance": assess_compliance(),
        "active_policies": len(list_policies()),
        "recent_audit": get_audit_log(team=team, limit=10),
    }
