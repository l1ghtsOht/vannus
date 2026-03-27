# ---------------- Decision Engine ----------------
"""
Core scoring & ranking logic for Praxis.

Responsibilities:
    • score_tool()  — multi-signal scoring for a single tool
    • find_tools()  — search + rank + optional profile filtering
    • score_profile_fit() — additional scoring based on user profile

The engine is intentionally kept as a pure-function module so it can be
used by both the CLI and the stack composer without side effects.
"""

try:
    from .data import TOOLS
except ImportError:
    from praxis.data import TOOLS
try:
    from . import config as _cfg
except ImportError:
    try:
        import config as _cfg
    except ImportError:
        _cfg = None
import logging
log = logging.getLogger("praxis.engine")

# Diagnostics — query failure tracking
try:
    from .diagnostics import record_failure as _record_failure, MIN_RESULTS_THRESHOLD, LOW_SCORE_THRESHOLD
    _DIAG_AVAILABLE = True
except ImportError:
    try:
        from praxis.diagnostics import record_failure as _record_failure, MIN_RESULTS_THRESHOLD, LOW_SCORE_THRESHOLD
        _DIAG_AVAILABLE = True
    except ImportError:
        _DIAG_AVAILABLE = False


def _w(key: str, fallback):
    """Read a scoring weight from config, fall back to hardcoded default."""
    if _cfg:
        try:
            return _cfg.get(key, fallback)
        except Exception:
            pass
    return fallback

# Import intelligence layer
try:
    from .intelligence import (
        get_tfidf_index, get_learned_boost, get_industry_boost,
        diversity_rerank, initialize as _init_intelligence,
    )
    _INTEL_AVAILABLE = True
except ImportError:
    try:
        from praxis.intelligence import (
            get_tfidf_index, get_learned_boost, get_industry_boost,
            diversity_rerank, initialize as _init_intelligence,
        )
        _INTEL_AVAILABLE = True
    except ImportError:
        _INTEL_AVAILABLE = False

# Initialize intelligence on first import
if _INTEL_AVAILABLE:
    try:
        _init_intelligence(TOOLS)
    except Exception as exc:
        log.warning("Intelligence init failed (permanently disabled): %s", exc)
        _INTEL_AVAILABLE = False

# ── 2026 Security Blueprint: Sovereignty scoring ──
try:
    from .sovereignty import sovereignty_score_modifier as _sov_mod, filter_by_sovereignty as _sov_filter
    _SOVEREIGNTY_AVAILABLE = True
except ImportError:
    try:
        from praxis.sovereignty import sovereignty_score_modifier as _sov_mod, filter_by_sovereignty as _sov_filter
        _SOVEREIGNTY_AVAILABLE = True
    except ImportError:
        _SOVEREIGNTY_AVAILABLE = False

# ── 2026 Trust Badge Architecture: Badge-aware scoring ──
try:
    from .trust_badges import calculate_all_badges as _calc_badges
    _BADGES_AVAILABLE = True
except ImportError:
    try:
        from praxis.trust_badges import calculate_all_badges as _calc_badges
        _BADGES_AVAILABLE = True
    except ImportError:
        _BADGES_AVAILABLE = False


def normalize(text: str) -> str:
    """Lowercase + basic cleanup."""
    return text.lower().strip()


# ======================================================================
# Tool scoring
# ======================================================================

# Words too generic to be useful scoring signals — they match nearly
# every tool in the catalog and add noise instead of relevance.
_SCORING_STOP_WORDS = {"ai", "tool", "tools", "app", "apps", "software", "platform", "best", "good", "e"}


