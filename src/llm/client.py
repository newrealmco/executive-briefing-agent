"""
Anthropic API client wrapper.
"""
from __future__ import annotations

import json
import os
import re

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from src.logger import get_logger

log = get_logger("llm.client")

_MODEL = "claude-sonnet-4-6"


def _get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call(system: str, user: str, max_tokens: int = 1024) -> dict:
    """Call Claude and parse the response as JSON."""
    client = _get_client()
    response = client.messages.create(
        model=_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw_text = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```[a-z]*\n?", "", raw_text)
        raw_text = re.sub(r"\n?```$", "", raw_text)
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        log.error("LLM returned non-JSON response: %s", raw_text[:500])
        raise ValueError(f"LLM response is not valid JSON: {raw_text[:200]}")


def call_batch(calls: list[tuple[str, str]], max_tokens: int = 1024) -> list[dict]:
    """Call `call()` sequentially for each (system, user) tuple."""
    results: list[dict] = []
    for idx, (system, user) in enumerate(calls):
        try:
            result = call(system, user, max_tokens=max_tokens)
            results.append(result)
        except Exception as exc:
            log.warning("call_batch item %d failed: %s", idx, exc)
            results.append({})
    return results
