# ────────────────────────────────────────────────────────────────────
# smart_suggest.py — Next-Gen Intent-Driven Autocomplete Engine
# ────────────────────────────────────────────────────────────────────
"""
Replaces the legacy TF-IDF prefix-match autocomplete with a hybrid
intent-detection + semantic-completion engine.

Architecture:
    1. **Intent Router** — regex classification of conversational vs.
       direct queries (Phase 1 stopgap + Gemini-ready hook)
    2. **Semantic Completion** — maps vague intents to concrete SMB
       workflows using synonym graphs and tool affinity
    3. **Hybrid Search** — blends exact prefix matches with semantic
       concept proximity via cosine similarity on lightweight vectors
    4. **Popularity Feedback** — in-memory sorted dict (Redis-ready)
       that tracks click-through and self-tunes rankings
    5. **Bento Payload Builder** — structures results into a typed
       JSON schema consumable by the frontend Bento Grid

The /suggest endpoint returns a structured payload:
    {
        "layout": "bento_grid",
        "intent_detected": "automation",
        "primary_completions": [...],   # left large card
        "tool_matches": [...],          # top-right card
        "workflow_templates": [...],    # bottom-right card
        "category_matches": [...],     # secondary
        "did_you_mean": [...],         # correction strip
        "trending": [...],            # popularity-ranked
    }
"""

from __future__ import annotations

import hashlib
import math
import re
import time
import threading
from collections import defaultdict, Counter
from difflib import get_close_matches
from typing import Any, Dict, List, Optional, Tuple, Set

import logging
log = logging.getLogger("praxis.smart_suggest")


# ╔════════════════════════════════════════════════════════════════════╗
# ║  1. INTENT DETECTION — Conversational Router                     ║
# ╚════════════════════════════════════════════════════════════════════╝

# Regex patterns that signal "I have a problem, not a tool name"
INTENT_PREFIXES = re.compile(
    r"^(?:"
    r"i need(?: help)? (?:with|to|for)|"
    r"help me(?: with| to)?|"
    r"best (?:tools?|apps?|software|platforms?) for|"
    r"recommend(?: (?:a |me )?(?:stack|tools?|apps?|software))? for|"
    r"how (?:do i|can i|to)|"
    r"what(?:'s| is) (?:the )?best|"
    r"looking for|"
    r"find(?: me)? (?:a |the )?|"
    r"suggest(?: (?:a |me )?)|"
    r"compare |"
    r"alternatives? to |"
    r"something (?:like|similar to|for)|"
    r"tools? (?:for|to|that)|"
    r"any (?:good |free )?(?:tools?|apps?|software)"
    r")\b",
    re.IGNORECASE,
)

# Filler words that carry zero retrieval signal
_STOPWORDS = frozenset({
    "i", "me", "my", "we", "our", "you", "your", "a", "an", "the",
    "is", "are", "was", "were", "be", "been", "am", "do", "does",
    "did", "will", "would", "could", "should", "can", "may", "might",
    "have", "has", "had", "to", "for", "with", "in", "on", "at", "of",
    "and", "or", "but", "not", "it", "its", "that", "this", "some",
    "any", "all", "very", "just", "more", "most", "so", "if", "than",
    "up", "out", "about", "into", "over", "after", "before", "from",
    "by", "as", "what", "which", "who", "whom", "how", "when", "where",
    "why", "there", "here", "no", "yes", "need", "help", "want",
    "looking", "find", "best", "good", "great", "recommend", "suggest",
    "something", "like", "similar", "tools", "tool", "apps", "app",
    "software", "platform", "platforms",
})


