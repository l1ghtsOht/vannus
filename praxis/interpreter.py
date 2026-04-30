# ------- Handles Task Understanding ---------
"""
Converts free-form user queries into structured intent dictionaries.

Two modes:
    1. LLM-backed (OpenAI / Anthropic) — richer, handles ambiguity
    2. Rule-based fallback — zero dependencies, always available

The caller always gets the same output shape regardless of mode:

    {
        "raw":       str,   # original text
        "intent":    str,   # primary task category
        "industry":  str,   # detected industry
        "goal":      str,   # user's goal
        "keywords":  list,  # extracted search terms
        "entities":  list,  # any tool / product names mentioned
        "clarification_needed": bool,
        "suggested_questions": list,  # follow-up Qs the system could ask
    }
"""

import json
import os
import re
import logging
import importlib
log = logging.getLogger("praxis.interpreter")

try:
    from . import config as _cfg
except Exception:
    try:
        import config as _cfg
    except Exception:
        _cfg = None

try:
    from .intelligence import (
        expand_synonyms, correct_typos, parse_multi_intent,
        extract_negatives, _REVERSE_SYNONYMS,
    )
    _INTEL_AVAILABLE = True
except Exception:
    try:
        from praxis.intelligence import (
            expand_synonyms, correct_typos, parse_multi_intent,
            extract_negatives, _REVERSE_SYNONYMS,
        )
        _INTEL_AVAILABLE = True
    except Exception:
        _INTEL_AVAILABLE = False


# ======================================================================
# Public API
# ======================================================================

def interpret(user_input: str) -> dict:
    """Primary entry point.  Tries LLM first, falls back to rule-based."""
    raw = user_input.strip()
    if not raw:
        return _empty_result(raw)

    # Attempt LLM interpretation if configured
    if _cfg and _cfg.llm_available():
        try:
            result = _llm_interpret(raw)
        except Exception as exc:
            log.warning("LLM interpretation failed, falling back to rules: %s", exc)
            result = _rule_based_interpret(raw)
    else:
        result = _rule_based_interpret(raw)

    # ── 2026 Security Blueprint: Sensitive Query Detection ──
    result["sensitive_context"] = detect_sensitive_context(raw)
    if result["sensitive_context"]["is_sensitive"]:
        log.info("sensitive query detected: domains=%s severity=%s",
                 result["sensitive_context"]["domains_detected"],
                 result["sensitive_context"]["severity"])

    return result


# ======================================================================
# LLM-backed interpretation
# ======================================================================

_SYSTEM_PROMPT = """\
You are the intent-extraction module of Vannus, an AI decision engine.
Given a user's free-form text, extract structured information.

Return **only** a JSON object (no markdown fences) with these keys:
  "intent"    – primary task category (one of: writing, design, coding, marketing, automation, research, analytics, devops, support, communication, data, ml, planning, organization)
  "industry"  – detected industry or "" if unclear
  "goal"      – user's high-level goal or "" if unclear
  "keywords"  – list of 3-8 search terms
  "entities"  – list of any specific tool/product/company names mentioned
  "clarification_needed" – true if the query is too vague for a confident recommendation
  "suggested_questions"  – list of 1-3 follow-up questions that would help narrow the recommendation (empty list if none needed)
"""


def _llm_interpret(raw: str) -> dict:
    provider = _cfg.get("llm_provider")
    if provider == "openai":
        return _openai_interpret(raw)
    elif provider == "anthropic":
        return _anthropic_interpret(raw)
    elif provider == "google":
        return _google_interpret(raw)
    elif provider == "groq":
        return _groq_interpret(raw)
    raise RuntimeError(f"Unknown LLM provider: {provider}")


def _openai_interpret(raw: str) -> dict:
    openai = importlib.import_module("openai")
    client = openai.OpenAI(api_key=_cfg.get("openai_api_key"))
    resp = client.chat.completions.create(
        model=_cfg.get("openai_model", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": raw},
        ],
        temperature=0.2,
        max_tokens=400,
    )
    text = resp.choices[0].message.content.strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        log.warning("OpenAI returned non-dict JSON (%s); falling back to rule-based", type(data).__name__)
        return _rule_based_interpret(raw)
    return _normalize_llm_output(raw, data)


