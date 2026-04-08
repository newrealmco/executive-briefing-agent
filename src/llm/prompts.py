"""
Prompt templates for the pipeline LLM calls.

Calls 1+2 are merged into a single combined call per item (enrich_and_score).
This halves API calls and avoids repeating the system prompt twice per item.
The static system prompt (profile + assumptions) is eligible for prompt caching.
"""
from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Combined Call 1+2: Summarize, classify, and score in one shot
# ---------------------------------------------------------------------------

def enrich_and_score(
    title: str,
    content_raw: str,
    source_name: str,
    trust_tier: int,
    topic_list: list[str],
    profile_md: str,
    assumptions_md: str,
) -> tuple[str, str]:
    """
    Single LLM call replacing the former separate summarize + score calls.
    Returns (system, user) tuple.
    The system prompt is static per run — use prompt caching on it.
    """
    topics_formatted = json.dumps(topic_list, ensure_ascii=False)

    # Truncate content — signal is almost always in the first 1500 chars
    content_truncated = content_raw[:1500].strip()

    system = f"""You are a personal intelligence analyst for Rami, a senior PM in AI/ML.

## Profile
{profile_md}

## Operating assumptions
{assumptions_md}

## Topics to classify against
{topics_formatted}

Your job: given a content item, return a single JSON object with all fields below.
Return ONLY valid JSON. No markdown fences. No commentary."""

    user = f"""Item:
Title: {title}
Source: {source_name} (trust tier {trust_tier})
Content: {content_truncated}

Return this JSON exactly:
{{
  "summary": "<2-3 sentences capturing the core point>",
  "topic_matches": ["<exact topic name from the list>"],
  "language": "<en or he>",
  "novelty_signal": "<breaking|incremental|repeat|background>",
  "relevance_score": <0.0-1.0>,
  "leverage_score": <0.0-1.0>,
  "personal_fit_score": <0.0-1.0>,
  "why_it_matters": "<1 sentence specific to Rami's context — never generic>",
  "recommended_action": "<read_now|skim|save_for_later|share|ignore|monitor>",
  "confidence": <0.0-1.0>
}}

Rules:
- topic_matches: only exact names from the topic list, only if genuinely applicable.
- why_it_matters: must reference JDD, consulting, career, or a current decision. Reject generic AI observations.
- novelty_signal: breaking=new release/announcement, incremental=follow-up, repeat=seen before, background=evergreen."""

    return system, user


# ---------------------------------------------------------------------------
# Call 3: Render briefing
# ---------------------------------------------------------------------------

def render_briefing(
    scored_items_json: str,
    output_template: str,
    name: str,
    threshold: float,
    max_items: int,
    mode: str,
) -> tuple[str, str]:
    system = """You are a precise personal briefing writer. Your job is to transform a list of scored and analyzed items into a clean, scannable briefing document.

Rules:
- Be direct and concise — the reader has under 10 minutes.
- Every item must include a recommended action.
- Group by topic clusters when multiple items share a theme.
- Lead with the highest-impact items.
- Do not add padding, preamble, or filler sentences.
- Output must follow the provided template exactly."""

    user = f"""Generate a {mode} briefing for {name}.

Threshold applied: {threshold} (all items below this were already filtered out)
Maximum items to include: {max_items}

Output template to follow:
{output_template}

Scored items (JSON):
{scored_items_json}

Generate the briefing now."""

    return system, user