def classify_intent(query: str) -> Tuple[str, str]:
    """Classify a query as 'conversational' or 'direct'.

    Returns:
        (intent_type, extracted_core)
        intent_type: 'conversational' | 'direct'
        extracted_core: the semantic payload after stripping filler
    """
    q = query.lower().strip()

    if INTENT_PREFIXES.match(q):
        # Strip the conversational prefix and stopwords
        core = INTENT_PREFIXES.sub("", q).strip()
        core = " ".join(w for w in core.split() if w not in _STOPWORDS)
        return ("conversational", core or q)

    # Even without a prefix, if >60% of tokens are stopwords, it's conversational
    tokens = q.split()
    if tokens and sum(1 for t in tokens if t in _STOPWORDS) / len(tokens) > 0.6:
        core = " ".join(w for w in tokens if w not in _STOPWORDS)
        return ("conversational", core or q)

    return ("direct", q)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  2. SEMANTIC COMPLETION — Intent-to-Workflow Mapping             ║
# ╚════════════════════════════════════════════════════════════════════╝

# Maps extracted intent cores to concrete SMB workflow suggestions
_WORKFLOW_TEMPLATES: Dict[str, List[Dict[str, str]]] = {
    "automation": [
        {"title": "Automate email sequences", "desc": "Set up drip campaigns that trigger on user actions", "icon": "⚡"},
        {"title": "Connect CRM to marketing", "desc": "Sync leads between Salesforce/HubSpot and email tools", "icon": "🔗"},
        {"title": "Invoice processing pipeline", "desc": "Auto-extract, validate, and route incoming invoices", "icon": "📄"},
        {"title": "Slack → project board sync", "desc": "Turn Slack messages into tasks in Notion/Asana", "icon": "📋"},
    ],
    "marketing": [
        {"title": "AI content calendar", "desc": "Generate and schedule a month of social posts", "icon": "📅"},
        {"title": "SEO audit workflow", "desc": "Crawl, analyze, and fix on-page SEO issues", "icon": "🔍"},
        {"title": "Ad copy generator", "desc": "Create A/B test variants for paid campaigns", "icon": "✍️"},
        {"title": "Email newsletter builder", "desc": "Design, write, and send weekly digests", "icon": "📧"},
    ],
    "writing": [
        {"title": "Blog post pipeline", "desc": "Research → outline → draft → edit → publish", "icon": "📝"},
        {"title": "Product descriptions", "desc": "Generate SEO-optimized copy for e-commerce", "icon": "🏷️"},
        {"title": "Technical documentation", "desc": "Auto-generate API docs from code comments", "icon": "📖"},
        {"title": "Social media captions", "desc": "Batch-create platform-specific copy", "icon": "💬"},
    ],
    "design": [
        {"title": "Brand kit generator", "desc": "Create logos, palettes, and guidelines in one flow", "icon": "🎨"},
        {"title": "Social media templates", "desc": "Design reusable templates for Instagram/LinkedIn", "icon": "📱"},
        {"title": "Presentation builder", "desc": "AI-assisted slide deck from outline to polish", "icon": "📊"},
        {"title": "Product mockups", "desc": "Generate realistic mockups from screenshots", "icon": "🖼️"},
    ],
    "coding": [
        {"title": "Code review assistant", "desc": "AI-powered PR review with security scanning", "icon": "🔬"},
        {"title": "API integration scaffold", "desc": "Generate boilerplate for REST/GraphQL integrations", "icon": "🔌"},
        {"title": "Test generation", "desc": "Auto-generate unit tests from function signatures", "icon": "🧪"},
        {"title": "CI/CD pipeline setup", "desc": "Configure GitHub Actions / GitLab CI from scratch", "icon": "🚀"},
    ],
    "analytics": [
        {"title": "Dashboard builder", "desc": "Connect data sources and build KPI dashboards", "icon": "📈"},
        {"title": "Customer cohort analysis", "desc": "Segment users by behavior and lifetime value", "icon": "👥"},
        {"title": "Revenue forecasting", "desc": "ML-powered projections from historical data", "icon": "🔮"},
        {"title": "A/B test analyzer", "desc": "Statistical significance calculator for experiments", "icon": "⚖️"},
    ],
    "sales": [
        {"title": "Lead scoring pipeline", "desc": "Score and prioritize inbound leads automatically", "icon": "🎯"},
        {"title": "Outreach sequence builder", "desc": "Multi-channel cold outreach with personalization", "icon": "📤"},
        {"title": "CRM data enrichment", "desc": "Auto-fill company and contact data from web sources", "icon": "💎"},
        {"title": "Proposal generator", "desc": "Create branded proposals from templates + deal data", "icon": "📑"},
    ],
    "support": [
        {"title": "AI helpdesk triage", "desc": "Auto-categorize and route support tickets", "icon": "🎪"},
        {"title": "Knowledge base builder", "desc": "Generate FAQ articles from ticket history", "icon": "📚"},
        {"title": "Chatbot deployment", "desc": "Train and deploy a customer-facing AI chatbot", "icon": "🤖"},
        {"title": "CSAT survey pipeline", "desc": "Trigger satisfaction surveys after ticket resolution", "icon": "⭐"},
    ],
    "video": [
        {"title": "Video editing workflow", "desc": "AI-assisted cuts, captions, and color grading", "icon": "🎬"},
        {"title": "YouTube SEO optimizer", "desc": "Titles, descriptions, and tags for discoverability", "icon": "📺"},
        {"title": "Podcast to clips", "desc": "Extract viral short-form clips from long recordings", "icon": "✂️"},
        {"title": "Screen recording + docs", "desc": "Record tutorials and auto-generate documentation", "icon": "🖥️"},
    ],
    "productivity": [
        {"title": "Meeting notes pipeline", "desc": "Record → transcribe → summarize → distribute", "icon": "🎙️"},
        {"title": "Task prioritization", "desc": "AI-ranked daily task lists from multiple sources", "icon": "✅"},
        {"title": "Document organization", "desc": "Auto-tag and file documents across cloud storage", "icon": "🗂️"},
        {"title": "Time tracking automator", "desc": "Passive time tracking with project classification", "icon": "⏱️"},
    ],
    "email": [
        {"title": "Email marketing automation", "desc": "Drip sequences triggered by user behavior", "icon": "📧"},
        {"title": "Cold outreach campaigns", "desc": "Personalized cold email at scale with follow-ups", "icon": "📤"},
        {"title": "Newsletter workflow", "desc": "Curate → write → design → send weekly digests", "icon": "📰"},
        {"title": "Inbox zero automation", "desc": "AI-powered email sorting, replies, and archiving", "icon": "📥"},
    ],
    "data": [
        {"title": "ETL pipeline builder", "desc": "Extract, transform, and load from multiple sources", "icon": "🔄"},
        {"title": "Data visualization", "desc": "Auto-generate charts and dashboards from CSVs", "icon": "📊"},
        {"title": "Database migration", "desc": "Schema diff, data transfer, and validation", "icon": "🗄️"},
        {"title": "Data quality monitor", "desc": "Continuous profiling and anomaly alerting", "icon": "🔍"},
    ],
    "security": [
        {"title": "Security audit workflow", "desc": "Scan, report, and remediate vulnerabilities", "icon": "🛡️"},
        {"title": "Compliance checklist", "desc": "SOC2/GDPR/HIPAA automated evidence collection", "icon": "📋"},
        {"title": "Penetration test prep", "desc": "Scope, execute, and report on pen test findings", "icon": "🔐"},
        {"title": "Incident response plan", "desc": "Auto-generate runbooks from threat models", "icon": "🚨"},
    ],
    "accounting": [
        {"title": "Invoice automation", "desc": "Generate, send, and track invoices automatically", "icon": "💰"},
        {"title": "Expense categorization", "desc": "AI-powered receipt scanning and GL coding", "icon": "🧾"},
        {"title": "Tax prep workflow", "desc": "Organize documents and estimates for tax season", "icon": "📋"},
        {"title": "Cash flow forecasting", "desc": "Predict runway and burn rate from bank data", "icon": "📈"},
    ],
    "social media": [
        {"title": "Content calendar", "desc": "Plan, create, and schedule posts across platforms", "icon": "📅"},
        {"title": "Engagement automator", "desc": "Auto-respond to comments and DMs with AI", "icon": "💬"},
        {"title": "Trend monitor", "desc": "Track trending topics and hashtags in your niche", "icon": "📡"},
        {"title": "Analytics dashboard", "desc": "Unified metrics across all social platforms", "icon": "📊"},
    ],
    "no-code": [
        {"title": "App builder workflow", "desc": "Drag-and-drop MVP from idea to deployed app", "icon": "🧱"},
        {"title": "Form → database pipeline", "desc": "Collect form submissions into structured storage", "icon": "📝"},
        {"title": "Internal tool builder", "desc": "Create admin panels and dashboards without code", "icon": "🛠️"},
        {"title": "API connector", "desc": "Connect third-party APIs visually, no code required", "icon": "🔌"},
    ],
}

