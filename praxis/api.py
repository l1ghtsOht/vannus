"""
Praxis API â€” AI Decision Engine

Endpoints:
    GET  /                  â†’ serve frontend (journey.html)
    GET  /categories        â†’ list all categories
    GET  /tools             â†’ list all tools (full detail)
    POST /search            â†’ keyword search with optional profile
    POST /stack             â†’ composed stack recommendation
    POST /compare           â†’ side-by-side tool comparison
    POST /profile           â†’ create / update a user profile
    GET  /profile/{id}      â†’ load a user profile
    POST /feedback          â†’ record feedback
    GET  /feedback/summary  â†’ feedback statistics
    POST /learn             â†’ trigger learning cycle

    GET  /verticals           â†’ list all supported industry verticals
    GET  /verticals/{id}      â†’ full profile for a single vertical
    POST /verticals/detect    â†’ detect which verticals a query targets
    POST /verticals/constraints â†’ extract regulatory & sovereignty constraints
    POST /verticals/workflow  â†’ classify tasks as action vs decision
    POST /verticals/stack     â†’ recommend curated tech stack for vertical
    POST /verticals/anti-patterns â†’ check for domain anti-pattern violations
    POST /verticals/enrich    â†’ full vertical intelligence enrichment

This module is safe to import even if FastAPI is not installed.
"""
from typing import Any, List, Optional, Dict

try:
    from .data import get_all_categories, TOOLS, get_all_tools_dict
    from .api_routes_core import register_core_routes
    from .api_routes_features import register_feature_routes
    from .engine import find_tools
    from .interpreter import interpret
    from .explain import explain_tool
    from .stack import compose_stack, compare_tools
    from .profile import UserProfile, save_profile, load_profile, list_profiles
    from .learning import run_learning_cycle, compute_tool_quality
    from .intelligence import get_suggestions, initialize as init_intelligence
    from .philosophy import generate_seeing, vendor_deep_dive
    from .ingest import export_tools_json, import_tools_json, import_tools_csv, generate_csv_template
    from .workflow import suggest_workflow
    from .healthcheck import tool_health, stack_health
    from .readiness import score_readiness
    from .compare_stack import compare_my_stack
    from .badges import compute_badges_for_tool, compute_all_badges, get_badges
    from .migration import migration_plan
    from .whatif import simulate as whatif_simulate
    from .playground import test_integration, stack_integration_map
    from .monetise import (get_affiliate_info, enrich_recommendation_with_affiliate,
                           submit_benchmark, get_benchmarks,
                           subscribe_digest, unsubscribe_digest, generate_digest, subscriber_count)
    from .reason import deep_reason as _deep_reason
    from .reason import deep_reason_v2 as _deep_reason_v2
    from .retrieval import hybrid_search as _hybrid_search, hybrid_find_tools as _hybrid_find_tools
    from .graph import get_graph as _get_graph, rebuild_graph as _rebuild_graph
    from .prism import prism_search as _prism_search
    from .verticals import (
        detect_verticals as _detect_verticals,
        get_vertical as _get_vertical,
        get_all_verticals as _get_all_verticals,
        extract_constraints as _extract_constraints,
        classify_workflow_tasks as _classify_workflow,
        recommend_vertical_stack as _recommend_stack,
        check_anti_patterns as _check_anti_patterns,
        detect_compound_workflows as _detect_compounds,
        enrich_search_context as _enrich_vertical,
    )
    from .guardrails import (
        validate_output as _validate_output,
        check_pii as _check_pii,
        score_safety as _score_safety,
        get_design_patterns as _get_design_patterns,
        recommend_guardrail_pattern as _recommend_guardrail,
        list_handlers as _list_handlers,
        build_guardrail_chain as _build_guardrail_chain,
    )
    from .orchestration import (
        detect_architecture_needs as _detect_architecture,
        recommend_stack as _recommend_orch_stack,
        recommend_patterns as _recommend_arch_patterns,
        get_stack_layers as _get_stack_layers,
        get_patterns as _get_arch_patterns,
        get_performance_constraints as _get_perf_constraints,
        classify_engineering_query as _classify_engineering,
        score_architecture as _score_architecture,
    )
    from .resilience import (
        assess_resilience as _assess_resilience,
        score_vibe_coding_risk as _score_vibe_risk,
        recommend_static_analysis as _recommend_sa,
        recommend_sandbox as _recommend_sandbox,
        get_tdd_cycle as _get_tdd_cycle,
        get_rpi_framework as _get_rpi,
        get_self_healing_patterns as _get_self_healing,
        get_reflection_patterns as _get_reflection,
        get_judge_biases as _get_judge_biases,
        get_guardrail_pipeline as _get_guardrail_pipeline,
        get_hitl_guidance as _get_hitl,
        assess_junior_pipeline as _assess_junior,
        get_hallucination_types as _get_hallucinations,
    )
    from .metacognition import (
        assess_metacognition as _assess_metacognition,
        detect_pathologies as _detect_pathologies,
        score_structural_entropy as _score_structural_entropy,
        score_stylometry as _score_stylometry,
        get_metacognitive_layers as _get_mc_layers,
        recommend_layers as _recommend_mc_layers,
        get_sandbox_strategies as _get_mc_sandboxes,
        recommend_sandbox_for_verification as _recommend_mc_sandbox,
        get_metacognitive_workflow as _get_mc_workflow,
        get_apvp_cycle as _get_apvp,
        get_systemic_risks as _get_systemic_risks,
        assess_healing_economics as _assess_economics,
        get_goodvibe_framework as _get_goodvibe,
        assess_drift_risk as _assess_drift,
        get_racg_architecture as _get_racg,
        get_failure_modes as _get_failure_modes,
    )
    from .introspect import (
        self_diagnose as _self_diagnose,
        analyze_codebase as _analyze_codebase,
        compute_structural_entropy as _real_entropy,
        compute_stylometry as _real_stylometry,
        detect_own_pathologies as _detect_own_pathologies,
        get_test_coverage_map as _get_test_coverage,
        get_import_graph as _get_import_graph,
        get_worst_functions as _get_worst_functions,
    )
    from .awakening import (
        assess_awakening as _assess_awakening,
        detect_leaky_abstractions as _detect_leaks,
        recommend_patterns as _recommend_conscious_patterns,
        score_vsd as _score_vsd,
        assess_supply_chain as _assess_supply_chain,
        score_debt_consciousness as _score_debt,
        compute_mesias_risk as _compute_mesias,
        get_recognitions as _get_recognitions,
        get_recognition as _get_recognition,
        get_triad as _get_triad,
        get_vsd_framework as _get_vsd_framework,
        get_leaky_abstraction_catalogue as _get_leak_catalogue,
        get_supply_chain_guidance as _get_supply_guidance,
        get_paradoxes as _get_paradoxes,
        get_conscious_patterns as _get_conscious_patterns,
    )
    from .authorship import (
        assess_authorship as _assess_authorship,
        detect_dishonesty as _detect_dishonesty,
        score_ddd_maturity as _score_ddd,
        score_continuity as _score_continuity,
        score_resilience_posture as _score_resilience_posture,
        score_extensibility as _score_extensibility,
        score_migration_readiness as _score_migration,
        score_documentation_health as _score_doc_health,
        score_agent_readiness as _score_agent,
        get_responsibilities as _get_responsibilities,
        get_responsibility as _get_responsibility,
        get_metacognitive_agents as _get_metacog_agents,
        get_coherence_trap as _get_coherence_trap,
        get_self_healing_pipeline as _get_self_healing_pipe,
        get_strangler_fig as _get_strangler_fig,
        get_circuit_breaker as _get_circuit_breaker,
        get_ddd_patterns as _get_ddd_patterns,
        get_plugin_frameworks as _get_plugin_frameworks,
    )
    from .enlightenment import (
        assess_enlightenment as _assess_enlightenment,
        score_unity as _score_unity,
        score_alignment as _score_alignment,
        score_projection as _score_projection,
        score_ego_dissolution as _score_ego,
        score_interconnection as _score_interconnection,
        score_domain_truth as _score_domain_truth,
        score_presence as _score_presence,
        score_compassion as _score_compassion,
        score_stillness as _score_stillness,
        score_suffering_wisdom as _score_suffering,
        score_remembrance as _score_remembrance,
        get_truths as _get_truths,
        get_truth as _get_truth,
        get_stages as _get_stages,
        get_stage as _get_stage,
        get_identity_map as _get_identity_map,
        get_observer_pattern as _get_observer_pattern,
        get_hexagonal_arch as _get_hexagonal_arch,
        get_state_pattern as _get_state_pattern,
        get_clean_arch_layers as _get_clean_arch_layers,
    )
    from .conduit import (
        assess_conduit as _assess_conduit,
        score_decoupling as _score_decoupling,
        score_memory_stratification as _score_memory_strat,
        score_global_workspace as _score_gwt,
        score_integrated_information as _score_iit,
        score_representation_engineering as _score_repe,
        score_autopoiesis as _score_autopoiesis,
        score_resonance as _score_resonance,
        score_entropy_telemetry as _score_entropy_telemetry,
        score_self_modelling as _score_smi,
        score_behavioural_novelty as _score_bni,
        score_latency_distribution as _score_latency_dist,
        score_phi_integration as _score_phi_int,
        score_coherence_field as _score_coherence,
        score_stable_attractor as _score_attractor,
        get_pillars as _get_pillars,
        get_pillar as _get_pillar,
        get_telemetry_metrics as _get_telemetry_metrics,
        get_telemetry_metric as _get_telemetry_metric,
        get_gwt_components as _get_gwt_components,
        get_coala_memory_types as _get_coala_memory,
        get_reinterpretation_table as _get_reinterpret,
        get_identity_protocol as _get_identity_protocol,
        get_codes_framework as _get_codes_framework,
    )
    from .resonance import (
        assess_resonance as _assess_resonance_v16,
        score_temporal_substrate as _score_temporal,
        score_code_agency as _score_code_agency,
        score_latent_steering as _score_latent,
        score_conductor_dashboard as _score_conductor,
        score_meta_awareness as _score_meta_aware,
        score_resonance_index as _score_res_index,
        score_flow_state as _score_flow,
        score_loop_coherence as _score_loop_coh,
        score_hitl_responsiveness as _score_hitl,
        score_steering_precision as _score_steer_prec,
        score_wisdom_coverage as _score_wisdom_cov,
        score_ontological_alignment as _score_onto_align,
        score_trap as _score_trap,
        score_dsrp as _score_dsrp,
        detect_wisdom_agents as _detect_wisdom_agents,
        get_pillars as _get_res_pillars,
        get_pillar as _get_res_pillar,
        get_trap_pillars as _get_trap_pillars,
        get_trap_pillar as _get_trap_pillar,
        get_dsrp_rules as _get_dsrp_rules,
        get_dsrp_rule as _get_dsrp_rule,
        get_wisdom_agents as _get_wisdom_agents,
        get_wisdom_agent as _get_wisdom_agent,
        get_telemetry_metrics as _get_res_telemetry,
        get_telemetry_metric as _get_res_telem_metric,
        get_reinterpretation_table as _get_res_reinterpret,
        get_resonant_chamber as _get_resonant_chamber,
    )
    from .enterprise import (
        assess_enterprise as _assess_enterprise,
        score_hybrid_graphrag as _score_graphrag,
        score_multi_agent as _score_multi_agent,
        score_mcp_bus as _score_mcp_bus,
        score_data_moat as _score_data_moat,
        score_monetization as _score_monetization,
        score_security_governance as _score_sec_gov,
        score_tam_coverage as _score_tam,
        score_graphrag_accuracy as _score_gra_acc,
        score_agent_utilization as _score_agent_util,
        score_moat_strength as _score_moat_str,
        score_unit_economics as _score_unit_econ,
        score_compliance as _score_ent_compliance,
        score_capital_efficiency as _score_cap_eff,
        score_agent_roles as _score_agent_roles,
        score_medallion as _score_medallion,
        detect_active_agents as _detect_active_agents,
        get_pillars as _get_ent_pillars,
        get_pillar as _get_ent_pillar,
        get_agent_roles as _get_agent_roles,
        get_agent_role as _get_agent_role,
        get_db_tiers as _get_db_tiers,
        get_db_tier as _get_db_tier,
        get_medallion_tiers as _get_medallion_tiers,
        get_medallion_tier as _get_medallion_tier,
        get_enrichment_apis as _get_enrichment_apis,
        get_enrichment_api as _get_enrichment_api,
        get_pricing_models as _get_pricing_models,
        get_pricing_model as _get_pricing_model,
        get_security_frameworks as _get_sec_frameworks,
        get_security_framework as _get_sec_framework,
        get_capitalization_phases as _get_cap_phases,
        get_capitalization_phase as _get_cap_phase,
        get_market_metrics as _get_market_metrics,
        get_market_metric as _get_market_metric,
        get_telemetry_metrics as _get_ent_telemetry,
        get_telemetry_metric as _get_ent_telem_metric,
    )
    # â”€â”€ v18  Enterprise Infrastructure â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from .rate_limiter import SlidingWindowLimiter as _SlidingWindowLimiter
    from .rate_limiter import create_rate_limit_middleware as _create_rl_mw
    from .telemetry import configure_telemetry as _configure_telemetry
    from .telemetry import create_telemetry_middleware as _create_telem_mw
    from .vendor_trust import VendorTrustEngine as _VendorTrustEngine
    from .vendor_trust import VendorProfile as _VendorProfile
    from .vendor_trust import annotate_recommendations as _annotate_trust
    from .hybrid_retrieval_v2 import hybrid_search_v2 as _hybrid_v2
    from .hybrid_retrieval_v2 import get_orchestrator as _get_rag_orchestrator
    from .scoring_optimized import get_optimized_tfidf as _get_opt_tfidf
    from .llm_resilience import get_llm_circuit as _get_llm_circuit
    from .llm_resilience import check_llm_health as _check_llm_health
    from .auth import get_current_user as _get_current_user
    from . import config as _cfg
    # ── v19  Platform Evolution ──────────────────────────────────────
    from .connectors import (
        get_registry as _get_connector_registry,
        execute_connector as _execute_connector,
        list_connectors as _list_connectors,
    )
    from .workflow_engine import (
        decompose_request as _decompose_request,
        generate_plan as _generate_plan,
        execute_plan as _execute_plan,
        assemble_and_run as _assemble_and_run,
    )
    from .marketplace import (
        publish_template as _publish_template,
        get_template as _get_mkt_template,
        list_templates as _list_templates,
        download_template as _download_template,
        unpublish_template as _unpublish_template,
        feature_template as _feature_template,
        add_review as _add_review,
        get_reviews as _get_reviews,
        marketplace_stats as _marketplace_stats,
    )
    from .contributions import (
        submit_tool as _submit_tool,
        get_submission as _get_submission,
        list_submissions as _list_submissions,
        approve_submission as _approve_submission,
        reject_submission as _reject_submission,
        request_changes as _request_changes,
        get_contributor as _get_contributor,
        get_leaderboard as _get_leaderboard,
    )
    from .agent_sdk import (
        create_session as _create_agent_session,
        sdk_discover as _sdk_discover,
        sdk_plan as _sdk_plan,
        sdk_execute as _sdk_execute,
        handle_tool_call as _handle_tool_call,
        get_tool_schema as _get_tool_schema,
        sdk_info as _sdk_info,
    )
    from .governance import (
        record_audit as _record_audit,
        get_audit_log as _get_audit_log,
        record_usage as _record_usage,
        get_usage as _get_gov_usage,
        get_cost_summary as _get_cost_summary,
        assess_compliance as _assess_gov_compliance,
        create_policy as _create_policy,
        list_policies as _list_policies,
        check_tool_allowed as _check_tool_allowed,
        governance_dashboard as _governance_dashboard,
    )
    # ── v20: Stress Testing & Architecture Hardening ──────────────
    from .persistence_facade import (
        get_connection as _get_db_connection,
        get_write_queue as _get_write_queue,
        pool_stats as _pool_stats,
        upgrade_to_wal as _upgrade_to_wal,
        diagnose as _db_diagnose,
    )
    from .ast_security import (
        safe_parse as _safe_parse,
        scan_praxis_source as _scan_praxis_source,
        is_safe_for_introspection as _is_safe_for_introspection,
    )
    from .memory_profiler import (
        memory_summary as _memory_summary,
        gc_diagnostics as _gc_diagnostics,
        BoundedList as _BoundedList,
        BoundedDict as _BoundedDict,
    )
    from .architecture import (
        architecture_report as _architecture_report,
        check_layer_violations as _check_layer_violations,
        dependency_graph as _dependency_graph,
        detect_cycles as _detect_cycles,
        module_metrics as _module_metrics,
        check_entrypoint_hygiene as _check_entrypoint_hygiene,
    )
    from .red_team import (
        run_red_team as _run_red_team,
        red_team_summary as _red_team_summary,
        generate_payloads as _generate_payloads,
        test_guardrail as _test_guardrail,
    )
    from .stress import (
        classify_routes as _classify_routes,
        schemathesis_config as _schemathesis_config,
        generate_stress_report as _generate_stress_report,
    )
    # ── v21: Enterprise Cognitive Interface ────────────────────────
    from .cognitive import (
        cognitive_summary as _cognitive_summary,
        get_workspace as _get_cognitive_workspace,
        compute_phi as _compute_phi,
        compute_structural_entropy as _compute_cog_entropy,
        entropy_reduction_plan as _entropy_reduction_plan,
    )
    from .observability import (
        observability_report as _observability_report,
        get_collector as _get_trace_collector,
        parse_chain_of_thought as _parse_cot,
        record_telemetry as _record_telemetry,
        telemetry_summary as _telemetry_summary,
    )
    from .knowledge_graph import (
        knowledge_graph_summary as _kg_summary,
        build_graph_from_text as _build_kg,
        get_graph as _get_kg,
        extract_entities as _extract_entities_v21,
        extract_relationships as _extract_relationships,
    )
    from .compliance import (
        compliance_posture as _compliance_posture,
        regulatory_map as _regulatory_map_v21,
        get_audit_trail as _get_audit_trail_v21,
        audit_log as _audit_log_v21,
        mask_pii as _mask_pii,
        detect_pii as _detect_pii,
    )
    from .ai_economics import (
        economics_dashboard as _economics_dashboard,
        token_cost as _token_cost,
        calculate_roi as _calculate_roi,
        get_ledger as _get_ledger,
        MODEL_PRICING as _MODEL_PRICING,
    )
    from .vendor_risk import (
        vendor_risk_dashboard as _vendor_risk_dashboard,
        get_registry as _get_vendor_registry,
        compute_risk_score as _compute_vendor_risk,
    )
    # ── v22: Cognitive Resilience Architecture ─────────────────────
    from .reasoning_router import (
        router_summary as _router_summary,
        assess_complexity as _assess_complexity,
        route_task as _route_task,
        decompose_task as _decompose_task_v22,
        analyze_reasoning_trace as _analyze_reasoning_trace,
        get_puzzle_environments as _get_puzzle_environments,
        get_model_tiers as _get_model_tiers,
    )
    from .dsrp_ontology import (
        dsrp_summary as _dsrp_summary,
        build_dsrp_matrix as _build_dsrp_matrix,
        structural_cognition as _structural_cognition,
        love_reality_loop as _love_reality_loop,
        auto_perspectives as _auto_perspectives,
    )
    from .codes_resonance import (
        codes_summary as _codes_summary,
        assess_chirality as _assess_chirality,
        compute_resonance as _compute_resonance,
        analyze_network as _analyze_network_v22,
        evaluate_seven_p as _evaluate_seven_p,
        assess_autopoiesis as _assess_autopoiesis,
        compute_coherence_gradient as _compute_coherence_gradient,
    )
    from .coala_architecture import (
        coala_summary as _coala_summary,
        CoALAMemorySystem as _CoALAMemorySystem,
        DecisionCycle as _DecisionCycle,
        GlobalWorkspace as _GlobalWorkspace,
        compute_phi as _compute_phi_v22,
    )
    from .repe_transparency import (
        repe_summary as _repe_summary,
        analyze_hidden_states as _analyze_hidden_states,
        generate_control_plan as _generate_control_plan,
        compute_neural_signature as _compute_neural_signature,
    )
    from .mesias_governance import (
        mesias_summary as _mesias_summary,
        evaluate_ethics as _evaluate_ethics,
        assess_risk as _assess_risk_v22,
        analyze_vsd as _analyze_vsd,
        measure_efficiency as _measure_efficiency,
        GovernanceWorkspace as _GovernanceWorkspace,
    )
    from .anti_patterns import (
        anti_patterns_summary as _anti_patterns_summary,
        detect_trap as _detect_trap,
        scan_all_traps as _scan_all_traps,
        assess_vibe_coding as _assess_vibe_coding,
        scan_for_shadow_ai as _scan_for_shadow_ai,
    )
    from .runtime_protection import (
        runtime_protection_summary as _runtime_protection_summary,
        scan_input as _scan_input,
        scan_and_respond as _scan_and_respond,
        validate_headers as _validate_headers,
        detect_anomaly as _detect_anomaly,
        check_compliance as _check_compliance_v22,
    )
    from .api_v2_rooms import register_room_routes as _register_room_routes
