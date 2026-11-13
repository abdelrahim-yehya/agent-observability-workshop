# Tool search protocol (multivocal, following Garousi et al., IST 106, 2019)

Goal: identify the tools that practitioners use to measure agent observability and evaluation metrics.
Every candidate must come from one of the three channels below, through a listed query or source.
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
One web channel for both kinds of tool (since 2026-11-09 the selection evidence for closed-source tools only; see the amendment below). A planned closed-source channel (pricing and cloud-vendor site queries, OpenTelemetry vendor list) and a literature channel (snowballing from three surveys) were never run and were dropped on 2026-10-30.
Run each query in a private window, signed out, region and language noted, on one day.
Screen the first 30 results (3 pages). Run 2026-10-22 in a private browser window (per the user); region and language were not recorded, and
each query logged 28 or 29 results (see `google_search_log.csv`). From each result, record every tool named as an
observability or evaluation tool for LLM agents.
```
"LLM observability" tools
"agent observability" platform
"LLM evaluation" framework
"agent evaluation" tools
"LLM tracing" OpenTelemetry
"AI agent monitoring" platform
```
Two further queries were planned and never run; decision of 2026-10-30: dropped, not run later (a second run date
would break the one-day rule and change the frozen candidate set). Dropped queries:
`"LLM observability" comparison` and `"LLM evaluation" platform comparison`.

## Channel 3 — Standards
The OpenTelemetry GenAI semantic conventions are included as the vendor-neutral reference for agent
telemetry. No other standard was found; any found in Channels 1–2 is added here.

## Inclusion criteria
- I1  Primary purpose: tracing, monitoring or evaluating LLM applications or agents.
- I2  Open-source tools: at least 1,000 GitHub stars, not archived, a push or release in the last 6 months.
- I3  Closed-source tools: public documentation, and named in at least two independent sources
      across Channel 2.

## Exclusion criteria
- E1  LLM gateways and proxies whose main purpose is routing (for example LiteLLM).
- E2  Agent-building frameworks (for example VoltAgent).
- E3  Model-level benchmark harnesses that do not evaluate agents (for example lm-evaluation-harness).
- E4  Tutorials, course material and lists of links ("awesome" lists).
- E5  Duplicates: an SDK and its platform count as one tool.

## Ranking
The tools that passed C1 in the first selection were ranked by `google_independent_sources`, then GitHub stars (rule S4 in `screening_rules.md`); the 2026-11-09 amendment below replaces this for open-source tools.
The rank only orders the tools: C1, not the rank, decides which tools are in. Counts depend on the 6 queries run.

## Recording (google_search_log.csv)
date, channel, query, rank, url, source_type (vendor / blog / docs / news / list), tools_named

## Amendments after the first Google run (22 Oct 2026) — report these in the paper
- E6  Exclude general-purpose observability, APM, data, security or ML platforms whose LLM support is a module
      (for example Datadog, Grafana, New Relic, Splunk, Databricks). Exception: an LLM-specific product that is
      distributed on its own with its own repository (for example W&B Weave).
- C1  Corroboration: a tool enters the matrix only if at least two independent sources name it (a tool's own
      website is not independent for that tool). Titles and snippets only were read; result pages were not opened.
- Benchmarks are out of scope (S1); the literature channel that would have admitted them (old I4) was dropped on 2026-10-30.
- MLflow had 0 independent Google sources (all 8 hits are mlflow.org). C1 was applied and
  MLflow was removed on 2026-10-26.

## Amendment 2026-11-09: open-source tools are selected by adoption, Google selects closed-source tools
Made after the first selection and after the adoption data were read (2026-11-06), so it is a post-hoc change and the
paper must say so. The earlier C1 selection (13 entries) is kept as a sensitivity comparison. Rules I1, E1 to E6, S1, S2
and A1 are unchanged.
- C1  Corroboration, revised: applies to **closed-source tools only**: at least two independent sources in the Channel 2
      log (its own website does not count). A tool whose platform can only be used as a hosted service counts as
      closed-source even if its SDK is open (for example W&B Weave, LangSmith).
- C2  Adoption, new, **open-source tools**: a tool that passes I1, E1 to E6, S1 and A1 is selected if it passes I2
      (at least 1,000 stars, not archived, a push or release in the last 6 months) and has adoption evidence: at least
      5,000 GitHub stars, or at least 1,000,000 downloads in the last 30 days (the larger of PyPI and npm); and, when a
      PyPI or npm package exists, at least 100,000 downloads. Stars, last push and downloads are read on one date
      (2026-11-06; `data/outputs/open_source_adoption_candidates.csv`). The thresholds were chosen after seeing the data
      and are reported with a sensitivity table.
- E6 reading used for the first tools selected under C2: an LLM-specific package that is distributed on its own counts as the exception even
  when it lives inside a larger repository (W&B Weave; `mlflow-tracing`, which had 14.8M PyPI downloads in 30 days). MLflow is therefore in
  (decision 2026-11-09, user). Evidently (general ML monitoring) and Harbor (benchmark runner, like Inspect AI) are out; Pydantic Logfire is out (E6).
- Added under C2 on 2026-11-09: MLflow, Laminar, LangWatch (metric rows collected 2026-11-09; MLflow's earlier rows were moved back from
  `data/interim/c1_removed/`). Evidence in `data/outputs/open_source_adoption_candidates.csv`.
- Google (Channel 2) stays as the discovery channel for every tool and is the selection evidence for closed-source tools.
- Ranking: open-source tools by downloads (larger of PyPI and npm), then stars; closed-source tools by independent
  Google sources; the paper reports the two groups apart. `results/best_tools.csv` keeps the earlier key until the new
  tools' metrics are collected.

## Amendment 2026-11-11: changelogs count as official documentation (metric collection)
Made after the first collection, when the author saw a tool-call count in the Langfuse product that no documentation page read
described; it is announced only in a changelog entry (2025-12-22). User's decision: changelog and release-notes pages published by
the vendor (site changelog, GitHub Releases, CHANGELOG.md) are official documentation for metric collection, for all 16 entries.
- Procedure, per-entry reading logs, all 103 candidate rows with a decision and reason, and the saved pages:
  `data/interim/changelog_review/` (start with its README.md and BRIEF.md). Read 2026-11-11 and 2026-11-12.
- Result: 33 rows added to `results/built_in_metrics.csv` (264 -> 297), 50 mapping pairs (326 -> 376), 36 cells became built-in,
  no new unique metric. Each added row's `note` starts with "changelog channel".
- A changelog entry describes the product on its release date: rows removed by a later entry were not added.
- Not added (author's decision, 2026-11-12: the taxonomy stays as it is): session count and duration, automatic issue detection,
  sycophancy, response trust. They are in `review_decisions.csv` with the reason "would need a new unique metric".
- Limits to report: see "Coverage limits" in the staging README (LangSmith changelog starts 2025-01, Weave release titles only,
  older Phoenix and LangWatch history keyword-searched, OpenTelemetry GenAI fragments unreleased).

## Related-work search (not a tool channel; run 2026-10-30)
Finds prior work to cite and compare against; it does not add tools. 8 queries through a web-search tool, restricted to
arxiv.org (7 queries) or dl.acm.org / ieeexplore.ieee.org / aclanthology.org (2 queries), first ~10 results each.
Decisions come from titles and snippets, not full texts. Log: `data/inputs/related_work_search_log.csv`.
Limits: Google Scholar and Semantic Scholar were not queried; ranks are as returned by the search tool and not reproducible.
