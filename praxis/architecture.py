# ────────────────────────────────────────────────────────────────────
# architecture.py — Dependency Governance & Clean Architecture Enforcement
# ────────────────────────────────────────────────────────────────────
"""
Automated architectural fitness functions that enforce Clean Architecture
boundaries across the Praxis codebase.  Prevents "layer skipping" where
Presentation routes import directly from Persistence modules.

Layer model::

    ┌─────────────────────────────────────────┐
    │  PRESENTATION  (api.py, routes)         │  ← HTTP / FastAPI
    ├─────────────────────────────────────────┤
    │  WORKFLOW      (engine, interpreter,    │  ← Business logic
    │    prism, orchestration, reason, ...)   │
    ├─────────────────────────────────────────┤
    │  PERSISTENCE   (storage, persistence)   │  ← SQLite / JSON
    └─────────────────────────────────────────┘

Rules enforced:
    1. Presentation MUST NOT import from Persistence directly.
    2. Persistence MUST NOT import from Presentation.
    3. No circular import chains longer than 2 hops.
    4. All internal imports MUST be absolute from the package root
       (no runpy / ``__main__`` dual-path shattering).

Usage::

    from praxis.architecture import (
        audit_imports, check_layer_violations,
        dependency_graph, architecture_report,
    )

    report = architecture_report()
    assert report["violations"] == 0
"""

from __future__ import annotations

import ast
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

log = logging.getLogger("praxis.architecture")

# ── Package root ──
_PKG_DIR = Path(__file__).resolve().parent


# ╔════════════════════════════════════════════════════════════════════╗
# ║  LAYER DEFINITIONS                                               ║
# ╚════════════════════════════════════════════════════════════════════╝

# Presentation layer — HTTP routing, request/response handling
PRESENTATION_MODULES: Set[str] = {
    "api",
}

# Persistence layer — all database / file I/O
PERSISTENCE_MODULES: Set[str] = {
    "storage",
    "persistence",
}

# Workflow / domain layer — everything else (unrestricted)
# All modules not in PRESENTATION or PERSISTENCE are considered workflow.

# ── Forbidden import pairs (source_layer → forbidden_target_layer) ──
FORBIDDEN_EDGES: List[Tuple[str, str]] = [
    ("presentation", "persistence"),   # api.py must not import storage.py
    ("persistence", "presentation"),   # storage.py must not import api.py
]


def _classify_module(name: str) -> str:
    """Map a module stem to its architectural layer."""
    stem = name.replace("praxis.", "").split(".")[0]
    if stem in PRESENTATION_MODULES:
        return "presentation"
    if stem in PERSISTENCE_MODULES:
        return "persistence"
    return "workflow"


# ╔════════════════════════════════════════════════════════════════════╗
# ║  IMPORT EXTRACTION  (AST-based)                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def _extract_imports(source: str) -> List[str]:
    """
    Parse a Python source string and extract all imported module names.

    Returns resolved module stems (e.g., ``storage`` from ``from .storage import ...``).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Relative imports (from .storage import ...) → "storage"
                parts = node.module.split(".")
                # Skip empty parts from leading dots
                stem = parts[-1] if parts else ""
                if stem:
                    imports.append(stem)
    return imports


def _extract_imports_from_file(path: Path) -> List[str]:
    """Read and parse imports from a ``.py`` file."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []
    return _extract_imports(source)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  DEPENDENCY GRAPH                                                ║
# ╚════════════════════════════════════════════════════════════════════╝

def dependency_graph() -> Dict[str, List[str]]:
    """
    Build the complete import dependency graph for the praxis package.

    Returns::

        {
            "engine": ["data", "intelligence", "config", "diagnostics"],
            "api": ["engine", "interpreter", ...],
            ...
        }
    """
    graph: Dict[str, List[str]] = {}
    praxis_modules = _discover_package_modules()

    for path in praxis_modules:
        stem = path.stem
        raw_imports = _extract_imports_from_file(path)
        # Only keep imports that reference other praxis modules
        internal = [i for i in raw_imports if i in {p.stem for p in praxis_modules}]
        graph[stem] = sorted(set(internal))

    return graph


def _discover_package_modules() -> List[Path]:
    """Find all non-test, non-pycache ``.py`` files in the package."""
    result = []
    for f in sorted(_PKG_DIR.rglob("*.py")):
        rel = str(f.relative_to(_PKG_DIR))
        if "__pycache__" in rel or "egg-info" in rel:
            continue
        if f.stem == "__init__":
            continue
        # Skip test files for architecture analysis
        if f.stem.startswith("test_") or "tests" in f.parts:
            continue
        result.append(f)
    return result


# ╔════════════════════════════════════════════════════════════════════╗
# ║  LAYER VIOLATION DETECTION                                       ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class LayerViolation:
    """A single architectural boundary violation."""
    source_module: str
    source_layer: str
    target_module: str
    target_layer: str
    rule: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_module": self.source_module,
            "source_layer": self.source_layer,
            "target_module": self.target_module,
            "target_layer": self.target_layer,
            "rule": self.rule,
        }


