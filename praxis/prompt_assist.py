# --------------- DMN-Guided Prompt Assistance Engine ---------------
"""
Praxis Prompt Assistance & Cross-Model Transfer.

Provides two core capabilities:

    1. **DMN-Guided Prompt Decomposition** — Takes a vague user intent and
       decomposes it into structured decision steps using a Decision Model
       Notation (DMN)-inspired framework. Generates tool-specific optimized
       prompts that dramatically improve output quality.

    2. **PromptBridge Cross-Model Transfer** — When users switch AI tools,
       PromptBridge reformulates their prompts from one model's dialect to
       another's, preserving intent while adapting to each model's strengths.

Confidence Threshold: Prompts below **85%** confidence trigger graceful
fallback to guided manual input rather than low-quality auto-generation.

Integrates with:
    - interpreter.py     (raw intent feeds into decomposition)
    - tools.py           (tool metadata for prompt optimization)
    - outcomes.py        (outcome-aligned prompt framing)

Architecture Note: This module does NOT call any external LLM. Instead it
uses template-based prompt generation with smart variable injection —
fully local, zero-latency, ZDR-compliant.
"""

from typing import Dict, List, Optional
import logging
import re

_log = logging.getLogger("praxis.prompt_assist")


# ======================================================================
# 1. DMN Decision Steps — Canonical Decomposition Templates
# ======================================================================

_DMN_STEPS = {
    "content_creation": {
        "label": "Content Creation Workflow",
        "steps": [
            {"id": "s1", "decision": "Define content type", "options": ["blog", "social", "email", "ad_copy", "whitepaper", "video_script"]},
            {"id": "s2", "decision": "Set target audience", "options": ["technical", "executive", "consumer", "mixed"]},
            {"id": "s3", "decision": "Choose tone & voice", "options": ["professional", "conversational", "persuasive", "educational"]},
            {"id": "s4", "decision": "Specify length & format", "options": ["short-form", "long-form", "structured-outline", "bullet-points"]},
            {"id": "s5", "decision": "Define success metric", "options": ["engagement", "conversion", "comprehension", "SEO_rank"]},
        ],
    },
    "data_analysis": {
        "label": "Data Analysis Workflow",
        "steps": [
            {"id": "s1", "decision": "Define analysis goal", "options": ["trend_detection", "anomaly_detection", "forecasting", "comparison", "segmentation"]},
            {"id": "s2", "decision": "Specify data source", "options": ["csv", "database", "api", "spreadsheet", "real-time_stream"]},
            {"id": "s3", "decision": "Choose analysis depth", "options": ["summary", "detailed", "deep_dive", "executive_overview"]},
            {"id": "s4", "decision": "Select output format", "options": ["chart", "table", "narrative", "dashboard", "report"]},
            {"id": "s5", "decision": "Define confidence level", "options": ["directional", "statistical", "audit-grade"]},
        ],
    },
    "code_generation": {
        "label": "Code Generation Workflow",
        "steps": [
            {"id": "s1", "decision": "Define language & framework", "options": ["python", "javascript", "typescript", "go", "rust", "java", "sql"]},
            {"id": "s2", "decision": "Specify task type", "options": ["new_feature", "refactor", "bug_fix", "test", "migration", "API_endpoint"]},
            {"id": "s3", "decision": "Set quality requirements", "options": ["prototype", "production", "enterprise", "security_hardened"]},
            {"id": "s4", "decision": "Context constraints", "options": ["standalone", "integrated", "microservice", "monolith_module"]},
            {"id": "s5", "decision": "Define documentation level", "options": ["inline_comments", "docstrings", "full_readme", "none"]},
        ],
    },
    "research": {
        "label": "Research & Knowledge Workflow",
        "steps": [
            {"id": "s1", "decision": "Define research scope", "options": ["broad_survey", "deep_dive", "competitive_analysis", "literature_review"]},
            {"id": "s2", "decision": "Set recency requirement", "options": ["latest", "last_6_months", "last_year", "historical"]},
            {"id": "s3", "decision": "Choose source priority", "options": ["academic", "industry", "government", "news", "mixed"]},
            {"id": "s4", "decision": "Define output structure", "options": ["executive_summary", "detailed_report", "comparison_matrix", "brief"]},
            {"id": "s5", "decision": "Bias mitigation", "options": ["balanced_perspectives", "pro_argument", "con_argument", "neutral_synthesis"]},
        ],
    },
    "automation": {
        "label": "Automation & Integration Workflow",
        "steps": [
            {"id": "s1", "decision": "Define trigger event", "options": ["schedule", "webhook", "manual", "data_change", "threshold"]},
            {"id": "s2", "decision": "Specify data flow", "options": ["one-to-one", "one-to-many", "many-to-one", "bidirectional"]},
            {"id": "s3", "decision": "Error handling strategy", "options": ["retry", "alert", "fallback", "queue", "skip"]},
            {"id": "s4", "decision": "Logging level", "options": ["minimal", "standard", "verbose", "audit"]},
            {"id": "s5", "decision": "Deployment target", "options": ["cloud", "on-prem", "hybrid", "local"]},
        ],
    },
}

