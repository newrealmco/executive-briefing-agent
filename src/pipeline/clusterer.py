"""
Groups items by theme for the weekly briefing.
"""
from __future__ import annotations

from src.logger import get_logger

log = get_logger("pipeline.clusterer")


def cluster(items: list[dict]) -> dict[str, list[dict]]:
    """Group items by their primary topic_match.

    Items with no topic_matches go into 'uncategorized'.
    Each group is sorted by final_score descending.
    """
    groups: dict[str, list[dict]] = {}

    for item in items:
        topic_matches: list[str] = item.get("topic_matches") or []
        primary = topic_matches[0] if topic_matches else "uncategorized"

        if primary not in groups:
            groups[primary] = []
        groups[primary].append(item)

    for topic in groups:
        groups[topic].sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

    log.info(
        "Clusterer: %d items → %d clusters (%s)",
        len(items),
        len(groups),
        ", ".join(f"{k}:{len(v)}" for k, v in groups.items()),
    )
    return groups
