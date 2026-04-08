"""
Email delivery via Resend.

Required env vars:
  RESEND_API_KEY   — from resend.com dashboard
  RECIPIENT_EMAIL  — one address or comma-separated list (e.g. a@x.com,b@x.com)

Sends HTML with a plain-text fallback.
"""
from __future__ import annotations

import os
from typing import Any

import resend
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logger import get_logger

log = get_logger(__name__)

FROM_ADDRESS = "briefing@updates.newrealm.co"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _send(params: dict[str, Any]) -> Any:
    return resend.Emails.send(params)


def send(subject: str, html_body: str, text_body: str = "") -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    recipient = os.environ.get("RECIPIENT_EMAIL")

    if not api_key or not recipient:
        log.warning("Email delivery skipped — RESEND_API_KEY or RECIPIENT_EMAIL not set")
        return False

    recipients = [r.strip() for r in recipient.split(",") if r.strip()]
    resend.api_key = api_key

    params: dict[str, Any] = {
        "from": FROM_ADDRESS,
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }
    if text_body:
        params["text"] = text_body

    try:
        response = _send(params)
        log.info("Email sent — id=%s to=%s subject=%r", response.get("id"), recipients, subject)
        return True
    except Exception as exc:
        log.error("Email delivery failed: %s", exc)
        return False