def score_tool(tool, keywords):
    """
    Score a tool against a list of search keywords.

    Scoring is split into two buckets:
        RELEVANCE (keyword, category, tag, TF-IDF) — primary signal
        QUALITY   (trust, sovereignty, popularity)  — tiebreaker only

    Quality signals are capped so they never overpower a relevance match.
    A tool that matches the query on keywords/categories will always rank
    above a tool that merely has high trust or popularity.
    """
    relevance = 0
    quality = 0

    desc_blob = (tool.description or "").lower()
    name_blob = (tool.name or "").lower()
    cat_set = {c.lower() for c in getattr(tool, "categories", [])}
    tag_set = {t.lower() for t in getattr(tool, "tags", [])}
    kw_set = {k.lower() for k in getattr(tool, "keywords", [])}
    uc_blob = " ".join(getattr(tool, "use_cases", [])).lower()

    w_cat = _w("weight_category_match", 4)
    w_tag = _w("weight_tag_match", 3)
    w_kw  = _w("weight_keyword_match", 2)
    w_nd  = _w("weight_name_desc_match", 1)
    w_uc  = _w("weight_usecase_bonus", 1)

    for word in keywords:
        w = str(word).lower()
        if w in _SCORING_STOP_WORDS:
            continue
        if w in cat_set:
            relevance += w_cat
        elif w in tag_set:
            relevance += w_tag
        elif w in kw_set:
            relevance += w_kw
        elif w in desc_blob or w in name_blob:
            relevance += w_nd
        # Use-case bonus
        if w in uc_blob:
            relevance += w_uc

    # ── TF-IDF semantic scoring ──
    if _INTEL_AVAILABLE:
        try:
            tfidf = get_tfidf_index()
            tfidf_score = tfidf.score(keywords, tool.name)
            scale = _w("weight_tfidf_scale", 8)
            relevance += int(tfidf_score * scale)
        except Exception as exc:
            log.debug("TF-IDF scoring failed for %s: %s", tool.name, exc)

    # ── Quality signals (capped tiebreakers) ──

    # Popularity — cap at 2 so seeded data can't dominate
    pop = int(getattr(tool, "popularity", 0) or 0)
    quality += min(pop, 2)

    # Learned feedback boost — cap at 2
    if _INTEL_AVAILABLE and _w("enable_learned_boosts", True):
        try:
            quality += min(get_learned_boost(tool.name), 2)
        except Exception as exc:
            log.debug("Learned boost failed for %s: %s", tool.name, exc)

    # Sovereignty — cap at 1
    if _SOVEREIGNTY_AVAILABLE and _w("enable_sovereignty_scoring", True):
        try:
            quality += min(_sov_mod(tool), 1)
        except Exception as exc:
            log.debug("Sovereignty scoring failed for %s: %s", tool.name, exc)

    # Trust badges — cap at 2 (down from +5/+3)
    if _BADGES_AVAILABLE and _w("enable_badge_scoring", True):
        try:
            badges = _calc_badges(tool)
            trust_score = badges.get("trust_score", 50)
            if trust_score >= 80:
                quality += 2
            elif trust_score >= 65:
                quality += 1
            elif trust_score < 35:
                quality -= 1
        except Exception as exc:
            log.debug("Badge scoring failed for %s: %s", tool.name, exc)

    # Quality signals can add at most a few points — never enough to
    # push a zero-relevance tool above a tool with even one keyword match.
    return relevance + quality


# Budget-related keywords that signal the user cares about pricing
_BUDGET_SIGNALS = {"budget", "price", "pricing", "cost", "cheap", "free",
                   "affordable", "expensive", "money", "subscription", "pay",
                   "tier", "plan", "enterprise", "premium", "$"}


