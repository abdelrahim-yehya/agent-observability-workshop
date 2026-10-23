#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
GOOGLE_SCREENING="tool_screening_google.csv"
FINAL_OUTPUT="combined_tools_no_duplicates.csv"

usage() {
  printf '%s\n' \
    "Usage: ./run_pipeline.sh" \
    "" \
    "Run a fresh GitHub search, filter and merge the tools, collect their" \
    "documentation, and produce reviewable supported-metric candidates."
}

if [[ $# -gt 1 ]]; then
  usage >&2
  printf 'This command does not accept positional arguments.\n' >&2
  exit 2
fi

case "${1:-}" in
  "")
    ;;
  -h|--help)
    usage
    exit 0
    ;;
  *)
    usage >&2
    printf 'Unknown option: %s\n' "$1" >&2
    exit 2
    ;;
esac

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  printf 'Python executable not found: %s\n' "$PYTHON_BIN" >&2
  exit 1
fi

for required_file in \
  github_tool_search.py \
  filter_github_results.py \
  merge_tool_sources.py \
  collect_metric_sources.py \
  extract_tool_metrics.py \
  normalize_and_review_metrics.py \
  metric_taxonomy.py \
  metric_source_urls.csv \
  "$GOOGLE_SCREENING"; do
  if [[ ! -f "$required_file" ]]; then
    printf 'Required file not found: %s\n' "$required_file" >&2
    exit 1
  fi
done

printf 'Running a fresh GitHub search...\n'
"$PYTHON_BIN" github_tool_search.py

printf 'Filtering GitHub candidates...\n'
"$PYTHON_BIN" filter_github_results.py

printf 'Merging GitHub and screened Google tools...\n'
"$PYTHON_BIN" merge_tool_sources.py

printf 'Collecting metric documentation...\n'
"$PYTHON_BIN" collect_metric_sources.py

printf 'Extracting metric candidates...\n'
"$PYTHON_BIN" extract_tool_metrics.py

printf 'Normalizing metrics and applying review decisions...\n'
"$PYTHON_BIN" normalize_and_review_metrics.py

if [[ ! -s "$FINAL_OUTPUT" ]]; then
  printf 'Pipeline did not create a non-empty final output: %s\n' "$FINAL_OUTPUT" >&2
  exit 1
fi

tool_count="$("$PYTHON_BIN" -c 'import csv, sys; print(sum(1 for _ in csv.DictReader(open(sys.argv[1], encoding="utf-8", newline=""))))' "$FINAL_OUTPUT")"
metric_count="$("$PYTHON_BIN" -c 'import csv; print(sum(bool(row["metric_normalized"]) for row in csv.DictReader(open("tool_metrics.csv", encoding="utf-8", newline=""))))')"

printf '\nPipeline complete: %s unique tools\n' "$tool_count"
printf 'Output: %s/%s\n' "$SCRIPT_DIR" "$FINAL_OUTPUT"
printf 'Metric candidates requiring review: %s\n' "$metric_count"
printf 'Metrics output: %s/tool_metrics.csv\n' "$SCRIPT_DIR"