# Keyword → workflow mapping for auto-detection
_WORKFLOW_SIGNALS = {
    "content_creation": ["write", "blog", "article", "copy", "content", "draft", "post", "newsletter", "email campaign", "social media"],
    "data_analysis": ["analyze", "data", "chart", "graph", "trend", "forecast", "metrics", "dashboard", "report", "sql"],
    "code_generation": ["code", "program", "script", "function", "api", "debug", "refactor", "deploy", "build"],
    "research": ["research", "compare", "find", "evaluate", "review", "study", "survey", "alternatives"],
    "automation": ["automate", "integrate", "connect", "workflow", "trigger", "sync", "schedule", "pipeline", "zapier", "make"],
}


# ======================================================================
# 2. Model Dialect Profiles — PromptBridge
# ======================================================================

_MODEL_DIALECTS = {
    "gpt-4": {
        "name": "GPT-4 / GPT-4o",
        "vendor": "OpenAI",
        "strengths": ["instruction following", "structured output", "nuanced reasoning"],
        "style": "system-message-first",
        "tips": [
            "Use system messages to set persona and constraints",
            "Request JSON output explicitly with `respond in JSON`",
            "Chain-of-thought with 'Let's think step by step'",
        ],
        "template": "System: You are {persona}.\n\nUser: {task_description}\n\nRequirements:\n{requirements}\n\nOutput format: {format}",
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "vendor": "Anthropic",
        "strengths": ["long context", "careful reasoning", "safety-aware", "document analysis"],
        "style": "human-assistant-alternating",
        "tips": [
            "Use XML tags to structure complex inputs: <context>, <task>, <constraints>",
            "Claude excels at 'thinking through' problems — encourage deliberation",
            "Place important instructions at the end of long prompts",
        ],
        "template": "Human: <context>{context}</context>\n\n<task>{task_description}</task>\n\n<constraints>\n{requirements}\n</constraints>\n\nPlease provide output as {format}.\n\nAssistant:",
    },
    "gemini": {
        "name": "Gemini (Google)",
        "vendor": "Google",
        "strengths": ["multimodal", "code generation", "factual grounding"],
        "style": "instruction-first",
        "tips": [
            "Gemini handles structured prompts well — use numbered instructions",
            "Leverage multimodal: reference images/documents inline",
            "Be explicit about format expectations",
        ],
        "template": "Instructions:\n1. {task_description}\n2. Requirements: {requirements}\n3. Output format: {format}\n\nContext: {context}",
    },
    "llama": {
        "name": "Llama 3 / Open Models",
        "vendor": "Meta (Open Source)",
        "strengths": ["local deployment", "privacy", "customizable"],
        "style": "instruct-format",
        "tips": [
            "Use [INST] tags for instruct-tuned variants",
            "Keep prompts shorter — open models have less instruction following capacity",
            "Provide 1-2 examples for best results (few-shot)",
        ],
        "template": "[INST] {task_description}\n\nRequirements: {requirements}\nFormat: {format} [/INST]",
    },
    "mistral": {
        "name": "Mistral / Mixtral",
        "vendor": "Mistral AI",
        "strengths": ["efficiency", "multilingual", "function calling"],
        "style": "instruct-format",
        "tips": [
            "Supports function calling natively — use tool-use prompts",
            "Effective at structured JSON output",
            "Strong multilingual support — prompts work well in non-English",
        ],
        "template": "[INST] Task: {task_description}\nConstraints: {requirements}\nExpected output: {format} [/INST]",
    },
    "copilot": {
        "name": "GitHub Copilot",
        "vendor": "GitHub / OpenAI",
        "strengths": ["code completion", "inline suggestions", "repo context"],
        "style": "code-context",
        "tips": [
            "Write descriptive comments before code for best completions",
            "Open relevant files in tabs for wider context",
            "Use '_' prefix for private helpers to get idiomatic suggestions",
        ],
        "template": "# {task_description}\n# Requirements: {requirements}\n# Expected: {format}\n\n",
    },
}


