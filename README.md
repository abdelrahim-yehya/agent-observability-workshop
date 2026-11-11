# Agent observability and evaluation tools: tool selection and built-in metrics

Goal: (1) identify the tools most widely named in public sources for observability and evaluation of AI agents (visibility in the searches, not usage), and (2) list the built-in metrics each one provides. Every claim in the results has a source URL, a verbatim quote and an access date.

## Results (`results/`)

| File | Content | Status |
|---|---|---|
| `best_tools.csv` | The 16 selected entries: 13 tools (12 platforms, 1 framework) and the three standards beneath them (OpenTelemetry, OpenLLMetry, OpenInference; role `standard`), with the evidence for each selection criterion | done |
| `metric_taxonomy.csv` | The 46 unique metrics, split into Observability (18, measurements captured from a run) and Evaluation (28, judgements of agent behaviour and output) and grouped in 13 categories (6 under Observability, 7 under Evaluation; "Tool use" and "Plan and trajectory" appear under both), with a definition and the list of tools that support each. `metric_taxonomy_diagram.svg` and `.png` draw it as a tree, one dot per tool that documents each metric (built by `src/plot_taxonomy.py`; `--no-tools` draws it without tools, and `src/plot_taxonomy_alt.py` draws two alternative tool-free layouts, `metric_taxonomy_cards` and `metric_taxonomy_radial`). `metric_taxonomy_coverage.svg` is the paper's Fig. 3, the taxonomy against the ten non-standard tools (built by `src/plot_taxonomy_coverage.py`) | draft for review |
| `standards_only_metrics.csv` | Metrics that only standards document as built-in and no studied tool provides (currently one: Time per output token / generation time). They keep their definition and evidence but are not part of the 45; the list is `data/inputs/taxonomy_standards_only.csv`, and `src/build_taxonomy.py` stops if a metric is on the list that a tool provides, or off the list but provided by standards only | draft for review |
| `tool_metric_matrix.csv` | The 46 metrics against the 16 entries (13 tools and three standards), one status per cell (built-in, integration, community, template, generic custom, records scores, not documented). `tool_metric_matrix_long.csv` has the same cells one per row, with the tool's own metric names, delivery and the doc URL. `tool_metric_matrix.html` is the same matrix drawn as a heatmap with the status legend (open it in a browser; built by `src/plot_matrix.py`) | draft for review |
| `built_in_metrics.csv` | 264 built-in metrics from the 16 entries (226 from the 13 tools, 38 from the three standards; rule M1). The entry named `DeepEval` is DeepEval plus its cloud platform Confident AI, merged by E5 (role: platform): its 23 evaluator rows come from deepeval.com and its 8 observability rows from the Confident AI docs (`confidentai__*` snapshots). Each row has the doc URL, a verbatim quote, the saved page it was copied from, and the access date | first pass done, being reviewed |

## Motivating example (`example_rag/`)

The paper's worked example: a course chatbot (one LLM with two tools over four course transcripts) asked twelve scripted questions, traced with Langfuse and scored offline with the built-in evaluators of Arize Phoenix and DeepEval. [`example_rag/README.md`](example_rag/README.md) lists the questions, the scripts, the recorded results and what is not redistributed (the course transcripts and keys).

## How the tools were selected

Rules are in [`docs/screening_rules.md`](docs/screening_rules.md) (S1–S4) and [`docs/search_protocol.md`](docs/search_protocol.md) (search channels, inclusion and exclusion criteria). [`docs/rule_index.md`](docs/rule_index.md) lists every rule ID once and says where it is defined.

