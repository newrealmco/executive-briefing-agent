# Personal Executive Briefing Agent

A scheduled Python agent that collects signals from Gmail, Zoho Mail, RSS/Substack, Reddit, and GitHub, scores them against your personal profile, and delivers a daily HTML email briefing each morning.

This is not a summarizer. It is a **judgment support system**. Every surfaced item answers four questions:

1. What is it?
2. Why does it matter to *you specifically*?
3. What is the TL;DR?
4. What should you do with it?

> **Screenshot / example output** — see [`examples/example-daily.md`](examples/example-daily.md)

---

## How it works

```
Sources                Pipeline                   Delivery
──────                 ────────                   ────────
Gmail        ──┐
Zoho Mail    ──┤  normalize → pre-filter   ┐
RSS/Substack ──┤  → dedup → enrich+score   ├─→ render → email (Resend)
Reddit RSS   ──┤  → diversity caps         ┘       ↓
GitHub       ──┘                              data/briefings/
```

**Key design decisions:**

- **Pre-filter before LLM**: keyword heuristic eliminates irrelevant items before any API call (~90% token reduction)
- **Merged LLM calls**: a single combined call per item does both enrichment and scoring (with prompt caching)
- **Formula-only final score**: the LLM produces dimension scores; the formula applies weights and boosts
- **Diversity caps**: no single source > 40% of items, no single topic > 35% — prevents any one signal type from flooding the briefing
- **7-day dedup store**: SQLite-backed, persisted across GitHub Actions runs via cache

---

## Repository structure

```
personal-briefing-agent/
├── .github/workflows/
│   ├── daily-briefing.yml      # runs daily at 03:00 UTC
│   └── weekly-briefing.yml     # runs Sundays at 04:00 UTC
├── config/
│   ├── profile.md              # your identity, priorities, constraints — edit this first
│   ├── topics.md               # topics you track, weights, keywords
│   ├── sources.md              # RSS feeds, Reddit subs, GitHub orgs, email accounts
│   ├── scoring.md              # scoring formula, thresholds, boosts
│   ├── assumptions.md          # evaluation lens the LLM applies
│   └── output_templates.md     # daily and weekly briefing structure
├── src/
│   ├── collectors/             # gmail, zoho, rss, reddit, github collectors
│   ├── pipeline/               # normalizer, pre_filter, enricher, scorer, clusterer, renderer
│   ├── llm/                    # anthropic client + prompt templates
│   ├── delivery/               # resend email sender
│   ├── storage/                # sqlite dedup store
│   └── main.py
├── scripts/
│   └── gmail_auth.py           # one-time OAuth flow to capture Gmail refresh token
├── data/
│   ├── raw/                    # collected items (JSON, per run)
│   ├── scored/                 # scored items above threshold (JSON, per run)
│   └── briefings/             # rendered briefings (Markdown, per run)
├── tests/
└── requirements.txt
```

---

## Cost

Approximately **$0.25 per daily run** at current Claude Sonnet pricing (~$7/month).  
Resend free tier covers 3,000 emails/month. GitHub Actions free tier is sufficient for two scheduled workflows.  
Total cost for personal use: roughly **$7–9/month** in API costs only.

---

## Setup guide

### Prerequisites

- Python 3.11+
- A GitHub account (for Actions)
- An Anthropic API key
- A Resend account (free tier is sufficient) with a verified sending domain
- A Gmail account (for collection and/or delivery)
- Optionally: a Zoho Mail account, a custom domain

---

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/personal-briefing-agent.git
cd personal-briefing-agent
pip install -r requirements.txt
```

---

### 2. Personalize config files

Edit these four files. No code changes needed.

#### `config/profile.md`

Replace all fields with your own information:

```markdown
---
name: Your Name
role: Your Role
timezone: Your/Timezone          # e.g. America/New_York, Europe/London
briefing_time: "07:00"
language_primary: English
language_secondary: ""           # leave blank or add a second language
briefing_style: direct, concise, decision-oriented
summary_depth: medium
---

## Current priorities
- [Your top priority]
- [Your second priority]
- ...

## Constraints
- [Your time or attention constraints]

## Evaluation lens
When deciding if something matters, ask:
- [Question 1 specific to your work]
- [Question 2]
```

#### `config/topics.md`

Define 4–10 topics you want to track. Each topic has a weight (1–5), keywords, and exclusions:

```markdown
---
default_weight: 2
---

## Your Topic Name
weight: 5
keywords: keyword1, keyword2, keyword3
exclude: what to filter out
```

Higher weight = higher priority in scoring. Set weights relative to each other — if everything is 5, nothing stands out.

#### `config/sources.md`

Add your RSS feeds, Reddit subreddits (as public RSS URLs), and GitHub orgs to watch. The format:

```markdown
## RSS and Substack feeds
feeds:
  - name: Source Name
    url: https://example.com/feed
    topic_weight_boost: your_topic_key

