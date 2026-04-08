"""
SQLite-backed deduplication store.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import sqlite_utils

from src.logger import get_logger

log = get_logger("storage.store")

DB_PATH = Path(__file__).parent.parent.parent / "data" / "store.db"


def _db() -> sqlite_utils.Database:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite_utils.Database(DB_PATH)
    if "seen_items" not in db.table_names():
        db["seen_items"].create(
            {
                "id": str,
                "source": str,
                "title": str,
                "first_seen_at": str,
                "score": float,
            },
            pk="id",
        )
    return db


def is_duplicate(item_id: str, lookback_days: int = 7) -> bool:
    """Return True if item was seen within lookback_days."""
    db = _db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()
    rows = list(
        db["seen_items"].rows_where(
            "id = ? AND first_seen_at >= ?", [item_id, cutoff]
        )
    )
    return len(rows) > 0


def mark_seen(item: dict) -> None:
    """Insert item into seen_items (upsert on id)."""
    db = _db()
    db["seen_items"].upsert(
        {
            "id": item.get("id", ""),
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "first_seen_at": datetime.now(timezone.utc).isoformat(),
            "score": item.get("final_score", 0.0),
        },
        pk="id",
    )


def prune(older_than_days: int = 30) -> None:
    """Delete rows older than N days."""
    db = _db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
    deleted = db["seen_items"].delete_where("first_seen_at < ?", [cutoff])
    log.info("Pruned seen_items older than %d days (cutoff=%s)", older_than_days, cutoff)
