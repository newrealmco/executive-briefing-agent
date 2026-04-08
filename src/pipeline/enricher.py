"""
LLM Call 1: summarize and classify each item.
"""
from __future__ import annotations

from src.llm import client as llm_client
from src.llm import prompts
from src.logger import get_logger

log = get_logger("pipeline.enricher")

_BATCH_SIZE = 10


def enrich(items: list[dict], cfg: dict) -> list[dict]:
    """Summarize and classify items using LLM Call 1.

    cfg must contain cfg["topics"] (dict of topic_name -> topic_data).
    """
    topic_list: list[str] = list(cfg.get("topics", {}).keys())

    enriched: list[dict] = []
    total = len(items)

    for batch_start in range(0, total, _BATCH_SIZE):
        batch = items[batch_start : batch_start + _BATCH_SIZE]
        batch_num = batch_start // _BATCH_SIZE + 1
        log.info(
            "Enricher batch %d: processing items %d–%d of %d",
            batch_num,
            batch_start + 1,
            min(batch_start + _BATCH_SIZE, total),
            total,
        )

        for item in batch:
            if not item.get("content_raw"):
                enriched.append(item)
                continue

            try:
                system, user = prompts.summarize_and_classify(
                    item["content_raw"], topic_list
                )
                result = llm_client.call(system, user)

                item["content_summary"] = result.get("summary", item.get("content_summary", ""))
                item["topic_matches"] = result.get("topic_matches", item.get("topic_matches", []))
                item["language"] = result.get("language", item.get("language", "en"))
                if "metadata" not in item or not isinstance(item["metadata"], dict):
                    item["metadata"] = {}
                item["metadata"]["novelty_signal"] = result.get("novelty_signal", "")

            except Exception as exc:
                log.warning(
                    "Enricher failed for item id=%s: %s", item.get("id", "?"), exc
                )

            enriched.append(item)

    log.info("Enricher complete: %d items processed", len(enriched))
    return enriched
