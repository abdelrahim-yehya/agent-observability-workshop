# Agent observability tool discovery pipeline

This workspace builds a reproducible inventory of tools for tracing, monitoring, and evaluating LLM applications and agents. It combines an open-source GitHub channel with a screened Google-search channel, then removes duplicate tool identities across both sources.

The detailed research criteria and search queries are recorded in [`search_protocol.md`](search_protocol.md).

## Run the complete pipeline

Run the pipeline from this directory:

```bash
./run_pipeline.sh
```

The runner always starts from scratch with a live GitHub search. It then filters the new results and merges them with the tools marked `include` in `tool_screening_google.csv`.

The final deduplicated tool set is written to `combined_tools_no_duplicates.csv`. The same run then collects documentation and creates `tool_metrics.csv` with evidence-backed metric candidates.

## Pipeline

### 1. Discover GitHub repositories

[`github_tool_search.py`](github_tool_search.py) calls the GitHub repository search API using the topic and keyword queries defined in the protocol.

Every query applies these constraints:

- At least 1,000 stars.
- Not archived.
- Pushed within the previous 183 days.
- Sorted by stars, with up to 30 results per query.

The script removes repeated repository names while processing the queries and writes [`github_raw_results.csv`](github_raw_results.csv).

Run:

```bash
python3 github_tool_search.py
```

Set `GITHUB_TOKEN` before running to increase the API rate limit. This step performs live network requests, so stars, activity dates, and returned repositories can change over time.

### 2. Screen the GitHub results

[`filter_github_results.py`](filter_github_results.py) screens each repository using its name and GitHub description. It applies the exclusion categories from the protocol:

- E1: gateways and proxies.
- E2: agent-building frameworks and harnesses.
- E3: model-level evaluation or training harnesses.
- E4: tutorials, courses, guides, and curated lists.
- E5: duplicate repository names.
- Unrelated results without clear LLM or agent measurement scope.

The script creates two outputs:

- [`github_filtered_results.csv`](github_filtered_results.csv): retained GitHub tools.
- [`github_excluded_results.csv`](github_excluded_results.csv): excluded repositories with the criterion and reason.

Run:

```bash
python3 filter_github_results.py
```

Ambiguous exceptions can be maintained in `FORCE_INCLUDE` and `FORCE_EXCLUDE` near the top of the script.

### 3. Screen the Google-search channel

[`google_search_log.csv`](google_search_log.csv) records the raw search results and tool names found through the Google queries.

[`tool_screening_google.csv`](tool_screening_google.csv) is the final screening table. Each tool has:

- The number of independent sources and covered queries.
- A decision: `include`, `exclude`, or `pending`.
- The applied inclusion or exclusion rule.
- A written decision reason.

Only rows marked `include` enter the combined inventory through the Google channel. An `exclude` or `pending` Google decision does not remove a tool that independently passed the GitHub channel.

### 4. Merge the included tools

[`merge_tool_sources.py`](merge_tool_sources.py) combines the filtered GitHub file with the `include` rows from the Google screening file.

Deduplication uses a canonical tool key:

- Unicode, case, spaces, punctuation, hyphens, and underscores are normalized.
- Repository slugs are converted to public tool names.
- Known naming differences, such as `lmnr-ai/lmnr` → `Laminar` and `Arize-ai/phoenix` → `Arize Phoenix`, are mapped explicitly.
- Known branding variants can be maintained in `NAME_ALIASES`.
- If the same canonical tool appears in both channels, one row is written with `sources=github;google`.
- A collision between different GitHub repositories raises an error instead of silently merging uncertain identities.

Run:

```bash
python3 merge_tool_sources.py
```

The final output is [`combined_tools_no_duplicates.csv`](combined_tools_no_duplicates.csv).

### 5. Collect and classify supported metrics

[`collect_metric_sources.py`](collect_metric_sources.py) reads every combined tool. For GitHub-backed tools it collects the repository README and relevant linked documentation. Tools without repositories use the official documentation registry in [`metric_source_urls.csv`](metric_source_urls.csv). Collection results, including failures, are written to `metric_source_documents.jsonl`.

[`extract_tool_metrics.py`](extract_tool_metrics.py) finds metric candidates using the controlled vocabulary in [`metric_taxonomy.py`](metric_taxonomy.py). It records the original wording, normalized metric, category, inferred support type, source URL, evidence, confidence, and review status in `tool_metric_candidates.csv`.

[`normalize_and_review_metrics.py`](normalize_and_review_metrics.py) deduplicates those candidates and writes the long-form `tool_metrics.csv`. Automated candidates remain marked `needs_review`; the pipeline never treats a keyword match as confirmed support.

Human decisions belong in [`tool_metrics_review.csv`](tool_metrics_review.csv), keyed by `tool_key`, `metric_normalized`, and `support_type`. The normalization stage adds new candidate keys without overwriting existing decisions. Use `confirmed` to approve a row or `exclude` to remove a false positive. Because reviews are stored separately, rerunning the pipeline preserves them.

Set `GITHUB_TOKEN` before a full run. It increases both GitHub search and documentation collection rate limits.

To refresh only the metrics stage from the current combined tool set:

```bash
python3 collect_metric_sources.py
python3 extract_tool_metrics.py
python3 normalize_and_review_metrics.py
```

## Run the local processing stages

When the raw GitHub results and final Google screening table already exist, regenerate the filtered and combined outputs with:

```bash
python3 filter_github_results.py
python3 merge_tool_sources.py
```

To rebuild the GitHub source data as well:

```bash
python3 github_tool_search.py
python3 filter_github_results.py
python3 merge_tool_sources.py
```

## Final combined columns

| Column | Meaning |
| --- | --- |
| `tool_key` | Normalized identity used for deduplication. |
| `tool` | Canonical display name. |
| `sources` | `github`, `google`, or `github;google`. |
| `github_repo` | GitHub `owner/repository`, when available. |
| `stars` | GitHub star count from the discovery run. |
| `last_push` | Most recent GitHub push date from the discovery run. |
| `license` | GitHub SPDX license value, when available. |
| `description` | GitHub repository description. |
| `google_independent_sources` | Independent-source count from the final Google screening. |
| `google_query_count` | Number of Google queries in which the tool appeared. |
| `google_rule` | Screening rule supporting the Google inclusion. |
| `google_reason` | Recorded reason for the Google inclusion. |

## Reproducibility notes

- The GitHub description is truncated to 150 characters by the discovery script, so automated screening may require explicit overrides for ambiguous cases.
- The filtering rules and canonical-name mappings are versioned in the Python scripts and should be reviewed when new naming patterns appear.
- The source CSV files remain separate from processed outputs so exclusions and merge decisions can be audited.
- Search results and GitHub metadata are time-dependent. Keep the run date in the CSV outputs when reporting results.
