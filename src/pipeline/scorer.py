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
