# --------------- Explanation Generator ---------------
"""
Generates human-readable explanations for *why* a tool or stack was
recommended.  This is what differentiates a decision engine from a search
engine — users see the reasoning, not just the results.

Two explanation levels:
    1. Per-tool  — "Why this tool fits your situation"
    2. Per-stack — "Why these tools work together"
"""

from typing import List, Optional

try:
    from .tools import Tool
    from .profile import UserProfile
except Exception:
    from tools import Tool
    from profile import UserProfile

# The vendor intelligence layer — optional but deeply integrated when present
try:
    from .philosophy import assess_transparency, assess_freedom, detect_masks
    _PHILOSOPHY_AVAILABLE = True
except Exception:
    try:
        from philosophy import assess_transparency, assess_freedom, detect_masks
        _PHILOSOPHY_AVAILABLE = True
    except Exception:
        _PHILOSOPHY_AVAILABLE = False

# ── 2026 Security Blueprint: Sovereignty & Nutrition Label integration ──
try:
    from .sovereignty import assess_sovereignty, get_trust_badge
    _SOVEREIGNTY_AVAILABLE = True
except Exception:
    try:
        from sovereignty import assess_sovereignty, get_trust_badge
        _SOVEREIGNTY_AVAILABLE = True
    except Exception:
        _SOVEREIGNTY_AVAILABLE = False

try:
    from .nutrition import generate_nutrition_label
    _NUTRITION_AVAILABLE = True
except Exception:
    try:
        from nutrition import generate_nutrition_label
        _NUTRITION_AVAILABLE = True
    except Exception:
        _NUTRITION_AVAILABLE = False

# ── 2026 Trust Badge Architecture ──
try:
    from .trust_badges import calculate_all_badges as _calc_all_badges
    _TRUST_BADGES_AVAILABLE = True
except Exception:
    try:
        from trust_badges import calculate_all_badges as _calc_all_badges
        _TRUST_BADGES_AVAILABLE = True
    except Exception:
        _TRUST_BADGES_AVAILABLE = False


# Budget-related keywords that signal the user cares about pricing
_BUDGET_SIGNALS = {"budget", "price", "pricing", "cost", "cheap", "free",
                   "affordable", "expensive", "money", "subscription", "pay",
                   "tier", "plan", "enterprise", "premium", "$"}


def _query_mentions_budget(intent: dict) -> bool:
    """Return True if the user's query explicitly references budget/pricing."""
    raw = (intent.get("raw") or "").lower()
    return any(w in raw for w in _BUDGET_SIGNALS)


# ── Deep-reasoning helpers ──────────────────────────────────────────

_TRIVIAL = {"a", "an", "the", "and", "or", "for", "with", "to", "in",
            "is", "it", "of", "on", "i", "my", "your", "that", "this",
            "be", "can", "do", "need", "help", "want", "some", "use",
            "me", "best", "tool", "tools", "looking", "like", "good"}

# Lightweight suffix stripping for stem-like matching
_SUFFIX_ORDER = ("ting", "ning", "bing", "ding", "ing", "tion", "ment",
                 "ness", "ous", "ive", "ful", "less", "able", "ible",
                 "ize", "ise", "ify", "ical", "ical", "ity", "ist",
                 "ence", "ance", "ated", "ized", "ised",
                 "ed", "er", "es", "ly", "al", "s")


def _stem(word: str) -> str:
    """Very light suffix stripping — NOT a proper stemmer, but good enough
    for matching 'transcribing'→'transcrib', 'chatbot'→'chatbot', etc."""
    w = word.lower().strip()
    if len(w) <= 4:
        return w
    for sfx in _SUFFIX_ORDER:
        if w.endswith(sfx) and len(w) - len(sfx) >= 3:
            return w[:-len(sfx)]
    return w


def _stems_match(word_a: str, word_b: str) -> bool:
    """Check if two words share a common stem OR one contains the other."""
    a, b = word_a.lower(), word_b.lower()
    if a == b:
        return True
    if len(a) > 3 and len(b) > 3:
        if a in b or b in a:
            return True
    sa, sb = _stem(a), _stem(b)
    if len(sa) >= 3 and len(sb) >= 3 and (sa == sb or sa.startswith(sb) or sb.startswith(sa)):
        return True
    return False


def _phrase_overlap(text_a: str, text_b: str, min_word: int = 2) -> List[str]:
    """Find meaningful word overlaps between two strings, including stem matches."""
    a_words = [w for w in text_a.lower().split() if w not in _TRIVIAL and len(w) > 2]
    b_words = [w for w in text_b.lower().split() if len(w) > 2]
    hits = []
    for aw in a_words:
        for bw in b_words:
            if _stems_match(aw, bw):
                hits.append(aw)
                break
    return hits


