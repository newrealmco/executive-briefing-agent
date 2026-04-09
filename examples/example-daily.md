# Briefing — 2025-11-14 | OpenTelemetry 1.9 + agent-assisted on-call patterns converging

> Anonymized example output demonstrating the daily briefing format.
> Replace `config/profile.md`, `config/topics.md`, and `config/sources.md` with your own
> content to receive a briefing tailored to your role and priorities.

---

## Today's focus

Two independent signals converge today: OpenTelemetry 1.9 shipped with stable semantic conventions for LLM traces, and a high-signal thread on r/sre documented how three platform teams are using lightweight coding agents to handle first-response on-call triage. Together these define the next horizon for the on-call automation project — there is now a standard telemetry substrate and practitioner evidence that agent-assisted triage is working in production. Neither is theoretical anymore.

---

## Read now (7 items)

---

**OpenTelemetry 1.9: stable semantic conventions for LLM and agent traces** — GitHub / open-telemetry  
Why it matters: This is the observability foundation the on-call automation project needs — once agent actions emit standardized traces, debugging agent decisions in production becomes tractable rather than guesswork.  
TL;DR: OTel 1.9 promotes `gen_ai.*` semantic conventions to stable, covering LLM inputs/outputs, tool calls, and agent spans. SDK support lands in Python and Go this release. This closes the main observability gap for deployed agent systems.  
Action: Read now  
Link: https://github.com/open-telemetry/opentelemetry-specification/releases/tag/v1.9.0

---

**Three platform teams using agents for on-call first response — what actually works** — Reddit / r/sre  
Why it matters: Direct practitioner evidence that agent-assisted triage is in production, with specifics on failure modes — exactly what's needed before writing the architecture proposal.  
TL;DR: A staff SRE documented how their team built a lightweight agent that reads runbooks, queries the metrics platform, and posts a structured triage report within 60 seconds of a page. Two other commenters shared similar setups. Main failure mode: agents confidently misclassify novel failure patterns as known ones. Thread has 1,200 upvotes.  
Action: Save for later  
Link: https://reddit.com/r/sre/comments/...

---

**[Inbound email] Re: platform engineering talk — CFP invitation** — Gmail  
Why it matters: A conference organizer is asking for a talk proposal on internal developer platforms — a direct visibility opportunity worth evaluating against the current schedule.  
TL;DR: A mid-size engineering conference (300–500 attendees) reached out after a recent blog post. They have a platform engineering track with a CFP deadline in 3 weeks. Speaking slot is 40 minutes.  
Action: Reply  
Link: (email — no URL)

---

**Backstage 1.28 ships with first-class AI plugin support** — GitHub / backstage  
Why it matters: If Backstage becomes the standard surface for AI tooling in internal platforms, this is a significant architectural direction signal for the developer portal conversation.  
TL;DR: Backstage 1.28 adds a plugin API for AI-powered catalog enrichment, automated dependency scanning, and natural language search across the service catalog. Early adopters include two large enterprises cited in the release notes.  
Action: Monitor  
Link: https://github.com/backstage/backstage/releases/tag/v1.28.0

---

**Staff engineers build leverage without authority** — Irrational Exuberance  
Why it matters: Directly relevant to the promotion cycle — concrete framing for the "impact without a title" narrative that a promotion packet needs.  
TL;DR: The post argues that staff engineers build leverage through three mechanisms: writing that travels, decisions that document, and problems that outlast. Distinguishes this from heroics-based impact. Includes a template for a work log that surfaces influence to leadership.  
Action: Save for later  
Link: https://lethain.com/staff-engineer-leverage

---

**Enterprise API tier launches — 5× rate limits, SLA included** — Anthropic Blog  
Why it matters: If the on-call agent hits rate limits in production (a known risk at scale), the enterprise tier removes that blocker — relevant for the cost/architecture proposal.  
TL;DR: A new enterprise API tier with 5× higher rate limits, 99.9% SLA, and dedicated capacity. Pricing is usage-based with a monthly minimum. Available now.  
Action: Monitor  
Link: https://anthropic.com/blog/enterprise-api

---

**Senior engineer compensation benchmarks, Q4 2025** — The Pragmatic Engineer  
Why it matters: Current market data for senior and staff-level roles — directly useful for evaluating compensation if the promotion goes through.  
TL;DR: Survey of 800 engineers shows median total comp for senior engineers at $220k in NYC/SF, $175k remote. Staff engineers at $280k median. Significant variance by company stage: public vs. late-stage private vs. early-stage.  
Action: Save for later  
Link: https://newsletter.pragmaticengineer.com/p/compensation-benchmarks-q4-2025

---

## Needs action

- **Reply to CFP invitation (Gmail)** — 3-week deadline. Propose a 40-minute talk on internal developer platforms. Reply within 48 hours to hold the slot.
- **OpenTelemetry 1.9** — Share the `gen_ai.*` conventions with the on-call automation working group. Resolves the open question about telemetry format from last sprint.

---

## One recommended move

Draft the conference talk abstract today — 150 words, framed as a case study rather than a tutorial: what the platform decision was, what it cost, what you learned. This takes 30 minutes and is the hardest part of the CFP to delay.
