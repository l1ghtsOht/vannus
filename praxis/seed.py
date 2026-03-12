# --------------- Seed Data Generator ---------------
"""
Bootstrap the feedback and learning loop with realistic seed data.

Run once to populate:
    - usage.json    (initial popularity scores based on market reality)
    - feedback.json (synthetic feedback entries to kickstart learning)

Safe to re-run — merges with existing data, won't duplicate.

Usage:
    python -m praxis.seed            # from project root
    python praxis/seed.py            # directly
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

_DIR = Path(__file__).parent


# ======================================================================
# Market-reality popularity seeds
# Top tools get high popularity; niche tools get modest scores.
# Based on public market share data and community signals.
# ======================================================================

_POPULARITY_SEEDS = {
    # Tier 1 — household names (pop 8-12)
    "ChatGPT": 12, "Canva AI": 10, "Zapier": 9, "Notion AI": 9,
    "GitHub Copilot": 11, "Figma AI": 8, "Grammarly": 9,
    "Slack": 10, "Google Analytics": 10, "HubSpot": 8,
    "Shopify": 9, "Salesforce Einstein": 8, "Stripe": 9,
    "Mailchimp": 7, "Airtable": 7, "Jira": 8,
    # Tier 2 — strong players (pop 5-7)
    "Claude": 7, "Midjourney": 7, "Jasper": 6, "Cursor": 7,
    "Vercel": 6, "Supabase": 6, "Postman": 6, "Linear": 5,
    "Asana": 6, "Monday.com": 6, "Trello": 5, "ClickUp": 5,
    "Intercom": 5, "Zendesk": 6, "Loom": 5, "Calendly": 5,
    "Semrush": 5, "Buffer": 5, "Hootsuite": 5, "Descript": 5,
    "Typeform": 5, "Tableau": 6, "Snowflake": 5,
    # Tier 3 — respected niche (pop 3-4)
    "Tabnine": 4, "Replit": 4, "Gemini": 4, "Perplexity": 5,
    "Runway ML": 4, "ElevenLabs": 4, "Synthesia": 3,
    "Otter.ai": 4, "Mixpanel": 4, "Amplitude": 4,
    "Sentry": 4, "Datadog": 4, "Segment": 3,
    "Miro": 4, "QuickBooks AI": 3, "Brex": 3,
    "Vanta": 3, "Greenhouse": 3, "Freshdesk": 3,
    "Drift": 3, "Tidio": 3,
    # Tier 4 — emerging / open source (pop 1-2)
    "Hugging Face": 5, "n8n": 3, "Retool": 3, "Bubble": 3,
    "LangChain": 4, "Pinecone": 3, "Weaviate": 2,
    "Cohere": 2, "Replicate": 2, "Stability AI": 3,
    "Make (Integromat)": 3, "Surfer SEO": 2, "Ahrefs": 4,
    "Hotjar": 3,
}


# ======================================================================
# Synthetic feedback seeds — realistic query/tool/rating combos
# ======================================================================

_FEEDBACK_SEEDS = [
    # Writing queries
    {"query": "write marketing copy for my startup", "tool": "ChatGPT", "rating": 9, "accepted": True},
    {"query": "write marketing copy for my startup", "tool": "Jasper", "rating": 8, "accepted": True},
    {"query": "blog content creation", "tool": "ChatGPT", "rating": 8, "accepted": True},
    {"query": "blog content creation", "tool": "Grammarly", "rating": 7, "accepted": True},
    {"query": "email newsletter tool", "tool": "Mailchimp", "rating": 8, "accepted": True},
    # Design queries
    {"query": "design social media graphics", "tool": "Canva AI", "rating": 9, "accepted": True},
    {"query": "design social media graphics", "tool": "Midjourney", "rating": 7, "accepted": True},
    {"query": "prototype mobile app UI", "tool": "Figma AI", "rating": 9, "accepted": True},
    # Coding queries
    {"query": "help me code faster", "tool": "GitHub Copilot", "rating": 9, "accepted": True},
    {"query": "help me code faster", "tool": "Cursor", "rating": 8, "accepted": True},
    {"query": "build a web app quickly", "tool": "Vercel", "rating": 7, "accepted": True},
    {"query": "build a web app quickly", "tool": "Supabase", "rating": 7, "accepted": True},
    # Automation / SMB queries
    {"query": "automate my small business workflows", "tool": "Zapier", "rating": 9, "accepted": True},
    {"query": "automate my small business workflows", "tool": "n8n", "rating": 7, "accepted": True},
    {"query": "automate my small business workflows", "tool": "Make (Integromat)", "rating": 6, "accepted": True},
    {"query": "CRM for small team", "tool": "HubSpot", "rating": 8, "accepted": True},
    {"query": "manage customer support tickets", "tool": "Zendesk", "rating": 7, "accepted": True},
    {"query": "manage customer support tickets", "tool": "Intercom", "rating": 7, "accepted": True},
    # Analytics
    {"query": "track website analytics", "tool": "Google Analytics", "rating": 8, "accepted": True},
    {"query": "product analytics for SaaS", "tool": "Mixpanel", "rating": 7, "accepted": True},
    {"query": "product analytics for SaaS", "tool": "Amplitude", "rating": 7, "accepted": True},
    # Negative feedback (rejected / low ratings)
    {"query": "simple design tool no learning curve", "tool": "Figma AI", "rating": 4, "accepted": False},
    {"query": "free AI for writing", "tool": "Jasper", "rating": 3, "accepted": False},
    {"query": "no-code app builder", "tool": "GitHub Copilot", "rating": 2, "accepted": False},
    # SMB / regional
    {"query": "best tool for restaurant marketing", "tool": "Canva AI", "rating": 8, "accepted": True},
    {"query": "best tool for restaurant marketing", "tool": "Mailchimp", "rating": 7, "accepted": True},
    {"query": "ecommerce analytics dashboard", "tool": "Shopify", "rating": 8, "accepted": True},
    {"query": "schedule social media posts cheaply", "tool": "Buffer", "rating": 7, "accepted": True},
    {"query": "AI for legal document review", "tool": "ChatGPT", "rating": 6, "accepted": True},
    {"query": "video editing AI", "tool": "Descript", "rating": 8, "accepted": True},
    {"query": "video editing AI", "tool": "Runway ML", "rating": 7, "accepted": True},
]


def seed_popularity(force: bool = False):
    """Write initial popularity scores to usage.json.

    Merges with existing data — existing scores are kept (max of seed vs current).
    """
    usage_path = _DIR / "usage.json"
    existing = {}
    if usage_path.exists():
        try:
            existing = json.loads(usage_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    for tool_name, pop in _POPULARITY_SEEDS.items():
        current = existing.get(tool_name, 0)
        existing[tool_name] = max(int(current), pop) if not force else pop

    usage_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"[seed] Wrote popularity for {len(existing)} tools → {usage_path}")
    return existing


def seed_feedback(force: bool = False):
    """Write synthetic feedback entries to feedback.json.

    If feedback.json already has data and force=False, appends only.
    Each seed entry gets a randomized timestamp over the past 30 days.
    """
    fb_path = _DIR / "feedback.json"
    existing = []
    if fb_path.exists() and not force:
        try:
            existing = json.loads(fb_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    # Check if seeds already exist (by matching query+tool pairs)
    existing_pairs = {(e.get("query"), e.get("tool")) for e in existing}

    now = datetime.now(tz=None)  # local time; entries get "Z" suffix for compat
    added = 0
    for seed in _FEEDBACK_SEEDS:
        pair = (seed["query"], seed["tool"])
        if pair in existing_pairs:
            continue
        # Random timestamp in the past 30 days
        offset = timedelta(days=random.randint(1, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        ts = (now - offset).isoformat() + "Z"
        entry = {
            "timestamp": ts,
            "query": seed["query"],
            "tool": seed["tool"],
            "accepted": seed["accepted"],
            "rating": seed["rating"],
            "details": {"source": "seed"},
        }
        existing.append(entry)
        existing_pairs.add(pair)
        added += 1

    # Sort by timestamp
    existing.sort(key=lambda e: e.get("timestamp", ""))

    fb_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"[seed] Added {added} feedback entries ({len(existing)} total) → {fb_path}")
    return existing


def seed_all(force: bool = False):
    """Run all seed operations, then trigger a learning cycle."""
    seed_popularity(force=force)
    seed_feedback(force=force)

    # Trigger learning cycle to compute signals from seed data
    try:
        from .learning import run_learning_cycle
    except Exception:
        from learning import run_learning_cycle

    signals = run_learning_cycle()
    print(f"[seed] Learning cycle complete. {len(signals.get('tool_quality', {}))} tools scored.")
    return signals


if __name__ == "__main__":
    seed_all()
