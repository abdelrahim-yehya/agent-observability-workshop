# Tool screening rules (S1 to S4)

Applies to the 42 tools in `combined_tools_no_duplicates.csv`.
Result per tool: `tools_scope_screening.csv`.

These rules replace T1, M1, E6 and C1 from earlier drafts. S1 and S2 use only
the tool's own description. S3 and S4 use the metric inventory
(`metric_inventory_candidates.csv`, then `real_metrics.csv`). The rules are
fixed before the S3/S4 results are read. Any later change goes in the change
log at the bottom.

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
Keep an S1 tool only if its code or official documentation shows at least one
**built-in metric**.

A metric is built-in if the tool itself ships it (in its main repository or its
official documentation) and it is not:
- user-written or user-defined (for example a generic judge where you supply the
  criteria),
- a community or third-party metric (for example the metrics DeepEval's docs tag
  as community),
- an infrastructure attribute that is not a measurement (for example
  `gen_ai.request.temperature`).

Open-source tools: checked with `github_metric_inventory.py` and
`filter_real_metrics.py` (evidence: commit, file, line), then reviewed by hand.
Tools without a public repository: official documentation, with URL and access
date. Output: `s3_builtin_metric_count`, `s3_decision`.

## S4 Coverage: keep a tool only if it adds something
Within each role, order the S3 survivors by independent evidence: first by
`google_independent_sources` (empty counts as 0), then by GitHub stars. The
order is fixed before metric coverage is looked at.

Walk the list from the top. **Keep** a tool if it provides at least one
built-in metric, mapped to a taxonomy metric, that no earlier kept tool
provides. **Remove** it otherwise. Report each removed tool together with the
(empty) set of metrics it would have added.

Output: `s4_decision`, `final_status` (studied, screened out, pending).

## Status
| Rule | Status |
|---|---|
| S1 | applied to all 42 (descriptions only) |
| S2 | applied to the 31 S1 tools |
| S3 | pending: needs inventory on all in-scope repos and a review pass |
| S4 | pending: needs the taxonomy mapping |

## Change log
- 2026-10-23: rules written. They replace T1, M1, E6, C1.
