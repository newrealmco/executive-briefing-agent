## Gmail (personal)
auth: oauth2
account: personal_gmail
priority: high
look_for:
  - emails sent by me to myself (intentional saves, treat as high priority)
  - newsletters from known publications (match against rss allowlist)
  - recruiter emails from target companies (Meta, Anthropic, tier-1 AI companies)
  - replies to outreach I sent
  - anything from a sender I have emailed more than 3 times
deprioritize:
  - automated saas notifications
  - promotional email not matching newsletter allowlist
  - social media notification digests
  - calendar confirmations
lookback_hours: 24

## Zoho Mail (newrealm.co)
auth: imap
account: zoho_newrealm
priority: high
look_for:
  - inbound interest in JDD consulting
  - responses to LinkedIn outreach
  - reader engagement with blog posts
  - any direct human-written email (not automated)
  - contact form submissions
deprioritize:
  - automated platform notifications
  - spam
lookback_hours: 24

## RSS and Substack feeds
auth: none
priority: medium-high
feeds:
  # Product and PM
  - name: Lenny's Newsletter
    url: https://www.lennysnewsletter.com/feed
    topic_weight_boost: product_leadership
  - name: The Pragmatic Engineer
    url: https://newsletter.pragmaticengineer.com/feed
    topic_weight_boost: tech_industry_signals
  # AI general
  - name: One Useful Thing
    url: https://www.oneusefulthing.org/feed
    topic_weight_boost: ai_ml_frontier
  - name: Last Week in AI
    url: https://lastweekin.ai/feed
    topic_weight_boost: ai_ml_frontier
  - name: The Neuron
    url: https://www.theneurondaily.com/feed
    topic_weight_boost: ai_ml_frontier
  - name: Ben's Bites
    url: https://bensbites.beehiiv.com/feed
    topic_weight_boost: ai_ml_frontier
  - name: Import AI
    url: https://importai.substack.com/feed
    topic_weight_boost: ai_ml_frontier
  # Tech strategy
  - name: The Diff
    url: https://thediff.co/feed
    topic_weight_boost: tech_industry_signals
  - name: Stratechery
    url: https://stratechery.com/feed
    topic_weight_boost: product_leadership
  # Agents
  - name: Latent Space
    url: https://www.latent.space/feed
    topic_weight_boost: agents
  # Blogs
  - name: Simon Willison
    url: https://simonwillison.net/atom/everything/
    topic_weight_boost: ai_ml_frontier
  - name: Paul Graham
    url: http://www.paulgraham.com/rss.html
    topic_weight_boost: product_leadership
  - name: Anthropic Blog
    url: https://www.anthropic.com/rss.xml
    topic_weight_boost: ai_ml_frontier
  - name: OpenAI Blog
    url: https://openai.com/news/rss.xml
    topic_weight_boost: ai_ml_frontier
  - name: Google DeepMind Blog
    url: https://deepmind.google/blog/rss.xml
    topic_weight_boost: ai_ml_frontier
  - name: Hugging Face Blog
    url: https://huggingface.co/blog/feed.xml
    topic_weight_boost: ai_ml_frontier
  # Medium tags
  - name: Medium — AI
    url: https://medium.com/feed/tag/artificial-intelligence
    topic_weight_boost: ai_ml_frontier
  - name: Medium — Agents
    url: https://medium.com/feed/tag/llm
    topic_weight_boost: agents
  # Israel tech (English)
  - name: Geektime English
    url: https://www.geektime.com/feed/
    topic_weight_boost: israel_tech
  # Israel tech (Hebrew)
  - name: Calcalist Tech
    url: https://www.calcalist.co.il/rss/AjaxRss,7340,L-calcalist_hitech.xml
    topic_weight_boost: israel_tech
    language: Hebrew
  - name: TheMarker Tech
    url: https://www.themarker.com/cmlink/1.4605045
    topic_weight_boost: israel_tech
    language: Hebrew

## Reddit
auth: none
priority: medium
feeds:
  - name: MachineLearning
    url: https://www.reddit.com/r/MachineLearning/top.rss?t=day
    topic: ai_ml_frontier
  - name: artificial
    url: https://www.reddit.com/r/artificial/top.rss?t=day
    topic: ai_ml_frontier
  - name: LocalLLaMA
    url: https://www.reddit.com/r/LocalLLaMA/hot.rss
    topic: ai_ml_frontier
  - name: AIAgents
    url: https://www.reddit.com/r/AIAgents/hot.rss
    topic: agents
  - name: ClaudeAI
    url: https://www.reddit.com/r/ClaudeAI/hot.rss
    topic: agents
  - name: CursorAI
    url: https://www.reddit.com/r/CursorAI/hot.rss
    topic: agents
  - name: ChatGPT
    url: https://www.reddit.com/r/ChatGPT/top.rss?t=day
    topic: ai_ml_frontier
  - name: ProductManagement
    url: https://www.reddit.com/r/ProductManagement/top.rss?t=day
    topic: product_leadership
  - name: cscareerquestions
    url: https://www.reddit.com/r/cscareerquestions/top.rss?t=day
    topic: tech_industry_signals

## GitHub
auth: token
priority: medium
watch:
  - org: anthropics
    repos: [anthropic-cookbook, model-spec]
    events: [release, discussion, starred]
  - org: modelcontextprotocol
    repos: all
    events: [release, new_repo, discussion]
    topic_weight_boost: ai_ml_frontier
  - org: openai
    repos: all
    events: [release, new_repo]
  - org: langchain-ai
    repos: [langchain, langgraph]
    events: [release]
    topic_weight_boost: agents
  - org: e2b-dev
    repos: [e2b]
    events: [release]
    topic_weight_boost: agents
  - org: AgentOps-AI
    repos: [agentops]
    events: [release]
    topic_weight_boost: agents
  - org: crewAIInc
    repos: [crewAI]
    events: [release]
    topic_weight_boost: agents
  - org: invariantlabs-ai
    repos: all
    events: [release, new_repo]
    topic_weight_boost: ai_governance
  - org: All-Hands-AI
    repos: [OpenHands]
    events: [release]
    topic_weight_boost: agents
  - org: microsoft
    repos: [autogen]
    events: [release]
    topic_weight_boost: agents
  - org: continuedev
    repos: [continue]
    events: [release]
    topic_weight_boost: agents

## Israeli influencers (manual RSS / social monitoring)
# These require individual feed discovery — check each account for RSS or newsletter
# Placeholder: extend this list based on known accounts
influencers:
  - name: Bar Zikr
    note: Israeli Security influencer — find LinkedIn/Twitter/Substack RSS if available
    language: Hebrew
  - name: Dror Globerman
    note: Public Speaker, A Content Creator, An Acclaimed Broadcaster and Podcaster, and the Author of "Skip Intro" Newsletter — find LinkedIn/Twitter/Substack RSS if available
    language: Hebrew
  - name: danny peled
    note: VC and Podcaster — find LinkedIn/Twitter/Substack RSS if available
    language: Hebrew
