# Agent observability and evaluation tools: tool selection and built-in metrics

Goal: (1) identify the most important tools for observability and evaluation of AI agents, and (2) list the built-in metrics each one provides. Every claim in the results has a source URL, a verbatim quote and an access date.

## Results (`results/`)

| File | Content | Status |
|---|---|---|
| `best_tools.csv` | The 13 selected tools, ranked, with the evidence for each selection criterion | done |
| `metric_taxonomy.csv` | The 31 unique metrics, split into Observability (19, measurements captured from a run) and Evaluation (12, judgements of agent behaviour) and grouped in 7 categories, with a definition and the list of tools that support each | draft for review |
| `built_in_metrics.csv` | 122 built-in agent-execution metrics from 12 of the 13 tools (rule M1). OpenInference has no rows: see Limitations. Each row has the doc URL, a verbatim quote, the saved page it was copied from, and the access date | first pass done, being reviewed |

## How the tools were selected

Rules are in [`docs/screening_rules.md`](docs/screening_rules.md) (S1–S4) and [`docs/search_protocol.md`](docs/search_protocol.md) (search channels, inclusion and exclusion criteria). [`docs/rule_index.md`](docs/rule_index.md) lists every rule ID once and says where it is defined.

1. **Discover**: GitHub search (182 repos, run 2026-10-22) plus a manual Google search (173 results, same day) → 42 tools.
2. **S1 scope**: primary purpose is observability or evaluation of LLM apps or agents → 31 tools in, 10 out, 1 on hold (iFixAi, treated as out).
3. **A1 agent relevance** (amendment to the protocol): official docs explicitly cover agents, tool calls or multi-step traces. Quotes were checked against the raw page text, and re-checked against the live pages on 2026-10-26 (all 13 found). Each A1 page is saved as `data/raw/doc_snapshots/a1__<tool>.txt` and its quote appears verbatim in it (for DeepEval the markdown backticks around `deepeval` were dropped, because the rendered page shows that word in code font).
4. **Corroborate (C1)**: a tool must be named by at least two independent sources (its own website does not count). 13 of the 31 S1 tools pass; the other 18 have none, so the list has 13 tools, not the 15 first planned. MLflow (28k stars, but all 8 Google results naming it are on mlflow.org) and Evidently fail C1 and are removed; their rows are kept in `data/interim/c1_removed/`.
5. **Rank** the 13 by independent Google sources, then GitHub stars. S3 (built-in metrics) was applied while collecting the metrics, and the original S4 coverage rule was replaced by this ranking (see `docs/screening_rules.md`).
6. **Corroborate downloads**: add last-month PyPI and npm downloads (`pypi_downloads_last_month`, `npm_downloads_last_month` in `best_tools.csv`, from the pypistats.org and npm download APIs on 2026-10-26). Downloads are reported next to the ranking but do not change it: the ranking rule was fixed before they were collected, and changing it afterwards would be unjustified. Each package was matched to its tool through the repository or author listed in its PyPI metadata.

## Data (`data/`)

| Folder | Files |
|---|---|
| `inputs/` | `google_search_log.csv`, `tool_screening_google.csv` (manual Google channel) |
| `raw/` | `github_raw_results.csv` (GitHub search snapshot), `doc_snapshots/` (plain-text copy of the documentation pages read, including every page quoted in `built_in_metrics.csv` (2026-10-25) and the A1 page of each selected tool, `a1__*.txt` (2026-10-26)) |
| `interim/` | `github_filtered_results.csv`, `github_excluded_results.csv` (first-pass GitHub screening), `metrics_out_of_scope.csv` (metrics removed by M1, with reason) |
| `outputs/` | `combined_tools_no_duplicates.csv` (42 tools), `tools_scope_screening.csv` (S1/S2), `a1_agent_relevance.csv` (A1 evidence) |

`src/github_tool_search.py` reproduces the GitHub search and `src/merge_tool_sources.py` builds the combined list. Stars and activity dates change over time, so the committed snapshot is the reference.

