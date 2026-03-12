# --------------- Tool Import / Export ---------------
"""
Ingest tools from external sources (CSV, JSON) and export
the current TOOLS list for backup or migration.

Supports:
    - CSV import  (one tool per row, list fields comma-separated in quotes)
    - JSON import (array of tool dicts matching Tool.to_dict() shape)
    - JSON export (dump current TOOLS to file or stdout)

All imports are additive — they merge into the existing TOOLS list,
skipping duplicates by name (case-insensitive).
"""

import csv
import json
import io
from pathlib import Path
from typing import List, Optional

try:
    from .tools import Tool
    from .data import TOOLS
except Exception:
    from tools import Tool
    from data import TOOLS

import logging
log = logging.getLogger("praxis.ingest")


# ======================================================================
# Export
# ======================================================================

def export_tools_json(path: Optional[str] = None) -> str:
    """Serialize all TOOLS to JSON.

    If *path* is given, writes to that file and returns the path.
    Otherwise returns the JSON string.
    """
    payload = [t.to_dict() for t in TOOLS]
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if path:
        Path(path).write_text(text, encoding="utf-8")
        log.info("Exported %d tools to %s", len(payload), path)
        return path
    return text


# ======================================================================
# JSON import
# ======================================================================

def import_tools_json(source: str) -> dict:
    """Import tools from a JSON file or JSON string.

    Args:
        source: file path or raw JSON string (auto-detected)

    Returns:
        {"added": int, "skipped": int, "errors": int, "names_added": list}
    """
    p = Path(source)
    if p.exists():
        raw = p.read_text(encoding="utf-8")
    else:
        raw = source  # treat as raw JSON

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error("JSON parse error: %s", e)
        return {"added": 0, "skipped": 0, "errors": 1, "names_added": []}

    if not isinstance(items, list):
        items = [items]

    return _merge_tools(items)


# ======================================================================
# CSV import
# ======================================================================

_CSV_FIELDS = [
    "name", "description", "categories", "url", "popularity",
    "tags", "keywords", "pricing", "integrations", "compliance",
    "skill_level", "use_cases", "stack_roles", "languages",
]

def import_tools_csv(source: str) -> dict:
    """Import tools from a CSV file or CSV string.

    Expected header row matches _CSV_FIELDS.  List fields should be
    semicolon-separated within their cell (e.g. ``design;marketing``).
    Pricing should be JSON or semicolon key=value pairs.

    Returns:
        {"added": int, "skipped": int, "errors": int, "names_added": list}
    """
    p = Path(source)
    if p.exists():
        raw = p.read_text(encoding="utf-8")
    else:
        raw = source

    reader = csv.DictReader(io.StringIO(raw))
    items = []
    errors = 0
    for row_num, row in enumerate(reader, start=2):
        try:
            d = _csv_row_to_dict(row)
            items.append(d)
        except Exception as e:
            log.warning("CSV row %d error: %s", row_num, e)
            errors += 1

    result = _merge_tools(items)
    result["errors"] += errors
    return result


def _csv_row_to_dict(row: dict) -> dict:
    """Convert a CSV row dict into a Tool-compatible dict."""
    def split_list(val):
        if not val:
            return []
        return [v.strip() for v in val.split(";") if v.strip()]

    def parse_pricing(val):
        if not val:
            return {}
        # Try JSON first
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            pass
        # Fall back to semicolon key=value
        pricing = {}
        for pair in val.split(";"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                k, v = k.strip(), v.strip()
                if v.lower() in ("true", "yes"):
                    pricing[k] = True
                elif v.lower() in ("false", "no"):
                    pricing[k] = False
                else:
                    try:
                        pricing[k] = int(v)
                    except ValueError:
                        pricing[k] = v
        return pricing

    return {
        "name": (row.get("name") or "").strip(),
        "description": (row.get("description") or "").strip(),
        "categories": split_list(row.get("categories")),
        "url": (row.get("url") or "").strip() or None,
        "popularity": int(row.get("popularity") or 0),
        "tags": split_list(row.get("tags")),
        "keywords": split_list(row.get("keywords")),
        "pricing": parse_pricing(row.get("pricing")),
        "integrations": split_list(row.get("integrations")),
        "compliance": split_list(row.get("compliance")),
        "skill_level": (row.get("skill_level") or "beginner").strip(),
        "use_cases": split_list(row.get("use_cases")),
        "stack_roles": split_list(row.get("stack_roles")) or ["primary"],
        "languages": split_list(row.get("languages")),
    }


# ======================================================================
# Merge logic
# ======================================================================

def _merge_tools(items: List[dict]) -> dict:
    """Merge a list of tool dicts into the runtime TOOLS list.

    Skips duplicates (by name, case-insensitive).
    """
    existing_names = {t.name.lower() for t in TOOLS}
    added = 0
    skipped = 0
    errors = 0
    names_added = []

    for item in items:
        name = item.get("name", "").strip()
        if not name:
            errors += 1
            continue
        if name.lower() in existing_names:
            skipped += 1
            continue
        try:
            tool = Tool.from_dict(item)
            TOOLS.append(tool)
            existing_names.add(name.lower())
            names_added.append(name)
            added += 1
        except Exception as e:
            log.warning("Failed to create Tool '%s': %s", name, e)
            errors += 1

    if added:
        log.info("Imported %d new tools: %s", added, ", ".join(names_added))

    return {"added": added, "skipped": skipped, "errors": errors, "names_added": names_added}


# ======================================================================
# CSV template generator
# ======================================================================

def generate_csv_template(path: Optional[str] = None) -> str:
    """Generate a CSV template with headers and 2 example rows.

    Returns the CSV text, optionally writes to *path*.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_CSV_FIELDS)
    writer.writeheader()
    writer.writerow({
        "name": "ExampleTool",
        "description": "AI tool for example tasks",
        "categories": "writing;marketing",
        "url": "https://example.com",
        "popularity": "0",
        "tags": "ai;assistant",
        "keywords": "blog writing;email campaigns",
        "pricing": "free_tier=true;starter=10;pro=29",
        "integrations": "Zapier;Slack",
        "compliance": "SOC2;GDPR",
        "skill_level": "beginner",
        "use_cases": "blog posts;social media copy",
        "stack_roles": "primary;companion",
        "languages": "no-code",
    })
    text = buf.getvalue()
    if path:
        Path(path).write_text(text, encoding="utf-8")
    return text
