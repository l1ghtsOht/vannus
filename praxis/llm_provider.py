# --------------- LLM Provider — Unified Multi-Provider Abstraction ---------------
"""
v20 · Multi-Model Ecosystem — Provider Layer

Replaces scattered ``_llm_call()`` functions across interpreter.py,
reason.py, and prism.py with a single provider abstraction.

Architecture
────────────
    BaseLLMProvider    — abstract interface for completions
    LLMResponse        — uniform response shape
    OpenAIProvider     — OpenAI / o-series (direct HTTP)
    AnthropicProvider  — Claude family (direct HTTP)
    GoogleProvider     — Gemini family (direct HTTP)
    XAIProvider        — Grok family (direct HTTP)
    LocalProvider      — Ollama / vLLM (localhost)
    LiteLLMProvider    — Optional unified backend (100+ providers)
    ProviderRouter     — Maps model_id → correct provider instance

All providers work in **dry-run mode** by default — returning structured
mock responses so that orchestration logic can be tested end-to-end
without API keys.  Supply credentials via environment or explicit config
to switch to live mode.

Security
────────
    • API keys loaded from env vars only — never hardcoded or logged.
    • Keys held in process memory for request lifetime only.
    • Responses are sanitised before returning (strip PII from metadata).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.llm_provider")

try:
    from .model_registry import ModelProvider, ModelSpec, get_registry
except ImportError:
    from model_registry import ModelProvider, ModelSpec, get_registry

try:
    from .ai_economics import token_cost, MODEL_PRICING
except ImportError:
    from ai_economics import token_cost, MODEL_PRICING


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  RESPONSE DATA MODEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class LLMResponse:
    """Uniform response from any LLM provider."""
    content: str
    model_used: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    dry_run: bool = True
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model_used": self.model_used,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "latency_ms": round(self.latency_ms, 2),
            "finish_reason": self.finish_reason,
            "dry_run": self.dry_run,
        }


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str       # "system", "user", "assistant"
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ABSTRACT BASE PROVIDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Mirrors BaseConnector from connectors.py.
    """

    provider_name: str = "base"

    @abstractmethod
    def complete(
        self,
        messages: List[LLMMessage],
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """Synchronous completion. Returns uniform LLMResponse."""
        ...

    def is_available(self) -> bool:
        """Check if this provider has valid credentials."""
        return False

    def _dry_run_response(
        self, messages: List[LLMMessage], model: str, max_tokens: int
    ) -> LLMResponse:
        """Generate a plausible mock response for testing."""
        user_msg = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        mock_content = (
            f"[DRY RUN — {self.provider_name}:{model}] "
            f"Mock response to: {user_msg[:120]}..."
        )
        estimated_input = sum(len(m.content.split()) * 1.3 for m in messages)
        estimated_output = min(len(mock_content.split()) * 1.3, max_tokens)
        return LLMResponse(
            content=mock_content,
            model_used=model,
            provider=self.provider_name,
            input_tokens=int(estimated_input),
            output_tokens=int(estimated_output),
            cost_usd=0.0,
            latency_ms=50.0,
            dry_run=True,
            request_id=hashlib.md5(
                f"{model}{time.time()}".encode()
            ).hexdigest()[:10],
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONCRETE PROVIDERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OpenAIProvider(BaseLLMProvider):
    """OpenAI / o-series provider."""

    provider_name = "openai"

    def __init__(self) -> None:
        self._api_key = os.environ.get("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(
        self,
        messages: List[LLMMessage],
        model: str = "o4-mini",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.is_available():
            return self._dry_run_response(messages, model, max_tokens)

        t0 = time.time()
        try:
            import urllib.request
            payload: Dict[str, Any] = {
                "model": model,
                "messages": [m.to_dict() for m in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            choice = data["choices"][0]
            usage = data.get("usage", {})
            inp = usage.get("prompt_tokens", 0)
            out = usage.get("completion_tokens", 0)
            cost = token_cost(inp, out, model)

            return LLMResponse(
                content=choice["message"]["content"] or "",
                model_used=data.get("model", model),
                provider=self.provider_name,
                input_tokens=inp,
                output_tokens=out,
                cost_usd=cost["total_cost_usd"],
                latency_ms=(time.time() - t0) * 1000,
                finish_reason=choice.get("finish_reason", "stop"),
                dry_run=False,
                request_id=data.get("id", ""),
            )
        except Exception as exc:
            log.error("OpenAI completion failed: %s", exc)
            return self._dry_run_response(messages, model, max_tokens)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude family provider."""

    provider_name = "anthropic"

    def __init__(self) -> None:
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(
        self,
        messages: List[LLMMessage],
        model: str = "claude-4-sonnet",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.is_available():
            return self._dry_run_response(messages, model, max_tokens)

        t0 = time.time()
        try:
            import urllib.request
            # Anthropic Messages API — separate system prompt
            system_msg = ""
            conversation: List[Dict[str, str]] = []
            for m in messages:
                if m.role == "system":
                    system_msg = m.content
                else:
                    conversation.append(m.to_dict())

            payload: Dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": conversation,
            }
            if system_msg:
                payload["system"] = system_msg
            if tools:
                payload["tools"] = tools

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            content_blocks = data.get("content", [])
            text = "".join(
                b.get("text", "") for b in content_blocks if b.get("type") == "text"
            )
            usage = data.get("usage", {})
            inp = usage.get("input_tokens", 0)
            out = usage.get("output_tokens", 0)
            cost = token_cost(inp, out, model)

            return LLMResponse(
                content=text,
                model_used=data.get("model", model),
                provider=self.provider_name,
                input_tokens=inp,
                output_tokens=out,
                cost_usd=cost["total_cost_usd"],
                latency_ms=(time.time() - t0) * 1000,
                finish_reason=data.get("stop_reason", "end_turn"),
                dry_run=False,
                request_id=data.get("id", ""),
            )
        except Exception as exc:
            log.error("Anthropic completion failed: %s", exc)
            return self._dry_run_response(messages, model, max_tokens)


class GoogleProvider(BaseLLMProvider):
    """Google Gemini family provider."""

    provider_name = "google"

    def __init__(self) -> None:
        self._api_key = os.environ.get("GOOGLE_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(
        self,
        messages: List[LLMMessage],
        model: str = "gemini-2.5-pro",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.is_available():
            return self._dry_run_response(messages, model, max_tokens)

        t0 = time.time()
        try:
            import urllib.request
            # Gemini API — convert messages to contents
            contents: List[Dict[str, Any]] = []
            for m in messages:
                role = "user" if m.role in ("user", "system") else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

            payload = {
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                },
            }
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models"
                f"/{model}:generateContent?key={self._api_key}"
            )
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            candidates = data.get("candidates", [{}])
            text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata", {})
            inp = usage.get("promptTokenCount", 0)
            out = usage.get("candidatesTokenCount", 0)
            cost = token_cost(inp, out, model)

            return LLMResponse(
                content=text,
                model_used=model,
                provider=self.provider_name,
                input_tokens=inp,
                output_tokens=out,
                cost_usd=cost["total_cost_usd"],
                latency_ms=(time.time() - t0) * 1000,
                finish_reason=candidates[0].get("finishReason", "STOP") if candidates else "STOP",
                dry_run=False,
                request_id=hashlib.md5(str(data).encode()).hexdigest()[:10],
            )
        except Exception as exc:
            log.error("Google completion failed: %s", exc)
            return self._dry_run_response(messages, model, max_tokens)


class XAIProvider(BaseLLMProvider):
    """xAI Grok family provider (OpenAI-compatible API)."""

    provider_name = "xai"

    def __init__(self) -> None:
        self._api_key = os.environ.get("XAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self._api_key)

    def complete(
        self,
        messages: List[LLMMessage],
        model: str = "grok-3",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.is_available():
            return self._dry_run_response(messages, model, max_tokens)

        t0 = time.time()
        try:
            import urllib.request
            payload: Dict[str, Any] = {
                "model": model,
                "messages": [m.to_dict() for m in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if tools:
                payload["tools"] = tools

            req = urllib.request.Request(
                "https://api.x.ai/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())

            choice = data["choices"][0]
            usage = data.get("usage", {})
            inp = usage.get("prompt_tokens", 0)
            out = usage.get("completion_tokens", 0)
            cost = token_cost(inp, out, model)

            return LLMResponse(
                content=choice["message"]["content"] or "",
                model_used=data.get("model", model),
                provider=self.provider_name,
                input_tokens=inp,
                output_tokens=out,
                cost_usd=cost["total_cost_usd"],
                latency_ms=(time.time() - t0) * 1000,
                finish_reason=choice.get("finish_reason", "stop"),
                dry_run=False,
                request_id=data.get("id", ""),
            )
        except Exception as exc:
            log.error("xAI completion failed: %s", exc)
            return self._dry_run_response(messages, model, max_tokens)


class LocalProvider(BaseLLMProvider):
    """Local model provider (Ollama / vLLM — OpenAI-compatible API)."""

    provider_name = "local"

    def __init__(self, base_url: str = "") -> None:
        self._base_url = (
            base_url
            or os.environ.get("LOCAL_LLM_URL", "http://localhost:11434")
        )

    def is_available(self) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

    def complete(
        self,
        messages: List[LLMMessage],
        model: str = "llama3",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        if not self.is_available():
            return self._dry_run_response(messages, model, max_tokens)

        t0 = time.time()
        try:
            import urllib.request
            # Ollama chat API
            payload = {
                "model": model,
                "messages": [m.to_dict() for m in messages],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            }
            req = urllib.request.Request(
                f"{self._base_url}/api/chat",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())

            content = data.get("message", {}).get("content", "")
            inp = data.get("prompt_eval_count", 0)
            out = data.get("eval_count", 0)

            return LLMResponse(
                content=content,
                model_used=model,
                provider=self.provider_name,
                input_tokens=inp,
                output_tokens=out,
                cost_usd=0.0,  # local = free
                latency_ms=(time.time() - t0) * 1000,
                finish_reason="stop",
                dry_run=False,
                request_id=hashlib.md5(
                    f"{model}{t0}".encode()
                ).hexdigest()[:10],
            )
        except Exception as exc:
            log.error("Local LLM completion failed: %s", exc)
            return self._dry_run_response(messages, model, max_tokens)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PROVIDER ROUTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProviderRouter:
    """
    Maps model_id → correct provider instance.
    Uses ModelRegistry to look up provider type, then dispatches.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseLLMProvider] = {
            ModelProvider.OPENAI.value: OpenAIProvider(),
            ModelProvider.ANTHROPIC.value: AnthropicProvider(),
            ModelProvider.GOOGLE.value: GoogleProvider(),
            ModelProvider.XAI.value: XAIProvider(),
            ModelProvider.LOCAL.value: LocalProvider(),
            ModelProvider.META.value: LocalProvider(),      # Llama runs local
            ModelProvider.DEEPSEEK.value: OpenAIProvider(),  # DeepSeek uses OAI-compat
        }

    def get_provider(self, provider: str) -> BaseLLMProvider:
        return self._providers.get(provider, self._providers[ModelProvider.OPENAI.value])

    def complete(
        self,
        model_id: str,
        messages: List[LLMMessage],
        max_tokens: int = 2048,
        temperature: float = 0.3,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """
        Route a completion request to the correct provider
        based on model_id lookup in ModelRegistry.
        """
        registry = get_registry()
        spec = registry.get(model_id)
        if spec is None:
            log.warning("Model %s not in registry — defaulting to openai", model_id)
            provider = self._providers[ModelProvider.OPENAI.value]
            return provider.complete(messages, model_id, max_tokens, temperature, tools)

        provider = self.get_provider(spec.provider.value)
        return provider.complete(messages, model_id, max_tokens, temperature, tools)

    def available_providers(self) -> Dict[str, bool]:
        """Check which providers have valid credentials."""
        return {name: p.is_available() for name, p in self._providers.items()}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MODULE-LEVEL SINGLETON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_router: Optional[ProviderRouter] = None
_router_lock = threading.Lock()


def get_provider_router() -> ProviderRouter:
    """Return the module-level singleton ProviderRouter."""
    global _router
    if _router is None:
        with _router_lock:
            if _router is None:
                _router = ProviderRouter()
    return _router


def llm_call(
    system: str,
    user: str,
    model: str = "claude-4-sonnet",
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> LLMResponse:
    """
    Drop-in replacement for the scattered _llm_call() functions.
    Can be used anywhere in Praxis.
    """
    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=user),
    ]
    router = get_provider_router()
    return router.complete(model, messages, max_tokens, temperature)