# ======================================================================
# 3. Workflow Detection
# ======================================================================

CONFIDENCE_THRESHOLD = 0.85  # Below this → graceful fallback


def detect_workflow(query: str) -> Dict:
    """
    Auto-detect the most relevant DMN workflow for a user query.

    Returns:
        {
            "workflow_id": str | None,
            "workflow_label": str,
            "confidence": float,
            "alternatives": [{"id": str, "label": str, "score": float}],
        }
    """
    query_lower = query.lower()
    scores = {}
    for wf_id, signals in _WORKFLOW_SIGNALS.items():
        score = 0.0
        for signal in signals:
            if signal in query_lower:
                score += 0.2
        scores[wf_id] = min(score, 1.0)

    if not scores or max(scores.values()) == 0:
        return {
            "workflow_id": None,
            "workflow_label": "Unknown",
            "confidence": 0.0,
            "alternatives": _format_alternatives(scores),
        }

    best = max(scores, key=scores.get)
    return {
        "workflow_id": best,
        "workflow_label": _DMN_STEPS[best]["label"],
        "confidence": round(scores[best], 3),
        "alternatives": _format_alternatives(scores, exclude=best),
    }


def _format_alternatives(scores: dict, exclude: str = None) -> list:
    return sorted(
        [
            {"id": k, "label": _DMN_STEPS[k]["label"], "score": round(v, 3)}
            for k, v in scores.items()
            if k != exclude and v > 0
        ],
        key=lambda x: x["score"],
        reverse=True,
    )


# ======================================================================
# 4. DMN Decomposition
# ======================================================================

def decompose_intent(query: str, workflow_id: str = None) -> Dict:
    """
    Decompose a user intent into structured DMN decision steps.

    If no workflow_id is provided, auto-detects from query.

    Returns:
        {
            "workflow": {id, label},
            "steps": [{id, decision, options, suggested}],
            "auto_filled": {step_id: suggested_value},
            "confidence": float,
            "needs_manual_input": bool,
        }
    """
    if not workflow_id:
        detected = detect_workflow(query)
        workflow_id = detected["workflow_id"]
        confidence = detected["confidence"]
    else:
        confidence = 1.0

    if not workflow_id or workflow_id not in _DMN_STEPS:
        return {
            "workflow": {"id": None, "label": "Unknown"},
            "steps": [],
            "auto_filled": {},
            "confidence": 0.0,
            "needs_manual_input": True,
        }

    wf = _DMN_STEPS[workflow_id]
    auto_filled = _auto_fill_steps(query, wf["steps"])

    return {
        "workflow": {"id": workflow_id, "label": wf["label"]},
        "steps": wf["steps"],
        "auto_filled": auto_filled,
        "confidence": round(confidence, 3),
        "needs_manual_input": confidence < CONFIDENCE_THRESHOLD or len(auto_filled) < 3,
    }


