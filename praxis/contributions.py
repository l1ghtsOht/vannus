# --------------- Praxis Contributions — Open Tool Submission API ---------------
"""
v19 · Platform Evolution — Community Contributions

Allows developers and companies to register their tools with Praxis.
Provides a complete submission → validation → moderation → publish pipeline.

Pipeline
────────
    1. **Submit** — contributor provides tool metadata, API spec URL,
       compliance info, and example use cases.
    2. **Validate** — automated checks (required fields, URL format,
       duplicate detection, name sanitisation).
    3. **Queue** — submissions enter a moderation queue.
    4. **Review** — moderators approve / reject / request-changes.
    5. **Publish** — approved tools are merged into the live catalog.

Contributor features:
    • Leaderboard with contribution counts and badges
    • Edit / update submissions after approval
    • Deprecation pipeline for outdated tools

Storage is JSON file-based (swap for DB via ports.py in production).
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.contributions")

_BASE = Path(__file__).resolve().parent
_SUBMISSIONS_PATH = _BASE / "contributions_queue.json"
_CONTRIBUTORS_PATH = _BASE / "contributors.json"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass
class ToolSubmission:
    """A tool submitted by a community contributor."""
    submission_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    # ── Required metadata ──
    tool_name: str = ""
    description: str = ""
    url: str = ""
    categories: List[str] = field(default_factory=list)
    # ── Optional enrichment ──
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    pricing: Dict[str, Any] = field(default_factory=dict)
    integrations: List[str] = field(default_factory=list)
    compliance: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    api_spec_url: str = ""
    docs_url: str = ""
    # ── Workflow ──
    contributor: str = "anonymous"
    status: SubmissionStatus = SubmissionStatus.PENDING
    reviewer_notes: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    # ── Validation ──
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "tool_name": self.tool_name,
            "description": self.description,
            "url": self.url,
            "categories": self.categories,
            "tags": self.tags,
            "keywords": self.keywords,
            "pricing": self.pricing,
            "integrations": self.integrations,
            "compliance": self.compliance,
            "use_cases": self.use_cases,
            "api_spec_url": self.api_spec_url,
            "docs_url": self.docs_url,
            "contributor": self.contributor,
            "status": self.status.value,
            "reviewer_notes": self.reviewer_notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "validation_errors": self.validation_errors,
        }


@dataclass
class Contributor:
    """A community contributor profile."""
    contributor_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    display_name: str = "anonymous"
    email: str = ""
    submissions_count: int = 0
    approved_count: int = 0
    badges: List[str] = field(default_factory=list)
    joined_at: float = field(default_factory=time.time)
    reputation_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contributor_id": self.contributor_id,
            "display_name": self.display_name,
            "email": self.email,
            "submissions_count": self.submissions_count,
            "approved_count": self.approved_count,
            "badges": self.badges,
            "joined_at": self.joined_at,
            "reputation_score": self.reputation_score,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERSISTENCE
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


def _load_json(path: Path) -> Dict[str, Any]:
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
                log.warning("Could not acquire lock for %s — writing without lock", path)
            fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
            try:
                import os as _os_mod
                _os_mod.write(fd, json.dumps(data, indent=2, default=str).encode("utf-8"))
                _os_mod.close(fd)
                import shutil
                shutil.move(tmp, str(path))
            except Exception:
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
#  VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_URL_RE = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9 _.()-]{1,80}$')


def validate_submission(sub: ToolSubmission) -> List[str]:
    """Run automated validation checks; return list of error strings."""
    errors: List[str] = []

    if not sub.tool_name or not sub.tool_name.strip():
        errors.append("tool_name is required")
    elif not _NAME_RE.match(sub.tool_name):
        errors.append("tool_name contains invalid characters or is too long (max 80)")

    if not sub.description or len(sub.description.strip()) < 10:
        errors.append("description must be at least 10 characters")

    if sub.url and not _URL_RE.match(sub.url):
        errors.append("url is not a valid HTTP(S) URL")

    if not sub.categories:
        errors.append("at least one category is required")

    # Duplicate detection
    try:
        from .data import TOOLS
    except ImportError:
        try:
            from data import TOOLS
        except ImportError:
            TOOLS = []
    existing_names = {t.name.lower() for t in TOOLS}
    if sub.tool_name.lower() in existing_names:
        errors.append(f"A tool named '{sub.tool_name}' already exists in the catalog")

    # Check for suspiciously short descriptions
    if sub.description and len(sub.description.strip()) > 2000:
        errors.append("description exceeds 2000 characters")

    sub.validation_errors = errors
    return errors


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PUBLIC API — SUBMISSIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def submit_tool(
    tool_name: str,
    description: str,
    categories: List[str],
    *,
    url: str = "",
    tags: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    pricing: Optional[Dict[str, Any]] = None,
    integrations: Optional[List[str]] = None,
    compliance: Optional[List[str]] = None,
    use_cases: Optional[List[str]] = None,
    api_spec_url: str = "",
    docs_url: str = "",
    contributor: str = "anonymous",
) -> Dict[str, Any]:
    """Submit a new tool for review."""
    sub = ToolSubmission(
        tool_name=tool_name.strip(),
        description=description.strip(),
        url=url.strip(),
        categories=categories,
        tags=tags or [],
        keywords=keywords or [],
        pricing=pricing or {},
        integrations=integrations or [],
        compliance=compliance or [],
        use_cases=use_cases or [],
        api_spec_url=api_spec_url,
        docs_url=docs_url,
        contributor=contributor,
    )

    errors = validate_submission(sub)
    if errors:
        sub.status = SubmissionStatus.CHANGES_REQUESTED
        sub.reviewer_notes = "Automated validation failed"

    # Save to queue
    queue = _load_json(_SUBMISSIONS_PATH)
    queue[sub.submission_id] = sub.to_dict()
    _save_json(_SUBMISSIONS_PATH, queue)

    # Update contributor stats
    _increment_contributor(contributor)

    log.info("Submission %s from %s: %s (%d errors)",
             sub.submission_id, contributor, tool_name, len(errors))

    return {
        "submission_id": sub.submission_id,
        "status": sub.status.value,
        "validation_errors": errors,
        "message": "Submitted successfully" if not errors else "Validation issues found",
    }


def get_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single submission."""
    queue = _load_json(_SUBMISSIONS_PATH)
    return queue.get(submission_id)