## Reddit
feeds:
  - name: SubredditName
    url: https://www.reddit.com/r/SubredditName/top.rss?t=day
    topic: your_topic_key

## GitHub
watch:
  - org: org-name
    repos: [repo1, repo2]   # or: all
    events: [release, new_repo]
```

Reddit RSS feeds require no authentication. Use `.rss` URLs directly — Reddit's public API is fetched with a browser User-Agent.

#### `config/assumptions.md`

Write your own evaluation lens here. This text is injected into the LLM system prompt as the "judgment calibration" for why-it-matters generation. Be specific about what matters vs. what is noise for your role.

---

### 3. Set up Gmail (OAuth2)

Gmail requires a one-time local OAuth flow. You need Google Cloud credentials.

**Step 1: Create a Google Cloud project**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Enable the **Gmail API** under *APIs & Services → Library*
4. Go to *APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID*
5. Application type: **Desktop app**
6. Download the JSON file — save it as `credentials.json` in the project root

**Step 2: Run the auth script**

```bash
python scripts/gmail_auth.py
```

This opens a browser window for OAuth consent. After approval, it prints your `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `GMAIL_REFRESH_TOKEN`. Copy these — you'll add them as secrets.

> The refresh token does not expire unless revoked. You only need to do this once.

---

### 4. Set up Zoho Mail (IMAP)

If you have a Zoho Mail account:

1. In Zoho Mail → Settings → Mail Accounts → select your account → IMAP Access → Enable
2. Generate an App Password: Settings → Security → App Passwords
3. Note your full email address and the app password

If you don't use Zoho, the Zoho collector will silently skip with a warning if `ZOHO_EMAIL`/`ZOHO_IMAP_PASSWORD` are not set.

---

### 5. Set up Resend (email delivery)

