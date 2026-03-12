# --------------- Praxis Configuration ---------------
"""
Centralized configuration for API keys, model settings, and feature flags.

Reads from environment variables first, then falls back to a local
``config.json`` file, then to sensible defaults.
"""

import json
import os
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent / "config.json"

# ------------------------------------------------------------------
# Defaults
# ------------------------------------------------------------------

DEFAULTS = {
    # LLM provider: "openai" | "anthropic" | "none" (rule-based fallback)
    "llm_provider": "none",
    # OpenAI
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    # Anthropic
    "anthropic_api_key": "",
    "anthropic_model": "claude-3-haiku-20240307",
    # Decision engine
    "default_top_n": 5,
    "stack_size": 3,
    # Feature flags
    "enable_llm_interpreter": False,
    "enable_learning_layer": True,
    "enable_stack_recommendations": True,
    # A/B testing: set False to disable learned-signal boosts for comparison
    "enable_learned_boosts": True,
    # Auto-learn: run learning cycle after this many new feedback entries
    "auto_learn_threshold": 10,
    # Scoring weights — tune these to shift ranking emphasis
    "weight_category_match": 4,
    "weight_tag_match": 3,
    "weight_keyword_match": 2,
    "weight_name_desc_match": 1,
    "weight_usecase_bonus": 1,
    "weight_fuzzy_name_strong": 3,
    "weight_fuzzy_name_weak": 1,
    "weight_fuzzy_desc_strong": 2,
    "weight_fuzzy_desc_weak": 1,
    "weight_tfidf_scale": 8,
    "weight_learned_boost": True,
    # Profile fit weights
    "weight_profile_budget_fit": 3,
    "weight_profile_budget_miss": -3,
    "weight_profile_skill_fit": 2,
    "weight_profile_skill_miss": -4,
    "weight_profile_integration": 3,
    "weight_profile_compliance_hit": 2,
    "weight_profile_compliance_miss": -2,
    "weight_profile_already_used": -2,
    # Rate limiting (requests per minute per IP)
    "rate_limit_rpm": 60,
    # Tool freshness: days before a tool is flagged stale
    "tool_freshness_days": 90,
    # Context-aware intent transfer — confidence formula weights
    "context_alpha": 0.25,          # term match weight
    "context_beta": 0.30,           # graph distance weight
    "context_gamma": 0.25,          # syntactic proximity weight
    "context_delta": 0.20,          # explicit match weight
    "context_tier1_threshold": 0.90, # auto-commit threshold
    "context_tier2_threshold": 0.60, # pre-fill threshold
    "context_auto_persist": True,    # auto-save T1 inferences to profile
    "context_max_gap_questions": 4,  # max residual gap questions per session
    # Praxis Room — elimination scope: "room" (default) or "global"
    "elimination_scope": "room",
}

# ------------------------------------------------------------------
# Loader
# ------------------------------------------------------------------

_cache: dict = {}


def _load_config_file() -> dict:
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def get(key: str, default=None):
    """Retrieve a config value.  Priority: env var → config.json → DEFAULTS."""
    if not _cache:
        _cache.update(DEFAULTS)
        _cache.update(_load_config_file())

    # Environment variables override everything (uppercased, prefixed PRAXIS_)
    env_key = f"PRAXIS_{key.upper()}"
    env_val = os.environ.get(env_key)
    if env_val is not None:
        # Attempt to parse booleans / ints
        if env_val.lower() in ("true", "1", "yes"):
            return True
        if env_val.lower() in ("false", "0", "no"):
            return False
        try:
            return int(env_val)
        except ValueError:
            return env_val

    return _cache.get(key, default)


def set_runtime(key: str, value):
    """Override a value for the current process lifetime."""
    _cache[key] = value


def save_config(overrides: dict):
    """Write overrides to the local config.json file."""
    existing = _load_config_file()
    existing.update(overrides)
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    _cache.update(overrides)


def llm_available() -> bool:
    """Return True if an LLM provider is configured and enabled."""
    if not get("enable_llm_interpreter"):
        return False
    provider = get("llm_provider")
    if provider == "openai" and get("openai_api_key"):
        return True
    if provider == "anthropic" and get("anthropic_api_key"):
        return True
    return False
