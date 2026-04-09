# Contributing

Thank you for your interest in contributing. This project welcomes bug reports, new source collector proposals, and pull requests.

---

## Reporting bugs

1. **Search existing issues first** — check [GitHub Issues](https://github.com/newrealmco/personal-briefing-agent/issues) to see if the bug has already been reported.

2. **Open a new issue** with the following information:
   - What you expected to happen
   - What actually happened (error message or incorrect behavior)
   - Reproduction steps (minimal example if possible)
   - Your Python version and OS
   - Relevant log output from `data/briefing.log` or the GitHub Actions run

3. **Sanitize before sharing** — never include API keys, email content, or personal data in issue reports. Mask secrets with `****` and replace real email content with `[redacted]`.

---

## Suggesting new source collectors

The project currently supports: Gmail, Zoho Mail, RSS/Atom, Reddit (public RSS), and GitHub releases.

To suggest a new source (e.g. LinkedIn, Slack, HackerNews, Twitter/X, Bluesky):

1. Open an issue with the label `new-collector`
2. Include:
   - **Source name and URL**
   - **What data it provides** and why it's useful for a personal briefing
   - **Auth model** — public API, OAuth, API key, or scraping
   - **Rate limits or ToS constraints** you're aware of
   - **Whether you're willing to implement it** (not required — proposals without a PR are still welcome)

New collectors should live in `src/collectors/` and return a list of items in the normalized schema defined in `src/collectors/schema.py`. Each collector must be independently testable with `--mode collect`.

---

## Submitting a pull request

### Before you start

- For non-trivial changes, open an issue first to discuss the approach.
- The `config/` layer is intentionally separate from `src/` — all personal behavior should be configurable via config files, not hardcoded in source.

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/personal-briefing-agent.git
cd personal-briefing-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your credentials for local testing.

### Guidelines

- **One concern per PR** — keep changes focused. A PR that adds a new collector and refactors the scorer is harder to review and harder to revert.
- **No personal data in `src/`** — all persona-specific behavior belongs in `config/`. The engine must remain generic.
- **Match the existing code style** — type hints, module-level loggers via `get_logger()`, `from __future__ import annotations` at the top of each file.
- **Test your collector** — run `PYTHONPATH=. python src/main.py --mode collect` and confirm your new source appears in `data/raw/`.
- **Update `requirements.txt`** if you add a dependency. Pin to a minimum version (`>=`) rather than an exact version.
- **Do not commit** `.env`, `credentials.json`, `token.json`, `data/`, or `config/profile.md`.

### PR checklist

- [ ] `PYTHONPATH=. python src/main.py --mode collect` runs without errors
- [ ] New collector returns items matching the normalized schema
- [ ] No secrets or personal data in any committed file
- [ ] `requirements.txt` updated if new dependencies added
- [ ] PR description explains what changed and why