def _use_case_match(query_lower: str, use_cases: List[str]) -> Optional[str]:
    """Find the best-matching use case. Returns the most specific match."""
    best = None
    best_score = 0
    q_words = [w for w in query_lower.split() if w not in _TRIVIAL and len(w) > 2]
    for uc in use_cases:
        uc_lower = uc.lower()
        uc_words = uc_lower.split()
        # Check stem-level overlap
        score = 0
        for qw in q_words:
            for uw in uc_words:
                if _stems_match(qw, uw):
                    score += 1
                    break
        if score > best_score:
            best = uc
            best_score = score
        # Substring containment fallback
        if not best:
            for qw in q_words:
                if len(qw) > 4 and qw in uc_lower:
                    best = uc
                    best_score = max(best_score, 1)
                    break
    return best if best_score > 0 else None


def _desc_relevance(query_lower: str, description: str) -> Optional[str]:
    """Extract a relevant phrase from the tool description that matches the query."""
    desc_lower = description.lower()
    overlap = _phrase_overlap(query_lower, desc_lower)
    if len(overlap) >= 2:
        # Find the section of the description that contains the overlap
        for part in description.split(","):
            part_lower = part.lower().strip()
            if any(w in part_lower for w in overlap):
                return part.strip()
    # Single strong overlap — still useful for specific queries
    if len(overlap) == 1 and len(overlap[0]) >= 5:
        for part in description.split(","):
            part_lower = part.lower().strip()
            if overlap[0] in part_lower:
                return part.strip()
    return None


# Action-verb vocabulary for richer explanations
_CAPABILITY_VERBS = {
    "writing": "generate, draft, and refine",
    "research": "research, synthesize, and summarize",
    "brainstorming": "brainstorm, ideate, and explore",
    "coding": "write, debug, and review code",
    "automation": "automate workflows and reduce manual tasks",
    "design": "design, create, and iterate on visuals",
    "marketing": "plan, execute, and measure marketing",
    "analytics": "analyze data and surface insights",
    "sales": "manage pipelines and accelerate outreach",
    "email": "craft, send, and track email campaigns",
    "video": "produce, edit, and publish video content",
    "audio": "record, edit, and transcribe audio",
    "support": "handle support tickets and customer queries",
    "communication": "streamline team communication",
    "planning": "plan projects and manage timelines",
    "organization": "organize information and streamline workflows",
    "devops": "deploy, monitor, and manage infrastructure",
    "data": "collect, transform, and manage data",
    "ml": "train, fine-tune, and deploy ML models",
    "seo": "optimize search rankings and track organic traffic",
    "no-code": "build without code using visual tools",
    "security": "secure systems and manage compliance",
    "productivity": "boost output and streamline daily workflows",
    "images": "generate, edit, and transform images",
    "forms": "build forms and collect structured input",
    "payments": "process payments and manage billing",
    "recruiting": "source, evaluate, and hire talent",
    "legal": "draft contracts and manage legal workflows",
    "accounting": "manage books, invoicing, and financial reporting",
    "presentations": "create compelling slide decks and presentations",
    "crm": "manage customer relationships and track deals",
    "database": "store, query, and organize structured data",
    "integration": "connect tools and sync data across systems",
    "graphics": "create graphics and visual assets",
}

# Map raw query verbs/phrases to deeper "why" explanations
_QUERY_CONTEXT_PHRASES = {
    "create": "Built for creation workflows",
    "build": "Designed to help you build from scratch",
    "improve": "Helps iterate and improve existing work",
    "replace": "Can serve as a replacement in your workflow",
    "scale": "Scales with your team as you grow",
    "learn": "Good learning curve — ramp up quickly",
    "collaborate": "Built for team collaboration",
    "prototype": "Fast prototyping capabilities",
    "launch": "Helps get from idea to launch faster",
    "grow": "Supports growth-stage workflows",
    "save time": "Designed to save significant manual effort",
    "simplify": "Simplifies complex processes into manageable steps",
    "migrate": "Supports data import and migration from other tools",
    "integrate": "Strong integration ecosystem",
    "secure": "Security-first architecture",
    "analyze": "Deep analytical capabilities",
    "track": "Built-in tracking and measurement",
    "manage": "End-to-end management capabilities",
    "generate": "AI-powered generation capabilities",
    "edit": "Professional editing tools included",
    "optimize": "Optimization and improvement features built in",
    "automate": "Automation-first — reduce repetitive manual work",
    "schedule": "Scheduling and calendar management built in",
    "monitor": "Real-time monitoring and alerting",
    "personalize": "Personalization engine for targeted output",
    "translate": "Multi-language and translation support",
    "visualize": "Data visualization and visual output",
    "summarize": "Summarization and distillation capabilities",
    "transcribe": "Audio-to-text transcription",
    "record": "Recording and capture tools",
}


# ======================================================================
# Per-tool explanations
# ======================================================================

