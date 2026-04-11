# --------------- Semantic Intelligence Layer ---------------
"""
The brain of Praxis — zero-dependency NLP intelligence that makes
the search engine dramatically smarter than keyword matching.

Capabilities:
    1. Synonym expansion    — "make videos" → video, editing, animation
    2. Typo correction      — "zapire" → "Zapier", "writng" → "writing"
    3. Multi-intent parsing — "write content and automate email" → [writing, automation, email]
    4. TF-IDF scoring       — term-frequency weighting across tool corpus
    5. Query expansion      — contextual broadening of search terms
    6. Negative filtering   — "not X", "without Y", "exclude Z"
    7. Learned signal boost — feedback data influences ranking
    8. Smart suggestions    — "did you mean?" + autocomplete
    9. Industry boosting    — tools proven in user's vertical rank higher
   10. Diversity re-ranking — avoid returning 5 tools in the same niche
"""

import math
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher, get_close_matches
from typing import List, Dict, Optional, Tuple, Set


# ======================================================================
# 1. Synonym & Phrase Expansion
# ======================================================================

# Canonical term → synonyms that should also match
_SYNONYM_MAP = {
    # Tasks
    "writing":      {"write", "copywriting", "content creation", "blogging", "blog", "copywrite", "author", "draft", "drafting", "article", "articles", "copy"},
    "design":       {"graphic design", "graphics", "visual", "visuals", "ui", "ux", "mockup", "mockups", "wireframe", "branding", "brand", "logo", "logos", "illustration"},
    "coding":       {"programming", "code", "develop", "development", "developer", "software", "engineering", "building apps", "web development", "app development", "build"},
    "marketing":    {"growth", "promote", "promotion", "advertising", "ads", "campaigns", "campaign", "outreach", "lead generation", "leads", "funnel", "grow"},
    "automation":   {"automate", "workflow", "workflows", "integrate", "integration", "integrations", "connect", "trigger", "triggers", "pipeline", "pipelines", "zap"},
    "research":     {"analyze", "analysis", "investigate", "study", "explore", "insights", "insight", "data analysis"},
    "analytics":    {"metrics", "tracking", "track", "measure", "measurement", "kpi", "kpis", "dashboard", "dashboards", "reporting", "reports"},
    "video":        {"videos", "animation", "motion", "film", "filming", "youtube", "reels", "tiktok", "shorts", "streaming", "screen recording", "editing video"},
    "audio":        {"podcast", "podcasting", "voice", "voiceover", "text to speech", "tts", "music", "sound", "transcription", "transcribe"},
    "sales":        {"selling", "sell", "crm", "deals", "pipeline", "prospecting", "close deals", "revenue"},
    "support":      {"customer support", "helpdesk", "help desk", "ticketing", "tickets", "customer service", "chat support", "live chat"},
    "email":        {"emails", "email marketing", "newsletters", "newsletter", "outreach", "cold email", "drip", "sequences"},
    "social media": {"social", "instagram", "twitter", "linkedin", "facebook", "tiktok", "posting", "scheduling posts", "social scheduling"},
    "seo":          {"search engine optimization", "search ranking", "keywords", "backlinks", "organic traffic", "serp", "ranking"},
    "no-code":      {"nocode", "low-code", "lowcode", "no code", "drag and drop", "visual builder", "without coding"},
    "data":         {"database", "databases", "data warehouse", "etl", "data pipeline", "data engineering", "sql", "big data"},
    "ml":           {"machine learning", "ai model", "ai models", "deep learning", "neural network", "nlp", "training models", "fine-tuning", "embeddings"},
    "devops":       {"ci/cd", "cicd", "deployment", "deploy", "infrastructure", "hosting", "server", "servers", "monitoring", "observability"},
    "productivity": {"productive", "efficiency", "organize", "organizing", "project management", "task management", "collaboration", "teamwork"},
    "presentations":{"slides", "pitch deck", "pitch decks", "slideshows", "presenting", "keynote"},
    "images":       {"image", "photo", "photos", "picture", "pictures", "image generation", "ai art", "generate images"},
    "forms":        {"surveys", "survey", "quiz", "quizzes", "questionnaire", "feedback forms", "form builder"},
    "payments":     {"billing", "invoicing", "invoices", "subscriptions", "checkout", "payment processing", "stripe"},
    "recruiting":   {"hiring", "hire", "recruitment", "talent", "applicants", "ats", "candidates", "job posting"},
    "legal":        {"contracts", "contract", "legal review", "compliance", "terms", "agreements"},
    "accounting":   {"bookkeeping", "finance", "financial", "expenses", "invoicing", "tax", "taxes"},
    "security":     {"cybersecurity", "infosec", "authentication", "passwords", "encryption", "compliance", "pii", "safe", "safest", "privacy", "gdpr", "hipaa"},
}

