"""
v21 — Enterprise Cognitive Interface Tests
Tests for: cognitive, observability, knowledge_graph, compliance, ai_economics, vendor_risk
"""
import time
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# cognitive.py
# ---------------------------------------------------------------------------
from cognitive import (
    GlobalWorkspace,
    get_workspace,
    AgentInteraction,
    compute_phi,
    compute_structural_entropy,
    entropy_reduction_plan,
    cognitive_summary,
    BroadcastEvent,
    AgentModule,
)


class TestGlobalWorkspace:
    def setup_method(self):
        self.ws = GlobalWorkspace()

    def test_register_and_list_agents(self):
        a1 = AgentModule(agent_id="a1", role="planner")
        a2 = AgentModule(agent_id="a2", role="executor")
        self.ws.register_agent(a1)
        self.ws.register_agent(a2)
        agents = self.ws.list_agents()
        assert len(agents) == 2
        ids = {a["agent_id"] for a in agents}
        assert ids == {"a1", "a2"}

    def test_register_duplicate_returns_false(self):
        a1 = AgentModule(agent_id="a1", role="planner")
        assert self.ws.register_agent(a1) is True
        a1b = AgentModule(agent_id="a1", role="critic")
        assert self.ws.register_agent(a1b) is False
        agents = self.ws.list_agents()
        assert len(agents) == 1
        assert agents[0]["role"] == "planner"

    def test_unregister_agent(self):
        a1 = AgentModule(agent_id="a1", role="planner")
        self.ws.register_agent(a1)
        assert self.ws.unregister_agent("a1") is True
        assert len(self.ws.list_agents()) == 0

    def test_unregister_nonexistent_returns_false(self):
        assert self.ws.unregister_agent("nonexistent") is False

    def test_heartbeat_updates_timestamp(self):
        a1 = AgentModule(agent_id="a1", role="x")
        self.ws.register_agent(a1)
        old_hb = a1.last_heartbeat
        time.sleep(0.01)
        self.ws.heartbeat("a1")
        agents = self.ws.list_agents()
        assert agents[0]["last_heartbeat"] >= old_hb

    def test_submit_broadcast(self):
        a1 = AgentModule(agent_id="a1", role="x")
        self.ws.register_agent(a1)
        evt = BroadcastEvent(agent_id="a1", event_type="alert", priority=0.9, payload={"msg": "hi"})
        assert self.ws.submit_broadcast(evt) is True
        state = self.ws.workspace_state()
        assert state["pending_broadcasts"] >= 1

    def test_submit_broadcast_increments_count(self):
        a1 = AgentModule(agent_id="a1", role="x")
        self.ws.register_agent(a1)
        e1 = BroadcastEvent(agent_id="a1", event_type="e1", priority=0.5)
        e2 = BroadcastEvent(agent_id="a1", event_type="e2", priority=0.5)
        self.ws.submit_broadcast(e1)
        self.ws.submit_broadcast(e2)
        state = self.ws.workspace_state()
        assert state["total_broadcasts_ever"] == 2

    def test_compete_for_spotlight(self):
        a1 = AgentModule(agent_id="a1", role="x")
        self.ws.register_agent(a1)
        for i in range(10):
            evt = BroadcastEvent(agent_id="a1", event_type=f"e{i}", priority=i / 10.0)
            self.ws.submit_broadcast(evt)
        spotlight = self.ws.compete_for_spotlight()
        assert len(spotlight) <= 5
        priorities = [s["priority"] for s in spotlight]
        assert priorities == sorted(priorities, reverse=True)

    def test_workspace_state_structure(self):
        state = self.ws.workspace_state()
        assert "agents_registered" in state
        assert "pending_broadcasts" in state
        assert "spotlight" in state
        assert "history_size" in state

    def test_broadcast_queue_bounded(self):
        a1 = AgentModule(agent_id="a1", role="x")
        self.ws.register_agent(a1)
        for i in range(600):
            evt = BroadcastEvent(agent_id="a1", event_type="e", priority=0.5)
            self.ws.submit_broadcast(evt)
        assert len(self.ws._broadcast_queue) <= 500