def _auto_fill_steps(query: str, steps: list) -> dict:
    """Attempt to auto-fill DMN steps from query context."""
    query_lower = query.lower()
    filled = {}
    for step in steps:
        for option in step["options"]:
            normalized = option.replace("_", " ").lower()
            if normalized in query_lower:
                filled[step["id"]] = option
                break
    return filled


# ======================================================================
# 5. Prompt Generation
# ======================================================================

def generate_optimized_prompt(
    query: str,
    tool_name: str = None,
    target_model: str = None,
    workflow_id: str = None,
    step_answers: dict = None,
) -> Dict:
    """
    Generate an optimized prompt for a specific tool/model combination.

    Args:
        query: User's raw intent
        tool_name: Target AI tool name (optional)
        target_model: Target model dialect (optional; key from _MODEL_DIALECTS)
        workflow_id: Pre-selected DMN workflow (optional)
        step_answers: User's answers to DMN steps {step_id: chosen_option}

    Returns:
        {
            "optimized_prompt": str,
            "model_tips": [str],
            "confidence": float,
            "decomposition": {DMN data},
            "model_dialect": str,
        }
    """
    # Decompose intent
    decomposition = decompose_intent(query, workflow_id)
    if step_answers:
        decomposition["auto_filled"].update(step_answers)

    # Build structured task description
    task_desc = query.strip()
    requirements = []
    for step in decomposition.get("steps", []):
        answer = decomposition["auto_filled"].get(step["id"])
        if answer:
            requirements.append(f"{step['decision']}: {answer}")

    requirements_str = "\n".join(f"- {r}" for r in requirements) if requirements else "- Follow best practices"
    context = f"Task based on: {query}"
    fmt = "structured response"

    # Select model dialect
    dialect_key = _resolve_dialect(target_model, tool_name)
    dialect = _MODEL_DIALECTS.get(dialect_key)

    if dialect:
        prompt = dialect["template"].format(
            persona="a helpful expert assistant",
            task_description=task_desc,
            requirements=requirements_str,
            format=fmt,
            context=context,
        )
        tips = dialect["tips"]
    else:
        prompt = f"Task: {task_desc}\n\nRequirements:\n{requirements_str}\n\nOutput: {fmt}"
        tips = ["Use clear, specific language", "Break complex tasks into steps"]

    return {
        "optimized_prompt": prompt,
        "model_tips": tips,
        "confidence": decomposition.get("confidence", 0.0),
        "decomposition": decomposition,
        "model_dialect": dialect_key,
    }


def _resolve_dialect(target_model: str = None, tool_name: str = None) -> str:
    """Map a model name or tool name to a dialect key."""
    if target_model and target_model in _MODEL_DIALECTS:
        return target_model

    if target_model:
        target_lower = target_model.lower()
        for key in _MODEL_DIALECTS:
            if key in target_lower:
                return key

    # Tool-name heuristic
    if tool_name:
        tool_lower = tool_name.lower()
        mapping = {
            "chatgpt": "gpt-4", "openai": "gpt-4", "gpt": "gpt-4",
            "claude": "claude", "anthropic": "claude",
            "gemini": "gemini", "bard": "gemini", "google": "gemini",
            "llama": "llama", "meta": "llama",
            "mistral": "mistral", "mixtral": "mistral",
            "copilot": "copilot", "github": "copilot",
        }
        for hint, dialect in mapping.items():
            if hint in tool_lower:
                return dialect

    return "gpt-4"  # Default dialect


# ======================================================================
# 6. PromptBridge Cross-Model Transfer
# ======================================================================

