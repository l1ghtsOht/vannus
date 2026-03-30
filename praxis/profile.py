# --------------- User Profile Management ---------------
"""
Captures and persists user context so the decision engine can make
profile-aware recommendations.

A profile contains:
    industry        – e.g. "startup", "e-commerce", "healthcare"
    budget          – spending tier: "free" | "low" | "medium" | "high"
    team_size       – "solo" | "small" (2-10) | "medium" (11-50) | "large" (50+)
    skill_level     – "beginner" | "intermediate" | "advanced"
    existing_tools  – list of tool names the user already uses
    goals           – list of high-level goals: "growth", "automation", "cost reduction"
    constraints     – list of hard requirements: "HIPAA", "GDPR", "SOC2", "self-hosted"
    preferences     – free-form dict for future extensibility
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.profile")

_DATA_DIR = os.environ.get("PRAXIS_DATA_DIR", "")
PROFILES_FILE = os.path.join(_DATA_DIR, "profiles.json") if _DATA_DIR else "profiles.json"


# ------------------------------------------------------------------
# Data class
# ------------------------------------------------------------------

class UserProfile:
    """Structured representation of a user's context."""

    VALID_BUDGETS = {"free", "low", "medium", "high"}
    VALID_SKILLS = {"beginner", "intermediate", "advanced"}
    VALID_TEAM_SIZES = {"solo", "small", "medium", "large"}

    def __init__(
        self,
        profile_id: str = "default",
        industry: str = "",
        budget: str = "medium",
        team_size: str = "solo",
        skill_level: str = "beginner",
        existing_tools: Optional[List[str]] = None,
        goals: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        preferences: Optional[Dict] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        # ── 2026 Security Blueprint Fields ──
        requires_us_sovereignty: bool = False,
        strict_privacy_mode: bool = False,
        sovereignty_tier_preference: Optional[str] = None,
    ):
        self.profile_id = profile_id
        self.industry = industry
        self.budget = budget if budget in self.VALID_BUDGETS else "medium"
        self.team_size = team_size if team_size in self.VALID_TEAM_SIZES else "solo"
        self.skill_level = skill_level if skill_level in self.VALID_SKILLS else "beginner"
        self.existing_tools = existing_tools or []
        self.goals = goals or []
        self.constraints = constraints or []
        self.preferences = preferences or {}
        self.created_at = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.updated_at = updated_at or self.created_at
        # ── 2026 Security Blueprint ──
        self.requires_us_sovereignty = requires_us_sovereignty
        self.strict_privacy_mode = strict_privacy_mode
        self.sovereignty_tier_preference = sovereignty_tier_preference  # "us_controlled" | "allied" | None

    # ---- serialization ----

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "industry": self.industry,
            "budget": self.budget,
            "team_size": self.team_size,
            "skill_level": self.skill_level,
            "existing_tools": self.existing_tools,
            "goals": self.goals,
            "constraints": self.constraints,
            "preferences": self.preferences,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "requires_us_sovereignty": self.requires_us_sovereignty,
            "strict_privacy_mode": self.strict_privacy_mode,
            "sovereignty_tier_preference": self.sovereignty_tier_preference,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UserProfile":
        return cls(
            profile_id=d.get("profile_id", "default"),
            industry=d.get("industry", ""),
            budget=d.get("budget", "medium"),
            team_size=d.get("team_size", "solo"),
            skill_level=d.get("skill_level", "beginner"),
            existing_tools=d.get("existing_tools"),
            goals=d.get("goals"),
            constraints=d.get("constraints"),
            preferences=d.get("preferences"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            requires_us_sovereignty=d.get("requires_us_sovereignty", False),
            strict_privacy_mode=d.get("strict_privacy_mode", False),
            sovereignty_tier_preference=d.get("sovereignty_tier_preference"),
        )

    def update(self, **kwargs):
        """Merge new values into the profile and bump updated_at."""
        for key, val in kwargs.items():
            if hasattr(self, key) and val is not None:
                setattr(self, key, val)
        self.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ---- convenience queries ----

    def requires_compliance(self, standard: str) -> bool:
        return standard.upper() in [c.upper() for c in self.constraints]

    def already_uses(self, tool_name: str) -> bool:
        return tool_name.lower() in [t.lower() for t in self.existing_tools]

    def __repr__(self):
        return (
            f"UserProfile(id={self.profile_id!r}, industry={self.industry!r}, "
            f"budget={self.budget!r}, skill={self.skill_level!r}, "
            f"team={self.team_size!r}, tools={self.existing_tools})"
        )


# ------------------------------------------------------------------
# Persistence helpers
# ------------------------------------------------------------------

def _profiles_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), PROFILES_FILE)


