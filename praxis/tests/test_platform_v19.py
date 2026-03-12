"""
Tests for v19 Platform Evolution modules:
    connectors, workflow_engine, marketplace, contributions, agent_sdk, governance
"""
import asyncio
import time

# ═══════════════════════════════════════════════════════════
#  Connectors
# ═══════════════════════════════════════════════════════════
from praxis.connectors import (
    get_registry, execute_connector, list_connectors,
    ConnectorRegistry, ConnectorSpec,
)


def test_connector_registry_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2
    assert isinstance(r1, ConnectorRegistry)


def test_list_connectors_returns_all():
    connectors = list_connectors()
    assert isinstance(connectors, list)
    assert len(connectors) >= 5  # 5 built-in stubs
    names = [c["id"] for c in connectors]
    for expected in ["slack", "openai", "google_sheets", "salesforce", "zapier"]:
        assert expected in names


def test_connector_spec_fields():
    connectors = list_connectors()
    for c in connectors:
        assert "id" in c
        assert "display_name" in c
        assert "actions" in c
        assert isinstance(c["actions"], list)


def test_execute_connector_dry_run():
    result = asyncio.run(execute_connector(
        "slack", action="send_message",
        params={"channel": "#test", "text": "hello"},
        dry_run=True,
    ))
    assert result.success is True
    assert result.dry_run is True
    assert isinstance(result.data, dict)


def test_execute_connector_unknown():
    result = asyncio.run(execute_connector(
        "nonexistent_connector", action="do_something",
        params={}, dry_run=True,
    ))
    assert result.success is False
    assert result.error


# ═══════════════════════════════════════════════════════════
#  Workflow Engine
# ═══════════════════════════════════════════════════════════
from praxis.workflow_engine import (
    decompose_request, generate_plan, execute_plan, assemble_and_run,
    SubTask, WorkflowPlan,
)


def test_decompose_request_basic():
    tasks = decompose_request("Send a Slack message when a new lead arrives in Salesforce")
    assert isinstance(tasks, list)
    assert len(tasks) >= 1
    for t in tasks:
        assert isinstance(t, SubTask)
        assert t.description


def test_decompose_request_keywords():
    tasks = decompose_request("Find a tool under $50 per month for CRM")
    # Should have keywords extracted
    assert any(len(t.keywords) > 0 for t in tasks)


def test_generate_plan_returns_dag():
    plan = generate_plan("Automate email marketing for my restaurant")
    assert isinstance(plan, WorkflowPlan)
    assert plan.id
    assert isinstance(plan.steps, list)
    d = plan.to_dict()
    assert "id" in d
    assert "steps" in d


def test_execute_plan_dry_run():
    plan = generate_plan("Send weekly sales reports via Slack")
    result = asyncio.run(execute_plan(plan, secrets={}, dry_run=True))
    assert result.plan_id == plan.id
    assert isinstance(result.step_results, list)
    d = result.to_dict()
    assert "success" in d


def test_assemble_and_run():
    result = asyncio.run(assemble_and_run(
        "Notify team on Slack about new CRM leads",
        secrets={}, dry_run=True,
    ))
    assert isinstance(result, dict)
    assert "plan" in result
    assert "result" in result


# ═══════════════════════════════════════════════════════════
#  Marketplace
# ═══════════════════════════════════════════════════════════
from praxis.marketplace import (
    publish_template, get_template, list_templates, download_template,
    unpublish_template, feature_template, add_review, get_reviews,
    marketplace_stats,
)


def _publish_test_template():
    tpl = publish_template(
        name="Test Workflow Template",
        description="A test template for unit tests",
        plan_json={"steps": [{"tool": "pytest", "action": "run_tests"}]},
        author="test_user",
        category="testing",
        tags=["test", "ci"],
    )
    return tpl.to_dict()


def test_publish_and_get_template():
    t = _publish_test_template()
    assert t["name"] == "Test Workflow Template"
    tid = t["template_id"]
    loaded = get_template(tid)
    assert loaded is not None
    assert loaded["template_id"] == tid