def bridge_prompt(
    source_prompt: str,
    source_model: str,
    target_model: str,
) -> Dict:
    """
    Transfer a prompt from one model's dialect to another.

    Preserves intent while adapting structure, formatting, and
    best-practice patterns for the target model.

    Returns:
        {
            "original_prompt": str,
            "transferred_prompt": str,
            "source_model": str,
            "target_model": str,
            "adaptation_notes": [str],
        }
    """
    source_dialect = _MODEL_DIALECTS.get(source_model, {})
    target_dialect = _MODEL_DIALECTS.get(target_model, {})

    if not target_dialect:
        return {
            "original_prompt": source_prompt,
            "transferred_prompt": source_prompt,
            "source_model": source_model,
            "target_model": target_model,
            "adaptation_notes": [f"Unknown target model '{target_model}' — returning original prompt"],
        }

    # Extract core intent from source prompt
    core_intent = _extract_core_intent(source_prompt, source_model)

    # Rebuild in target dialect
    transferred = target_dialect["template"].format(
        persona="a helpful expert assistant",
        task_description=core_intent["task"],
        requirements=core_intent["requirements"],
        format=core_intent["format"],
        context=core_intent.get("context", ""),
    )

    notes = []
    if source_dialect.get("style") != target_dialect.get("style"):
        notes.append(
            f"Adapted from {source_dialect.get('style', 'unknown')} style "
            f"to {target_dialect['style']} style"
        )
    notes.extend([
        f"Target strengths: {', '.join(target_dialect.get('strengths', []))}",
        *target_dialect.get("tips", []),
    ])

    return {
        "original_prompt": source_prompt,
        "transferred_prompt": transferred,
        "source_model": source_model,
        "target_model": target_model,
        "adaptation_notes": notes,
    }


def _extract_core_intent(prompt: str, model: str) -> Dict:
    """Parse a prompt to extract task, requirements, and format regardless of source model."""
    lines = prompt.strip().split("\n")
    task = ""
    requirements = ""
    fmt = "structured response"
    context = ""

    for line in lines:
        line_stripped = line.strip()
        low = line_stripped.lower()

        if low.startswith(("task:", "user:", "[inst]", "human:")):
            task = re.sub(r'^(?:task:|user:|human:|\[inst\])\s*', '', line_stripped, flags=re.IGNORECASE)
        elif low.startswith(("requirements:", "constraints:", "rules:")):
            requirements = re.sub(r'^(?:requirements:|constraints:|rules:)\s*', '', line_stripped, flags=re.IGNORECASE)
        elif low.startswith(("format:", "output:", "expected:")):
            fmt = re.sub(r'^(?:format:|output:|expected:)\s*', '', line_stripped, flags=re.IGNORECASE)
        elif low.startswith(("context:", "system:")):
            context = re.sub(r'^(?:context:|system:)\s*', '', line_stripped, flags=re.IGNORECASE)

    if not task:
        task = lines[0] if lines else prompt[:200]

    return {"task": task, "requirements": requirements, "format": fmt, "context": context}


# ======================================================================
# 7. Available Workflows & Models (for UI)
# ======================================================================

def get_available_workflows() -> List[Dict]:
    """Return all DMN workflow templates for UI selection."""
    return [
        {"id": wf_id, "label": wf["label"], "step_count": len(wf["steps"])}
        for wf_id, wf in _DMN_STEPS.items()
    ]


def get_available_models() -> List[Dict]:
    """Return all model dialects for PromptBridge UI."""
    return [
        {
            "id": key,
            "name": dialect["name"],
            "vendor": dialect["vendor"],
            "strengths": dialect["strengths"],
        }
        for key, dialect in _MODEL_DIALECTS.items()
    ]


_log.info(
    "prompt_assist.py loaded — %d DMN workflows, %d model dialects, "
    "confidence threshold %.0f%%",
    len(_DMN_STEPS), len(_MODEL_DIALECTS), CONFIDENCE_THRESHOLD * 100,
)