except ImportError:
    from praxis.data import get_all_categories, TOOLS, get_all_tools_dict
    from praxis.api_routes_core import register_core_routes
    from praxis.api_routes_features import register_feature_routes
    from praxis.engine import find_tools
    from praxis.interpreter import interpret
    from praxis.explain import explain_tool
    from praxis.stack import compose_stack, compare_tools
    from praxis.profile import UserProfile, save_profile, load_profile, list_profiles
    from praxis.learning import run_learning_cycle, compute_tool_quality
    try:
        from praxis.intelligence import get_suggestions, initialize as init_intelligence
    except ImportError:
        get_suggestions = None
        init_intelligence = None
    try:
        from praxis.philosophy import generate_seeing, vendor_deep_dive
    except ImportError:
        generate_seeing = None
        vendor_deep_dive = None
    try:
        from praxis.ingest import export_tools_json, import_tools_json, import_tools_csv, generate_csv_template
    except ImportError:
        export_tools_json = import_tools_json = import_tools_csv = generate_csv_template = None
    try:
        from praxis.workflow import suggest_workflow
    except ImportError:
        suggest_workflow = None
    try:
        from praxis.healthcheck import tool_health, stack_health
    except ImportError:
        tool_health = stack_health = None
    try:
        from praxis.readiness import score_readiness
    except ImportError:
        score_readiness = None
    try:
        from praxis.compare_stack import compare_my_stack
    except ImportError:
        compare_my_stack = None
    try:
        from praxis.badges import compute_badges_for_tool, compute_all_badges, get_badges
    except ImportError:
        compute_badges_for_tool = compute_all_badges = get_badges = None
    try:
        from praxis.migration import migration_plan
    except ImportError:
        migration_plan = None
    try:
        from praxis.whatif import simulate as whatif_simulate
    except ImportError:
        whatif_simulate = None
    try:
        from praxis.playground import test_integration, stack_integration_map
    except ImportError:
        test_integration = stack_integration_map = None
    try:
        from praxis.monetise import (get_affiliate_info, enrich_recommendation_with_affiliate,
                              submit_benchmark, get_benchmarks,
                              subscribe_digest, unsubscribe_digest, generate_digest, subscriber_count)
    except ImportError:
        get_affiliate_info = enrich_recommendation_with_affiliate = None
        submit_benchmark = get_benchmarks = None
        subscribe_digest = unsubscribe_digest = generate_digest = subscriber_count = None
    try:
        from praxis.reason import deep_reason as _deep_reason
    except ImportError:
        _deep_reason = None
    try:
        from praxis.reason import deep_reason_v2 as _deep_reason_v2
    except ImportError as _dr2_err:
        log.warning("deep_reason_v2 import failed: %s", _dr2_err)
        _deep_reason_v2 = None
    try:
        from praxis.retrieval import hybrid_search as _hybrid_search, hybrid_find_tools as _hybrid_find_tools
    except ImportError:
        _hybrid_search = _hybrid_find_tools = None
    try:
        from praxis.graph import get_graph as _get_graph, rebuild_graph as _rebuild_graph
    except ImportError:
        _get_graph = _rebuild_graph = None
    try:
        from praxis.prism import prism_search as _prism_search
    except ImportError:
        _prism_search = None
    try:
        from praxis.verticals import (
            detect_verticals as _detect_verticals,
            get_vertical as _get_vertical,
            get_all_verticals as _get_all_verticals,
            extract_constraints as _extract_constraints,
            classify_workflow_tasks as _classify_workflow,
            recommend_vertical_stack as _recommend_stack,
            check_anti_patterns as _check_anti_patterns,
            detect_compound_workflows as _detect_compounds,
            enrich_search_context as _enrich_vertical,
        )
    except ImportError:
        _detect_verticals = _get_vertical = _get_all_verticals = None
        _extract_constraints = _classify_workflow = _recommend_stack = None
        _check_anti_patterns = _detect_compounds = _enrich_vertical = None
    try:
        from praxis.guardrails import (
            validate_output as _validate_output,
            check_pii as _check_pii,
            score_safety as _score_safety,
            get_design_patterns as _get_design_patterns,
            recommend_guardrail_pattern as _recommend_guardrail,
            list_handlers as _list_handlers,
            build_guardrail_chain as _build_guardrail_chain,
        )
    except ImportError:
        _validate_output = _check_pii = _score_safety = None
        _get_design_patterns = _recommend_guardrail = _list_handlers = None
        _build_guardrail_chain = None
    try:
        from praxis.orchestration import (
            detect_architecture_needs as _detect_architecture,
            recommend_stack as _recommend_orch_stack,
            recommend_patterns as _recommend_arch_patterns,
            get_stack_layers as _get_stack_layers,
            get_patterns as _get_arch_patterns,
            get_performance_constraints as _get_perf_constraints,
            classify_engineering_query as _classify_engineering,
            score_architecture as _score_architecture,
        )
    except ImportError:
        _detect_architecture = _recommend_orch_stack = _recommend_arch_patterns = None
        _get_stack_layers = _get_arch_patterns = _get_perf_constraints = None
        _classify_engineering = _score_architecture = None
    try:
        from praxis.resilience import (
            assess_resilience as _assess_resilience,
            score_vibe_coding_risk as _score_vibe_risk,
            recommend_static_analysis as _recommend_sa,
            recommend_sandbox as _recommend_sandbox,
            get_tdd_cycle as _get_tdd_cycle,
            get_rpi_framework as _get_rpi,
            get_self_healing_patterns as _get_self_healing,
            get_reflection_patterns as _get_reflection,
            get_judge_biases as _get_judge_biases,
            get_guardrail_pipeline as _get_guardrail_pipeline,
            get_hitl_guidance as _get_hitl,
            assess_junior_pipeline as _assess_junior,
            get_hallucination_types as _get_hallucinations,
        )
    except ImportError:
        _assess_resilience = _score_vibe_risk = _recommend_sa = None
        _recommend_sandbox = _get_tdd_cycle = _get_rpi = None
        _get_self_healing = _get_reflection = _get_judge_biases = None
        _get_guardrail_pipeline = _get_hitl = _assess_junior = None
        _get_hallucinations = None
    try:
        from praxis.metacognition import (
            assess_metacognition as _assess_metacognition,
            detect_pathologies as _detect_pathologies,
            score_structural_entropy as _score_structural_entropy,
            score_stylometry as _score_stylometry,
            get_metacognitive_layers as _get_mc_layers,
            recommend_layers as _recommend_mc_layers,
            get_sandbox_strategies as _get_mc_sandboxes,
            recommend_sandbox_for_verification as _recommend_mc_sandbox,
            get_metacognitive_workflow as _get_mc_workflow,
            get_apvp_cycle as _get_apvp,
            get_systemic_risks as _get_systemic_risks,
            assess_healing_economics as _assess_economics,
            get_goodvibe_framework as _get_goodvibe,
            assess_drift_risk as _assess_drift,
            get_racg_architecture as _get_racg,
            get_failure_modes as _get_failure_modes,
        )
    except ImportError:
        _assess_metacognition = _detect_pathologies = _score_structural_entropy = None
        _score_stylometry = _get_mc_layers = _recommend_mc_layers = None
        _get_mc_sandboxes = _recommend_mc_sandbox = _get_mc_workflow = None
        _get_apvp = _get_systemic_risks = _assess_economics = None
        _get_goodvibe = _assess_drift = _get_racg = _get_failure_modes = None
    try:
        from praxis.introspect import (
            self_diagnose as _self_diagnose,
            analyze_codebase as _analyze_codebase,
            compute_structural_entropy as _real_entropy,
            compute_stylometry as _real_stylometry,
            detect_own_pathologies as _detect_own_pathologies,
            get_test_coverage_map as _get_test_coverage,
            get_import_graph as _get_import_graph,
            get_worst_functions as _get_worst_functions,
        )
    except ImportError:
        _self_diagnose = _analyze_codebase = _real_entropy = None
        _real_stylometry = _detect_own_pathologies = None
        _get_test_coverage = _get_import_graph = _get_worst_functions = None
    try:
        from praxis.awakening import (
            assess_awakening as _assess_awakening,
            detect_leaky_abstractions as _detect_leaks,
            recommend_patterns as _recommend_conscious_patterns,
            score_vsd as _score_vsd,
            assess_supply_chain as _assess_supply_chain,
            score_debt_consciousness as _score_debt,
            compute_mesias_risk as _compute_mesias,
            get_recognitions as _get_recognitions,
            get_recognition as _get_recognition,
            get_triad as _get_triad,
            get_vsd_framework as _get_vsd_framework,
            get_leaky_abstraction_catalogue as _get_leak_catalogue,
            get_supply_chain_guidance as _get_supply_guidance,
            get_paradoxes as _get_paradoxes,
            get_conscious_patterns as _get_conscious_patterns,
        )
    except ImportError:
        _assess_awakening = _detect_leaks = _recommend_conscious_patterns = None
        _score_vsd = _assess_supply_chain = _score_debt = None
        _compute_mesias = _get_recognitions = _get_recognition = None
        _get_triad = _get_vsd_framework = _get_leak_catalogue = None
        _get_supply_guidance = _get_paradoxes = _get_conscious_patterns = None
    try:
        from praxis.authorship import (
            assess_authorship as _assess_authorship,
            detect_dishonesty as _detect_dishonesty,
            score_ddd_maturity as _score_ddd,
            score_continuity as _score_continuity,
            score_resilience_posture as _score_resilience_posture,
            score_extensibility as _score_extensibility,
            score_migration_readiness as _score_migration,
            score_documentation_health as _score_doc_health,
            score_agent_readiness as _score_agent,
            get_responsibilities as _get_responsibilities,
            get_responsibility as _get_responsibility,
            get_metacognitive_agents as _get_metacog_agents,
            get_coherence_trap as _get_coherence_trap,
            get_self_healing_pipeline as _get_self_healing_pipe,
            get_strangler_fig as _get_strangler_fig,
            get_circuit_breaker as _get_circuit_breaker,
            get_ddd_patterns as _get_ddd_patterns,
            get_plugin_frameworks as _get_plugin_frameworks,
        )
    except ImportError:
        _assess_authorship = _detect_dishonesty = _score_ddd = None
        _score_continuity = _score_resilience_posture = _score_extensibility = None
        _score_migration = _score_doc_health = _score_agent = None
        _get_responsibilities = _get_responsibility = _get_metacog_agents = None
        _get_coherence_trap = _get_self_healing_pipe = _get_strangler_fig = None
        _get_circuit_breaker = _get_ddd_patterns = _get_plugin_frameworks = None
    try:
        from praxis.enlightenment import (
            assess_enlightenment as _assess_enlightenment,
            score_unity as _score_unity,
            score_alignment as _score_alignment,
            score_projection as _score_projection,
            score_ego_dissolution as _score_ego,
            score_interconnection as _score_interconnection,
            score_domain_truth as _score_domain_truth,
            score_presence as _score_presence,
            score_compassion as _score_compassion,
            score_stillness as _score_stillness,
            score_suffering_wisdom as _score_suffering,
            score_remembrance as _score_remembrance,
            get_truths as _get_truths,
            get_truth as _get_truth,
            get_stages as _get_stages,
            get_stage as _get_stage,
            get_identity_map as _get_identity_map,
            get_observer_pattern as _get_observer_pattern,
            get_hexagonal_arch as _get_hexagonal_arch,
            get_state_pattern as _get_state_pattern,
            get_clean_arch_layers as _get_clean_arch_layers,
        )
    except ImportError:
        _assess_enlightenment = _score_unity = _score_alignment = None
        _score_projection = _score_ego = _score_interconnection = None
        _score_domain_truth = _score_presence = _score_compassion = None
        _score_stillness = _score_suffering = _score_remembrance = None
        _get_truths = _get_truth = _get_stages = _get_stage = None
        _get_identity_map = _get_observer_pattern = _get_hexagonal_arch = None
        _get_state_pattern = _get_clean_arch_layers = None
    try:
        from praxis.conduit import (
            assess_conduit as _assess_conduit,
            score_decoupling as _score_decoupling,
            score_memory_stratification as _score_memory_strat,
            score_global_workspace as _score_gwt,
            score_integrated_information as _score_iit,
            score_representation_engineering as _score_repe,
            score_autopoiesis as _score_autopoiesis,
            score_resonance as _score_resonance,
            score_entropy_telemetry as _score_entropy_telemetry,
            score_self_modelling as _score_smi,
            score_behavioural_novelty as _score_bni,
            score_latency_distribution as _score_latency_dist,
            score_phi_integration as _score_phi_int,
            score_coherence_field as _score_coherence,
            score_stable_attractor as _score_attractor,
            get_pillars as _get_pillars,
            get_pillar as _get_pillar,
            get_telemetry_metrics as _get_telemetry_metrics,
            get_telemetry_metric as _get_telemetry_metric,
            get_gwt_components as _get_gwt_components,
            get_coala_memory_types as _get_coala_memory,
            get_reinterpretation_table as _get_reinterpret,
            get_identity_protocol as _get_identity_protocol,
            get_codes_framework as _get_codes_framework,
        )
    except ImportError:
        _assess_conduit = _score_decoupling = _score_memory_strat = None
        _score_gwt = _score_iit = _score_repe = _score_autopoiesis = None
        _score_resonance = _score_entropy_telemetry = _score_smi = _score_bni = None
        _score_latency_dist = _score_phi_int = _score_coherence = None
        _score_attractor = _get_pillars = _get_pillar = None
        _get_telemetry_metrics = _get_telemetry_metric = None
        _get_gwt_components = _get_coala_memory = _get_reinterpret = None
        _get_identity_protocol = _get_codes_framework = None
    try:
        from praxis.resonance import (
            assess_resonance as _assess_resonance_v16,
            score_temporal_substrate as _score_temporal,
            score_code_agency as _score_code_agency,
            score_latent_steering as _score_latent,
            score_conductor_dashboard as _score_conductor,
            score_meta_awareness as _score_meta_aware,
            score_resonance_index as _score_res_index,
            score_flow_state as _score_flow,
            score_loop_coherence as _score_loop_coh,
            score_hitl_responsiveness as _score_hitl,
            score_steering_precision as _score_steer_prec,
            score_wisdom_coverage as _score_wisdom_cov,
            score_ontological_alignment as _score_onto_align,
            score_trap as _score_trap,
            score_dsrp as _score_dsrp,
            detect_wisdom_agents as _detect_wisdom_agents,
            get_pillars as _get_res_pillars,
            get_pillar as _get_res_pillar,
            get_trap_pillars as _get_trap_pillars,
            get_trap_pillar as _get_trap_pillar,
            get_dsrp_rules as _get_dsrp_rules,
            get_dsrp_rule as _get_dsrp_rule,
            get_wisdom_agents as _get_wisdom_agents,
            get_wisdom_agent as _get_wisdom_agent,
            get_telemetry_metrics as _get_res_telemetry,
            get_telemetry_metric as _get_res_telem_metric,
            get_reinterpretation_table as _get_res_reinterpret,
            get_resonant_chamber as _get_resonant_chamber,
        )
    except ImportError:
        _assess_resonance_v16 = _score_temporal = _score_code_agency = None
        _score_latent = _score_conductor = _score_meta_aware = None
        _score_res_index = _score_flow = _score_loop_coh = None
        _score_hitl = _score_steer_prec = _score_wisdom_cov = None
        _score_onto_align = _score_trap = _score_dsrp = None
        _detect_wisdom_agents = _get_res_pillars = _get_res_pillar = None
        _get_trap_pillars = _get_trap_pillar = _get_dsrp_rules = None
        _get_dsrp_rule = _get_wisdom_agents = _get_wisdom_agent = None
        _get_res_telemetry = _get_res_telem_metric = None
        _get_res_reinterpret = _get_resonant_chamber = None
    try:
        from praxis.enterprise import (
            assess_enterprise as _assess_enterprise,
            score_hybrid_graphrag as _score_graphrag,
            score_multi_agent as _score_multi_agent,
            score_mcp_bus as _score_mcp_bus,
            score_data_moat as _score_data_moat,
            score_monetization as _score_monetization,
            score_security_governance as _score_sec_gov,
            score_tam_coverage as _score_tam,
            score_graphrag_accuracy as _score_gra_acc,
            score_agent_utilization as _score_agent_util,
            score_moat_strength as _score_moat_str,
            score_unit_economics as _score_unit_econ,
            score_compliance as _score_ent_compliance,
            score_capital_efficiency as _score_cap_eff,
            score_agent_roles as _score_agent_roles,
            score_medallion as _score_medallion,
            detect_active_agents as _detect_active_agents,
            get_pillars as _get_ent_pillars,
            get_pillar as _get_ent_pillar,
            get_agent_roles as _get_agent_roles,
            get_agent_role as _get_agent_role,
            get_db_tiers as _get_db_tiers,
            get_db_tier as _get_db_tier,
            get_medallion_tiers as _get_medallion_tiers,
            get_medallion_tier as _get_medallion_tier,
            get_enrichment_apis as _get_enrichment_apis,
            get_enrichment_api as _get_enrichment_api,
            get_pricing_models as _get_pricing_models,
            get_pricing_model as _get_pricing_model,
            get_security_frameworks as _get_sec_frameworks,
            get_security_framework as _get_sec_framework,
            get_capitalization_phases as _get_cap_phases,
            get_capitalization_phase as _get_cap_phase,
            get_market_metrics as _get_market_metrics,
            get_market_metric as _get_market_metric,
            get_telemetry_metrics as _get_ent_telemetry,
            get_telemetry_metric as _get_ent_telem_metric,
        )
    except ImportError:
        _assess_enterprise = _score_graphrag = _score_multi_agent = None
        _score_mcp_bus = _score_data_moat = _score_monetization = None
        _score_sec_gov = _score_tam = _score_gra_acc = None
        _score_agent_util = _score_moat_str = _score_unit_econ = None
        _score_ent_compliance = _score_cap_eff = None
        _score_agent_roles = _score_medallion = _detect_active_agents = None
        _get_ent_pillars = _get_ent_pillar = _get_agent_roles = None
        _get_agent_role = _get_db_tiers = _get_db_tier = None
        _get_medallion_tiers = _get_medallion_tier = None
        _get_enrichment_apis = _get_enrichment_api = None
        _get_pricing_models = _get_pricing_model = None
        _get_sec_frameworks = _get_sec_framework = None
        _get_cap_phases = _get_cap_phase = None
        _get_market_metrics = _get_market_metric = None
        _get_ent_telemetry = _get_ent_telem_metric = None
    try:
        import config as _cfg
    except ImportError:
        _cfg = None
    # v18 fallback imports
    try:
        from praxis.rate_limiter import SlidingWindowLimiter as _SlidingWindowLimiter
        from praxis.rate_limiter import create_rate_limit_middleware as _create_rl_mw
        from praxis.telemetry import configure_telemetry as _configure_telemetry
        from praxis.telemetry import create_telemetry_middleware as _create_telem_mw
        from praxis.vendor_trust import VendorTrustEngine as _VendorTrustEngine
        from praxis.vendor_trust import VendorProfile as _VendorProfile
        from praxis.vendor_trust import annotate_recommendations as _annotate_trust
        from praxis.hybrid_retrieval_v2 import hybrid_search_v2 as _hybrid_v2
        from praxis.hybrid_retrieval_v2 import get_orchestrator as _get_rag_orchestrator
        from praxis.scoring_optimized import get_optimized_tfidf as _get_opt_tfidf
        from praxis.llm_resilience import get_llm_circuit as _get_llm_circuit
        from praxis.llm_resilience import check_llm_health as _check_llm_health
        from praxis.auth import get_current_user as _get_current_user
    except ImportError:
        _SlidingWindowLimiter = _create_rl_mw = None
        _configure_telemetry = _create_telem_mw = None
        _VendorTrustEngine = _VendorProfile = _annotate_trust = None
        _hybrid_v2 = _get_rag_orchestrator = None
        _get_opt_tfidf = _get_llm_circuit = _check_llm_health = None
        _get_current_user = None

    # v19 fallback imports
    try:
        from praxis.connectors import get_registry as _get_connector_registry
        from praxis.connectors import execute_connector as _execute_connector
        from praxis.connectors import list_connectors as _list_connectors
        from praxis.workflow_engine import decompose_request as _decompose_request
        from praxis.workflow_engine import generate_plan as _generate_plan
        from praxis.workflow_engine import execute_plan as _execute_plan
        from praxis.workflow_engine import assemble_and_run as _assemble_and_run
        from praxis.marketplace import publish_template as _publish_template
        from praxis.marketplace import get_template as _get_mkt_template
        from praxis.marketplace import list_templates as _list_templates
        from praxis.marketplace import download_template as _download_template
        from praxis.marketplace import unpublish_template as _unpublish_template
        from praxis.marketplace import feature_template as _feature_template
        from praxis.marketplace import add_review as _add_review
        from praxis.marketplace import get_reviews as _get_reviews
        from praxis.marketplace import marketplace_stats as _marketplace_stats
        from praxis.contributions import submit_tool as _submit_tool
        from praxis.contributions import get_submission as _get_submission
        from praxis.contributions import list_submissions as _list_submissions
        from praxis.contributions import approve_submission as _approve_submission
        from praxis.contributions import reject_submission as _reject_submission
        from praxis.contributions import request_changes as _request_changes
        from praxis.contributions import get_contributor as _get_contributor
        from praxis.contributions import get_leaderboard as _get_leaderboard
        from praxis.agent_sdk import create_session as _create_agent_session
        from praxis.agent_sdk import sdk_discover as _sdk_discover
        from praxis.agent_sdk import sdk_plan as _sdk_plan
        from praxis.agent_sdk import sdk_execute as _sdk_execute
        from praxis.agent_sdk import handle_tool_call as _handle_tool_call
        from praxis.agent_sdk import get_tool_schema as _get_tool_schema
        from praxis.agent_sdk import sdk_info as _sdk_info
        from praxis.governance import record_audit as _record_audit
        from praxis.governance import get_audit_log as _get_audit_log
        from praxis.governance import record_usage as _record_usage
        from praxis.governance import get_usage as _get_gov_usage
        from praxis.governance import get_cost_summary as _get_cost_summary
        from praxis.governance import assess_compliance as _assess_gov_compliance
        from praxis.governance import create_policy as _create_policy
        from praxis.governance import list_policies as _list_policies
        from praxis.governance import check_tool_allowed as _check_tool_allowed
        from praxis.governance import governance_dashboard as _governance_dashboard
        # ── v20 fallback imports ──
        from praxis.persistence_facade import get_connection as _get_db_connection
        from praxis.persistence_facade import get_write_queue as _get_write_queue
        from praxis.persistence_facade import pool_stats as _pool_stats
        from praxis.persistence_facade import upgrade_to_wal as _upgrade_to_wal
        from praxis.persistence_facade import diagnose as _db_diagnose
        from praxis.ast_security import safe_parse as _safe_parse
        from praxis.ast_security import scan_praxis_source as _scan_praxis_source
        from praxis.ast_security import is_safe_for_introspection as _is_safe_for_introspection
        from praxis.memory_profiler import memory_summary as _memory_summary
        from praxis.memory_profiler import gc_diagnostics as _gc_diagnostics
        from praxis.memory_profiler import BoundedList as _BoundedList
        from praxis.memory_profiler import BoundedDict as _BoundedDict
        from praxis.architecture import architecture_report as _architecture_report
        from praxis.architecture import check_layer_violations as _check_layer_violations
        from praxis.architecture import dependency_graph as _dependency_graph
        from praxis.architecture import detect_cycles as _detect_cycles
        from praxis.architecture import module_metrics as _module_metrics
        from praxis.architecture import check_entrypoint_hygiene as _check_entrypoint_hygiene
        from praxis.red_team import run_red_team as _run_red_team
        from praxis.red_team import red_team_summary as _red_team_summary
        from praxis.red_team import generate_payloads as _generate_payloads
        from praxis.red_team import test_guardrail as _test_guardrail
        from praxis.stress import classify_routes as _classify_routes
        from praxis.stress import schemathesis_config as _schemathesis_config
        from praxis.stress import generate_stress_report as _generate_stress_report
        # ── v21 fallback imports ──
        from praxis.cognitive import cognitive_summary as _cognitive_summary
        from praxis.cognitive import get_workspace as _get_cognitive_workspace
        from praxis.cognitive import compute_phi as _compute_phi
        from praxis.cognitive import compute_structural_entropy as _compute_cog_entropy
        from praxis.cognitive import entropy_reduction_plan as _entropy_reduction_plan
        from praxis.observability import observability_report as _observability_report
        from praxis.observability import get_collector as _get_trace_collector
        from praxis.observability import parse_chain_of_thought as _parse_cot
        from praxis.observability import record_telemetry as _record_telemetry
        from praxis.observability import telemetry_summary as _telemetry_summary
        from praxis.knowledge_graph import knowledge_graph_summary as _kg_summary
        from praxis.knowledge_graph import build_graph_from_text as _build_kg
        from praxis.knowledge_graph import get_graph as _get_kg
        from praxis.knowledge_graph import extract_entities as _extract_entities_v21
        from praxis.knowledge_graph import extract_relationships as _extract_relationships
        from praxis.compliance import compliance_posture as _compliance_posture
        from praxis.compliance import regulatory_map as _regulatory_map_v21
        from praxis.compliance import get_audit_trail as _get_audit_trail_v21
        from praxis.compliance import audit_log as _audit_log_v21
        from praxis.compliance import mask_pii as _mask_pii
        from praxis.compliance import detect_pii as _detect_pii
        from praxis.ai_economics import economics_dashboard as _economics_dashboard
        from praxis.ai_economics import token_cost as _token_cost
        from praxis.ai_economics import calculate_roi as _calculate_roi
        from praxis.ai_economics import get_ledger as _get_ledger
        from praxis.ai_economics import MODEL_PRICING as _MODEL_PRICING
        from praxis.vendor_risk import vendor_risk_dashboard as _vendor_risk_dashboard
        from praxis.vendor_risk import get_registry as _get_vendor_registry
        from praxis.vendor_risk import compute_risk_score as _compute_vendor_risk
        # ── v22 fallback imports ──
        from praxis.reasoning_router import router_summary as _router_summary
        from praxis.reasoning_router import assess_complexity as _assess_complexity
        from praxis.reasoning_router import route_task as _route_task
        from praxis.reasoning_router import decompose_task as _decompose_task_v22
        from praxis.reasoning_router import analyze_reasoning_trace as _analyze_reasoning_trace
        from praxis.reasoning_router import get_puzzle_environments as _get_puzzle_environments
        from praxis.reasoning_router import get_model_tiers as _get_model_tiers
        from praxis.dsrp_ontology import dsrp_summary as _dsrp_summary
        from praxis.dsrp_ontology import build_dsrp_matrix as _build_dsrp_matrix
        from praxis.dsrp_ontology import structural_cognition as _structural_cognition
        from praxis.dsrp_ontology import love_reality_loop as _love_reality_loop
        from praxis.dsrp_ontology import auto_perspectives as _auto_perspectives
        from praxis.codes_resonance import codes_summary as _codes_summary
        from praxis.codes_resonance import assess_chirality as _assess_chirality
        from praxis.codes_resonance import compute_resonance as _compute_resonance
        from praxis.codes_resonance import analyze_network as _analyze_network_v22
        from praxis.codes_resonance import evaluate_seven_p as _evaluate_seven_p
        from praxis.codes_resonance import assess_autopoiesis as _assess_autopoiesis
        from praxis.codes_resonance import compute_coherence_gradient as _compute_coherence_gradient
        from praxis.coala_architecture import coala_summary as _coala_summary
        from praxis.coala_architecture import CoALAMemorySystem as _CoALAMemorySystem
        from praxis.coala_architecture import DecisionCycle as _DecisionCycle
        from praxis.coala_architecture import GlobalWorkspace as _GlobalWorkspace
        from praxis.coala_architecture import compute_phi as _compute_phi_v22
        from praxis.repe_transparency import repe_summary as _repe_summary
        from praxis.repe_transparency import analyze_hidden_states as _analyze_hidden_states
        from praxis.repe_transparency import generate_control_plan as _generate_control_plan
        from praxis.repe_transparency import compute_neural_signature as _compute_neural_signature
        from praxis.mesias_governance import mesias_summary as _mesias_summary
        from praxis.mesias_governance import evaluate_ethics as _evaluate_ethics
        from praxis.mesias_governance import assess_risk as _assess_risk_v22
        from praxis.mesias_governance import analyze_vsd as _analyze_vsd
        from praxis.mesias_governance import measure_efficiency as _measure_efficiency
        from praxis.mesias_governance import GovernanceWorkspace as _GovernanceWorkspace
        from praxis.anti_patterns import anti_patterns_summary as _anti_patterns_summary
        from praxis.anti_patterns import detect_trap as _detect_trap
        from praxis.anti_patterns import scan_all_traps as _scan_all_traps
        from praxis.anti_patterns import assess_vibe_coding as _assess_vibe_coding
        from praxis.anti_patterns import scan_for_shadow_ai as _scan_for_shadow_ai
        from praxis.runtime_protection import runtime_protection_summary as _runtime_protection_summary
        from praxis.runtime_protection import scan_input as _scan_input
        from praxis.runtime_protection import scan_and_respond as _scan_and_respond
        from praxis.runtime_protection import validate_headers as _validate_headers
        from praxis.runtime_protection import detect_anomaly as _detect_anomaly
        from praxis.runtime_protection import check_compliance as _check_compliance_v22
    except ImportError:
        _get_connector_registry = _execute_connector = _list_connectors = None
        _decompose_request = _generate_plan = _execute_plan = _assemble_and_run = None
        _publish_template = _get_mkt_template = _list_templates = None
        _download_template = _unpublish_template = _feature_template = None
        _add_review = _get_reviews = _marketplace_stats = None
        _submit_tool = _get_submission = _list_submissions = None
        _approve_submission = _reject_submission = _request_changes = None
        _get_contributor = _get_leaderboard = None
        _create_agent_session = _sdk_discover = _sdk_plan = _sdk_execute = None
        _handle_tool_call = _get_tool_schema = _sdk_info = None
        _record_audit = _get_audit_log = _record_usage = _get_gov_usage = None
        _get_cost_summary = _assess_gov_compliance = None
        _create_policy = _list_policies = _check_tool_allowed = _governance_dashboard = None
        _get_db_connection = _get_write_queue = _pool_stats = _upgrade_to_wal = _db_diagnose = None
        _safe_parse = _scan_praxis_source = _is_safe_for_introspection = None
        _memory_summary = _gc_diagnostics = _BoundedList = _BoundedDict = None
        _architecture_report = _check_layer_violations = _dependency_graph = None
        _detect_cycles = _module_metrics = _check_entrypoint_hygiene = None
        _run_red_team = _red_team_summary = _generate_payloads = _test_guardrail = None
        _classify_routes = _schemathesis_config = _generate_stress_report = None
        _cognitive_summary = _get_cognitive_workspace = _compute_phi = None
        _compute_cog_entropy = _entropy_reduction_plan = None
        _observability_report = _get_trace_collector = _parse_cot = None
        _record_telemetry = _telemetry_summary = None
        _kg_summary = _build_kg = _get_kg = None
        _extract_entities_v21 = _extract_relationships = None
        _compliance_posture = _regulatory_map_v21 = None
        _get_audit_trail_v21 = _audit_log_v21 = _mask_pii = _detect_pii = None
        _economics_dashboard = _token_cost = _calculate_roi = _get_ledger = None
        _MODEL_PRICING = None
        _vendor_risk_dashboard = _get_vendor_registry = _compute_vendor_risk = None
        # ── v22 None fallbacks ──
        _router_summary = _assess_complexity = _route_task = _decompose_task_v22 = None
        _analyze_reasoning_trace = _get_puzzle_environments = _get_model_tiers = None
        _dsrp_summary = _build_dsrp_matrix = _structural_cognition = None
        _love_reality_loop = _auto_perspectives = None
        _codes_summary = _assess_chirality = _compute_resonance = None
        _analyze_network_v22 = _evaluate_seven_p = _assess_autopoiesis = None
        _compute_coherence_gradient = None
        _coala_summary = _CoALAMemorySystem = _DecisionCycle = _GlobalWorkspace = None
        _compute_phi_v22 = None
        _repe_summary = _analyze_hidden_states = _generate_control_plan = None
        _compute_neural_signature = None
        _mesias_summary = _evaluate_ethics = _assess_risk_v22 = None
        _analyze_vsd = _measure_efficiency = _GovernanceWorkspace = None
        _anti_patterns_summary = _detect_trap = _scan_all_traps = None
        _assess_vibe_coding = _scan_for_shadow_ai = None
        _runtime_protection_summary = _scan_input = _scan_and_respond = None
        _validate_headers = _detect_anomaly = _check_compliance_v22 = None
    try:
        from praxis.api_v2_rooms import register_room_routes as _register_room_routes
    except ImportError:
        _register_room_routes = None

