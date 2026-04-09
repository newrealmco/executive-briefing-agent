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
leverage: potential impact on current projects, career positioning, or active decisions
urgency: time sensitivity — releases, deadlines, limited-window opportunities score higher
novelty: not already surfaced this week; not a repeat of yesterday's items
source_trust: known high-quality sources score higher (see trust tiers below)
personal_fit: direct connection to active projects — multi-tenant layer, on-call automation, promotion cycle

## Source trust tiers

tier_1 (1.0): Will Larson, Charity Majors, Martin Fowler, The Pragmatic Engineer, Increment
tier_2 (0.8): Simon Willison, Latent Space, Stratechery, Anthropic Blog, Hugging Face Blog
tier_3 (0.6): Reddit (score > 200), The Diff, curated newsletters
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

active_project_connection: +0.20
career_signal: +0.15
novel_tool_or_pattern: +0.15
open_source_release: +0.10
industry_compensation_data: +0.10
