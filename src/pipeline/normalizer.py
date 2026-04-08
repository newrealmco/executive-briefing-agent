"""
Validates and cleans raw items from collectors.
"""
from __future__ import annotations

import re

from src.collectors.schema import empty_item
from src.logger import get_logger

log = get_logger("pipeline.normalizer")

_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
_CONTENT_MAX = 8000


def normalize(items: list[dict]) -> list[dict]:
    """Validate and clean raw items. Returns list of normalized items."""
    cleaned: list[dict] = []

    for raw in items:
        item = {**empty_item(), **raw}

        # Strip whitespace from string fields
        item["title"] = (item.get("title") or "").strip()
        item["url"] = (item.get("url") or "").strip()
        item["author"] = (item.get("author") or "").strip()

        # Truncate content_raw
        content = item.get("content_raw") or ""
        if len(content) > _CONTENT_MAX:
            content = content[:_CONTENT_MAX]
        item["content_raw"] = content

        # Skip items with no title AND no content
        if not item["title"] and not item["content_raw"]:
            log.warning(
                "Skipping item id=%s — empty title and content_raw", item.get("id", "?")
            )
            continue

        # Language detection: Hebrew characters → "he"
        combined = item["title"] + " " + item["content_raw"]
        if _HEBREW_RE.search(combined):
            item["language"] = "he"

        cleaned.append(item)

    log.info("Normalizer: %d → %d items after cleaning", len(items), len(cleaned))
    return cleaned
