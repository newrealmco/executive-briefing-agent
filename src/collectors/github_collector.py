"""
GitHub collector via PyGitHub.

Watches releases and (where possible) new repos for configured orgs.
Auth: GITHUB_TOKEN env var (read:public_repo PAT).
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from github import Github, GithubException
from tenacity import retry, stop_after_attempt, wait_exponential

from src.collectors.schema import empty_item, make_id
from src.logger import get_logger

log = get_logger(__name__)

LOOKBACK_HOURS = 24


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cutoff() -> datetime:
    return _now() - timedelta(hours=LOOKBACK_HOURS)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get_latest_release(repo: Any) -> Any | None:
    try:
        return repo.get_latest_release()
    except GithubException:
        return None


def _collect_releases(gh: Github, org_name: str, repo_names: list[str] | str, topic_boost: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    cutoff = _cutoff()

    try:
        org = gh.get_organization(org_name)
    except GithubException as exc:
        log.warning("GitHub org not found [%s]: %s", org_name, exc)
        return []

    if repo_names == "all":
        try:
            repos = list(org.get_repos(type="public"))
        except GithubException as exc:
            log.warning("Could not list repos for [%s]: %s", org_name, exc)
            return []
    else:
        repos = []
        for rname in repo_names:
            try:
                repos.append(gh.get_repo(f"{org_name}/{rname}"))
            except GithubException as exc:
                log.warning("Repo not found [%s/%s]: %s", org_name, rname, exc)

    for repo in repos:
        release = _get_latest_release(repo)
        if not release:
            continue

        published_at = release.published_at
        if published_at is None:
            continue
        if published_at.replace(tzinfo=timezone.utc) < cutoff:
            continue

        title = f"{repo.full_name} — {release.tag_name}"
        url = release.html_url
        body = (release.body or "")[:8000]

        item = empty_item()
        item.update(
            {
                "id": make_id(url=url),
                "source": "github",
                "source_name": f"GitHub/{org_name}",
                "source_trust_tier": 2,
                "source_trust_score": 0.8,
                "title": title,
                "url": url,
                "author": release.author.login if release.author else org_name,
                "published_at": published_at.replace(tzinfo=timezone.utc).isoformat(),
                "content_raw": body,
                "metadata": {
                    "org": org_name,
                    "repo": repo.name,
                    "tag": release.tag_name,
                    "event": "release",
                    "topic_weight_boost": topic_boost,
                    "stars": repo.stargazers_count,
                },
            }
        )
        items.append(item)

    return items


def collect(github_cfg: list[dict[str, Any]]) -> list[dict[str, Any]]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.warning("GITHUB_TOKEN not set — skipping GitHub collector")
        return []

    gh = Github(token)
    all_items: list[dict[str, Any]] = []

    for watch in github_cfg:
        org_name: str = watch["org"]
        repo_names = watch.get("repos", "all")
        events: list[str] = watch.get("events", ["release"])
        topic_boost: str = watch.get("topic_weight_boost", "")

        log.info("GitHub fetch: %s repos=%s events=%s", org_name, repo_names, events)

        if "release" in events:
            all_items.extend(_collect_releases(gh, org_name, repo_names, topic_boost))

    log.info("GitHub collector: %d items collected", len(all_items))
    return all_items
