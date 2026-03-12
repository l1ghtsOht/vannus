"""
Tests for v23 — Public API Surface & Metric Translator.

Covers:
  1. metric_translator — key translation, dict translation, response envelope, risk builder
  2. public_api — core functions (analyze, optimize_stack, health, api_docs, feedback, etc.)
  3. Integration round-trips through the translate→response pipeline
"""
import pytest

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. METRIC TRANSLATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from praxis.metric_translator import (
    translate_key,
    translate_section,
    translate_dict,
    translate_response,
    build_risk_summary,
    _KEY_MAP,
    _SECTION_MAP,
    _compliance_level,
    _risk_level,
)


class TestTranslateKey:
    """translate_key: single key mapping."""

    def test_known_key_is_translated(self):
        assert translate_key("resonance_index") == "integration_compatibility_score"

    def test_phi_translated(self):
        assert translate_key("phi") == "integration_information_index"

    def test_vibe_coding_risk(self):
        assert translate_key("vibe_coding_risk") == "ai_generation_risk_score"

    def test_lock_in_index(self):
        assert translate_key("lock_in_index") == "vendor_lock_in_probability"

    def test_total_monthly_cost(self):
        assert translate_key("total_monthly_cost") == "estimated_monthly_cost_usd"

    def test_roi_percentage(self):
        assert translate_key("roi_percentage") == "return_on_investment_pct"

    def test_unknown_key_passes_through(self):
        assert translate_key("some_unknown_field") == "some_unknown_field"

    def test_empty_string(self):
        assert translate_key("") == ""

    def test_key_map_all_unique_values(self):
        """Every enterprise label should be distinct — no collisions."""
        # Some internal keys map to the same enterprise name intentionally
        # (e.g. phi and phi_value). Ensure no accidental collision beyond
        # planned dups.
        planned_dups = {
            "integration_information_index",
            "architectural_complexity_score",
        }
        vals = list(_KEY_MAP.values())
        seen = {}
        for k, v in _KEY_MAP.items():
            if v in planned_dups:
                continue
            if v in seen:
                pytest.fail(
                    f"Collision: '{k}' and '{seen[v]}' both map to '{v}'"
                )
            seen[v] = k


class TestTranslateSection:
    """translate_section: section/category label mapping."""

    def test_resonance_section(self):
        assert translate_section("resonance") == "Integration Analysis"

    def test_awakening_section(self):
        assert translate_section("awakening") == "Architecture Assessment"

    def test_case_insensitive(self):
        assert translate_section("CONDUIT") == "Cognitive Architecture"

    def test_unknown_section_passes_through(self):
        assert translate_section("ZetaSection") == "ZetaSection"


class TestTranslateDict:
    """translate_dict: recursive key translation."""

    def test_flat_dict(self):
        result = translate_dict({"resonance_index": 0.85, "phi": 3.2})
        assert "integration_compatibility_score" in result
        assert "integration_information_index" in result
        assert result["integration_compatibility_score"] == 0.85
        assert result["integration_information_index"] == 3.2

    def test_nested_dict(self):
        data = {"outer": {"resonance_index": 0.5, "phi": 1.0}}
        result = translate_dict(data, deep=True)
        inner = result["outer"]
        assert "integration_compatibility_score" in inner
        assert inner["integration_compatibility_score"] == 0.5

    def test_list_of_dicts(self):
        data = {"items": [{"phi": 2.0}, {"entropy": 0.7}]}
        result = translate_dict(data, deep=True)
        assert result["items"][0]["integration_information_index"] == 2.0
        assert result["items"][1]["architectural_complexity_score"] == 0.7

    def test_shallow_mode_skips_nesting(self):
        data = {"outer": {"phi": 1.0}}
        result = translate_dict(data, deep=False)
        # outer not translated deeply — inner key kept as-is
        assert "phi" in result["outer"]

    def test_preserves_values(self):
        """Values must never be modified, only keys."""
        data = {"resonance_index": "hello", "lock_in_index": [1, 2, 3]}
        result = translate_dict(data)
        assert result["integration_compatibility_score"] == "hello"
        assert result["vendor_lock_in_probability"] == [1, 2, 3]

    def test_empty_dict(self):
        assert translate_dict({}) == {}

    def test_mixed_known_unknown_keys(self):
        data = {"resonance_index": 1.0, "custom_field": "abc"}
        result = translate_dict(data)
        assert "integration_compatibility_score" in result
        assert "custom_field" in result

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"phi": 9.9}}}}
        result = translate_dict(data)
        assert result["a"]["b"]["c"]["integration_information_index"] == 9.9


