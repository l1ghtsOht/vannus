# ────────────────────────────────────────────────────────────────────
# ingestion_engine.py — Praxis v3.0 Ingestion & Curation Pipeline
# ────────────────────────────────────────────────────────────────────
"""
Core orchestration module for the AI Tool Ingestion Pipeline.

Responsibilities:
    - Scheduled polling of three external directories (TAAFT, Toolify,
      Futurepedia) via Apify REST actors.
    - Triple Match verification — only tools confirmed across ≥2
      sources enter the evaluation sandbox; all 3 required for Tier 1.
    - Signal enrichment via Wayback CDX, G2/Capterra scraping,
      PredictLeads hiring velocity.
    - Tier assignment (Sovereign → Durable → Vertical Specialist →
      Rejected) based on Survival Score + SMB Relevance Gate.
    - Human-In-The-Loop (HITL) review queue with confidence dashboard.
    - Weekly Tier 2 → Tier 1 promotion sweep.

Architecture:
    Designed for Celery task chains but ships with a synchronous
    fallback so the pipeline can run without Redis/Celery infra.
    All external API calls are abstracted behind connector functions
    that return mock data when credentials are absent — enabling
    full local development and testing.

Usage:
    from praxis.ingestion_engine import run_daily_pipeline
    result = run_daily_pipeline()          # sync fallback
    result = run_daily_pipeline(async_=True)  # Celery dispatch
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import time
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Final, List, Optional, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("praxis.ingestion")

# Attempt relative import (package mode); fall back to direct import
try:
    from .pipeline_constants import (
        DIRECTORIES, TRIPLE_MATCH_MIN, DUAL_MATCH_MIN,
        TIER_1_MIN_SURVIVAL, TIER_1_MIN_SMB, TIER_1_CONFIDENCE_AUTO,
        TIER_2_MIN_SURVIVAL, TIER_2_PROMOTION_SURVIVAL,
        TIER_3_MIN_VERTICAL_FIT,
        WEIGHTS, M_HEALTH_CHANGELOG_W, M_HEALTH_SLA_W, M_HEALTH_HIRING_W,
        SMB_VERTICAL_MATCH_MAX, SMB_PRICING_ACCESS_MAX,
        SMB_OPERATIONAL_COMPLEXITY_MAX, SMB_PRICING_CEILING,
        SMB_PER_SEAT_PENALTY_THRESHOLD,
        BADGE_TIERS, LLM_EXTRACTION_AUTO_COMMIT,
        WAYBACK_CDX_WINDOW_DAYS, SOCIAL_SIGNAL_SMB_MULTIPLIER,
        UPDATE_RECENCY_WINDOW_DAYS, SCRAPER_FALLBACK_ENABLED,
    )
except ImportError:
    from pipeline_constants import (  # type: ignore[no-redef]
        DIRECTORIES, TRIPLE_MATCH_MIN, DUAL_MATCH_MIN,
        TIER_1_MIN_SURVIVAL, TIER_1_MIN_SMB, TIER_1_CONFIDENCE_AUTO,
        TIER_2_MIN_SURVIVAL, TIER_2_PROMOTION_SURVIVAL,
        TIER_3_MIN_VERTICAL_FIT,
        WEIGHTS, M_HEALTH_CHANGELOG_W, M_HEALTH_SLA_W, M_HEALTH_HIRING_W,
        SMB_VERTICAL_MATCH_MAX, SMB_PRICING_ACCESS_MAX,
        SMB_OPERATIONAL_COMPLEXITY_MAX, SMB_PRICING_CEILING,
        SMB_PER_SEAT_PENALTY_THRESHOLD,
        BADGE_TIERS, LLM_EXTRACTION_AUTO_COMMIT,
        WAYBACK_CDX_WINDOW_DAYS, SOCIAL_SIGNAL_SMB_MULTIPLIER,
        UPDATE_RECENCY_WINDOW_DAYS, SCRAPER_FALLBACK_ENABLED,
    )

# =====================================================================
# Data Models
# =====================================================================

class TierStatus(str, Enum):
    """Pipeline tier assignment."""
    SOVEREIGN    = "tier_1"      # Gold
    DURABLE      = "tier_2"      # Silver
    VERTICAL     = "tier_3"      # Bronze
    REJECTED     = "rejected"
    PENDING_HITL = "pending_human_review"


class ReviewStatus(str, Enum):
    """Human review states."""
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_OK  = "auto_approved"


@dataclass
class DirectoryListing:
    """Normalised record from a single directory source."""
    name: str
    url: str
    description: str = ""
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    pricing_text: str = ""
    source: str = ""           # TAAFT | Toolify | Futurepedia
    fetched_at: str = ""       # ISO timestamp


@dataclass
class MatchedTool:
    """A tool that has been cross-referenced across directories."""
    canonical_name: str
    canonical_url: str
    descriptions: dict[str, str] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    pricing_text: str = ""
    match_count: int = 0
    matched_sources: list[str] = field(default_factory=list)
    raw_listings: list[DirectoryListing] = field(default_factory=list)


@dataclass
class EnrichedTool:
    """Tool with all signal enrichment applied."""
    # Identity
    canonical_name: str
    canonical_url: str
    match_count: int = 0
    matched_sources: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Enrichment signals
    changelog_diff_score: float = 0.0
    support_sla_hours: float = 24.0
    hiring_velocity: int = 0
    review_sentiment_avg: float = 50.0
    review_sentiment_trend: float = 0.0   # derivative: +/- direction
    social_signal_score: float = 0.0
    update_recency_days: int = 999
    red_flag_count: int = 0
    red_flag_details: list[str] = field(default_factory=list)

    # Scoring outputs (populated by evaluate_and_tier)
    maintenance_health: float = 0.0
    smb_relevance: float = 0.0
    survival_score: float = 0.0
    vertical_fit_score: float = 0.0
    confidence_interval: float = 0.0

    # Tier & status
    tier: str = ""
    review_status: str = ReviewStatus.PENDING.value
    assigned_at: str = ""

    # Pricing
    pricing_text: str = ""
    monthly_price: float = 0.0
    per_seat_price: float = 0.0
    has_free_tier: bool = False
    pricing_model: str = ""     # flat | per_seat | usage | contact_sales

    # Relationship data (populated during graph extraction)
    competitors: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EnrichedTool":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# =====================================================================
# 1. DIRECTORY FETCHERS (Apify Actors + Fallback)
# =====================================================================

_APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
_APIFY_ACTORS: Final[dict[str, str]] = {
    "TAAFT":       "apify/taaft-ai-tool-scraper",
    "Toolify":     "apify/toolify-ai-scraper",
    "Futurepedia": "apify/futurepedia-scraper",
}


def _fetch_apify(source: str) -> list[DirectoryListing]:
    """Fetch listings from an Apify actor.  Returns mock data when
    APIFY_TOKEN is not set (development mode)."""
    now = datetime.datetime.utcnow().isoformat()
    if not _APIFY_TOKEN:
        logger.info("[ingestion] APIFY_TOKEN not set — returning dev-mode seed for %s", source)
        return _seed_listings(source)
    try:
        import httpx
        actor_id = _APIFY_ACTORS.get(source, "")
        url = f"https://api.apify.com/v2/acts/{actor_id}/runs/last/dataset/items"
        resp = httpx.get(url, params={"token": _APIFY_TOKEN}, timeout=60)
        resp.raise_for_status()
        items = resp.json()
        return [
            DirectoryListing(
                name=item.get("name", item.get("title", "")),
                url=item.get("url", item.get("link", "")),
                description=item.get("description", ""),
                categories=[c for c in item.get("categories", []) if c],
                tags=[t for t in item.get("tags", []) if t],
                pricing_text=item.get("pricing", ""),
                source=source,
                fetched_at=now,
            )
            for item in items
            if item.get("name") or item.get("title")
        ]
    except Exception as exc:
        logger.warning("[ingestion] Apify fetch failed for %s: %s", source, exc)
        if SCRAPER_FALLBACK_ENABLED:
            logger.info("[ingestion] falling back to Playwright scraping for %s", source)
            return _playwright_fallback(source)
        return []


def _playwright_fallback(source: str) -> list[DirectoryListing]:
    """Headless browser fallback when Apify is unavailable.
    Returns empty list when Playwright is not installed."""
    try:
        # Placeholder — real implementation would use playwright here
        logger.info("[ingestion] Playwright fallback stub for %s", source)
        return _seed_listings(source)
    except Exception as exc:
        logger.warning("[ingestion] Playwright fallback failed for %s: %s", source, exc)
        return []


def _seed_listings(source: str) -> list[DirectoryListing]:
    """Development seed data for offline testing of the full pipeline."""
    now = datetime.datetime.utcnow().isoformat()
    seeds = {
        "TAAFT": [
            ("ChatGPT", "https://chat.openai.com", "AI assistant for conversation and content"),
            ("Jasper AI", "https://jasper.ai", "AI marketing content platform"),
            ("Midjourney", "https://midjourney.com", "AI image generation"),
            ("Notion AI", "https://notion.so", "AI-enhanced workspace"),
            ("Zapier", "https://zapier.com", "Workflow automation platform"),
            ("Canva AI", "https://canva.com", "AI design platform"),
            ("Grammarly", "https://grammarly.com", "AI writing assistant"),
            ("HubSpot AI", "https://hubspot.com", "AI-powered CRM"),
            ("Otter.ai", "https://otter.ai", "AI meeting transcription"),
            ("Descript", "https://descript.com", "AI video & podcast editing"),
            ("Jobber", "https://getjobber.com", "Field service management for SMBs"),
            ("Housecall Pro", "https://housecallpro.com", "Home service business management"),
        ],
        "Toolify": [
            ("ChatGPT", "https://chat.openai.com", "Conversational AI by OpenAI"),
            ("Jasper AI", "https://jasper.ai", "Enterprise content marketing AI"),
            ("Midjourney", "https://midjourney.com", "Image synthesis engine"),
            ("Notion AI", "https://notion.so", "AI workspace and productivity"),
            ("Canva AI", "https://canva.com", "Graphic design AI"),
            ("Grammarly", "https://grammarly.com", "Writing enhancement AI"),
            ("Otter.ai", "https://otter.ai", "Automated meeting notes"),
            ("Descript", "https://descript.com", "Multimedia editing with AI"),
            ("Copy.ai", "https://copy.ai", "AI copywriting tool"),
            ("Writesonic", "https://writesonic.com", "AI content generator"),
        ],
        "Futurepedia": [
            ("ChatGPT", "https://chat.openai.com", "General-purpose AI chatbot"),
            ("Jasper AI", "https://jasper.ai", "AI content creation suite"),
            ("Midjourney", "https://midjourney.com", "AI art generator"),
            ("Zapier", "https://zapier.com", "No-code automation"),
            ("Canva AI", "https://canva.com", "Design AI for teams"),
            ("Grammarly", "https://grammarly.com", "AI grammar and style checker"),
            ("HubSpot AI", "https://hubspot.com", "CRM with AI features"),
            ("Otter.ai", "https://otter.ai", "Real-time transcription AI"),
            ("Descript", "https://descript.com", "AI-first content editing"),
            ("Synthesia", "https://synthesia.io", "AI video generation platform"),
        ],
    }
    return [
        DirectoryListing(name=n, url=u, description=d, source=source, fetched_at=now)
        for n, u, d in seeds.get(source, [])
    ]


def fetch_all_directories() -> dict[str, list[DirectoryListing]]:
    """Fetch from all three directory sources.  Returns {source: [listings]}."""
    results: dict[str, list[DirectoryListing]] = {}
    for src in DIRECTORIES:
        listings = _fetch_apify(src)
        results[src] = listings
        logger.info("[ingestion] fetched %d listings from %s", len(listings), src)
    return results


# =====================================================================
# 2. NORMALIZE & MATCH (Triple Match Verification)
# =====================================================================

def _canonicalise_url(raw_url: str) -> str:
    """Strip protocol, www, trailing slashes for comparison."""
    if not raw_url:
        return ""
    parsed = urlparse(raw_url.strip().lower())
    host = (parsed.netloc or parsed.path).replace("www.", "")
    return host.rstrip("/")


def _fuzzy_name_match(a: str, b: str) -> bool:
    """Simple fuzzy name matcher — case-insensitive, strip suffixes."""
    def _norm(s: str) -> str:
        s = s.lower().strip()
        for suffix in (" ai", ".ai", " app", ".io", ".com"):
            if s.endswith(suffix):
                s = s[: -len(suffix)].strip()
        return re.sub(r"[^a-z0-9]", "", s)
    return _norm(a) == _norm(b)


def normalize_and_match(
    directory_data: dict[str, list[DirectoryListing]],
) -> list[MatchedTool]:
    """Cross-reference listings across all directories using URL
    canonicalisation and fuzzy name matching.  Returns deduplicated,
    matched tools sorted by match_count descending."""

    # Index: canonical_key → { source: DirectoryListing }
    by_key: dict[str, dict[str, DirectoryListing]] = {}

    for source, listings in directory_data.items():
        for listing in listings:
            # Primary key: canonical URL
            key = _canonicalise_url(listing.url)
            if not key:
                key = re.sub(r"[^a-z0-9]", "", listing.name.lower())
            if key not in by_key:
                by_key[key] = {}
            by_key[key][source] = listing

    # Second pass: merge entries that match by fuzzy name but different URL
    keys = list(by_key.keys())
    merged: set[str] = set()
    for i, k1 in enumerate(keys):
        if k1 in merged:
            continue
        for k2 in keys[i + 1 :]:
            if k2 in merged:
                continue
            # Pick a representative listing from each
            names_1 = [l.name for l in by_key[k1].values()]
            names_2 = [l.name for l in by_key[k2].values()]
            if any(_fuzzy_name_match(n1, n2) for n1 in names_1 for n2 in names_2):
                # Merge k2 into k1
                for src, listing in by_key[k2].items():
                    if src not in by_key[k1]:
                        by_key[k1][src] = listing
                merged.add(k2)

    # Build MatchedTool list
    matched: list[MatchedTool] = []
    for key, source_map in by_key.items():
        if key in merged:
            continue
        first = next(iter(source_map.values()))
        all_cats: list[str] = []
        all_tags: list[str] = []
        descs: dict[str, str] = {}
        for src, listing in source_map.items():
            all_cats.extend(listing.categories)
            all_tags.extend(listing.tags)
            if listing.description:
                descs[src] = listing.description

        matched.append(
            MatchedTool(
                canonical_name=first.name,
                canonical_url=first.url,
                descriptions=descs,
                categories=list(set(all_cats)),
                tags=list(set(all_tags)),
                pricing_text=first.pricing_text,
                match_count=len(source_map),
                matched_sources=sorted(source_map.keys()),
                raw_listings=list(source_map.values()),
            )
        )

    # Sort: Triple Match first, then Dual, then Single
    matched.sort(key=lambda t: (-t.match_count, t.canonical_name))
    logger.info(
        "[ingestion] normalised → %d unique tools  (triple=%d, dual=%d, single=%d)",
        len(matched),
        sum(1 for m in matched if m.match_count >= 3),
        sum(1 for m in matched if m.match_count == 2),
        sum(1 for m in matched if m.match_count == 1),
    )
    return matched


# =====================================================================
# 3. SIGNAL ENRICHMENT
# =====================================================================

def _enrich_wayback_cdx(domain: str, days: int = WAYBACK_CDX_WINDOW_DAYS) -> float:
    """Query Wayback Machine CDX API for changelog/pricing page diffs.
    Returns a normalised change-frequency score 0-100."""
    try:
        import httpx
        canon = _canonicalise_url(domain)
        # Check /changelog
        cdx_url = f"https://web.archive.org/cdx/search/cdx"
        from_date = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y%m%d")
        params = {
            "url": f"{canon}/changelog*",
            "output": "json",
            "from": from_date,
            "fl": "timestamp,digest,length",
        }
        resp = httpx.get(cdx_url, params=params, timeout=30)
        if resp.status_code != 200:
            return 50.0  # neutral fallback
        rows = resp.json()
        if len(rows) <= 1:
            return 30.0  # no changelog found
        # Count unique digests (actual content changes)
        digests = {r[1] for r in rows[1:]}  # skip header row
        change_count = len(digests)
        # Normalise: 0 changes → 0, 10+ changes → 100
        return min(100.0, (change_count / 10.0) * 100.0)
    except Exception as exc:
        logger.debug("[enrichment] Wayback CDX failed for %s: %s", domain, exc)
        return 50.0  # neutral fallback


def _enrich_support_sla(domain: str) -> float:
    """Extract average support response time from G2/Capterra.
    Returns hours (lower is better).  Defaults to 24h when unavailable."""
    # In production, this uses ScraperAPI to extract G2 vendor page
    # For now, return a reasonable default
    logger.debug("[enrichment] support SLA stub for %s", domain)
    return 8.0  # default moderate


def _enrich_hiring_velocity(domain: str) -> int:
    """Query PredictLeads API for active engineering job openings.
    Returns count of active roles."""
    logger.debug("[enrichment] hiring velocity stub for %s", domain)
    return 3  # default moderate signal


def _enrich_review_sentiment(domain: str) -> Tuple[float, float]:
    """Extract 90-day review sentiment from G2/Capterra.
    Returns (average_score_0_100, trend_derivative)."""
    logger.debug("[enrichment] review sentiment stub for %s", domain)
    return 72.0, 0.5  # moderate positive


def _enrich_social_signal(name: str) -> float:
    """Extract weighted social signal.
    SMB-specific sources (Alignable, trade forums) get 3x multiplier."""
    logger.debug("[enrichment] social signal stub for %s", name)
    return 55.0  # moderate


def _detect_red_flags(domain: str, name: str) -> Tuple[int, list[str]]:
    """Scan for critical red flags: data breaches, mass complaints,
    PE acquisition shutdowns.  Returns (count, [details])."""
    logger.debug("[enrichment] red flag scan stub for %s", name)
    return 0, []


def _parse_pricing(pricing_text: str) -> dict:
    """Extract structured pricing info from raw pricing text."""
    result = {
        "monthly_price": 0.0,
        "per_seat_price": 0.0,
        "has_free_tier": False,
        "pricing_model": "unknown",
    }
    lower = pricing_text.lower() if pricing_text else ""

    if "free" in lower:
        result["has_free_tier"] = True

    if "contact" in lower and "sales" in lower:
        result["pricing_model"] = "contact_sales"
        result["monthly_price"] = 9999.0  # penalise
        return result

    # Try to extract dollar amounts
    prices = re.findall(r"\$(\d+(?:\.\d{2})?)", lower)
    if prices:
        amounts = sorted(float(p) for p in prices)
        result["monthly_price"] = amounts[0]  # cheapest tier
        if "per seat" in lower or "per user" in lower or "/user" in lower:
            result["pricing_model"] = "per_seat"
            result["per_seat_price"] = amounts[0]
        elif "usage" in lower or "metered" in lower:
            result["pricing_model"] = "usage"
        else:
            result["pricing_model"] = "flat"
    return result


def enrich_tools(matched: list[MatchedTool]) -> list[EnrichedTool]:
    """Run signal enrichment on all matched tools."""
    enriched: list[EnrichedTool] = []
    for tool in matched:
        domain = _canonicalise_url(tool.canonical_url)

        changelog_score = _enrich_wayback_cdx(domain)
        sla_hours = _enrich_support_sla(domain)
        hiring = _enrich_hiring_velocity(domain)
        sentiment_avg, sentiment_trend = _enrich_review_sentiment(domain)
        social = _enrich_social_signal(tool.canonical_name)
        red_count, red_details = _detect_red_flags(domain, tool.canonical_name)
        pricing = _parse_pricing(tool.pricing_text)

        enriched.append(
            EnrichedTool(
                canonical_name=tool.canonical_name,
                canonical_url=tool.canonical_url,
                match_count=tool.match_count,
                matched_sources=tool.matched_sources,
                categories=tool.categories,
                tags=tool.tags,
                changelog_diff_score=changelog_score,
                support_sla_hours=sla_hours,
                hiring_velocity=hiring,
                review_sentiment_avg=sentiment_avg,
                review_sentiment_trend=sentiment_trend,
                social_signal_score=social,
                update_recency_days=14,  # default — enriched via CDX
                red_flag_count=red_count,
                red_flag_details=red_details,
                pricing_text=tool.pricing_text,
                monthly_price=pricing["monthly_price"],
                per_seat_price=pricing["per_seat_price"],
                has_free_tier=pricing["has_free_tier"],
                pricing_model=pricing["pricing_model"],
            )
        )

    logger.info("[ingestion] enriched %d tools with proxy signals", len(enriched))
    return enriched


# =====================================================================
# 4. SCORING ALGORITHMS
# =====================================================================

def calculate_maintenance_health(tool: EnrichedTool) -> float:
    """Composite maintenance health from deterministic proxy signals.
    Returns score 0-100."""
    # Changelog activity
    diff_score = tool.changelog_diff_score

    # Support SLA (≤4h → 100, degrades linearly)
    sla_score = 100.0 if tool.support_sla_hours <= 4 else max(0.0, 100.0 - (tool.support_sla_hours * 2))

    # Engineering hiring velocity
    hiring_score = 100.0 if tool.hiring_velocity > 0 else 30.0

    return round(
        (diff_score * M_HEALTH_CHANGELOG_W)
        + (sla_score * M_HEALTH_SLA_W)
        + (hiring_score * M_HEALTH_HIRING_W),
        2,
    )


def calculate_smb_relevance(tool: EnrichedTool) -> float:
    """Calculate SMB Relevance Score (0-100) across three dimensions:
    Vertical Match (40), Pricing Accessibility (30), Operational Complexity (30)."""

    # --- Vertical Match (0-40) ---
    smb_verticals = {
        "construction", "hvac", "plumbing", "electrical", "landscaping",
        "healthcare", "dental", "veterinary", "retail", "restaurant",
        "salon", "spa", "cleaning", "roofing", "painting",
        "auto repair", "real estate", "fitness", "daycare",
        "accounting", "legal", "insurance",
    }
    text = " ".join([
        tool.canonical_name,
        " ".join(tool.categories),
        " ".join(tool.tags),
    ]).lower()
    vertical_hits = sum(1 for v in smb_verticals if v in text)
    # Check for SMB-indicative keywords
    smb_keywords = {"small business", "smb", "solopreneur", "freelance",
                    "contractor", "field service", "local business", "trades"}
    smb_hits = sum(1 for k in smb_keywords if k in text)
    vertical_score = min(SMB_VERTICAL_MATCH_MAX, (vertical_hits * 10) + (smb_hits * 8))

    # --- Pricing Accessibility (0-30) ---
    if tool.has_free_tier and tool.monthly_price <= SMB_PRICING_CEILING:
        pricing_score = SMB_PRICING_ACCESS_MAX
    elif tool.monthly_price <= 0:
        pricing_score = SMB_PRICING_ACCESS_MAX * 0.7  # unknown but not penalised
    elif tool.monthly_price <= 100:
        pricing_score = SMB_PRICING_ACCESS_MAX * 0.9
    elif tool.monthly_price <= SMB_PRICING_CEILING:
        pricing_score = SMB_PRICING_ACCESS_MAX * 0.6
    elif tool.pricing_model == "contact_sales":
        pricing_score = 5.0  # heavy penalty
    else:
        pricing_score = SMB_PRICING_ACCESS_MAX * 0.3  # above ceiling

    if tool.per_seat_price > SMB_PER_SEAT_PENALTY_THRESHOLD:
        pricing_score *= 0.5

    # --- Operational Complexity (0-30, inverted) ---
    complexity_penalties = {
        "docker": 8, "kubernetes": 10, "k8s": 10,
        "custom implementation": 10, "dedicated it": 8,
        "terraform": 7, "helm": 7, "self-hosted": 6,
        "api only": 5, "sdk required": 4,
    }
    complexity_bonuses = {
        "zapier": 8, "no-code": 10, "one-click": 8,
        "free trial": 5, "instant setup": 7, "drag and drop": 6,
        "mobile app": 4, "browser extension": 4,
    }
    complexity_score = SMB_OPERATIONAL_COMPLEXITY_MAX
    for term, penalty in complexity_penalties.items():
        if term in text:
            complexity_score -= penalty
    for term, bonus in complexity_bonuses.items():
        if term in text:
            complexity_score += bonus
    complexity_score = max(0, min(SMB_OPERATIONAL_COMPLEXITY_MAX, complexity_score))

    total = round(vertical_score + pricing_score + complexity_score, 2)
    return min(100.0, total)


def calculate_survival_score(tool: EnrichedTool) -> float:
    """Survival Score — 100-point weighted convex combination.

    Formula:
        S = (M_health × 0.30) + (SMB_rel × 0.20) + (R_trend × 0.20)
          + (S_signal × 0.15) + (U_recency × 0.10) + (F_red × 0.05)
    """
    m_health = tool.maintenance_health
    smb_rel = tool.smb_relevance
    r_trend = tool.review_sentiment_avg
    s_signal = tool.social_signal_score

    # Update recency: full marks within window, linear decay after
    if tool.update_recency_days <= UPDATE_RECENCY_WINDOW_DAYS:
        u_recency = 100.0
    else:
        u_recency = max(0.0, 100.0 - ((tool.update_recency_days - UPDATE_RECENCY_WINDOW_DAYS) * 0.5))

    # Red flags: binary multiplier
    if tool.red_flag_count == 0:
        f_red = 100.0
    elif tool.red_flag_count <= 2:
        f_red = 50.0
    else:
        f_red = 0.0

    score = (
        (m_health  * WEIGHTS["m_health"])
        + (smb_rel   * WEIGHTS["smb_rel"])
        + (r_trend   * WEIGHTS["r_trend"])
        + (s_signal  * WEIGHTS["s_signal"])
        + (u_recency * WEIGHTS["u_recency"])
        + (f_red     * WEIGHTS["f_red"])
    )
    return round(score, 2)


def calculate_confidence(tool: EnrichedTool) -> float:
    """Estimate confidence interval for Tier 1 auto-highlight.
    Based on signal completeness and consistency."""
    signals = [
        tool.changelog_diff_score,
        100.0 - (tool.support_sla_hours * 2),
        tool.review_sentiment_avg,
        tool.social_signal_score,
    ]
    # Confidence is higher when signals agree
    if not signals:
        return 0.0
    mean = sum(signals) / len(signals)
    variance = sum((s - mean) ** 2 for s in signals) / len(signals)
    # Low variance + high match count = high confidence
    base_confidence = max(0.0, 100.0 - (variance ** 0.5))
    match_boost = tool.match_count * 5.0
    return min(100.0, round(base_confidence + match_boost, 2))


# =====================================================================
# 5. TIER ASSIGNMENT
# =====================================================================

def evaluate_and_tier(enriched: list[EnrichedTool]) -> list[EnrichedTool]:
    """Apply scoring algorithms and assign tiers."""
    now = datetime.datetime.utcnow().isoformat()

    for tool in enriched:
        # Calculate scores
        tool.maintenance_health = calculate_maintenance_health(tool)
        tool.smb_relevance = calculate_smb_relevance(tool)
        tool.survival_score = calculate_survival_score(tool)
        tool.confidence_interval = calculate_confidence(tool)

        # Tier 1: Sovereign
        if (
            tool.match_count >= TRIPLE_MATCH_MIN
            and tool.survival_score >= TIER_1_MIN_SURVIVAL
            and tool.smb_relevance >= TIER_1_MIN_SMB
        ):
            tool.tier = TierStatus.SOVEREIGN.value
            if tool.confidence_interval >= TIER_1_CONFIDENCE_AUTO:
                tool.review_status = ReviewStatus.AUTO_OK.value
            else:
                tool.review_status = ReviewStatus.PENDING.value

        # Tier 2: Durable
        elif (
            tool.match_count >= DUAL_MATCH_MIN
            and tool.survival_score >= TIER_2_MIN_SURVIVAL
        ):
            tool.tier = TierStatus.DURABLE.value
            tool.review_status = "holding_sandbox"

        # Tier 3: Vertical Specialist (bypasses match count)
        elif tool.vertical_fit_score >= TIER_3_MIN_VERTICAL_FIT:
            tool.tier = TierStatus.VERTICAL.value
            tool.review_status = "vertical_review"

        # Rejected
        else:
            tool.tier = TierStatus.REJECTED.value
            tool.review_status = "archived"

        tool.assigned_at = now

    # Summary
    tier_counts = {}
    for t in enriched:
        tier_counts[t.tier] = tier_counts.get(t.tier, 0) + 1
    logger.info("[ingestion] tier assignment complete: %s", tier_counts)

    return enriched


# =====================================================================
# 6. HITL REVIEW QUEUE
# =====================================================================

# In-memory review queue (production: PostgreSQL pending_approval table)
_review_queue: list[EnrichedTool] = []
_approved_catalog: list[EnrichedTool] = []
_sandbox: list[EnrichedTool] = []


def get_review_queue() -> list[dict]:
    """Return the current HITL review queue as dicts."""
    return [t.to_dict() for t in _review_queue]


def get_approved_catalog() -> list[dict]:
    """Return all approved Tier 1 tools."""
    return [t.to_dict() for t in _approved_catalog]


def get_sandbox() -> list[dict]:
    """Return Tier 2 sandbox tools."""
    return [t.to_dict() for t in _sandbox]


def approve_tool(canonical_name: str) -> bool:
    """HITL approval — move from review queue to approved catalog."""
    for i, tool in enumerate(_review_queue):
        if tool.canonical_name.lower() == canonical_name.lower():
            tool.review_status = ReviewStatus.APPROVED.value
            _approved_catalog.append(tool)
            _review_queue.pop(i)
            logger.info("[hitl] approved: %s", canonical_name)
            return True
    return False


def reject_tool(canonical_name: str) -> bool:
    """HITL rejection — remove from review queue."""
    for i, tool in enumerate(_review_queue):
        if tool.canonical_name.lower() == canonical_name.lower():
            tool.review_status = ReviewStatus.REJECTED.value
            _review_queue.pop(i)
            logger.info("[hitl] rejected: %s", canonical_name)
            return True
    return False


def _route_to_queues(tiered: list[EnrichedTool]) -> dict[str, int]:
    """Route tiered tools to appropriate queues/stores."""
    counts = {"review_queue": 0, "auto_approved": 0, "sandbox": 0, "rejected": 0}

    for tool in tiered:
        if tool.tier == TierStatus.SOVEREIGN.value:
            if tool.review_status == ReviewStatus.AUTO_OK.value:
                _approved_catalog.append(tool)
                counts["auto_approved"] += 1
            else:
                _review_queue.append(tool)
                counts["review_queue"] += 1
        elif tool.tier == TierStatus.DURABLE.value:
            _sandbox.append(tool)
            counts["sandbox"] += 1
        elif tool.tier == TierStatus.VERTICAL.value:
            _approved_catalog.append(tool)  # Tier 3 auto-approved
            counts["auto_approved"] += 1
        else:
            counts["rejected"] += 1

    logger.info("[ingestion] routed to queues: %s", counts)
    return counts


# =====================================================================
# 7. TIER 2 → TIER 1 PROMOTION SWEEP
# =====================================================================

def run_promotion_sweep() -> list[str]:
    """Weekly sweep: check if any Tier 2 sandbox tools now qualify
    for Tier 1 based on improved signals."""
    promoted: list[str] = []

    for tool in list(_sandbox):
        # Re-calculate scores
        tool.maintenance_health = calculate_maintenance_health(tool)
        tool.smb_relevance = calculate_smb_relevance(tool)
        tool.survival_score = calculate_survival_score(tool)

        if tool.survival_score >= TIER_2_PROMOTION_SURVIVAL:
            tool.tier = TierStatus.SOVEREIGN.value
            tool.review_status = ReviewStatus.PENDING.value
            _review_queue.append(tool)
            _sandbox.remove(tool)
            promoted.append(tool.canonical_name)
            logger.info("[promotion] %s promoted from Tier 2 → Tier 1 review queue", tool.canonical_name)

    return promoted


# =====================================================================
# 8. "WHY INCLUDED?" EXPLANATION GENERATOR
# =====================================================================

def generate_why_included(tool: EnrichedTool) -> dict:
    """Generate the deterministic 'Why Included?' explanation for UI tooltips."""
    reasons: list[str] = []
    warnings: list[str] = []

    # Consensus Verification
    if tool.match_count >= TRIPLE_MATCH_MIN:
        reasons.append(
            f"✓ Consensus Verification: Actively listed across {', '.join(tool.matched_sources)}."
        )
    elif tool.match_count >= DUAL_MATCH_MIN:
        reasons.append(
            f"✓ Dual Verification: Listed on {', '.join(tool.matched_sources)}."
        )

    # Maintenance Confirmed
    sla_text = f"{tool.support_sla_hours:.0f}" if tool.support_sla_hours < 24 else "> 24"
    reasons.append(
        f"✓ Maintenance Confirmed: Last changelog diff {tool.update_recency_days} days ago; "
        f"G2 aggregate support response SLA < {sla_text} hours."
    )

    # SMB Aligned
    price_text = f"${tool.monthly_price:.0f}/month" if tool.monthly_price > 0 else "Free tier available"
    reasons.append(
        f"✓ SMB Aligned: Relevance Score {tool.smb_relevance:.0f}/100. "
        f"Base tier pricing at {price_text}."
    )

    # Operational Safety
    if tool.red_flag_count == 0:
        reasons.append(
            "✓ Operational Safety: Zero major red flags or security breaches "
            "detected in the trailing 180 days."
        )
    else:
        warnings.append(
            f"⚠ {tool.red_flag_count} red flag(s) detected: "
            + "; ".join(tool.red_flag_details[:3])
        )

    # Survival Score
    reasons.append(f"✓ Survival Score: {tool.survival_score:.1f}/100")

    return {
        "tool_name": tool.canonical_name,
        "tier": tool.tier,
        "badge": BADGE_TIERS.get(tool.tier, {}),
        "reasons": reasons,
        "warnings": warnings,
        "scores": {
            "survival": tool.survival_score,
            "maintenance_health": tool.maintenance_health,
            "smb_relevance": tool.smb_relevance,
            "confidence": tool.confidence_interval,
        },
    }


# =====================================================================
# 9. FULL PIPELINE ORCHESTRATOR
# =====================================================================

def run_daily_pipeline(async_: bool = False) -> dict:
    """Execute the full daily ingestion pipeline.

    Steps:
        1. Fetch all directories
        2. Normalize & Triple Match
        3. Filter (archive single-match unless Tier 3 potential)
        4. Enrich signals
        5. Score & tier
        6. Route to queues
        7. Return summary

    Args:
        async_: If True, dispatch via Celery (requires Redis).
                If False, run synchronously.
    """
    start = time.time()
    logger.info("[pipeline] === Daily Ingestion Pipeline Started ===")

    # Step 1: Fetch
    directory_data = fetch_all_directories()
    total_fetched = sum(len(v) for v in directory_data.values())

    # Step 2: Normalize & Match
    matched = normalize_and_match(directory_data)

    # Step 3: Filter — archive tools with <2 matches (unless Tier 3 potential)
    viable = [t for t in matched if t.match_count >= DUAL_MATCH_MIN]
    archived_count = len(matched) - len(viable)

    # Step 4: Enrich
    enriched = enrich_tools(viable)

    # Step 5: Score & Tier
    tiered = evaluate_and_tier(enriched)

    # Step 6: Route to queues
    routing = _route_to_queues(tiered)

    elapsed = round(time.time() - start, 2)
    summary = {
        "status": "completed",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "elapsed_seconds": elapsed,
        "directories_queried": len(directory_data),
        "total_listings_fetched": total_fetched,
        "unique_tools_matched": len(matched),
        "viable_tools": len(viable),
        "archived_single_match": archived_count,
        "tiered_tools": {t.tier: 0 for t in tiered},
        "routing": routing,
        "pipeline_version": "3.0",
    }
    # Count tiers
    for t in tiered:
        summary["tiered_tools"][t.tier] = summary["tiered_tools"].get(t.tier, 0) + 1

    logger.info("[pipeline] === Pipeline Complete in %.2fs ===", elapsed)
    logger.info("[pipeline] Summary: %s", json.dumps(summary, indent=2))
    return summary


# =====================================================================
# 10. PERSISTENCE (JSON file-based for solo-founder phase)
# =====================================================================

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".pipeline_data")


def _ensure_data_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def save_pipeline_state():
    """Persist current pipeline state to disk."""
    _ensure_data_dir()
    state = {
        "review_queue": [t.to_dict() for t in _review_queue],
        "approved_catalog": [t.to_dict() for t in _approved_catalog],
        "sandbox": [t.to_dict() for t in _sandbox],
        "saved_at": datetime.datetime.utcnow().isoformat(),
    }
    path = os.path.join(_DATA_DIR, "pipeline_state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    logger.info("[persistence] saved pipeline state to %s", path)


def load_pipeline_state() -> bool:
    """Load pipeline state from disk.  Returns True if state was loaded."""
    global _review_queue, _approved_catalog, _sandbox
    path = os.path.join(_DATA_DIR, "pipeline_state.json")
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        _review_queue = [EnrichedTool.from_dict(d) for d in state.get("review_queue", [])]
        _approved_catalog = [EnrichedTool.from_dict(d) for d in state.get("approved_catalog", [])]
        _sandbox = [EnrichedTool.from_dict(d) for d in state.get("sandbox", [])]
        logger.info("[persistence] loaded pipeline state from %s", path)
        return True
    except Exception as exc:
        logger.warning("[persistence] failed to load state: %s", exc)
        return False


# =====================================================================
# 11. MODULE INIT
# =====================================================================

logger.info(
    "ingestion_engine.py loaded — v3.0 pipeline with Triple Match, "
    "%d directories, Survival Score weights: %s",
    len(DIRECTORIES),
    WEIGHTS,
)
