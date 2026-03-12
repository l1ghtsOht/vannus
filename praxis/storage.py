import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any


DB_NAME = "tools.db"


def db_path() -> Path:
    return Path(__file__).parent / DB_NAME


def init_db(path: Path = None):
    """Create the tools table if the DB doesn't exist yet.

    Schema v2 — includes pricing, integrations, compliance, skill_level,
    use_cases, stack_roles, and languages columns.
    """
    p = path or db_path()
    created = False
    if not p.exists():
        conn = sqlite3.connect(p)
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE tools (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                categories TEXT,
                url TEXT,
                popularity INTEGER,
                tags TEXT,
                keywords TEXT,
                pricing TEXT,
                integrations TEXT,
                compliance TEXT,
                skill_level TEXT,
                use_cases TEXT,
                stack_roles TEXT,
                languages TEXT
            )
            """
        )
        conn.commit()
        conn.close()
        created = True
    return p, created


def insert_tool(conn: sqlite3.Connection, tool: Dict[str, Any]):
    conn.execute(
        "INSERT INTO tools (name, description, categories, url, popularity, tags, keywords, pricing, integrations, compliance, skill_level, use_cases, stack_roles, languages) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            tool.get("name"),
            tool.get("description"),
            json.dumps(tool.get("categories", [])),
            tool.get("url"),
            int(tool.get("popularity", 0) or 0),
            json.dumps(tool.get("tags", [])),
            json.dumps(tool.get("keywords", [])),
            json.dumps(tool.get("pricing", {})),
            json.dumps(tool.get("integrations", [])),
            json.dumps(tool.get("compliance", [])),
            tool.get("skill_level", "beginner"),
            json.dumps(tool.get("use_cases", [])),
            json.dumps(tool.get("stack_roles", ["primary"])),
            json.dumps(tool.get("languages", [])),
        ),
    )


def migrate_tools(tools_list: List[Any], path: Path = None):
    p, created = init_db(path)
    conn = sqlite3.connect(p)
    # If created, insert provided tools
    if created:
        for t in tools_list:
            # support Tool objects or dicts
            if hasattr(t, "__dict__"):
                d = {
                    "name": getattr(t, "name", ""),
                    "description": getattr(t, "description", ""),
                    "categories": getattr(t, "categories", []),
                    "url": getattr(t, "url", None),
                    "popularity": getattr(t, "popularity", 0),
                    "tags": getattr(t, "tags", []),
                    "keywords": getattr(t, "keywords", []),
                    "pricing": getattr(t, "pricing", {}),
                    "integrations": getattr(t, "integrations", []),
                    "compliance": getattr(t, "compliance", []),
                    "skill_level": getattr(t, "skill_level", "beginner"),
                    "use_cases": getattr(t, "use_cases", []),
                    "stack_roles": getattr(t, "stack_roles", ["primary"]),
                    "languages": getattr(t, "languages", []),
                }
            elif isinstance(t, dict):
                d = t
            else:
                continue
            insert_tool(conn, d)
        conn.commit()
    conn.close()
    return p


def load_tools(path: Path = None) -> List[Dict[str, Any]]:
    p = path or db_path()
    if not p.exists():
        return []
    conn = sqlite3.connect(p)
    try:
        c = conn.cursor()
        c.execute("SELECT name, description, categories, url, popularity, tags, keywords, pricing, integrations, compliance, skill_level, use_cases, stack_roles, languages FROM tools ORDER BY id ASC")
        rows = c.fetchall()
    finally:
        conn.close()

    def _parse_json(val, default):
        if not val:
            return default
        try:
            return json.loads(val)
        except Exception:
            return default

    tools = []
    for r in rows:
        (name, description, categories, url, popularity, tags, keywords,
         pricing, integrations, compliance, skill_level, use_cases,
         stack_roles, languages) = r

        tools.append(
            {
                "name": name,
                "description": description,
                "categories": _parse_json(categories, []),
                "url": url,
                "popularity": int(popularity or 0),
                "tags": _parse_json(tags, []),
                "keywords": _parse_json(keywords, []),
                "pricing": _parse_json(pricing, {}),
                "integrations": _parse_json(integrations, []),
                "compliance": _parse_json(compliance, []),
                "skill_level": skill_level or "beginner",
                "use_cases": _parse_json(use_cases, []),
                "stack_roles": _parse_json(stack_roles, ["primary"]),
                "languages": _parse_json(languages, []),
            }
        )
    return tools
