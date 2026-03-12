# --------------- Praxis Domain Models — Strict Pydantic v2 ---------------
"""
v18 · Enterprise-Grade Solidification

Canonical Pydantic v2 models that enforce strict type boundaries at the
domain layer.  Every external payload (LLM output, user input, API request)
is funnelled through these models before touching business logic.

Key design choices:
    • ``model_config = ConfigDict(strict=False)`` — allows harmless string→int
      coercion (the LLM often sends ``"42"`` instead of ``42``).
    • ``@field_validator`` decorators cross-reference live data where needed.
    • All models are immutable (``frozen=True``) unless explicitly marked
      otherwise, preventing silent mutation in concurrent contexts.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)


# -----------------------------------------------------------------------
# Enumerations
# -----------------------------------------------------------------------

class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class BudgetTier(str, Enum):
    FREE = "free"
    LOW = "low"          # ≤ $50/mo
    MEDIUM = "medium"    # ≤ $500/mo
    HIGH = "high"        # > $500/mo


class StackRole(str, Enum):
    PRIMARY = "primary"
    COMPANION = "companion"
    INFRASTRUCTURE = "infrastructure"
    ANALYTICS = "analytics"


class FeedbackAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    RATE = "rate"


class SecurityMaturity(str, Enum):
    """SOC2/ISO 27001 maturity tier for vendor trust scoring."""
    NONE = "none"
    BASIC = "basic"
    MODERATE = "moderate"
    HIGH = "high"
    CERTIFIED = "certified"


# -----------------------------------------------------------------------
# Tool Domain Model
# -----------------------------------------------------------------------

class ToolModel(BaseModel):
    """Canonical, validated representation of an AI tool."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    categories: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    popularity: int = Field(default=0, ge=0)
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    pricing: Dict[str, Any] = Field(default_factory=dict)
    integrations: List[str] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    skill_level: SkillLevel = SkillLevel.BEGINNER
    use_cases: List[str] = Field(default_factory=list)
    stack_roles: List[StackRole] = Field(default_factory=lambda: [StackRole.PRIMARY])
    languages: List[str] = Field(default_factory=list)
    last_updated: Optional[date] = None

    @field_validator("tags", "keywords", "categories", mode="before")
    @classmethod
    def _normalize_string_lists(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return [str(x) for x in (v or [])]

    @field_validator("url", mode="before")
    @classmethod
    def _validate_url(cls, v: Any) -> Optional[str]:
        if v is None or v == "":
            return None
        if isinstance(v, str) and not re.match(r"^https?://", v):
            return f"https://{v}"
        return v


# -----------------------------------------------------------------------
# User Profile
# -----------------------------------------------------------------------

class UserProfileModel(BaseModel):
    """Validated user profile for personalized recommendations."""

    model_config = ConfigDict(extra="ignore")

    profile_id: str = Field(..., min_length=1)
    industry: Optional[str] = None
    budget_tier: BudgetTier = BudgetTier.MEDIUM
    team_size: Optional[int] = Field(default=None, ge=1)
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE
    existing_tools: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------
# Intent (parsed from user query)
# -----------------------------------------------------------------------

class IntentModel(BaseModel):
    """Structured output from the Interpreter (LLM or rule-based)."""

    model_config = ConfigDict(extra="allow")

    raw_query: str = ""
    keywords: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    task_type: Optional[str] = None
    industry: Optional[str] = None
    budget_signal: Optional[BudgetTier] = None
    constraints: List[str] = Field(default_factory=list)
    negative_keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)

    @field_validator("keywords", "categories", "constraints", "negative_keywords", mode="before")
    @classmethod
    def _ensure_list(cls, v: Any) -> list:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return list(v or [])


# -----------------------------------------------------------------------
# Stack Recommendation
# -----------------------------------------------------------------------

class ToolRecommendation(BaseModel):
    """One tool within a recommended stack."""

    model_config = ConfigDict(extra="ignore")

    name: str
    role: StackRole = StackRole.PRIMARY
    fit_score: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)


class StackRecommendation(BaseModel):
    """A composed AI tool stack with explanation."""

    model_config = ConfigDict(extra="ignore")

    tools: List[ToolRecommendation] = Field(default_factory=list)
    narrative: str = ""
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------
# Feedback
# -----------------------------------------------------------------------

class FeedbackEvent(BaseModel):
    """User feedback on a recommendation."""

    model_config = ConfigDict(extra="ignore")

    tool_name: str = Field(..., min_length=1)
    action: FeedbackAction
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    query: str = ""
    profile_id: Optional[str] = None
    timestamp: Optional[datetime] = None


# -----------------------------------------------------------------------
# Vendor Trust Assessment
# -----------------------------------------------------------------------

