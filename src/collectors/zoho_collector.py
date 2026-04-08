"""
Zoho Mail collector via IMAP (read-only).

Required env vars:
  ZOHO_EMAIL         — your @newrealm.co address
  ZOHO_IMAP_PASSWORD — app-specific password from Zoho Mail settings

Zoho IMAP server: imap.zoho.com, port 993, SSL.

Priority logic:
  - Any direct human-written email is high priority
  - Contact form / inbound JDD consulting interest
  - Automated platform notifications → deprioritize
"""
from __future__ import annotations

import email
import imaplib
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.schema import empty_item, make_id, now_iso
from src.logger import get_logger

log = get_logger(__name__)

IMAP_HOST = "imap.zoho.com"
IMAP_PORT = 993

AUTOMATED_PATTERNS = re.compile(
    r"no.?reply|noreply|notification|donotreply|automated|mailer-daemon",
    re.IGNORECASE,
)

JDD_SIGNALS = re.compile(
    r"jdd|judgment.driven|newrealm|consulting|book|speaking|collaboration",
    re.IGNORECASE,
)


def _strip_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


def _decode_payload(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass
            if ct == "text/html":
                try:
                    raw = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    return _strip_html(raw)
                except Exception:
                    pass
        return ""
    else:
        try:
            payload = msg.get_payload(decode=True)
            raw = payload.decode("utf-8", errors="replace") if payload else ""
            if msg.get_content_type() == "text/html":
                return _strip_html(raw)
            return raw
        except Exception:
            return ""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _imap_connect(username: str, password: str) -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(username, password)
    return conn


def collect(lookback_hours: int = 24, max_results: int = 50) -> list[dict[str, Any]]:
    zoho_email = os.environ.get("ZOHO_EMAIL")
    zoho_password = os.environ.get("ZOHO_IMAP_PASSWORD")

    if not zoho_email or not zoho_password:
        log.warning("Zoho credentials missing — skipping Zoho collector")
        return []

    try:
        conn = _imap_connect(zoho_email, zoho_password)
    except Exception as exc:
        log.warning("Zoho IMAP connect failed: %s", exc)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    since_str = cutoff.strftime("%d-%b-%Y")

    items: list[dict[str, Any]] = []

    try:
        conn.select("INBOX")
        _, data = conn.search(None, f'(SINCE "{since_str}")')
        msg_ids = data[0].split() if data[0] else []
        log.info("Zoho IMAP: %d messages found since %s", len(msg_ids), since_str)

        # Fetch newest first, limit to max_results
        for msg_id in reversed(msg_ids[-max_results:]):
            try:
                _, msg_data = conn.fetch(msg_id, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
            except Exception as exc:
                log.warning("Zoho fetch msg %s failed: %s", msg_id, exc)
                continue

            subject = msg.get("Subject", "(no subject)")
            sender = msg.get("From", "")
            date_str = msg.get("Date", "")

            # Skip briefing emails sent by this system
            if "updates.newrealm.co" in sender:
                continue

            try:
                published_at = parsedate_to_datetime(date_str).isoformat() if date_str else now_iso()
            except Exception:
                published_at = now_iso()

            content_raw = _decode_payload(msg)[:8000]
            is_automated = bool(AUTOMATED_PATTERNS.search(sender))
            has_jdd_signal = bool(JDD_SIGNALS.search(subject + " " + content_raw[:500]))

            if is_automated:
                tier, trust_score = 5, 0.2
            elif has_jdd_signal:
                tier, trust_score = 1, 1.0
            else:
                tier, trust_score = 3, 0.6

            unique_key = f"zoho:{zoho_email}:{msg_id.decode()}"
            item = empty_item()
            item.update(
                {
                    "id": make_id(content=unique_key),
                    "source": "zoho",
                    "source_name": "Zoho Mail (newrealm.co)",
                    "source_trust_tier": tier,
                    "source_trust_score": trust_score,
                    "title": subject,
                    "url": "",
                    "author": sender,
                    "published_at": published_at,
                    "content_raw": content_raw,
                    "metadata": {
                        "imap_id": msg_id.decode(),
                        "sender": sender,
                        "is_automated": is_automated,
                        "has_jdd_signal": has_jdd_signal,
                    },
                }
            )
            items.append(item)

    finally:
        try:
            conn.logout()
        except Exception:
            pass

    log.info("Zoho collector: %d items collected", len(items))
    return items
