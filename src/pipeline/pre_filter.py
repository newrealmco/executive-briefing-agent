"""
Keyword-based pre-filter — runs before any LLM call.

Scores each item against topic keywords from config/topics.md.
Items scoring zero (no keyword matches anywhere) are dropped entirely.
Items with weak matches get a low heuristic score to inform the LLM scorer.

This is the single biggest token reduction lever:
  - Before: every collected item goes to LLM (161 items → 322 API calls)
  - After: only keyword-matched items go to LLM (typically 40–60% pass)
"""
from __future__ import annotations

import re
from typing import Any

from src.logger import get_logger

log = get_logger("pipeline.pre_filter")

# Minimum number of keyword matches to pass to LLM pipeline
_MIN_MATCHES = 1


def _searchable(item: dict) -> str:
    """Combine all text fields into one lowercase string for matching."""
    parts = [
        item.get("title", ""),
        item.get("content_raw", "")[:2000],  # only search first 2000 chars
        item.get("source_name", ""),
    ]
    return " ".join(parts).lower()


def _count_matches(text: str, keywords: list[str]) -> int:
    total = 0
    for kw in keywords:
        if kw.lower() in text:
            total += 1
    return total


def pre_filter(items: list[dict[str, Any]], topics: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return only items that match at least one topic keyword.
    Sets item["_keyword_score"] (0.0–1.0) as a heuristic pre-score.
    """
    passed: list[dict[str, Any]] = []
    dropped = 0

    # Flatten all keywords with their topic weights
    topic_keywords: list[tuple[str, list[str], int]] = []
    for topic_name, topic_data in topics.items():
        keywords = topic_data.get("keywords", [])
        weight = topic_data.get("weight", 2)
        if keywords:
            topic_keywords.append((topic_name, keywords, weight))

    max_possible_score = sum(w for _, _, w in topic_keywords) or 1

    for item in items:
        text = _searchable(item)
        total_score = 0.0
        matched_topics: list[str] = []

        for topic_name, keywords, weight in topic_keywords:
            n = _count_matches(text, keywords)
            if n > 0:
                # Diminishing returns: log-scale within topic
                topic_score = weight * min(1.0, n / 3)
                total_score += topic_score
                matched_topics.append(topic_name)

        if total_score >= _MIN_MATCHES or _is_email(item):
            item["_keyword_score"] = min(1.0, total_score / max_possible_score)
            item["_keyword_topics"] = matched_topics
            passed.append(item)
        else:
            dropped += 1

    log.info(
        "Pre-filter: %d/%d items passed (%d dropped, no keyword match)",
        len(passed), len(items), dropped,
    )
    return passed


def _is_email(item: dict) -> bool:
    """Always pass email items — they have high prior relevance."""
    return item.get("source") in ("gmail", "zoho")
