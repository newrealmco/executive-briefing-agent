## Gmail (personal)
auth: oauth2
account: personal_gmail
priority: high
look_for:
  - emails sent by me to myself (intentional saves, treat as high priority)
  - newsletters from known publications
  - recruiter emails from target companies (infra-focused, platform engineering roles)
  - replies to outreach I sent
  - anything from a sender I have emailed more than 3 times
deprioritize:
  - automated SaaS notifications
  - promotional email not matching newsletter allowlist
  - social media notification digests
  - calendar confirmations
lookback_hours: 24

## Zoho Mail (work domain)
auth: imap
account: zoho_work
priority: high
look_for:
  - inbound inquiries about consulting or speaking
  - reader replies to blog posts
  - any direct human-written email (not automated)
deprioritize:
  - automated platform notifications
  - spam
lookback_hours: 24

## RSS and Substack feeds
auth: none
priority: medium-high
feeds:
  # Platform and SRE
  - name: The Pragmatic Engineer
    url: https://newsletter.pragmaticengineer.com/feed
    topic_weight_boost: engineering_leadership
  - name: Increment
    url: https://increment.com/feeds/all/
    topic_weight_boost: platform_engineering
  - name: Charity Majors (Honeycomb)
    url: https://charity.wtf/feed/
    topic_weight_boost: sre_reliability
  - name: Will Larson (Irrational Exuberance)
    url: https://lethain.com/feeds/
    topic_weight_boost: engineering_leadership

  # AI and developer tooling
  - name: Simon Willison
    url: https://simonwillison.net/atom/everything/
    topic_weight_boost: ai_dev_tooling
  - name: Latent Space
    url: https://www.latent.space/feed
    topic_weight_boost: ai_dev_tooling
  - name: Anthropic Blog
    url: https://www.anthropic.com/rss.xml
    topic_weight_boost: ai_dev_tooling
  - name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    topic_weight_boost: ai_dev_tooling

  # Tech strategy and industry
  - name: The Diff
    url: https://thediff.co/feed
    topic_weight_boost: tech_industry_signals
  - name: Stratechery
    url: https://stratechery.com/feed
    topic_weight_boost: tech_industry_signals

  # SaaS architecture
  - name: Martin Fowler
    url: https://martinfowler.com/feed.atom
    topic_weight_boost: multi_tenancy

## Reddit
auth: none
priority: medium
feeds:
  - name: ExperiencedDevs
    url: https://www.reddit.com/r/ExperiencedDevs/top.rss?t=day
    topic: engineering_leadership
  - name: devops
    url: https://www.reddit.com/r/devops/top.rss?t=day
    topic: sre_reliability
  - name: sre
    url: https://www.reddit.com/r/sre/top.rss?t=day
    topic: sre_reliability
  - name: LocalLLaMA
    url: https://www.reddit.com/r/LocalLLaMA/hot.rss
    topic: ai_dev_tooling
  - name: MachineLearning
    url: https://www.reddit.com/r/MachineLearning/top.rss?t=day
    topic: ai_dev_tooling
  - name: cscareerquestions
    url: https://www.reddit.com/r/cscareerquestions/top.rss?t=day
    topic: tech_industry_signals

## GitHub
auth: token
priority: medium
watch:
  - org: modelcontextprotocol
    repos: all
    events: [release, new_repo]
    topic_weight_boost: ai_dev_tooling
  - org: backstage
    repos: [backstage]
    events: [release]
    topic_weight_boost: platform_engineering
  - org: grafana
    repos: [grafana, loki, tempo]
    events: [release]
    topic_weight_boost: sre_reliability
  - org: open-telemetry
    repos: all
    events: [release, new_repo]
    topic_weight_boost: sre_reliability
  - org: anthropics
    repos: [anthropic-cookbook]
    events: [release]
    topic_weight_boost: ai_dev_tooling
  - org: langchain-ai
    repos: [langchain, langgraph]
    events: [release]
    topic_weight_boost: ai_dev_tooling