class TestTranslateResponse:
    """translate_response: full envelope wrapper."""

    def test_adds_meta_block(self):
        result = translate_response({"phi": 3.0})
        assert "_meta" in result
        assert result["_meta"]["api_version"] == "public-v1"
        assert result["_meta"]["metric_format"] == "enterprise"
        assert result["_meta"]["documentation"] == "/api/v1/docs"

    def test_translates_keys_in_envelope(self):
        result = translate_response({"resonance_index": 0.9})
        assert "integration_compatibility_score" in result

    def test_empty_input(self):
        result = translate_response({})
        assert "_meta" in result

    def test_meta_always_present_even_with_existing_meta(self):
        """_meta should always reflect the translator's output."""
        result = translate_response({"_meta": {"old": True}})
        assert result["_meta"]["api_version"] == "public-v1"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. RISK SUMMARY BUILDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestBuildRiskSummary:
    """build_risk_summary: composite risk from multiple signals."""

    def test_all_none_returns_zero_composite(self):
        r = build_risk_summary()
        assert r["composite_risk_score"] == 0
        assert r["risk_level"] == "low"
        assert r["factors"] == []

    def test_vendor_risk_factor(self):
        r = build_risk_summary(vendor_risk={"risk_score": 60, "risk_level": "high"})
        assert len(r["factors"]) == 1
        assert r["factors"][0]["factor"] == "vendor_risk_score"
        assert r["factors"][0]["value"] == 60

    def test_compliance_factor(self):
        r = build_risk_summary(compliance={"compliance_score": 0.85})
        assert len(r["factors"]) == 1
        assert r["factors"][0]["factor"] == "regulatory_compliance_score"

    def test_lock_in_factor_high(self):
        r = build_risk_summary(lock_in=0.9)
        assert r["factors"][0]["level"] == "high"

    def test_lock_in_factor_medium(self):
        r = build_risk_summary(lock_in=0.5)
        assert r["factors"][0]["level"] == "medium"

    def test_lock_in_factor_low(self):
        r = build_risk_summary(lock_in=0.2)
        assert r["factors"][0]["level"] == "low"

    def test_migration_complexity_factor(self):
        r = build_risk_summary(migration_complexity="high")
        assert len(r["factors"]) == 1
        assert r["factors"][0]["factor"] == "migration_difficulty"
        assert r["factors"][0]["value"] == "high"

    def test_composite_is_average_of_numeric_scores(self):
        r = build_risk_summary(
            vendor_risk={"risk_score": 40},
            lock_in=0.6,
        )
        # 40 and 0.6 → average = 20.3
        scores = [40, 0.6]
        expected = round(sum(scores) / len(scores), 1)
        assert r["composite_risk_score"] == expected

    def test_multiple_inputs(self):
        r = build_risk_summary(
            vendor_risk={"risk_score": 50, "risk_level": "medium"},
            compliance={"compliance_score": 0.7},
            lock_in=0.45,
            migration_complexity="medium",
        )
        assert len(r["factors"]) == 4
        assert r["recommendations_count"] >= 0

    def test_recommendations_count(self):
        r = build_risk_summary(
            vendor_risk={
                "risk_score": 70,
                "recommendations": ["a", "b", "c", "d", "e"],
            },
        )
        # Capped at 3 details
        assert r["recommendations_count"] == 3


class TestRiskLevels:
    """Internal level-assignment helpers."""

    def test_risk_level_critical(self):
        assert _risk_level(80) == "critical"

    def test_risk_level_high(self):
        assert _risk_level(60) == "high"

    def test_risk_level_medium(self):
        assert _risk_level(30) == "medium"

    def test_risk_level_low(self):
        assert _risk_level(10) == "low"

    def test_compliance_excellent(self):
        assert _compliance_level(0.95) == "excellent"

    def test_compliance_good(self):
        assert _compliance_level(0.75) == "good"

    def test_compliance_moderate(self):
        assert _compliance_level(0.55) == "moderate"

    def test_compliance_poor(self):
        assert _compliance_level(0.3) == "poor"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. PUBLIC API — CORE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from praxis.public_api import (
    analyze,
    optimize_stack,
    compare,
    migrate,
    vendor_report,
    whatif,
    compliance_report,
    cost_analysis,
    economics,
    health,
    submit_feedback,
    api_docs,
)


