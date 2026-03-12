# --------------- Integration Playground ---------------
"""
"Test if Tool A integrates with Tool B" — simple simulator using
integration metadata + user reports.

Reduces stack anxiety by answering:
    • Do these tools integrate natively?
    • What's the integration method? (API, Zapier, webhook, manual)
    • Which tools in my stack don't talk to each other?
    • What's the best bridge tool for non-native integrations?
"""

import logging
from typing import Optional, List

log = logging.getLogger("praxis.playground")

try:
    from .tools import Tool
    from .data import TOOLS
except Exception:
    from tools import Tool
    from data import TOOLS


# ======================================================================
# Integration knowledge base
# ======================================================================

# Known integration methods between tool pairs (curated)
_INTEGRATION_METHODS = {
    ("zapier", "hubspot ai"):      "native",
    ("zapier", "slack"):           "native",
    ("zapier", "notion ai"):       "native",
    ("zapier", "mailchimp ai"):    "native",
    ("zapier", "google sheets"):   "native",
    ("zapier", "salesforce ai"):   "native",
    ("make", "hubspot ai"):        "native",
    ("make", "notion ai"):         "native",
    ("make", "slack"):             "native",
    ("slack", "notion ai"):        "native",
    ("slack", "hubspot ai"):       "native",
    ("github copilot", "cursor"):  "shared_ecosystem",
    ("chatgpt", "zapier"):         "api",
    ("canva ai", "hubspot ai"):    "native",
    ("semrush", "hubspot ai"):     "native",
    ("intercom ai", "slack"):      "native",
    ("segment", "hubspot ai"):     "native",
    ("segment", "mixpanel"):       "native",
}


def test_integration(tool_a_name: str, tool_b_name: str) -> dict:
    """Test if two tools integrate.

    Returns:
        {
            "tool_a": str,
            "tool_b": str,
            "integrates": bool,
            "method": "native" | "api" | "zapier_bridge" | "manual" | "unknown",
            "confidence": "high" | "medium" | "low",
            "notes": str,
            "bridge_suggestions": [...]
        }
    """
    tool_a = _find_tool(tool_a_name)
    tool_b = _find_tool(tool_b_name)

    if not tool_a:
        return {"error": f"Tool '{tool_a_name}' not found"}
    if not tool_b:
        return {"error": f"Tool '{tool_b_name}' not found"}

    # Check direct integration metadata
    a_integrates_b = tool_a.integrates_with(tool_b.name)
    b_integrates_a = tool_b.integrates_with(tool_a.name)
    direct = a_integrates_b or b_integrates_a

    # Check curated method
    pair = tuple(sorted([tool_a.name.lower(), tool_b.name.lower()]))
    method = _INTEGRATION_METHODS.get(pair)

    if direct and method:
        return {
            "tool_a": tool_a.name,
            "tool_b": tool_b.name,
            "integrates": True,
            "method": method,
            "confidence": "high",
            "notes": f"Native {method} integration verified between {tool_a.name} and {tool_b.name}",
            "bridge_suggestions": [],
        }
    elif direct:
        return {
            "tool_a": tool_a.name,
            "tool_b": tool_b.name,
            "integrates": True,
            "method": "native",
            "confidence": "medium",
            "notes": f"{tool_a.name} lists {tool_b.name} as an integration (or vice versa)",
            "bridge_suggestions": [],
        }

    # Check if a bridge tool connects them
    bridges = _find_bridges(tool_a, tool_b)

    if bridges:
        return {
            "tool_a": tool_a.name,
            "tool_b": tool_b.name,
            "integrates": False,
            "method": "bridge",
            "confidence": "medium",
            "notes": f"No direct integration, but can be connected via {bridges[0]['bridge']}",
            "bridge_suggestions": bridges,
        }

    # No integration found
    return {
        "tool_a": tool_a.name,
        "tool_b": tool_b.name,
        "integrates": False,
        "method": "manual",
        "confidence": "low",
        "notes": f"No known integration path between {tool_a.name} and {tool_b.name}. "
                 f"Manual export/import or custom API work may be required.",
        "bridge_suggestions": _suggest_generic_bridges(),
    }


