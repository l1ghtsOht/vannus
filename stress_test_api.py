#!/usr/bin/env python3
"""
Praxis API Professional Stress Test Suite
==========================================
Comprehensive endpoint coverage with latency profiling, error tracking,
concurrency stress, and a final summary report.

Usage:
    python stress_test_api.py [--base-url http://localhost:8000] [--concurrency 10]
"""

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

import requests

# ─── Configuration ──────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"


@dataclass
class EndpointResult:
    category: str
    method: str
    path: str
    status: int = 0
    latency_ms: float = 0.0
    error: str = ""
    response_size: int = 0


@dataclass
class CategoryReport:
    name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    latencies: list = field(default_factory=list)


# ─── Endpoint Definitions ──────────────────────────────────────────

def build_test_suite() -> list[dict[str, Any]]:
    """Return every testable endpoint grouped by category."""
    return [
        # ══════════════════════════════════════════════════════════
        # CORE
        # ══════════════════════════════════════════════════════════
        {"cat": "Core", "method": "GET", "path": "/health"},
        {"cat": "Core", "method": "GET", "path": "/categories"},
        {"cat": "Core", "method": "GET", "path": "/tools"},
        {"cat": "Core", "method": "GET", "path": "/suggest?q=project+management"},
        {"cat": "Core", "method": "POST", "path": "/search",
         "body": {"query": "best CI/CD tools for startups"}},
        {"cat": "Core", "method": "POST", "path": "/stack",
         "body": {"query": "full-stack web development"}},
        {"cat": "Core", "method": "POST", "path": "/compare",
         "body": {"tool_a": "GitHub", "tool_b": "GitLab"}},
        {"cat": "Core", "method": "POST", "path": "/profile",
         "body": {"profile_id": "stress_test", "industry": "fintech", "budget": 500, "team_size": 8}},
        {"cat": "Core", "method": "POST", "path": "/feedback",
         "body": {"query": "CI tools", "tool": "GitHub Actions", "accepted": True, "rating": 5}},
        {"cat": "Core", "method": "POST", "path": "/learn",
         "body": {"query": "monitoring", "tool": "Datadog", "accepted": True}},
        {"cat": "Core", "method": "GET", "path": "/profiles"},
        {"cat": "Core", "method": "POST", "path": "/tuesday-test",
         "body": {"query": "deploy pipeline"}},
        {"cat": "Core", "method": "POST", "path": "/rfp/generate",
         "body": {"query": "enterprise CRM platform"}},

        # ══════════════════════════════════════════════════════════
        # COGNITIVE & REASONING
        # ══════════════════════════════════════════════════════════
        {"cat": "Cognitive", "method": "POST", "path": "/cognitive",
         "body": {"query": "I need HIPAA compliant tools under $50"}},
        {"cat": "Cognitive", "method": "POST", "path": "/reason",
         "body": {"query": "best email marketing platform for small business"}},
        {"cat": "Cognitive", "method": "POST", "path": "/hybrid",
         "body": {"query": "project management for remote teams"}},
        {"cat": "Cognitive", "method": "POST", "path": "/prism",
         "body": {"query": "evaluate security scanning tools"}},

        # ══════════════════════════════════════════════════════════
        # FEATURE ROUTES
        # ══════════════════════════════════════════════════════════
        {"cat": "Features", "method": "GET", "path": "/tools/stale"},
        {"cat": "Features", "method": "POST", "path": "/workflow-suggest",
         "body": {"query": "automate testing pipeline"}},
        {"cat": "Features", "method": "POST", "path": "/migration-plan",
         "body": {"from_tool": "Jenkins", "to_tool": "GitHub Actions"}},
        {"cat": "Features", "method": "POST", "path": "/whatif",
         "body": {"tool": "Slack", "scenario": "team doubles in size"}},
        {"cat": "Features", "method": "POST", "path": "/benchmark",
         "body": {"query": "CI/CD performance"}},
        {"cat": "Features", "method": "GET", "path": "/diagnostics/self"},
        {"cat": "Features", "method": "GET", "path": "/diagnostics/readiness"},

        # ══════════════════════════════════════════════════════════
        # KNOWLEDGE GRAPH
        # ══════════════════════════════════════════════════════════
        {"cat": "Graph", "method": "GET", "path": "/graph/tools"},
        {"cat": "Graph", "method": "GET", "path": "/graph/competitors/GitHub"},
        {"cat": "Graph", "method": "GET", "path": "/graph/integrations/Slack"},
        {"cat": "Graph", "method": "GET", "path": "/graph/community/GitHub"},
        {"cat": "Graph", "method": "GET", "path": "/graph/stats"},

        # ══════════════════════════════════════════════════════════
        # VERTICALS
        # ══════════════════════════════════════════════════════════
        {"cat": "Verticals", "method": "GET", "path": "/verticals"},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/detect",
         "body": {"query": "healthcare patient management", "industry": "healthcare"}},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/constraints",
         "body": {"query": "HIPAA compliant hosting"}},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/workflow",
         "body": {"query": "e-commerce checkout flow"}},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/stack",
         "body": {"query": "fintech payment processing"}},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/anti-patterns",
         "body": {"query": "monolith migration"}},
        {"cat": "Verticals", "method": "POST", "path": "/verticals/enrich",
         "body": {"query": "real-time analytics"}},

        # ══════════════════════════════════════════════════════════
        # GUARDRAILS
        # ══════════════════════════════════════════════════════════
        {"cat": "Guardrails", "method": "POST", "path": "/guardrails/validate",
         "body": {"prompt": "recommend a tool for password management"}},
        {"cat": "Guardrails", "method": "POST", "path": "/guardrails/check-pii",
         "body": {"text": "Contact john@example.com or call 555-1234"}},
        {"cat": "Guardrails", "method": "POST", "path": "/guardrails/score-safety",
         "body": {"prompt": "how to deploy to production"}},
        {"cat": "Guardrails", "method": "POST", "path": "/guardrails/recommend",
         "body": {"use_case": "LLM chatbot", "risk_tolerance": "low"}},
        {"cat": "Guardrails", "method": "GET", "path": "/guardrails/handlers"},
        {"cat": "Guardrails", "method": "GET", "path": "/guardrails/design-patterns"},

        # ══════════════════════════════════════════════════════════
        # ORCHESTRATION
        # ══════════════════════════════════════════════════════════
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/analyze",
         "body": {"query": "microservices architecture"}},
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/recommend-stack",
         "body": {"query": "real-time data pipeline"}},
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/recommend-patterns",
         "body": {"query": "event-driven architecture"}},
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/performance",
         "body": {"query": "high-throughput API"}},
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/classify",
         "body": {"query": "serverless functions"}},
        {"cat": "Orchestration", "method": "POST", "path": "/orchestration/score",
         "body": {"query": "container orchestration"}},
        {"cat": "Orchestration", "method": "GET", "path": "/orchestration/stack-catalogue"},
        {"cat": "Orchestration", "method": "GET", "path": "/orchestration/pattern-catalogue"},

        # ══════════════════════════════════════════════════════════
        # RESILIENCE
        # ══════════════════════════════════════════════════════════
        {"cat": "Resilience", "method": "POST", "path": "/resilience/assess",
         "body": {"query": "disaster recovery plan"}},
        {"cat": "Resilience", "method": "POST", "path": "/resilience/vibe-coding-risk",
         "body": {"query": "rapid prototyping without tests"}},
        {"cat": "Resilience", "method": "POST", "path": "/resilience/static-analysis",
         "body": {"query": "code quality enforcement"}},
        {"cat": "Resilience", "method": "POST", "path": "/resilience/sandbox",
         "body": {"query": "isolated test environments"}},
        {"cat": "Resilience", "method": "POST", "path": "/resilience/junior-pipeline",
         "body": {"query": "onboarding junior developers"}},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/tdd-cycle"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/rpi-framework"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/self-healing"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/reflection-patterns"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/judge-biases"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/guardrail-pipeline"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/hitl"},
        {"cat": "Resilience", "method": "GET", "path": "/resilience/hallucinations"},

        # ══════════════════════════════════════════════════════════
        # METACOGNITION
        # ══════════════════════════════════════════════════════════
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/assess",
         "body": {"query": "evaluate architectural decisions"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/pathologies",
         "body": {"query": "detect anti-patterns in codebase"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/entropy",
         "body": {"query": "measure system complexity"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/stylometry",
         "body": {"query": "analyze coding style consistency"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/recommend-layers",
         "body": {"query": "layered architecture"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/recommend-sandbox",
         "body": {"query": "safe experimentation"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/healing-economics",
         "body": {"query": "self-healing cost analysis"}},
        {"cat": "Metacognition", "method": "POST", "path": "/metacognition/drift",
         "body": {"query": "architectural drift detection"}},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/layers"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/sandbox-strategies"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/workflow"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/apvp-cycle"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/systemic-risks"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/goodvibe"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/racg"},
        {"cat": "Metacognition", "method": "GET", "path": "/metacognition/failure-modes"},

        # ══════════════════════════════════════════════════════════
        # AWAKENING
        # ══════════════════════════════════════════════════════════
        {"cat": "Awakening", "method": "POST", "path": "/awakening/assessment",
         "body": {"query": "architectural awareness audit"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/leaky-abstractions",
         "body": {"query": "identify leaky abstractions"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/patterns",
         "body": {"query": "design pattern recommendations"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/vsd",
         "body": {"query": "value sensitive design"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/supply-chain",
         "body": {"query": "dependency supply chain risk"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/debt",
         "body": {"query": "technical debt assessment"}},
        {"cat": "Awakening", "method": "POST", "path": "/awakening/mesias",
         "body": {"query": "evaluate tool maturity"}},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/recognitions"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/triad"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/vsd-framework"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/leaky-catalogue"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/supply-chain-guidance"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/paradoxes"},
        {"cat": "Awakening", "method": "GET", "path": "/awakening/conscious-patterns"},

        # ══════════════════════════════════════════════════════════
        # SELF-AUTHORSHIP
        # ══════════════════════════════════════════════════════════
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/assess",
         "body": {"query": "team autonomy assessment"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/dishonesty",
         "body": {"query": "detect dishonest abstractions"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/ddd",
         "body": {"query": "domain-driven design scoring"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/continuity",
         "body": {"query": "system continuity planning"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/resilience-posture",
         "body": {"query": "resilience posture evaluation"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/extensibility",
         "body": {"query": "plugin architecture scoring"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/migration",
         "body": {"query": "system migration readiness"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/documentation",
         "body": {"query": "documentation quality scoring"}},
        {"cat": "SelfAuthorship", "method": "POST", "path": "/self-authorship/agent-readiness",
         "body": {"query": "AI agent integration readiness"}},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/responsibilities"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/metacognitive-agents"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/coherence-trap"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/self-healing-pipeline"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/strangler-fig"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/circuit-breaker"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/ddd-patterns"},
        {"cat": "SelfAuthorship", "method": "GET", "path": "/self-authorship/plugin-frameworks"},

        # ══════════════════════════════════════════════════════════
        # ENLIGHTENMENT
        # ══════════════════════════════════════════════════════════
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/stage/1",
         "body": {"query": "stage 1 assessment"}},
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/stage/2",
         "body": {"query": "stage 2 assessment"}},
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/stage/3",
         "body": {"query": "stage 3 assessment"}},
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/truth/observer",
         "body": {"query": "observer pattern truth"}},
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/truth/hexagonal",
         "body": {"query": "hexagonal architecture truth"}},
        {"cat": "Enlightenment", "method": "POST", "path": "/enlightenment/truth/state",
         "body": {"query": "state pattern truth"}},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/truths"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/stages"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/identity-map"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/observer-pattern"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/hexagonal-architecture"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/state-pattern"},
        {"cat": "Enlightenment", "method": "GET", "path": "/enlightenment/clean-architecture"},

        # ══════════════════════════════════════════════════════════
        # CONDUIT
        # ══════════════════════════════════════════════════════════
        {"cat": "Conduit", "method": "POST", "path": "/conduit/pillar/identity",
         "body": {"query": "identity pillar scoring"}},
        {"cat": "Conduit", "method": "POST", "path": "/conduit/pillar/memory",
         "body": {"query": "memory pillar scoring"}},
        {"cat": "Conduit", "method": "POST", "path": "/conduit/pillar/reasoning",
         "body": {"query": "reasoning pillar scoring"}},
        {"cat": "Conduit", "method": "POST", "path": "/conduit/telemetry/latency",
         "body": {"query": "latency telemetry"}},
        {"cat": "Conduit", "method": "POST", "path": "/conduit/telemetry/throughput",
         "body": {"query": "throughput telemetry"}},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/pillars"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/telemetry-metrics"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/gwt-components"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/coala-memory"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/reinterpretation"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/identity-protocol"},
        {"cat": "Conduit", "method": "GET", "path": "/conduit/codes-framework"},

        # ══════════════════════════════════════════════════════════
        # RESONANCE
        # ══════════════════════════════════════════════════════════
        {"cat": "Resonance", "method": "POST", "path": "/resonance/pillar/emergence",
         "body": {"query": "emergence pillar"}},
        {"cat": "Resonance", "method": "POST", "path": "/resonance/pillar/coherence",
         "body": {"query": "coherence pillar"}},
        {"cat": "Resonance", "method": "POST", "path": "/resonance/telemetry/drift",
         "body": {"query": "drift telemetry"}},
        {"cat": "Resonance", "method": "POST", "path": "/resonance/trap",
         "body": {"query": "resonance trap detection"}},
        {"cat": "Resonance", "method": "POST", "path": "/resonance/dsrp",
         "body": {"query": "DSRP analysis"}},
        {"cat": "Resonance", "method": "POST", "path": "/resonance/wisdom-detect",
         "body": {"query": "wisdom detection"}},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/pillars"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/trap-pillars"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/dsrp-rules"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/wisdom-agents"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/telemetry-metrics"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/reinterpretation"},
        {"cat": "Resonance", "method": "GET", "path": "/resonance/chamber"},

        # ══════════════════════════════════════════════════════════
        # ENTERPRISE ENGINE
        # ══════════════════════════════════════════════════════════
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/pillar/governance",
         "body": {"query": "enterprise governance scoring"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/pillar/scalability",
         "body": {"query": "enterprise scalability scoring"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/telemetry/cost",
         "body": {"query": "cost telemetry analysis"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/telemetry/security",
         "body": {"query": "security telemetry"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/agent-roles",
         "body": {"query": "enterprise agent role analysis"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/medallion",
         "body": {"query": "medallion architecture"}},
        {"cat": "Enterprise", "method": "POST", "path": "/enterprise/detect-agents",
         "body": {"query": "detect agent patterns"}},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/pillars"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/agent-roles-catalogue"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/db-tiers"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/medallion-tiers"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/enrichment-apis"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/pricing-models"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/security-frameworks"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/capitalization"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/market-metrics"},
        {"cat": "Enterprise", "method": "GET", "path": "/enterprise/telemetry-metrics"},

        # ══════════════════════════════════════════════════════════
        # INTROSPECTION
        # ══════════════════════════════════════════════════════════
        {"cat": "Introspection", "method": "GET", "path": "/introspect/self-diagnose"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/codebase"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/structural-entropy"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/stylometry"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/pathologies"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/test-coverage"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/import-graph"},
        {"cat": "Introspection", "method": "GET", "path": "/introspect/worst-functions"},

        # ══════════════════════════════════════════════════════════
        # v18 ENTERPRISE INFRASTRUCTURE
        # ══════════════════════════════════════════════════════════
        {"cat": "v18", "method": "POST", "path": "/v18/vendor-trust/score",
         "body": {"vendor": "GitHub"}},
        {"cat": "v18", "method": "POST", "path": "/v18/hybrid-search",
         "body": {"query": "container orchestration", "top_n": 5}},
        {"cat": "v18", "method": "POST", "path": "/v18/tfidf/batch-score",
         "body": {"queries": ["CI/CD", "monitoring", "logging"]}},
        {"cat": "v18", "method": "GET", "path": "/v18/tfidf/stats"},
        {"cat": "v18", "method": "GET", "path": "/v18/llm/circuit-status"},
        {"cat": "v18", "method": "GET", "path": "/v18/health"},

        # ══════════════════════════════════════════════════════════
        # v19 PLATFORM EVOLUTION
        # ══════════════════════════════════════════════════════════
        {"cat": "v19", "method": "GET", "path": "/v19/connectors"},
        {"cat": "v19", "method": "POST", "path": "/v19/connectors/execute",
         "body": {"connector": "github", "action": "list_repos", "dry_run": True}},
        {"cat": "v19", "method": "POST", "path": "/v19/workflow/decompose",
         "body": {"query": "set up CI/CD pipeline"}},
        {"cat": "v19", "method": "POST", "path": "/v19/workflow/plan",
         "body": {"query": "deploy microservices"}},
        {"cat": "v19", "method": "POST", "path": "/v19/workflow/execute",
         "body": {"query": "run deployment", "dry_run": True}},
        {"cat": "v19", "method": "GET", "path": "/v19/marketplace/templates"},
        {"cat": "v19", "method": "GET", "path": "/v19/contributions/leaderboard"},
        {"cat": "v19", "method": "POST", "path": "/v19/agent-sdk/session",
         "body": {"agent_name": "stress_test_agent"}},
        {"cat": "v19", "method": "GET", "path": "/v19/governance/policies"},
        {"cat": "v19", "method": "POST", "path": "/v19/governance/audit",
         "body": {"user_id": "stress_tester", "action": "api_test", "resource": "all"}},
        {"cat": "v19", "method": "POST", "path": "/v19/governance/usage",
         "body": {"user_id": "stress_tester", "metric": "api_calls", "value": 1.0}},

        # ══════════════════════════════════════════════════════════
        # v20 STRESS & SECURITY
        # ══════════════════════════════════════════════════════════
        {"cat": "v20", "method": "GET", "path": "/v20/persistence/canary"},
        {"cat": "v20", "method": "GET", "path": "/v20/ast-security/scan"},
        {"cat": "v20", "method": "GET", "path": "/v20/memory/profile"},
        {"cat": "v20", "method": "GET", "path": "/v20/architecture/analyze"},
        {"cat": "v20", "method": "POST", "path": "/v20/red-team/probe",
         "body": {"query": "test injection resilience"}},

        # ══════════════════════════════════════════════════════════
        # PUBLIC API v1
        # ══════════════════════════════════════════════════════════
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/analyze",
         "body": {"query": "best tools for DevOps automation"}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/stack/optimize",
         "body": {"query": "optimize cloud infrastructure stack"}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/compare",
         "body": {"tool_a": "AWS", "tool_b": "Azure"}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/migrate",
         "body": {"from_tool": "Heroku", "to_tool": "AWS"}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/whatif",
         "body": {"tool": "Kubernetes", "scenario": "scale to 1000 nodes"}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/cost",
         "body": {"tools": ["GitHub", "Slack", "Jira"], "team_size": 50}},
        {"cat": "PublicAPI", "method": "POST", "path": "/api/v1/feedback",
         "body": {"query": "DevOps tools", "tool": "Terraform", "accepted": True}},
        {"cat": "PublicAPI", "method": "GET", "path": "/api/v1/vendor/GitHub"},
        {"cat": "PublicAPI", "method": "GET", "path": "/api/v1/compliance"},
        {"cat": "PublicAPI", "method": "GET", "path": "/api/v1/economics"},
        {"cat": "PublicAPI", "method": "GET", "path": "/api/v1/health"},
        {"cat": "PublicAPI", "method": "GET", "path": "/api/v1/docs"},

        # ══════════════════════════════════════════════════════════
        # ROOMS (v21+)
        # ══════════════════════════════════════════════════════════
        {"cat": "Rooms", "method": "POST", "path": "/room",
         "body": {"name": "Stress Test Room"}},
        {"cat": "Rooms", "method": "GET", "path": "/rooms"},
    ]


# ─── Test Runner ────────────────────────────────────────────────────

def execute_single(ep: dict, base: str, timeout: float = 30.0) -> EndpointResult:
    """Fire a single request and measure latency."""
    url = f"{base}{ep['path']}"
    method = ep["method"].upper()
    result = EndpointResult(
        category=ep["cat"],
        method=method,
        path=ep["path"],
    )
    t0 = time.perf_counter()
    try:
        if method == "GET":
            r = requests.get(url, timeout=timeout)
        else:
            r = requests.post(url, json=ep.get("body", {}), timeout=timeout)
        result.status = r.status_code
        result.latency_ms = (time.perf_counter() - t0) * 1000
        result.response_size = len(r.content)
    except (requests.exceptions.Timeout, TimeoutError):
        result.latency_ms = timeout * 1000
        result.error = "TIMEOUT"
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, OSError) as exc:
        result.latency_ms = (time.perf_counter() - t0) * 1000
        result.error = f"CONNECTION_ERROR"
    except (KeyboardInterrupt, SystemExit):
        result.latency_ms = (time.perf_counter() - t0) * 1000
        result.error = "INTERRUPTED"
    except Exception as exc:
        result.latency_ms = (time.perf_counter() - t0) * 1000
        result.error = f"EXCEPTION: {type(exc).__name__}"
    return result


def run_sequential(suite: list[dict], base: str) -> list[EndpointResult]:
    """Run every endpoint sequentially — baseline pass."""
    results = []
    total = len(suite)
    for i, ep in enumerate(suite, 1):
        tag = f"[{i}/{total}]"
        label = f"{ep['method']:4s} {ep['path']}"
        r = execute_single(ep, base)
        status_icon = "✓" if 200 <= r.status < 300 else ("⚠" if r.status < 500 else "✗")
        print(f"  {tag:>10s} {status_icon} {r.status:3d} {r.latency_ms:8.1f}ms  {label}")
        results.append(r)
    return results


def run_concurrent(suite: list[dict], base: str, workers: int = 10) -> list[EndpointResult]:
    """Blast all endpoints concurrently — stress pass."""
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(execute_single, ep, base): ep for ep in suite}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results


# ─── Reporting ──────────────────────────────────────────────────────

def build_report(results: list[EndpointResult], label: str) -> dict:
    """Aggregate results into a structured report."""
    categories: dict[str, CategoryReport] = {}
    failures: list[EndpointResult] = []

    for r in results:
        cat = categories.setdefault(r.category, CategoryReport(name=r.category))
        cat.total += 1
        if r.error or r.status >= 500:
            cat.failed += 1
            failures.append(r)
        else:
            cat.passed += 1
        cat.latencies.append(r.latency_ms)

    total = len(results)
    passed = sum(c.passed for c in categories.values())
    failed = sum(c.failed for c in categories.values())
    all_lat = [r.latency_ms for r in results]

    report = {
        "label": label,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed / total * 100:.1f}%" if total else "N/A",
        "latency": {
            "min_ms": round(min(all_lat), 1) if all_lat else 0,
            "max_ms": round(max(all_lat), 1) if all_lat else 0,
            "mean_ms": round(statistics.mean(all_lat), 1) if all_lat else 0,
            "median_ms": round(statistics.median(all_lat), 1) if all_lat else 0,
            "p95_ms": round(sorted(all_lat)[int(len(all_lat) * 0.95)] if all_lat else 0, 1),
            "p99_ms": round(sorted(all_lat)[int(len(all_lat) * 0.99)] if all_lat else 0, 1),
        },
        "categories": {},
        "failures": [],
    }

    for name, cat in sorted(categories.items()):
        lat = cat.latencies
        report["categories"][name] = {
            "total": cat.total,
            "passed": cat.passed,
            "failed": cat.failed,
            "mean_ms": round(statistics.mean(lat), 1) if lat else 0,
            "max_ms": round(max(lat), 1) if lat else 0,
        }

    for f in failures:
        report["failures"].append({
            "method": f.method,
            "path": f.path,
            "status": f.status,
            "error": f.error,
            "latency_ms": round(f.latency_ms, 1),
        })

    return report


def print_report(report: dict):
    """Pretty-print the report to stdout."""
    W = 72
    print()
    print("=" * W)
    print(f"  {report['label']}")
    print("=" * W)
    print(f"  Total: {report['total']}   Passed: {report['passed']}   "
          f"Failed: {report['failed']}   Pass Rate: {report['pass_rate']}")
    print("-" * W)

    lat = report["latency"]
    print(f"  Latency  min={lat['min_ms']}ms  mean={lat['mean_ms']}ms  "
          f"median={lat['median_ms']}ms  p95={lat['p95_ms']}ms  "
          f"p99={lat['p99_ms']}ms  max={lat['max_ms']}ms")
    print("-" * W)

    print(f"  {'Category':<20s} {'Total':>5s} {'Pass':>5s} {'Fail':>5s} "
          f"{'Mean':>8s} {'Max':>8s}")
    print(f"  {'─' * 20} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 8} {'─' * 8}")
    for name, c in report["categories"].items():
        fail_flag = " !" if c["failed"] > 0 else ""
        print(f"  {name:<20s} {c['total']:>5d} {c['passed']:>5d} {c['failed']:>5d} "
              f"{c['mean_ms']:>7.1f}ms {c['max_ms']:>7.1f}ms{fail_flag}")

    if report["failures"]:
        print()
        print(f"  FAILURES ({len(report['failures'])}):")
        print(f"  {'─' * (W - 4)}")
        for f in report["failures"]:
            err = f["error"] or f"HTTP {f['status']}"
            print(f"    {f['method']:4s} {f['path']:<45s} {err}")

    print("=" * W)


# ─── Main ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Praxis API Stress Test")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--concurrency", type=int, default=10,
                        help="Number of concurrent workers for stress pass")
    parser.add_argument("--skip-sequential", action="store_true",
                        help="Skip sequential pass, only run concurrent")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    suite = build_test_suite()
    print(f"\n  Praxis API Stress Test")
    print(f"  Target: {base}")
    print(f"  Endpoints: {len(suite)}")
    print(f"  Concurrency: {args.concurrency}")
    print()

    # ── Phase 1: Sequential baseline ────────────────────────────
    if not args.skip_sequential:
        print("─── Phase 1: Sequential Baseline ───────────────────────────")
        seq_results = run_sequential(suite, base)
        seq_report = build_report(seq_results, "Sequential Baseline")
        print_report(seq_report)
    else:
        seq_report = None

    # ── Phase 2: Concurrent stress ──────────────────────────────
    print("\n─── Phase 2: Concurrent Stress ─────────────────────────────")
    print(f"  Firing {len(suite)} requests with {args.concurrency} workers...")
    t0 = time.perf_counter()
    con_results = run_concurrent(suite, base, workers=args.concurrency)
    wall_time = time.perf_counter() - t0
    print(f"  Completed in {wall_time:.2f}s  "
          f"({len(suite) / wall_time:.1f} req/s)")
    con_report = build_report(con_results, f"Concurrent Stress ({args.concurrency} workers)")
    print_report(con_report)

    # ── Phase 3: Burst (3x concurrency) ────────────────────────
    burst_workers = args.concurrency * 3
    print(f"\n─── Phase 3: Burst Load ({burst_workers} workers) ──────────")
    # Triple the suite for burst
    burst_suite = suite * 3
    print(f"  Firing {len(burst_suite)} requests with {burst_workers} workers...")
    t0 = time.perf_counter()
    burst_results = run_concurrent(burst_suite, base, workers=burst_workers)
    burst_wall = time.perf_counter() - t0
    print(f"  Completed in {burst_wall:.2f}s  "
          f"({len(burst_suite) / burst_wall:.1f} req/s)")
    burst_report = build_report(burst_results, f"Burst Load ({burst_workers} workers, 3x volume)")
    print_report(burst_report)

    # ── Summary ─────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  FINAL SUMMARY")
    print("=" * 72)
    reports = [r for r in [seq_report, con_report, burst_report] if r]
    for r in reports:
        status = "PASS" if r["failed"] == 0 else "DEGRADED" if int(r["pass_rate"].rstrip("%").split(".")[0]) >= 90 else "FAIL"
        print(f"  [{status:>8s}]  {r['label']:<45s}  "
              f"{r['passed']}/{r['total']}  mean={r['latency']['mean_ms']}ms  p95={r['latency']['p95_ms']}ms")

    total_failures = sum(r["failed"] for r in reports)
    print()
    if total_failures == 0:
        print("  ✓ ALL PHASES PASSED — Zero failures across all test phases.")
    else:
        print(f"  ⚠ {total_failures} total failures detected across phases.")
    print("=" * 72)

    return 1 if any(r["failed"] > 0 for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
