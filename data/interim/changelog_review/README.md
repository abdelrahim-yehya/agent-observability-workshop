# Changelog review (2026-11-11 and 2026-11-12)

**Status: applied on 2026-11-12** with the author's approval. The 33 accepted rows are in `results/built_in_metrics.csv` (their `note` starts with "changelog channel"), their pages in `data/raw/doc_snapshots/`, the 50 pairs in `data/inputs/taxonomy_mapping.csv`. The author decided the taxonomy stays as it is, so the candidates that would need a new unique metric were not added. The two renamed OpenTelemetry rows were kept with a note and the new names added.

## Why
The first collection read documentation pages only. Langfuse ships a tool-call count that is announced only in a changelog entry, so the dataset marked it "not documented". On 2026-11-11 the author decided that changelog and release-notes pages published by the vendor count as official documentation, for all 16 entries. This is an amendment to the protocol and must be reported in the paper.

## Files
| File | What it is |
| --- | --- |
| `BRIEF.md` | The procedure every reviewer followed (sources, built-in rule, scope rule M1, evidence rules, output format) |
| `<tool>__log.csv` | Per entry: which changelog sources were read, how, how many entries, the date range, and what could not be read |
| `<tool>__proposed.csv` | Per entry: every row a reviewer proposed, with URL, saved page, verbatim quote, access date and entry date |
| `snapshots/` | The saved copy of every page quoted (37 files) |
| `review_decisions.csv` | All 103 proposals with `decision` (accept / not added), `reason`, and the final mapping |
| `accepted_rows.csv` | The 33 rows that would be added to `results/built_in_metrics.csv`, with the unique metric(s) each maps to (50 pairs) |

## Evidence
Every proposed and accepted row carries a public URL, the saved page, a verbatim quote of at least 20 characters and the access date. Check them with:

    python3 src/check_quotes.py data/interim/changelog_review/accepted_rows.csv data/interim/changelog_review/snapshots

(33 rows checked, 0 failed on 2026-11-12; all 103 proposals also pass.)

## Result if applied
264 -> 297 evidence rows, 326 -> 376 mapping pairs, 36 tool-by-metric cells become built-in (34 for the 13 tools, 2 for OpenLLMetry). The 46 unique metrics do not change.

## Open decisions (author)
1. Three patterns fit none of the 46 unique metrics and were not added: session count and duration (Phoenix, MLflow), automatic issue detection (MLflow, Braintrust), and single-tool evaluators for sycophancy (Opik) and response trust (Weave).
2. OpenTelemetry: the development branch merged `gen_ai.invoke_workflow.duration` into `gen_ai.invoke_agent.duration` and moved inference timing from `gen_ai.client.operation.duration` to `gen_ai.client.inference.duration`. Proposal: keep the recorded rows with a note and add the new names.
3. Four accepted rows rest on thin wording: Helicone time to first token, Opik PromptInjection, Opik bias detection, and Galileo "Latency" (read as per trace).

## Coverage limits (to report in the paper)
- LangSmith: the cloud changelog starts in January 2025; the self-hosted and Fleet changelogs were not read.
- Weave: the release-notes page redirects to a login; only GitHub release titles were read.
- Arize Phoenix: entries before September 2025 were read from GitHub releases, not the release-notes pages.
- LangWatch releases before October 2025 and the Braintrust SDK changelogs were keyword-searched, not read in full.
- OpenTelemetry: the GenAI conventions repository has no release, so its unreleased changelog fragments were used (no entry dates).
- Langfuse: besides the changelog, four documentation pages missed by the first collection were read.

## To apply (after review)
Copy the snapshots of accepted rows to `data/raw/doc_snapshots/`, append the rows to `results/built_in_metrics.csv` and the pairs to `data/inputs/taxonomy_mapping.csv`, then run `build_taxonomy.py`, `build_matrix.py`, `check_quotes.py`, `plot_taxonomy_coverage.py`, `build_tool_table.py` and `build_site.py`, and update the paper's numbers, method and limitations.
