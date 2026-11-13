# Changelog review: procedure (2026-11-11 and 2026-11-12)

This is the procedure given to each reviewer of the changelog channel. It is kept as the record of what was done.

## Why
`results/built_in_metrics.csv` holds the built-in metrics found in each tool's official documentation pages. Documentation pages turned out not to be enough: Langfuse announced a tool-call count only in a changelog entry, so the dataset said Langfuse does not document it. On 2026-11-11 the author decided that changelog and release-notes pages published by the vendor count as official documentation, for every tool. The review looks for built-in metrics the first collection missed.

## What to do, per entry
1. Find the vendor's own changelog or release notes: a "changelog", "release notes" or "what's new" page on the vendor's site, and/or GitHub Releases / CHANGELOG.md of the official repository. A web search may be used only to locate URLs.
2. Download the raw text with `curl` (never a summarising fetch tool: its output is not evidence). Docs sites are often JavaScript-rendered: try the page's `.md` URL, `/llms.txt`, the docs source in the GitHub repository, or the GitHub API (`https://api.github.com/repos/<owner>/<repo>/releases?per_page=100&page=N`). If the download is HTML, strip the tags to plain text before saving.
3. Cover the whole changelog history that is available. Work economically: do not print whole files. Shortlist entries with `grep -n -i` on keywords (metric, evaluator, eval, judge, scorer, score, token, cost, latency, duration, time to first token, tool call, error rate, count, dashboard, trace, span, session, agent, trajectory, hallucination, faithfulness, groundedness, toxicity, PII, guardrail, moderation), then read each shortlisted entry in full with a line range.
4. Compare with what is already recorded: filter `results/built_in_metrics.csv` by `tool` for the tool-specific metrics already there; read `data/inputs/taxonomy_definitions.csv` (the 46 unique metrics with definitions, plus one metric only standards document) and `data/inputs/taxonomy_mapping.csv` (tool metric -> unique metric). `data/interim/metrics_out_of_scope.csv` lists metrics already seen and set aside for that tool: do not propose them again.
5. Propose a row for every in-scope built-in metric that the changelog documents and that is NOT already recorded for that tool under the same tool-specific name.

## Rules that decide what counts
- **Built-in**: the tool itself ships it and the user writes no code for it. NOT built-in: user-written or user-defined metrics (for example a generic judge where the user supplies the criteria), community or third-party metrics, metrics available only through a third-party integration, and infrastructure attributes that are not measurements (for example `gen_ai.request.temperature`, model name, request parameters).
- **Scope (rule M1)**: keep only metrics that describe how an agent run executes (tool use, task/goal, plan/trajectory, tokens, cost, latency, errors, counts of traces/spans/calls) or how good its output is (answer quality, grounding/faithfulness, safety, conversation). OUT of scope: text-match and format checks (exact match, regex, JSON validity, BLEU/ROUGE), retrieval scores (context precision/recall, retrieval relevance), audio, voice, image and multimodal metrics, task-specific metrics (SQL, summarization, code), red-teaming attack plugins, and generic custom judges.
- A changelog entry describes the product on its release date. If a later entry or the current documentation shows the metric was removed, renamed or deprecated, say so in `note` and in the report, with the current name.
- If a changelog entry shows that a metric ALREADY recorded was removed, renamed or deprecated, report that too.
- Be conservative: propose a row only when the page states the metric plainly. If unsure whether something is built-in or in scope, still list it, set `confidence` to `low` and explain in `note`.

## Evidence rules (strict)
- Save every page quoted under `data/interim/changelog_review/snapshots/` as `<toolslug>__changelog-<short-name>.txt`. For a very large changelog, save the whole file once and quote from it.
- `quote` must be copied verbatim from the saved file, be at least 20 characters, and name the metric. Verify every quote before finishing (whitespace collapsed on both sides):
  `python3 -c "import re,sys; t=re.sub(r'\s+',' ',open(sys.argv[1],encoding='utf-8',errors='replace').read()); q=re.sub(r'\s+',' ',sys.argv[2]).strip(); print(len(q)>=20 and q in t)" <snapshot> "<quote>"`
- `access_date` is the day the quoted file was downloaded: 2026-11-12 for anything downloaded now, 2026-11-11 for files that were already in `snapshots/` or in the scratch folders named in the task.

## Output files (write only inside `data/interim/changelog_review/`; nothing else in the repository is edited)
Per entry, `<toolslug>__proposed.csv` (header even if there are no rows), written with Python's `csv` module, columns:
`tool,metric_name,kind,agent_aspect,description,doc_url,snapshot_file,quote,access_date,note,how_measured,delivery,entry_date,proposed_taxonomy_metric,already_covered,confidence`
- `kind`: `telemetry` or `evaluator`
- `agent_aspect`: one or more of tool_use, task_goal, plan_trajectory, tokens, cost, latency, errors, counts, answer_quality, grounding, safety, conversation (joined with `; `)
- `description`: one sentence, close to the page's wording
- `doc_url`: the public URL of the changelog entry or release
- `how_measured`: `telemetry`, `model judge`, `code check` or `not stated`
- `delivery`: `automatic telemetry`, `dashboard or query`, `convention` (standards) or `built-in evaluator`
- `entry_date`: date of the changelog entry or release (YYYY-MM-DD)
- `proposed_taxonomy_metric`: the exact name of the unique metric(s) it maps to (several joined with `; `), or `NEW: <short name>` if none fits
- `already_covered`: `yes` if the tool already has a built-in row mapped to that unique metric (the new row would not change the tool x metric matrix), else `no`
- `confidence`: `high` or `low`

Per entry, `<toolslug>__log.csv` with columns `tool,changelog_url,how_read,entries_total,date_range,entries_read_in_full,comment`: one line per changelog source used, saying plainly if a source could not be read or was only partly covered.

## Report (under 350 words)
Per entry: which changelog sources were read and how completely; the proposed rows as a short list (metric name -> unique metric, already_covered yes/no, confidence); anything removed, renamed or deprecated; anything that could not be checked. No page contents.