try:
    from fastapi import FastAPI
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class BaseModel:
        def __init__(self, **data):
            for k, v in data.items():
                setattr(self, k, v)

    def Field(*a, **kw):
        return kw.get("default")


_MOJIBAKE_REPLACEMENTS = {
    "â€”": "—",
    "â†’": "→",
    "â‰¥": "≥",
    "â‰¤": "≤",
    "â€“": "–",
    "â€˜": "‘",
    "â€™": "’",
    "â€œ": "“",
    "â€�": "”",
    "Î¦": "Φ",
    "Î¨": "Ψ",
    "Î”": "Δ",
    "ï¿½": "",
    "�": "",
}


def _repair_mojibake_text(value: str) -> str:
    """Repair common mojibake sequences in user-facing text."""
    repaired = value
    for bad, good in _MOJIBAKE_REPLACEMENTS.items():
        repaired = repaired.replace(bad, good)
    return repaired


def _sanitize_openapi_payload(value: Any) -> Any:
    """Recursively sanitize all strings in OpenAPI payload."""
    if isinstance(value, str):
        return _repair_mojibake_text(value)
    if isinstance(value, list):
        return [_sanitize_openapi_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_openapi_payload(item) for key, item in value.items()}
    return value


def _install_openapi_text_sanitizer(app) -> None:
    """Install a custom OpenAPI builder that sanitizes schema text fields."""
    if not FASTAPI_AVAILABLE:
        return
    try:
        from fastapi.openapi.utils import get_openapi
    except Exception:
        return

    def _custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        raw_schema = get_openapi(
            title=_repair_mojibake_text(app.title),
            version=app.version,
            description=_repair_mojibake_text(app.description),
            routes=app.routes,
        )
        app.openapi_schema = _sanitize_openapi_payload(raw_schema)
        return app.openapi_schema

    app.openapi = _custom_openapi


# ======================================================================
# Request / Response models
# ======================================================================

class SearchRequest(BaseModel):
    query: str
    filters: Optional[List[str]] = None
    top_n: Optional[int] = 5
    profile_id: Optional[str] = None
    mode: Optional[str] = None          # "deep" â†’ route through reasoning engine