def test_list_templates_pagination():
    _publish_test_template()
    result = list_templates(limit=5)
    assert "items" in result
    assert "total" in result
    assert isinstance(result["items"], list)


def test_download_template_increments():
    t = _publish_test_template()
    tid = t["template_id"]
    download_template(tid)
    loaded = get_template(tid)
    assert loaded["download_count"] >= 1


def test_add_review_and_get():
    t = _publish_test_template()
    tid = t["template_id"]
    rev = add_review(tid, rating=4, comment="Great template!", author="tester")
    assert rev.rating == 4
    reviews = get_reviews(tid)
    assert isinstance(reviews, list)
    assert len(reviews) >= 1


def test_feature_template():
    t = _publish_test_template()
    tid = t["template_id"]
    result = feature_template(tid)
    assert result is True
    loaded = get_template(tid)
    assert loaded["featured"] is True


def test_unpublish_template():
    t = _publish_test_template()
    tid = t["template_id"]
    result = unpublish_template(tid)
    assert result is True


def test_marketplace_stats():
    _publish_test_template()
    stats = marketplace_stats()
    assert "total_templates" in stats
    assert stats["total_templates"] >= 1


# ═══════════════════════════════════════════════════════════
#  Contributions
# ═══════════════════════════════════════════════════════════
from praxis.contributions import (
    submit_tool, get_submission, list_submissions,
    approve_submission, reject_submission, request_changes,
    get_contributor, get_leaderboard,
)


def test_submit_tool_creates_submission():
    result = submit_tool(
        "TestToolX",
        "A test tool for unit testing",
        ["testing"],
        url="https://example.com/testtoolx",
        tags=["unit-test"],
        contributor="test_contributor",
    )
    assert "submission_id" in result
    assert "status" in result


def test_get_submission():
    result = submit_tool(
        "TestToolY", "Another test tool", ["testing"],
        url="https://example.com/testtooly",
        contributor="contributor_y",
    )
    sid = result["submission_id"]
    loaded = get_submission(sid)
    assert loaded is not None
    assert loaded["submission_id"] == sid


def test_list_submissions():
    submit_tool("TestToolZ", "Z tool", ["testing"],
                url="https://z.com", contributor="z_contributor")
    result = list_submissions(limit=10)
    assert isinstance(result, dict)
    assert "items" in result
    assert len(result["items"]) >= 1


def test_approve_submission():
    result = submit_tool(
        "ApprovableToolTest", "Good tool", ["productivity"],
        url="https://example.com/approvable",
        tags=["test"],
        contributor="good_contributor",
    )
    sid = result["submission_id"]
    approved = approve_submission(sid, reviewer_notes="Looks good")
    assert approved.get("status") == "approved"


def test_reject_submission():
    result = submit_tool(
        "RejectableToolTest", "Bad tool", ["testing"],
        url="https://example.com/rejectable",
        contributor="bad_contributor",
    )
    sid = result["submission_id"]
    rejected = reject_submission(sid, reason="Duplicate")
    assert rejected.get("status") == "rejected"


def test_request_changes():
    result = submit_tool(
        "ChangeableToolTest", "Needs work", ["testing"],
        url="https://example.com/changeable",
        contributor="change_contributor",
    )
    sid = result["submission_id"]
    changed = request_changes(sid, "Needs better description")
    assert changed.get("status") == "changes_requested"


def test_contributor_profile():
    submit_tool("ContribTestTool", "A tool", ["testing"],
                url="https://example.com/contribtool",
                contributor="prof_test_user")
    c = get_contributor("prof_test_user")
    assert c is not None
    assert c["display_name"] == "prof_test_user"


def test_leaderboard():
    board = get_leaderboard(limit=10)
    assert isinstance(board, list)


# ═══════════════════════════════════════════════════════════
#  Agent SDK
# ═══════════════════════════════════════════════════════════
from praxis.agent_sdk import (
    create_session, sdk_discover, sdk_plan, sdk_execute,
    handle_tool_call, get_tool_schema, sdk_info,
)


def test_sdk_info():
    info = sdk_info()
    assert "sdk_version" in info
    assert "capabilities" in info


