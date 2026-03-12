# ------- Holds the Tool class -------

class Tool:
    """Represents an AI tool in the Praxis knowledge base.

    Core fields (original):
        name, description, categories, url, popularity, tags, keywords

    Decision-engine fields (Phase 1):
        pricing         – dict with tier info  {"free_tier": True, "starter": 12, "pro": 49, "enterprise": "custom"}
        integrations    – list of other tool names this connects with
        compliance      – list of standards/certifications  ["SOC2", "GDPR"]
        skill_level     – minimum user skill: "beginner" | "intermediate" | "advanced"
        use_cases       – concrete use-case strings  ["blog writing", "email campaigns"]
        stack_roles     – roles this tool can fill: "primary" | "companion" | "infrastructure" | "analytics"
        languages       – supported languages / platforms  ["python", "javascript", "no-code"]
    """

    def __init__(
        self,
        name,
        description,
        categories,
        url=None,
        popularity: int = 0,
        tags=None,
        keywords=None,
        # --- Phase 1 additions ---
        pricing=None,
        integrations=None,
        compliance=None,
        skill_level=None,
        use_cases=None,
        stack_roles=None,
        languages=None,
        # --- Phase 2 additions ---
        last_updated=None,
        # --- Phase 3: Sovereignty & Privacy (2026) ---
        country_of_origin=None,       # ISO 3166-1 alpha-3 (e.g. "USA", "GBR", "CHN")
        is_us_controlled=None,        # True if >51% US UBO + domestic infra
        high_risk_backend=None,       # True if deps on sanctioned/flagged entities
        zdr_compliant=None,           # True if Zero Data Retention enforced
        training_data_usage=None,     # "never" | "opt_out" | "opt_in"
        base_model=None,              # e.g. "GPT-4o", "Claude 3.5", "Llama 3", "proprietary"
        data_jurisdiction=None,       # Where user data is processed/stored
        # --- Phase 3: Outcome Metrics ---
        target_outcome_kpi=None,      # Primary KPI: "time_saved", "cost_reduction", etc.
        verified_roi_score=None,      # 0.0-1.0 empirical outcome confidence
        outcome_metrics=None,         # dict: {"time_saved_pct": 40, "error_reduction_pct": 25, ...}
        # --- Phase 4: Trust Badge Architecture (2026) ---
        uptime_tier=None,             # Uptime Institute tier 1-4
        psr_score=None,               # Prompt Success Rate 0.0-1.0
        oqs_score=None,               # Output Quality Score 0.0-1.0
        portability_score_val=None,   # Exit portability 1-10
    ):
        acronym_map = {
            "api": "API",
            "rag": "RAG",
            "llm": "LLM",
            "seo": "SEO",
            "wasm": "WASM",
            "hitl": "HITL",
        }

        def _normalize_tokens(values):
            normalized = []
            for token in (values or []):
                if isinstance(token, str):
                    normalized.append(acronym_map.get(token.lower(), token))
                else:
                    normalized.append(token)
            return normalized

        # Core
        self.name = name
        self.description = description
        self.categories = categories or []
        self.url = url
        self.popularity = int(popularity or 0)
        self.tags = _normalize_tokens(tags)
        self.keywords = _normalize_tokens(keywords)

        # Decision-engine extensions
        self.pricing = pricing or {}
        self.integrations = integrations or []
        self.compliance = compliance or []
        self.skill_level = skill_level or "beginner"
        self.use_cases = use_cases or []
        self.stack_roles = stack_roles or ["primary"]
        self.languages = languages or []

        # Freshness tracking — ISO date string "2026-02-20" or None
        self.last_updated = last_updated

        # Phase 3: Sovereignty & Privacy
        self.country_of_origin = country_of_origin or "USA"
        self.is_us_controlled = is_us_controlled if is_us_controlled is not None else True
        self.high_risk_backend = high_risk_backend if high_risk_backend is not None else False
        self.zdr_compliant = zdr_compliant if zdr_compliant is not None else False
        self.training_data_usage = training_data_usage or "opt_out"
        self.base_model = base_model
        self.data_jurisdiction = data_jurisdiction or "US"

        # Phase 3: Outcome Metrics
        self.target_outcome_kpi = target_outcome_kpi
        self.verified_roi_score = float(verified_roi_score) if verified_roi_score else 0.0
        self.outcome_metrics = outcome_metrics or {}

        # Phase 4: Trust Badge Architecture
        self.uptime_tier = int(uptime_tier) if uptime_tier else 0
        self.psr_score = float(psr_score) if psr_score else 0.0
        self.oqs_score = float(oqs_score) if oqs_score else 0.0
        self.portability_score_val = int(portability_score_val) if portability_score_val else 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def matches(self, intent_keywords):
        """Return a basic score based on keyword overlap with categories/tags/keywords."""
        score = 0
        for word in intent_keywords:
            w = word.lower()
            if any(w == c.lower() for c in self.categories):
                score += 2
            if any(w == t.lower() for t in self.tags):
                score += 2
            if any(w == k.lower() for k in self.keywords):
                score += 1
            if w in self.name.lower() or w in self.description.lower():
                score += 1
        return score

    def fits_budget(self, budget_tier: str) -> bool:
        """Check whether this tool is accessible at the given budget tier.

        Budget tiers: "free", "low" (≤$50), "medium" (≤$500), "high" (>$500)
        """
        if not self.pricing:
            return True  # unknown pricing → don't exclude
        if budget_tier == "high":
            return True
        if budget_tier == "free":
            return bool(self.pricing.get("free_tier"))
        if budget_tier == "low":
            starter = self.pricing.get("starter") or self.pricing.get("pro") or 0
            try:
                return bool(self.pricing.get("free_tier")) or (float(starter) <= 50)
            except (TypeError, ValueError):
                return True
        if budget_tier == "medium":
            pro = self.pricing.get("pro") or self.pricing.get("starter") or 0
            try:
                return bool(self.pricing.get("free_tier")) or (float(pro) <= 500)
            except (TypeError, ValueError):
                return True
        return True

    def fits_skill(self, user_skill: str) -> bool:
        """Check whether the tool is appropriate for the user's skill level."""
        levels = {"beginner": 0, "intermediate": 1, "advanced": 2}
        tool_level = levels.get(self.skill_level, 0)
        user_level = levels.get(user_skill, 0)
        return user_level >= tool_level

    def integrates_with(self, other_name: str) -> bool:
        """Return True if this tool lists *other_name* in its integrations."""
        return other_name.lower() in [i.lower() for i in self.integrations]

    def to_dict(self) -> dict:
        """Serialize to a plain dict (for JSON / API responses)."""
        return {
            "name": self.name,
            "description": self.description,
            "categories": self.categories,
            "url": self.url,
            "popularity": self.popularity,
            "tags": self.tags,
            "keywords": self.keywords,
            "pricing": self.pricing,
            "integrations": self.integrations,
            "compliance": self.compliance,
            "skill_level": self.skill_level,
            "use_cases": self.use_cases,
            "stack_roles": self.stack_roles,
            "languages": self.languages,
            "last_updated": self.last_updated,
            # Phase 3: Sovereignty & Privacy
            "country_of_origin": self.country_of_origin,
            "is_us_controlled": self.is_us_controlled,
            "high_risk_backend": self.high_risk_backend,
            "zdr_compliant": self.zdr_compliant,
            "training_data_usage": self.training_data_usage,
            "base_model": self.base_model,
            "data_jurisdiction": self.data_jurisdiction,
            # Phase 3: Outcome Metrics
            "target_outcome_kpi": self.target_outcome_kpi,
            "verified_roi_score": self.verified_roi_score,
            "outcome_metrics": self.outcome_metrics,
            # Phase 4: Trust Badge Architecture
            "uptime_tier": self.uptime_tier,
            "psr_score": self.psr_score,
            "oqs_score": self.oqs_score,
            "portability_score_val": self.portability_score_val,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Tool":
        """Reconstruct a Tool from a dict."""
        return cls(
            name=d.get("name", ""),
            description=d.get("description", ""),
            categories=d.get("categories", []),
            url=d.get("url"),
            popularity=d.get("popularity", 0),
            tags=d.get("tags", []),
            keywords=d.get("keywords", []),
            pricing=d.get("pricing"),
            integrations=d.get("integrations"),
            compliance=d.get("compliance"),
            skill_level=d.get("skill_level"),
            use_cases=d.get("use_cases"),
            stack_roles=d.get("stack_roles"),
            languages=d.get("languages"),
            last_updated=d.get("last_updated"),
            # Phase 3
            country_of_origin=d.get("country_of_origin"),
            is_us_controlled=d.get("is_us_controlled"),
            high_risk_backend=d.get("high_risk_backend"),
            zdr_compliant=d.get("zdr_compliant"),
            training_data_usage=d.get("training_data_usage"),
            base_model=d.get("base_model"),
            data_jurisdiction=d.get("data_jurisdiction"),
            target_outcome_kpi=d.get("target_outcome_kpi"),
            verified_roi_score=d.get("verified_roi_score"),
            outcome_metrics=d.get("outcome_metrics"),
            # Phase 4
            uptime_tier=d.get("uptime_tier"),
            psr_score=d.get("psr_score"),
            oqs_score=d.get("oqs_score"),
            portability_score_val=d.get("portability_score_val"),
        )

    def is_stale(self, max_days: int = 90) -> bool:
        """Return True if this tool's metadata hasn't been updated within max_days."""
        if not self.last_updated:
            return True  # no date recorded → assume stale
        try:
            from datetime import datetime, date
            updated = date.fromisoformat(self.last_updated)
            return (date.today() - updated).days > max_days
        except Exception:
            return True

    def __repr__(self):
        return f"{self.name}: {self.description}"