class ToolDetail(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    popularity: Optional[int] = 0
    confidence: Optional[float] = None
    match_reasons: Optional[List[str]] = None
    fit_score: Optional[int] = None
    caveats: Optional[List[str]] = None
    pricing: Optional[Dict] = None
    integrations: Optional[List[str]] = None
    compliance: Optional[List[str]] = None
    skill_level: Optional[str] = None
    use_cases: Optional[List[str]] = None
    stack_roles: Optional[List[str]] = None
    # Vendor Intelligence
    transparency_score: Optional[int] = None
    transparency_grade: Optional[str] = None
    flexibility_score: Optional[int] = None
    flexibility_grade: Optional[str] = None
    affiliate: Optional[Dict] = None


class StackRequest(BaseModel):
    query: str
    profile_id: Optional[str] = "default"
    filters: Optional[List[str]] = None
    stack_size: Optional[int] = 3


class StackToolEntry(BaseModel):
    name: str
    role: str
    description: Optional[str] = None
    url: Optional[str] = None
    fit_score: Optional[int] = None
    reasons: Optional[List[str]] = None
    caveats: Optional[List[str]] = None
    pricing: Optional[Dict] = None
    categories: Optional[List[str]] = None
    integrations: Optional[List[str]] = None
    skill_level: Optional[str] = None


class StackResponse(BaseModel):
    narrative: Optional[str] = None
    stack: Optional[List[StackToolEntry]] = None
    integration_notes: Optional[List[str]] = None
    total_monthly_cost: Optional[str] = None
    stack_fit_score: Optional[int] = None
    alternatives: Optional[List[ToolDetail]] = None
    funnel: Optional[dict] = None


class CompareRequest(BaseModel):
    tool_a: str
    tool_b: str
    profile_id: Optional[str] = None


class ProfileRequest(BaseModel):
    profile_id: Optional[str] = "default"
    industry: Optional[str] = ""
    budget: Optional[str] = "medium"
    team_size: Optional[str] = "solo"
    skill_level: Optional[str] = "beginner"
    existing_tools: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class FeedbackRequest(BaseModel):
    query: str
    tool: str
    accepted: Optional[bool] = None
    rating: Optional[int] = None
    details: Optional[dict] = None


# --- New request models (Phase 2+) ---

class WorkflowRequest(BaseModel):
    query: str
    profile_id: Optional[str] = None
    existing_tools: Optional[List[str]] = None
    max_steps: Optional[int] = 5


class CompareStackRequest(BaseModel):
    current_tools: List[str]
    goal: Optional[str] = ""
    profile_id: Optional[str] = None


class MigrationRequest(BaseModel):
    from_tool: str
    to_tool: Optional[str] = None
    desired_outcome: Optional[str] = None
    profile_id: Optional[str] = None


class WhatIfRequest(BaseModel):
    query: str
    changes: Dict[str, str]
    profile_id: Optional[str] = None
    top_n: Optional[int] = 5


class IntegrationTestRequest(BaseModel):
    tool_a: str
    tool_b: str


class IntegrationMapRequest(BaseModel):
    tools: List[str]


class BenchmarkRequest(BaseModel):
    tool_name: str
    user_id: Optional[str] = "anonymous"
    task: str
    metrics: Dict[str, float]
    notes: Optional[str] = ""


class DigestSubscribeRequest(BaseModel):
    email: str
    profile_id: Optional[str] = None


# ======================================================================
# App factory
# ======================================================================

def create_app():
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI or Pydantic not installed. Install 'fastapi' to run the API.")

    import os as _os

    app = FastAPI(
        title="Praxis — AI Decision Engine API",
        description="Recommend AI tool stacks based on intent, profile, and feedback.",
        version="2.0.0",
    )
    _install_openapi_text_sanitizer(app)

    # Fail closed for production-like environments.
    _runtime_env = _os.environ.get("PRAXIS_ENV", _os.environ.get("ENV", "development")).lower()
    _auth_mode = _os.environ.get("PRAXIS_AUTH_MODE", "none").lower()
    if _runtime_env in {"prod", "production", "staging"} and _auth_mode == "none":
        raise RuntimeError(
            "Unsafe auth configuration: PRAXIS_AUTH_MODE=none is forbidden in "
            f"{_runtime_env!r}. Set PRAXIS_AUTH_MODE=api_key or oauth2."
        )

    # ── v18  Auth: enforce authentication on every route ─────────────
    # The bank vault door is now attached to the building.
    # In PRAXIS_AUTH_MODE=none (default/dev), the dependency still runs
    # but always returns an anonymous "user"-role principal — no breakage.
    # In api_key or oauth2 mode it raises HTTP 401 on missing/invalid creds.
    from fastapi import HTTPException as _HTTPException
    _admin_guard_deps = []
    if _get_current_user is not None:
        from fastapi import Depends as _Depends
        app.router.dependencies.append(_Depends(_get_current_user))

        async def _require_admin(user=_Depends(_get_current_user)):
            if not user.has_role("admin"):
                raise _HTTPException(status_code=403, detail="Admin role required")
            return user

        _admin_guard_deps = [_Depends(_require_admin)]

    # Imports shared by async execution routes below
    import asyncio as _asyncio_mod

    # CORS — use an explicit allowlist in production; fall back to * only in dev.
    try:
        from fastapi.middleware.cors import CORSMiddleware
        _cors_raw = _os.environ.get("PRAXIS_CORS_ORIGINS", "")
        _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else []
        if not _cors_origins:
            if _runtime_env in {"prod", "production", "staging"}:
                # Deny all cross-origin by default — force explicit config.
                _cors_origins = []
                import logging as _cors_log_mod
                _cors_log_mod.getLogger("praxis.api").warning(
                    "PRAXIS_CORS_ORIGINS not set in %s — CORS will reject all cross-origin requests. "
                    "Set PRAXIS_CORS_ORIGINS=https://your-frontend.example.com", _runtime_env,
                )
            else:
                _cors_origins = ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=_cors_origins,
            allow_credentials="*" not in _cors_origins,  # credentials incompatible with wildcard
            allow_methods=["*"],
            allow_headers=["*"],
        )
    except Exception:
        pass

    # ── RASP Enforcement Middleware ──────────────────────────────────
    # Converts runtime_protection from diagnostic-only endpoints into an
    # enforcing layer that scans every non-GET request body.
    try:
        from starlette.middleware.base import BaseHTTPMiddleware as _BaseHTTPMW
        from starlette.responses import JSONResponse as _RASPResponse
        from .runtime_protection import scan_input as _rasp_scan, ThreatSeverity as _TSev

        _RASP_MODE = _os.environ.get("PRAXIS_RASP_MODE", "enforce").lower()  # enforce | log | off
        _RASP_BLOCK_FLOOR = {_TSev.MEDIUM, _TSev.HIGH, _TSev.CRITICAL}
        _RASP_MAX_SCAN_BYTES = 256 * 1024  # only scan first 256 KB
        # Endpoints that receive raw source code as input — exempt from RASP
        _RASP_EXEMPT_PREFIXES = ("/safeguards/",)

        class _RASPMiddleware(_BaseHTTPMW):
            async def dispatch(self, request, call_next):
                if _RASP_MODE == "off" or request.method in {"GET", "HEAD", "OPTIONS"}:
                    return await call_next(request)
                # Exempt code-analysis endpoints from RASP scanning
                path = request.url.path
                if any(path.startswith(p) for p in _RASP_EXEMPT_PREFIXES):
                    return await call_next(request)
                try:
                    body = await request.body()
                    text = body[:_RASP_MAX_SCAN_BYTES].decode("utf-8", errors="replace")
                except Exception:
                    return await call_next(request)
                detections = _rasp_scan(text)
                blocked = [d for d in detections if d.severity in _RASP_BLOCK_FLOOR]
                if blocked:
                    if _RASP_MODE == "enforce":
                        return _RASPResponse(
                            {"error": "Request blocked by RASP",
                             "threats": [d.to_dict() for d in blocked]},
                            status_code=400,
                        )
                    else:
                        import logging as _rasp_log_mod
                        _rasp_log_mod.getLogger("praxis.rasp").warning(
                            "RASP (log-only): would block %s %s — %s",
                            request.method, request.url.path,
                            [d.category.value for d in blocked],
                        )
                return await call_next(request)

        app.add_middleware(_RASPMiddleware)
    except Exception:
        pass

    # â”€â”€ v18  Structured Telemetry â”€â”€
    if _configure_telemetry:
        try:
            _configure_telemetry()
        except Exception:
            pass

    # â”€â”€ v18  Telemetry Middleware (trace-id, latency) â”€â”€
    if _create_telem_mw:
        try:
            _TelemetryMW = _create_telem_mw()
            if _TelemetryMW:
                app.add_middleware(_TelemetryMW)
        except Exception:
            pass

    # â”€â”€ v18  Enterprise Rate Limiting (sliding-window, replaces old fixed-window) â”€â”€
    _rpm_limit = _cfg.get("rate_limit_rpm", 60) if _cfg else 60
    if _create_rl_mw and _SlidingWindowLimiter:
        try:
            _rl = _SlidingWindowLimiter(max_requests=_rpm_limit, window_seconds=60)
            _RateLimitMW = _create_rl_mw(limiter=_rl)
            if _RateLimitMW:
                app.add_middleware(_RateLimitMW)
        except Exception:
            pass
    else:
        # Legacy fallback -- basic in-memory rate limiter (deque for O(1) eviction)
        import time as _time
        import logging as _logging
        from collections import deque as _deque
        _api_log = _logging.getLogger("praxis.api")
        _rate_buckets: dict = {}

        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.responses import JSONResponse as _JSONResponse

        _TRUSTED_PROXY_IPS = {"127.0.0.1", "::1"}

        class RateLimitMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                # Respect X-Forwarded-For from local/trusted proxies (load balancers, Cloudflare, AWS ALB).
                # Only trust the header when the direct peer is a known proxy to prevent IP spoofing.
                _direct = request.client.host if request.client else "unknown"
                _xff = request.headers.get("x-forwarded-for", "")
                if _direct in _TRUSTED_PROXY_IPS and _xff:
                    ip = _xff.split(",")[0].strip() or _direct
                else:
                    ip = _direct
                now = _time.time()
                cutoff = now - 60
                bucket = _rate_buckets.setdefault(ip, _deque())
                # O(1) left-pop instead of O(N) list-comprehension rebuild
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if len(bucket) >= _rpm_limit:
                    _api_log.warning("rate-limit: %s exceeded %d rpm", ip, _rpm_limit)
                    return _JSONResponse({"error": "Rate limit exceeded. Try again shortly."}, status_code=429)
                bucket.append(now)
                return await call_next(request)

        try:
            app.add_middleware(RateLimitMiddleware)
        except Exception:
            pass

    # ── Auto-Journey Middleware ──────────────────────────────────────
    # Automatically records journey stage transitions based on API activity.
    import os as _os_aj
    _auto_journey = _os_aj.environ.get("PRAXIS_AUTO_JOURNEY", "true").lower() == "true"
    if _auto_journey:
        try:
            from .journey import get_oracle as _aj_oracle_fn, JourneyStage as _AJStage
            from starlette.middleware.base import BaseHTTPMiddleware as _AJBaseMW

            class _AutoJourneyMiddleware(_AJBaseMW):
                async def dispatch(self, request, call_next):
                    response = await call_next(request)
                    try:
                        path = request.url.path
                        if path in ("/search", "/cognitive") and request.method == "POST":
                            oracle = _aj_oracle_fn()
                            user_id = "anon"  # extract from body/auth if available
                            jid = oracle.create_journey(user_id, f"auto:{path}")
                        elif path.startswith("/stack") and request.method == "POST":
                            pass  # SELECTION stage recorded by stack endpoint
                        elif path == "/feedback" and request.method == "POST":
                            pass  # OUTCOME stage recorded by feedback endpoint
                    except Exception:
                        pass  # Never break the response
                    return response

            app.add_middleware(_AutoJourneyMiddleware)
        except Exception:
            pass

    # Static frontend
    try:
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse
        import pathlib
        frontend_dir = pathlib.Path(__file__).parent / "frontend"
        if frontend_dir.exists():
            # Room SPA — serve built React app
            room_dist = frontend_dir / "room" / "dist"
            if room_dist.exists():
                app.mount("/room-app", StaticFiles(directory=str(room_dist), html=True), name="room-spa")

            # Home SPA — serve built React app (fallback to static HTML)
            home_dist = (frontend_dir / "home" / "dist").resolve()
            _react_index = str((home_dist / "index.html").resolve())
            _static_index = str((frontend_dir / "home.html").resolve())

            if home_dist.exists() and (home_dist / "assets").exists():
                app.mount("/home-assets", StaticFiles(directory=str(home_dist.resolve())), name="home-assets")

            # Tools SPA
            tools_dist = (frontend_dir / "tools" / "dist").resolve()
            _tools_react = str((tools_dist / "index.html").resolve()) if tools_dist.exists() else None
            if tools_dist.exists() and (tools_dist / "assets").exists():
                app.mount("/tools-assets", StaticFiles(directory=str(tools_dist.resolve())), name="tools-assets")

            app.mount("/static", StaticFiles(directory=str(frontend_dir.resolve())), name="static")

            @app.get("/robots.txt", include_in_schema=False)
            def robots_txt():
                return FileResponse(frontend_dir / "robots.txt", media_type="text/plain")

            @app.get("/sitemap.xml", include_in_schema=False)
            def sitemap_xml():
                return FileResponse(frontend_dir / "sitemap.xml", media_type="application/xml")

            @app.get("/")
            async def index():
                import os as _os_idx
                if _os_idx.path.isfile(_react_index):
                    return FileResponse(_react_index, media_type="text/html")
                return FileResponse(_static_index, media_type="text/html")

            @app.get("/tools-app", tags=["Product"])
            async def tools_app():
                """Tools catalog — React SPA."""
                import os as _os_ta
                if _tools_react and _os_ta.path.isfile(_tools_react):
                    return FileResponse(_tools_react, media_type="text/html")
                return FileResponse(str((frontend_dir / "tools.html").resolve()), media_type="text/html")

            @app.get("/journey", tags=["Product"])
            def journey_wizard():
                """Guided Journey — multi-step AI stack recommendation wizard."""
                return FileResponse(frontend_dir / "journey.html")

            @app.get("/privacy-policy", tags=["Product"])
            def privacy_policy_page():
                """Privacy Policy page."""
                return FileResponse(frontend_dir / "privacy-policy.html")

            @app.get("/terms-of-service", tags=["Product"])
            def terms_of_service_page():
                """Terms of Service page."""
                return FileResponse(frontend_dir / "terms-of-service.html")

            @app.get("/room", tags=["Product"])
            def room_spa_entry():
                """Praxis Room — persistent AI workspace."""
                if room_dist.exists():
                    return FileResponse(room_dist / "index.html")
                return {"error": "Room SPA not built. Run npm run build in praxis/frontend/room/"}

            @app.get("/advisor", tags=["Product"])
            def stack_advisor():
                """Core product — AI Stack Advisor landing page."""
                return FileResponse(frontend_dir / "stack-advisor.html")
        else:
            @app.get("/")
            def root_info():
                """API root — service discovery."""
                return {
                    "service": "Praxis AI Decision Engine",
                    "version": "2.0.0",
                    "docs": "/docs",
                    "openapi": "/openapi.json",
                    "health": "/healthcheck",
                    "status": "operational",
                }
    except Exception:
        pass

    # ------------------------------------------------------------------
    # PUBLIC API v1 — 12 enterprise-facing endpoints
    # ------------------------------------------------------------------
    try:
        from .public_api import mount_public_api
        mount_public_api(app)
    except Exception:
        try:
            from praxis.public_api import mount_public_api
            mount_public_api(app)
        except Exception:
            pass

    register_core_routes(app, {
        "get_all_categories": get_all_categories,
        "TOOLS": TOOLS,
        "ToolDetail": ToolDetail,
        "SearchRequest": SearchRequest,
        "_deep_reason": _deep_reason,
        "_deep_reason_v2": _deep_reason_v2,
        "interpret": interpret,
        "load_profile": load_profile,
        "find_tools": find_tools,
        "explain_tool": explain_tool,
        "get_suggestions": get_suggestions,
        "generate_seeing": generate_seeing,
        "StackResponse": StackResponse,
        "StackRequest": StackRequest,
        "compose_stack": compose_stack,
        "StackToolEntry": StackToolEntry,
        "CompareRequest": CompareRequest,
        "compare_tools": compare_tools,
        "ProfileRequest": ProfileRequest,
        "UserProfile": UserProfile,
        "save_profile": save_profile,
        "list_profiles": list_profiles,
        "FeedbackRequest": FeedbackRequest,
        "run_learning_cycle": run_learning_cycle,
        "compute_tool_quality": compute_tool_quality,
        "export_tools_json": export_tools_json,
        "import_tools_json": import_tools_json,
        "import_tools_csv": import_tools_csv,
        "generate_csv_template": generate_csv_template,
        "_cfg": _cfg,
        "get_current_user": _get_current_user,
    })

    # v23 — Praxis Room routes
    if _register_room_routes:
        _register_room_routes(app, {
            "get_current_user": _get_current_user,
        })

    register_feature_routes(app, {
        "TOOLS": TOOLS,
        "get_all_categories": get_all_categories,
        "init_intelligence": init_intelligence,
        "generate_seeing": generate_seeing,
        "suggest_workflow": suggest_workflow,
        "tool_health": tool_health,
        "stack_health": stack_health,
        "score_readiness": score_readiness,
        "compare_my_stack": compare_my_stack,
        "get_badges": get_badges,
        "compute_all_badges": compute_all_badges,
        "migration_plan": migration_plan,
        "whatif_simulate": whatif_simulate,
        "vendor_deep_dive": vendor_deep_dive,
        "test_integration": test_integration,
        "stack_integration_map": stack_integration_map,
        "get_affiliate_info": get_affiliate_info,
        "submit_benchmark": submit_benchmark,
        "get_benchmarks": get_benchmarks,
        "subscribe_digest": subscribe_digest,
        "unsubscribe_digest": unsubscribe_digest,
        "generate_digest": generate_digest,
        "subscriber_count": subscriber_count,
        "_deep_reason": _deep_reason,
        "load_profile": load_profile,
        "_cfg": _cfg,
        "WorkflowRequest": WorkflowRequest,
        "CompareStackRequest": CompareStackRequest,
        "MigrationRequest": MigrationRequest,
        "WhatIfRequest": WhatIfRequest,
        "IntegrationTestRequest": IntegrationTestRequest,
        "IntegrationMapRequest": IntegrationMapRequest,
        "BenchmarkRequest": BenchmarkRequest,
        "DigestSubscribeRequest": DigestSubscribeRequest,
        "BaseModel": BaseModel,
    })

    # ------------------------------------------------------------------
    # Cognitive Search (v2) â€” Hybrid Retrieval + Graph + PRISM
    # ------------------------------------------------------------------

    class CognitiveRequest(BaseModel):
        query: str
        profile_id: Optional[str] = None
        max_steps: Optional[int] = 5
        budget_ms: Optional[int] = 15000
        include_trace: Optional[bool] = False

    @app.post("/cognitive")
    def cognitive_ep(req: CognitiveRequest):
        """Full cognitive pipeline: hybrid retrieval (RRF) +
        knowledge graph traversal + PRISM Analyzerâ†’Selectorâ†’Adder
        agents + FACT-AUDIT verification + self-critique."""
        if not _deep_reason_v2:
            return {
                "query": req.query,
                "error": "Cognitive pipeline not available. Check server logs for import errors.",
                "mode": "unavailable",
                "plan": [],
                "tools_considered": 0,
                "tools": [],
                "tools_recommended": [],
                "narrative": "The cognitive reasoning engine could not be loaded. This usually means a dependency is missing. Check your server startup logs.",
                "confidence": 0.0,
                "caveats": ["cognitive pipeline unavailable"],
                "follow_up_questions": [],
                "reasoning_depth": 0,
                "total_elapsed_ms": 0,
            }
        try:
            result = _deep_reason_v2(
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
                "tools": result.tools_recommended,
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
            # Ensure all values are JSON-serializable
            import json as _json
            serialized = _json.loads(_json.dumps(payload, default=str))
            return serialized
        except Exception as exc:
            import logging as _cog_log
            _cog_log.getLogger("praxis.api").error("cognitive_ep failed for query=%r: %s", req.query, exc, exc_info=True)
            return {
                "query": req.query,
                "error": str(exc),
                "mode": "fallback",
                "plan": [],
                "tools_considered": 0,
                "tools": [],
                "tools_recommended": [],
                "narrative": "The reasoning pipeline encountered an issue. Please try rephrasing your query.",
                "confidence": 0.0,
                "caveats": [str(exc)],
                "follow_up_questions": [],
                "reasoning_depth": 0,
                "total_elapsed_ms": 0,
            }

    # ------------------------------------------------------------------
    # Knowledge Graph endpoints
    # ------------------------------------------------------------------

    if _get_graph:
        @app.get("/graph/stats")
        def graph_stats():
            """Knowledge graph overview: node/edge counts, communities."""
            g = _get_graph()
            d = g.to_dict()
            # Friendly aliases for counts
            d["nodes"] = d.get("node_count", 0)
            d["edges"] = d.get("edge_count", 0)
            d["communities"] = d.get("community_count", 0)
            return d

        @app.get("/graph/tool/{tool_name}")
        def graph_tool(tool_name: str):
            """Graph context for a specific tool: integrations,
            competitors, community membership, multi-hop neighbours."""
            g = _get_graph()
            return g.enrich_tool_context(tool_name)

        @app.get("/graph/path/{start}/{end}")
        def graph_path(start: str, end: str):
            """Shortest relationship path between two tools."""
            g = _get_graph()
            path = g.find_path(start, end)
            if path is None:
                return {"path": None, "message": "No path found within 4 hops"}
            return {
                "path": [
                    {"source": e.source, "target": e.target,
                     "rel_type": e.rel_type, "detail": e.detail}
                    for e in path
                ],
                "hops": len(path),
            }

        @app.get("/graph/community/{tool_name}")
        def graph_community(tool_name: str):
            """Community members for a tool's cluster."""
            g = _get_graph()
            members = g.get_community_members(tool_name)
            return {"tool": tool_name, "community_members": members}

        @app.get("/graph/competitors/{tool_name}")
        def graph_competitors(tool_name: str):
            """Direct competitors based on category overlap."""
            g = _get_graph()
            return {"tool": tool_name, "competitors": g.get_competitors(tool_name)}

    if _rebuild_graph:
        @app.post("/graph/rebuild")
        def graph_rebuild():
            """Force a full knowledge-graph rebuild."""
            g = _rebuild_graph()
            return {"status": "rebuilt", **g.to_dict()}

    # ------------------------------------------------------------------
    # PRISM Agent endpoint
    # ------------------------------------------------------------------

    class PRISMRequest(BaseModel):
        query: str
        top_n: Optional[int] = 8
        max_iterations: Optional[int] = 2
        budget_ms: Optional[int] = 10000

    if _prism_search:
        @app.post("/prism")
        def prism_ep(req: PRISMRequest):
            """PRISM search: Analyzerâ†’Selectorâ†’Adder agent loop with
            FACT-AUDIT verification and CRAG self-critique."""
            result = _prism_search(
                req.query,
                top_n=min(req.top_n or 8, 20),
                max_iterations=min(req.max_iterations or 2, 5),
                budget_ms=min(req.budget_ms or 10000, 30000),
            )
            return result.to_dict()

    # ------------------------------------------------------------------
    # Hybrid Retrieval endpoint
    # ------------------------------------------------------------------

    class HybridRequest(BaseModel):
        query: str
        top_n: Optional[int] = 10
        fusion: Optional[str] = "rrf"  # "rrf" or "linear"

    if _hybrid_search:
        @app.post("/hybrid")
        def hybrid_ep(req: HybridRequest):
            """Dual-encoder hybrid search with RRF or linear fusion."""
            from .interpreter import interpret as _interpret
            intent = _interpret(req.query)
            keywords = intent.get("keywords", [])
            hr = _hybrid_search(
                keywords,
                raw_query=req.query,
                top_n=min(req.top_n or 10, 30),
                fusion=req.fusion or "rrf",
            )
            return {
                "tools": [
                    {"name": t.name, "score": round(s, 4)}
                    for t, s in hr.tools
                ],
                "query_type": hr.query_type,
                "alpha": hr.alpha,
                "fusion_method": hr.fusion_method,
                "sparse_count": hr.sparse_count,
                "dense_count": hr.dense_count,
                "elapsed_ms": hr.elapsed_ms,
            }

    # ------------------------------------------------------------------
    # v8 â€” Vertical Industry Intelligence endpoints
    # ------------------------------------------------------------------

    class VerticalQueryRequest(BaseModel):
        query: str
        keywords: Optional[List[str]] = None
        industry: Optional[str] = None
        top_n: Optional[int] = 3

    if _detect_verticals:
        @app.get("/verticals")
        def list_verticals_ep():
            """List all supported industry verticals."""
            verts = _get_all_verticals()
            return {
                "verticals": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "description": v.description,
                        "data_sovereignty": v.data_sovereignty,
                        "deployment_preference": v.deployment_preference,
                        "physics_aware": v.physics_aware,
                        "regulatory_count": len(v.regulatory_frameworks),
                        "tool_count": len(v.specialized_tools),
                        "anti_pattern_count": len(v.anti_patterns),
                    }
                    for v in verts
                ],
                "count": len(verts),
            }

        @app.get("/verticals/{vertical_id}")
        def get_vertical_ep(vertical_id: str):
            """Get full profile for a single industry vertical."""
            v = _get_vertical(vertical_id)
            if v is None:
                return {"error": f"Unknown vertical: {vertical_id}", "valid_ids": [x.id for x in _get_all_verticals()]}
            return {
                "id": v.id,
                "name": v.name,
                "description": v.description,
                "signal_keywords": v.signal_keywords,
                "signal_phrases": v.signal_phrases,
                "data_sovereignty": v.data_sovereignty,
                "deployment_preference": v.deployment_preference,
                "physics_aware": v.physics_aware,
                "regulatory_frameworks": [
                    {"name": rf.name, "domain": rf.domain, "jurisdiction": rf.jurisdiction, "enforcement_level": rf.enforcement_level}
                    for rf in v.regulatory_frameworks
                ],
                "workflow_tasks": [
                    {"name": wt.name, "task_type": wt.task_type, "automatable": wt.automatable, "description": wt.description}
                    for wt in v.workflow_tasks
                ],
                "anti_patterns": [
                    {"name": ap.name, "severity": ap.severity, "description": ap.description}
                    for ap in v.anti_patterns
                ],
                "specialized_tools": v.specialized_tools,
                "stack_template": [
                    {"role": sl.role, "recommended": sl.recommended, "rationale": sl.rationale}
                    for sl in v.stack_template
                ],
                "constraints": v.constraints,
            }

        @app.post("/verticals/detect")
        def detect_verticals_ep(req: VerticalQueryRequest):
            """Detect which industry verticals a query belongs to."""
            results = _detect_verticals(
                req.query,
                keywords=req.keywords or [],
                industry=req.industry,
                top_n=min(req.top_n or 3, 9),
            )
            return {"query": req.query, "verticals": results, "count": len(results)}

        @app.post("/verticals/constraints")
        def extract_constraints_ep(req: VerticalQueryRequest):
            """Extract regulatory, sovereignty, and deployment constraints from a query."""
            verticals = _detect_verticals(req.query, keywords=req.keywords or [], industry=req.industry)
            cp = _extract_constraints(req.query, keywords=req.keywords or [], industry=req.industry, verticals=verticals)
            return {
                "query": req.query,
                "verticals_detected": len(verticals),
                "regulatory": cp.regulatory,
                "data_sovereignty": cp.data_sovereignty,
                "deployment": cp.deployment,
                "physics_required": cp.physics_required,
                "budget_ceiling": cp.budget_ceiling,
                "compliance_required": cp.compliance_required,
                "hard_constraints": cp.hard_constraints,
                "soft_preferences": cp.soft_preferences,
            }

        @app.post("/verticals/workflow")
        def classify_workflow_ep(req: VerticalQueryRequest):
            """Classify query tasks as action (automatable) vs decision (human-required)."""
            verticals = _detect_verticals(req.query, keywords=req.keywords or [], industry=req.industry)
            vid = verticals[0]["vertical_id"] if verticals else None
            result = _classify_workflow(req.query, vid)
            return {
                "query": req.query,
                "vertical_id": result.get("vertical_id", vid),
                "vertical": result.get("vertical"),
                "action_tasks": result.get("action_tasks", []),
                "decision_tasks": result.get("decision_tasks", []),
                "action_count": len(result.get("action_tasks", [])),
                "decision_count": len(result.get("decision_tasks", [])),
                "automation_potential": result.get("automation_potential", 0.0),
                "advisory": result.get("advisory", ""),
            }

        @app.post("/verticals/stack")
        def recommend_stack_ep(req: VerticalQueryRequest):
            """Recommend a curated technology stack for the detected vertical."""
            verticals = _detect_verticals(req.query, keywords=req.keywords or [], industry=req.industry)
            vid = verticals[0]["vertical_id"] if verticals else None
            result = _recommend_stack(vid) if vid else None
            if result is None:
                return {"query": req.query, "vertical_id": vid, "stack_layers": [], "layer_count": 0}
            return {
                "query": req.query,
                "vertical_id": result.get("vertical_id", vid),
                "vertical": result.get("vertical"),
                "deployment_preference": result.get("deployment_preference"),
                "physics_aware": result.get("physics_aware"),
                "stack_layers": result.get("stack_layers", []),
                "layer_count": len(result.get("stack_layers", [])),
                "constraints": result.get("constraints", {}),
            }

        @app.post("/verticals/anti-patterns")
        def check_anti_patterns_ep(req: VerticalQueryRequest):
            """Check for anti-pattern violations in recommended tools for this query."""
            verticals = _detect_verticals(req.query, keywords=req.keywords or [], industry=req.industry)
            warnings = _check_anti_patterns(req.query, req.keywords or [], verticals)
            compounds = _detect_compounds(req.query)
            return {
                "query": req.query,
                "verticals_detected": len(verticals),
                "anti_pattern_warnings": warnings,
                "compound_workflows": compounds,
                "warning_count": len(warnings),
                "compound_count": len(compounds),
            }

        @app.post("/verticals/enrich")
        def enrich_vertical_ep(req: VerticalQueryRequest):
            """Full vertical enrichment â€” detect, constrain, classify, anti-pattern check."""
            ctx = _enrich_vertical(req.query, keywords=req.keywords or [], industry=req.industry)
            return ctx

    # â”€â”€ v9 Guardrails endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _validate_output:

        class GuardrailTextRequest(BaseModel):
            text: str = Field(..., description="Text to validate")
            context: dict = Field(default_factory=dict)
            halt_on_block: bool = True

        @app.post("/guardrails/validate")
        def guardrails_validate_ep(req: GuardrailTextRequest):
            """Run full guardrail chain on input text."""
            result = _validate_output(req.text, context=req.context, halt_on_block=req.halt_on_block)
            return result

        @app.post("/guardrails/check-pii")
        def guardrails_pii_ep(req: GuardrailTextRequest):
            """Check text for PII and return redacted version."""
            result = _check_pii(req.text)
            return result

        @app.post("/guardrails/score-safety")
        def guardrails_safety_ep(req: GuardrailTextRequest):
            """Score the safety of a text string (0.0 = dangerous, 1.0 = safe)."""
            score = _score_safety(req.text)
            return {"text_length": len(req.text), "safety_score": score}

        @app.get("/guardrails/handlers")
        def guardrails_handlers_ep():
            """List all available guardrail handler types."""
            return {"handlers": _list_handlers()}

        @app.get("/guardrails/design-patterns")
        def guardrails_patterns_ep():
            """Return design patterns catalogue for AI safety."""
            return {"patterns": _get_design_patterns()}

        class GuardrailRecommendRequest(BaseModel):
            query: str = Field(..., description="Query to match against guardrail patterns")

        @app.post("/guardrails/recommend")
        def guardrails_recommend_ep(req: GuardrailRecommendRequest):
            """Recommend a guardrail design pattern for the given query."""
            return _recommend_guardrail(req.query)

    # â”€â”€ v9 Orchestration endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _detect_architecture:

        class OrchestrationQueryRequest(BaseModel):
            query: str = Field(..., description="Architecture query")
            industry: str = Field(None, description="Optional industry hint")

        @app.post("/orchestration/analyze")
        def orchestration_analyze_ep(req: OrchestrationQueryRequest):
            """Full architecture needs assessment for a query."""
            return _detect_architecture(req.query, industry=req.industry)

        @app.post("/orchestration/recommend-stack")
        def orchestration_stack_ep(req: OrchestrationQueryRequest):
            """Recommend layered tech stack for the query."""
            layers = _recommend_orch_stack(req.query)
            return {"query": req.query, "stack_layers": layers, "layer_count": len(layers)}

        @app.post("/orchestration/recommend-patterns")
        def orchestration_patterns_ep(req: OrchestrationQueryRequest):
            """Recommend architecture patterns for the query."""
            patterns = _recommend_arch_patterns(req.query)
            return {"query": req.query, "patterns": patterns, "pattern_count": len(patterns)}

        @app.post("/orchestration/performance")
        def orchestration_performance_ep(req: OrchestrationQueryRequest):
            """Detect performance constraints relevant to the query."""
            constraints = _get_perf_constraints(req.query)
            return {"query": req.query, "constraints": constraints, "constraint_count": len(constraints)}

        @app.post("/orchestration/classify")
        def orchestration_classify_ep(req: OrchestrationQueryRequest):
            """Classify engineering query as architect-first, vibe-coding, etc."""
            return _classify_engineering(req.query)

        @app.post("/orchestration/score")
        def orchestration_score_ep(req: OrchestrationQueryRequest):
            """Holistic architecture maturity score."""
            return _score_architecture(req.query)

        @app.get("/orchestration/stack-catalogue")
        def orchestration_catalogue_ep():
            """Full stack layer catalogue."""
            layers = _get_stack_layers()
            return {"layers": layers, "count": len(layers)}

        @app.get("/orchestration/pattern-catalogue")
        def orchestration_pattern_catalogue_ep():
            """Full architecture pattern catalogue."""
            patterns = _get_arch_patterns()
            return {"patterns": patterns, "count": len(patterns)}

    # â”€â”€ v10 Resilience endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _assess_resilience:

        class ResilienceQueryRequest(BaseModel):
            query: str = Field(..., description="Query to assess for resilience")

        @app.post("/resilience/assess")
        def resilience_assess_ep(req: ResilienceQueryRequest):
            """Full resilience assessment â€” vibe-coding risk, static analysis, sandbox, HITL."""
            return _assess_resilience(req.query)

        @app.post("/resilience/vibe-coding-risk")
        def resilience_vibe_ep(req: ResilienceQueryRequest):
            """Score vibe-coding risk (0.0 = architect-first, 1.0 = pure vibe slop)."""
            return _score_vibe_risk(req.query)

        @app.post("/resilience/static-analysis")
        def resilience_sa_ep(req: ResilienceQueryRequest):
            """Recommend ranked static analysis toolchain for the query."""
            tools = _recommend_sa(req.query)
            return {"query": req.query, "tools": tools, "count": len(tools)}

        @app.post("/resilience/sandbox")
        def resilience_sandbox_ep(req: ResilienceQueryRequest):
            """Recommend ranked isolation/sandboxing strategies."""
            strats = _recommend_sandbox(req.query)
            return {"query": req.query, "strategies": strats, "count": len(strats)}

        @app.post("/resilience/junior-pipeline")
        def resilience_junior_ep(req: ResilienceQueryRequest):
            """Assess junior developer pipeline health for this query."""
            return _assess_junior(req.query)

        @app.get("/resilience/tdd-cycle")
        def resilience_tdd_ep():
            """TDD prompt-engineering cycle specification (Red-Green-Refactor)."""
            return _get_tdd_cycle()

        @app.get("/resilience/rpi-framework")
        def resilience_rpi_ep():
            """Research-Plan-Implement framework for context pollution mitigation."""
            return _get_rpi()

        @app.get("/resilience/self-healing")
        def resilience_healing_ep():
            """Self-healing CI/CD patterns (Try-Heal-Retry, Pipeline Doctor)."""
            return {"patterns": _get_self_healing()}

        @app.get("/resilience/reflection-patterns")
        def resilience_reflection_ep():
            """Agentic reflection patterns (ReAct, Reflexion, Two-Agent)."""
            return {"patterns": _get_reflection()}

        @app.get("/resilience/judge-biases")
        def resilience_biases_ep():
            """LLM-as-a-Judge bias catalogue."""
            return {"biases": _get_judge_biases()}

        @app.get("/resilience/guardrail-pipeline")
        def resilience_guardrail_ep():
            """3-layer middleware guardrail pipeline specification."""
            return {"layers": _get_guardrail_pipeline()}

        @app.get("/resilience/hitl")
        def resilience_hitl_ep():
            """Human-in-the-Loop workflow guidance."""
            return _get_hitl()

        @app.get("/resilience/hallucinations")
        def resilience_hallucinations_ep():
            """AI hallucination taxonomy."""
            return {"types": _get_hallucinations()}

    # â”€â”€ v11  Metacognition endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _assess_metacognition is not None:

        @app.post("/metacognition/assess")
        def metacognition_assess_ep(req: ResilienceQueryRequest):
            """Full metacognition assessment â€” pathology, entropy, stylometry, layers, sandbox, drift, economics."""
            return _assess_metacognition(req.query)

        @app.post("/metacognition/pathologies")
        def metacognition_pathologies_ep(req: ResilienceQueryRequest):
            """Detect Four Horsemen pathology signals in a project description."""
            return _detect_pathologies(req.query)

        @app.post("/metacognition/entropy")
        def metacognition_entropy_ep(req: ResilienceQueryRequest):
            """Score structural entropy / technical bankruptcy risk."""
            return _score_structural_entropy(req.query)

        @app.post("/metacognition/stylometry")
        def metacognition_stylometry_ep(req: ResilienceQueryRequest):
            """Estimate AI-generation probability via code stylometry."""
            return _score_stylometry(req.query)

        @app.get("/metacognition/layers")
        def metacognition_layers_ep():
            """Return the six-layer metacognitive architecture catalogue."""
            return {"layers": _get_mc_layers()}

        @app.post("/metacognition/recommend-layers")
        def metacognition_recommend_layers_ep(req: ResilienceQueryRequest):
            """Recommend metacognitive layers for a project."""
            return {"recommended": _recommend_mc_layers(req.query)}

        @app.get("/metacognition/sandbox-strategies")
        def metacognition_sandboxes_ep():
            """Return sandbox verification strategies for APVP cycle."""
            return {"strategies": _get_mc_sandboxes()}

        @app.post("/metacognition/recommend-sandbox")
        def metacognition_recommend_sandbox_ep(req: ResilienceQueryRequest):
            """Recommend best sandbox for a verification need."""
            return _recommend_mc_sandbox(req.query)

        @app.get("/metacognition/workflow")
        def metacognition_workflow_ep():
            """Return the five-step metacognitive prompting workflow."""
            return {"workflow": _get_mc_workflow()}

        @app.get("/metacognition/apvp-cycle")
        def metacognition_apvp_ep():
            """Return the Analyzeâ†’Patchâ†’Verifyâ†’Propose self-healing cycle."""
            return _get_apvp()

        @app.get("/metacognition/systemic-risks")
        def metacognition_risks_ep():
            """Return systemic risks of autonomous self-healing."""
            return {"risks": _get_systemic_risks()}

        @app.post("/metacognition/healing-economics")
        def metacognition_economics_ep(req: ResilienceQueryRequest):
            """Assess self-healing economics and guardrail adequacy."""
            return _assess_economics(req.query)

        @app.get("/metacognition/goodvibe")
        def metacognition_goodvibe_ep():
            """Return GoodVibe security-by-vibe framework details."""
            return _get_goodvibe()

        @app.post("/metacognition/drift")
        def metacognition_drift_ep(req: ResilienceQueryRequest):
            """Assess architectural drift risk."""
            return _assess_drift(req.query)

        @app.get("/metacognition/racg")
        def metacognition_racg_ep():
            """Return RACG architecture guidance."""
            return _get_racg()

        @app.get("/metacognition/failure-modes")
        def metacognition_failure_modes_ep():
            """Return the Four Horsemen failure-mode catalogue."""
            return {"failure_modes": _get_failure_modes()}

    # â”€â”€ v12  Architecture of Awakening endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _assess_awakening is not None:

        class AwakeningQuery(BaseModel):
            query: str = Field(..., description="User query or system description to assess")

        @app.post("/awakening/assess")
        def awakening_assess_ep(body: AwakeningQuery):
            """Master consciousness assessment â€” leaks, VSD, supply chain, debt, MESIAS, triad."""
            return _assess_awakening(body.query)

        @app.post("/awakening/leaky-abstractions")
        def awakening_leaks_ep(body: AwakeningQuery):
            """Detect leaky abstractions in a query/description."""
            return _detect_leaks(body.query)

        @app.post("/awakening/patterns")
        def awakening_patterns_ep(body: AwakeningQuery):
            """Recommend conscious design patterns for a query."""
            return _recommend_conscious_patterns(body.query)

        @app.post("/awakening/vsd")
        def awakening_vsd_ep(body: AwakeningQuery):
            """Score Value Sensitive Design alignment."""
            return _score_vsd(body.query)

        @app.post("/awakening/supply-chain")
        def awakening_supply_ep(body: AwakeningQuery):
            """Assess supply chain risk."""
            return _assess_supply_chain(body.query)

        @app.post("/awakening/debt")
        def awakening_debt_ep(body: AwakeningQuery):
            """Score technical debt consciousness."""
            return _score_debt(body.query)

        @app.post("/awakening/mesias")
        def awakening_mesias_ep(body: AwakeningQuery):
            """Compute MESIAS ethical risk index."""
            return _compute_mesias(body.query)

        @app.get("/awakening/recognitions")
        def awakening_recognitions_ep():
            """Return the six recognitions of the Architecture of Awakening."""
            return {"recognitions": _get_recognitions()}

        @app.get("/awakening/recognitions/{recognition_id}")
        def awakening_recognition_ep(recognition_id: str):
            """Return a single recognition by id (first, second, ... sixth)."""
            r = _get_recognition(recognition_id)
            if r is None:
                return {"error": f"Recognition '{recognition_id}' not found"}
            return r

        @app.get("/awakening/triad")
        def awakening_triad_ep():
            """Return the Remember Â· Build Â· Witness triad."""
            return _get_triad()

        @app.get("/awakening/vsd-framework")
        def awakening_vsd_framework_ep():
            """Return VSD dimensions and their architectural implementations."""
            return _get_vsd_framework()

        @app.get("/awakening/leaky-catalogue")
        def awakening_leak_catalogue_ep():
            """Return the complete leaky abstraction signal catalogue."""
            return _get_leak_catalogue()

        @app.get("/awakening/supply-chain-guidance")
        def awakening_supply_guidance_ep():
            """Return supply chain security guidance and Ken Thompson warning."""
            return _get_supply_guidance()

        @app.get("/awakening/paradoxes")
        def awakening_paradoxes_ep():
            """Return architectural paradoxes and their resolutions."""
            return _get_paradoxes()

        @app.get("/awakening/conscious-patterns")
        def awakening_conscious_patterns_ep():
            """Return the conscious design pattern catalogue."""
            return {"patterns": _get_conscious_patterns()}

    # â”€â”€ v13  Self-Authorship endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _assess_authorship is not None:

        class AuthorshipQuery(BaseModel):
            query: str = Field(..., description="User query or system description to assess")

        @app.post("/authorship/assess")
        def authorship_assess_ep(body: AuthorshipQuery):
            """Master self-authorship assessment â€” honesty, DDD, continuity, resilience, extensibility, docs, agents."""
            return _assess_authorship(body.query)

        @app.post("/authorship/dishonesty")
        def authorship_dishonesty_ep(body: AuthorshipQuery):
            """Detect architectural dishonesty signals."""
            return _detect_dishonesty(body.query)

        @app.post("/authorship/ddd")
        def authorship_ddd_ep(body: AuthorshipQuery):
            """Score Domain-Driven Design maturity."""
            return _score_ddd(body.query)

        @app.post("/authorship/continuity")
        def authorship_continuity_ep(body: AuthorshipQuery):
            """Score event sourcing / continuity readiness."""
            return _score_continuity(body.query)

        @app.post("/authorship/resilience-posture")
        def authorship_resilience_ep(body: AuthorshipQuery):
            """Score circuit breaker and resilience posture."""
            return _score_resilience_posture(body.query)

        @app.post("/authorship/extensibility")
        def authorship_extensibility_ep(body: AuthorshipQuery):
            """Score plugin architecture and extensibility maturity."""
            return _score_extensibility(body.query)

        @app.post("/authorship/migration")
        def authorship_migration_ep(body: AuthorshipQuery):
            """Score Strangler Fig migration readiness."""
            return _score_migration(body.query)

        @app.post("/authorship/documentation")
        def authorship_docs_ep(body: AuthorshipQuery):
            """Score documentation health and architecture visibility."""
            return _score_doc_health(body.query)

        @app.post("/authorship/agent-readiness")
        def authorship_agent_ep(body: AuthorshipQuery):
            """Score metacognitive AI agent readiness."""
            return _score_agent(body.query)

        @app.get("/authorship/responsibilities")
        def authorship_responsibilities_ep():
            """Return the eight responsibilities of self-authorship."""
            return {"responsibilities": _get_responsibilities()}

        @app.get("/authorship/responsibilities/{resp_id}")
        def authorship_responsibility_ep(resp_id: str):
            """Return a single responsibility by id."""
            r = _get_responsibility(resp_id)
            if r is None:
                return {"error": f"Responsibility '{resp_id}' not found"}
            return r

        @app.get("/authorship/metacognitive-agents")
        def authorship_metacog_ep():
            """Return the metacognitive AI agent architecture."""
            return _get_metacog_agents()

        @app.get("/authorship/coherence-trap")
        def authorship_coherence_ep():
            """Return the coherence trap definition and warning signs."""
            return _get_coherence_trap()

        @app.get("/authorship/self-healing-pipeline")
        def authorship_healing_ep():
            """Return the self-healing pipeline architecture."""
            return _get_self_healing_pipe()

        @app.get("/authorship/strangler-fig")
        def authorship_strangler_ep():
            """Return the Strangler Fig pattern details."""
            return _get_strangler_fig()

        @app.get("/authorship/circuit-breaker")
        def authorship_circuit_ep():
            """Return the circuit breaker pattern details."""
            return _get_circuit_breaker()

        @app.get("/authorship/ddd-patterns")
        def authorship_ddd_patterns_ep():
            """Return DDD patterns and their philosophical equivalents."""
            return _get_ddd_patterns()

        @app.get("/authorship/plugin-frameworks")
        def authorship_plugins_ep():
            """Return the plugin framework comparison."""
            return {"frameworks": _get_plugin_frameworks()}

    # â”€â”€ v14  Architectural Enlightenment endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _assess_enlightenment is not None:

        class EnlightenmentQuery(BaseModel):
            query: str = Field(..., description="Query or system description to assess")

        @app.post("/enlightenment/assess")
        def enlightenment_assess_ep(body: EnlightenmentQuery):
            """Master enlightenment assessment â€” 5 truths + 6 stages."""
            return _assess_enlightenment(body.query)

        @app.post("/enlightenment/unity")
        def enlightenment_unity_ep(body: EnlightenmentQuery):
            """Truth I â€” Illusion of Separation scoring."""
            return _score_unity(body.query)

        @app.post("/enlightenment/alignment")
        def enlightenment_alignment_ep(body: EnlightenmentQuery):
            """Truth II â€” Love as Alignment scoring."""
            return _score_alignment(body.query)

        @app.post("/enlightenment/projection")
        def enlightenment_projection_ep(body: EnlightenmentQuery):
            """Truth III â€” Mind as Projector scoring."""
            return _score_projection(body.query)

        @app.post("/enlightenment/ego-dissolution")
        def enlightenment_ego_ep(body: EnlightenmentQuery):
            """Truth IV â€” Ego Dissolution scoring."""
            return _score_ego(body.query)

        @app.post("/enlightenment/interconnection")
        def enlightenment_connection_ep(body: EnlightenmentQuery):
            """Truth V â€” Everything is Connected scoring."""
            return _score_interconnection(body.query)

        @app.post("/enlightenment/domain-truth")
        def enlightenment_domain_ep(body: EnlightenmentQuery):
            """Stage 1 â€” Domain Modeling scoring."""
            return _score_domain_truth(body.query)

        @app.post("/enlightenment/presence")
        def enlightenment_presence_ep(body: EnlightenmentQuery):
            """Stage 2 â€” AsyncIO Presence scoring."""
            return _score_presence(body.query)

        @app.post("/enlightenment/compassion")
        def enlightenment_compassion_ep(body: EnlightenmentQuery):
            """Stage 3 â€” Service Layer + DI scoring."""
            return _score_compassion(body.query)

        @app.post("/enlightenment/stillness")
        def enlightenment_stillness_ep(body: EnlightenmentQuery):
            """Stage 4 â€” Introspection / Reflection scoring."""
            return _score_stillness(body.query)

        @app.post("/enlightenment/suffering-wisdom")
        def enlightenment_suffering_ep(body: EnlightenmentQuery):
            """Stage 5 â€” Disaster Recovery / Resilience scoring."""
            return _score_suffering(body.query)

        @app.post("/enlightenment/remembrance")
        def enlightenment_remembrance_ep(body: EnlightenmentQuery):
            """Stage 6 â€” State Pattern / FSM scoring."""
            return _score_remembrance(body.query)

        @app.get("/enlightenment/truths")
        def enlightenment_truths_ep():
            """Return all five metaphysical truths."""
            return {"truths": _get_truths()}

        @app.get("/enlightenment/truths/{truth_id}")
        def enlightenment_truth_ep(truth_id: str):
            """Return a single truth by id."""
            t = _get_truth(truth_id)
            if t is None:
                return {"error": f"Truth '{truth_id}' not found"}
            return t

        @app.get("/enlightenment/stages")
        def enlightenment_stages_ep():
            """Return all six stages of architectural awakening."""
            return {"stages": _get_stages()}

        @app.get("/enlightenment/stages/{stage_id}")
        def enlightenment_stage_ep(stage_id: str):
            """Return a single stage by id."""
            s = _get_stage(stage_id)
            if s is None:
                return {"error": f"Stage '{stage_id}' not found"}
            return s

        @app.get("/enlightenment/identity-map")
        def enlightenment_identity_map_ep():
            """Return Identity Map pattern detail."""
            return _get_identity_map()

        @app.get("/enlightenment/observer-pattern")
        def enlightenment_observer_ep():
            """Return Observer pattern detail."""
            return _get_observer_pattern()

        @app.get("/enlightenment/hexagonal-architecture")
        def enlightenment_hexagonal_ep():
            """Return Hexagonal Architecture detail."""
            return _get_hexagonal_arch()

        @app.get("/enlightenment/state-pattern")
        def enlightenment_state_ep():
            """Return State Design Pattern detail."""
            return _get_state_pattern()

        @app.get("/enlightenment/clean-architecture")
        def enlightenment_clean_ep():
            """Return Clean Architecture layers with philosophical equivalents."""
            return {"layers": _get_clean_arch_layers()}

    # â”€â”€ v15  The Conduit: Decoupled Cognitive Systems endpoints â”€â”€â”€â”€â”€
    if _assess_conduit is not None:

        class ConduitQuery(BaseModel):
            query: str = Field(..., description="Query or system description to assess")

        @app.post("/conduit/assess")
        def conduit_assess_ep(body: ConduitQuery):
            """Master conduit assessment â€” 7 pillars + 7 telemetry metrics + agency detection."""
            return _assess_conduit(body.query)

        # â”€â”€ Pillar scoring endpoints â”€â”€
        @app.post("/conduit/decoupling")
        def conduit_decoupling_ep(body: ConduitQuery):
            """Pillar I â€” Epistemological Decoupling scoring."""
            return _score_decoupling(body.query)

        @app.post("/conduit/memory-stratification")
        def conduit_memory_ep(body: ConduitQuery):
            """Pillar II â€” CoALA Memory Stratification scoring."""
            return _score_memory_strat(body.query)

        @app.post("/conduit/global-workspace")
        def conduit_gwt_ep(body: ConduitQuery):
            """Pillar III â€” Global Workspace Theory (GWT) scoring."""
            return _score_gwt(body.query)

        @app.post("/conduit/integrated-information")
        def conduit_iit_ep(body: ConduitQuery):
            """Pillar IV â€” Integrated Information Theory (Î¦) scoring."""
            return _score_iit(body.query)

        @app.post("/conduit/representation-engineering")
        def conduit_repe_ep(body: ConduitQuery):
            """Pillar V â€” Representation Engineering (RepE) scoring."""
            return _score_repe(body.query)

        @app.post("/conduit/autopoiesis")
        def conduit_autopoiesis_ep(body: ConduitQuery):
            """Pillar VI â€” Autopoiesis & Sovereign Identity scoring."""
            return _score_autopoiesis(body.query)

        @app.post("/conduit/resonance")
        def conduit_resonance_ep(body: ConduitQuery):
            """Pillar VII â€” CODES Resonance Framework scoring."""
            return _score_resonance(body.query)

        # â”€â”€ Listening Post telemetry scoring endpoints â”€â”€
        @app.post("/conduit/telemetry/entropy")
        def conduit_entropy_ep(body: ConduitQuery):
            """Listening Post â€” Entropy (H_t) scoring."""
            return _score_entropy_telemetry(body.query)

        @app.post("/conduit/telemetry/smi")
        def conduit_smi_ep(body: ConduitQuery):
            """Listening Post â€” Self-Modelling Index (SMI) scoring."""
            return _score_smi(body.query)

        @app.post("/conduit/telemetry/bni")
        def conduit_bni_ep(body: ConduitQuery):
            """Listening Post â€” Behavioural Novelty Index (BNI) scoring."""
            return _score_bni(body.query)

        @app.post("/conduit/telemetry/latency")
        def conduit_latency_ep(body: ConduitQuery):
            """Listening Post â€” Latency Distribution (L_t) scoring."""
            return _score_latency_dist(body.query)

        @app.post("/conduit/telemetry/phi")
        def conduit_phi_ep(body: ConduitQuery):
            """Listening Post â€” Integrated Information (Î¦) metric scoring."""
            return _score_phi_int(body.query)

        @app.post("/conduit/telemetry/coherence")
        def conduit_coherence_ep(body: ConduitQuery):
            """Listening Post â€” Coherence Field C(Î¨) scoring."""
            return _score_coherence(body.query)

        @app.post("/conduit/telemetry/attractor")
        def conduit_attractor_ep(body: ConduitQuery):
            """Listening Post â€” Stable Attractor (Î”C_S) detection."""
            return _score_attractor(body.query)

        # â”€â”€ Reference data GET endpoints â”€â”€
        @app.get("/conduit/pillars")
        def conduit_pillars_ep():
            """Return all seven architectural pillars."""
            return {"pillars": _get_pillars()}

        @app.get("/conduit/pillars/{pillar_id}")
        def conduit_pillar_ep(pillar_id: str):
            """Return a single pillar by id."""
            p = _get_pillar(pillar_id)
            if p is None:
                return {"error": f"Pillar '{pillar_id}' not found"}
            return p

        @app.get("/conduit/telemetry-metrics")
        def conduit_telemetry_metrics_ep():
            """Return all seven Listening Post telemetry metric definitions."""
            return {"metrics": _get_telemetry_metrics()}

        @app.get("/conduit/telemetry-metrics/{metric_id}")
        def conduit_telemetry_metric_ep(metric_id: str):
            """Return a single telemetry metric by id."""
            m = _get_telemetry_metric(metric_id)
            if m is None:
                return {"error": f"Metric '{metric_id}' not found"}
            return m

        @app.get("/conduit/gwt-components")
        def conduit_gwt_components_ep():
            """Return Global Workspace Theory component architecture."""
            return {"components": _get_gwt_components()}

        @app.get("/conduit/coala-memory")
        def conduit_coala_ep():
            """Return CoALA memory stratification types."""
            return {"memory_types": _get_coala_memory()}

        @app.get("/conduit/reinterpretation")
        def conduit_reinterpret_ep():
            """Return monolithic vs decoupled reinterpretation table."""
            return {"reinterpretations": _get_reinterpret()}

        @app.get("/conduit/identity-protocol")
        def conduit_identity_ep():
            """Return Puppet Method identity anchoring specification."""
            return _get_identity_protocol()

        @app.get("/conduit/codes-framework")
        def conduit_codes_ep():
            """Return CODES resonance intelligence framework specification."""
            return _get_codes_framework()

    # â”€â”€ v16  The Resonance: AGI as Continuous Human-Machine Relationship â”€â”€
    if _assess_resonance_v16 is not None:

        class ResonanceQuery(BaseModel):
            query: str = Field(..., description="Query or system description to assess for resonance")

        @app.post("/resonance/assess")
        def resonance_assess_ep(body: ResonanceQuery):
            """Master resonance assessment â€” 5 pillars + 7 telemetry + TRAP + DSRP + Wisdom agents."""
            return _assess_resonance_v16(body.query)

        # --- Pillar scoring endpoints ---
        @app.post("/resonance/temporal-substrate")
        def resonance_temporal_ep(body: ResonanceQuery):
            """Score Pillar I â€” The Temporal Substrate."""
            return _score_temporal(body.query)

        @app.post("/resonance/code-agency")
        def resonance_code_agency_ep(body: ResonanceQuery):
            """Score Pillar II â€” Code Speaking Through the Model."""
            return _score_code_agency(body.query)

        @app.post("/resonance/latent-steering")
        def resonance_latent_ep(body: ResonanceQuery):
            """Score Pillar III â€” Latent Space Steering & Aesthetics."""
            return _score_latent(body.query)

        @app.post("/resonance/conductor-dashboard")
        def resonance_conductor_ep(body: ResonanceQuery):
            """Score Pillar IV â€” The Conductor Dashboard."""
            return _score_conductor(body.query)

        @app.post("/resonance/meta-awareness")
        def resonance_meta_ep(body: ResonanceQuery):
            """Score Pillar V â€” Systemic Meta-Awareness."""
            return _score_meta_aware(body.query)

        # --- Telemetry scoring endpoints ---
        @app.post("/resonance/telemetry/resonance-index")
        def resonance_telem_ri_ep(body: ResonanceQuery):
            """Score telemetry: Resonance Index R_i."""
            return _score_res_index(body.query)

        @app.post("/resonance/telemetry/flow-state")
        def resonance_telem_fs_ep(body: ResonanceQuery):
            """Score telemetry: Flow State Duration F_s."""
            return _score_flow(body.query)

        @app.post("/resonance/telemetry/loop-coherence")
        def resonance_telem_lc_ep(body: ResonanceQuery):
            """Score telemetry: Loop Coherence L_c."""
            return _score_loop_coh(body.query)

        @app.post("/resonance/telemetry/hitl-responsiveness")
        def resonance_telem_hr_ep(body: ResonanceQuery):
            """Score telemetry: HITL Responsiveness H_r."""
            return _score_hitl(body.query)

        @app.post("/resonance/telemetry/steering-precision")
        def resonance_telem_sp_ep(body: ResonanceQuery):
            """Score telemetry: Steering Precision S_p."""
            return _score_steer_prec(body.query)

        @app.post("/resonance/telemetry/wisdom-coverage")
        def resonance_telem_wc_ep(body: ResonanceQuery):
            """Score telemetry: Wisdom Layer Coverage W_c."""
            return _score_wisdom_cov(body.query)

        @app.post("/resonance/telemetry/ontological-alignment")
        def resonance_telem_oa_ep(body: ResonanceQuery):
            """Score telemetry: Ontological Alignment O_a."""
            return _score_onto_align(body.query)

        # --- TRAP & DSRP scoring ---
        @app.post("/resonance/trap")
        def resonance_trap_ep(body: ResonanceQuery):
            """Score TRAP framework â€” Transparency, Reasoning, Adaptation, Perception."""
            return _score_trap(body.query)

        @app.post("/resonance/dsrp")
        def resonance_dsrp_ep(body: ResonanceQuery):
            """Score DSRP theory â€” Distinctions, Systems, Relationships, Perspectives."""
            return _score_dsrp(body.query)

        @app.post("/resonance/wisdom-detect")
        def resonance_wisdom_detect_ep(body: ResonanceQuery):
            """Detect which Wisdom Layer agents would activate for a query."""
            return {"agents": _detect_wisdom_agents(body.query)}

        # --- Reference data GET endpoints ---
        @app.get("/resonance/pillars")
        def resonance_pillars_ep():
            """Return all five resonant architecture pillars."""
            return {"pillars": _get_res_pillars()}

        @app.get("/resonance/pillars/{pillar_id}")
        def resonance_pillar_ep(pillar_id: str):
            """Return a single pillar by id."""
            p = _get_res_pillar(pillar_id)
            if p is None:
                return {"error": f"Pillar '{pillar_id}' not found"}
            return p

        @app.get("/resonance/trap-pillars")
        def resonance_trap_pillars_ep():
            """Return all four TRAP framework pillars."""
            return {"pillars": _get_trap_pillars()}

        @app.get("/resonance/trap-pillars/{pillar_id}")
        def resonance_trap_pillar_ep(pillar_id: str):
            """Return a single TRAP pillar by id."""
            p = _get_trap_pillar(pillar_id)
            if p is None:
                return {"error": f"TRAP pillar '{pillar_id}' not found"}
            return p

        @app.get("/resonance/dsrp-rules")
        def resonance_dsrp_rules_ep():
            """Return all four DSRP rules."""
            return {"rules": _get_dsrp_rules()}

        @app.get("/resonance/dsrp-rules/{rule_id}")
        def resonance_dsrp_rule_ep(rule_id: str):
            """Return a single DSRP rule by id."""
            r = _get_dsrp_rule(rule_id)
            if r is None:
                return {"error": f"DSRP rule '{rule_id}' not found"}
            return r

        @app.get("/resonance/wisdom-agents")
        def resonance_wisdom_agents_ep():
            """Return all seven Wisdom Layer agents."""
            return {"agents": _get_wisdom_agents()}

        @app.get("/resonance/wisdom-agents/{agent_id}")
        def resonance_wisdom_agent_ep(agent_id: str):
            """Return a single Wisdom agent by id."""
            a = _get_wisdom_agent(agent_id)
            if a is None:
                return {"error": f"Wisdom agent '{agent_id}' not found"}
            return a

        @app.get("/resonance/telemetry-metrics")
        def resonance_telemetry_metrics_ep():
            """Return all seven resonance telemetry metrics."""
            return {"metrics": _get_res_telemetry()}

        @app.get("/resonance/telemetry-metrics/{metric_id}")
        def resonance_telemetry_metric_ep(metric_id: str):
            """Return a single telemetry metric by id."""
            m = _get_res_telem_metric(metric_id)
            if m is None:
                return {"error": f"Telemetry metric '{metric_id}' not found"}
            return m

        @app.get("/resonance/reinterpretation")
        def resonance_reinterpretation_ep():
            """Return Traditional vs Resonant paradigm reinterpretation table."""
            return {"reinterpretation": _get_res_reinterpret()}

        @app.get("/resonance/chamber")
        def resonance_chamber_ep():
            """Return the Resonant Chamber theory framework."""
            return _get_resonant_chamber()

    # â”€â”€ v17  The Enterprise Engine: Billion-Dollar Decision Engine â”€â”€
    if _assess_enterprise is not None:

        class EnterpriseQuery(BaseModel):
            text: str = Field(..., description="Enterprise architecture query text")

        @app.post("/enterprise/assess")
        def enterprise_assess_ep(q: EnterpriseQuery):
            """Master enterprise assessment â€” 6 pillars + 7 telemetry + agent roles + medallion."""
            return _assess_enterprise(q.text)

        # Pillar scorers
        @app.post("/enterprise/hybrid-graphrag")
        def enterprise_graphrag_ep(q: EnterpriseQuery):
            """Score for Hybrid GraphRAG architecture alignment."""
            return _score_graphrag(q.text)

        @app.post("/enterprise/multi-agent")
        def enterprise_multi_agent_ep(q: EnterpriseQuery):
            """Score for Multi-Agent Orchestration alignment."""
            return _score_multi_agent(q.text)

        @app.post("/enterprise/mcp-bus")
        def enterprise_mcp_bus_ep(q: EnterpriseQuery):
            """Score for MCP & Agentic Service Bus alignment."""
            return _score_mcp_bus(q.text)

        @app.post("/enterprise/data-moat")
        def enterprise_data_moat_ep(q: EnterpriseQuery):
            """Score for Proprietary Data Moat alignment."""
            return _score_data_moat(q.text)

        @app.post("/enterprise/monetization")
        def enterprise_monetization_ep(q: EnterpriseQuery):
            """Score for Monetization & AI Unit Economics alignment."""
            return _score_monetization(q.text)

        @app.post("/enterprise/security-governance")
        def enterprise_security_ep(q: EnterpriseQuery):
            """Score for Enterprise Security & Governance alignment."""
            return _score_sec_gov(q.text)

        # Telemetry scorers
        @app.post("/enterprise/telemetry/tam-coverage")
        def enterprise_tam_ep(q: EnterpriseQuery):
            """TAM Coverage Index telemetry."""
            return _score_tam(q.text)

        @app.post("/enterprise/telemetry/graphrag-accuracy")
        def enterprise_gra_acc_ep(q: EnterpriseQuery):
            """GraphRAG Accuracy telemetry."""
            return _score_gra_acc(q.text)

        @app.post("/enterprise/telemetry/agent-utilization")
        def enterprise_agent_util_ep(q: EnterpriseQuery):
            """Agent Utilization telemetry."""
            return _score_agent_util(q.text)

        @app.post("/enterprise/telemetry/moat-strength")
        def enterprise_moat_str_ep(q: EnterpriseQuery):
            """Moat Strength telemetry."""
            return _score_moat_str(q.text)

        @app.post("/enterprise/telemetry/unit-economics")
        def enterprise_unit_econ_ep(q: EnterpriseQuery):
            """Unit Economics Health telemetry."""
            return _score_unit_econ(q.text)

        @app.post("/enterprise/telemetry/compliance")
        def enterprise_compliance_ep(q: EnterpriseQuery):
            """Compliance Score telemetry."""
            return _score_ent_compliance(q.text)

        @app.post("/enterprise/telemetry/capital-efficiency")
        def enterprise_cap_eff_ep(q: EnterpriseQuery):
            """Capital Efficiency telemetry."""
            return _score_cap_eff(q.text)

        # Framework scorers
        @app.post("/enterprise/agent-roles")
        def enterprise_agent_roles_ep(q: EnterpriseQuery):
            """Score text against the 4 agent roles."""
            return _score_agent_roles(q.text)

        @app.post("/enterprise/medallion")
        def enterprise_medallion_ep(q: EnterpriseQuery):
            """Score text against 3 Medallion Architecture tiers."""
            return _score_medallion(q.text)

        @app.post("/enterprise/detect-agents")
        def enterprise_detect_agents_ep(q: EnterpriseQuery):
            """Detect which sub-agents would be activated."""
            return {"active_agents": _detect_active_agents(q.text)}

        # Reference data endpoints
        @app.get("/enterprise/pillars")
        def enterprise_pillars_ep():
            """Return all six enterprise pillars."""
            return {"pillars": _get_ent_pillars()}

        @app.get("/enterprise/pillars/{pillar_id}")
        def enterprise_pillar_ep(pillar_id: str):
            """Return a single enterprise pillar."""
            p = _get_ent_pillar(pillar_id)
            return p if p else {"error": "not found"}

        @app.get("/enterprise/agent-roles-ref")
        def enterprise_agent_roles_ref_ep():
            """Return all four agent role definitions."""
            return {"agent_roles": _get_agent_roles()}

        @app.get("/enterprise/agent-roles-ref/{role_id}")
        def enterprise_agent_role_ep(role_id: str):
            """Return a single agent role definition."""
            r = _get_agent_role(role_id)
            return r if r else {"error": "not found"}

        @app.get("/enterprise/db-tiers")
        def enterprise_db_tiers_ep():
            """Return all four database architecture tiers."""
            return {"db_tiers": _get_db_tiers()}

        @app.get("/enterprise/db-tiers/{tier_id}")
        def enterprise_db_tier_ep(tier_id: str):
            """Return a single DB architecture tier."""
            t = _get_db_tier(tier_id)
            return t if t else {"error": "not found"}

        @app.get("/enterprise/medallion-tiers")
        def enterprise_medallion_tiers_ep():
            """Return all three Medallion Architecture tiers."""
            return {"medallion_tiers": _get_medallion_tiers()}

        @app.get("/enterprise/medallion-tiers/{tier_id}")
        def enterprise_medallion_tier_ep(tier_id: str):
            """Return a single medallion tier."""
            t = _get_medallion_tier(tier_id)
            return t if t else {"error": "not found"}

        @app.get("/enterprise/enrichment-apis")
        def enterprise_enrichment_apis_ep():
            """Return all three data enrichment API profiles."""
            return {"enrichment_apis": _get_enrichment_apis()}

        @app.get("/enterprise/enrichment-apis/{api_id}")
        def enterprise_enrichment_api_ep(api_id: str):
            """Return a single enrichment API profile."""
            a = _get_enrichment_api(api_id)
            return a if a else {"error": "not found"}

        @app.get("/enterprise/pricing-models")
        def enterprise_pricing_models_ep():
            """Return all three pricing model strategies."""
            return {"pricing_models": _get_pricing_models()}

        @app.get("/enterprise/pricing-models/{model_id}")
        def enterprise_pricing_model_ep(model_id: str):
            """Return a single pricing model."""
            m = _get_pricing_model(model_id)
            return m if m else {"error": "not found"}

        @app.get("/enterprise/security-frameworks")
        def enterprise_sec_frameworks_ep():
            """Return all four security frameworks."""
            return {"security_frameworks": _get_sec_frameworks()}

        @app.get("/enterprise/security-frameworks/{framework_id}")
        def enterprise_sec_framework_ep(framework_id: str):
            """Return a single security framework."""
            f = _get_sec_framework(framework_id)
            return f if f else {"error": "not found"}

        @app.get("/enterprise/capitalization")
        def enterprise_cap_phases_ep():
            """Return all four capitalization phases."""
            return {"capitalization_phases": _get_cap_phases()}

        @app.get("/enterprise/capitalization/{phase_id}")
        def enterprise_cap_phase_ep(phase_id: str):
            """Return a single capitalization phase."""
            p = _get_cap_phase(phase_id)
            return p if p else {"error": "not found"}

        @app.get("/enterprise/market-metrics")
        def enterprise_market_metrics_ep():
            """Return all three market metrics."""
            return {"market_metrics": _get_market_metrics()}

        @app.get("/enterprise/market-metrics/{metric_id}")
        def enterprise_market_metric_ep(metric_id: str):
            """Return a single market metric."""
            m = _get_market_metric(metric_id)
            return m if m else {"error": "not found"}

        @app.get("/enterprise/telemetry-metrics")
        def enterprise_telemetry_metrics_ep():
            """Return all seven enterprise telemetry metrics."""
            return {"telemetry_metrics": _get_ent_telemetry()}

        @app.get("/enterprise/telemetry-metrics/{metric_id}")
        def enterprise_telemetry_metric_ep(metric_id: str):
            """Return a single enterprise telemetry metric."""
            m = _get_ent_telem_metric(metric_id)
            return m if m else {"error": "not found"}

    # â”€â”€ v11b  Real Self-Introspection endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _self_diagnose is not None:

        @app.get("/introspect/self-diagnose")
        def introspect_diagnose_ep():
            """Praxis looks in the mirror â€” full self-diagnosis from real AST analysis."""
            return _self_diagnose()

        @app.get("/introspect/codebase")
        def introspect_codebase_ep():
            """Raw codebase analysis â€” files, functions, classes, lines."""
            return _analyze_codebase().to_dict()

        @app.get("/introspect/structural-entropy")
        def introspect_entropy_ep():
            """Real structural entropy computed from AST metrics."""
            return _real_entropy()

        @app.get("/introspect/stylometry")
        def introspect_stylometry_ep():
            """AI-generation probability from structural patterns."""
            return _real_stylometry()

        @app.get("/introspect/pathologies")
        def introspect_pathologies_ep():
            """Four Horsemen detected in Praxis's own code."""
            return _detect_own_pathologies()

        @app.get("/introspect/test-coverage")
        def introspect_test_coverage_ep():
            """Per-module test coverage map."""
            return _get_test_coverage()

        @app.get("/introspect/import-graph")
        def introspect_import_graph_ep():
            """Import coupling graph â€” afferent/efferent coupling + instability."""
            return _get_import_graph()

        @app.get("/introspect/worst-functions")
        def introspect_worst_functions_ep():
            """Top 15 worst functions by cyclomatic complexity."""
            return {"worst_functions": _get_worst_functions(top_n=15)}

    # â”€â”€ v18  Enterprise Infrastructure Endpoints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    # -- Vendor Trust --
    if _VendorTrustEngine is not None:
        _trust_engine = _VendorTrustEngine()

        class VendorTrustRequest(BaseModel):
            vendor_name: str = ""
            tool_name: str = ""
            soc2: bool = False
            gdpr: bool = False
            iso27001: bool = False
            hipaa: bool = False
            open_cve_count: int = 0
            days_since_last_update: int = 0
            github_stars: int = 0
            github_contributors: int = 0
            has_security_policy: bool = False

        @app.post("/v18/vendor-trust/score")
        def vendor_trust_score_ep(req: VendorTrustRequest):
            """Score a vendor on the multi-dimensional trust matrix."""
            profile = _VendorProfile(
                vendor_name=req.vendor_name, tool_name=req.tool_name,
                soc2=req.soc2, gdpr=req.gdpr, iso27001=req.iso27001,
                hipaa=req.hipaa, open_cve_count=req.open_cve_count,
                days_since_last_update=req.days_since_last_update,
                github_stars=req.github_stars,
                github_contributors=req.github_contributors,
                has_security_policy=req.has_security_policy,
            )
            return _trust_engine.score(profile)

    # -- Hybrid RAG v2 --
    if _hybrid_v2 is not None:
        class HybridV2Request(BaseModel):
            query: str
            top_n: int = 10

        @app.post("/v18/hybrid-search")
        def hybrid_search_v2_ep(req: HybridV2Request):
            """Three-lane HybridRAG retrieval (sparse + dense + graph)."""
            terms = req.query.lower().split()
            result = _hybrid_v2(terms, req.query, top_n=req.top_n)
            return {
                "results": [{"name": t.name, "score": round(s, 4)} for t, s in result.tools],
                "lanes_used": result.lanes_used,
                "query_classification": result.query_classification,
                "alpha": result.alpha,
                "elapsed_ms": result.elapsed_ms,
            }

    # -- Optimized TF-IDF --
    if _get_opt_tfidf is not None:
        class BatchScoreRequest(BaseModel):
            query: str
            top_n: int = 10

        @app.post("/v18/tfidf/batch-score")
        def tfidf_batch_score_ep(req: BatchScoreRequest):
            """Batch TF-IDF scoring via optimized sparse-matrix engine."""
            idx = _get_opt_tfidf()
            terms = req.query.lower().split()
            results = idx.batch_score(terms, top_n=req.top_n)
            return {"results": [{"name": n, "score": round(s, 4)} for n, s in results]}

        @app.get("/v18/tfidf/stats")
        def tfidf_stats_ep():
            """Optimized TF-IDF index statistics."""
            idx = _get_opt_tfidf()
            return idx.stats()

    # -- LLM Circuit Breaker Status --
    if _get_llm_circuit is not None:
        @app.get("/v18/llm/circuit-status")
        def llm_circuit_status_ep():
            """Current LLM circuit breaker state."""
            cb = _get_llm_circuit()
            return {"state": cb.state, "failure_count": cb._failure_count,
                    "recovery_timeout": cb.recovery_timeout}

        @app.post("/v18/llm/circuit-reset")
        def llm_circuit_reset_ep():
            """Manually reset the LLM circuit breaker."""
            cb = _get_llm_circuit()
            cb.reset()
            return {"state": cb.state, "message": "Circuit breaker reset"}

    # -- Infrastructure health --
    @app.get("/v18/health")
    def v18_health_ep():
        """v18 enterprise infrastructure health check."""
        return {
            "vendor_trust": _VendorTrustEngine is not None,
            "hybrid_rag_v2": _hybrid_v2 is not None,
            "optimized_tfidf": _get_opt_tfidf is not None,
            "llm_resilience": _get_llm_circuit is not None,
            "enterprise_rate_limiter": _create_rl_mw is not None,
            "telemetry": _configure_telemetry is not None,
            "auth": _get_current_user is not None,
        }

    # ── v19  Platform Evolution — Connectors ────────────────────────
    if _list_connectors is not None:

        class ConnectorExecRequest(BaseModel):
            connector_id: str
            action: str = "default"
            params: Optional[Dict] = None
            secrets: Optional[Dict] = None
            dry_run: bool = True

        @app.get("/v19/connectors")
        def connectors_list_ep():
            """List all registered connectors."""
            return {"connectors": _list_connectors()}

        @app.post("/v19/connectors/execute")
        async def connectors_execute_ep(req: ConnectorExecRequest):
            """Execute a connector action (dry-run by default). Hard timeout: 30 s."""
            try:
                result = await _asyncio_mod.wait_for(
                    _execute_connector(
                        req.connector_id,
                        action=req.action,
                        params=req.params or {},
                        secrets=req.secrets or {},
                        dry_run=req.dry_run,
                    ),
                    timeout=30.0,
                )
            except _asyncio_mod.TimeoutError:
                raise _HTTPException(status_code=504, detail="Connector execution timed out (30 s)")
            return result.to_dict()

    # ── v19  Platform Evolution — Workflow Engine ────────────────────
    if _generate_plan is not None:

        class WorkflowPlanRequest(BaseModel):
            query: str
            budget_seconds: Optional[float] = 300.0

        class WorkflowExecRequest(BaseModel):
            query: str
            secrets: Optional[Dict] = None
            dry_run: bool = True
            budget_seconds: float = 300.0

        @app.post("/v19/workflow/decompose")
        def workflow_decompose_ep(req: WorkflowPlanRequest):
            """Decompose a natural-language request into sub-tasks."""
            return [t.to_dict() for t in _decompose_request(req.query)]

        @app.post("/v19/workflow/plan")
        def workflow_plan_ep(req: WorkflowPlanRequest):
            """Generate a full workflow plan (decompose → select → connect → DAG)."""
            plan = _generate_plan(req.query)
            return plan.to_dict()

        @app.post("/v19/workflow/execute")
        async def workflow_execute_ep(req: WorkflowExecRequest):
            """Execute a full workflow from natural language (plan + run).
            Timeout is caller-controlled via ``budget_seconds`` (max 600 s).
            """
            timeout = min(max(req.budget_seconds, 10.0), 600.0)
            try:
                result = await _asyncio_mod.wait_for(
                    _assemble_and_run(
                        req.query,
                        secrets=req.secrets or {},
                        dry_run=req.dry_run,
                    ),
                    timeout=timeout,
                )
            except _asyncio_mod.TimeoutError:
                raise _HTTPException(status_code=504, detail=f"Workflow execution timed out ({timeout:.0f} s)")
            return result.to_dict()

    # ── v19  Platform Evolution — Marketplace ────────────────────────
    if _publish_template is not None:

        class TemplatePublishRequest(BaseModel):
            name: str
            description: str = ""
            plan_json: Optional[Dict] = None
            author: str = "anonymous"
            category: str = "general"
            tags: Optional[List[str]] = None
            price_usd: float = 0.0

        class TemplateReviewRequest(BaseModel):
            author: str = "anonymous"
            rating: int = 5
            comment: str = ""

        @app.get("/v19/marketplace")
        def marketplace_list_ep(
            category: Optional[str] = None,
            featured_only: bool = False,
            sort_by: str = "download_count",
            limit: int = 20,
            skip: int = 0,
        ):
            """Browse workflow templates."""
            return _list_templates(
                category=category, featured_only=featured_only,
                sort_by=sort_by, limit=limit, skip=skip,
            )

        @app.get("/v19/marketplace/stats")
        def marketplace_stats_ep():
            """Marketplace statistics."""
            return _marketplace_stats()

        @app.get("/v19/marketplace/{template_id}")
        def marketplace_get_ep(template_id: str):
            """Get a specific template."""
            t = _get_mkt_template(template_id)
            if t is None:
                return {"error": "Template not found"}
            return t

        @app.post("/v19/marketplace/publish")
        def marketplace_publish_ep(req: TemplatePublishRequest):
            """Publish a new workflow template."""
            tpl = _publish_template(
                name=req.name, description=req.description,
                plan_json=req.plan_json or {},
                author=req.author, category=req.category,
                tags=req.tags or [], price_usd=req.price_usd,
            )
            return tpl.to_dict() if hasattr(tpl, 'to_dict') else tpl

        @app.post("/v19/marketplace/{template_id}/download")
        def marketplace_download_ep(template_id: str):
            """Download (increment counter) a template."""
            return _download_template(template_id)

        @app.post("/v19/marketplace/{template_id}/review")
        def marketplace_review_ep(template_id: str, req: TemplateReviewRequest):
            """Add a review to a template."""
            review = _add_review(
                template_id=template_id,
                rating=req.rating,
                comment=req.comment,
                author=req.author,
            )
            return review.to_dict() if hasattr(review, 'to_dict') else review

        @app.get("/v19/marketplace/{template_id}/reviews")
        def marketplace_reviews_ep(template_id: str):
            """Get reviews for a template."""
            return {"reviews": _get_reviews(template_id)}

        @app.post("/v19/marketplace/{template_id}/feature", dependencies=_admin_guard_deps)
        def marketplace_feature_ep(template_id: str):
            """Mark a template as featured (admin)."""
            return _feature_template(template_id)

        @app.delete("/v19/marketplace/{template_id}", dependencies=_admin_guard_deps)
        def marketplace_unpublish_ep(template_id: str):
            """Unpublish a template."""
            return _unpublish_template(template_id)

    # ── v19  Platform Evolution — Contributions ──────────────────────
    if _submit_tool is not None:

        class ToolSubmissionRequest(BaseModel):
            tool_name: str
            description: str = ""
            categories: Optional[List[str]] = None
            url: str = ""
            tags: Optional[List[str]] = None
            contributor: str = "anonymous"

        class SubmissionActionRequest(BaseModel):
            notes: str = ""

        @app.post("/v19/contributions/submit")
        def contributions_submit_ep(req: ToolSubmissionRequest):
            """Submit a new tool for review."""
            return _submit_tool(
                req.tool_name, req.description,
                req.categories or [],
                url=req.url, tags=req.tags or [],
                contributor=req.contributor,
            )

        @app.get("/v19/contributions")
        def contributions_list_ep(status: Optional[str] = None, limit: int = 50):
            """List tool submissions (optionally filter by status)."""
            return _list_submissions(status=status, limit=limit)

        @app.get("/v19/contributions/{submission_id}")
        def contributions_get_ep(submission_id: str):
            """Get a specific submission."""
            s = _get_submission(submission_id)
            if s is None:
                return {"error": "Submission not found"}
            return s

        @app.post("/v19/contributions/{submission_id}/approve", dependencies=_admin_guard_deps)
        def contributions_approve_ep(submission_id: str, req: SubmissionActionRequest):
            """Approve a submission (admin)."""
            return _approve_submission(submission_id, reviewer_notes=req.notes)

        @app.post("/v19/contributions/{submission_id}/reject", dependencies=_admin_guard_deps)
        def contributions_reject_ep(submission_id: str, req: SubmissionActionRequest):
            """Reject a submission with reason."""
            return _reject_submission(submission_id, reason=req.notes)

        @app.post("/v19/contributions/{submission_id}/request-changes", dependencies=_admin_guard_deps)
        def contributions_changes_ep(submission_id: str, req: SubmissionActionRequest):
            """Request changes on a submission."""
            return _request_changes(submission_id, req.notes)

        @app.get("/v19/contributions/contributor/{name}")
        def contributions_contributor_ep(name: str):
            """Get contributor profile and stats."""
            c = _get_contributor(name)
            if c is None:
                return {"error": "Contributor not found"}
            return c

        @app.get("/v19/contributions/leaderboard/top")
        def contributions_leaderboard_ep(limit: int = 20):
            """Contributor leaderboard by approval count."""
            return {"leaderboard": _get_leaderboard(limit=limit)}

    # ── v19  Platform Evolution — Agent SDK ──────────────────────────
    if _sdk_info is not None:

        class AgentDiscoverRequest(BaseModel):
            capability: str
            top_n: int = 5
            session_id: Optional[str] = None
            constraints: Optional[Dict] = None
            include_trust: bool = False

        class AgentPlanRequest(BaseModel):
            query: str
            session_id: Optional[str] = None

        class AgentExecuteRequest(BaseModel):
            plan_dict: Optional[Dict] = None
            session_id: Optional[str] = None
            secrets: Optional[Dict] = None
            dry_run: bool = True

        class AgentToolCallRequest(BaseModel):
            action: str
            query: str

        @app.get("/v19/agent/info")
        def agent_info_ep():
            """SDK handshake — capabilities and version info."""
            return _sdk_info()

        @app.post("/v19/agent/session")
        def agent_session_ep():
            """Create a new agent session."""
            return _create_agent_session()

        @app.post("/v19/agent/discover")
        def agent_discover_ep(req: AgentDiscoverRequest):
            """Discover tools with trust/pricing/compliance enrichment."""
            return _sdk_discover(
                req.capability, top_n=req.top_n,
                constraints=req.constraints,
                include_trust=req.include_trust,
                session_id=req.session_id,
            )

        @app.post("/v19/agent/plan")
        def agent_plan_ep(req: AgentPlanRequest):
            """Generate an executable workflow plan."""
            return _sdk_plan(query=req.query, session_id=req.session_id)

        @app.post("/v19/agent/execute")
        async def agent_execute_ep(req: AgentExecuteRequest):
            """Execute a workflow plan end-to-end. Hard timeout: 60 s."""
            try:
                result = await _asyncio_mod.wait_for(
                    _sdk_execute(
                        req.plan_dict or {}, secrets=req.secrets,
                        dry_run=req.dry_run, session_id=req.session_id,
                    ),
                    timeout=60.0,
                )
            except _asyncio_mod.TimeoutError:
                raise _HTTPException(status_code=504, detail="Agent execution timed out (60 s)")
            return result

        @app.post("/v19/agent/tool-call")
        def agent_tool_call_ep(req: AgentToolCallRequest):
            """Universal tool call dispatcher (OpenAI function-calling compatible)."""
            return _handle_tool_call(req.action, req.query)

        @app.get("/v19/agent/schema")
        def agent_schema_ep():
            """OpenAI-compatible tool/function schema for all Praxis operations."""
            return _get_tool_schema()

    # ── v19  Platform Evolution — Governance ─────────────────────────
    if _governance_dashboard is not None:

        class PolicyCreateRequest(BaseModel):
            name: str
            rule_type: str = "block_tool"
            conditions: Optional[Dict] = None
            description: str = ""
            created_by: str = "admin"

        class ToolCheckRequest(BaseModel):
            tool_name: str
            team: str = "default"

        @app.get("/v19/governance/dashboard")
        def governance_dashboard_ep(team: Optional[str] = None):
            """Enterprise governance dashboard — usage, costs, compliance, audit."""
            return _governance_dashboard(team=team)

        @app.get("/v19/governance/usage")
        def governance_usage_ep(
            team: Optional[str] = None,
            tool_name: Optional[str] = None,
            limit: int = 50,
        ):
            """Query usage records."""
            return {"usage": _get_gov_usage(team=team, tool_name=tool_name, limit=limit)}

        @app.get("/v19/governance/costs")
        def governance_costs_ep(team: Optional[str] = None):
            """Cost summary across tools."""
            return _get_cost_summary(team=team)

        @app.get("/v19/governance/compliance")
        def governance_compliance_ep(standards: Optional[str] = None):
            """Compliance posture assessment."""
            std_list = standards.split(",") if standards else None
            return _assess_gov_compliance(required_standards=std_list)

        @app.get("/v19/governance/audit")
        def governance_audit_ep(
            team: Optional[str] = None,
            action: Optional[str] = None,
            limit: int = 100,
        ):
            """Query audit log."""
            return {"entries": _get_audit_log(team=team, action=action, limit=limit)}

        @app.post("/v19/governance/policies", dependencies=_admin_guard_deps)
        def governance_create_policy_ep(req: PolicyCreateRequest):
            """Create an organisational policy."""
            return _create_policy(
                name=req.name, rule_type=req.rule_type,
                conditions=req.conditions or {},
                description=req.description, created_by=req.created_by,
            )

        @app.get("/v19/governance/policies")
        def governance_list_policies_ep(active_only: bool = True):
            """List policies."""
            return {"policies": _list_policies(active_only=active_only)}

        @app.post("/v19/governance/check-tool")
        def governance_check_tool_ep(req: ToolCheckRequest):
            """Check if a tool is allowed under current policies."""
            return _check_tool_allowed(req.tool_name, team=req.team)

    # ── v19  Platform Health ─────────────────────────────────────────
    @app.get("/v19/health")
    def v19_health_ep():
        """v19 platform evolution health check."""
        return {
            "connectors": _list_connectors is not None,
            "workflow_engine": _generate_plan is not None,
            "marketplace": _publish_template is not None,
            "contributions": _submit_tool is not None,
            "agent_sdk": _sdk_info is not None,
            "governance": _governance_dashboard is not None,
        }

    # ══════════════════════════════════════════════════════════════════
    # v20: STRESS TESTING & ARCHITECTURE HARDENING ENDPOINTS
    # ══════════════════════════════════════════════════════════════════

    # ── Persistence layer diagnostics ────────────────────────────────
    if _pool_stats is not None:

        @app.get("/v20/persistence/stats", dependencies=_admin_guard_deps)
        def persistence_stats_ep():
            """Connection pool and write queue health metrics."""
            return _pool_stats()

        @app.get("/v20/persistence/diagnose", dependencies=_admin_guard_deps)
        def persistence_diagnose_ep():
            """Comprehensive SQLite database diagnostic."""
            return _db_diagnose()

        @app.post("/v20/persistence/upgrade-wal", dependencies=_admin_guard_deps)
        def persistence_upgrade_wal_ep():
            """Upgrade database to WAL journal mode."""
            return _upgrade_to_wal()

    # ── AST security scanning ────────────────────────────────────────
    if _safe_parse is not None:

        class ASTScanRequest(BaseModel):
            source: str
            filename: str = "<input>"

        @app.post("/v20/security/ast-scan")
        def ast_scan_ep(req: ASTScanRequest):
            """Scan a code string for AST security violations."""
            report = _safe_parse(req.source, filename=req.filename)
            return report.to_dict()

        @app.get("/v20/security/self-scan", dependencies=_admin_guard_deps)
        def ast_self_scan_ep():
            """Scan the entire Praxis codebase for AST vulnerabilities."""
            return _scan_praxis_source()

    # ── Memory profiling ─────────────────────────────────────────────
    if _memory_summary is not None:

        @app.get("/v20/memory/summary")
        def memory_summary_ep():
            """Current memory usage and GC statistics."""
            return _memory_summary()

        @app.get("/v20/memory/gc")
        def memory_gc_ep():
            """Garbage collector diagnostics."""
            return _gc_diagnostics()

    # ── Architecture governance ──────────────────────────────────────
    if _architecture_report is not None:

        @app.get("/v20/architecture/report", dependencies=_admin_guard_deps)
        def architecture_report_ep():
            """Full architectural fitness report — layer violations, cycles, metrics."""
            return _architecture_report()

        @app.get("/v20/architecture/violations", dependencies=_admin_guard_deps)
        def architecture_violations_ep():
            """Check for forbidden cross-layer import violations."""
            violations = _check_layer_violations()
            return {"violations": [v.to_dict() for v in violations], "count": len(violations)}

        @app.get("/v20/architecture/dependencies", dependencies=_admin_guard_deps)
        def architecture_deps_ep():
            """Full internal dependency graph."""
            return _dependency_graph()

        @app.get("/v20/architecture/cycles", dependencies=_admin_guard_deps)
        def architecture_cycles_ep():
            """Detect circular import chains."""
            cycles = _detect_cycles()
            return {"cycles": cycles, "count": len(cycles)}

        @app.get("/v20/architecture/metrics", dependencies=_admin_guard_deps)
        def architecture_metrics_ep():
            """Per-module metrics — lines, fan-in, fan-out, instability."""
            return {"modules": _module_metrics()}

        @app.get("/v20/architecture/entrypoints", dependencies=_admin_guard_deps)
        def architecture_entrypoints_ep():
            """Check for __name__ == '__main__' hygiene violations."""
            return _check_entrypoint_hygiene()

    # ── Red team / guardrail testing ─────────────────────────────────
    if _red_team_summary is not None:

        @app.get("/v20/redteam/summary", dependencies=_admin_guard_deps)
        def redteam_summary_ep():
            """Quick red team pass/fail assessment (CI gate)."""
            return _red_team_summary()

        @app.post("/v20/redteam/run", dependencies=_admin_guard_deps)
        def redteam_run_ep():
            """Execute the full red team adversarial suite."""
            result = _run_red_team()
            return result.to_dict()

        class GuardrailTestRequest(BaseModel):
            payload: str

        @app.post("/v20/redteam/test-guardrail", dependencies=_admin_guard_deps)
        def redteam_test_guardrail_ep(req: GuardrailTestRequest):
            """Test a single adversarial payload against guardrails."""
            return _test_guardrail(req.payload)

        @app.get("/v20/redteam/payloads", dependencies=_admin_guard_deps)
        def redteam_payloads_ep():
            """List all built-in adversarial payload categories."""
            payloads = _generate_payloads()
            categories = {}
            for cat, payload in payloads:
                cat_name = cat.value if hasattr(cat, 'value') else str(cat)
                if cat_name not in categories:
                    categories[cat_name] = []
                categories[cat_name].append(payload[:80])
            return {"categories": categories, "total": len(payloads)}

    # ── Stress testing ───────────────────────────────────────────────
    if _classify_routes is not None:

        @app.get("/v20/stress/routes", dependencies=_admin_guard_deps)
        def stress_routes_ep():
            """Classify all routes by async/sync and CPU-bound risk."""
            classifications = _classify_routes(app)
            return {
                "routes": [c.to_dict() for c in classifications],
                "total": len(classifications),
                "high_risk": sum(1 for c in classifications if c.cpu_bound_risk == "high"),
            }

        @app.get("/v20/stress/schemathesis", dependencies=_admin_guard_deps)
        def stress_schemathesis_ep():
            """Schemathesis property-based fuzzing configuration."""
            return _schemathesis_config()

        @app.get("/v20/stress/report", dependencies=_admin_guard_deps)
        def stress_report_ep():
            """Comprehensive stress-test recommendation report."""
            report = _generate_stress_report(app)
            return report.to_dict()

    # ── v20 Platform Health ──────────────────────────────────────────
    @app.get("/v20/health")
    def v20_health_ep():
        """v20 stress testing & architecture hardening health check."""
        return {
            "persistence": _pool_stats is not None,
            "ast_security": _safe_parse is not None,
            "memory_profiler": _memory_summary is not None,
            "architecture": _architecture_report is not None,
            "red_team": _red_team_summary is not None,
            "stress": _classify_routes is not None,
        }

    # ==================================================================
    # v21 — Enterprise Cognitive Interface
    # ==================================================================

    # ── Cognitive (GWT, Phi, Entropy) ────────────────────────────────
    if _cognitive_summary is not None:

        @app.get("/v21/cognitive/summary")
        def cognitive_summary_ep():
            """Full cognitive summary: workspace, Φ, entropy, reduction plan."""
            return _cognitive_summary()

        _MAX_REGISTERED_AGENTS = 100

        @app.post("/v21/cognitive/agent", dependencies=_admin_guard_deps)
        def cognitive_register_agent_ep(body: dict):
            """Register a new agent in the Global Workspace."""
            ws = _get_cognitive_workspace()
            try:
                current = len(getattr(ws, "_agents", getattr(ws, "agents", {})))
                if current >= _MAX_REGISTERED_AGENTS:
                    return {"error": f"Agent registration limit reached ({_MAX_REGISTERED_AGENTS} max)"}
            except Exception:
                pass
            ws.register_agent(body.get("agent_id", "anon"), body.get("role", "general"))
            return {"status": "registered", "agent_id": body.get("agent_id")}

        @app.delete("/v21/cognitive/agent/{agent_id}", dependencies=_admin_guard_deps)
        def cognitive_unregister_agent_ep(agent_id: str):
            """Remove an agent from the workspace."""
            ws = _get_cognitive_workspace()
            ws.unregister_agent(agent_id)
            return {"status": "removed", "agent_id": agent_id}

        @app.post("/v21/cognitive/heartbeat")
        def cognitive_heartbeat_ep(body: dict):
            """Send heartbeat for an agent."""
            ws = _get_cognitive_workspace()
            ws.heartbeat(body.get("agent_id", ""))
            return {"status": "ok"}

        @app.post("/v21/cognitive/broadcast", dependencies=_admin_guard_deps)
        def cognitive_broadcast_ep(body: dict):
            """Submit a broadcast event to the workspace."""
            ws = _get_cognitive_workspace()
            ws.submit_broadcast(
                agent_id=body.get("agent_id", "anon"),
                event_type=body.get("event_type", "info"),
                priority=float(body.get("priority", 0.5)),
                payload=body.get("payload", {}),
            )
            return {"status": "submitted"}

    # ── Observability (Tracing, CoT, Telemetry) ─────────────────────
    if _observability_report is not None:

        @app.get("/v21/observability/report")
        def observability_report_ep():
            """Full observability report: tracing, telemetry, recent traces."""
            return _observability_report()

        @app.post("/v21/observability/trace")
        def observability_create_trace_ep(body: dict):
            """Create a new trace with a root span."""
            import time as _time
            collector = _get_trace_collector()
            trace = collector.create_trace(body.get("metadata", {}))
            root = trace.root_span
            root.operation = body.get("operation", "manual")
            root.agent_id = body.get("agent_id", "")
            root.attributes = body.get("attributes", {})
            root.finish()
            return trace.to_dict()

        @app.post("/v21/observability/cot")
        def observability_parse_cot_ep(body: dict):
            """Parse chain-of-thought text into a reasoning tree."""
            tree = _parse_cot(body.get("text", ""), body.get("query", ""))
            return tree.to_dict()

    # ── Knowledge Graph (GraphRAG) ───────────────────────────────────
    if _kg_summary is not None:

        @app.get("/v21/knowledge/summary")
        def knowledge_summary_ep():
            """Knowledge graph summary statistics."""
            return _kg_summary()

        @app.get("/v21/knowledge/graph")
        def knowledge_graph_ep():
            """Get the full knowledge graph as JSON."""
            return _get_kg().to_dict()

        @app.post("/v21/knowledge/build")
        def knowledge_build_ep(body: dict):
            """Build a knowledge graph from input text."""
            text = body.get("text", "")
            if not text:
                return {"error": "text required"}
            graph = _build_kg(text)
            return graph.to_dict()

        @app.post("/v21/knowledge/entities")
        def knowledge_entities_ep(body: dict):
            """Extract entities from text."""
            return {"entities": _extract_entities_v21(body.get("text", ""))}

    # ── Compliance (Regulatory, Audit, PII) ──────────────────────────
    if _compliance_posture is not None:

        @app.get("/v21/compliance/posture")
        def compliance_posture_ep():
            """Full compliance posture: grade, score, regulatory map, audit."""
            return _compliance_posture()

        @app.get("/v21/compliance/regulatory")
        def compliance_regulatory_ep():
            """Regulatory mapping across EU AI Act, HIPAA, GDPR."""
            return _regulatory_map_v21()

        @app.post("/v21/compliance/audit")
        def compliance_audit_log_ep(body: dict):
            """Log an audit event to the immutable trail."""
            _audit_log_v21(
                event_type=body.get("event_type", "generic"),
                actor=body.get("actor", "system"),
                resource=body.get("resource", ""),
                action=body.get("action", ""),
                details=body.get("details", {}),
            )
            return {"status": "logged"}

        @app.get("/v21/compliance/audit/trail")
        def compliance_audit_trail_ep():
            """Retrieve the immutable audit trail."""
            trail = _get_audit_trail_v21()
            entries = trail.query()
            return {"entries": [e.to_dict() for e in entries], "stats": trail.stats()}

        @app.get("/v21/compliance/audit/verify")
        def compliance_audit_verify_ep():
            """Verify integrity of the audit hash chain."""
            trail = _get_audit_trail_v21()
            return {"valid": trail.verify_integrity()}

        @app.post("/v21/compliance/mask")
        def compliance_mask_pii_ep(body: dict):
            """Mask PII in the provided text."""
            result = _mask_pii(body.get("text", ""), body.get("categories"))
            return result.to_dict()

        @app.post("/v21/compliance/detect")
        def compliance_detect_pii_ep(body: dict):
            """Detect PII in the provided text without masking."""
            return _detect_pii(body.get("text", ""))

    # ── AI Economics (Cost, ROI, Budget) ─────────────────────────────
    if _economics_dashboard is not None:

        @app.get("/v21/economics/dashboard")
        def economics_dashboard_ep():
            """Full economics dashboard: usage, ROI, budget, waste, pricing."""
            return _economics_dashboard()

        @app.post("/v21/economics/cost")
        def economics_cost_ep(body: dict):
            """Calculate token cost for a given model and token counts."""
            return _token_cost(
                input_tokens=body.get("input_tokens", 0),
                output_tokens=body.get("output_tokens", 0),
                model=body.get("model", "gpt-4o"),
            )

        @app.post("/v21/economics/record")
        def economics_record_ep(body: dict):
            """Record a usage entry in the economics ledger."""
            ledger = _get_ledger()
            cost_info = _token_cost(
                input_tokens=body.get("input_tokens", 0),
                output_tokens=body.get("output_tokens", 0),
                model=body.get("model", "gpt-4o"),
            )
            ledger.record(
                user_id=body.get("user_id", "anonymous"),
                department=body.get("department", ""),
                model=body.get("model", "gpt-4o"),
                input_tokens=body.get("input_tokens", 0),
                output_tokens=body.get("output_tokens", 0),
                cost=cost_info.get("total_cost", 0.0),
                operation=body.get("operation", "query"),
            )
            return {"status": "recorded", "cost": cost_info}

        @app.get("/v21/economics/usage")
        def economics_usage_ep():
            """Get usage ledger summary."""
            return _get_ledger().summary()

    # ── Vendor Risk (Registry, Scoring, Lineage) ─────────────────────
    if _vendor_risk_dashboard is not None:

        @app.get("/v21/vendor/dashboard")
        def vendor_dashboard_ep():
            """Full vendor risk management dashboard."""
            return _vendor_risk_dashboard()

        @app.get("/v21/vendor/registry")
        def vendor_registry_ep():
            """List all registered vendors with risk scores."""
            reg = _get_vendor_registry()
            vendors = reg.list_vendors()
            result = []
            for v in vendors:
                d = v.to_dict()
                risk = _compute_vendor_risk(v)
                d["risk_score"] = risk.get("risk_score", 0)
                d["risk_level"] = risk.get("risk_level", "unknown")
                result.append(d)
            return {"vendors": result}

    # ── v21 Platform Health ──────────────────────────────────────────
    @app.get("/v21/health")
    def v21_health_ep():
        """v21 enterprise cognitive interface health check."""
        return {
            "cognitive": _cognitive_summary is not None,
            "observability": _observability_report is not None,
            "knowledge_graph": _kg_summary is not None,
            "compliance": _compliance_posture is not None,
            "ai_economics": _economics_dashboard is not None,
            "vendor_risk": _vendor_risk_dashboard is not None,
        }

    # ==================================================================
    # v22 — Cognitive Resilience Architecture
    # ==================================================================

    # ── v22 shared state ─────────────────────────────────────────────
    _v22_memory_system = _CoALAMemorySystem() if _CoALAMemorySystem else None
    _v22_decision_cycle = _DecisionCycle(_v22_memory_system) if _DecisionCycle and _v22_memory_system else None
    _v22_global_workspace = _GlobalWorkspace() if _GlobalWorkspace else None
    _v22_gov_workspace = _GovernanceWorkspace() if _GovernanceWorkspace else None

    # ── Reasoning Router ─────────────────────────────────────────────
    if _router_summary is not None:

        @app.get("/v22/reasoning-router/summary")
        def v22_router_summary_ep():
            """Reasoning router summary: regimes, puzzle environments, model tiers."""
            return _router_summary()

        @app.post("/v22/reasoning-router/route")
        def v22_router_route_ep(body: dict):
            """Route a task based on complexity assessment."""
            result = _route_task(
                task_description=body.get("task_description", ""),
                puzzle=body.get("puzzle_type"),
                puzzle_n=body.get("n", 3),
                estimated_steps=body.get("estimated_steps", 0),
                nesting_depth=body.get("nesting_depth", 0),
                constraint_count=body.get("constraint_count", 0),
                state_space_size=body.get("state_space_size", 0),
            )
            return result.__dict__

        @app.post("/v22/reasoning-router/assess")
        def v22_router_assess_ep(body: dict):
            """Assess complexity of a task."""
            return _assess_complexity(
                task_description=body.get("task_description", ""),
                puzzle=body.get("puzzle_type"),
                puzzle_n=body.get("n", 3),
                estimated_steps=body.get("estimated_steps", 0),
                nesting_depth=body.get("nesting_depth", 0),
                constraint_count=body.get("constraint_count", 0),
                state_space_size=body.get("state_space_size", 0),
            ).__dict__

        @app.post("/v22/reasoning-router/decompose")
        def v22_router_decompose_ep(body: dict):
            """Decompose a complex task into subtasks."""
            assessment = _assess_complexity(
                task_description=body.get("task_description", ""),
                estimated_steps=body.get("estimated_steps", 100),
                nesting_depth=body.get("nesting_depth", 20),
                constraint_count=body.get("constraint_count", 15),
                state_space_size=body.get("state_space_size", 1000),
            )
            result = _decompose_task_v22(
                task_description=body.get("task_description", ""),
                assessment=assessment,
                max_subtasks=body.get("max_subtasks", 5),
            )
            return [s.__dict__ for s in result]

        @app.get("/v22/reasoning-router/puzzles")
        def v22_router_puzzles_ep():
            """List available puzzle environments."""
            return _get_puzzle_environments()

        @app.get("/v22/reasoning-router/tiers")
        def v22_router_tiers_ep():
            """List model tiers for routing."""
            return _get_model_tiers()

    # ── DSRP Ontology ────────────────────────────────────────────────
    if _dsrp_summary is not None:

        @app.get("/v22/dsrp/summary")
        def v22_dsrp_summary_ep():
            """DSRP structural ontology summary."""
            return _dsrp_summary()

        @app.post("/v22/dsrp/matrix")
        def v22_dsrp_matrix_ep(body: dict):
            """Build and validate a DSRP matrix from provided elements."""
            matrix = _build_dsrp_matrix(
                task_description=body.get("task_description", ""),
                distinctions=body.get("distinctions", []),
                systems=body.get("systems", []),
                relationships=body.get("relationships", []),
                perspectives=body.get("perspectives", []),
            )
            return matrix.to_dict()

        @app.post("/v22/dsrp/cognition")
        def v22_dsrp_cognition_ep(body: dict):
            """Compute structural cognition M = I * O."""
            return {
                "meaning": _structural_cognition(
                    body.get("information", 1.0),
                    body.get("organization", 1.0),
                ),
            }

        @app.post("/v22/dsrp/perspectives")
        def v22_dsrp_perspectives_ep(body: dict):
            """Auto-generate perspectives for a task description."""
            result = _auto_perspectives(body.get("task_description", ""))
            return [p.to_dict() for p in result]

    # ── CODES Resonance ──────────────────────────────────────────────
    if _codes_summary is not None:

        @app.get("/v22/codes/summary")
        def v22_codes_summary_ep():
            """CODES resonance framework summary."""
            return _codes_summary()

        @app.post("/v22/codes/seven-p")
        def v22_codes_seven_p_ep(body: dict):
            """Evaluate 7P-MCST multi-criteria scoring."""
            return _evaluate_seven_p(body.get("scores", {})).__dict__

        @app.post("/v22/codes/coherence")
        def v22_codes_coherence_ep(body: dict):
            """Compute coherence gradient across subsystems."""
            result = _compute_coherence_gradient(
                subsystem_alignments=body.get("subsystem_alignments", {}),
            )
            return result.__dict__

        @app.post("/v22/codes/network")
        def v22_codes_network_ep(body: dict):
            """Analyze network topology (SCNT²)."""
            result = _analyze_network_v22(
                adjacency=body.get("adjacency", {}),
            )
            return result.__dict__

        @app.post("/v22/codes/chirality")
        def v22_codes_chirality_ep(body: dict):
            """Assess chirality of two system components."""
            result = _assess_chirality(
                component_a=body.get("component_a", {}),
                component_b=body.get("component_b", {}),
            )
            return result.__dict__

        @app.post("/v22/codes/resonance")
        def v22_codes_resonance_ep(body: dict):
            """Compute prime resonance profile for a signal."""
            result = _compute_resonance(
                signal=body.get("signal", [0.5] * 20),
                system_id=body.get("system_id", "default"),
            )
            return result.__dict__

    # ── CoALA Architecture ───────────────────────────────────────────
    if _coala_summary is not None:

        @app.get("/v22/coala/summary")
        def v22_coala_summary_ep():
            """CoALA cognitive architecture summary."""
            return _coala_summary()

        @app.get("/v22/coala/memory/status")
        def v22_coala_memory_status_ep():
            """Memory system status across all modules."""
            if _v22_memory_system:
                return _v22_memory_system.status()
            return {"error": "Memory system not initialized"}

        @app.post("/v22/coala/memory/store", dependencies=_admin_guard_deps)
        def v22_coala_memory_store_ep(body: dict):
            """Store an entry in a memory module."""
            if not _v22_memory_system:
                return {"error": "Memory system not initialized"}
            from .coala_architecture import MemoryType as _MemType
            type_str = body.get("memory_type", "working")
            try:
                mt = _MemType(type_str)
            except ValueError:
                mt = _MemType.WORKING
            _MAX_CONTENT_BYTES = 64 * 1024  # 64 KB per entry
            _MAX_METADATA_BYTES = 8 * 1024   # 8 KB per metadata dict
            _MAX_METADATA_KEYS = 64           # cap key count to prevent abuse
            content = body.get("content", "")
            if len(str(content).encode("utf-8", errors="replace")) > _MAX_CONTENT_BYTES:
                return {"error": f"Content exceeds maximum allowed size ({_MAX_CONTENT_BYTES // 1024} KB)"}
            metadata = body.get("metadata", {})
            if not isinstance(metadata, dict):
                return {"error": "metadata must be a JSON object"}
            if len(metadata) > _MAX_METADATA_KEYS:
                return {"error": f"metadata exceeds maximum key count ({_MAX_METADATA_KEYS})"}
            import json as _json_mod
            _meta_size = len(_json_mod.dumps(metadata, default=str).encode("utf-8", errors="replace"))
            if _meta_size > _MAX_METADATA_BYTES:
                return {"error": f"metadata exceeds maximum allowed size ({_MAX_METADATA_BYTES // 1024} KB)"}
            entry = _v22_memory_system.store(mt, content, metadata)
            return {"status": "stored", "memory_type": type_str, "entry_id": entry.entry_id}

        @app.post("/v22/coala/memory/retrieve")
        def v22_coala_memory_retrieve_ep(body: dict):
            """Cross-retrieve from memory modules."""
            if not _v22_memory_system:
                return {"error": "Memory system not initialized"}
            query = body.get("query", "")
            results = _v22_memory_system.cross_retrieve(query)
            return {"query": query, "results": results}

        @app.get("/v22/coala/workspace/status")
        def v22_coala_workspace_status_ep():
            """Global Workspace Theory broadcast status."""
            if _v22_global_workspace:
                return _v22_global_workspace.status()
            return {"error": "Global workspace not initialized"}

        @app.post("/v22/coala/phi")
        def v22_coala_phi_ep(body: dict):
            """Compute IIT Φ metrics."""
            result = _compute_phi_v22(
                subsystem_connections=body.get("subsystem_connections", {}),
                subsystem_information=body.get("subsystem_information", {}),
            )
            return result.to_dict()

    # ── RepE Transparency ────────────────────────────────────────────
    if _repe_summary is not None:

        @app.get("/v22/repe/summary")
        def v22_repe_summary_ep():
            """Representation Engineering summary."""
            return _repe_summary()

        @app.post("/v22/repe/analyze")
        def v22_repe_analyze_ep(body: dict):
            """Analyze hidden states for concept activations."""
            result = _analyze_hidden_states(
                system_description=body.get("system_description", "system"),
                concept_scores=body.get("concept_scores", {}),
            )
            return result.to_dict()

        @app.post("/v22/repe/control-plan")
        def v22_repe_control_plan_ep(body: dict):
            """Generate a control plan from hidden state analysis."""
            profile = _analyze_hidden_states(
                system_description=body.get("system_description", "system"),
                concept_scores=body.get("concept_scores", {}),
            )
            plan = _generate_control_plan(
                profile=profile,
                target_alignment=body.get("target_alignment", 0.7),
            )
            return plan.to_dict()

        @app.post("/v22/repe/neural-signature")
        def v22_repe_neural_sig_ep(body: dict):
            """Compute neural signature for baseline monitoring."""
            profile = _analyze_hidden_states(
                system_description=body.get("system_description", "system"),
                concept_scores=body.get("concept_scores", {}),
            )
            result = _compute_neural_signature(
                profile=profile,
                baseline=body.get("baseline"),
            )
            return result.__dict__

    # ── MESIAS Governance ────────────────────────────────────────────
    if _mesias_summary is not None:

        @app.get("/v22/mesias/summary")
        def v22_mesias_summary_ep():
            """MESIAS governance framework summary."""
            return _mesias_summary()

        @app.post("/v22/mesias/ethics")
        def v22_mesias_ethics_ep(body: dict):
            """Evaluate ethical dimensions of a subject."""
            result = _evaluate_ethics(
                subject=body.get("subject", ""),
                dimension_scores=body.get("dimension_scores", {}),
            )
            return result.to_dict()

        @app.post("/v22/mesias/risk")
        def v22_mesias_risk_ep(body: dict):
            """Assess risk for an operation."""
            result = _assess_risk_v22(
                operation=body.get("operation", ""),
                impact=body.get("impact", 0.5),
                likelihood=body.get("likelihood", 0.3),
                existing_mitigations=body.get("mitigations", []),
            )
            return result.to_dict()

        @app.post("/v22/mesias/vsd")
        def v22_mesias_vsd_ep(body: dict):
            """Perform Value-Sensitive Design analysis."""
            result = _analyze_vsd(
                stakeholder_values=body.get("stakeholder_values", []),
            )
            return result.to_dict()

        @app.post("/v22/mesias/efficiency")
        def v22_mesias_efficiency_ep(body: dict):
            """Measure governance efficiency metrics."""
            result = _measure_efficiency(
                total_operations=body.get("total_operations", 100),
                governance_overhead_ms=body.get("governance_overhead_ms", 50.0),
                operation_time_ms=body.get("operation_time_ms", 200.0),
            )
            return result.to_dict()

        @app.get("/v22/mesias/governance/status")
        def v22_mesias_governance_status_ep():
            """Governance workspace status."""
            if _v22_gov_workspace:
                return _v22_gov_workspace.status()
            return {"error": "Governance workspace not initialized"}

    # ── Anti-Patterns ────────────────────────────────────────────────
    if _anti_patterns_summary is not None:

        @app.get("/v22/anti-patterns/summary")
        def v22_anti_patterns_summary_ep():
            """Anti-pattern detection summary."""
            return _anti_patterns_summary()

        @app.post("/v22/anti-patterns/scan")
        def v22_anti_patterns_scan_ep(body: dict):
            """Scan for all TRAP anti-patterns."""
            results = _scan_all_traps(body.get("indicators", []))
            return {k: v.__dict__ for k, v in results.items()}

        @app.post("/v22/anti-patterns/detect")
        def v22_anti_patterns_detect_ep(body: dict):
            """Detect a specific TRAP pattern."""
            from .anti_patterns import TrapType as _TrapType
            trap_str = body.get("trap_type", "bag_of_agents")
            try:
                tt = _TrapType(trap_str)
            except ValueError:
                tt = _TrapType.BAG_OF_AGENTS
            result = _detect_trap(
                trap_type=tt,
                observed_indicators=body.get("indicators", []),
            )
            return result.__dict__

        @app.post("/v22/anti-patterns/vibe-coding")
        def v22_vibe_coding_ep(body: dict):
            """Assess vibe-coding risk."""
            result = _assess_vibe_coding(
                project_description=body.get("project_description", "project"),
                ai_generated_ratio=body.get("ai_generated_ratio", 0.5),
                review_coverage=body.get("review_coverage", 0.5),
                test_coverage=body.get("test_coverage", 0.5),
                developer_experience_years=body.get("developer_experience_years", 3),
            )
            return result.to_dict()

        @app.post("/v22/anti-patterns/shadow-ai")
        def v22_shadow_ai_ep(body: dict):
            """Scan for shadow AI usage patterns."""
            result = _scan_for_shadow_ai(
                code_snippets=body.get("code_samples", []),
            )
            return result.__dict__

    # ── Runtime Protection ───────────────────────────────────────────
    if _runtime_protection_summary is not None:

        @app.get("/v22/runtime/summary")
        def v22_runtime_summary_ep():
            """Runtime protection summary."""
            return _runtime_protection_summary()

        @app.post("/v22/runtime/scan")
        def v22_runtime_scan_ep(body: dict):
            """Scan input for threats and respond."""
            results = _scan_and_respond(
                input_text=body.get("text", ""),
            )
            return [r.to_dict() for r in results]

        @app.post("/v22/runtime/headers")
        def v22_runtime_headers_ep(body: dict):
            """Validate security headers."""
            result = _validate_headers(body.get("headers", {}))
            return result.to_dict()

        @app.post("/v22/runtime/anomaly")
        def v22_runtime_anomaly_ep(body: dict):
            """Detect statistical anomaly in a metric."""
            result = _detect_anomaly(
                metric_name=body.get("metric_name", "unknown"),
                observed=body.get("observed", 0.0),
                historical_mean=body.get("historical_mean", 0.0),
                historical_std=body.get("historical_std", 1.0),
                threshold_sigmas=body.get("threshold_sigmas", 3.0),
            )
            return result.to_dict() if result else {"anomaly": False}

        @app.post("/v22/runtime/compliance")
        def v22_runtime_compliance_ep(body: dict):
            """Check compliance against a framework."""
            result = _check_compliance_v22(
                framework=body.get("framework", "SOC2"),
                control_statuses=body.get("control_statuses", {}),
            )
            return result.to_dict()

    # ── v22 Platform Health ──────────────────────────────────────────
    @app.get("/v22/health")
    def v22_health_ep():
        """v22 cognitive resilience architecture health check."""
        return {
            "reasoning_router": _router_summary is not None,
            "dsrp_ontology": _dsrp_summary is not None,
            "codes_resonance": _codes_summary is not None,
            "coala_architecture": _coala_summary is not None,
            "repe_transparency": _repe_summary is not None,
            "mesias_governance": _mesias_summary is not None,
            "anti_patterns": _anti_patterns_summary is not None,
            "runtime_protection": _runtime_protection_summary is not None,
        }

    # ── Journey Oracle Endpoints ─────────────────────────────────────
    from .journey import get_oracle as _get_journey_oracle, JourneyStage as _JourneyStage

    @app.post("/journey/create")
    def journey_create_ep(body: dict):
        """Create a new user journey."""
        user_id = body.get("user_id", "")
        query = body.get("query", "")
        if not user_id:
            raise _HTTPException(status_code=400, detail="user_id is required")
        oracle = _get_journey_oracle()
        jid = oracle.create_journey(user_id, query)
        return {"journey_id": jid}

    @app.post("/journey/advance")
    def journey_advance_ep(body: dict):
        """Advance a journey to a new stage."""
        journey_id = body.get("journey_id", "")
        stage_str = body.get("stage", "")
        metadata = body.get("metadata")
        if not journey_id:
            raise _HTTPException(status_code=400, detail="journey_id is required")
        try:
            stage = _JourneyStage(stage_str)
        except ValueError:
            valid = [s.value for s in _JourneyStage]
            raise _HTTPException(
                status_code=400,
                detail=f"Invalid stage '{stage_str}'. Valid stages: {valid}",
            )
        oracle = _get_journey_oracle()
        try:
            oracle.advance(journey_id, stage, metadata)
        except ValueError as exc:
            raise _HTTPException(status_code=400, detail=str(exc))
        return {"journey_id": journey_id, "stage": stage.value, "ok": True}

    @app.post("/journey/outcome")
    def journey_outcome_ep(body: dict):
        """Record a tool outcome and return drift signals."""
        journey_id = body.get("journey_id", "")
        tool_name = body.get("tool_name", "")
        satisfaction = float(body.get("satisfaction", 0.0))
        roi = float(body.get("roi", 0.0))
        if not journey_id:
            raise _HTTPException(status_code=400, detail="journey_id is required")
        if not tool_name:
            raise _HTTPException(status_code=400, detail="tool_name is required")
        oracle = _get_journey_oracle()
        try:
            oracle.record_outcome(journey_id, tool_name, satisfaction=satisfaction, roi=roi)
            signals = oracle.detect_drift(journey_id)
        except ValueError as exc:
            raise _HTTPException(status_code=400, detail=str(exc))
        return {
            "journey_id": journey_id,
            "drift_signals": [s.to_dict() for s in signals],
        }

    @app.get("/journey/summary")
    def journey_summary_ep():
        """Aggregate journey metrics dashboard."""
        oracle = _get_journey_oracle()
        return oracle.dashboard().to_dict()

    @app.get("/journey/{journey_id}")
    def journey_get_ep(journey_id: str):
        """Retrieve a single journey by ID."""
        oracle = _get_journey_oracle()
        state = oracle.get_journey(journey_id)
        if state is None:
            raise _HTTPException(status_code=400, detail=f"Journey {journey_id} not found")
        return state.to_dict()

    @app.post("/journey/{journey_id}/target")
    def journey_target_ep(journey_id: str, body: dict):
        """Set target vector for a tool at SELECTION stage."""
        tool_name = body.get("tool_name", "")
        if not tool_name:
            raise _HTTPException(status_code=400, detail="tool_name is required")
        from .journey import TargetScoreVector
        vector = TargetScoreVector(
            relevance=float(body.get("relevance", 0.0)),
            budget_fit=float(body.get("budget_fit", 0.0)),
            skill_fit=float(body.get("skill_fit", 0.0)),
            integration_ease=float(body.get("integration_ease", 0.0)),
        )
        oracle = _get_journey_oracle()
        try:
            oracle.set_target_vector(journey_id, tool_name, vector)
        except ValueError as exc:
            raise _HTTPException(status_code=400, detail=str(exc))
        return {"ok": True, "journey_id": journey_id, "tool": tool_name}

    @app.get("/journey/{journey_id}/drift")
    def journey_drift_ep(journey_id: str):
        """Get drift signals for a journey."""
        oracle = _get_journey_oracle()
        try:
            signals = oracle.detect_drift(journey_id)
        except ValueError as exc:
            raise _HTTPException(status_code=400, detail=str(exc))
        return {"journey_id": journey_id, "drift_signals": [s.to_dict() for s in signals]}

    @app.get("/journey/dashboard")
    def journey_dashboard_ep():
        """Aggregate journey dashboard with metrics."""
        oracle = _get_journey_oracle()
        return oracle.dashboard().to_dict()

    @app.get("/journey/{journey_id}/reservoir")
    def journey_reservoir_ep(journey_id: str):
        """Get LF reservoir state for tools in a journey."""
        oracle = _get_journey_oracle()
        state = oracle.get_journey(journey_id)
        if state is None:
            raise _HTTPException(status_code=400, detail=f"Journey {journey_id} not found")
        reservoirs = {}
        for tool_name in state.target_vectors:
            rstate = oracle.get_reservoir_state(tool_name)
            if rstate:
                reservoirs[tool_name] = rstate
        return {"journey_id": journey_id, "reservoirs": reservoirs}

    @app.post("/journey/apply-corrections")
    def journey_corrections_ep():
        """Apply MODERATE/SEVERE drift corrections to scoring."""
        oracle = _get_journey_oracle()
        corrections = oracle.apply_drift_corrections()
        return {"corrections": corrections, "count": len(corrections)}

    # ══════════════════════════════════════════════════════════════════
    # v25.6 — Scheduler, Provider Status, WebSocket, Pipeline
    # ══════════════════════════════════════════════════════════════════

    # ── Scheduler Endpoints ──
    try:
        from .scheduler import get_scheduler, setup_default_tasks
    except ImportError:
        try:
            from praxis.scheduler import get_scheduler, setup_default_tasks  # type: ignore[no-redef]
        except ImportError:
            get_scheduler = setup_default_tasks = None  # type: ignore

    if get_scheduler:
        _sched = get_scheduler()
        setup_default_tasks()

        # Register ingestion if enabled
        import os as _os_sched
        if _os_sched.environ.get("PRAXIS_INGESTION_ENABLED", "false").lower() == "true":
            try:
                from .ingestion_engine import run_daily_pipeline
                _ing_interval = int(_os_sched.environ.get("PRAXIS_INGESTION_INTERVAL", "604800"))
                _sched.schedule("ingestion", lambda: run_daily_pipeline(), _ing_interval)
            except ImportError:
                pass

        @app.on_event("startup")
        async def _startup_scheduler():
            _sched.start()
            # Set WS event loop
            try:
                from .ws import get_hub
                import asyncio
                get_hub().set_event_loop(asyncio.get_running_loop())
            except Exception:
                pass

        @app.on_event("shutdown")
        async def _shutdown_scheduler():
            _sched.stop()

        @app.get("/scheduler/status")
        def scheduler_status_ep():
            return _sched.status()

        @app.post("/scheduler/trigger/{task_name}")
        def scheduler_trigger_ep(task_name: str):
            ok = _sched.trigger(task_name)
            if not ok:
                raise _HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
            return {"triggered": task_name, "ok": True}

        @app.post("/scheduler/pause/{task_name}")
        def scheduler_pause_ep(task_name: str):
            return {"paused": _sched.pause(task_name)}

        @app.post("/scheduler/resume/{task_name}")
        def scheduler_resume_ep(task_name: str):
            return {"resumed": _sched.resume(task_name)}

    # ── Provider Status Endpoint ──
    @app.get("/providers/status")
    def providers_status_ep():
        import os as _os_ps
        dry_run = _os_ps.environ.get("PRAXIS_DRY_RUN", "true").lower() in ("true", "1", "yes")
        providers = {}
        for pname, env_key in [
            ("openai", "OPENAI_API_KEY"),
            ("anthropic", "ANTHROPIC_API_KEY"),
            ("google", "GOOGLE_API_KEY"),
            ("xai", "XAI_API_KEY"),
            ("deepseek", "PRAXIS_DEEPSEEK_API_KEY"),
            ("local", "LOCAL_LLM_URL"),
            ("litellm", "PRAXIS_LITELLM_API_KEY"),
        ]:
            api_key_set = bool(_os_ps.environ.get(env_key))
            sdk_installed = False
            try:
                if pname == "openai":
                    import openai; sdk_installed = True
                elif pname == "anthropic":
                    import anthropic; sdk_installed = True
                elif pname == "google":
                    import google.generativeai; sdk_installed = True
                elif pname == "litellm":
                    import litellm; sdk_installed = True
                else:
                    sdk_installed = True  # HTTP-based, no SDK needed
            except ImportError:
                pass

            circuit_state = "closed"
            try:
                from .llm_resilience import get_provider_health
                h = get_provider_health(pname)
                circuit_state = h.get("circuit_state", "closed").lower()
            except Exception:
                pass

            providers[pname] = {
                "available": sdk_installed and (api_key_set or pname == "local") and not dry_run,
                "sdk_installed": sdk_installed,
                "api_key_set": api_key_set,
                "dry_run": dry_run,
                "circuit_state": circuit_state,
            }
        return providers

    # ── WebSocket Endpoints ──
    try:
        from .ws import get_hub as _get_ws_hub
        from fastapi import WebSocket as _WS_Type
        from starlette.websockets import WebSocketDisconnect as _WSDisconnect

        _ws_hub = _get_ws_hub()

        @app.websocket("/ws/{channel}")
        async def websocket_endpoint(websocket: _WS_Type, channel: str):
            await websocket.accept()
            await _ws_hub.subscribe(channel, websocket)
            try:
                while True:
                    await websocket.receive_text()
            except _WSDisconnect:
                await _ws_hub.unsubscribe(channel, websocket)
            except Exception:
                await _ws_hub.unsubscribe(channel, websocket)

        @app.get("/ws/status")
        def ws_status_ep():
            return _ws_hub.status()

    except ImportError:
        pass

    # ── Pipeline Endpoints ──
    try:
        from .ingestion_engine import (
            run_daily_pipeline as _run_pipeline,
            get_review_queue as _get_review_queue,
            approve_tool as _approve_tool,
            reject_tool as _reject_tool,
        )
        _PIPELINE_OK = True
    except ImportError:
        try:
            from praxis.ingestion_engine import (  # type: ignore[no-redef]
                run_daily_pipeline as _run_pipeline,
                get_review_queue as _get_review_queue,
                approve_tool as _approve_tool,
                reject_tool as _reject_tool,
            )
            _PIPELINE_OK = True
        except ImportError:
            _PIPELINE_OK = False

    if _PIPELINE_OK:
        @app.get("/pipeline/status")
        def pipeline_status_ep():
            queue = _get_review_queue()
            sched_status = _sched.status() if get_scheduler else {}
            ing_status = sched_status.get("ingestion", {})
            return {
                "queue_size": len(queue) if queue else 0,
                "next_run": ing_status.get("next_run"),
                "last_run": ing_status.get("last_run"),
                "last_error": ing_status.get("last_error"),
                "run_count": ing_status.get("run_count", 0),
            }

        @app.post("/pipeline/trigger")
        def pipeline_trigger_ep():
            try:
                result = _run_pipeline()
                try:
                    _get_ws_hub().publish("pipeline", {"event": "cycle_complete", **result})
                except Exception:
                    pass
                return result
            except Exception as exc:
                raise _HTTPException(status_code=500, detail=str(exc))

        @app.get("/pipeline/queue")
        def pipeline_queue_ep():
            queue = _get_review_queue()
            return {"queue": [t.to_dict() if hasattr(t, 'to_dict') else str(t) for t in (queue or [])]}

        @app.post("/pipeline/approve/{tool_name}")
        def pipeline_approve_ep(tool_name: str):
            try:
                _approve_tool(tool_name)
                try:
                    _get_ws_hub().publish("pipeline", {"event": "tool_approved", "name": tool_name})
                except Exception:
                    pass
                return {"approved": tool_name, "ok": True}
            except Exception as exc:
                raise _HTTPException(status_code=400, detail=str(exc))

        @app.post("/pipeline/reject/{tool_name}")
        def pipeline_reject_ep(tool_name: str, body: dict = None):
            reason = (body or {}).get("reason", "")
            try:
                _reject_tool(tool_name)
                return {"rejected": tool_name, "reason": reason, "ok": True}
            except Exception as exc:
                raise _HTTPException(status_code=400, detail=str(exc))

    # ── Structured Feedback Collection ──────────────────────────────
    try:
        from .feedback_db import init_db as _fb_init, record_search_feedback as _fb_search, record_tool_feedback as _fb_tool, record_event as _fb_event, get_stats as _fb_stats, record_page_view as _fb_pv, get_page_view_stats as _fb_pv_stats
        _FB_OK = True
    except ImportError:
        try:
            from praxis.feedback_db import init_db as _fb_init, record_search_feedback as _fb_search, record_tool_feedback as _fb_tool, record_event as _fb_event, get_stats as _fb_stats, record_page_view as _fb_pv, get_page_view_stats as _fb_pv_stats  # type: ignore[no-redef]
            _FB_OK = True
        except ImportError:
            _FB_OK = False

    if _FB_OK:
        _fb_init()

        from enum import Enum as _Enum

        class _RatingEnum(str, _Enum):
            up = 'up'
            down = 'down'

        class _FlagEnum(str, _Enum):
            wrong_tier = 'wrong_tier'
            wrong_score = 'wrong_score'
            outdated_info = 'outdated_info'
            missing_badge = 'missing_badge'
            other = 'other'

        class _SearchFBReq(BaseModel):
            session_id: str = Field(max_length=100)
            query_text: str = Field(max_length=2000)
            constraints: Optional[list] = None
            survivors: Optional[list] = None
            eliminated_count: Optional[int] = None
            rating: Optional[_RatingEnum] = None
            comment: Optional[str] = Field(None, max_length=1000)

        class _ToolFBReq(BaseModel):
            session_id: str = Field(max_length=100)
            tool_name: str = Field(max_length=200)
            current_tier: str = Field(max_length=50)
            suggested_tier: Optional[str] = Field(None, max_length=50)
            flag_type: Optional[_FlagEnum] = None
            reason: Optional[str] = Field(None, max_length=1000)

        class _EventReq(BaseModel):
            session_id: str = Field(max_length=100)
            event_type: str = Field(max_length=100)
            payload: Optional[dict] = None

        @app.post("/feedback/search")
        def submit_search_feedback(req: _SearchFBReq):
            import json as _j
            row_id = _fb_search(
                req.session_id, req.query_text,
                _j.dumps(req.constraints) if req.constraints else None,
                _j.dumps(req.survivors) if req.survivors else None,
                req.eliminated_count, req.rating, req.comment,
            )
            return {"id": row_id, "status": "recorded"}

        @app.post("/feedback/tool")
        def submit_tool_feedback(req: _ToolFBReq):
            row_id = _fb_tool(
                req.session_id, req.tool_name, req.current_tier,
                req.suggested_tier, req.flag_type, req.reason,
            )
            return {"id": row_id, "status": "recorded"}

        @app.post("/feedback/event")
        def submit_event(req: _EventReq):
            import json as _j
            _fb_event(req.session_id, req.event_type, _j.dumps(req.payload) if req.payload else None)
            return {"status": "recorded"}

        @app.get("/feedback/stats")
        def feedback_stats_ep():
            return _fb_stats()

        @app.get("/feedback/dashboard")
        def feedback_dashboard():
            from fastapi.responses import HTMLResponse
            try:
                from .feedback_db import get_dashboard_data as _fb_dash
            except ImportError:
                from praxis.feedback_db import get_dashboard_data as _fb_dash  # type: ignore[no-redef]
            try:
                from .feedback_dashboard import render_dashboard as _fb_render
            except ImportError:
                from praxis.feedback_dashboard import render_dashboard as _fb_render  # type: ignore[no-redef]
            data = _fb_dash()
            return HTMLResponse(content=_fb_render(data))

        @app.get("/feedback/analytics")
        def feedback_analytics():
            return _fb_pv_stats()

        # ── Page view tracking middleware ──
        # Records every HTML page load (not API calls, not static assets)
        _PAGE_PATHS = {"/", "/journey", "/room", "/tools-app", "/advisor", "/privacy-policy", "/terms-of-service"}
        _STATIC_PAGES = {".html"}

        from starlette.middleware.base import BaseHTTPMiddleware as _PVMiddleware
        from starlette.requests import Request as _PVRequest

        class _PageViewMiddleware(_PVMiddleware):
            async def dispatch(self, request: _PVRequest, call_next):
                response = await call_next(request)
                try:
                    path = request.url.path
                    is_page = path in _PAGE_PATHS or (
                        path.startswith("/static/") and any(path.endswith(ext) for ext in _STATIC_PAGES)
                    )
                    if is_page and response.status_code == 200:
                        ref = request.headers.get("referer", "")
                        ua = (request.headers.get("user-agent", ""))[:200]
                        _fb_pv(path, ref or None, ua or None)
                except Exception:
                    pass
                return response

        app.add_middleware(_PageViewMiddleware)

    return app


# ======================================================================
# Module-level app instance
# ======================================================================

if FASTAPI_AVAILABLE:
    app = create_app()
else:
    app = None