def _anthropic_interpret(raw: str) -> dict:
    anthropic = importlib.import_module("anthropic")
    client = anthropic.Anthropic(api_key=_cfg.get("anthropic_api_key"))
    resp = client.messages.create(
        model=_cfg.get("anthropic_model", "claude-3-haiku-20240307"),
        max_tokens=400,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": raw}],
    )
    text = resp.content[0].text.strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        log.warning("Anthropic returned non-dict JSON (%s); falling back to rule-based", type(data).__name__)
        return _rule_based_interpret(raw)
    return _normalize_llm_output(raw, data)


def _google_interpret(raw: str) -> dict:
    import urllib.request
    api_key = os.environ.get("GOOGLE_API_KEY", _cfg.get("google_api_key", ""))
    model = _cfg.get("google_model", "gemini-2.0-flash")
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": _SYSTEM_PROMPT + "\n\nUser query: " + raw}]},
        ],
        "generationConfig": {"maxOutputTokens": 400, "temperature": 0.2},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    text = text.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        return _rule_based_interpret(raw)
    return _normalize_llm_output(raw, data)


def _groq_interpret(raw: str) -> dict:
    import urllib.request
    api_key = os.environ.get("GROQ_API_KEY", _cfg.get("groq_api_key", ""))
    model = _cfg.get("groq_model", "llama-3.3-70b-versatile")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": raw},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    text = result["choices"][0]["message"]["content"].strip()
    text = text.removeprefix("```json").removesuffix("```").strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        return _rule_based_interpret(raw)
    return _normalize_llm_output(raw, data)


def _normalize_llm_output(raw: str, data: dict) -> dict:
    """Ensure LLM output matches the expected schema."""
    return {
        "raw": raw,
        "intent": data.get("intent", ""),
        "industry": data.get("industry", ""),
        "goal": data.get("goal", ""),
        "keywords": data.get("keywords", []),
        "entities": data.get("entities", []),
        "clarification_needed": bool(data.get("clarification_needed", False)),
        "suggested_questions": data.get("suggested_questions", []),
    }


# ======================================================================
# Enhanced rule-based interpretation (zero dependencies)
# ======================================================================

# Stop words to strip from keyword extraction
_STOP_WORDS = {
    "i", "need", "help", "with", "for", "a", "the",
    "please", "want", "to", "my", "some", "me", "on", "in",
    "an", "is", "it", "can", "you", "do", "how", "what",
    "that", "this", "of", "and", "or", "am", "are", "be",
    "looking", "find", "get", "best", "good", "recommend",
    "suggest", "tool", "tools", "use", "using", "should",
}

# Known intent tokens
_INTENTS = {
    "marketing", "design", "automation", "coding", "research",
    "writing", "planning", "organization", "analytics", "data",
    "devops", "support", "communication", "ml", "video", "audio",
    "sales", "email", "social media", "seo", "no-code", "nocode", "security",
    "productivity", "images", "forms", "payments", "recruiting",
    "legal", "accounting", "presentations",
}

# Extended intents reachable via synonym expansion
_SYNONYM_LIKE_INTENTS = _INTENTS | {
    "video", "audio", "sales", "email", "social media", "seo",
    "no-code", "nocode", "security", "productivity", "images", "forms",
    "payments", "recruiting", "legal", "accounting", "presentations",
}

# Known industries
_INDUSTRIES = {
    "restaurant", "restaurants", "ecommerce", "e-commerce", "finance",
    "healthcare", "education", "startup", "retail", "saas",
    "small business", "agency", "enterprise", "fintech", "media",
    "real estate", "legal", "nonprofit",
}