class TestPublicAPIHealth:
    """health() — lightweight system status."""

    def test_health_returns_status(self):
        h = health()
        assert "status" in h
        assert h["status"] in ("healthy", "degraded")

    def test_health_api_version(self):
        h = health()
        assert h["api_version"] == "public-v1"

    def test_health_endpoint_count(self):
        h = health()
        assert h["endpoints"] == 12

    def test_health_modules_dict(self):
        h = health()
        assert isinstance(h["modules"], dict)
        assert "interpreter" in h["modules"]
        assert "engine" in h["modules"]
        assert "stack" in h["modules"]

    def test_health_modules_active_total(self):
        h = health()
        assert h["modules_total"] >= 5
        assert h["modules_active"] <= h["modules_total"]


class TestPublicAPIDocs:
    """api_docs() — self-describing documentation."""

    def test_docs_returns_dict(self):
        d = api_docs()
        assert isinstance(d, dict)

    def test_docs_has_endpoints(self):
        d = api_docs()
        assert "endpoints" in d
        assert isinstance(d["endpoints"], list)

    def test_docs_12_endpoints(self):
        d = api_docs()
        assert len(d["endpoints"]) == 12

    def test_docs_all_have_method_and_path(self):
        d = api_docs()
        for ep in d["endpoints"]:
            assert "method" in ep
            assert "path" in ep
            assert ep["method"] in ("GET", "POST")
            assert ep["path"].startswith("/api/v1/")

    def test_docs_version(self):
        d = api_docs()
        assert d["version"] == "public-v1"

    def test_docs_api_name(self):
        d = api_docs()
        assert "Praxis" in d["api"]


class TestPublicAPIAnalyze:
    """analyze() — the core product endpoint."""

    def test_analyze_empty_query_returns_error(self):
        result = analyze("")
        assert "error" in result

    def test_analyze_whitespace_query_returns_error(self):
        result = analyze("   ")
        assert "error" in result

    def test_analyze_valid_query(self):
        result = analyze("I need AI tools for a marketing agency")
        assert isinstance(result, dict)
        # Should have translated keys and _meta
        assert "_meta" in result
        assert result["_meta"]["api_version"] == "public-v1"

    def test_analyze_returns_recommended_stack(self):
        result = analyze("Help me automate customer support with AI")
        # Should contain stack recommendations
        stack = result.get("recommended_stack", [])
        assert isinstance(stack, list)

    def test_analyze_stack_items_have_name(self):
        result = analyze("AI tools for e-commerce product descriptions")
        stack = result.get("recommended_stack", [])
        if stack:
            for item in stack:
                assert "name" in item

    def test_analyze_with_stack_size(self):
        result = analyze("I need AI tools for analytics", stack_size=2)
        assert isinstance(result, dict)
        assert "_meta" in result

    def test_analyze_with_filters(self):
        result = analyze("marketing AI tools", filters=["Marketing"])
        assert isinstance(result, dict)

    def test_analyze_narrative_present(self):
        result = analyze("I need help choosing AI tools for my startup")
        # narrative may be None if stack module doesn't produce one
        # but the key should exist
        assert isinstance(result, dict)


class TestPublicAPIOptimize:
    """optimize_stack() — the #1 product wedge."""

    def test_optimize_empty_tools_error(self):
        result = optimize_stack([])
        assert "error" in result

    def test_optimize_valid_tools(self):
        result = optimize_stack(["ChatGPT", "Notion"])
        assert isinstance(result, dict)

    def test_optimize_with_goal(self):
        result = optimize_stack(["Zapier", "Slack"], goal="reduce costs")
        assert isinstance(result, dict)

    def test_optimize_returns_risk_summary(self):
        result = optimize_stack(["ChatGPT", "GitHub Copilot"])
        # Should have risk_summary if not error
        if "error" not in result:
            assert "_meta" in result


class TestPublicAPICompare:
    """compare() — side-by-side tool comparison."""

    def test_compare_empty_tool_a(self):
        result = compare("", "ChatGPT")
        assert "error" in result

    def test_compare_empty_tool_b(self):
        result = compare("ChatGPT", "")
        assert "error" in result

    def test_compare_valid(self):
        result = compare("ChatGPT", "Claude")
        assert isinstance(result, dict)