def explain_tool(tool: Tool, intent: dict, profile: Optional[UserProfile] = None) -> dict:
    """Return a structured explanation for a single tool recommendation.

    Generates deep, query-specific reasoning that connects the user's exact
    words to the tool's capabilities — not generic category labels.

    Returns:
        {
            "summary":  str,          # one-liner reason
            "reasons":  list[str],    # bullet-point reasons
            "caveats":  list[str],    # potential downsides / watch-outs
            "fit_score": int,         # 0-100 subjective fit percentage
        }
    """
    reasons = []
    caveats = []
    fit = 50  # baseline

    keywords = intent.get("keywords", [])
    raw_lower = (intent.get("raw") or "").lower()
    intent_val = (intent.get("intent") or "").lower()
    goal_val = (intent.get("goal") or "").lower()

    cat_set = {c.lower() for c in tool.categories}
    tag_set = {t.lower() for t in tool.tags}
    kw_set = {k.lower() for k in tool.keywords}
    desc_lower = (tool.description or "").lower()

    # ────────────────────────────────────────────────
    # 1. DEEP QUERY ↔ DESCRIPTION MATCH
    #    Connect the user's actual words to what the tool does.
    # ────────────────────────────────────────────────
    desc_match = _desc_relevance(raw_lower, tool.description or "")
    if desc_match:
        # Trim long description fragments for cleaner display
        dm_clean = desc_match.lower().strip()
        if len(dm_clean) > 60:
            dm_clean = dm_clean[:60].rsplit(" ", 1)[0] + "…"
        reasons.append(f"Directly relevant — {tool.name} is built for {dm_clean}")
        fit += 12
    elif intent_val and any(_stems_match(intent_val, dw) for dw in desc_lower.split() if len(dw) > 3):
        # Description mentions the user's intent
        cap_intent = intent_val[0].upper() + intent_val[1:]
        verbs = _CAPABILITY_VERBS.get(intent_val, f"handle {intent_val} tasks")
        reasons.append(f"{cap_intent}-focused — {tool.name} can {verbs}")
        fit += 10

    # ────────────────────────────────────────────────
    # 2. USE CASE ↔ QUERY MATCH
    #    The most specific signal: the tool lists a use case
    #    that directly maps to what the user asked for.
    # ────────────────────────────────────────────────
    uc_match = _use_case_match(raw_lower, tool.use_cases)
    if uc_match:
        reasons.append(f"Supports exactly this: {uc_match}")
        fit += 8
    elif goal_val:
        # Check if any use case connects to the extracted goal
        for uc in tool.use_cases:
            if goal_val in uc.lower() or any(w in uc.lower() for w in goal_val.split() if len(w) > 3):
                reasons.append(f"Aligns with your goal — proven for {uc}")
                fit += 6
                break

    # ────────────────────────────────────────────────
    # 3. CATEGORY & CAPABILITY REASONING
    #    Instead of "Categorized under X", explain *why* that category matters.
    # ────────────────────────────────────────────────
    matched_cats = []
    for w in keywords:
        wl = w.lower()
        if wl in cat_set and wl not in matched_cats:
            matched_cats.append(wl)
        else:
            # Stem match against categories
            for cat in tool.categories:
                if _stems_match(wl, cat.lower()) and cat.lower() not in matched_cats:
                    matched_cats.append(cat.lower())
                    break
    # Also check if intent is a category match
    if intent_val and intent_val in cat_set and intent_val not in matched_cats:
        matched_cats.insert(0, intent_val)
    # Stem match intent against categories
    if intent_val and intent_val not in matched_cats:
        for cat in tool.categories:
            if _stems_match(intent_val, cat.lower()) and cat.lower() not in matched_cats:
                matched_cats.insert(0, cat.lower())
                break

    if matched_cats:
        # Generate one rich sentence instead of N "Categorized under X" lines
        if len(matched_cats) == 1:
            cat = matched_cats[0]
            verbs = _CAPABILITY_VERBS.get(cat, f"support {cat} workflows")
            # Don't duplicate if we already have a desc-based reason for this
            if not any(cat in r.lower() for r in reasons):
                reasons.append(f"Core capability in {cat} — can {verbs}")
                fit += 8
        else:
            cat_labels = " and ".join(matched_cats[:3])
            reasons.append(f"Spans multiple areas you need: {cat_labels}")
            fit += 5 + (3 * min(len(matched_cats), 3))

    # ────────────────────────────────────────────────
    # 4. KEYWORD DEPTH (with stem matching)
    #    Match the user's specific terms to the tool's domain
    #    knowledge (keywords, tags) with contextual phrasing.
    # ────────────────────────────────────────────────
    deep_kw_hits = []
    for w in keywords:
        wl = w.lower()
        # Exact match first
        if wl in kw_set:
            deep_kw_hits.append(w)
        elif wl in tag_set and wl not in matched_cats:
            deep_kw_hits.append(w)
        else:
            # Stem-level match against keywords and tags
            for tk in tool.keywords:
                if _stems_match(wl, tk.lower()):
                    deep_kw_hits.append(w)
                    break
            else:
                for tg in tool.tags:
                    if _stems_match(wl, tg.lower()) and wl not in matched_cats:
                        deep_kw_hits.append(w)
                        break
    # Remove duplicates of what we already covered
    already_mentioned = " ".join(reasons).lower()
    deep_kw_hits = [k for k in deep_kw_hits if k.lower() not in already_mentioned]
    if deep_kw_hits:
        if len(deep_kw_hits) == 1:
            reasons.append(f"Known for {deep_kw_hits[0]} — a documented strength")
            fit += 3
        else:
            reasons.append(f"Domain expertise in: {', '.join(deep_kw_hits[:4])}")
            fit += 2 * min(len(deep_kw_hits), 3)

    # ────────────────────────────────────────────────
    # 5. QUERY VERB / ACTION REASONING
    #    Pick up on verbs in the raw query and explain how
    #    the tool addresses that specific action.
    # ────────────────────────────────────────────────
    already_mentioned = " ".join(reasons).lower()  # refresh
    for verb, phrase in _QUERY_CONTEXT_PHRASES.items():
        if verb in raw_lower:
            # Check if the tool can plausibly do this action (via desc, use_cases, or categories)
            tool_text = desc_lower + " " + " ".join(uc.lower() for uc in tool.use_cases) + " " + " ".join(c.lower() for c in tool.categories)
            if (verb in tool_text or
                any(_stems_match(verb, tw) for tw in tool_text.split() if len(tw) > 3)):
                if phrase.lower() not in already_mentioned:
                    reasons.append(phrase)
                    fit += 3
                    break  # One verb match is enough

    # ────────────────────────────────────────────────
    # 6. PROFILE-AWARE REASONING
    # ────────────────────────────────────────────────
    if profile:
        # Budget — only surface when the query mentions pricing
        budget_mentioned = _query_mentions_budget(intent)
        if budget_mentioned:
            if tool.fits_budget(profile.budget):
                budget_labels = {"free": "free", "low": "affordable", "medium": "mid-range", "high": "premium"}
                label = budget_labels.get(profile.budget, "")
                pricing = tool.pricing or {}
                if pricing.get("free_tier"):
                    reasons.append(f"Has a free tier — you can start without commitment")
                else:
                    starter = pricing.get("starter") or pricing.get("pro")
                    if starter:
                        reasons.append(f"Fits your {label} budget — starts at ${starter}/mo")
                    else:
                        reasons.append(f"Accessible at your {label} budget level")
                fit += 5
            else:
                pricing = tool.pricing or {}
                starter = pricing.get("starter") or pricing.get("pro")
                if starter:
                    caveats.append(f"Starts at ${starter}/mo — may stretch your '{profile.budget}' budget")
                else:
                    caveats.append(f"May exceed your '{profile.budget}' budget tier")
                fit -= 10

        # Skill — contextual phrasing
        if tool.fits_skill(profile.skill_level):
            if tool.skill_level == "beginner":
                reasons.append("No technical background needed — guided, intuitive interface")
            elif tool.skill_level == profile.skill_level:
                reasons.append(f"Designed for {profile.skill_level}-level users like you")
            fit += 5
        else:
            if tool.skill_level == "advanced" and profile.skill_level == "beginner":
                caveats.append(f"Steep learning curve — {tool.name} needs {tool.skill_level} skills (you selected {profile.skill_level})")
            else:
                caveats.append(f"Requires {tool.skill_level}-level skills (you selected {profile.skill_level})")
            fit -= 10

        # Industry — contextual
        industry = (profile.industry or "").lower()
        if industry:
            for uc in tool.use_cases + tool.keywords:
                if industry in uc.lower():
                    reasons.append(f"Used by teams in {profile.industry} for {uc}")
                    fit += 5
                    break

        # Compliance
        for constraint in profile.constraints:
            if constraint.upper() in [c.upper() for c in tool.compliance]:
                reasons.append(f"Meets your {constraint.upper()} compliance requirement")
                fit += 5
            else:
                caveats.append(f"Does not list {constraint.upper()} compliance — verify with vendor")
                fit -= 5

        # Already used
        if profile.already_uses(tool.name):
            reasons.append("Already in your stack — build on what you know")
            fit += 5

        # Integrations with existing tools — specific
        integrated_with = []
        for et in profile.existing_tools:
            if tool.integrates_with(et):
                integrated_with.append(et)
        if integrated_with:
            if len(integrated_with) == 1:
                reasons.append(f"Connects directly with {integrated_with[0]} (already in your stack)")
            else:
                reasons.append(f"Plugs into your existing tools: {', '.join(integrated_with[:3])}")
            fit += 5

    # ────────────────────────────────────────────────
    # 7. POPULARITY CONTEXT
    # ────────────────────────────────────────────────
    if tool.popularity >= 7:
        reasons.append(f"Widely adopted — one of the most-used tools in this space")
        fit += 3
    elif tool.popularity >= 5:
        reasons.append(f"Proven track record with a strong user base")
        fit += 2

    # ────────────────────────────────────────────────
    # 8. INTEGRATION ECOSYSTEM
    #    If the tool has a rich integration list, that's a signal.
    # ────────────────────────────────────────────────
    integ_count = len(tool.integrations or [])
    if integ_count >= 8 and "integrat" not in " ".join(reasons).lower():
        reasons.append(f"Rich integration ecosystem ({integ_count}+ connections) — easy to fit into your workflow")
        fit += 2

    # ────────────────────────────────────────────────
    # 9. DESCRIPTION FALLBACK
    #    When the query is very broad or niche and we didn't find
    #    strong category/keyword matches, use the tool's own
    #    description to explain what it does and why it showed up.
    # ────────────────────────────────────────────────
    substantive_reasons = [r for r in reasons if "widely adopted" not in r.lower()
                          and "proven track" not in r.lower()
                          and "integration ecosystem" not in r.lower()]
    if not substantive_reasons and tool.description:
        desc_short = tool.description
        if len(desc_short) > 100:
            desc_short = desc_short[:100].rsplit(" ", 1)[0] + "…"
        reasons.insert(0, f"{tool.name}: {desc_short}")

    # Clamp
    fit = max(10, min(100, fit))

    # Deduplicate reasons
    seen = set()
    unique_reasons = []
    for r in reasons:
        key = r.lower().strip()
        if key not in seen:
            seen.add(key)
            unique_reasons.append(r)

    # ── Vendor Intelligence ──
    transparency = {}
    freedom = {}
    risk_indicators = []
    if _PHILOSOPHY_AVAILABLE:
        try:
            transparency = assess_transparency(tool)
            freedom = assess_freedom(tool)
            risk_indicators = detect_masks(tool)

            if transparency.get("grade") in ("D", "F"):
                caveats.append(f"Transparency rating: {transparency['grade']} — review vendor data practices before procurement")
            if freedom.get("grade") in ("D", "F"):
                caveats.append(f"Flexibility rating: {freedom['grade']} — elevated vendor lock-in risk")
            for indicator in risk_indicators[:1]:
                caveats.append(indicator)

            if transparency.get("grade") in ("A", "B"):
                fit += 3
            if freedom.get("grade") in ("A", "B"):
                fit += 3
            if freedom.get("grade") in ("D", "F"):
                fit -= 3

            fit = max(10, min(100, fit))
        except Exception:
            pass

    # Build summary — a natural one-liner that references the user's query
    if unique_reasons:
        summary = unique_reasons[0]
    elif intent_val:
        summary = f"{tool.name} is a strong match for {intent_val} tasks"
    else:
        summary = f"{tool.name} can help with what you're looking for"

    return {
        "summary": summary,
        "reasons": unique_reasons[:6],
        "caveats": caveats[:4],
        "fit_score": fit,
        "transparency_score": transparency.get("score"),
        "transparency_grade": transparency.get("grade"),
        "freedom_score": freedom.get("score"),
        "freedom_grade": freedom.get("grade"),
        # ── 2026 Security Blueprint: Sovereignty & Nutrition ──
        "sovereignty": _get_sovereignty_data(tool),
        "nutrition_label": _get_nutrition_data(tool),
        # ── 2026 Trust Badge Architecture ──
        "trust_badges": _get_trust_badge_data(tool),
    }