# Goal token → canonical goal
_GOAL_MAP = {
    "grow": "growth", "growth": "growth", "scale": "growth", "scaling": "growth",
    "traffic": "traffic", "visitors": "traffic", "seo": "traffic",
    "sales": "sales", "revenue": "sales", "sell": "sales", "monetize": "sales",
    "prototype": "prototype", "mvp": "prototype", "build": "prototype",
    "learn": "learn", "learning": "learn", "study": "learn",
    "hire": "hire", "hiring": "hire", "recruit": "hire",
    "automate": "automation", "automating": "automation", "efficiency": "automation",
    "save": "cost reduction", "cost": "cost reduction", "cheaper": "cost reduction",
    "collaborate": "collaboration", "teamwork": "collaboration",
}

# Verb → intent mapping
_VERB_MAP = {
    "design": "design", "create": "design", "build": "coding",
    "automate": "automation", "automating": "automation",
    "market": "marketing", "advertise": "marketing", "promote": "marketing",
    "write": "writing", "draft": "writing", "blog": "writing",
    "research": "research", "analyze": "analytics", "analyse": "analytics",
    "monitor": "devops", "deploy": "devops", "track": "analytics",
    "support": "support", "communicate": "communication",
    "plan": "planning", "organize": "organization",
    "record": "video", "edit": "video", "film": "video",
    "sell": "sales", "prospect": "sales", "outreach": "sales",
    "email": "email", "invoice": "accounting", "pay": "payments",
    "hire": "recruiting", "recruit": "recruiting",
    "schedule": "productivity", "manage": "productivity",
    "generate": "images", "illustrate": "design",
    "transcribe": "audio", "podcast": "audio",
    "secure": "security", "encrypt": "security",
}

# Known tool/product names (lowercased) for entity extraction
_KNOWN_TOOLS = {
    "chatgpt", "canva", "zapier", "notion", "figma", "grammarly",
    "hugging face", "huggingface", "airtable", "github", "openai",
    "anthropic", "claude", "pinecone", "weaviate", "descript",
    "replicate", "stability", "surfer", "ahrefs", "hotjar",
    "amplitude", "sentry", "datadog", "segment", "intercom",
    "zendesk", "loom", "otter", "typeform", "slack", "hubspot",
    "jira", "asana", "trello", "monday", "copilot", "cursor",
    "replit", "tabnine", "jasper", "midjourney", "dall-e", "dalle",
    "runway", "elevenlabs", "synthesia", "stripe", "shopify",
    "salesforce", "mailchimp", "semrush", "buffer", "hootsuite",
    "linear", "vercel", "supabase", "postman", "langchain",
    "cohere", "mistral", "perplexity", "gemini", "miro",
    "clickup", "calendly", "freshdesk", "drift", "tidio",
    "bubble", "retool", "make", "n8n", "tableau", "snowflake",
    "mixpanel", "quickbooks", "brex", "vanta", "greenhouse",
}