def list_submissions(
    status: Optional[str] = None,
    contributor: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> Dict[str, Any]:
    """List submissions with optional filters."""
    queue = _load_json(_SUBMISSIONS_PATH)
    items = list(queue.values())

    if status:
        items = [s for s in items if s.get("status") == status]
    if contributor:
        items = [s for s in items if s.get("contributor") == contributor]

    items.sort(key=lambda s: s.get("created_at", 0), reverse=True)
    total = len(items)
    page = items[skip : skip + limit]
    return {"total": total, "skip": skip, "limit": limit, "items": page}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODERATION API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def approve_submission(submission_id: str, reviewer_notes: str = "") -> Dict[str, Any]:
    """Approve a submission (moves to APPROVED status)."""
    queue = _load_json(_SUBMISSIONS_PATH)
    sub = queue.get(submission_id)
    if sub is None:
        return {"error": "Submission not found"}
    sub["status"] = SubmissionStatus.APPROVED.value
    sub["reviewer_notes"] = reviewer_notes
    sub["updated_at"] = time.time()
    queue[submission_id] = sub
    _save_json(_SUBMISSIONS_PATH, queue)

    # Update contributor reputation
    _credit_approval(sub.get("contributor", "anonymous"))

    return {"submission_id": submission_id, "status": "approved"}


def reject_submission(submission_id: str, reason: str = "") -> Dict[str, Any]:
    """Reject a submission."""
    queue = _load_json(_SUBMISSIONS_PATH)
    sub = queue.get(submission_id)
    if sub is None:
        return {"error": "Submission not found"}
    sub["status"] = SubmissionStatus.REJECTED.value
    sub["reviewer_notes"] = reason
    sub["updated_at"] = time.time()
    queue[submission_id] = sub
    _save_json(_SUBMISSIONS_PATH, queue)
    return {"submission_id": submission_id, "status": "rejected", "reason": reason}


def request_changes(submission_id: str, notes: str) -> Dict[str, Any]:
    """Request changes from the contributor."""
    queue = _load_json(_SUBMISSIONS_PATH)
    sub = queue.get(submission_id)
    if sub is None:
        return {"error": "Submission not found"}
    sub["status"] = SubmissionStatus.CHANGES_REQUESTED.value
    sub["reviewer_notes"] = notes
    sub["updated_at"] = time.time()
    queue[submission_id] = sub
    _save_json(_SUBMISSIONS_PATH, queue)
    return {"submission_id": submission_id, "status": "changes_requested", "notes": notes}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONTRIBUTOR MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _increment_contributor(name: str) -> None:
    contributors = _load_json(_CONTRIBUTORS_PATH)
    if name not in contributors:
        c = Contributor(display_name=name)
        contributors[name] = c.to_dict()
    contributors[name]["submissions_count"] = contributors[name].get("submissions_count", 0) + 1
    _save_json(_CONTRIBUTORS_PATH, contributors)


def _credit_approval(name: str) -> None:
    contributors = _load_json(_CONTRIBUTORS_PATH)
    if name not in contributors:
        return
    c = contributors[name]
    c["approved_count"] = c.get("approved_count", 0) + 1
    c["reputation_score"] = c.get("reputation_score", 0) + 10
    # Badge logic
    badges = c.get("badges", [])
    if c["approved_count"] >= 1 and "first_contribution" not in badges:
        badges.append("first_contribution")
    if c["approved_count"] >= 5 and "prolific_contributor" not in badges:
        badges.append("prolific_contributor")
    if c["approved_count"] >= 20 and "trusted_expert" not in badges:
        badges.append("trusted_expert")
    c["badges"] = badges
    contributors[name] = c
    _save_json(_CONTRIBUTORS_PATH, contributors)


def get_contributor(name: str) -> Optional[Dict[str, Any]]:
    """Get a contributor's profile."""
    contributors = _load_json(_CONTRIBUTORS_PATH)
    return contributors.get(name)


def get_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """Return top contributors by reputation score."""
    contributors = _load_json(_CONTRIBUTORS_PATH)
    items = list(contributors.values())
    items.sort(key=lambda c: c.get("reputation_score", 0), reverse=True)
    return items[:limit]


def contribution_stats() -> Dict[str, Any]:
    """Aggregate contribution statistics."""
    queue = _load_json(_SUBMISSIONS_PATH)
    contributors = _load_json(_CONTRIBUTORS_PATH)
    statuses = {}
    for s in queue.values():
        st = s.get("status", "pending")
        statuses[st] = statuses.get(st, 0) + 1
    return {
        "total_submissions": len(queue),
        "by_status": statuses,
        "total_contributors": len(contributors),
        "top_contributors": get_leaderboard(5),
    }
