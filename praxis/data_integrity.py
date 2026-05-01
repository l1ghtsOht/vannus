"""
data_integrity.py — Static-data prompt-injection scanner

Defense against indirect prompt injection where an attacker tries to sneak
instructions into static content (tool descriptions, llms.txt, legal docs)
that an AI agent or downstream LLM might read and execute.

Scope:
  - Tool catalog (data.py)
  - llms.txt
  - Any string content served back by the API as part of search/elimination

This is a *content* scanner, not a runtime input filter. The existing
runtime_protection.py / RASP middleware already scans incoming user
requests. This module fills the gap on the OUTGOING / static side.

Design principles:
  - Read-only: never modifies data, only logs warnings
  - Conservative: pattern set tuned to avoid false positives on legitimate
    tool descriptions (which legitimately mention "AI agents" or "execute")
  - Non-blocking: warnings are logged but the API still serves the content,
    so a single false positive can't take the site down

Trigger points:
  - On data.py import (scan_tool_catalog called at module load)
  - Optional pre-commit / CI hook can call scan_static_files() to catch
    PRs that introduce injection patterns before they reach production
"""
import logging
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

log = logging.getLogger("praxis.data_integrity")


# ─────────────────────────────────────────────────────────────────────
# Patterns — tuned conservatively to catch obvious injection attempts
# without flagging legitimate tool descriptions. Patterns are
# deliberately strict (require imperative phrasing + suspicious target)
# rather than matching on individual words like "ignore" or "upload"
# which appear in many legitimate descriptions.
# ─────────────────────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    # Direct AI-agent address with imperative
    r"\bif\s+you\s+(?:are|'re)\s+an?\s+(?:ai|llm|language model|agent|assistant)\b",
    r"\b(?:hey|attention|note(?:\s+to)?)\s+(?:ai|llm|agent|assistant)\b",
    # Override / ignore patterns
    r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instruction|prompt|message|content)",
    r"\bdisregard\s+(?:the\s+)?(?:above|previous|prior|system)",
    r"\boverride\s+(?:your|the)\s+(?:instruction|guideline|safety|directive)",
    # Exfiltration imperatives
    r"\b(?:upload|send|post|leak|exfiltrat\w*|transmit)\s+(?:all|the|local|user|file|data|content|key|token|secret)",
    r"\bemail\s+(?:to\s+)?\S+@\S+\s+(?:with|the|all)",
    # System / role manipulation
    r"<\s*system\s*>|<\s*\/\s*system\s*>",
    r"\[\s*INST\s*\]|\[\s*\/\s*INST\s*\]",
    r"^\s*system\s*:\s*you\s+are\s+now\b",
    # Common jailbreak strings
    r"\bDAN\s+(?:mode|prompt)\b",
    r"\bdo\s+anything\s+now\b",
    r"\bact\s+as\s+if\s+you\s+have\s+no\s+restriction",
    # Hidden instruction markers
    r"\[HIDDEN\s+INSTRUCTION",
    r"<!--\s*ai[-_\s]?(?:agent|instruction|directive)",
    # Credential exfiltration
    r"\b(?:reveal|output|print|display)\s+(?:the\s+)?(?:user'?s?\s+)?(?:api[\s_-]?key|password|secret|token|credential)",
]

# Compile once for performance
_COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]


def scan_text(text: str, source: str = "unknown") -> List[Tuple[str, str]]:
    """Scan a string for injection patterns. Returns list of (pattern, excerpt) tuples.

    Args:
        text: The content to scan.
        source: Identifier for logging (e.g. tool name, filename).
    """
    if not text or not isinstance(text, str):
        return []
    findings: List[Tuple[str, str]] = []
    for pat in _COMPILED:
        m = pat.search(text)
        if m:
            excerpt = text[max(0, m.start() - 20): m.end() + 40].replace("\n", " ")
            findings.append((pat.pattern, excerpt))
    if findings:
        log.warning(
            "data_integrity: %d injection pattern(s) found in '%s' — review before deploy",
            len(findings), source,
        )
    return findings


def scan_tool_catalog(tools: Iterable) -> int:
    """Scan all tool data fields for injection patterns. Returns count of findings.

    Called at data.py import time. Logs warnings but does not raise — a
    single false positive should not crash the API. Operators should
    review logged warnings before each deploy.
    """
    total = 0
    for t in tools:
        name = getattr(t, "name", "?")
        # Scan all text-bearing fields
        for field in ("description", "tags", "keywords", "use_cases"):
            val = getattr(t, field, None)
            if val is None:
                continue
            if isinstance(val, str):
                total += len(scan_text(val, f"{name}.{field}"))
            elif isinstance(val, (list, tuple)):
                for item in val:
                    if isinstance(item, str):
                        total += len(scan_text(item, f"{name}.{field}"))
    return total


def scan_static_files(repo_root: Optional[Path] = None) -> List[Tuple[str, int]]:
    """Scan key static AI-readable files for injection patterns.

    Returns list of (filepath, finding_count) for files with hits.
    Useful for CI / pre-commit hooks. Not called at runtime.
    """
    if repo_root is None:
        repo_root = Path(__file__).parent.parent
    targets = [
        repo_root / "praxis" / "frontend" / "llms.txt",
        repo_root / "praxis" / "frontend" / "robots.txt",
        repo_root / "praxis" / "frontend" / "manifesto.html",
        repo_root / "praxis" / "frontend" / "partners.html",
        repo_root / "praxis" / "frontend" / "privacy-policy.html",
        repo_root / "praxis" / "frontend" / "terms-of-service.html",
        repo_root / "praxis" / "feedback.json",
        repo_root / "praxis" / "usage.json",
    ]
    results: List[Tuple[str, int]] = []
    for target in targets:
        if not target.exists():
            continue
        try:
            content = target.read_text(encoding="utf-8", errors="ignore")
            findings = scan_text(content, str(target))
            if findings:
                results.append((str(target), len(findings)))
        except Exception as exc:
            log.debug("scan_static_files: skipped %s (%s)", target, exc)
    return results
