"""
Loads all config/*.md files and exposes them as structured data.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import frontmatter
import yaml

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_md(filename: str) -> frontmatter.Post:
    path = CONFIG_DIR / filename
    return frontmatter.load(str(path))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def load_profile() -> dict[str, Any]:
    post = _load_md("profile.md")
    return {**post.metadata, "body": post.content}


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

def load_topics() -> dict[str, Any]:
    post = _load_md("topics.md")
    default_weight = post.metadata.get("default_weight", 2)

    topics: dict[str, Any] = {}
    current_topic: str | None = None
    current_data: dict[str, Any] = {}

    for line in post.content.splitlines():
        if line.startswith("## "):
            if current_topic:
                topics[current_topic] = current_data
            current_topic = line[3:].strip()
            current_data = {"weight": default_weight, "keywords": [], "exclude": []}
        elif line.startswith("weight:") and current_topic:
            current_data["weight"] = int(line.split(":", 1)[1].strip())
        elif line.startswith("keywords:") and current_topic:
            raw = line.split(":", 1)[1].strip()
            current_data["keywords"] = [k.strip() for k in re.split(r",\s*", raw) if k.strip()]
        elif line.startswith("  ") and current_topic and "keywords" in current_data:
            # continuation of keywords block (YAML multiline)
            current_data["keywords"].extend(
                k.strip() for k in re.split(r",\s*", line.strip()) if k.strip()
            )
        elif line.startswith("exclude:") and current_topic:
            raw = line.split(":", 1)[1].strip()
            current_data["exclude"] = [e.strip() for e in re.split(r",\s*", raw) if e.strip()]

    if current_topic:
        topics[current_topic] = current_data

    return topics


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def load_sources() -> dict[str, Any]:
    """Return the raw text of sources.md for now; callers parse what they need."""
    post = _load_md("sources.md")
    return {"raw": post.content, "metadata": post.metadata}


def load_rss_feeds() -> list[dict[str, str]]:
    post = _load_md("sources.md")
    feeds: list[dict[str, str]] = []
    in_rss_section = False
    in_feeds = False
    current_feed: dict[str, str] = {}

    for line in post.content.splitlines():
        if line.startswith("## RSS and Substack feeds"):
            in_rss_section = True
            continue
        if in_rss_section and line.startswith("## "):
            # Entered a different section — stop entirely
            break
        if not in_rss_section:
            continue
        if line.strip() == "feeds:":
            in_feeds = True
            continue
        if in_feeds:
            if re.match(r"^\S", line) and not line.startswith(" "):
                in_feeds = False
                if current_feed:
                    feeds.append(current_feed)
                    current_feed = {}
                continue
            stripped = line.strip()
            if stripped.startswith("- name:"):
                if current_feed:
                    feeds.append(current_feed)
                current_feed = {"name": stripped.split(":", 1)[1].strip()}
            elif stripped.startswith("url:"):
                current_feed["url"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("topic_weight_boost:"):
                current_feed["topic_weight_boost"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("language:"):
                current_feed["language"] = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# "):
                continue  # skip comments

    if current_feed:
        feeds.append(current_feed)

    return [f for f in feeds if "url" in f]


def load_reddit_config() -> dict[str, Any]:
    post = _load_md("sources.md")
    feeds: list[dict[str, Any]] = []
    in_reddit = False
    in_feeds = False
    current: dict[str, Any] = {}

    for line in post.content.splitlines():
        if line.startswith("## Reddit"):
            in_reddit = True
            in_feeds = False
            continue
        if in_reddit and line.startswith("## "):
            in_reddit = False
            if current:
                feeds.append(current)
                current = {}
            continue
        if not in_reddit:
            continue

        stripped = line.strip()
        if stripped == "feeds:":
            in_feeds = True
            continue
        if not in_feeds:
            continue

        if stripped.startswith("- name:"):
            if current:
                feeds.append(current)
            current = {"name": stripped.split(":", 1)[1].strip()}
        elif stripped.startswith("url:"):
            current["url"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("topic:"):
            current["topic"] = stripped.split(":", 1)[1].strip()

    if current:
        feeds.append(current)

    return {"feeds": [f for f in feeds if "url" in f]}


def load_github_config() -> list[dict[str, Any]]:
    post = _load_md("sources.md")
    watch: list[dict[str, Any]] = []
    in_github = False
    in_watch = False
    current: dict[str, Any] = {}

    for line in post.content.splitlines():
        if line.startswith("## GitHub"):
            in_github = True
            in_watch = False
            continue
        if in_github and line.startswith("## "):
            in_github = False
            if current:
                watch.append(current)
                current = {}
            continue
        if not in_github:
            continue

        stripped = line.strip()
        if stripped == "watch:":
            in_watch = True
            continue
        if not in_watch:
            continue

        if stripped.startswith("- org:"):
            if current:
                watch.append(current)
            current = {"org": stripped.split(":", 1)[1].strip(), "repos": [], "events": []}
        elif stripped.startswith("repos:"):
            raw = stripped.split(":", 1)[1].strip()
            if raw == "all":
                current["repos"] = "all"
            else:
                current["repos"] = [r.strip().strip("[]'\"") for r in raw.strip("[]").split(",")]
        elif stripped.startswith("events:"):
            raw = stripped.split(":", 1)[1].strip()
            current["events"] = [e.strip().strip("[]'\"") for e in raw.strip("[]").split(",")]
        elif stripped.startswith("topic_weight_boost:"):
            current["topic_weight_boost"] = stripped.split(":", 1)[1].strip()

    if current:
        watch.append(current)

    return watch


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def load_scoring() -> dict[str, Any]:
    post = _load_md("scoring.md")
    content = post.content

    scoring: dict[str, Any] = {
        "weights": {
            "relevance": 0.30,
            "leverage": 0.20,
            "urgency": 0.15,
            "novelty": 0.15,
            "source_trust": 0.10,
            "personal_fit": 0.10,
        },
        "trust_tiers": {},
        "penalties": {},
        "thresholds": {},
        "boosts": {},
    }

    # Trust tiers
    tier_pattern = re.compile(r"tier_(\d)\s*\(([0-9.]+)\):\s*(.+)")
    for match in tier_pattern.finditer(content):
        tier_num, score, names = match.groups()
        for name in names.split(","):
            scoring["trust_tiers"][name.strip()] = float(score)

    # Penalties
    penalty_pattern = re.compile(r"^(\w+):\s*(-[0-9.]+)", re.MULTILINE)
    for match in penalty_pattern.finditer(content):
        scoring["penalties"][match.group(1)] = float(match.group(2))

    # Thresholds
    threshold_pattern = re.compile(r"^(daily_briefing|weekly_briefing):\s*([0-9.]+)", re.MULTILINE)
    for match in threshold_pattern.finditer(content):
        scoring["thresholds"][match.group(1)] = float(match.group(2))

    # Boosts
    boost_pattern = re.compile(r"^(\w+):\s*(\+[0-9.]+)", re.MULTILINE)
    for match in boost_pattern.finditer(content):
        scoring["boosts"][match.group(1)] = float(match.group(2))

    return scoring


# ---------------------------------------------------------------------------
# Assumptions and output templates (raw text)
# ---------------------------------------------------------------------------

def load_assumptions() -> str:
    return _load_md("assumptions.md").content


def load_output_templates() -> str:
    return _load_md("output_templates.md").content


# ---------------------------------------------------------------------------
# All config bundled
# ---------------------------------------------------------------------------

def load_all() -> dict[str, Any]:
    return {
        "profile": load_profile(),
        "topics": load_topics(),
        "rss_feeds": load_rss_feeds(),
        "reddit": load_reddit_config(),
        "github": load_github_config(),
        "scoring": load_scoring(),
        "assumptions": load_assumptions(),
        "output_templates": load_output_templates(),
    }
