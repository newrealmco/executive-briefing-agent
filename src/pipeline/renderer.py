"""
Renderer — LLM Call 3.

Takes scored items and produces the final briefing text (markdown + HTML).
Saves the markdown to data/briefings/ and returns both formats for delivery.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from src.llm import client as llm_client
from src.llm import prompts
from src.logger import get_logger

log = get_logger(__name__)

BRIEFINGS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "briefings"
BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

# Limit items sent to renderer to keep prompt size reasonable
MAX_DAILY_ITEMS = 12
MAX_WEEKLY_ITEMS = 25


def _markdown_to_html(md: str) -> str:
    """Minimal markdown → HTML conversion for email delivery."""
    lines = md.splitlines()
    html_lines: list[str] = []
    in_list = False

    for line in lines:
        # Headings
        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        # Horizontal rule
        elif line.strip() == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
        # List item
        elif line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            content = _inline_md(line[2:])
            html_lines.append(f"<li>{content}</li>")
        # Empty line
        elif line.strip() == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
        # Normal paragraph
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{_inline_md(line)}</p>")

    if in_list:
        html_lines.append("</ul>")

    body = "\n".join(html_lines)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 700px; margin: 40px auto; color: #1a1a1a; line-height: 1.6; }}
  h1 {{ font-size: 1.4em; border-bottom: 2px solid #1a1a1a; padding-bottom: 6px; }}
  h2 {{ font-size: 1.2em; margin-top: 28px; }}
  h3 {{ font-size: 1.05em; margin-top: 20px; color: #333; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 6px; }}
  p {{ margin: 8px 0; }}
  a {{ color: #0066cc; }}
  strong {{ font-weight: 600; }}
  code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 3px; font-size: 0.9em; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _inline_md(text: str) -> str:
    """Convert inline markdown (bold, links, code) to HTML."""
    # Bold: **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Code: `text`
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    # Links: [text](url)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def _extract_subject(briefing_text: str, mode: str, today: str) -> str:
    """Pull the subject line from the briefing if the LLM included it, else generate one."""
    for line in briefing_text.splitlines():
        if line.lower().startswith("subject:"):
            return line.split(":", 1)[1].strip()
    if mode == "daily":
        return f"Briefing — {today}"
    return f"Weekly briefing — week of {today}"


def render(items: list[dict[str, Any]], cfg: dict, mode: str) -> tuple[str, str, str]:
    """
    Run LLM Call 3 and produce the briefing.

    Returns:
        (subject, markdown_text, html_text)
    """
    today = date.today().isoformat()
    max_items = MAX_DAILY_ITEMS if mode == "daily" else MAX_WEEKLY_ITEMS

    # Take top N by score
    top_items = sorted(items, key=lambda x: x["final_score"], reverse=True)[:max_items]

    # Slim down payload — only fields the renderer needs
    slim = [
        {
            "title": i["title"],
            "source": i["source_name"],
            "url": i["url"],
            "score": round(i["final_score"], 3),
            "topics": i["topic_matches"],
            "summary": i["content_summary"] or i["content_raw"][:300],
            "why_it_matters": i["why_it_matters"],
            "action": i["recommended_action"],
            "published_at": i["published_at"],
        }
        for i in top_items
    ]

    scored_items_json = json.dumps(slim, indent=2, ensure_ascii=False)
    threshold = cfg["scoring"]["thresholds"].get(f"{mode}_briefing", 0.55)

    # Select the right template section
    templates = cfg["output_templates"]
    if mode == "daily":
        template_section = templates.split("## Weekly briefing structure")[0].strip()
    else:
        weekly_start = templates.find("## Weekly briefing structure")
        template_section = templates[weekly_start:].strip() if weekly_start >= 0 else templates

    profile = cfg["profile"]
    name = profile.get("name", "Rami")

    system, user = prompts.render_briefing(
        scored_items_json=scored_items_json,
        output_template=template_section,
        name=name,
        threshold=threshold,
        max_items=max_items,
        mode=mode,
    )

    log.info("Renderer: calling LLM with %d items (mode=%s)", len(slim), mode)

    try:
        # Call 3 returns plain text, not JSON — use the raw API directly
        import anthropic, os
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        briefing_md = response.content[0].text.strip()
    except Exception as exc:
        log.error("Renderer LLM call failed: %s", exc)
        # Fallback: plain text concatenation
        briefing_md = _fallback_briefing(top_items, mode, today)

    subject = _extract_subject(briefing_md, mode, today)
    html = _markdown_to_html(briefing_md)

    # Save markdown to disk
    filename = f"{today}-{mode}.md"
    out_path = BRIEFINGS_DIR / filename
    out_path.write_text(briefing_md, encoding="utf-8")
    log.info("Briefing saved to %s", out_path)

    return subject, briefing_md, html


def _fallback_briefing(items: list[dict], mode: str, today: str) -> str:
    """Plain-text fallback if LLM rendering fails."""
    lines = [f"# Briefing — {today}", ""]
    for item in items:
        lines.append(f"**{item['title']}** — {item['source_name']}")
        lines.append(f"Why it matters: {item['why_it_matters']}")
        lines.append(f"Action: {item['recommended_action']}")
        lines.append(f"Link: {item['url']}")
        lines.append("")
    return "\n".join(lines)
