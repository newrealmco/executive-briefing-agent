"""
Combined enrich + score — single LLM call per item (was two).

Replaces the former separate enricher (Call 1) and scorer (Call 2).
Uses prompt caching on the static system prompt to cut input tokens ~75%
after the first call in each batch.
"""
from __future__ import annotations

from src.llm import client as llm_client
from src.llm import prompts
from src.logger import get_logger

log = get_logger("pipeline.enricher")

_BATCH_SIZE = 10


def enrich(items: list[dict], cfg: dict) -> list[dict]:
    """
    Summarize, classify, and score each item in a single LLM call.
    Populates: content_summary, topic_matches, language, novelty_signal,
               relevance_score, leverage_score, personal_fit_score,
               why_it_matters, recommended_action.
    """
    topic_list: list[str] = list(cfg.get("topics", {}).keys())
    profile = cfg.get("profile", {})
    profile_md: str = profile.get("body", "")
    assumptions_md: str = cfg.get("assumptions", "")

    enriched: list[dict] = []
    total = len(items)

    for batch_start in range(0, total, _BATCH_SIZE):
        batch = items[batch_start: batch_start + _BATCH_SIZE]
        batch_num = batch_start // _BATCH_SIZE + 1
        log.info(
            "Enricher batch %d: processing items %d–%d of %d",
            batch_num,
            batch_start + 1,
            min(batch_start + _BATCH_SIZE, total),
            total,
        )

        for item in batch:
            if not item.get("content_raw") and not item.get("title"):
                enriched.append(item)
                continue

            try:
                system, user = prompts.enrich_and_score(
                    title=item.get("title", ""),
                    content_raw=item.get("content_raw", ""),
                    source_name=item.get("source_name", item.get("source", "")),
                    trust_tier=item.get("source_trust_tier", 5),
                    topic_list=topic_list,
                    profile_md=profile_md,
                    assumptions_md=assumptions_md,
                )
                # cache_system=True — system prompt is identical for all items
                result = llm_client.call(system, user, max_tokens=512, cache_system=True)

                item["content_summary"] = result.get("summary", "")
                item["topic_matches"] = result.get("topic_matches", [])
                item["language"] = result.get("language", item.get("language", "en"))
                item.setdefault("metadata", {})["novelty_signal"] = result.get("novelty_signal", "")
                item["relevance_score"] = float(result.get("relevance_score", 0.0))
                item["leverage_score"] = float(result.get("leverage_score", 0.0))
                item["personal_fit_score"] = float(result.get("personal_fit_score", 0.0))
                item["why_it_matters"] = result.get("why_it_matters", "")
                item["recommended_action"] = result.get("recommended_action", "monitor")

            except Exception as exc:
                log.warning("Enricher failed for item id=%s: %s", item.get("id", "?"), exc)

            enriched.append(item)

    log.info("Enricher complete: %d items processed", len(enriched))
    return enriched