class TestBroadcastEvent:
    def test_to_dict(self):
        b = BroadcastEvent(agent_id="a1", event_type="test", priority=0.8, payload={"k": "v"})
        d = b.to_dict()
        assert d["agent_id"] == "a1"
        assert d["priority"] == 0.8
        assert "timestamp" in d


class TestAgentModule:
    def test_to_dict(self):
        a = AgentModule(agent_id="a1", role="planner")
        d = a.to_dict()
        assert d["role"] == "planner"
        assert d["status"] == "idle"


class TestComputePhi:
    def test_empty_interactions(self):
        result = compute_phi([])
        assert result["phi"] == 0.0

    def test_single_interaction(self):
        interactions = [
            AgentInteraction(source="a1", target="a2", tokens_exchanged=100,
                             messages_exchanged=5, mutual_information=0.5, latency_ms=50)
        ]
        result = compute_phi(interactions)
        assert "phi" in result
        assert "interpretation" in result
        assert "fragmentation_risk" in result

    def test_multiple_interactions(self):
        interactions = [
            AgentInteraction(source="a1", target="a2", tokens_exchanged=100,
                             messages_exchanged=10, mutual_information=0.8, latency_ms=50),
            AgentInteraction(source="a2", target="a3", tokens_exchanged=200,
                             messages_exchanged=15, mutual_information=0.6, latency_ms=30),
            AgentInteraction(source="a1", target="a3", tokens_exchanged=150,
                             messages_exchanged=8, mutual_information=0.7, latency_ms=40),
        ]
        result = compute_phi(interactions)
        assert result["phi"] >= 0
        assert result["agent_count"] == 3


class TestStructuralEntropy:
    def test_default_entropy(self):
        snap = compute_structural_entropy()
        assert snap.entropy_bits >= 0
        assert isinstance(snap.above_threshold, bool)

    def test_custom_values(self):
        snap = compute_structural_entropy(panel_count=10, widget_count=20, data_partitions=5)
        assert snap.panel_count == 10
        assert snap.widget_count == 20

    def test_high_entropy_triggers_threshold(self):
        snap = compute_structural_entropy(
            panel_count=50, widget_count=100, data_partitions=30,
            active_agents=20, pending_events=200, threshold=1.5
        )
        assert snap.above_threshold is True


class TestEntropyReductionPlan:
    def test_above_threshold_generates_actions(self):
        snap = compute_structural_entropy(
            panel_count=50, widget_count=100, data_partitions=30,
            active_agents=20, pending_events=200, threshold=1.0
        )
        plan = entropy_reduction_plan(snap)
        assert isinstance(plan, dict)
        assert plan["action_required"] is True

    def test_below_threshold_no_actions(self):
        snap = compute_structural_entropy(threshold=999.0)
        plan = entropy_reduction_plan(snap)
        assert plan["action_required"] is False


class TestCognitiveSummary:
    def test_returns_dict(self):
        result = cognitive_summary()
        assert "global_workspace" in result
        assert "structural_entropy" in result
        assert "entropy_reduction" in result


# ---------------------------------------------------------------------------
# observability.py
# ---------------------------------------------------------------------------
from observability import (
    Span,
    Trace,
    TraceCollector,
    get_collector,
    ReasoningNode,
    parse_chain_of_thought,
    TelemetryWindow,
    record_telemetry,
    telemetry_summary,
    observability_report,
)


class TestSpan:
    def test_defaults(self):
        s = Span()
        assert s.status == "in_progress"
        assert s.span_id is not None

    def test_finish_sets_duration(self):
        s = Span()
        time.sleep(0.01)
        s.finish()
        assert s.end_time is not None
        assert s.duration_ms >= 0

    def test_add_event(self):
        s = Span()
        s.add_event("test_event", {"k": "v"})
        assert len(s.events) == 1
        assert s.events[0]["name"] == "test_event"

    def test_to_dict(self):
        s = Span(operation="test_op", agent_id="a1")
        d = s.to_dict()
        assert d["operation"] == "test_op"