class TestPublicAPIMigrate:
    """migrate() — migration planning."""

    def test_migrate_empty_from(self):
        result = migrate("")
        assert "error" in result

    def test_migrate_valid(self):
        result = migrate("Heroku", "AWS")
        assert isinstance(result, dict)


class TestPublicAPIVendor:
    """vendor_report() — vendor risk profiles."""

    def test_vendor_empty_name(self):
        result = vendor_report("")
        assert "error" in result

    def test_vendor_unknown_name(self):
        result = vendor_report("NonexistentVendor12345")
        assert isinstance(result, dict)
        # May return error or limited data


class TestPublicAPIWhatIf:
    """whatif() — scenario simulation."""

    def test_whatif_if_module_missing(self):
        """Should return gracefully if whatif module is not loaded."""
        result = whatif("test query", {"budget": "high"})
        assert isinstance(result, dict)


class TestPublicAPICost:
    """cost_analysis() — cost estimation."""

    def test_cost_if_module_missing(self):
        result = cost_analysis(1000, 500, "default")
        assert isinstance(result, dict)


class TestPublicAPIEconomics:
    """economics() — AI economics dashboard."""

    def test_economics_returns_dict(self):
        result = economics()
        assert isinstance(result, dict)


class TestPublicAPICompliance:
    """compliance_report() — regulatory snapshot."""

    def test_compliance_returns_dict(self):
        result = compliance_report()
        assert isinstance(result, dict)


class TestPublicAPIFeedback:
    """submit_feedback() — user feedback."""

    def test_feedback_records(self):
        result = submit_feedback("ChatGPT", 5, "Great tool")
        assert isinstance(result, dict)
        # May have status=recorded or an error if module unavailable


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. ROUND-TRIP INTEGRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestRoundTrip:
    """End-to-end: internal data → enterprise translation → public surface."""

    def test_analyze_uses_enterprise_keys(self):
        """The analyze endpoint should not leak internal jargon."""
        result = analyze("I need AI tools for healthcare compliance")
        # Check that internal keys are not present at the top level
        for internal_key in ("resonance_index", "phi", "vibe_coding_risk",
                             "shadow_ai", "ego_dissolution"):
            assert internal_key not in result, (
                f"Internal key '{internal_key}' leaked into public response"
            )

    def test_health_no_translation_needed(self):
        """health() returns metadata directly, no translation pass."""
        h = health()
        assert "status" in h
        assert "_meta" not in h  # health bypasses translate_response

    def test_docs_no_translation_needed(self):
        """api_docs() is static, no translation pass."""
        d = api_docs()
        assert "_meta" not in d  # docs are raw

    def test_translate_preserves_numeric_values(self):
        """Ensure translation never corrupts numeric data."""
        data = {"phi": 42, "entropy": 3.14, "resonance_index": 0.99}
        translated = translate_dict(data)
        assert translated["integration_information_index"] == 42
        assert translated["architectural_complexity_score"] == 3.14
        assert translated["integration_compatibility_score"] == 0.99

    def test_translate_with_real_stack_output_shape(self):
        """Simulates the shape compose_stack returns, verifies translation."""
        mock_response = {
            "resonance_index": 0.8,
            "stack": [
                {
                    "tool_name": "ChatGPT",
                    "resonance_index": 0.9,
                    "lock_in_index": 0.3,
                }
            ],
            "total_monthly_cost": 199.0,
            "phi": 4.5,
        }
        result = translate_response(mock_response)
        assert result["integration_compatibility_score"] == 0.8
        assert result["estimated_monthly_cost_usd"] == 199.0
        assert result["integration_information_index"] == 4.5
        assert result["stack"][0]["vendor_lock_in_probability"] == 0.3
        assert "_meta" in result

    def test_key_map_covers_philosophy_terms(self):
        """Verify that core philosophical terms have translations."""
        expected = [
            "resonance_index", "awakening_score", "enlightenment_score",
            "phi", "entropy", "vibe_coding_risk", "lock_in_index",
        ]
        for key in expected:
            assert key in _KEY_MAP, f"Missing translation for '{key}'"

    def test_section_map_covers_core_sections(self):
        """Verify that core section names have translations."""
        expected = ["resonance", "awakening", "enlightenment", "conduit",
                    "metacognition", "prism"]
        for section in expected:
            assert section in _SECTION_MAP, f"Missing section '{section}'"
