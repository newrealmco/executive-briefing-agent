"""
Normalized item schema shared by all collectors.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def make_id(url: str = "", content: str = "") -> str:
    raw = (url or content).encode()
    return hashlib.sha256(raw).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_item() -> dict[str, Any]:
    return {
        "id": "",
        "source": "",
        "source_name": "",
        "source_trust_tier": 5,
        "title": "",
        "url": "",
        "author": "",
        "published_at": "",
        "collected_at": now_iso(),
        "content_raw": "",
        "content_summary": "",
        "language": "en",
        "topic_matches": [],
        "relevance_score": 0.0,
        "urgency_score": 0.0,
        "leverage_score": 0.0,
        "novelty_score": 0.0,
        "source_trust_score": 0.2,
        "personal_fit_score": 0.0,
        "final_score": 0.0,
        "why_it_matters": "",
        "recommended_action": "monitor",
        "penalties_applied": [],
        "boosts_applied": [],
        "metadata": {},
    }