class TestTrace:
    def test_create_trace(self):
        t = Trace()
        assert t.root_span is None

    def test_add_span_sets_root(self):
        t = Trace()
        s = Span(operation="root_op")
        t.add_span(s)
        assert t.root_span is not None
        assert len(t.spans) == 1

    def test_add_child_span(self):
        t = Trace()
        root = Span(operation="root")
        t.add_span(root)
        child = Span(operation="child", parent_span_id=root.span_id)
        t.add_span(child)
        assert len(t.spans) == 2
        assert t.root_span.operation == "root"

    def test_to_dict(self):
        t = Trace(metadata={"ver": "1"})
        d = t.to_dict()
        assert d["metadata"]["ver"] == "1"

    def test_total_tokens(self):
        t = Trace()
        s1 = Span()
        s1.attributes = {"tokens": 100}
        t.add_span(s1)
        s2 = Span(parent_span_id=s1.span_id)
        s2.attributes = {"tokens": 200}
        t.add_span(s2)
        assert t.total_tokens() == 300


class TestTraceCollector:
    def test_create_and_get(self):
        tc = TraceCollector()
        trace = tc.create_trace()
        fetched = tc.get_trace(trace.trace_id)
        assert fetched is not None
        assert fetched["trace_id"] == trace.trace_id

    def test_list_traces(self):
        tc = TraceCollector()
        tc.create_trace()
        tc.create_trace()
        assert len(tc.list_traces()) == 2

    def test_stats(self):
        tc = TraceCollector()
        tc.create_trace()
        stats = tc.stats()
        assert stats["total_traces"] == 1

    def test_bounded_size(self):
        tc = TraceCollector()
        tc.MAX_TRACES = 5
        for _ in range(10):
            tc.create_trace()
        assert len(tc._traces) <= 5


class TestReasoningNode:
    def test_add_child(self):
        root = ReasoningNode(label="root", content="q")
        child = ReasoningNode(label="step1", content="do thing", node_type="step")
        root.add_child(child)
        assert len(root.children) == 1

    def test_edit(self):
        n = ReasoningNode(label="step", content="original")
        n.edit("updated")
        assert n.content == "updated"
        assert n.edited is True
        assert n.original_content == "original"

    def test_flatten(self):
        root = ReasoningNode(label="root", content="q")
        c1 = ReasoningNode(label="step1", content="s1")
        c2 = ReasoningNode(label="step2", content="s2")
        root.add_child(c1)
        root.add_child(c2)
        flat = root.flatten()
        assert len(flat) == 3

    def test_to_dict(self):
        n = ReasoningNode(label="test", content="c", confidence=0.9)
        d = n.to_dict()
        assert d["confidence"] == 0.9


class TestParseChainOfThought:
    def test_basic_parse(self):
        text = "Step 1: Analyze query.\nStep 2: Find tools.\nConclusion: Use LangGraph."
        tree = parse_chain_of_thought(text, "test")
        assert tree.node_type == "root"
        assert len(tree.children) >= 2

    def test_parses_assumptions(self):
        text = "Step 1: Start.\nAssuming budget is $50K.\nConclusion: Done."
        tree = parse_chain_of_thought(text, "q")
        types = {c["node_type"] for c in tree.flatten()}
        assert "assumption" in types

    def test_parses_conclusions(self):
        text = "Step 1: Analyze.\nStep 2: Evaluate.\nConclusion: Implementation is ready."
        tree = parse_chain_of_thought(text, "q")
        types = {c["node_type"] for c in tree.flatten()}
        assert "conclusion" in types


class TestTelemetryWindow:
    def test_record_and_percentile(self):
        tw = TelemetryWindow()
        for i in range(100):
            tw.record(float(i))
        assert tw.percentile(50) == pytest.approx(49.5, abs=1)
        assert tw.percentile(99) >= 90

    def test_to_dict(self):
        tw = TelemetryWindow()
        tw.record(10.0)
        tw.record(20.0)
        d = tw.to_dict()
        assert "p50_ms" in d
        assert "p95_ms" in d
        assert "p99_ms" in d