# ── 2026 Security Blueprint: Sovereignty & Nutrition helpers ──

def _get_sovereignty_data(tool) -> dict:
    """Generate sovereignty assessment for a tool explanation."""
    if not _SOVEREIGNTY_AVAILABLE:
        return {}
    try:
        assessment = assess_sovereignty(tool)
        badge = get_trust_badge(tool)
        return {
            "trust_tier": assessment.get("trust_tier", "unknown"),
            "badge": badge,
            "risk_score": assessment.get("risk_score", 0.0),
            "warnings": assessment.get("warnings", []),
            "recommendation": assessment.get("recommendation", ""),
        }
    except Exception:
        return {}


def _get_nutrition_data(tool) -> dict:
    """Generate nutrition label for a tool explanation."""
    if not _NUTRITION_AVAILABLE:
        return {}
    try:
        sov_data = None
        if _SOVEREIGNTY_AVAILABLE:
            sov_data = assess_sovereignty(tool)
        return generate_nutrition_label(tool, sov_data)
    except Exception:
        return {}


def _get_trust_badge_data(tool) -> dict:
    """Generate trust badge profile for a tool explanation."""
    if not _TRUST_BADGES_AVAILABLE:
        return {}
    try:
        return _calc_all_badges(tool)
    except Exception:
        return {}