def stack_integration_map(tool_names: List[str]) -> dict:
    """Map all integration paths within a stack of tools.

    Returns:
        {
            "tools": [...],
            "connections": [{"from": "A", "to": "B", "method": "native", ...}, ...],
            "disconnected_pairs": [...],
            "integration_score": int (0-100),
            "bridge_recommendations": [...]
        }
    """
    tools = [_find_tool(n) for n in tool_names]
    tools = [t for t in tools if t is not None]

    if len(tools) < 2:
        return {"error": "Need at least 2 valid tools to map integrations"}

    connections = []
    disconnected = []
    total_pairs = 0

    for i, a in enumerate(tools):
        for b in tools[i + 1:]:
            total_pairs += 1
            result = test_integration(a.name, b.name)
            if result.get("integrates"):
                connections.append({
                    "from": a.name,
                    "to": b.name,
                    "method": result["method"],
                    "confidence": result["confidence"],
                })
            elif result.get("bridge_suggestions"):
                connections.append({
                    "from": a.name,
                    "to": b.name,
                    "method": "bridge",
                    "bridge": result["bridge_suggestions"][0]["bridge"],
                    "confidence": "medium",
                })
            else:
                disconnected.append({
                    "from": a.name,
                    "to": b.name,
                })

    # Integration density score
    connected = len(connections)
    score = int((connected / max(total_pairs, 1)) * 100)

    # Bridge recommendations for disconnected pairs
    bridges = []
    if disconnected:
        bridge_tools = {"Zapier", "Make"}
        for bt_name in bridge_tools:
            bt = _find_tool(bt_name)
            if bt:
                bridges.append({
                    "tool": bt.name,
                    "can_bridge": len([
                        d for d in disconnected
                        if (bt.integrates_with(d["from"]) or bt.integrates_with(d["to"]))
                    ]),
                    "description": bt.description[:80] if bt.description else "",
                })

    return {
        "tools": [t.name for t in tools],
        "connections": connections,
        "disconnected_pairs": disconnected,
        "integration_score": score,
        "bridge_recommendations": bridges,
    }


# ======================================================================
# Helpers
# ======================================================================

def _find_tool(name: str) -> Optional[Tool]:
    for t in TOOLS:
        if t.name.lower() == name.lower():
            return t
    return None


def _find_bridges(tool_a: Tool, tool_b: Tool) -> list:
    """Find tools that integrate with both tool_a and tool_b."""
    bridges = []
    bridge_candidates = ["Zapier", "Make", "n8n", "Workato"]

    for bc_name in bridge_candidates:
        bc = _find_tool(bc_name)
        if not bc:
            continue
        connects_a = bc.integrates_with(tool_a.name) or tool_a.integrates_with(bc.name)
        connects_b = bc.integrates_with(tool_b.name) or tool_b.integrates_with(bc.name)
        if connects_a and connects_b:
            bridges.append({
                "bridge": bc.name,
                "method": "automation_platform",
                "notes": f"Use {bc.name} to connect {tool_a.name} ↔ {tool_b.name}",
            })
    # Also check all tools in DB as potential bridges
    if not bridges:
        for t in TOOLS:
            if t.name in (tool_a.name, tool_b.name):
                continue
            connects_a = t.integrates_with(tool_a.name) or tool_a.integrates_with(t.name)
            connects_b = t.integrates_with(tool_b.name) or tool_b.integrates_with(t.name)
            if connects_a and connects_b:
                bridges.append({
                    "bridge": t.name,
                    "method": "shared_integration",
                    "notes": f"{t.name} connects to both {tool_a.name} and {tool_b.name}",
                })
                if len(bridges) >= 3:
                    break
    return bridges


def _suggest_generic_bridges() -> list:
    """Fallback bridge suggestions."""
    return [
        {"bridge": "Zapier", "method": "automation_platform",
         "notes": "Most popular integration platform — connects 5000+ apps"},
        {"bridge": "Make (Integromat)", "method": "automation_platform",
         "notes": "Visual automation builder with broad app support"},
    ]
