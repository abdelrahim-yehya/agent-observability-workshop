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
applied to the 13 selected tools while collecting `results/built_in_metrics.csv`,
with the evidence rule in `CLAUDE.md` (URL, saved page, verbatim quote, access
date). A tool with no built-in agent-execution metric is still reported, with
zero rows.

An early keyword scan of the repositories (columns `s3_candidate_rows` and
`s3_note`, now removed from `tools_scope_screening.csv`) is not part of this
repository and its results were not used.

## S4 Selection: C1, then rank
**As applied:** the 31 S1 tools were checked for A1 (agent relevance, in
`data/outputs/a1_agent_relevance.csv`; each A1 page is saved as
`data/raw/doc_snapshots/a1__<tool>.txt`). C1 (at least two independent sources,
from `google_independent_sources`; empty counts as 0) was then applied. 13 tools
pass; the other 18 have no independent source, so the list is 13 tools. The 13
are ranked by `google_independent_sources`, then GitHub stars
(`results/best_tools.csv`). The order was fixed before metric coverage and
download counts were looked at.

The first selection took the top 15 and let MLflow and Evidently in with 0
independent sources. C1 was applied on 2026-10-26 and both were removed (their
rows are in `data/interim/c1_removed/`).

**Revised 2026-11-09:** C1 now applies to closed-source tools only and open-source tools must pass C2 (adoption: stars, downloads,
activity); see `search_protocol.md`. The statement above that the order was fixed before download counts were looked at
holds for the first selection only; the revision was made after the adoption data were read. The 13-entry C1 selection is
kept as a sensitivity comparison.

The original S4 plan was a coverage rule (keep a tool only if it adds a
built-in metric that no earlier tool provides). It was not applied, because the
study reports every selected tool's metrics, including overlaps.

Columns `s3_builtin_metric_count`, `s3_decision`, `s4_decision` and
`final_status` in `tools_scope_screening.csv` record this outcome.

## Status
| Rule | Status |
|---|---|
| S1 | applied to all 42 (descriptions only): 31 in, 10 out, 1 verify (treated as out) |
| S2 | applied to the 31 S1 tools |
| S3 | applied to the 16 selected entries through the metric collection (see above) |
| S4 | first selection: C1 then ranking, 13 entries; revised 2026-11-09: C1 for closed-source tools, C2 for open-source tools, 16 entries (see above); the original coverage rule was not used |

## Change log
- 2026-10-23: rules written. They supersede the tool-screening rules of earlier drafts.
- 2026-10-26: removed the reference to T1 (never defined in the repo) and clarified
  that E6 and C1 remain in force and M1 is the metric scope rule.
- 2026-10-26: S3 and S4 rewritten to describe what was done. The scanner scripts and
  files they named (`github_metric_inventory.py`, `filter_real_metrics.py`,
  `metric_inventory_candidates.csv`, `real_metrics.csv`) were never part of this
  repository and are no longer referenced.
- 2026-10-26: C1 applied to the selection. MLflow and Evidently removed, list is 13 tools. A1 snapshots added.
  Stale scanner columns removed from `tools_scope_screening.csv`.
- 2026-11-05: the paper reports the 13 entries that passed C1 as ten tools (platforms and frameworks) plus three
  standards (role `standard`). The data and the ranking are unchanged; only the wording and the tool table's grouping changed.
- 2026-11-09: MLflow, Laminar and LangWatch added (C2; MLflow through an E6 exception); Evidently and Harbor left out. 33 built-in rows collected;
  Fluency added as a unique metric. `data/interim/c1_removed/` now holds only Evidently's rows.
- 2026-11-09: search strategy changed (post-hoc): open-source tools by adoption (C2), Google for closed-source tools (C1
  revised), E1 to E6, S1, A1 unchanged. Candidates, adoption data and E-rule verdicts are in
  `data/outputs/open_source_adoption_candidates.csv`.
- 2026-11-05: rules audited and kept (user's decision, option 1). No tool outside the 13 passes them; Ragas fails I2 on activity.
  The selection is described as "most widely named", not "most important". Excluded high-adoption tools (MLflow, Laminar,
  Evidently, LangWatch, OpenLIT) and Ragas are in `data/outputs/excluded_tools_sensitivity.csv` and in the paper's Limitations.
- 2026-11-05: DeepEval and its cloud platform Confident AI stay one entry under E5, now with role platform and
  metrics from both sets of docs (23 evaluator rows from deepeval.com, 8 observability rows from the Confident AI docs).
  3 of its 12 independent sources name only Confident AI (9 name DeepEval).
- 2026-11-05: OpenLLMetry stays in the list as a standard, library only. Its 18 evaluator rows were Traceloop
  platform pages, not the library, and Traceloop is not added as a tool (it has no independent Google sources, so it
  would also fail C1). Rows, mappings and page snapshots moved to `data/interim/traceloop_platform_removed/`;
  `s3_builtin_metric_count` for OpenLLMetry is now 10.