def _rule_based_interpret(raw: str) -> dict:
    cleaned = raw.lower()

    # Rewrite "without coding" / "no coding" → "no-code" BEFORE negative
    # extraction, so these phrases are treated as intent, not negation.
    _NOCODE_PATTERNS = [
        ("without coding", "nocode"), ("without code", "nocode"),
        ("no coding", "nocode"), ("don't code", "nocode"),
        ("dont code", "nocode"), ("can't code", "nocode"),
    ]
    for pattern, replacement in _NOCODE_PATTERNS:
        if pattern in cleaned:
            cleaned = cleaned.replace(pattern, replacement)

    # ── Intelligence Layer: negatives ──
    negatives = []
    if _INTEL_AVAILABLE:
        cleaned, negatives = extract_negatives(cleaned)

    # Preserve hyphenated compounds (e-commerce, no-code, etc.) before splitting
    _COMPOUND_WORDS = {
        "e-commerce": "ecommerce", "no-code": "nocode", "low-code": "lowcode",
        "ci-cd": "cicd", "co-pilot": "copilot", "text-to-speech": "texttospeech",
    }
    for compound, canonical in _COMPOUND_WORDS.items():
        cleaned = cleaned.replace(compound, canonical)

    words = [w for w in re.split(r'\W+', cleaned) if w and w not in _STOP_WORDS]

    # ── Intelligence Layer: typo correction ──
    corrections = {}
    if _INTEL_AVAILABLE and words:
        words, corrections = correct_typos(words, cutoff=0.75)

    found_intent = None
    found_industry = None
    found_goal = None
    entities = []

    # ── Intelligence Layer: multi-intent ──
    sub_intents = []
    if _INTEL_AVAILABLE:
        sub_intents = parse_multi_intent(cleaned)

    # Scan for intents, industries, goals
    for w in words:
        if not found_intent and w in _INTENTS:
            found_intent = w
        if not found_industry and w in _INDUSTRIES:
            found_industry = w
        if not found_goal and w in _GOAL_MAP:
            found_goal = _GOAL_MAP[w]

    # ── Intelligence Layer: synonym-based intent detection ──
    if not found_intent and _INTEL_AVAILABLE:
        # Try matching multi-word phrases first
        for phrase_len in (3, 2):
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len])
                if phrase in _REVERSE_SYNONYMS:
                    canonical = _REVERSE_SYNONYMS[phrase]
                    if canonical in _INTENTS:
                        found_intent = canonical
                        break
            if found_intent:
                break
        # Then try single-word synonym lookup
        if not found_intent:
            for w in words:
                if w in _REVERSE_SYNONYMS:
                    canonical = _REVERSE_SYNONYMS[w]
                    if canonical in _INTENTS or canonical in _SYNONYM_LIKE_INTENTS:
                        found_intent = canonical
                        break

    # Verb-based intent fallback
    if not found_intent and words:
        found_intent = _VERB_MAP.get(words[0])

    # Entity extraction — check bigrams and unigrams
    cleaned_lower = cleaned
    for tool in _KNOWN_TOOLS:
        if tool in cleaned_lower:
            entities.append(tool)

    # Assemble keywords
    keywords = []
    if found_intent:
        keywords.append(found_intent)
    if found_industry:
        keywords.append(found_industry)
    if found_goal:
        keywords.append(found_goal)
    keywords.extend([w for w in words if w not in keywords])

    # Add secondary intents from multi-intent parsing
    if _INTEL_AVAILABLE and len(sub_intents) > 1:
        for sub in sub_intents[1:]:
            sub_words = [sw for sw in re.split(r'\W+', sub.lower()) if sw and sw not in _STOP_WORDS]
            for sw in sub_words:
                if sw in _INTENTS and sw not in keywords:
                    keywords.append(sw)
                elif sw in _REVERSE_SYNONYMS:
                    canonical = _REVERSE_SYNONYMS[sw]
                    if canonical not in keywords:
                        keywords.append(canonical)

    # ── Intelligence Layer: expand synonyms ──
    if _INTEL_AVAILABLE:
        keywords = expand_synonyms(keywords)

    log.info("interpret: raw=%r → intent=%s, industry=%s, keywords=%s, negatives=%s",
             raw, found_intent, found_industry, keywords[:6], negatives)

    # Determine if clarification is needed
    clarification_needed = not found_intent and len(words) < 3
    suggested_questions = []
    if clarification_needed:
        suggested_questions = [
            "What's the main task you're trying to accomplish?",
            "What industry or domain are you working in?",
        ]
    elif not found_industry:
        suggested_questions.append("What industry are you in? This helps us pick tools that fit your context.")

    return {
        "raw": raw,
        "intent": found_intent,
        "industry": found_industry,
        "goal": found_goal,
        "keywords": keywords,
        "entities": entities,
        "negatives": negatives,
        "corrections": corrections,
        "multi_intents": sub_intents if len(sub_intents) > 1 else [],
        "clarification_needed": clarification_needed,
        "suggested_questions": suggested_questions,
    }