# ======================================================================
# Per-stack explanations
# ======================================================================

def explain_stack(
    stack: list,  # list of dicts: {"tool": Tool, "role": str}
    intent: dict,
    profile: Optional[UserProfile] = None,
) -> dict:
    """Return a high-level explanation of why a stack of tools was composed.

    Returns:
        {
            "narrative":       str,
            "tool_explanations": list[dict],  # per-tool explain_tool output + role
            "integration_notes": list[str],
            "total_monthly_cost": str,
            "stack_fit_score":  int,
        }
    """
    tool_explanations = []
    integration_notes = []
    monthly_costs = []
    fit_scores = []

    tool_names = [entry["tool"].name for entry in stack]

    for entry in stack:
        tool = entry["tool"]
        role = entry["role"]
        expl = explain_tool(tool, intent, profile)
        expl["role"] = role
        expl["tool_name"] = tool.name
        tool_explanations.append(expl)
        fit_scores.append(expl["fit_score"])

        # Estimate cost
        pricing = tool.pricing or {}
        if profile and profile.budget == "free":
            cost = 0 if pricing.get("free_tier") else None
        elif profile and profile.budget == "low":
            cost = pricing.get("starter", pricing.get("pro"))
        else:
            cost = pricing.get("pro", pricing.get("starter"))
        if isinstance(cost, (int, float)):
            monthly_costs.append(cost)

    # Integration notes
    for i, entry_a in enumerate(stack):
        for entry_b in stack[i + 1:]:
            a, b = entry_a["tool"], entry_b["tool"]
            if a.integrates_with(b.name):
                integration_notes.append(f"{a.name} ↔ {b.name} — native integration available")
            elif b.integrates_with(a.name):
                integration_notes.append(f"{b.name} ↔ {a.name} — native integration available")

    # Cost summary
    if monthly_costs:
        total = sum(monthly_costs)
        cost_str = f"~${total:.0f}/month (estimated for selected tiers)"
    else:
        cost_str = "Varies — check individual tool pricing"

    # Narrative
    roles_summary = ", ".join(
        f"{e['tool'].name} ({e['role']})" for e in stack
    )
    intent_str = intent.get("intent") or intent.get("raw", "your task")
    narrative = (
        f"For {intent_str}, we recommend a {len(stack)}-tool stack: {roles_summary}. "
    )
    if integration_notes:
        narrative += f"These tools integrate natively, reducing setup friction. "
    if profile:
        parts = [f"{profile.skill_level}-level", profile.industry or 'general', 'user']
        if _query_mentions_budget(intent):
            parts.append(f"on a {profile.budget} budget")
        narrative += f"This stack is tailored for a {' '.join(parts)}."

    avg_fit = int(sum(fit_scores) / len(fit_scores)) if fit_scores else 50

    return {
        "narrative": narrative,
        "tool_explanations": tool_explanations,
        "integration_notes": integration_notes,
        "total_monthly_cost": cost_str,
        "stack_fit_score": avg_fit,
    }


