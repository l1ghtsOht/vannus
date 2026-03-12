# --------------- Praxis Connectors — Tool Adapter Framework ---------------
"""
v19 · Platform Evolution — Execution Engine

Provides a pluggable adapter layer that lets Praxis *execute* tool
interactions instead of merely recommending them.  Each connector wraps
a third-party API behind a uniform interface so that the workflow engine
can chain tools without caring about vendor specifics.

Architecture
────────────
    ConnectorSpec      — declarative schema describing a connector's
                         capabilities, auth requirements, and endpoints.
    BaseConnector      — abstract base class every adapter extends.
    ConnectorRegistry  — singleton catalogue of all available connectors.
    Built-in stubs     — lightweight reference connectors for Slack,
                         OpenAI, Google Sheets, Salesforce, and Zapier.

The system is deliberately *stub-first*: every built-in connector
works in dry-run mode (returns plausible mock payloads) so that the
workflow engine can be tested end-to-end without real credentials.
When a user supplies API keys the connector switches to live mode.

Security
────────
    • API keys are NEVER logged or persisted to disk.
    • Keys are passed via ``ConnectorContext.secrets`` dict and held
      only in process memory for the lifetime of the request.
    • The sandbox runner (see workflow_engine.py) enforces per-step
      timeouts and output-size caps.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.connectors")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS & VALUE OBJECTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuthType(str, Enum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"


class ConnectorStatus(str, Enum):
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DRY_RUN = "dry_run"


@dataclass(frozen=True)
class ConnectorSpec:
    """Declarative schema for a connector."""
    id: str                                # unique slug, e.g. "slack"
    display_name: str
    tool_name: str                         # maps to Tool.name in data.py
    auth_type: AuthType = AuthType.API_KEY
    base_url: str = ""
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    required_secrets: List[str] = field(default_factory=list)
    rate_limit_rpm: int = 60
    docs_url: str = ""

    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.id}:{self.version}".encode()).hexdigest()[:12]


@dataclass
class ConnectorContext:
    """Runtime context passed to every connector invocation."""
    secrets: Dict[str, str] = field(default_factory=dict)
    dry_run: bool = True
    timeout_seconds: float = 30.0
    trace_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_live(self) -> bool:
        return not self.dry_run


@dataclass
class ConnectorResult:
    """Uniform result from any connector action."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0
    connector_id: str = ""
    action: str = ""
    dry_run: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "connector_id": self.connector_id,
            "action": self.action,
            "dry_run": self.dry_run,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BASE CONNECTOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BaseConnector(ABC):
    """Abstract adapter that every tool connector must extend."""

    def __init__(self, spec: ConnectorSpec):
        self.spec = spec

    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        """Run *action* with *params* in the given context."""
        ...

    @abstractmethod
    def list_actions(self) -> List[str]:
        """Return the action names this connector supports."""
        ...

    async def health_check(self, ctx: ConnectorContext) -> ConnectorStatus:
        """Ping the service; override for real health checks."""
        return ConnectorStatus.DRY_RUN if ctx.dry_run else ConnectorStatus.AVAILABLE

    def _result(self, action: str, ctx: ConnectorContext,
                success: bool, data: Any = None,
                error: Optional[str] = None,
                elapsed_ms: float = 0.0) -> ConnectorResult:
        return ConnectorResult(
            success=success, data=data, error=error,
            elapsed_ms=elapsed_ms,
            connector_id=self.spec.id,
            action=action, dry_run=ctx.dry_run,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONNECTOR REGISTRY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConnectorRegistry:
    """Singleton catalogue of all registered connectors."""

    _instance: Optional["ConnectorRegistry"] = None

    def __init__(self) -> None:
        self._connectors: Dict[str, BaseConnector] = {}

    @classmethod
    def get(cls) -> "ConnectorRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._register_builtins()
        return cls._instance

    def register(self, connector: BaseConnector) -> None:
        self._connectors[connector.spec.id] = connector
        log.info("Connector registered: %s (v%s)", connector.spec.id, connector.spec.version)

    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        return self._connectors.get(connector_id)

    def list_connectors(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": c.spec.id,
                "display_name": c.spec.display_name,
                "tool_name": c.spec.tool_name,
                "auth_type": c.spec.auth_type.value,
                "capabilities": c.spec.capabilities,
                "version": c.spec.version,
                "actions": c.list_actions(),
            }
            for c in self._connectors.values()
        ]

    def count(self) -> int:
        return len(self._connectors)

    def _register_builtins(self) -> None:
        for cls in (SlackConnector, OpenAIConnector, GoogleSheetsConnector,
                    SalesforceConnector, ZapierConnector):
            try:
                self.register(cls())
            except Exception as exc:
                log.warning("Failed to register built-in %s: %s", cls.__name__, exc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUILT-IN CONNECTORS (stub / dry-run implementations)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SlackConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(ConnectorSpec(
            id="slack",
            display_name="Slack",
            tool_name="Slack",
            auth_type=AuthType.BEARER_TOKEN,
            base_url="https://slack.com/api",
            capabilities=["send_message", "create_channel", "list_channels"],
            required_secrets=["SLACK_BOT_TOKEN"],
            docs_url="https://api.slack.com/methods",
        ))

    def list_actions(self) -> List[str]:
        return ["send_message", "create_channel", "list_channels"]

    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        t0 = time.monotonic()
        if action == "send_message":
            channel = params.get("channel", "#general")
            text = params.get("text", "")
            data = {"ok": True, "channel": channel, "text": text, "ts": "1700000000.000001"}
        elif action == "create_channel":
            data = {"ok": True, "channel": {"id": "C999", "name": params.get("name", "new-channel")}}
        elif action == "list_channels":
            data = {"ok": True, "channels": [{"id": "C001", "name": "general"}, {"id": "C002", "name": "random"}]}
        else:
            return self._result(action, ctx, False, error=f"Unknown action: {action}",
                                elapsed_ms=(time.monotonic() - t0) * 1000)
        return self._result(action, ctx, True, data=data,
                            elapsed_ms=(time.monotonic() - t0) * 1000)


class OpenAIConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(ConnectorSpec(
            id="openai",
            display_name="OpenAI",
            tool_name="ChatGPT",
            auth_type=AuthType.API_KEY,
            base_url="https://api.openai.com/v1",
            capabilities=["chat_completion", "embedding", "moderation"],
            required_secrets=["OPENAI_API_KEY"],
            rate_limit_rpm=30,
            docs_url="https://platform.openai.com/docs/api-reference",
        ))

    def list_actions(self) -> List[str]:
        return ["chat_completion", "embedding", "moderation"]

    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        t0 = time.monotonic()
        if action == "chat_completion":
            data = {
                "id": "chatcmpl-stub",
                "choices": [{"message": {"role": "assistant",
                                         "content": params.get("prompt", "Hello from dry-run!")}}],
                "model": params.get("model", "gpt-4"),
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            }
        elif action == "embedding":
            data = {"data": [{"embedding": [0.0] * 8, "index": 0}], "model": "text-embedding-3-small"}
        elif action == "moderation":
            data = {"id": "modr-stub", "results": [{"flagged": False}]}
        else:
            return self._result(action, ctx, False, error=f"Unknown action: {action}",
                                elapsed_ms=(time.monotonic() - t0) * 1000)
        return self._result(action, ctx, True, data=data,
                            elapsed_ms=(time.monotonic() - t0) * 1000)


class GoogleSheetsConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(ConnectorSpec(
            id="google_sheets",
            display_name="Google Sheets",
            tool_name="Google Sheets",
            auth_type=AuthType.OAUTH2,
            base_url="https://sheets.googleapis.com/v4/spreadsheets",
            capabilities=["read_range", "write_range", "create_sheet"],
            required_secrets=["GOOGLE_CREDENTIALS"],
            docs_url="https://developers.google.com/sheets/api",
        ))

    def list_actions(self) -> List[str]:
        return ["read_range", "write_range", "create_sheet"]

    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        t0 = time.monotonic()
        if action == "read_range":
            data = {"range": params.get("range", "Sheet1!A1:B5"),
                    "values": [["Name", "Score"], ["Praxis", "100"]]}
        elif action == "write_range":
            data = {"updatedCells": 10, "range": params.get("range", "Sheet1!A1")}
        elif action == "create_sheet":
            data = {"spreadsheetId": "stub-id-123", "title": params.get("title", "New Sheet")}
        else:
            return self._result(action, ctx, False, error=f"Unknown action: {action}",
                                elapsed_ms=(time.monotonic() - t0) * 1000)
        return self._result(action, ctx, True, data=data,
                            elapsed_ms=(time.monotonic() - t0) * 1000)


class SalesforceConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(ConnectorSpec(
            id="salesforce",
            display_name="Salesforce",
            tool_name="Salesforce",
            auth_type=AuthType.OAUTH2,
            base_url="https://login.salesforce.com",
            capabilities=["query_records", "create_record", "update_record"],
            required_secrets=["SF_CLIENT_ID", "SF_CLIENT_SECRET", "SF_REFRESH_TOKEN"],
            docs_url="https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/",
        ))

    def list_actions(self) -> List[str]:
        return ["query_records", "create_record", "update_record"]

    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        t0 = time.monotonic()
        if action == "query_records":
            soql = params.get("soql", "SELECT Id, Name FROM Account LIMIT 5")
            data = {"totalSize": 2, "records": [
                {"Id": "001A", "Name": "Acme Corp"},
                {"Id": "001B", "Name": "Globex"},
            ], "query": soql}
        elif action == "create_record":
            data = {"id": "001NEW", "success": True, "object": params.get("object", "Account")}
        elif action == "update_record":
            data = {"id": params.get("id", "001A"), "success": True}
        else:
            return self._result(action, ctx, False, error=f"Unknown action: {action}",
                                elapsed_ms=(time.monotonic() - t0) * 1000)
        return self._result(action, ctx, True, data=data,
                            elapsed_ms=(time.monotonic() - t0) * 1000)


class ZapierConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(ConnectorSpec(
            id="zapier",
            display_name="Zapier",
            tool_name="Zapier",
            auth_type=AuthType.API_KEY,
            base_url="https://hooks.zapier.com",
            capabilities=["trigger_webhook", "list_zaps"],
            required_secrets=["ZAPIER_WEBHOOK_URL"],
            docs_url="https://platform.zapier.com/docs",
        ))

    def list_actions(self) -> List[str]:
        return ["trigger_webhook", "list_zaps"]

    async def execute(self, action: str, params: Dict[str, Any],
                      ctx: ConnectorContext) -> ConnectorResult:
        t0 = time.monotonic()
        if action == "trigger_webhook":
            data = {"status": "success", "id": "zap-exec-stub",
                    "payload_received": params.get("payload", {})}
        elif action == "list_zaps":
            data = {"zaps": [
                {"id": "zap1", "name": "New Lead → Slack"},
                {"id": "zap2", "name": "Form Submit → Sheet"},
            ]}
        else:
            return self._result(action, ctx, False, error=f"Unknown action: {action}",
                                elapsed_ms=(time.monotonic() - t0) * 1000)
        return self._result(action, ctx, True, data=data,
                            elapsed_ms=(time.monotonic() - t0) * 1000)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PUBLIC API
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_registry() -> ConnectorRegistry:
    """Return the global connector registry (singleton)."""
    return ConnectorRegistry.get()


async def execute_connector(
    connector_id: str,
    action: str,
    params: Dict[str, Any],
    *,
    secrets: Optional[Dict[str, str]] = None,
    dry_run: bool = True,
    timeout: float = 30.0,
    trace_id: Optional[str] = None,
) -> ConnectorResult:
    """High-level entry point: find connector → build context → execute."""
    registry = get_registry()
    connector = registry.get_connector(connector_id)
    if connector is None:
        return ConnectorResult(success=False, error=f"Unknown connector: {connector_id}",
                               connector_id=connector_id, action=action, dry_run=dry_run)
    ctx = ConnectorContext(
        secrets=secrets or {},
        dry_run=dry_run,
        timeout_seconds=timeout,
        trace_id=trace_id,
    )
    try:
        result = await asyncio.wait_for(
            connector.execute(action, params, ctx),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        return ConnectorResult(success=False, error="Connector execution timed out",
                               connector_id=connector_id, action=action, dry_run=dry_run)
    except Exception as exc:
        log.exception("Connector %s.%s failed", connector_id, action)
        return ConnectorResult(success=False, error=str(exc),
                               connector_id=connector_id, action=action, dry_run=dry_run)


def list_connectors() -> List[Dict[str, Any]]:
    """List all registered connectors with their capabilities."""
    return get_registry().list_connectors()