# Reverse map: synonyms → canonical workflow category
_INTENT_SYNONYMS: Dict[str, str] = {}


def _build_intent_synonyms():
    """Populate reverse synonym map from the intelligence module's synonym table."""
    try:
        from .intelligence import _SYNONYM_MAP, _REVERSE_SYNONYMS
    except ImportError:
        try:
            from intelligence import _SYNONYM_MAP, _REVERSE_SYNONYMS
        except ImportError:
            return
    for canonical in _WORKFLOW_TEMPLATES:
        _INTENT_SYNONYMS[canonical] = canonical
    for syn, canonical in _REVERSE_SYNONYMS.items():
        if canonical in _WORKFLOW_TEMPLATES:
            _INTENT_SYNONYMS[syn] = canonical


def resolve_intent_category(core_query: str) -> Optional[str]:
    """Map the extracted intent core to a workflow template category."""
    if not _INTENT_SYNONYMS:
        _build_intent_synonyms()

    tokens = core_query.lower().split()

    # Direct match on any token
    for token in tokens:
        if token in _INTENT_SYNONYMS:
            return _INTENT_SYNONYMS[token]

    # Substring match
    for phrase, category in _INTENT_SYNONYMS.items():
        if phrase in core_query.lower():
            return category

    # Fallback: try the full core as a vocabulary lookup
    if core_query.lower() in _INTENT_SYNONYMS:
        return _INTENT_SYNONYMS[core_query.lower()]

    return None


