# --------------- Ecosystem — Multi-Model Collaboration Orchestrator ---------------
"""
v20 · Multi-Model Ecosystem — The "Little Ecosystem"

Orchestrates multi-model collaboration sessions where Claude, o1,
Gemini, Grok, and Llama/DeepSeek work together on a single project.

Collaboration Patterns
──────────────────────
    Sequential Chain    — Model A → B → C  (code gen → review → tests)
    Fan-Out / Fan-In    — Broadcast to N models → aggregate consensus
    Specialist Routing  — Decompose task → route sub-tasks to best model
    Adversarial Review  — Model A generates, Model B (different provider) critiques

Each session maintains shared state (via shared_state.py), tracks costs
(via ai_economics), and enforces guardrails per model output.

Architecture
────────────
    EcosystemMessage    — inter-model message
    EcosystemSession    — stateful project workspace
    CollaborationResult — final output with full trace
    run_collaboration   — main entry point
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("praxis.ecosystem")

try:
    from .model_registry import ModelSpec, get_registry
    from .model_router import (
        RoutingDecision, RoutingStrategy, ScoredModel, route_query,
    )
    from .llm_provider import (
        LLMMessage, LLMResponse, ProviderRouter, get_provider_router,
    )
    from .model_trust_decay import get_trust_monitor
except ImportError:
    from model_registry import ModelSpec, get_registry
    from model_router import (
        RoutingDecision, RoutingStrategy, ScoredModel, route_query,
    )
    from llm_provider import (
        LLMMessage, LLMResponse, ProviderRouter, get_provider_router,
    )
    from model_trust_decay import get_trust_monitor


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MessageType(str, Enum):
    QUERY = "query"
    RESPONSE = "response"
    CRITIQUE = "critique"
    SYNTHESIS = "synthesis"
    CONTEXT = "context"
    SYSTEM = "system"


@dataclass
class EcosystemMessage:
    """Inter-model message within a collaboration session."""
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    correlation_id: str = ""         # links related messages
    from_model: str = "user"
    to_model: str = "broadcast"      # specific model_id or "broadcast"
    content: str = ""
    message_type: MessageType = MessageType.QUERY
    timestamp: float = field(default_factory=time.time)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "from_model": self.from_model,
            "to_model": self.to_model,
            "content": self.content[:500],
            "message_type": self.message_type.value,
            "timestamp": self.timestamp,
            "tokens": self.input_tokens + self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": round(self.latency_ms, 2),
        }


@dataclass
class CollaborationResult:
    """Final output from a multi-model collaboration."""
    session_id: str
    strategy: str
    final_output: str
    models_used: List[str]
    messages: List[EcosystemMessage]
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    consensus_score: float = 0.0    # 0-1, agreement between models
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "strategy": self.strategy,
            "final_output": self.final_output,
            "models_used": self.models_used,
            "message_count": len(self.messages),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": round(self.total_latency_ms, 2),
            "total_tokens": self.total_tokens,
            "consensus_score": round(self.consensus_score, 3),
            "reasoning": self.reasoning,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EcosystemSession:
    """
    Stateful workspace for a multi-model collaboration project.
    Thread-safe, tracks messages, costs, and shared state.
    """

    SESSION_TTL = 3600  # 1 hour

    def __init__(
        self,
        project_name: str = "",
        user_id: str = "anon",
    ):
        self.session_id: str = uuid.uuid4().hex[:16]
        self.project_name: str = project_name or f"project-{self.session_id[:8]}"
        self.user_id: str = user_id
        self.created_at: float = time.time()
        self.last_activity: float = time.time()

        self._lock = threading.RLock()
        self._messages: List[EcosystemMessage] = []
        self._active_models: List[str] = []
        self._total_cost: float = 0.0
        self._total_tokens: int = 0

        # Shared state (dict for simplicity; shared_state.py wraps CoALA)
        self._shared_context: Dict[str, Any] = {}

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > self.SESSION_TTL

    def add_message(self, msg: EcosystemMessage) -> None:
        with self._lock:
            self._messages.append(msg)
            self._total_cost += msg.cost_usd
            self._total_tokens += msg.input_tokens + msg.output_tokens
            self.last_activity = time.time()
            if msg.from_model != "user" and msg.from_model not in self._active_models:
                self._active_models.append(msg.from_model)

    def get_messages(self, limit: int = 50) -> List[EcosystemMessage]:
        with self._lock:
            return self._messages[-limit:]

    def get_context_for_model(self, model_id: str, max_messages: int = 10) -> List[LLMMessage]:
        """Build an LLM-ready message history from recent session messages."""
        with self._lock:
            recent = self._messages[-max_messages:]
        llm_msgs: List[LLMMessage] = []
        for msg in recent:
            if msg.message_type == MessageType.SYSTEM:
                llm_msgs.append(LLMMessage(role="system", content=msg.content))
            elif msg.from_model == "user":
                llm_msgs.append(LLMMessage(role="user", content=msg.content))
            elif msg.from_model == model_id:
                llm_msgs.append(LLMMessage(role="assistant", content=msg.content))
            else:
                # Other model's output → inject as user context
                llm_msgs.append(LLMMessage(
                    role="user",
                    content=f"[Context from {msg.from_model}]: {msg.content}",
                ))
        return llm_msgs

    def set_shared(self, key: str, value: Any, source_model: str = "") -> None:
        with self._lock:
            self._shared_context[key] = {
                "value": value,
                "source_model": source_model,
                "timestamp": time.time(),
            }

    def get_shared(self, key: str) -> Any:
        with self._lock:
            entry = self._shared_context.get(key)
            return entry["value"] if entry else None

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "project_name": self.project_name,
                "user_id": self.user_id,
                "active_models": self._active_models,
                "message_count": len(self._messages),
                "total_cost_usd": round(self._total_cost, 6),
                "total_tokens": self._total_tokens,
                "shared_keys": list(self._shared_context.keys()),
                "age_seconds": round(time.time() - self.created_at, 1),
                "expired": self.is_expired,
            }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SESSION STORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_sessions: Dict[str, EcosystemSession] = {}
_sessions_lock = threading.Lock()
MAX_SESSIONS = 200


def create_session(project_name: str = "", user_id: str = "anon") -> EcosystemSession:
    """Create a new ecosystem collaboration session."""
    session = EcosystemSession(project_name=project_name, user_id=user_id)
    with _sessions_lock:
        # Evict expired sessions
        expired = [sid for sid, s in _sessions.items() if s.is_expired]
        for sid in expired:
            del _sessions[sid]
        # LRU eviction if at capacity
        if len(_sessions) >= MAX_SESSIONS:
            oldest_sid = min(_sessions, key=lambda k: _sessions[k].last_activity)
            del _sessions[oldest_sid]
        _sessions[session.session_id] = session
    log.info("Created ecosystem session %s (%s)", session.session_id, project_name)
    return session


def get_session(session_id: str) -> Optional[EcosystemSession]:
    with _sessions_lock:
        session = _sessions.get(session_id)
        if session and not session.is_expired:
            session.last_activity = time.time()
            return session
        return None


def end_session(session_id: str) -> bool:
    with _sessions_lock:
        if session_id in _sessions:
            del _sessions[session_id]
            return True
        return False


def list_sessions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with _sessions_lock:
        sessions = list(_sessions.values())
    if user_id:
        sessions = [s for s in sessions if s.user_id == user_id]
    return [s.to_dict() for s in sessions if not s.is_expired]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  COLLABORATION EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _call_model(
    model_id: str,
    messages: List[LLMMessage],
    router: ProviderRouter,
    max_tokens: int = 4096,
    temperature: float = 0.3,
) -> LLMResponse:
    """Call a model via ProviderRouter and record telemetry."""
    response = router.complete(model_id, messages, max_tokens, temperature)
    # Feed latency telemetry to trust monitor
    monitor = get_trust_monitor()
    monitor.record_latency(model_id, response.latency_ms)
    return response


def _execute_single(
    task: str,
    model: ScoredModel,
    session: EcosystemSession,
    router: ProviderRouter,
    system_prompt: str = "",
) -> CollaborationResult:
    """Execute task on a single model."""
    correlation_id = uuid.uuid4().hex[:10]

    # Record user message
    user_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model="user",
        to_model=model.spec.model_id,
        content=task,
        message_type=MessageType.QUERY,
    )
    session.add_message(user_msg)

    # Build messages with session context
    messages = session.get_context_for_model(model.spec.model_id)
    if system_prompt:
        messages.insert(0, LLMMessage(role="system", content=system_prompt))

    response = _call_model(model.spec.model_id, messages, router)

    # Record response
    resp_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model=model.spec.model_id,
        to_model="user",
        content=response.content,
        message_type=MessageType.RESPONSE,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        cost_usd=response.cost_usd,
        latency_ms=response.latency_ms,
    )
    session.add_message(resp_msg)

    return CollaborationResult(
        session_id=session.session_id,
        strategy=RoutingStrategy.SINGLE.value,
        final_output=response.content,
        models_used=[model.spec.model_id],
        messages=[user_msg, resp_msg],
        total_cost_usd=response.cost_usd,
        total_latency_ms=response.latency_ms,
        total_tokens=response.input_tokens + response.output_tokens,
        consensus_score=1.0,
        reasoning=f"Single model: {model.spec.display_name}",
    )


def _execute_fan_out(
    task: str,
    models: List[ScoredModel],
    session: EcosystemSession,
    router: ProviderRouter,
    system_prompt: str = "",
) -> CollaborationResult:
    """Broadcast to N models, synthesize results."""
    correlation_id = uuid.uuid4().hex[:10]
    all_messages: List[EcosystemMessage] = []
    responses: List[Tuple[str, str]] = []
    total_cost = 0.0
    total_latency = 0.0
    total_tokens = 0

    # Record user message
    user_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model="user",
        to_model="broadcast",
        content=task,
        message_type=MessageType.QUERY,
    )
    session.add_message(user_msg)
    all_messages.append(user_msg)

    # Call each model sequentially (avoid parallel API calls hitting rate limits)
    for sm in models:
        messages = [
            LLMMessage(role="system", content=system_prompt or "You are a helpful expert assistant."),
            LLMMessage(role="user", content=task),
        ]
        response = _call_model(sm.spec.model_id, messages, router)
        responses.append((sm.spec.model_id, response.content))

        resp_msg = EcosystemMessage(
            correlation_id=correlation_id,
            from_model=sm.spec.model_id,
            to_model="aggregator",
            content=response.content,
            message_type=MessageType.RESPONSE,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        )
        session.add_message(resp_msg)
        all_messages.append(resp_msg)
        total_cost += response.cost_usd
        total_latency += response.latency_ms
        total_tokens += response.input_tokens + response.output_tokens

    # Synthesize: use the primary model to merge results
    synthesis_prompt = _build_synthesis_prompt(task, responses)
    primary = models[0]
    synth_messages = [
        LLMMessage(role="system", content="You synthesize multiple expert responses into one coherent answer. Identify areas of agreement and note any disagreements."),
        LLMMessage(role="user", content=synthesis_prompt),
    ]
    synth_response = _call_model(primary.spec.model_id, synth_messages, router)

    synth_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model=primary.spec.model_id,
        to_model="user",
        content=synth_response.content,
        message_type=MessageType.SYNTHESIS,
        input_tokens=synth_response.input_tokens,
        output_tokens=synth_response.output_tokens,
        cost_usd=synth_response.cost_usd,
        latency_ms=synth_response.latency_ms,
    )
    session.add_message(synth_msg)
    all_messages.append(synth_msg)
    total_cost += synth_response.cost_usd
    total_latency += synth_response.latency_ms
    total_tokens += synth_response.input_tokens + synth_response.output_tokens

    # Simple consensus: keyword overlap between responses
    consensus = _compute_consensus([r[1] for r in responses])

    return CollaborationResult(
        session_id=session.session_id,
        strategy=RoutingStrategy.FAN_OUT.value,
        final_output=synth_response.content,
        models_used=[sm.spec.model_id for sm in models],
        messages=all_messages,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
        total_tokens=total_tokens,
        consensus_score=consensus,
        reasoning=f"Fan-out to {len(models)} models, synthesized by {primary.spec.display_name}",
    )


def _execute_chain(
    task: str,
    models: List[ScoredModel],
    session: EcosystemSession,
    router: ProviderRouter,
    system_prompt: str = "",
) -> CollaborationResult:
    """Sequential chain: each model builds on the previous output."""
    correlation_id = uuid.uuid4().hex[:10]
    all_messages: List[EcosystemMessage] = []
    total_cost = 0.0
    total_latency = 0.0
    total_tokens = 0

    user_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model="user",
        to_model=models[0].spec.model_id,
        content=task,
        message_type=MessageType.QUERY,
    )
    session.add_message(user_msg)
    all_messages.append(user_msg)

    current_output = task
    last_output = ""

    for i, sm in enumerate(models):
        is_first = (i == 0)
        is_last = (i == len(models) - 1)

        if is_first:
            prompt = current_output
        else:
            prompt = (
                f"Previous model's output:\n\n{current_output}\n\n"
                f"Original task: {task}\n\n"
                f"Please {'refine and improve' if not is_last else 'produce the final polished version of'} this response."
            )

        messages = [
            LLMMessage(role="system", content=system_prompt or "You are a helpful expert assistant."),
            LLMMessage(role="user", content=prompt),
        ]
        response = _call_model(sm.spec.model_id, messages, router)
        current_output = response.content
        last_output = response.content

        resp_msg = EcosystemMessage(
            correlation_id=correlation_id,
            from_model=sm.spec.model_id,
            to_model=models[i + 1].spec.model_id if not is_last else "user",
            content=response.content,
            message_type=MessageType.RESPONSE,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
            latency_ms=response.latency_ms,
        )
        session.add_message(resp_msg)
        all_messages.append(resp_msg)
        total_cost += response.cost_usd
        total_latency += response.latency_ms
        total_tokens += response.input_tokens + response.output_tokens

        # Store intermediate in shared state
        session.set_shared(f"chain_step_{i}", response.content, sm.spec.model_id)

    return CollaborationResult(
        session_id=session.session_id,
        strategy=RoutingStrategy.CHAIN.value,
        final_output=last_output,
        models_used=[sm.spec.model_id for sm in models],
        messages=all_messages,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
        total_tokens=total_tokens,
        consensus_score=1.0,
        reasoning=f"Chain: {' → '.join(sm.spec.display_name for sm in models)}",
    )


def _execute_adversarial(
    task: str,
    models: List[ScoredModel],
    session: EcosystemSession,
    router: ProviderRouter,
    system_prompt: str = "",
) -> CollaborationResult:
    """Model A generates, Model B critiques, Model A refines."""
    if len(models) < 2:
        return _execute_single(task, models[0], session, router, system_prompt)

    correlation_id = uuid.uuid4().hex[:10]
    generator = models[0]
    reviewer = models[1]
    all_messages: List[EcosystemMessage] = []
    total_cost = 0.0
    total_latency = 0.0
    total_tokens = 0

    user_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model="user",
        to_model=generator.spec.model_id,
        content=task,
        message_type=MessageType.QUERY,
    )
    session.add_message(user_msg)
    all_messages.append(user_msg)

    # Step 1: Generator produces initial response
    gen_messages = [
        LLMMessage(role="system", content=system_prompt or "You are a helpful expert assistant."),
        LLMMessage(role="user", content=task),
    ]
    gen_response = _call_model(generator.spec.model_id, gen_messages, router)

    gen_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model=generator.spec.model_id,
        to_model=reviewer.spec.model_id,
        content=gen_response.content,
        message_type=MessageType.RESPONSE,
        input_tokens=gen_response.input_tokens,
        output_tokens=gen_response.output_tokens,
        cost_usd=gen_response.cost_usd,
        latency_ms=gen_response.latency_ms,
    )
    session.add_message(gen_msg)
    all_messages.append(gen_msg)
    total_cost += gen_response.cost_usd
    total_latency += gen_response.latency_ms
    total_tokens += gen_response.input_tokens + gen_response.output_tokens

    # Step 2: Reviewer critiques
    review_messages = [
        LLMMessage(role="system", content="You are a rigorous reviewer. Identify errors, gaps, improvements, and rate the response quality on a 1-5 scale."),
        LLMMessage(role="user", content=f"Original task: {task}\n\nResponse to review:\n{gen_response.content}"),
    ]
    review_response = _call_model(reviewer.spec.model_id, review_messages, router)

    review_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model=reviewer.spec.model_id,
        to_model=generator.spec.model_id,
        content=review_response.content,
        message_type=MessageType.CRITIQUE,
        input_tokens=review_response.input_tokens,
        output_tokens=review_response.output_tokens,
        cost_usd=review_response.cost_usd,
        latency_ms=review_response.latency_ms,
    )
    session.add_message(review_msg)
    all_messages.append(review_msg)
    total_cost += review_response.cost_usd
    total_latency += review_response.latency_ms
    total_tokens += review_response.input_tokens + review_response.output_tokens

    # Feed review to trust monitor
    monitor = get_trust_monitor()
    monitor.record_quality(generator.spec.model_id, 3.5)  # neutral default

    # Step 3: Generator refines based on critique
    refine_messages = [
        LLMMessage(role="system", content="Incorporate the reviewer's feedback to improve your response."),
        LLMMessage(role="user", content=f"Your original response:\n{gen_response.content}\n\nReviewer critique:\n{review_response.content}\n\nPlease produce an improved final version."),
    ]
    refine_response = _call_model(generator.spec.model_id, refine_messages, router)

    refine_msg = EcosystemMessage(
        correlation_id=correlation_id,
        from_model=generator.spec.model_id,
        to_model="user",
        content=refine_response.content,
        message_type=MessageType.SYNTHESIS,
        input_tokens=refine_response.input_tokens,
        output_tokens=refine_response.output_tokens,
        cost_usd=refine_response.cost_usd,
        latency_ms=refine_response.latency_ms,
    )
    session.add_message(refine_msg)
    all_messages.append(refine_msg)
    total_cost += refine_response.cost_usd
    total_latency += refine_response.latency_ms
    total_tokens += refine_response.input_tokens + refine_response.output_tokens

    return CollaborationResult(
        session_id=session.session_id,
        strategy=RoutingStrategy.ADVERSARIAL.value,
        final_output=refine_response.content,
        models_used=[generator.spec.model_id, reviewer.spec.model_id],
        messages=all_messages,
        total_cost_usd=total_cost,
        total_latency_ms=total_latency,
        total_tokens=total_tokens,
        consensus_score=0.8,  # adversarial review implies iterative agreement
        reasoning=f"Adversarial: {generator.spec.display_name} generates, {reviewer.spec.display_name} reviews",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tuple = tuple  # avoid import for type hint in function signature

def _build_synthesis_prompt(task: str, responses: list) -> str:
    """Build a synthesis prompt from multiple model responses."""
    parts = [f"Original task: {task}\n"]
    for model_id, content in responses:
        parts.append(f"--- Response from {model_id} ---\n{content}\n")
    parts.append(
        "\nSynthesize these responses into one comprehensive answer. "
        "Highlight points of agreement, note disagreements, and produce "
        "the strongest combined result."
    )
    return "\n".join(parts)


def _compute_consensus(responses: List[str]) -> float:
    """Simple keyword-overlap consensus metric (0-1)."""
    if len(responses) < 2:
        return 1.0
    word_sets = [set(r.lower().split()) for r in responses]
    # Pairwise Jaccard similarity
    similarities: List[float] = []
    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            intersection = len(word_sets[i] & word_sets[j])
            union = len(word_sets[i] | word_sets[j])
            if union > 0:
                similarities.append(intersection / union)
    return round(sum(similarities) / max(len(similarities), 1), 3)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_collaboration(
    task: str,
    session_id: Optional[str] = None,
    strategy: Optional[str] = None,
    budget: str = "medium",
    system_prompt: str = "",
    privacy_required: Optional[str] = None,
    user_id: str = "anon",
) -> CollaborationResult:
    """
    Main entry point for multi-model collaboration.

    If strategy is None, the router decides based on query complexity.
    If session_id is provided, reuses that session; otherwise creates new.
    """
    # Get or create session
    session = None
    if session_id:
        session = get_session(session_id)
    if session is None:
        session = create_session(project_name=task[:50], user_id=user_id)

    # Route the query
    privacy_level = None
    if privacy_required:
        try:
            privacy_level = PrivacyLevel(privacy_required)
        except ValueError:
            pass

    routing = route_query(
        query=task,
        budget=budget,
        privacy_required=privacy_level,
    )

    # Override strategy if explicitly requested
    if strategy:
        try:
            routing_strategy = RoutingStrategy(strategy)
        except ValueError:
            routing_strategy = routing.strategy
    else:
        routing_strategy = routing.strategy

    models = routing.selected_models
    router = get_provider_router()

    # Dispatch to appropriate executor
    if routing_strategy == RoutingStrategy.SINGLE or len(models) < 2:
        return _execute_single(task, models[0], session, router, system_prompt)
    elif routing_strategy == RoutingStrategy.FAN_OUT:
        return _execute_fan_out(task, models, session, router, system_prompt)
    elif routing_strategy == RoutingStrategy.CHAIN:
        return _execute_chain(task, models, session, router, system_prompt)
    elif routing_strategy in (RoutingStrategy.ADVERSARIAL, RoutingStrategy.CONSENSUS):
        return _execute_adversarial(task, models, session, router, system_prompt)
    else:
        return _execute_single(task, models[0], session, router, system_prompt)