# ======================================================================
# Differential Diagnosis — Counterfactual "Why Not" Explanations
# ======================================================================

# Stage labels for human-readable output
_STAGE_LABELS = {
    2: "Deterministic Pruning (Hard Constraint)",
    3: "Probabilistic Penalisation (Soft Penalty)",
}

# Templates for generating natural-language elimination explanations
_ELIMINATION_TEMPLATES = {
    "BUDGET_EXCEEDED": (
        "🚨 {name} was considered but eliminated.\n"
        "Primary Reason: {explanation}\n"
        "This is a hard budget constraint — no configuration of {name} "
        "can deliver the required capabilities within your stated budget ceiling."
    ),
    "COMPLIANCE_FAILURE": (
        "🚨 {name} was considered but eliminated.\n"
        "Primary Reason: {explanation}\n"
        "This is a non-negotiable compliance requirement. Deploying {name} "
        "without {mandate} certification would expose your organisation to "
        "significant legal and financial risk."
    ),
    "NEGATIVE_INTENT_MATCH": (
        "🚫 {name} was excluded by your explicit request.\n"
        "Reason: {explanation}\n"
        "Praxis respects your direct exclusions as absolute filters."
    ),
    "STACK_CONFLICT": (
        "♻️ {name} is already in your stack.\n"
        "Reason: {explanation}\n"
        "We focus on discovering tools you haven't yet adopted."
    ),
    "DEPLOYMENT_CONFLICT": (
        "🏢 {name} was eliminated due to deployment incompatibility.\n"
        "Reason: {explanation}\n"
        "Your infrastructure requirements mandate deployment options "
        "this tool does not support."
    ),
    "ARCHITECTURAL_REDUNDANCY": (
        "📋 {name} was eliminated to prevent shadow IT.\n"
        "Reason: {explanation}\n"
        "Adding redundant tools increases operational complexity and cost "
        "without proportional benefit."
    ),
    "CUMULATIVE_PENALTY": (
        "⚠️ {name} survived hard constraints but failed probabilistic review.\n"
        "Reason: {explanation}\n"
        "While technically eligible, cumulative risk factors made this tool "
        "a suboptimal choice for your specific organisational profile."
    ),
}


