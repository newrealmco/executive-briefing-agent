"""
Entry point for the personal briefing agent.

Usage:
  python src/main.py --mode daily
  python src/main.py --mode weekly
  python src/main.py --mode collect   # collect only, no LLM, for testing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present (local dev only — GitHub Actions uses secrets)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_ROOT / ".env", override=True)

from src.config_loader import load_all
from src.logger import get_logger
from src.collectors import (
    rss_collector,
    reddit_collector,
    github_collector,
    gmail_collector,
    zoho_collector,
)
from src.storage.store import is_duplicate, mark_seen, prune
from src.pipeline.normalizer import normalize
from src.pipeline.pre_filter import pre_filter
from src.pipeline.enricher import enrich
from src.pipeline.scorer import score
from src.pipeline.clusterer import cluster
from src.pipeline.renderer import render
from src.delivery.email_sender import send

log = get_logger("main")

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def run_collectors(cfg: dict) -> list[dict]:
    log.info("=== Starting collectors ===")
    items: list[dict] = []

    items += rss_collector.collect(cfg["rss_feeds"])
    items += reddit_collector.collect(cfg["reddit"])
    items += github_collector.collect(cfg["github"])
    items += gmail_collector.collect()
    items += zoho_collector.collect()

    log.info("=== Total raw items collected: %d ===", len(items))
    return items


def save_raw(items: list[dict], mode: str) -> Path:
    today = date.today().isoformat()
    out = RAW_DIR / f"{today}-{mode}-raw.json"
    with open(out, "w") as f:
        json.dump(items, f, indent=2, default=str)
    log.info("Raw items saved to %s", out)
    return out


def run_pipeline(items: list[dict], cfg: dict, mode: str) -> list[dict]:
    # 1. Normalize
    items = normalize(items)

    # 2. Keyword pre-filter (no LLM — eliminates irrelevant items before any API call)
    candidates = pre_filter(items, cfg["topics"])

    # 3. Deduplicate
    prune()
    fresh = [i for i in candidates if not is_duplicate(i["id"])]
    log.info("After dedup: %d/%d candidates fresh", len(fresh), len(candidates))

    # 4. Enrich + Score (single combined LLM call per item, with prompt caching)
    enriched = enrich(fresh, cfg)
    scored = score(enriched, cfg)

    # 5. Filter by threshold
    threshold = cfg["scoring"]["thresholds"].get(f"{mode}_briefing", 0.55)
    above = [i for i in scored if i["final_score"] >= threshold]
    log.info("Above threshold (%.2f): %d items", threshold, len(above))

    # 6. Mark all scored items as seen
    for item in scored:
        mark_seen(item)

    return above


def main() -> None:
    parser = argparse.ArgumentParser(description="Personal Briefing Agent")
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "collect"],
        default="daily",
        help="Run mode",
    )
    args = parser.parse_args()

    log.info("Briefing agent starting — mode=%s", args.mode)

    cfg = load_all()
    log.info("Config loaded: %d topics, %d RSS feeds", len(cfg["topics"]), len(cfg["rss_feeds"]))

    items = run_collectors(cfg)
    save_raw(items, args.mode)

    if args.mode == "collect":
        log.info("Collect-only mode — done.")
        return

    above_threshold = run_pipeline(items, cfg, args.mode)
    log.info("Pipeline complete — %d items ready for rendering", len(above_threshold))

    scored_path = DATA_DIR / "scored" / f"{date.today().isoformat()}-{args.mode}-scored.json"
    scored_path.parent.mkdir(exist_ok=True)
    with open(scored_path, "w") as f:
        json.dump(above_threshold, f, indent=2, default=str)
    log.info("Scored items saved to %s", scored_path)

    # Phase 4: Render and deliver
    if not above_threshold:
        log.info("No items above threshold — skipping render and delivery")
        return

    subject, briefing_md, briefing_html = render(above_threshold, cfg, args.mode)
    log.info("Briefing rendered: %d chars", len(briefing_md))

    delivered = send(subject=subject, html_body=briefing_html, text_body=briefing_md)
    if delivered:
        log.info("=== Briefing delivered successfully ===")
    else:
        log.warning("=== Email delivery failed — briefing saved to disk only ===")


if __name__ == "__main__":
    main()