## How the taxonomy was built

Two tool-specific metrics are merged into one unique metric when they measure the same property of the same object (a tool call, an agent run, an LLM call, a token type), whatever the tools call them. A row that lists several measures (for example a dashboard showing input and output tokens) maps to each of them. The mapping is hand-made and kept in `data/inputs/taxonomy_mapping.csv`, the definitions (written by the author, not quoted from the docs) in `data/inputs/taxonomy_definitions.csv`. `python3 src/build_taxonomy.py` rebuilds `results/metric_taxonomy.csv` and fails if any metric is left unmapped.

## How the metrics were collected

**Scope (M1):** only built-in metrics that describe how an agent run executes are kept: `tool_use` (selection, invocation, arguments, errors, efficiency), `task_goal`, `plan_trajectory`, and run telemetry (`tokens`, `cost`, `latency`, `errors`, `counts`). Output-text checks (is-json, regex, contains, BLEU), generic answer quality, RAG retrieval, safety, tone, voice and image metrics are out of scope. The 345 removed rows, with the reason, are in `data/interim/metrics_out_of_scope.csv`.

The collection used `built_in` values: `built-in` (ships with the tool, no user code), `custom-only` (generic mechanism where the user supplies the criteria), `via-integration` (provided by a third-party library the tool wraps), `community` (tagged community in the docs). `kind` is `evaluator` or `telemetry` (measure captured automatically, such as latency, tokens, cost).
Every quote in `built_in_metrics.csv` was checked by script to appear word for word in its saved page.

## Limitations

- OpenInference contributes no built-in metric rows: it defines a span attribute for evaluation results, but only as a user-supplied field (custom-only). It is reported with zero rows, not dropped.
- C1 reduced the list to 13 tools. MLflow and Evidently were first in the top 15, then removed under C1 (0 independent Google sources; MLflow's 8 hits are all its own site). Other widely used tools with no third-party mention in the first 30 results of the 8 Google queries are also absent (for example Harbor, Giskard, TruLens, AgentOps). The Google counts reflect what ranks in those queries, not usage.
- Benchmarks and eval harnesses (SWE-bench, τ-bench, Inspect AI) are out of scope: S1 removes benchmarks, although I4 in the protocol would admit them through the literature channel. Metrics such as pass^k that come from them are therefore not in the tables.
- Grounding, safety and conversation-level metrics were removed by M1. The study covers how an agent run executes, not how good its output is.
- The tool is called "Weights & Biases" in the screening files and "Weights & Biases Weave" in `results/`; only the Weave toolkit is studied.

- Google counts come from result titles and snippets only; pages were not opened.
- Ranking by stars favours open-source tools: closed-source tools can only rank on Google sources.
- Metrics come from official documentation pages. Metrics that exist only in a tool's source code, and not in its docs, are not listed (checked for OpenLLMetry only).
- Row counts are not comparable across tools: some docs list individual prompt templates or assertion types, others list fewer, broader metrics.
- Download counts are only corroboration. They include installs triggered as dependencies of other packages (for example `langsmith`, `mlflow`) and CI downloads. They are blank for tools without a representative package: Helicone is used through an API proxy, and the only `helicone` package on PyPI is an old OpenAI wrapper. The OpenTelemetry figure is the general semantic-conventions library, not AI-specific.

## Relation to the earlier weekly briefing (20 Oct 2026)

The briefing presented a first pass: 13 tools picked by GitHub stars from 41 candidates, and a 31-metric taxonomy with 8 categories (adding Grounding and Safety and policy, and counting "derivable" cells). This repository replaces it. The tool set changed (Helicone, Braintrust, Galileo, W&B Weave and Evidently in; Inspect AI, SWE-bench and τ-bench out), the ranking uses independent Google sources, and only built-in metrics with a verbatim quote are counted. Numbers from the briefing (for example "token usage built in for 11 of 13 tools") do not carry over.