class VendorTrustScore(BaseModel):
    """Enterprise-grade vendor maturity assessment."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    tool_name: str
    composite_score: float = Field(ge=0.0, le=1.0)
    soc2_compliant: bool = False
    gdpr_compliant: bool = False
    hipaa_compliant: bool = False
    iso27001_certified: bool = False
    update_frequency_days: Optional[int] = None
    open_cve_count: int = Field(default=0, ge=0)
    transparency_score: float = Field(default=0.0, ge=0.0, le=1.0)
    freedom_score: float = Field(default=0.0, ge=0.0, le=1.0)
    lock_in_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    maturity: SecurityMaturity = SecurityMaturity.NONE
    warnings: List[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def passed(self) -> bool:
        """Derived — no need to mutate the frozen model."""
        return self.composite_score >= 0.4 and self.open_cve_count <= 5


# -----------------------------------------------------------------------
# API Request / Response Envelopes
# -----------------------------------------------------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    profile_id: Optional[str] = None
    top_n: int = Field(default=5, ge=1, le=50)


class ReasonRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    profile_id: Optional[str] = None
    depth: int = Field(default=3, ge=1, le=10)


class APIResponse(BaseModel):
    """Standard envelope for all API responses."""

    model_config = ConfigDict(extra="allow")

    success: bool = True
    data: Any = None
    error: Optional[str] = None
    trace_id: Optional[str] = None
    latency_ms: Optional[float] = None


# -----------------------------------------------------------------------
# v23 — Praxis Room: Persistent Model-Agnostic Workspace
# -----------------------------------------------------------------------

class Room(BaseModel):
    """Persistent workspace anchoring multiple journey cycles.

    Maps to CoALA Semantic + Episodic memory layers.  Survives across
    sessions indefinitely.  ``operator_context`` stores a serialised
    ContextVector (via ``to_dict()``); we keep it as a plain dict here
    so ``context_engine.py`` does not need to become a Pydantic model.
    """

    model_config = ConfigDict(extra="ignore")

    room_id: str = Field(..., description="Unique immutable Room identifier (UUID4 hex)")
    name: str = Field(..., min_length=1, max_length=200,
                      description="Human-readable room name")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    updated_at: str = Field(..., description="ISO-8601 last-update timestamp")

    # Semantic memory — persistent operator baseline
    operator_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Serialised ContextVector (T1/T2/T3 tiers, sovereignty modifiers)")

    # Episodic memory — chronological journey log
    journey_history: List[str] = Field(
        default_factory=list,
        description="Ordered list of journey_ids executed in this room")

    # Elimination state
    active_eliminations: Dict[str, str] = Field(
        default_factory=dict,
        description="model_id → EliminationCode for permanently excluded models")

    # Budget
    budget_cap_usd: float = Field(default=50.0, ge=0.0,
                                  description="Hard expenditure ceiling for the room lifecycle")
    current_spend_usd: float = Field(default=0.0, ge=0.0,
                                     description="Accumulated cost across all sessions")

    # Lifecycle
    is_archived: bool = Field(default=False,
                              description="Soft-delete flag — removes room from active routing")


class RoomSession(BaseModel):
    """Ephemeral Working-memory container for one continuous interaction block.

    Created on connect, destroyed on disconnect or OUTCOME.
    Streaming buffers and temporary penalties are never persisted.
    """

    model_config = ConfigDict(extra="ignore")

    session_id: str = Field(..., description="Unique ephemeral session identifier")
    room_id: str = Field(..., description="FK to parent Room")
    started_at: str = Field(..., description="ISO-8601 session start")
    ended_at: Optional[str] = Field(default=None,
                                    description="ISO-8601 session end (None while active)")

    active_journey_id: Optional[str] = Field(
        default=None,
        description="Currently executing journey (from journey.py)")

    # Transient — never written to SQLite
    streaming_buffers: Dict[str, str] = Field(
        default_factory=dict,
        description="model_id → partial token buffer for live UI rendering")
    temporary_penalties: Dict[str, float] = Field(
        default_factory=dict,
        description="Soft routing penalties from trust_decay, scoped to this session only")


class RoomArtifact(BaseModel):
    """Persistent output deliverable produced within a Room.

    Versioned — Fan-Out may create multiple versions of the same artifact
    from different models.
    """

    model_config = ConfigDict(extra="ignore")

    artifact_id: str = Field(..., description="Unique artifact identifier")
    room_id: str = Field(...)
    journey_id: str = Field(..., description="Journey that produced this artifact")

    title: str = Field(..., min_length=1, max_length=500)
    content_type: str = Field(..., description="MIME type or custom Praxis type")
    content: str = Field(..., description="Raw artifact payload")

    version: int = Field(default=1, ge=1)
    parent_artifact_id: Optional[str] = Field(
        default=None,
        description="Previous version if this is an LLM refinement")

    created_by_model: str = Field(...,
                                  description="LLM that generated this artifact")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")


class ContextBundle(BaseModel):
    """Immutable payload delivered to an LLM connector for one execution step.

    Gives the model longitudinal room awareness: who was eliminated and
    why, what collaboration pattern is active, and the role it must play.
    """

    model_config = ConfigDict(extra="ignore")

    room_id: str = Field(...)
    journey_id: str = Field(...)

    raw_transcript: str = Field(..., description="Conversational history string")
    structured_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Serialised ContextVector with T1/T2/T3 data")

    elimination_summary: List[str] = Field(
        default_factory=list,
        description="System-level notices to the model about eliminated alternatives")

    pattern_type: str = Field(default="single",
                              description="Active topology: sequential, fan_out, specialist, adversarial")
    role_instruction: str = Field(default="",
                                  description="Dynamic system prompt tailored to the ecosystem pattern")


class RoutingExplanation(BaseModel):
    """Surfaces the elimination engine's decision matrix to the UI."""

    model_config = ConfigDict(extra="ignore")

    decision_id: str = Field(..., description="Unique routing decision identifier")
    selected_model: str = Field(..., description="Chosen LLM for this execution")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    eliminated_models: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="EliminationEntry dicts from differential / model_router")
    trust_signals_applied: List[str] = Field(
        default_factory=list,
        description="Trust decay alerts that influenced routing")
    cost_estimate_usd: float = Field(default=0.0, ge=0.0)

    override_eligible: bool = Field(
        default=True,
        description="Whether the operator may force a different model")
