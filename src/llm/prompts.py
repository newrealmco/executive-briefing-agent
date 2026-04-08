"""
Prompt templates for the three LLM calls in the pipeline.
"""
from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Call 1: Summarize and classify
# ---------------------------------------------------------------------------

def summarize_and_classify(
    content_raw: str,
    topic_list: list[str],
) -> tuple[str, str]:
    system = (
        "You are a precise research assistant. "
        "Your job is to extract the essential content from a piece of text "
        "and classify it against a set of topics."
    )

    topics_formatted = json.dumps(topic_list, ensure_ascii=False)

    user = f"""Analyze the following content and return a JSON object with these exact fields:

{{
  "summary": "<2-4 sentence summary of the core content>",
  "topic_matches": ["<topic name from the list that clearly matches>", ...],
  "language": "<ISO 639-1 language code, e.g. 'en' or 'he'>",
  "novelty_signal": "<one of: 'breaking', 'incremental', 'repeat', 'background'>"
}}

Rules:
- Only include topic_matches that genuinely apply — no guessing.
- topic_matches must be exact names from the provided topic list.
- If no topics match, return an empty list.
- novelty_signal: 'breaking' = new announcement or release; 'incremental' = follow-up or update; 'repeat' = seen before; 'background' = evergreen/reference.
- Return ONLY the JSON object, no markdown fences, no extra text.

Topic list:
{topics_formatted}

Content:
{content_raw}"""

    return system, user


# ---------------------------------------------------------------------------
# Call 2: Score and explain
# ---------------------------------------------------------------------------

def score_and_explain(
    title: str,
    summary: str,
    topic_matches: list[str],
    source_name: str,
    trust_tier: int,
    profile_md: str,
    priorities: str,
    assumptions_md: str,
) -> tuple[str, str]:
    system = f"""You are a personal intelligence analyst for a senior product manager named Rami.

Your job is to evaluate each piece of content against Rami's priorities, profile, and operating assumptions, and produce structured scores with clear reasoning.

## Rami's profile
{profile_md}

## Current priorities
{priorities}

## Operating assumptions
{assumptions_md}

Scoring dimensions (all 0.0–1.0):
- relevance_score: How directly does this align with declared topics and current priorities?
- leverage_score: Potential impact on JDD book, consulting pipeline, career positioning, or current decisions.
- personal_fit_score: Direct connection to active projects — JDD book, newrealm.co, Meta process, consulting.
- confidence: How confident are you in these scores given the available content? (0.0–1.0)

Return ONLY a JSON object, no markdown, no extra commentary."""

    topics_formatted = json.dumps(topic_matches, ensure_ascii=False)

    user = f"""Evaluate this item and return a JSON object with these exact fields:

{{
  "relevance_score": <0.0–1.0>,
  "leverage_score": <0.0–1.0>,
  "personal_fit_score": <0.0–1.0>,
  "why_it_matters": "<1-2 sentences: why this is or isn't important for Rami right now>",
  "recommended_action": "<one of: read_now, skim, save_for_later, share, ignore, monitor>",
  "confidence": <0.0–1.0>
}}

Item details:
- Title: {title}
- Source: {source_name} (trust tier {trust_tier})
- Topic matches: {topics_formatted}
- Summary: {summary}"""

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