def explain_elimination(eliminated_entry: dict) -> dict:
    """
    Generate a rich, human-readable counterfactual explanation for
    why a specific tool was eliminated from the recommendation set.

    Args:
        eliminated_entry: dict from DifferentialResult.eliminated
            {name, reason_type, code, explanation, stage, stage_label}

    Returns:
        {
            "tool_name": str,
            "headline": str,          # One-line summary
            "full_explanation": str,   # Multi-line natural-language explanation
            "stage": str,              # "Hard Constraint" or "Soft Penalty"
            "severity": str,           # "critical" | "warning" | "info"
            "code": str,
            "can_challenge": bool,     # Whether user can flag this as incorrect
        }
    """
    name = eliminated_entry.get("name", "Unknown Tool")
    code = eliminated_entry.get("code", "UNKNOWN")
    explanation = eliminated_entry.get("explanation", "No details available.")
    stage = eliminated_entry.get("stage", 2)
    stage_label = eliminated_entry.get("stage_label", _STAGE_LABELS.get(stage, "Unknown"))

    # Generate headline
    reason_type = eliminated_entry.get("reason_type", "HARD_CONSTRAINT")
    if reason_type == "HARD_CONSTRAINT":
        headline = f"{name} eliminated — fails mandatory requirement"
        severity = "critical"
    else:
        headline = f"{name} deprioritised — cumulative risk factors"
        severity = "warning"

    # Use template if available
    template = _ELIMINATION_TEMPLATES.get(code, "{name} was eliminated. Reason: {explanation}")
    full_text = template.format(
        name=name,
        explanation=explanation,
        mandate=explanation.split("mandated ")[-1].split(" ")[0] if "mandated" in explanation else "required",
    )

    return {
        "tool_name": name,
        "headline": headline,
        "full_explanation": full_text,
        "stage": stage_label,
        "severity": severity,
        "code": code,
        "can_challenge": True,  # All eliminations can be challenged
    }


def explain_survival(survivor_entry: dict) -> dict:
    """
    Generate a plain-language summary of why a tool survived the
    differential diagnosis pipeline.

    Args:
        survivor_entry: dict from DifferentialResult.survivors

    Returns:
        {
            "tool_name": str,
            "headline": str,
            "survival_narrative": str,
            "resilience_badge": str | None,
            "confidence": str,
        }
    """
    name = survivor_entry.get("name", "Unknown Tool")
    reasons = survivor_entry.get("survival_reasons", [])
    penalties = survivor_entry.get("penalties_applied", [])
    resilience = survivor_entry.get("resilience") or {}
    score = survivor_entry.get("final_score", 0)

    tier = resilience.get("tier", "unknown")
    grade = resilience.get("grade", "?")

    # Headline
    if tier in ("sovereign", "durable"):
        badge = f"🛡️ {tier.title()} Architecture (Grade {grade})"
        headline = f"{name} — Resilient, verified fit"
    elif tier == "moderate":
        badge = f"✅ Moderate Architecture (Grade {grade})"
        headline = f"{name} — Solid functional match"
    else:
        badge = f"⚡ {tier.title()} (Grade {grade})" if tier != "unknown" else None
        headline = f"{name} — Functional match with caveats"

    # Narrative
    parts = []
    if reasons:
        parts.append("Survives your constraints: " + "; ".join(reasons[:4]))
    if penalties:
        parts.append("Risk factors noted: " + "; ".join(penalties[:2]))
    if not parts:
        parts.append(f"Matched your query with a viability score of {score:.0%}.")

    narrative = " ".join(parts)

    # Confidence level
    if score >= 0.7:
        confidence = "high"
    elif score >= 0.4:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "tool_name": name,
        "headline": headline,
        "survival_narrative": narrative,
        "resilience_badge": badge,
        "confidence": confidence,
    }