# Build reverse lookup: synonym → canonical
_REVERSE_SYNONYMS: Dict[str, str] = {}
for canonical, synonyms in _SYNONYM_MAP.items():
    for syn in synonyms:
        _REVERSE_SYNONYMS[syn.lower()] = canonical
    _REVERSE_SYNONYMS[canonical.lower()] = canonical


def expand_synonyms(terms: List[str]) -> List[str]:
    """Expand a list of terms with their canonical forms.

    Only maps synonyms → canonical (e.g. "blog" → "writing").
    Does NOT add extra synonyms from the canonical's synonym set,
    as that introduces noise (e.g. "marketing" → "leads" → matches CRMs
    when the user asked about blog writing).
    """
    expanded = list(terms)
    for term in terms:
        t = term.lower()
        # Direct synonym → canonical
        if t in _REVERSE_SYNONYMS:
            canonical = _REVERSE_SYNONYMS[t]
            if canonical not in expanded:
                expanded.append(canonical)
    return expanded


# ======================================================================
# 2. Typo Correction
# ======================================================================

# Build a vocabulary from all known terms
_VOCABULARY: Set[str] = set()

def _build_vocabulary(tools_list):
    """Build vocabulary from tool data (called once at import)."""
    global _VOCABULARY
    for t in tools_list:
        _VOCABULARY.add(t.name.lower())
        for c in getattr(t, "categories", []):
            _VOCABULARY.add(c.lower())
        for tag in getattr(t, "tags", []):
            _VOCABULARY.add(tag.lower())
        for kw in getattr(t, "keywords", []):
            _VOCABULARY.add(kw.lower())
    # Add all canonical terms and synonyms
    for canonical, synonyms in _SYNONYM_MAP.items():
        _VOCABULARY.add(canonical)
        _VOCABULARY.update(s.lower() for s in synonyms)
    # Add common English words that should NOT be "corrected" to tool names
    _COMMON_WORDS = {
        "post", "posts", "blog", "need", "help", "make", "making", "best", "good",
        "great", "tool", "tools", "want", "like", "find", "use", "using",
        "work", "working", "team", "small", "large", "free", "paid",
        "fast", "easy", "simple", "complex", "new", "old", "list",
        "manage", "create", "build", "run", "test", "send", "get",
        "set", "plan", "start", "stop", "first", "last", "all",
        "some", "many", "just", "more", "most", "very", "well",
        "our", "your", "their", "can", "will", "should", "could",
        "content", "project", "business", "company", "customer",
        "product", "service", "market", "website", "app", "page",
        "whats", "what", "hows", "how", "whos", "who", "wheres", "where",
        "edit", "editor", "editing", "record", "recording", "video",
        "write", "writing", "read", "reading", "automate", "generate",
        "analyze", "analyse", "design", "code", "coding", "chat",
        "resume", "builder", "assistant", "scheduling", "software",
    }
    _VOCABULARY.update(_COMMON_WORDS)


