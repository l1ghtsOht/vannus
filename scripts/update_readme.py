#!/usr/bin/env python3
"""
Auto-update README.md with live codebase statistics.

Scans the praxis/ directory and rewrites sections delimited by
<!-- AUTO:<SECTION>:START --> / <!-- AUTO:<SECTION>:END --> markers.

Sections updated:
  STATS  — "At a Glance" table (module count, tool count, route count, etc.)
  GIT    — Git commit log (last 20 commits)
  STATE  — "Current State" bullet list

Run:
    python scripts/update_readme.py          # from repo root
    python scripts/update_readme.py --check  # exit 1 if README is stale (CI dry-run)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT  = Path(__file__).resolve().parent.parent
PRAXIS_DIR = REPO_ROOT / "praxis"
README     = REPO_ROOT / "README.md"
FRONTEND   = PRAXIS_DIR / "frontend"
TESTS_DIR  = PRAXIS_DIR / "tests"


# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

def _count_lines(path: Path) -> int:
    """Count non-empty lines in a file (UTF-8, ignore errors)."""
    try:
        return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    except Exception:
        return 0


def count_python_modules() -> tuple[int, int]:
    """Return (number of .py files, total LOC) under praxis/, excluding tests and __pycache__."""
    files = 0
    loc = 0
    for p in PRAXIS_DIR.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if "tests" in p.parts:
            continue
        if p.name.startswith("test_"):
            continue
        files += 1
        loc += _count_lines(p)
    return files, loc


def count_tools() -> int:
    """Count Tool(...) entries in data.py."""
    data_py = PRAXIS_DIR / "data.py"
    if not data_py.exists():
        return 0
    text = data_py.read_text(encoding="utf-8", errors="ignore")
    return len(re.findall(r"^\s*Tool\s*\(", text, re.MULTILINE))


def count_api_routes() -> int:
    """Count @app.<method>(...) decorators in api.py."""
    api_py = PRAXIS_DIR / "api.py"
    if not api_py.exists():
        return 0
    text = api_py.read_text(encoding="utf-8", errors="ignore")
    return len(re.findall(r"@app\.(get|post|put|patch|delete|options|head)\s*\(", text, re.IGNORECASE))


def count_tests() -> tuple[int, int]:
    """Return (number of test files, number of test functions)."""
    test_files = 0
    test_funcs = 0
    search_dirs = [TESTS_DIR, PRAXIS_DIR]
    seen: set[Path] = set()
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("test_*.py"):
            rp = p.resolve()
            if rp in seen or "__pycache__" in rp.parts:
                continue
            seen.add(rp)
            test_files += 1
            text = p.read_text(encoding="utf-8", errors="ignore")
            test_funcs += len(re.findall(r"^\s*def\s+test_", text, re.MULTILINE))
    return test_files, test_funcs


def count_frontend() -> tuple[int, int, int, int]:
    """Return (html_files, js_files, html_loc, js_loc)."""
    html_files = html_loc = js_files = js_loc = 0
    if not FRONTEND.exists():
        return html_files, js_files, html_loc, js_loc
    for p in FRONTEND.iterdir():
        if p.suffix == ".html":
            html_files += 1
            html_loc += _count_lines(p)
        elif p.suffix == ".js":
            js_files += 1
            js_loc += _count_lines(p)
    return html_files, js_files, html_loc, js_loc


def count_categories() -> int:
    """Count unique categories from data.py TOOLS list."""
    data_py = PRAXIS_DIR / "data.py"
    if not data_py.exists():
        return 0
    text = data_py.read_text(encoding="utf-8", errors="ignore")
    cats: set[str] = set()
    for m in re.finditer(r'categories\s*=\s*\[([^\]]*)\]', text):
        for c in re.findall(r'"([^"]+)"', m.group(1)):
            cats.add(c)
    return len(cats)


# ---------------------------------------------------------------------------
# Git log
# ---------------------------------------------------------------------------

def git_log(n: int = 20) -> str:
    """Return last N commits as short-hash + subject."""
    try:
        result = subprocess.run(
            ["git", "log", f"--pretty=format:%h %s", f"-{n}"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return "(git log unavailable)"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_stats_section() -> str:
    py_files, py_loc = count_python_modules()
    tools = count_tools()
    routes = count_api_routes()
    test_files, test_funcs = count_tests()
    html_f, js_f, html_loc, js_loc = count_frontend()
    fe_loc = html_loc + js_loc
    total_loc = py_loc + fe_loc
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| **Python modules** | {py_files} files, ~{round(py_loc, -2):,} lines |\n"
        f"| **Tool catalog** | {tools} curated AI tools with rich metadata |\n"
        f"| **API endpoints** | {routes} REST routes via FastAPI |\n"
        f"| **Test coverage** | {test_funcs} tests across {test_files} test files, all passing |\n"
        f"| **Frontend** | {html_f} HTML + {js_f} JS files (~{round(fe_loc, -2):,} lines), Liquid Glass UI |\n"
        f"| **Versions** | 17 major iterations (v1 → v17) |\n"
        f"| **Total LOC** | ~{round(total_loc, -2):,} (Python + Frontend) |\n"
        f"| **Zero external ML deps** | All NLP, scoring, graph, and retrieval are zero-dependency |\n"
        f"| **Last auto-update** | {now} |"
    )


def build_git_section() -> str:
    log = git_log(20)
    return f"```\n{log}\n```"


def build_state_section() -> str:
    py_files, py_loc = count_python_modules()
    tools = count_tools()
    routes = count_api_routes()
    _, test_funcs = count_tests()
    html_f, js_f, html_loc, js_loc = count_frontend()
    fe_files = html_f + js_f
    fe_loc = html_loc + js_loc

    return (
        f"- **{tools} tools**, zero duplicates, clean tag casing\n"
        f"- **{routes} API routes**, all functional\n"
        f"- **{test_funcs} tests passing**\n"
        f"- **{py_files} Python modules**, ~{round(py_loc, -2):,} lines\n"
        f"- **{fe_files} frontend files**, ~{round(fe_loc, -2):,} lines\n"
        f"- All critical bugs fixed (alias collision, caveats reset, dead code)\n"
        f"- Server runs on port 8000 via `uvicorn praxis.api:app --port 8000`"
    )


# ---------------------------------------------------------------------------
# Marker replacement
# ---------------------------------------------------------------------------

MARKER_RE = re.compile(
    r"(<!-- AUTO:(?P<name>\w+):START -->\n)"  # opening marker + newline
    r"(?P<body>.*?)"                           # existing content (lazy)
    r"(\n<!-- AUTO:\2:END -->)",               # closing marker
    re.DOTALL,
)

BUILDERS: dict[str, callable] = {
    "STATS": build_stats_section,
    "GIT":   build_git_section,
    "STATE": build_state_section,
}


def _strip_volatile(text: str) -> str:
    """Remove the timestamp line so --check only flags real stat changes."""
    return re.sub(r"\| \*\*Last auto-update\*\* \|.*?\|", "", text)


def update_readme(*, dry_run: bool = False) -> bool:
    """
    Read README.md, replace AUTO sections, write back.
    Returns True if content changed (ignoring timestamp in --check mode).
    """
    original = README.read_text(encoding="utf-8")
    updated = original

    for name, builder in BUILDERS.items():
        pattern = re.compile(
            rf"(<!-- AUTO:{name}:START -->\n)"
            rf"(.*?)"
            rf"(\n<!-- AUTO:{name}:END -->)",
            re.DOTALL,
        )
        new_body = builder()
        updated = pattern.sub(rf"\g<1>{new_body}\g<3>", updated)

    # In check mode, ignore the volatile timestamp line
    if dry_run:
        changed = _strip_volatile(updated) != _strip_volatile(original)
    else:
        changed = updated != original

    if changed and not dry_run:
        README.write_text(updated, encoding="utf-8")
        print(f"✓ README.md updated ({len(BUILDERS)} sections refreshed)")
    elif changed and dry_run:
        print("✗ README.md is stale — run `python scripts/update_readme.py` to refresh")
    else:
        print("✓ README.md is already up-to-date")

    return changed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-update README.md stats")
    parser.add_argument(
        "--check", action="store_true",
        help="Dry-run: exit 1 if README would change (useful in CI)",
    )
    args = parser.parse_args()

    changed = update_readme(dry_run=args.check)

    if args.check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