def assemble_presentation(survivors: list, eliminated: list) -> dict:
    """
    Master assembly function for the differential diagnosis UI.
    Produces a complete presentation payload with explained survivors,
    explained eliminations, and a summary narrative.

    Args:
        survivors:  list of survivor dicts from DifferentialResult
        eliminated: list of eliminated dicts from DifferentialResult

    Returns:
        {
            "survivor_cards": [explained survivor dicts],
            "elimination_cards": [explained elimination dicts],
            "summary": str,
            "total_survivors": int,
            "total_eliminated": int,
            "notable_eliminations": [dicts for well-known tools only],
        }
    """
    survivor_cards = [explain_survival(s) for s in survivors]
    elimination_cards = [explain_elimination(e) for e in eliminated]

    # Identify "notable" eliminations — well-known tools users might expect
    _NOTABLE_TOOLS = {
        "chatgpt", "salesforce", "hubspot", "slack", "jira", "asana",
        "notion ai", "zapier", "monday", "trello", "figma ai", "canva ai",
        "copilot", "gemini", "claude", "stripe", "shopify", "mailchimp",
        "zendesk", "intercom", "amplitude", "mixpanel", "datadog",
    }

    notable = [
        c for c in elimination_cards
        if c["tool_name"].lower() in _NOTABLE_TOOLS
    ]

    # Summary
    s_count = len(survivors)
    e_count = len(eliminated)
    hard_count = sum(1 for e in eliminated if e.get("reason_type") == "HARD_CONSTRAINT")
    soft_count = e_count - hard_count

    summary = (
        f"Differential diagnosis complete: {s_count} optimal survivors "
        f"from {s_count + e_count} candidates evaluated. "
    )
    if hard_count:
        summary += f"{hard_count} tools eliminated by hard constraints. "
    if soft_count:
        summary += f"{soft_count} tools deprioritised by risk penalties. "
    if notable:
        notable_names = ", ".join(c["tool_name"] for c in notable[:3])
        summary += f"Notable exclusions: {notable_names}."

    return {
        "survivor_cards": survivor_cards,
        "elimination_cards": elimination_cards,
        "summary": summary,
        "total_survivors": s_count,
        "total_eliminated": e_count,
        "notable_eliminations": notable,
    }

# =====================================================================
# Safeguard 3a — AST Mutation Engine for LLM-to-LLM Verification
# =====================================================================
# Generates semantically-mutated variants of source code so a second
# LLM agent can verify the first agent's comprehension.  If the second
# agent cannot detect the mutation, the original output is flagged as
# potentially hallucinated.
# =====================================================================

import ast as _ast
import copy as _copy
import random as _random
from typing import Tuple


class ASTMutator(_ast.NodeTransformer):
    """
    Flips comparison and boolean operators in an AST to produce a
    semantically-different but syntactically-valid mutation.

    Mutation types:
        • Eq ↔ NotEq
        • Lt ↔ Gt
        • LtE ↔ GtE
        • And ↔ Or
        • Is ↔ IsNot
    """

    # Operator flip table
    _COMPARE_FLIPS = {
        _ast.Eq:    _ast.NotEq,
        _ast.NotEq: _ast.Eq,
        _ast.Lt:    _ast.Gt,
        _ast.Gt:    _ast.Lt,
        _ast.LtE:   _ast.GtE,
        _ast.GtE:   _ast.LtE,
        _ast.Is:    _ast.IsNot,
        _ast.IsNot: _ast.Is,
    }

    _BOOL_FLIPS = {
        _ast.And: _ast.Or,
        _ast.Or:  _ast.And,
    }

    def __init__(self, *, max_mutations: int = 3, seed: int | None = None):
        super().__init__()
        self.mutations_applied: list[str] = []
        self._max_mutations = max_mutations
        self._rng = _random.Random(seed)

    def visit_Compare(self, node):
        self.generic_visit(node)
        if len(self.mutations_applied) >= self._max_mutations:
            return node

        new_ops = []
        mutated = False
        for op in node.ops:
            flipped = self._COMPARE_FLIPS.get(type(op))
            if flipped and not mutated and self._rng.random() < 0.6:
                new_ops.append(flipped())
                self.mutations_applied.append(
                    f"Line {node.lineno}: {type(op).__name__} → {flipped.__name__}"
                )
                mutated = True
            else:
                new_ops.append(op)
        node.ops = new_ops
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if len(self.mutations_applied) >= self._max_mutations:
            return node

        flipped = self._BOOL_FLIPS.get(type(node.op))
        if flipped and self._rng.random() < 0.5:
            self.mutations_applied.append(
                f"Line {node.lineno}: {type(node.op).__name__} → {flipped.__name__}"
            )
            node.op = flipped()
        return node


def generate_mutation(
    source_code: str,
    *,
    max_mutations: int = 3,
    seed: int | None = None,
) -> Tuple[str, list[str]]:
    """
    Generate a semantically-mutated variant of *source_code*.

    Returns:
        (mutated_source, list_of_mutations_applied)

    If no mutations are possible (e.g. no comparisons), returns the
    original code unchanged with an empty list.
    """
    try:
        tree = _ast.parse(source_code)
    except SyntaxError:
        return source_code, []

    mutator = ASTMutator(max_mutations=max_mutations, seed=seed)
    mutated_tree = mutator.visit(tree)
    _ast.fix_missing_locations(mutated_tree)

    try:
        mutated_code = _ast.unparse(mutated_tree)
    except Exception:
        return source_code, []

    return mutated_code, mutator.mutations_applied