1. Sign up at [resend.com](https://resend.com)
2. Add and verify your sending domain under *Domains*
   - If your root domain (`example.com`) already has MX records (e.g. for email hosting), add a **subdomain** instead: `updates.example.com`
   - Add the DNS records Resend shows you (TXT for SPF, CNAME for DKIM, CNAME for tracking)
3. Create an API key with **Full Access** under *API Keys*
4. Set `FROM_ADDRESS` in `src/pipeline/renderer.py` and `src/delivery/email_sender.py` to `briefing@your-verified-domain.com`

---

### 6. Set up a GitHub PAT (for GitHub collector)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Create a token with **read access to public repositories** (Contents: Read, Metadata: Read)
3. Call it `BRIEFING_GITHUB_TOKEN` in your secrets

---

### 7. Create a `.env` file for local runs

```bash
cp .env.example .env   # if provided, or create manually
```

`.env` contents:

```
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_CLIENT_ID=....apps.googleusercontent.com
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
ZOHO_EMAIL=you@yourdomain.com
ZOHO_IMAP_PASSWORD=...
RESEND_API_KEY=re_...
RECIPIENT_EMAIL=you@gmail.com
GITHUB_TOKEN=github_pat_...
```

> `.env` is gitignored — never commit it.

---

### 8. Test locally

```bash
# Collect only — no LLM calls, fast
PYTHONPATH=. python src/main.py --mode collect

# Full daily run
PYTHONPATH=. python src/main.py --mode daily

# Full weekly run
PYTHONPATH=. python src/main.py --mode weekly
```

Collected items are saved to `data/raw/`. Briefings are saved to `data/briefings/`.

---

### 9. Deploy to GitHub Actions

Add the following secrets to your GitHub repository under *Settings → Secrets and variables → Actions*:

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_CLIENT_ID` | From the OAuth flow in step 3 |
| `GMAIL_CLIENT_SECRET` | From the OAuth flow in step 3 |
| `GMAIL_REFRESH_TOKEN` | From `scripts/gmail_auth.py` output |
| `ZOHO_EMAIL` | Your Zoho email address |
| `ZOHO_IMAP_PASSWORD` | Zoho app password |
| `BRIEFING_GITHUB_TOKEN` | Fine-grained PAT from step 6 |
| `RESEND_API_KEY` | From Resend dashboard |
| `RECIPIENT_EMAIL` | Email address(es) to deliver the briefing to (comma-separated) |

The workflows run automatically:
- **Daily**: every day at **03:00 UTC** (`daily-briefing.yml`)
- **Weekly**: every Sunday at **04:00 UTC** (`weekly-briefing.yml`)

Trigger a manual run anytime via *Actions → Daily Briefing → Run workflow*.

> **Note on first run**: GitHub Actions skips the first scheduled trigger on a newly pushed workflow. Trigger once manually to initialize the dedup store, then scheduled runs will carry it forward via `actions/cache`.

---

## Configuration reference

### `config/scoring.md`

Controls how items are ranked. The final score is:

```
final_score = (
  0.30 × relevance +
  0.20 × leverage +
  0.15 × urgency +
  0.15 × novelty +
  0.10 × source_trust +
  0.10 × personal_fit
) − penalties + boosts
```

- **Thresholds**: `daily_briefing: 0.55`, `weekly_briefing: 0.45` — items below these are excluded
- **Boosts**: applied automatically based on item characteristics (e.g. `consulting_lead_signal: +0.25`)
- **Penalties**: applied for generic hype, low-confidence extraction, already-covered items

**Diversity caps** (applied after threshold filter, not configurable in the file — edit `src/main.py`):
- Source cap: no single source > 40% of final items
- Topic cap: no single primary topic > 35% of final items

### `config/output_templates.md`

Defines the exact structure of daily and weekly briefings. The renderer (LLM Call 3) is instructed to follow this template. Edit it to add or remove sections, change the subject line format, or adjust section ordering.

### Source trust tiers

Defined in `config/scoring.md`. Tier 1 sources (score: 1.0) include hand-curated high-quality feeds. Tier 5 (score: 0.2) covers unknown sources. Assign your own sources to tiers based on your trust in them.

---

## Token usage and performance

The pipeline is optimized for minimal API usage:

| Optimization | Effect |
|---|---|
| Keyword pre-filter | Eliminates ~70–80% of items before any LLM call |
| Merged enrich+score calls | Single LLM call per item instead of two |
| Prompt caching | System prompt (profile + topics + assumptions) cached across all item calls |
| Content truncation | Raw content capped at 1500 chars before sending to LLM |
| 7-day dedup store | Already-seen items never re-enter the pipeline |

Typical token usage: **~30–50k tokens per daily run** (after optimization).

GitHub Actions runtime: **~8–12 min** with pip and store.db caching enabled.

---

## Customization tips

**To track a new topic**: add a `##` section to `config/topics.md` with a weight, keywords, and exclusions. No code change needed.

**To add an RSS feed**: add a `- name / url / topic_weight_boost` entry under `## RSS and Substack feeds` in `config/sources.md`.

**To change the briefing threshold**: edit `daily_briefing:` or `weekly_briefing:` in `config/scoring.md`. Lower = more items, higher = fewer and more curated.

**To add a recipient**: set `RECIPIENT_EMAIL` to a comma-separated list: `you@gmail.com,partner@company.com`.

**To change briefing delivery time**: edit the `cron:` expression in `.github/workflows/daily-briefing.yml`. The format is UTC.

**To test the LLM pipeline without sending email**: run with `--mode collect` to collect only, then inspect `data/raw/`.

---

## Design principles (for forkers)

This project is designed to be forked and repersonalized:

- **All personal configuration lives in `config/`** — no personal data anywhere in `src/`
- **All secrets come from environment variables** — no defaults, no hardcoded fallbacks
- **`config/profile.md` is the only file a new user must edit** to get a personalized briefing
- **`src/` is generic** — it does not know who you are. Only `config/` knows.
- **No vendor lock-in** beyond Anthropic (LLM) and Resend (email) — both are swappable

---

## Example output

See [`examples/example-daily.md`](examples/example-daily.md) for an anonymized example of a daily briefing.

---

## Failure modes and defenses

| Failure | Defense |
|---|---|
| Too many items surfaced | Minimum score threshold + diversity caps |
| Generic why-it-matters copy | Prompt explicitly contrasts bad vs. good examples |
| No action recommendation | Required field — LLM validation fails without it |
| Duplicate items across days | SHA256 dedup with 7-day lookback in SQLite |
| Reddit API blocking | Fetch via `requests` with browser User-Agent, pass content to feedparser |
| Gmail OAuth expiry | Refresh token — does not expire unless revoked |
| GitHub rate limits | Authenticated requests (5000/hour) + exponential backoff via tenacity |
| LLM call failure | Tenacity retry, max 3 attempts with exponential backoff |
| Briefing not delivered | Briefing always saved to `data/briefings/` as fallback; GitHub Actions logs show delivery status |
| Self-sent briefing emails collected | Excluded via `-from:updates.yourdomain.com` in Gmail query and sender filter in Zoho |

---

## v2 ideas (not built)

- Feedback loop: mark items useful/not useful via email reply parsing — adjusts topic weights over time
- LinkedIn monitoring via RSS workaround or browser extension
- Obsidian integration: save high-scored items directly to vault
- Chat interface: "what did I miss this week on agents?"
- Automated blog post idea extraction from high-scored items
- Israeli influencer Substack/Twitter/X monitoring