def score_profile_fit(tool, profile, intent=None) -> int:
    """Extra score adjustments based on the user profile.

    Returns a positive or negative integer modifier.
    """
    if profile is None:
        return 0

    mod = 0

    # Budget fit — only factor in when the query mentions pricing
    raw = ((intent or {}).get("raw") or "").lower()
    budget_mentioned = any(w in raw for w in _BUDGET_SIGNALS)
    if budget_mentioned:
        if hasattr(tool, "fits_budget") and tool.fits_budget(getattr(profile, "budget", "medium")):
            mod += _w("weight_profile_budget_fit", 3)
        else:
            mod += _w("weight_profile_budget_miss", -3)

    # Skill fit
    if hasattr(tool, "fits_skill") and tool.fits_skill(getattr(profile, "skill_level", "beginner")):
        mod += _w("weight_profile_skill_fit", 2)
    else:
        mod += _w("weight_profile_skill_miss", -4)

    # Integration with existing tools
    existing = getattr(profile, "existing_tools", [])
    for et in existing:
        if hasattr(tool, "integrates_with") and tool.integrates_with(et):
            mod += _w("weight_profile_integration", 3)
            break

    # Compliance
    constraints = getattr(profile, "constraints", [])
    for c in constraints:
        tool_compliance = [x.upper() for x in getattr(tool, "compliance", [])]
        if c.upper() in tool_compliance:
            mod += _w("weight_profile_compliance_hit", 2)
        else:
            mod += _w("weight_profile_compliance_miss", -2)

    # Already-used penalty (user probably wants new suggestions)
    if hasattr(profile, "already_uses") and profile.already_uses(tool.name):
        mod += _w("weight_profile_already_used", -2)

    return mod


# ======================================================================
# Search
# ======================================================================