1. **Discover**: GitHub search (182 repos, run 2026-10-22) plus a manual Google search (173 results, same day) → 42 tools.
2. **S1 scope**: primary purpose is observability or evaluation of LLM apps or agents → 31 tools in, 10 out, 1 on hold (iFixAi, treated as out).
3. **A1 agent relevance** (amendment to the protocol): official docs explicitly cover agents, tool calls or multi-step traces. Quotes were checked against the raw page text, and re-checked against the live pages on 2026-10-26 (all 13 found). Each A1 page is saved as `data/raw/doc_snapshots/a1__<tool>.txt` and its quote appears verbatim in it (for DeepEval the markdown backticks around `deepeval` were dropped, because the rendered page shows that word in code font).
4. **Select**: closed-source tools must pass C1, at least two independent Google sources (its own website does not count); open-source tools must pass C2, adoption by GitHub stars, PyPI/npm downloads and activity (amendment of 2026-11-09, made after the first selection; see `docs/search_protocol.md`). The first selection applied C1 to every tool: 13 of the 31 S1 tools passed; the other 18 have none, so the list has 13 entries (ten tools and three standards), not the 15 first planned. MLflow (28k stars, but all 8 Google results naming it are on mlflow.org) and Evidently fail C1 and are removed; their rows are kept in `data/interim/c1_removed/`. Under the amendment the result is 16 entries: 13 tools (9 open-source, 4 closed-source) and 3 standards. C2 added MLflow, Laminar and LangWatch (metric rows collected 2026-11-09); Evidently (E6) and Harbor (S1/E3) passed C2 but were left out, and Pydantic Logfire is out under E6; MLflow is in through an E6 exception for `mlflow-tracing`, an LLM-specific package distributed on its own.
5. **Rank** (first selection) the 13 by independent Google sources, then GitHub stars; under the 2026-11-09 amendment open-source tools are ordered by downloads, then stars, and closed-source tools by Google sources. S3 (built-in metrics) was applied while collecting the metrics, and the original S4 coverage rule was replaced by this ranking (see `docs/screening_rules.md`).
6. **Corroborate downloads**: add last-month PyPI and npm downloads (`pypi_downloads_last_month`, `npm_downloads_last_month` in `best_tools.csv`, from the pypistats.org and npm download APIs on 2026-10-26). In the first selection downloads were reported next to the ranking and did not change it. The 2026-11-09 amendment then made adoption (stars, downloads, activity) the selection rule for open-source tools; that is a post-hoc change and the paper reports both selections. Each package was matched to its tool through the repository or author listed in its PyPI metadata.

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

Every one of the 13 tools except OpenLLMetry has a custom-evaluator or score-recording row in `metrics_out_of_scope.csv`, and the script stops if one is missing (OpenLLMetry is listed in `NO_EVALUATOR_DOCS`: its library pages document no evaluator, so its Evaluation cells read "not documented"), so "generic custom" and "records scores" always rest on a quoted page. They say the metric could be built, not that it exists. The integration, community and template cells come from `data/inputs/taxonomy_mapping_not_built_in.csv`, a hand-made mapping of those rows, and cover only the metrics that were in scope when the rows were collected. Counts of built-in cells per tool are not capability scores: documentation lists metrics at different granularity.

## How the metrics were collected

**Scope (M1):** only built-in metrics that describe how an agent run executes or how good its output is are kept. Execution: `tool_use` (selection, invocation, arguments, errors, efficiency), `task_goal`, `plan_trajectory`, and run telemetry (`tokens`, `cost`, `latency`, `errors`, `counts`). Output quality: `answer_quality` (correctness, relevance, helpfulness, conciseness, tone), `grounding` (faithfulness to context), `safety` (toxicity, bias, data leakage, injection, refusal, policy violations) and `conversation` (knowledge retention, user satisfaction, conversation coherence). Out of scope: text-match, format and reference-overlap checks (contains, regex, is-json, BLEU, ROUGE, embedding similarity), text statistics, retrieval scores (context precision and recall), audio, voice and image metrics, task-specific output metrics (summarisation, translation, SQL, code), instruction, role and topic adherence (they overlap plan adherence), and custom judges. A metric provided by one tool is kept, and a metric that restates one already in the taxonomy is merged into it (for example conversation completeness and answer completeness count as Task / goal completion, and per-turn relevancy as Answer relevance). The 252 removed rows, with the reason, are in `data/interim/metrics_out_of_scope.csv`.