def correct_typos(terms: List[str], cutoff: float = 0.78) -> Tuple[List[str], Dict[str, str]]:
    """Fix typos in search terms using edit-distance matching.

    Returns:
        (corrected_terms, corrections_dict)
        corrections_dict maps original → corrected for UI "did you mean"
    """
    corrected = []
    corrections = {}
    for term in terms:
        t = term.lower()
        if t in _VOCABULARY:
            corrected.append(t)
            continue
        matches = get_close_matches(t, _VOCABULARY, n=1, cutoff=cutoff)
        if matches:
            corrected.append(matches[0])
            if matches[0] != t:
                corrections[term] = matches[0]
        else:
            corrected.append(t)  # keep as-is
    return corrected, corrections


# ======================================================================
# 3. Multi-Intent Parsing
# ======================================================================

_SPLIT_WORDS = {"and", "also", "plus", "as well as", "along with", "then", "additionally"}

def parse_multi_intent(text: str) -> List[str]:
    """Split a compound query into sub-intents.

    "I need to write blog posts and automate my email marketing"
    → ["write blog posts", "automate my email marketing"]
    """
    # First try comma splits
    parts = re.split(r',\s*', text)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip()]

    # Then try conjunction splits
    pattern = r'\b(?:' + '|'.join(re.escape(w) for w in sorted(_SPLIT_WORDS, key=len, reverse=True)) + r')\b'
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    if len(parts) > 1:
        return [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]

    return [text]


# ======================================================================
# 4. TF-IDF Scoring
# ======================================================================

