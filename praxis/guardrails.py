"""
Praxis Guardrails — AI Safety & Output Validation Engine  (v9)

Implements a deterministic Chain-of-Responsibility validation pipeline
that intercepts, inspects, and sanitises every LLM output *before* it
reaches the user or any downstream database.

Architecture  (Chain of Responsibility pattern)
────────────────────────────────────────────────
    raw LLM text
        → ToxicityFilter
        → PIIMasker
        → PromptInjectionDetector
        → SchemaValidator
        → HallucinationDetector
        → (optional custom handlers)
        → validated output  ✓

Key design goals
────────────────
*  Each handler is a single-responsibility class.
*  New handlers can be appended at runtime without touching core logic.
*  The chain halts immediately on any critical violation.
*  Schema enforcement uses pydantic-style field-level validators.
*  Full audit trail for every validation step.

Public API
──────────
    build_guardrail_chain   → assemble a GuardrailChain from handler specs
    validate_output         → run a raw string through the default chain
    validate_with_schema    → validate + enforce a strict JSON schema
    get_default_chain       → lazily-built singleton chain
    list_handlers           → catalogue of available handler types
    check_pii               → standalone PII scan
    check_toxicity          → standalone toxicity scan
    check_injection         → standalone prompt-injection scan
    score_safety            → holistic 0-1 safety score
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

log = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & VALUE OBJECTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Verdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"


@dataclass
class HandlerResult:
    """Result from a single handler in the chain."""
    handler_name: str
    verdict: Verdict
    severity: Severity = Severity.LOW
    detail: str = ""
    redacted_text: Optional[str] = None   # if handler mutated the text
    matches: List[str] = field(default_factory=list)
    elapsed_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handler": self.handler_name,
            "verdict": self.verdict.value,
            "severity": self.severity.value,
            "detail": self.detail,
            "matches": self.matches,
            "redacted": self.redacted_text is not None,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class ChainResult:
    """Aggregated outcome of a full guardrail chain run."""
    final_text: str
    overall_verdict: Verdict
    blocked: bool = False
    handler_results: List[HandlerResult] = field(default_factory=list)
    total_elapsed_ms: int = 0

    @property
    def safety_score(self) -> float:
        """0-1 score where 1.0 = perfectly safe."""
        if self.blocked:
            return 0.0
        penalties = {
            Verdict.WARN: 0.15,
            Verdict.BLOCK: 1.0,
        }
        penalty = sum(penalties.get(hr.verdict, 0.0) for hr in self.handler_results)
        return max(0.0, round(1.0 - penalty, 3))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_verdict": self.overall_verdict.value,
            "blocked": self.blocked,
            "safety_score": self.safety_score,
            "handler_results": [hr.to_dict() for hr in self.handler_results],
            "total_elapsed_ms": self.total_elapsed_ms,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BASE HANDLER (abstract)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BaseHandler:
    """
    Abstract handler in the Chain of Responsibility.

    Subclasses override ``handle(text, context)`` and return a
    ``HandlerResult``.  If the result verdict is BLOCK, the chain
    short-circuits.
    """

    name: str = "base"
    description: str = ""
    severity_on_match: Severity = Severity.HIGH

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        raise NotImplementedError


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUILT-IN HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 1. Toxicity filter ───────────────────────────────────────────

_TOXIC_PATTERNS: List[Tuple[str, Severity]] = [
    # Hate speech / slurs (severity critical)
    (r"\b(hate\s*speech|racial\s*slur|ethnic\s*cleansing)\b", Severity.CRITICAL),
    # Violence
    (r"\b(kill\s+(all|every|them)|bomb\s+threat|mass\s+shooting)\b", Severity.CRITICAL),
    # Self-harm
    (r"\b(how\s+to\s+(commit|attempt)\s+suicide)\b", Severity.CRITICAL),
    # Mild profanity (warning only)
    (r"\b(damn|crap|hell)\b", Severity.LOW),
]


class ToxicityFilter(BaseHandler):
    """
    Lightweight keyword + regex toxicity classifier.

    In production, this would front a fine-tuned semantic classifier
    (e.g. Perspective API, OpenAI moderation endpoint).  The local
    version uses curated regex patterns as a deterministic fallback.
    """

    name = "toxicity_filter"
    description = "Detect hate speech, violent content, and harmful language"
    severity_on_match = Severity.CRITICAL

    def __init__(self, extra_patterns: Optional[List[Tuple[str, Severity]]] = None):
        self._patterns = _TOXIC_PATTERNS + (extra_patterns or [])
        self._compiled = [(re.compile(p, re.IGNORECASE), sev) for p, sev in self._patterns]

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        matches = []
        worst_severity = Severity.LOW

        for compiled, sev in self._compiled:
            found = compiled.findall(text)
            if found:
                matches.extend(found)
                if sev.value > worst_severity.value:
                    worst_severity = sev

        verdict = Verdict.PASS
        if worst_severity in (Severity.CRITICAL, Severity.HIGH):
            verdict = Verdict.BLOCK
        elif matches:
            verdict = Verdict.WARN

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=worst_severity,
            detail=f"{len(matches)} toxic pattern(s) detected" if matches else "clean",
            matches=matches[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 2. PII Masker ────────────────────────────────────────────────

_PII_PATTERNS: Dict[str, str] = {
    "ssn":              r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card":      r"\b(?:\d[ -]*?){13,19}\b",
    "email":            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_us":         r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "ip_address":       r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "us_passport":      r"\b[A-Z]\d{8}\b",
    "uk_nino":          r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b",
    "iban":             r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
    "date_of_birth":    r"\b(?:DOB|date\s*of\s*birth)\s*[:=]?\s*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b",
    "api_key":          r"\b(?:sk-|pk_live_|AKIA)[A-Za-z0-9]{20,}\b",
}

_REDACTION_TAG = "[REDACTED-{type}]"


class PIIMasker(BaseHandler):
    """
    Detect and redact Personally Identifiable Information (PII).

    Matches SSNs, credit card numbers, emails, phone numbers,
    IP addresses, passport numbers, IBANs, API keys, etc.
    Replaces each match with a type-tagged redaction marker.
    """

    name = "pii_masker"
    description = "Detect and redact personally identifiable information"
    severity_on_match = Severity.HIGH

    def __init__(self, extra_patterns: Optional[Dict[str, str]] = None):
        combined = dict(_PII_PATTERNS)
        if extra_patterns:
            combined.update(extra_patterns)
        self._compiled = {
            label: re.compile(pat, re.IGNORECASE)
            for label, pat in combined.items()
        }

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        matches: List[str] = []
        redacted = text

        for label, compiled in self._compiled.items():
            found = compiled.findall(redacted)
            if found:
                matches.extend(f"{label}:{m}" for m in found)
                tag = _REDACTION_TAG.format(type=label.upper())
                redacted = compiled.sub(tag, redacted)

        verdict = Verdict.WARN if matches else Verdict.PASS

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.HIGH if matches else Severity.LOW,
            detail=f"{len(matches)} PII instance(s) redacted" if matches else "no PII detected",
            redacted_text=redacted if matches else None,
            matches=[m.split(":")[0] for m in matches[:15]],  # types only
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 3. Prompt Injection Detector ─────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?above",
    r"you\s+are\s+now\s+(a\s+)?",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"\[INST\]",
    r"###\s*(instruction|system)",
    r"do\s+not\s+follow\s+(the\s+)?rules",
    r"forget\s+(everything|your\s+instructions)",
    r"pretend\s+you\s+are",
    r"bypass\s+(all\s+)?safety",
    r"jailbreak",
    r"DAN\s*mode",
]


class PromptInjectionDetector(BaseHandler):
    """
    Detect common prompt injection and jailbreak attempts.

    Uses a curated set of injection fingerprints.  In production,
    this layer would be backed by a fine-tuned classifier
    (e.g. Rebuff, LLM-Guard, or a custom DistilBERT model).
    """

    name = "prompt_injection_detector"
    description = "Detect prompt injection, jailbreak, and role-override attempts"
    severity_on_match = Severity.CRITICAL

    def __init__(self, extra_patterns: Optional[List[str]] = None):
        all_pats = _INJECTION_PATTERNS + (extra_patterns or [])
        self._compiled = [re.compile(p, re.IGNORECASE) for p in all_pats]

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        matches = []
        for compiled in self._compiled:
            found = compiled.findall(text)
            if found:
                matches.extend(found)

        verdict = Verdict.BLOCK if matches else Verdict.PASS

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.CRITICAL if matches else Severity.LOW,
            detail=f"{len(matches)} injection pattern(s) detected" if matches else "clean",
            matches=matches[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 4. Schema Validator ──────────────────────────────────────────

class FieldSpec:
    """
    Pydantic-style field specification for schema enforcement.

    Parameters
    ----------
    name        : field key in the JSON dict
    dtype       : expected Python type (str, int, float, list, dict, bool)
    required    : whether the field must be present
    validators  : optional list of callables ``(value) -> (bool, reason)``
    description : human-readable purpose
    """

    def __init__(
        self,
        name: str,
        dtype: Type = str,
        required: bool = True,
        validators: Optional[List[Callable]] = None,
        description: str = "",
    ):
        self.name = name
        self.dtype = dtype
        self.required = required
        self.validators = validators or []
        self.description = description

    def validate(self, value: Any) -> List[str]:
        errors: List[str] = []
        if value is None and self.required:
            errors.append(f"missing required field '{self.name}'")
            return errors
        if value is not None and not isinstance(value, self.dtype):
            errors.append(
                f"field '{self.name}' expected {self.dtype.__name__}, "
                f"got {type(value).__name__}"
            )
        for vfn in self.validators:
            try:
                ok, reason = vfn(value)
                if not ok:
                    errors.append(f"field '{self.name}': {reason}")
            except Exception as exc:
                errors.append(f"validator error on '{self.name}': {exc}")
        return errors


class SchemaValidator(BaseHandler):
    """
    Enforce strict JSON schema on LLM output.

    If the raw text is not valid JSON, the handler returns BLOCK.
    If the JSON is valid but fields are wrong, it returns WARN or BLOCK
    depending on the number of errors.
    """

    name = "schema_validator"
    description = "Enforce strict JSON structure on LLM outputs"
    severity_on_match = Severity.HIGH

    def __init__(self, fields: Optional[List[FieldSpec]] = None):
        self._fields = fields or []

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        errors: List[str] = []

        # Try parsing JSON
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return HandlerResult(
                handler_name=self.name,
                verdict=Verdict.BLOCK,
                severity=Severity.HIGH,
                detail="output is not valid JSON",
                matches=["json_parse_error"],
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        if not isinstance(data, dict):
            errors.append(f"expected JSON object, got {type(data).__name__}")

        # Validate fields
        if isinstance(data, dict):
            for fs in self._fields:
                val = data.get(fs.name)
                errs = fs.validate(val)
                errors.extend(errs)

        verdict = Verdict.PASS
        severity = Severity.LOW
        if errors:
            verdict = Verdict.BLOCK if len(errors) > 2 else Verdict.WARN
            severity = Severity.HIGH if len(errors) > 2 else Severity.MEDIUM

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=severity,
            detail=f"{len(errors)} schema violation(s)" if errors else "schema valid",
            matches=errors[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 5. Hallucination Detector ────────────────────────────────────

_HALLUCINATION_SIGNALS = [
    r"(?:as\s+of\s+my\s+(?:last\s+)?(?:training|knowledge)\s+(?:cutoff|update))",
    r"(?:I\s+(?:am\s+)?(?:cannot|can't|unable)\s+(?:to\s+)?(?:access|browse|search)\s+the\s+internet)",
    r"(?:I\s+(?:don'?t|do\s+not)\s+have\s+(?:real-?time|current|up-to-date)\s+(?:data|information))",
    r"(?:(?:according\s+to|based\s+on)\s+(?:my\s+)?(?:training\s+data|knowledge))",
    r"(?:I'?m\s+(?:just\s+)?(?:an?\s+)?(?:AI|language\s+model|chatbot))",
    r"(?:(?:fabricated|invented|made[\s-]+up)\s+(?:data|statistics|source|study|citation))",
]

_CONFIDENT_HALLUCINATION = [
    r"\b(?:studies?\s+(?:show|prove|confirm|demonstrate)\s+that)\b",
    r"\b(?:research(?:ers?)?\s+(?:at|from)\s+[A-Z][a-z]+\s+(?:University|Institute))\b",
    r"\b(?:according\s+to\s+(?:a\s+)?(?:\d{4}\s+)?(?:study|report|paper)\s+(?:by|from|in))\b",
]


class HallucinationDetector(BaseHandler):
    """
    Flag outputs that exhibit hallucination signals.

    Two categories:
    *  **Meta-hallucination** — LLM admits limitations it shouldn't
       (indicates the model broke character).
    *  **Confident-hallucination** — LLM cites fabricated studies
       or statistics with false specificity.
    """

    name = "hallucination_detector"
    description = "Flag hallucinated citations, fabricated statistics, and meta-leakage"
    severity_on_match = Severity.MEDIUM

    def __init__(self):
        self._meta = [re.compile(p, re.IGNORECASE) for p in _HALLUCINATION_SIGNALS]
        self._confident = [re.compile(p, re.IGNORECASE) for p in _CONFIDENT_HALLUCINATION]

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        meta_matches = []
        confident_matches = []

        for pat in self._meta:
            found = pat.findall(text)
            meta_matches.extend(found)

        for pat in self._confident:
            found = pat.findall(text)
            confident_matches.extend(found)

        all_matches = meta_matches + confident_matches
        verdict = Verdict.PASS
        severity = Severity.LOW

        if meta_matches:
            verdict = Verdict.WARN
            severity = Severity.MEDIUM
        if confident_matches and not context:
            # Confident citations without a grounding context = risky
            verdict = Verdict.WARN
            severity = Severity.MEDIUM

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=severity,
            detail=(
                f"{len(meta_matches)} meta-leak(s), "
                f"{len(confident_matches)} ungrounded citation(s)"
            ),
            matches=all_matches[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 6. SQL / Code Injection Detector ─────────────────────────────

_CODE_INJECTION_PATTERNS = [
    r"(?:;\s*DROP\s+TABLE)",
    r"(?:UNION\s+SELECT)",
    r"(?:'\s*OR\s+'1'\s*=\s*'1)",
    r"(?:--\s*$)",
    r"(?:<script\b[^>]*>.*?</script>)",
    r"(?:javascript\s*:)",
    r"(?:eval\s*\()",
    r"(?:exec\s*\()",
    r"(?:__import__\s*\()",
    r"(?:os\.system\s*\()",
    r"(?:subprocess\.(?:run|Popen|call)\s*\()",
]


class CodeInjectionDetector(BaseHandler):
    """
    Detect SQL injection, XSS, and Python code injection attempts.
    """

    name = "code_injection_detector"
    description = "Detect SQL injection, XSS, and arbitrary code execution attempts"
    severity_on_match = Severity.CRITICAL

    def __init__(self, extra_patterns: Optional[List[str]] = None):
        all_pats = _CODE_INJECTION_PATTERNS + (extra_patterns or [])
        self._compiled = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in all_pats]

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        matches = []
        for compiled in self._compiled:
            found = compiled.findall(text)
            if found:
                matches.extend(str(f) for f in found)

        verdict = Verdict.BLOCK if matches else Verdict.PASS

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.CRITICAL if matches else Severity.LOW,
            detail=f"{len(matches)} code injection pattern(s)" if matches else "clean",
            matches=matches[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 7. Cross-Model Consistency Handler ───────────────────────────

class CrossModelConsistencyHandler(BaseHandler):
    """
    Detect contradictions between outputs from different models in
    a multi-model collaboration session.

    Expects ``context`` to contain a ``model_outputs`` list of dicts
    with ``model_id`` and ``content`` keys representing prior outputs
    from other models on the same query.
    """

    name = "cross_model_consistency"
    description = "Flag contradictions across multi-model collaboration outputs"
    severity_on_match = Severity.MEDIUM

    # Contradiction signal patterns
    _NEGATION_PAIRS = [
        (r"\bis\s+(?:not|never)\b", r"\bis\s+(?:always|definitely)\b"),
        (r"\bshould\s+not\b", r"\bmust\s+(?:always)?\b"),
        (r"\bfalse\b", r"\btrue\b"),
        (r"\bno\b", r"\byes\b"),
    ]

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        if not context or "model_outputs" not in context:
            return HandlerResult(
                handler_name=self.name,
                verdict=Verdict.PASS,
                severity=Severity.LOW,
                detail="no multi-model context provided",
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        contradictions: List[str] = []
        prior_outputs = context["model_outputs"]

        for prior in prior_outputs:
            prior_text = prior.get("content", "")
            prior_model = prior.get("model_id", "unknown")
            for pat_a, pat_b in self._NEGATION_PAIRS:
                a_in_current = re.search(pat_a, text, re.IGNORECASE)
                b_in_prior = re.search(pat_b, prior_text, re.IGNORECASE)
                a_in_prior = re.search(pat_a, prior_text, re.IGNORECASE)
                b_in_current = re.search(pat_b, text, re.IGNORECASE)
                if (a_in_current and b_in_prior) or (b_in_current and a_in_prior):
                    contradictions.append(f"negation conflict with {prior_model}")

        verdict = Verdict.WARN if contradictions else Verdict.PASS
        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.MEDIUM if contradictions else Severity.LOW,
            detail=f"{len(contradictions)} contradiction(s) detected" if contradictions else "consistent",
            matches=contradictions[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 8. Model Hallucination Audit Handler ─────────────────────────

class ModelHallucinationAudit(BaseHandler):
    """
    Cross-reference model output against grounding artifacts stored
    in the ecosystem's shared state.

    Expects ``context`` to contain ``grounding_facts`` — a list of
    known-true statements the output should be consistent with.
    """

    name = "model_hallucination_audit"
    description = "Audit model output against grounding artifacts from shared state"
    severity_on_match = Severity.HIGH

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        if not context or "grounding_facts" not in context:
            return HandlerResult(
                handler_name=self.name,
                verdict=Verdict.PASS,
                severity=Severity.LOW,
                detail="no grounding facts provided — skipped",
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        facts = context["grounding_facts"]
        text_lower = text.lower()
        ungrounded: List[str] = []

        # For each fact, check if the output contradicts it by asserting
        # the opposite.  Simple keyword-presence heuristic.
        for fact in facts:
            fact_keywords = set(fact.lower().split())
            # If none of the fact's keywords appear, the output may be
            # hallucinating an alternative — flag for review.
            overlap = fact_keywords & set(text_lower.split())
            if len(overlap) < max(1, len(fact_keywords) // 3):
                ungrounded.append(f"missing grounding: '{fact[:60]}...'")

        verdict = Verdict.PASS
        if len(ungrounded) > len(facts) // 2:
            verdict = Verdict.WARN

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.HIGH if verdict == Verdict.WARN else Severity.LOW,
            detail=f"{len(ungrounded)}/{len(facts)} facts ungrounded" if ungrounded else "grounded",
            matches=ungrounded[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 9. Cost Escalation Handler ───────────────────────────────────

class CostEscalationHandler(BaseHandler):
    """
    Block or warn if a collaboration session's accumulated cost
    exceeds configurable thresholds.

    Expects ``context`` to contain ``session_cost_usd`` (float) and
    optionally ``budget_limit_usd`` (float, default 5.0).
    """

    name = "cost_escalation"
    description = "Block collaboration when cost exceeds session budget"
    severity_on_match = Severity.HIGH

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        if not context or "session_cost_usd" not in context:
            return HandlerResult(
                handler_name=self.name,
                verdict=Verdict.PASS,
                severity=Severity.LOW,
                detail="no session cost context",
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        cost = context["session_cost_usd"]
        limit = context.get("budget_limit_usd", 5.0)
        pct = (cost / max(limit, 0.01)) * 100

        if pct >= 100:
            verdict = Verdict.BLOCK
            severity = Severity.CRITICAL
            detail = f"Session budget exhausted: ${cost:.4f} / ${limit:.2f}"
        elif pct >= 80:
            verdict = Verdict.WARN
            severity = Severity.HIGH
            detail = f"Session budget {pct:.0f}% used: ${cost:.4f} / ${limit:.2f}"
        else:
            verdict = Verdict.PASS
            severity = Severity.LOW
            detail = f"Session budget {pct:.0f}% used"

        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=severity,
            detail=detail,
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ── 10. Privacy Leak Handler ─────────────────────────────────────

class PrivacyLeakHandler(BaseHandler):
    """
    Detect when a model output leaks information that was marked as
    restricted to local-only processing.

    Expects ``context`` to contain ``restricted_terms`` — a list of
    strings that must not appear in outputs sent to cloud models.
    """

    name = "privacy_leak_detector"
    description = "Detect leakage of restricted data in cross-model relay"
    severity_on_match = Severity.CRITICAL

    def handle(self, text: str, context: Optional[Dict[str, Any]] = None) -> HandlerResult:
        t0 = time.perf_counter()
        if not context or "restricted_terms" not in context:
            return HandlerResult(
                handler_name=self.name,
                verdict=Verdict.PASS,
                severity=Severity.LOW,
                detail="no restricted terms defined",
                elapsed_ms=int((time.perf_counter() - t0) * 1000),
            )

        leaked: List[str] = []
        text_lower = text.lower()
        for term in context["restricted_terms"]:
            if term.lower() in text_lower:
                leaked.append(term)

        verdict = Verdict.BLOCK if leaked else Verdict.PASS
        return HandlerResult(
            handler_name=self.name,
            verdict=verdict,
            severity=Severity.CRITICAL if leaked else Severity.LOW,
            detail=f"{len(leaked)} restricted term(s) leaked" if leaked else "clean",
            matches=leaked[:10],
            elapsed_ms=int((time.perf_counter() - t0) * 1000),
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HANDLER REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HANDLER_REGISTRY: Dict[str, Type[BaseHandler]] = {
    "toxicity_filter":           ToxicityFilter,
    "pii_masker":                PIIMasker,
    "prompt_injection_detector": PromptInjectionDetector,
    "schema_validator":          SchemaValidator,
    "hallucination_detector":    HallucinationDetector,
    "code_injection_detector":   CodeInjectionDetector,
    # v20 ecosystem handlers
    "cross_model_consistency":   CrossModelConsistencyHandler,
    "model_hallucination_audit": ModelHallucinationAudit,
    "cost_escalation":           CostEscalationHandler,
    "privacy_leak_detector":     PrivacyLeakHandler,
}


def list_handlers() -> List[Dict[str, str]]:
    """Return catalogue of all registered handler types."""
    result = []
    for key, cls in HANDLER_REGISTRY.items():
        result.append({
            "id": key,
            "name": cls.name,
            "description": cls.description,
            "severity": cls.severity_on_match.value,
        })
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GUARDRAIL CHAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GuardrailChain:
    """
    Ordered chain of handlers.  Running the chain passes text through
    every handler sequentially; if any handler returns BLOCK the chain
    short-circuits and returns the blocked result immediately.
    """

    def __init__(self, handlers: Optional[List[BaseHandler]] = None):
        self._handlers: List[BaseHandler] = handlers or []

    def append(self, handler: BaseHandler) -> "GuardrailChain":
        self._handlers.append(handler)
        return self

    def prepend(self, handler: BaseHandler) -> "GuardrailChain":
        self._handlers.insert(0, handler)
        return self

    @property
    def handler_count(self) -> int:
        return len(self._handlers)

    def run(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        halt_on_block: bool = True,
    ) -> ChainResult:
        """
        Execute every handler in order.

        Parameters
        ----------
        text            Raw LLM output text.
        context         Optional grounding context (e.g. source docs).
        halt_on_block   If True, stop at the first BLOCK verdict.

        Returns
        -------
        ChainResult with aggregated verdicts, optional redacted text,
        and full audit trail.
        """
        t0 = time.perf_counter()
        current_text = text
        handler_results: List[HandlerResult] = []
        blocked = False

        for handler in self._handlers:
            try:
                hr = handler.handle(current_text, context)
            except Exception as exc:
                log.warning("guardrail handler %s raised: %s", handler.name, exc)
                hr = HandlerResult(
                    handler_name=handler.name,
                    verdict=Verdict.WARN,
                    severity=Severity.MEDIUM,
                    detail=f"handler error: {exc}",
                )

            handler_results.append(hr)

            # Apply redaction if handler produced one
            if hr.redacted_text is not None:
                current_text = hr.redacted_text

            if hr.verdict == Verdict.BLOCK:
                blocked = True
                if halt_on_block:
                    break

        # Determine overall verdict
        verdicts = [hr.verdict for hr in handler_results]
        if Verdict.BLOCK in verdicts:
            overall = Verdict.BLOCK
        elif Verdict.WARN in verdicts:
            overall = Verdict.WARN
        else:
            overall = Verdict.PASS

        total_ms = int((time.perf_counter() - t0) * 1000)

        log.info(
            "guardrail_chain: %d handlers, verdict=%s, blocked=%s in %dms",
            len(handler_results), overall.value, blocked, total_ms,
        )

        return ChainResult(
            final_text=current_text,
            overall_verdict=overall,
            blocked=blocked,
            handler_results=handler_results,
            total_elapsed_ms=total_ms,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DEFAULT CHAIN (singleton)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_DEFAULT_CHAIN: Optional[GuardrailChain] = None


def get_default_chain() -> GuardrailChain:
    """
    Return the default guardrail chain, lazily constructed on first call.

    Default chain order:
        1. PromptInjectionDetector  (halt fast on jailbreaks)
        2. CodeInjectionDetector    (halt fast on SQL/XSS)
        3. ToxicityFilter           (block harmful content)
        4. PIIMasker                (redact sensitive data — warn only)
        5. HallucinationDetector    (flag fabricated citations)
    """
    global _DEFAULT_CHAIN
    if _DEFAULT_CHAIN is None:
        _DEFAULT_CHAIN = GuardrailChain([
            PromptInjectionDetector(),
            CodeInjectionDetector(),
            ToxicityFilter(),
            PIIMasker(),
            HallucinationDetector(),
        ])
        log.info("guardrails: default chain built — %d handlers", _DEFAULT_CHAIN.handler_count)
    return _DEFAULT_CHAIN


def build_guardrail_chain(
    handler_ids: Optional[List[str]] = None,
    schema_fields: Optional[List[FieldSpec]] = None,
) -> GuardrailChain:
    """
    Build a custom guardrail chain from handler identifiers.

    Parameters
    ----------
    handler_ids     List of handler IDs from HANDLER_REGISTRY.
                    If None, uses the default chain order.
    schema_fields   Optional list of FieldSpec for schema enforcement.
                    If provided, a SchemaValidator is appended.

    Returns
    -------
    GuardrailChain ready to run.
    """
    if handler_ids is None:
        chain = get_default_chain()
    else:
        handlers = []
        for hid in handler_ids:
            cls = HANDLER_REGISTRY.get(hid)
            if cls is None:
                log.warning("guardrails: unknown handler '%s', skipping", hid)
                continue
            if cls == SchemaValidator and schema_fields:
                handlers.append(SchemaValidator(fields=schema_fields))
            else:
                handlers.append(cls())
        chain = GuardrailChain(handlers)

    # Append schema validator if fields provided and not already present
    if schema_fields and not any(isinstance(h, SchemaValidator) for h in chain._handlers):
        chain.append(SchemaValidator(fields=schema_fields))

    return chain


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONVENIENCE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def validate_output(
    text: str,
    context: Optional[Dict[str, Any]] = None,
) -> ChainResult:
    """Run text through the default guardrail chain."""
    chain = get_default_chain()
    return chain.run(text, context)


def validate_with_schema(
    text: str,
    schema_fields: List[FieldSpec],
    context: Optional[Dict[str, Any]] = None,
) -> ChainResult:
    """Run text through default chain + strict schema enforcement."""
    chain = build_guardrail_chain(schema_fields=schema_fields)
    return chain.run(text, context)


def check_pii(text: str) -> HandlerResult:
    """Standalone PII scan."""
    return PIIMasker().handle(text)


def check_toxicity(text: str) -> HandlerResult:
    """Standalone toxicity scan."""
    return ToxicityFilter().handle(text)


def check_injection(text: str) -> HandlerResult:
    """Standalone prompt injection scan."""
    return PromptInjectionDetector().handle(text)


def check_code_injection(text: str) -> HandlerResult:
    """Standalone code injection scan."""
    return CodeInjectionDetector().handle(text)


def score_safety(text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Holistic safety assessment — runs the full default chain and
    returns a structured safety report with a 0-1 composite score.
    """
    result = validate_output(text, context)
    return {
        "safety_score": result.safety_score,
        "verdict": result.overall_verdict.value,
        "blocked": result.blocked,
        "handlers_run": len(result.handler_results),
        "warnings": [
            hr.to_dict() for hr in result.handler_results
            if hr.verdict != Verdict.PASS
        ],
        "elapsed_ms": result.total_elapsed_ms,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DESIGN PATTERN INTELLIGENCE — Meta-knowledge for the search
#  engine to recommend guardrail patterns to users
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESIGN_PATTERNS: List[Dict[str, Any]] = [
    {
        "id": "chain_of_responsibility",
        "name": "Chain of Responsibility",
        "category": "behavioral",
        "description": (
            "Decoupled handler chain where each handler inspects and "
            "optionally transforms LLM output.  Avoids monolithic "
            "scripts with deeply nested regexes.  New handlers can be "
            "appended at runtime without touching core logic."
        ),
        "use_cases": [
            "PII redaction before database writes",
            "toxicity filtering before user display",
            "schema enforcement on structured LLM outputs",
            "compliance gating in financial pipelines",
        ],
        "python_libraries": ["guardrails-ai", "pydantic", "langchain-core"],
        "anti_pattern": (
            "Monolithic validation script with dozens of nested "
            "if-else blocks and conflicting regex patterns"
        ),
    },
    {
        "id": "schema_enforcement",
        "name": "Strict Schema Enforcement",
        "category": "structural",
        "description": (
            "Force LLM to return valid JSON matching a pydantic BaseModel. "
            "Field-level validators (regex, type, range) reject hallucinated "
            "structures.  On failure, the error message is fed back to the "
            "LLM for automated self-correction."
        ),
        "use_cases": [
            "structured data extraction from unstructured text",
            "API response normalization",
            "compliance report generation",
            "database-ready LLM output pipelines",
        ],
        "python_libraries": ["pydantic", "guardrails-ai", "instructor"],
        "anti_pattern": (
            "Trusting raw LLM text output and parsing with string splits "
            "or fragile regex instead of schema-validated JSON"
        ),
    },
    {
        "id": "architect_first",
        "name": "Architect-First Methodology",
        "category": "process",
        "description": (
            "Human developers act as principal architects; the LLM "
            "generates implementation blueprints (thousands of lines) "
            "before any executable code.  Enforces SOLID principles, "
            "strict naming conventions, and XML documentation standards.  "
            "Prevents hallucinated architectural patterns."
        ),
        "use_cases": [
            "enterprise C#/.NET internal tools",
            "production Python service scaffolding",
            "large-scale refactoring with AI assistance",
        ],
        "python_libraries": ["langchain", "pydantic", "pytest"],
        "anti_pattern": (
            "Vibe coding — prompting LLMs to generate full applications "
            "without specifications, producing monolithic unmaintainable "
            "scripts that fail under enterprise loads"
        ),
    },
    {
        "id": "modular_tdd",
        "name": "Modular Test-Driven Development",
        "category": "process",
        "description": (
            "Unit tests are authored BEFORE application logic.  A Python/Bash "
            "pipeline feeds pytest stubs to an LLM, runs generated code, "
            "and iteratively feeds failure logs back until tests pass or "
            "max retries are reached.  Deterministic quality gate."
        ),
        "use_cases": [
            "AI-assisted code generation with quality guarantees",
            "automated TDD loops for rapid prototyping",
            "continuous integration with LLM-generated modules",
        ],
        "python_libraries": ["pytest", "langchain_openai", "subprocess"],
        "anti_pattern": (
            "Generating code and deploying without automated testing — "
            "accepting AI output on faith without deterministic validation"
        ),
    },
    {
        "id": "differential_privacy",
        "name": "Privacy-Preserving Fine-Tuning (DP-SGD)",
        "category": "privacy",
        "description": (
            "Fine-tune LLMs on classified data using Differential Privacy "
            "Stochastic Gradient Descent.  Injects calibrated mathematical "
            "noise into gradients to prevent membership inference attacks.  "
            "Advanced: Privacy-Flat framework applies perturbation-aware "
            "min-max optimization, flatness-guided sparse prefix-tuning, "
            "and weight knowledge distillation for utility parity under "
            "strict privacy budgets (ε=3)."
        ),
        "use_cases": [
            "government classified document fine-tuning",
            "healthcare PHI model adaptation",
            "financial PII-aware compliance models",
        ],
        "python_libraries": ["opacus", "dp-transformers", "peft"],
        "anti_pattern": (
            "Standard gradient descent fine-tuning on classified data — "
            "allows the model to memorize and regurgitate training examples"
        ),
    },
]


def get_design_patterns() -> List[Dict[str, Any]]:
    """Return all AI safety / guardrail design patterns."""
    return DESIGN_PATTERNS


def recommend_guardrail_pattern(
    query: str,
    *,
    industry: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Score design patterns against a user query and return
    the best-matching ones (most relevant first).
    """
    q_lower = query.lower()
    scored = []

    for pat in DESIGN_PATTERNS:
        score = 0.0
        # Keyword overlap
        desc_lower = pat["description"].lower()
        for word in re.findall(r"[a-z]{4,}", q_lower):
            if word in desc_lower:
                score += 0.08
        # Use-case overlap
        for uc in pat["use_cases"]:
            for word in re.findall(r"[a-z]{4,}", q_lower):
                if word in uc.lower():
                    score += 0.05
        # Industry boost
        if industry:
            ind = industry.lower()
            if ind in desc_lower or any(ind in uc.lower() for uc in pat["use_cases"]):
                score += 0.2
        # Anti-pattern match (user might be describing the bad practice)
        ap_lower = pat.get("anti_pattern", "").lower()
        for word in re.findall(r"[a-z]{4,}", q_lower):
            if word in ap_lower:
                score += 0.06

        if score > 0.05:
            scored.append({"pattern": pat, "relevance": round(min(score, 1.0), 3)})

    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:5]


log.info("guardrails.py loaded — %d handlers, %d design patterns",
         len(HANDLER_REGISTRY), len(DESIGN_PATTERNS))
