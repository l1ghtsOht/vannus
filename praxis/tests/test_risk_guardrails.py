from praxis.api import _repair_mojibake_text, _sanitize_openapi_payload
from praxis.data import TOOLS


def test_repair_mojibake_text_replaces_known_sequences():
    raw = "Praxis â€” endpoint â†’ score â‰¥ 0 and Î¦/Î¨/Î”"
    fixed = _repair_mojibake_text(raw)
    assert "â€”" not in fixed
    assert "â†’" not in fixed
    assert "â‰¥" not in fixed
    assert "Î¦" not in fixed
    assert "Î¨" not in fixed
    assert "Î”" not in fixed
    assert "—" in fixed
    assert "→" in fixed
    assert "≥" in fixed
    assert "Φ" in fixed
    assert "Ψ" in fixed
    assert "Δ" in fixed


def test_sanitize_openapi_payload_recurses_nested_values():
    payload = {
        "summary": "API â€” Search",
        "paths": [
            {"description": "Analyzerâ†’Selectorâ†’Adder"},
            "Integrated Information Î¦",
        ],
    }
    sanitized = _sanitize_openapi_payload(payload)
    assert sanitized["summary"] == "API — Search"
    assert sanitized["paths"][0]["description"] == "Analyzer→Selector→Adder"
    assert sanitized["paths"][1] == "Integrated Information Φ"


def test_reserved_acronyms_are_consistently_cased_in_tool_metadata():
    lowercase_api_tag = []
    lowercase_rag_token = []

    for tool in TOOLS:
        if any(tag == "api" for tag in tool.tags):
            lowercase_api_tag.append(tool.name)
        if any(keyword == "rag" for keyword in tool.keywords):
            lowercase_rag_token.append(tool.name)

    assert not lowercase_api_tag, f"Lowercase 'api' tag found in: {lowercase_api_tag}"
    assert not lowercase_rag_token, f"Lowercase 'rag' keyword found in: {lowercase_rag_token}"
