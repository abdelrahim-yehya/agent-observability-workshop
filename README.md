# Agent observability and evaluation tools: tool selection and built-in metrics

Goal: (1) identify the most important tools for observability and evaluation of AI agents, and (2) list the built-in metrics each one provides. Every claim in the results has a source URL, a verbatim quote and an access date.

## Results (`results/`)

| File | Content | Status |
|---|---|---|
| `best_tools.csv` | The 13 selected tools, ranked, with the evidence for each selection criterion | done |
| `metric_taxonomy.csv` | The 46 unique metrics, split into Observability (19, measurements captured from a run) and Evaluation (27, judgements of agent behaviour and output) and grouped in 13 categories (6 under Observability, 7 under Evaluation; "Tool use" and "Plan and trajectory" appear under both), with a definition and the list of tools that support each. `metric_taxonomy_diagram.svg` and `.png` draw it as a tree, one dot per tool that documents each metric (built by `src/plot_taxonomy.py`) | draft for review |
| `tool_metric_matrix.csv` | The 46 metrics against the 13 tools, one status per cell (built-in, integration, community, template, generic custom, records scores, not documented). `tool_metric_matrix_long.csv` has the same cells one per row, with the tool's own metric names, delivery and the doc URL. `tool_metric_matrix.html` is the same matrix drawn as a heatmap with the status legend (open it in a browser; built by `src/plot_matrix.py`) | draft for review |
| `built_in_metrics.csv` | 241 built-in metrics from the 13 tools (rule M1). Each row has the doc URL, a verbatim quote, the saved page it was copied from, and the access date | first pass done, being reviewed |

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
| `interim/` | `github_filtered_results.csv`, `github_excluded_results.csv` (first-pass GitHub screening), `metrics_out_of_scope.csv` (rows removed by M1 or for another stated reason) |
| `outputs/` | `combined_tools_no_duplicates.csv` (42 tools), `tools_scope_screening.csv` (S1/S2), `a1_agent_relevance.csv` (A1 evidence) |

`src/github_tool_search.py` reproduces the GitHub search and `src/merge_tool_sources.py` builds the combined list. Stars and activity dates change over time, so the committed snapshot is the reference.

## How the taxonomy was built

Two tool-specific metrics are merged into one unique metric when they measure the same property of the same object (a tool call, an agent run, an LLM call, a token type), whatever the tools call them. A row that lists several measures (for example a dashboard showing input and output tokens) maps to each of them. The mapping is hand-made and kept in `data/inputs/taxonomy_mapping.csv`, the definitions (written by the author, not quoted from the docs) in `data/inputs/taxonomy_definitions.csv`. `python3 src/build_taxonomy.py` rebuilds `results/metric_taxonomy.csv` and fails if any metric is left unmapped.

## How to read the matrix

`python3 src/build_matrix.py` builds it from the evidence tables, and `python3 src/plot_matrix.py` draws the heatmap from the long file. Each cell takes the strongest status found:

| Status | Meaning |
|---|---|
| built-in | a documented built-in row maps to the metric (see `built_in_metrics.csv`) |
| integration | only through a third-party library the tool wraps (for example Ragas) |
| community | a community-contributed metric in the tool's own docs |
| template | a copy-and-run example in the docs, not shipped as a metric |
| generic custom | Evaluation metrics only. No specific metric, but the tool documents a way to write your own evaluator |
| records scores | Evaluation metrics only. The tool defines or stores fields for scores produced elsewhere and has no evaluator mechanism of its own (OpenTelemetry, OpenInference, Helicone) |
| not documented | nothing found in the pages read. This is not proof that the tool lacks the capability |

Every one of the 13 tools has a custom-evaluator or score-recording row in `metrics_out_of_scope.csv`, and the script stops if one is missing, so "generic custom" and "records scores" always rest on a quoted page. They say the metric could be built, not that it exists. The integration, community and template cells come from `data/inputs/taxonomy_mapping_not_built_in.csv`, a hand-made mapping of those rows, and cover only the metrics that were in scope when the rows were collected. Counts of built-in cells per tool are not capability scores: documentation lists metrics at different granularity.

## How the metrics were collected