def _empty_result(raw: str) -> dict:
    return {
        "raw": raw,
        "intent": None,
        "industry": None,
        "goal": None,
        "keywords": [],
        "entities": [],
        "clarification_needed": True,
        "suggested_questions": ["Please describe the task you need help with."],
    }


# ======================================================================
# Differential Diagnosis — Structured Intent Extraction
# ======================================================================

# Negation patterns for advanced dependency parsing
_NEGATION_TRIGGERS = {
    "no", "not", "without", "excluding", "except", "avoid",
    "never", "don't", "dont", "doesn't", "doesnt", "isn't", "isnt",
    "won't", "wont", "refuse", "skip", "ban", "block", "remove",
    "absolutely no", "definitely not", "nothing like",
}

# Deployment / environment keywords
_DEPLOYMENT_CONSTRAINTS = {
    "self-hosted", "on-premise", "on-prem", "air-gapped",
    "sovereign", "private cloud", "vpc", "local", "docker",
}

# Compliance keywords
_COMPLIANCE_KEYWORDS = {
    "hipaa", "soc2", "soc 2", "gdpr", "iso27001", "iso 27001",
    "pci-dss", "pci", "ferpa", "ccpa", "fedramp",
}

# ── Sensitive Query Detection (2026 Security Blueprint) ──
# Queries touching these domains auto-escalate to strict privacy mode
# and mandate US-controlled / allied sovereignty tiers.

_SENSITIVE_DOMAINS = {
    "healthcare": {
        "keywords": {"patient", "hipaa", "ehr", "phi", "medical", "diagnosis", "clinical",
                      "prescription", "health record", "protected health", "hospital"},
        "severity": "high",
        "mandate_sovereignty": True,
    },
    "legal": {
        "keywords": {"attorney", "legal", "lawsuit", "litigation", "court", "subpoena",
                      "privilege", "deposition", "compliance", "regulatory filing",
                      "confidential legal", "nda", "contract review"},
        "severity": "high",
        "mandate_sovereignty": True,
    },
    "financial": {
        "keywords": {"pci", "credit card", "bank account", "ssn", "social security",
                      "tax return", "financial statement", "account number", "routing number",
                      "investment portfolio", "trading", "audit financials"},
        "severity": "high",
        "mandate_sovereignty": True,
    },
    "government": {
        "keywords": {"classified", "secret", "top secret", "cui", "fouo",
                      "government contract", "fedramp", "itar", "export control",
                      "defense", "military", "clearance", "dod"},
        "severity": "critical",
        "mandate_sovereignty": True,
    },
    "pii": {
        "keywords": {"personal data", "pii", "date of birth", "passport", "driver license",
                      "biometric", "fingerprint", "face recognition", "identity",
                      "home address", "phone number", "email address"},
        "severity": "medium",
        "mandate_sovereignty": False,
    },
}


def detect_sensitive_context(query: str) -> dict:
    """
    Scan a query for sensitive-domain indicators.

    Returns:
        {
            "is_sensitive": bool,
            "domains_detected": [str],       # healthcare, legal, financial, etc.
            "severity": "none"|"medium"|"high"|"critical",
            "mandate_sovereignty": bool,     # True → force US-controlled tier
            "mandate_zdr": bool,             # True → force zero data retention
            "privacy_escalation": str,       # "none"|"elevated"|"strict"
        }
    """
    q_lower = query.lower()
    detected = []
    max_severity = "none"
    mandate_sov = False
    severity_order = {"none": 0, "medium": 1, "high": 2, "critical": 3}

    for domain, cfg in _SENSITIVE_DOMAINS.items():
        for kw in cfg["keywords"]:
            if kw in q_lower:
                if domain not in detected:
                    detected.append(domain)
                sev = cfg["severity"]
                if severity_order.get(sev, 0) > severity_order.get(max_severity, 0):
                    max_severity = sev
                if cfg.get("mandate_sovereignty"):
                    mandate_sov = True
                break

    is_sensitive = len(detected) > 0
    if max_severity == "critical":
        escalation = "strict"
    elif max_severity == "high":
        escalation = "strict"
    elif max_severity == "medium":
        escalation = "elevated"
    else:
        escalation = "none"

    return {
        "is_sensitive": is_sensitive,
        "domains_detected": detected,
        "severity": max_severity,
        "mandate_sovereignty": mandate_sov,
        "mandate_zdr": is_sensitive,  # Any sensitive context → ZDR
        "privacy_escalation": escalation,
    }


