"""
Tests for Phase 1: config loading.
Run from project root: python -m pytest tests/ -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import (
    load_profile,
    load_topics,
    load_rss_feeds,
    load_reddit_config,
    load_github_config,
    load_scoring,
    load_assumptions,
    load_all,
)


def test_profile_loads():
    p = load_profile()
    assert p["name"] == "Rami"
    assert p["timezone"] == "Asia/Jerusalem"


def test_topics_loads():
    t = load_topics()
    assert len(t) >= 5
    # All topics should have a weight and keywords
    for name, data in t.items():
        assert "weight" in data, f"topic '{name}' missing weight"
        assert "keywords" in data, f"topic '{name}' missing keywords"


def test_rss_feeds_loads():
    feeds = load_rss_feeds()
    assert len(feeds) >= 10
    for f in feeds:
        assert "url" in f, f"feed missing url: {f}"
        assert "name" in f, f"feed missing name: {f}"


def test_reddit_config_loads():
    cfg = load_reddit_config()
    assert "feeds" in cfg
    assert len(cfg["feeds"]) >= 5
    for f in cfg["feeds"]:
        assert "url" in f
        assert "name" in f


def test_github_config_loads():
    cfg = load_github_config()
    assert len(cfg) >= 5
    for entry in cfg:
        assert "org" in entry
        assert "repos" in entry


def test_scoring_loads():
    s = load_scoring()
    weights = s["weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.01, f"weights must sum to 1.0, got {total}"
    assert s["thresholds"]["daily_briefing"] == 0.55
    assert s["thresholds"]["weekly_briefing"] == 0.45


def test_assumptions_loads():
    a = load_assumptions()
    assert len(a) > 100  # non-trivial content


def test_load_all():
    cfg = load_all()
    keys = ["profile", "topics", "rss_feeds", "reddit", "github", "scoring", "assumptions", "output_templates"]
    for k in keys:
        assert k in cfg, f"load_all missing key: {k}"
