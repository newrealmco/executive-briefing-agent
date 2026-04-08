"""
Reddit collector via public RSS feeds (no auth required).

Reddit exposes .rss endpoints for every subreddit — no API key needed.
Feed URLs are configured in config/sources.md under ## Reddit > feeds.

Each entry is normalized to the same schema as the RSS collector.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import feedparser
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.schema import empty_item, make_id, now_iso
from src.logger import get_logger

log = get_logger(__name__)

LOOKBACK_HOURS = 24
USER_AGENT = "personal-briefing-agent/1.0 (RSS reader)"


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
        return True
    published = datetime(*ts[:6], tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    return published >= cutoff


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _fetch_feed(url: str) -> Any:
    # Reddit requires a descriptive User-Agent or it returns 429/403
    return feedparser.parse(url, agent=USER_AGENT)


def collect(reddit_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    feeds = reddit_cfg.get("feeds", [])
    if not feeds:
        log.warning("No Reddit feeds configured — skipping Reddit collector")
        return []

    items: list[dict[str, Any]] = []

    for feed_cfg in feeds:
        name: str = feed_cfg["name"]
        url: str = feed_cfg["url"]
        topic: str = feed_cfg.get("topic", "")
        source_name = f"r/{name}"

        try:
            log.info("Reddit RSS fetch: %s (%s)", source_name, url)
            parsed = _fetch_feed(url)
        except Exception as exc:
            log.warning("Reddit RSS fetch failed [%s]: %s", source_name, exc)
            continue

        if parsed.bozo and not parsed.entries:
            log.warning("Reddit RSS malformed [%s]", source_name)
            continue

        for entry in parsed.entries:
            if not _is_recent(entry, LOOKBACK_HOURS):
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
                    "source": "reddit",
                    "source_name": source_name,
                    "source_trust_tier": 4,
                    "source_trust_score": 0.4,
                    "title": title,
                    "url": link,
                    "author": author,
                    "published_at": published_at,
                    "content_raw": content_raw[:8000],
                    "metadata": {
                        "feed_url": url,
                        "subreddit": name,
                        "topic": topic,
                    },
                }
            )
            items.append(item)

    log.info("Reddit collector: %d items collected", len(items))
    return items