def extract_structured_intents(user_query: str) -> dict:
    """
    Advanced intent extraction for the differential diagnosis pipeline.

    Produces a richer output than the standard `interpret()` function,
    with explicit separation of positive intents, negative constraints,
    and ambiguity assessment.

    Returns:
        {
            "raw": str,
            "positive_intents": [str],      # what the user WANTS
            "negative_constraints": [str],   # what the user REJECTS
            "compliance_requirements": [str], # detected compliance mandates
            "deployment_preferences": [str], # deployment env requirements
            "entities_mentioned": [str],     # specific tool/vendor names
            "ambiguity_flags": {
                "severity": float,           # 0.0 (clear) – 1.0 (opaque)
                "missing_axes": [str],
                "is_vague": bool,
            },
            "multi_intents": [str],          # if compound query detected
            "interpreted": dict,             # full output from interpret()
        }
    """
    interpreted = interpret(user_query)
    raw_lower = user_query.lower()

    # ── Positive Intents ──
    positives = []
    for key in ("intent", "industry", "goal"):
        val = interpreted.get(key)
        if val:
            positives.append(str(val).lower())
    positives.extend([k.lower() for k in interpreted.get("keywords", [])])
    positives = list(dict.fromkeys(positives))  # dedupe preserving order

    # ── Negative Constraints (enhanced) ──
    negatives = list(interpreted.get("negatives", []))

    # Deep scan for negation patterns not caught by basic extraction
    for trigger in _NEGATION_TRIGGERS:
        idx = raw_lower.find(trigger)
        if idx >= 0:
            # Extract the object of negation (next 1-3 words)
            remainder = raw_lower[idx + len(trigger):].strip()
            words = [w for w in re.split(r'\W+', remainder) if w and w not in _STOP_WORDS]
            for w in words[:3]:
                # Check if it's a known tool or meaningful noun
                if w in _KNOWN_TOOLS and w not in negatives:
                    negatives.append(w)
                elif w in _INTENTS and w not in negatives:
                    negatives.append(w)
            break  # avoid double-counting overlapping triggers

    negatives = list(dict.fromkeys(negatives))

    # ── Compliance Requirements (auto-detect from raw query) ──
    compliance = []
    for kw in _COMPLIANCE_KEYWORDS:
        if kw in raw_lower:
            canonical = kw.upper().replace(" ", "").replace("-", "")
            # Normalise
            mapping = {
                "SOC2": "SOC2", "HIPAA": "HIPAA", "GDPR": "GDPR",
                "ISO27001": "ISO27001", "PCIDSS": "PCI-DSS", "PCI": "PCI-DSS",
                "FERPA": "FERPA", "CCPA": "CCPA", "FEDRAMP": "FedRAMP",
            }
            norm = mapping.get(canonical, canonical)
            if norm not in compliance:
                compliance.append(norm)

    # ── Deployment Preferences ──
    deployment = []
    for dp in _DEPLOYMENT_CONSTRAINTS:
        if dp in raw_lower:
            deployment.append(dp)

    # ── Entities ──
    entities = list(interpreted.get("entities", []))

    # ── Ambiguity Assessment ──
    keyword_count = len(positives)
    has_intent = bool(interpreted.get("intent"))
    has_industry = bool(interpreted.get("industry"))

    if keyword_count == 0:
        severity = 1.0
    elif not has_intent and keyword_count < 2:
        severity = 0.85
    elif not has_intent:
        severity = 0.6
    elif not has_industry and keyword_count < 3:
        severity = 0.4
    else:
        severity = 0.1

    missing_axes = []
    if not has_intent:
        missing_axes.append("task_category")
    if not has_industry:
        missing_axes.append("industry_vertical")
    if keyword_count < 2:
        missing_axes.append("specific_requirements")

    # ── Multi-intents ──
    multi = interpreted.get("multi_intents", [])

    return {
        "raw": user_query,
        "positive_intents": positives,
        "negative_constraints": negatives,
        "compliance_requirements": compliance,
        "deployment_preferences": deployment,
        "entities_mentioned": entities,
        "ambiguity_flags": {
            "severity": severity,
            "missing_axes": missing_axes,
            "is_vague": severity >= 0.7,
        },
        "multi_intents": multi,
        "interpreted": interpreted,
        # ── 2026 Security Blueprint: Sensitive context propagation ──
        "sensitive_context": interpreted.get("sensitive_context", detect_sensitive_context(user_query)),
    }


