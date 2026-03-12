# ────────────────────────────────────────────────────────────────────
# verification.py — Anti-Wrapper Verification Shield
# ────────────────────────────────────────────────────────────────────
"""
Algorithmically scores every tool in the Praxis knowledge base on
architectural resilience, sovereign IP signals, and long-term viability.

The "Wrapper Epidemic" is the #1 vendor-fatigue factor for SMBs:
thousands of indistinguishable apps built as thin pass-throughs to
OpenAI/Anthropic APIs with zero proprietary logic.  This module
assigns each tool a **Resilience Score** (0–100) and a letter grade
so business owners can instantly distinguish durable platforms from
transient shells.

Scoring Dimensions (weighted):
    1. Native IP Signal        (30%)  — fine-tuned models, proprietary
       algorithms, custom training pipelines
    2. Integration Depth       (20%)  — native integrations vs. Zapier-
       only, bidirectional data flow
    3. Compliance Posture      (15%)  — SOC2 / GDPR / HIPAA / ISO certs
    4. Pricing Sustainability  (15%)  — unit economics that imply R&D
       investment, not pure API margin arbitrage
    5. Data Portability        (10%)  — export formats, off-ramp quality
    6. Ecosystem Lock-in Risk  (10%)  — dependency on single upstream
       provider, API ToS fragility

Phase 1:  heuristic scoring from existing Tool metadata.
Phase 2+: live API header analysis, financial burn-rate modeling,
          automated web scraping for technology stack detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import logging
log = logging.getLogger("praxis.verification")


# ╔════════════════════════════════════════════════════════════════════╗
# ║  CONSTANTS                                                        ║
# ╚════════════════════════════════════════════════════════════════════╝

# Tools known to possess significant native IP / proprietary models
_NATIVE_IP_SIGNALS: Set[str] = {
    "chatgpt", "claude", "gemini", "midjourney", "dall-e", "stable diffusion",
    "runway", "eleven labs", "descript", "notion ai", "figma ai", "canva ai",
    "grammarly", "jasper", "copy.ai", "writesonic", "hugging face",
    "semrush", "ahrefs", "surfer seo", "clearscope",
    "salesforce", "hubspot", "zapier", "make", "n8n",
    "tableau", "power bi", "looker", "datadog",
    "github copilot", "cursor", "replit", "v0",
    "vercel", "supabase", "firebase",
    "stripe", "quickbooks", "xero", "wave",
    "slack", "asana", "monday.com", "clickup", "linear",
    "airtable", "retool", "appsmith", "bubble",
    "twilio", "sendgrid", "mailchimp", "convertkit",
    "zendesk", "intercom", "freshdesk", "tidio",
    "loom", "synthesia", "heygen",
    "otter.ai", "fireflies.ai",
    "notion", "obsidian",
}

# Tools that are known thin wrappers (pass-through to upstream LLM)
_KNOWN_WRAPPERS: Set[str] = set()  # populated via community reports

# Upstream providers whose API dependency = higher fragility
_UPSTREAM_PROVIDERS = {"openai", "anthropic", "google", "meta", "mistral", "cohere"}

# Compliance certifications ranked by rigor
_COMPLIANCE_WEIGHTS = {
    "hipaa": 20, "soc2": 15, "gdpr": 12, "iso27001": 18,
    "pci-dss": 15, "fedramp": 20, "ccpa": 8, "ferpa": 10,
}

# Grade breakpoints
_GRADE_MAP = [
    (90, "A+"), (85, "A"), (80, "A-"),
    (75, "B+"), (70, "B"), (65, "B-"),
    (60, "C+"), (55, "C"), (50, "C-"),
    (40, "D"),  (0,  "F"),
]


# ╔════════════════════════════════════════════════════════════════════╗
# ║  RESULT DATACLASS                                                 ║
# ╚════════════════════════════════════════════════════════════════════╝

@dataclass
class ResilienceReport:
    """Full verification result for a single tool."""
    tool_name: str
    score: int                  # 0–100
    grade: str                  # A+ through F
    dimensions: Dict[str, int]  # sub-scores per dimension
    flags: List[str]            # human-readable warnings
    tier: str                   # "sovereign" | "durable" | "moderate" | "fragile" | "wrapper"
    summary: str                # one-line verdict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "resilience_score": self.score,
            "grade": self.grade,
            "tier": self.tier,
            "dimensions": self.dimensions,
            "flags": self.flags,
            "summary": self.summary,
        }


def _letter_grade(score: int) -> str:
    for threshold, grade in _GRADE_MAP:
        if score >= threshold:
            return grade
    return "F"


def _tier_label(score: int) -> str:
    if score >= 85:
        return "sovereign"
    if score >= 70:
        return "durable"
    if score >= 50:
        return "moderate"
    if score >= 30:
        return "fragile"
    return "wrapper"


# ╔════════════════════════════════════════════════════════════════════╗
# ║  SCORING ENGINE                                                   ║
# ╚════════════════════════════════════════════════════════════════════╝

def score_tool(tool) -> ResilienceReport:
    """Compute the Anti-Wrapper Resilience Score for a single Tool object.

    Parameters
    ----------
    tool : Tool  (from tools.py)

    Returns
    -------
    ResilienceReport
    """
    flags: List[str] = []
    dims: Dict[str, int] = {}

    name_lower = tool.name.lower().strip()

    # ── 1. Native IP Signal (0–30) ──────────────────────────────────
    ip_score = 0
    if name_lower in _NATIVE_IP_SIGNALS or any(
        n in name_lower for n in _NATIVE_IP_SIGNALS
    ):
        ip_score = 25
    # Bonus: has documented use_cases (implies depth beyond wrapper)
    if len(tool.use_cases) >= 3:
        ip_score = min(30, ip_score + 5)
    # Penalty: known wrapper
    if name_lower in _KNOWN_WRAPPERS:
        ip_score = max(0, ip_score - 20)
        flags.append("⚠ Identified as thin API wrapper — low native IP")
    # Penalty: description hints at wrapper
    desc_lower = (tool.description or "").lower()
    wrapper_signals = ["wrapper", "built on top of openai", "powered by gpt",
                       "uses chatgpt", "openai api", "gpt-4 api"]
    if any(sig in desc_lower for sig in wrapper_signals):
        ip_score = max(0, ip_score - 10)
        flags.append("⚠ Description suggests upstream API dependency")
    dims["native_ip"] = ip_score

    # ── 2. Integration Depth (0–20) ─────────────────────────────────
    integ_count = len(tool.integrations)
    if integ_count >= 8:
        integ_score = 20
    elif integ_count >= 5:
        integ_score = 15
    elif integ_count >= 3:
        integ_score = 10
    elif integ_count >= 1:
        integ_score = 5
    else:
        integ_score = 0
        flags.append("⚠ No documented integrations — siloed tool")
    dims["integration_depth"] = integ_score

    # ── 3. Compliance Posture (0–15) ────────────────────────────────
    compliance_raw = 0
    for cert in tool.compliance:
        compliance_raw += _COMPLIANCE_WEIGHTS.get(cert.lower(), 5)
    compliance_score = min(15, int(compliance_raw * 15 / 35))  # normalize
    if not tool.compliance:
        flags.append("⚠ No compliance certifications documented")
    dims["compliance"] = compliance_score

    # ── 4. Pricing Sustainability (0–15) ────────────────────────────
    pricing = tool.pricing or {}
    pricing_score = 0
    has_free = pricing.get("free_tier", False)
    starter = pricing.get("starter") or pricing.get("pro") or 0
    enterprise = pricing.get("enterprise")

    if has_free:
        pricing_score += 3  # freemium = low barrier
    if isinstance(starter, (int, float)) and starter > 0:
        pricing_score += 4  # paid tier = revenue to fund R&D
    if enterprise == "custom" or (isinstance(enterprise, (int, float)) and enterprise > 100):
        pricing_score += 5  # enterprise tier = serious product
    # Penalty: absurdly cheap (margin looks like pure API pass-through)
    if isinstance(starter, (int, float)) and 0 < starter < 5:
        pricing_score = max(0, pricing_score - 3)
        flags.append("⚠ Very low pricing suggests thin margin / API arbitrage")
    pricing_score = min(15, pricing_score + 3)  # base credit
    dims["pricing_sustainability"] = pricing_score

    # ── 5. Data Portability (0–10) ──────────────────────────────────
    # Phase 1 heuristic: tools with >= intermediate skill + integrations
    # are more likely to support data export
    portability_score = 5  # baseline
    if integ_count >= 5:
        portability_score += 3
    if tool.skill_level == "advanced":
        portability_score += 2
    elif tool.skill_level == "intermediate":
        portability_score += 1
    portability_score = min(10, portability_score)
    dims["data_portability"] = portability_score

    # ── 6. Ecosystem Lock-in Risk (0–10) ────────────────────────────
    # Lower is better here, but we score as "freedom from lock-in"
    lockin_score = 7  # start optimistic
    # Penalty if only integrates with one ecosystem
    if integ_count <= 1:
        lockin_score -= 4
    # Penalty if tool name matches an upstream provider (e.g., "OpenAI GPT Wrapper")
    for provider in _UPSTREAM_PROVIDERS:
        if provider in name_lower and name_lower not in _NATIVE_IP_SIGNALS:
            lockin_score -= 3
            flags.append(f"⚠ Name implies dependency on {provider} infrastructure")
            break
    # Bonus: multi-language/platform support
    if len(tool.languages) >= 2:
        lockin_score = min(10, lockin_score + 2)
    lockin_score = max(0, min(10, lockin_score))
    dims["ecosystem_freedom"] = lockin_score

    # ── AGGREGATE ────────────────────────────────────────────────────
    total = sum(dims.values())
    total = max(0, min(100, total))
    grade = _letter_grade(total)
    tier = _tier_label(total)

    # Build summary
    if tier == "sovereign":
        summary = f"{tool.name} demonstrates strong native IP, deep integrations, and verified compliance — a durable platform choice."
    elif tier == "durable":
        summary = f"{tool.name} is a solid, well-integrated tool with good long-term viability."
    elif tier == "moderate":
        summary = f"{tool.name} shows adequate resilience but has gaps in integration depth or compliance documentation."
    elif tier == "fragile":
        summary = f"{tool.name} carries significant dependency risk — evaluate alternatives before committing."
    else:
        summary = f"{tool.name} appears to be a thin wrapper with minimal proprietary logic — high vendor risk."

    return ResilienceReport(
        tool_name=tool.name,
        score=total,
        grade=grade,
        tier=tier,
        dimensions=dims,
        flags=flags,
        summary=summary,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  BATCH SCORING                                                    ║
# ╚════════════════════════════════════════════════════════════════════╝

def score_all_tools(tools_list: list) -> List[ResilienceReport]:
    """Score every tool and return sorted by resilience (highest first)."""
    reports = [score_tool(t) for t in tools_list]
    reports.sort(key=lambda r: r.score, reverse=True)
    return reports


def tier_distribution(tools_list: list) -> Dict[str, int]:
    """Return count of tools per resilience tier."""
    dist: Dict[str, int] = {"sovereign": 0, "durable": 0, "moderate": 0, "fragile": 0, "wrapper": 0}
    for t in tools_list:
        report = score_tool(t)
        dist[report.tier] = dist.get(report.tier, 0) + 1
    return dist


# ╔════════════════════════════════════════════════════════════════════╗
# ║  TUESDAY TEST ROI SIMULATOR                                       ║
# ╚════════════════════════════════════════════════════════════════════╝

# Regional wage data (BLS 2025 averages, $/hour)
REGIONAL_WAGES = {
    "midwest": {"admin": 22.50, "manager": 38.00, "specialist": 45.00, "executive": 65.00},
    "southeast": {"admin": 20.00, "manager": 35.00, "specialist": 42.00, "executive": 60.00},
    "northeast": {"admin": 26.00, "manager": 45.00, "specialist": 55.00, "executive": 78.00},
    "west": {"admin": 28.00, "manager": 48.00, "specialist": 58.00, "executive": 82.00},
    "southwest": {"admin": 21.00, "manager": 36.00, "specialist": 43.00, "executive": 62.00},
    "default": {"admin": 24.00, "manager": 40.00, "specialist": 48.00, "executive": 70.00},
}

# Average tool costs per month by category
_TYPICAL_TOOL_COSTS = {
    "automation": 35, "marketing": 40, "writing": 15, "design": 15,
    "coding": 20, "analytics": 45, "sales": 50, "support": 30,
    "video": 25, "productivity": 12, "email": 20, "data": 40,
    "security": 35, "accounting": 25, "no-code": 20, "default": 25,
}


@dataclass
class TuesdayTestResult:
    """Result of the 'Tuesday Test' ROI simulation."""
    region: str
    role: str
    hourly_wage: float
    task_description: str
    hours_per_week_manual: float
    error_rate_manual: float
    tool_category: str
    estimated_tool_cost_monthly: float

    # Computed
    hours_saved_weekly: float = 0.0
    hours_saved_monthly: float = 0.0
    labor_savings_monthly: float = 0.0
    error_cost_reduction_monthly: float = 0.0
    net_monthly_savings: float = 0.0
    break_even_days: float = 0.0
    annual_savings: float = 0.0
    roi_percentage: float = 0.0
    tuesday_verdict: str = ""
    confidence: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region": self.region,
            "role": self.role,
            "hourly_wage": self.hourly_wage,
            "task_description": self.task_description,
            "hours_per_week_manual": self.hours_per_week_manual,
            "estimated_tool_cost_monthly": self.estimated_tool_cost_monthly,
            "hours_saved_weekly": round(self.hours_saved_weekly, 1),
            "hours_saved_monthly": round(self.hours_saved_monthly, 1),
            "labor_savings_monthly": round(self.labor_savings_monthly, 2),
            "error_cost_reduction_monthly": round(self.error_cost_reduction_monthly, 2),
            "net_monthly_savings": round(self.net_monthly_savings, 2),
            "break_even_days": round(self.break_even_days, 1),
            "annual_savings": round(self.annual_savings, 2),
            "roi_percentage": round(self.roi_percentage, 1),
            "tuesday_verdict": self.tuesday_verdict,
            "confidence": self.confidence,
        }


def tuesday_test(
    region: str = "midwest",
    role: str = "admin",
    task_description: str = "manual data entry",
    hours_per_week_manual: float = 8.0,
    error_rate_manual: float = 0.05,
    tool_category: str = "automation",
    tool_cost_override: Optional[float] = None,
) -> TuesdayTestResult:
    """Run the 'Tuesday Test' ROI simulation.

    Models the real-world impact of automating a specific task,
    using localized wage data and conservative automation estimates.

    Parameters
    ----------
    region              : Geographic region for wage lookup.
    role                : Job role (admin, manager, specialist, executive).
    task_description    : Free-text description of the task being automated.
    hours_per_week_manual : Hours currently spent per week on this task.
    error_rate_manual   : Current human error rate (0.0–1.0).
    tool_category       : Category of AI tool to estimate cost.
    tool_cost_override  : Override the estimated monthly tool cost.
    """
    # Resolve wage
    wages = REGIONAL_WAGES.get(region.lower(), REGIONAL_WAGES["default"])
    hourly = wages.get(role.lower(), wages.get("admin", 24.0))

    # Resolve tool cost
    tool_cost = tool_cost_override or _TYPICAL_TOOL_COSTS.get(
        tool_category.lower(), _TYPICAL_TOOL_COSTS["default"]
    )

    # Conservative automation efficiency: 65% time reduction
    automation_efficiency = 0.65
    hours_saved_weekly = hours_per_week_manual * automation_efficiency
    hours_saved_monthly = hours_saved_weekly * 4.33

    # Labor savings
    labor_savings = hours_saved_monthly * hourly

    # Error cost reduction (assume each error costs 30 min to fix)
    tasks_per_week = max(1, hours_per_week_manual * 2)  # rough estimate
    errors_per_month_before = tasks_per_week * 4.33 * error_rate_manual
    errors_per_month_after = tasks_per_week * 4.33 * (error_rate_manual * 0.2)  # 80% error reduction
    error_cost_reduction = (errors_per_month_before - errors_per_month_after) * (hourly * 0.5)

    # Net savings
    net_monthly = labor_savings + error_cost_reduction - tool_cost
    annual = net_monthly * 12

    # Break-even
    if net_monthly > 0:
        break_even = tool_cost / (net_monthly + tool_cost) * 30  # days
    else:
        break_even = 999  # never breaks even

    # ROI
    roi_pct = (net_monthly / max(tool_cost, 1)) * 100

    # Tuesday verdict
    if net_monthly >= hourly * 20:
        verdict = "Transformative — this automation pays for a part-time hire"
        confidence = "high"
    elif net_monthly >= hourly * 8:
        verdict = "Strong win — saves a full workday per week"
        confidence = "high"
    elif net_monthly >= tool_cost * 2:
        verdict = "Clear positive — tool pays for itself 2×+"
        confidence = "medium"
    elif net_monthly > 0:
        verdict = "Marginally positive — consider a free-tier alternative first"
        confidence = "low"
    else:
        verdict = "Fails the Tuesday Test — this tool adds cost without proportionate relief"
        confidence = "low"

    return TuesdayTestResult(
        region=region,
        role=role,
        hourly_wage=hourly,
        task_description=task_description,
        hours_per_week_manual=hours_per_week_manual,
        error_rate_manual=error_rate_manual,
        tool_category=tool_category,
        estimated_tool_cost_monthly=tool_cost,
        hours_saved_weekly=hours_saved_weekly,
        hours_saved_monthly=hours_saved_monthly,
        labor_savings_monthly=labor_savings,
        error_cost_reduction_monthly=error_cost_reduction,
        net_monthly_savings=net_monthly,
        break_even_days=break_even,
        annual_savings=annual,
        roi_percentage=roi_pct,
        tuesday_verdict=verdict,
        confidence=confidence,
    )


# ╔════════════════════════════════════════════════════════════════════╗
# ║  RFP GENERATOR                                                    ║
# ╚════════════════════════════════════════════════════════════════════╝

def generate_rfp(
    business_name: str,
    industry: str,
    team_size: str,
    workflow_description: str,
    selected_tools: List[str],
    budget_tier: str = "medium",
    compliance_requirements: Optional[List[str]] = None,
    constraints: Optional[List[str]] = None,
    tools_list: Optional[list] = None,
) -> Dict[str, Any]:
    """Generate a neutral, objective RFP document for ITSP bidding.

    Parameters
    ----------
    business_name           : Company name.
    industry                : Business vertical.
    team_size               : "solo" | "small" | "medium" | "large"
    workflow_description    : Natural language description of the workflow to automate.
    selected_tools          : Tool names from Praxis recommendations.
    budget_tier             : "free" | "low" | "medium" | "high"
    compliance_requirements : Required certifications (SOC2, HIPAA, etc.)
    constraints             : Hard constraints (self-hosted, air-gapped, etc.)
    tools_list              : Full Tool objects list for metadata enrichment.
    """
    compliance_reqs = compliance_requirements or []
    hard_constraints = constraints or []

    # Resolve tool metadata
    tool_details = []
    if tools_list:
        tools_by_name = {t.name.lower(): t for t in tools_list}
        for name in selected_tools:
            t = tools_by_name.get(name.lower())
            if t:
                report = score_tool(t)
                tool_details.append({
                    "name": t.name,
                    "category": ", ".join(t.categories[:3]),
                    "resilience_grade": report.grade,
                    "resilience_score": report.score,
                    "pricing": t.pricing,
                    "integrations": t.integrations[:5],
                    "compliance": t.compliance,
                    "skill_level": t.skill_level,
                })

    # Budget ranges
    budget_ranges = {
        "free": "$0/month (free-tier tools only)",
        "low": "$50–200/month",
        "medium": "$200–1,000/month",
        "high": "$1,000+/month (enterprise licensing acceptable)",
    }

    # Team size descriptions
    team_descriptions = {
        "solo": "1 person (owner-operator)",
        "small": "2–10 employees",
        "medium": "11–50 employees",
        "large": "50+ employees",
    }

    rfp = {
        "document_type": "Request for Proposal (RFP)",
        "generated_by": "Praxis — Neutral AI Workflow Advisor",
        "version": "1.0",
        "sections": {
            "1_business_overview": {
                "title": "Business Overview",
                "company": business_name,
                "industry": industry,
                "team_size": team_descriptions.get(team_size, team_size),
                "description": f"{business_name} is a {team_descriptions.get(team_size, team_size)} "
                               f"{industry} organization seeking to automate and optimize "
                               f"the following operational workflow.",
            },
            "2_scope_of_work": {
                "title": "Scope of Work",
                "workflow_objective": workflow_description,
                "target_tools": tool_details if tool_details else selected_tools,
                "integration_requirements": [
                    "All selected tools must integrate bidirectionally with existing business systems",
                    "Data must flow without manual CSV export/import steps",
                    "API-based connections required; no screen-scraping or RPA bridges",
                ],
            },
            "3_technical_requirements": {
                "title": "Technical Requirements",
                "data_format": "All data must be exportable to CSV/JSON/SQL at any time",
                "uptime_sla": "99.5% minimum monthly uptime",
                "latency": "API response time < 2 seconds for synchronous operations",
                "compliance": compliance_reqs if compliance_reqs else ["SOC2 Type II preferred"],
                "constraints": hard_constraints if hard_constraints else ["Cloud-hosted acceptable"],
                "security": [
                    "All data encrypted at rest (AES-256) and in transit (TLS 1.3)",
                    "No vendor access to raw business data without explicit written consent",
                    "Audit logs for all automated actions retained for minimum 12 months",
                ],
            },
            "4_budget_parameters": {
                "title": "Budget Parameters",
                "budget_range": budget_ranges.get(budget_tier, budget_ranges["medium"]),
                "includes": "Software licensing, initial setup, 90-day support",
                "excludes": "Hardware procurement, ongoing consulting retainers",
            },
            "5_evaluation_criteria": {
                "title": "Evaluation Criteria",
                "criteria": [
                    {"criterion": "Architectural resilience", "weight": "25%",
                     "note": "Preference for tools with Praxis Resilience Grade B+ or above"},
                    {"criterion": "Integration completeness", "weight": "25%",
                     "note": "Native bidirectional integrations; no manual middleware required"},
                    {"criterion": "Time to value", "weight": "20%",
                     "note": "Targeted deployment within 2 weeks; measurable ROI within 30 days"},
                    {"criterion": "Total cost of ownership", "weight": "15%",
                     "note": "Including hidden costs: training, maintenance, API overages"},
                    {"criterion": "Data portability", "weight": "15%",
                     "note": "Full data export capability; documented off-ramp procedure"},
                ],
            },
            "6_submission_requirements": {
                "title": "Submission Requirements",
                "format": "Proposals must be submitted in PDF format",
                "deadline": "14 calendar days from receipt of this RFP",
                "include": [
                    "Itemized cost breakdown (setup, monthly, per-seat)",
                    "Implementation timeline with milestones",
                    "References from similar-sized businesses in the same industry",
                    "Data off-ramp procedure documentation",
                    "Sample integration architecture diagram",
                ],
            },
        },
        "praxis_note": (
            "This RFP was generated by Praxis, a neutral AI workflow advisor. "
            "Praxis does not receive compensation from any vendor listed above. "
            "Tool recommendations are based solely on architectural resilience, "
            "integration compatibility, and verified ROI metrics."
        ),
    }

    return rfp