def check_layer_violations() -> List[LayerViolation]:
    """
    Scan the dependency graph for forbidden cross-layer imports.

    Returns a list of all violations found.
    """
    graph = dependency_graph()
    violations: List[LayerViolation] = []

    for source_mod, targets in graph.items():
        source_layer = _classify_module(source_mod)
        for target_mod in targets:
            target_layer = _classify_module(target_mod)
            for forbidden_source, forbidden_target in FORBIDDEN_EDGES:
                if source_layer == forbidden_source and target_layer == forbidden_target:
                    violations.append(LayerViolation(
                        source_module=source_mod,
                        source_layer=source_layer,
                        target_module=target_mod,
                        target_layer=target_layer,
                        rule=f"{forbidden_source} → {forbidden_target}",
                    ))

    return violations


# ╔════════════════════════════════════════════════════════════════════╗
# ║  CIRCULAR DEPENDENCY DETECTION                                   ║
# ╚════════════════════════════════════════════════════════════════════╝

def detect_cycles(max_depth: int = 5) -> List[List[str]]:
    """
    Detect circular import chains in the dependency graph.

    Returns a list of cycles, each represented as a list of module names.
    Uses DFS with backtracking.
    """
    graph = dependency_graph()
    cycles: List[List[str]] = []
    visited: Set[str] = set()

    def _dfs(node: str, path: List[str]) -> None:
        if len(path) > max_depth:
            return
        if node in path:
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            # Normalize cycle (rotate to smallest element) for dedup
            min_idx = cycle.index(min(cycle[:-1]))
            normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
            if normalized not in cycles:
                cycles.append(normalized)
            return
        for dep in graph.get(node, []):
            _dfs(dep, path + [node])

    for module in graph:
        _dfs(module, [])

    return cycles


# ╔════════════════════════════════════════════════════════════════════╗
# ║  MODULE METRICS                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def module_metrics() -> List[Dict[str, Any]]:
    """
    Compute per-module metrics: line count, import count, layer, fan-in/fan-out.
    """
    graph = dependency_graph()
    modules = _discover_package_modules()

    # Compute fan-in (who imports me)
    fan_in: Dict[str, int] = defaultdict(int)
    for _src, targets in graph.items():
        for t in targets:
            fan_in[t] += 1

    results = []
    for path in modules:
        stem = path.stem
        try:
            lines = len(path.read_text(encoding="utf-8").splitlines())
        except Exception:
            lines = 0

        deps = graph.get(stem, [])
        results.append({
            "module": stem,
            "layer": _classify_module(stem),
            "lines": lines,
            "fan_out": len(deps),     # how many modules I import
            "fan_in": fan_in.get(stem, 0),  # how many modules import me
            "dependencies": deps,
        })

    results.sort(key=lambda x: x["lines"], reverse=True)
    return results


# ╔════════════════════════════════════════════════════════════════════╗
# ║  ENTRY-POINT VALIDATION                                         ║
# ╚════════════════════════════════════════════════════════════════════╝

def check_entrypoint_hygiene() -> Dict[str, Any]:
    """
    Verify that no modules use ``if __name__ == '__main__'`` patterns
    that could cause dual-instantiation of singletons when the same
    module is both executed directly and imported as a package member.

    The project should use ``[project.scripts]`` in pyproject.toml
    exclusively to define entry points.
    """
    violations = []
    for path in _discover_package_modules():
        try:
            source = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if '__name__' in source and "'__main__'" in source or '__name__' in source and '"__main__"' in source:
            violations.append(path.stem)

    return {
        "clean": len(violations) == 0,
        "modules_with_main_guard": violations,
        "recommendation": (
            "Remove __name__ == '__main__' guards. Use [project.scripts] "
            "in pyproject.toml for all entry points."
            if violations else "All modules are clean."
        ),
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  COMPREHENSIVE REPORT                                            ║
# ╚════════════════════════════════════════════════════════════════════╝

def architecture_report() -> Dict[str, Any]:
    """
    Run all architectural fitness functions and return a consolidated report.

    This is the function to call in CI — fail the build if ``violations > 0``.
    """
    violations = check_layer_violations()
    cycles = detect_cycles()
    entrypoint = check_entrypoint_hygiene()
    metrics = module_metrics()

    total_lines = sum(m["lines"] for m in metrics)
    total_modules = len(metrics)

    # Instability metric (Robert C. Martin):
    # I = fan_out / (fan_in + fan_out)  — 0 = maximally stable, 1 = maximally unstable
    for m in metrics:
        total_fan = m["fan_in"] + m["fan_out"]
        m["instability"] = round(m["fan_out"] / total_fan, 2) if total_fan else 0.0

    return {
        "total_modules": total_modules,
        "total_lines": total_lines,
        "layer_violations": [v.to_dict() for v in violations],
        "violation_count": len(violations),
        "cycles": cycles,
        "cycle_count": len(cycles),
        "entrypoint_hygiene": entrypoint,
        "module_metrics": metrics,
        "health": "clean" if not violations and not cycles else "violations_detected",
    }
