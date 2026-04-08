"""
LLM Call 2 + formula application.
"""
from __future__ import annotations

from src.llm import client as llm_client
from src.llm import prompts
from src.logger import get_logger

log = get_logger("pipeline.scorer")

# Default urgency and novelty before dedup store adjustments
_DEFAULT_URGENCY = 0.5
_DEFAULT_NOVELTY = 0.7


def _apply_boosts(item: dict) -> tuple[float, list[str]]:
    """Return (total_boost, boosts_applied_list)."""
    topic_matches: list[str] = item.get("topic_matches") or []
    title_lower: str = (item.get("title") or "").lower()
    source: str = (item.get("source") or "").lower()
    boosts: list[str] = []
    total = 0.0

    # jdd_direct_connection
    if "jdd_direct_connection" in topic_matches or "Judgment Driven Development" in topic_matches:
        total += 0.20
        boosts.append("jdd_direct_connection")

    # agent_governance_intersection
    has_agent_gov = (
        "agent_governance_intersection" in topic_matches
        or ("Agents" in topic_matches and "AI governance" in topic_matches)
    )
    if has_agent_gov:
        total += 0.15
        boosts.append("agent_governance_intersection")

    # consulting_lead_signal — zoho source
    if "zoho" in source:
        total += 0.25
        boosts.append("consulting_lead_signal")

    # mcp_new_development — mcp or model context protocol in title
    if "mcp" in title_lower or "model context protocol" in title_lower:
        total += 0.15
        boosts.append("mcp_new_development")

    # has_jdd_signal from zoho or gmail
    has_jdd_signal = "jdd_direct_connection" in topic_matches or "Judgment Driven Development" in topic_matches
    if ("zoho" in source or "gmail" in source) and has_jdd_signal:
        total += 0.10
        boosts.append("zoho_gmail_jdd_signal")

    return total, boosts


def score(items: list[dict], cfg: dict) -> list[dict]:
    """Score items using LLM Call 2 and apply the scoring formula."""
    scoring_cfg = cfg.get("scoring", {})
    weights = scoring_cfg.get(
        "weights",
        {
            "relevance": 0.30,
            "leverage": 0.20,
            "urgency": 0.15,
            "novelty": 0.15,
            "source_trust": 0.10,
            "personal_fit": 0.10,
        },
    )

    profile = cfg.get("profile", {})
    profile_body: str = profile.get("body", "")
    priorities: str = "\n".join(
        f"- {p}" for p in profile.get("priorities", [])
    ) if isinstance(profile.get("priorities"), list) else profile_body
    assumptions_md: str = cfg.get("assumptions", "")

    scored: list[dict] = []

    for item in items:
        title: str = item.get("title", "")
        summary: str = item.get("content_summary", "") or item.get("content_raw", "")[:500]
        topic_matches: list[str] = item.get("topic_matches") or []
        source_name: str = item.get("source_name", item.get("source", ""))
        trust_tier: int = item.get("source_trust_tier", 5)
        source_trust_score: float = item.get("source_trust_score", 0.2)

        try:
            system, user = prompts.score_and_explain(
                title=title,
                summary=summary,
                topic_matches=topic_matches,
                source_name=source_name,
                trust_tier=trust_tier,
                profile_md=profile_body,
                priorities=priorities,
                assumptions_md=assumptions_md,
            )
            result = llm_client.call(system, user)

            item["relevance_score"] = float(result.get("relevance_score", 0.0))
            item["leverage_score"] = float(result.get("leverage_score", 0.0))
            item["personal_fit_score"] = float(result.get("personal_fit_score", 0.0))
            item["why_it_matters"] = result.get("why_it_matters", "")
            item["recommended_action"] = result.get("recommended_action", "monitor")

            urgency = float(item.get("urgency_score") or _DEFAULT_URGENCY)
            novelty = float(item.get("novelty_score") or _DEFAULT_NOVELTY)

            raw_score = (
                weights["relevance"] * item["relevance_score"]
                + weights["leverage"] * item["leverage_score"]
                + weights["urgency"] * urgency
                + weights["novelty"] * novelty
                + weights["source_trust"] * source_trust_score
                + weights["personal_fit"] * item["personal_fit_score"]
            )

            boost_total, boosts_applied = _apply_boosts(item)
            item["boosts_applied"] = (item.get("boosts_applied") or []) + boosts_applied

            final = raw_score + boost_total
            item["final_score"] = max(0.0, min(1.0, final))

        except Exception as exc:
            log.warning("Scorer LLM failed for item id=%s: %s", item.get("id", "?"), exc)
            item["final_score"] = max(0.0, min(1.0, source_trust_score * 0.5))

        scored.append(item)

    scored.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
    log.info("Scorer complete: %d items scored", len(scored))
    return scored
