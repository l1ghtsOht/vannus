"""Feature/operations API route registration extracted from api.create_app()."""
# pyright: reportInvalidTypeForm=false
from typing import Optional


def register_feature_routes(app, deps):
    TOOLS = deps["TOOLS"]
    get_all_categories = deps["get_all_categories"]
    init_intelligence = deps["init_intelligence"]
    generate_seeing = deps["generate_seeing"]
    suggest_workflow = deps["suggest_workflow"]
    tool_health = deps["tool_health"]
    stack_health = deps["stack_health"]
    score_readiness = deps["score_readiness"]
    compare_my_stack = deps["compare_my_stack"]
    get_badges = deps["get_badges"]
    compute_all_badges = deps["compute_all_badges"]
    migration_plan = deps["migration_plan"]
    whatif_simulate = deps["whatif_simulate"]
    vendor_deep_dive = deps["vendor_deep_dive"]
    test_integration = deps["test_integration"]
    stack_integration_map = deps["stack_integration_map"]
    get_affiliate_info = deps["get_affiliate_info"]
    submit_benchmark = deps["submit_benchmark"]
    get_benchmarks = deps["get_benchmarks"]
    subscribe_digest = deps["subscribe_digest"]
    unsubscribe_digest = deps["unsubscribe_digest"]
    generate_digest = deps["generate_digest"]
    subscriber_count = deps["subscriber_count"]
    _deep_reason = deps["_deep_reason"]
    load_profile = deps["load_profile"]
    _cfg = deps["_cfg"]

    WorkflowRequest = deps["WorkflowRequest"]
    CompareStackRequest = deps["CompareStackRequest"]
    MigrationRequest = deps["MigrationRequest"]
    WhatIfRequest = deps["WhatIfRequest"]
    IntegrationTestRequest = deps["IntegrationTestRequest"]
    IntegrationMapRequest = deps["IntegrationMapRequest"]
    BenchmarkRequest = deps["BenchmarkRequest"]
    DigestSubscribeRequest = deps["DigestSubscribeRequest"]
    BaseModel = deps["BaseModel"]

    @app.get("/health")
    def health():
        """Health check with diagnostics."""
        return {
            "status": "ok",
            "tools_loaded": len(TOOLS),
            "categories": len(get_all_categories()),
            "intelligence": init_intelligence is not None,
            "philosophy": generate_seeing is not None,
            "modules": {
                "workflow": suggest_workflow is not None,
                "healthcheck": tool_health is not None,
                "readiness": score_readiness is not None,
                "compare_stack": compare_my_stack is not None,
                "badges": get_badges is not None,
                "migration": migration_plan is not None,
                "whatif": whatif_simulate is not None,
                "vendor_deep_dive": vendor_deep_dive is not None,
                "playground": test_integration is not None,
                "affiliates": get_affiliate_info is not None,
                "benchmarks": submit_benchmark is not None,
                "digest": subscribe_digest is not None,
            },
        }

    @app.get("/tools/stale")
    def stale_tools():
        """List tools whose metadata hasn't been updated within the freshness window."""
        max_days = int(_cfg.get("tool_freshness_days", 90) if _cfg else 90)
        stale = [
            {
                "name": t.name,
                "last_updated": getattr(t, "last_updated", None),
                "categories": t.categories,
            }
            for t in TOOLS
            if getattr(t, "is_stale", lambda d: True)(max_days)
        ]
        return {
            "freshness_window_days": max_days,
            "stale_count": len(stale),
            "total_tools": len(TOOLS),
            "stale_tools": stale,
        }

    try:
        from .diagnostics import get_failures, get_failure_summary
        _diag_available = True
    except Exception:
        try:
            from diagnostics import get_failures, get_failure_summary
            _diag_available = True
        except Exception:
            _diag_available = False

    if _diag_available:
        @app.get("/diagnostics/failures")
        def diagnostics_failures(limit: int = 50):
            """Return the most recent query failures."""
            return {"failures": get_failures(limit=limit)}

        @app.get("/diagnostics/summary")
        def diagnostics_summary():
            """Aggregate failure stats for gap analysis."""
            return get_failure_summary()

    if suggest_workflow:
        @app.post("/workflow-suggest")
        def workflow_suggest(req: WorkflowRequest):
            """Return a sequenced multi-step workflow recommendation."""
            profile = load_profile(req.profile_id) if req.profile_id else None
            return suggest_workflow(
                query=req.query,
                profile=profile,
                profile_id=req.profile_id,
                existing_tools=req.existing_tools,
                max_steps=req.max_steps,
            )

    if tool_health:
        @app.get("/tool-health/{tool_name}")
        def tool_health_ep(tool_name: str):
            """Early-warning health report for a single tool."""
            return tool_health(tool_name)

    if stack_health:
        @app.post("/stack-health")
        def stack_health_ep(payload: dict):
            """Aggregate health for a list of tools. Body: {"tools": [...]}"""
            tools = payload.get("tools", [])
            if not tools:
                return {"error": "Provide a 'tools' list."}
            return stack_health(tools)

    if score_readiness:
        @app.get("/profile-readiness/{profile_id}")
        def profile_readiness(profile_id: str):
            """AI readiness score 0-100 for a saved profile."""
            profile = load_profile(profile_id)
            if not profile:
                return {"error": f"Profile '{profile_id}' not found"}
            return score_readiness(profile, profile_id)

    if compare_my_stack:
        @app.post("/compare-stack")
        def compare_stack_ep(req: CompareStackRequest):
            """Current stack vs optimised alternative analysis."""
            profile = load_profile(req.profile_id) if req.profile_id else None
            return compare_my_stack(
                current_tools=req.current_tools,
                goal=req.goal,
                profile=profile,
                profile_id=req.profile_id,
            )

    if get_badges:
        @app.get("/badges/{tool_name}")
        def badges_for_tool(tool_name: str):
            """Return earned community badges for a single tool."""
            return {"tool": tool_name, "badges": get_badges(tool_name)}

    if compute_all_badges:
        @app.get("/badges")
        def badges_all():
            """Return badges for every tool in the database."""
            return compute_all_badges()

    if migration_plan:
        @app.post("/migration-plan")
        def migration_plan_ep(req: MigrationRequest):
            """Step-by-step migration plan between two tools."""
            profile = load_profile(req.profile_id) if req.profile_id else None
            return migration_plan(
                from_tool=req.from_tool,
                to_tool=req.to_tool,
                desired_outcome=req.desired_outcome,
                profile=profile,
                profile_id=req.profile_id,
            )

    if whatif_simulate:
        @app.post("/whatif")
        def whatif_ep(req: WhatIfRequest):
            """Simulate profile changes and compare baseline vs hypothetical."""
            return whatif_simulate(
                query=req.query,
                changes=req.changes,
                profile_id=req.profile_id,
                top_n=req.top_n,
            )

    if vendor_deep_dive:
        @app.get("/vendor-report/{tool_name}")
        def vendor_report(tool_name: str):
            """Extended vendor risk report with news, exit cost, strategy."""
            tool = None
            for t in TOOLS:
                if t.name.lower() == tool_name.lower():
                    tool = t
                    break
            if not tool:
                return {"error": f"Tool '{tool_name}' not found"}
            return vendor_deep_dive(tool)

    if test_integration:
        @app.post("/integration-test")
        def integration_test_ep(req: IntegrationTestRequest):
            """Test whether tool_a integrates with tool_b."""
            return test_integration(req.tool_a, req.tool_b)

    if stack_integration_map:
        @app.post("/integration-map")
        def integration_map_ep(req: IntegrationMapRequest):
            """Full integration matrix for a list of tools."""
            return stack_integration_map(req.tools)

    if get_affiliate_info:
        @app.get("/affiliate/{tool_name}")
        def affiliate_ep(tool_name: str):
            """Return affiliate/promo info for a tool."""
            return get_affiliate_info(tool_name)

    if submit_benchmark:
        @app.post("/benchmark")
        def benchmark_submit(req: BenchmarkRequest):
            """Submit a user-generated benchmark for a tool."""
            return submit_benchmark(
                tool_name=req.tool_name,
                user_id=req.user_id,
                task=req.task,
                metrics=req.metrics,
                notes=req.notes,
            )

    if get_benchmarks:
        @app.get("/benchmark/{tool_name}")
        def benchmark_get(tool_name: str):
            """Retrieve aggregated benchmarks for a tool."""
            return get_benchmarks(tool_name)

    if subscribe_digest:
        @app.post("/digest/subscribe")
        def digest_subscribe_ep(req: DigestSubscribeRequest):
            """Subscribe an email to the weekly AI digest."""
            return subscribe_digest(req.email, req.profile_id)

    if unsubscribe_digest:
        @app.post("/digest/unsubscribe")
        def digest_unsubscribe_ep(payload: dict):
            """Unsubscribe from the weekly digest. Body: {"email": "..."}"""
            email = payload.get("email", "")
            if not email:
                return {"error": "Provide an 'email' field."}
            return unsubscribe_digest(email)

    if generate_digest:
        @app.get("/digest/preview/{profile_id}")
        def digest_preview(profile_id: str = "default"):
            """Preview the weekly digest for a profile."""
            return generate_digest(profile_id)

    if subscriber_count:
        @app.get("/digest/stats")
        def digest_stats():
            """Return digest subscriber count."""
            return {"subscribers": subscriber_count()}

    class ReasonRequest(BaseModel):
        query: str
        profile_id: Optional[str] = None
        max_steps: Optional[int] = 5
        budget_ms: Optional[int] = 15000
        include_trace: Optional[bool] = False

    if _deep_reason:
        @app.post("/reason")
        def reason_ep(req: ReasonRequest):
            """Agentic deep-reasoning search.  Decomposes the query,
            runs iterative sub-searches, applies constraints & vendor
            intelligence, self-critiques, and synthesises a narrative."""
            result = _deep_reason(
                req.query,
                profile_id=req.profile_id,
                max_steps=min(req.max_steps or 5, 10),
                budget_ms=min(req.budget_ms or 15000, 60000),
            )
            payload = {
                "query": result.query,
                "mode": result.mode,
                "plan": result.plan,
                "tools_considered": result.tools_considered,
                "tools_recommended": result.tools_recommended,
                "narrative": result.narrative,
                "confidence": result.confidence,
                "caveats": result.caveats,
                "follow_up_questions": result.follow_up_questions,
                "reasoning_depth": result.reasoning_depth,
                "total_elapsed_ms": result.total_elapsed_ms,
            }
            if req.include_trace:
                payload["trace"] = [
                    {"phase": s.phase, "action": s.action,
                     "detail": s.detail, "elapsed_ms": s.elapsed_ms}
                    for s in result.steps
                ]
            return payload

    # ── v20 Multi-Model Ecosystem Routes ─────────────────────────
    try:
        from .ecosystem import (
            run_collaboration, create_session as eco_create_session,
            get_session as eco_get_session, end_session as eco_end_session,
            list_sessions as eco_list_sessions,
        )
        from .model_registry import get_registry
        from .model_router import route_query
        from .model_trust_decay import get_trust_monitor
        from .shared_state import get_shared_state_manager
        from .ai_economics import get_model_budget_manager
        _ecosystem_available = True
    except ImportError:
        try:
            from ecosystem import (
                run_collaboration, create_session as eco_create_session,
                get_session as eco_get_session, end_session as eco_end_session,
                list_sessions as eco_list_sessions,
            )
            from model_registry import get_registry
            from model_router import route_query
            from model_trust_decay import get_trust_monitor
            from shared_state import get_shared_state_manager
            from ai_economics import get_model_budget_manager
            _ecosystem_available = True
        except ImportError:
            _ecosystem_available = False

    if _ecosystem_available:
        class EcosystemRequest(BaseModel):
            task: str
            session_id: Optional[str] = None
            strategy: Optional[str] = None
            budget_usd: Optional[float] = 5.0
            system_prompt: Optional[str] = None
            privacy_required: Optional[bool] = False
            user_id: Optional[str] = "api"

        @app.post("/ecosystem/collaborate")
        def ecosystem_collaborate(req: EcosystemRequest):
            """Run a multi-model collaboration task."""
            result = run_collaboration(
                task=req.task,
                session_id=req.session_id,
                strategy=req.strategy,
                budget_usd=req.budget_usd,
                system_prompt=req.system_prompt,
                privacy_required=req.privacy_required,
                user_id=req.user_id,
            )
            return result.to_dict()

        @app.post("/ecosystem/route")
        def ecosystem_route(payload: dict):
            """Route a query to the best model(s) without execution."""
            query = payload.get("query", "")
            if not query:
                return {"error": "Provide a 'query' field."}
            decision = route_query(query)
            return decision.to_dict()

        @app.post("/ecosystem/session")
        def ecosystem_session_create(payload: dict):
            """Create a new ecosystem collaboration session."""
            return eco_create_session(
                user_id=payload.get("user_id", "api"),
                system_prompt=payload.get("system_prompt"),
            )

        @app.get("/ecosystem/session/{session_id}")
        def ecosystem_session_get(session_id: str):
            """Get ecosystem session details."""
            session = eco_get_session(session_id)
            if session is None:
                return {"error": f"Session '{session_id}' not found"}
            return session.to_dict()

        @app.delete("/ecosystem/session/{session_id}")
        def ecosystem_session_end(session_id: str):
            """End an ecosystem session."""
            return {"ended": eco_end_session(session_id)}

        @app.get("/ecosystem/sessions")
        def ecosystem_sessions():
            """List active ecosystem sessions."""
            return {"sessions": eco_list_sessions()}

        @app.get("/ecosystem/models")
        def ecosystem_models():
            """List all registered models and their status."""
            registry = get_registry()
            return {"models": [m.to_dict() for m in registry.list_all()]}

        @app.get("/ecosystem/trust")
        def ecosystem_trust():
            """Trust status for all models."""
            monitor = get_trust_monitor()
            return monitor.get_model_trust_status()

        @app.get("/ecosystem/budget")
        def ecosystem_budget():
            """Per-model budget status."""
            mgr = get_model_budget_manager()
            return mgr.to_dict()

        # ── Context-Aware Intent Transfer endpoints ──────────────

        @app.post("/context/extract")
        def context_extract(body: dict):
            """Extract context from a free-form query.

            Body: {"query": str, "profile_id": str (optional)}
            Returns: ContextVector + GapAnalysis
            """
            from .context_engine import extract_context, enrich_via_graph
            from .residual_gap import compute_gap

            query = body.get("query", "").strip()
            if not query:
                return {"error": "query is required"}, 400

            profile_id = body.get("profile_id")
            cv = extract_context(query, profile_id=profile_id)

            # Optional graph enrichment
            try:
                from .graph import get_graph
                tg = get_graph()
                cv = enrich_via_graph(cv, tg)
            except Exception:
                pass  # graph not built yet — proceed without

            gap = compute_gap(cv)
            return {
                "context": cv.to_dict(),
                "gap": gap.to_dict(),
            }

        @app.post("/context/resolve")
        def context_resolve(body: dict):
            """Resolve gap questions with user answers.

            Body: {"query": str, "answers": {"field": "value", ...}, "profile_id": str (optional)}
            Returns: Updated ContextVector
            """
            from .context_engine import extract_context, enrich_via_graph
            from .residual_gap import compute_gap, resolve_gap

            query = body.get("query", "").strip()
            answers = body.get("answers", {})
            if not query:
                return {"error": "query is required"}, 400
            if not answers:
                return {"error": "answers dict is required"}, 400

            profile_id = body.get("profile_id")
            cv = extract_context(query, profile_id=profile_id)

            try:
                from .graph import get_graph
                tg = get_graph()
                cv = enrich_via_graph(cv, tg)
            except Exception:
                pass

            gap = compute_gap(cv)
            updated_cv = resolve_gap(gap, answers)

            # Auto-hydrate profile if configured
            if profile_id and _cfg and _cfg.get("context_auto_persist", True):
                try:
                    from .profile import load_profile as _lp, save_profile
                    from .context_engine import TIER_1
                    profile = _lp(profile_id)
                    if profile and updated_cv:
                        from .profile import hydrate_profile
                        hydrate_profile(profile, updated_cv, user_confirmed=True)
                except Exception:
                    pass

            return {
                "context": updated_cv.to_dict() if updated_cv else {},
                "resolved": True,
            }

        @app.post("/context/analyse")
        def context_analyse(body: dict):
            """One-call convenience: extract + gap analysis in one step.

            Body: {"query": str, "profile_id": str (optional)}
            Returns: Full GapAnalysis with questions
            """
            from .residual_gap import analyse_query

            query = body.get("query", "").strip()
            if not query:
                return {"error": "query is required"}, 400

            profile_id = body.get("profile_id")
            result = analyse_query(query, profile_id=profile_id)
            return result.to_dict()