def find_tools(user_input, top_n: int = 5, categories_filter: list = None, profile=None, context=None):
    """Main search function.

    Args:
        user_input:        raw string OR structured interpreter output (dict)
        top_n:             max results to return
        categories_filter: optional category whitelist
        profile:           optional UserProfile for profile-aware scoring
        context:           optional ContextVector for context-aware ranking

    Returns:
        list of Tool objects, highest score first.
    """
    # Build keyword list
    if isinstance(user_input, dict):
        keywords = []
        for k in (user_input.get("intent"), user_input.get("industry"), user_input.get("goal")):
            if k:
                keywords.append(str(k))
        keywords.extend(user_input.get("keywords", []))
        if not keywords and user_input.get("raw"):
            keywords = normalize(user_input.get("raw")).split()
        negatives = user_input.get("negatives", [])
        industry = user_input.get("industry")
    else:
        keywords = normalize(str(user_input)).split()
        negatives = []
        industry = None

    # ── Context enrichment: inject T1/T2 fields into keyword/filter pipeline ──
    context_compliance = []
    context_budget = None
    context_skill = None
    if context is not None:
        # T1 industry overrides
        if hasattr(context, "industry") and hasattr(context.industry, "tier"):
            if context.industry.tier == 1 and context.industry.value:
                industry = context.industry.value
            elif context.industry.tier == 2 and context.industry.value and not industry:
                industry = context.industry.value

        # T1/T2 compliance → hard pruning list
        if hasattr(context, "compliance") and hasattr(context.compliance, "value"):
            if context.compliance.value:
                context_compliance = context.compliance.value

        # Budget and skill for scoring modifiers
        if hasattr(context, "budget") and hasattr(context.budget, "value"):
            context_budget = context.budget.value
        if hasattr(context, "skill_level") and hasattr(context.skill_level, "value"):
            context_skill = context.skill_level.value

    # Normalize filters
    if categories_filter:
        categories_filter = [c.lower().strip() for c in categories_filter if c.strip()]
    else:
        categories_filter = None

    # Get industry from profile if not in query
    if not industry and profile:
        industry = getattr(profile, "industry", None)

    scored = []

    for tool in TOOLS:
        # ── Negative filter: exclude tools whose NAME matches a negative term ──
        # Only match on tool names, not descriptions. "without coding" means
        # the user wants no-code tools, not "exclude every tool that mentions code".
        if negatives:
            tool_name_lower = tool.name.lower()
            if any(neg == tool_name_lower or neg in tool_name_lower.split() for neg in negatives):
                continue

        # Category filter gate
        if categories_filter:
            tool_cats = [c.lower() for c in tool.categories]
            if not any(fc in tool_cats for fc in categories_filter):
                continue

        base = score_tool(tool, keywords)
        profile_mod = score_profile_fit(tool, profile, intent=user_input if isinstance(user_input, dict) else None)

        # ── Industry context boost ──
        industry_mod = 0
        if _INTEL_AVAILABLE and industry:
            try:
                industry_mod = get_industry_boost(industry, tool)
            except Exception:
                pass

        total = base + profile_mod + industry_mod

        # ── Context-aware scoring ──
        if context is not None:
            # Boost tools that appear in graph neighbors
            if hasattr(context, "graph_neighbors") and context.graph_neighbors:
                if tool.name.lower() in {n.lower() for n in context.graph_neighbors}:
                    total += 3

            # Penalise tools pruned by compliance
            if hasattr(context, "pruned_tools") and context.pruned_tools:
                if tool.name.lower() in {t.lower() for t in context.pruned_tools}:
                    continue  # hard prune — compliance violation

            # Budget alignment boost from context
            if context_budget and hasattr(tool, "pricing"):
                pricing = (getattr(tool, "pricing", "") or "").lower()
                if context_budget == "free" and "free" in pricing:
                    total += 2
                elif context_budget == "high" and "enterprise" in pricing:
                    total += 1

        if total > 0:
            scored.append((total, tool))

    scored.sort(key=lambda x: x[0], reverse=True)

    top_score = scored[0][0] if scored else 0
    raw_query = user_input if isinstance(user_input, str) else user_input.get("raw", "")

    log.info("find_tools: query=%r → %d candidates scored, top=%s",
             raw_query, len(scored),
             scored[0][1].name if scored else "none")

    # ── Track query failures / low-confidence results ──
    if _DIAG_AVAILABLE:
        if len(scored) < MIN_RESULTS_THRESHOLD or top_score < LOW_SCORE_THRESHOLD:
            try:
                _record_failure(
                    raw_query,
                    results_count=len(scored),
                    top_score=top_score,
                    interpreted=user_input if isinstance(user_input, dict) else None,
                )
            except Exception:
                pass

    # ── Diversity re-ranking ──
    if _INTEL_AVAILABLE and len(scored) > top_n:
        try:
            scored = diversity_rerank(scored, top_n=top_n)
        except Exception as exc:
            log.warning("Diversity reranking failed: %s", exc)

    results = [tool for _, tool in scored[:top_n]]

    # ── 2026 Security Blueprint: Sovereignty filtering ──
    if _SOVEREIGNTY_AVAILABLE and profile:
        require_us = getattr(profile, "requires_us_sovereignty", False)
        require_zdr = getattr(profile, "strict_privacy_mode", False)
        tier_pref = getattr(profile, "sovereignty_tier_preference", None)

        if require_us or require_zdr or tier_pref:
            try:
                tier_whitelist = None
                if tier_pref == "us_controlled":
                    tier_whitelist = {"us_controlled"}
                elif tier_pref == "allied":
                    tier_whitelist = {"us_controlled", "allied"}

                filtered = _sov_filter(
                    results,
                    tier_whitelist=tier_whitelist,
                    exclude_high_risk=True,
                    require_zdr=require_zdr,
                    require_us=require_us,
                )
                if filtered:
                    results = filtered
                    log.info("Sovereignty filter: %d → %d tools after tier/ZDR constraints",
                             len(scored), len(results))
            except Exception as exc:
                log.warning("Sovereignty filtering failed: %s", exc)

    return results


# =====================================================================
# Safeguard 1 — Architectural Boundary Enforcement
# =====================================================================
# Enforces Hexagonal Architecture constraints on LLM-generated code.
# Domain and use-case layers are forbidden from importing infrastructure
# modules (ORMs, HTTP clients, cloud SDKs, web frameworks).
# =====================================================================

import ast
from dataclasses import dataclass as _dc, field as _fld
from typing import Dict, List, Optional