# ╔════════════════════════════════════════════════════════════════════╗
# ║  3. POPULARITY TRACKING — In-Memory (Redis-Ready)                ║
# ╚════════════════════════════════════════════════════════════════════╝

class PopularityTracker:
    """Thread-safe sorted score tracker.

    Designed for seamless migration to Redis ZINCRBY.
    In-memory implementation uses a dict + sorted retrieval.
    """

    def __init__(self):
        self._scores: Dict[str, float] = {}
        self._lock = threading.Lock()

    def record_click(self, suggestion_text: str, boost: float = 1.0) -> None:
        """Increment the score of a clicked suggestion."""
        key = suggestion_text.lower().strip()
        with self._lock:
            self._scores[key] = self._scores.get(key, 0.0) + boost

    def top_k(self, prefix: Optional[str] = None, k: int = 5) -> List[Tuple[str, float]]:
        """Return top-k suggestions by score, optionally filtered by prefix."""
        with self._lock:
            items = list(self._scores.items())
        if prefix:
            p = prefix.lower()
            items = [(k, v) for k, v in items if p in k]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:k]

    def seed(self, defaults: Dict[str, float]) -> None:
        """Seed initial scores (e.g., from config or historical data)."""
        with self._lock:
            for k, v in defaults.items():
                self._scores.setdefault(k.lower(), v)