Two columns say how turnkey a row is (added 2026-10-26, and copied into `metric_taxonomy.csv` as counts):
- `delivery`: `automatic telemetry` (recorded by the tool's tracing or SDK), `convention` (an attribute or metric name defined by a standard such as OpenTelemetry or OpenInference, filled in by instrumentation), `dashboard or query` (a prebuilt dashboard, alert or query field) and `built-in evaluator` (a shipped evaluator that runs code or calls a model). The label is assigned by a rule on `kind`, the tool and the page type, and has not been checked row by row.
- `how_measured`: `telemetry`, `model judge` or `code check`, given only when the row's own description or quote says so. Otherwise `not stated`. 124 of the 140 evaluators are `not stated`, because the quoted text does not say whether a model or code does the scoring. Absence of a statement is not evidence of either.

A timing attribute (online during a run, after a run, or offline on a dataset) was not added: the documentation pages rarely say when a metric is computed, so any value would be the author's judgement, not evidence.

The collection used `built_in` values: `built-in` (ships with the tool, no user code), `custom-only` (generic mechanism where the user supplies the criteria), `via-integration` (provided by a third-party library the tool wraps), `community` (tagged community in the docs). `kind` is `evaluator` or `telemetry` (measure captured automatically, such as latency, tokens, cost).
Every quote in `built_in_metrics.csv` was checked by script to appear word for word in its saved page.

## Limitations

- OpenInference's evaluation field is custom-only (the producer supplies the criterion and score), so its rows are token and cost attributes only.
- The first selection (C1 for every tool) left 13 entries and dropped widely used open-source tools that Google did not name (for example MLflow, Laminar, LangWatch). The 2026-11-09 amendment replaced C1 for open-source tools by an adoption rule (C2), whose thresholds were chosen after seeing the data. Still out: Ragas (inactive since 2026-02-24, I2), Evidently and Pydantic Logfire (E6), Harbor (S1/E3), and tools below the thresholds (OpenLIT, AgentOps, Giskard). The Google counts for closed-source tools reflect what ranks in those queries, not usage. See `data/outputs/open_source_adoption_candidates.csv` and `excluded_tools_sensitivity.csv`.
- Benchmarks and eval harnesses (SWE-bench, τ-bench, Inspect AI) are out of scope: S1 removes benchmarks (the literature channel and rule I4 that would have admitted them were dropped). Metrics such as pass^k that come from them are therefore not in the tables.
- Six metrics are provided by a single entry (Step count, Plan quality, Action progress toward goal, Tool response handling, Flow and reasoning coherence, Fluency). Fluency (MLflow's scorer "Is the response grammatically correct and naturally flowing?") is the one unique metric added with the 2026-11-09 tools. Some single-provider metrics come from the first collection and were not held to the two-tool rule used for the output-quality metrics; Flow and reasoning coherence lost its second provider when the Traceloop evaluator rows were removed from OpenLLMetry (2026-11-05).
- OpenLLMetry is studied as a standard (the open-source library only, 10 rows). Traceloop, the company behind it, sells a platform built on OpenLLMetry with its own evaluators; those pages are not part of the study and their 18 rows are in `data/interim/traceloop_platform_removed/`. Traceloop announced in March 2026 that it is joining ServiceNow and that OpenLLMetry will remain open source ([announcement](https://traceloop.com/blog/traceloop-is-joining-servicenow)).
- The tool is called "Weights & Biases" in the screening files and "Weights & Biases Weave" in `results/`; only the Weave toolkit is studied.

- Google counts come from result titles and snippets only; pages were not opened.
- Ranking by stars favours open-source tools: closed-source tools can only rank on Google sources.
- Metrics come from official documentation pages. Metrics that exist only in a tool's source code, and not in its docs, are not listed (checked for OpenLLMetry only). On 2026-10-26 the three tools with the fewest rows were re-read: OpenInference (token and cost attributes were missing and were added), Helicone (four alert metrics were added from its alerts page) and Weave (its Call schema page confirms the latency, error, token and cost rows already present; nothing was added). Braintrust (nine `metrics.*` fields from its SQL reference were added) and Langfuse (its metrics pages add nothing beyond the token, cost and latency rows present) were re-read the same day. The other eight tools' saved dashboard and metrics pages were compared with their rows on the same day (one gap found: Phoenix's trace count, added), and Galileo's docs index was searched for operational metrics (none found in the pages read). This was a comparison of the pages already saved, not a full re-read of every documentation page.
- Row counts are not comparable across tools: some docs list individual prompt templates or assertion types, others list fewer, broader metrics.
- Download counts are only corroboration. They include installs triggered as dependencies of other packages (for example `langsmith`, `mlflow`) and CI downloads. They are blank for tools without a representative package: Helicone is used through an API proxy, and the only `helicone` package on PyPI is an old OpenAI wrapper. The OpenTelemetry figure is the general semantic-conventions library, not AI-specific.
