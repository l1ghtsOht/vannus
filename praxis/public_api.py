# ────────────────────────────────────────────────────────────────────
# public_api.py — Praxis Public API Surface
#
# 12 enterprise-facing endpoints.  Everything else stays internal.
# This module is the product layer the CTO review called for:
#   "Upload your stack → get optimized AI stack + risks"
#
# All responses pass through the metric translator so external
# consumers see enterprise language, not research jargon.
# ────────────────────────────────────────────────────────────────────
"""
Public API v1 — the focused product surface.

Endpoints:
    POST /api/v1/analyze          → Describe needs → get AI stack recommendation
    POST /api/v1/stack/optimize   → Upload current stack → get optimized stack + risks
    POST /api/v1/compare          → Side-by-side tool comparison
    POST /api/v1/migrate          → Migration plan between tools
    GET  /api/v1/vendor/{name}    → Vendor risk report
    POST /api/v1/whatif            → What-if scenario simulation
    GET  /api/v1/compliance        → Compliance posture snapshot
    POST /api/v1/cost              → Cost analysis for a model/stack
    GET  /api/v1/economics         → AI economics dashboard
    GET  /api/v1/health            → System health check
    GET  /api/v1/docs              → API documentation
    POST /api/v1/feedback          → Submit feedback
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

# ── Internal imports (graceful fallback) ─────────────────────────
try:
    from .interpreter import interpret
    from .engine import find_tools
    from .stack import compose_stack
    from .compare_stack import compare_my_stack
    from .migration import migration_plan
    from .profile import load_profile, save_profile, UserProfile
    from .metric_translator import translate_response, build_risk_summary
except ImportError:
    try:
        from interpreter import interpret
        from engine import find_tools
        from stack import compose_stack
        from compare_stack import compare_my_stack
        from migration import migration_plan
        from profile import load_profile, save_profile, UserProfile
        from metric_translator import translate_response, build_risk_summary
    except ImportError:
        interpret = None
        find_tools = None
        compose_stack = None
        compare_my_stack = None
        migration_plan = None
        load_profile = None
        save_profile = None
        UserProfile = None
        translate_response = lambda d: d
        build_risk_summary = lambda **kw: {}

# Optional deeper modules
whatif_simulate = None
vendor_deep_dive = None
compliance_posture = None
regulatory_map = None
token_cost = None
calculate_roi = None
economics_dashboard = None
check_budget = None
vendor_risk_dashboard = None
compute_risk_score = None

try:
    from .whatif import simulate as whatif_simulate
except Exception:
    pass
try:
    from .philosophy import vendor_deep_dive
except Exception:
    pass
try:
    from .compliance import compliance_posture, regulatory_map
except Exception:
    pass
try:
    from .ai_economics import (
        token_cost, calculate_roi, economics_dashboard, check_budget,
    )
except Exception:
    pass
try:
    from .vendor_risk import vendor_risk_dashboard, compute_risk_score
except Exception:
    pass
try:
    from .data import TOOLS
except Exception:
    TOOLS = []


# ╔════════════════════════════════════════════════════════════════════╗
# ║  REQUEST / RESPONSE MODELS (plain dicts — no Pydantic required)  ║
# ╚════════════════════════════════════════════════════════════════════╝

def _ok(data: dict) -> dict:
    """Wrap a result in the enterprise response envelope."""
    return translate_response(data)


def _err(msg: str, status: int = 400) -> dict:
    return {"error": msg, "status": status}


# ╔════════════════════════════════════════════════════════════════════╗
# ║  CORE FUNCTIONS (framework-agnostic)                             ║
# ║  These can be called directly or wired to FastAPI / Flask / etc. ║
# ╚════════════════════════════════════════════════════════════════════╝

def analyze(query: str, *, profile_id: str | None = None,
            stack_size: int = 3, filters: list | None = None) -> dict:
    """
    POST /api/v1/analyze

    The core product endpoint:
    "Tell me what AI stack I should use and why."

    Accepts a free-text description of needs and returns:
      - interpreted intent
      - recommended tool stack with fit scores
      - risk summary
      - cost estimate
      - integration notes
    """
    if not query or not query.strip():
        return _err("Query cannot be empty")

    intent = interpret(query)
    profile = load_profile(profile_id) if profile_id and load_profile else None

    # Get stack recommendation
    result = compose_stack(
        intent,
        profile=profile,
        stack_size=stack_size,
        categories_filter=filters,
    )

    explanation = result.get("explanation", {})
    stack_items = result.get("stack", [])
    alternatives = result.get("alternatives", [])

    # Build clean stack response
    recommended_stack = []
    for entry in stack_items:
        tool = entry["tool"]
        tool_expl = None
        for te in explanation.get("tool_explanations", []):
            if te.get("tool_name") == tool.name:
                tool_expl = te
                break

        recommended_stack.append({
            "name":         tool.name,
            "role":         entry["role"],
            "description":  tool.description,
            "fit_score":    tool_expl.get("fit_score") if tool_expl else None,
            "reasons":      (tool_expl.get("reasons", [])[:4] if tool_expl else []),
            "caveats":      (tool_expl.get("caveats", [])[:2] if tool_expl else []),
            "pricing":      getattr(tool, "pricing", None),
            "categories":   getattr(tool, "categories", None),
        })

    alternative_tools = [
        {"name": t.name, "description": t.description,
         "pricing": getattr(t, "pricing", None)}
        for t in alternatives[:5]
    ]

    return _ok({
        "intent":               intent,
        "recommended_stack":    recommended_stack,
        "alternatives":         alternative_tools,
        "narrative":            explanation.get("narrative"),
        "integration_notes":    explanation.get("integration_notes"),
        "total_monthly_cost":   explanation.get("total_monthly_cost"),
        "stack_fit_score":      explanation.get("stack_fit_score"),
    })


def optimize_stack(current_tools: list[str], *, goal: str = "",
                   profile_id: str | None = None) -> dict:
    """
    POST /api/v1/stack/optimize

    The #1 product wedge:
    "Upload your current stack → get optimized AI stack + risks"

    Returns current vs. optimized comparison with cost savings,
    risk reduction, and migration guidance.
    """
    if not current_tools:
        return _err("Provide at least one tool in current_tools")

    profile = load_profile(profile_id) if profile_id and load_profile else None

    comparison = compare_my_stack(
        current_tools=current_tools,
        goal=goal,
        profile=profile,
        profile_id=profile_id,
    )

    if "error" in comparison:
        return _err(comparison["error"])

    # Enrich with risk summary
    risk = build_risk_summary(
        lock_in=comparison.get("comparison", {}).get("risk_delta"),
    )

    return _ok({
        "current_stack":    comparison.get("current_stack"),
        "optimized_stack":  comparison.get("optimised_stack"),
        "savings":          comparison.get("savings"),
        "comparison":       comparison.get("comparison"),
        "risk_summary":     risk,
        "recommendation":   comparison.get("recommendation"),
    })


def compare(tool_a: str, tool_b: str, *,
            profile_id: str | None = None) -> dict:
    """
    POST /api/v1/compare

    Side-by-side comparison of two tools.
    """
    if not tool_a or not tool_b:
        return _err("Both tool_a and tool_b are required")

    from .stack import compare_tools
    profile = load_profile(profile_id) if profile_id and load_profile else None
    result = compare_tools(tool_a, tool_b, profile)
    return _ok(result)


def migrate(from_tool: str, to_tool: str | None = None, *,
            desired_outcome: str | None = None,
            profile_id: str | None = None) -> dict:
    """
    POST /api/v1/migrate

    Step-by-step migration plan between tools.
    Includes risk assessment, timeline, and bridging tools.
    """
    if not from_tool:
        return _err("from_tool is required")

    profile = load_profile(profile_id) if profile_id and load_profile else None
    result = migration_plan(
        from_tool=from_tool,
        to_tool=to_tool,
        desired_outcome=desired_outcome,
        profile=profile,
        profile_id=profile_id,
    )

    if "error" in result:
        return _err(result["error"])

    # Enrich with risk summary
    risk = build_risk_summary(
        migration_complexity=result.get("migration_complexity"),
    )
    result["risk_summary"] = risk

    return _ok(result)


def vendor_report(tool_name: str) -> dict:
    """
    GET /api/v1/vendor/{tool_name}

    Extended vendor risk report: risk score, compliance gaps,
    lock-in probability, data handling practices.
    """
    if not tool_name:
        return _err("tool_name is required")

    result: Dict[str, Any] = {"tool": tool_name}

    # Try deep-dive vendor report
    if vendor_deep_dive:
        tool = None
        for t in TOOLS:
            if t.name.lower() == tool_name.lower():
                tool = t
                break
        if tool:
            result["deep_dive"] = vendor_deep_dive(tool)

    # Try risk dashboard for this vendor
    if vendor_risk_dashboard:
        dashboard = vendor_risk_dashboard()
        for v in dashboard.get("vendors", []):
            if v.get("tool_name", "").lower() == tool_name.lower():
                result["risk_profile"] = v
                break

    if len(result) == 1:
        return _err(f"Vendor '{tool_name}' not found")

    return _ok(result)


def whatif(query: str, changes: dict, *,
           profile_id: str | None = None, top_n: int = 5) -> dict:
    """
    POST /api/v1/whatif

    Simulate profile/constraint changes and see how
    recommendations shift.
    """
    if not whatif_simulate:
        return _err("What-if simulation not available", 501)

    result = whatif_simulate(
        query=query,
        changes=changes,
        profile_id=profile_id,
        top_n=top_n,
    )
    return _ok(result)


def compliance_report() -> dict:
    """
    GET /api/v1/compliance

    Full regulatory compliance snapshot:
    EU AI Act, HIPAA, GDPR coverage + audit integrity.
    """
    if compliance_posture:
        return _ok(compliance_posture())

    if regulatory_map:
        return _ok({"regulatory_compliance": regulatory_map()})

    return _err("Compliance module not available", 501)


def cost_analysis(input_tokens: int = 0, output_tokens: int = 0,
                  model: str = "default") -> dict:
    """
    POST /api/v1/cost

    Estimate cost for a given model usage pattern.
    """
    if not token_cost:
        return _err("Economics module not available", 501)

    result = token_cost(input_tokens, output_tokens, model)
    return _ok(result)


def economics() -> dict:
    """
    GET /api/v1/economics

    Full AI economics dashboard:
    usage, ROI, budget, waste detection, attribution.
    """
    if economics_dashboard:
        return _ok(economics_dashboard())
    return _err("Economics module not available", 501)


def health() -> dict:
    """
    GET /api/v1/health

    Lightweight system health check.
    """
    modules = {
        "interpreter":  interpret is not None,
        "engine":       find_tools is not None,
        "stack":        compose_stack is not None,
        "compare":      compare_my_stack is not None,
        "migration":    migration_plan is not None,
        "whatif":        whatif_simulate is not None,
        "compliance":    compliance_posture is not None,
        "economics":     economics_dashboard is not None,
        "vendor_risk":   vendor_risk_dashboard is not None,
    }
    active = sum(1 for v in modules.values() if v)
    return {
        "status":           "healthy" if active >= 5 else "degraded",
        "api_version":      "public-v1",
        "modules_active":   active,
        "modules_total":    len(modules),
        "modules":          modules,
        "endpoints":        12,
    }


def submit_feedback(tool_name: str, rating: int,
                    comment: str = "", profile_id: str | None = None) -> dict:
    """
    POST /api/v1/feedback

    Submit user feedback on a tool recommendation.
    """
    try:
        from .feedback import record_feedback
    except ImportError:
        try:
            from feedback import record_feedback
        except ImportError:
            return _err("Feedback module not available", 501)

    record_feedback(tool_name, rating, comment, profile_id)
    return {"status": "recorded", "tool": tool_name, "rating": rating}


def api_docs() -> dict:
    """
    GET /api/v1/docs

    Self-describing API documentation.
    """
    return {
        "api":      "Praxis AI Decision Engine",
        "version":  "public-v1",
        "description": (
            "Enterprise AI stack advisor. Analyze needs, optimize stacks, "
            "assess vendor risk, plan migrations, and track compliance."
        ),
        "endpoints": [
            {
                "method": "POST", "path": "/api/v1/analyze",
                "description": "Describe your needs → get recommended AI stack",
                "body": {"query": "str (required)", "profile_id": "str?",
                         "stack_size": "int (default 3)", "filters": "list?"},
            },
            {
                "method": "POST", "path": "/api/v1/stack/optimize",
                "description": "Upload current stack → get optimized stack + risks + savings",
                "body": {"current_tools": "list[str] (required)",
                         "goal": "str?", "profile_id": "str?"},
            },
            {
                "method": "POST", "path": "/api/v1/compare",
                "description": "Side-by-side tool comparison",
                "body": {"tool_a": "str", "tool_b": "str", "profile_id": "str?"},
            },
            {
                "method": "POST", "path": "/api/v1/migrate",
                "description": "Migration plan between tools with risk assessment",
                "body": {"from_tool": "str", "to_tool": "str?",
                         "desired_outcome": "str?", "profile_id": "str?"},
            },
            {
                "method": "GET", "path": "/api/v1/vendor/{tool_name}",
                "description": "Vendor risk report: risk score, compliance, lock-in",
            },
            {
                "method": "POST", "path": "/api/v1/whatif",
                "description": "Simulate constraint changes and preview recommendation shifts",
                "body": {"query": "str", "changes": "dict", "profile_id": "str?"},
            },
            {
                "method": "GET", "path": "/api/v1/compliance",
                "description": "Regulatory compliance snapshot (EU AI Act, HIPAA, GDPR)",
            },
            {
                "method": "POST", "path": "/api/v1/cost",
                "description": "Estimate inference cost for a model/usage pattern",
                "body": {"input_tokens": "int", "output_tokens": "int", "model": "str?"},
            },
            {
                "method": "GET", "path": "/api/v1/economics",
                "description": "Full AI economics dashboard: ROI, budget, waste",
            },
            {
                "method": "GET", "path": "/api/v1/health",
                "description": "System health check",
            },
            {
                "method": "GET", "path": "/api/v1/docs",
                "description": "This endpoint — API documentation",
            },
            {
                "method": "POST", "path": "/api/v1/feedback",
                "description": "Submit feedback on a tool recommendation",
                "body": {"tool_name": "str", "rating": "int (1-5)", "comment": "str?"},
            },
        ],
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  FASTAPI WIRING                                                  ║
# ╚════════════════════════════════════════════════════════════════════╝

def mount_public_api(app) -> None:
    """
    Mount the 12 public endpoints onto a FastAPI app instance.
    Called from api.py's create_app().
    """
    from pydantic import BaseModel, Field

    # ── Request models ───────────────────────────────────────────
    class AnalyzeRequest(BaseModel):
        query: str
        profile_id: Optional[str] = None
        stack_size: int = Field(default=3, ge=1, le=10)
        filters: Optional[List[str]] = None

    class OptimizeRequest(BaseModel):
        current_tools: List[str]
        goal: str = ""
        profile_id: Optional[str] = None

    class CompareRequest(BaseModel):
        tool_a: str
        tool_b: str
        profile_id: Optional[str] = None

    class MigrateRequest(BaseModel):
        from_tool: str
        to_tool: Optional[str] = None
        desired_outcome: Optional[str] = None
        profile_id: Optional[str] = None

    class WhatIfRequest(BaseModel):
        query: str
        changes: Dict[str, str] = Field(default_factory=dict)
        profile_id: Optional[str] = None
        top_n: int = 5

    class CostRequest(BaseModel):
        input_tokens: int = 0
        output_tokens: int = 0
        model: str = "default"

    class FeedbackRequest(BaseModel):
        tool_name: str
        rating: int = Field(ge=1, le=5)
        comment: str = ""
        profile_id: Optional[str] = None

    # ── Routes ───────────────────────────────────────────────────

    @app.post("/api/v1/analyze", tags=["Public API"])
    def v1_analyze(req: AnalyzeRequest):
        """Describe your needs → get recommended AI stack with reasoning."""
        return analyze(req.query, profile_id=req.profile_id,
                       stack_size=req.stack_size, filters=req.filters)

    @app.post("/api/v1/stack/optimize", tags=["Public API"])
    def v1_optimize(req: OptimizeRequest):
        """Upload current stack → get optimized stack + risks + savings."""
        return optimize_stack(req.current_tools, goal=req.goal,
                              profile_id=req.profile_id)

    @app.post("/api/v1/compare", tags=["Public API"])
    def v1_compare(req: CompareRequest):
        """Side-by-side tool comparison with fit scoring."""
        return compare(req.tool_a, req.tool_b, profile_id=req.profile_id)

    @app.post("/api/v1/migrate", tags=["Public API"])
    def v1_migrate(req: MigrateRequest):
        """Migration plan with risks, timeline, and bridging tools."""
        return migrate(req.from_tool, req.to_tool,
                       desired_outcome=req.desired_outcome,
                       profile_id=req.profile_id)

    @app.get("/api/v1/vendor/{tool_name}", tags=["Public API"])
    def v1_vendor(tool_name: str):
        """Vendor risk report: score, compliance gaps, lock-in probability."""
        return vendor_report(tool_name)

    @app.post("/api/v1/whatif", tags=["Public API"])
    def v1_whatif(req: WhatIfRequest):
        """Simulate constraint changes → preview recommendation shifts."""
        return whatif(req.query, req.changes,
                      profile_id=req.profile_id, top_n=req.top_n)

    @app.get("/api/v1/compliance", tags=["Public API"])
    def v1_compliance():
        """EU AI Act, HIPAA, GDPR compliance snapshot + audit integrity."""
        return compliance_report()

    @app.post("/api/v1/cost", tags=["Public API"])
    def v1_cost(req: CostRequest):
        """Estimate inference cost for a model/usage pattern."""
        return cost_analysis(req.input_tokens, req.output_tokens, req.model)

    @app.get("/api/v1/economics", tags=["Public API"])
    def v1_economics():
        """AI economics dashboard: ROI, budget, waste detection."""
        return economics()

    @app.get("/api/v1/health", tags=["Public API"])
    def v1_health():
        """System health check — module status and endpoint count."""
        return health()

    @app.get("/api/v1/docs", tags=["Public API"])
    def v1_docs():
        """Self-describing API documentation."""
        return api_docs()

    @app.post("/api/v1/feedback", tags=["Public API"])
    def v1_feedback(req: FeedbackRequest):
        """Submit feedback on a tool recommendation."""
        return submit_feedback(req.tool_name, req.rating,
                               req.comment, req.profile_id)
