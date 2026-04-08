"""
Gmail collector via Gmail API (OAuth2, read-only).

Required env vars:
  GMAIL_CLIENT_ID
  GMAIL_CLIENT_SECRET
  GMAIL_REFRESH_TOKEN

Returns normalized items for emails received in the last `lookback_hours`.
Applies priority logic from sources.md:
  - Emails FROM self → high priority boost
  - Recruiters from target companies → note in metadata
  - Automated/promotional email → deprioritized (lower trust score)
"""
from __future__ import annotations

import base64
import email
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.schema import empty_item, make_id, now_iso
from src.logger import get_logger

log = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TARGET_COMPANIES = {"meta", "anthropic", "openai", "google", "deepmind", "mistral", "cohere"}

AUTOMATED_PATTERNS = re.compile(
    r"no.?reply|noreply|notification|donotreply|automated|mailer|newsletter@",
    re.IGNORECASE,
)


def _build_service() -> Any:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _decode_body(msg: Any) -> str:
    payload = msg.get("payload", {})

    def _extract(part: dict) -> str:
        mime = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data", "")
        if mime == "text/plain" and body_data:
            return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        if mime == "text/html" and body_data:
            from bs4 import BeautifulSoup
            raw = base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
            return BeautifulSoup(raw, "html.parser").get_text(separator=" ", strip=True)
        for sub in part.get("parts", []):
            result = _extract(sub)
            if result:
                return result
        return ""

    return _extract(payload)


def _header(msg: Any, name: str) -> str:
    headers = msg.get("payload", {}).get("headers", [])
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _priority_signals(sender: str, recipient: str, own_email: str) -> dict[str, Any]:
    is_self = sender.lower().strip("<>").endswith(own_email.lower())
    is_automated = bool(AUTOMATED_PATTERNS.search(sender))
    company = next((c for c in TARGET_COMPANIES if c in sender.lower()), None)
    return {
        "is_self_email": is_self,
        "is_automated": is_automated,
        "target_company": company,
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _list_messages(service: Any, query: str, max_results: int) -> list[dict]:
    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    return result.get("messages", [])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get_message(service: Any, msg_id: str) -> dict:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()


def collect(lookback_hours: int = 24, max_results: int = 50) -> list[dict[str, Any]]:
    required = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        log.warning("Gmail credentials missing (%s) — skipping Gmail collector", missing)
        return []

    try:
        service = _build_service()
        own_email = service.users().getProfile(userId="me").execute().get("emailAddress", "")
    except Exception as exc:
        log.warning("Gmail auth failed: %s", exc)
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    after_ts = int(cutoff.timestamp())
    query = f"after:{after_ts} -in:spam -in:trash"

    log.info("Gmail fetch: query=%s", query)

    try:
        messages = _list_messages(service, query, max_results)
    except Exception as exc:
        log.warning("Gmail list failed: %s", exc)
        return []

    items: list[dict[str, Any]] = []

    for msg_ref in messages:
        try:
            msg = _get_message(service, msg_ref["id"])
        except Exception as exc:
            log.warning("Gmail get message failed [%s]: %s", msg_ref["id"], exc)
            continue

        subject = _header(msg, "Subject")
        sender = _header(msg, "From")
        recipient = _header(msg, "To")
        date_str = _header(msg, "Date")
        msg_id_header = _header(msg, "Message-ID")

        try:
            published_at = parsedate_to_datetime(date_str).isoformat() if date_str else now_iso()
        except Exception:
            published_at = now_iso()

        content_raw = _decode_body(msg)[:8000]
        signals = _priority_signals(sender, recipient, own_email)

        # Trust score based on signals
        if signals["is_self_email"]:
            tier, trust_score = 1, 1.0
        elif signals["target_company"]:
            tier, trust_score = 2, 0.8
        elif signals["is_automated"]:
            tier, trust_score = 5, 0.2
        else:
            tier, trust_score = 3, 0.6

        thread_id = msg.get("threadId", "")
        url = f"https://mail.google.com/mail/u/0/#inbox/{thread_id}"

        item = empty_item()
        item.update(
            {
                "id": make_id(url=msg_ref["id"]),
                "source": "gmail",
                "source_name": "Gmail",
                "source_trust_tier": tier,
                "source_trust_score": trust_score,
                "title": subject or "(no subject)",
                "url": url,
                "author": sender,
                "published_at": published_at,
                "content_raw": content_raw,
                "metadata": {
                    "gmail_id": msg_ref["id"],
                    "thread_id": thread_id,
                    "sender": sender,
                    "recipient": recipient,
                    **signals,
                },
            }
        )
        items.append(item)

    log.info("Gmail collector: %d items collected", len(items))
    return items
