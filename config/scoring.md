## Scoring formula

final_score = (
  0.30 * relevance +
  0.20 * leverage +
  0.15 * urgency +
  0.15 * novelty +
  0.10 * source_trust +
  0.10 * personal_fit
) - penalties

All dimensions are 0.0 to 1.0.

## Dimension definitions

relevance: alignment with declared topics and their weights
leverage: potential impact on JDD book, consulting pipeline, career positioning, or current decisions
urgency: time sensitivity — releases, deadlines, limited-window opportunities score higher
novelty: not already surfaced this week; not a repeat of yesterday's items
source_trust: known high-quality sources score higher (see trust tiers below)
personal_fit: direct connection to active projects — JDD book, newrealm.co, Meta process, consulting

## Source trust tiers

tier_1 (1.0): Simon Willison, Anthropic blog, Lenny's Newsletter, The Pragmatic Engineer, Latent Space
tier_2 (0.8): OpenAI blog, Hugging Face blog, Stratechery, One Useful Thing, Import AI
tier_3 (0.6): Reddit (score > 200), Geektime, Calcalist, Ben's Bites
tier_4 (0.4): Reddit (score 50–200), Medium, general RSS
tier_5 (0.2): Unknown sources, low-engagement posts

## Penalties

duplicate_this_week: -0.3
generic_hype_no_implication: -0.25
low_confidence_extraction: -0.15
no_actionable_connection: -0.10
already_widely_covered_yesterday: -0.20

## Minimum threshold for inclusion

daily_briefing: 0.55
weekly_briefing: 0.45

## Special boost rules

jdd_direct_connection: +0.20
agent_governance_intersection: +0.15
consulting_lead_signal: +0.25
mcp_new_development: +0.15
israel_tech_local_relevance: +0.10