@_dc
class PortContract:
    """Describes a hexagonal port that LLM-generated code must respect."""
    port_name: str
    input_types: Dict[str, str]   # e.g. {"user_id": "str", "query": "str"}
    return_type: str              # e.g. "List[ToolResult]"
    domain_rules: List[str]       # e.g. ["must validate user_id", "max 50 results"]


class ArchitecturalBoundaryEnforcer:
    """
    Validates that LLM-generated code respects Hexagonal Architecture
    boundaries by checking imports against a forbidden-list per layer.

    Layers:
        domain     — pure business logic, zero infrastructure imports
        use_cases  — orchestration, no direct infra except ports
        adapters   — free to import anything (infrastructure boundary)
    """

    FORBIDDEN_IMPORTS: Dict[str, List[str]] = {
        "domain": [
            "sqlalchemy", "requests", "fastapi", "boto3", "flask",
            "django", "httpx", "aiohttp", "psycopg2", "pymongo",
            "redis", "celery", "pika", "grpc",
        ],
        "use_cases": [
            "sqlalchemy", "requests", "flask", "django",
            "psycopg2", "pymongo",
        ],
        "adapters": [],   # adapters may import anything
    }

    def __init__(self, target_module_path: Optional[str] = None):
        self.target_module_path = target_module_path
        self.violations: List[Dict[str, str]] = []

    # ── Core validation ──────────────────────────────────────────

    def validate_llm_output(
        self, generated_code: str, layer: str = "domain"
    ) -> Dict:
        """
        Parse *generated_code* and reject any forbidden imports for *layer*.

        Returns:
            {
                "valid": bool,
                "layer": str,
                "violations": [{"module": str, "line": int, "statement": str}],
                "imports_found": [str],
            }
        """
        self.violations = []
        forbidden = self.FORBIDDEN_IMPORTS.get(layer, [])
        imports_found: List[str] = []

        try:
            tree = ast.parse(generated_code)
        except SyntaxError as exc:
            return {
                "valid": False,
                "layer": layer,
                "violations": [{"module": "SYNTAX_ERROR", "line": exc.lineno or 0,
                                 "statement": str(exc)}],
                "imports_found": [],
            }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    imports_found.append(alias.name)
                    if self._is_forbidden(root, forbidden):
                        self.violations.append({
                            "module": alias.name,
                            "line": node.lineno,
                            "statement": f"import {alias.name}",
                        })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    imports_found.append(node.module)
                    if self._is_forbidden(root, forbidden):
                        self.violations.append({
                            "module": node.module,
                            "line": node.lineno,
                            "statement": f"from {node.module} import ...",
                        })

        return {
            "valid": len(self.violations) == 0,
            "layer": layer,
            "violations": self.violations,
            "imports_found": imports_found,
        }

    # ── Prompt generation ────────────────────────────────────────

    def generate_constrained_prompt(self, contract: PortContract) -> str:
        """
        Generate a Hexagonal-Architecture-scoped prompt that instructs
        the LLM to produce code honouring *contract* boundaries.
        """
        input_sig = ", ".join(f"{k}: {v}" for k, v in contract.input_types.items())
        rules = "\n".join(f"  - {r}" for r in contract.domain_rules)
        forbidden = ", ".join(self.FORBIDDEN_IMPORTS.get("domain", []))

        return (
            f"## Hexagonal Architecture Port: {contract.port_name}\n\n"
            f"Generate a Python function implementing this port contract.\n\n"
            f"### Signature\n"
            f"```python\n"
            f"def {contract.port_name}({input_sig}) -> {contract.return_type}:\n"
            f"```\n\n"
            f"### Domain Rules\n{rules}\n\n"
            f"### FORBIDDEN Imports (domain layer)\n"
            f"Do NOT import any of: {forbidden}\n\n"
            f"The function must be a pure domain operation with no side effects.\n"
            f"All I/O must go through injected port interfaces, never direct imports.\n"
        )

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _is_forbidden(module_root: str, forbidden: List[str]) -> bool:
        return module_root.lower() in [f.lower() for f in forbidden]
