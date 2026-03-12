import json
import os

USAGE_FILE = "usage.json"


def _load_usage():
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_usage(data):
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get(tool_name: str) -> int:
    data = _load_usage()
    return int(data.get(tool_name, 0))


def increment(tool_name: str, delta: int = 1) -> int:
    data = _load_usage()
    current = int(data.get(tool_name, 0))
    current += int(delta)
    data[tool_name] = current
    _save_usage(data)
    return current


def apply_to_tools(tools_list: list):
    """Apply stored popularity values to Tool objects in-place."""
    data = _load_usage()
    for t in tools_list:
        try:
            t.popularity = int(data.get(t.name, 0))
        except Exception:
            t.popularity = 0
