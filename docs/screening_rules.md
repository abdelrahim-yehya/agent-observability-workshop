# Tool screening rules (S1 to S4)

Applies to the 42 tools in `combined_tools_no_duplicates.csv`.
Result per tool: `tools_scope_screening.csv`.

These rules supersede the tool-screening rules of earlier drafts. E6 and C1
stay in force as defined in `search_protocol.md`. M1 is the metric scope rule
and is unrelated to tool screening. S1 and S2 use only
the tool's own description. S3 and S4 use the documented built-in metrics and the ranking. Any change
goes in the change log at the bottom.

## Goal
Keep the smallest set of tools that represents agent observability and
evaluation, and that together document the built-in metrics worth putting in the
paper's metrics x tools table.

## S1 Scope: primary purpose
**Keep** a tool if its own description (GitHub repository description, README
first section, or vendor page) says its primary purpose is the **observability**
(tracing, monitoring, logging of runs) or **evaluation** (evals, testing,
scoring) of LLM applications or AI agents.

**Remove** a tool if its primary purpose is one of:
- security scanning or red-teaming only (mixed tools where evaluation is the
  primary purpose stay in, for example promptfoo)
- a benchmark or dataset
- a prompt file format or asset type
- testing of one protocol (for example MCP servers)
- a broader suite where observability or evaluation is only one module (data
  generation, fine-tuning, and so on)
- an end-user application
- a general-purpose observability platform (logs, metrics and traces for any
  software) where LLM support is one feature

**Borderline** cases are marked `verify`. They stay out unless the README states
that observability or evaluation of AI agents is the primary purpose.

Decided from descriptions only. Input: `description`. Output: `s1_decision`
(in, out, verify) and `s1_reason`.

## S2 Role: label, no removal
Give each S1 tool exactly one role. At least one tool per role is studied.
- **standard**: defines telemetry conventions or instrumentation libraries for
  LLM/agent traces. It has no backend UI or evaluators of its own.
- **platform**: an application (self-hosted or hosted) that stores and shows
  traces and also offers evaluation or monitoring.
- **framework**: a library or CLI that runs evaluations or tests, with no trace
  backend of its own.

Output: `s2_role`.

## S3 Built-in metrics: the tool documents at least one
A tool is useful for the metrics table only if it documents at least one
**built-in metric**.

A metric is built-in if the tool itself ships it (in its official documentation)
and it is not:
- user-written or user-defined (for example a generic judge where you supply the
  criteria),
- a community or third-party metric (for example the metrics DeepEval's docs tag
  as community),
- provided only through a third-party integration,
- an infrastructure attribute that is not a measurement (for example
  `gen_ai.request.temperature`).

**As applied:** S3 was not run as a separate filter over all 31 tools. It was
applied to the 15 selected tools while collecting `results/built_in_metrics.csv`,
with the evidence rule in `CLAUDE.md` (URL, saved page, verbatim quote, access
date). A tool with no built-in agent-execution metric is still reported, with
zero rows (OpenInference and Evidently).

The columns `s3_candidate_rows` and `s3_note` in `tools_scope_screening.csv` are
notes from an early keyword scan of the repositories. That scan's scripts and
outputs are not part of this repository and its results are not used.

## S4 Selection: rank and take the top 15
**As applied:** the 31 S1 tools were checked for A1 (agent relevance, in
`data/outputs/a1_agent_relevance.csv`), ranked by `google_independent_sources`
(empty counts as 0), then by GitHub stars, and the top 15 were taken
(`results/best_tools.csv`). The order was fixed before metric coverage and
download counts were looked at.

The original S4 plan was a coverage rule (keep a tool only if it adds a
built-in metric that no earlier tool provides). It was not applied, because the
study reports every selected tool's metrics, including overlaps.

Known tension with C1: Evidently (rank 15) had fewer than two independent
Google sources and was marked `exclude` under C1 in
`data/inputs/tool_screening_google.csv`; MLflow (rank 14) was left `pending`.
Both entered through the ranking rule, which takes the top 15 whatever their
source count. This is reported as a limitation in `README.md`.

Columns `s3_decision`, `s4_decision` and `final_status` in
`tools_scope_screening.csv` record this outcome.

## Status
| Rule | Status |
|---|---|
| S1 | applied to all 42 (descriptions only): 31 in, 10 out, 1 verify (treated as out) |
| S2 | applied to the 31 S1 tools |
| S3 | applied to the 15 selected tools through the metric collection (see above) |
| S4 | applied as ranking, top 15 (see above); the original coverage rule was not used |

## Change log
- 2026-10-23: rules written. They supersede the tool-screening rules of earlier drafts.
- 2026-10-26: removed the reference to T1 (never defined in the repo) and clarified
  that E6 and C1 remain in force and M1 is the metric scope rule.
- 2026-10-26: S3 and S4 rewritten to describe what was done. The scanner scripts and
  files they named (`github_metric_inventory.py`, `filter_real_metrics.py`,
  `metric_inventory_candidates.csv`, `real_metrics.csv`) were never part of this
  repository and are no longer referenced.
