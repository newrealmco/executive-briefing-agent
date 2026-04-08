"""
RSS/Atom/Substack collector.

Returns normalized items for every feed entry published within `lookback_hours`.
No auth required.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.schema import empty_item, make_id, now_iso
from src.logger import get_logger

log = get_logger(__name__)

# Trust tier by source name (must match scoring.md)
SOURCE_TRUST = {
    "Simon Willison": (1, 1.0),
    "Anthropic Blog": (1, 1.0),
    "Lenny's Newsletter": (1, 1.0),
    "The Pragmatic Engineer": (1, 1.0),
    "Latent Space": (1, 1.0),
    "OpenAI Blog": (2, 0.8),
    "Hugging Face Blog": (2, 0.8),
    "Stratechery": (2, 0.8),
    "One Useful Thing": (2, 0.8),
    "Import AI": (2, 0.8),
    "Geektime English": (3, 0.6),
    "Calcalist Tech": (3, 0.6),
    "Ben's Bites": (3, 0.6),
}


def _strip_html(html: str) -> str:
    return BeautifulSoup(html or "", "html.parser").get_text(separator=" ", strip=True)


def _parse_published(entry: Any) -> str:
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if ts:
        return datetime(*ts[:6], tzinfo=timezone.utc).isoformat()
    return now_iso()


def _is_recent(entry: Any, lookback_hours: int) -> bool:
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    if not ts:
        return True  # can't tell — include it
    published = datetime(*ts[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    return published >= cutoff


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_feed(url: str) -> Any:
    return feedparser.parse(url)


def collect(feeds: list[dict[str, str]], lookback_hours: int = 24) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for feed_cfg in feeds:
        name = feed_cfg.get("name", "Unknown")
        url = feed_cfg["url"]
        language = feed_cfg.get("language", "en")
        topic_boost = feed_cfg.get("topic_weight_boost", "")

        try:
            log.info("RSS fetch: %s (%s)", name, url)
            parsed = _fetch_feed(url)
        except Exception as exc:
            log.warning("RSS feed failed [%s]: %s", name, exc)
            continue

        if parsed.bozo and not parsed.entries:
            log.warning("RSS feed malformed [%s]", name)
            continue

        tier, trust_score = SOURCE_TRUST.get(name, (4, 0.4))

        for entry in parsed.entries:
            if not _is_recent(entry, lookback_hours):
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            author = entry.get("author", "")
            content_raw = _strip_html(
                entry.get("content", [{}])[0].get("value", "")
                or entry.get("summary", "")
            )
            published_at = _parse_published(entry)

            item = empty_item()
            item.update(
                {
                    "id": make_id(url=link or title),
                    "source": "rss",
                    "source_name": name,
                    "source_trust_tier": tier,
                    "source_trust_score": trust_score,
                    "title": title,
                    "url": link,
                    "author": author,
                    "published_at": published_at,
                    "content_raw": content_raw[:8000],  # cap to avoid token bloat
                    "language": "he" if language == "Hebrew" else "en",
                    "metadata": {
                        "feed_url": url,
                        "topic_weight_boost": topic_boost,
                    },
                }
            )
            items.append(item)

    log.info("RSS collector: %d items collected", len(items))
    return items