def test_create_session():
    session = create_session()
    assert "session_id" in session
    assert session["session_id"]


def test_sdk_discover():
    result = sdk_discover("email marketing automation", top_n=3)
    assert "results" in result
    assert isinstance(result["results"], list)


def test_sdk_discover_with_session():
    session = create_session()
    sid = session["session_id"]
    result = sdk_discover("CRM for small business", top_n=3, session_id=sid)
    assert "results" in result


def test_sdk_plan():
    result = sdk_plan("automate newsletter sending")
    assert "plan" in result


def test_sdk_execute_dry_run():
    plan_result = sdk_plan("send a Slack notification")
    plan_dict = plan_result.get("plan", {})
    result = asyncio.run(sdk_execute(plan_dict, dry_run=True))
    assert isinstance(result, dict)


def test_handle_tool_call_discover():
    result = handle_tool_call("discover", "project management")
    assert isinstance(result, dict)
    assert "results" in result


def test_handle_tool_call_unknown():
    result = handle_tool_call("nonexistent_action", "test")
    assert "error" in result


def test_get_tool_schema():
    schema = get_tool_schema()
    assert "function" in schema
    assert "type" in schema
    assert schema["type"] == "function"


# ═══════════════════════════════════════════════════════════
#  Governance
# ═══════════════════════════════════════════════════════════
from praxis.governance import (
    record_audit, get_audit_log, record_usage, get_usage,
    get_cost_summary, assess_compliance, create_policy,
    list_policies, check_tool_allowed, governance_dashboard,
    AuditAction,
)


def test_record_audit():
    entry = record_audit(AuditAction.TOOL_SEARCH, actor="tester",
                         team="engineering", details={"query": "CRM"})
    assert entry.action == AuditAction.TOOL_SEARCH
    assert entry.actor == "tester"


def test_get_audit_log():
    record_audit(AuditAction.CONFIG_CHANGED, actor="admin",
                 details={"key": "test"})
    entries = get_audit_log(limit=5)
    assert isinstance(entries, list)


def test_record_and_get_usage():
    record_usage("TestTool", "search", team="qa_team")
    record_usage("TestTool", "selection", team="qa_team")
    record_usage("TestTool", "workflow", team="qa_team", cost_usd=1.50)
    usage = get_usage(team="qa_team", tool_name="TestTool")
    assert len(usage) >= 1
    rec = usage[0]
    assert rec["search_count"] >= 1
    assert rec["selection_count"] >= 1
    assert rec["estimated_cost_usd"] >= 1.50


def test_get_cost_summary():
    record_usage("CostTestTool", "workflow", team="finance", cost_usd=25.00)
    summary = get_cost_summary(team="finance")
    assert summary["total_cost_usd"] >= 25.00
    assert "by_tool" in summary


def test_assess_compliance():
    result = assess_compliance(required_standards=["GDPR", "SOC2"])
    assert "required_standards" in result
    assert "total_tools" in result
    assert "compliant" in result


def test_create_and_list_policies():
    policy = create_policy(
        name="Block Risky Tool",
        rule_type="block_tool",
        conditions={"tools": ["RiskyToolABC"]},
        description="Block usage of RiskyToolABC",
    )
    assert policy["name"] == "Block Risky Tool"
    policies = list_policies()
    assert isinstance(policies, list)
    assert any(p["name"] == "Block Risky Tool" for p in policies)


def test_check_tool_allowed():
    create_policy(
        name="Block ForbiddenTool Test",
        rule_type="block_tool",
        conditions={"tools": ["ForbiddenToolTest"]},
    )
    result = check_tool_allowed("ForbiddenToolTest")
    assert result["allowed"] is False
    assert len(result["violations"]) >= 1


def test_check_tool_allowed_passes():
    result = check_tool_allowed("SomeSafeTool12345")
    assert result["allowed"] is True


def test_governance_dashboard():
    dashboard = governance_dashboard()
    assert "usage" in dashboard
    assert "cost_summary" in dashboard
    assert "compliance" in dashboard
    assert "active_policies" in dashboard
    assert "recent_audit" in dashboard