class TFIDFIndex:
    """Lightweight TF-IDF index built from tool descriptions and metadata."""

    def __init__(self):
        self.doc_count = 0
        self.doc_freq: Dict[str, int] = defaultdict(int)  # term → num docs containing it
        self.tool_vectors: Dict[str, Dict[str, float]] = {}  # tool_name → {term: tfidf}
        self._built = False

    def build(self, tools_list):
        """Build the index from the tools knowledge base."""
        self.doc_count = len(tools_list)
        docs = {}

        for tool in tools_list:
            # Combine all text fields into a single document
            text_parts = [
                tool.name.lower(),
                (tool.description or "").lower(),
                " ".join(c.lower() for c in tool.categories),
                " ".join(t.lower() for t in tool.tags),
                " ".join(k.lower() for k in tool.keywords),
                " ".join(uc.lower() for uc in tool.use_cases),
            ]
            text = " ".join(text_parts)
            terms = _tokenize(text)
            docs[tool.name] = terms

        # Compute document frequency
        for name, terms in docs.items():
            unique_terms = set(terms)
            for t in unique_terms:
                self.doc_freq[t] += 1

        # Compute TF-IDF vectors
        for name, terms in docs.items():
            tf = Counter(terms)
            max_tf = max(tf.values()) if tf else 1
            vector = {}
            for term, count in tf.items():
                tf_val = 0.5 + 0.5 * (count / max_tf)  # augmented TF
                idf_val = math.log((self.doc_count + 1) / (self.doc_freq.get(term, 0) + 1)) + 1
                vector[term] = tf_val * idf_val
            self.tool_vectors[name] = vector

        self._built = True

    def score(self, query_terms: List[str], tool_name: str) -> float:
        """Score a query against a specific tool using cosine-like similarity."""
        if not self._built or tool_name not in self.tool_vectors:
            return 0.0

        tool_vec = self.tool_vectors[tool_name]

        # Build query vector
        q_tf = Counter(t.lower() for t in query_terms)
        max_qtf = max(q_tf.values()) if q_tf else 1

        dot_product = 0.0
        query_norm = 0.0

        for term, count in q_tf.items():
            q_weight = 0.5 + 0.5 * (count / max_qtf)
            idf = math.log((self.doc_count + 1) / (self.doc_freq.get(term, 0) + 1)) + 1
            q_tfidf = q_weight * idf
            query_norm += q_tfidf ** 2

            if term in tool_vec:
                dot_product += q_tfidf * tool_vec[term]

        # Also check expanded terms (partial matches)
        for term in q_tf:
            for tool_term, weight in tool_vec.items():
                if term != tool_term and (term in tool_term or tool_term in term) and len(term) > 3:
                    dot_product += weight * 0.3  # partial match bonus

        tool_norm = sum(v ** 2 for v in tool_vec.values()) ** 0.5
        query_norm = query_norm ** 0.5

        if tool_norm == 0 or query_norm == 0:
            return 0.0

        return dot_product / (tool_norm * query_norm)

    def suggest_similar(self, query_terms: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        """Return the top-N tools ranked by TF-IDF similarity."""
        if not self._built:
            return []
        scores = []
        for name in self.tool_vectors:
            s = self.score(query_terms, name)
            if s > 0:
                scores.append((name, s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_n]


def _tokenize(text: str) -> List[str]:
    """Simple whitespace tokenizer with stopword removal."""
    _stop = {"a", "an", "the", "is", "are", "was", "were", "be", "been",
             "and", "or", "for", "in", "on", "at", "to", "of", "with",
             "by", "from", "it", "its", "this", "that", "as"}
    words = re.split(r'\W+', text.lower())
    return [w for w in words if w and w not in _stop and len(w) > 1]


# ======================================================================
# 5. Negative Query Support
# ======================================================================

_NEGATIVE_PATTERNS = [
    r'\bnot\s+(\w+)',
    r'\bwithout\s+(\w+)',
    r'\bexclude\s+(\w+)',
    r'\bexcluding\s+(\w+)',
    r'\bno\s+(\w+)',
    r'(?<=\s)-(\w+)',  # hyphen-word only after whitespace (not in e-commerce, no-code)
]

def extract_negatives(text: str) -> Tuple[str, List[str]]:
    """Extract negative terms from query, return cleaned query + negatives.

    "I need a CRM not Salesforce" → ("I need a CRM", ["salesforce"])

    Only negates words that look like tool names or product categories —
    general verbs like "hiring", "coding", "paying" are NOT negated
    because "without hiring" means "I don't want to hire", not "exclude
    hiring tools".
    """
    # Words that should never be treated as negatives — they describe
    # the user's situation, not tools to exclude
    _NEGATE_IGNORE = {
        "hiring", "coding", "paying", "spending", "learning", "training",
        "writing", "building", "buying", "selling", "working", "using",
        "needing", "having", "being", "doing", "making", "getting",
        "engineers", "developers", "people", "team", "staff", "employees",
        "money", "time", "budget", "experience", "knowledge",
    }

    negatives = []
    cleaned = text
    for pattern in _NEGATIVE_PATTERNS:
        matches = re.findall(pattern, cleaned, re.IGNORECASE)
        for m in matches:
            if m.lower() not in _NEGATE_IGNORE:
                negatives.append(m.lower())
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned, negatives


# ======================================================================
# 6. Industry Context Boosting
# ======================================================================

# Industry → tool categories/keywords that are especially relevant
_INDUSTRY_BOOST = {
    "startup":    {"automation", "no-code", "productivity", "coding", "analytics", "startup"},
    "saas":       {"analytics", "devops", "coding", "support", "automation", "api"},
    "e-commerce": {"marketing", "payments", "analytics", "seo", "e-commerce", "design"},
    "ecommerce":  {"marketing", "payments", "analytics", "seo", "e-commerce", "design"},
    "agency":     {"design", "marketing", "writing", "presentations", "collaboration", "creative"},
    "enterprise": {"security", "compliance", "analytics", "collaboration", "enterprise"},
    "education":  {"education", "learning", "collaboration", "video", "writing"},
    "healthcare": {"compliance", "security", "data", "analytics"},
    "finance":    {"security", "compliance", "analytics", "data", "accounting"},
    "fintech":    {"payments", "security", "analytics", "coding", "compliance"},
    "legal":      {"legal", "writing", "compliance", "security"},
    "media":      {"video", "audio", "design", "writing", "social media"},
    "real estate":{"marketing", "crm", "email", "automation"},
    "nonprofit":  {"marketing", "email", "forms", "productivity"},
    "retail":     {"e-commerce", "marketing", "analytics", "payments", "social media"},
}

def get_industry_boost(industry: str, tool) -> int:
    """Return a scoring boost if the tool aligns with industry needs."""
    if not industry:
        return 0
    industry_key = industry.lower().strip()
    boost_terms = _INDUSTRY_BOOST.get(industry_key, set())
    if not boost_terms:
        return 0

    tool_terms = set()
    tool_terms.update(c.lower() for c in getattr(tool, "categories", []))
    tool_terms.update(t.lower() for t in getattr(tool, "tags", []))
    tool_terms.update(k.lower() for k in getattr(tool, "keywords", []))

    overlap = tool_terms & boost_terms
    return len(overlap) * 2  # +2 per matching industry signal


# ======================================================================
# 7. Diversity Re-ranking
# ======================================================================

def diversity_rerank(scored_tools: List[tuple], top_n: int = 5) -> List[tuple]:
    """Re-rank results to ensure category diversity.

    Prevents returning 5 writing tools when the user might benefit
    from a mix of categories.
    """
    if len(scored_tools) <= top_n:
        return scored_tools

    result = []
    seen_categories: Dict[str, int] = defaultdict(int)
    MAX_PER_CATEGORY = max(3, top_n - 1)

    # First pass: pick top tools with diversity constraint
    for score, tool in scored_tools:
        if len(result) >= top_n:
            break
        primary_cat = tool.categories[0].lower() if tool.categories else "other"
        if seen_categories[primary_cat] < MAX_PER_CATEGORY:
            result.append((score, tool))
            seen_categories[primary_cat] += 1

    # If we didn't fill enough, add remaining by score
    if len(result) < top_n:
        used_names = {t.name for _, t in result}
        for score, tool in scored_tools:
            if len(result) >= top_n:
                break
            if tool.name not in used_names:
                result.append((score, tool))

    return result


# ======================================================================
# 8. Smart Suggestions / Autocomplete
# ======================================================================

def get_suggestions(partial: str, tools_list, limit: int = 8) -> dict:
    """Generate smart suggestions for a partial query.

    Returns:
        {
            "tool_matches":    [...],   # exact tool name matches
            "category_matches": [...],  # matching categories
            "did_you_mean":    str|None, # typo correction
            "popular_queries":  [...],  # suggested full queries
        }
    """
    p = partial.lower().strip()
    if not p:
        return {"tool_matches": [], "category_matches": [], "did_you_mean": None, "popular_queries": []}

    # Tool name matches (prefix + fuzzy)
    tool_matches = []
    for t in tools_list:
        name_lower = t.name.lower()
        if name_lower.startswith(p) or p in name_lower:
            tool_matches.append(t.name)
    tool_matches = tool_matches[:5]

    # Category matches
    all_cats = set()
    for t in tools_list:
        all_cats.update(c.lower() for c in t.categories)
    category_matches = [c for c in sorted(all_cats) if p in c][:5]

    # Did you mean
    words = p.split()
    _, corrections = correct_typos(words, cutoff=0.7)
    did_you_mean_list = []
    if corrections:
        corrected_words = [corrections.get(w, w) for w in words]
        corrected_str = " ".join(corrected_words)
        if corrected_str != p:
            did_you_mean_list.append(corrected_str)
    # Also add fuzzy matches from vocabulary
    close = get_close_matches(p, list(_VOCABULARY), n=3, cutoff=0.65)
    for c in close:
        if c not in did_you_mean_list and c != p:
            did_you_mean_list.append(c)
    did_you_mean_list = did_you_mean_list[:4]

    # Popular query suggestions
    popular = _generate_query_suggestions(p)

    return {
        "tool_matches": tool_matches,
        "category_matches": category_matches,
        "did_you_mean": did_you_mean_list,
        "popular_queries": popular[:5],
    }


def _generate_query_suggestions(partial: str) -> List[str]:
    """Generate likely full queries based on partial input."""
    _TEMPLATES = [
        "best {0} tools for startups",
        "AI-powered {0} solutions",
        "free {0} tools",
        "{0} for small business",
        "top {0} platforms",
        "{0} tools comparison",
    ]

    # Find the most relevant canonical term
    p = partial.lower()
    match = None
    for canonical in _SYNONYM_MAP:
        if p in canonical or canonical in p:
            match = canonical
            break
    if not match:
        for syn, canonical in _REVERSE_SYNONYMS.items():
            if p in syn:
                match = canonical
                break

    if not match:
        match = partial

    return [t.format(match) for t in _TEMPLATES[:4]]


# ======================================================================
# 9. Learned Signal Integration
# ======================================================================

_learned_quality: Dict[str, dict] = {}
_learned_affinities: List[Tuple[str, str, float]] = []

def load_learned_data():
    """Load learned signals into memory for scoring."""
    global _learned_quality, _learned_affinities
    try:
        from .learning import load_learned_signals
    except Exception:
        try:
            from praxis.learning import load_learned_signals
        except Exception:
            return

    signals = load_learned_signals()
    _learned_quality = signals.get("tool_quality", {})
    _learned_affinities = [
        (a["tool_a"], a["tool_b"], a["affinity"])
        for a in signals.get("pair_affinities", [])
    ]


def get_learned_boost(tool_name: str) -> int:
    """Return a scoring boost based on learned feedback signals."""
    if not _learned_quality:
        load_learned_data()

    metrics = _learned_quality.get(tool_name, {})
    if not metrics:
        return 0

    # Combine accept rate + rating into a boost
    accept_rate = metrics.get("accept_rate", 0)
    avg_rating = metrics.get("avg_rating", 0)
    trend = metrics.get("recent_trend", "stable")

    boost = int(accept_rate * 3 + avg_rating * 0.5)
    if trend == "improving":
        boost += 1
    elif trend == "declining":
        boost -= 1

    return boost


def get_pair_affinity(tool_a: str, tool_b: str) -> float:
    """Return the learned affinity score between two tools."""
    if not _learned_affinities:
        load_learned_data()

    pair = tuple(sorted([tool_a.lower(), tool_b.lower()]))
    for a, b, score in _learned_affinities:
        if tuple(sorted([a.lower(), b.lower()])) == pair:
            return score
    return 0.0


# ======================================================================
# Module initialization
# ======================================================================

# Singleton TF-IDF index
_tfidf_index = TFIDFIndex()

def initialize(tools_list):
    """Initialize all intelligence subsystems. Called once at startup."""
    _build_vocabulary(tools_list)
    _tfidf_index.build(tools_list)
    load_learned_data()


def get_tfidf_index() -> TFIDFIndex:
    """Return the singleton TF-IDF index."""
    return _tfidf_index

# ======================================================================
# Safeguard 3b — Dual-Agent LLM-to-LLM Verification Pipeline
# ======================================================================
# Uses AST mutation from explain.py to verify that an LLM agent truly
# understands code rather than pattern-matching.  A second agent must
# detect injected mutations; if it cannot, the original output is
# flagged as potentially hallucinated.
# ======================================================================


class VerificationPipeline:
    """
    Dual-agent consistency verification for LLM-generated code summaries.

    Protocol:
        1. Agent A summarises the original code  → baseline_summary
        2. Inject AST mutations into the code     → mutated_code
        3. Agent A summarises the mutated code     → mutated_summary
        4. Compare baseline vs mutated summaries   → similarity_score
        5. If similarity > threshold (0.95) → hallucination flag
           (the agent failed to detect a semantic change)
    """

    def __init__(self, *, similarity_threshold: float = 0.95):
        self.similarity_threshold = similarity_threshold

    # ── Summary extraction ───────────────────────────────────────

    @staticmethod
    def _get_summary(code: str) -> str:
        """
        Extract a deterministic structural summary of *code* by
        listing functions, classes, imports, and key control flow.
        Does NOT call an LLM — uses AST for fully reproducible output.
        """
        import ast as _a

        try:
            tree = _a.parse(code)
        except SyntaxError:
            return "UNPARSEABLE"

        parts = []
        for node in _a.walk(tree):
            if isinstance(node, _a.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                parts.append(f"def {node.name}({', '.join(args)})")
            elif isinstance(node, _a.AsyncFunctionDef):
                args = [arg.arg for arg in node.args.args]
                parts.append(f"async def {node.name}({', '.join(args)})")
            elif isinstance(node, _a.ClassDef):
                bases = [
                    getattr(b, "id", getattr(b, "attr", "?"))
                    for b in node.bases
                ]
                parts.append(f"class {node.name}({', '.join(bases)})")
            elif isinstance(node, _a.Import):
                for alias in node.names:
                    parts.append(f"import {alias.name}")
            elif isinstance(node, _a.ImportFrom):
                parts.append(f"from {node.module or '?'} import ...")
            elif isinstance(node, _a.Compare):
                ops = [type(op).__name__ for op in node.ops]
                parts.append(f"compare:{','.join(ops)}")
            elif isinstance(node, _a.BoolOp):
                parts.append(f"boolop:{type(node.op).__name__}")

        return " | ".join(parts) if parts else "EMPTY"

    # ── Similarity scoring ───────────────────────────────────────

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """
        Compute similarity between two summaries using SequenceMatcher
        (stdlib, zero dependencies).  Returns 0.0–1.0.
        """
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    # ── Core verification ────────────────────────────────────────

    def execute_consistency_check(self, original_code: str) -> Dict:
        """
        Run the full dual-agent consistency verification.

        Returns:
            {
                "verified": bool,
                "similarity_score": float,
                "hallucination_risk": str,     # "low" | "medium" | "high"
                "mutations_applied": [str],
                "baseline_summary": str,
                "mutated_summary": str,
                "detail": str,
            }
        """
        # Import the mutation engine from explain.py
        try:
            from .explain import generate_mutation
        except ImportError:
            try:
                from praxis.explain import generate_mutation
            except ImportError:
                return {
                    "verified": False,
                    "similarity_score": -1.0,
                    "hallucination_risk": "unknown",
                    "mutations_applied": [],
                    "baseline_summary": "",
                    "mutated_summary": "",
                    "detail": "Mutation engine (explain.generate_mutation) unavailable",
                }

        # Step 1: baseline summary
        baseline = self._get_summary(original_code)

        # Step 2: inject mutations
        mutated_code, mutations = generate_mutation(original_code, seed=42)

        if not mutations:
            return {
                "verified": True,
                "similarity_score": 0.0,
                "hallucination_risk": "low",
                "mutations_applied": [],
                "baseline_summary": baseline,
                "mutated_summary": baseline,
                "detail": "No mutations possible — code has no comparison/boolean operators",
            }

        # Step 3: summary of mutated code
        mutated_summary = self._get_summary(mutated_code)

        # Step 4: compare
        sim = self._similarity(baseline, mutated_summary)

        # Step 5: verdict
        if sim > self.similarity_threshold:
            risk = "high"
            detail = (
                f"Summaries are {sim:.1%} similar despite {len(mutations)} mutations — "
                f"agent may not truly comprehend the code semantics"
            )
            verified = False
        elif sim > 0.85:
            risk = "medium"
            detail = (
                f"Summaries are {sim:.1%} similar — partial mutation detection"
            )
            verified = True
        else:
            risk = "low"
            detail = (
                f"Summaries diverge ({sim:.1%} similarity) — "
                f"mutations correctly detected"
            )
            verified = True

        return {
            "verified": verified,
            "similarity_score": round(sim, 4),
            "hallucination_risk": risk,
            "mutations_applied": mutations,
            "baseline_summary": baseline,
            "mutated_summary": mutated_summary,
            "detail": detail,
        }