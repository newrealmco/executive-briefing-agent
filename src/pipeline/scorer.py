"""
Scorer — formula application only (no LLM call).

LLM scoring now happens in enricher.py (combined call).
This module applies the weighted formula, boosts, and sorts.
"""
from __future__ import annotations

from src.logger import get_logger

log = get_logger("pipeline.scorer")

_DEFAULT_URGENCY = 0.5
_DEFAULT_NOVELTY = 0.7


def _apply_boosts(item: dict) -> tuple[float, list[str]]:
    topic_matches: list[str] = item.get("topic_matches") or []
    title_lower: str = (item.get("title") or "").lower()
    source: str = (item.get("source") or "").lower()
    boosts: list[str] = []
    total = 0.0

    if "Judgment Driven Development" in topic_matches:
        total += 0.10
        boosts.append("jdd_direct_connection")

    has_agent = "Agents — coding and deployed" in topic_matches
    has_gov = "AI governance and supply chain security" in topic_matches
    if has_agent and has_gov:
        total += 0.15
        boosts.append("agent_governance_intersection")

    if "zoho" in source:
        total += 0.25
        boosts.append("consulting_lead_signal")

    if "mcp" in title_lower or "model context protocol" in title_lower:
        total += 0.15
        boosts.append("mcp_new_development")

    if ("zoho" in source or "gmail" in source) and "Judgment Driven Development" in topic_matches:
        total += 0.10
        boosts.append("zoho_gmail_jdd_signal")

    # genuinely_novel_capability — breaking signal on a new model/tool/capability
    novelty = item.get("metadata", {}).get("novelty_signal", "")
    if novelty == "breaking" and any(
        t in topic_matches for t in [
            "AI and ML frontier",
            "Agents — coding and deployed",
            "AI governance and supply chain security",
        ]
    ):
        total += 0.15
        boosts.append("genuinely_novel_capability")

    return total, boosts


def score(items: list[dict], cfg: dict) -> list[dict]:
    """Apply scoring formula and boosts. No LLM calls."""
    weights = cfg.get("scoring", {}).get("weights", {
        "relevance": 0.30,
        "leverage": 0.20,
        "urgency": 0.15,
        "novelty": 0.15,
        "source_trust": 0.10,
        "personal_fit": 0.10,
    })

    for item in items:
        source_trust_score: float = item.get("source_trust_score", 0.2)
        urgency = float(item.get("urgency_score") or _DEFAULT_URGENCY)
        novelty = float(item.get("novelty_score") or _DEFAULT_NOVELTY)

        raw_score = (
            weights["relevance"] * item.get("relevance_score", 0.0)
            + weights["leverage"] * item.get("leverage_score", 0.0)
            + weights["urgency"] * urgency
            + weights["novelty"] * novelty
            + weights["source_trust"] * source_trust_score
            + weights["personal_fit"] * item.get("personal_fit_score", 0.0)
        )

        boost_total, boosts_applied = _apply_boosts(item)
        item["boosts_applied"] = (item.get("boosts_applied") or []) + boosts_applied
        item["final_score"] = max(0.0, min(1.0, raw_score + boost_total))

    items.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
    log.info("Scorer complete: %d items scored", len(items))
    return items


def apply_diversity_caps(
    items: list[dict],
    source_cap: float = 0.40,
    topic_cap: float = 0.35,
) -> list[dict]:
    """
    Enforce source and topic diversity on an already-scored, sorted list.

    source_cap: no single source may exceed this fraction of final items.
    topic_cap:  no single topic (primary = first topic_match) may exceed
                this fraction of final items.

    Items must be sorted by final_score descending before calling this.
    Lowest-scored items are dropped first (they appear last in the list).
    """
    if not items:
        return items

    total = len(items)

    # ── 1. Source cap ────────────────────────────────────────────────────────
    max_per_source = max(1, int(total * source_cap))
    source_counts: dict[str, int] = {}
    after_source: list[dict] = []
    dropped_source = 0

    for item in items:
        src = (item.get("source") or "unknown").lower()
        if source_counts.get(src, 0) < max_per_source:
            after_source.append(item)
            source_counts[src] = source_counts.get(src, 0) + 1
        else:
            dropped_source += 1
            log.debug("Source cap dropped [%s]: %s", src, item.get("title", "")[:60])

    if dropped_source:
        log.info(
            "Source cap (%.0f%%): dropped %d items; per-source counts: %s",
            source_cap * 100,
            dropped_source,
            source_counts,
        )

    # ── 2. Topic cap ─────────────────────────────────────────────────────────
    # Attribute each item to its primary topic (first element of topic_matches).
    # Items with no topic_matches are always kept.
    post_source_total = len(after_source)
    max_per_topic = max(1, int(post_source_total * topic_cap))
    topic_counts: dict[str, int] = {}
    final: list[dict] = []
    dropped_topic = 0

    for item in after_source:
        topics = item.get("topic_matches") or []
        primary = topics[0] if topics else None
        if primary is None or topic_counts.get(primary, 0) < max_per_topic:
            final.append(item)
            if primary:
                topic_counts[primary] = topic_counts.get(primary, 0) + 1
        else:
            dropped_topic += 1
            log.debug(
                "Topic cap dropped [%s]: %s", primary, item.get("title", "")[:60]
            )

    if dropped_topic:
        log.info(
            "Topic cap (%.0f%%): dropped %d items; per-topic counts: %s",
            topic_cap * 100,
            dropped_topic,
            topic_counts,
        )

    log.info(
        "Diversity caps applied: %d → %d items (−%d source, −%d topic)",
        total,
        len(final),
        dropped_source,
        dropped_topic,
    )
    return final