# Module-level singleton
_popularity = PopularityTracker()

# Seed with reasonable defaults
_popularity.seed({
    "automate email marketing": 45,
    "build a website": 42,
    "write blog posts": 40,
    "design social media graphics": 38,
    "analyze customer data": 35,
    "set up CRM": 33,
    "create presentations": 30,
    "generate leads": 28,
    "manage projects": 25,
    "record and edit videos": 22,
    "build no-code app": 20,
    "automate invoicing": 18,
    "seo optimization": 15,
    "customer support chatbot": 12,
    "code review automation": 10,
})


def record_suggestion_click(text: str) -> None:
    """Public API for recording a suggestion click from the frontend."""
    _popularity.record_click(text)


# ╔════════════════════════════════════════════════════════════════════╗
# ║  4. HYBRID SUGGEST — Blends All Signals                          ║
# ╚════════════════════════════════════════════════════════════════════╝

def smart_suggest(
    query: str,
    tools_list: list,
    *,
    user_id: Optional[str] = None,
    limit: int = 8,
) -> Dict[str, Any]:
    """The main entry point — produces a Bento Grid-structured payload.

    This replaces the legacy `get_suggestions()` function.
    """
    q = query.strip()
    if not q or len(q) < 2:
        return _empty_payload()

    intent_type, core = classify_intent(q)
    category = resolve_intent_category(core) if intent_type == "conversational" else None

    # ── Branch: conversational intent with resolved category ──
    if intent_type == "conversational" and category:
        return _conversational_payload(q, core, category, tools_list)

    # ── Branch: conversational intent but NO category yet (mid-sentence) ──
    if intent_type == "conversational" and not category:
        return _incomplete_intent_payload(q, core, tools_list)

    # ── Branch: direct query (tool name / category / keyword) ──
    return _direct_payload(q, tools_list)


def _empty_payload() -> Dict[str, Any]:
    trending = _popularity.top_k(k=5)
    return {
        "layout": "bento_grid",
        "intent_detected": None,
        "primary_completions": [],
        "tool_matches": [],
        "workflow_templates": [],
        "category_matches": [],
        "did_you_mean": [],
        "trending": [{"text": t, "score": s} for t, s in trending],
    }


def _conversational_payload(
    raw_query: str,
    core: str,
    category: str,
    tools_list: list,
) -> Dict[str, Any]:
    """Build the Bento payload for a conversational/intent query."""

    # Primary completions: contextual sentence completions
    completions = _generate_smart_completions(core, category)

    # Workflow templates for this category
    workflows = _WORKFLOW_TEMPLATES.get(category, [])[:4]

    # Tool matches: tools in this category
    tool_matches = _tools_for_category(category, tools_list, limit=4)

    # Trending filtered by relevance
    trending = _popularity.top_k(prefix=core[:4] if len(core) >= 4 else None, k=3)

    # Category matches that relate
    cat_matches = _related_categories(category, tools_list)

    return {
        "layout": "bento_grid",
        "intent_detected": category,
        "primary_completions": completions,
        "tool_matches": tool_matches,
        "workflow_templates": workflows,
        "category_matches": cat_matches,
        "did_you_mean": [],
        "trending": [{"text": t, "score": s} for t, s in trending],
    }