class TestObservabilityReport:
    def test_returns_structure(self):
        report = observability_report()
        assert "tracing" in report
        assert "telemetry" in report


# ---------------------------------------------------------------------------
# knowledge_graph.py
# ---------------------------------------------------------------------------
from knowledge_graph import (
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    extract_entities,
    extract_relationships,
    build_graph_from_text,
    get_graph as get_kg,
    knowledge_graph_summary,
    Community,
)


class TestGraphNode:
    def test_to_dict(self):
        n = GraphNode(node_id="n1", label="Test", entity_type="concept")
        d = n.to_dict()
        assert d["node_id"] == "n1"
        assert d["entity_type"] == "concept"


class TestGraphEdge:
    def test_edge_id(self):
        e = GraphEdge(source="a", target="b", relation="related_to")
        assert "a" in e.edge_id and "b" in e.edge_id

    def test_to_dict(self):
        e = GraphEdge(source="a", target="b", relation="depends_on", weight=0.8)
        d = e.to_dict()
        assert d["weight"] == 0.8


class TestKnowledgeGraph:
    def setup_method(self):
        self.kg = KnowledgeGraph()

    def test_add_and_get_node(self):
        node = GraphNode(node_id="n1", label="Test Node", entity_type="concept")
        self.kg.add_node(node)
        result = self.kg.get_node("n1")
        assert result is not None
        assert result["label"] == "Test Node"

    def test_remove_node(self):
        node = GraphNode(node_id="n1", label="Test")
        self.kg.add_node(node)
        self.kg.remove_node("n1")
        assert self.kg.get_node("n1") is None

    def test_add_edge(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        edge = GraphEdge(source="a", target="b", relation="related_to")
        self.kg.add_edge(edge)
        edges = self.kg.get_edges("a")
        assert len(edges) == 1

    def test_node_count_and_edge_count(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        self.kg.add_edge(GraphEdge(source="a", target="b", relation="rel"))
        assert self.kg.node_count() == 2
        assert self.kg.edge_count() == 1

    def test_compute_centrality(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        self.kg.add_node(GraphNode(node_id="c", label="C"))
        self.kg.add_edge(GraphEdge(source="a", target="b", relation="r"))
        self.kg.add_edge(GraphEdge(source="a", target="c", relation="r"))
        centrality = self.kg.compute_centrality()
        assert centrality["a"] >= centrality["b"]

    def test_detect_communities(self):
        for i in range(6):
            self.kg.add_node(GraphNode(node_id=f"n{i}", label=f"Node{i}"))
        self.kg.add_edge(GraphEdge(source="n0", target="n1", relation="r"))
        self.kg.add_edge(GraphEdge(source="n1", target="n2", relation="r"))
        self.kg.add_edge(GraphEdge(source="n0", target="n2", relation="r"))
        self.kg.add_edge(GraphEdge(source="n3", target="n4", relation="r"))
        self.kg.add_edge(GraphEdge(source="n4", target="n5", relation="r"))
        self.kg.add_edge(GraphEdge(source="n3", target="n5", relation="r"))
        self.kg.add_edge(GraphEdge(source="n2", target="n3", relation="r"))
        communities = self.kg.detect_communities()
        assert len(communities) >= 1

    def test_neighbors(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        self.kg.add_node(GraphNode(node_id="c", label="C"))
        self.kg.add_edge(GraphEdge(source="a", target="b", relation="r"))
        self.kg.add_edge(GraphEdge(source="b", target="c", relation="r"))
        result = self.kg.neighbors("a", depth=1)
        assert "nodes" in result
        node_ids = [n["node_id"] for n in result["nodes"]]
        assert "b" in node_ids
        result2 = self.kg.neighbors("a", depth=2)
        node_ids2 = [n["node_id"] for n in result2["nodes"]]
        assert "c" in node_ids2

    def test_shortest_path(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        self.kg.add_node(GraphNode(node_id="c", label="C"))
        self.kg.add_edge(GraphEdge(source="a", target="b", relation="r"))
        self.kg.add_edge(GraphEdge(source="b", target="c", relation="r"))
        path = self.kg.shortest_path("a", "c")
        assert path == ["a", "b", "c"]

    def test_shortest_path_no_path(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        self.kg.add_node(GraphNode(node_id="b", label="B"))
        path = self.kg.shortest_path("a", "b")
        assert path is None or path == []

    def test_to_dict(self):
        self.kg.add_node(GraphNode(node_id="n1", label="Test"))
        d = self.kg.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert "communities" in d

    def test_graph_stats(self):
        self.kg.add_node(GraphNode(node_id="a", label="A"))
        stats = self.kg.graph_stats()
        assert stats["node_count"] == 1


class TestExtractEntities:
    def test_extracts_proper_nouns(self):
        text = "LangGraph and CrewAI are orchestration frameworks. OpenAI provides GPT models."
        entities = extract_entities(text)
        assert len(entities) >= 1

    def test_extracts_acronyms(self):
        text = "The API uses JSON-RPC and supports SOC2 compliance."
        entities = extract_entities(text)
        labels = [e["label"] for e in entities]
        assert any("API" in l or "JSON" in l or "SOC" in l for l in labels)


class TestExtractRelationships:
    def test_finds_relationships(self):
        text = "Praxis depends on FastAPI. LangGraph is part of LangChain."
        rels = extract_relationships(text)
        assert len(rels) >= 1


class TestBuildGraphFromText:
    def test_builds_graph(self):
        text = "Praxis depends on Python. FastAPI is part of Praxis. Python and FastAPI share similar goals."
        graph = build_graph_from_text(text)
        assert graph.node_count() >= 1
        assert isinstance(graph, KnowledgeGraph)


# ---------------------------------------------------------------------------
# compliance.py
# ---------------------------------------------------------------------------
from compliance import (
    regulatory_map,
    AuditTrail,
    get_audit_trail,
    audit_log,
    mask_pii,
    detect_pii,
    compliance_posture,
    MaskingResult,
)


class TestRegulatoryMap:
    def test_returns_frameworks(self):
        rm = regulatory_map()
        assert "frameworks" in rm
        assert "EU_AI_ACT" in rm["frameworks"]
        assert "HIPAA" in rm["frameworks"]
        assert "GDPR" in rm["frameworks"]

    def test_has_compliance_scores(self):
        rm = regulatory_map()
        for fw_name, fw_data in rm["frameworks"].items():
            assert "compliance_score" in fw_data
            assert 0 <= fw_data["compliance_score"] <= 1.0

    def test_has_requirements(self):
        rm = regulatory_map()
        eu = rm["frameworks"]["EU_AI_ACT"]
        assert len(eu["requirements"]) >= 5

    def test_has_total_requirements(self):
        rm = regulatory_map()
        assert "total_requirements" in rm
        assert rm["total_requirements"] >= 24


class TestAuditTrail:
    def setup_method(self):
        self.trail = AuditTrail()

    def test_log_event(self):
        self.trail.log("access", "user1", "dataset", "read", {"detail": "test"})
        assert len(self.trail._entries) == 1

    def test_hash_chaining(self):
        self.trail.log("a", "u", "r", "act1")
        self.trail.log("b", "u", "r", "act2")
        assert self.trail._entries[1].previous_hash == self.trail._entries[0].entry_hash

    def test_verify_integrity_empty(self):
        result = self.trail.verify_integrity()
        assert result["valid"] is True

    def test_verify_integrity_valid(self):
        for i in range(10):
            self.trail.log(f"event_{i}", "user", "res", f"action_{i}")
        result = self.trail.verify_integrity()
        assert result["valid"] is True

    def test_verify_integrity_tampered(self):
        self.trail.log("a", "u", "r", "act")
        self.trail.log("b", "u", "r", "act")
        self.trail._entries[0].entry_hash = "TAMPERED"
        result = self.trail.verify_integrity()
        assert result["valid"] is False

    def test_query_by_event_type(self):
        self.trail.log("access", "u", "r", "a")
        self.trail.log("modification", "u", "r", "a")
        self.trail.log("access", "u", "r", "a")
        results = self.trail.query(event_type="access")
        assert len(results) == 2

    def test_query_by_actor(self):
        self.trail.log("e", "admin", "r", "a")
        self.trail.log("e", "user", "r", "a")
        results = self.trail.query(actor="admin")
        assert len(results) == 1

    def test_stats(self):
        self.trail.log("a", "u", "r", "act")
        stats = self.trail.stats()
        assert stats["total_entries"] == 1

    def test_bounded_size(self):
        self.trail.MAX_ENTRIES = 10
        for i in range(20):
            self.trail.log(f"e{i}", "u", "r", "a")
        assert len(self.trail._entries) <= 10


class TestMaskPII:
    def test_masks_email(self):
        result = mask_pii("Contact john@example.com for info.")
        assert "john@example.com" not in result.masked_text
        assert "[EMAIL_REDACTED]" in result.masked_text

    def test_masks_phone(self):
        result = mask_pii("Call 555-123-4567.")
        assert "555-123-4567" not in result.masked_text

    def test_masks_ssn(self):
        result = mask_pii("SSN: 123-45-6789")
        assert "123-45-6789" not in result.masked_text
        assert "[SSN_REDACTED]" in result.masked_text

    def test_masks_credit_card(self):
        result = mask_pii("Card: 4111-1111-1111-1111")
        assert "4111" not in result.masked_text

    def test_no_pii(self):
        result = mask_pii("This is a normal sentence.")
        assert result.pii_found is False
        assert result.total_redactions == 0

    def test_multiple_pii(self):
        result = mask_pii("Email: a@b.com, SSN: 123-45-6789, Phone: 555-111-2222")
        assert result.total_redactions >= 3

    def test_category_filter(self):
        result = mask_pii("Email: a@b.com, SSN: 123-45-6789", categories=["email"])
        assert "[EMAIL_REDACTED]" in result.masked_text
        assert result.total_redactions >= 1

    def test_to_dict(self):
        result = mask_pii("test a@b.com")
        d = result.to_dict()
        assert "masked_text" in d
        assert "detections" in d


class TestDetectPII:
    def test_detects_email(self):
        result = detect_pii("Send to user@example.com")
        assert result["pii_detected"] is True
        assert "email" in result["categories"]


class TestCompliancePosture:
    def test_returns_structure(self):
        result = compliance_posture()
        assert "regulatory_compliance" in result
        assert "overall_grade" in result
        assert "audit_trail" in result


# ---------------------------------------------------------------------------
# ai_economics.py
# ---------------------------------------------------------------------------
from ai_economics import (
    token_cost,
    UsageLedger,
    get_ledger,
    calculate_roi,
    economics_dashboard,
    MODEL_PRICING,
    BudgetConfig,
    check_budget,
)


class TestTokenCost:
    def test_known_model(self):
        result = token_cost(1000, 500, "gpt-4o")
        assert result["total_cost_usd"] > 0
        assert result["model"] == "gpt-4o"

    def test_unknown_model_fallback(self):
        result = token_cost(1000, 500, "unknown-model-xyz")
        assert result["total_cost_usd"] > 0

    def test_zero_tokens(self):
        result = token_cost(0, 0, "gpt-4o")
        assert result["total_cost_usd"] == 0.0


class TestUsageLedger:
    def setup_method(self):
        self.ledger = UsageLedger()

    def test_record(self):
        self.ledger.record(user_id="u1", model="gpt-4o", input_tokens=100, output_tokens=50)
        summary = self.ledger.summary()
        assert summary["total_records"] == 1

    def test_aggregate_by_model(self):
        self.ledger.record(model="gpt-4o", input_tokens=100, output_tokens=50)
        self.ledger.record(model="gpt-4o", input_tokens=200, output_tokens=100)
        self.ledger.record(model="claude-3.5-sonnet", input_tokens=100, output_tokens=50)
        agg = self.ledger.aggregate_by("model")
        assert "gpt-4o" in agg
        assert agg["gpt-4o"]["request_count"] == 2

    def test_aggregate_by_user(self):
        self.ledger.record(user_id="alice", input_tokens=10)
        self.ledger.record(user_id="bob", input_tokens=20)
        agg = self.ledger.aggregate_by("user_id")
        assert "alice" in agg
        assert "bob" in agg

    def test_detect_waste(self):
        for i in range(5):
            self.ledger.record(model="gpt-4o", input_tokens=100, output_tokens=50)
        waste = self.ledger.detect_waste()
        assert isinstance(waste, list)

    def test_summary(self):
        self.ledger.record(input_tokens=1000, output_tokens=500)
        s = self.ledger.summary()
        assert s["total_cost_usd"] >= 0
        assert s["total_tokens"] == 1500

    def test_bounded_size(self):
        self.ledger.MAX_RECORDS = 10
        for i in range(20):
            self.ledger.record(input_tokens=10)
        assert len(self.ledger._records) <= 10


class TestCalculateROI:
    def test_basic_roi(self):
        result = calculate_roi(
            total_ai_cost_usd=1000,
            tasks_automated=100,
            avg_manual_minutes_per_task=30.0,
            labor_rate_per_hour=50,
        )
        assert result.roi_percentage > 0
        assert result.labor_hours_saved > 0

    def test_negative_roi(self):
        result = calculate_roi(total_ai_cost_usd=100000, tasks_automated=1, avg_manual_minutes_per_task=5)
        assert result.roi_percentage < 0

    def test_to_dict(self):
        result = calculate_roi(total_ai_cost_usd=100, tasks_automated=10)
        d = result.to_dict()
        assert "roi_percentage" in d
        assert "payback_days" in d


class TestBudgetCheck:
    def test_normal_budget(self):
        config = BudgetConfig(monthly_budget_usd=1000.0)
        result = check_budget(config)
        assert "within_budget" in result

    def test_model_pricing_populated(self):
        assert "gpt-4o" in MODEL_PRICING
        assert "claude-3.5-sonnet" in MODEL_PRICING


class TestEconomicsDashboard:
    def test_returns_structure(self):
        result = economics_dashboard()
        assert "usage_summary" in result
        assert "roi" in result
        assert "model_pricing" in result


# ---------------------------------------------------------------------------
# vendor_risk.py
# ---------------------------------------------------------------------------
from vendor_risk import (
    VendorProfile as VRProfile,
    VendorCategory,
    RiskLevel,
    compute_risk_score,
    DataLineageTracker,
    VendorRegistry,
    get_registry,
    vendor_risk_dashboard,
)


class TestVendorProfile:
    def test_to_dict(self):
        vp = VRProfile(
            vendor_id="test-vendor", name="Test", category=VendorCategory.FOUNDATION_MODEL.value,
            soc2_compliant=True, iso27001=False, gdpr_compliant=True, hipaa_compliant=False,
            model_types=["llm"], data_retention_days=90, trains_on_customer_data=False,
            transparency_score=0.8, data_access_scope="read",
        )
        d = vp.to_dict()
        assert d["vendor_id"] == "test-vendor"
        assert d["soc2_compliant"] is True


class TestComputeRiskScore:
    def test_low_risk_vendor(self):
        vp = VRProfile(
            vendor_id="safe", name="Safe Vendor", category=VendorCategory.FOUNDATION_MODEL.value,
            soc2_compliant=True, iso27001=True, gdpr_compliant=True, hipaa_compliant=True,
            model_types=["llm"], data_retention_days=30, trains_on_customer_data=False,
            transparency_score=0.9, data_access_scope="read", supports_data_deletion=True,
        )
        result = compute_risk_score(vp)
        assert result["risk_score"] < 30
        assert result["risk_level"] in ("low", "minimal")

    def test_high_risk_vendor(self):
        vp = VRProfile(
            vendor_id="risky", name="Risky Vendor", category=VendorCategory.FOUNDATION_MODEL.value,
            soc2_compliant=False, iso27001=False, gdpr_compliant=False, hipaa_compliant=False,
            model_types=["llm"], data_retention_days=365, trains_on_customer_data=True,
            transparency_score=0.1, data_access_scope="read_write_execute",
            vulnerabilities_known=5,
        )
        result = compute_risk_score(vp)
        assert result["risk_score"] >= 50
        assert result["risk_level"] in ("high", "critical")

    def test_has_recommendations(self):
        vp = VRProfile(
            vendor_id="test", name="Test", category=VendorCategory.OTHER.value,
            soc2_compliant=False, iso27001=False, gdpr_compliant=False, hipaa_compliant=False,
            model_types=[], data_retention_days=180, trains_on_customer_data=True,
            transparency_score=0.3, data_access_scope="read_write",
        )
        result = compute_risk_score(vp)
        assert "recommendations" in result
        assert len(result["recommendations"]) >= 1


class TestDataLineageTracker:
    def setup_method(self):
        self.tracker = DataLineageTracker()

    def test_record_flow(self):
        self.tracker.record_flow(
            data_type="prompt", source="user", destination_vendor="v1",
            purpose="inference", contains_pii=False, authorized=True,
        )
        assert len(self.tracker._entries) == 1

    def test_detect_unauthorized(self):
        self.tracker.record_flow("prompt", "user", "v1", authorized=False)
        unauth = self.tracker.detect_unauthorized()
        assert len(unauth) == 1

    def test_detect_pii_exposure(self):
        self.tracker.record_flow("prompt", "user", "v1", purpose="training", contains_pii=True, authorized=True)
        pii = self.tracker.detect_pii_exposure()
        assert len(pii) == 1

    def test_lineage_for_vendor(self):
        self.tracker.record_flow("prompt", "user", "v1")
        self.tracker.record_flow("response", "api", "v2")
        assert len(self.tracker.lineage_for_vendor("v1")) == 1

    def test_summary(self):
        self.tracker.record_flow("prompt", "user", "v1", contains_pii=True, authorized=True)
        s = self.tracker.summary()
        assert s["total_flows"] == 1


class TestVendorRegistry:
    def setup_method(self):
        self.reg = VendorRegistry()

    def test_register(self):
        vp = VRProfile(
            vendor_id="new", name="New Vendor", category=VendorCategory.OTHER.value,
            soc2_compliant=True, iso27001=False, gdpr_compliant=True, hipaa_compliant=False,
            model_types=[], data_retention_days=30, trains_on_customer_data=False,
            transparency_score=0.7, data_access_scope="read",
        )
        assert self.reg.register(vp) is True
        assert self.reg.get("new") is not None

    def test_list_vendors(self):
        vp = VRProfile(
            vendor_id="v1", name="V1", category=VendorCategory.OTHER.value,
            soc2_compliant=True, iso27001=False, gdpr_compliant=True, hipaa_compliant=False,
            model_types=[], data_retention_days=30, trains_on_customer_data=False,
            transparency_score=0.5, data_access_scope="read",
        )
        self.reg.register(vp)
        vendors = self.reg.list_vendors()
        assert len(vendors) >= 1
        assert isinstance(vendors[0], dict)


class TestGetRegistry:
    def test_singleton_seeded(self):
        reg = get_registry()
        vendors = reg.list_vendors()
        assert len(vendors) >= 5
        ids = {v["vendor_id"] for v in vendors}
        assert "openai" in ids
        assert "anthropic" in ids


class TestVendorRiskDashboard:
    def test_returns_structure(self):
        result = vendor_risk_dashboard()
        assert "vendors" in result
        assert "risk_summary" in result
        assert "data_lineage" in result
