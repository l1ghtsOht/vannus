import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any


DB_NAME = "tools.db"


def db_path() -> Path:
    return Path(__file__).parent / DB_NAME


def init_db(path: Path = None):
    """Create the tools table if the DB doesn't exist yet.

    Schema v3 (May 2026) — adds Phase 3 sovereignty/privacy fields and
    Phase 4 trust-badge fields so the elimination engine and trust-
    dimension scoring receive the data the in-memory Tool objects
    actually carry. Previous v2 schema silently dropped these on
    round-trip, causing every tool to load with USA / is_us_controlled=True
    defaults regardless of source data.
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
                languages TEXT,
                last_updated TEXT,
                country_of_origin TEXT,
                is_us_controlled INTEGER,
                high_risk_backend INTEGER,
                zdr_compliant INTEGER,
                training_data_usage TEXT,
                base_model TEXT,
                data_jurisdiction TEXT,
                target_outcome_kpi TEXT,
                verified_roi_score REAL,
                outcome_metrics TEXT,
                uptime_tier INTEGER,
                psr_score REAL,
                oqs_score REAL,
                portability_score_val INTEGER
            )
            """
        )
        conn.commit()
        conn.close()
        created = True
    return p, created


def _bool_to_int(val):
    """Serialize a boolean (or None) for SQLite INTEGER storage."""
    if val is None:
        return None
    return 1 if val else 0


def _int_to_bool(val):
    """Deserialize SQLite INTEGER back to bool / None."""
    if val is None:
        return None
    return bool(val)


def insert_tool(conn: sqlite3.Connection, tool: Dict[str, Any]):
    conn.execute(
        "INSERT INTO tools (name, description, categories, url, popularity, tags, keywords, pricing, integrations, compliance, skill_level, use_cases, stack_roles, languages, last_updated, country_of_origin, is_us_controlled, high_risk_backend, zdr_compliant, training_data_usage, base_model, data_jurisdiction, target_outcome_kpi, verified_roi_score, outcome_metrics, uptime_tier, psr_score, oqs_score, portability_score_val) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            tool.get("last_updated"),
            tool.get("country_of_origin"),
            _bool_to_int(tool.get("is_us_controlled")),
            _bool_to_int(tool.get("high_risk_backend")),
            _bool_to_int(tool.get("zdr_compliant")),
            tool.get("training_data_usage"),
            tool.get("base_model"),
            tool.get("data_jurisdiction"),
            tool.get("target_outcome_kpi"),
            float(tool.get("verified_roi_score", 0) or 0) or None,
            json.dumps(tool.get("outcome_metrics", {})),
            int(tool.get("uptime_tier", 0) or 0) or None,
            float(tool.get("psr_score", 0) or 0) or None,
            float(tool.get("oqs_score", 0) or 0) or None,
            int(tool.get("portability_score_val", 0) or 0) or None,
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
                    "last_updated": getattr(t, "last_updated", None),
                    # Phase 3 — Sovereignty & Privacy
                    "country_of_origin": getattr(t, "country_of_origin", None),
                    "is_us_controlled": getattr(t, "is_us_controlled", None),
                    "high_risk_backend": getattr(t, "high_risk_backend", None),
                    "zdr_compliant": getattr(t, "zdr_compliant", None),
                    "training_data_usage": getattr(t, "training_data_usage", None),
                    "base_model": getattr(t, "base_model", None),
                    "data_jurisdiction": getattr(t, "data_jurisdiction", None),
                    # Phase 3 — Outcome Metrics
                    "target_outcome_kpi": getattr(t, "target_outcome_kpi", None),
                    "verified_roi_score": getattr(t, "verified_roi_score", None),
                    "outcome_metrics": getattr(t, "outcome_metrics", {}),
                    # Phase 4 — Trust Badges
                    "uptime_tier": getattr(t, "uptime_tier", None),
                    "psr_score": getattr(t, "psr_score", None),
                    "oqs_score": getattr(t, "oqs_score", None),
                    "portability_score_val": getattr(t, "portability_score_val", None),
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
        c.execute(
            "SELECT name, description, categories, url, popularity, tags, keywords, "
            "pricing, integrations, compliance, skill_level, use_cases, stack_roles, "
            "languages, last_updated, country_of_origin, is_us_controlled, "
            "high_risk_backend, zdr_compliant, training_data_usage, base_model, "
            "data_jurisdiction, target_outcome_kpi, verified_roi_score, outcome_metrics, "
            "uptime_tier, psr_score, oqs_score, portability_score_val "
            "FROM tools ORDER BY id ASC"
        )
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
         stack_roles, languages, last_updated, country_of_origin,
         is_us_controlled, high_risk_backend, zdr_compliant,
         training_data_usage, base_model, data_jurisdiction,
         target_outcome_kpi, verified_roi_score, outcome_metrics,
         uptime_tier, psr_score, oqs_score, portability_score_val) = r

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
                "last_updated": last_updated,
                # Phase 3 — Sovereignty & Privacy
                "country_of_origin": country_of_origin,
                "is_us_controlled": _int_to_bool(is_us_controlled),
                "high_risk_backend": _int_to_bool(high_risk_backend),
                "zdr_compliant": _int_to_bool(zdr_compliant),
                "training_data_usage": training_data_usage,
                "base_model": base_model,
                "data_jurisdiction": data_jurisdiction,
                # Phase 3 — Outcome Metrics
                "target_outcome_kpi": target_outcome_kpi,
                "verified_roi_score": verified_roi_score,
                "outcome_metrics": _parse_json(outcome_metrics, {}),
                # Phase 4 — Trust Badges
                "uptime_tier": uptime_tier,
                "psr_score": psr_score,
                "oqs_score": oqs_score,
                "portability_score_val": portability_score_val,
            }
        )
    return tools