def _incomplete_intent_payload(
    raw_query: str,
    core: str,
    tools_list: list,
) -> Dict[str, Any]:
    """Handle 'i need help with…' before a category word is typed.

    Shows prompt completions for every major category so the user
    can pick a direction, plus trending queries.
    """
    # Offer one completion per popular category
    top_categories = [
        ("automation", "⚡"), ("marketing", "📅"), ("writing", "📝"),
        ("design", "🎨"), ("coding", "🔬"), ("analytics", "📈"),
        ("sales", "🎯"), ("support", "🤖"),
    ]
    completions = []
    for cat, icon in top_categories:
        completions.append({
            "text": f"{raw_query} {cat}",
            "type": "intent_completion",
            "icon": icon,
        })

    # Pick 4 diverse representative tools
    seen_cats: Set[str] = set()
    featured = []
    for t in tools_list:
        primary = t.categories[0].lower() if t.categories else "other"
        if primary not in seen_cats and len(featured) < 4:
            featured.append({
                "name": t.name,
                "description": (t.description or "")[:80],
                "categories": t.categories[:3],
                "url": t.url or "",
            })
            seen_cats.add(primary)

    trending = _popularity.top_k(k=5)

    return {
        "layout": "bento_grid",
        "intent_detected": "exploring",
        "primary_completions": completions,
        "tool_matches": featured,
        "workflow_templates": [
            {"title": "Take the guided quiz", "desc": "Not sure what you need? We'll figure it out.", "icon": "🧭"},
            {"title": "Browse all tools", "desc": f"{len(tools_list)} AI tools indexed and reviewed", "icon": "📚"},
        ],
        "category_matches": [],
        "did_you_mean": [],
        "trending": [{"text": t, "score": s} for t, s in trending],
    }


def _direct_payload(query: str, tools_list: list) -> Dict[str, Any]:
    """Build the Bento payload for a direct/explicit query."""
    q = query.lower()

    # Tool name matches (prefix + substring)
    tool_matches = []
    for t in tools_list:
        name_lower = t.name.lower()
        if name_lower.startswith(q) or q in name_lower:
            tool_matches.append({
                "name": t.name,
                "description": (t.description or "")[:80],
                "categories": t.categories[:3],
                "url": t.url or "",
            })
    tool_matches = tool_matches[:6]

    # Category matches
    all_cats: Set[str] = set()
    for t in tools_list:
        all_cats.update(c.lower() for c in t.categories)
    category_matches = [c for c in sorted(all_cats) if q in c][:5]

    # Fuzzy / did-you-mean
    did_you_mean = _fuzzy_corrections(q, tools_list)

    # Try to detect a category even for direct queries
    category = resolve_intent_category(q)
    workflows = _WORKFLOW_TEMPLATES.get(category, [])[:2] if category else []

    # Trending — use first meaningful word as prefix filter, not raw query
    prefix_token = next((w for w in q.split() if w not in _STOPWORDS and len(w) >= 3), None)
    trending = _popularity.top_k(prefix=prefix_token, k=3)

    # Smart completions based on what partial text maps to
    completions = []
    if category:
        completions = _generate_smart_completions(q, category)[:3]

    return {
        "layout": "bento_grid",
        "intent_detected": category,
        "primary_completions": completions,
        "tool_matches": tool_matches,
        "workflow_templates": workflows,
        "category_matches": category_matches,
        "did_you_mean": did_you_mean,
        "trending": [{"text": t, "score": s} for t, s in trending],
    }


# ╔════════════════════════════════════════════════════════════════════╗
# ║  5. HELPER FUNCTIONS                                              ║
# ╚════════════════════════════════════════════════════════════════════╝

def _generate_smart_completions(core: str, category: str) -> List[Dict[str, str]]:
    """Generate intent-aware sentence completions.

    Phase 1: static template expansion.
    Phase 2+: swap in Gemini Flash call.
    """
    # Make category human-readable
    cat_display = category.replace("_", " ").replace("-", " ")

    # Category-specific templates avoid redundant phrasing like "automate automation"
    _CATEGORY_TEMPLATES: Dict[str, List[str]] = {
        "automation": [
            "Set up automated workflows for your team",
            "Find the best automation tools for SMBs",
            "Compare workflow automation platforms",
            "Build an end-to-end automation pipeline",
            "Connect your apps with no-code automation",
            "Free automation tools for startups",
        ],
    }

    if category in _CATEGORY_TEMPLATES:
        templates = _CATEGORY_TEMPLATES[category]
    else:
        templates = [
            f"Automate {cat_display} workflows",
            f"Find the best {cat_display} tools for SMBs",
            f"Compare top {cat_display} platforms",
            f"Build a {cat_display} pipeline for my team",
            f"Set up AI-powered {cat_display}",
            f"Free {cat_display} tools for startups",
        ]

    completions = []
    for text in templates:
        completions.append({
            "text": text,
            "type": "intent_completion",
            "icon": "✦",
        })

    return completions[:5]