**Scope (M1):** only built-in metrics that describe how an agent run executes or how good its output is are kept. Execution: `tool_use` (selection, invocation, arguments, errors, efficiency), `task_goal`, `plan_trajectory`, and run telemetry (`tokens`, `cost`, `latency`, `errors`, `counts`). Output quality: `answer_quality` (correctness, relevance, helpfulness, conciseness, tone), `grounding` (faithfulness to context), `safety` (toxicity, bias, data leakage, injection, refusal, policy violations) and `conversation` (knowledge retention, user satisfaction, conversation coherence). Out of scope: text-match, format and reference-overlap checks (contains, regex, is-json, BLEU, ROUGE, embedding similarity), text statistics, retrieval scores (context precision and recall), audio, voice and image metrics, task-specific output metrics (summarisation, translation, SQL, code), instruction, role and topic adherence (they overlap plan adherence), and custom judges. A new metric needs at least two tools that provide it, and a metric that restates one already in the taxonomy is merged into it (for example conversation completeness and answer completeness count as Task / goal completion, and per-turn relevancy as Answer relevance). The 252 removed rows, with the reason, are in `data/interim/metrics_out_of_scope.csv`.

Two columns say how turnkey a row is (added 2026-10-26, and copied into `metric_taxonomy.csv` as counts):
- `delivery`: `automatic telemetry` (recorded by the tool's tracing or SDK), `convention` (an attribute or metric name defined by a standard such as OpenTelemetry or OpenInference, filled in by instrumentation), `dashboard or query` (a prebuilt dashboard, alert or query field) and `built-in evaluator` (a shipped evaluator that runs code or calls a model). The label is assigned by a rule on `kind`, the tool and the page type, and has not been checked row by row.
- `how_measured`: `telemetry`, `model judge` or `code check`, given only when the row's own description or quote says so. Otherwise `not stated`. 124 of the 140 evaluators are `not stated`, because the quoted text does not say whether a model or code does the scoring. Absence of a statement is not evidence of either.

A timing attribute (online during a run, after a run, or offline on a dataset) was not added: the documentation pages rarely say when a metric is computed, so any value would be the author's judgement, not evidence.

The collection used `built_in` values: `built-in` (ships with the tool, no user code), `custom-only` (generic mechanism where the user supplies the criteria), `via-integration` (provided by a third-party library the tool wraps), `community` (tagged community in the docs). `kind` is `evaluator` or `telemetry` (measure captured automatically, such as latency, tokens, cost).
Every quote in `built_in_metrics.csv` was checked by script to appear word for word in its saved page.

## Limitations

- OpenInference's evaluation field is custom-only (the producer supplies the criterion and score), so its rows are token and cost attributes only.
- C1 reduced the list to 13 tools. MLflow and Evidently were first in the top 15, then removed under C1 (0 independent Google sources; MLflow's 8 hits are all its own site). Other widely used tools with no third-party mention in the first 30 results of the 8 Google queries are also absent (for example Harbor, Giskard, TruLens, AgentOps). The Google counts reflect what ranks in those queries, not usage.
- Benchmarks and eval harnesses (SWE-bench, τ-bench, Inspect AI) are out of scope: S1 removes benchmarks, although I4 in the protocol would admit them through the literature channel. Metrics such as pass^k that come from them are therefore not in the tables.
- Five metrics are provided by a single tool (Step count, Plan quality, Action progress toward goal, Tool response handling, Tool call efficiency). They come from the first collection and were not held to the two-tool rule used for the output-quality metrics.
- The tool is called "Weights & Biases" in the screening files and "Weights & Biases Weave" in `results/`; only the Weave toolkit is studied.

- Google counts come from result titles and snippets only; pages were not opened.
- Ranking by stars favours open-source tools: closed-source tools can only rank on Google sources.
- Metrics come from official documentation pages. Metrics that exist only in a tool's source code, and not in its docs, are not listed (checked for OpenLLMetry only). On 2026-10-26 the three tools with the fewest rows were re-read: OpenInference (token and cost attributes were missing and were added), Helicone (four alert metrics were added from its alerts page) and Weave (its Call schema page confirms the latency, error, token and cost rows already present; nothing was added). Braintrust (nine `metrics.*` fields from its SQL reference were added) and Langfuse (its metrics pages add nothing beyond the token, cost and latency rows present) were re-read the same day. The other eight tools' saved dashboard and metrics pages were compared with their rows on the same day (one gap found: Phoenix's trace count, added), and Galileo's docs index was searched for operational metrics (none found in the pages read). This was a comparison of the pages already saved, not a full re-read of every documentation page.
- Row counts are not comparable across tools: some docs list individual prompt templates or assertion types, others list fewer, broader metrics.
- Download counts are only corroboration. They include installs triggered as dependencies of other packages (for example `langsmith`, `mlflow`) and CI downloads. They are blank for tools without a representative package: Helicone is used through an API proxy, and the only `helicone` package on PyPI is an old OpenAI wrapper. The OpenTelemetry figure is the general semantic-conventions library, not AI-specific.
