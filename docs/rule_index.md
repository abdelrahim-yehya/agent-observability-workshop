# Rule index

Every rule ID used in this repo, defined once. The full text is in the file named in the last column. If two documents disagree, that file wins.

## Tool search and selection

| ID | Rule | Defined in |
|---|---|---|
| I1 | Inclusion: primary purpose is tracing, monitoring or evaluating LLM applications or agents | `search_protocol.md` |
| I2 | Inclusion, open source: at least 1,000 GitHub stars, not archived, a push or release in the last 6 months | `search_protocol.md` |
| I3 | Inclusion, closed source: public documentation, and named in at least two independent sources in Channel 2 (Google) | `search_protocol.md` |
| E1 | Exclude LLM gateways and proxies whose main purpose is routing | `search_protocol.md` |
| E2 | Exclude agent-building frameworks | `search_protocol.md` |
| E3 | Exclude model-level benchmark harnesses that do not evaluate agents | `search_protocol.md` |
| E4 | Exclude tutorials, course material and "awesome" lists | `search_protocol.md` |
| E5 | Exclude duplicates: an SDK and its platform count as one tool | `search_protocol.md` |
| E6 | Exclude general-purpose observability, APM, data, security or ML platforms whose LLM support is a module (exception: an LLM-specific product distributed on its own, such as W&B Weave) | `search_protocol.md` |
| C1 | Corroboration, closed-source tools only (revised 2026-11-09): at least two independent sources name it; its own website does not count | `search_protocol.md` |
| C2 | Adoption, open-source tools (added 2026-11-09): passes I2 and has at least 5,000 stars or at least 1M downloads in 30 days (PyPI or npm), with at least 100k downloads when a package exists | `search_protocol.md` |

## Tool screening of the 42 candidates

| ID | Rule | Defined in |
|---|---|---|
| S1 | Scope: keep a tool whose own description gives observability or evaluation of LLM applications or agents as its primary purpose; benchmarks and datasets are removed | `screening_rules.md` |
| S2 | Role: label each S1 tool as standard, platform or framework; no removal | `screening_rules.md` |
| S3 | Built-in metrics: a tool is useful for the metrics table only if its official documentation shows at least one built-in metric. Applied to the 13 selected tools during metric collection | `screening_rules.md` |
| S4 | Selection: closed-source tools pass C1, open-source tools pass C2 (revised 2026-11-09; before that C1 applied to every tool and gave 13 entries); ranking per group; the original coverage rule was not applied | `screening_rules.md` |
| A1 | Agent relevance: official documentation explicitly covers agents, tool calls or multi-step traces. An amendment to the protocol; the paper must report it | `README.md`, evidence in `data/outputs/a1_agent_relevance.csv` |

## Metrics

| ID | Rule | Defined in |
|---|---|---|
| M1 | Metric scope: keep only built-in metrics that describe how an agent run executes or how good its output is (execution aspects plus answer quality, grounding, safety and conversation). Text-match and format checks, retrieval scores, audio/voice/image and task-specific metrics are out; a metric provided by one tool is kept, and one that restates an existing metric is merged into it. Removed rows, with reasons, are in `data/interim/metrics_out_of_scope.csv`. An amendment to the protocol; the paper must report it. Unrelated to tool screening | `README.md` (Scope) |

## Matrix statuses

The cell statuses of `results/tool_metric_matrix.csv` are defined in `README.md` (How to read the matrix) and in the header of `src/build_matrix.py`.

## Known overlaps

- Benchmarks are out of scope under S1. The old rule I4 (benchmarks through a literature channel) was dropped with that channel on 2026-10-30.
- Earlier drafts had a rule called T1. It was never defined in the repo and has been dropped.