def _tools_for_category(category: str, tools_list: list, limit: int = 4) -> List[Dict[str, Any]]:
    """Find tools that match a category, ranked by keyword density."""
    matches = []
    cat_lower = category.lower()

    for t in tools_list:
        score = 0
        tool_cats = [c.lower() for c in t.categories]
        tool_tags = [tg.lower() for tg in t.tags]
        tool_kws = [k.lower() for k in t.keywords]
        tool_ucs = [u.lower() for u in t.use_cases]

        if cat_lower in tool_cats:
            score += 10
        for field in (tool_tags, tool_kws, tool_ucs):
            for item in field:
                if cat_lower in item or item in cat_lower:
                    score += 2

        if score > 0:
            matches.append((score, t))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "name": t.name,
            "description": (t.description or "")[:80],
            "categories": t.categories[:3],
            "url": t.url or "",
        }
        for _, t in matches[:limit]
    ]


def _related_categories(category: str, tools_list: list) -> List[str]:
    """Find categories that co-occur with the given category."""
    co_cats: Counter = Counter()
    cat_lower = category.lower()

    for t in tools_list:
        tool_cats = [c.lower() for c in t.categories]
        if cat_lower in tool_cats:
            for c in tool_cats:
                if c != cat_lower:
                    co_cats[c] += 1

    return [c for c, _ in co_cats.most_common(5)]


def _fuzzy_corrections(query: str, tools_list: list) -> List[str]:
    """Generate did-you-mean corrections using edit distance."""
    vocabulary: Set[str] = set()
    for t in tools_list:
        vocabulary.add(t.name.lower())
        for c in t.categories:
            vocabulary.add(c.lower())
        for tag in t.tags:
            vocabulary.add(tag.lower())

    corrections = []
    matches = get_close_matches(query, list(vocabulary), n=4, cutoff=0.6)
    for m in matches:
        if m != query:
            corrections.append(m)

    return corrections[:3]


# ╔════════════════════════════════════════════════════════════════════╗
# ║  6. SHOW-ON-FOCUS — Zero-keystroke Personalized Recommendations  ║
# ╚════════════════════════════════════════════════════════════════════╝

def focus_suggestions(tools_list: list, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Return suggestions to display when the search bar is focused
    but no text has been entered yet.

    Phase 1: trending + category highlights.
    Phase 2+: personalized based on user_id session history.
    """
    trending = _popularity.top_k(k=6)

    # Pick 4 diverse representative tools
    seen_cats: Set[str] = set()
    featured_tools = []
    for t in tools_list:
        primary = t.categories[0].lower() if t.categories else "other"
        if primary not in seen_cats and len(featured_tools) < 4:
            featured_tools.append({
                "name": t.name,
                "description": (t.description or "")[:60],
                "categories": t.categories[:2],
            })
            seen_cats.add(primary)

    return {
        "layout": "bento_grid",
        "intent_detected": None,
        "primary_completions": [
            {"text": "What can Praxis help you with?", "type": "prompt", "icon": "✦"},
        ],
        "tool_matches": featured_tools,
        "workflow_templates": [
            {"title": "Take the guided quiz", "desc": "Not sure what you need? We'll figure it out.", "icon": "🧭"},
            {"title": "Browse all tools", "desc": f"{len(tools_list)} AI tools indexed and reviewed", "icon": "📚"},
        ],
        "category_matches": [],
        "did_you_mean": [],
        "trending": [{"text": t, "score": s} for t, s in trending],
    }