# =====================================================================
# Safeguard 4 — Boring Code Optimization (KERNEL Prompting Framework)
# =====================================================================
# Forces LLM-generated code toward maintainability by constructing
# prompts that explicitly forbid clever patterns and mandate "boring"
# idiomatic Python.  Uses the KERNEL framework:
#   K — Knowledge context
#   E — Explicit constraints
#   R — Required output format
#   N — Negative examples (what NOT to do)
#   E — Evaluation criteria
#   L — Limitations acknowledgement
# =====================================================================

from dataclasses import dataclass as _dc2, field as _fld2
from typing import List as _List2, Optional as _Opt2


@_dc2
class KernelPromptContext:
    """Input context for the KERNEL boring-code prompt builder."""
    task_goal: str                          # What the code should accomplish
    input_context: str = ""                 # Relevant codebase context
    verification_criteria: _List2[str] = _fld2(default_factory=list)
    target_language: str = "Python"
    max_function_lines: int = 30


class PromptInterpreter:
    """
    Builds KERNEL-framework prompts that steer LLMs toward producing
    maintainable, "boring" code — no clever tricks, no deep nesting,
    explicit control flow, comprehensive docstrings.
    """

    EXPLICIT_CONSTRAINTS: _List2[str] = [
        "Follow PEP 8 style conventions strictly",
        "No nested ternary expressions",
        "No multi-clause list/dict/set comprehensions (max 1 clause)",
        "Maximum function length: 30 lines (excluding docstring)",
        "Use explicit for-loops instead of map/filter/reduce",
        "Every function must have a Google-style docstring",
        "No single-letter variable names except i/j/k in loops and x/y in lambdas",
        "No monkey-patching or runtime class modification",
        "No *args/**kwargs unless wrapping an external API",
        "Prefer early returns over deeply nested if/else chains",
        "No global mutable state — use dependency injection",
        "Type hints on all function signatures",
    ]

    NEGATIVE_EXAMPLES: _List2[str] = [
        "# BAD: nested ternary\nresult = a if x else (b if y else c)",
        "# BAD: multi-clause comprehension\n[f(x) for x in items if x.active for y in x.parts if y.valid]",
        "# BAD: clever one-liner\ndata = {k: v for d in [a, b, c] for k, v in d.items()}",
        "# BAD: implicit behaviour\ndef process(items, cache={}): ...",
    ]

    def __init__(self, extra_constraints: _Opt2[_List2[str]] = None):
        self.constraints = list(self.EXPLICIT_CONSTRAINTS)
        if extra_constraints:
            self.constraints.extend(extra_constraints)

    def build_boring_prompt(self, ctx: KernelPromptContext) -> str:
        """
        Build a KERNEL-framework prompt from the given context.

        Returns a fully formatted prompt string ready to send to an LLM.
        """
        constraints_block = "\n".join(f"  {i+1}. {c}" for i, c in enumerate(self.constraints))
        negatives_block = "\n\n".join(self.NEGATIVE_EXAMPLES)
        criteria = ctx.verification_criteria or [
            "All functions < 30 lines",
            "No nesting deeper than 3 levels",
            "Every public function has a docstring",
            "Type hints on all signatures",
        ]
        criteria_block = "\n".join(f"  - {c}" for c in criteria)

        prompt = (
            f"## K — Knowledge Context\n"
            f"Language: {ctx.target_language}\n"
            f"Task: {ctx.task_goal}\n"
        )
        if ctx.input_context:
            prompt += f"Existing code context:\n```\n{ctx.input_context}\n```\n"

        prompt += (
            f"\n## E — Explicit Constraints\n"
            f"{constraints_block}\n"
            f"\n## R — Required Output Format\n"
            f"Return ONLY valid {ctx.target_language} code. "
            f"Each function must be ≤ {ctx.max_function_lines} lines. "
            f"Include complete type hints and docstrings.\n"
            f"\n## N — Negative Examples (DO NOT produce code like this)\n"
            f"```python\n{negatives_block}\n```\n"
            f"\n## E — Evaluation Criteria\n"
            f"Your code will be verified against:\n"
            f"{criteria_block}\n"
            f"\n## L — Limitations\n"
            f"- Do not assume availability of external packages unless specified\n"
            f"- Do not use deprecated APIs\n"
            f"- Prefer stdlib solutions over third-party dependencies\n"
            f"- If a task requires >5 functions, split across multiple modules\n"
        )

        return prompt.strip()

    def validate_boring_compliance(self, source_code: str) -> dict:
        """
        Check whether *source_code* adheres to boring-code constraints.

        Returns:
            {
                "compliant": bool,
                "violations": [{"rule": str, "detail": str, "line": int}],
                "stats": {"functions": int, "max_length": int, "has_type_hints": bool},
            }
        """
        import ast as _a

        violations = []
        try:
            tree = _a.parse(source_code)
        except SyntaxError as exc:
            return {
                "compliant": False,
                "violations": [{"rule": "syntax", "detail": str(exc), "line": exc.lineno or 0}],
                "stats": {},
            }

        lines = source_code.splitlines()
        func_count = 0
        max_length = 0
        has_any_hints = False

        for node in _a.walk(tree):
            if isinstance(node, (_a.FunctionDef, _a.AsyncFunctionDef)):
                func_count += 1
                # Length check
                func_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                # Subtract docstring lines
                _str_types = (_a.Constant,) + ((_a.Str,) if hasattr(_a, 'Str') else ())
                if (node.body and isinstance(node.body[0], _a.Expr)
                        and isinstance(node.body[0].value, _str_types)):
                    doc_lines = (node.body[0].end_lineno or node.body[0].lineno) - node.body[0].lineno + 1
                    func_lines -= doc_lines

                if func_lines > max_length:
                    max_length = func_lines

                if func_lines > 30:
                    violations.append({
                        "rule": "max_function_length",
                        "detail": f"{node.name}() is {func_lines} lines (limit: 30)",
                        "line": node.lineno,
                    })

                # Docstring check
                has_doc = (
                    node.body
                    and isinstance(node.body[0], _a.Expr)
                    and isinstance(node.body[0].value, _str_types)
                )
                if not has_doc:
                    violations.append({
                        "rule": "missing_docstring",
                        "detail": f"{node.name}() has no docstring",
                        "line": node.lineno,
                    })

                # Return type hint check
                if node.returns:
                    has_any_hints = True
                else:
                    violations.append({
                        "rule": "missing_return_type",
                        "detail": f"{node.name}() missing return type hint",
                        "line": node.lineno,
                    })

        # Check for nested ternaries (simple regex heuristic)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Nested ternary: "x if ... else y if ... else z"
            if_count = stripped.count(" if ") + stripped.count(" else ")
            if if_count >= 4:  # at least 2 ternary expressions
                violations.append({
                    "rule": "nested_ternary",
                    "detail": "Possible nested ternary expression",
                    "line": i,
                })

        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "stats": {
                "functions": func_count,
                "max_length": max_length,
                "has_type_hints": has_any_hints,
            },
        }