def _load_all() -> dict:
    p = _profiles_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_all(data: dict):
    with open(_profiles_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_profile(profile: UserProfile):
    """Persist a profile (upsert by profile_id)."""
    data = _load_all()
    profile.updated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    data[profile.profile_id] = profile.to_dict()
    _save_all(data)
    return profile


def load_profile(profile_id: str = "default") -> Optional[UserProfile]:
    """Load a profile by ID. Returns None if not found."""
    data = _load_all()
    entry = data.get(profile_id)
    if entry:
        return UserProfile.from_dict(entry)
    return None


def list_profiles() -> List[str]:
    """Return all stored profile IDs."""
    return list(_load_all().keys())


def delete_profile(profile_id: str) -> bool:
    data = _load_all()
    if profile_id in data:
        del data[profile_id]
        _save_all(data)
        return True
    return False


# ------------------------------------------------------------------
# Context-Aware Profile Hydration
# ------------------------------------------------------------------

def hydrate_profile(
    profile: UserProfile,
    context_vector,
    *,
    user_confirmed: bool = False,
) -> Dict[str, Any]:
    """Merge context-inferred fields into a user profile with PII guardrails.

    Args:
        profile:          The UserProfile to hydrate.
        context_vector:   ContextVector from context_engine.
        user_confirmed:   If True, persist T1 fields immediately.

    Returns:
        Dict with 'updated_fields' (persisted) and 'staged_fields' (need confirmation).
    """
    # PII guardrail: screen all values before profile serialisation
    pii_masker = None
    try:
        from .guardrails import PIIMasker
        pii_masker = PIIMasker()
    except Exception:
        try:
            from praxis.guardrails import PIIMasker  # type: ignore
            pii_masker = PIIMasker()
        except Exception:
            pass

    updated_fields: Dict[str, Any] = {}
    staged_fields: Dict[str, Any] = {}

    field_to_attr = {
        "industry": "industry",
        "budget": "budget",
        "team_size": "team_size",
        "skill_level": "skill_level",
        "existing_tools": "existing_tools",
    }

    for field_name, attr_name in field_to_attr.items():
        fe = context_vector.all_fields.get(field_name)
        if fe is None or fe.value is None:
            continue

        # PII check on the value
        value = fe.value
        if pii_masker is not None:
            val_str = str(value) if not isinstance(value, str) else value
            result = pii_masker.handle(val_str)
            if hasattr(result, "verdict") and str(result.verdict) != "Verdict.PASS":
                log.warning("PII detected in field %s — blocking hydration", field_name)
                continue

        if fe.tier == 1:  # T1 — auto-commit
            if user_confirmed or _cfg_get("context_auto_persist", True):
                setattr(profile, attr_name, value)
                updated_fields[field_name] = value
            else:
                staged_fields[field_name] = {"value": value, "confidence": fe.confidence}
        elif fe.tier == 2:  # T2 — stage for confirmation
            staged_fields[field_name] = {"value": value, "confidence": fe.confidence}

    # Compliance → constraints if detected
    comp_fe = context_vector.all_fields.get("compliance")
    if comp_fe and comp_fe.value and isinstance(comp_fe.value, list):
        existing_constraints = set(profile.constraints)
        new_constraints = [c for c in comp_fe.value if c not in existing_constraints]
        if new_constraints and (comp_fe.tier == 1 or user_confirmed):
            profile.constraints = profile.constraints + new_constraints
            updated_fields["constraints"] = new_constraints

    # Persist if any T1 fields were applied
    if updated_fields:
        save_profile(profile)
        log.info("Profile %s hydrated: %s", profile.profile_id, list(updated_fields.keys()))

    return {
        "updated_fields": updated_fields,
        "staged_fields": staged_fields,
        "profile_id": profile.profile_id,
    }


def _cfg_get(key, fallback):
    try:
        from . import config as _cfg_mod
        return _cfg_mod.get(key, fallback)
    except Exception:
        return fallback


# ------------------------------------------------------------------
# CLI helper — interactive profile builder
# ------------------------------------------------------------------

def build_profile_interactive(profile_id: str = "default") -> UserProfile:
    """Walk the user through creating / updating a profile via CLI prompts."""
    existing = load_profile(profile_id)
    if existing:
        print(f"\nExisting profile found: {existing}")
        update = input("Update this profile? (y/n): ").strip().lower()
        if not update.startswith("y"):
            return existing

    print("\n--- Build Your Profile ---")

    industry = input("Industry (e.g. startup, e-commerce, healthcare, agency, saas): ").strip().lower() or "general"

    budget_input = input("Monthly AI-tool budget — free / low ($0-50) / medium ($50-500) / high ($500+): ").strip().lower()
    budget = budget_input if budget_input in UserProfile.VALID_BUDGETS else "medium"

    team_input = input("Team size — solo / small (2-10) / medium (11-50) / large (50+): ").strip().lower()
    team_size = team_input if team_input in UserProfile.VALID_TEAM_SIZES else "solo"

    skill_input = input("Technical skill level — beginner / intermediate / advanced: ").strip().lower()
    skill_level = skill_input if skill_input in UserProfile.VALID_SKILLS else "beginner"

    existing_tools_raw = input("Tools you already use (comma-separated, or blank): ").strip()
    existing_tools = [t.strip() for t in existing_tools_raw.split(",") if t.strip()] if existing_tools_raw else []

    goals_raw = input("Goals — e.g. growth, automation, cost reduction (comma-separated): ").strip()
    goals = [g.strip() for g in goals_raw.split(",") if g.strip()] if goals_raw else []

    constraints_raw = input("Hard requirements — e.g. HIPAA, GDPR, SOC2, self-hosted (comma-separated, or blank): ").strip()
    constraints = [c.strip().upper() for c in constraints_raw.split(",") if c.strip()] if constraints_raw else []

    profile = UserProfile(
        profile_id=profile_id,
        industry=industry,
        budget=budget,
        team_size=team_size,
        skill_level=skill_level,
        existing_tools=existing_tools,
        goals=goals,
        constraints=constraints,
    )
    save_profile(profile)
    print(f"\nProfile saved: {profile}")
    return profile


# ======================================================================
# Differential Diagnosis — Constraint Matrix
# ======================================================================

# Compliance mandates that serve as hard elimination filters
_COMPLIANCE_MANDATES = {"HIPAA", "SOC2", "GDPR", "ISO27001", "PCI-DSS",
                        "FERPA", "CCPA", "FedRAMP"}

# Deployment constraints that serve as hard elimination filters
_DEPLOYMENT_HARD = {"self-hosted", "on-premise", "air-gapped", "sovereign-vpc"}

# Industries that auto-escalate risk tolerance to "low"
_REGULATED_INDUSTRIES = {"healthcare", "finance", "legal", "defense",
                         "government", "insurance", "banking", "pharma"}

# Budget tier → maximum monthly spend ($)
_BUDGET_CEILINGS = {
    "free": 0,
    "low": 50,
    "medium": 500,
    "high": float("inf"),
}

VALID_RISK_TOLERANCES = {"low", "medium", "high"}


def build_constraint_matrix(profile: UserProfile) -> dict:
    """
    Transform a UserProfile into an executable Constraint Matrix for
    the differential diagnosis pipeline.

    The matrix separates hard constraints (Boolean eliminators) from
    soft preferences (penalty modifiers), enabling the engine to
    apply deterministic pruning first, then probabilistic penalisation.

    Returns:
        {
            "profile_id": str,
            "risk_tolerance": "low" | "medium" | "high",
            "hard_constraints": {
                "budget_ceiling": float | None,
                "compliance_mandates": [str],
                "deployment_requirements": [str],
                "existing_tools": [str],
                "excluded_tools": [str],
            },
            "soft_preferences": {
                "preferred_skill_level": str,
                "team_size": str,
                "industry": str,
                "goals": [str],
                "resilience_floor": str | None,
                "max_acceptable_lock_in": str | None,
            },
            "inferred_flags": {
                "is_regulated": bool,
                "is_mission_critical": bool,
                "is_cost_sensitive": bool,
                "auto_escalated_risk": bool,
            },
        }
    """
    prefs = profile.preferences or {}
    constraints = [c.upper() for c in profile.constraints]
    constraints_lower = [c.lower() for c in profile.constraints]
    industry = (profile.industry or "").lower()

    # ── Risk Tolerance ──
    explicit_risk = prefs.get("risk_tolerance", "medium")
    if explicit_risk not in VALID_RISK_TOLERANCES:
        explicit_risk = "medium"

    auto_escalated = False

    # Auto-escalate for regulated industries
    if industry in _REGULATED_INDUSTRIES:
        if explicit_risk != "low":
            explicit_risk = "low"
            auto_escalated = True

    # Auto-escalate for compliance-heavy profiles
    compliance_mandates = [c for c in constraints if c in _COMPLIANCE_MANDATES]
    if len(compliance_mandates) >= 2 and explicit_risk != "low":
        explicit_risk = "low"
        auto_escalated = True

    # ── Hard Constraints ──
    budget_ceiling = _BUDGET_CEILINGS.get(profile.budget, 500)
    deployment_reqs = [c for c in constraints_lower if c in _DEPLOYMENT_HARD]
    excluded = [t.lower() for t in prefs.get("excluded_tools", [])]

    # ── Soft Preferences ──
    resilience_floor = prefs.get("resilience_floor")  # e.g. "durable"
    max_lock_in = prefs.get("max_lock_in")  # e.g. "medium"

    # ── Inferred Flags ──
    is_regulated = industry in _REGULATED_INDUSTRIES or len(compliance_mandates) > 0
    is_mission_critical = any(
        g.lower() in {"uptime", "reliability", "mission-critical", "compliance"}
        for g in profile.goals
    )
    is_cost_sensitive = profile.budget in ("free", "low")

    return {
        "profile_id": profile.profile_id,
        "risk_tolerance": explicit_risk,
        "hard_constraints": {
            "budget_ceiling": budget_ceiling if budget_ceiling < float("inf") else None,
            "compliance_mandates": compliance_mandates,
            "deployment_requirements": deployment_reqs,
            "existing_tools": [t.lower() for t in profile.existing_tools],
            "excluded_tools": excluded,
        },
        "soft_preferences": {
            "preferred_skill_level": profile.skill_level,
            "team_size": profile.team_size,
            "industry": industry,
            "goals": profile.goals,
            "resilience_floor": resilience_floor,
            "max_acceptable_lock_in": max_lock_in,
        },
        "inferred_flags": {
            "is_regulated": is_regulated,
            "is_mission_critical": is_mission_critical,
            "is_cost_sensitive": is_cost_sensitive,
            "auto_escalated_risk": auto_escalated,
        },
        # ── 2026 Security Blueprint: Sovereignty Constraints ──
        "sovereignty": {
            "requires_us_sovereignty": getattr(profile, "requires_us_sovereignty", False),
            "strict_privacy_mode": getattr(profile, "strict_privacy_mode", False),
            "sovereignty_tier_preference": getattr(profile, "sovereignty_tier_preference", None),
            "mandate_zdr": getattr(profile, "strict_privacy_mode", False) or is_regulated,
        },
    }
