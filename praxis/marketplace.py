# --------------- Praxis Marketplace — Workflow Templates & Community ---------------
"""
v19 · Platform Evolution — Workflow Marketplace

Enables users to save, share, rate, and discover pre-built workflow
templates.  A template is a serialised WorkflowPlan that others can
clone and execute with their own credentials.

Features
────────
    • Publish / unpublish workflow templates
    • Browse by category, rating, popularity
    • Rate and review templates (1-5 stars + comment)
    • Featured / curated collections
    • Revenue tracking stubs for Pro tier monetisation

Storage is file-based (JSON) for single-process deployments.  Swap
for a database adapter in production using the ToolRepository port
pattern.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.marketplace")

_BASE = Path(__file__).resolve().parent
_TEMPLATES_PATH = _BASE / "marketplace_templates.json"
_REVIEWS_PATH = _BASE / "marketplace_reviews.json"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DATA MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class TemplateReview:
    """A user review of a marketplace template."""
    review_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    template_id: str = ""
    author: str = "anonymous"
    rating: int = 5                        # 1-5 stars
    comment: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "template_id": self.template_id,
            "author": self.author,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowTemplate:
    """A shareable workflow template in the marketplace."""
    template_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    description: str = ""
    author: str = "anonymous"
    category: str = "general"              # general | marketing | support | dev | analytics | compliance
    tags: List[str] = field(default_factory=list)
    plan_json: Dict[str, Any] = field(default_factory=dict)
    published: bool = False
    featured: bool = False
    download_count: int = 0
    avg_rating: float = 0.0
    review_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    price_usd: float = 0.0                # 0 = free
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "tags": self.tags,
            "plan_json": self.plan_json,
            "published": self.published,
            "featured": self.featured,
            "download_count": self.download_count,
            "avg_rating": self.avg_rating,
            "review_count": self.review_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "price_usd": self.price_usd,
            "version": self.version,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERSISTENCE HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _load_json(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_json(path: Path, data: Any) -> None:
    try:
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except OSError as exc:
        log.warning("Failed to save %s: %s", path, exc)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEMPLATE STORAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _load_templates() -> Dict[str, Dict]:
    return _load_json(_TEMPLATES_PATH)


def _save_templates(templates: Dict[str, Dict]) -> None:
    _save_json(_TEMPLATES_PATH, templates)


def _load_reviews() -> Dict[str, List[Dict]]:
    return _load_json(_REVIEWS_PATH)


def _save_reviews(reviews: Dict[str, List[Dict]]) -> None:
    _save_json(_REVIEWS_PATH, reviews)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PUBLIC API — TEMPLATES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def publish_template(
    name: str,
    description: str,
    plan_json: Dict[str, Any],
    *,
    author: str = "anonymous",
    category: str = "general",
    tags: Optional[List[str]] = None,
    price_usd: float = 0.0,
) -> WorkflowTemplate:
    """Create and publish a workflow template."""
    tpl = WorkflowTemplate(
        name=name,
        description=description,
        author=author,
        category=category,
        tags=tags or [],
        plan_json=plan_json,
        published=True,
        price_usd=price_usd,
    )
    templates = _load_templates()
    templates[tpl.template_id] = tpl.to_dict()
    _save_templates(templates)
    log.info("Template published: %s (%s) by %s", tpl.name, tpl.template_id, tpl.author)
    return tpl


def get_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single template by ID."""
    templates = _load_templates()
    return templates.get(template_id)


def list_templates(
    *,
    category: Optional[str] = None,
    featured_only: bool = False,
    sort_by: str = "download_count",       # download_count | avg_rating | created_at
    limit: int = 20,
    skip: int = 0,
) -> Dict[str, Any]:
    """Browse templates with filtering, sorting, and pagination."""
    templates = _load_templates()
    items = [v for v in templates.values() if v.get("published", False)]

    if category:
        items = [t for t in items if t.get("category") == category]
    if featured_only:
        items = [t for t in items if t.get("featured", False)]

    # Sort
    reverse = True
    if sort_by == "created_at":
        key = lambda t: t.get("created_at", 0)
    elif sort_by == "avg_rating":
        key = lambda t: t.get("avg_rating", 0)
    else:
        key = lambda t: t.get("download_count", 0)
    items.sort(key=key, reverse=reverse)

    total = len(items)
    page = items[skip : skip + limit]
    return {"total": total, "skip": skip, "limit": limit, "items": page}


def download_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Get a template and increment its download counter."""
    templates = _load_templates()
    tpl = templates.get(template_id)
    if tpl is None:
        return None
    tpl["download_count"] = tpl.get("download_count", 0) + 1
    templates[template_id] = tpl
    _save_templates(templates)
    return tpl


def unpublish_template(template_id: str) -> bool:
    """Hide a template from the public gallery."""
    templates = _load_templates()
    if template_id not in templates:
        return False
    templates[template_id]["published"] = False
    _save_templates(templates)
    return True


def feature_template(template_id: str, featured: bool = True) -> bool:
    """Mark a template as featured (staff pick)."""
    templates = _load_templates()
    if template_id not in templates:
        return False
    templates[template_id]["featured"] = featured
    _save_templates(templates)
    return True


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PUBLIC API — REVIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def add_review(
    template_id: str,
    rating: int,
    comment: str = "",
    author: str = "anonymous",
) -> Optional[TemplateReview]:
    """Add a review to a template and recalculate average rating."""
    templates = _load_templates()
    if template_id not in templates:
        return None
    rating = max(1, min(5, rating))

    review = TemplateReview(
        template_id=template_id,
        author=author,
        rating=rating,
        comment=comment,
    )
    reviews = _load_reviews()
    tpl_reviews = reviews.get(template_id, [])
    tpl_reviews.append(review.to_dict())
    reviews[template_id] = tpl_reviews
    _save_reviews(reviews)

    # Update aggregate on template
    all_ratings = [r["rating"] for r in tpl_reviews]
    templates[template_id]["avg_rating"] = round(sum(all_ratings) / len(all_ratings), 2)
    templates[template_id]["review_count"] = len(all_ratings)
    _save_templates(templates)

    return review


def get_reviews(template_id: str) -> List[Dict[str, Any]]:
    """Get all reviews for a template."""
    reviews = _load_reviews()
    return reviews.get(template_id, [])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MARKETPLACE STATS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def marketplace_stats() -> Dict[str, Any]:
    """Aggregate marketplace statistics."""
    templates = _load_templates()
    published = [t for t in templates.values() if t.get("published")]
    reviews = _load_reviews()
    total_reviews = sum(len(r) for r in reviews.values())
    total_downloads = sum(t.get("download_count", 0) for t in published)

    return {
        "total_templates": len(templates),
        "published_templates": len(published),
        "featured_count": sum(1 for t in published if t.get("featured")),
        "total_reviews": total_reviews,
        "total_downloads": total_downloads,
        "categories": list({t.get("category", "general") for t in published}),
        "avg_rating": (
            round(sum(t.get("avg_rating", 0) for t in published) / len(published), 2)
            if published else 0.0
        ),
    }
