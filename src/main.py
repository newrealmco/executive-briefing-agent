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
load_dotenv()

from src.config_loader import load_all
from src.logger import get_logger
from src.collectors import (
    rss_collector,
    reddit_collector,
    github_collector,
    gmail_collector,
    zoho_collector,
)

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

    # Phase 3+ (pipeline, scoring, rendering) — stubs for now
    log.info("Pipeline and rendering not yet implemented (Phase 3+)")
    log.info("Run with --mode collect to test collectors end-to-end")


if __name__ == "__main__":
    main()
