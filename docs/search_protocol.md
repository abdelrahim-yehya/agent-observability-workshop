# Tool search protocol (multivocal, following Garousi et al., IST 106, 2019)

Goal: identify the tools that practitioners use to measure agent observability and evaluation metrics.
Every candidate must come from one of the five channels below, through a listed query or source.
Record every run (date, query, results) so the search can be repeated.

## Channel 1 — GitHub (open-source tools)
Endpoint: GitHub REST search API, `GET /search/repositories`, `sort=stars`, `order=desc`, `per_page=30`.
Common qualifiers on every query: `stars:>=1000 archived:false pushed:>=<run date minus 6 months>`

G1 — topic queries
```
topic:llm-observability     topic:llm-evaluation     topic:llmops
topic:agent-observability   topic:agent-evaluation   topic:llm-tracing
topic:ai-observability      topic:llm-testing        topic:llm-eval      topic:evals
```
G2 — keyword queries (`in:name,description,readme`)
```
"llm observability"   "agent observability"   "llm evaluation"   "agent evaluation"
"llm tracing"         "opentelemetry" llm      "semantic conventions" llm
```
Script: `github_tool_search.py` (writes every hit to `github_raw_results.csv`).

## Channel 2 — Google (web, open and closed tools)
Run each query in a private window, signed out, region and language noted, on one day.
Screen the first 30 results (3 pages). From each result, record every tool named as an
observability or evaluation tool for LLM agents.
```
"LLM observability" tools
"agent observability" platform
"LLM evaluation" framework
"agent evaluation" tools
"LLM tracing" OpenTelemetry
"AI agent monitoring" platform
"LLM observability" comparison
"LLM evaluation" platform comparison
```

## Channel 3 — Closed-source and commercial tools
Google queries (same procedure as Channel 2):
```
"LLM observability" pricing
"agent observability" enterprise
"LLM evaluation" platform pricing
"agent observability" site:aws.amazon.com
"agent evaluation" site:learn.microsoft.com
"agent evaluation" site:cloud.google.com
```
Registry: OpenTelemetry vendor list, https://opentelemetry.io/ecosystem/vendors/ — keep vendors whose
documentation states support for generative-AI or LLM telemetry.

## Channel 4 — Academic literature (snowballing)
Tools and benchmarks named in the surveys cited by the paper:
- Wang et al., A survey on AgentOps (arXiv:2508.02121) — its comparison table of observability tools.
- Mohammadi et al., Evaluation and benchmarking of LLM agents: a survey (arXiv:2507.21504).
- Yehudai et al., Survey on evaluation of LLM-based agents (arXiv:2503.16416).
Benchmarks enter only through this channel.

## Channel 5 — Standards
The OpenTelemetry GenAI semantic conventions are included as the vendor-neutral reference for agent
telemetry. No other standard was found; any found in Channels 1–4 is added here.

## Inclusion criteria
- I1  Primary purpose: tracing, monitoring or evaluating LLM applications or agents.
- I2  Open-source tools: at least 1,000 GitHub stars, not archived, a push or release in the last 6 months.
- I3  Closed-source tools: public documentation, and named in at least two independent sources
      across Channels 2–4.
- I4  Benchmarks (Channel 4): named in at least one cited survey; the activity rule does not apply,
      because a benchmark is a fixed dataset.

## Exclusion criteria
- E1  LLM gateways and proxies whose main purpose is routing (for example LiteLLM).
- E2  Agent-building frameworks (for example VoltAgent).
- E3  Model-level benchmark harnesses that do not evaluate agents (for example lm-evaluation-harness).
- E4  Tutorials, course material and lists of links ("awesome" lists).
- E5  Duplicates: an SDK and its platform count as one tool.

## Recording (google_search_log.csv)
date, channel, query, rank, url, source_type (vendor / blog / docs / news / list), tools_named

## Amendments after the first Google run (22 Oct 2026) — report these in the paper
- E6  Exclude general-purpose observability, APM, data, security or ML platforms whose LLM support is a module
      (for example Datadog, Grafana, New Relic, Splunk, Databricks). Exception: an LLM-specific product that is
      distributed on its own with its own repository (for example W&B Weave).
- C1  Corroboration: a tool enters the matrix only if at least two independent sources name it (a tool's own
      website is not independent for that tool). Titles and snippets only were read; result pages were not opened.
- Deferred: benchmarks and Inspect AI wait for the literature channel (not run; benchmarks are out of scope, see README).
- MLflow had 0 independent Google sources (all 8 hits are mlflow.org). The literature channel was not run, so C1 was applied and
  MLflow was removed on 2026-10-26.
