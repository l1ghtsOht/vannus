"""Core API route registration extracted from api.create_app()."""
# pyright: reportInvalidTypeForm=false


def register_core_routes(app, deps):
    get_all_categories = deps["get_all_categories"]
    TOOLS = deps["TOOLS"]
    ToolDetail = deps["ToolDetail"]
    SearchRequest = deps["SearchRequest"]
    _deep_reason = deps["_deep_reason"]
    _deep_reason_v2 = deps["_deep_reason_v2"]
    interpret = deps["interpret"]
    load_profile = deps["load_profile"]
    find_tools = deps["find_tools"]
    explain_tool = deps["explain_tool"]
    get_suggestions = deps["get_suggestions"]
    generate_seeing = deps["generate_seeing"]
    StackResponse = deps["StackResponse"]
    StackRequest = deps["StackRequest"]
    compose_stack = deps["compose_stack"]
    StackToolEntry = deps["StackToolEntry"]
    CompareRequest = deps["CompareRequest"]
    compare_tools = deps["compare_tools"]
    ProfileRequest = deps["ProfileRequest"]
    UserProfile = deps["UserProfile"]
    save_profile = deps["save_profile"]
    list_profiles = deps["list_profiles"]
    FeedbackRequest = deps["FeedbackRequest"]
    run_learning_cycle = deps["run_learning_cycle"]
    compute_tool_quality = deps["compute_tool_quality"]
    export_tools_json = deps["export_tools_json"]
    import_tools_json = deps["import_tools_json"]
    import_tools_csv = deps["import_tools_csv"]
    generate_csv_template = deps["generate_csv_template"]
    _cfg = deps["_cfg"]
    _get_current_user = deps.get("get_current_user")

    # Build a Depends-based admin guard if FastAPI auth is available.
    # Routes decorated with admin_required will return 401/403 when
    # PRAXIS_AUTH_MODE is not "none" and credentials are absent/invalid.
    _admin_guard = None
    if _get_current_user:
        try:
            from fastapi import Depends, HTTPException

            async def _require_admin(user=Depends(_get_current_user)):
                if not user.has_role("admin"):
                    raise HTTPException(status_code=403, detail="Admin role required")
                return user

            _admin_guard = [Depends(_require_admin)]
        except Exception:
            pass

    @app.get("/categories")
    def categories():
        return get_all_categories()

    @app.get("/tools")
    def list_tools(skip: int = 0, limit: int = 50):
        """Return paginated tool list.  Use ``?skip=0&limit=50`` to page."""
        page = TOOLS[skip : skip + limit]
        out = []
        for t in page:
            out.append(ToolDetail(
                name=t.name,
                description=t.description,
                url=getattr(t, "url", None),
                categories=getattr(t, "categories", None),
                tags=getattr(t, "tags", None),
                keywords=getattr(t, "keywords", None),
                popularity=getattr(t, "popularity", 0),
                pricing=getattr(t, "pricing", None),
                integrations=getattr(t, "integrations", None),
                compliance=getattr(t, "compliance", None),
                skill_level=getattr(t, "skill_level", None),
                use_cases=getattr(t, "use_cases", None),
                stack_roles=getattr(t, "stack_roles", None),
            ))
        return {"total": len(TOOLS), "skip": skip, "limit": limit, "items": out}

    @app.post("/search")
    def search(req: SearchRequest):
        if req.mode == "deep" and _deep_reason:
            result = _deep_reason(
                req.query,
                profile_id=req.profile_id,
                max_steps=min(req.top_n or 5, 8),
            )
            return {
                "results": result.tools_recommended,
                "meta": {
                    "mode": "deep",
                    "reasoning_depth": result.reasoning_depth,
                    "confidence": result.confidence,
                    "plan": result.plan,
                    "narrative": result.narrative,
                    "follow_up_questions": result.follow_up_questions,
                    "tools_considered": result.tools_considered,
                    "total_elapsed_ms": result.total_elapsed_ms,
                },
            }

        if req.mode == "cognitive" and _deep_reason_v2:
            result = _deep_reason_v2(
                req.query,
                profile_id=req.profile_id,
                max_steps=min(req.top_n or 5, 8),
            )
            return {
                "results": result.tools_recommended,
                "meta": {
                    "mode": "cognitive",
                    "reasoning_depth": result.reasoning_depth,
                    "confidence": result.confidence,
                    "plan": result.plan,
                    "narrative": result.narrative,
                    "follow_up_questions": result.follow_up_questions,
                    "tools_considered": result.tools_considered,
                    "total_elapsed_ms": result.total_elapsed_ms,
                    "caveats": result.caveats,
                    "steps": len(result.steps),
                },
            }

        struct = interpret(req.query)

        profile = None
        if req.profile_id:
            profile = load_profile(req.profile_id)

        results = find_tools(struct, top_n=req.top_n, categories_filter=req.filters, profile=profile)

        out = []
        for idx, t in enumerate(results):
            expl = explain_tool(t, struct, profile)
            confidence = expl.get("fit_score", max(0, 100 - idx * 15))
            out.append(ToolDetail(
                name=t.name,
                description=t.description,
                url=getattr(t, "url", None),
                categories=getattr(t, "categories", None),
                tags=getattr(t, "tags", None),
                keywords=getattr(t, "keywords", None),
                popularity=getattr(t, "popularity", 0),
                confidence=confidence,
                match_reasons=expl.get("reasons", [])[:3],
                fit_score=expl.get("fit_score"),
                caveats=expl.get("caveats", [])[:3],
                pricing=getattr(t, "pricing", None),
                integrations=getattr(t, "integrations", None),
                compliance=getattr(t, "compliance", None),
                skill_level=getattr(t, "skill_level", None),
                use_cases=getattr(t, "use_cases", None),
                stack_roles=getattr(t, "stack_roles", None),
                transparency_score=expl.get("transparency_score"),
                transparency_grade=expl.get("transparency_grade"),
                flexibility_score=expl.get("freedom_score"),
                flexibility_grade=expl.get("freedom_grade"),
            ))

        meta = {
            "intent": struct.get("intent"),
            "industry": struct.get("industry"),
            "goal": struct.get("goal"),
            "corrections": struct.get("corrections", {}),
            "negatives": struct.get("negatives", []),
            "multi_intents": struct.get("multi_intents", []),
            "expanded_keywords": struct.get("keywords", []),
            "suggested_questions": struct.get("suggested_questions", []),
        }

        return {"results": out, "meta": meta}

    @app.get("/suggest")
    def suggest(q: str = ""):
        """Smart autocomplete — returns a Bento Grid payload with
        intent detection, semantic completions, and tool matches."""
        try:
            from .smart_suggest import smart_suggest
        except ImportError:
            from smart_suggest import smart_suggest
        if q and len(q.strip()) >= 2:
            return smart_suggest(q, TOOLS, limit=8)
        # Show-on-focus: return pre-populated suggestions for empty query
        try:
            from .smart_suggest import focus_suggestions
        except ImportError:
            from smart_suggest import focus_suggestions
        return focus_suggestions(TOOLS)

    @app.post("/suggest/click")
    def suggest_click(body: dict):
        """Record a click on an autocomplete suggestion for popularity tracking."""
        text = body.get("text", "").strip()
        if not text:
            return {"status": "ignored"}
        try:
            from .smart_suggest import record_suggestion_click
        except ImportError:
            from smart_suggest import record_suggestion_click
        record_suggestion_click(text)
        return {"status": "recorded", "text": text}

    @app.get("/intelligence/{tool_name}")
    def intelligence(tool_name: str):
        if not generate_seeing:
            return {"error": "Vendor intelligence module not available"}
        tool = None
        for t in TOOLS:
            if t.name.lower() == tool_name.lower():
                tool = t
                break
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return generate_seeing(tool)

    @app.get("/seeing/{tool_name}")
    def seeing(tool_name: str):
        return intelligence(tool_name)

    @app.post("/stack", response_model=StackResponse)
    def stack(req: StackRequest):
        struct = interpret(req.query)
        profile = load_profile(req.profile_id) if req.profile_id else None

        result = compose_stack(
            struct,
            profile=profile,
            stack_size=req.stack_size,
            categories_filter=req.filters,
        )

        explanation = result.get("explanation", {})

        stack_entries = []
        for entry in result.get("stack", []):
            tool = entry["tool"]
            tool_expl = None
            for te in explanation.get("tool_explanations", []):
                if te.get("tool_name") == tool.name:
                    tool_expl = te
                    break

            stack_entries.append(StackToolEntry(
                name=tool.name,
                role=entry["role"],
                description=tool.description,
                url=getattr(tool, "url", None),
                fit_score=tool_expl.get("fit_score") if tool_expl else None,
                reasons=tool_expl.get("reasons", [])[:4] if tool_expl else None,
                caveats=tool_expl.get("caveats", [])[:2] if tool_expl else None,
                pricing=getattr(tool, "pricing", None),
                categories=getattr(tool, "categories", None),
                integrations=getattr(tool, "integrations", None),
                skill_level=getattr(tool, "skill_level", None),
            ))

        alts = []
        for t in result.get("alternatives", [])[:5]:
            alts.append(ToolDetail(
                name=t.name,
                description=t.description,
                url=getattr(t, "url", None),
                categories=getattr(t, "categories", None),
                pricing=getattr(t, "pricing", None),
            ))

        return StackResponse(
            narrative=explanation.get("narrative"),
            stack=stack_entries,
            integration_notes=explanation.get("integration_notes"),
            total_monthly_cost=explanation.get("total_monthly_cost"),
            stack_fit_score=explanation.get("stack_fit_score"),
            alternatives=alts,
        )

    @app.post("/compare")
    def compare(req: CompareRequest):
        profile = load_profile(req.profile_id) if req.profile_id else None
        return compare_tools(req.tool_a, req.tool_b, profile)

    @app.post("/profile")
    def upsert_profile(req: ProfileRequest):
        p = UserProfile(
            profile_id=req.profile_id,
            industry=req.industry,
            budget=req.budget,
            team_size=req.team_size,
            skill_level=req.skill_level,
            existing_tools=req.existing_tools or [],
            goals=req.goals or [],
            constraints=req.constraints or [],
        )
        save_profile(p)
        return {"ok": True, "profile": p.to_dict()}

    @app.get("/profile/{profile_id}")
    def get_profile(profile_id: str):
        p = load_profile(profile_id)
        if not p:
            return {"error": "Profile not found"}
        return p.to_dict()

    @app.get("/profiles")
    def get_profiles():
        return list_profiles()

    @app.post("/feedback")
    def feedback(entry: FeedbackRequest):
        try:
            from .feedback import record_feedback
        except Exception:
            from feedback import record_feedback

        try:
            record_feedback(
                entry.query, entry.tool,
                accepted=entry.accepted,
                rating=entry.rating,
                details=entry.details,
            )
        except TypeError:
            record_feedback(entry.query, entry.tool, entry.accepted)

        return {"ok": True}

    @app.get("/feedback/summary")
    def feedback_summary():
        try:
            from .feedback import summary
        except Exception:
            from feedback import summary
        return summary()

    @app.post("/learn", dependencies=_admin_guard or [])
    def learn():
        signals = run_learning_cycle()
        return {
            "ok": True,
            "tools_processed": len(signals.get("tool_quality", {})),
            "computed_at": signals.get("computed_at"),
        }

    @app.get("/learn/quality")
    def tool_quality():
        return compute_tool_quality()

    @app.get("/tools/export")
    def tools_export():
        """Export all tools as downloadable JSON."""
        if export_tools_json:
            import json as _json
            return _json.loads(export_tools_json())
        return {"error": "Export module not available"}

    @app.post("/tools/import/json", dependencies=_admin_guard or [])
    async def tools_import_json(payload: dict):
        """Import tools from JSON.  Body: {"tools": [...]} or raw array."""
        if not import_tools_json:
            return {"error": "Import module not available"}
        import json as _json
        items = payload.get("tools", payload) if isinstance(payload, dict) else payload
        return import_tools_json(_json.dumps(items))

    @app.post("/tools/import/csv", dependencies=_admin_guard or [])
    async def tools_import_csv(payload: dict):
        """Import tools from CSV string.  Body: {"csv": "name,desc,...\nrow,..."}"""
        if not import_tools_csv:
            return {"error": "Import module not available"}
        csv_text = payload.get("csv", "")
        if not csv_text:
            return {"error": "No CSV data in 'csv' field"}
        return import_tools_csv(csv_text)

    @app.get("/tools/csv-template")
    def csv_template():
        """Download a CSV template for bulk tool import."""
        if generate_csv_template:
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(generate_csv_template(), media_type="text/csv",
                                     headers={"Content-Disposition": "attachment; filename=praxis_tools_template.csv"})
        return {"error": "Template generator not available"}

    @app.get("/config/weights")
    def config_weights():
        """Return current scoring weights for transparency / tuning."""
        weight_keys = [k for k in (_cfg.DEFAULTS if _cfg else {}) if k.startswith("weight_")]
        return {k: _cfg.get(k) for k in weight_keys} if _cfg else {}

    # ══════════════════════════════════════════════════════════════════
    # PHASE 1 — Anti-Wrapper Shield, Tuesday Test, RFP Generator
    # ══════════════════════════════════════════════════════════════════

    def _import_verification():
        try:
            from .verification import score_tool, score_all_tools, tier_distribution, tuesday_test, generate_rfp
        except ImportError:
            from verification import score_tool, score_all_tools, tier_distribution, tuesday_test, generate_rfp
        return score_tool, score_all_tools, tier_distribution, tuesday_test, generate_rfp

    @app.get("/tools/resilience")
    def tools_resilience():
        """Score every tool with the Anti-Wrapper Verification Shield.
        Returns resilience scores sorted highest-first."""
        score_tool, score_all_tools, *_ = _import_verification()
        reports = score_all_tools(TOOLS)
        return {
            "total": len(reports),
            "tools": [r.to_dict() for r in reports],
        }

    @app.get("/tools/resilience/{tool_name}")
    def tool_resilience(tool_name: str):
        """Resilience report for a single tool."""
        score_tool_fn = _import_verification()[0]
        tool = next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return score_tool_fn(tool).to_dict()

    @app.get("/tools/resilience-summary")
    def tools_resilience_summary():
        """Tier distribution across all tools."""
        *_, tier_dist_fn, _, _ = _import_verification()
        return tier_dist_fn(TOOLS)

    @app.post("/tuesday-test")
    def tuesday_test_endpoint(body: dict):
        """Run the 'Tuesday Test' ROI simulation.

        Body:
            region, role, task_description, hours_per_week_manual,
            error_rate_manual, tool_category, tool_cost_override
        """
        *_, tuesday_fn, _ = _import_verification()
        result = tuesday_fn(
            region=body.get("region", "midwest"),
            role=body.get("role", "admin"),
            task_description=body.get("task_description", "manual data entry"),
            hours_per_week_manual=float(body.get("hours_per_week_manual", 8)),
            error_rate_manual=float(body.get("error_rate_manual", 0.05)),
            tool_category=body.get("tool_category", "automation"),
            tool_cost_override=body.get("tool_cost_override"),
        )
        return result.to_dict()

    @app.post("/rfp/generate")
    def rfp_generate(body: dict):
        """Generate a neutral vendor RFP document.

        Body:
            business_name, industry, team_size, workflow_description,
            tools_to_evaluate (or selected_tools), monthly_budget, pain_points,
            budget_tier, compliance_requirements, constraints
        """
        *_, rfp_fn = _import_verification()
        # Accept either key name from frontend
        tools = body.get("tools_to_evaluate") or body.get("selected_tools", [])
        # Derive budget tier from monthly_budget if provided
        budget = body.get("monthly_budget")
        budget_tier = body.get("budget_tier", "medium")
        if budget is not None:
            budget = float(budget)
            if budget <= 0: budget_tier = "free"
            elif budget <= 100: budget_tier = "low"
            elif budget <= 500: budget_tier = "medium"
            else: budget_tier = "high"
        rfp = rfp_fn(
            business_name=body.get("business_name", "My Business"),
            industry=body.get("industry", "general"),
            team_size=body.get("team_size", "small"),
            workflow_description=body.get("workflow_description", ""),
            selected_tools=tools,
            budget_tier=budget_tier,
            compliance_requirements=body.get("compliance_requirements"),
            constraints=body.get("constraints"),
            tools_list=TOOLS,
        )
        return rfp

    # ══════════════════════════════════════════════════════════════════
    # PHASE 2 — Tiered Directory, Category Pages, Comparison
    # ══════════════════════════════════════════════════════════════════

    @app.get("/tools/tiered")
    def tools_tiered():
        """Return tools grouped by resilience tier with full tool data.
        Used by the Curated Swimlane view and Homepage Sovereign Showcase."""
        score_tool_fn, score_all_fn, *_ = _import_verification()
        reports = score_all_fn(TOOLS)
        by_name = {t.name: t for t in TOOLS}
        tiers = {"sovereign": [], "durable": [], "moderate": [], "fragile": [], "wrapper": []}
        for r in reports:
            t = by_name.get(r.tool_name)
            if not t:
                continue
            entry = {
                "name": t.name,
                "description": t.description,
                "url": t.url,
                "categories": t.categories[:5],
                "tags": t.tags[:5],
                "pricing": t.pricing,
                "integrations": t.integrations[:6],
                "compliance": t.compliance,
                "skill_level": t.skill_level,
                "use_cases": t.use_cases[:4],
                "resilience_score": r.score,
                "grade": r.grade,
                "tier": r.tier,
                "dimensions": r.dimensions,
                "flags": r.flags[:3],
                "summary": r.summary,
            }
            if r.tier in tiers:
                tiers[r.tier].append(entry)
        return {
            "tiers": tiers,
            "counts": {k: len(v) for k, v in tiers.items()},
            "total": len(TOOLS),
        }

    @app.get("/tools/category/{category}")
    def tools_by_category(category: str):
        """Return tools filtered by category, enriched with resilience data."""
        score_tool_fn = _import_verification()[0]
        matches = [t for t in TOOLS if category.lower() in [c.lower() for c in t.categories]]
        results = []
        for t in matches:
            r = score_tool_fn(t)
            results.append({
                "name": t.name,
                "description": t.description,
                "url": t.url,
                "categories": t.categories[:5],
                "tags": t.tags[:5],
                "pricing": t.pricing,
                "integrations": t.integrations[:6],
                "compliance": t.compliance,
                "skill_level": t.skill_level,
                "use_cases": t.use_cases[:4],
                "resilience_score": r.score,
                "grade": r.grade,
                "tier": r.tier,
                "flags": r.flags[:3],
            })
        results.sort(key=lambda x: x["resilience_score"], reverse=True)
        return {
            "category": category,
            "total": len(results),
            "tools": results,
        }

    @app.post("/tools/compare")
    def tools_compare(body: dict):
        """Side-by-side comparison of up to 4 tools with full resilience data."""
        score_tool_fn = _import_verification()[0]
        names = body.get("tools", [])[:4]
        by_name = {t.name.lower(): t for t in TOOLS}
        comparisons = []
        for name in names:
            t = by_name.get(name.lower())
            if not t:
                continue
            r = score_tool_fn(t)
            comparisons.append({
                "name": t.name,
                "description": t.description,
                "url": t.url,
                "categories": t.categories,
                "pricing": t.pricing,
                "integrations": t.integrations,
                "compliance": t.compliance,
                "skill_level": t.skill_level,
                "use_cases": t.use_cases[:6],
                "resilience_score": r.score,
                "grade": r.grade,
                "tier": r.tier,
                "dimensions": r.dimensions,
                "flags": r.flags,
                "summary": r.summary,
            })
        return {"tools": comparisons}

    # ==================================================================
    # Differential Diagnosis Engine Routes
    # ==================================================================

    def _import_differential():
        """Lazy import to avoid circular dependency."""
        try:
            from . import differential
            return differential
        except ImportError:
            import differential
            return differential

    def _import_explain_diff():
        try:
            from .explain import explain_elimination, explain_survival, assemble_presentation
            return explain_elimination, explain_survival, assemble_presentation
        except ImportError:
            from explain import explain_elimination, explain_survival, assemble_presentation
            return explain_elimination, explain_survival, assemble_presentation

    def _import_profile_matrix():
        try:
            from .profile import build_constraint_matrix
            return build_constraint_matrix
        except ImportError:
            from profile import build_constraint_matrix
            return build_constraint_matrix

    def _import_learning_overrides():
        try:
            from .learning import compute_override_rate, get_elimination_efficacy
            return compute_override_rate, get_elimination_efficacy
        except ImportError:
            from learning import compute_override_rate, get_elimination_efficacy
            return compute_override_rate, get_elimination_efficacy

    def _import_interpreter_structured():
        try:
            from .interpreter import extract_structured_intents
            return extract_structured_intents
        except ImportError:
            from interpreter import extract_structured_intents
            return extract_structured_intents

    @app.post("/differential")
    def differential_diagnosis(body: dict):
        """
        Execute the full differential diagnosis pipeline.

        Body:
            {
                "query": str (required),
                "profile_id": str (optional — loads saved profile),
                "profile": { ... } (optional — inline profile override),
                "top_n": int (optional, default 5)
            }

        Returns the complete DifferentialResult with survivors,
        eliminated tools, funnel narrative, and stage metadata.
        """
        diff = _import_differential()
        query = body.get("query", "").strip()
        if not query:
            return {"error": "Query is required", "detail": "Provide a 'query' field."}

        top_n = body.get("top_n", 5)

        # Load or construct profile
        profile = None
        profile_id = body.get("profile_id")
        if profile_id:
            profile = load_profile(profile_id)

        inline = body.get("profile")
        if inline and not profile:
            profile = UserProfile(
                profile_id=inline.get("profile_id", "inline"),
                industry=inline.get("industry", ""),
                budget=inline.get("budget", "medium"),
                team_size=inline.get("team_size", "solo"),
                skill_level=inline.get("skill_level", "beginner"),
                existing_tools=inline.get("existing_tools", []),
                goals=inline.get("goals", []),
                constraints=inline.get("constraints", []),
                preferences=inline.get("preferences", {}),
            )

        result = diff.generate_differential(query, profile=profile, top_n=top_n)

        # Enrich with explain layer
        explain_elim, explain_surv, assemble = _import_explain_diff()
        presentation = assemble(result.survivors, result.eliminated)

        return {
            "query": result.query,
            "profile_id": result.profile_id,
            "clarification_needed": result.clarification_needed,
            "clarification": result.clarification,
            "funnel_narrative": result.funnel_narrative,
            "stages": result.stages,
            "survivors": result.survivors,
            "eliminated": result.eliminated,
            "presentation": {
                "summary": presentation["summary"],
                "survivor_cards": presentation["survivor_cards"],
                "elimination_cards": presentation["elimination_cards"],
                "notable_eliminations": presentation["notable_eliminations"],
                "total_survivors": presentation["total_survivors"],
                "total_eliminated": presentation["total_eliminated"],
            },
        }

    @app.post("/differential/intent")
    def differential_intent(body: dict):
        """
        Parse a query through the structured intent extractor.
        Useful for previewing how the pipeline will interpret a query
        before running the full diagnosis.

        Body: { "query": str }
        """
        extract = _import_interpreter_structured()
        query = body.get("query", "").strip()
        if not query:
            return {"error": "Query is required"}
        return extract(query)

    @app.post("/differential/constraint-matrix")
    def differential_constraint_matrix(body: dict):
        """
        Generate a Constraint Matrix from a profile.
        Shows the executable elimination rules derived from user context.

        Body: { "profile_id": str } or { "profile": { inline profile } }
        """
        build_matrix = _import_profile_matrix()

        profile = None
        profile_id = body.get("profile_id")
        if profile_id:
            profile = load_profile(profile_id)

        inline = body.get("profile")
        if inline and not profile:
            profile = UserProfile(
                profile_id=inline.get("profile_id", "inline"),
                industry=inline.get("industry", ""),
                budget=inline.get("budget", "medium"),
                team_size=inline.get("team_size", "solo"),
                skill_level=inline.get("skill_level", "beginner"),
                existing_tools=inline.get("existing_tools", []),
                goals=inline.get("goals", []),
                constraints=inline.get("constraints", []),
                preferences=inline.get("preferences", {}),
            )

        if not profile:
            return {"error": "No profile found", "detail": "Provide profile_id or inline profile."}

        return build_matrix(profile)

    @app.post("/differential/challenge")
    def differential_challenge(body: dict):
        """
        Challenge an elimination result.
        Records an override and returns acknowledgement.

        Body: {
            "query": str,
            "tool_name": str,
            "reason_code": str,
            "profile_id": str (optional),
            "comment": str (optional)
        }
        """
        diff = _import_differential()
        query = body.get("query", "")
        tool_name = body.get("tool_name", "")
        reason_code = body.get("reason_code", "UNKNOWN")
        profile_id = body.get("profile_id")

        if not tool_name:
            return {"error": "tool_name is required"}

        entry = diff.record_override(
            query=query,
            eliminated_tool=tool_name,
            reason_code=reason_code,
            profile_id=profile_id,
        )

        return {
            "status": "recorded",
            "message": (
                f"Your challenge of {tool_name}'s elimination has been recorded. "
                f"This feedback helps calibrate our filters."
            ),
            "entry": entry,
        }

    @app.get("/differential/override-stats")
    def differential_override_stats():
        """
        Return override statistics for monitoring filter accuracy.
        High override rates signal aggressive filters that need recalibration.
        """
        compute_rate, _ = _import_learning_overrides()
        return compute_rate()

    @app.get("/differential/filter-health")
    def differential_filter_health():
        """
        Cross-reference override data with tool quality metrics.
        Determines whether eliminations are vindicated or questionable.
        """
        _, get_efficacy = _import_learning_overrides()
        return get_efficacy()

    # ==================================================================
    # 2026 Security Blueprint: Sovereignty, Nutrition, Outcomes, Prompts
    # ==================================================================

    def _import_sovereignty():
        from praxis.sovereignty import (
            assess_sovereignty, get_trust_badge, filter_by_sovereignty,
            assess_all_tools, get_sovereignty_intel,
        )
        return assess_sovereignty, get_trust_badge, filter_by_sovereignty, assess_all_tools, get_sovereignty_intel

    def _import_nutrition():
        from praxis.nutrition import generate_nutrition_label, generate_all_labels, praxis_self_label
        return generate_nutrition_label, generate_all_labels, praxis_self_label

    def _import_outcomes():
        from praxis.outcomes import (
            detect_outcome_intent, assemble_outcome_results,
            get_outcome_pills, get_outcome_detail,
        )
        return detect_outcome_intent, assemble_outcome_results, get_outcome_pills, get_outcome_detail

    def _import_prompt_assist():
        from praxis.prompt_assist import (
            generate_optimized_prompt, bridge_prompt, decompose_intent,
            get_available_workflows, get_available_models,
        )
        return generate_optimized_prompt, bridge_prompt, decompose_intent, get_available_workflows, get_available_models

    # ── Sovereignty Routes ──

    @app.get("/sovereignty/assess/{tool_name}")
    def sovereignty_assess(tool_name: str):
        """Assess sovereignty risk for a specific tool."""
        assess, badge, *_ = _import_sovereignty()
        tool = next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return {
            "tool": tool_name,
            "assessment": assess(tool),
            "badge": badge(tool),
        }

    @app.get("/sovereignty/dashboard")
    def sovereignty_dashboard_data():
        """
        Return sovereignty assessment for all tools.
        Powers the Sovereignty Dashboard UI.
        """
        *_, assess_all, _ = _import_sovereignty()
        raw = assess_all(TOOLS)
        # Reshape for frontend consumption
        by_tier = raw.get("by_tier", {})
        return {
            "summary": {
                "us_controlled": by_tier.get("us_controlled", 0),
                "allied": by_tier.get("allied", 0),
                "high_risk": by_tier.get("high_risk", 0),
                "unknown": by_tier.get("unknown", 0),
                "total": raw.get("total", 0),
                "zdr_percentage": raw.get("zdr_percentage", 0),
                "average_risk_score": raw.get("average_risk_score", 0),
            },
            "tools": [
                {
                    "tool_name": a["tool_name"],
                    "assessment": a,
                    "badge": a.get("badge", {}),
                }
                for a in raw.get("assessments", [])
            ],
            "high_risk_tools": raw.get("high_risk_tools", []),
        }

    @app.get("/sovereignty/intel/{tool_name}")
    def sovereignty_intel(tool_name: str):
        """Get raw sovereignty intelligence for a tool."""
        *_, get_intel = _import_sovereignty()
        intel = get_intel(tool_name)
        if not intel:
            return {"error": f"No sovereignty intel for '{tool_name}'", "tool": tool_name}
        return {"tool": tool_name, "intel": intel}

    # ── Nutrition Label Routes ──
    # NOTE: Static paths must come before dynamic {tool_name} to avoid shadowing

    @app.get("/nutrition/self-label")
    def nutrition_self():
        """Show Praxis platform's own AI Nutrition Label."""
        _, _, self_label = _import_nutrition()
        return self_label()

    @app.get("/nutrition/all")
    def nutrition_all():
        """Generate AI Nutrition Labels for all tools (batch)."""
        _, gen_all, _ = _import_nutrition()
        *_, assess_all, _ = _import_sovereignty()
        sov_data = assess_all(TOOLS)
        assessments = {
            item["tool_name"]: item["assessment"]
            for item in sov_data.get("tools", [])
        }
        return gen_all(TOOLS, assessments)

    @app.get("/nutrition/{tool_name}")
    def nutrition_label(tool_name: str):
        """Generate AI Nutrition Label for a specific tool."""
        gen_label, _, _ = _import_nutrition()
        assess, *_ = _import_sovereignty()
        tool = next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        sov_data = assess(tool)
        return gen_label(tool, sov_data)

    # ── Outcome Routes ──

    @app.post("/outcomes/recommend")
    def outcomes_recommend(body: dict):
        """
        Outcome-oriented recommendation.

        Body: {
            "query": str,
            "force_outcome": str | null,  // time_saved, cost_reduction, revenue_growth, compliance
            "profile_id": str | null,
        }
        """
        _, assemble, _, _ = _import_outcomes()
        query = body.get("query", "")
        force = body.get("force_outcome")
        profile = None
        pid = body.get("profile_id")
        if pid:
            profile = load_profile(pid)

        tools = find_tools(query, top_n=20, profile=profile)
        result = assemble(tools, query, profile=profile, force_outcome=force)
        # Serialize tool objects in ranked_results
        for entry in result.get("ranked_results", []):
            t = entry.pop("tool", None)
            if t:
                entry["tool_name"] = t.name
                entry["tool_description"] = t.description
        return result

    @app.get("/outcomes/pills")
    def outcomes_pills():
        """Return outcome navigation pills for the UI."""
        _, _, get_pills, _ = _import_outcomes()
        return {"pills": get_pills()}

    @app.get("/outcomes/{outcome_id}")
    def outcomes_detail(outcome_id: str):
        """Get details for a specific outcome pillar."""
        _, _, _, get_detail = _import_outcomes()
        detail = get_detail(outcome_id)
        if not detail:
            return {"error": f"Unknown outcome pillar '{outcome_id}'"}
        return detail

    # ── Prompt Assistance Routes ──

    @app.post("/prompt-assist/generate")
    def prompt_generate(body: dict):
        """
        Generate an optimized prompt for a tool/model.

        Body: {
            "query": str,
            "tool_name": str | null,
            "target_model": str | null,
            "workflow_id": str | null,
            "step_answers": { step_id: chosen_option } | null,
        }
        """
        gen_prompt, _, _, _, _ = _import_prompt_assist()
        return gen_prompt(
            query=body.get("query", ""),
            tool_name=body.get("tool_name"),
            target_model=body.get("target_model"),
            workflow_id=body.get("workflow_id"),
            step_answers=body.get("step_answers"),
        )

    @app.post("/prompt-assist/bridge")
    def prompt_bridge(body: dict):
        """
        Transfer a prompt between model dialects.

        Body: {
            "source_prompt": str,
            "source_model": str,
            "target_model": str,
        }
        """
        _, bridge, _, _, _ = _import_prompt_assist()
        return bridge(
            source_prompt=body.get("source_prompt", ""),
            source_model=body.get("source_model", "gpt-4"),
            target_model=body.get("target_model", "claude"),
        )

    @app.post("/prompt-assist/decompose")
    def prompt_decompose(body: dict):
        """
        Decompose a query into DMN decision steps.

        Body: {
            "query": str,
            "workflow_id": str | null,
        }
        """
        _, _, decompose, _, _ = _import_prompt_assist()
        return decompose(
            query=body.get("query", ""),
            workflow_id=body.get("workflow_id"),
        )

    @app.get("/prompt-assist/workflows")
    def prompt_workflows():
        """List available DMN workflow templates."""
        _, _, _, get_wf, _ = _import_prompt_assist()
        return {"workflows": get_wf()}

    @app.get("/prompt-assist/models")
    def prompt_models():
        """List available model dialects for PromptBridge."""
        _, _, _, _, get_models = _import_prompt_assist()
        return {"models": get_models()}

    # ==================================================================
    # 2026 Trust Badge Architecture Routes
    # ==================================================================

    def _find_tool(tool_name: str):
        """Lookup a tool by name (case-insensitive)."""
        return next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)

    def _import_trust_badges():
        from . import trust_badges
        return (
            trust_badges.calculate_all_badges,
            trust_badges.calculate_all_tools_badges,
            trust_badges.get_badge_categories,
            trust_badges.get_badge_intel,
            trust_badges.generate_stat_bar,
        )

    def _import_portability():
        from . import portability
        return (
            portability.calculate_exit_portability,
            portability.calculate_all_portability,
            portability.compare_portability,
        )

    def _import_learning_psr():
        from . import learning
        return (
            learning.compute_psr_scores,
            learning.compute_roi_metrics,
            learning.apply_psr_to_tools,
        )

    def _import_philosophy_badge():
        from . import philosophy
        return philosophy.assess_trust_badge_risk

    # ── Trust Badge Routes ──

    @app.get("/trust-badges/categories")
    def badge_categories():
        """Return all 9 badge category definitions with visual system."""
        _, _, get_cats, _, _ = _import_trust_badges()
        return {"categories": get_cats()}

    @app.get("/trust-badges/tool/{tool_name}")
    def badge_tool(tool_name: str):
        """Calculate all trust badges for a specific tool."""
        calc_badges, _, _, _, _ = _import_trust_badges()
        tool = _find_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return calc_badges(tool)

    @app.get("/trust-badges/dashboard")
    def badge_dashboard():
        """Full trust badge dashboard with all tools and aggregate statistics."""
        _, calc_all, _, _, _ = _import_trust_badges()
        result = calc_all(TOOLS)
        return {
            "summary": result["summary"],
            "tools": [
                {
                    "tool_name": name,
                    "trust_score": profile["trust_score"],
                    "trust_grade": profile["trust_grade"],
                    "badge_count": profile["badge_count"],
                    "has_risk_flag": profile["has_risk_flag"],
                    "risk_flag_count": profile["risk_flag_count"],
                    "primary_badges": profile["primary_badges"],
                    "summary": profile["summary"],
                }
                for name, profile in result["tools"].items()
            ],
            "total_tools": result["summary"]["total"],
        }

    @app.get("/trust-badges/stat-bar")
    def badge_stat_bar():
        """Generate the Dynamic Results Stat Bar for the current tool set."""
        _, _, _, _, gen_stat = _import_trust_badges()
        return gen_stat(TOOLS)

    @app.get("/trust-badges/intel/{tool_name}")
    def badge_intel(tool_name: str):
        """Return raw badge intelligence data for a tool."""
        _, _, _, get_intel, _ = _import_trust_badges()
        intel = get_intel(tool_name)
        if not intel:
            return {"error": f"No badge intelligence for '{tool_name}'", "tool_name": tool_name}
        return {"tool_name": tool_name, "intel": intel}

    # ── Portability Routes ──

    @app.get("/portability/tool/{tool_name}")
    def portability_tool(tool_name: str):
        """Calculate exit portability score for a specific tool."""
        calc_port, _, _ = _import_portability()
        tool = _find_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return calc_port(tool)

    @app.get("/portability/all")
    def portability_all():
        """Calculate portability scores for all tools."""
        _, calc_all, _ = _import_portability()
        return calc_all(TOOLS)

    @app.post("/portability/compare")
    def portability_compare(body: dict):
        """
        Compare portability for multiple tools side-by-side.

        Body: { "tools": ["ChatGPT", "Notion AI", "Salesforce"] }
        """
        _, _, compare = _import_portability()
        tool_names = body.get("tools", [])
        return {"comparisons": compare(tool_names, TOOLS)}

    # ── PSR Telemetry Routes ──

    @app.get("/telemetry/psr")
    def telemetry_psr():
        """Compute Prompt Success Rate scores from verified telemetry."""
        compute_psr, _, _ = _import_learning_psr()
        return {"psr_scores": compute_psr()}

    @app.get("/telemetry/roi")
    def telemetry_roi():
        """Compute verified ROI metrics from user feedback."""
        _, compute_roi, _ = _import_learning_psr()
        return {"roi_metrics": compute_roi()}

    @app.post("/telemetry/apply-psr")
    def telemetry_apply():
        """Apply computed PSR/OQS scores to in-memory tools (admin)."""
        _, _, apply_psr = _import_learning_psr()
        scores = apply_psr()
        return {"applied": len(scores), "scores": scores}

    # ── Badge-Aware Risk Assessment ──

    @app.get("/risk/badge-assessment/{tool_name}")
    def risk_badge_assessment(tool_name: str):
        """Extended risk assessment incorporating trust badge data."""
        assess = _import_philosophy_badge()
        tool = _find_tool(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return assess(tool)
    # ══════════════════════════════════════════════════════════════
    # Cognitive Offloading Safeguards — Blueprint 2026
    # ══════════════════════════════════════════════════════════════

    # ── Safeguard 1: Architectural Boundary Enforcement ──

    @app.post("/safeguards/validate-boundaries")
    def validate_boundaries(body: dict):
        """
        Validate LLM-generated code against Hexagonal Architecture boundaries.

        Body: { "code": "import requests\\n...", "layer": "domain" }
        """
        from praxis.engine import ArchitecturalBoundaryEnforcer
        code = body.get("code", "")
        layer = body.get("layer", "domain")
        enforcer = ArchitecturalBoundaryEnforcer()
        return enforcer.validate_llm_output(code, layer=layer)

    @app.post("/safeguards/generate-prompt")
    def generate_constrained_prompt(body: dict):
        """
        Generate a Hexagonal-Architecture-scoped prompt for an LLM.

        Body: {
            "port_name": "find_tools",
            "input_types": {"query": "str", "limit": "int"},
            "return_type": "List[Tool]",
            "domain_rules": ["max 50 results", "validate query length"]
        }
        """
        from praxis.engine import ArchitecturalBoundaryEnforcer, PortContract
        contract = PortContract(
            port_name=body.get("port_name", "unnamed_port"),
            input_types=body.get("input_types", {}),
            return_type=body.get("return_type", "Any"),
            domain_rules=body.get("domain_rules", []),
        )
        enforcer = ArchitecturalBoundaryEnforcer()
        return {"prompt": enforcer.generate_constrained_prompt(contract)}

    # ── Safeguard 2: Complexity Ceiling Enforcement ──

    @app.post("/safeguards/complexity-check")
    def complexity_check(body: dict):
        """
        Enforce complexity ceilings on submitted code.

        Body: {
            "code": "def foo():\\n  ...",
            "max_cyclomatic": 10,   (optional, default 10)
            "max_nesting": 5        (optional, default 5)
        }
        """
        from praxis.introspect import enforce_complexity_ceilings
        code = body.get("code", "")
        return enforce_complexity_ceilings(
            code,
            max_cyclomatic=body.get("max_cyclomatic", 10),
            max_nesting=body.get("max_nesting", 5),
        )

    # ── Safeguard 3: LLM-to-LLM Verification ──

    @app.post("/safeguards/mutation-test")
    def mutation_test(body: dict):
        """
        Generate a semantically-mutated variant of code for verification.

        Body: { "code": "def foo(x):\\n  return x > 5" }
        """
        from praxis.explain import generate_mutation
        code = body.get("code", "")
        mutated, mutations = generate_mutation(code)
        return {
            "original_code": code,
            "mutated_code": mutated,
            "mutations_applied": mutations,
        }

    @app.post("/safeguards/verify-consistency")
    def verify_consistency(body: dict):
        """
        Run dual-agent consistency verification on code.

        Body: { "code": "def process(items):\\n  ..." }
        """
        from praxis.intelligence import VerificationPipeline
        code = body.get("code", "")
        pipeline = VerificationPipeline(
            similarity_threshold=body.get("threshold", 0.95)
        )
        return pipeline.execute_consistency_check(code)

    # ── Safeguard 4: Boring Code Optimisation ──

    @app.post("/safeguards/boring-prompt")
    def boring_prompt(body: dict):
        """
        Build a KERNEL-framework prompt that steers LLMs toward
        maintainable "boring" code.

        Body: {
            "task_goal": "Parse CSV and return validated records",
            "input_context": "existing code snippet...",
            "verification_criteria": ["< 30 lines per function"],
            "extra_constraints": ["Use pathlib for paths"]
        }
        """
        from praxis.interpreter import PromptInterpreter, KernelPromptContext
        ctx = KernelPromptContext(
            task_goal=body.get("task_goal", ""),
            input_context=body.get("input_context", ""),
            verification_criteria=body.get("verification_criteria", []),
            max_function_lines=body.get("max_function_lines", 30),
        )
        interpreter = PromptInterpreter(
            extra_constraints=body.get("extra_constraints"),
        )
        return {"prompt": interpreter.build_boring_prompt(ctx)}

    @app.post("/safeguards/boring-validate")
    def boring_validate(body: dict):
        """
        Validate code against boring-code compliance rules.

        Body: { "code": "def foo():\\n  ..." }
        """
        from praxis.interpreter import PromptInterpreter
        code = body.get("code", "")
        interpreter = PromptInterpreter()
        return interpreter.validate_boring_compliance(code)

    # ── Safeguard Dashboard (all-in-one) ──

    @app.post("/safeguards/full-analysis")
    def safeguard_full_analysis(body: dict):
        """
        Run all 4 safeguards on a piece of code and return a unified report.

        Body: {
            "code": "...",
            "layer": "domain",       (optional)
            "max_cyclomatic": 10,    (optional)
            "max_nesting": 5         (optional)
        }
        """
        from praxis.engine import ArchitecturalBoundaryEnforcer
        from praxis.introspect import enforce_complexity_ceilings
        from praxis.intelligence import VerificationPipeline
        from praxis.interpreter import PromptInterpreter

        code = body.get("code", "")
        layer = body.get("layer", "domain")

        # S1: Architectural boundaries
        enforcer = ArchitecturalBoundaryEnforcer()
        boundaries = enforcer.validate_llm_output(code, layer=layer)

        # S2: Complexity ceilings
        complexity = enforce_complexity_ceilings(
            code,
            max_cyclomatic=body.get("max_cyclomatic", 10),
            max_nesting=body.get("max_nesting", 5),
        )

        # S3: Consistency verification
        pipeline = VerificationPipeline()
        consistency = pipeline.execute_consistency_check(code)

        # S4: Boring code compliance
        boring = PromptInterpreter().validate_boring_compliance(code)

        # Unified verdict
        all_pass = (
            boundaries["valid"]
            and complexity["accepted"]
            and consistency["verified"]
            and boring["compliant"]
        )

        return {
            "all_safeguards_pass": all_pass,
            "safeguard_1_boundaries": boundaries,
            "safeguard_2_complexity": complexity,
            "safeguard_3_verification": consistency,
            "safeguard_4_boring_code": boring,
            "summary": (
                "All 4 safeguards passed — code is safe to accept"
                if all_pass
                else "One or more safeguards failed — review required"
            ),
        }

    # ── Fort Knox Security Status Dashboard ─────────────────────────
    import os as _fk_os

    @app.get("/fort-knox/status")
    def fort_knox_status():
        """
        Live status of the Fort Knox security architecture.

        Returns axiom states, RASP mode, safeguard operational status,
        and architecture posture for the Fort Knox dashboard.
        """
        rasp_mode = _fk_os.environ.get("PRAXIS_RASP_MODE", "enforce").lower()
        cors_raw = _fk_os.environ.get("PRAXIS_CORS_ORIGINS", "")
        cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

        # Check each safeguard is importable and operational
        safeguard_status = []
        sg_names = [
            ("Architectural Boundaries", "praxis.engine", "ArchitecturalBoundaryEnforcer"),
            ("Complexity Ceilings", "praxis.introspect", "enforce_complexity_ceilings"),
            ("LLM-to-LLM Verification", "praxis.intelligence", "VerificationPipeline"),
            ("Boring Code Optimisation", "praxis.interpreter", "PromptInterpreter"),
        ]
        for label, mod_path, cls_name in sg_names:
            try:
                import importlib
                mod = importlib.import_module(mod_path)
                obj = getattr(mod, cls_name, None)
                safeguard_status.append({
                    "name": label,
                    "module": mod_path,
                    "class": cls_name,
                    "operational": obj is not None,
                })
            except Exception as exc:
                safeguard_status.append({
                    "name": label,
                    "module": mod_path,
                    "class": cls_name,
                    "operational": False,
                    "error": str(exc)[:120],
                })

        safeguards_active = sum(1 for s in safeguard_status if s["operational"])

        return {
            "architecture": "Hexagonal (Ports and Adapters)",
            "philosophy": "Fail-Closed",
            "rasp_mode": rasp_mode,
            "cors_policy": "strict-allowlist" if cors_origins else "open-dev",
            "cors_origins_count": len(cors_origins),
            "safeguards_active": safeguards_active,
            "safeguard_status": safeguard_status,
            "axioms": {
                "axiom1": {
                    "name": "The Moat",
                    "description": "Outer Perimeter — CORS + Rate Limiting",
                    "active": True,
                },
                "axiom2": {
                    "name": "The Sally Port",
                    "description": "RASP Middleware — Runtime Inspection",
                    "active": rasp_mode != "off",
                },
                "axiom3": {
                    "name": "Identity Gates",
                    "description": "AuthN/AuthZ — Zero-Trust JWT",
                    "active": True,
                },
                "axiom4": {
                    "name": "Internal Scanners",
                    "description": "AST Taint Propagation",
                    "active": True,
                },
                "axiom5": {
                    "name": "The Vault",
                    "description": "Bounded Write Queues + File Locking",
                    "active": True,
                },
            },
            "layers": {
                "presentation": {
                    "analogue": "The Moat & Sally Port",
                    "role": "External I/O: REST, APIs, UIs, webhooks",
                },
                "workflow": {
                    "analogue": "The Vault",
                    "role": "PRISM engine, state management, multi-agent pipelines",
                },
                "persistence": {
                    "analogue": "The Ledgers",
                    "role": "Database transactions, vector stores, knowledge graphs",
                },
            },
            "prism_agents": ["Analyzer", "Selector", "Critic", "Adder"],
            "threat_mitigations": 6,
        }

    # ══════════════════════════════════════════════════════════════════
    # ──  PIPELINE v3.0: Ingestion, Trust Decay, SMB Scoring  ────────
    # ══════════════════════════════════════════════════════════════════

    # ── Ingestion Pipeline ──

    @app.post("/pipeline/ingest/trigger")
    def pipeline_trigger():
        """
        Trigger the daily ingestion pipeline.

        Fetches from TAAFT, Toolify, Futurepedia → Triple Match → Enrich
        → Score → Tier → Route to queues.
        """
        from praxis.ingestion_engine import run_daily_pipeline
        return run_daily_pipeline()

    @app.get("/pipeline/status")
    def pipeline_status():
        """
        Dashboard status of the ingestion pipeline.

        Returns queue sizes, tier distribution, and last run metadata.
        """
        from praxis.ingestion_engine import (
            get_review_queue, get_approved_catalog, get_sandbox,
        )
        review = get_review_queue()
        approved = get_approved_catalog()
        sandbox = get_sandbox()
        return {
            "review_queue_size": len(review),
            "approved_catalog_size": len(approved),
            "sandbox_size": len(sandbox),
            "tier_distribution": {
                "tier_1_sovereign": sum(1 for t in approved if t.get("tier") == "tier_1"),
                "tier_2_durable": len(sandbox),
                "tier_3_vertical": sum(1 for t in approved if t.get("tier") == "tier_3"),
            },
            "pipeline_version": "3.0",
        }

    @app.get("/pipeline/review-queue")
    def pipeline_review_queue():
        """Return the HITL review queue for Tier 1 candidates."""
        from praxis.ingestion_engine import get_review_queue
        return {"queue": get_review_queue()}

    @app.get("/pipeline/approved")
    def pipeline_approved():
        """Return all approved Tier 1 (Sovereign) tools."""
        from praxis.ingestion_engine import get_approved_catalog
        return {"catalog": get_approved_catalog()}

    @app.get("/pipeline/sandbox")
    def pipeline_sandbox():
        """Return Tier 2 (Durable) sandbox tools."""
        from praxis.ingestion_engine import get_sandbox
        return {"sandbox": get_sandbox()}

    @app.post("/pipeline/approve/{tool_name}")
    def pipeline_approve(tool_name: str):
        """HITL approval — promote tool from review queue to Tier 1 catalog."""
        from praxis.ingestion_engine import approve_tool
        if approve_tool(tool_name):
            return {"status": "approved", "tool": tool_name}
        return {"status": "not_found", "tool": tool_name}

    @app.post("/pipeline/reject/{tool_name}")
    def pipeline_reject(tool_name: str):
        """HITL rejection — remove tool from review queue."""
        from praxis.ingestion_engine import reject_tool
        if reject_tool(tool_name):
            return {"status": "rejected", "tool": tool_name}
        return {"status": "not_found", "tool": tool_name}

    @app.post("/pipeline/promotion-sweep")
    def pipeline_promotion_sweep():
        """
        Run the weekly Tier 2 → Tier 1 promotion sweep.

        Checks if any sandbox tools now qualify for Sovereign status.
        """
        from praxis.ingestion_engine import run_promotion_sweep
        promoted = run_promotion_sweep()
        return {"promoted": promoted, "count": len(promoted)}

    @app.get("/pipeline/why-included/{tool_name}")
    def pipeline_why_included(tool_name: str):
        """
        Generate the deterministic 'Why Included?' tooltip for a tool.

        Returns the structured reasoning chain:
        ✓ Consensus Verification, ✓ Maintenance Confirmed,
        ✓ SMB Aligned, ✓ Operational Safety.
        """
        from praxis.ingestion_engine import (
            get_approved_catalog, get_review_queue, generate_why_included,
            EnrichedTool,
        )
        all_tools = get_approved_catalog() + get_review_queue()
        found = next(
            (t for t in all_tools
             if t.get("canonical_name", "").lower() == tool_name.lower()),
            None,
        )
        if not found:
            return {"error": "Tool not found in pipeline catalog", "tool": tool_name}
        enriched = EnrichedTool.from_dict(found)
        return generate_why_included(enriched)

    # ── Trust Decay Monitoring ──

    @app.post("/trust-decay/sweep")
    def trust_decay_sweep():
        """
        Execute a full trust decay monitoring sweep.

        Checks all Tier 1 and Tier 3 tools for:
        - Pricing page structural changes
        - Review sentiment anomalies
        - SSL certificate validity
        - DNS routing changes
        """
        from praxis.trust_decay import run_trust_sweep
        result = run_trust_sweep()
        return result.to_dict()

    @app.get("/trust-decay/alerts")
    def trust_decay_alerts(severity: str = None, tool_name: str = None):
        """Return active trust decay alerts, optionally filtered."""
        from praxis.trust_decay import get_decay_alerts
        return {"alerts": get_decay_alerts(severity=severity, tool_name=tool_name)}

    @app.get("/trust-decay/summary")
    def trust_decay_summary():
        """Dashboard summary of the trust decay monitoring system."""
        from praxis.trust_decay import get_decay_summary
        return get_decay_summary()

    @app.get("/trust-decay/tool/{tool_name}")
    def trust_decay_tool_status(tool_name: str):
        """Get trust status for a specific tool (badge + active signals)."""
        from praxis.trust_decay import get_tool_trust_status
        return get_tool_trust_status(tool_name)

    @app.post("/trust-decay/acknowledge/{tool_name}")
    def trust_decay_acknowledge(tool_name: str):
        """Acknowledge a decay alert (HITL verification)."""
        from praxis.trust_decay import acknowledge_alert
        if acknowledge_alert(tool_name):
            return {"status": "acknowledged", "tool": tool_name}
        return {"status": "not_found", "tool": tool_name}

    @app.post("/trust-decay/dismiss/{tool_name}")
    def trust_decay_dismiss(tool_name: str):
        """Dismiss a decay alert as false positive."""
        from praxis.trust_decay import dismiss_alert
        if dismiss_alert(tool_name):
            return {"status": "dismissed", "tool": tool_name}
        return {"status": "not_found", "tool": tool_name}

    @app.get("/trust-decay/history")
    def trust_decay_history():
        """Return historical decay alerts."""
        from praxis.trust_decay import get_alert_history
        return {"history": get_alert_history()}

    # ── SMB Relevance Scoring ──

    @app.get("/smb/score/{tool_name}")
    def smb_score_tool(tool_name: str):
        """
        Calculate the SMB Relevance Score for a specific tool.

        Returns the three-dimensional breakdown:
        - Vertical Match (0-40)
        - Pricing Accessibility (0-30)
        - Operational Complexity (0-30)
        """
        from praxis.smb_scoring import score_smb_relevance
        tool = next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)
        if not tool:
            return {"error": "Tool not found", "tool": tool_name}
        breakdown = score_smb_relevance(tool)
        return breakdown.to_dict()

    @app.get("/smb/score-all")
    def smb_score_all():
        """Calculate SMB Relevance Scores for all tools in the catalog."""
        from praxis.smb_scoring import score_smb_relevance
        results = []
        for tool in TOOLS:
            breakdown = score_smb_relevance(tool)
            results.append({
                "name": tool.name,
                "total_score": breakdown.total_score,
                "passes_gate": breakdown.passes_gate,
                "vertical_score": breakdown.vertical_score,
                "pricing_score": breakdown.pricing_score,
                "complexity_score": breakdown.complexity_score,
            })
        results.sort(key=lambda r: r["total_score"], reverse=True)
        return {"tools": results, "count": len(results)}

    @app.get("/smb/vertical-fit/{tool_name}")
    def smb_vertical_fit(tool_name: str, vertical: str = None):
        """Calculate the Vertical Fit Score for Tier 3 eligibility."""
        from praxis.smb_scoring import score_vertical_fit
        tool = next((t for t in TOOLS if t.name.lower() == tool_name.lower()), None)
        if not tool:
            return {"error": "Tool not found", "tool": tool_name}
        score = score_vertical_fit(tool, vertical=vertical)
        return {"tool": tool_name, "vertical": vertical, "vertical_fit_score": score}

    @app.get("/smb/verticals")
    def smb_verticals():
        """List all defined SMB verticals with keyword counts."""
        from praxis.smb_scoring import SMB_VERTICALS
        return {
            "verticals": {
                k: {"keywords": len(v), "examples": v[:3]}
                for k, v in SMB_VERTICALS.items()
            },
            "count": len(SMB_VERTICALS),
        }

    # ── Relationship Extraction ──

    @app.post("/relationships/extract/{tool_name}")
    def extract_tool_relationships(tool_name: str, body: dict = None):
        """
        Extract ecosystem relationships (competitors, integrations,
        supplements) for a tool using LLM or rule-based fallback.
        """
        from praxis.relationship_extraction import extract_relationships
        body = body or {}
        use_llm = body.get("use_llm", True)
        result = extract_relationships(tool_name, use_llm=use_llm)
        return result.to_dict()

    @app.get("/relationships/hitl-queue")
    def relationships_hitl_queue():
        """Return pending HITL extractions for human review."""
        from praxis.relationship_extraction import get_hitl_queue
        return {"queue": get_hitl_queue()}

    @app.post("/relationships/approve")
    def relationships_approve(body: dict):
        """Approve a HITL-queued extraction."""
        from praxis.relationship_extraction import approve_extraction
        source = body.get("source", "")
        target = body.get("target", "")
        if approve_extraction(source, target):
            return {"status": "approved", "source": source, "target": target}
        return {"status": "not_found"}

    @app.post("/relationships/reject")
    def relationships_reject(body: dict):
        """Reject a HITL-queued extraction."""
        from praxis.relationship_extraction import reject_extraction
        source = body.get("source", "")
        target = body.get("target", "")
        if reject_extraction(source, target):
            return {"status": "rejected", "source": source, "target": target}
        return {"status": "not_found"}

    @app.get("/relationships/summary")
    def relationships_summary():
        """Summary statistics for the extraction system."""
        from praxis.relationship_extraction import get_extraction_summary
        return get_extraction_summary()

    # ── Pipeline Constants ──

    @app.get("/pipeline/constants")
    def pipeline_constants():
        """Return all pipeline v3.0 constants for transparency."""
        from praxis.pipeline_constants import (
            TIER_1_MIN_SURVIVAL, TIER_1_MIN_SMB, TIER_1_CONFIDENCE_AUTO,
            TIER_2_MIN_SURVIVAL, TIER_2_PROMOTION_SURVIVAL,
            TIER_3_MIN_VERTICAL_FIT,
            WEIGHTS, BADGE_TIERS,
            TRUST_DECAY_INTERVAL_HOURS,
            SMB_PRICING_CEILING,
            LLM_EXTRACTION_AUTO_COMMIT,
            TARGET_TRUST_DECAY_PRECISION, TARGET_INGESTION_LATENCY_HOURS,
            TARGET_SAYDO_VARIANCE, TARGET_HITL_THROUGHPUT_PER_HOUR,
        )
        return {
            "tier_thresholds": {
                "tier_1_min_survival": TIER_1_MIN_SURVIVAL,
                "tier_1_min_smb": TIER_1_MIN_SMB,
                "tier_1_confidence_auto": TIER_1_CONFIDENCE_AUTO,
                "tier_2_min_survival": TIER_2_MIN_SURVIVAL,
                "tier_2_promotion_survival": TIER_2_PROMOTION_SURVIVAL,
                "tier_3_min_vertical_fit": TIER_3_MIN_VERTICAL_FIT,
            },
            "survival_score_weights": WEIGHTS,
            "smb_pricing_ceiling": SMB_PRICING_CEILING,
            "trust_decay_interval_hours": TRUST_DECAY_INTERVAL_HOURS,
            "llm_extraction_auto_commit": LLM_EXTRACTION_AUTO_COMMIT,
            "badge_tiers": BADGE_TIERS,
            "success_targets": {
                "trust_decay_precision": TARGET_TRUST_DECAY_PRECISION,
                "ingestion_latency_hours": TARGET_INGESTION_LATENCY_HOURS,
                "saydo_variance": TARGET_SAYDO_VARIANCE,
                "hitl_throughput_per_hour": TARGET_HITL_THROUGHPUT_PER_HOUR,
            },
        }