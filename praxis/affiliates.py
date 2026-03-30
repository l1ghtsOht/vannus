# ────────────────────────────────────────────────────────────────────
# affiliates.py — Partner link registry (presentation layer only)
# ────────────────────────────────────────────────────────────────────
"""
Maps tool names to affiliate URLs. This module is NEVER imported by
the scoring engine — it exists solely for the API response layer to
annotate results with partner links after scoring is complete.

Adding a tool here does NOT affect its score, ranking, or inclusion.
"""

# tool_name → { url, label, disclosure }
PARTNERS = {
    "Semrush": {
        "url": "https://semrush.sjv.io/c/7066929/3838504/13053",
        "label": "Try Semrush free for 7 days",
        "disclosure": "Partner link — Praxis earns a commission on signups",
    },
}


def get_affiliate(tool_name: str) -> dict | None:
    """Return affiliate data for a tool, or None if no partnership exists."""
    return PARTNERS.get(tool_name)


def annotate_results(tools: list) -> list:
    """Add affiliate field to tool dicts that have partnerships.

    Accepts a list of dicts (API response format). Returns the same
    list with an 'affiliate' key added where applicable.
    """
    for tool in tools:
        name = tool.get("name") or ""
        partner = PARTNERS.get(name)
        if partner:
            tool["affiliate"] = partner
    return tools
